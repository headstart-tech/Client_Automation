"""
This file contain class and functions related to Call Review Query
"""
import datetime
from bson.objectid import ObjectId
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.core.custom_error import CustomError
from enum import Enum


class ReviewFields(Enum):
    # Enumerator value of the fields which has to be validate
    QC_STATUS = "qc_status"
    PRODUCT_KNOWLEDGE = "product_knowledge"
    CALL_STARTING = "call_starting"
    CALL_CLOSING = "call_closing"
    ISSUE_HANDLING = "issue_handling"
    ENGAGEMENT = "engagement"
    CALL_QUALITY_SCORE = "call_quality_score"


class ReviewQuery:
    async def score_validate(self, calll_review_dict: dict):
        """Validate all the required field with correct data.

        Params:
            - call_review_dict (dict): A dictionary which contains all the data set.

        Returns:
            - bool: A boolean value True when all the data are validate.
        """
        if calll_review_dict[ReviewFields.QC_STATUS.value] not in ['Accepted', 'Rejected', 'Fatal Rejected']:
            raise CustomError(f"{ReviewFields.QC_STATUS.value} must be 'Accepted', 'Rejected' or 'Fatal Rejected'")
        
        for value in [ReviewFields.PRODUCT_KNOWLEDGE.value, ReviewFields.CALL_STARTING.value, ReviewFields.CALL_CLOSING.value, ReviewFields.ISSUE_HANDLING.value, ReviewFields.ENGAGEMENT.value]:
            await utility_obj.is_score_valid(calll_review_dict[value], value)
        
        await utility_obj.is_quality_score_valid(calll_review_dict[ReviewFields.CALL_QUALITY_SCORE.value], ReviewFields.CALL_QUALITY_SCORE.value)

        return True


    async def create_review(self, call_review_data: dict, user: dict, call_id: str) -> dict:
        """
        Validate call review data and add call review data in the collection.

        Params:
            - call_review_data (dict): A dictionary which contains call review data.
            - user (dict): A dictionary which contains user data.
            - call_id (str): An unique id/identifier of a call.

        Returns:
            - dict: A dictionary which contains information about call review.

        Raises:
            - CustomError: An error occurred when call data not found by call_id.
        """

        created_at = datetime.datetime.utcnow()     # current date time
        user_name = utility_obj.name_can(user)      # user name which applied update or insert
        user_id = ObjectId(user.get("_id"))         # user id
        added_data = {
            "date_time": created_at,
            "qced_qa": user_id,
            "qced_qa_name": user_name,
        }
        call_review_data.update(added_data)

        await utility_obj.is_length_valid(call_id, name="Call ID")
        if (call := await DatabaseConfiguration().call_activity_collection.find_one({"_id": ObjectId(call_id)})) is None:
            # If invalid ID of the call.
            raise CustomError(f"Call not found by id: {call_id}")

        # Create data segment of which contains None if there is empty field in place of blank.
        call_review_dict = {key: value for key, value in call_review_data.items() if value is not None}

        await self.score_validate(call_review_dict)

        qced_calls = call.get("qced")
        if not qced_calls:
            qced_calls = []

        qced_calls.insert(0, call_review_dict)

        await DatabaseConfiguration().call_activity_collection.update_one(
            {'_id': ObjectId(call_id)},
            {
                "$set": {
                    "qced": qced_calls
                }
            }
        )

        return {"message": "Review added successfully."}