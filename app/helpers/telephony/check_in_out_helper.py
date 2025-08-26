"""
Check-in active/inactive function
"""
from app.database.configuration import DatabaseConfiguration
from app.core.utils import settings, utility_obj
from fastapi.exceptions import HTTPException
from app.dependencies.oauth import cache_invalidation
from datetime import datetime
from bson.objectid import ObjectId
import httpx


class CheckInOutHelper:
    """
    All related functions of Check-in active/inactive from telephony.
    """

    async def update_check_status(self, user: dict, check_in_out_data: dict) -> dict:
        """
        Check-in active/inactive API updation function from telephony dashboard and log activity in database.

        Params:
            user (dict): Requested user (Counsellor, Head Counsellor, Moderator)
            check_in_out_data (dict): Check-in Activity user requested payload

        Returns:
            dict: Message response
        """

        if (telephony_secret_key := settings.telephony_secret_key) is None:
            raise HTTPException(status_code=404, detail="Telephony secret key not found.")

        check_dict = {
            "check_in_status": check_in_out_data.get("check_in_status")
        }

        if check_in_out_data.get("check_in_status") == False:
            check_dict.update({
                "reason": check_in_out_data.get("reason")
            })

        await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(user.get("_id"))},
            {
                "$set": check_dict
            }
        )
        await cache_invalidation(api_updated="telephony/multiple_check_in_or_out")
        await cache_invalidation(api_updated="updated_user", user_id=user.get("email") if user else None)
        check_in_out_query = {
            "user_id": ObjectId(user.get("_id")),
            "user_name": utility_obj.name_can(user),
            "datetime": datetime.utcnow()
        }

        payload = {
            "apikey": telephony_secret_key,
            "empnumber": user.get("mobile_number"),
            "empemail": user.get("email")
        }

        if check_in_out_data.get("check_in_status"):
            check_in_out_query.update({
                "check_in_status": check_in_out_data.get("check_in_status")
            })
            payload.update({
                "status": "1"
            })

        else:
            check_in_out_query.update({
                "check_in_status": check_in_out_data.get("check_in_status"),
                "reason": check_in_out_data.get("reason")
            })
            payload.update({
                "status": "0",
                "reason": check_in_out_data.get("reason", {}).get("title", "NO REASON GIVEN")
            })

        await DatabaseConfiguration().check_in_out_log.insert_one(check_in_out_query)

        url = "https://mcube.vmctechnologies.com/onlineAPI/self_disable"

        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json=payload)
        except:
            raise HTTPException(status_code=404, detail="Check-in status does not update from telephony dashboard.")
        
        return {"message": "Check-in status update successfully."}
