"""
This file contains function related to SMS activity
"""
from bson import ObjectId
from fastapi import Depends, APIRouter, Request, Body, UploadFile, File
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError

from app.background_task.send_mail_configuration import EmailActivity
from app.celery_tasks.celery_communication_log import CommunicationLogActivity
from app.core.custom_error import ObjectIdInValid
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id
from app.dependencies.oauth import CurrentUser, is_testing_env, Is_testing
from app.helpers.sms_activity.sms_configuration import SMSHelper
from app.helpers.user_curd.user_configuration import UserHelper
from app.helpers.whatsapp_sms_activity.whatsapp_activity import WhatsappHelper
from app.models.interview_module_schema import whatsapp_webhook_schema
from app.models.student_user_schema import User
from app.models.template_schema import WhatsappTemplate, media_helper
from app.core.reset_credentials import Reset_the_settings

logger = get_logger(__name__)
whatsapp_router = APIRouter()


@whatsapp_router.post("/send_whatsapp_to_user/")
@requires_feature_permission("write")
async def send_whatsapp_sms(
        *,
        testing: Is_testing,
        request: Request,
        text: str = None,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
        payload: WhatsappTemplate = Body(),
        is_interview_list: bool = False,
        data_segment_id: str = None,
):
    """
    Send SMS to a particular student
    params:
      send_to (list): list of numbers or interview list ids to send sms
      text (str) : text to send
      is_interview_list(bool): True is sent are interviewList ids are snt,
       False if numbers are sent.
    return:
      dict : {"message": "WHATSAPP SMS sent successfully",
       "result": response.json()}
    """
    payload = jsonable_encoder(payload)
    await UserHelper().is_valid_user(current_user)
    try:
        college_id = college.get("id")
        if not testing:
            Reset_the_settings().check_college_mapped(college_id)
        ip_address = utility_obj.get_ip_address(request)
        template = WhatsappHelper().whatsapp_template_helper(
            template_id=payload.get("template_id"),
            template_content=payload.get("template_content"),
        )
        send_to = None
        data_segments_ids, data_segments = payload.get("data_segments_ids"), {}
        if template is not None:
            text = template.get("template_content")
        if is_interview_list:
            send_to = await SMSHelper().get_mobile_numbers(send_to)
        elif data_segments_ids:
            (
                send_to,
                data_segments,
            ) = await EmailActivity().update_list_by_data_segments_ids(
                data_segments_ids,
                send_to,
                data_segments,
                college_id,
                numbers=True,
                emails=False,
                get_emails=True
            )
            for _id in data_segments:
                await DatabaseConfiguration(
                ).data_segment_collection.update_one(
                    {"_id": ObjectId(_id)},
                    {"$inc": {"communication_count.whatsapp": len(
                        data_segments.get(_id, []))}})
        else:
            send_to = payload.get("send_to")
        if send_to:
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
                        {"$inc": {
                            "communication_count.whatsapp": len(send_to)}})
            response = WhatsappHelper().send_whatsapp_to_users(
                send_to=send_to,
                text=text if text is not None else "",
                template=template,
                media=payload.get("media"),
                button=payload.get("whatsapp_button"),
                _id=payload.get("whatsapp_obj_id"),
                button_list=payload.get("list_button"),
                location=payload.get("location"),
                ip_address=ip_address,
                data_segments=data_segments,
                college_id=college_id
            )
            if response.status_code != 200:
                raise HTTPException(status_code=403, detail="Whatsapp msg not sent")
            return {"message": "WHATSAPP SMS sent successfully",
                    "result": response.json()}
        return {"detail": "There is no any recipient fount for send whatsapp."}
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except KombuError as celery_error:
        logger.error(f"error send bulk mail to student {celery_error}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when send whatsapp "
                   f"message to students. "
                   f"Error - {celery_error}",
        )
    except Exception as error:
        logger.error(
            f"An error occurred when send whatsapp message to "
            f"students. Error - {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when send whatsapp "
                   f"message to students. Error - {error}",
        )


@whatsapp_router.post("/whatsapp_send_file")
@requires_feature_permission("write")
async def whatsapp_file_send(
        current_user: CurrentUser,
        request: Request,
        text: str = None,
        send_to: list[str] = None,
        file: UploadFile = File(),
        payload: media_helper = Depends(),
):
    """
    Whatsapp file send request with text and current user

    params:
        -text (str): Text the message sent this is not mandatory.
        -current_user (str): Current user getting from the token automatically.
        -request (generate): Get the socket connection details.
        -file (str): Upload the image and video.
    return:
        -response: success/failure response to the user.
    """
    payload = jsonable_encoder(payload)
    file = await utility_obj.temporary_path(file)
    await UserHelper().is_valid_user(current_user)
    ip_address = utility_obj.get_ip_address(request)
    if not send_to:
        raise HTTPException(status_code=422, detail="Please enter the number")
    response = WhatsappHelper().send_whatsapp_to_users(
        send_to=send_to,
        text=text if text is not None else "",
        media=payload,
        file=file,
        ip_address=ip_address,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=403, detail="Whatsapp msg not sent")
    return {"message": "WHATSAPP SMS sent successfully", "result": response.json()}


@whatsapp_router.post("/webhook/")
async def whatsapp_activity(payload: whatsapp_webhook_schema = Depends()):
    """
    use for capture the webhook from whatsapp
    """
    data = payload.model_dump()
    guid = data.get("CLIENT_GUID")
    status = str(data.get("MSG_STATUS")).lower()
    await DatabaseConfiguration().whatsapp_sms_activity.update_one(
        {"guid": guid}, {"$set": {"status": status}}
    )
    mobile_number = str(data.get("TO", ""))[2:]
    event_type = ""
    if str(data.get("MESSAGE_STATUS")) == "0":
        event_type = "whatsapp"
    else:
        if str(data.get("STATUS_ERROR")) == "8448":
            if str(data.get("REASON_STATUS")) == "173":
                event_type = "delivered"
            elif str(data.get("REASON_STATUS")) == "000":
                event_type = "read"
    logger.info(
        f"whatsapp webhook received event type: %s, guid: %s, " f"status: %s",
        event_type,
        guid,
        status,
    )
    if (
            student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                {"basic_details.mobile_number": mobile_number}
            )
    ) is not None:
        try:
            # TODO: Not able to add student timeline data
            #  using celery task when environment is
            #  demo. We'll remove the condition when
            #  celery work fine.
            if settings.environment in ["demo"]:
                CommunicationLogActivity().add_whatsapp_communication_log(
                    student_id=str(student.get("_id")),
                    data_type="whatsapp",
                    event_type=event_type,
                    event_status="sent",
                    massage_id=data.get("MESSAGE_ID"),
                    webhook=True,
                )
            else:
                if not is_testing_env():
                    CommunicationLogActivity().add_whatsapp_communication_log.delay(
                        student_id=str(student.get("_id")),
                        data_type="whatsapp",
                        event_type=event_type,
                        event_status="sent",
                        massage_id=data.get("MESSAGE_ID"),
                        webhook=True,
                    )
        except KombuError as celery_error:
            logger.error(f"error whatsapp_communication_log {celery_error}")
        except Exception as error:
            logger.error(f"error whatsapp_communication_log {error}")
    else:
        logger.info("Whatsapp webhook student not found")
