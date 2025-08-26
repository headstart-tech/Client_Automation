"""
This file contains class and functions related to notification
"""
import asyncio
import datetime
import json
from json import dumps

from bson import ObjectId
from fastapi import WebSocket
from pymongo.errors import OperationFailure

from app.core.log_config import get_logger
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import Authentication

logger = get_logger(name=__name__)


class Notification:
    """
    Contains functions related to notification
    """

    async def send_notifications(self, websocket: WebSocket, user_id: str):
        """
        Send notification through websocket
        """
        if not user_id:
            logger.warning("User not found, skipping sending notifications.")
            return
        # Listen for changes in the notifications collection
        try:
            async with DatabaseConfiguration().notification_collection.watch(full_document='updateLookup') as stream:
                async for change in stream:
                    if change is None:
                        continue
                    # Check if the inserted document contains the specified user ID
                    if change.get('operationType') == "insert":
                        if str(change.get("fullDocument", {}).get("send_to", "")) == user_id:
                            current_datetime = datetime.datetime.utcnow()
                            hours = abs(
                                int((current_datetime - change.get("fullDocument", {}).get("event_datetime",
                                                                                           current_datetime)).total_seconds() // 3600))
                            if utility_obj.local_time_for_compare(
                                    current_datetime.strftime("%d-%m-%Y %H:%M:%S")).strftime(
                                "%d-%m-%Y") == utility_obj.local_time_for_compare(
                                change.get("fullDocument", {}).get("event_datetime", current_datetime).strftime(
                                    "%d-%m-%Y %H:%M:%S")).strftime("%d-%m-%Y"):
                                event_datetime = f"{hours} hours ago"
                                category = "today"
                            else:
                                yesterday = str(datetime.date.today() - datetime.timedelta(days=1)).split(
                                    " "
                                )
                                days = abs((
                                                   utility_obj.local_time_for_compare(
                                                       current_datetime.strftime("%d-%m-%Y %H:%M:%S"))
                                                   - utility_obj.local_time_for_compare(
                                               change.get("fullDocument", {}).get("event_datetime",
                                                                                  current_datetime).strftime(
                                                   "%d-%m-%Y %H:%M:%S"
                                               ))).days)
                                if yesterday[0] == utility_obj.local_time_for_compare(
                                        change.get("fullDocument", {}).get("event_datetime").strftime(
                                            "%d-%m-%Y %H:%M:%S")
                                ).strftime("%Y-%m-%d"):
                                    if hours < 24:
                                        event_datetime = f"{hours} hours ago"
                                    else:
                                        event_datetime = f"{days} day ago"
                                    category = "yesterday"
                                else:
                                    event_datetime = f"{days} days ago"
                                    category = "older"
                            # Send the notification to the React web app via the WebSocket connection
                            await websocket.send_text(dumps({
                                "notification_id": str(change.get("fullDocument", {}).get("_id")),
                                "event_type": change.get("fullDocument", {}).get("event_type"),
                                "student_id": str(change.get("fullDocument", {}).get("student_id")),
                                "application_id": str(change.get("fullDocument", {}).get("application_id")),
                                "message": change.get("fullDocument", {}).get("message"),
                                "mark_as_read": change.get("fullDocument", {}).get("mark_as_read"),
                                "event_datetime": event_datetime,
                                "category": category
                            }))
                            await asyncio.sleep(18000)
        except OperationFailure as e:
            logger.error("Unable to start change stream: %s" % e)
        finally:
            pass

    async def get_user_details(self, websocket: WebSocket, college_id):
        """
        Get user details with the help of data sent through websocket
        """
        try:
            data = await websocket.receive_text()
            if data is not None:
                data = json.loads(data)
                token_data = await Authentication().verify_token(data.get('access_token'),
                                                                 {"detail": "Could not validate credentials"},
                                                                 websocket=True)
                if (
                        user := await DatabaseConfiguration().user_collection.find_one(
                            {"user_name": token_data.user_name, "associated_colleges": {"$in": [ObjectId(college_id)]}})
                ) is None:
                    user = {}
                if not user:
                    logger.error(f"User not found for college_id: {college_id}")
                    return None
                
                return user

        except Exception as e:
            logger.error(f"Something went wrong. {e}")
