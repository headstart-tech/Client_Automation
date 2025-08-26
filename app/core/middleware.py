import random
import string
import time
import json
import asyncio
import os
import logging
from datetime import datetime, timezone
from starlette.datastructures import URL, MutableHeaders
from starlette.requests import Request
from app.core.utils import utility_obj, settings
from app.core.settings.tag_metadata import tags_metadata
from app.dependencies.oauth import get_redis_client
from app.core.log_config import get_logger

logger = get_logger(name=__name__)
avoid_prefix = []
avoid_urls = ["/", "/openapi.json", "/docs", "/favicon.ico", "/redoc", "/payments/webhook/{college_id}/",
              "/reports/webhook/", "/sms/webhook/", "/email/webhook/", "/whatsapp/webhook/", "/tawk/webhook/",
              "/telephony/webhook/"]
route_details = tags_metadata[0].get("route_details", {}) if tags_metadata else []
avoid_prefix_urls = []
for i in avoid_prefix:
    avoid_prefix_urls += route_details.get(i, {}).get("routes", {}).keys()
rate_limit_type = settings.rate_limit_type
private_api_limit = settings.private_limit_count
public_api_limit = settings.public_limit_count
global_api_limit = settings.global_limit_count
advance_private_api_limit = settings.advance_private_limit_count
advance_public_api_limit = settings.advance_public_limit_count
advance_global_api_limit = settings.advance_global_limit_count
testing_env = utility_obj.read_current_toml_file().get("testing", {}).get("test")


class BaseMiddleware:
    """
    Base middleware class for handling common operations among middlewares.
    """

    def __init__(self, app):
        self.app = app

    async def get_user_data_and_rate_limit(
        self,
        scope,
        api_type,
        redis_client
    ):
        """
        Retrieve user data and determine the rate limit based on API type and scope.

        Parameters:
            scope (dict): Request metadata including headers.
            api_type (str): The type of API being accessed, either "Private" or "Public".

        Returns:
        tuple
            user_data (str): User data based on client IP or authorization token.
            rate_limit (int): Rate limit value based on the API type.
        """
        while True:
            try:
                request = Request(scope)
                if "X-Forwarded-For" in request.headers:
                    user_ip = request.headers["X-Forwarded-For"].split(",")[0]
                else:
                    user_ip = request.client.host
                scope["ip_address"] = user_ip
                scope["port"] = request.client.port
                user_data = user_ip
                redis_data = await redis_client.lrange("extra_limit_ip_collection", 0, -1)
                extra_limit_ips = json.loads(redis_data[0]) if redis_data else []
                has_extra_limits = user_ip in extra_limit_ips
                if rate_limit_type == "api_wise":
                    if api_type == "Private":
                        user_data += "_private"
                        has_extra_limits = True if user_data in extra_limit_ips else has_extra_limits
                        rate_limit = advance_private_api_limit if has_extra_limits else private_api_limit
                    else:
                        user_data += "_public"
                        rate_limit = advance_public_api_limit if has_extra_limits else public_api_limit
                else:
                    user_data += "_global"
                    rate_limit = advance_global_api_limit if has_extra_limits else global_api_limit
                return user_data, rate_limit, has_extra_limits
            except ConnectionError as e:
                logger.error(f"Some connection error occurred while connecting to Redis: {e}")
                continue

    async def get_api_used_count(self, user_data, end_point, redis_client):
        """
        Get the count of API hits for the user and endpoint.

        Parameters:
            user_data (str): User identifier.
            end_point (str): API endpoint.

        Returns:
            int: API hit count.
        """
        try:
            rate_limit_count = len(await redis_client.keys(f"*{str(user_data) + '_api_used'}*"))
            return rate_limit_count
        except Exception as e:
            logger.error(f"Some connection error occurred while fetching data from Redis: {e}")
            return 0


    async def change_api_response(
        self,
        send,
        api_type,
        rate_limit_count,
        endpoint,
        user_data,
        has_extra_limits,
        redis_client
    ):
        """
        Change API response based on rate limits and API type.

        Parameters:
            send (callable): ASGI send function to send responses.
            api_type (str): Type of API, either "Public" or "Private".
            rate_limit_count (int): Current count of API hits for the user.
            endpoint (str): The API endpoint being accessed.
            user_data (str): User identifier.
            has_extra_limits (bool): Indicates whether the user has extra rate limits based on their account type.

        Returns:
            status (bool): Indicates if the rate limit was exceeded.
        """
        limit_exceeded_error_start = {
            "type": "http.response.start",
            "status": 429,  # Status code for "Too Many Requests"
            "headers": [
                (b"content-type", b"application/json"),
            ],
        }
        limit_exceeded_error_body = {
            "type": "http.response.body",
            "body": b'{"detail": "Too many requests. Please try again after some time. Continuing to hit this API may '
                    b'result in your IP address being blocked."}',
            "more_body": False,  # Set to False indicating this is the end of the response body
        }
        status = True
        if rate_limit_type == "api_wise":
            public_limit = advance_public_api_limit if has_extra_limits else public_api_limit
            private_limit = advance_private_api_limit if has_extra_limits else private_api_limit
            if (api_type == "Public" and rate_limit_count >= public_limit) or (
                api_type == "Private" and rate_limit_count >= private_limit
            ):
                await send(limit_exceeded_error_start)
                await send(limit_exceeded_error_body)
                status = False
            else:
                await utility_obj.store_api_hit(user_data, endpoint, redis_client)
        else:
            global_limit = advance_global_api_limit if has_extra_limits else global_api_limit
            if rate_limit_count >= global_limit:
                await send(limit_exceeded_error_start)
                await send(limit_exceeded_error_body)
                status = False
            else:
                await utility_obj.store_api_hit(user_data, endpoint, redis_client)
        return status

    async def set_headers(self, url, scope, send) -> dict:
        """
        Asynchronously sets headers and metadata for an API request.

        This method:
        - Extracts the API description and type from the URL.
        - Retrieves user data and rate limit information.
        - Computes the API usage count for rate limiting.
        - Updates the response based on rate limit checks.

        Params:
            url (str): The request URL.
            scope (dict): ASGI scope with request data.
            send (Callable): ASGI send function to send response.

        Returns:
            dict: Updated scope with API description, type, user data, rate limit, and usage count.
        """
        endpoint = scope.get("path", "")
        api_type = "Public"
        for key, value in scope.get('headers', []):
            if key == b'authorization':
                if value.startswith(b'Bearer '):
                    api_type = "Private"
                break
        scope["api_type"] = api_type
        redis_client = get_redis_client()
        user_data, rate_limit, has_extra_limits = await self.get_user_data_and_rate_limit(scope, api_type, redis_client)
        scope["user_data"] = user_data
        scope["rate_limit"] = rate_limit
        scope["has_extra_limits"] = has_extra_limits
        rate_limit_count = await self.get_api_used_count(user_data, endpoint, redis_client)
        scope["rate_limit_count"] = rate_limit_count if rate_limit_count else 0
        rate_limit_check = await self.change_api_response(
            send,
            api_type,
            rate_limit_count,
            endpoint,
            user_data,
            has_extra_limits,
            redis_client
        )
        scope["rate_limit_check"] = rate_limit_check
        return scope


class AuditAndHeaderMiddleware(BaseMiddleware):
    """
    Run with every API request and return the total time taken by APIs to run in the response
    """

    def __init__(self, app):
        super().__init__(app)
        self.log_queue = asyncio.Queue()
        self.worker_task = asyncio.create_task(self.log_worker())

    async def log_worker(self):
        """
        Continuously processes log data from the queue, publishing to RabbitMQ.
        On failure, writes data to a local log file.
        """
        while True:
            data, queue_name = await self.log_queue.get()
            try:
                await utility_obj.publish_to_rabbitmq(data, queue_name)
            except Exception as e:
                logger.error(f"Error sending data to logging service: {e}")
                log_file = 'local_logs.log'
                if queue_name == "role_permission_logs":
                    log_file = "rbac_activity_logs.log"
                with open(log_file, 'a') as f:
                    f.write(json.dumps(data) + '\n')
                logger.debug("Data sent to logging service!")
            finally:
                self.log_queue.task_done()

    async def common_data(self, scope, details=None, description=None, queue_name=None):
        """Generates common log data based on the request scope."""
        data = {
            "requested_user": scope.get("user_data"),
            "action": scope["path"],
            "details": details,
            "ip_address": scope.get("ip_address"),
            "port": scope.get("port"),
            "timestamp": str(datetime.now(timezone.utc)),
        }
        if description:
            data["description"] = description
        await self.log_queue.put((data, queue_name))
        return

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        url = URL(scope=scope)
        idem = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        logger.info(f"rid={idem} start request path={url.path}")
        start_time = time.perf_counter()
        if (
            scope["path"] not in avoid_urls
            and scope["path"] not in avoid_prefix_urls
            and len(scope["path"].split("/")) >= 3
        ):
            scope = await self.set_headers(url, scope, send)
            if not scope["rate_limit_check"]:
                error_message = (
                    "Too many requests. Please try again after some time. Continuing to hit this API may "
                    "result in your IP address being blocked."
                )
                await self.common_data(scope, details=error_message)
                logger.debug(error_message)
                return

        async def send_with_extra_headers(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                process_time_ms = (time.perf_counter() - start_time) * 1000
                process_time_sec = process_time_ms / 1000
                formatted_process_time_ms = "{0:.2f}".format(process_time_ms)
                formatted_process_time_sec = "{0:.2f}".format(process_time_sec)
                headers.append("X-Process-Time", f"{str(formatted_process_time_ms)} ms")
                headers.append(
                    "X-Process-Time-Sec", f"{str(formatted_process_time_sec)} s"
                )
                rate_limit = scope.get("rate_limit", 0)
                rate_limit_count = scope.get("rate_limit_count", 0)
                headers.append("X-RateLimit-Limit", str(rate_limit))
                headers.append(
                    "X-RateLimit-Remaining",
                    str(max(rate_limit - rate_limit_count - 1, 0)),
                )
                headers.append("X-RateLimit-Reset", "60 s")
                status = message["status"]
                logger.info(
                    f"rid={idem} request completed_in={formatted_process_time_ms}ms ({formatted_process_time_sec}s) status_code={status}"
                )
            if message["type"] == "http.response.body":
                response_data = message["body"].decode("utf-8")
                try:
                    response_dict = json.loads(response_data) if response_data else {}
                except Exception as e:
                    logger.error(f"JSON decode error: {e}")
                    response_dict = {}
                route = scope["route"].path if "route" in scope else scope.get("path", "")
                description, queue_name = utility_obj.get_api_and_description(route)
                await self.common_data(scope, details=response_dict, description=description, queue_name = queue_name)
                logger.debug("data stored into audit history!")

            await send(message)

        await self.app(scope, receive, send_with_extra_headers)
