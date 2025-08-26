"""
Telephony websocket connection
"""
import asyncio
import json, redis
import random
from typing import Dict, List

import aio_pika
from fastapi import WebSocket
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.dependencies.oauth import get_redis_client, insert_data_in_cache, get_sync_redis_client
from app.helpers.notification.real_time_configuration import Notification
import threading


logger = get_logger(name=__name__)


class ConnectionManager:
    """
    This class contains all related functions for telephony websocket connections
    """

    async def connect(self, websocket: WebSocket, college: dict) -> dict:
        """Connect the browser to a websocket

        Params:
            websocket (WebSocket): websocket instance
            college (dict): college unique id

        Returns:
            dict: User details dictionary
        """
        try:
            await websocket.accept()
            user = await Notification().get_user_details(websocket, college.get("id"))
            if user:

                from app.helpers.telephony.telephony_webhook_helper import TelephonyWebhook
                call_activity = await TelephonyWebhook().websocket_data(user.get("_id"))

                await websocket.send_json({
                        "data": call_activity
                    })
                await self.publish_data_on_redis(f"{user.get('_id')}_telephony", call_activity)
            return user
        except Exception as e:
            logger.error(f"Something want wrong in connection websocket - {e}")


    async def send_message(self, websocket, key):
        """Send data to the browser from the websocket

        Params:
            websocket: Websocket details
            key: cache data unique key
        """
        try:
            r = get_redis_client()
            data = await r.get(key)
            data = json.loads(data)
            await websocket.send_json({
                "data": data
            })
        except Exception as e:
            logger.error("Message could not be sent by websocket")

    def run_async_function_telephony(self, websocket, key):
        """
            create a loop to run async function in thread

            Params:
                - websocket_con (obj): The websocket connection object to perform websocket operations
                - key: cache data unique key

            Returns:
                None

            Raises:
                - Exception: An error occurred when something wrong happen in the code.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.send_message(websocket, key))
            else:
                loop.run_until_complete(self.send_message(websocket, key))
        except Exception as error:
            logger.error(f"An error occurred while creating loop to call async telephony popup: {error}")

    async def publish_data_on_redis(self, key: str, data: list):
        """Function of publish data to the websocket

        Params:
            key (str): redis key
            data (list): data list which is to be sent on websocket
        """
        
        try:
            key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/{key}"
            call_activity = json.dumps(data)
            r = get_sync_redis_client()
            try:
                with r.pipeline() as pipe:
                    while True:
                        try:
                            pipe.watch(key)
                            pipe.multi()
                            if pipe.set(key, call_activity):
                                pipe.expire(key, (300 + random.randint(0, 300)))
                            pipe.execute()
                            break
                        except redis.WatchError as e:
                            logger.error(f"While storing telephony data in cache got error: {e}")
                            break
                        except redis.TimeoutError as e:
                            logger.error(f"Timeout while storing telephony data in cache: {e}")
                            break
                        except Exception as e:
                            logger.error(f"Some telephony internal error occurred: {e}")
                            break
                connection = await utility_obj.get_rabbitMQ_connection_channel()
                async with connection:
                    channel = await connection.channel()
                    message_body = "Data published"
                    exchange = await channel.declare_exchange(key, aio_pika.ExchangeType.FANOUT, durable=True)
                    await exchange.publish(
                        aio_pika.Message(body=message_body.encode()),
                        routing_key=""
                    )
                    await channel.close()
                await connection.close()
            except Exception as error:
                logger.error(f"An error occurred while storing the data in redis: {error} ")


        except Exception as e:
            logger.error(f"Publish data error - {e}")



manager = ConnectionManager()
