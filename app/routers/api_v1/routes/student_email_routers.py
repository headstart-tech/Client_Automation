"""
This file contains API routes related to student email
"""

import ast
from datetime import datetime, timezone

from bson.objectid import ObjectId
from fastapi import APIRouter, BackgroundTasks, Query, Request, Depends, Body
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError
from pydantic import EmailStr

from app.celery_tasks.celery_login_activity import login_activity
from app.celery_tasks.celery_send_mail import send_mail_config
from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.custom_error import DataNotFoundError
from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, settings, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id
from app.dependencies.cryptography import EncryptionDecryption
from app.dependencies.hashing import Hash
from app.dependencies.oauth import AuthenticateUser, Is_testing, is_testing_env
from app.dependencies.oauth import CurrentUser
from app.helpers.student_curd.student_user_crud_configuration import (
    StudentUserCrudHelper,
)
from app.helpers.user_curd.user_configuration import UserHelper

email_router = APIRouter()
logger = get_logger(name=__name__)
toml_data = utility_obj.read_current_toml_file()


@email_router.post("/reset_password_template/", summary="Send Email for Reset Password")
async def reset_password_template(
    request: Request,
    background_tasks: BackgroundTasks,
    email: EmailStr = Query(..., description="Enter your registered email ID"),
    college: dict = Depends(get_college_id),
):
    if toml_data.get("testing", {}).get("test") is False:
        Reset_the_settings().check_college_mapped(college_id=str(college.get("id")))
        student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"user_name": email}
        )
        if not student:
            raise HTTPException(
                status_code=404,
                detail="You have not registered with us, please register.",
            )
        data = {"userid": str(student["_id"]), "descend": "al"}
        token = EncryptionDecryption().encrypt_message(str(data))
        token = token.decode("utf-8")
        reset_password_url = (
            f"https://{settings.base_path}/student/email/reset_password/{token}/"
        )
        # Do not move position of below statement at top otherwise we'll get
        # circular ImportError
        from app.background_task.send_mail_configuration import EmailActivity
        await EmailActivity().reset_password_user(
            email=email,
            reset_password_url=reset_password_url,
            event_type="email",
            event_status="sent",
            event_name="Reset password",
            payload={"content": "reset password", "email_list": [email]},
            current_user=email,
            request=request,
            email_preferences=college.get("email_preferences", {}),
            college_id=college.get("id")
        )
        name = utility_obj.name_can(student.get("basic_details", {}))
        try:
            # TODO: Not able to add student timeline data
            #  using celery task when environment is
            #  demo. We'll remove the condition when
            #  celery work fine.
            if settings.environment in ["demo"]:
                StudentActivity().student_timeline(
                    student_id=str(student.get("_id")),
                    event_type="Password",
                    event_status="Request reset Password",
                    message=f"{name}" f" has clicked on reset password.",
                    college_id=college.get("id"),
                )
            else:
                if not is_testing_env():
                    StudentActivity().student_timeline.delay(
                        student_id=str(student.get("_id")),
                        event_type="Password",
                        event_status="Request reset Password",
                        message=f"{name}" f" has clicked on reset password.",
                        college_id=college.get("id"),
                    )
        except KombuError as celery_error:
            logger.error(f"error storing resetting password data " f"{celery_error}")
        except Exception as error:
            logger.error(f"error storing resetting password data {error}")

    return {"message": "Mail sent successfully."}


@email_router.get("/dkper/redirect/{token}")
async def get_direct(request: Request, token: str, testing: Is_testing):
    """
    Get the login credentials like access_token and refresh_token based on token.

    Params:\n
        - token (str): token which useful for get login credentials like access_token and refresh_token.

    Returns:\n
        - dict: A dictionary which contains login credentials like access_token and refresh_token.

    Raises:\n
        - Exception: An error occurred with status code 400 when student not found.
    """
    try:
        dt = await EncryptionDecryption().decrypt_message(token)
        dt = ast.literal_eval(dt)
        college_id = dt.get("college_id")
        if not testing:
            Reset_the_settings().check_college_mapped(college_id)
        if (
            student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                {
                    "_id": ObjectId(dt.get("userid")),
                    "college_id": ObjectId(college_id),
                }
            )
        ) is None:
            raise HTTPException(status_code=404, detail="username not found")
        await StudentUserCrudHelper().update_verification_status(student)
        user = await AuthenticateUser().authenticate_student(
            student.get("user_name"),
            dt.get("password"),
            ["student"],
            college_id,
            refresh_token=True,
            request=request,
        )
    except Exception as error:
        raise HTTPException(
            status_code=400, detail=f"Something went wrong. Error - {error}"
        )
    if not testing:
        ip_address = utility_obj.get_ip_address(request)
        logger.warning("Got the origin IP address of student.")
        logger.warning(
            "Start storing login activity of student when "
            "tried direct login using url..."
        )
        try:
            # TODO: Not able to add student timeline data
            #  using celery task when environment is
            #  demo. We'll remove the condition when
            #  celery work fine.
            if settings.environment in ["demo"]:
                login_activity().store_login_activity(
                    user_name=student.get("user_name"), ip_address=ip_address
                )
            else:
                if not is_testing_env():
                    login_activity().store_login_activity.delay(
                        user_name=student.get("user_name"), ip_address=ip_address
                    )
        except Exception as error:
            logger.error(
                f"celery task storing login activity" f" failed to call server {error}"
            )
    return user


@email_router.get("/reset_password/{token}/", summary="Student Reset Password")
async def reset_password(
    token: str,
    new_password: str = Query(
        ..., description="Enter your new password", min_length=8, max_length=20
    ),
):
    """
    Student Reset Password\n
    * :*param* **password**:
        * new_password e.g., test
        * confirm_password e.g., test
    * :*return* **Message - Reset password successfully.**:
    """
    try:
        dt = await EncryptionDecryption().decrypt_message(token)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid token")
    dt = ast.literal_eval(dt)
    if dt.get("descend") != "al":
        raise HTTPException(status_code=410, detail="url has expired")
    data = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"_id": ObjectId(dt["userid"])}
    )
    if Hash().verify_password(data.get("password"), new_password):
        raise HTTPException(
            status_code=422,
            detail="Your new password should not match with last password.",
        )
    password = Hash().get_password_hash(new_password)
    updated_password = await DatabaseConfiguration().studentsPrimaryDetails.update_one(
        {"_id": ObjectId(data.get("_id"))}, {"$set": {"password": password}}
    )
    if updated_password:
        return utility_obj.response_model(
            data=True, message="Your password has been updated successfully."
        )
    else:
        raise HTTPException(status_code=500, detail="Something went wrong.")


@email_router.post("/verification/", summary="Send verification email to student")
async def send_verification_email(
    request: Request,
    student_email: list[EmailStr] = Body(..., description="Enter student email id"),
    college: dict = Depends(get_college_id),
    user_id: str = None
):
    """
    Send verification email to student
    """
    if len(student_email) < 1:
        raise HTTPException(
            status_code=422,
            detail="Please enter student email id",
        )
    user = None
    if user_id:
        user = (await UserHelper().get_user_data_by_id(
            None, user_id, False))["data"]
    testing_environment = is_testing_env()
    if not testing_environment:
        Reset_the_settings().get_user_database(college.get("id"), form_data=None)
    if testing_environment is False:
        ip_address = utility_obj.get_ip_address(request)
        for email in student_email:
            student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                {"user_name": email}
            )
            if not student:
                raise HTTPException(status_code=404, detail="Student not found.")
            random_password = utility_obj.random_pass()
            new_password = Hash().get_password_hash(random_password)
            await DatabaseConfiguration().studentsPrimaryDetails.update_one(
                {"user_name": email}, {"$set": {"password": new_password}}
            )
            # send mail to user only in production code. skip for testcases
            email_preferences = {
                key: str(val)
                for key, val in college.get("email_preferences", {}).items()
            }
            if not testing_environment:
                try:
                    basic_details = student.get("basic_details", {})
                    # TODO: Not able to add student timeline data
                    #  using celery task when environment is
                    #  demo. We'll remove the condition when
                    #  celery work fine.
                    if settings.environment in ["demo"]:
                        send_mail_config().send_mail(
                            data={
                                "id": str(student.get("_id")),
                                "user_name": email,
                                "password": random_password,
                                "first_name": basic_details.get("first_name"),
                                "mobile_number": basic_details.get(
                                    "mobile_number"
                                ),
                            },
                            payload={
                                "content": "student signup send token" " for verification mail",
                                "email_list": [email],
                            },
                            current_user=email,
                            ip_address=ip_address,
                            email_preferences=email_preferences,
                            event_type="email",
                            event_status="sent",
                            event_name="Verification",
                            college_id=college.get("id"),
                            add_timeline=False
                        )
                        StudentActivity().student_timeline(
                            student_id=str(student.get("_id")),
                            event_type="Email",
                            event_status="Sent verification mail",
                            message=f"Verification Template has been shared by"
                            f" {utility_obj.name_can(user) if user else utility_obj.name_can(basic_details)} on "
                            f"{email} using amazon_ses",
                            college_id=college.get("id"),
                        )
                    else:
                        send_mail_config().send_mail.delay(
                            data={
                                "id": str(student.get("_id")),
                                "user_name": email,
                                "password": random_password,
                                "first_name": basic_details.get("first_name"),
                                "mobile_number": basic_details.get(
                                    "mobile_number"),
                            },
                            payload={
                                "content": "student signup send token" " for verification mail",
                                "email_list": [email],
                            },
                            current_user=email,
                            ip_address=ip_address,
                            email_preferences=email_preferences,
                            event_type="email",
                            event_status="sent",
                            event_name="Verification",
                            college_id=college.get("id"),
                            add_timeline=False
                        )
                        StudentActivity().student_timeline.delay(
                            student_id=str(student.get("_id")),
                            event_type="Email",
                            event_status="Sent verification mail",
                            message=f"Verification Template has been shared by"
                                    f" {utility_obj.name_can(user) if user else utility_obj.name_can(basic_details)} on "
                                    f"{email} using amazon_ses",
                            college_id=college.get("id"),
                        )
                except KombuError as celery_error:
                    logger.error(
                        f"error sending verification mail" f" timeline data {celery_error}"
                    )
                except Exception as error:
                    logger.error(
                        f"error sending verification mail" f" timeline data {error}"
                    )
    return {"message": "Verification email sent."}


@email_router.post(
    "/comments_and_status/",
    summary="Send comments and status to student"
    " which are posted on document locker",
)
@requires_feature_permission("write")
async def send_email_to_notify_comments_status(
    current_user: CurrentUser,
    testing: Is_testing,
    request: Request,
    student_id: str = Query(
        description="Id of a student you'd like to remove \n*e.g.,"
        "**6223040bea8c8768d96d3880**",
    ),
    college: dict = Depends(get_college_id),
):
    """
        Send student documents information like verification status, comment/remark and reupload link if document verification failed etc through email.

    Params:
        college_id (str): An unique id/identifier of a college. e.g., 12345678901234567891
        student_id (str): An unique id/identifier of a student. e.g., 12345678901234567890

    Returns:
        dict: A dictionary which contains send email regarding student documents information like verification status, comment/remark and reupload link if document verification failed etc
    """
    await UserHelper().is_valid_user(user_name=current_user)
    await utility_obj.is_id_length_valid(student_id, "Student id")
    stu_doc = None
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
        ip_address = utility_obj.get_ip_address(request)
        if (
            stu_doc := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                {"_id": ObjectId(student_id)}
            )
        ) is None:
            raise DataNotFoundError(student_id, "Student")
        email = stu_doc.get("user_name")
        name = utility_obj.name_can(stu_doc.get("basic_details"))
        if (
            sec_doc := await DatabaseConfiguration().studentSecondaryDetails.find_one(
                {"student_id": ObjectId(student_id)}
            )
        ) is None:
            raise HTTPException(
                status_code=404,
                detail="Student documents not found.",
            )
        feedback = {}
        if (attachments := sec_doc.get("attachments")) is None:
            raise HTTPException(
                status_code=404,
                detail="Student documents not found.",
            )
        for doc in attachments:
            document = attachments.get(doc)
            if document:
                status = document.get("status", "")
                comments = document.get("comments", "")
                if status or comments:
                    feedback[doc] = {
                        "status": status if status else "--",
                        "comments": (
                            comments[0].get("message", "") if comments else "--"
                        ),
                    }
        if not feedback:
            raise HTTPException(
                status_code=404,
                detail="Since the Document Verification status is blank, mail can not be sent"
            )
        email_preferences = {
            key: str(val) for key, val in college.get("email_preferences", {}).items()
        }
        # Do not move position of below statement at top otherwise we'll get
        # circular ImportError
        from app.background_task.send_mail_configuration import EmailActivity
        email_ids = await EmailActivity().add_default_set_mails(email)
        if not is_testing_env():
            send_mail_config().send_comment_notification_mail.delay(
                feedback,
                email_ids,
                name=name,
                ip_address=ip_address,
                email_preferences=email_preferences,
                college_id=college.get("id"),

            )
    current_datetime = datetime.now(timezone.utc)
    update_data = {"last_user_activity_date": current_datetime}
    if stu_doc and not stu_doc.get("first_lead_activity_date"):
        update_data["first_lead_activity_date"] = current_datetime
    await DatabaseConfiguration().studentsPrimaryDetails.update_one({
        "_id": ObjectId(student_id)}, {"$set": update_data})
    return {"message": "Notification email about comments and status sent."}
