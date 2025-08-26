"""
this file contains all function of email subscribe from email route file
"""
import datetime
from typing import Optional

from bson import ObjectId
from fastapi.exceptions import HTTPException

from app.core.reset_credentials import Reset_the_settings
from app.database.configuration import DatabaseConfiguration
from app.database.database_sync import DatabaseConfigurationSync
from fastapi import status
from app.dependencies.jwttoken import Authentication


class unsubscribe:
    """this class handle email subscribe or unsubscribe"""

    async def unsubscribe_promotional_email(
        self,
        token: str,
        unsubscribe_status: bool,
        is_raw_data: str,
        data_segment_id: Optional[str],
        release_type: Optional[str],
        template_id: Optional[str],
        user_id: Optional[str],
        reason: Optional[str],
        category: Optional[str],
        release_date: Optional[str]
    ) -> bool:
        """
            Update the subscription status of a student in primary details.

            This function unsubscribes a student from promotional email notifications
            based on the provided token and other parameters.

            Params:
                token (str): Unique identifier for the student.
                unsubscribe_status (bool): Flag to indicate whether to unsubscribe.
                is_raw_data (str): Indicates if raw data processing is required.
                data_segment_id (Optional[str]): ID of the data segment (if applicable).
                release_type (Optional[str]): Type of release associated with the email.
                template_id (Optional[str]): ID of the email template.
                user_id (Optional[str]): ID of the user who sent the mail.
                reason (Optional[str]): Reason for unsubscribing.
                category (Optional[str]): Category of the email being unsubscribed from.
                release_date (Optional[str]): Date when the email was released.

            Returns:
                bool: True If action is successful else False
        """
        credentials_exception = HTTPException(
            detail="Token is not valid", status_code=status.HTTP_401_UNAUTHORIZED
        )
        data = await Authentication().get_token_details(token, credentials_exception)
        email_id = data.get("sub")
        college_info = data.get("college_info")
        college_id = college_info[0].get("_id") if college_info else None
        if college_id:
            Reset_the_settings().check_college_mapped(college_id=college_id)
            Reset_the_settings().get_user_database(college_id)
            if is_raw_data == "false":
                student = await DatabaseConfiguration().studentsPrimaryDetails.find_one({"user_name": email_id})
            else:
                student = await DatabaseConfiguration().raw_data.find_one({"mandatory_field.email": email_id})
            if student:
                tags, data_segment, template_details, user_details = student.get("tags", []), {}, {}, {}
                if data_segment_id:
                    data_segment_id = ObjectId(data_segment_id)
                    data_segment = await DatabaseConfiguration().data_segment_collection.find_one({"_id": data_segment_id})
                if template_id and ObjectId.is_valid(template_id):
                    if (template_details := await DatabaseConfiguration().template_collection.find_one({"_id": ObjectId(template_id)})) is None:
                        template_details = {}
                if user_id and ObjectId.is_valid(user_id):
                    if (user_details := await DatabaseConfiguration().user_collection.find_one({"_id": ObjectId(user_id)})) is None:
                        user_details = {}
                if unsubscribe_status:
                    if "DND" not in tags:
                        tags.append("DND")
                    unsubscribe = {
                        "value": True,
                        "release_type": release_type.title() if release_type else "Manual",
                        "user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id,
                        "user_name": user_details.get("user_name") if user_details else "",
                        "datasegment_id": ObjectId(data_segment_id) if ObjectId.is_valid(data_segment_id) else data_segment_id,
                        "template_id": ObjectId(template_id) if ObjectId.is_valid(template_id) else template_id,
                        "template_name": template_details.get("template_name") if template_details else "",
                        "timestamp": datetime.datetime.utcnow(),
                        "data_segment_data_type": data_segment.get("module_name", "") if data_segment else None,
                        "data_segment_type": data_segment.get("segment_type", "") if data_segment else None,
                        "excluded": True,
                        "excluded_timestamp": datetime.datetime.utcnow(),
                        "category": category,
                        "reason": reason if reason else "",
                        "release_date": datetime.datetime.fromisoformat(release_date) if release_date else None
                    }
                else:
                    if "DND" in tags:
                        tags.remove("DND")
                    unsubscribe = {
                        "value": False,
                        "release_type": None,
                        "user_id": None,
                        "datasegment_id": None,
                        "template_id": None,
                        "timestamp": datetime.datetime.utcnow(),
                        "data_segment_data_type": None,
                        "data_segment_type": None
                    }
                if is_raw_data == "true":
                    if unsubscribe_status:
                        unsubscribe.update(
                            {"offline_data_id": ObjectId(student.get("offline_data_id"))}
                        )
                    await DatabaseConfiguration().raw_data.update_one({
                        "mandatory_field.email": email_id},
                        {
                            "$set": {"unsubscribe":  unsubscribe}
                        }
                    )
                else:
                    await DatabaseConfiguration().studentsPrimaryDetails.update_one({"user_name": email_id},
                                                                                    {"$set": {"unsubscribe": unsubscribe,
                                                                                              "tags": tags
                                                                                    }})
                return True
            else:
                return False
        else:
            return False


    def filter_email_unsubscribe(self, email_ids):
        """
        filter to unsubscribe email from the list of email
        """
        pipeline = [
            {
                "$match": {
                    "user_name": {"$in": email_ids},
                    "$or": [{"unsubscribe": False}, {"unsubscribe": {"$exists": False}}]
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "user_name": 1
                }
            },
            {
                "$group": {
                    "_id": 0,
                    "email_id": {
                        "$push": "$user_name"
                    }
                }
            }
        ]
        result = DatabaseConfigurationSync().studentsPrimaryDetails.aggregate(
            pipeline)
        for student_doc in result:
            if student_doc is not None:
                return student_doc.get("email_id", [])
        return []
