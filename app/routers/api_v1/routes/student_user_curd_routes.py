"""
This file contains API routes related to student user
"""

import re
from datetime import datetime
from typing import Optional
from typing import Union

import requests
from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Body, Depends, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from kombu.exceptions import KombuError

from app.background_task.send_mail_configuration import EmailActivity
from app.background_task.send_sms import SmsActivity
from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, settings, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import (
    get_current_user,
    CurrentUser,
    AuthenticateUser,
    cache_invalidation,
    Is_testing,
    is_testing_env,
    get_collection_from_cache,
    store_collection_in_cache,
)
from app.helpers.student_curd.student_configuration import StudentHelper
from app.helpers.student_curd.student_user_crud_configuration import (
    StudentUserCrudHelper,
)
from app.helpers.student_helper.otp_helper import VerifyEmail_Mobile
from app.helpers.telephony.check_in_out_helper import CheckInOutHelper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.student_user_crud_schema import (
    StudentUser,
    UpdateStudentUser,
    VerifyReCaptcha,
)
from app.core.custom_error import CustomError, DataNotFoundError, NotEnoughPermission
from app.models.student_user_schema import User

router = APIRouter()

logger = get_logger(__name__)


async def verify_student(email_or_mobile, college_id):
    """
    Verify student by email id or mobile number, return student details
    """
    if re.search(
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        email_or_mobile,
    ):
        student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"user_name": email_or_mobile, "college_id": college_id}
        )
    else:
        student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"basic_details.mobile_number": email_or_mobile, "college_id": college_id}
        )
    return student


@router.post("/signup", response_description="Student signup")
async def student_signup(
    request: Request,
    background_tasks: BackgroundTasks,
    testing: Is_testing,
    user: dict,
    college: dict = Depends(get_college_id),
):
    """
    Student Signup\n
    * :*param* **full_name** e.g., John Michel Dow:\n
    * :*param* **email** e.g., john@example.com:\n
    * :*param* **mobile_number** e.g., 1234567890:\n
    * :*param* **country_code** e.g., IN:\n
    * :*param* **state_code** e.g., UP:\n
    * :*param* **city** e.g., Mathura :\n
    * :*param* **course** e.g., Bsc:\n
    * :*param* **main_specialization** e.g., Medical Lab Technology:\n
    * :*param* **college_id** e.g., 123456789012345678901234:\n
    * :*return* **Student details**:
    """
    user = jsonable_encoder(user)
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    user["college_id"] = college.get("id")
    st_reg = await StudentUserCrudHelper().student_register(
        user, request=request, background_tasks=background_tasks
    )
    if st_reg:
        await cache_invalidation(api_updated="student_user_crud/signup")
        return st_reg
    else:
        logger.error("Some thing went wrong in student signup!")


@router.get(
    "/logout/", response_description="Student logout"
)  # response_class=HTMLResponse
async def student_logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    device: str = "computer",
    device_info: str | None = None,
    ):
    """
    Student Logout\n
    * :*return* **Student successfully logout with message
     '{"success": "logout successfully"}'**:
    """
    user = await UserHelper().is_valid_user(current_user)
    user_id = user.get("_id")
    today_date = datetime.now().strftime("%Y-%m-%d")
    user_data = await DatabaseConfiguration().checkincheckout.find_one({
        "user_id": ObjectId(user_id),
        "date": today_date
    })
    ip_address = utility_obj.get_ip_address(request)
    try:
        if user_data:
            login_details = user_data.get("login_details", [])
            present_time = datetime.utcnow()
            if user_data.get("current_stage") != "CheckOut":
                await utility_obj.update_checkout_details(user_data, present_time)
            for i in range(len(login_details) - 1, -1, -1):
                if login_details[i].get("login") and not login_details[i].get("logout", None):
                    check_in_time = login_details[i].get("login")
                    total_mins = int((present_time - check_in_time).total_seconds() // 60)
                    DatabaseConfiguration().checkincheckout.update_one({
                        "user_id": ObjectId(user.get("_id")),
                        "date": today_date,
                        f"login_details.{i}.logout": {"$exists": False},
                    }, {
                        "$set": {
                            f"login_details.{i}.logout": present_time,
                            f"login_details.{i}.total_mins": total_mins,
                            f"{device}_logout_details.timestamp": present_time,
                            f"{device}_logout_details.device_info": device_info,
                            f"{device}_logout_details.ip_address": ip_address,
                            "current_stage": "LogOut",
                            "last_logout": present_time,
                            f"live_on_computer": False,
                            "live_on_mobile": False
                        }
                    })
        await CheckInOutHelper().update_check_status(
            user,
            {
                "check_in_status": False,
                "reason": {"title": "User Logout from system", "icon": None},
            },
        )
    except Exception as error:
        logger.error(f"An error got when update check-in status. Error - {error}")

    response = RedirectResponse(url="/login/", status_code=302)
    response.delete_cookie(key="access_token")
    return {"success": "logout successfully"}


@router.put(
    "/update_student_primary_data/", response_description="Update the student data"
)
@requires_feature_permission("edit")
async def update_student_primary_data(
    current_user: CurrentUser,
    testing: Is_testing,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    req: Optional[UpdateStudentUser] = Body(...),
    season: str | None = None,
    student_id: str | None = None
):
    """
    Update Student Data/Information using id.\n

    Params:\n
        - college_id (str): An unique identifier of a college. e.g., "123456789012345678901234"
        - season (str | None): Optional field. Either None or a string value which represents season id.
        - student_id (str | None): Optional field. Either None or a string value which represents unique identifier of a student.

    Request body params:\n
        - req (dict): A dictionary which contains fields which want to update.

    Returns:\n
        - dict: A dictionary which contains information about student data update.

    Raises:\n
        - NotEnoughPermission: An error occurred with status code 401 when user don't have permission to
            update primary data.
        - CustomError: An error occurred with status code 422 when email/mobile_number already exists.
        - DataNotFoundError: An error occurred with status code 404 when student not found.
        - Exception: An error occurred with status code 500 when something went wrong in the backend code.
    """
    try:
        college_id = college.get("id")
        if not testing:
            Reset_the_settings().check_college_mapped(college_id)
        req = {k: v for k, v in req.model_dump().items() if v is not None}
        updated_student = await StudentUserCrudHelper().update_student_data(
            current_user, req, ObjectId(college_id), season, student_id
        )
        return updated_student
    except NotEnoughPermission as error:
        raise HTTPException(status_code=401, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Something went wrong when update the student data. Error - {error}")


@router.post("/verify_captcha/", summary="Verify google recaptcha v3")
async def verify_captcha(token: VerifyReCaptcha):
    """
    Verify google recaptcha v3
    """
    try:
        token = token.model_dump()
        YOUR_SECRET_KEY = settings.captcha_secret_key
        url = "https://www.google.com/recaptcha/api/siteverify"
        payload = {"response": token.get("response"), "secret": YOUR_SECRET_KEY}
        response = requests.request("POST", url, data=payload)
        # Receiving the response
        google_response = response.json()

        # Analyzing the response
        if google_response["success"] is True:
            # Preparing our response that will be sent to our front-end
            response = {"is_human": True}

            # This is our custom logic in case the request was
            # initiated by a bot.
            if google_response["score"] < 0.5:
                response["is_human"] = False
                return utility_obj.response_model(
                    data=response, message="Bot is found."
                )
            return utility_obj.response_model(data=response, message="Human is found.")
        else:
            raise HTTPException(
                status_code=404, detail="Validation of FE token went wrong."
            )
    except Exception:
        raise HTTPException(status_code=400, detail=f"Bad request.")


async def send_otp(background_tasks, student, request, college,
                   action_type="system", name=None, user_id=None):
    """send otp by sms and email"""
    if settings.environment != "demo":
        email_otp = await utility_obj.generate_random_otp()
        mobile_otp = await utility_obj.generate_random_otp()
    else:
        email_otp = mobile_otp = "123456"
    ip_address = utility_obj.get_ip_address(request)
    background_tasks.add_task(
        EmailActivity().send_otp_through_email,
        first_name=student.get("basic_details", {}).get("first_name"),
        email_otp=email_otp,
        email=student.get("user_name"),
        event_type="email",
        event_status="sent",
        event_name="Login with OTP",
        payload={
            "content": "Login with OTP",
            "email_list": [student.get("user_name")],
        },
        current_user=student.get("user_name"),
        ip_address=ip_address,
        email_preferences=college.get("email_preferences", {}),
        action_type=action_type,
        college_id=college.get("id")
    )
    templates = await get_collection_from_cache(collection_name="templates")
    if templates:
        otp_template = utility_obj.search_for_document(
            templates, field="template_name", search_name="otp"
        )
    else:
        otp_template = await DatabaseConfiguration().otp_template_collection.find_one(
            {"template_name": "otp"}
        )
        collection = (
            await DatabaseConfiguration()
            .otp_template_collection.aggregate([])
            .to_list(None)
        )
        await store_collection_in_cache(collection, collection_name="templates")

    if otp_template is not None:
        background_tasks.add_task(
            SmsActivity().send_sms_to_users,
            send_to=[student.get("basic_details", {}).get("mobile_number")],
            dlt_content_id=otp_template.get("dlt_content_id", ""),
            sms_content=otp_template.get("content", "").format(
                name=student.get("basic_details", {}).get("first_name",
                                                          "Student"),
                otp=mobile_otp,
            ),
            sms_type=otp_template.get("sms_type", ""),
            sender=otp_template.get("sender", ""),
            ip_address=ip_address,
            student=student,
            action_type=action_type,
        )
    await DatabaseConfiguration().studentsPrimaryDetails.update_one(
        {"_id": student.get("_id"), "college_id": ObjectId(college.get("id"))},
        {
            "$set": {
                "otp": {
                    "email": email_otp,
                    "mobile": mobile_otp,
                    "created_at": datetime.utcnow(),
                }
            }
        },
    )
    if name is not None:
        message = (f"{name} has sent a mobile OTP on student’s"
                   f" phone number - "
                   f"{student.get('basic_details', {}).get('mobile_number')}")
        try:
            # TODO: Not able to add student timeline data
            #  using celery task when environment is
            #  demo. We'll remove the condition when
            #  celery work fine.
            if settings.environment in ["demo"]:
                StudentActivity().student_timeline(
                    student_id=str(student.get("_id")),
                    event_type="sms",
                    event_name="sent sms",
                    template_type="sms",
                    user_id=user_id,
                    message=message,
                    college_id=str(student.get("college_id")),
                )
            else:
                StudentActivity().student_timeline.delay(
                    student_id=str(student.get("_id")),
                    event_type="sms",
                    event_name="sent sms",
                    template_type="sms",
                    user_id=user_id,
                    message=message,
                    college_id=str(student.get("college_id")),
                )
        except KombuError as celery_error:
            logger.error(f"error add_student_timeline {celery_error}")
        except Exception as error:
            logger.error(f"error add_student_timeline {error}")


@router.post("/login_with_otp/", summary="Login with OTP")
async def login_with_otp(
    request: Request,
    background_tasks: BackgroundTasks,
    testing: Is_testing,
    college: dict = Depends(get_college_id),
        user_id: str | None = None,
    email_or_mobile: str = Query(
        ..., description="Enter the" " email or" " mobile" " number"
    ),
):
    """
    Send OTP through email id or mobile number
    """
    college_id = college.get("id")
    if not testing:
        Reset_the_settings().get_user_database(college_id)
    student = await verify_student(email_or_mobile, ObjectId(college_id))
    name = None
    if user_id is not None:
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid User ObjectId")
        if (
                user := await DatabaseConfiguration().user_collection.find_one(
                    {"_id": ObjectId(user_id)}
                )
        ) is not None:
            name = utility_obj.name_can(user)
    if student:
        if not testing:
            if student.get("otp"):
                time_difference = datetime.utcnow() - student.get("otp", {}).get(
                    "created_at", datetime.utcnow()
                )
                if (time_difference.total_seconds() / 60) < 5:
                    time_difference = (
                        datetime.utcnow()
                        - student.get("otp", {}).get("created_at", datetime.utcnow())
                    ).total_seconds() * 1000
                    return {
                        "detail": f"OTP already sent to your registered mobile"
                        f" or email. You can regenerate OTP after "
                        f"{int(900000 - time_difference)} "
                        f"milliseconds.",
                        "time_remaining": int(900000 - time_difference),
                    }
                else:
                    await send_otp(
                        background_tasks, student, request, college,
                        action_type="user", name=name, user_id=user_id
                    )
            else:
                await send_otp(
                    background_tasks, student, request, college,
                    action_type="user", name=name, user_id=user_id
                )

        return {
            "message": "OTP is sent through email id or mobile number.",
            "time_remaining": 900000,
        }
    else:
        return {"detail": "Enter correct email id or mobile number."}


@router.get("/verify_otp/", summary="Verify otp")
async def verify_otp(
    request: Request,
    testing: Is_testing,
    college: dict = Depends(get_college_id),
    email_or_mobile: str = Query(
        ..., description="Enter the " "email or" " mobile" " number"
    ),
    otp: str = Query(..., description="Enter the email or" " mobile otp"),
):
    """
    Verify OTP of email or mobile
    """
    college_id = college.get("id")
    if not testing:
        Reset_the_settings().get_user_database(college_id)
    student = await verify_student(email_or_mobile, ObjectId(college.get("id")))
    if student:
        if not testing:
            update_status, today = {}, datetime.utcnow()
            if settings.environment == "demo":
                if student.get("otp", {}) == {}:
                    student["otp"] = {"email": "123456", "mobile": "123456"}
                student["otp"] = {"created_at": today}
            time_difference = today - student.get("otp", {}).get("created_at", today)
            if (time_difference.total_seconds() / 60) > 15:
                return {
                    "message": "Invalid OTP! Please enter correct OTP.",
                    "time_remaining": 0,
                }
            elif (
                await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {
                        "_id": student.get("_id"),
                        "college_id": ObjectId(college.get("id")),
                        "otp.email": otp,
                    }
                )
                is not None
            ):
                if student.get("is_email_verify") in [None, False]:
                    update_status.update(
                        {"is_email_verify": True, "email_verify_at": today}
                    )
            elif (
                await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {
                        "_id": student.get("_id"),
                        "college_id": ObjectId(college.get("id")),
                        "otp.mobile": otp,
                    }
                )
                is not None
            ):
                if student.get("is_mobile_verify") in [None, False]:
                    update_status = {
                        "is_mobile_verify": True,
                        "mobile_verify_at": today,
                    }
            else:
                time_difference = (
                    today - student.get("otp", {}).get("created_at", today)
                ).total_seconds() * 1000
                return {
                    "detail": "Invalid OTP! Please enter correct OTP.",
                    "time_remaining": int(900000 - time_difference),
                }
            if student.get("is_verify") in [None, False]:
                update_status.update({"is_verify": True, "verify_at": today})
            if update_status:
                await DatabaseConfiguration().studentsPrimaryDetails.update_one(
                    {
                        "_id": student.get("_id"),
                        "college_id": ObjectId(college.get("id")),
                    },
                    {"$set": update_status},
                )
            await DatabaseConfiguration().studentsPrimaryDetails.update_one(
                {"_id": student.get("_id"), "college_id": ObjectId(college.get("id"))},
                {"$unset": {"otp": True}},
            )
            try:
                toml_data = utility_obj.read_current_toml_file()
                if toml_data.get("testing", {}).get("test") is False:
                    # TODO: Not able to add student timeline data
                    #  using celery task when environment is
                    #  demo. We'll remove the condition when
                    #  celery work fine.
                    if settings.environment in ["demo"]:
                        StudentActivity().student_timeline(
                            student_id=str(student.get("_id")),
                            event_type="Login",
                            event_status="Login",
                            message=f"{utility_obj.name_can(student.get('basic_details', {}))}"
                            f" logged in through OTP method into"
                            f" the Dashboard",
                            college_id=str(student.get("college_id")),
                        )
                    else:
                        if not is_testing_env():
                            StudentActivity().student_timeline.delay(
                                student_id=str(student.get("_id")),
                                event_type="Login",
                                event_status="Login",
                                message=f"{utility_obj.name_can(student.get('basic_details', {}))}"
                                f" logged in through OTP method into"
                                f" the Dashboard",
                                college_id=str(student.get("college_id")),
                            )
            except KombuError as celery_error:
                logger.error(f"error storing login by otp data " f"{celery_error}")
            except Exception as error:
                logger.error(f"error storing otp data {error}")
            return await AuthenticateUser().create_refresh_token_helper(
                student=student, request=request, college=college
            )
        else:
            return {"message": "testing"}
    else:
        return {"detail": "Enter correct email id or mobile number."}


@router.get("/board_detail/")
async def board_details(
    page_num: Union[int, None] = Query(None, gt=0),
    page_size: Union[int, None] = Query(None, gt=0),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Returns board details
    """
    if page_num and page_size:
        board = await StudentHelper().tenth_inter_board_name(
            page_num, page_size, route_name="/student_user_curd/board_detail/"
        )
    else:
        board = await StudentHelper().tenth_inter_board_name()
    if board:
        if page_num and page_size:
            return board
        return utility_obj.response_model(
            data=board, message="data fetch successfully."
        )


@router.put("/email_mobile_verify")
async def email_or_mobile_verify(
    request: Request,
    testing: Is_testing,
    background_task: BackgroundTasks,
    email_or_mobile: str,
    college_id: str,
    otp: int = None,
    mobile_prefix: str = None
):
    """
    Verification of email address or mobile number

    params:
        email_or_mobile (str): get string value from the user
         eq. email, mobile
         otp (int):  get otp value from the user
    return:
        Response: otp send on you email or mobile number
    """
    await utility_obj.is_id_length_valid(college_id, "College id")
    if not testing:
        Reset_the_settings().get_user_database(college_id)
    ip_address = utility_obj.get_ip_address(request)
    return await VerifyEmail_Mobile().validate_email_mobile(
        college_id=college_id,
        email_or_mobile=email_or_mobile,
        otp=otp,
        background_task=background_task,
        ip_address=ip_address,
        action_type="user",
        mobile_prefix=mobile_prefix
    )
