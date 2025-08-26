"""
This file contain class and functions related to raw_data
"""

import datetime
import operator

from bson.objectid import ObjectId

from app.celery_tasks.celery_communication_log import CommunicationLogActivity
from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.celery_app import celery_app
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, settings
from app.database.database_sync import DatabaseConfigurationSync
from app.database.motor_base_singleton import MotorBaseSingleton
from app.helpers.sms_activity.sms_configuration import SMSHelper
from app.helpers.whatsapp_sms_activity.whatsapp_activity import WhatsappHelper


class RawDataActivity:
    """
    Contain functions related to raw data activity
    """

    @staticmethod
    @celery_app.task(ignore_result=True)
    def upload_raw_data(file, user, data_name, college_id=None):
        """
        Store raw data
        """
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)
        data_dict = file.get("data_dict")
        duplicate_dict = file.get("duplicate_dict")
        duplicate_data_lead, failed_data_lead, lead_inserted, successful_lead_count = (
            [],
            [],
            [],
            0,
        )
        off_data = DatabaseConfigurationSync().offline_data.insert_one(
            {
                "imported_by": ObjectId(user.get("_id")),
                "import_status": "pending",
                "data_name": str(data_name).lower(),
                "uploaded_on": datetime.datetime.utcnow(),
                "uploaded_by": utility_obj.name_can(user),
                "lead_processed": sum(map(operator.itemgetter("size"), data_dict))
                + sum(map(operator.itemgetter("size"), duplicate_dict)),
                "duplicate_leads": 0,
                "failed_lead": 0,
            }
        )
        offline_id = off_data.inserted_id
        for each in data_dict:
            if each.get("size") > 1:
                for i in range(each.get("size") - 1):
                    duplicate_data_lead.append(each)
            temp_data = {}
            each.pop("size")
            temp_data.update(
                {
                    "mandatory_field": {
                        "email": each.get("email"),
                        "mobile_number": each.get("mobile_number"),
                    },
                    "offline_data_id": ObjectId(offline_id),
                    "created_at": datetime.datetime.utcnow(),
                }
            )
            if each.get("email", "") == "" and each.get("mobile_number", "") == "":
                failed_data_lead.append(each)
            elif (
                DatabaseConfigurationSync().raw_data.find_one(
                    {"mandatory_field.mobile_number": each.get("mobile_number")}
                )
                is not None
            ):
                duplicate_data_lead.append(each)
            elif (
                DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                    {"basic_details.mobile_number": each.get("mobile_number")}
                )
                is not None
            ):
                duplicate_data_lead.append(each)
            else:
                if (
                    each.get("email") is not None
                    and each.get("mobile_number") is not None
                ):
                    each.pop("email")
                    each.pop("mobile_number")
                temp_data.update({"other_field": each})
                lead_inserted.append(temp_data)
                successful_lead_count += 1
        if lead_inserted:
            DatabaseConfigurationSync().raw_data.insert_many(lead_inserted)
        duplicate_data_lead.extend(duplicate_dict)
        DatabaseConfigurationSync().offline_data.update_one(
            {"_id": ObjectId(offline_id)},
            {
                "$set": {
                    "duplicate_leads": len(duplicate_data_lead),
                    "duplicate_lead_data": duplicate_data_lead,
                    "failed_lead": len(failed_data_lead),
                    "failed_lead_data": failed_data_lead,
                    "successful_lead_count": successful_lead_count,
                    "import_status": "completed",
                }
            },
        )

    @staticmethod
    @celery_app.task(ignore_result=True)
    def perform_action_on_raw_data_leads(
        email_preferences,
        action,
        payload,
        data,
        user,
        ip_address,
        current_user,
        template_id=None,
        college_id=None,
    ):
        """
        Perform action on raw data leads
        """
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)
        action_type = (
            "counselor"
            if user.get("role", {}).get("role_name") == "college_counselor"
            else "system"
        )
        if action == "email":
            email_ids = list(
                set(
                    [
                        item.get("mandatory_field", {}).get("email")
                        for item in data
                        if item.get("mandatory_field", {}).get("email") is not None
                    ]
                )
            )
            # Do not move position of below statement at top otherwise
            # we'll get circular ImportError
            data = {
                "email_preferences": email_preferences,
                "email_type": "transactional",
                "email_ids": email_ids,
                "subject": payload.get("subject", "").title(),
                "template": payload.get("template"),
                "event_type": "email",
                "event_status": f"sent by {utility_obj.name_can(user)} whose id: ",
                "event_name": "Bulk",
                "current_user": current_user,
                "ip_address": ip_address,
                "payload": {"content": "Send templates", "email_list": email_ids},
                "attachments": None,
                "action_type": action_type,
                "college_id": college_id,
                "data_segments": None,
                "template_id": None,
                "add_timeline": True,
                "priority": True,
                "environment": settings.aws_env
            }
            utility_obj.sync_publish_email_sending_on_queue(data)
        else:
            send_to = list(
                set(
                    [
                        item.get("mandatory_field", {}).get("mobile_number")
                        for item in data
                        if item.get("mandatory_field", {}).get("mobile_number")
                        is not None
                    ]
                )
            )
            if action == "sms":
                response = SMSHelper().send_sms_to_many(
                    send_to,
                    payload.get("dlt_content_id"),
                    payload.get("sms_content"),
                    payload.get("sms_type"),
                    payload.get("sender_name"),
                )
                for number, response_data in zip(
                    send_to, response.json()["submitResponses"]
                ):
                    student = (
                        DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                            {"basic_details.mobile_number": number}
                        )
                    )
                    if student:
                        CommunicationLogActivity().add_communication_log(
                            student_id=str(student.get("_id")),
                            response=response_data,
                            data_type="sms",
                            event_type="sms",
                            event_status="sent",
                            event_name=f"mobile number {number}",
                            action_type=action_type,
                            current_user=current_user,
                            template_id=template_id,
                            college_id=college_id,
                            user_id=str(user.get("_id"))
                        )
                        name = utility_obj.name_can(student.get("basic_details", {}))
                        StudentActivity().student_timeline(
                            student_id=str(student.get("_id")),
                            event_type="SMS",
                            event_status="Send SMS",
                            message=f"{name}" f" has send a SMS",
                            template_id=template_id,
                            college_id=college_id,
                            user_id=str(user.get("_id"))
                        )
                # For Billing Dashboard
                selected_college_id = MotorBaseSingleton.get_instance().master_data.get("college_id")
                DatabaseConfigurationSync("master").college_collection.update_one(
                    {"_id": ObjectId(selected_college_id)}, {"$inc": {"usages.sms_sent": 1}}
                )

                DatabaseConfigurationSync().sms_activity.insert_one(
                    {
                        "user_name": user.get("user_name"),
                        "user_id": ObjectId(user.get("_id")),
                        "send_to": send_to,
                        "ip_address": ip_address,
                        "created_at": datetime.datetime.utcnow(),
                        "sms-content": payload.get("sms_content"),
                        "dlt_content_id": payload.get("dlt_content_id"),
                        "sms_response": response.json(),
                    }
                )
            else:
                response = WhatsappHelper().send_whatsapp_to_users(
                    send_to, payload.get("whatsapp_text")
                )
                message_list = []
                for number, response_data in zip(
                    send_to, response.json()["MESSAGEBACK"]
                ):
                    if (
                        student := DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                            {"basic_details.mobile_number": number}
                        )
                    ) is not None:
                        CommunicationLogActivity().add_whatsapp_communication_log(
                            student_id=str(student.get("_id")),
                            response=response_data,
                            data_type="whatsapp",
                            event_type="whatsapp",
                            event_status="sent",
                            event_name=f"mobile number {number}",
                            action_type=action_type,
                            template_id=template_id,
                        )
                        name = utility_obj.name_can(student.get("basic_details", {}))
                        StudentActivity().student_timeline(
                            student_id=str(student.get("_id")),
                            event_type="Whatsapp",
                            event_status="Send Whatsapp",
                            message=f"{name} has send a Whatsapp",
                            template_id=template_id,
                            college_id=college_id,
                        )

                    message_list.append(
                        {
                            "user_name": user.get("user_name"),
                            "user_id": ObjectId(user.get("_id")),
                            "send_to": student,
                            "ip_address": ip_address,
                            "created_at": datetime.datetime.utcnow(),
                            "submit_date": response_data.get("GUID").get("SUBMITDATE"),
                            "wa_sms_content": payload.get("whatsapp_text", ""),
                            "id": response_data.get("GUID").get("ID"),
                            "guid": response_data.get("GUID").get("GUID"),
                            "status": "sent",
                        }
                    )

                # For Billing Dashboard
                selected_college_id = MotorBaseSingleton.get_instance().master_data.get("college_id")
                DatabaseConfigurationSync("master").college_collection.update_one(
                    {"_id": ObjectId(selected_college_id)}, {"$inc": {"usages.whatsapp_sms_sent": len(message_list)}}
                )

                DatabaseConfigurationSync().whatsapp_sms_activity.insert_many(
                    message_list
                )

    @staticmethod
    @celery_app.task(ignore_result=True)
    def delete_student_by_offline(offline_ids: list, college_id=None):
        """
        Delete the student from the studentPrimary collection
         based on offline id
        params:
            offline_ids (list): list of offline IDs to delete from
             the student primary collection
        """
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)
        for _id in offline_ids:
            if (
                DatabaseConfigurationSync().lead_upload_history.find_one(
                    {"_id": ObjectId(_id)}
                )
                is None
            ):
                continue
            total_student = DatabaseConfigurationSync().studentsPrimaryDetails.aggregate(
                [{"$match": {"lead_data_id": ObjectId(_id)}}]
            )
            student_id = [
                ObjectId(student_detail.get("_id")) for student_detail in total_student
            ]
            DatabaseConfigurationSync().studentApplicationForms.delete_many(
                {"student_id": {"$in": student_id}}
            )
            DatabaseConfigurationSync().leadsFollowUp.delete_many(
                {"student_id": {"$in": student_id}}
            )
            DatabaseConfigurationSync().studentTimeline.delete_many(
                {"student_id": {"$in": student_id}}
            )
            DatabaseConfigurationSync().studentSecondaryDetails.delete_many(
                {"student_id": {"$in": student_id}}
            )
            DatabaseConfigurationSync().queries.delete_many(
                {"student_id": ObjectId(_id)}
            )
            DatabaseConfigurationSync().login_activity_collection.delete_many(
                {"user_id": ObjectId(_id)}
            )
            DatabaseConfigurationSync().payment_collection.delete_many(
                {"user_id": ObjectId(_id)}
            )
            DatabaseConfigurationSync().studentsPrimaryDetails.delete_many(
                {"lead_data_id": ObjectId(_id)}
            )
            DatabaseConfigurationSync().lead_upload_history.delete_one(
                {"_id": ObjectId(_id)}
            )
