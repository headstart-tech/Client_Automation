"""
This file contains class and functions related to assigned application on calls
"""
from app.database.configuration import DatabaseConfiguration
from bson.objectid import ObjectId
from app.helpers.telephony.assigned_counsellor_helper import AssignedCounsellor
from app.core.custom_error import CustomError
from app.core.log_config import get_logger

logger = get_logger(name=__name__)

class ApplicationAssigned:
    """
    All related functions of call assigned to any application
    """

    async def application_assigned_on_call(self, application_info: dict, missed_call_tag: bool) -> dict:
        """Helper function which call ends by the user and assigned applicationn on any call.

         Params:
            application_info (dict): A dictionary which contains call_id and application_id which have to assigned for that call.
            missed_call_tag (bool): A boolean data if true then that that lead as missed call.

        Returns:
            dict: A dictionary which contains information about call ends.
        """

        try:
            application_id = ObjectId(application_info.get("application_id"))
            if (call_id := application_info.get("call_id")):
                await DatabaseConfiguration().call_activity_collection.update_one({"_id": ObjectId(call_id)}, {"$set": {
                    "application": application_id
                }})
            else:
                phone_num = int(application_info.get("phone_num")[3:])
                calls = await AssignedCounsellor().match_stage_calls(phone_num)

                for call in calls:
                    await DatabaseConfiguration().call_activity_collection.update_one({"_id": call.get("_id")}, {"$set": {
                        "application": application_id
                    }})

            if missed_call_tag:
                lead_application = await DatabaseConfiguration().studentApplicationForms.find_one({"_id": application_id})
                await DatabaseConfiguration().studentsPrimaryDetails.update_one({"_id": lead_application.get("student_id")}, {
                    "$addToSet": {
                        "tags": "Missed Call"
                    }
                })

        except Exception as error:
            logger.error(f"There is somethig wrong in updating data, error - {error}")
            raise CustomError("There is something wrong in updating data")


        return {"message": "Application assigned on call successfully."}
