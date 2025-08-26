"""
This file contains API routes related to payment gateway
"""

import datetime
import json
from typing import Union

import razorpay
from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    Path,
    Query,
    Request,
    UploadFile,
    BackgroundTasks,
)
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError
from razorpay.errors import BadRequestError

from app.background_task.send_mail_configuration import EmailActivity
from app.background_task.student_payment import StudentPaymentActivity
from app.celery_tasks.celery_send_mail import send_mail_config
from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.custom_error import DataNotFoundError, ObjectIdInValid
from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, settings, requires_feature_permission
from app.database.aggregation.payment import Payment
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id
from app.dependencies.oauth import CurrentUser, Is_testing, is_testing_env
from app.helpers.college_configuration import CollegeHelper
from app.helpers.payment_configuration import PaymentHelper
from app.helpers.promocode_voucher_helper.promocode_vouchers_helper import (
    promocode_vouchers_obj,
)
from app.helpers.student_curd.student_application_configuration import StudentApplicationHelper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.payment_gateway_schema import UpdatePaymentDetails

logger = get_logger(name=__name__)
payment_router = APIRouter()


@payment_router.get("/{payment_id}/", summary="Fetch payment details by payment_id")
async def payment_details_by_payment_id(
    testing: Is_testing,
    request: Request,
    payment_id: str = Path(..., description="Enter payment ID"),
    college: dict = Depends(get_college_id),
):
    """
    Fetch Payment Details by payment_id\n
    * :*param* **payment_id** e.g., pay_G3P9vcIhRs3NV4:\n
    * :*return* **Payment details** if payment_id exist:
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    payment = await DatabaseConfiguration().payment_collection.find_one(
        {"payment_id": payment_id}
    )
    if payment:
        return utility_obj.response_model(
            data=await utility_obj.payment_helper(payment, college, request),
            message="Payment details fetched successfully.",
        )
    raise HTTPException(
        status_code=404, detail="Make sure payment id should be correct."
    )


@payment_router.get(
    "/{payment_id}/card/", summary="Fetch card details of payment by payment_id"
)
async def card_details_of_payment(
    payment_id: str = Path(..., description="Enter payment ID"),
    college: dict = Depends(get_college_id),
):
    """
    Fetch Card Details of Payment by payment_id\n
    * :*param* **payment_id** e.g., pay_G3P9vcIhRs3NV4:\n
    * :*return* **Card details of a payment**:
    """

    headers, x_razorpay_account, client_id, client_secret = (
        await CollegeHelper().razorpay_header_update_partner(college)
    )
    client = razorpay.Client(auth=(client_id, client_secret))
    try:
        card_details = client.payment.fetchCardDetails(payment_id, headers=headers)
    except BadRequestError as e:
        raise HTTPException(status_code=500, detail=str(e.args)[2:-3])
    if card_details:
        return utility_obj.response_model(
            data=card_details, message="Payment details fetched successfully."
        )
    raise HTTPException(
        status_code=404, detail="Make sure payment id should be correct."
    )


@payment_router.get(
    "/application/{application_id}/", summary="Fetch payment details by application_id."
)
async def payment_details_by_application_id(
    testing: Is_testing,
    application_id: str = Path(description="Enter application ID."),
    college: dict = Depends(get_college_id),
):
    """
    Fetch all payment details by application_id.

    Params:
        - application_id (str): An unique identifier of an application.
            e.g., 628374373cd9fae967aa63ee
        - college_id (str): An unique identifier of a college.

    Returns:
        - dict: A dictionary which contains all payment details based on
            application_id along with successful message.

    Raises:
        - Exception: An error occurred with status code 500 when something
            happen wrong in the backend code.
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    application = await StudentApplicationHelper().get_application_data(application_id)
    try:
        return {
            "data": await Payment().get_payment_details_by_app_id(
                application.get("_id")
            ),
            "message": "All payment details fetched successfully.",
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="An error occurred when get payment details by "
            f"application id. Error - {error}",
        )


@payment_router.get("/", summary="Fetch all payment details")
async def all_payment_details(
    testing: Is_testing,
    request: Request,
    page_num: Union[int, None] = Query(None, gt=0),
    page_size: Union[int, None] = Query(None, gt=0),
    college: dict = Depends(get_college_id),
):
    """
    Fetch All Payment Details\n
    * :*param* **payment_id** e.g., pay_G3P9vcIhRs3NV4:\n
    * :*return* **All Payment details**  if payment details exist:
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    payments_list = []
    if (data := DatabaseConfiguration().payment_collection.find({})) is not None:
        total_payments = (
            await DatabaseConfiguration().payment_collection.count_documents({})
        )
        payments_list = [
            await utility_obj.payment_helper(item, college, request)
            for item in await data.to_list(length=total_payments)
        ]

    if payments_list:
        if page_num and page_size:
            payments_length = len(payments_list)
            response = await utility_obj.pagination_in_api(
                page_num,
                page_size,
                payments_list,
                payments_length,
                route_name=f"/payments/",
            )
            return {
                "data": response["data"],
                "total": response["total"],
                "count": page_size,
                "pagination": response["pagination"],
                "message": "All Payment details fetched successfully.",
            }
        return utility_obj.response_model(
            data=payments_list, message="All Payment details fetched successfully."
        )
    raise HTTPException(status_code=404, detail="Payment not found.")


@payment_router.post(
    "/{payment_id}/capture/", summary="Capture a payment by payment_id"
)
async def capture_payment(
    payment_id: str = Path(
        ..., description="Enter payment ID", example="pay_JWHHwGFEiUOyUx"
    ),
    amount: int = Query(..., gt=0),
    college: dict = Depends(get_college_id),
):
    """
    Capture a Payment by payment_id\n
    * :*param* **payment_id** e.g., pay_JWHHwGFEiUOyUx:\n
    * :*param* **amount** e.g., 5:\n
    * :*return* **Payment details**:
    """
    headers, x_razorpay_account, client_id, client_secret = (
        await CollegeHelper().razorpay_header_update_partner(college)
    )
    client = razorpay.Client(auth=(client_id, client_secret))

    try:
        payment_capture = client.payment.capture(
            payment_id, amount=amount, headers=headers
        )
    except BadRequestError as e:
        raise HTTPException(status_code=500, detail=str(e.args)[2:-3])
    return utility_obj.response_model(
        data=payment_capture, message="Payment captured successfully."
    )


async def validate_details(application_id: str):
    """
    Validate input application id and return required details

    Params:
        application_id (str): Application id for get application details.

    Returns:
        tuple: return application and course details in a tuple form.
    """
    try:
        application = await DatabaseConfiguration().studentApplicationForms.find_one(
            {"_id": ObjectId(application_id)}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e.args))
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")
    course = await DatabaseConfiguration().course_collection.find_one(
        {"_id": ObjectId(application.get("course_id"))}
    )
    if course is None:
        course = {}
    return application, course


@payment_router.put("/{payment_id}/update/", summary="Update payment details")
async def update_payment(
    testing: Is_testing,
    request: Request,
    payment_details: UpdatePaymentDetails,
    payment_id: str = Path(
        ..., description="Enter payment ID", example="pay_JWHHwGFEiUOyUx"
    ),
    user_id: str = Query(None, description="Enter user id"),
    application_id: str = Query(None, description="Enter application id"),
    order_id=None,
    payment_device: str = None,
    device_os: str = None,
    college: dict = Depends(get_college_id),
    payment_method: str = "As per Flow",
):
    """
    Update the payment details
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    application, course = await validate_details(application_id)
    req = {k: v for k, v in payment_details.model_dump().items() if v is not None}
    if len(req) < 1:
        raise HTTPException(status_code=422, detail="Need to pass atleast one field.")
    if (
        student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"_id": ObjectId(application.get("student_id"))}
        )
    ) is None:
        student = {}
    if req.get("error_code"):
        req.update({"error.error_code": req.get("error_code")})
        req.pop("error_code")
    if req.get("error_description"):
        req.update({"error.description": req.get("error_description")})
        req.pop("error_description")
    current_datetime, payment_status = (
        datetime.datetime.utcnow(),
        req.get("status", "").lower(),
    )
    payment_attempt_info = {
        "payment_id": payment_id,
        "order_id": order_id,
        "status": payment_status,
        "attempt_time": current_datetime,
    }
    payment_extra_info = {
        "payment_device": payment_device,
        "device_os": device_os,
        "payment_method": payment_method,
        "payment_mode": "NA",
        "payment_mode_info": await PaymentHelper().get_payment_mode_info({}, request),
    }
    payment_attempt_info.update(payment_extra_info)
    temp_payment = application.get("payment_attempts", [])
    temp_payment.insert(0, payment_attempt_info)
    application.update({"payment_attempts": temp_payment})
    payment_info = {
        "payment_id": payment_id,
        "order_id": order_id,
        "status": payment_status,
        "created_at": current_datetime,
    }
    payment_info.update(payment_extra_info)
    update_info = {
        "payment_attempts": application.get("payment_attempts")
    }
    if application.get("payment_info", {}).get("status") != "captured":
        update_info.update({"payment_info": payment_info})
    req.update({"order_id": order_id}) if order_id else None
    course_name = (
        f"{course.get('course_name')} in " f"{application.get('spec_name1')}"
        if (application.get("spec_name1") != "" and application.get("spec_name1"))
        else f"{course.get('course_name')} " f"Program"
    )
    if (
        await DatabaseConfiguration().payment_collection.find_one(
            {"payment_id": payment_id}
        )
        is None
    ):
        try:
            # TODO: Not able to add student timeline data
            #  using celery task when environment is
            #  demo. We'll remove the condition when
            #  celery work fine.
            if settings.environment in ["demo"]:
                StudentActivity().student_timeline(
                    student_id=str(application.get("student_id")),
                    event_type="Payment",
                    event_status="Failed",
                    message=f"{utility_obj.name_can(student.get('basic_details', {}))}"
                    f" Failed Payment of"
                    f" Application Name: {course_name}",
                    college_id=str(application.get("college_id")),
                )
            else:
                if not is_testing_env():
                    StudentActivity().student_timeline.delay(
                        student_id=str(application.get("student_id")),
                        event_type="Payment",
                        event_status="Failed",
                        message=f"{utility_obj.name_can(student.get('basic_details', {}))}"
                        f" Failed Payment of"
                        f" Application Name: {course_name}",
                        college_id=str(application.get("college_id")),
                    )
        except KombuError as celery_error:
            logger.error(f"error storing failed payment timeline data {celery_error}")
        except Exception as error:
            logger.error(f"error storing failed payment timeline data {error}")
        data = {
            "payment_id": payment_id,
            "order_id": order_id,
            "merchant": "RazorPay",
            "user_id": ObjectId(user_id),
            "details": {
                "purpose": "StudentApplication",
                "application_id": ObjectId(application_id),
            },
            "status": payment_status,
            "error": {
                "error_code": f"{req.get('error.error_code')}",
                "description": f"{req.get('error.description')}",
                "created_at": datetime.datetime.utcnow(),
            },
            "attempt_time": current_datetime,
        }
        data.update(payment_extra_info)
        inserted_data = await DatabaseConfiguration().payment_collection.insert_one(
            data
        )
        if application["payment_info"]["status"] != "captured":
            if payment_status == "paid":
                payment_status = "captured"
                payment_attempt_info.update({"status": payment_status})
        await DatabaseConfiguration().studentApplicationForms.update_one(
            {"_id": ObjectId(application_id)}, {"$set": update_info}
        )
        if inserted_data:
            return utility_obj.response_model(
                data=await utility_obj.payment_helper(data, college, request),
                message="Data inserted successfully.",
            )
    if req:
        if (
            await DatabaseConfiguration().payment_collection.update_one(
                {"payment_id": payment_id}, {"$set": req}
            )
            is not None
        ):
            if application:
                course = await DatabaseConfiguration().course_collection.find_one(
                    {"_id": ObjectId(application.get("course_id"))}
                )
                await DatabaseConfiguration().studentApplicationForms.update_one(
                    {"_id": ObjectId(application_id)}, {"$set": update_info}
                )
                try:
                    # TODO: Not able to add student timeline data
                    #  using celery task when environment is
                    #  demo. We'll remove the condition when
                    #  celery work fine.
                    if settings.environment in ["demo"]:
                        StudentActivity().student_timeline(
                            student_id=str(application.get("student_id")),
                            event_type="Payment",
                            event_status="Updated",
                            message=f"{utility_obj.name_can(student.get('basic_details', {}))} Updated Payment of"
                            f" Application Name: {course_name}",
                            college_id=str(application.get("college_id")),
                        )
                    else:
                        if not is_testing_env():
                            StudentActivity().student_timeline.delay(
                                student_id=str(application.get("student_id")),
                                event_type="Payment",
                                event_status="Updated",
                                message=f"{utility_obj.name_can(student.get('basic_details', {}))} Updated Payment of"
                                f" Application Name: {course_name}",
                                college_id=str(application.get("college_id")),
                            )
                except KombuError as celery_error:
                    logger.error(
                        f"error storing update payment update"
                        f" payment timeline data "
                        f"{celery_error}"
                    )
                except Exception as error:
                    logger.error(
                        f"error storing update payment" f" timeline data {error}"
                    )
                return utility_obj.response_model(
                    data=req, message="Payment details updated successfully."
                )
    raise HTTPException(status_code=500, detail="Something went wrong.")


async def create_order_by_data(client, data, headers):
    """
    Create order with data and return order data.

    Params:
        client: A client object for use razorpay methods.
        data (dict): Data useful for create order.
        headers (dict): Useful for pass data in headers.

    Returns:
        order_info (dict): order data.
    """
    try:
        order_info = client.order.create(data=data, headers=headers)
    except BadRequestError as e:
        raise HTTPException(status_code=500, detail=str(e.args)[2:-3])
    return order_info


async def validate_existing_order_details(
    order_data: dict, client, headers: dict, data: dict, request: Request, payment_attempt_info: dict,
        student_id: ObjectId, application: dict, promocode_update: dict, promocode: str | None, application_id: ObjectId
        , student: dict, amount: int, college: dict, background_tasks: BackgroundTasks
):
    """
    Validate order details and return order details

    Params:
        - order_data (str): Existing order data.
        - client: A client object for use razorpay methods.
        - headers (dict): Useful for pass data in headers.
        - data (dict): Data useful for create order.
        - request (Request): An object of `Request` which contains request data, useful for get ip address.
        - payment_attempt_info (dict): A dictionary which contains payment attempt information.
        - student_id (ObjectId): An unique identifier of a student.
        - application (dict): A dictionary which contains application data.
        - promocode_update (dict): A dictionary which contains promo-code related data.
        - promocode: Either None or a promo-code which used for create order.
        - application_id (ObjectId): An unique identifier of an application.
        - student (dict): A dictionary which contains student data.
        - amount (int): An amount which used to create order.
        - college (dict): A dictionary which contains college data.
        - background_tasks (BackgroundTasks): An object of
            `BackgroundTasks` which useful for perform background task (s).

    Returns:
        - order_info (dict): order data.

    Raises:
        - HTTPException: An error occurred with status code 422 when payment is already captured.
    """
    order_id = order_data.get("order_id")
    order_info = client.order.fetch(order_id, headers=headers)
    if order_info.get("status") == "paid":
        orders = client.order.payments(order_id, headers=headers)
        items = orders.get("items")
        for item in items:
            if item.get("status") == "refunded":
                order_info = await create_order_by_data(client, data, headers)
                break
            if item.get("status") == "captured":
                payment_mode, payment_mode_info, payment_id = (
                    await PaymentHelper().get_payment_mode_info(
                        item, request
                    )
                )
                payment_date = datetime.datetime.fromtimestamp(item.get("created_at"), datetime.timezone.utc)
                payment_attempt_info.update({
                    "status": "captured",
                    "captured_at": payment_date,
                    "created_at": payment_date,
                    "attempt_time": payment_date,
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "payment_mode": payment_mode,
                    "payment_mode_info": payment_mode_info
                })
                if promocode:
                    payment_attempt_info.update(promocode_update)
                if (
                    await DatabaseConfiguration().payment_collection.find_one(
                        {"payment_id": payment_id}
                    )
                ) is None:
                    data = {
                        "merchant": "RazorPay",
                        "user_id": student_id,
                        "details": {
                            "purpose": "studentApplication",
                            "application_id": application_id,
                        },
                        "error": {
                            "error_code": None,
                            "description": None,
                            "created_at": payment_date
                        }
                    }
                    data.update(payment_attempt_info)
                    await DatabaseConfiguration().payment_collection.insert_one(data)
                if (await DatabaseConfiguration().studentApplicationForms.find_one(
                        {"_id": application_id, "payment_info.payment_id": payment_id})) is None:
                    payment_info = application.get("payment_info", {})
                    payment_info.update(payment_attempt_info)
                    application.get("payment_attempts", []).insert(0, payment_attempt_info)
                    update_info = {
                        "payment_attempts": application.get("payment_attempts", []),
                        "payment_initiated": True,
                        "payment_info": payment_info
                    }
                    if (
                        await DatabaseConfiguration().studentApplicationForms.update_one(
                            {"_id": application_id}, {"$set": update_info}
                        )
                        is not None
                    ):
                        if (course := await DatabaseConfiguration().course_collection.find_one(
                            {"_id": ObjectId(application.get("course_id"))}
                        )) is None:
                            course = {}
                        await StudentApplicationHelper().update_stage(
                            str(student_id), course.get("course_name"),
                            7.50, application.get("spec_name1"), college_id=application.get("college_id")
                        )
                        toml_data = utility_obj.read_current_toml_file()
                        if toml_data.get("testing", {}).get("test") is False:
                            basic_details = student.get("basic_details", {})
                            background_tasks.add_task(
                                EmailActivity().payment_successful,
                                data={
                                    "payment_status": "success",
                                    "created_at": payment_date,
                                    "order_id": order_id,
                                    "payment_id": payment_id,
                                    "student_name": utility_obj.name_can(basic_details),
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
                                        else amount
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
                raise HTTPException(status_code=422, detail="Payment is captured.")
    return order_info


@payment_router.post("/create_order/")
@requires_feature_permission("write")
async def create_order(
    background_tasks: BackgroundTasks,
    testing: Is_testing,
    request: Request,
    application_id: str,
    current_user: CurrentUser,
    promocode: str = None,
    college: dict = Depends(get_college_id),
    payment_method: str = "As per Flow",
    payment_device: str = None,
    device_os: str = None,
):
    """ " "
    Create Order
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    application, course = await validate_details(application_id)
    if (
        student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"_id": application.get("student_id")}
        )
    ) is None:
        student = {}
    course_name = course.get("course_name")
    system_preference = college.get("system_preference")
    fee_rules = college.get("fee_rules")
    amount, preference_fee = course.get("fees"), None
    if system_preference and isinstance(system_preference, dict) and system_preference.get("preference") and application.get("preference_info", []):
        temp_preference_info = application.get("preference_info", [])
        amount, preference_fee = await StudentApplicationHelper().calculate_application_fee(
            temp_preference_info, fee_rules, course_name)
    else:
        amount = str(amount).replace('Rs.', '')
        amount = amount.replace('.0/-', '')
        amount = amount.replace('/-', '')
    temp_amount = int(amount)
    amount = int(f"{str(temp_amount)}00")
    student_id, application_id = application.get("student_id"), application.get("_id")
    data = {"amount": amount, "currency": "INR", "receipt": "#1"}

    headers, x_razorpay_account, client_id, client_secret = (
        await CollegeHelper().razorpay_header_update_partner(college)
    )
    client = razorpay.Client(auth=(client_id, client_secret))
    current_datetime = datetime.datetime.utcnow()
    payment_attempt_info = {
        "payment_id": "None",
        "status": "None",
        "attempt_time": current_datetime,
    }
    payment_extra_info = {
        "payment_device": payment_device,
        "device_os": device_os,
        "payment_method": payment_method,
        "payment_mode": "NA",
        "payment_mode_info": (await PaymentHelper().get_payment_mode_info({}, request))[1],
    }
    payment_attempt_info.update(payment_extra_info)
    if promocode:
        student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"_id": student_id}
        )
        promocode_validation = await promocode_vouchers_obj.verify_promocode_voucher(
            promocode, temp_amount, str(application_id), preference_fee
        )
        status = promocode_validation.get("status")
        temp_amount = int(promocode_validation.get("amount", 0))
        amount = int(f"{temp_amount}00")
        data.update({"amount": amount})
        if status in ["Invalid", "Not Applicable"]:
            raise HTTPException(status_code=404, detail=f"Promocode is {status}")
    promocode_update = {
        "payment_method": "Promocode",
        "used_promocode": promocode,
        "paid_amount": temp_amount
    }
    if (
        order_data := await DatabaseConfiguration().payment_collection.find_one(
            {"details.application_id": application_id, "order_amount": amount}
        )
    ) is not None:
        if application.get("payment_attempts") is None:
            application["payment_attempts"] = []
        if promocode:
            payment_attempt_info.update(promocode_update)
        order_info = await validate_existing_order_details(
            order_data, client, headers, data, request, payment_attempt_info, student_id, application, promocode_update,
            promocode, application_id, student, amount, college, background_tasks
        )
        application.get("payment_attempts", []).insert(0, payment_attempt_info)
        payment_attempt_info.update(
            {"order_id": order_info.get("id"), "status": order_info.get("status")}
        )
        update_info = {"payment_attempts": application.get("payment_attempts")}
    else:
        order_info = await create_order_by_data(client, data, headers)
        payment_doc = {
            "payment_id": "None",
            "order_id": order_info.get("id"),
            "merchant": "RazorPay",
            "user_id": student_id,
            "details": {
                "purpose": "StudentApplication",
                "application_id": application_id,
            },
            "status": "attempted",
            "attempt_time": current_datetime,
            "error": {
                "error_code": None,
                "description": None,
                "created_at": current_datetime,
            },
            "order_amount": amount,
        }
        payment_doc.update(payment_extra_info)
        if promocode:
            payment_doc.update(promocode_update)
        await DatabaseConfiguration().payment_collection.insert_one(payment_doc)
        payment_attempt_info.update(
            {"order_id": order_info.get("id"), "status": order_info.get("status")}
        )
        if promocode:
            payment_attempt_info.update(promocode_update)
        payment_info = application.get("payment_info", {})
        payment_info.update(payment_extra_info)
        update_info = {
            "payment_attempts": [payment_attempt_info],
            "payment_initiated": True,
            "payment_info": payment_info,
        }
        course_name = (
            f"{course.get('course_name')} in " f"{application.get('spec_name1')}"
            if (application.get("spec_name1") != "" and application.get("spec_name1"))
            else f"{course.get('course_name')} Program"
        )
        await DatabaseConfiguration().studentsPrimaryDetails.update_one({
            "_id": ObjectId(student_id)},
            {
                "$set": {"last_accessed": datetime.datetime.utcnow()}
            }
        )
        try:
            # TODO: Not able to add student timeline data
            #  using celery task when environment is
            #  demo. We'll remove the condition when
            #  celery work fine.
            if settings.environment in ["demo"]:
                StudentActivity().student_timeline(
                    student_id=str(student_id),
                    event_type="Payment",
                    event_status="Initiated",
                    message=f"{utility_obj.name_can(student.get('basic_details', {}))} "
                    f"Initiated Payment of "
                    f"Application Name: {course_name}",
                    college_id=str(application.get("college_id")),
                )
            else:
                if not is_testing_env():
                    StudentActivity().student_timeline.delay(
                        student_id=str(student_id),
                        event_type="Payment",
                        event_status="Initiated",
                        message=f"{utility_obj.name_can(student.get('basic_details', {}))} "
                        f"Initiated Payment of "
                        f"Application Name: {course_name}",
                        college_id=str(application.get("college_id")),
                    )
        except KombuError as celery_error:
            logger.error(
                f"error storing initiate payment" f" timeline data {celery_error}"
            )
        except Exception as error:
            logger.error(f"error storing initiate payment" f" timeline data {error}")
    await DatabaseConfiguration().studentApplicationForms.update_one(
        {"_id": application_id}, {"$set": update_info}
    )
    await utility_obj.update_notification_db(
        event="Payment started", application_id=application_id
    )
    order_info["amount"] = temp_amount
    return utility_obj.response_model(
        data=order_info, message="Order created successfully."
    )


@payment_router.get("/get_client_id")
@requires_feature_permission("read")
async def get_client_id(
    current_user: CurrentUser, college: dict = Depends(get_college_id)
):
    if (
            college_details := await DatabaseConfiguration().college_collection.find_one(
                {"_id": ObjectId(college.get("id"))}
            )
    ) is None:
        raise HTTPException(status_code=404, detail="Client details not found.")
    try:
        razorpay_details = college_details.get("razorpay", {})
        client_id = razorpay_details.get("razorpay_api_key")
        is_partner = razorpay_details.get("partner", False)
        data = {
            "client_id": client_id,
            # Adding this Statically as per Frontend Request currently Selecting Multiple Option is not Here in this PR.
            "payment_gateway": "RazorPay"
        }

        if is_partner:
            data.update(
                {
                    "account_id": razorpay_details.get("x_razorpay_account", ""),
                }
            )

    except BadRequestError as e:
        raise HTTPException(status_code=500, detail=str(e.args)[2:-3])

    return utility_obj.response_model(
        data=data, message="Client id fetched " "successfully."
    )


@payment_router.get("/order_details/{order_id}")
async def order_details(
    order_id: str = Path(..., description="Enter order id"),
    college: dict = Depends(get_college_id),
):
    """
    Returns the order details using order_id
    """
    headers, x_razorpay_account, client_id, client_secret = (
        await CollegeHelper().razorpay_header_update_partner(college)
    )
    client = razorpay.Client(auth=(client_id, client_secret))

    try:
        details = client.order.fetch(order_id, headers=headers)
    except BadRequestError as e:
        raise HTTPException(status_code=500, detail=str(e.args)[2:-3])
    return details["status"]


@payment_router.get("/payment_details/{payment_id}/")
async def payment_details(
    payment_id: str = Path(..., description="Enter payment id"),
    college: dict = Depends(get_college_id),
):
    """
    Returns the payment details
    """
    headers, x_razorpay_account, client_id, client_secret = (
        await CollegeHelper().razorpay_header_update_partner(college)
    )
    client = razorpay.Client(auth=(client_id, client_secret))
    try:
        details = client.payment.fetch(payment_id, headers=headers)
    except BadRequestError as e:
        raise HTTPException(status_code=500, detail=str(e.args)[2:-3])

    return details["status"]


@payment_router.post("/webhook/{college_id}/")
async def get_webhook_details(testing: Is_testing,
                              request: Request, college_id: str):
    """
    Returns the Webhook details
    """
    try:
        college = await get_college_id(college_id)
        request_data = await request.body()

        logger.debug(
            f"Request received with headers: {request.headers}, "
            f"body length: {len(request_data)}, College id: {college_id}"
        )

        logger.debug(f"Request data type: {type(request_data)}")

        received_signature = request.headers.get("x-razorpay-signature")
        if not received_signature:
            logger.error("Missing x-razorpay-signature in headers")
            raise HTTPException(status_code=400,
                                detail="Missing x-razorpay-signature")

        headers, x_razorpay_account, client_id, client_secret = (
            await CollegeHelper().razorpay_header_update_partner(college)
        )

        client = razorpay.Client(auth=(client_id, client_secret))
        verify_signature = client.utility.verify_webhook_signature(
            request_data.decode("utf-8"),
            received_signature,
            settings.razorpay_webhook_secret,
        )

        if not verify_signature:
            logger.error("Webhook signature verification failed.")
            raise HTTPException(status_code=400,
                                detail="Invalid webhook signature")

        logger.info("Webhook signature verified successfully.")

        # Parse request_data as JSON for further processing after verification
        request_data = json.loads(request_data)
    except razorpay.errors.SignatureVerificationError as error:
        logger.error(
            f"Razorpay signature verification failed. "
            f"Error: {str(error)}. "
            f"Error line#: {error.__traceback__.tb_lineno}."
        )
        raise HTTPException(status_code=400,
                            detail="Invalid webhook signature")
    except Exception as error:
        logger.exception(
            "An unexpected error occurred in the payment webhook API. Error: "
            f"{str(error)}. Error line#: {error.__traceback__.tb_lineno}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    await StudentPaymentActivity().update_payment_status(
        data=request_data, request=request, college=college
    )

    logger.info("Webhook processed successfully for college_id: %s",
                college_id)
    return {"status": "success"}


@payment_router.post("/manual_capture/", summary="Store manual payment data.")
@requires_feature_permission("write")
async def manual_payment(
    testing: Is_testing,
    request: Request,
    background_tasks: BackgroundTasks,
    application_id: str,
    payment_id: str,
    reason_type: str,
    current_user: CurrentUser,
    name: str | None = None,
    course_name: str | None = None,
    specialization_name: str | None = None,
    amount: str | None = None,
    reason_name: str | None = None,
    note: str | None = None,
    document_files: list[UploadFile] = [],
    college: dict = Depends(get_college_id),
    season: str = None,
    payment_device: str = None,
    device_os: str = None,
):
    """
    Store manual payment data.

    Params:
        - college_id (str): An unique identifier of a college.
            e.g., 123456789012345678901234

    Params:
        - application_id (str): An unique identifier of an application.
        - payment_id (str): An unique identifier of payment.
        - document_files (list[UploadFile]): A list of documents.
        - reason_type (PaymentReason): Type of payment reason like
            Campus visit, Outreach event, Payment by vendor,
            Join payment and Other.
        - reason_name (str): Reason name in-case of reason type
            `Other`.
        - note (str | None): Either None or string which represents
            note.

    Request body params:
        - document_files (list[UploadFile]): Default value: [], user can
            upload multiple files.

    Returns:
        - dict: A dictionary which contains payment successful information.

    Raises:
        - ObjectIdInValid: An error occurred when application_id not valid.
        - DataNotFoundError: An error occurred when application not found
            using id.
        - Exception: An error occurred when something wrong happen in the code.
    """
    current_datetime = datetime.datetime.utcnow()
    user = await UserHelper().is_valid_user(current_user)
    for file in document_files:
        if utility_obj.validate_document_format(file.filename) is False:
            raise HTTPException(
                status_code=422,
                detail=f"File `{file.filename}` format is not "
                f"supported. Expected formats: png, "
                f"jpg, jpeg and pdf",
            )
    try:
        if not testing:
            Reset_the_settings().check_college_mapped(college.get("id"))
        await PaymentHelper().update_payment_data_and_send_mail(
            application_id,
            document_files,
            payment_id,
            user,
            current_datetime,
            season,
            background_tasks,
            reason_type,
            reason_name,
            note,
            college,
            request,
            payment_device,
            device_os,
            name,
            course_name,
            specialization_name,
            amount
        )
        return {"message": "Payment is captured through offline way."}
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"An internal error occurred: " f"Error - {error}"
        )


@payment_router.post(
    "/send_receipt_through_mail/", summary="Send payment receipt through mail."
)
@requires_feature_permission("write")
async def send_payment_receipt_through_mail(
    request: Request,
    testing: Is_testing,
    background_tasks: BackgroundTasks,
    application_id: str,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id),
    season: str = None,
):
    """
    Send receipt through mail.

    Params:
        - college_id (str): An unique identifier of a college.
            e.g., 123456789012345678901234

    Params:
        - application_id (str): An unique identifier of an application.


    Returns:
        - dict: A dictionary which contains message regarding payment receipt
            send thorugh mail.

    Raises:
        - Exception: An error occurred when something wrong happen in the code.
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    user = await UserHelper().is_valid_user(current_user)
    application = await StudentApplicationHelper().get_application_data(application_id)
    if (
        student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"_id": ObjectId(application.get("student_id"))}
        )
    ) is None:
        return {
            "message": "Student data not found to send payment receipt " "through mail."
        }
    if not testing:
        payment_info = application.get("payment_info", {})
        payment_method = payment_info.get("payment_method", "As per Flow")
        invoice_document = None
        if payment_method == "Offline":
            invoice_documents = application.get("document_files", [])
            if invoice_documents:
                invoice_document = invoice_documents[0].get("public_url")
        else:
            if (
                payment_invoice := await DatabaseConfiguration().application_payment_invoice_collection.find_one(
                    {"application_number": application.get("custom_application_id")}
                )
            ) is not None:
                invoice_document = payment_invoice.get("invoice_url")
        try:
            if invoice_document:
                if college.get("key_categories"):
                    college.pop("key_categories")
                await send_mail_config().send_payment_receipt_to_user(
                    invoice_document,
                    college,
                    user,
                    request,
                    student.get("user_name"),
                    utility_obj.name_can(student.get("basic_details", {})),
                    (
                        "counselor"
                        if user.get("role", {}).get("role_name") == "college_counselor"
                        else "system"
                    ),
                    season=season,
                )
                return {"message": "Payment receipt send to user over mail."}
            return {"message": "Payment receipt not found to send it over mail."}
        except ObjectIdInValid as error:
            raise HTTPException(status_code=422, detail=error.message)
        except DataNotFoundError as error:
            raise HTTPException(status_code=404, detail=error.message)
        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail=f"An internal error occurred: " f"Error - {error}",
            )
    return {"detail": "Not able to send mail in the case testing environment."}
