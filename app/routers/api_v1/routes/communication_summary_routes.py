"""
This file contains APIs related to Communication summary module in admin profile.
"""

from fastapi import APIRouter, Depends, Body
from fastapi.exceptions import HTTPException

from app.core.custom_error import CustomError, ObjectIdInValid
from app.core.log_config import get_logger
from app.core.utils import utility_obj, requires_feature_permission
from app.database.aggregation.admin_user import AdminUser
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import cache_dependency, insert_data_in_cache
from app.dependencies.oauth import CurrentUser
from app.helpers.communication_summary.dashboard_header_helper import \
    CommunicationHeader
from app.helpers.communication_summary.counsellor_wise_followup_helper import \
    CounsellorWiseFollowup
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.student_user_schema import User, DateRange, ChangeIndicator
from app.database.configuration import DatabaseConfiguration
from bson import ObjectId

communication = APIRouter()
logger = get_logger(name=__name__)


@communication.post("/header_summary", summary="All communication summary data.")
@requires_feature_permission("read")
async def header_summary(
    current_user: CurrentUser,
    date_range: DateRange | None = Body(None),
    change_indicator: ChangeIndicator = "last_7_days",
    cache_data = Depends(cache_dependency),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """\nCommunicaiton summary Header data API with date range and change indicator filter\n

    Params:
        date_range (DateRange | None, optional): Date range filter contains start_date and end_date. Defaults to Body(None).
        change_indicator (ChangeIndicator, optional): Change indicatior string for segregating progress through past data. Defaults to "last_7_days".
        current_user (User, optional): Current requested user. Defaults to Depends(get_current_user).
        cache_data (_type_, optional): _description_. Defaults to Depends(cache_dependency).
        college_id (dict, optional): College unique id. Defaults to Depends(get_college_id).\n

    Returns:
        dict: Json data as a response which contains all communication details number.
    """
    date_range = await utility_obj.format_date_range(date_range)
    cache_key, data = cache_data
    if data:
        return data

    try:
        if (
            user := await UserHelper().is_valid_user(user_name=current_user)
        ) is None or user.get("role", {}).get("role_name", "") not in [
            "college_admin",
            "college_super_admin",
            "super_admin",
            "college_counselor",
            "college_head_counselor"
        ]:
            raise HTTPException(status_code=401, detail="permission denied")

        counselor_id = []
        if user.get("role", {}).get("role_name") == "college_counselor":
            counselor_id = [ObjectId(user.get("_id"))]
        elif user.get("role", {}).get("role_name") == "college_head_counselor":
            counselor_id = await AdminUser().get_users_ids_by_role_name(
                "college_counselor", college.get('id'), user.get("_id")
            )
            counselor_id.append(ObjectId(user.get("_id")))

        response = await CommunicationHeader().header_helper(
            date_range, change_indicator, counselor_id
        )
        data = {"data": response, "message": "Communication summary dashboard header data."}

        if cache_key:
            await insert_data_in_cache(cache_key, data)

        return data

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the communication summary dashboard header data. Error: {error}.",
        )


@communication.post("/counsellor_wise_followup_details")
@requires_feature_permission("read")
async def counsellor_wise_followup_details(
    current_user: CurrentUser,
    counsellor_ids: list[str] | None = None,
    head_counsellor_id: str | None = None,
    date: str = Body(None),
    cache_data = Depends(cache_dependency),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """\nAPI for getting counsellor wise followup data.\n

    Body Params:\n
        counsellor_ids (list[str] | None, optional): List of counsellor id for filtering counsellors.
        date (str, optional): Pass single date for getting that date's data. Format: "YYYY-MM-DD".

    Params:\n
        head_counsellor_id (str | None, optional): Head counsellor id for getting all counsellors related to that head counsellor.
        college_id (dict, optional): college unique id

    Raises:\n
        HTTPException: Internal server error.
        CustomError: If passed any invalid counsellor id.
        CustomError: If passed any invalid head counsellor id.

    Returns:\n
        dict: Response related to counsellor wise followup summary.
    """

    cache_key, data = cache_data
    if data:
        return data
    
    try:
        if (
            user := await UserHelper().is_valid_user(user_name=current_user)
        ) is None or user.get("role", {}).get("role_name", "") not in [
            "college_admin",
            "college_super_admin",
            "super_admin",
        ]:
            raise HTTPException(status_code=401, detail="permission denied")

        if counsellor_ids:
            for counsellor_id in counsellor_ids:
                if len(counsellor_id) != 24 or not await DatabaseConfiguration().user_collection.find_one({"_id": ObjectId(counsellor_id), "role.role_name": "college_counselor"}):
                    raise CustomError("Counsellor id is invalid.")

        if head_counsellor_id and (len(head_counsellor_id) != 24 or not await DatabaseConfiguration().user_collection.find_one({"_id": ObjectId(head_counsellor_id), "role.role_name": "college_head_counselor"})):
            raise CustomError("Head counsellor id is invalid.")

        if counsellor_ids:
            counsellor_ids = [ObjectId(counsellor_id) for counsellor_id in counsellor_ids]
        head_counsellor_id = ObjectId(head_counsellor_id)

        response = await CounsellorWiseFollowup().counsellor_wise_followup(
            counsellor_ids, head_counsellor_id, date
        )

        data = {"data": response, "message": "Counsellor wise followup data response."}

        if cache_key:
            await insert_data_in_cache(cache_key, data)

        return data

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the counsellor wise followup details. Error: {error}.",
        )