"""
This file contain class and functions related to communication log
"""

from datetime import datetime

from bson import ObjectId

from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.celery_app import celery_app
from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj
from app.database.database_sync import DatabaseConfigurationSync

logger = get_logger(name=__name__)


class CommunicationLogActivity:
    """
    Contain functions related to communication log activity
    """

    @staticmethod
    @celery_app.task(ignore_result=True)
    def add_communication_log(
        response: dict,
        student_id: str | None = None,
        data_type: str | None = None,
        event_type: str | None = None,
        event_status: str | None = None,
        event_name: str | None = None,
        email_type: str | None = None,
        provider: str | None = None,
        action_type: str | None = "system",
        template_id: str | None = None,
        current_user: str | None = None,
        college_id: str | None = None,
        add_timeline: bool = True,
        user_id: str | None = None,
        data_segments: dict | None = None,
        offer_letter_information: dict | None = None,
        scholarship_information: dict | None = None
    ):
        """
        Store communication log of student in DB.

        Params:
            - response(dict): The response we got after sending mail.
            - student_id(str | None): Default value: None. Either None or Unique identifier of student.
            - data_type(str | None): Default value: None. Either None or Type of data.
            - event_type(str | None): Default value: None. Either None or The type of event.
                It can have values like "email", "payment" e.t.c
            - event_status(str | None): Default value: None. Either None or The status of the communication event.
            - event_name(str, optional): Default value: None. Either None or The name of the communication event.
            - email_type(str, optional): Default value: None. Either None or The type of email sent.
            - provider(str, optional): Default value: None. Either None or
                The email service provider used to send the communication.
            - action_type(str, optional): Default value: "system". Either None or
                the type of action that triggered the communication.
            - template_id(str, optional):The ID of the template used for the communication, Default is None.
            - current_user(str, optional):The user or system that initiated the communication.Default is None.
            - college_id(str, optional):The ID of the college associated with the communication,Default is None.
            - add_timeline(bool, optional): Whether to add communication event to the student's timeline.
                Default is True.
            - user_id(str | None): Default value: None. Either None or Unique identifier of user.
            - data_segments(dict, optional): Default value: None. Either None or
                Additional data segments or context related to the communication.
            - offer_letter_information (dict | None): Default value: None.
                A dictionary which contains offer letter information.
            - scholarship_information (dict | None): Default value: None. Either None or scholarship information.

        Returns: None
        """
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)
        student = {}
        if student_id:
            student = DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                {"_id": ObjectId(student_id)}
            )
        template_details = {}
        if template_id:
            template_details = DatabaseConfigurationSync().template_collection.find_one(
                {"_id": ObjectId(template_id)}
            )
        user_name = ""
        user_details = None
        if current_user:
            if (
                user_details := DatabaseConfigurationSync(
                    database="master"
                ).user_collection.find_one({"user_name": current_user})
            ) is not None:
                user_name = utility_obj.name_can(user_details)
        communication_log = (
            DatabaseConfigurationSync().communication_log_collection.find_one(
                {"student_id": ObjectId(student_id)}
            )
        )
        data = {f"{data_type}_summary": {}}
        current_datetime = datetime.utcnow()
        if response is None:
            response = {}
        data_segment_id = None
        if data_segments:
            data_segment_ids = data_segments.keys()
            data_segments_details = utility_obj.get_data_segment_details(data_segment_ids=data_segment_ids)
            for _id, students in data_segments.items():
                if student.get("basic_details", {}).get("mobile_number") in students:
                    data_segment_id = _id
                    break
            if data_segment_id:
                segment_details = data_segments_details.get(data_segment_id)
                response.update(
                    {
                        "data_segment": {
                            "name": segment_details.get("data_segment_name"),
                            "_id": ObjectId(segment_details.get("data_segment_id")),
                            "data_type": segment_details.get("data_type"),
                            "segment_type": segment_details.get("segment_type"),
                        }
                    }
                )
        template_name = template_details.get("template_name", "")
        response.update(
            {
                "created_at": current_datetime,
                "template_id": ObjectId(template_id) if ObjectId.is_valid(template_id) else template_id,
                "template_name": template_name,
                "provider": "" if provider is None else provider,
                "template_type": data_type,
                "user_name": user_name,
                "release_type": "Manual",
                "user": {
                      "user_name": user_details.get("user_name"),
                      "name": user_name,
                      "id": user_details.get("_id"),
                      "role": user_details.get("role", {}).get("role_name")
                    } if user_details else None
            }
        )
        if offer_letter_information:
            response.update({"is_offer_letter_sent": True,
                             "offer_letter_list_id": ObjectId(offer_letter_information.get("offer_letter_list_id"))})

        if scholarship_information:
            response.update({"is_scholarship_letter_sent": True,
                             "scholarship_id": scholarship_information.get("scholarship_id")})

        data[f"{data_type}_summary"][f"{data_type}_sent"] = 1
        data[f"{data_type}_summary"][f"{data_type}_delivered"] = 0
        data[f"{data_type}_summary"]["transaction_id"] = [response]
        timeline = {
            "action_type": action_type,
            "event_type": event_type,
            "event_status": event_status,
            "event_name": event_name,
            "template_id": template_id,
            "timestamp": current_datetime,
        }
        for key, value in {"email_type": email_type, "provider": provider}.items():
            if value is not None:
                timeline.update({f"{key}": value})
        if communication_log:
            if communication_log.get(f"{data_type}_summary"):
                communication_log.get(f"{data_type}_summary", {}).get(
                    "transaction_id"
                ).insert(0, response)
                data[f"{data_type}_summary"]["transaction_id"] = communication_log.get(
                    f"{data_type}_summary", {}
                ).get("transaction_id")
                data[f"{data_type}_summary"][f"{data_type}_sent"] = (
                    communication_log.get(f"{data_type}_summary", {}).get(
                        f"{data_type}_sent"
                    )
                    + 1
                )
                data[f"{data_type}_summary"][f"{data_type}_delivered"] = (
                    communication_log.get(f"{data_type}_summary", {}).get(
                        f"{data_type}_delivered"
                    )
                )
                if data_type == "email":
                    data[f"{data_type}_summary"]["open_rate"] = communication_log.get(
                        f"{data_type}_summary", {}
                    ).get("open_rate")
                    data[f"{data_type}_summary"]["click_rate"] = communication_log.get(
                        f"{data_type}_summary", {}
                    ).get("click_rate")
            else:
                data = data
            communication_log.get("timeline").insert(0, timeline)
            data["timeline"] = communication_log.get("timeline")
            DatabaseConfigurationSync().communication_log_collection.update_one(
                {"student_id": ObjectId(student_id)}, {"$set": data}
            )
        else:
            if data_type == "email":
                data[f"{data_type}_summary"]["open_rate"] = 0
                data[f"{data_type}_summary"]["click_rate"] = 0
            data.update({"student_id": ObjectId(student_id), "timeline": [timeline]})
            DatabaseConfigurationSync().communication_log_collection.insert_one(data)
        toml_data = utility_obj.read_current_toml_file()
        if toml_data.get("testing", {}).get("test") is False:
            if student:
                template = {}
                if not template_details:
                    template = {"template_name": data_type}
                user_detail = user_details
                if not user_detail:
                    user_detail = {"first_name": "System"}
                message = (f"{data_type.upper()} about: "
                           f"{template_name} {event_name}"
                           f" has been sent by "
                           f"{utility_obj.name_can(user_detail)}")
                if add_timeline:
                    StudentActivity().student_timeline(
                        student_id=str(student.get("_id")),
                        event_type=event_type,
                        event_status=event_status,
                        template_id=template_id,
                        template_type=data_type.lower(),
                        user_id=user_id if user_details is None else str(
                            user_details.get("_id")),
                        template_name=template.get('template_name'),
                        message=message,
                        college_id=college_id,
                    )

    @staticmethod
    @celery_app.task(ignore_result=True)
    def add_whatsapp_communication_log(
        response=None,
        student_id=None,
        data_type=None,
        event_type=None,
        event_status=None,
        event_name=None,
        massage_id=None,
        webhook=None,
        action_type="system",
    ):
        """
        Store communication log of student's whatsapp messages
        """
        data = {f"{data_type}_summary": {}}
        if (
            communication := DatabaseConfigurationSync().communication_log_collection.find_one(
                {"student_id": ObjectId(student_id)}
            )
        ) is not None:
            data = communication
            if f"{data_type}_summary" not in data:
                data[f"{data_type}_summary"] = {}
        if event_type == "sent":
            data[f"{data_type}_summary"][f"{data_type}_sent"] = (
                data.get(f"{data_type}_summary", {}).get(f"{data_type}_sent", 0) + 1
            )
        elif event_type == "delivered":
            data[f"{data_type}_summary"][f"{data_type}_delivered"] = (
                data.get(f"{data_type}_summary", {}).get(f"{data_type}_delivered", 0)
                + 1
            )
        elif event_type == "read":
            data[f"{data_type}_summary"][f"{data_type}_read"] = (
                data.get(f"{data_type}_summary", {}).get(f"{data_type}_read", 0) + 1
            )
        elif event_type == "whatsapp":
            data[f"{data_type}_summary"][f"{data_type}_received"] = True

        current_datetime = datetime.utcnow()
        timeline = {
            "action_type": action_type,
            "event_type": data_type,
            "event_status": event_status,
            "event_name": event_name,
            "timestamp": current_datetime,
        }
        communication_log = (
            DatabaseConfigurationSync().communication_log_collection.find_one(
                {"student_id": ObjectId(student_id)}
            )
        )
        if communication_log:
            transaction_id = communication_log.get(f"{data_type}_summary", {}).get(
                "transaction_id"
            )
            if transaction_id and webhook:
                for event in transaction_id:
                    if event.get("MessageId") == massage_id:
                        event.update(
                            {
                                f"{data_type}_{event_type}": True,
                                f"{event_type}_time": current_datetime,
                            }
                        )
                    else:
                        transaction_id.insert(
                            0,
                            {
                                "MessageId": massage_id,
                                f"{data_type}_{event_type}": True,
                                f"{event_type}_time": current_datetime,
                            },
                        )
                data[f"{data_type}_summary"]["transaction_id"] = transaction_id
            elif not transaction_id and webhook:
                data[f"{data_type}_summary"]["transaction_id"] = [
                    {
                        "MessageId": massage_id,
                        f"{data_type}_{event_type}": True,
                        f"{event_type}_time": current_datetime,
                    }
                ]
            elif not webhook:
                communication_log.get("timeline").insert(0, timeline)
                data["timeline"] = communication_log.get("timeline")
                response.update({"created_at": current_datetime})
                if not transaction_id:
                    data[f"{data_type}_summary"]["transaction_id"] = [response]
                else:
                    transaction_id.insert(0, response)
            DatabaseConfigurationSync().communication_log_collection.update_one(
                {"student_id": ObjectId(student_id)}, {"$set": data}
            )
        else:
            data.update({"student_id": ObjectId(student_id), "timeline": [timeline]})
            DatabaseConfigurationSync().communication_log_collection.insert_one(data)
