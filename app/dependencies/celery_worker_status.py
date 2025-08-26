from functools import wraps
from urllib.parse import urlparse

import redis
from fastapi import HTTPException
from redis.exceptions import RedisError

from app.core.celery_app import create_celery_app
from app.core.log_config import get_logger
from app.core.utils import settings

logger = get_logger(__name__)
app = create_celery_app()


def require_celery_connection(func):
    """
    Decorator to ensure Celery connection before executing a function.
    If Celery workers are not available, it raises an HTTPException.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.warning("Inside Celery connection decorator")

        try:
            i = app.control.inspect(timeout=5)
            active = i.active()
            reserved = i.reserved()

            if not active and not reserved:
                logger.warning("No active or reserved Celery workers found.")
                raise HTTPException(status_code=503,
                                    detail="Celery workers are not available")

            logger.info(f"Active Workers: {active}")
            logger.info(f"Reserved Tasks: {reserved}")
        except Exception as e:
            logger.error(f"Error checking Celery worker status: {e}")
            raise HTTPException(status_code=503,
                                detail="Error in connecting to Celery")

        return func(*args, **kwargs)

    return wrapper


# def require_redis_connection(func):
#     """
#     Decorator to ensure Redis connection before executing an async function.
#     If Redis is not available, it raises an HTTPException.
#     """
#
#     @wraps(func)
#     async def wrapper(*args, **kwargs):
#         logger.warning("Inside Redis connection decorator")
#         try:
#             redis_url = urlparse(settings.redis_server_url)
#             redis_client = redis.StrictRedis(
#                 host=redis_url.hostname,
#                 port=redis_url.port,
#                 password=redis_url.password,
#                 socket_timeout=5
#             )
#             if not redis_client.ping():
#                 raise HTTPException(status_code=503,
#                                     detail="Redis is not available")
#             logger.info("Successfully connected to Redis.")
#             logger.info("Redis connection details")
#             logger.info(redis_client.info())
#         except RedisError:
#             raise HTTPException(status_code=503,
#                                 detail="Redis is not available")
#
#         return await func(*args, **kwargs)
#
#     return wrapper
