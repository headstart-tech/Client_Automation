"""
This file contains of the counselor route functions
"""

from datetime import datetime

from bson import ObjectId

from app.core.celery_app import celery_app
from app.core.utils import utility_obj
from app.database.database_sync import DatabaseConfigurationSync


class manual_allocation:
    """
    Manual counselor allocation to the function
    """

    @staticmethod
    @celery_app.task(ignore_result=True)
    def counselor_allocation_helper(offline_data_id: list, counselor_id: str):
        """
        Allocation manual counselor
        params:
            offline_counselor_id (list): The id of the offline counselor id
                                        to be allocated
            counselor_id (str): The id of the counselor id to be allocated

        returns:
            response: successful allocation to the counselor
        """
        counselor_detail = DatabaseConfigurationSync(
            database="master"
        ).user_collection.find_one({"_id": ObjectId(counselor_id)})
        data = {
            "allocate_to_counselor": {
                "counselor_id": counselor_detail.get("_id"),
                "counselor_name": utility_obj.name_can(counselor_detail),
                "last_update": datetime.utcnow(),
            }
        }
        for offline_id in offline_data_id:
            if (
                DatabaseConfigurationSync().lead_upload_history.find_one(
                    {"_id": ObjectId(offline_id)}
                )
                is None
            ):
                continue
            DatabaseConfigurationSync().studentsPrimaryDetails.update_many(
                {"lead_data_id": offline_id}, {"$set": data}
            )
