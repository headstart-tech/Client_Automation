"""
This file contains APIs regarding promo code and vouchers
"""
import datetime

from bson import ObjectId
from fastapi.encoders import jsonable_encoder

from app.background_task.admin_user import DownloadRequestActivity
from app.core.log_config import get_logger
from fastapi import APIRouter, Body, Depends, Path, Query, Request, HTTPException, BackgroundTasks

from app.core.utils import utility_obj, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import CurrentUser, Is_testing
from app.helpers.promocode_voucher_helper.promocode_vouchers_helper import promocode_vouchers_obj
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.applications import DateRange
from app.models.promocode_vouchers_schema import create_promocode_payload, update_promocode, CreateVoucherPayload, \
    UpdateVoucher
from app.models.student_user_schema import ChangeIndicator
from app.s3_events.s3_events_configuration import upload_csv_and_get_public_url

logger = get_logger(name=__name__)
promocode_vouchers = APIRouter()


@promocode_vouchers.post("/create_promocode/")
@requires_feature_permission("write")
async def create_promocode(
        payload: create_promocode_payload,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    API to create promo code
    Params:
        - payload (dict): Contains information about promo code that is to be created
        - current_user (str): The email id of current user
        - college (dict): The college details
    Return (dict): A dict that has message of successful creation of promocode
    Raises:
        - Exception : An error occurred when something wrong happen in the code.
    """

    user = await UserHelper().is_valid_user(user_name=current_user)
    if user.get("role", {}).get("role_name") not in ["college_super_admin", "college_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    if payload is None:
        payload = {}
    payload = jsonable_encoder(payload)
    try:
        return await promocode_vouchers_obj.create_promocode(payload, user)
    except Exception as e:
        logger.error("An error occurred while creating promo code")
        raise HTTPException(
            status_code=500, detail=f"An error occurred while creating promo code. Error - {e}")


@promocode_vouchers.post("/get_promocodes/")
@requires_feature_permission("read")
async def get_promocodes(
        background_tasks: BackgroundTasks,
        request: Request,
        current_user: CurrentUser,
        page_num: int | None = None,
        page_size: int | None = None,
        date_range: DateRange = Body(None),
        download: bool = Body(False),
        season: str = Body(None),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get all the promocodes.

    Params:\n
        - page_num (int | None): Either None or page number which is required for pagination.
        - page_size (int | None): Either None or page size which is required for pagination.
        - date_range (dict): The daterange filter if required.
        - season (str): season is given if want to return season wise data.
        - college (dict): check college id and get college information.
        - download (bool): True if want to download the details else false.

    Returns:\n
        - (dict): This has result along with pagination

    Raises:\n
        - Exception - An Unexpected error raised from the code.
    """
    user = await UserHelper().is_valid_user(user_name=current_user)
    try:
        if date_range:
            date_range = jsonable_encoder(date_range)
        result, total = await promocode_vouchers_obj.get_all_promocodes(page_num, page_size, date_range, download)
        if download:
            current_datetime = datetime.datetime.utcnow()
            data_keys = list(result[0].keys())
            get_url = await upload_csv_and_get_public_url(
                fieldnames=data_keys, data=result, name="applications_data"
            )
            background_tasks.add_task(
                DownloadRequestActivity().store_download_request_activity,
                request_type="Get promocodes", requested_at=current_datetime,
                ip_address=utility_obj.get_ip_address(request),
                user=user,
                total_request_data=1, is_status_completed=True,
                request_completed_at=datetime.datetime.utcnow())
            return get_url
        response = {"pagination": None}
        if page_num and page_size:
            response = await utility_obj.pagination_in_aggregation(
                page_num, page_size, total,
                route_name="/promocode_vouchers/get_promocodes/"
            )
        return {
            "data": result,
            "total": total,
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Get all promocodes",
        }
    except Exception as e:
        logger.error(f"Some unexpected error while trying to fetch all promocodes: {e}")
        raise HTTPException(status_code=500, detail=str(e.args))


@promocode_vouchers.post("/update_promocode/")
@requires_feature_permission("edit")
async def update_edit_promocodes(
        current_user: CurrentUser,
        _id: str,
        payload: update_promocode = Body(None),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    update or edit promocode
    Params:
        - current_user: username of current user
        - duration (dict): The change in duration that is needed to update
        - units (int): The units that is to be updated
        - status_value (str): The status values that is being changed
        - status (bool): True if need to change the status False if need to change the duration
        - college (dict): check college id and get college information
    Returns:
        (dict): A message that the required fields are changed
    Raises:
        None
    """
    user = await UserHelper().is_valid_user(user_name=current_user)
    if user.get("role", {}).get("role_name") not in ["college_super_admin", "college_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    if payload:
        payload = jsonable_encoder(payload)
    await promocode_vouchers_obj.update_edit_promocode(_id, payload)
    return {
        "message": "Updated successfully!"
    }


@promocode_vouchers.post("/get_applied_students/")
@requires_feature_permission("read")
async def get_applied_students(
        current_user: CurrentUser,
        page_num: int,
        page_size: int,
        promocode_id: str,
        program_name: list = Body(None),
        search: str = Body(None),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    API to get applied students info
    Params:
        - current_user: username of current user.
        - promocode_id (str): Unique id of promocode.
        - college (dict): Check college id and get college information.
    """
    await UserHelper().is_valid_user(user_name=current_user)
    result, total = await promocode_vouchers_obj.get_applied_students(promocode_id, page_num, page_size, program_name, search)
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total,
        route_name="/promocode_vouchers/get_applied_students/"
    )
    return {
        "data": result,
        "total": total,
        "count": page_size,
        "pagination": response["pagination"],
        "message": "Get applied students info",
    }


@promocode_vouchers.post("/create_voucher/")
@requires_feature_permission("write")
async def create_voucher(
        payload: CreateVoucherPayload,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Create voucher payload
    Params:
        - payload (dict): Contains information about voucher that is to be created
        - current_user (str): The email id of current user
        - college (dict): The college details
    Return (dict): A dict that has message of successful creation of voucher
    Raises:
        - Exception : An error occurred when something wrong happen in the code.
    """
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") not in ["college_super_admin", "college_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    if payload is None:
        payload = {}
    payload = jsonable_encoder(payload)
    try:
        await promocode_vouchers_obj.create_voucher(payload, user)
        return {
            "message": "Created voucher successfully!"
        }
    except Exception as e:
        logger.error("An error occurred while creating promo code")
        raise HTTPException(
            status_code=500, detail=f"An error occurred while creating promo code. Error - {e}")


@promocode_vouchers.post("/get_vouchers/")
@requires_feature_permission("read")
async def get_vouchers(
        background_tasks: BackgroundTasks,
        request: Request,
        current_user: CurrentUser,
        page_num: int,
        page_size: int,
        date_range: DateRange = Body(None),
        program_name: list = Body(None),
        download: bool = Body(False),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get voucher details
    Params:
        - CurrentUser (str): The email id of current user.
        - date_range (DateRange): Date range filter. It has start_date and end_date values
        - Program_name (list): List of dicts. It has values course_id, course_specialization
        - college (dict): Details of college
    Returns:
        dict - Details of all vouchers
    """
    user = await UserHelper().is_valid_user(current_user)
    publisher = None
    if user.get("role", {}).get("role_name") in ["college_publisher_console"]:
        publisher = ObjectId(user.get("_id"))
    if date_range is None:
        date_range = {}
    date_range = jsonable_encoder(date_range)
    result, total = await promocode_vouchers_obj.get_all_vouchers(page_num, page_size, date_range, program_name, publisher, download)
    if download:
        current_datetime = datetime.datetime.utcnow()
        data_keys = list(result[0].keys())
        get_url = await upload_csv_and_get_public_url(
            fieldnames=data_keys, data=result, name="applications_data"
        )
        background_tasks.add_task(
            DownloadRequestActivity().store_download_request_activity,
            request_type="Get vouchers", requested_at=current_datetime,
            ip_address=utility_obj.get_ip_address(request),
            user=user,
            total_request_data=1, is_status_completed=True,
            request_completed_at=datetime.datetime.utcnow())
        return get_url
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total,
        route_name="/promocode_vouchers/get_vouchers/"
    )
    return {
        "data": result,
        "total": total,
        "count": page_size,
        "pagination": response["pagination"],
        "message": "Get vouchers!",
    }


@promocode_vouchers.post("/update_voucher/")
@requires_feature_permission("edit")
async def update_voucher(
        current_user: CurrentUser,
        voucher_id: str,
        payload: UpdateVoucher = Body(None),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Update voucher
    Params:
        - current_user: username of current user
        - duration (dict): The change in duration that is needed to update
        - units (int): The units that is to be updated
        - status_value (str): The status values that is being changed
        - status (bool): True if need to change the status False if need to change the duration
        - college (dict): check college id and get college information
    Returns:
        (dict): A message that the required fields are changed
    Raises:
        None
    """
    user = await UserHelper().is_valid_user(user_name=current_user)
    if user.get("role", {}).get("role_name") not in ["college_super_admin", "college_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    if payload:
        payload = jsonable_encoder(payload)
    await promocode_vouchers_obj.update_voucher(voucher_id, payload)
    return {
        "message": "Updated successfully!"
    }


@promocode_vouchers.post("/get_voucher_details/")
@requires_feature_permission("read")
async def get_voucher_details(
        page_num: int,
        page_size: int,
        voucher_id: str,
        current_user: CurrentUser,
        sort: bool = Body(None),
        sort_name: str = Body(None),
        sort_type: str = Body(None),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get particular voucher details
    Params:
        - current_user: username of current user
        - page_num (int): Page number for pagination purpose
        - page_size (int): Page size for pagination purpose
        - sort (bool): True if need to sort else false
        - sort_name (str): This can have two values student_name/status
        - sort_type (str): This can have two values asc/dsc
        - voucher_id (str): The unique id of voucher
        - college (dict): check college id and get college information
    Returns:
        (dict): All voucher details along with pagination information
    Raises:
        None
    """
    await UserHelper().is_valid_user(user_name=current_user)
    result, total = await promocode_vouchers_obj.get_voucher_details(voucher_id, page_num, page_size, sort, sort_name, sort_type)
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total,
        route_name="/promocode_vouchers/get_voucher_details/"
    )
    return {
        "data": result,
        "total": total,
        "count": page_size,
        "pagination": response["pagination"],
        "message": "Get voucher details",
    }


@promocode_vouchers.post("/get_quick_view/")
@requires_feature_permission("read")
async def get_quick_view(
        current_user: CurrentUser,
        change_indicator: ChangeIndicator = "last_7_days",
        date_range: DateRange = Body(None),
        season: str = Body(None),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get quick view details
    Params:
        - Current user (str): The email id of current user
        - unused (str): Get unused count of promocode/vouchers
        - change_indicator (str): Change indicator value. This can have 3 values last_7_days/last_15_days/last_30_days
        - date_range (DateRange): Date range filter. It has start date and end date in it
        - season (str): If required season wise data
        - college (dict): Current college details
    Returns:
        - dict: Details of quick view
    """
    await UserHelper().is_valid_user(current_user)
    if date_range is None:
        date_range = {}
    date_range = jsonable_encoder(date_range)
    data = await promocode_vouchers_obj.get_quick_view(date_range, change_indicator)
    return {
        "data": data,
        "message": "Get quick view details!"
    }


@promocode_vouchers.post("/delete_promocode_voucher/")
@requires_feature_permission("delete")
async def delete_promocode_voucher(
        current_user: CurrentUser,
        promocode: bool,
        ids: list = Body(),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Delete promocode or voucher
    Params:
        - current_user (str): The email id of current user.
        - promocode (bool): True if want to delete promocode else false
        - ids (list): list of unique ids of promocode/vouchers that are to be deleted.
        - college (dict): Current college details
    Returns:
        - dict : message that promocode/voucher is deleted
    """
    user = await UserHelper().is_valid_user(user_name=current_user)
    if user.get("role", {}).get("role_name") not in ["college_super_admin", "college_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    ids = [ObjectId(id) for id in ids if await utility_obj.is_id_length_valid(_id=id,
                                                                              name="Id")]
    try:
        if promocode:
            await DatabaseConfiguration().promocode_collection.delete_many({"_id": {"$in": ids}})
            return {
                "message": "Successfully deleted promocode!"
            }
        else:
            await DatabaseConfiguration().voucher_collection.delete_many({"_id": {"$in": ids}})
            return {
                "message": "Successfully deleted vouchers!"
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong in delete promocode/voucher. Error-{e}",
        )


@promocode_vouchers.post("/verify_promocode_voucher/")
@requires_feature_permission("read")
async def verify_promocode_voucher(
        current_user: CurrentUser,
        application_id: str,
        course_fee: int,
        code: str,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        preference_fee: int | None = None
):
    """
    Verify the existance of given promocode or voucher
    Params:
        - application_id (str): The unique id of application.
        - code (str): The code of promocode/voucher
        - course_fee (int): The course fee of particular application
        - code (str): The unique code that is to be checked
        - college (dict): Details of college
    Returns:
        - dict (details of given code. It has status, discount, code, amount)
    Raises:
        - Exception: An error occurred with status code 500 when something happen wrong backend code at the time of verify promocode/voucher.
    """
    if (student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": current_user.get("user_name")})) is None:
        raise HTTPException(status_code=404, detail="Username not found")
    await utility_obj.is_id_length_valid(_id=application_id,
                                         name="Application id")
    if (await DatabaseConfiguration().studentApplicationForms.find_one({"_id": ObjectId(application_id)})) is None:
        raise HTTPException(status_code=404, detail="Application not found")
    try:
        data = await promocode_vouchers_obj.verify_promocode_voucher(code, course_fee, application_id, preference_fee)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong when verifying promocode/voucher. Error-{e}",
        )


@promocode_vouchers.post("/payment_through_code/")
@requires_feature_permission("write")
async def payment_through_code(
    current_user: CurrentUser,
    testing: Is_testing,
    application_id: str,
    code: str,
    code_type: str,
    course_fee: int,
    payment_device: str = None,
    device_os: str = None,
    college: dict = Depends(get_college_id)
):
    """
    This API is used to do payment through code (voucher code/ promocode with full discount)
    Params:
        - current_user (str): The email id of current user
        - college (dict): Details of college
        - application_id (str): The unique of application id
        - code (str): The unique code
        - code_type (str): This can have two values (promocode/voucher)
        - course_fee (int): The course fee on which promocode is applied
        - payment_devise (str): The payment device through which payment is done
        - devise_os (str): The devise os of lead where payment is done
    Returns:
        - (dict): Sample message that voucher is applied nd payment is done
    Raises:
        - Exception: An error occurred with status code 500 when something happen wrong backend code at the time of applying voucher code
    """
    if (student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"user_name": current_user.get("user_name")})) is None:
        raise HTTPException(status_code=404, detail="Username not found")
    await promocode_vouchers_obj.payment_through_code(application_id, code, student, college, testing, code_type,
                                                      payment_device, device_os, course_fee)
    return {
        "message": "Code applied and payment done successfully"
    }
