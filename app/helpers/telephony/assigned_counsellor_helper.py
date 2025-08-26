"""
This file contains class and functions related to assigned counsellor on missed calls
"""
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import cache_invalidation
from app.core.log_config import get_logger
from app.core.utils import utility_obj

logger = get_logger(name=__name__)

class AssignedCounsellor:
    """
    All related functions of counsellor assigned to any calls
    """

    async def match_stage_calls(self, phone: int|list[int]) -> list:
        """Match stage of call activity filter helper

        Params:
            phone (int | list[int]): It should be a phone number or a list of phone number

        Returns:
            list: Returns the list of calls related to the given phone number(s)
        """
        return await (DatabaseConfiguration().call_activity_collection.aggregate([
            {
                '$match': {
                    'call_from_number': {
                        '$in': phone
                    } if isinstance(phone, list) else phone, 
                    'status': {
                        '$in': ['NOANSWER', 'BUSY', 'CANCEL', "Missed"]
                    }
                }
            }
        ])).to_list(None)


    async def counsellor_assigned_on_call(self, counsellor: dict, phone_numbers: list[int]) -> dict:
        """Counsellor assigned on missed call helper

        Params:
            counsellor (dict): counsellor details
            phone_numbers (list[int]): List of student phone number

        Returns:
            dict: Response message
        """
        calls = await self.match_stage_calls(phone_numbers)

        for call in calls:
            await DatabaseConfiguration().call_activity_collection.update_one({"_id": call.get("_id")}, {"$set": {
                "call_to": counsellor.get("_id"),
                "call_to_name": utility_obj.name_can(counsellor),
                "call_to_number": counsellor.get("mobile_number")
            }})

        await cache_invalidation(api_updated="telephony/assigned_counsellor_on_missed_call")

        return {"message": "Counsellor updated successfully"}