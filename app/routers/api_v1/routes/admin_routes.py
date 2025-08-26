"""
This file contains API routes related to admin user
"""

import asyncio
import datetime
import functools
import re
from pathlib import PurePath
from typing import Annotated
from typing import List, Optional, Union

import chardet
import numpy as np
import pandas as pd
from bson.objectid import ObjectId
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    Path,
    Query,
    UploadFile,
    Request,
)
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from fastapi.param_functions import File
from fastapi.security import OAuth2PasswordRequestForm
from kombu.exceptions import KombuError
from meilisearch.errors import MeilisearchCommunicationError, \
    MeilisearchApiError

from app.background_task.admin_user import DownloadRequestActivity
from app.celery_tasks.celery_publisher_upload_leads import PublisherActivity
from app.core.custom_error import DataNotFoundError, ObjectIdInValid, \
    CustomError
from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, settings, Settings, requires_feature_permission
from app.database.aggregation.admin_user import AdminUser
from app.database.aggregation.get_all_applications import Application
from app.database.aggregation.paid_application import PaidApplication
from app.database.aggregation.publisher import Publisher
from app.database.aggregation.student import Student
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import (
    AuthenticateUser,
    CurrentUser,
    cache_dependency,
    insert_data_in_cache,
    cache_invalidation,
    is_testing_env,
    change_indicator_cache, delete_keys_matching_pattern,
    Is_testing
)
from app.helpers.admin_dashboard.admin_board import AdminBoardHelper
from app.helpers.admin_dashboard.admin_dashboard import AdminDashboardHelper
from app.helpers.admin_dashboard.user_audit_trail import AuditTrail
from app.helpers.admin_dashboard.admin_crud import AdminCRUD
from app.helpers.college_configuration import CollegeHelper
from app.helpers.course_configuration import CourseHelper
from app.helpers.student_curd.student_application_configuration import (
    StudentApplicationHelper,
)
from app.helpers.student_curd.student_configuration import StudentHelper
from app.helpers.student_curd.student_user_crud_configuration import (
    StudentUserCrudHelper,
)
from app.helpers.user_curd.role_configuration import RoleHelper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.applications import DateRange, ApplicationFilterOptions, \
    CourseFilter
from app.models.course_schema import ProgramFilter
from app.models.query import QueryType
from app.models.student_application_schema import DocumentStatus
from app.models.admin import AdminCreationModel, AdminUpdateModel
from app.models.student_user_crud_schema import StudentUser
from app.models.student_user_schema import (
    User,
    payload_data,
    paid_application_payload,
    ChangeIndicator,
    upload_docs,
)
from app.s3_events.s3_events_configuration import (
    upload_csv_and_get_public_url,
    upload_multiple_files,
    get_primary_sec_download_link,
    upload_multiple_files_and_return_temporary_urls,
)
from app.s3_events.s3_utils import S3_SERVICE

logger = get_logger(name=__name__)
admin = APIRouter()

s3_client = S3_SERVICE(
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region=settings.region_name,
)


async def get_counselor_list(college, counselor_id):
    all_counselor = DatabaseConfiguration().user_collection.aggregate(
        [
            {
                "$match": {
                    "associated_colleges": ObjectId(college.get("id")),
                    "role.role_name": "college_counselor",
                    "head_counselor_id": ObjectId(counselor_id),
                    }
            }
        ]
    )
    return [str(user.get("_id")) async for user in all_counselor]


async def get_counselor_id(user, counselor_id):
    """
    If login user is counselor then return his id as a counselor id
    """
    if user.get("role", {}).get("role_name",
                                "").lower() == "college_counselor":
        counselor_id = [str(user.get("_id"))]
    return counselor_id


async def get_field_name(paid_applications_filter, leads_filter, forms_filter, document_filter):
    """

    Return correct field name

    Params:
        paid_application_filter (bool): A boolean value will be True
         when want to add/delete/get paid
        application filter.
        leads_filter (bool): A boolean value will be True when want to
         add/delete/get lead filter.
        forms_filter (bool): A boolean value will be True when want to
         add/delete/get form filter.

    Returns:
        str: A field_name which useful for add/delete/get filter
         of particular type.
    """
    temp_dict = {
        "leads_filter": leads_filter,
        "paid_applications_filter": paid_applications_filter,
        "forms_filter": forms_filter,
        "document_filter": document_filter
    }
    return next((key for key, value in temp_dict.items() if value),
                "saved_filter")


async def unique_code_for_graph(
        current_user,
        date_range,
        college_id,
        route=None,
        counselor_id=None,
        season=None,
        lead_funnel=False,
        form_stage_wise_segregation=False,
        change_indicator=None,
        application_type=None,
        source=None,
        school_names=None,
        preference=None
):
    """
    Unique code for get data
    """
    user = await UserHelper().check_user_has_permission(user_name=current_user)
    is_head_counselor = False
    if user.get("role", {}).get("role_name") in [
        "college_counselor",
        "college_head_counselor",
    ]:
        college_id = college_id
    date_range = await utility_obj.format_date_range(date_range)
    if route == "score_board":
        data = await AdminBoardHelper().score_board(
            college_id=college_id,
            date_range=date_range,
            route="score_board",
            user=user,
            season=season,
            change_indicator=change_indicator,
            application_type=application_type,
        )
    elif route == "declaration":
        data = await AdminBoardHelper().score_board(
            college_id=college_id,
            date_range=date_range,
            route="declaration",
            user=user,
            season=season,
            lead_funnel=lead_funnel,
            form_stage_wise_segregation=form_stage_wise_segregation,
            change_indicator=change_indicator,
        )
    elif route == "form_wise_record":
        counselor_id = await get_counselor_id(user=user,
                                              counselor_id=counselor_id)
        if user.get("role", {}).get("role_name") == "college_head_counselor":
            if counselor_id:
                pass
            else:
                is_head_counselor = True
                counselor_id = await AdminUser().get_users_ids_by_role_name(
                    "college_counselor", college_id, user.get("_id")
                )
        data = await AdminDashboardHelper().form_wise_record(
            college_id=college_id,
            date_range=date_range,
            counselor_id=counselor_id,
            season=season,
            change_indicator=change_indicator,
            source=source,
            school_names=school_names,
            is_head_counselor=is_head_counselor,
            preference=preference
        )
    elif route == "lead_application":
        counselor_id = await get_counselor_id(user=user,
                                              counselor_id=counselor_id)
        data = await AdminBoardHelper().lead_application(
            college_id=college_id,
            date_range=date_range,
            source=source,
            counselor_id=counselor_id,
            season=season,
        )
    else:
        data = await AdminBoardHelper().score_board(
            college_id=college_id, date_range=date_range, user=user,
            season=season
        )
    return data


async def get_payload_and_date_range(payload):
    """
    Return payload and date_range
    """
    if payload is None:
        payload = {}
    payload = jsonable_encoder(payload)
    season = None
    if payload is not None:
        payload = {k: v for k, v in payload.items() if v is not None}
        date_range = payload.get("date_range", {})
        if payload.get("season", {}):
            season = payload.get("season", {})
        if date_range is None:
            date_range = {}
    else:
        payload = {}
        date_range = {}
    return payload, date_range, season


@admin.post("/create", summary="Create admin user")
@requires_feature_permission("write")
async def create_admin_user(
        current_user: CurrentUser,
        details: AdminCreationModel
    ):
    """
    This API is used to create admin user, This API can be Used by Super Admin only

    ### Request Body
    - **first_name (str)**: The first name of the admin user
    - **middle_name (Optional[str])**: The middle name of the admin user
    - **last_name (Optional[str])**: The last name of the admin user
    - **email (str)**: The email of the admin user
    - **mobile_number (str)**: The mobile number of the admin user

    ### Example Request Body
    ```json
    {
      "first_name": "Sandeep",
      "middle_name": "",
      "last_name": "Mehta",
      "email": "sandeep@example.com",
      "mobile_number": "7896543210"
    }
    ```

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **422**: Custom Error (Error will be mentioned in `detail`)
    - **401**: Unauthorized/Not Enough Permissions
    - **400**: Bad Request

    ### Returns
    - **message (str)**: The message of the response
    - **admin_id (str)**: The id of the admin user
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await AdminCRUD().create_admin_user(details.model_dump(), user)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin.get("/get_admin_by_id", summary="Get admin by id")
@requires_feature_permission("read")
async def get_admin_by_id(
        current_user: CurrentUser,
        admin_id: str = Query(title="Admin Id")
    ):
    """
    This API is used to get admin by id, This API can be Used by Super Admin and Self User profile (Admin)

    ### Path Parameters
    - **admin_id (str)**: The id of the admin user

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **422**: Custom Error (Error will be mentioned in `detail`)
    - **401**: Unauthorized/Not Enough Permissions
    - **400**: Bad Request

    ### Returns
    - **admin (dict)**: The admin details
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await AdminCRUD().get_admin_by_id(admin_id, user)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin.get("/get_all_admins", summary="Get all admins")
@requires_feature_permission("read")
async def get_all_admins(current_user: CurrentUser,
        page: Optional[int] = Query(None, gt=0),
        limit: Optional[int] = Query(None, gt=0)):
    """
    This API is used to get all admins, This API can be Used by Super Admin only

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **422**: Custom Error (Error will be mentioned in `detail`)
    - **401**: Unauthorized/Not Enough Permissions
    - **400**: Bad Request

    ### Returns
    - **message (str)**: The message of the response
    - **admins (list)**: The list of admin details
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    await UserHelper().is_valid_user(current_user)
    try:
        return await AdminCRUD().get_all_admins(route="get_all", page=page, limit=limit)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin.put("/update_admin", summary="Update admin Details")
@requires_feature_permission("edit")
async def update_admin_details(
        current_user: CurrentUser,
        admin_details: AdminUpdateModel,
        admin_id: str = Query(title="Admin Id")
    ):
    """
    This API is used to update admin details, This API can be Used by Super Admin and Self User profile (Admin)

    ### Path Parameters
    - **admin_id (str)**: The id of the admin user

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **422**: Custom Error (Error will be mentioned in `detail`)
    - **401**: Unauthorized/Not Enough Permissions
    - **400**: Bad Request

    ### Returns
    - **message (str)**: The message of the response
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await AdminCRUD().update_admin(admin_id, admin_details.model_dump(exclude_defaults=True), user)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin.put("/activate/{admin_id}", summary="Activate admin")
@requires_feature_permission("edit")
async def activate_admin(
        current_user: CurrentUser,
        admin_id: str = Path(title="Admin Id")
    ):
    """
    This API is used to activate admin by id, This API can be Used by Super Admin only

    ### Path Parameters
    - **admin_id (str)**: The id of the admin user

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **422**: Custom Error (Error will be mentioned in `detail`)
    - **401**: Unauthorized/Not Enough Permissions
    - **400**: Bad Request

    ### Returns
    - **message (str)**: The message of the response
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await AdminCRUD().activate_admin(admin_id, user)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin.put("/deactivate/{admin_id}", summary="Deactivate admin")
@requires_feature_permission("edit")
async def deactivate_admin(
        current_user: CurrentUser,
        admin_id: str = Path(title="Admin Id")
    ):
    """
    This API is used to deactivate admin by id, This API can be Used by Super Admin only

    ### Path Parameters
    - **admin_id (str)**: The id of the admin user

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **422**: Custom Error (Error will be mentioned in `detail`)
    - **401**: Unauthorized/Not Enough Permissions
    - **400**: Bad Request

    ### Returns
    - **message (str)**: The message of the response
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await AdminCRUD().deactivate_admin(admin_id, user)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin.post("/login/", summary="Admin login")
# @require_redis_connection
async def login_for_access_token(
        request: Request,
        form_data: OAuth2PasswordRequestForm = Depends(),
        refresh_token: bool = False,
        device: str = "computer",
        device_info: str | None = None
):
    """
    login with valid access_token and token_type,
     and running background task of login activities,
    to the add the data of login user in login_activity_collection.
    """

    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": form_data.username}
    )
    if not user:
        raise HTTPException(status_code=404, detail=f"Wrong user_name.")

    is_college_level_user = False
    if user.get("role", {}).get("role_name") in ["college_super_admin", "college_counselor", "college_head_counselor"]:
        is_college_level_user = True

    toml_data = utility_obj.read_current_toml_file()
    if toml_data.get("testing", {}).get("test") is False:
        if user.get("role", {}).get("role_name") in ["super_admin", "admin", "super_account_manager", "account_manager", "client_admin"]:
            Reset_the_settings().get_user_database(
                str("628dfd41ef796e8f757a5c13"), form_data
            )
        else:
            Reset_the_settings().get_user_database(
                str(user.get("associated_colleges")[0]), form_data
            )

    data = await AuthenticateUser().authenticate_user(
        form_data.username,
        password=form_data.password,
        scopes=[user["role"]["role_name"]],
        refresh_token=refresh_token,
        request=request,
        is_college_level_user=is_college_level_user
    )

    if not data:
        raise HTTPException(status_code=400, detail="Data not valid.")
    client_ip = utility_obj.get_ip_address(request)
    await utility_obj.update_login_details(user.get("_id"), user, device, device_info, client_ip)
    await utility_obj.store_login_activity_helper(
        username=form_data.username, ip_address=client_ip
    )
    return data


@admin.delete(
    "/remove_by_id/{student_id}/",
    response_description="Remove student data",
    deprecated=True,
)
@requires_feature_permission("delete")
async def remove_student(
        current_user: CurrentUser,
        student_id: str = Path(
            ...,
            description="Id of a student you'd like"
                        " to remove \n*e.g.,"
                        "**6223040bea8c8768d96d3880**",
        ),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Remove Student using id\n
    * :*param* **id**:\n
    * :*return* **Remove Student details with message 'Student data
     removed successfully'**:
    """
    await UserHelper().check_user_has_permission(
        user_name=current_user, check_roles=["super_admin"], condition=True
    )
    student = await StudentUserCrudHelper().delete_student(
        student_id, ObjectId(college.get("id"))
    )
    if student:
        return utility_obj.response_model(student,
                                          "Student data removed successfully.")
    raise HTTPException(status_code=404, detail="Student Id doesn't exist!")


@admin.post(
    "/all_leads/",
    summary="Get All Students Data",
    response_description="Get all students details",
)
@requires_feature_permission("read")
async def get_all_leads_details(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        payload: payload_data = Body(None),
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        twelve_score_sort: bool = Query(
            None,
            description="Sort data based on 12th score. Send value true"
                        " if want data based on 12th score ascending values."
                        " Send value false if want data based on 12th"
                        " score descending values",
        ),
):
    """
    Get All Application Details Based on Filter Apply\n
    * :*param* **date_range** description="Get data based on date_range,
     pass sub-param start_date and sub-param
    end_date, date format will be YYYY-MM-DD", example='start_date':
     '2022-05-24' 'end_date': '2022-05-24' :\n
    * :*param* **state** description="Filter data based on state,
     pass sub-param state_b is True if want state_name
    in the resultant data, pass *sub-param* state_code (example="UP")
     if want data based on state_code":\n
    * :*param* **city** description="Filter data based on city,
     pass *sub-param* city_b is True if want city_name in
    the resultant data, pass sub-param city_name (example="Mathura")
     if want data based on city_name":\n
    * :*param* **source** description="Filter data based on source,
     pass sub-param source_b is True if want source_name
    in the resultant data, pass sub-param source_name (example="google")
     if want data based on source_name":\n
    * :*param* **lead_stage** description="Filter data based on lead_stage,
     pass sub-param lead_b is True if want
     lead_name in the resultant data, pass sub-param lead_name
      (example="Not Interested") if want data based on
      lead_name":\n
    * :*param* **lead_type** description="Filter data based on lead_type,
     pass sub-param lead_type_b is True if want
    lead_type_name in the resultant data, pass sub-param lead_type_name
     (example="API") if want data based on
     lead_type_name":\n
    * :*param* **counselor** description="Filter data based on counselor,
     pass sub-param counselor_b is True if want
    counselor_name in the resultant data, pass sub-param counselor_id
     (example="62de4653f3a898e4275962b7") if want
    data based on counselor":\n
    * :*param* **application_stage** description="Filter data based on
     application_stage, application stage can be
    any of the following: complete and incomplete, pass sub-param
     application_stage_name (example="incomplete")
    if want data based on application status":\n
    * :*param* **page_num** description="Enter page number where you want
     to show applications data", example=1:\n
    * :*param* **page_size** description="Enter page size means how many
     data you want to show on page_num", example=25:\n
    :*return* **Application data based on filter apply with message**:
    """
    user = await UserHelper().is_valid_user(current_user)
    role_name = user.get("role", {}).get("role_name", "")
    is_head_counselor = False
    if role_name in ["super_admin", "client_manager"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    try:
        payload, date_range, season = await get_payload_and_date_range(
            payload=payload)
        cache_key, data = cache_data
        if data:
            return data
        counselor_id, source_name, publisher = None, None, False
        if role_name == "college_counselor":
            counselor_id = [ObjectId(user.get("_id"))]
        elif role_name == "college_head_counselor":
            is_head_counselor = True
            counselor_id = await AdminUser().get_users_ids_by_role_name(
                "college_counselor", college.get("id"), user.get("_id")
            )
        elif role_name == "college_publisher_console":
            publisher = True
            source_name = user.get("associated_source_value", "").lower()
        all_data = await StudentApplicationHelper().get_all_application(
            payload=payload,
            page_num=page_num,
            page_size=page_size,
            college_id=college.get("id"),
            counselor_id=counselor_id,
            applications=False,
            source_name=source_name,
            publisher=publisher,
            twelve_score_sort=twelve_score_sort,
            is_head_counselor=is_head_counselor,
        )
        if cache_key:
            await insert_data_in_cache(cache_key, all_data)
        return all_data
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"An error got when get the " f"all leads details. Error - {error}",
        )


@admin.post(
    "/all_applications/",
    summary="Get All Student Application Data",
    response_description="Get all application details",
)
@requires_feature_permission("read")
async def get_all_application_details(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        form_initiated: bool = Query(True,
                                     description="Get application based on stage"),
        payload: payload_data | None = Body(None),
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        twelve_score_sort: bool | None = Query(
            None,
            description="Sort data based on 12th score. Send value true"
                        " if want data based on 12th score ascending values."
                        " Send value false if want data based on 12th"
                        " score descending values",
        ),
):
    """
    Get All Application Details Based on Filter Apply\n
    * :*param* **date_range** description="Get data based on date_range,
     pass sub-param start_date and sub-param
    end_date, date format will be YYYY-MM-DD", example='start_date':
     '2022-05-24' 'end_date': '2022-05-24' :\n
    * :*param* **state** description="Filter data based on state, pass
     sub-param state_b is True if want state_name
    in the resultant data, pass *sub-param* state_code (example="UP")
     if want data based on state_code":\n
    * :*param* **city** description="Filter data based on city,
    pass *sub-param* city_b is True if want city_name in
    the resultant data, pass sub-param city_name (example="Mathura")
     if want data based on city_name":\n
    * :*param* **source** description="Filter data based on source,
     pass sub-param source_b is True if want source_name
    in the resultant data, pass sub-param source_name (example="google")
    if want data based on source_name":\n
    * :*param* **lead_stage** description="Filter data based on lead_stage,
     pass sub-param lead_b is True if want
     lead_name in the resultant data, pass sub-param lead_name
     (example="Not Interested") if want data based on
      lead_name":\n
    * :*param* **lead_type** description="Filter data based on lead_type,
     pass sub-param lead_type_b is True if want
    lead_type_name in the resultant data, pass sub-param lead_type_name
     (example="API") if want data based on
     lead_type_name":\n
    * :*param* **counselor** description="Filter data based on counselor,
     pass sub-param counselor_b is True if want
    counselor_name in the resultant data, pass sub-param counselor_id
     (example="62de4653f3a898e4275962b7") if want
    data based on counselor":\n
    * :*param* **application_stage** description="Filter data based on
     application_stage, application stage can be
    any of the following: complete and incomplete, pass sub-param
     application_stage_name (example="incomplete")
    if want data based on application status":\n
    * :*param* **page_num** description="Enter page number where you want
     to show applications data", example=1:\n
    * :*param* **page_size** description="Enter page size means how many
     data you want to show on page_num", example=25:\n
    :*return* **Application data based on filter apply with message**:
    """
    user = await UserHelper().is_valid_user(current_user)
    role_name = user.get("role", {}).get("role_name", "")
    is_head_counselor = False
    if role_name in ["super_admin", "client_manager",
                     "college_publisher_console"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    try:
        payload, date_range, season = await get_payload_and_date_range(
            payload=payload)
        counselor_id = None
        if role_name == "college_counselor":
            counselor_id = [ObjectId(user.get("_id"))]
        if role_name == "college_head_counselor":
            is_head_counselor = True
            counselor_id = await AdminUser().get_users_ids_by_role_name(
                "college_counselor", college.get("id"), user.get("_id")
            )
        cache_key, data = cache_data
        if data:
            return data
        all_data = await StudentApplicationHelper().get_all_application(
            payload=payload,
            page_num=page_num,
            page_size=page_size,
            college_id=college.get("id"),
            counselor_id=counselor_id,
            form_initiated=form_initiated,
            twelve_score_sort=twelve_score_sort,
            is_head_counselor=is_head_counselor,
        )
        if cache_key:
            await insert_data_in_cache(cache_key, all_data)
        return all_data
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"An error got when get the "
                   f"applications details. Error - {error}",
        )


@admin.post(
    "/all_paid_applications/",
    summary="Get All paid Application Status",
    response_description="Get all paid application details",
)
@requires_feature_permission("read")
async def get_paid_application_details(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        payload: paid_application_payload = Body(None),
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        twelve_score_sort: bool = Query(
            None,
            description="Sort data based on 12th score. Send value true"
                        " if want data based on 12th score ascending values."
                        " Send value false if want data based on 12th score"
                        " descending values",
        ),
):
    """
    Get All Application Details Based on Filter Apply\n
    * :*param* **date_range** description="Get data based on date_range,
     pass sub-param start_date and sub-param
    end_date, date format will be YYYY-MM-DD",
    example='start_date': '2022-05-24' 'end_date': '2022-05-24' :\n
    * :*param* **state** description="Filter data based on state,
     pass sub-param state_b is True if want state_name
    in the resultant data, pass *sub-param* state_code
    (example="UP") if want data based on state_code":\n
    * :*param* **city** description="Filter data based on city,
     pass *sub-param* city_b is True if want city_name in
    the resultant data, pass sub-param city_name (example="Mathura")
     if want data based on city_name":\n
    * :*param* **source** description="Filter data based on source,
    pass sub-param source_b is True if want source_name
    in the resultant data, pass sub-param source_name (example="google")
     if want data based on source_name":\n
    * :*param* **lead_stage** description="Filter data based on lead_stage,
    pass sub-param lead_b is True if want
     lead_name in the resultant data, pass sub-param lead_name
      (example="Not Interested") if want data based on
      lead_name":\n
    * :*param* **lead_type** description="Filter data based on lead_type,
     pass sub-param lead_type_b is True if want
    lead_type_name in the resultant data, pass sub-param lead_type_name
    (example="API") if want data based on
     lead_type_name":\n
    * :*param* **counselor** description="Filter data based on counselor,
     pass sub-param counselor_b is True if want
    counselor_name in the resultant data, pass sub-param counselor_id
     (example="62de4653f3a898e4275962b7") if want
    data based on counselor":\n
    * :*param* **application_stage** description="Filter data based on
    application_stage, application stage can be
    any of the following: complete and incomplete, pass sub-param
    application_stage_name (example="incomplete")
    if want data based on application status":\n
    * :*param* **page_num** description="Enter page number where you want
     to show applications data", example=1:\n
    * :*param* **page_size** description="Enter page size means
     how many data you want to show on page_num", example=25:\n
    :*return* **Application data based on filter apply with message**:
    """
    user = await UserHelper().is_valid_user(current_user)
    role_name = user.get("role", {}).get("role_name", "")
    if role_name in ["super_admin", "client_manager",
                     "college_publisher_console"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    try:
        payload, date_range, season = await get_payload_and_date_range(
            payload=payload)
        counselor_id = None
        if role_name == "college_counselor":
            counselor_id = [ObjectId(user.get("_id"))]
        if role_name == "college_head_counselor":
            counselor_id = await AdminUser().get_users_ids_by_role_name(
                "college_counselor", college.get("id"), user.get("_id")
            )
        cache_key, data = cache_data
        if data:
            return data
        all_application_data, total = await PaidApplication().all_paid_applications(
            payload=payload,
            page_num=page_num,
            page_size=page_size,
            counselor_id=counselor_id,
            date_range=date_range,
            season=season,
            college_id=ObjectId(college.get("id")),
            twelve_score_sort=twelve_score_sort,
        )
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, total,
            route_name="/admin/all_paid_applications/"
        )
        all_data = {
            "data": all_application_data,
            "total": total,
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Applications data fetched successfully!",
        }
        if cache_key:
            await insert_data_in_cache(cache_key, all_data)
        return all_data
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"AN error got when get the "
                   f"all paid applications details. "
                   f"Error - {error}",
        )


@admin.post(
    "/upload_single_file/",
    response_description="Upload file in amazon s3 bucket then add file data",
)
@requires_feature_permission("write")
async def upload_single_file(
        background_tasks: BackgroundTasks,
        file: UploadFile,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
):
    """
    Upload File student  bulk data in  Database\n
    * :*param* file:\n
    * :*csv or excel:\n
    * :*return* **Upload  all students information into database with message
    '{"success": "data insert successfully"}'**:
    """
    await UserHelper().check_user_has_permission(current_user)
    if not file:
        return {"message": "No upload file sent"}
    data = await StudentHelper().upload_data_in_db(file, background_tasks, college)
    if data:
        return utility_obj.response_model(True,
                                          message="data insert successfully")
    raise HTTPException(status_code=404, detail="No found!")


def _is_csv(filename: str):
    """
    Upload File
    :param filename:
    :return:
    """
    valid_extension = ".csv"
    return filename.endswith(valid_extension)


@admin.get("/student_documents/",
           summary="Get student uploaded document details")
@requires_feature_permission("read")
async def student_documents(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        student_id: str = Query(..., description="Enter student id"),
        season: str = None,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get the details of Student's uploaded documents
    """
    await UserHelper().is_valid_user(current_user)
    try:
        file = await DatabaseConfiguration().studentSecondaryDetails.find_one(
            {"student_id": ObjectId(student_id)}
        )
    except Exception as error:
        raise HTTPException(
            status_code=422, detail=f"Invalid student id. " f"Error - {error}"
        )
    cache_key, data = cache_data
    if data:
        return data
    if file:
        if file.get("attachments"):
            result = await AdminBoardHelper().student_documents_info(
                file, student_id, season=season
            )
            all_data = utility_obj.response_model(
                result, message="File fetched successfully."
            )
            if cache_key:
                await insert_data_in_cache(cache_key, all_data, expiration_time=600)
            return all_data
        raise HTTPException(status_code=404, detail="Document not found.")
    raise HTTPException(status_code=404, detail="Document not found.")


@admin.post("/form_wise_record/{college_id}")
@requires_feature_permission("read")
async def form_wise_status(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        college_id: str = Path(..., description="Enter college id"),
        season: str = Body(
            None,
            description="Enter season value if want" " to get data season-wise"
        ),
        counselor_id: Optional[List[str]] = Body(None),
        date_range: DateRange | None = Body(None),
        school_names: Optional[list[str]] = Body(None),
        source: Optional[list[str]] = Body(None),
        change_indicator: ChangeIndicator = "last_7_days",
        preference: Optional[list[str]] = Body(None)
):
    """
    Return the data of Student's Application form
    college_id: str
    """
    cache_key, data = cache_data
    if data:
        return data
    data = await unique_code_for_graph(
        current_user=current_user,
        date_range=date_range,
        college_id=college_id,
        route="form_wise_record",
        counselor_id=counselor_id,
        season=season,
        change_indicator=change_indicator,
        school_names=school_names,
        source=source,
        preference=preference
    )
    if data:
        data = utility_obj.response_model(
            data=data, message="data fetched successfully."
        )
        if cache_key:
            await insert_data_in_cache(cache_key, data)
        return data
    return {"data": [[]], "message": "Form wise record data not found."}


@admin.post("/download_form_wise_status_data/{college_id}")
@requires_feature_permission("download")
async def download_form_wise_status_data(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        request: Request,
        college_id: Annotated[str, Path(..., description="Enter college id")],
        season: str = Body(
            None,
            description="Enter season value if want" " to get data season-wise"
        ),
        counselor_id: Optional[List[str]] = Body(None),
        date_range: DateRange = Body(None),
        school_names: Optional[list[str]] = Body(None),
        source: Optional[list[str]] = Body(None),
        change_indicator: ChangeIndicator = None,
        preference: Optional[list[str]] = Body(None)
):
    """downloads the csv file which stores the status of
     Student's Admission detail
    college_id: str
    date range format:- 2022-05-24
    """
    current_datetime = datetime.datetime.utcnow()
    data = await unique_code_for_graph(
        current_user=current_user,
        date_range=date_range,
        college_id=college_id,
        route="form_wise_record",
        counselor_id=counselor_id,
        season=season,
        change_indicator=change_indicator,
        school_names=school_names,
        source=source,
        preference=preference
    )
    if data:
        data_keys = list(data[0].keys())
        get_url = await upload_csv_and_get_public_url(
            fieldnames=data_keys,
            data=data,
            name="form_wise_status_data",
        )
        background_tasks.add_task(
            DownloadRequestActivity().store_download_request_activity,
            request_type="Form wise status data",
            requested_at=current_datetime,
            ip_address=utility_obj.get_ip_address(request),
            user=await UserHelper().check_user_has_permission(
                user_name=current_user),
            total_request_data=len(data),
            is_status_completed=True,
            request_completed_at=datetime.datetime.utcnow(),
        )
        return get_url
    return {"data": [[]], "message": "Form wise record data not found."}


@admin.put("/score_board/{college_id}")
@requires_feature_permission("read")
async def top_score_board(
        current_user: CurrentUser,
        college_id: Annotated[str, Path(..., description="Enter college id")],
        cache_data=Depends(cache_dependency),
        cache_change_indicator=Depends(change_indicator_cache),
        season: str = Body(
            None,
            description="Enter season name if want" " to get data season-wise"
        ),
        date_range: DateRange = Body(None),
        change_indicator: ChangeIndicator = None,
        application_type: str = "paid",
):
    """Returns the data of Admission status based on route 'score_board'
     and college_id and date_range
    college_id: str
    date range format:- 2022-05-24
    """
    user = await UserHelper().is_valid_user(user_name=current_user)
    cache_key, data = cache_data
    if data:
        return data
    date_range = await utility_obj.format_date_range(date_range)
    data = await AdminBoardHelper().score_board_helper(
        user=user,
        date_range=date_range,
        college_id=college_id,
        season=season,
        change_indicator=change_indicator,
        application_type=application_type,
        cache_change_indicator=cache_change_indicator,
    )
    if data:
        data = utility_obj.response_model(data=data,
                                          message="data fetch successfully")
        if cache_key:
            await insert_data_in_cache(cache_key, data)
        return data
    raise HTTPException(status_code=422, detail="data not found")


@admin.post("/download_data/{college_id}")
@requires_feature_permission("download")
async def download_data(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        request: Request,
        college_id: Annotated[str, Path(..., description="Enter college id")],
        season: str = Body(
            None,
            description="Enter season value if want" " to get data season-wise"
        ),
        date_range: DateRange = Body(None),
        change_indicator: ChangeIndicator = None,
        application_type: str = None,
):
    """
    Downloads the unique data of Student's Admission status in form of csv file
    college_id: str
    date range format:- 2022-05-24
    """
    user = await UserHelper().is_valid_user(user_name=current_user)
    current_datetime = datetime.datetime.utcnow()
    date_range = await utility_obj.format_date_range(date_range)
    data = await AdminBoardHelper().score_board_helper(
        user=user,
        date_range=date_range,
        college_id=college_id,
        season=season,
        change_indicator=change_indicator,
        application_type=application_type,
    )
    data_keys = list(data.keys())
    get_url = await upload_csv_and_get_public_url(fieldnames=data_keys,
                                                  data=data)
    background_tasks.add_task(
        DownloadRequestActivity().store_download_request_activity,
        request_type="Score board data",
        requested_at=current_datetime,
        ip_address=utility_obj.get_ip_address(request),
        user=await UserHelper().check_user_has_permission(
            user_name=current_user),
        total_request_data=1,
        is_status_completed=True,
        request_completed_at=datetime.datetime.utcnow(),
    )
    return get_url


@admin.put("/top_performing_channel/{college_id}")
@requires_feature_permission("read")
async def top_performing(
        current_user: CurrentUser,
        college_id: Annotated[str, Path(..., description="Enter college id")],
        season: str = Body(
            None,
            description="Enter season value if want" " to get data season-wise"
        ),
        cache_data=Depends(cache_dependency),
        cache_change_indicator=Depends(change_indicator_cache),
        date_range: DateRange = Body(None),
        program_name: list | None = Body(None),
        change_indicator: ChangeIndicator = "last_7_days",
):
    """
    Get the top performing channels data
    """
    await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    date_range = await utility_obj.format_date_range(date_range)
    data = await AdminBoardHelper().top_performing_channel(
        college_id,
        date_range,
        season,
        change_indicator,
        program_name,
        cache_change_indicator,
    )
    if data:
        data = utility_obj.response_model(data=data,
                                          message="data fetch successfully")
        if cache_key:
            await insert_data_in_cache(cache_key, data)
        return data
    raise HTTPException(status_code=422, detail="data not found")


@admin.post("/download_top_performing_channel_data/{college_id}")
@requires_feature_permission("download")
async def download_top_performing_channel_data(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        request: Request,
        college_id: Annotated[str, Path(..., description="Enter college id")],
        season: str = Body(
            None,
            description="Enter season value if want" " to get data season-wise"
        ),
        date_range: DateRange = Body(None),
        program_name: list | None = Body(None),
        change_indicator: ChangeIndicator = "last_7_days",
):
    """
    Download the data of top performing channels in csv format
    """
    user = await UserHelper().check_user_has_permission(user_name=current_user)
    current_datetime = datetime.datetime.utcnow()
    date_range = await utility_obj.format_date_range(date_range)
    data = await AdminBoardHelper().top_performing_channel(
        college_id, date_range, season, change_indicator, program_name
    )
    final_data = data.get("source_wise_lead", [])
    if final_data:
        data_keys = list(final_data[0].keys())
        get_url = await upload_csv_and_get_public_url(
            fieldnames=data_keys, data=final_data, name="applications_data"
        )
        background_tasks.add_task(
            DownloadRequestActivity().store_download_request_activity,
            request_type="Top performing channel data",
            requested_at=current_datetime,
            ip_address=utility_obj.get_ip_address(request),
            user=user,
            total_request_data=len(final_data),
            is_status_completed=True,
            request_completed_at=datetime.datetime.utcnow(),
        )
        return get_url
    raise HTTPException(status_code=422, detail="data not found")


@admin.put("/application_funnel/{college_id}")
@requires_feature_permission("read")
async def application_funnel(
        current_user: CurrentUser,
        college_id: Annotated[str, Path(description="Enter college id")],
        source: list = Body(None),
        season: str = Body(
            None,
            description="Enter season value if want" " to get data season-wise"
        ),
        date_range: DateRange = Body(None),
):
    """
    return the unique code for get data, with message : data fetch successfully
    college_id: str
    date range format:- 2022-05-24
    """
    user = await UserHelper().is_valid_user(user_name=current_user)
    user_id = user.get("_id")
    user_role = user.get("role", {}).get("role_name")
    counselor_id = None
    is_head_counselor = False
    if user_role in ["college_head_counselor", "college_counselor"]:
        if user_role == "college_head_counselor":
            is_head_counselor = True
            counselor_id = await AdminUser().get_users_ids_by_role_name(
                "college_counselor", college_id, user_id
            )
        else:
            counselor_id = [ObjectId(user_id)]
    if date_range:
        date_range = await utility_obj.format_date_range(date_range)
    data = await AdminBoardHelper().get_application_funnel_data(
        college_id=college_id,
        date_range=date_range,
        source=source,
        counselor_id=counselor_id,
        season=season,
        is_head_counselor=is_head_counselor,
    )
    if data:
        return utility_obj.response_model(data=data,
                                          message="data fetch successfully")
    raise HTTPException(status_code=404, detail="data not found")


@admin.post("/download_application_funnel_data/{college_id}")
@requires_feature_permission("download")
async def download_application_funnel_data(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        request: Request,
        college_id: Annotated[str, Path(..., description="Enter college id")],
        source: list = Body(None),
        season: str = Body(
            None,
            description="Enter season value if want" " to get data season-wise"
        ),
        date_range: DateRange = Body(None),
):
    """downloads the unique code of get data in csv format
    excluded with "payment_init_but_not_paid", "payment_not_initiated" field
    college_id: str
    date range format:- 2022-05-24
    """
    user = await UserHelper().is_valid_user(user_name=current_user)
    current_datetime = datetime.datetime.utcnow()
    user_id = user.get("_id")
    user_role = user.get("role", {}).get("role_name")
    counselor_id = None
    if user_role in ["college_head_counselor", "college_counselor"]:
        if user_role == "college_head_counselor":
            counselor_id = await AdminUser().get_users_ids_by_role_name(
                "college_counselor", college_id, user_id
            )
        else:
            counselor_id = [ObjectId(user_id)]
    data = await AdminBoardHelper().get_application_funnel_data(
        college_id=college_id,
        date_range=date_range,
        source=source,
        counselor_id=counselor_id,
        season=season,
    )
    data_keys = list(data.keys())
    get_url = await upload_csv_and_get_public_url(fieldnames=data_keys,
                                                  data=data)
    background_tasks.add_task(
        DownloadRequestActivity().store_download_request_activity,
        request_type="Application funnel data",
        requested_at=current_datetime,
        ip_address=utility_obj.get_ip_address(request),
        user=await UserHelper().check_user_has_permission(
            user_name=current_user),
        total_request_data=1,
        is_status_completed=True,
        request_completed_at=datetime.datetime.utcnow(),
    )
    return get_url


@admin.put("/lead_funnel/{college_id}")
@requires_feature_permission("read")
async def lead_funnel_application(
        current_user: CurrentUser,
        college_id: Annotated[str, Path(..., description="Enter college id")],
        cache_data=Depends(cache_dependency),
        season: str = Body(None, description="Enter season name"),
        date_range: DateRange = Body(None),
        change_indicator: ChangeIndicator = None,
):
    """return the unique code for get data with route 'declaration'
    college_id: str
    date range format:- 2022-05-24
    """
    await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    data = await unique_code_for_graph(
        current_user=current_user,
        date_range=date_range,
        college_id=college_id,
        route="declaration",
        season=season,
        lead_funnel=True,
        change_indicator=change_indicator,
    )
    if data:
        data = utility_obj.response_model(data=data,
                                          message="data fetch successfully")
        if cache_key:
            await insert_data_in_cache(cache_key, data)
        return data
    raise HTTPException(status_code=404, detail="data not found")


@admin.post("/download_lead_funnel_application_data/{college_id}")
@requires_feature_permission("download")
async def download_lead_funnel_application_data(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        request: Request,
        college_id: Annotated[str, Path(..., description="Enter college id")],
        season: str = Body(
            None,
            description="Enter season value if " "want to get data season-wise"
        ),
        date_range: DateRange = Body(None),
        change_indicator: ChangeIndicator = None,
):
    """
    Downloads the unique code of get data in csv format of route 'declaration'
    by excluding unnecessary fields like
        "payment_init_but_not_paid",
        "payment_not_initiated",
        "total_unpaid_application"
    college_id: str
    date range format:- 2022-05-24
    """
    await UserHelper().is_valid_user(current_user)
    current_datetime = datetime.datetime.utcnow()
    data = await unique_code_for_graph(
        current_user=current_user,
        date_range=date_range,
        college_id=college_id,
        route="declaration",
        season=season,
        lead_funnel=True,
        change_indicator=change_indicator,
    )
    for key in [
        "payment_init_but_not_paid",
        "payment_not_initiated",
        "unpaid_application",
    ]:
        data.pop(key)
    data_keys = list(data.keys())
    get_url = await upload_csv_and_get_public_url(
        fieldnames=data_keys,
        data=data,
    )
    background_tasks.add_task(
        DownloadRequestActivity().store_download_request_activity,
        request_type="Lead funnel application data",
        requested_at=current_datetime,
        ip_address=utility_obj.get_ip_address(request),
        user=await UserHelper().check_user_has_permission(
            user_name=current_user),
        total_request_data=1,
        is_status_completed=True,
        request_completed_at=datetime.datetime.utcnow(),
    )
    return get_url


@admin.put("/form_stage_wise/{college_id}")
@requires_feature_permission("read")
async def form_stage_wise_segregation(
        current_user: CurrentUser,
        college_id: Annotated[str, Path(..., description="Enter college id")],
        cache_data=Depends(cache_dependency),
        season: str = Body(
            None,
            description="Enter season value if want" " to get data season-wise"
        ),
        date_range: DateRange = Body(None),
):
    """returns student's admission detail/status according to college_id
    with route 'declaration'
    college_id: str
    date range format:- 2022-05-24
    """
    cache_key, data = cache_data
    if data:
        return data
    data = await unique_code_for_graph(
        current_user=current_user,
        date_range=date_range,
        college_id=college_id,
        route="declaration",
        season=season,
        form_stage_wise_segregation=True,
    )
    if data:
        data = utility_obj.response_model(data=data,
                                          message="data fetch successfully")
        if cache_key:
            await insert_data_in_cache(cache_key, data)
        return data
    raise HTTPException(status_code=404, detail="data not found")


@admin.post("/download_form_stage_wise_segregation_data/{college_id}")
@requires_feature_permission("download")
async def download_form_stage_wise_segregation_data(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        request: Request,
        college_id: Annotated[str, Path(..., description="Enter college id")],
        season: str = Body(
            None,
            description="Enter season value if" " want to get data season-wise"
        ),
        date_range: DateRange = Body(None),
):
    """downloads student's admission detail/status according
     to college_id in csv format
    college_id: str
    date range format:- 2022-05-24
    """
    current_datetime = datetime.datetime.utcnow()
    data = await unique_code_for_graph(
        current_user=current_user,
        date_range=date_range,
        college_id=college_id,
        route="declaration",
        season=season,
        form_stage_wise_segregation=True,
    )
    keys_to_remove = [
        "form_initiated",
        "payment_not_initiated",
        "unpaid_application",
    ]
    for key in keys_to_remove:
        data.pop(key)
    get_url = await upload_csv_and_get_public_url(
        fieldnames=[
            "total_initiated",
            "payment_init_but_not_paid",
            "paid_application",
            "form_submitted",
        ],
        data=data,
    )
    background_tasks.add_task(
        DownloadRequestActivity().store_download_request_activity,
        request_type="Form stage wise segregation data",
        requested_at=current_datetime,
        ip_address=utility_obj.get_ip_address(request),
        user=await UserHelper().check_user_has_permission(
            user_name=current_user),
        total_request_data=1,
        is_status_completed=True,
        request_completed_at=datetime.datetime.utcnow(),
    )
    return get_url


@admin.put("/lead_application/{college_id}")
@requires_feature_permission("read")
async def lead_application_graph(
        current_user: CurrentUser,
        college_id: Annotated[str, Path(..., description="Enter college id")],
        cache_data=Depends(cache_dependency),
        season: str | None = Body(None, description="Enter season name"),
        counselor_id: Optional[List[str] | None] = Body(None),
        date_range: DateRange = Body(None),
        source: list[str] | None = Body(None),
):
    """returns the data of route 'lead_application'
     with message : data fetch successfully
    college_id: str
    date range format:- 2022-05-24
    """
    cache_key, data = cache_data
    if data:
        return data
    data = await unique_code_for_graph(
        current_user=current_user,
        date_range=date_range,
        college_id=college_id,
        route="lead_application",
        counselor_id=counselor_id,
        season=season,
        source=source,
    )
    data = utility_obj.response_model(data=data,
                                      message="data fetch successfully")
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@admin.post("/download_lead_application_graph_data/{college_id}")
@requires_feature_permission("download")
async def download_lead_application_graph_data(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        request: Request,
        college_id: Annotated[str, Path(..., description="Enter college id")],
        season: str = Body(
            None,
            description="Enter season value if" " want to get data season-wise"
        ),
        counselor_id: Optional[List[str]] = Body(None),
        date_range: DateRange = Body(None),
        source: list[str] | None = Body(None),
):
    """Downloads the lead_application_graph_data in csv format
    college_id: str
    date range format:- 2022-05-24
    """
    current_datetime = datetime.datetime.utcnow()
    await UserHelper().is_valid_user(current_user)
    date_range = await utility_obj.format_date_range(date_range)
    data = await AdminBoardHelper().lead_application(
        college_id, date_range, counselor_id, season, source=source
    )
    get_url = await upload_csv_and_get_public_url(
        fieldnames=["date", "lead", "application"], data=data,
        name="lead_application"
    )
    background_tasks.add_task(
        DownloadRequestActivity().store_download_request_activity,
        request_type="Lead application graph data",
        requested_at=current_datetime,
        ip_address=utility_obj.get_ip_address(request),
        user=await UserHelper().check_user_has_permission(
            user_name=current_user),
        total_request_data=1,
        is_status_completed=True,
        request_completed_at=datetime.datetime.utcnow(),
    )
    return get_url


@admin.post(
    "/upload_colleges/",
    summary="Upload Colleges Data using CSV",
    status_code=200,
    description="***** Upload csv file to S3 then" " add csv data into database *****",
)
@requires_feature_permission("write")
async def upload_colleges(
        current_user: CurrentUser,
        file: UploadFile = File(...),
        season: str = None,
):
    """
    Upload csv file to S3 then add csv data into database\n
    * :*param* **file**:\n
    * :*param* **college_id**:\n
    * :*return* **Upload csv file to S3 then add csv data into database**:
    """
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not user:
        raise HTTPException(status_code=401, detail="Not enough permissions")
    role = await DatabaseConfiguration().role_collection.find_one(
        {"_id": ObjectId(user["role"]["role_id"])}
    )
    if not role["permission"]["add_client"]:
        raise HTTPException(status_code=401, detail="Not enough permissions")

    extension = PurePath(file.filename).suffix
    file_name = utility_obj.create_unique_filename(extension=extension)
    filename = file.filename
    file_format = _is_csv(filename)
    if not file_format:
        raise HTTPException(status_code=422,
                            detail="file format is not supported")
    file_copy = await utility_obj.temporary_path(file)
    season_year = utility_obj.get_year_based_on_season(season)
    aws_env = settings.aws_env
    base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
    path = (
        f"{utility_obj.get_university_name_s3_folder()}/{season_year}/"
        f"{settings.s3_assets_bucket_name}/"
    )
    uploads3 = await s3_client.upload_to_aws(
        local_file=file_copy.name,
        bucket=base_bucket,
        s3_file=f"{path}{file_name}",
    )

    if uploads3:
        csv_data = await s3_client.read_csv_from_s3(
            bucket_name=base_bucket, object_key=f"{path}{file_name}"
        )
        inserted_data = await CollegeHelper().add_csv_file_college_data_into_database(
            csv_data
        )
        if inserted_data:
            return utility_obj.response_model(
                inserted_data,
                message="Colleges data successfully " "inserted into the database.",
            )


@admin.post(
    "/upload_courses/",
    summary="Upload Courses Data using CSV",
    status_code=200,
    description="***** Upload csv file to S3 then" " add csv data into database *****",
)
@requires_feature_permission("write")
async def upload_courses(
        current_user: CurrentUser,
        file: UploadFile = File(...),
        college_id: str = Query(
            ...,
            description="College ID \n* e.g., **624e8d6a92cc415f1f578a24**"
        ),
        season: str = None,
):
    """
    Upload csv file to S3 then add csv data into database\n
    * :*param* **file**:\n
    * :*param* **college_id**:\n
    * :*return* **Upload csv file to S3 then add csv data into database**:
    """
    college = await DatabaseConfiguration().college_collection.find_one(
        {"_id": ObjectId(college_id)}
    )
    if not college:
        raise HTTPException(status_code=422, detail="College does not exist.")
    user = await UserHelper().check_user_has_permission(current_user)
    season_year = utility_obj.get_year_based_on_season(season)
    aws_env = settings.aws_env
    base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
    if user.get("associated_colleges"):
        for i in user.get("associated_colleges"):
            if str(i) == str(college.get("_id")):
                extension = PurePath(file.filename).suffix
                file_name = utility_obj.create_unique_filename(
                    extension=extension)
                file_name_1 = str(file_name)
                filename = file.filename
                file_format = _is_csv(filename)
                if not file_format:
                    raise HTTPException(
                        status_code=422, detail="file format is not supported"
                    )
                file_copy = await utility_obj.temporary_path(file)
                path = (
                    f"{utility_obj.get_university_name_s3_folder()}/"
                    f"{season_year}/{settings.s3_assets_bucket_name}/"
                    f"{file_name_1}"
                )
                uploads3 = await s3_client.upload_to_aws(
                    local_file=file_copy.name,
                    bucket=base_bucket,
                    s3_file=path,
                )

                if uploads3:
                    csv_data = await s3_client.read_csv_from_s3(
                        bucket_name=base_bucket,
                        object_key=path,
                    )
                    inserted_data = await CourseHelper().add_course_data_into_database(
                        csv_data, college_id
                    )
                    if inserted_data:
                        return utility_obj.response_model(
                            inserted_data,
                            message="Courses data successfully"
                                    " inserted into the database.",
                        )
    else:
        return HTTPException(status_code=422, detail="Not enough permissions.")


@admin.post(
    "/upload_files/",
    summary="Upload files on amazon bucket",
    status_code=200,
    description="***** Upload multiple files *****",
)
async def upload_multiple_file(
        college_documents: bool = Query(
            False,
            description="Send value true when uploading " "college document(s)"
        ),
        files: List[UploadFile] = File(...,
                                       description="Multiple files as UploadFile"),
        season: str = None,
):
    """
    Upload files on amazon bucket, with message
    "Files are uploaded successfully."
    """
    season_year = utility_obj.get_year_based_on_season(season)
    aws_env = settings.aws_env
    base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
    base_bucket_url = getattr(settings, f"s3_{aws_env}_base_bucket_url")
    if college_documents:
        upload_files = await upload_multiple_files_and_return_temporary_urls(
            files=files,
            bucket_name=base_bucket,
        )
    else:
        upload_files = await upload_multiple_files(
            files=files,
            bucket_name=base_bucket,
            base_url=base_bucket_url,
            path=f"{utility_obj.get_university_name_s3_folder()}/"
                 f"{season_year}/{settings.s3_assets_bucket_name}/",
        )
    if upload_files:
        return utility_obj.response_model(
            data=upload_files, message="Files are uploaded successfully."
        )
    raise HTTPException(status_code=500, detail="Failed to upload files.")


@admin.post(
    "/upload_student_data/",
    summary="Upload Student Data using CSV",
    status_code=200,
    description="***** Upload csv file to S3 then" " add csv data into database *****",
)
@requires_feature_permission("write")
async def upload_student_data(
        current_user: CurrentUser,
        request: Request,
        file: UploadFile = File(...),
        college_id: str = Query(
            ...,
            description="College ID \n* e.g., **624e8d6a92cc415f1f578a24**"
        ),
        season: str = None,
):
    """
    Upload csv file to S3 then add csv data into database\n
    * :*param* **college_id**: e.g. 624e8d6a92cc415f1f578a24\n
    * :*return* **Upload csv file to S3 then add csv data into database**:
    """
    college = await DatabaseConfiguration().college_collection.find_one(
        {"_id": ObjectId(college_id)}
    )
    if not college:
        raise HTTPException(status_code=422, detail="College does not exist.")
    user = await UserHelper().check_user_has_permission(current_user)
    aws_env = settings.aws_env
    base_bucket = getattr(Settings, f"s3_{aws_env}_base_bucket")
    if user.get("associated_colleges"):
        for i in user.get("associated_colleges"):
            if str(i) == str(college.get("_id")):
                extension = PurePath(file.filename).suffix
                file_name = utility_obj.create_unique_filename(
                    extension=extension)
                file_name_1 = str(file_name)
                filename = file.filename
                file_format = _is_csv(filename)
                if not file_format:
                    raise HTTPException(
                        status_code=422, detail="file format is not supported"
                    )
                file_copy = await utility_obj.temporary_path(file)

                uploads3 = await s3_client.upload_to_aws(
                    local_file=file_copy.name,
                    bucket=base_bucket,
                    s3_file=f"{utility_obj.get_university_name_s3_folder()}/"
                            f"{settings.s3_download_bucket_name}/{file_name_1}",
                )

                if uploads3:
                    csv_data = await s3_client.read_csv_from_s3(
                        bucket_name=base_bucket,
                        object_key=f"{utility_obj.get_university_name_s3_folder()}/{settings.s3_download_bucket_name}/{file_name_1}",
                    )
                    inserted_data = (
                        await StudentUserCrudHelper().add_student_data_into_database(
                            csv_data, college_id, user, request
                        )
                    )
                    if inserted_data:
                        return utility_obj.response_model(
                            inserted_data,
                            message="Student data successfully"
                                    " inserted into the database.",
                        )
            else:
                return {"message": "college_id not matched"}
    else:
        return HTTPException(status_code=422, detail="Not enough permissions.")


@admin.get("/college_name")
@requires_feature_permission("read")
async def college_lead_name(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency)
):
    """
    Returns the data of college associated with user
    """
    cache_key, data = cache_data
    if data:
        return data
    data = await AdminDashboardHelper().college_data(current_user)
    if data:
        data = utility_obj.response_model(data=data,
                                          message="data fetch successfully")
        if cache_key:
            await insert_data_in_cache(cache_key, data)
        return data


@admin.get("/get_user_permission")
@requires_feature_permission("read")
async def get_user_permissions(current_user: CurrentUser,
                               season: str | None = None):
    """
    Returns the permissions and menus of user according to role_type
    """
    if season == "":
        season = None
    user = None
    if (
            await DatabaseConfiguration(season=season).studentsPrimaryDetails.find_one(
                {"user_name": current_user.get("user_name")}
            )
    ) is None:
        if (
                user := await DatabaseConfiguration().user_collection.find_one(
                    {"user_name": current_user.get("user_name")}
                )
        ) is None:
            raise HTTPException(status_code=404, detail="user not found")
    if (
            data := await DatabaseConfiguration().role_collection.find_one(
                {"role_name": user.get("role", {}).get("role_name") if user else "student"}
            )
    ) is None:
        raise HTTPException(status_code=404, detail="user type not found")
    data = RoleHelper().role_serialize(data)
    return utility_obj.response_model(data=data,
                                      message="data fetch successfully")


@admin.post("/download_applications_data/")
@requires_feature_permission("download")
async def download_applications_data(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        request: Request,
        application_ids: list[str] = None,
        payload: ApplicationFilterOptions = Body(None),
        course: CourseFilter = Body(None),
        payment_status: list[str] = Body(None),
        column_names: list[str] = None,
        college: dict = Depends(get_college_id),
        form_initiated: bool = Query(True,
                                     description="Get application based on stage"),
        twelve_score_sort: bool = Query(
            None,
            description="Sort data based on 12th score. Send value true"
                        " if want data based on 12th score ascending values."
                        " Send value false if want data based on 12th"
                        " score descending values",
        ),
):
    """
    Download application data by ids, based on filter
    """
    current_datetime = datetime.datetime.utcnow()
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not user:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    if (
            user.get("role", {}).get("role_name") == "super_admin"
            or user.get("role", {}).get("role_name") == "client_manager"
    ):
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    all_applicants = []
    payload, date_range, season = await get_payload_and_date_range(payload)
    course = jsonable_encoder(course)
    if payload or course or payment_status:
        payload.update(
            {
                "course": course,
                "payment_status": payment_status,
                "college_id": college.get("id"),
            }
        )
        if date_range:
            date_range = {k: v for k, v in date_range.items() if v is not None}
        payload = {k: v for k, v in payload.items() if v is not None}
        publisher = False
        if user.get("role", {}).get("role_name") == "college_counselor":
            payload["counselor_id"] = [str(user.get("_id"))]
        elif user.get("role", {}).get(
                "role_name") == "college_publisher_console":
            publisher = True
        application_ids = await AdminBoardHelper().get_application_ids(
            payload=payload,
            date_range=date_range,
            publisher=publisher,
            user=user,
            form_initiated=form_initiated,
            twelve_score_sort=twelve_score_sort,
        )
    if application_ids:
        for _id in application_ids:
            await utility_obj.is_id_length_valid(_id=_id,
                                                 name="Application id")
            application = (
                await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"_id": ObjectId(_id),
                     "college_id": ObjectId(college.get("id"))}
                )
            )
            if not application:
                raise HTTPException(
                    status_code=422,
                    detail=f"Either application id '{_id}' not exist or"
                           f" you don't have access to download details of "
                           f"application.",
                )
            all_applicants.append({"id": str(application["_id"])})
    data = await StudentApplicationHelper().get_data(
        all_applicants=all_applicants, column_names=column_names, user=user
    )
    background_tasks.add_task(
        DownloadRequestActivity().store_download_request_activity,
        request_type="Applications data",
        requested_at=current_datetime,
        ip_address=utility_obj.get_ip_address(request),
        user=user,
        total_request_data=len(data),
        is_status_completed=True,
        request_completed_at=datetime.datetime.utcnow(),
    )
    if data:
        for item in data:
            item.pop("application_id")
        data_keys = list(data[0].keys())
        get_url = await upload_csv_and_get_public_url(
            fieldnames=data_keys, data=data, name="applications_data"
        )
        return get_url
    raise HTTPException(status_code=404, detail="No found.")


@admin.post("/download_leads/")
@requires_feature_permission("download")
async def download_leads_data(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        request: Request,
        student_ids: list[str] = None,
        payload: payload_data = Body(None),
        college: dict = Depends(get_college_id),
        twelve_score_sort: bool = Query(
            None,
            description="Sort data based on 12th score. Send value true"
                        " if want data based on 12th score ascending values."
                        " Send value false if want data based on 12th"
                        " score descending values",
        ),
):
    """
    Download leads data by ids or based on filter
    """
    current_datetime = datetime.datetime.utcnow()
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not user:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    role_name = user.get("role", {}).get("role_name", "")
    if role_name in ["super_admin", "client_manager"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    start_date, end_date = None, None
    payload, date_range, season = await get_payload_and_date_range(
        payload=payload)
    if not student_ids:
        date_range = await utility_obj.get_valid_date_range(date_range)
        start_date, end_date = await utility_obj.date_change_format(
            date_range.get("start_date"), date_range.get("end_date")
        )
    publisher, counselor_id = False, None
    if role_name == "college_counselor":
        counselor_id = [str(user.get("_id"))]
    elif role_name == "college_publisher_console":
        publisher = True
    student_obj = Student()
    pipeline = await student_obj.pipeline_for_view_all_leads(
        start_date,
        end_date,
        payload,
        counselor_id,
        student_ids=student_ids,
        twelve_score_sort=twelve_score_sort,
        publisher=publisher,
        source_name=(
            user.get("associated_source_value",
                     "").lower() if publisher else None
        ),
    )
    data, total_data = await student_obj.get_leads_data_with_count(
        pipeline=pipeline, payload=payload, total_data=0, publisher=publisher
    )
    background_tasks.add_task(
        DownloadRequestActivity().store_download_request_activity,
        request_type="Leads data",
        requested_at=current_datetime,
        ip_address=utility_obj.get_ip_address(request),
        user=user,
        total_request_data=len(data),
        is_status_completed=True,
        request_completed_at=datetime.datetime.utcnow(),
    )
    if data:
        data_keys = list(data[0].keys())
        get_url = await upload_csv_and_get_public_url(
            fieldnames=data_keys, data=data, name="applications_data"
        )
        return get_url
    raise HTTPException(status_code=404, detail="No found.")


@admin.post(
    "/all_applications_by_email/",
    summary="Get All Student Application Details by Email",
    response_description="Get all application details",
)
@requires_feature_permission("read")
async def get_all_application_details(
        current_user: CurrentUser,
        date_range: DateRange = Body(None),
        search_input: str = Query(None, description="Enter search pattern"),
        page_size: Union[int, None] = Query(None, gt=0),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        is_interview: Union[bool, None] = Query(None),
        basic_details: Union[bool, None] = Query(None),
        course: str = Query(None),
        specialization_name: str = Query(None),
        page_num: Union[int, None] = Query(None, gt=0),
        client=Depends(utility_obj.get_meili_client),
):
    """
    Get the search result of all application data from the database

    params:
        date_range: Date range to be start date and last date.
        search_input (str): search the result based on user input.
        current_user (str): current user to be authenticated.
        page_size (int): number of results to be returned.
        college (dict): dictionary of college information.
        is_interview (bool): default is None, value can be given true or
               false and false will return who interview is not schedule.
        basic_details (bool): default is None and
            value should be true or false.
        course (str): filter by course name.
        specialization_name (str): filter by specialization name.
        page_num (int): number of results to be return.
        client (generic): generic request object for pipeline execution
                            with meili search.
    return:
        Response: Response list containing information

    """
    user = await UserHelper().check_user_has_permission(current_user)
    try:
        filters = [f"college_id={college.get('id')}"]
        if date_range:
            date_range = jsonable_encoder(date_range)
            start_date, end_date = await utility_obj.date_change_format_unix_time(
                date_range.get("start_date"), date_range.get("end_date")
            )
            filters.append(
                [f"created_at >= {start_date} AND created_at <= {end_date}"])
        if user["role"]["role_name"] == "college_publisher_console":
            filters.append(
                [f"source={str(user.get('associated_source_value'))}"])
        elif user["role"]["role_name"] == "college_head_counselor":
            counselor_list = await get_counselor_list(college, user.get("_id"))
            filters.append([f"counselor_id IN {counselor_list}"])
        elif user["role"]["role_name"] == "college_counselor":
            filters.append([f"counselor_id={str(user.get('_id'))}"])
        if is_interview is not None:
            filters.append([f"is_interview={is_interview}"])
        if basic_details:
            filters.append([f"application_stage>2"])
        if course is not None:
            filters.append([f"course='{str(course)}'"])
        if specialization_name is not None:
            filters.append(
                [f"specialization_name='{str(specialization_name)}'"])

        name = f"{settings.client_name.lower().replace(' ', '_')}_{settings.current_season.lower()}"
        all_application = client.index(f"{name}_student_application").search(
            search_input,
            {
                "filter": filters,
                "showMatchesPosition": True,
                "attributesToHighlight": ["*"],
                "highlightPreTag": "<span class='search-" "query-highlight'>",
                "highlightPostTag": "</span>",
                "hitsPerPage": page_size,
                "page": page_num,
            },
        )
        logger.info(
            f"Fetched {len(all_application.get('hits', []))} "
            f"student applications for college {college.get('id')}"
        )
        return {
            "data": all_application.get("hits"),
            "count": all_application.get("totalHits"),
            "page_size": all_application.get("hitsPerPage"),
            "page_num": all_application.get("page"),
            "message": "Fetched student data successfully",
        }
    except MeilisearchCommunicationError as meil_error:
        logger.error(f"Error - {str(meil_error.args)}")
        raise HTTPException(status_code=404,
                            detail="meilisearch server is not running")
    except MeilisearchApiError as meil_error:
        logger.error(f"Error - {str(meil_error.args)}")
        raise HTTPException(status_code=404, detail=str(meil_error.args))
    except Exception as e:
        logger.error(f"Error - {str(e.args)}")
        raise HTTPException(status_code=404, detail=str(e.args))


@admin.put("/source_wise_detail")
@requires_feature_permission("read")
async def source_wise(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        cache_change_indicator=Depends(change_indicator_cache),
        season: str = Body(
            None,
            description="Enter season value if" " want to get data season-wise"
        ),
        lead_type: Optional[str] = None,
        date_range: DateRange = Body(None),
        mode: str | None = Body(None),
        change_indicator: ChangeIndicator = "last_7_days",
        sort: str = None,
        sort_type: str = Query(None,
                               description="Sort_type can be 'asc' or 'dsc'"),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    **input lead type:**/n
    **API, Online**/n
    **return data by source name**
    """
    await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    date_range = await utility_obj.format_date_range(date_range)
    source = await AdminBoardHelper().source_wise_application(
        date_range=date_range,
        sort=sort,
        sort_type=sort_type,
        lead_type=lead_type,
        season=season,
        change_indicator=change_indicator,
        cache_change_indicator=cache_change_indicator,
        lead_stage_list=college.get("lead_stage_label"),
        mode=mode
    )
    source.update({"message": "data fetch successfully"})
    if cache_key:
        await insert_data_in_cache(cache_key, source)
    return source


@admin.put("/download_source_wise_details")
@requires_feature_permission("download")
async def download_source_wise_details(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        request: Request,
        season: str = Body(
            None,
            description="Enter season value if" " want to get data season-wise"
        ),
        date_range: DateRange = Body(None),
        mode: str | None = Body(None),
        change_indicator: ChangeIndicator = "last_7_days",
        lead_type: Optional[str] = None,
        sort: str = None,
        sort_type: str = Query(None,
                               description="Sort_type can be 'asc' or 'dsc'"),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Downloads the source wise details in form of csv file
    college_id: str
    date range format:- 2022-05-24
    """
    await UserHelper().is_valid_user(user_name=current_user)
    current_datetime = datetime.datetime.utcnow()
    date_range = await utility_obj.format_date_range(date_range)
    source = await AdminBoardHelper().source_wise_application(
        date_range=date_range,
        sort=sort,
        sort_type=sort_type,
        lead_type=lead_type,
        season=season,
        change_indicator=change_indicator,
        download_function=True,
        lead_stage_list=college.get("lead_stage_label"),
        mode=mode
    )
    data_keys = list(source[0].keys())
    get_url = await upload_csv_and_get_public_url(
        fieldnames=data_keys, data=source, name="applications_data"
    )
    background_tasks.add_task(
        DownloadRequestActivity().store_download_request_activity,
        request_type="Source wise details",
        requested_at=current_datetime,
        ip_address=utility_obj.get_ip_address(request),
        user=await UserHelper().check_user_has_permission(
            user_name=current_user),
        total_request_data=1,
        is_status_completed=True,
        request_completed_at=datetime.datetime.utcnow(),
    )
    return get_url


@admin.get("/get_source_name/")
@requires_feature_permission("read")
async def get_source_name(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    returns the unique utm sources in list with message
     'data getch successfully'
    :param current_user:
    :return: all source name
    """
    await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
        [
            {
                "$group": {
                    "_id": "",
                    "source": {
                        "$addToSet": "$source.primary_source" ".utm_source"},
                }
            }
        ]
    )
    utm = []
    async for data in result:
        utm = data.get("source", [])
    data = utility_obj.response_model(data=utm,
                                      message="data getch successfully")
    if cache_key:
        await insert_data_in_cache(cache_key, data, expiration_time=1800)
    return data


@admin.get("/users_by_college_id")
@requires_feature_permission("read")
async def users_by_colleges(
        current_user: CurrentUser,
        college_id: str,
        cache_data=Depends(cache_dependency),
):
    """
    take input as college id
    return all user with role name
    """
    await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    if len(college_id) != 24:
        raise HTTPException(
            status_code=401,
            detail=f"{college_id} is not a valid ObjectId, "
                   f"it must be a 12-byte input or a 24-character hex string",
        )
    data = await AdminDashboardHelper().get_users_by_college_id(college_id)
    data = utility_obj.response_model(data=data,
                                      message="data fetched successfully")
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@admin.delete("/delete_student_by_email_id")
@requires_feature_permission("delete")
async def delete_student_by_email_id(
        testing: Is_testing,
        email_ids: list[str],
        current_user: CurrentUser,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Checking whether the given student email is present in
    the student primary details collection,
    if present delete all the matched records of student from
    all other collection also
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not user or user.get("role", {}).get("role_name") != "super_admin":
        return {"message": "Not enough permissions"}

    for email in email_ids:
        student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"user_name": email, "college_id": ObjectId(college.get("id"))}
        )

        if not student:
            continue
        student_id = student["_id"]
        applications = await DatabaseConfiguration().studentApplicationForms.aggregate(
            [
                {
                    '$match': {
                        'student_id': student_id
                    }
                }, {
                '$group': {
                    '_id': None,
                    'ids': {
                        '$push': '$_id'
                    }
                }
            }, {
                '$project': {
                    '_id': 0,
                    'ids': 1
                }
            }
            ]
        ).to_list(None)

        application_ids = []
        if applications:
            application_ids = applications[0].get("ids", [])

        # Delete from activity_email collection
        await DatabaseConfiguration().activity_email.delete_many(
            {"email_list.student_id": student_id}
        )

        # Delete from application_payment_invoice collection
        await DatabaseConfiguration().application_payment_invoice_collection.delete_many(
            {"student_email_id": email}
        )

        # Delete from call_activity collection
        await DatabaseConfiguration().call_activity_collection.delete_many({
            "$or": [
                {"application": {"$in": application_ids}},
                {"call_to_number": int(student.get("basic_details", {}).get("mobile_number"))},
                {"call_from_number": int(student.get("basic_details", {}).get("mobile_number"))}
            ]
        })

        # Delete from communication_log collection
        await DatabaseConfiguration().communication_log_collection.delete_many(
            {"student_id": student_id}
        )

        # Handle data segment collection updates
        data_segments = await DatabaseConfiguration().data_segment_mapping_collection.find(
            {"student_id": student_id},
            {"data_segment_id": 1, "_id": 0}
        ).to_list(length=None)

        data_segment_ids = [doc["data_segment_id"] for doc in data_segments]

        for segment_id in data_segment_ids:
            segment = await DatabaseConfiguration().data_segment_collection.find_one({"_id": segment_id})
            if segment:
                count_at_origin = (segment.get("count_at_origin", 0) or 0) - 1
                data_count = (segment.get("data_count", 0) or 0) - 1

                await DatabaseConfiguration().data_segment_collection.update_one(
                    {"_id": segment_id},
                    {
                        "$set": {
                            "count_at_origin": max(0, count_at_origin),
                            "data_count": max(0, data_count)
                        }
                    }
                )

        # Delete from data_segment_mapping collection
        await DatabaseConfiguration().data_segment_mapping_collection.delete_many(
            {"student_id": student_id}
        )

        # Delete from leadsFollowUp collection
        await DatabaseConfiguration().leadsFollowUp.delete_many(
            {"student_id": student_id}
        )

        # Delete from notification collection
        await DatabaseConfiguration().notification_collection.delete_many(
            {"student_id": student_id}
        )

        # Update offer_letter_list collection
        await DatabaseConfiguration().offer_letter_list_collection.update_many(
            {},
            {
                "$pull": {
                    "eligible_applicants": {"$in": application_ids},
                    "initial_applicants": {"$in": application_ids},
                    "total_applicants": {"$in": application_ids},
                    "ineligible_applicants": {"$in": application_ids}
                }
            }
        )

        # Update offer letter counts
        offer_letter_data = DatabaseConfiguration().offer_letter_list_collection.find({})
        async for doc in offer_letter_data:
            eligible_count = len(doc.get("eligible_applicants", []))
            ineligible_count = len(doc.get("ineligible_applicants", []))
            initial_count = len(doc.get("initial_applicants", []))
            total_count = len(doc.get("total_applicants", []))

            if (doc.get("eligible_applicants_count") != eligible_count or
                    doc.get("initial_applicants_count") != initial_count or
                    doc.get("total_applicants_count") != total_count or
                    doc.get("ineligible_applicants_count") != ineligible_count
            ):
                await DatabaseConfiguration().offer_letter_list_collection.update_one(
                    {"_id": doc["_id"]},
                    {
                        "$set": {
                            "eligible_applicants_count": eligible_count,
                            "ineligible_applicants_count": ineligible_count,
                            "initial_applicants_count": initial_count,
                            "total_applicants_count": total_count
                        }
                    }
                )

        # Delete from payment collection
        await DatabaseConfiguration().payment_collection.delete_many(
            {"user_id": student_id}
        )

        # Update promocode collection
        await DatabaseConfiguration().promocode_collection.update_many(
            {},
            {
                "$pull": {
                    "applied_by": {"application_id": {"$in": application_ids}}
                }
            }
        )

        # Update promocode counts
        promocode_data = DatabaseConfiguration().promocode_collection.find({})
        async for doc in promocode_data:
            applied_count = len(doc.get("applied_by", []))
            if doc.get("applied_count") != applied_count:
                await DatabaseConfiguration().promocode_collection.update_one(
                    {"_id": doc["_id"]},
                    {
                        "$set": {
                            "applied_count": applied_count
                        }
                    }
                )

        # Delete from queries collection
        await DatabaseConfiguration().queries.delete_many(
            {"student_id": student_id}
        )

        # Update scholarship collection
        await DatabaseConfiguration().scholarship_collection.update_many(
            {},
            {
                "$pull": {
                    "initial_eligible_applicants": {"$in": application_ids},
                    "offered_applicants": {"$in": application_ids},
                    "delist_applicants": {"$in": application_ids}
                }
            }
        )

        # Update scholarship counts
        scholarship_data = DatabaseConfiguration().scholarship_collection.find({})
        async for doc in scholarship_data:
            initial_eligible_applicants_count = len(doc.get("initial_eligible_applicants", []))
            offered_applicants_count = len(doc.get("offered_applicants", []))
            delist_applicants_count = len(doc.get("delist_applicants", []))

            if (doc.get("initial_eligible_applicants_count") != initial_eligible_applicants_count or
                    doc.get("offered_applicants_count") != offered_applicants_count or
                    doc.get("delist_applicants_count") != delist_applicants_count
            ):
                await DatabaseConfiguration().scholarship_collection.update_one(
                    {"_id": doc["_id"]},
                    {
                        "$set": {
                            "initial_eligible_applicants_count": initial_eligible_applicants_count,
                            "offered_applicants_count": offered_applicants_count,
                            "delist_applicants_count": delist_applicants_count
                        }
                    }
                )

        # Delete from sms_activity collection
        await DatabaseConfiguration().sms_activity.delete_many(
            {"send_to": student.get("basic_details", {}).get("mobile_number")}
        )

        # Delete from studentApplicationForms collection
        await DatabaseConfiguration().studentApplicationForms.delete_many(
            {
                "student_id": student_id,
                "college_id": ObjectId(college.get("id")),
            }
        )

        # Delete from studentSecondaryDetails collection
        await DatabaseConfiguration().studentSecondaryDetails.delete_many(
            {"student_id": student_id}
        )

        # Delete from studentTimeline collection
        await DatabaseConfiguration().studentTimeline.delete_many(
            {"student_id": student_id}
        )

        # Delete from studentsPrimaryDetails collection
        await DatabaseConfiguration().studentsPrimaryDetails.delete_many(
            {"_id": student_id,
             "college_id": ObjectId(college.get("id"))}
        )

        # Update voucher collection
        voucher_data = DatabaseConfiguration().voucher_collection.find({
            "vouchers.used_by.student_id": student_id
        })

        async for voucher_doc in voucher_data:
            updated_vouchers = []
            updated = False

            for voucher in voucher_doc.get("vouchers", []):
                used_by = voucher.get("used_by", {})
                if used_by and used_by.get("student_id") == student_id:
                    voucher["used"] = False
                    voucher["used_by"] = {}
                    updated = True
                updated_vouchers.append(voucher)

            if updated:
                await DatabaseConfiguration().voucher_collection.update_one(
                    {"_id": voucher_doc["_id"]},
                    {
                        "$set": {
                            "vouchers": updated_vouchers
                        }
                    }
                )

    return {"message": "Records deleted successfully"}


@admin.get("/remove_students_by_source_name/")
@requires_feature_permission("delete")
async def remove_students_by_source_name(
        source_name: str,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Getting the student_id from studentsPrimaryDetails
    deleting all the details of matched student_ids from other collections
    """
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not user:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")

    if user.get("role", {}).get("role_name") == "super_admin":
        source_name = source_name.lower()

        data = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            [
                {"$match": {"source.primary_source.utm_source": source_name}},
                {"$project": {"_id": 1}},
            ]
        )

        students = [source async for source in data]
        if len(students) == 0:
            raise HTTPException(
                status_code=404,
                detail=f" No Data Found in with Source = {source_name} ",
            )

        ids = [_id for _id in set([dict(s).get("_id") for s in students]) if
               _id]
        deletes = [
            DatabaseConfiguration().studentsPrimaryDetails.delete_many(
                {"_id": {"$in": ids},
                 "college_id": ObjectId(college.get("id"))}
            ),
            DatabaseConfiguration().studentSecondaryDetails.delete_many(
                {"student_id": {"$in": ids}}
            ),
            DatabaseConfiguration().studentTimeline.delete_many(
                {"student_id": {"$in": ids}}
            ),
            DatabaseConfiguration().studentApplicationForms.delete_many(
                {"student_id": {"$in": ids},
                 "college_id": ObjectId(college.get("id"))}
            ),
            DatabaseConfiguration().queries.delete_many(
                {"student_id": {"$in": ids}}),
            DatabaseConfiguration().leadsFollowUp.delete_many(
                {"student_id": {"$in": ids}}
            ),
        ]
        # asyncio.gather fires all 7 requests in parallel,
        # but depending on the driver's connection pool settings,
        # Request may wait for a free socket.
        await asyncio.gather(*deletes)
        return {
            "message": f"Deleted student records whose "
                       f"utm_source named {source_name}"
        }
    else:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")


@admin.get("/get_usernames_by_pattern")
@requires_feature_permission("read")
async def get_usernames_by_pattern(
        username: str,
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    get the List of application details of username based on matched
     string of username
    """
    user = await DatabaseConfiguration().user_collection.find_one(
        {
            "user_name": current_user.get("user_name"),
            "associated_colleges": {"$in": [ObjectId(college.get("id"))]},
        }
    )
    if not user:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")

    if user.get("role", {}).get("role_name") not in ["super_admin",
                                                     "client_manager"]:
        cache_key, data = cache_data
        if data:
            return data
        users = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            [{"$project": {"_id": 0, "user_name": 1}}]
        )

        emails = [data.get("user_name") async for data in users]
        expression = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
        result = [i for i in expression.findall(str(emails)) if username in i]

        all_applicants = []
        try:
            for email_id in result:
                applicants = await Application().all_applications_by_email(
                    email=email_id, college_id=college.get("id")
                )
                all_applicants.append(applicants)

        except Exception as e:
            logger.error(f"Error - {str(e.args)}")
        data = []

        for applicant in all_applicants:
            if applicant:
                async for doc in applicant:
                    city = await DatabaseConfiguration().city_collection.find_one(
                        {"_id": doc.get("city_id")}
                    )
                    doc["state_name"] = city["state_name"]
                    doc["city_name"] = city["name"]
                    data.append(
                        StudentApplicationHelper().application_details_helper(
                            doc)
                    )

        if data:
            if page_num and page_size:
                total = len(data)

                response = await utility_obj.pagination_in_api(
                    page_num,
                    page_size,
                    data,
                    total,
                    route_name="/admin/all_applications_by_email/",
                )
                data = {
                    "data": response["data"],
                    "total": total,
                    "count": page_size,
                    "pagination": response["pagination"],
                    "message": "Applications data fetched successfully!",
                }
                if cache_key:
                    await insert_data_in_cache(cache_key, data)
                return data

        if len(result) == 0:
            raise HTTPException(status_code=404, detail="username not found")

        return {"message": "data fetched successfully", "result": data}
    else:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")


@admin.post(
    "/download_documents/{student_id}/",
    summary="Download all student documents"
)
@requires_feature_permission("download")
async def download_documents(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        request: Request,
        student_id: str = Path(..., description="Enter student id"),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Download All Student Documents
    * :*return* **Zip file url which will download all student documents**:
    """
    await UserHelper().is_valid_user(current_user)
    current_datetime = datetime.datetime.utcnow()
    await utility_obj.is_id_length_valid(_id=student_id, name="Student id")
    data = await get_primary_sec_download_link(student_id,
                                               ObjectId(college.get("id")))
    background_tasks.add_task(
        DownloadRequestActivity().store_download_request_activity,
        request_type="Student documents",
        requested_at=current_datetime,
        ip_address=utility_obj.get_ip_address(request),
        user=await UserHelper().check_user_has_permission(
            user_name=current_user),
        total_request_data=1,
        is_status_completed=True,
        request_completed_at=datetime.datetime.utcnow(),
    )
    return utility_obj.response_model(data={"zip_url": data},
                                      message="Get zip url")


@admin.put("/get_lead_detail_by_number")
@requires_feature_permission("read")
async def get_lead_data_by_mobile_number(
        current_user: CurrentUser,
        mobile_number: str,
        cache_data=Depends(cache_dependency),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    get lead detail based on mobile number
    """
    if (
            user := await DatabaseConfiguration().user_collection.find_one(
                {
                    "user_name": current_user.get("user_name"),
                    "role.role_name": "college_counselor",
                    "associated_colleges": {
                        "$in": [ObjectId(college.get("id"))]},
                }
            )
    ) is None:
        raise HTTPException(status_code=401, detail="Not enough permissions")
    cache_key, data = cache_data
    if data:
        return data
    data = await AdminBoardHelper().get_lead_detail_by_number(
        mobile_number, user, ObjectId(college.get("id"))
    )
    data = {"data": data, "message": "data fetch successfully"}
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@admin.post("/filter/add/", summary="Save/Add filter")
@requires_feature_permission("write")
async def save_filter(
        current_user: CurrentUser,
        paid_applications_filter: bool = Query(
            False,
            description="Want to save paid application filter " "then pass value as True",
        ),
        leads_filter: bool = Query(
            False,
            description="Want to save lead filter then" " pass value as True"
        ),
        forms_filter: bool = Query(
            False,
            description="Want to save form filter then" " pass value as True"
        ),
        document_filter: bool = Query(
            False,
            description="Want to save document verification filter then" " pass value as True"
        ),
        filter_name: str = Body("", description="Enter filter name"),
        payload: dict = Body({}, description="Add fiter in a key value-pair"),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Add/Save filter in the collection named users
    """
    user = await UserHelper().is_valid_user(current_user)
    if filter_name == "":
        return {"detail": "Enter valid name of filter."}
    elif len(payload) == 0:
        return {"detail": "Please provide valid payload."}
    field_name = await get_field_name(
        paid_applications_filter, leads_filter, forms_filter, document_filter
    )
    for item in user.get(f"{field_name}", []):
        if item.get("name") == filter_name:
            return {
                "detail": "Filter name already exist. Please use "
                          "another name for save filter."
            }
    if len(user.get(f"{field_name}", [])) == 5:
        user.get(f"{field_name}", []).pop()
    if user.get(f"{field_name}"):
        user.get(f"{field_name}", []).insert(
            0, {"name": filter_name, "payload": payload}
        )
        await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(user.get("_id"))},
            {"$set": {f"{field_name}": user.get(f"{field_name}")}},
        )
    else:
        await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(user.get("_id"))},
            {"$set": {
                f"{field_name}": [{"name": filter_name, "payload": payload}]}},
        )
    await cache_invalidation(api_updated="updated_user", user_id=user.get("email") if user else None)
    await cache_invalidation(api_updated="add_or_delete_filter")
    return {"message": "Filter saved."}


@admin.delete("/filter/delete_by_name/", summary="Delete filter by name")
@requires_feature_permission("delete")
async def delete_filter_by_id_or_name(
        current_user: CurrentUser,
        paid_applications_filter: bool = Query(
            False,
            description="Want to delete paid "
                        "application filter "
                        "then pass value as "
                        "True",
        ),
        leads_filter: bool = Query(
            False,
            description="Want to delete lead filter" " then pass value as True"
        ),
        forms_filter: bool = Query(
            False,
            description="Want to save form filter" " then pass value as True"
        ),
        document_filter: bool = Query(
            False,
            description="Want to save document verification filter" " then pass value as True"
        ),

        filter_name: str = Query(..., description="Enter filter name"),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Delete filter by name
    """
    user = await UserHelper().is_valid_user(current_user)
    if filter_name == "":
        return {"detail": "Enter valid name of filter."}
    field_name = await get_field_name(
        paid_applications_filter, leads_filter, forms_filter, document_filter
    )
    delete_filter = False
    for _id, item in enumerate(user.get(f"{field_name}", [])):
        if item.get("name") == filter_name:
            user.get(f"{field_name}").pop(_id)
            await DatabaseConfiguration().user_collection.update_one(
                {"_id": ObjectId(user.get("_id"))},
                {"$set": {f"{field_name}": user.get(f"{field_name}")}},
            )
            delete_filter = True
    await cache_invalidation(api_updated="updated_user", user_id=user.get("email") if user else None)
    await cache_invalidation(api_updated="add_or_delete_filter")
    if delete_filter:
        return {"message": "Filter deleted."}
    return {"message": "Make sure filter name is correct and present."}


@admin.get("/filter/", summary="Get all filters of user")
@requires_feature_permission("read")
async def get_all_filters_of_user(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        paid_applications_filter: bool = Query(
            False,
            description="Want to get paid "
                        "applications filters "
                        "then pass value as "
                        "True",
        ),
        leads_filter: bool = Query(
            False,
            description="Want to get leads filters then pass " "value as True"
        ),
        forms_filter: bool = Query(
            False,
            description="Want to save form filter then pass " "value as True"
        ),
        document_filter: bool = Query(
            False,
            description="Want to save document verification filter then pass" " value as True"
        ),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get all filters of user
    """
    user = await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    field_name = await get_field_name(
        paid_applications_filter, leads_filter, forms_filter, document_filter
    )
    data = {
        "data": user.get(f"{field_name}") if user.get(f"{field_name}") else [],
        "message": "Get all filters.",
    }
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@admin.post("/add_student/", response_description="Add student")
@requires_feature_permission("write")
async def add_student_by_user(
        testing: Is_testing,
        background_tasks: BackgroundTasks,
        request: Request,
        user: StudentUser,
        current_user: CurrentUser,
):
    """
    Add student\n
    * :*param* **full_name** e.g., John Michel Dow:\n
    * :*param* **email** e.g., john@example.com:\n
    * :*param* **mobile_number** e.g., 1234567890:\n
    * :*param* **country_code** e.g., IN:\n
    * :*param* **state_code** e.g., UP:\n
    * :*param* **city** e.g., Mathura:\n
    * :*param* **course** e.g., Bsc:\n
    * :*param* **main_specialization** e.g., Medical Lab Technology:\n
    * :*param* **college_id** e.g., 123456789012345678901234:\n
    * :*return* **Student details**:
    """
    user = jsonable_encoder(user)
    college_id = user.get("college_id")
    user["full_name"] = user.get("full_name", "").strip()
    if not testing:
        Reset_the_settings().check_college_mapped(college_id)
    current_user = await UserHelper().check_user_has_permission(current_user, check_roles=["super_admin", "client_manager"])
    if college_id not in [str(i) for i in current_user.get("associated_colleges", [])]:
        raise HTTPException(status_code=401,
                            detail="Not enough permission because you are not associated with college.")
    is_publisher = True if current_user.get("role", {}).get("role_name") == "college_publisher_console" else False
    if is_publisher:
        user["utm_source"] = current_user.get("associated_source_value")
    st_reg = await StudentUserCrudHelper().student_register(
        user,
        publisher_id=str(current_user.get("_id")) if is_publisher else "NA",
        lead_type="api",
        is_created_by_user=False if is_publisher else True,
        is_created_by_publisher=is_publisher,
        user_details=current_user,
        request=request,
        background_tasks=background_tasks,
    )
    if st_reg:
        if is_publisher:
            await cache_invalidation(api_updated="publisher/add_student")
        else:
            await cache_invalidation(api_updated="student_user_crud/signup")
        student_info = st_reg.get("data", {})
        student_id = student_info.get("id")
        if (
                application := await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"student_id": ObjectId(student_id)}
                )
        ) is None:
            application = {}
        if (
                course := await DatabaseConfiguration().course_collection.find_one(
                    {"_id": application.get("course_id")}
                )
        ) is None:
            course = {}
        return {
            "data": {
                "student_id": student_id,
                "student_username": student_info.get("user_name"),
                "application_id": str(application.get("_id")),
                "course_name": (
                    f"{course.get('course_name')} in"
                    f" {application.get('spec_name1')}"
                    if (
                            application.get("spec_name1") != ""
                            and application.get("spec_name1")
                    )
                    else f"{course.get('course_name')} Program"
                ),
            },
            "message": "Account Created Successfully.",
        }


@admin.post("/add_leads_using_or_csv/", summary="Add leads using csv file")
@requires_feature_permission("write")
async def add_leads_using_json_or_csv(
        current_user: CurrentUser,
        request: Request,
        counselor_id: list[str] = None,
        data_name: str = Query(..., description="get name of doc"),
        file: UploadFile = File(...),
        college: dict = Depends(get_college_id),
):
    """
    Add leads using csv file\n
    """
    user = await UserHelper().is_valid_user(current_user)
    if (
            await DatabaseConfiguration().lead_upload_history.find_one(
                {"data_name": data_name}
            )
            is not None
    ):
        raise HTTPException(status_code=422, detail="Data name already exists")
    if college.get("id") not in [str(i) for i in
                                 user.get("associated_colleges")]:
        raise HTTPException(status_code=401, detail="Not enough permission because you are not associated with college.")
    filename = file.filename
    file_format = utility_obj.is_valid_extension(filename,
                                                 extensions=(".csv",))
    if not file_format:
        raise HTTPException(status_code=422, detail="File format is not supported.")

    if counselor_id:
        counselor_id = [cid.strip() for cid_str in counselor_id for cid in cid_str.split(',')]
    try:
        file_copy = await utility_obj.temporary_path(file)
        with open(file_copy.name, 'rb') as f:
            result = chardet.detect(f.read())
        encoding = result.get('encoding', "utf-8")
        df = pd.read_csv(file_copy.name, encoding=encoding)  # read the csv file

        student_header = [
            "full_name",
            "email",
            "course",
            "mobile_number",
            "main_specialization",
            "country_code",
            "state_code",
            "city",
        ]
        data = df.dropna(
            how="all", subset=student_header
        )  # remove the extra line from csv file

        data = data.fillna(np.nan).replace([np.nan], [None])
        # Convert the DataFrame to a list of dictionaries
        data = data.to_dict(orient="records")
    except UnicodeDecodeError as error:
        raise HTTPException(status_code=500, detail=f"UnicodeDecodeError. Error - {error}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Something went wrong. Error - {error}")
    if data:
        data_length = len(data)
        if data_length == 0:
            logger.error("Student details not found.")
            raise HTTPException(status_code=422,
                                detail="Student details not found.")
        if user.get("role", {}).get("role_name") == "college_publisher_console":
            uploaded_leads_count = await Publisher().get_uploaded_leads_count(
                user.get("_id")
            )
            bulk_lead_push_limit = user.get("bulk_lead_push_limit", settings.publisher_bulk_lead_push_limit)
            if uploaded_leads_count + data_length >= bulk_lead_push_limit.get("daily_limit", 0):
                logger.error("Reached maximum limit of per day for upload leads")
                raise HTTPException(
                    status_code=422,
                    detail="You have reached maximum limit of per day for upload leads.",
                )
            elif data_length >= bulk_lead_push_limit.get("bulk_limit", 0):
                logger.error("Reached maximum limit of bulk upload leads")
                raise HTTPException(
                    status_code=422,
                    detail="You have reached maximum limit of bulk upload leads.",
                )
        else:
            if len(data) > 200:
                raise HTTPException(
                    status_code=422, detail="You can upload leads up to 200."
                )
        try:
            ip_address = utility_obj.get_ip_address(request)
            toml_data = utility_obj.read_current_toml_file()
            if toml_data.get("testing", {}).get("test") is False:
                # TODO: Not able to add student timeline data
                #  using celery task when environment is
                #  demo. We'll remove the condition when
                #  celery work fine.
                if settings.environment in ["demo"]:
                    PublisherActivity().process_uploaded_loads(
                        user=user,
                        data={"student_details": data},
                        filename=filename,
                        college=college,
                        is_created_by_user=False if user.get("role", {}).get("role_name") == "college_publisher_console" else True,
                        counselor_id=counselor_id,
                        ip_address=ip_address,
                        data_name=data_name,
                        college_id=college.get("id"),
                    )
                else:
                    if not is_testing_env():
                        PublisherActivity().process_uploaded_loads.delay(
                            user=user,
                            data={"student_details": data},
                            filename=filename,
                            college=college,
                            is_created_by_user=False if user.get("role", {}).get("role_name") == "college_publisher_console" else True,
                            counselor_id=counselor_id,
                            ip_address=ip_address,
                            data_name=data_name,
                            college_id=college.get("id"),
                        )
        except KombuError as celery_error:
            logger.error(f"Error add student by publisher {celery_error}")
        except Exception as error:
            logger.error(f"Error add student by publisher {error}")
        await cache_invalidation(api_updated="student_user_crud/signup")
        return {
            "message": "Received Request will be processed in the background"
                       " once finished you will receive an email."
                       " Data processing might take anywhere between 2 min - 1"
                       " hour depending on the data volume."
        }
    else:
        raise HTTPException(status_code=404, detail="File is empty.")


@admin.get("/search_students/", summary="search students details")
@requires_feature_permission("read")
async def search_student(
        page_num: int,
        page_size: int,
        search_input: str,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        client=Depends(utility_obj.get_meili_client),
):
    """
    .search student details
    .college_id is compulsory

    It will return the student details
    """
    user = await UserHelper().check_user_has_permission(current_user)
    filters = [f"college_id={college.get('id')}"]

    if not (
            (
                    await utility_obj.is_email_valid(search_input)
                    and await DatabaseConfiguration()
                    .studentsPrimaryDetails.aggregate(
                [{"$match": {"user_name": search_input}}])
                    .to_list(None)
            )
            or await utility_obj.is_phone_number_valid(search_input)
    ):
        if user["role"]["role_name"] == "college_publisher_console":
            filters.append(
                [f"source={str(user.get('associated_source_value'))}"])
        elif user["role"]["role_name"] == "college_head_counselor":
            counselor_list = await get_counselor_list(college, user.get("_id"))
            filters.append([f"counselor_id IN {counselor_list}"])
        elif user["role"]["role_name"] == "college_counselor":
            filters.append([f"counselor_id={str(user.get('_id'))}"])
    name = f"{settings.client_name.lower().replace(' ', '_')}_{settings.current_season.lower()}"
    try:
        all_student_record = client.index(f"{name}_students").search(
            search_input,
            {
                "filter": filters,
                "showMatchesPosition": True,
                "attributesToHighlight": ["*"],
                "highlightPreTag": "<span class='search-query-highlight'>",
                "highlightPostTag": "</span>",
                "hitsPerPage": page_size,
                "page": page_num,
            },
        )

        logger.info(
            f"Fetched {len(all_student_record.get('hits', []))} "
            f"student parents details for college {college.get('id')}"
        )
        return {
            "data": all_student_record.get("hits"),
            "total": all_student_record.get("totalHits"),
            "count": all_student_record.get("hitsPerPage"),
            "page_num": all_student_record.get("page"),
            "message": "Fetched student_id and application_id " "successfully",
        }
    except MeilisearchCommunicationError as meil_error:
        logger.error(f"Error - {str(meil_error.args)}")
        raise HTTPException(
            status_code=404, detail="Meilisearch server is not running."
        )
    except MeilisearchApiError as meil_error:
        logger.error(f"Error - {str(meil_error.args)}")
        raise HTTPException(status_code=404, detail=str(meil_error.args))
    except Exception as e:
        logger.error(f"Error - {str(e.args)}")
        raise HTTPException(status_code=404, detail=str(e.args))


@admin.post(
    "/search_leads/",
    summary="Get Leads Details by Search Pattern",
    response_description="Get all application details",
)
@requires_feature_permission("read")
async def get_leads_details(
        current_user: CurrentUser,
        date_range: DateRange = Body(None),
        search_input: str = Query(..., description="Enter search pattern"),
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        client=Depends(utility_obj.get_meili_client),
):
    """
    Admin Scope Required \n
    Get Leads Details by Search Pattern\n
    *:return **All Student details**:
    """
    user = await UserHelper().check_user_has_permission(current_user)
    try:
        filters = []
        if date_range:
            date_range = jsonable_encoder(date_range)
            start_date, end_date = await utility_obj.date_change_format_unix_time(
                date_range.get("start_date"), date_range.get("end_date")
            )
            filters.append(
                [f"created_at >= {start_date} AND created_at <= {end_date}"])
        if user["role"]["role_name"] == "college_publisher_console":
            filters.append(
                [f"source_name={str(user.get('associated_source_value'))}"])
        elif user["role"]["role_name"] == "college_head_counselor":
            counselor_list = await get_counselor_list(college, user.get("_id"))
            filters.append([f"counselor_ids IN {counselor_list}"])
        elif user["role"]["role_name"] == "college_counselor":
            counselor_id = str(user.get("_id"))
            filters.append([f"counselor_ids={counselor_id}"])
        name = f"{settings.client_name.lower().replace(' ', '_')}_{settings.current_season.lower()}"
        all_leads = client.index(f"{name}_leads").search(
            search_input,
            {
                "filter": filters,
                "showMatchesPosition": True,
                "attributesToHighlight": ["*"],
                "highlightPreTag": "<span class=" "'search-query-highlight'>",
                "highlightPostTag": "</span>",
                "hitsPerPage": page_size,
                "page": page_num,
            },
        )
        logger.info(
            f"Fetched {len(all_leads.get('hits', []))} "
            f"student applications for college {college.get('id')}"
        )
        return {
            "data": all_leads.get("hits"),
            "count": all_leads.get("totalHits"),
            "page_size": all_leads.get("hitsPerPage"),
            "page_num": all_leads.get("page"),
            "message": "Fetched student data successfully",
        }
    except MeilisearchCommunicationError as meil_error:
        logger.error(f"Error - {str(meil_error.args)}")
        raise HTTPException(
            status_code=404, detail="Meilisearch server is not running."
        )
    except MeilisearchApiError as meil_error:
        logger.error(f"Error - {str(meil_error.args)}")
        raise HTTPException(status_code=404, detail=str(meil_error.args))
    except Exception as e:
        logger.error(f"Error - {str(e.args)}")
        raise HTTPException(status_code=404, detail=str(e.args))


@admin.get("/post_application_stages_info/",
           summary="Get post application stages info")
@requires_feature_permission("read")
async def post_application_stages_info(
        current_user: CurrentUser,
        testing: Is_testing,
        application_id: str = Query(
            ...,
            description="Application ID \n* e.g.," "**62551f6d7a3f3d06d4196b7f**"
        ),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get post application stages info.

    Params:
        application_id (int | None): An unique application id for
         get post application stages info.
        current_user (str): An user_name of current user.
        college (dict): College data.
    Returns:
        dict: Post application stages info.
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    return await StudentApplicationHelper().post_application_stages_info(
        application_id)


@admin.post("/add_comment_for_document/", summary="Add comment for a document")
@requires_feature_permission("write")
async def comment_on_document(
        current_user: CurrentUser,
        student_id: str = Query(..., description="Enter student id"),
        data: upload_docs = Depends(functools.partial(upload_docs)),
        comment: str = Query(description="Enter a comment"),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Add comment for a document.

    Params:
        student_id (str): An unique student id.
        current_user (str): An user_name of current user.
        data (upload_docs): Payload useful for get document name.
        comment (str): A comment which want to add for document.
        college (dict): College data.
    Returns:
        dict: A dictionary contains message.
    """
    if (
            await DatabaseConfiguration().user_collection.find_one(
                {"user_name": current_user.get("user_name")}
            )
            is None
    ):
        raise HTTPException(status_code=401, detail="Not enough permissions")
    data = await StudentApplicationHelper().comment_on_document(
        student_id, current_user.get("user_name"), data, comment, college
    )
    await cache_invalidation(api_updated="admin/add_comment_for_document")
    return data


@admin.get("/get_document_comments/", summary="Get a document comments")
@requires_feature_permission("read")
async def get_comments_of_document(
        current_user: CurrentUser,
        student_id: str = Query(..., description="Enter student id"),
        data: upload_docs = Depends(functools.partial(upload_docs)),
        cache_info=Depends(cache_dependency),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get comments for a document

    Params:
        student_id (str): An unique student id.
        current_user (str): An user_name of current user.
        data (upload_docs): Payload useful for get document name.
        college (dict): College data.
    Returns:
        dict: A dictionary contains message.
    """
    cache_key, cache_data = cache_info
    if cache_data:
        return cache_data
    if not is_testing_env():
        Reset_the_settings().check_college_mapped(college.get("id"))
    data = await StudentApplicationHelper().get_document_comments(
        student_id, current_user, data
    )
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@admin.put("/update_status_of_document/",
           summary="Update status of a document")
@requires_feature_permission("edit")
async def update_status_of_document(
        current_user: CurrentUser,
        status: DocumentStatus,
        application_id: str = Query(..., description="Enter application id"),
        data: upload_docs = Depends(functools.partial(upload_docs)),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Update status of a document.

    Params:
        application_id (str): An unique application id.
        current_user (str): An user_name of current user.
        data (upload_docs): Payload useful for get document name.
        status (DocumentStatus): A status of a document which want to update.
        college (dict): College data.
    Returns:
        dict: A dictionary contains message.
    """
    return await StudentApplicationHelper().update_document_status(
        application_id, current_user, data, status
    )


@admin.put("/edit_comment/", summary="Update comment data")
@requires_feature_permission("edit")
async def edit_comment(
        current_user: CurrentUser,
        comment: str = Query(description="Enter comment"),
        comment_id: int = Query(description="Enter comment id"),
        student_id: str = Query(description="Enter student id"),
        data: upload_docs = Depends(functools.partial(upload_docs)),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Update comment of a document.
    Only the user who created the comment can delete and
    edit or admin can delete or edit.

    Params:
        student_id (str): An unique student id.
        current_user (str): An user_name of current user.
        data (upload_docs): Payload useful for get document name.
        comment (str): A comment which want to update.
        comment_id (int): A comment id which helpful for
         update particular comment.
        college (dict): College data.
    Returns:
        dict: A dictionary contains message.
    """
    return await StudentApplicationHelper().update_comment(
        student_id, current_user, data, comment, comment_id
    )


@admin.delete("/delete_comment/", summary="Delete comment of a document")
@requires_feature_permission("delete")
async def delete_comment(
        current_user: CurrentUser,
        comment_id: int = Query(description="Enter comment id"),
        student_id: str = Query(description="Enter student id"),
        data: upload_docs = Depends(functools.partial(upload_docs)),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Delete comment of a document.
    Only the user who created the comment can delete and edit or
     admin can delete or edit.

    Params:
        student_id (str): An unique student id.
        current_user (str): An user_name of current user.
        data (upload_docs): Payload useful for get document name.
        comment_id (int): A comment id which helpful for delete
         particular comment.
        college (dict): College data.
    Returns:
        dict: A dictionary contains message.
    """
    return await StudentApplicationHelper().delete_comment(
        student_id, current_user, data, comment_id
    )


@admin.get("/school_names/", summary="Get school names")
@requires_feature_permission("read")
async def get_school_names(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get school names.

    Params:
        current_user (str): An user_name of current user.
        college (dict): College data.
    Returns:
        dict: A dictionary which contains school names info.
    """
    await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    data = await CollegeHelper().get_school_names(current_user)
    if cache_key:
        await insert_data_in_cache(cache_key, data, expiration_time=1800)
    return data


@admin.post("/send_student_document_to_board/")
@requires_feature_permission("write")
async def send_student_document_to_board(
        background_tasks: BackgroundTasks,
        current_user: CurrentUser,
        request: Request,
        data: upload_docs = Depends(functools.partial(upload_docs)),
        application_id: str = Query(description="Enter application id"),
        season: str = None,
        college: dict = Depends(get_college_id),
):
    """
    Send student document to respective board through mail for verification.

    Params:\n
        college_id (str): An unique identifier of college for get college data.
            For example, 123456789012345678901234
        data (upload_docs): Useful for get document.
        application_id (str): An unique identifier application.
            For example, 123456789012345678901231

    Returns:
        dict: A dictionary contains send email info.
    """
    return await StudentApplicationHelper().send_student_document_to_board(
        current_user,
        application_id,
        request,
        data,
        college,
        background_tasks,
        season=season,
        college_id=college.get("id"),
    )


@admin.get("/get_external_links_of_student_documents/")
@requires_feature_permission("read")
async def external_links_of_student_documents(
        current_user: CurrentUser,
        application_id: str = Query(description="Enter application id"),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get external links of student documents.

    Params:\n
        college_id (str): An unique identifier of college for get college data.
            For example, 123456789012345678901234
        application_id (str): An unique identifier application.
            For example, 123456789012345678901231

    Returns:
        dict: A dictionary contains external links of student documents.
    """
    return await StudentApplicationHelper().get_external_links_of_student_documents(
        current_user, application_id
    )


@admin.post("/key_indicator/")
@requires_feature_permission("read")
async def key_indicator(
        current_user: CurrentUser,
        college_id: Annotated[str, Query(..., description="Enter college id")],
        cache_data=Depends(cache_dependency),
        season: str = Body(
            None,
            description="Enter season value if want to" " get data season-wise"
        ),
        program_name: list | None = Body(None),
        change_indicator: ChangeIndicator = None,
):
    """
    get key indicators information

    Params:\n
        college_id (str): An unique identifier of college for get college data.
            For example, 123456789012345678901234
        program_name (dict) : This is a filter used.
        This is simply the course name
         change_indicator (str):
         Returns:
        dict: All the key indicators
    """
    await UserHelper().is_valid_user(user_name=current_user)
    cache_key, data = cache_data
    if data:
        return data
    try:
        data = await AdminBoardHelper().get_key_indicators(
            college_id=college_id,
            program_name=program_name,
            change_indicator=change_indicator,
            season=season,
        )
        if data:
            data = utility_obj.response_model(
                data=data, message="Get the key indicators data."
            )
            if cache_key:
                await insert_data_in_cache(cache_key, data)
            return data
    except DataNotFoundError as e:
        logger.error(f"{e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"An internal error" f" occurred: {e}"
        )


@admin.post("/student_queries/")
@requires_feature_permission("read")
async def student_queries(
        current_user: CurrentUser,
        college_id: Annotated[str, Query(..., description="Enter college id")],
        season: str = Body(
            None,
            description="Enter season value if" " want to get data season-wise"
        ),
        cache_data=Depends(cache_dependency),
        program_name: list | None = Body(None),
        counselor_Id: list | None = Body(None),
        date_range: DateRange | None = Body(None),
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0),
        sort: str | None = Body(None),
        sort_type: str | None = Body(None),
        search: str | None = Body(None),
):
    """
    get student queries information
    Params:\n
     college_id (str): An unique identifier of college for get college data.
         For example, 123456789012345678901234
     program_name (dict) : This is a filter used.
      This is simply the course name
     query_type (str): The query which is required(filter)
     date_range (Date Range): This is given to add filter for date range
     search (str): Search for some counselor name
     sort(str): Sort the data based on given key
     Returns:
     dict: All the key indicators
    """
    cache_key, data = cache_data
    if data:
        return data
    user = await UserHelper().is_valid_user(user_name=current_user)
    if user.get("role", {}).get("role_name") == "college_counselor":
        counselor_Id = [ObjectId(user.get("_id"))]
    elif user.get("role", {}).get("role_name") == "college_head_counselor":
        counselors = await DatabaseConfiguration().user_collection.aggregate(
            [{"$match": {"head_counselor_id": ObjectId(user.get("_id"))}}]
        ).to_list(length=None)
        counselor_Id = [ObjectId(temp.get("_id")) for temp in counselors]
    date_range = await utility_obj.format_date_range(date_range)
    data = await AdminBoardHelper().get_student_queires(
        college_id=college_id,
        program_name=program_name,
        date_range=date_range,
        search=search,
        counselor_id=counselor_Id,
        season=season,
    )
    if sort:
        data = (
            sorted(data, key=lambda x: x[sort], reverse=True)
            if sort_type == "dsc"
            else sorted(data, key=lambda x: x[sort])
        )
    response, total = {}, 0
    if page_num and page_size:
        total = len(data)
        response = await utility_obj.pagination_in_api(
            page_num,
            page_size,
            data,
            total,
            route_name="/admin/student_queries/",
        )
    data = {
        "data": response["data"],
        "total": total,
        "count": page_size,
        "pagination": response["pagination"],
        "message": "queries data fetched successfully!",
    }
    if cache_key:
        await insert_data_in_cache(cache_key, data, 30)
    return data


@admin.post("/student_total_queries_header/")
@requires_feature_permission("read")
async def student_total_queries_header(
        current_user: CurrentUser,
        college_id: Annotated[str, Query(..., description="Enter college id")],
        season: str = Body(
            None,
            description="Enter season value if want" " to get data season-wise"
        ),
        cache_data=Depends(cache_dependency),
        date_range: DateRange = Body(None),
):
    """
    get student total queries information
    Params:\n
        college_id (str): An unique identifier of college for get college data.
            For example, 123456789012345678901234
        date_range (Date Range): This is given to add filter for date range
    Returns:
        dict: All the key indicators
    """
    user = await UserHelper().is_valid_user(user_name=current_user)
    cache_key, data = cache_data
    if data:
        return data
    counselor_id = None
    if user.get("role", {}).get("role_name") == "college_counselor":
        counselor_id = [ObjectId(user.get("_id"))]
    elif user.get("role", {}).get("role_name") == "college_head_counselor":
        counselor_detail = DatabaseConfiguration().user_collection.aggregate(
            [
                {
                    "$match": {"head_counselor_id": ObjectId(user.get("_id"))}
                }
            ]
        )
        counselor_id = [
            ObjectId(counselor.get("_id")) async for counselor in
            counselor_detail
        ]
    date_range = await utility_obj.format_date_range(date_range)
    try:
        data = await AdminBoardHelper().get_student_total_queires_header(
            college_id=college_id,
            date_range=date_range,
            counselor_id=counselor_id,
            season=season,
        )
        if data:
            data = utility_obj.response_model(
                data=data, message="Get the student queries data."
            )
            if cache_key:
                await insert_data_in_cache(cache_key, data)
            return data
    except DataNotFoundError as e:
        logger.error(f"{e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"An internal error" f" occurred: {e}"
        )


@admin.post("/student_total_queries/")
@requires_feature_permission("read")
async def student_total_queries(
        current_user: CurrentUser,
        college_id: dict = Depends(get_college_id_short_version(short_version=True)),
        season: str = Body(
            None,
            description="Enter season value if want" " to get data season-wise"
        ),
        cache_data=Depends(cache_dependency),
        program_name: list | None = None,
        query_type: list | None = Body(None),
        date_range: DateRange | None = Body(None),
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0),
        search: str | None = Body(None),
):
    """
    get student queries total information
    Params:\n
        college_id (str): An unique identifier of college for get college data.
            For example, 123456789012345678901234
        program_name (dict) : This is a filter used.
         This is simply the course name
        query_type (str): The query which is required(filter)
        date_range (Date Range): This is given to add filter for date range
    Returns:
        dict: All the key indicators
    """
    await UserHelper().is_valid_user(user_name=current_user)
    cache_key, data = cache_data
    if data:
        return data
    date_range = await utility_obj.format_date_range(date_range)
    try:
        data = await AdminBoardHelper().get_student_total_queries(
            college_id=college_id,
            program_name=program_name,
            query_type=query_type,
            date_range=date_range,
            search=search,
            page_num=page_num,
            page_size=page_size,
            season=season,
        )
        if cache_key:
            await insert_data_in_cache(cache_key, data)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"An internal error" f" occurred: {e}"
        )


@admin.post(
    "/student_queries_based_on_counselor/",
    summary="Get the counselor wise student queries summary info.",
)
@requires_feature_permission("read")
async def get_student_queries(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        season: str = Body(
            None,
            description="Enter season value if want" " to get data season-wise"
        ),
        cache_data=Depends(cache_dependency),
        program_names: list[ProgramFilter] | None = Body(None),
        date_range: DateRange | None = Body(None),
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0),
        search: str = Body(None),
        query_type: list[QueryType] | None = Body(None),
        counselor_ids: list[str] | None = Body(None),
):
    """
    Get the counselor wise student queries summary info.

    Params:\n
        college_id (str): An unique identifier of college for get college data.
            For example, 123456789012345678901234.

    Returns:
        dict: A dictionary which contains the counselor wise student queries
        summary info along with success message.
    """
    await UserHelper().is_valid_user(user_name=current_user)
    cache_key, data = cache_data
    if data:
        return data
    date_range = await utility_obj.format_date_range(date_range)
    try:
        data = {
            "data": await Student().get_student_queries(
                season,
                program_names,
                date_range,
                page_num,
                page_size,
                query_type,
                search,
                counselor_ids,
            ),
            "message": "Get the counselor wise student queries summary " "info.",
        }
        if cache_key:
            await insert_data_in_cache(cache_key, data)
        return data
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"An internal error" f" occurred: {error}"
        )


@admin.post(
    "/upload_user_audit_details/",
    response_description="Upload user audit details into the database",
)
@requires_feature_permission("write")
async def upload_user_audit_details(
        current_user: CurrentUser,
):
    """
    Upload user audit details into the database.

    This endpoint allows authorized users with roles 'super_admin' or 'college_super_admin'
    to upload user audit details into the database.

    Parameters:
        current_user (User): The current user accessing the endpoint. Automatically
                             retrieved from the request headers using the `get_current_user`
                             dependency.

    Returns:
        dict: A dictionary containing the response data.

    Raises:
        HTTPException: If the user does not have enough permissions to access the endpoint
                       or if an error occurs while uploading the user audit details.

    Response Description:
        Uploads user audit details into the database and returns the response data.
    """

    user = await UserHelper().is_valid_user(current_user)
    role_name = user.get("role", {}).get("role_name", "")
    if role_name not in ["super_admin", "college_super_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    try:
        return await utility_obj.fetch_and_store()
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"An error got while uploading the "
                   f"user audit details. Error - {error}",
        )


@admin.post(
    "/get_user_audit_details/",
    response_description="Fetch user audit details",
)
@requires_feature_permission("read")
async def get_user_audit_details(
        current_user: CurrentUser,
        user: Union[str, None] = Query(None,
                                       description="Enter user's id or ip address"),
        page_num: int = Query(1, gt=0),
        page_size: int = Query(15, gt=0),
        date_range: DateRange | None = Body(None),
):
    """
    Fetch user audit details.

    This endpoint allows authorized users to fetch audit trail details for a specified user
    within a given date range. The results can be paginated using the `page_num` and `page_size`
    query parameters.

    Args:
        current_user (User): The user currently authenticated and making the request.
        user (Union[str, None], optional): The ID or IP address of the user whose audit details are
                                           to be fetched. Defaults to None.
        page_num (int, optional): The page number for pagination. Must be greater than 0. Defaults to 1.
        page_size (int, optional): The number of records per page for pagination. Must be greater than 0. Defaults to 15.
        date_range (DateRange | None, optional): The date range within which to fetch audit details.
                                                 Contains `start_date` and `end_date`. Defaults to None.

    Raises:
        HTTPException: If the authenticated user does not have sufficient permissions.

    Returns:
        dict: A dictionary containing the fetched data, total count, page size, pagination details, and a success message.
    """
    user_data = await UserHelper().is_valid_user(current_user)
    role_name = user_data.get("role", {}).get("role_name", "")
    if role_name not in ["super_admin", "college_super_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    date_range = await utility_obj.format_date_range(date_range)
    start_date, end_date = await utility_obj.date_change_format(
        start_date=date_range.get("start_date"),
        end_date=date_range.get("end_date")
    )
    skip, limit = await utility_obj.return_skip_and_limit(
        page_num=page_num, page_size=page_size
    )
    result_data, count = await AuditTrail().get_audit_trail_aggregate(
        user=user,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    response = await utility_obj.pagination_in_aggregation(
        page_num,
        page_size,
        count,
        route_name="/admin/get_user_audit_details/",
    )
    data = {
        "data": result_data,
        "total": count,
        "count": page_size,
        "pagination": response["pagination"],
        "message": "data fetched successfully!",
    }
    return utility_obj.response_model(data=data,
                                      message="Data fetched successfully.")


@admin.post(
    "/grant_extra_limits_to_ip_address/",
    response_description="Grant extra API limits to an IP-Address",
)
@requires_feature_permission("write")
async def grant_extra_limits_to_ip_address(
        current_user: CurrentUser,
        ip_address: str = Query(
            description="IP-address you'd like to grant extra limits. \n*e.g.,"
                        "**172.23.0.6**",
        ),
):
    """
    Grant extra API limits to a given IP address.

    This endpoint grants additional API limits to the specified IP address.
    Only users with the roles 'super_admin' or 'college_super_admin' have the necessary
    permissions to perform this action.

    Args:
        ip_address (str): The IP address to which you want to grant extra API limits.
        current_user (User): The current user invoking this endpoint, obtained from
                             dependency injection.

    Raises:
        HTTPException:
            - status_code=401: If the current user does not have sufficient permissions.
            - status_code=400: If extra limits have already been granted to the IP address.
            - status_code=500: If there is an internal server error while processing the request.

    Returns:
        dict: A message indicating the success of the operation.
    """
    user = await UserHelper().is_valid_user(current_user)
    role_name = user.get("role", {}).get("role_name", "")
    if role_name not in ["super_admin", "college_super_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    try:
        existing_data = (
            await DatabaseConfiguration().extra_limit_ip_collection.find_one()
        )
        if existing_data is not None:
            if ip_address in existing_data.get("ip_address"):
                raise CustomError(
                    f"Extra limits already granted to Ip address: {ip_address}."
                )
            else:
                await DatabaseConfiguration().extra_limit_ip_collection.update_one(
                    {}, {"$push": {"ip_address": ip_address}}
                )
        else:
            DatabaseConfiguration().extra_limit_ip_collection.insert_one(
                {"ip_address": [ip_address]}
            )
    except CustomError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=f"{e}")
    except Exception as e:
        logger.error(f"An error got while granting extra limits. Error - {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error got while granting extra limits. Error - {e}",
        )
    else:
        if await utility_obj.update_ip_addresses_in_redis():
            return {"message": "Extra limits granted successfully!"}


@admin.post(
    "/remove_extra_limits_from_ip_address/",
    response_description="Remove extra API limits from an IP-Address",
)
@requires_feature_permission("write")
async def remove_extra_limits_from_ip_address(
        current_user: CurrentUser,
        ip_address: str = Query(
            description="IP-address you'd like to grant extra limits. \n*e.g.,"
                        "**172.23.0.6**",
        ),
):
    """
    Remove extra API limits from a given IP address.

    This endpoint removes any extra API limits associated with the specified IP address.
    Only users with the roles 'super_admin' or 'college_super_admin' have the necessary
    permissions to perform this action.

    Args:
        ip_address (str): The IP address from which you want to remove extra API limits.
        current_user (User): The current user invoking this endpoint, obtained from
                             dependency injection.

    Raises:
        HTTPException:
            - status_code=401: If the current user does not have sufficient permissions.
            - status_code=400: If the IP address does not exist in the database.
            - status_code=500: If there is an internal server error while processing the request.

    Returns:
        dict: A message indicating the success of the operation.
    """
    user = await UserHelper().is_valid_user(current_user)
    role_name = user.get("role", {}).get("role_name", "")
    if role_name not in ["super_admin", "college_super_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    try:
        existing_data = (
            await DatabaseConfiguration().extra_limit_ip_collection.find_one()
        )
        if existing_data is not None and ip_address in existing_data.get(
                "ip_address"):
            await DatabaseConfiguration().extra_limit_ip_collection.update_one(
                {}, {"$pull": {"ip_address": ip_address}}
            )
        else:
            raise CustomError(f"Ip address: {ip_address}, doesn't exist")
    except CustomError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=f"{e}")
    except Exception as e:
        logger.error(
            f"An error got while removing extra limits from Ip address. Error - {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"An error got while removing extra limits from Ip address. Error - {e}",
        )
    else:
        if await utility_obj.update_ip_addresses_in_redis():
            return {"message": "Extra limits removed successfully!"}


@admin.post("/invalidate_cache")
async def invalidate_cache(
        invalidate_string: str
):
    """
    This route is used to invalidate cache manually
    Params:
        invalidate_string (str): The string which is to be matched and invalidate cache
    Returns:
        Statement that cache is invalidated
    """
    try:
        await delete_keys_matching_pattern([invalidate_string])
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Something went wrong while deleting cache: {e}")


@admin.post(
    "/preference_wise_data/",
    response_description="Get/download the preference wise data."
)
@requires_feature_permission("read")
async def preference_wise_info(
        current_user: CurrentUser,
        testing: Is_testing,
        request: Request,
        background_tasks: BackgroundTasks,
        data_for: str = "Leads",
        season: str = None,
        download_data: bool = False,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        program_name: list | None = Body(None),
        date_range: DateRange | None = Body(None),
        sort: bool = Body(None),
        sort_name: str = Body(None),
        sort_type: str = Body(None),
):
    """
    Get/download the preference wise data.

    Params:\n
        - college_id (str): An unique id/identifier of a college.
            e.g., 123456789012345678901234
        - download_data (bool). Useful for download preference wise
            information. Default value: False.
        - data_for (str): Useful for get particular type preference count data.
            Possible values are: Leads and Applications.
        - season (str | None): Either None or season id which useful for get
            particular season data. e.g., season0

    Request body params:\n
        - program_name (list | None): Optional field. Either None or program
            names which useful for get data based on program (s).
            e.g., [{"course_id":
                "123456789012345678901234", "spec_name1": "xyx"}]
        - date_range (DateRange | None): Optional field. Either none or
            daterange which useful for filter data based on date_range.
            e.g., {"start_date": "2023-09-07", "end_date": "2023-09-07"}
        - sort (bool): A boolean value which useful sort data.
            Possible values are: true or false.
        - sort_name (str): A string value which represent field name based on
            we want to sort data.
            Possible value are: course_name, preference1, ....
        - sort_type (str): Type of sorting. Possible values are: asc and dsc.

    Returns:\n
        - dict: A dictionary which contains preference wise information.
            e.g., {"header": ["Course Name", "Preference 1", "Preference 2", ...],
                "data": [{"course_name": "B.Sc. Physician Assistant",
                "preference1": 20, "preference2": 30, ...}]}

    Raises:\n
        - 401 (Not enough permissions): An error raised with status code 401
            when user don't have permission to get/download user chart
            information.
        - DataNotFoundError: An error raised with status code 404
            when data not found.
        - Exception: An error with status code 500 which occurred when
            something went wrong in the background code apart from 401 error.
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        college_id = college.get("id")
        if not testing:
            Reset_the_settings().check_college_mapped(college_id)
        current_datetime = datetime.datetime.utcnow()
        counselor_id, user_role = None, user.get("role", {}).get("role_name")
        if user_role in ["college_head_counselor", "college_counselor"]:
            if user_role == "college_head_counselor":
                counselor_id = await AdminUser().get_users_ids_by_role_name(
                    "college_counselor", college_id, user.get("_id")
                )
            else:
                counselor_id = [ObjectId(user.get("_id"))]
        date_range = await utility_obj.format_date_range(date_range)
        header, data, total = await AdminDashboardHelper().get_preference_wise_info(
            college_id, season, college.get("system_preference", {}), data_for,
            program_name, date_range, counselor_id)
        if sort:
            data.sort(key=lambda x: x.get(sort_name),
                                        reverse=False if sort_type == "asc" else True)
        if download_data:
            background_tasks.add_task(
                DownloadRequestActivity().store_download_request_activity,
                request_type="Preference Wise Info",
                requested_at=current_datetime,
                ip_address=utility_obj.get_ip_address(request),
                user=user,
                total_request_data=len(data),
                is_status_completed=True,
                request_completed_at=datetime.datetime.utcnow(),
            )
            if data:
                header = list(data[0].keys())
                if total and isinstance(total, list):
                    total = {key: value for key, value in zip(header, total)}
                    data.append(total)
                get_url = await upload_csv_and_get_public_url(
                    fieldnames=header, data=data,
                    name="applications_data"
                )
                return get_url
            raise DataNotFoundError("Data")
        return {"header": header, "data": data, "total": total,
                "message": "Get the preference wise information."}
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"An error got when get preference wise information. "
                   f"Error - {error}"
        )

@admin.post("/get_assigned_unassigned_details/")
@requires_feature_permission("read")
async def get_assigned_unassigned_details(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        date_range: DateRange | None = Body(None),
):
    """
    Return Assigned and unassigned leads details
    Params:
        college (dict): Details of college
        date_range (Date range): The date range filter. It will have start date and end date
    Returns:
        Dict: The details of unassigned and assigned forms
    """
    user_data = await UserHelper().is_valid_user(current_user)
    role_name = user_data.get("role", {}).get("role_name", "")
    if role_name not in ["super_admin", "college_super_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    date_range = await utility_obj.format_date_range(date_range)
    result = await AdminBoardHelper().get_assigned_unassigned_details(date_range)
    return result


@admin.get(
    "/get_untouched_leads",
    response_description="Get Pending Leads",
)
@requires_feature_permission("read")
async def get_pending_leads(
        page_num: int,
        page_size: int,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):

    """
        Retrieve a paginated list of pending leads for the specified college.

        Parameters:
        ----------
        page_num : int
            The page number to retrieve (for pagination).
        page_size : int
            The number of leads to return per page.
        current_user : User
            The currently authenticated user, injected via dependency.
        college : dict
            The college context (including ID and short version), injected via dependency.

        Returns:
        -------
        dict:
            A list of pending lead records with pagination applied.

        Raises:
        ------
        HTTPException
            If the user is not authorized or if the data retrieval fails.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        result, count = await AdminBoardHelper().get_pending_leads(page_num, page_size)
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, count,
            route_name="/admin/get_pending_leads"
        )
        return {
            "data": result,
            "total": count,
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Pending Leads data fetched successfully!",
        }
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


