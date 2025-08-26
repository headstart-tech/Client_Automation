"""
This file contain class and functions related to send sms
"""

from datetime import datetime

from bson import ObjectId
from kombu.exceptions import KombuError

from app.celery_tasks.celery_communication_log import CommunicationLogActivity
from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.background_task_logging import background_task_wrapper
from app.core.utils import logger, utility_obj, settings
from app.database.configuration import DatabaseConfiguration
from app.database.motor_base_singleton import MotorBaseSingleton
from app.dependencies.oauth import is_testing_env
from app.helpers.sms_activity.sms_configuration import SMSHelper


class SmsActivity:
    """
    Contain functions related to sms activity
    """

    @background_task_wrapper
    async def send_sms_to_users(
        self,
        send_to,
        dlt_content_id,
        sms_content,
        sms_type,
        sender,
        ip_address=None,
        student=None,
        action_type="system",
        user_id=None,
        mobile_prefix=None
    ):
        """
        Send sms to users
        """
        response = SMSHelper().send_sms_to_many(
            send_to=send_to,
            dlt_content_id=dlt_content_id,
            sms_content=sms_content,
            sms_type=sms_type,
            sender_name=sender,
            mobile_prefix=mobile_prefix
        )
        if (template := await DatabaseConfiguration().template_collection.find_one(
                {"dlt_content_id": dlt_content_id})) is None:
            template = {}
        for number, response_data in zip(send_to, response.json()["submitResponses"]):
            student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                {"basic_details.mobile_number": number}
            )
            if student:
                try:
                    toml_data = utility_obj.read_current_toml_file()
                    if toml_data.get("testing", {}).get("test") is False:
                        name = utility_obj.name_can(
                            student.get("basic_details", {}))
                        # TODO: Not able to add student timeline data
                        #  using celery task when environment is
                        #  demo. We'll remove the condition when
                        #  celery work fine.
                        if settings.environment in ["demo"]:
                            CommunicationLogActivity().add_communication_log(
                                student_id=str(student.get("_id")),
                                response=response_data,
                                data_type="sms",
                                event_type="sms",
                                event_status="sent",
                                event_name=f"mobile number {number}",
                                user_id=user_id,
                                action_type=action_type,
                                college_id=str(student.get("college_id")),
                                add_timeline=False
                            )
                            StudentActivity().student_timeline(
                                student_id=str(student.get("_id")),
                                event_type="sms",
                                event_name="sent sms",
                                template_type="sms",
                                user_id=user_id,
                                template_id=str(template.get("_id")),
                                message=f"{name} has tried to login through OTP.",
                                college_id=str(student.get("college_id")),
                            )
                        else:
                            if not is_testing_env():
                                CommunicationLogActivity().add_communication_log.delay(
                                    student_id=str(student.get("_id")),
                                    response=response_data,
                                    data_type="sms",
                                    event_type="sms",
                                    event_status="sent",
                                    event_name=f"mobile number {number}",
                                    user_id=user_id,
                                    action_type=action_type,
                                    college_id=str(student.get("college_id")),
                                    add_timeline=False
                                )
                                StudentActivity().student_timeline.delay(
                                    student_id=str(student.get("_id")),
                                    event_type="sms",
                                    event_name="sent sms",
                                    template_type="sms",
                                    user_id=user_id,
                                    template_id=str(template.get("_id")),
                                    message=f"{name} has tried to login through OTP.",
                                    college_id=str(student.get("college_id")),
                                )
                except KombuError as celery_error:
                    logger.error(f"error storing communication log {celery_error}")
                except Exception as error:
                    logger.error(f"error storing communication log {error}")
                logger.info("Finished the communication log process")
                selected_college_id = MotorBaseSingleton.get_instance().master_data.get("college_id")
                await DatabaseConfiguration().college_collection.update_one(
                    {"_id": ObjectId(selected_college_id)}, {"$inc": {"usages.sms_sent": 1}}
                )
                await DatabaseConfiguration().sms_activity.insert_one(
                    {
                        "user_name": student.get("user_name"),
                        "user_id": ObjectId(str(student.get("_id"))),
                        "send_to": [student.get("basic_details", {}).get("mobile_number")],
                        "ip_address": ip_address,
                        "created_at": datetime.utcnow(),
                        "sms-content": sms_content,
                        "dlt_content_id": dlt_content_id,
                        "sms_response": response.json(),
                    }
                )
