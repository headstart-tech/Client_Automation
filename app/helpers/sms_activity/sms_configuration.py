"""
This file contain class and functions related to SMS activity process
"""
from datetime import datetime, timezone
import json

import requests
from bson import ObjectId

from app.background_task.send_mail_configuration import EmailActivity
from app.core.custom_error import DataNotFoundError
from app.core.log_config import get_logger
from app.core.utils import settings, utility_obj
from app.database.configuration import DatabaseConfiguration
from app.database.database_sync import DatabaseConfigurationSync

logger = get_logger(name=__name__)


class SMSHelper:
    """
    Perform sms related activity
    """

    async def update_delivery_status(self, data):
        """
        Update sms delivery status
        """
        try:
            result = (DatabaseConfiguration()
            .communication_log_collection.aggregate(
                [
                    {'$match': {
                        "sms_summary.transaction_id.transactionId": int(
                            data.get('transactionId'))}},
                    {'$group': {
                        '_id': "$_id"
                    }}
                ]
            ))
            async for item in result:
                communication_data = await (DatabaseConfiguration()
                .communication_log_collection.find_one(
                    {'_id': item.get('_id')}))
                if communication_data:
                    for _id, element in enumerate(
                            communication_data.get("sms_summary", {}).get(
                                "transaction_id", [])):
                        if element.get('transactionId') == int(
                                data.get('transactionId')):
                            if len(data) > 0:
                                element.update(data)
                            else:
                                break
                            if data.get("sms_delivered"):
                                communication_data["sms_summary"][
                                    "sms_delivered"] = \
                                    communication_data["sms_summary"][
                                        "sms_delivered"] + 1
                                await utility_obj.update_transaction_details_by_message_id(
                                    message_id=data.get('transactionId'),
                                    communication_data=communication_data,
                                    name="transactionId", com_type="sms")

                            communication_data["sms_summary"][
                                "transaction_id"][_id] = element

                            await (DatabaseConfiguration()
                            .communication_log_collection.update_one(
                                {"_id": item.get('_id')},
                                {'$set': communication_data}))
            activity_result = DatabaseConfiguration().sms_activity.aggregate(
                [
                    {"$unwind": {"path": "$sms_response.submitResponses"}},
                    {'$match': {
                        "sms_response.submitResponses.transactionId": int(
                            data.get('transactionId'))}},
                    {'$group': {
                        '_id': "$_id"
                    }}
                ]
            )
            async for item in activity_result:
                sms_activity_data = await (DatabaseConfiguration()
                .sms_activity.find_one(
                    {'_id': item.get('_id')}))
                if sms_activity_data:
                    for _id, element in enumerate(
                            sms_activity_data.get("sms_response", {}).get(
                                "submitResponses", [])):
                        if element.get('transactionId') == int(
                                data.get('transactionId')):
                            if len(data) > 0:
                                element.update(data)
                                await (DatabaseConfiguration()
                                .sms_activity.update_one(
                                    {"_id": item.get('_id')}, {
                                        '$set': {
                                            f'sms_response.submitResponses.{_id}': element}}))
                            else:
                                break
        except Exception as e:
            logger.error("Something went wrong. ", e)

    async def automation_update_sms_status(self, data):
        """
        Update the automation status update for the specified
        """
        try:
            result = (DatabaseConfiguration()
            .automation_communicationLog_details.aggregate(
                [
                    {"$unwind": {"path": "$sms_summary.transaction_id"}},
                    {'$match': {
                        "sms_summary.transaction_id.transactionId": int(
                            data.get('transactionId'))}},
                    {'$group': {
                        '_id': "$_id"
                    }}
                ]
            ))
            async for item in result:
                communication_data = await (DatabaseConfiguration()
                .automation_communicationLog_details.find_one(
                    {'_id': item.get('_id')}))
                if communication_data:
                    for _id, element in enumerate(communication_data.get(
                            "sms_summary", {}).get("transaction_id", [])):
                        if element.get('transactionId') == int(data.get(
                                'transactionId')):
                            if len(data) > 0:
                                element.update(data)
                            else:
                                break
                            if data.get("sms_delivered"):
                                communication_data["sms_summary"][
                                    "sms_delivered"] = communication_data.get(
                                    "sms_summary", {}).get("sms_delivered",
                                                           0) + 1
                            communication_data["sms_summary"][
                                "transaction_id"][_id] = element
                            await (DatabaseConfiguration()
                            .automation_communicationLog_details.update_one(
                                {"_id": item.get('_id')},
                                {'$set': communication_data}))
        except Exception as e:
            logger.error("Something went wrong. ", e)

    def text_message_activity(self, send_to, sms_content, dlt_content_id):
        """
        Send the SMS to particular student and return the response accordingly
        """
        url = f"https://api.oot.bz/api/v1/message"
        payload = json.dumps(
            {
                "extra": {"dltContentId": dlt_content_id},
                "message": {
                    "recipient": settings.sms_send_to_prefix + send_to,
                    "text": sms_content,
                },
                "sender": settings.sms_sender,
                "unicode": "True",
            }
        )
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Basic {settings.sms_authorization}",
        }

        response = requests.request("POST", url, headers=headers,
                                    data=payload)
        return response

    async def get_data_from_interview_list(self, interview_lists: list,
                                           get_email_ids=False):
        """
        Get the mobile numbers or email_ids of interview lists students.

        Params:
            interview_lists (list): A list which contains unique
             identifiers/ids of interview lists.

        Returns:
            data (list): A list which can contains mobile numbers or
             email ids of interview lists students.
        """
        data = []
        for list_id in interview_lists:
            if (
                    interview_list := await DatabaseConfiguration()
                            .interview_list_collection.find_one(
                        {"_id": ObjectId(list_id)})) is None:
                raise DataNotFoundError(_id=list_id, message="Interview List")
            applications = interview_list.get("eligible_applications", [])
            if applications:
                for application_id in applications:
                    if (
                            app_doc := await DatabaseConfiguration()
                                    .studentApplicationForms.find_one(
                                {"_id": application_id})) is None:
                        raise DataNotFoundError(_id=application_id,
                                                message="Application")
                    student_id = app_doc.get("student_id")
                    if (
                            stu_doc := await DatabaseConfiguration()
                                    .studentsPrimaryDetails.find_one(
                                {"_id": student_id})) is None:
                        raise DataNotFoundError(_id=student_id,
                                                message="Student")
                    if get_email_ids:
                        data.append(stu_doc.get("user_name"))
                    else:
                        if (basic_details := stu_doc.get("basic_details",
                                                         {})) is None:
                            basic_details = {}
                        data.append(basic_details.get("mobile_number"))
                    current_datetime = datetime.now(timezone.utc)
                    update_data = {"last_user_activity_date": current_datetime}
                    if stu_doc and not stu_doc.get("first_lead_activity_date"):
                        update_data["first_lead_activity_date"] = current_datetime
                    await DatabaseConfiguration().studentsPrimaryDetails.update_one({
                        "_id": ObjectId(student_id)},
                        {"$set": update_data})
        return data

    async def get_mobile_numbers(self, interview_lists: list | None):
        """
        Get the mobile numbers of interview lists students.

        Params:
            interview_lists (list): A list which contains interview list ids.

        Returns:
            list: A list which contains mobile numbers based on interview
            lists.
        """
        return await self.get_data_from_interview_list(interview_lists)

    async def get_email_ids(self, interview_lists: list):
        """
        Get the email ids of interview lists students.

        Params:
            interview_lists (list): A list which contains unique
            idenfiers/ids of interview list.
                e.g., ["123456789012345678901211", "123456789012345678901222"]

        Returns:
            list: A list which contains interview list students email ids.
        """
        return await self.get_data_from_interview_list(interview_lists,
                                                       get_email_ids=True)

    def send_sms_to_many(self, send_to, dlt_content_id, sms_content, sms_type,
                         sender_name, mobile_prefix=None, college_id=None):
        url = "https://api.oot.bz/api/v1/one2Many"
        if sms_type.lower() == "service implicit":
            user_name = settings.sms_username_trans
        elif sms_type.lower() == "service explicit":
            user_name = settings.sms_username_trans
        else:
            user_name = settings.sms_username_pro
        if mobile_prefix is None:
            mobile_prefix = settings.sms_send_to_prefix
        number_list, response, contents = [], {}, []
        for number in send_to:
            number = str(number)
            number_list.append({"mobile": mobile_prefix + number})

            email_activity_obj = EmailActivity()
            student = (DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                {"basic_details.mobile_number": number}))
            content = sms_content
            if student:
                content = email_activity_obj.detect_and_validate_variables(
                    sms_content, ObjectId(college_id), student.get("user_name")
                )
            contents.append(content)
        for number_info, content in zip(number_list, contents):
            payload = json.dumps(
                {
                    "options": {
                        "dltContentId": dlt_content_id},
                    "credentials": {
                        "password": settings.sms_password,
                        "user": user_name,
                    },
                    "recpients": [number_info],
                    "messageText": content,
                    "from": sender_name,
                    "unicode": "True",
                }
            )
            headers = {"Content-Type": "application/json",
                       "Accept": "application/json"}
            response = requests.request("POST", url,
                                        headers=headers, data=payload)
        return response


smshelper_obj = SMSHelper()
