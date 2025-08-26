"""
This file contains function related to SMS activity
"""

from datetime import datetime

from bson import ObjectId
from fastapi import Depends, APIRouter, Request, BackgroundTasks
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError

from app.background_task.send_mail_configuration import EmailActivity
from app.celery_tasks.celery_send_mail import send_mail_config
from app.core.custom_error import ObjectIdInValid
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.database.motor_base_singleton import MotorBaseSingleton
from app.dependencies.college import get_college_id
from app.dependencies.oauth import CurrentUser
from app.dependencies.oauth import is_testing_env
from app.helpers.sms_activity.sms_configuration import SMSHelper
from app.helpers.user_curd.user_configuration import UserHelper

sms_router = APIRouter()
logger = get_logger(name=__name__)


@sms_router.post("/send_to_user/")
@requires_feature_permission("write")
async def send_sms_activity(
    request: Request,
    background_tasks: BackgroundTasks,
    send_to: list[str],
    sms_content: str,
    dlt_content_id: str,
    sms_type: str,
    sender_name: str,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id),
    is_interview_list: bool = False,
    data_segments_ids: list[str] | None = None,
        data_segment_id: str = None
):
    """
    Send SMS to a given students
    params:
      send_to (list) : list of numbers or interview list ids to send sms
      sms_content (str) : sms content to send,
      dlt_content_id (str):
      sms_type (str) : type of sms (promotional/transactional)
      sender_name (str): name of sender,
      is_interview_list(bool): True is sent are interviewList ids are snt, False if numbers are sent.
    return:
      dict : {"message": "SMS sent successfully", "result": response.json()}
    """
    user = await UserHelper().is_valid_user(current_user)
    if not user:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    try:
        ip_address = utility_obj.get_ip_address(request)
        numbers, data_segments, college_id = None, {}, college.get("id")
        if is_interview_list:
            numbers = await SMSHelper().get_mobile_numbers(send_to)
        elif data_segments_ids:
            students_data, data_segments = (
                await EmailActivity().update_list_by_data_segments_ids(
                    data_segments_ids,
                    numbers,
                    data_segments,
                    college_id,
                    numbers=True,
                    emails=False,
                    get_emails=True
                )
            )
            for _id in data_segments:
                await DatabaseConfiguration(
                ).data_segment_collection.update_one(
                    {"_id": ObjectId(_id)},
                    {"$inc": {"communication_count.sms": len(
                        data_segments.get(_id, []))}})
            numbers = students_data
        else:
            numbers = send_to
        if numbers:
            if data_segment_id is not None:
                if not ObjectId.is_valid(data_segment_id):
                    raise ValueError("Invalid data segment ObjectId")
                if (
                await DatabaseConfiguration().data_segment_collection.find_one(
                        {
                            "_id": ObjectId(data_segment_id)}
                )) is not None:
                    await DatabaseConfiguration(
                    ).data_segment_collection.update_one(
                        {"_id": ObjectId(data_segment_id)},
                        {"$inc": {"communication_count.sms": len(numbers)}})
            response = SMSHelper().send_sms_to_many(
                numbers, dlt_content_id, sms_content, sms_type, sender_name, college_id=college_id
            )
            if not is_testing_env():
                logger.debug("Start to add_communication_log.")
                # TODO: Not able to add student timeline data
                #  using celery task when environment is
                #  demo. We'll remove the condition when
                #  celery work fine.
                if settings.environment in ["demo"]:
                    send_mail_config().update_student_timeline_after_send_sms(
                        numbers, response.json(), college, user,
                        dlt_content_id, current_user, sms_content, data_segments)
                else:
                    send_mail_config().update_student_timeline_after_send_sms.delay(
                        numbers, response.json(), college, user,
                    dlt_content_id, current_user, sms_content, data_segments)
                logger.debug("End of add_communication_log.")

                # For Billing Dashboard
                selected_college_id = MotorBaseSingleton.get_instance().master_data.get("college_id")
                await DatabaseConfiguration().college_collection.update_one(
                    {"_id": ObjectId(selected_college_id)}, {"$inc": {"usages.sms_sent": 1}}
                )

            await DatabaseConfiguration().sms_activity.insert_one(
                {
                    "user_name": user.get("user_name"),
                    "user_id": ObjectId(user.get("_id")),
                    "send_to": numbers,
                    "ip_address": ip_address,
                    "created_at": datetime.utcnow(),
                    "sms-content": sms_content,
                    "dlt_content_id": dlt_content_id,
                    "sms_response": response.json(),
                }
            )
            return {"message": "SMS sent successfully",
                    "result": response.json()}
        return {"detail": "There is no any recipient fount for send sms."}
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except KombuError as celery_error:
        logger.error(f"error storing communication log {celery_error}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when send sms to students. "
            f"Error - {celery_error}",
        )
    except Exception as error:
        logger.error(f"error storing communication log {error}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when send sms to students. " f"Error - {error}. "
                   f"Error line#: {error.__traceback__.tb_lineno}",
        )


@sms_router.get("/webhook/")
async def sms_webhook(
    request: Request,
    txid: str = None,
    to: str = None,
    description: str = None,
    pdu: str = None,
    text: str = None,
    deliverystatus: str = None,
    deliverydt: str = None,
    submitdt: str = None,
    corelationid: str = None,
):
    """
    Webhook for capture sms delivery status
    """
    try:
        logger.info(
            f"Request: {request}, Transaction Id: {txid}, Mobile Number: {to},"
            f" System Message Delivery Description: {description},"
            f" Part of Message: {pdu}, Message Text: {text},"
            f" Message Delivery Status: {deliverystatus},"
            f" Delivery Date & Time: {deliverydt},"
            f" Submission Date & Time: {submitdt},"
            f" User Defined Additional Message Request "
            f"Identifier: {corelationid}"
        )
        data = {
            "transactionId": txid,
            "description": description,
            "content": text,
            "sms_delivered": (
                True if str(deliverystatus).upper() == "DELIVERY_SUCCESS" else False
            ),
            "delivery_date": deliverydt,
            "send_date": submitdt,
        }
        data = {key: value for key, value in data.items() if value is not None}
        if txid:
            await SMSHelper().update_delivery_status(data)
            await SMSHelper().automation_update_sms_status(data)
    except Exception as e:
        logger.error("Something went wrong. ", e)
