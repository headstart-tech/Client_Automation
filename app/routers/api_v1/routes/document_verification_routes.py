"""
This file contains API routes related to Verification of Documents
"""
import datetime
from typing import List, Union
from bson import ObjectId
from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    BackgroundTasks, Query, Request, Path
)
from fastapi.encoders import jsonable_encoder
from app.background_task.admin_user import DownloadRequestActivity
from app.core.utils import utility_obj, requires_feature_permission
from app.core.reset_credentials import Reset_the_settings
from app.database.configuration import DatabaseConfiguration
from app.models.document_verification_schema import ApplicationDetailsSchema
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import insert_data_in_cache, CurrentUser, cache_dependency, \
    change_indicator_cache, is_testing_env, cache_invalidation
from app.helpers.document_verification_helpers import doc_verification_obj, DocumentVerification
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.applications import DateRange
from app.models.lead_schema import DvStatus
from app.models.student_user_schema import ChangeIndicator, User, SortType

document_verification = APIRouter()


@document_verification.post("/all_applications/")
@requires_feature_permission("read")
async def get_all_application_details(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        college: dict = Depends(get_college_id),
        payload: ApplicationDetailsSchema | None = Body(None),
        page_num: int = Query(1, gt=0),
        page_size: int = Query(25, gt=0),
        season: str | None = Query(None, description="Enter season id if want to" " get data season-wise"),
        sort_type: SortType | None | str = None,
        column_name: str | None = Query(
            None,
            description="Column name which useful for sort data based on sort type. Column name can be: "
            "course_name, dv_status, current_application_stage, reupload_status"
        ),
        search_input: str | None = Query(None, description="Search by name, email, or phone number")

):
    """
        Fetches paginated application details for document verification
        Params:
            cache_data (tuple): Cached data and key.
            payload (ApplicationDetailsSchema, optional): Filter criteria for the application data.
            page_num (int): The current page number for pagination (default: 1).
            page_size (int): The number of records per page (default: 25).
            season (str, optional): The season ID for filtering data season-wise.
            sort_type(asc or dsc): sort applications based on column_name in sort_type(ascending or descending order)
            column_name(str, optional): Sort application based on column_name
        Returns:
            dict: The paginated application data
        Raises:
            HTTPException: An error occurred with status code 500 when something
            went wrong in backend code.
    """
    try:
        user = await UserHelper().is_valid_user(current_user)
        if payload is None:
            payload = {}
        payload = jsonable_encoder(payload)
        cache_key, data = cache_data
        if data:
            return data
        counselor_ids = None
        if user.get("role", {}).get("role_name") == "college_counselor":
            counselor_ids = [ObjectId(user.get("_id"))]
        elif user.get("role", {}).get("role_name") == "college_head_counselor":
            counselors = await DatabaseConfiguration().user_collection.aggregate(
                [{"$match": {"head_counselor_id": ObjectId(user.get("_id"))}}]
            ).to_list(length=None)
            counselor_ids = [ObjectId(temp.get("_id")) for temp in counselors]

        search_condition = None
        if search_input:
            search_condition = {
                "$or": [
                    {"result.user_name": {"$regex": search_input, "$options": "i"}},
                    {"result.basic_details.first_name": {"$regex": search_input, "$options": "i"}},
                    {"result.basic_details.mobile_number": {"$regex": search_input, "$options": "i"}}
                ]
            }

        data = await DocumentVerification().get_application_data(
            payload=payload,
            page_num=page_num,
            page_size=page_size,
            season=season,
            counselor_ids=counselor_ids,
            sort_type=sort_type,
            column_name=column_name,
            search_condition=search_condition
        )
        if cache_key:
            await insert_data_in_cache(cache_key, data)
        return data
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"An internal error" f" occurred: {error}"
        )


@document_verification.post("/quick_view/")
@requires_feature_permission("read")
async def get_quick_view_details(
    current_user: CurrentUser,
    date_range: DateRange | None = Body(None),
    change_indicator: ChangeIndicator = "last_7_days",
    cache_data=Depends(cache_dependency),
    cache_change_indicator=Depends(change_indicator_cache),
    college: dict = Depends(get_college_id)
):
    """
    This function handles retrieving document verification details based on the
    user's role and filters such as date range and change indicators
    Params:
        - Current user (str): The email id of current user
        - change_indicator (str): Change indicator value. This can have 3 values last_7_days/last_15_days/last_30_days
        - date_range (DateRange): Date range filter. It has start date and end date in it
        - college (dict): Current college details
        - cache_change_indicator (tuple): Change indicator key and cached value
    Returns:
        - dict: A dictionary containing details of quick view
    """
    try:
        user = await UserHelper().is_valid_user(current_user)
        cache_key, data = cache_data
        if data:
            return data
        if date_range is None:
            date_range = {}
        counselor_ids = None
        if user.get("role", {}).get("role_name") == "college_counselor":
            counselor_ids = [ObjectId(user.get("_id"))]
        elif user.get("role", {}).get("role_name") == "college_head_counselor":
            counselors = await DatabaseConfiguration().user_collection.aggregate(
                [{"$match": {"head_counselor_id": ObjectId(user.get("_id"))}}]
            ).to_list(length=None)
            counselor_ids = [ObjectId(temp.get("_id")) for temp in counselors]
        date_range = jsonable_encoder(date_range)
        data = await doc_verification_obj.get_document_verification_details(date_range, change_indicator, counselor_ids, cache_change_indicator)
        result = {
            "data": data,
            "message": "Get quick view details"
        }
        if cache_key:
            await insert_data_in_cache(cache_key, result)
        return result
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"An internal error" f" occurred: {error}"
        )


@document_verification.put("/update_dv_status/")
@requires_feature_permission("edit")
async def update_document_status(
        status: DvStatus,
        application_id: str,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)
):
    """
    Update document verification status (dv_status) for the specified attachments.
    Params:
        - current_user (str): An user_name of current user.
        - application_id (str): An unique application id.
        - status (DvStatus): The document verification status to be applied.
        - college (dict): College data.
    Returns:
        - dict: A dictionary contains message.
    """

    return await DocumentVerification().update_document_status(
        application_id, current_user, status
    )


@document_verification.post(
    "/download_application_or_all_documents/",
    summary="Download student application or all documents"
)
@requires_feature_permission("download")
async def download_application_or_all_documents(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        request: Request,
        download_applications: bool,
        student_ids: List[str] = Body(description="Enter list of student ids"),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Download All Student Documents or Applications.

    This endpoint allows the user to download either the student applications or all student documents based on the
    `download_applications` flag. The result will be a URL to download a zip file containing the requested documents
    Params:
        background_tasks (BackgroundTasks): Used for running background tasks asynchronously.
        request (Request): The HTTP request object.
        download_applications (bool): If True, download only applications; otherwise, download all documents.
        current_user (CurrentUser): The current authenticated user.
        college (dict): The college details with a short version of the ID.
    Request Body Params:
        student_ids (List[str]): List of student IDs for which documents are to be downloaded.
    Returns:
        downloaded URL for the zip file.
    """
    await UserHelper().is_valid_user(current_user)
    current_datetime = datetime.datetime.utcnow()
    if download_applications:
        try:
            data = await DocumentVerification().get_student_application(
                student_ids
            )
        except Exception as error:
            raise HTTPException(status_code=500, detail=f"Failed to download student applications.{error}")
    else:
        data = await DocumentVerification().get_primary_sec_download_links(student_ids, (college.get("id")))
    try:
        background_tasks.add_task(
            DownloadRequestActivity().store_download_request_activity,
            request_type="Student documents",
            requested_at=current_datetime,
            ip_address=utility_obj.get_ip_address(request),
            user=await UserHelper().check_user_has_permission(user_name=current_user),
            total_request_data=len(student_ids),
            is_status_completed=True,
            request_completed_at=datetime.datetime.utcnow(),
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to log download request activity.{error}")
    return data

  
@document_verification.get("/get_auditor_remarks/", summary="Get auditor remarks")
@requires_feature_permission("read")
async def get_auditor_remarks(
        current_user: CurrentUser,
        student_id: str = Query(..., description="Enter student id"),
        cache_info=Depends(cache_dependency),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get auditor remarks

    Params:
        student_id (str): An unique student id.
        current_user (str): An user_name of current user.
        college (dict): College data.
    Returns:
        dict: A dictionary contains message.
    """
    cache_key, cache_data = cache_info
    if cache_data:
        return cache_data
    if not is_testing_env():
        Reset_the_settings().check_college_mapped(college.get("id"))
    data = await DocumentVerification().get_document_remarks(
        student_id=student_id, current_user=current_user
    )
    if cache_key:
        await insert_data_in_cache(cache_key,data)
    return data


@document_verification.post("/auditor_remark/",
                            summary="Add an overall auditor remark on student document")
@requires_feature_permission("write")
async def add_auditor_remark(
        current_user: CurrentUser,
        student_id: str = Query(description="Enter student ID"),
        remark: str = Body(description="Enter the auditor remark"),

        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Add an overall auditor remark for a document.

    Params:
        student_id (str): A unique student ID.e.g., 123456789012345678901233
        current_user (CurrentUser): The current auditor who is making the remark.
        college (dict): College data.e.g., 123456789012345678901231
    Request Body params:
         - remark (str): A string value which represents the auditor's comment or remark.
    Returns:
        - dict: A dictionary which contains information about add auditor mark or not.
    Raises:
        -  HTTPException: An error occurred with status code 500 when something
            went wrong in backend code.
    """

    data = await DocumentVerification().auditor_remark(
        current_user=current_user.get("user_name"), student_id=student_id,
        remark=remark

    )
    await cache_invalidation(api_updated="admin/add_comment_for_document")

    return data



