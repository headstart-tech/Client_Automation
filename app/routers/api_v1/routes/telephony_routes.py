"""
This file contains APIs related to telephony integration in CRM.
"""

from urllib.parse import parse_qs

from bson.objectid import ObjectId
from fastapi import APIRouter, Request, Depends, Body
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException

from app.core.custom_error import CustomError, ObjectIdInValid
from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import cache_dependency, insert_data_in_cache
from app.dependencies.oauth import CurrentUser
from app.helpers.telephony.assigned_counsellor_helper import AssignedCounsellor
from app.helpers.telephony.call_assigned_helper import ApplicationAssigned
from app.helpers.telephony.call_end_helper import CallEndHelper
from app.helpers.telephony.call_initiate_helper import CallInitiateHelper
from app.helpers.telephony.check_in_out_helper import CheckInOutHelper
from app.helpers.telephony.checkout_reason_helper import CheckOutReasonList
from app.helpers.telephony.counsellor_call_activity_helper import CallActivity
from app.helpers.telephony.download_call_recording_helper import CallRecording
from app.helpers.telephony.call_info_table_helper import CallInfo
from app.helpers.telephony.call_quality_table_helper import CallQuality
from app.helpers.telephony.get_user_list_helper import UserListHelper
from app.helpers.telephony.inbound_call_summary_helper import \
    InboundCallSummary
from app.helpers.telephony.counsellor_call_log_helper import CounsellorCallLog
from app.helpers.telephony.missed_call_dashboard_header_helper import (
    MissedCallDashboard,
)
from app.helpers.telephony.missed_call_data_helper import MissedCallSummary
from app.helpers.telephony.outbound_call_summary_helper import \
    OutboundCallSummary
from app.helpers.telephony.telephony_dashboard_helper import TelephonyDashboard
from app.helpers.telephony.telephony_webhook_helper import TelephonyWebhook
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.check_in_out_schema import (
    CheckInOut,
    CallInitiateDetail,
    CallDisposeData,
    ApplicationCallInfo,
    MultipleCheckInOut,
    AssignedCounsellorOnMissedCall,
)
from app.models.student_user_schema import User, DateRange, ChangeIndicator
from app.s3_events.s3_events_configuration import upload_csv_and_get_public_url

telephony = APIRouter()
logger = get_logger(name=__name__)


@telephony.post("/webhook", summary="Webhook API for store response data from " "MCube")
async def check_response(
    request: Request, college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """\nGet data from telephony and save it accordangly.\n\n

    Params:\n
        request (Request): Payload data sent by telephony\n\n

    Returns:\n
        dict: Response message for telephony\n
    """
    Reset_the_settings().check_college_mapped(college.get("id"))
    try:

        logger.info("########### Telephony webhook call by MCube ###########")
        raw_body = await request.body()
        logger.info(f"Raw data - {raw_body}")
        decoded_data_str = parse_qs(raw_body.decode("utf-8"))
        data_dict_str = decoded_data_str["data"][0]
        data = eval(data_dict_str)
        logger.info(f"Data - {data}")
        response = await TelephonyWebhook().update_websocket_data(data)
        return response
    except Exception as error:
        logger.error(
            "An error got when sending the telephony data through webhook by mcube."
        )
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@telephony.get(
    "/get_checkout_reasons", summary="Get list of all telephony check-out reasons"
)
@requires_feature_permission("read")
async def get_telephony_checkout_reasons(
    current_user: CurrentUser,
    cache_data=Depends(cache_dependency),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """\n
    Get all the telephony checkout reasons.\n\n

    Params:\n
        - college_id (str): An unique identifier of a college. e.g., 123456789012345678901234\n\n

    Returns:\n
        - dict: A dictionary which contains list of checkout reasons along with successful message.
    """
    cache_key, data = cache_data
    if data:
        return data

    reason_data = await CheckOutReasonList().get_reason_helper()

    data = utility_obj.response_model(reason_data, "Check-out reason data list.")

    if cache_key:
        await insert_data_in_cache(cache_key, data, expiration_time=30)

    return data


@telephony.post("/check_in_or_out", summary="API for telephony check-in or check-out")
@requires_feature_permission("edit")
async def check_in_or_out(
    check_in_out: CheckInOut,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """\nAPI for updating the status of telephony check-in "Active" or "Inactive"\n\n

    Params:\n
        check_in_out (CheckInOut): Payload schema for check-in -> Active or Inactive\n
        current_user (User, optional): Current requested user. Defaults to Depends(get_current_user).\n
        college (dict, optional): College unique id. Defaults to Depends(get_college_id).\n\n

    Returns:\n
        dict: Return response message.
    """
    user = await UserHelper().is_valid_user(current_user)
    check_in_out_data = jsonable_encoder(check_in_out)

    if check_in_out_data.get("check_in_status") == False:
        if check_in_out_data.get("reason") == None:
            raise CustomError("Reason must be specified in case of check-in inactive.")

    try:

        if user.get("role").get("role_name") in [
            "college_counselor",
            "college_head_counselor",
            "moderator",
        ]:
            return await CheckInOutHelper().update_check_status(user, check_in_out_data)

        else:
            raise CustomError("You are not allowed for updation.")

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(f"An error got when update check-in status. Error - {error}")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@telephony.post(
    "/multiple_check_in_or_out",
    summary="API for multiple users telephony check-in or check-out",
)
@requires_feature_permission("edit")
async def multiple_check_in_or_out(
    multiple_check_in_out: MultipleCheckInOut,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """\nAPI for updating the multiple status of telephony check-in "Active" or "Inactive"\n\n

    Params:
        multiple_check_in_out (MultipleCheckInOut) Parameters:
            - counsellor_ids (List[str]): List of counsellor ids which has to be active or inactive.
            - check_in_out (dict): Check in out data. Parameters:
                - check_in_status (bool): True for `Checked-In` or False represents `Checked-Out`.
                - reason (dict, optional): Mandatory if check_in_status will false only. Parameters:
                    - title (str): Title of reason.
                    - icon (str, optional): Icon of reason.
                college_id (str): Unique identifier/id of a college which useful for get college data.

    Returns:
    - dict: A dictionary which contains information about check in/out status update.

    Raises:
        - 401: An error occurred with status code 401 when user don't have permission to access/use API.
        - ObjectIdInValid: An error occurred with status code 422 when send wrong counselor_id.
        - CustomError: An error occurred with status code 400 when something improper condition happen.
        - Exception: An error occurred with status code 500 when something wrong happen in the backend code.
    """
    user = await UserHelper().is_valid_user(current_user)
    check_in_out_data = jsonable_encoder(multiple_check_in_out)

    try:

        if user.get("role", {}).get("role_name", "") not in [
            "college_admin",
            "college_super_admin",
            "super_admin",
        ]:
            raise HTTPException(status_code=401, detail="permission denied")

        for counsellor_id in check_in_out_data.get("counsellor_ids", []):
            if (
                user := await DatabaseConfiguration().user_collection.find_one(
                    {"_id": ObjectId(counsellor_id)}
                )
            ) and user.get("role", {}).get("role_name", "") != "college_counselor":
                raise ValueError(f"Invalid counsellor id = {str(user.get('_id'))}")

        if check_in_out_data.get("check_in_out", {}).get("check_in_status") == False:
            if check_in_out_data.get("check_in_out", {}).get("reason") == None:
                raise CustomError(
                    "Reason must be specified in case of check-in inactive."
                )

        for counsellor_id in check_in_out_data.get("counsellor_ids", []):
            user = await DatabaseConfiguration().user_collection.find_one(
                {"_id": ObjectId(counsellor_id)}
            )
            await CheckInOutHelper().update_check_status(
                user, check_in_out_data.get("check_in_out", {})
            )
        return {"message": "Multiple Check-in status update successfully."}

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(
            f"An error got when update multiple check-in status. Error - {error}"
        )
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@telephony.put("/dashboard_header", summary="Dashboard header")
@requires_feature_permission("read")
async def dashboard_header(
    current_user: CurrentUser,
    date_range: DateRange | None = Body(None),
    change_indicator: ChangeIndicator = "last_7_days",
    cache_data=Depends(cache_dependency),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """
    \nGet telephony dashboard header data.\n

    Params:\n
        - change_indicator (ChangeIndicator): An object of class `ChangeIndicator` which useful for show percentage comparison. By default showing "last_7_days" comparison of data. Possible values: last_7_days, last_15_days and last_30_days.
        - college_id (str): An unique identifier/id of a college which useful for get college data. e.g., "123456789012345678901234"

    Request body params:\n
        - date_range (DateRange | None): Either None or an instance of class `DateRange` which contains following fields:
            - start_date (str): Start date which useful for get telephony header data according to start date.
            - end_date (str): End date which useful for get telephony header data according to end date.

    Returns:\n
        - dict: A dictionary which contains telephony header data.

    Raises:\n
        - Exception: An error occurred with status code 500 when something wrong happen in the backend code.
    """
    date_range = await utility_obj.format_date_range(date_range)
    cache_key, data = cache_data
    if data:
        return data
    if (
        user := await DatabaseConfiguration().user_collection.find_one(
            {"user_name": current_user.get("user_name")}
        )
    ) is None or user.get("role", {}).get("role_name", "") not in [
        "college_admin",
        "college_super_admin",
        "super_admin",
        "college_counselor",
        "college_head_counselor",
    ]:
        raise HTTPException(status_code=401, detail="permission denied")

    try:
        response = await TelephonyDashboard().header_data_helper(
            date_range=date_range, change_indicator=change_indicator
        )
        data = {"data": response, "message": "Telephony dashboard header data."}
    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the telephony dashboard header data. Error: {error}.",
        )
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@telephony.post(
    "/initiate_call", summary="Initiate call by using CTA button by counsellor"
)
@requires_feature_permission("write")
async def initiate_telephony_call(
    call_initiate: CallInitiateDetail,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """API to initiate call to lead by counsellor, head counsellor or moderator\n\n

    Params:\n
        - college_id (str): An unique identifier/id of a college which useful for get college data.

    Request body params:\n
        - call_initiate (CallInitiateDetail): An instance of class `CallInitiateDetail` which contains following fields:
            - dialed_phone_number (str | None): Mobile number of student in the following format: "+91XXXXXXXXXX"
            - application id (str | None): An unique identifier/id of application. e.g., "123456789012345678901234"

    Returns:\n
        - dict: A dictionary which contains call initiation data.

    Raises:\n
        - ObjectIdInValid: An error occurred with status code 422 when application id will be wrong.
        - CustomError: An error occurred with status code 400 when invalid data passed.
        - Exception: An error occurred with status code 500 when something wrong happen in the backend code.
    """
    user = await UserHelper().is_valid_user(current_user)
    call_initiate = jsonable_encoder(call_initiate)

    try:
        return await CallInitiateHelper().initiate_call(
            user, call_initiate, college.get("id")
        )

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(f"An error got when call initiated. Error - {error}")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@telephony.post(
    "/save_and_dispose",
    summary="Dispose popup after call end by updating with application.",
)
@requires_feature_permission("write")
async def save_and_dispose(
    call_end_payload: CallDisposeData,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """API for call end dispose popup and save application as per call.\n\n

    Params:\n
        - college (str): An unique identifier/id of a college which useful for get college data.

    Request body params:\n
        - call_end_payload (CallDisposeData): An instance of class `CallDisposeData` which contains following fields:
            - call_id (str): Call unique id (_id) pass through popup websocket array
            - application_id (str): An unique identifier/id of application. e.g., "123456789012345678901234"

    Returns:\n
        - dict: A dictionary which contains status message.

    Raises:\n
        - ObjectIdInValid: An error occurred with status code 422 when application id will be wrong.
        - CustomError: An error occurred with status code 400 when invalid data passed.
        - Exception: An error occurred with status code 500 when something wrong happen in the backend code.
    """
    user = await UserHelper().is_valid_user(current_user)
    call_end = jsonable_encoder(call_end_payload)

    try:
        if await DatabaseConfiguration().call_activity_collection.find_one(
            {"_id": ObjectId(call_end.get("call_id"))}
        ):
            return await CallEndHelper().popup_dispose_on_call_end_helper(
                user, call_end
            )

        else:
            raise HTTPException(
                status_code=404, detail="Invalid call_id or application_id in payload."
            )

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(f"An error got when call end dispose popup. Error - {error}")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@telephony.post("/outbound_call_log", summary="Get list of outbound calls")
@requires_feature_permission("read")
async def get_outbound_calls_list(
    current_user: CurrentUser,
    dialed_by: list[str] | None = None,
    call_status: str | None = None,
    page_num: int = 1,
    page_size: int = 10,
    date_range: DateRange | None = Body(None),
    search: str = Body(None),
    sort: bool = Body(None),
    sort_name: str = Body(None),
    sort_type: str = Body(None),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """Outbound call list API for communication summary module.\n\n

    Params:\n
        dialed_by (list[str] | None, optional): List of dialer user id's. Defaults to None.
        call_status (str | None, optional): It must be `Answered` or `Not Answered`. Defaults to None.
        page_num (int, optional): No. of page. Defaults to 1.
        page_size (int, optional): Count of data in one page. Defaults to 10.
        date_range (DateRange, optional): Apply date range for filter the data. Defaults to Body(None).
        search (str, optional): Search key for filteration. Defaults to Body(None).
        sort (bool, optional): Is sort apply on the data or not (True/False). Defaults to Body(None).
        sort_name (str, optional): Field name must be ['Call status', 'Duration', 'Dialed by']. Defaults to Body(None).
        sort_type (str, optional): It must be `asc` or `desc`. Defaults to Body(None).
        current_user (User, optional): Current user details. Defaults to Depends(get_current_user).
        college (dict, optional): College unique id. Defaults to Depends(get_college_id).

    Returns:\n
        dict: List of calls data.
    """
    date_range = await utility_obj.format_date_range(date_range)
    user = await UserHelper().is_valid_user(user_name=current_user)

    if user.get("role", {}).get("role_name") in [
        "college_admin",
        "college_super_admin",
        "super_admin",
    ]:
        data, count = await OutboundCallSummary().outbound_calls(
            dialed_by,
            call_status,
            date_range,
            search,
            sort,
            sort_name,
            sort_type,
            page_num,
            page_size,
        )

    elif user.get("role", {}).get("role_name") == "college_head_counselor":
        allowed_counsellor_list = [
            str(counsellor.get("_id"))
            for counsellor in await DatabaseConfiguration()
            .user_collection.aggregate(
                [{"$match": {"head_counselor_id": ObjectId(user.get("_id"))}}]
            )
            .to_list(None)
        ]
        allowed_counsellor_list.append(user.get("_id"))
        if dialed_by == []:
            dialed_by = allowed_counsellor_list

        elif set(dialed_by) - set(allowed_counsellor_list) == []:
            data, count = await OutboundCallSummary().outbound_calls(
                dialed_by,
                call_status,
                date_range,
                search,
                sort,
                sort_name,
                sort_type,
                page_num,
                page_size,
            )
        else:
            raise ValueError("Don't have enough permission to see other users data.")

    else:
        dialed_by = [user.get("_id")]
        data, count = await OutboundCallSummary().outbound_calls(
            dialed_by,
            call_status,
            date_range,
            search,
            sort,
            sort_name,
            sort_type,
            page_num,
            page_size,
        )

    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, count, "/telephony/outbound_call_log"
    )
    return {
        "data": data,
        "total": count,
        "count": page_size,
        "pagination": {
            "next": response.get("pagination", {}).get("next"),
            "previous": response.get("pagination", {}).get("previous"),
        },
        "message": "Get Calls",
    }


@telephony.post("/inbound_call_log", summary="Get list of inbound calls")
@requires_feature_permission("read")
async def get_outbound_calls_list(
    current_user: CurrentUser,
    answered_by: list[str] | None = None,
    call_status: str | None = None,
    page_num: int = 1,
    page_size: int = 10,
    date_range: DateRange | None = Body(None),
    search: str = Body(None),
    sort: bool = Body(None),
    sort_name: str = Body(None),
    sort_type: str = Body(None),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """\nInbound call list API for communication summary module.\n\n

    Params:\n
        answered_by (list[str] | None, optional): List of receiver user id's. Defaults to None.
        call_status (str | None, optional): It must be `Answered` or `Not Answered`. Defaults to None.
        page_num (int, optional): No. of page. Defaults to 1.
        page_size (int, optional): Count of data in one page. Defaults to 10.
        date_range (DateRange, optional): Apply date range for filter the data. Defaults to Body(None).
        search (str, optional): Search key for filteration. Defaults to Body(None).
        sort (bool, optional): Is sort apply on the data or not (True/False). Defaults to Body(None).
        sort_name (str, optional): Field name must be ['Answered by', 'Landing number', 'Call status', 'Duration']. Defaults to Body(None).
        sort_type (str, optional): It must be `asc` or `desc`. Defaults to Body(None).
        current_user (User, optional): Current user details. Defaults to Depends(get_current_user).
        college (dict, optional): College unique id. Defaults to Depends(get_college_id).

    Returns:\n
        dict: List of calls data.
    """

    date_range = await utility_obj.format_date_range(date_range)
    user = await UserHelper().is_valid_user(user_name=current_user)

    if user.get("role", {}).get("role_name") in [
        "college_admin",
        "college_super_admin",
        "super_admin",
    ]:
        data, count = await InboundCallSummary().inbound_calls(
            answered_by,
            call_status,
            date_range,
            search,
            sort,
            sort_name,
            sort_type,
            page_num,
            page_size,
        )

    elif user.get("role", {}).get("role_name") == "college_head_counselor":
        allowed_counsellor_list = [user.get("_id")].extend(
            [
                str(counsellor.get("_id"))
                for counsellor in await (
                    DatabaseConfiguration().user_collection.aggregate(
                        {"$match": {"head_counselor_id": ObjectId(user.get("_id"))}}
                    )
                ).to_list(
                    None
                )
            ]
        )
        if answered_by == []:
            answered_by = allowed_counsellor_list

        elif set(answered_by) - set(allowed_counsellor_list) == []:
            data, count = await InboundCallSummary().inbound_calls(
                answered_by,
                call_status,
                date_range,
                search,
                sort,
                sort_name,
                sort_type,
                page_num,
                page_size,
            )
        else:
            raise ValueError("Don't have enough permission to see other users data.")

    else:
        data, count = await InboundCallSummary().inbound_calls(
            answered_by,
            call_status,
            date_range,
            search,
            sort,
            sort_name,
            sort_type,
            page_num,
            page_size,
        )

    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, count, "/telephony/inbound_call_log"
    )
    return {
        "data": data,
        "total": count,
        "count": page_size,
        "pagination": {
            "next": response.get("pagination", {}).get("next"),
            "previous": response.get("pagination", {}).get("previous"),
        },
        "message": "Get Calls",
    }


@telephony.get("/get_dialed_by_users", summary="Get list of all Dialed user")
@requires_feature_permission("read")
async def get_dialed_by_user_list(
    current_user: CurrentUser,
    cache_data=Depends(cache_dependency),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """\n
    Get all the dialed by users list.\n\n

    Params:\n
        - college (str): An unique identifier of a college. e.g., 123456789012345678901234\n\n
        - cache_data: It is for incase memory data.
        - current_user (User): Requested user data.\n\n

    Returns:\n
        - dict: A dictionary which contains list of dialed by users along with successful message.
    """
    cache_key, data = cache_data
    if data:
        return data

    user = await UserHelper().is_valid_user(current_user)
    users_data = await UserListHelper().get_user_list(user, is_answered_by=False)

    data = utility_obj.response_model(users_data, "Dialed by users data list.")

    if cache_key:
        await insert_data_in_cache(cache_key, data, expiration_time=30)

    return data


@telephony.get("/get_answered_by_users", summary="Get list of all answered by users")
@requires_feature_permission("read")
async def get_answered_by_user_list(
    current_user: CurrentUser,
    cache_data=Depends(cache_dependency),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """\n
    Get all the answered by users list.\n\n

    Params:\n
        - college (str): An unique identifier of a college. e.g., 123456789012345678901234\n\n
        - cache_data: It is for incase memory data.
        - current_user (User): Requested user data.\n\n

    Returns:\n
        - dict: A dictionary which contains list of answered by users along with successful message.
    """
    cache_key, data = cache_data
    if data:
        return data

    user = await UserHelper().is_valid_user(current_user)
    users_data = await UserListHelper().get_user_list(user, is_answered_by=True)

    data = utility_obj.response_model(users_data, "Answered by users data list.")

    if cache_key:
        await insert_data_in_cache(cache_key, data, expiration_time=30)

    return data


@telephony.post("/assign_application_on_call")
@requires_feature_permission("write")
async def assign_application_on_call(
    current_user: CurrentUser,
    application_info: ApplicationCallInfo,
    missed_call_tag: bool = False,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """\n
    Assigned Application on calls after call end API\n\n

    Params:\n
        application_info (ApplicationCallInfo): This payload contains two field which are following.
            - phone_num (str, None): Phone number must be in the format +91XXXXXXXXXX
            - call_id (str, None): Unique call id of 24 characters.
            - application_id (str): Unique application id of 24 chars.
            NOTE: `phone_num` or 'call_id` One from both of them are minderatory.
        missed_call_tag (bool): Add missed call tag to the to the lead if true then it will mark.
        current_user (User, optional): Current requested user. Defaults to Depends(get_current_user).
        college_id (strl): Unique identifier/id of a college which useful for get college data.

    Returns:\n
        dict: Message of the data request.

    Raises:
        - 401: An error occurred with status code 401 when user don't have permission to access/use API.
        - ObjectIdInValid: An error occurred with status code 422 when send wrong counselor_id.
        - CustomError: An error occurred with status code 400 when something improper condition happen.
        - Exception: An error occurred with status code 500 when something wrong happen in the backend code.
    """
    application_info = jsonable_encoder(application_info)

    try:
        if (
            await DatabaseConfiguration().studentApplicationForms.find_one(
                {"_id": ObjectId(application_info.get("application_id"))}
            )
            and (
                await DatabaseConfiguration().call_activity_collection.find_one(
                    {"_id": ObjectId(application_info.get("call_id"))}
                )
            )
            or await DatabaseConfiguration().call_activity_collection.find_one(
                {
                    "call_from_number": (
                        int(application_info.get("phone_num")[3:])
                        if application_info.get("phone_num")
                        else None
                    )
                }
            )
        ):
            return await ApplicationAssigned().application_assigned_on_call(
                application_info, missed_call_tag
            )

        else:
            raise HTTPException(
                status_code=404, detail="Invalid call_id or application_id in payload."
            )

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(f"An error got when assign applicaiton on call. Error - {error}")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@telephony.get("/download_call_recording")
@requires_feature_permission("download")
async def download_call_recording(
    call_id: str,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:

    try:

        await utility_obj.is_id_length_valid(call_id, name="Call id")

        if call := await DatabaseConfiguration().call_activity_collection.find_one(
            {
                "_id": ObjectId(call_id),
                "mcube_file_path": {"$exists": True},
                "recording": {"$exists": False},
            }
        ):

            return await CallRecording().download_recording_helper(call)

        else:
            raise HTTPException(
                status_code=404,
                detail="Invalid call_id, Please pass the valid call_id to download file.",
            )

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)

    except Exception as error:
        logger.error(
            f"An error got while downloading call recording file. Error - {error}"
        )
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@telephony.get("/landing_number")
@requires_feature_permission("read")
async def get_all_landing_numbers(
    current_user: CurrentUser,
    cache_data=Depends(cache_dependency),
    college: dict = Depends(get_college_id),
) -> dict:
    """\nGetting landing number list of organization from the database.\n

    Params:\n
        - college_id (str): An unique identifier/id of college which useful for get college data/information.

    Returns:\n
        - dict: A dictionary which contains list of landing numbers.
    """
    cache_key, data = cache_data
    if data:
        return data

    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") in [
        "college_admin",
        "college_super_admin",
        "super_admin",
    ]:
        data = college.get("landing_numbers", [])

    data = {"data": data, "message": "Get the landing number list."}

    if cache_key:
        await insert_data_in_cache(cache_key, data)

    return data


@telephony.post("/missed_call_top_strip")
@requires_feature_permission("read")
async def missed_call_top_strip(
    current_user: CurrentUser,
    date_range: DateRange | None = Body(None),
    change_indicator: ChangeIndicator = "last_7_days",
    cache_data=Depends(cache_dependency),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """\nMissed call top strip data

    Params:
        date_range (DateRange, optional): startdate and enddate. Defaults to Body(None).
        change_indicator (ChangeIndicator, optional): Change indicator parameter. Defaults to "last_7_days".
        college (dict, optional): College unique id. Defaults to Depends(get_college_id).

    Returns:
        dict: Response top strip data.
    """
    date_range = await utility_obj.format_date_range(date_range)
    cache_key, data = cache_data
    if data:
        return data
    if (
        user := await DatabaseConfiguration().user_collection.find_one(
            {"user_name": current_user.get("user_name")}
        )
    ) is None or user.get("role", {}).get("role_name", "") not in [
        "college_admin",
        "college_super_admin",
        "super_admin",
        "college_counselor",
        "college_head_counselor",
    ]:
        raise HTTPException(status_code=401, detail="permission denied")

    try:
        response = await MissedCallDashboard().header_data_helper(
            date_range=date_range, change_indicator=change_indicator
        )
        data = {"data": response, "message": "Missed call dashboard header data."}
    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the missed call dashboard header data. Error: {error}.",
        )
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@telephony.post("/missed_call_list")
@requires_feature_permission("read")
async def missed_call_list(
    current_user: CurrentUser,
    counsellors: list[str] | None = None,
    landing_number: str | None = None,
    page_num: int = 1,
    page_size: int = 10,
    date_range: DateRange | None = Body(None),
    search: str | None = Body(None),
    sort: bool | None = Body(None),
    sort_name: str | None = Body(None),
    sort_type: str | None = Body(None),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """\nMissed call list data for missed call dashboard.

    Params:
        counsellors (list[str] | None, optional): Counsellor filter by counsellor id. Defaults to None.
        landing_number (str | None, optional): landing no. filter. Defaults to None.
        page_num (int, optional): No. of page. Defaults to 1.
        page_size (int, optional): Count of data in one page. Defaults to 10.
        date_range (DateRange, optional): Apply date range for filter the data. Defaults to Body(None).
            Body Params:
                - start_date ("YYYY-MM-DD"): start date
                - end_date ("YYYY-MM-DD"): end date
        search (str, optional): Search key for filteration. Defaults to Body(None).
            Body Params:
                - search (str): search keyword.
        sort (bool, optional): Is sort apply on the data or not (True/False). Defaults to Body(None).
        sort_name (str, optional): Field name must be ['missed_call_count', 'dialed_call_count', 'missed_call_age']. Defaults to Body(None).
        sort_type (str, optional): It must be `asc` or `desc`. Defaults to Body(None).
        college_id (dict, optional): College unique id. Defaults to Depends(get_college_id).

    Returns:
        dict: Response data.
    """
    date_range = await utility_obj.format_date_range(date_range)
    user = await UserHelper().is_valid_user(user_name=current_user)
    role_name = user.get("role", {}).get("role_name")

    if role_name in ["college_admin", "college_super_admin", "super_admin"]:
        data, count = await MissedCallSummary().missed_call_list(
            counsellors,
            landing_number,
            date_range,
            search,
            sort,
            sort_name,
            sort_type,
            page_num,
            page_size,
        )

    elif role_name == "college_head_counselor":
        allowed_counsellor_list = [
            str(counsellor.get("_id"))
            for counsellor in await DatabaseConfiguration()
            .user_collection.aggregate(
                [{"$match": {"head_counselor_id": ObjectId(user.get("_id"))}}]
            )
            .to_list(None)
        ]
        allowed_counsellor_list.append(user.get("_id"))
        if counsellors == []:
            counsellors = allowed_counsellor_list

        elif set(counsellors) - set(allowed_counsellor_list) == []:
            data, count = await MissedCallSummary().missed_call_list(
                counsellors,
                landing_number,
                date_range,
                search,
                sort,
                sort_name,
                sort_type,
                page_num,
                page_size,
            )
        else:
            raise ValueError("Don't have enough permission to see other users data.")

    else:
        counsellors = [user.get("_id")]
        data, count = await MissedCallSummary().missed_call_list(
            counsellors,
            landing_number,
            date_range,
            search,
            sort,
            sort_name,
            sort_type,
            page_num,
            page_size,
        )

    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, count, "/telephony/missed_call_list"
    )
    return {
        "data": data,
        "total": count,
        "count": page_size,
        "pagination": {
            "next": response.get("pagination", {}).get("next"),
            "previous": response.get("pagination", {}).get("previous"),
        },
        "message": "Get Missed Calls",
    }


@telephony.post("/assigned_counsellor_on_missed_call")
@requires_feature_permission("edit")
async def assigned_counsellor_on_missed_call(
    payload: AssignedCounsellorOnMissedCall,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """Assign and update Counsellor of any missed call.

    Params:
        payload (AssignedCounsellorOnMissedCall): Information of calls and counsellor which has to be assign.
            - counsellor_id (str): Counsellor Unique id.
            - student_phone (list(str)): Phone number must be in the format ["+91XXXXXXXXXX", "+91XXXXXXXXXX"].

        college_id (strl): Unique identifier/id of a college which useful for get college data.

    Returns:
        dict: Response message
    """
    user = await UserHelper().is_valid_user(current_user)
    payload = jsonable_encoder(payload)
    counsellor_id = payload.get("counsellor_id")
    try:
        if user.get("role", {}).get("role_name") in [
            "college_admin",
            "college_super_admin",
            "super_admin",
        ]:
            phone_numbers = []
            if counsellor := await DatabaseConfiguration().user_collection.find_one(
                {"_id": ObjectId(counsellor_id), "role.role_name": "college_counselor"}
            ):
                for phone in payload.get("student_phone"):
                    phone_numbers.append(int(phone[3:]))
                return await AssignedCounsellor().counsellor_assigned_on_call(
                    counsellor, phone_numbers
                )
            else:
                raise CustomError("Invalid counsellor ID.")

        else:
            raise HTTPException(status_code=401, detail="permission denied")

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when assign counsellor on missed call. Error: {error}.",
        )


@telephony.post("/counsellor_call_activity")
@requires_feature_permission("read")
async def counsellor_call_activity(
    current_user: CurrentUser,
    quick_filter: str | None = None,
    activity_status: list[str] | None = None,
    date_range: DateRange | None = Body(None),
    sort: bool | None = Body(None),
    sort_name: str | None = Body(None),
    sort_type: str | None = Body(None),
    cache_data=Depends(cache_dependency),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """\nCounsellor call activity dashboard data API\n\n

    Params:
        quick_filter (str | None, optional): It must be 'Active', 'Inactive' or 'On Call'. Defaults to None.
        activity_status (list[str] | None, optional): It must be the list from the check-out reason list data. Defaults to None.
        date_range (DateRange | None, optional): start_date and end_date. Defaults to Body(None).
        sort (bool | None, optional): Apply sort or not on the response data. Defaults to Body(None).
        sort_name (str | None, optional): Field name which has to be sort, It must be from 'caller_name', 'check_in_duration_sec', 'talk_time', 'aht', 'ideal_duration' or 'check_out_duration_sec'. Defaults to Body(None).
        sort_type (str | None, optional): It must be 'asc' or 'dsc'. Defaults to Body(None).
        current_user (User, optional): Current requested user which should always 'college_admin', 'college_super_admin' or 'super_admin' for accessing thease data. Defaults to Depends(get_current_user).
        college_id (dict, optional): Colege unique id. Defaults to Depends(get_college_id).

    Returns:
        dict: Data set of the counsellors and their details of activity.
    """

    date_range = await utility_obj.format_date_range(date_range)
    cache_key, data = cache_data
    if data:
        return data

    try:
        if (
            user := await DatabaseConfiguration().user_collection.find_one(
                {"user_name": current_user.get("user_name")}
            )
        ) is None or user.get("role", {}).get("role_name", "") not in [
            "college_admin",
            "college_super_admin",
            "super_admin",
        ]:
            raise HTTPException(status_code=401, detail="permission denied")

        if quick_filter and quick_filter not in ["Active", "Inactive", "On Call"]:
            raise CustomError("Quick filter must be 'Active', 'Inactive' or 'On Call'")

        if sort and sort_name not in [
            "caller_name",
            "check_in_duration_sec",
            "talk_time",
            "aht",
            "ideal_duration",
            "check_out_duration_sec",
        ]:
            raise CustomError(
                "sort_name must be 'caller_name', 'check_in_duration_sec', 'talk_time', 'aht', 'ideal_duration' or 'check_out_duration_sec'"
            )

        if sort and sort_type not in ["asc", "dsc"]:
            raise CustomError("sort_type must be 'asc' or 'dsc'")

        response = await CallActivity().counsellor_data_helper(
            quick_filter, activity_status, date_range, sort, sort_name, sort_type, [ObjectId(college.get("id"))]
        )
        data = {"data": response, "message": "Counsellor call activity dashboard data."}

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the call activity dashboard data. Error: {error}.",
        )

    if cache_key:
        await insert_data_in_cache(cache_key, data)

    return data


@telephony.post("/counsellor_call_log_header")
@requires_feature_permission("read")
async def counsellor_call_log_header(
    current_user: CurrentUser,
    date_range: DateRange | None = Body(None),
    change_indicator: ChangeIndicator = "last_7_days",
    cache_data=Depends(cache_dependency),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """\nCounsellor dashboard telephony header call summary data
    Params:
        date_range (DateRange | None, optional): Start date and end date for data filteration. Defaults to Body(None).
        change_indicator (ChangeIndicator, optional): Change indicator parameters for 7, 15 and 30 days. Defaults to "last_7_days".
        college (dict, optional): College unique id. Defaults to Depends(get_college_id).
    Returns:
        dict: Json response data for header
    """
    date_range = await utility_obj.format_date_range(date_range)
    cache_key, data = cache_data
    if data:
        return data
    user = await UserHelper().is_valid_user(user_name=current_user)

    try:
        role_name = user.get("role", {}).get("role_name")
        counsellors = []

        if role_name in ["college_admin", "college_super_admin", "super_admin"]:
            data = await CounsellorCallLog().log_header_helper(
                counsellors,
                date_range,
                change_indicator
            )

        elif role_name == "college_head_counselor":
            allowed_counsellor_list = [
                str(counsellor.get("_id"))
                for counsellor in await DatabaseConfiguration()
                .user_collection.aggregate(
                    [{"$match": {"head_counselor_id": ObjectId(user.get("_id"))}}]
                )
                .to_list(None)
            ]
            allowed_counsellor_list.append(user.get("_id"))
            if counsellors == []:
                counsellors = allowed_counsellor_list

            elif set(counsellors) - set(allowed_counsellor_list) == []:
                data = await CounsellorCallLog().log_header_helper(
                    counsellors,
                    date_range,
                    change_indicator
                )
            else:
                raise ValueError("Don't have enough permission to see other users data.")

        else:
            counsellors = [user.get("_id")]
            data = await CounsellorCallLog().log_header_helper(
                counsellors,
                date_range,
                change_indicator
            )

        response = {
            "data": data,
            "message": "Counsellor Calllog data fetched successfully."
        }

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the call activity dashboard data. Error: {error}.",
        )

    if cache_key:
        await insert_data_in_cache(cache_key, response)
    return response

         
@telephony.post("/call_quality_table")
@requires_feature_permission("read")
async def counsellor_call_quality_table(
    current_user: CurrentUser,
    date_range: DateRange | None = Body(None),
    change_indicator: ChangeIndicator = "last_7_days",
    page_num: int = 1,
    page_size: int = 10,
    cache_data=Depends(cache_dependency),
    college: dict = Depends(get_college_id)
) -> dict:
    """\nCall quality table for all counsellor calls
    Params:
        date_range (DateRange | None, optional): Start date and end date for data filteration. Defaults to Body(None).
        change_indicator (ChangeIndicator, optional): Change indicator parameters for 7, 15 and 30 days. Defaults to "last_7_days".
        college (dict, optional): College unique id. Defaults to Depends(get_college_id).
    Returns:
        dict: Json response data for header
    """
    date_range = await utility_obj.format_date_range(date_range)
    cache_key, data = cache_data
    if data:
        return data
    
    try:
        user = await UserHelper().is_valid_user(user_name=current_user)

        if user.get("role", {}).get("role_name") not in ["college_admin", "college_super_admin", "super_admin"]:
            raise CustomError("Permission denied.")

        call_quality_helper = CallQuality()
        data, count = await call_quality_helper.call_quality_data_helper(date_range, change_indicator, page_num, page_size, college)
        total_count = await call_quality_helper.call_quality_total_data_helper(date_range)

        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, count, "/telephony/call_quality_table"
        )
        response = {
            "data": data,
            "total_data": total_count,
            'total': count,
            "count": page_size,
            "pagination": {
                "next": response.get("pagination", {}).get("next"),
                "previous": response.get("pagination", {}).get("previous"),
            },
            "message": "Call quality data fetched successfully.",
        }

        if cache_key:
            await insert_data_in_cache(cache_key, response)

        return response

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when calling call quality table data. Error: {error}."
        )

          
@telephony.post("/counsellor_call_info")
@requires_feature_permission("read")
async def counsellor_call_info(
    current_user: CurrentUser,
    counsellors: list[str] | None = None,
    data_type: str = "Outbound",
    date_range: DateRange | None = Body(None),
    page_num: int = 1,
    page_size: int = 10,
    sort: bool = Body(None),
    sort_name: str = Body(None),
    sort_type: str = Body(None),
    cache_data=Depends(cache_dependency),
    college: dict = Depends(get_college_id)
) -> dict:
    """\nCounsellor call info table API

    Body Params:
        date_range (DateRange | None, optional): Date range which data has to be filter. Defaults to Body(None).

    Params:
        counsellors (list[str] | None, optional): List of counsellor which data has to be filtering out. Defaults to None.
        data_type (str, optional): It denotes and accepts the data as `Outbound` or `Inbound`. Defaults to "Outbound".
        page_num (int, optional): Current page no.. Defaults to 1.
        page_size (int, optional): No of data in one page. Defaults to 10.
        sort (bool, optional): Apply sort or not. Defaults to Body(None).
        sort_name (str, optional): Name of field which has to be sort (['counsellor_name', 'attempted_call', 'connected_call', 'duration', 'average_duration', 'received_call', 'missed_call']). Defaults is None.
        sort_type (str, optional): It denotes the arrangement of sort ([`asc`, `dsc`]). Defaults to Body(None).
        college_id (dict, optional): College unique id. Defaults to Depends(get_college_id).

    Raises:
        CustomError: Raise on invalid parameters
        HTTPException: Raise on invalid ids.

    Returns:
        dict: Return json response for the user
    """
    
    date_range = await utility_obj.format_date_range(date_range)
    cache_key, data = cache_data
    if data:
        return data
    
    try:
        user = await UserHelper().is_valid_user(user_name=current_user)

        if user.get("role", {}).get("role_name") not in ["college_admin", "college_super_admin", "super_admin"]:
            raise CustomError("Permission denied.")
        
        if counsellors:
            for counsellor in counsellors:
                if not await utility_obj.is_id_length_valid(counsellor, "Counsellor id") or not await (DatabaseConfiguration().user_collection.find_one({"_id": ObjectId(counsellor), "is_activated": True, "role.role_name": "college_counselor", "associated_colleges": {"$in": [ObjectId(college.get("id"))]}})):
                    raise CustomError("Invalid counsellor for filter.")
        
        if sort:
            if sort_type not in ['asc', 'dsc']:
                raise CustomError("Sort type must be `asc` or `dsc`")
            if sort_name not in ['counsellor_name', 'attempted_call', 'connected_call', 'duration', 'average_duration', 'received_call', 'missed_call']:
                raise CustomError("Invalid sort value.")
        
        if data_type not in ['Inbound', 'Outbound']:
            raise CustomError("data type must be `Inbound` or `Outbound`")
    
        data, count = await CallInfo().call_info_helper(
            counsellors,
            data_type,
            date_range,
            page_num,
            page_size,
            sort,
            sort_name,
            sort_type,
            college
        )

        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, count, "/telephony/counsellor_call_info"
        )
        response = {
            "data": data,
            'total': count,
            "count": page_size,
            "pagination": {
                "next": response.get("pagination", {}).get("next"),
                "previous": response.get("pagination", {}).get("previous"),
            },
            "message": "Call info data fetched successfully."
        }
        
        if cache_key:
            await insert_data_in_cache(cache_key, response)

        return response

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    
    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when calling call info table data. Error: {error}."
        )


@telephony.post("/call_quality_table_download")
@requires_feature_permission("download")
async def counsellor_call_quality_table_download(
    current_user: CurrentUser,
    date_range: DateRange | None = Body(None),
    change_indicator: str = "last_7_days",
    page_num: int = 1,
    page_size: int = 10,
    college: dict = Depends(get_college_id)
) -> dict:
    """\nCall quality table for all counsellor calls download API
    Params:
        date_range (DateRange | None, optional): Start date and end date for data filteration. Defaults to Body(None).
        change_indicator (ChangeIndicator, optional): Change indicator parameters for 7, 15 and 30 days. Defaults to "last_7_days".
        page_num (int, optional): Current page no.. Defaults to 1.
        page_size (int, optional): No of data in one page. Defaults to 10.
        college (dict, optional): College unique id. Defaults to Depends(get_college_id).

    Returns:
        json: CSV download url link
    """
    try:
        formatted_date_range = await utility_obj.format_date_range(date_range)
        user = await UserHelper().is_valid_user(user_name=current_user)
        
        if user.get("role", {}).get("role_name") not in ["college_admin", "college_super_admin", "super_admin"]:
            raise CustomError("Permission denied.")
        
        call_quality_helper = CallQuality()
        data, count = await call_quality_helper.call_quality_data_helper(
            formatted_date_range, change_indicator, page_num, page_size, college
        )
        
        if data:
            data_keys = list(data[0].keys())
            get_url = await upload_csv_and_get_public_url(
                fieldnames=data_keys, data=data, name="call_quality_data"
            )
            return {"download_url": get_url}

        raise HTTPException(status_code=404, detail="No data found.")

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        logger.error(f"An error occurred: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when calling call quality table data download. Error: {error}."
        )