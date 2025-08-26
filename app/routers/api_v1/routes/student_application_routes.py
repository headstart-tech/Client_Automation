"""
This file contains API routes related to student application
"""

import datetime
import json
from pathlib import PurePath
from typing import Union

import razorpay
from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, Request, UploadFile, Form, File
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError

from app.background_task.send_mail_configuration import EmailActivity
from app.celery_tasks.celery_generate_pdf import generate_pdf_config
from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.custom_error import (DataNotFoundError, CustomError,
                                   ObjectIdInValid)
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, logger, settings, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import CurrentUser, cache_invalidation, \
    is_testing_env, Is_testing
from app.helpers.college_configuration import CollegeHelper
from app.helpers.payment_configuration import PaymentHelper
from app.helpers.promocode_voucher_helper.promocode_vouchers_helper import (
    promocode_vouchers_obj,
)
from app.helpers.student_curd.student_application_configuration import (
    StudentApplicationHelper,
)
from app.models.student_serialize import student_helper
from app.models.student_user_schema import User, UpdateApplication
from app.routers.api_v1.routes.payment_gateway_routes import (
    capture_payment,
    order_details,
)

application_router = APIRouter()


@application_router.get(
    "/get_student_application",
    summary="Get Current Student Application",
    response_description="Get student application details",
)
@requires_feature_permission("read")
async def get_student_application(
    testing: Is_testing,
    current_user: CurrentUser,
    season: str = None,
    page_num: Union[int, None] = Query(None, gt=0),
    page_size: Union[int, None] = Query(None, gt=0),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get student Application Detail\n
    * :*return* **Get all application details**:
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    user = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not user:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    student = await StudentApplicationHelper().get_detail_of_student_application(
        str(user["_id"]),
        page_num,
        page_size,
        route_name="/student_application/get_student_application",
        season=season,
        system_preference=college.get("system_preference"),
        fee_rules=college.get("fee_rules")
    )
    if student:
        if page_size and page_num:
            return student
        return utility_obj.response_model(
            data=student, message="Applications data fetched successfully."
        )
    raise HTTPException(status_code=404, detail="No found!")


@application_router.get(
    "/check_form_status/",
    summary="Check Application form status of current user",
    response_description="Check Application form status",
)
@requires_feature_permission("read")
async def check_form_status(
    testing: Is_testing,
    application_id: str,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Check Application Form Status\n
    * :*param* **application_id**:\n
    * :*return* **Check form status**:
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    user = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not user:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    checking_status = await StudentApplicationHelper().check_form_status_of_student(
        str(user["_id"]), application_id
    )
    if checking_status:
        return {"message": f"Form status is completed"}
    raise HTTPException(status_code=400, detail="Form status is Incomplete")


@application_router.post(
    "/declaration/",
    summary="Declaration of Application",
    response_description="Student Declaration",
)
@requires_feature_permission("write")
async def student_declaration(
    testing: Is_testing,
    request: Request,
    background_tasks: BackgroundTasks,
    application_id: str,
    current_user: CurrentUser,
    short: bool = False,
    season: str = None,
    college: dict = Depends(get_college_id),
):
    """
    Student Application Form Declaration\n
    * :*param* **short**:\n
    * :*param* **application_id** e.g., 25153153434134534534:\n
    * :*return* Student declaration**:
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not student:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    application = await DatabaseConfiguration().studentApplicationForms.find_one(
        {"_id": ObjectId(application_id), "student_id": ObjectId(str(student["_id"]))}
    )
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    student = await student_helper().student_serialization(student)
    application = await student_helper().application_serialize(application)
    if not short:
        return {"pending": f"Your form is still pending."}
    #  TODO: Uncomment accordingly
    # if application.get("current_stage") < 8:
    #     raise HTTPException(status_code=400, detail="Documents not uploaded")
    else:
        course = await DatabaseConfiguration().course_collection.find_one(
            {"_id": ObjectId(application["course_id"])}
        )
        check = await StudentApplicationHelper().form_status(
            str(student["_id"]), short, application, course
        )
        await utility_obj.update_notification_db(
            event="Application submitted", application_id=application_id
        )
        await cache_invalidation(api_updated="declaration/")
        if check:
            logger.info("Start the generate_application_pdf using celery")
            try:
                if not is_testing_env():
                    generate_pdf_config().generate_application_pdf.delay(
                        student=student,
                        application=application,
                        season=season,
                        college_id=college.get("id"),
                    )
            except KombuError as celery_error:
                logger.error(f"error generate application pdf {celery_error}")
            except Exception as error:
                logger.error(f"error generate application pdf {error}")
            logger.info("Finished the generate_application_pdf process")
            background_tasks.add_task(
                EmailActivity().application_submit,
                student=student,
                application=application,
                course=course,
                event_type="email",
                event_status="sent",
                event_name=f"Application of ({course.get('course_name')} "
                f"in {application.get('spec_name1')}) submitted",
                email_preferences=college.get("email_preferences", {}),
                college=college,
                request=request,
                college_id=college.get("id"),
            )
            return {"success": f"Your from is successfully submitted."}


@application_router.put(
    "/update_payment_status/{application_id}/",
    summary="Update Payment Status of student application",
    response_description="Update payment status",
)
@requires_feature_permission("edit")
async def update_payment_status(
    current_user: CurrentUser,
    testing: Is_testing,
    request: Request,
    background_tasks: BackgroundTasks,
    course_fee: int = Query(..., example=5),
    preference_fee: int | None = None,
    payment_id: str = Query(..., example="pay_JWHHwGFEiUOyUx"),
    application_id: str = Path(
        description="Enter application id", example="62821ac867cad887c5b42483"
    ),
    order_id: str = Query(
        description="Enter order id.", example="order_DaZlswtdcn9UNV"
    ),
    rezorpay_signature: str = Query(description="Enter Rezorpay signature."),
    promocode: str = None,
    payment_device: str = None,
    device_os: str = None,
    paid_amount: int = None,
    payment_method: str = "As per Flow",
    college: dict = Depends(get_college_id),
):
    """
    Update Payment Status\n
    * :*param* **application_id**:\n
    * :*param* **course_fee** e.g., 5:
    * :*param* **payment_id** e.g., pay_JWHHwGFEiUOyUx:
    * :*return* **Update payment status with message'**:
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    try:
        application = await DatabaseConfiguration().studentApplicationForms.find_one(
            {"_id": ObjectId(application_id)}
        )
    except:
        raise HTTPException(status_code=400, detail="Invalid application id")
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")
    student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"_id": application.get("student_id")}
    )
    if not student:
        student = {}
    try:
        headers, x_razorpay_account, client_id, client_secret = (
            await CollegeHelper().razorpay_header_update_partner(college)
        )
        client = razorpay.Client(auth=(client_id, client_secret))

        verify = client.utility.verify_payment_signature(
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": rezorpay_signature,
            }
        )
        course = await DatabaseConfiguration().course_collection.find_one(
            {"_id": ObjectId(application.get("course_id"))}
        )
        if verify:
            verify_payment = await order_details(order_id=order_id, college=college)
            payment_mode, payment_mode_info = "NA", "NA"
            if verify_payment:
                payment_helper = PaymentHelper()
                if verify_payment == "paid":
                    verify_payment = "captured"
                    orders = client.order.payments(order_id, headers=headers)
                    items = orders.get("items")
                    for item in items:
                        if item.get("status") == "captured":
                            payment_mode, payment_mode_info, payment_id = (
                                await payment_helper.get_payment_mode_info(
                                    item, request
                                )
                            )
                            break
                elif verify_payment == "attempted":
                    payment_capture = await capture_payment(
                        payment_id=payment_id, amount=int(str(paid_amount)+"00") if paid_amount else course_fee,
                        college=college
                    )
                    payment_mode, payment_mode_info, payment_id = (
                        await payment_helper.get_payment_mode_info(
                            payment_capture["data"][0], request
                        )
                    )
                    verify_payment = payment_capture["data"][0]["status"]
                current_datetime = datetime.datetime.utcnow()
                if verify_payment == "captured":
                    toml_data = utility_obj.read_current_toml_file()
                    if toml_data.get("testing", {}).get("test") is False:
                        basic_details = student.get("basic_details", {})
                        background_tasks.add_task(
                            EmailActivity().payment_successful,
                            data={
                                "payment_status": "success",
                                "created_at": current_datetime,
                                "order_id": order_id,
                                "payment_id": payment_id,
                                "student_name": utility_obj.name_can(basic_details),
                                "student_id": str(student.get("_id")),
                                "student_email_id": basic_details.get("email"),
                                "student_mobile_no": basic_details.get("mobile_number"),
                                "application_number": application.get(
                                    "custom_application_id"
                                ),
                                "degree": f"{course.get('course_name')} in "
                                f"{application.get('spec_name1')}",
                                "college_name": college.get("name"),
                                "nationality": basic_details.get("nationality"),
                                "application_fees": (
                                    course.get("fees")
                                    if promocode is None
                                    else paid_amount
                                ),
                                "college_id": str(college.get("id")),
                                "student_first_name": basic_details.get(
                                    "first_name", {}
                                ),
                            },
                            event_type="email",
                            event_status="sent",
                            event_name=f"Application "
                            f"({course.get('course_name')} in "
                            f"{application.get('spec_name1')}) "
                            f"payment successful",
                            email_preferences=college.get("email_preferences", {}),
                            college=college,
                        )
                        try:
                            # TODO: Not able to add student timeline
                            #  data in the DB when performing celery
                            #  task so added condition which add student
                            #  timeline when environment is not
                            #  development. We'll remove the condition
                            #  when celery work fine.
                            course_name = (
                                f"{course.get('course_name')} in {application.get('spec_name1')}"
                                if application.get("spec_name1") not in ["", None]
                                else f"{course.get('course_name')} Program"
                            )
                            # TODO: Not able to add student timeline data
                            #  using celery task when environment is
                            #  demo. We'll remove the condition when
                            #  celery work fine.
                            if settings.environment in ["demo"]:
                                StudentActivity().student_timeline(
                                    student_id=str(application.get("student_id")),
                                    event_type="Payment",
                                    event_status="Done",
                                    message=f"{utility_obj.name_can(student.get('basic_details', {}))} "
                                            f"captured Payment of Application"
                                    f" Name: {course_name}",
                                    college_id=str(application.get("college_id")),
                                )
                            else:
                                if not is_testing_env():
                                    StudentActivity().student_timeline.delay(
                                        student_id=str(application.get("student_id")),
                                        event_type="Payment",
                                        event_status="Done",
                                        message=f"{utility_obj.name_can(student.get('basic_details', {}))} "
                                                f" has captured Payment of Application"
                                        f" Name: {course_name}",
                                        college_id=str(application.get("college_id")),
                                    )
                        except KombuError as celery_error:
                            logger.error(
                                f"error storing payment done"
                                f" timeline data "
                                f"{celery_error}"
                            )
                        except Exception as error:
                            logger.error(
                                f"error storing payment done"
                                f" timeline data "
                                f"{error}"
                            )
                data = {
                    "status": verify_payment,
                    f"{verify_payment}_at": current_datetime,
                }
                payment_extra_info = {
                    "payment_device": payment_device,
                    "device_os": device_os,
                    "payment_method": payment_method,
                    "payment_mode": payment_mode,
                    "payment_mode_info": payment_mode_info,
                }
                data.update(payment_extra_info)
                if promocode and verify_payment == "captured":
                    data.update(
                        {
                            "payment_method": "Promocode",
                            "used_promocode": promocode,
                            "paid_amount": paid_amount,
                        }
                    )
                if (
                    payment_details := await DatabaseConfiguration().payment_collection.find_one(
                        {"payment_id": payment_id}
                    )
                ) is not None:
                    await DatabaseConfiguration().payment_collection.update_one(
                        {"payment_id": payment_id}, {"$set": data}
                    )
                else:
                    data.update(
                        {
                            "payment_id": payment_id,
                            "order_id": order_id,
                            "merchant": "RazorPay",
                            "user_id": ObjectId(student.get("_id")),
                            "details": {
                                "purpose": "studentApplication",
                                "application_id": ObjectId(application_id),
                            },
                            "attempt_time": current_datetime,
                            "error": {
                                "error_code": None,
                                "description": None,
                                "created_at": current_datetime,
                            },
                        }
                    )
                    details = (
                        await DatabaseConfiguration().payment_collection.insert_one(
                            data
                        )
                    )
                    payment_details = (
                        await DatabaseConfiguration().payment_collection.find_one(
                            {"_id": details.inserted_id}
                        )
                    )
                if application.get("payment_attempts") is None:
                    application["payment_attempts"] = []
                payment_attempt_info = {
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "status": verify_payment,
                    "attempt_time": current_datetime,
                }
                payment_attempt_info.update(payment_extra_info)
                application.get("payment_attempts", []).insert(0, payment_attempt_info)
                payment_info = {
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "status": verify_payment,
                    "created_at": current_datetime,
                }
                payment_info.update(payment_extra_info)
                update_info = {
                    "payment_attempts": application.get("payment_attempts"),
                    "payment_info": payment_info,
                }
                if promocode and verify_payment == "captured":
                    update_info.get("payment_info").update(
                        {
                            "payment_method": "Promocode",
                            "promocode_used": promocode,
                            "paid_amount": paid_amount,
                        }
                    )
                if (
                    await DatabaseConfiguration().studentApplicationForms.update_one(
                        {"_id": ObjectId(application_id)}, {"$set": update_info}
                    )
                    is not None
                ):
                    await DatabaseConfiguration().studentsPrimaryDetails.update_one({
                        "_id": ObjectId(student.get("_id"))},
                        {
                            "$set": {"last_accessed": datetime.datetime.utcnow()}
                        }
                    )
                    await StudentApplicationHelper().update_stage(
                        str(student.get("_id")), course.get("course_name"),
                        7.50, application.get("spec_name1"), college_id=application.get("college_id")
                    )
            data = utility_obj.response_model(
                data=await utility_obj.payment_helper(
                    payment_details, college, request
                ),
                message="Payment details added and updated successfully.",
            )
            if verify_payment == "captured":
                if promocode:
                    course_fee = preference_fee if preference_fee else int(str(course_fee)[:-2])
                    await promocode_vouchers_obj.update_promocode_usage(
                        promocode, application_id, course, course_fee
                    )
                await utility_obj.update_notification_db(
                    event="Payment captured", application_id=application_id
                )
            await cache_invalidation(
                api_updated="student_application/update_payment_status"
            )
            return data
        raise HTTPException(status_code=500, detail="Verify signature failed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@application_router.get(
    "/get_all_course_of_current_user",
    summary="Current User List of Course from Current College",
)
@requires_feature_permission("read")
async def get_all_course_of_student(
    testing: Is_testing,
    current_user: CurrentUser,
    season: str = None,
    page_num: Union[int, None] = Query(None, gt=0),
    page_size: Union[int, None] = Query(None, gt=0),
    college: dict = Depends(get_college_id),
):
    """
    Get student applications data with respect to college.

    Params:
        current_user (str): An user_name of current user.
        page_num (int | None): The page number for pagination.
        page_size (int | None): The number of records per page.
        college (dict): College data.
    Returns:
        dict: Student applications data with respect to college.
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    # Get student data
    student = await DatabaseConfiguration(
        season=season
    ).studentsPrimaryDetails.find_one({"user_name": current_user.get("user_name")})
    if not student:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    # Get student all courses data
    course = await StudentApplicationHelper().all_course_status(
        str(student.get("_id")),
        college.get("id"),
        page_num,
        page_size,
        route_name="/admin/get_all_course_of_current_user",
        season=season,
    )

    if course:
        return course
    else:
        return {"failure": f"not able to fetch course status of user"}


@application_router.put(
    "/manage_preference/",
    summary="Change the preference order",
)
@requires_feature_permission("edit")
async def manage_preference(
    application_id: str,
    change_preference: str,
    change_preference_with: str,
    testing: Is_testing,
    current_user: CurrentUser,
    season: str | None = None,
    college: dict = Depends(get_college_id)
):
    """
    Change the preference order.

    Params:\n
        - college_id (str): An unique college id which useful for get
            college information.
        - application_id (str): An unique application id which useful for get
            application information.
        - change_preference (str): Preference name which order want to change.
        - change_preference_with (str): Preference name which order want to
            replace with order of change_preference.
        - season (str | None): Either None or season id which useful for change
            particular

    Returns:\n
        - dict: A dictionary which contains information about change order of
        preference.

    Raises:\n
        - ObjectIdInValid: An error with status code 422 which occurred
            when application id will be wrong.
        - DataNotFoundError: An error with status code 404 which occurred
            when application not found.
        - CustomError: An error occurred with status code 400
            when provide incorrect preference information or preference
            information not found.
        - Exception: An error with status code 500 which occurred when
            something went wrong in the background code.
    """
    try:
        return await StudentApplicationHelper().manage_preference_order(
            application_id, change_preference,
            change_preference_with, season, college.get("id"), testing)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"Something went wrong when change the "
                                    f"preference order. Error - {error}")


@application_router.post(
    "/fee_details/",
    summary="Get the fee details.",
)
@requires_feature_permission("read")
async def manage_preference(
    course_name: str,
    preference_info: list[str] | None,
    testing: Is_testing,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id)
):
    """
    Get the fee details.

    Params:\n
        - college_id (str): An unique college id which useful for get
            college information.
        - season (str | None): Either None or season id which useful for change
            particular
        - course_name (str): Name of course. e.g., B.Tech.
        - preference_info (list): A list which contains preferences.
            e.g., ["Preference1", "Preference2"]

    Returns:\n
        - dict: A dictionary which contains information fee details.

    Raises:\n
        - Exception: An error with status code 500 which occurred when
            something went wrong in the background code.
    """
    try:
        if not testing:
            Reset_the_settings().check_college_mapped(college.get("id"))
        fee_rules = college.get("fee_rules", {})
        if not fee_rules:
            fee_rules = {}
        total_fee, preference_fee = await StudentApplicationHelper().calculate_application_fee(
            preference_info, fee_rules, course_name)
        return {"total_fee": total_fee, "preference_fee": preference_fee}
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"Something went wrong when get the "
                                    f"fee details. Error - {error}")


@application_router.post(
    "/update_student_application_details/",
    summary="Update Student Application Details",
)
@requires_feature_permission("edit")
async def update_student_application_details(
    current_user: CurrentUser,
    testing: Is_testing,
    course_name: str = Form(...),
    section: str = Form(...),
    last_stage: bool = False,
    application_details: str = Form(...),  # stringified JSON
    attachments: list[UploadFile] = File([]),
    college: dict = Depends(get_college_id),
):
    """
        Handles the update of a specific section of a student's application, including optional file attachments.

        This endpoint processes form data and files to update a student's application in the system.
        The application details should be provided as a JSON string and will be parsed internally.

        Args:
            testing (Is_testing): Dependency for testing or environment flag control.
            course_name (str): The unique identifier of the application to be updated.
            section (str): The specific section of the application being updated (e.g., "education", "personal_info").
            application_details (str): A stringified JSON object containing the data to update within the section.
            attachments (list[UploadFile]): Optional list of files to upload for the section.
            current_user (User): The currently authenticated user, provided via dependency injection.
            college (dict): Dictionary containing details about the college, injected via dependency.

        Returns:
            JSONResponse: Confirmation of a successful update or an error message with appropriate status code.

        Raises:
            HTTPException: If parsing fails, application is not found, user is unauthorized, or validation fails.
    """
    try:
        if not testing:
            Reset_the_settings().check_college_mapped(college.get("id"))
        application_details = UpdateApplication(**json.loads(application_details))
        application_details = jsonable_encoder(application_details)
        default_extensions, default_max_size_mb = {".jpg", ".jpeg", ".png", ".pdf"}, 5
        file_format = college.get('file_format')
        file_format = file_format if file_format else {}
        allowed_extensions = set(file_format.get('format', default_extensions))
        max_size_mb = file_format.get('size', default_max_size_mb)
        for file in attachments:
            extension = PurePath(file.filename).suffix
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)
            if extension.lower() not in allowed_extensions:
                raise CustomError(message=f"Unsupported file format: {extension}. File: {file.filename}")
            if file_size > max_size_mb * 1024 * 1024:
                raise CustomError(message=f"File size exceeds the {max_size_mb} MB limit. "
                                          f"File: {file.filename}")
        await StudentApplicationHelper().update_student_application(current_user.get("user_name"), application_details.get("payload", {})
                                                                    , attachments, application_details.
                                                                    get("attachment_details", {}), section, college,
                                                                    course_name, last_stage)
        return {"message": "Updated successfully!"}
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"Something went wrong While updating student details. Error - {error}")


@application_router.post(
    "/get_student_application_data/",
    summary="Get student application data",
)
@requires_feature_permission("read")
async def get_student_application_data(
    current_user: CurrentUser,
    testing: Is_testing,
    course_name: str = Query(...),
    college: dict = Depends(get_college_id),
):
    """
    """
    try:
        if not testing:
            Reset_the_settings().check_college_mapped(college.get("id"))
        return await StudentApplicationHelper().get_student_application_details(college_id=college.get("id"),
                                                                                user_name=current_user.get("user_name"),
                                                                                course_name=course_name
                                                                                )
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"Something went wrong While updating student details. Error - {error}")

