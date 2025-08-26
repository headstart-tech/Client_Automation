"""
This file contains class and functions related to call initiate.
"""
from app.database.configuration import DatabaseConfiguration
from app.core.utils import settings, utility_obj
from fastapi.exceptions import HTTPException
from bson.objectid import ObjectId
from app.helpers.telephony.telephony_webhook_helper import TelephonyWebhook
from app.helpers.telephony.call_popup_websocket import manager
from app.core.log_config import get_logger
from datetime import datetime
import httpx, json

logger = get_logger(name=__name__)

class CallInitiateHelper:
    """
    All related functions of call initiate from the counsellor side
    """

    async def initiate_call(self, user: dict, call_initiate: dict, college: str) -> dict:
        """Helper function which initiate call through mcube.

         Params:
            user (dict): A dictionary which contains user information.
            call_initiate (dict): A dictionary which contains call_initiate information like calling number of lead from the system.
            college (str): College ID

        Returns:
            dict: A dictionary which contains information about call initiate.
        """

        
        if (telephony_secret_key := settings.telephony_secret_key) is None:
            raise HTTPException(status_code=404, detail="Telephony secret key not found.")

        url = "http://mcube.vmc.in/api/outboundcall"

        base_path = settings.base_dev_path

        student_phone = call_initiate.get("student_phone")[3:]

        params = {
            "apikey": telephony_secret_key,
            "exenumber": str(user.get("mobile_number"))[:10],
            "custnumber": student_phone,
            "url": f"{base_path}telephony/webhook?college_id={college}",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                detail = f"Call initiation failed with status {e.response.status_code}: {e.response.text}"
                raise HTTPException(status_code=e.response.status_code, detail=detail)
            except httpx.RequestError as e:
                raise HTTPException(status_code=500, detail=f"An error occurred while initiating the call: {str(e)}")

        response_data = response.json()


        student_details = await DatabaseConfiguration().studentsPrimaryDetails.find_one({
            "basic_details.mobile_number": student_phone
        })

        data = {
            "call_id": response_data.get("callid"),
            "type": "Outbound",
            "call_from": ObjectId(user.get("_id")),
            "call_from_name": utility_obj.name_can(user),
            "call_from_number": user.get("mobile_number"),
            "call_to_number": int(student_phone),
            "call_to": student_details.get("_id"),
            "call_to_name": utility_obj.name_can(student_details.get("basic_details", {})),
            "show_popup": True,
            "created_at": datetime.utcnow()
        }

        await DatabaseConfiguration().studentsPrimaryDetails.update_one({
                "basic_details.mobile_number": student_phone
            },
            {
                "$pull": {
                    "tags": "Missed Call"
                }
            }
        )

        if call_initiate.get("application_id"):

            student_application = await DatabaseConfiguration().studentApplicationForms.find_one({
                "_id": ObjectId(call_initiate.get("application_id"))
            })

            if student_application:
                data.update({
                    "application": student_application.get("_id")
                })

            if await DatabaseConfiguration().call_activity_collection.find_one({"call_id": response_data.get("callid")}):
                await DatabaseConfiguration().call_activity_collection.update_one({"call_id": response_data.get("callid")}, {"$set": data})
            
            else:
                await DatabaseConfiguration().call_activity_collection.insert_one(data)

        # This code executes in case of missed call
        else:
            if await DatabaseConfiguration().call_activity_collection.find_one({"call_id": response_data.get("callid")}):
                await DatabaseConfiguration().call_activity_collection.update_one({"call_id": response_data.get("callid")}, {"$set": data})
            
            else:
                await DatabaseConfiguration().call_activity_collection.insert_one(data)

        call_activity = await TelephonyWebhook().websocket_data(user.get("_id"))
        await manager.publish_data_on_redis(f"{user.get('_id')}_telephony", call_activity)


        return {"message": "Call initiate successfully."}
    
