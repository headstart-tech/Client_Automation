"""
this file contains information about the email activity by the celery server
"""

import datetime

from bson import ObjectId

from app.core.celery_app import celery_app
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj
from app.database.database_sync import DatabaseConfigurationSync
from app.database.motor_base_singleton import MotorBaseSingleton


class email_activity:
    """A class representing an email activity that can be used
    to send emails to a celery server"""

    @staticmethod
    @celery_app.task(ignore_result=True)
    def storing_email_activity(
        payload: dict,
        current_user: str,
        ip_address: str | None = None,
        transaction_details: any = None,
        email_type: str | None = None,
        provider: str | None = None,
        college_id: str | None = None,
        offer_letter_information: dict | None = None,
        offer_letter_applicants: list | None = None,
        offered_applicants_info: list | None = None,
        scholarship_information: dict | None = None
    ):
        """
        Store email activity details of user in DB.

        Params:
            - payload (dict): A dictionary which contains email information like email_list, content and template_id.
            - current_user (str): Email id of currently looged in user.
            - ip_address (str | None): Default value: None. Either None or IP address of current user.
            - transaction_details (any): Default value: None. Either None or Email transaction information.
            - email_type (str | None): Default value: None. Either None or Type of email.
            - provider (str | None): Default value: None. Either None or Email service provider which useful for send
                mail.
            - college_id (str | None): Default value: None. Either None or unique identifier of college.
            - offer_letter_information (dict | None): Default value: None.
                A dictionary which contains offer letter information.
            - offer_letter_applicants (list | None): Default value: None. Either None or offer letter application ids.
            - offered_applicants_info (list | None): Default value: None. Either None or offered scholarship
                information.
            - scholarship_information (dict | None): Default value: None. Either None or scholarship information.

        Returns: None
        """
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)
        user_name = ""
        if (
            user := DatabaseConfigurationSync("master").user_collection.find_one(
                {"user_name": current_user}
            )
        ) is not None:
            user_name = utility_obj.name_can(user)
        else:
            if (
                user := DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                    {"user_name": current_user}
                )
            ) is not None:
                user_name = utility_obj.name_can(user.get("basic_details", {}))
        email_list = []
        if len(payload.get("email_list")) == 0:
            count = 1
        else:
            count = 0
            for _id, email in enumerate(payload.get("email_list", [])):
                if (
                    student := DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                        {"user_name": email}
                    )
                ) is None:
                    student = {}
                data = {
                    "student_id": (
                        ObjectId(student.get("_id")) if student.get("_id") else None
                    ),
                    "student_name": utility_obj.name_can(
                        student.get("basic_details", {})
                    ),
                    "student_email": email,
                }

                if offer_letter_applicants:
                    data.update({"application_id": ObjectId(offer_letter_applicants[_id])})

                if offered_applicants_info:
                    applicant_info = offered_applicants_info[_id]
                    data.update({"application_id": ObjectId(applicant_info.get("application_id"))})

                email_list.append(data)
                count += 1
        if user:
            add_data = {
                    "user_name": user_name,
                    "user_id": user.get("_id"),
                    "ip_address": ip_address,
                    "created_at": datetime.datetime.utcnow(),
                    "email_type": email_type,
                    "provider": provider,
                    "email_list": email_list,
                    "email_content": {
                        "content": payload.get("content", ""),
                        "template_id": payload.get("template_id", ""),
                        "template_type": payload.get("template_type", ""),
                    },
                    "total_email": count,
                    "transaction_details": transaction_details,
                }

            if offer_letter_information:
                add_data.update({"is_offer_letter_sent": True,
                                 "offer_letter_list_id": ObjectId(offer_letter_information.get("offer_letter_list_id"))})

            if scholarship_information:
                add_data.update({"is_scholarship_letter_sent": True,
                                 "scholarship_id": ObjectId(scholarship_information.get("scholarship_id"))})

            selected_college_id = MotorBaseSingleton.get_instance().master_data.get("college_id")
            DatabaseConfigurationSync("master").college_collection.update_one(
                {"_id": ObjectId(selected_college_id)}, {"$inc": {"usages.email_sent": 1}}
            )
            DatabaseConfigurationSync().activity_email.insert_one(add_data)
