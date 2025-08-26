"""
This file contains class and functions related to call end popup dispose.
"""
from app.database.configuration import DatabaseConfiguration
from bson.objectid import ObjectId
from app.helpers.telephony.telephony_webhook_helper import TelephonyWebhook
from app.helpers.telephony.call_popup_websocket import manager

class CallEndHelper:
    """
    All related functions of call end dispose from the counsellor side
    """

    async def popup_dispose_on_call_end_helper(self, user: dict, call_end: dict) -> dict:
        """Helper function which call ends by the user and dispose popup from the screen.

         Params:
            user (dict): A dictionary which contains user information.
            call_end (dict): A dictionary which contains call_end information like call unique id (_id) and application_id which have to assigned for that call.

        Returns:
            dict: A dictionary which contains information about call ends.
        """

        data = {
            "show_popup": False
        }

        application_id = call_end.get("application_id")

        if application_id:
            data.update({
                "application": ObjectId(application_id)
            })

        await DatabaseConfiguration().call_activity_collection.update_one({"_id": ObjectId(call_end.get("call_id"))}, {"$set": data})

        user_id = user.get("_id")

        call_activity = await TelephonyWebhook().websocket_data(user_id)
        await manager.publish_data_on_redis(f"{user_id}_telephony", call_activity)
        # await manager.send_message(call_activity, user_id)
        return {"message": "Call end and dispose successfully."}
