"""
This file contains APIs related to Communication Performance module in admin profile.
"""
import datetime

from fastapi import APIRouter, Depends, Body, BackgroundTasks, Request
from fastapi.exceptions import HTTPException

from app.background_task.admin_user import DownloadRequestActivity
from app.core.log_config import get_logger
from app.core.utils import utility_obj, requires_feature_permission
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import CurrentUser
from app.helpers.admin_dashboard.checkin_checkout_dashboard import checkincheckout_obj
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.applications import UpdateAction
from app.models.student_user_schema import User, DateRange, ChangeIndicator, CommunicationType
from app.database.configuration import DatabaseConfiguration
from bson import ObjectId

from app.s3_events.s3_events_configuration import upload_csv_and_get_public_url

checkinout_router = APIRouter()
logger = get_logger(name=__name__)

@checkinout_router.post("/header_details")
@requires_feature_permission("read")
async def get_top_header(
    current_user: CurrentUser,
    role_ids: list = Body(None),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get CheckIn CheckOut header details based on the user's role and college information.

    This endpoint retrieves header-related data for the user based on their role and
    the associated college. The response may include specific details relevant to
    the user's role and college context.
    Params:
        role_ids (list, optional): A list of role IDs for which header details need to be fetched.
                                   Defaults to None if not provided.
        current_user (User): The authenticated user object. This is obtained using dependency injection
                            through `get_current_user`.
        college (dict): College information dictionary fetched using the `get_college_id_short_version`
                       dependency with `short_version=True`.

    Returns:
        JSON: Header details specific to the user's role and associated college.
    """
    user = await UserHelper().is_valid_user(user_name=current_user)
    if user.get("role", {}).get("role_name") != "college_super_admin":
        raise HTTPException(status_code=404, detail='Not Enough Permissions')
    return await checkincheckout_obj.get_top_header(role_ids=role_ids, college_id=college.get("id"))


@checkinout_router.post("/manage_sessions")
@requires_feature_permission("write")
async def get_manage_sessions(
    current_user: CurrentUser,
    user_ids: list = Body(None),
    date: str = Body(None),
    role_ids: list = Body(None),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
        Manage user sessions based on provided filters.

        Params:
            user_ids (list, optional): List of user IDs to filter sessions. Defaults to None.
            date (str, optional): Date string (in 'YYYY-MM-DD' format) to filter sessions for a specific day. Defaults to None.
            role_ids (list, optional): List of role IDs to filter sessions by user roles. Defaults to None.
            current_user (User): The current authenticated user, injected via dependency.
            college (dict): College information, including short version details, injected via dependency.

        Returns:
            JSON response containing session details filtered based on the provided parameters.

        Raises:
            HTTPException:
                Not enough Permissions: When the user has no permissions
                When something unexpected happen
    """
    user = await UserHelper().is_valid_user(user_name=current_user)
    if user.get("role", {}).get("role_name") != "college_super_admin":
        raise HTTPException(status_code=404, detail='Not Enough Permissions')
    try:
        return {"data": await checkincheckout_obj.get_manage_sessions(role_ids=role_ids, user_ids=user_ids, date=date),
                "message": "Return Manage Sessions"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Some thing went Wrong! {e}"
        )


@checkinout_router.post("/bench_marking")
@requires_feature_permission("read")
async def get_bench_marking(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    request: Request,
    date: str = Body(None),
    download: bool = False,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Handles benchmarking data retrieval for a given date.

    Params:
        background_tasks (BackgroundTasks): FastAPI background task manager for handling async tasks.
        request (Request): The incoming HTTP request.
        date (str, optional): The date for which benchmarking data is requested. Defaults to None.
        download (bool, optional): Flag to indicate if the data should be downloaded. Defaults to False.
        current_user (User): The authenticated user making the request.
        college (dict): The college details retrieved based on the short version.

    Returns:
        JSON response containing benchmarking data or a downloadable file if `download` is True.
    """
    user = await UserHelper().is_valid_user(user_name=current_user)
    if user.get("role", {}).get("role_name") != "college_super_admin":
        raise HTTPException(status_code=404, detail='Not Enough Permissions')
    response = await checkincheckout_obj.get_bench_marking(date=date)
    if download:
        if response:
            data_keys = list(response[0].keys())
            get_url = await upload_csv_and_get_public_url(
                fieldnames=data_keys,
                data=response,
                name="utm",
            )
            background_tasks.add_task(
                DownloadRequestActivity().store_download_request_activity,
                request_type="Check IN/OUT Data",
                requested_at=datetime.datetime.utcnow(),
                ip_address=utility_obj.get_ip_address(request),
                user=await UserHelper().check_user_has_permission(
                    user_name=current_user),
                total_request_data=len(response),
                is_status_completed=True,
                request_completed_at=datetime.datetime.utcnow(),
            )
            return get_url
        else:
            raise HTTPException(status_code=404, detail="No Data Found!")
    return {"data": response,
            "message": "Return Bench Marking"}


@checkinout_router.post("/update_status")
@requires_feature_permission("edit")
async def update_status(
    user_id: str,
    action: UpdateAction,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Updates the status of a user based on the specified action.

    Params:
        user_id (str): The unique identifier of the user whose status needs to be updated.
        action (UpdateAction): The action to be performed on the user's status.
        current_user (User, optional): The currently authenticated user.
            Retrieved via dependency injection from `get_current_user`.
        college (dict, optional): The college details associated with the user,
            fetched using `get_college_id_short_version` with `short_version=True`.

    Returns:
        dict: A response indicating the success or failure of the update operation.
    """
    action = action.value
    user = await UserHelper().is_valid_user(user_name=current_user)
    if user.get("role", {}).get("role_name") != "college_super_admin":
        raise HTTPException(status_code=404, detail='Not Enough Permissions')
    status = await checkincheckout_obj.update_status(user_id, action, user)
    if status:
        return {"message": "Updated Successfully!"}
    else:
        return {"message": "Something went wrong!"}

