"""
This file contains API routes/endpoints related to raw_data and offline data
"""

import numpy as np
import datetime
import pandas as pd
from bson import ObjectId
from fastapi import (
    APIRouter,
    BackgroundTasks,
    UploadFile,
    File,
    Depends,
    Query,
    Request,
    Body
)
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError

from app.celery_tasks.celery_manage import RawDataActivity
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings, requires_feature_permission
from app.database.aggregation.row_data import RawData
from app.database.configuration import DatabaseConfiguration
from app.models.student_user_schema import DateRange
from app.core.reset_credentials import Reset_the_settings
from app.dependencies.college import get_college_id_short_version
from app.dependencies.oauth import (
    CurrentUser,
    cache_dependency,
    insert_data_in_cache, is_testing_env,
    Is_testing
)
from app.helpers.admin_dashboard.lead_user import LeadUser
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.lead_schema import offline_schema, ActionPayload, Action
from app.core.reset_credentials import Reset_the_settings
from app.core.custom_error import CustomError, ObjectIdInValid
from app.background_task.admin_user import DownloadRequestActivity
from app.s3_events.s3_events_configuration import upload_csv_and_get_public_url

logger = get_logger(__name__)

manage = APIRouter()


@manage.post("/raw_data")
@requires_feature_permission("write")
async def raw_data_upload(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    data_name,
    file: UploadFile = File(..., description="upload excel file"),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    upload raw data in raw_data collection
    file format should excel and csv
    """
    if (
        user := await DatabaseConfiguration().user_collection.find_one(
            {"user_name": current_user.get("user_name")}
        )
    ) is None:
        raise HTTPException(status_code=404, detail="user not found")
    user = await utility_obj.user_serialize(user)
    file_copy = await utility_obj.temporary_path(file)
    if (
        file.filename.endswith(".xlsx")
        or file.filename.endswith(".xlx")
        or file.filename.endswith(".csv")
    ):
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file_copy.name, encoding="latin1")
        else:
            df = pd.read_excel(file_copy.name)
        if (
            await DatabaseConfiguration().offline_data.find_one(
                {"data_name": str(data_name).lower()}
            )
            is not None
        ):
            return {"detail": "Data name already exists. " "Please use another name."}
        data_frame = df.groupby(
            df.columns.tolist(), dropna=False, as_index=False
        ).size()  # check duplicate raw count
        df = data_frame.replace(np.nan, "", regex=True)
        duplicate = df.loc[
            df.duplicated(subset=["mobile_number", "size"], keep="first"), :
        ]
        duplicate_dict, data_dict = [], []
        if duplicate is not None:
            duplicate_dict = duplicate.to_dict("records")
        df = df.drop_duplicates(subset=["mobile_number", "size"], keep="first")
        if df is not None:
            data_dict = df.to_dict("records")
        # TODO: Not able to add student timeline data
        #  using celery task when environment is
        #  demo. We'll remove the condition when
        #  celery work fine.
        if settings.environment in ["demo"]:
            RawDataActivity().upload_raw_data(
                file={"data_dict": data_dict, "duplicate_dict": duplicate_dict},
                user=user,
                data_name=data_name,
                college_id=college.get("id"),
            )
        else:
            if not is_testing_env():
                RawDataActivity().upload_raw_data.delay(
                    file={"data_dict": data_dict, "duplicate_dict": duplicate_dict},
                    user=user,
                    data_name=data_name,
                    college_id=college.get("id"),
                )

        return utility_obj.response_model(data=True, message="file uploading......")
    raise HTTPException(status_code=401, detail="file not supported")


@manage.post("/get_all_raw_data/")
@requires_feature_permission("read")
async def get_all_raw_data(
    current_user: CurrentUser,
    cache_data=Depends(cache_dependency),
    page_num: int = Query(gt=0),
    page_size: int = Query(gt=0),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get all raw data
    """
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") in ["super_admin", "client_manager"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    cache_key, data = cache_data
    if data:
        return data
    skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
    data = await RawData().retrieve_raw_data(skip, limit)
    total_raw_data = await DatabaseConfiguration().raw_data.count_documents(
        {"mandatory_field": {"$ne": False}}
    )
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total_raw_data, route_name="/manage/get_all_raw_data/"
    )
    data = {
        "data": data,
        "total": total_raw_data,
        "count": page_size,
        "pagination": response["pagination"],
        "message": "Get all raw data.",
    }
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@manage.post("/download_raw_data")
@requires_feature_permission("download")
async def download_raw_data(
    current_user: CurrentUser,
    testing: Is_testing,
    background_tasks: BackgroundTasks,
    request: Request,
    raw_data_ids: list[str] = None,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """\nAPI for downloading offline data in excel by the using of unique id.\n

    Params:\n
        raw_data_ids (list[str], optional): Unique id of offline data in the form of list. Defaults to None.
        college_id (dict, optional): College unique id. Defaults to Depends(get_college_id).

    Raises:\n
        Custom Error: If the user is invalid or not found.

    Returns:\n
        dict: Return the link of download csv file.
    """
    try:
        if not testing:
            Reset_the_settings().check_college_mapped(college.get("id"))
        if (
            user := await DatabaseConfiguration().user_collection.find_one(
                {"user_name": current_user.get("user_name")}
            )
        ) is None or user.get("role", {}).get("role_name", "") not in [
            "college_admin",
            "college_super_admin",
            "super_admin"
        ]:
            raise CustomError("permission denied")
        
        current_datetime = datetime.datetime.utcnow()
        
        for data_id in raw_data_ids:
            if len(data_id) != 24 or \
                not await DatabaseConfiguration().offline_data.find_one({"_id": ObjectId(data_id)}):
                raise CustomError("Offline data id is invalid.")

        data_list, total = await LeadUser().offline_data_list(
            raw_data_ids=raw_data_ids
        )

        background_tasks.add_task(
            DownloadRequestActivity().store_download_request_activity,
            request_type="Offline data",
            requested_at=current_datetime,
            ip_address=utility_obj.get_ip_address(request),
            user=user,
            total_request_data=total,
            is_status_completed=True,
            request_completed_at=datetime.datetime.utcnow(),
        )
        if data_list:
            data_keys = list(data_list[0].keys())
            get_url = await upload_csv_and_get_public_url(
                fieldnames=data_keys, data=data_list, name="offline_data"
            )
            return get_url
        
        raise CustomError("Data not found.")
    
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when downloading offline data. Error: {error}.",
        )


@manage.put("/display_offline/")
@requires_feature_permission("read")
async def display_offline_data(
    current_user: CurrentUser,
    payload: offline_schema = None,
    page_num: int = Query(..., gt=0),
    page_size: int = Query(..., gt=0),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    display offline data using filter and daterange
    date_range format will be 2022-10-12
    imported_by will be objectId of users
    import_status will be pending/completed
    """
    await UserHelper().is_valid_user(current_user)
    skip, limit = await utility_obj.return_skip_and_limit(
        page_num=page_num, page_size=page_size
    )
    if payload is None:
        payload = {}
    payload = jsonable_encoder(payload)
    date_range = payload.get("date_range", {})
    if date_range is None:
        date_range = {}
    start_date = end_date = None
    if date_range.get("start_date") not in ["", None] and date_range.get(
            "end_date") not in ["", None]:
        start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
    data, total = await LeadUser().offline_display(
        payload=payload,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total, route_name="/manage/display_offline/"
    )
    return {
        "data": data,
        "total": total,
        "count": len(data),
        "pagination": response["pagination"],
        "message": "data fetched successfully",
    }


@manage.post("/converted_lead_and_application_list/")
@requires_feature_permission("read")
async def converted_lead_application(
    current_user: CurrentUser,
    testing: Is_testing,
    offline_id: str,
    is_application: bool = True,
    date_range: DateRange | None = Body(None),
    page_num: int = Query(..., gt=0),
    page_size: int = Query(..., gt=0),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """\nAPI for getting the list of student and applications which is converted from raw data.\n

    Body Params:\n
        date_range (DateRange | None, optional): Date range for filtering. Defaults to Body(None).

    Params:\n
        offline_id (str): Offline data unique id for filtering.
        is_application (bool, optional): Need the list of applications or not. Defaults to True.
        page_num (int, optional): Page no which data have to fetch. Defaults to Query(..., gt=0).
        page_size (int, optional): No of data in one page. Defaults to Query(..., gt=0).
        college_id (dict, optional): College unique id. Defaults to Depends(get_college_id).

    Returns:\n
        dict: Data response
    """
    await UserHelper().is_valid_user(current_user)
    if not testing:
            Reset_the_settings().check_college_mapped(college.get("id"))
    skip, limit = await utility_obj.return_skip_and_limit(
        page_num=page_num, page_size=page_size
    )

    if date_range is None:
        date_range = {}

    date_range = await utility_obj.format_date_range(date_range)
    start_date, end_date = await utility_obj.get_start_and_end_date(date_range)
    
    data, total = await LeadUser().converted_count(
        offline_id=offline_id,
        is_application=is_application,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total, route_name="/manage/converted_lead_and_application_list/"
    )
    return {
        "data": data,
        "total": total,
        "count": len(data),
        "pagination": response["pagination"],
        "message": "data fetched successfully",
    }


@manage.post("/show_successful_lead")
@requires_feature_permission("read")
async def successful_lead(
    offline_id,
    current_user: CurrentUser,
    page_num: int = Query(..., gt=0),
    page_size: int = Query(..., gt=0),
):
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") in ["super_admin", "client_manager"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    await utility_obj.is_id_length_valid(offline_id, name="offline_id")
    skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
    successful_leads = await RawData().retrieve_successful_lead(skip, limit, offline_id)
    total = await DatabaseConfiguration().raw_data.count_documents(
        {"offline_data_id": ObjectId(offline_id)}
    )
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total, route_name="/manage/show_successful_lead/"
    )
    return {
        "data": successful_leads,
        "total": total,
        "count": page_size,
        "pagination": response["pagination"],
        "message": "data fetch successfully",
    }


@manage.get("/list_of_raw_data_names/", summary="Get list of raw data names")
@requires_feature_permission("read")
async def list_of_raw_data_names(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get list of raw data names
    """
    await UserHelper().is_valid_user(current_user)
    raw_data_names = await RawData().retrieve_raw_data_names()
    return {"data": raw_data_names, "message": "Get list of raw data names."}


@manage.put("/lead_upload_display_offline/")
@requires_feature_permission("read")
async def display_lead_offline_data(
    current_user: CurrentUser,
    payload: offline_schema = None,
    page_num: int = Query(..., gt=0),
    page_size: int = Query(..., gt=0),
):
    """
    display offline data using filter and daterange
    date_range format will be 2022-10-12
    imported_by will be objectId of users
    import_status will be pending/completed
    """
    await UserHelper().is_valid_user(current_user)
    skip, limit = await utility_obj.return_skip_and_limit(
        page_num=page_num, page_size=page_size
    )
    if payload is None:
        payload = {}
    payload = jsonable_encoder(payload)
    date_range = payload.get("date_range", {})
    if date_range is None:
        date_range = {}
    start_date, end_date = await utility_obj.get_start_and_end_date(date_range)
    data, total = await LeadUser().offline_display(
        payload=payload,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
        lead_upload=True,
    )
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total, route_name="/manage/lead_upload_display_offline/"
    )
    return {
        "data": data,
        "total": total,
        "count": len(data),
        "pagination": response["pagination"],
        "message": "data fetched successfully",
    }


@manage.post("/system_successful_lead_data")
@requires_feature_permission("read")
async def system_successful_lead(
    offline_id,
    current_user: CurrentUser,
    page_num: int = Query(..., gt=0),
    page_size: int = Query(..., gt=0),
):
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") in ["super_admin", "client_manager"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    await utility_obj.is_id_length_valid(offline_id, name="offline_id")
    skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
    successful_leads = await RawData().system_retrieve_successful_lead(
        skip, limit, offline_id
    )
    total = 0
    if (
    offline_data := await DatabaseConfiguration().lead_upload_history.find_one(
            {"_id": ObjectId(offline_id)}
    )) is not None:
        total = offline_data.get("successful_lead_count", 0)
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total, route_name="/manage/system_successful_lead_data/"
    )
    return {
        "data": successful_leads,
        "total": total,
        "count": page_size,
        "pagination": response["pagination"],
        "message": "data fetch successfully",
    }


@manage.post("/action_on_raw_data/", summary="Perform action on raw data")
@requires_feature_permission("write")
async def action_on_raw_data(
    current_user: CurrentUser,
    action: Action,
    payload: ActionPayload,
    request: Request,
    template_id: str = None,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Perform action on successful lead of raw data
    """
    email_preferences = {
        key: str(value) for key, value in college.get("email_preferences", {}).items()
    }
    payload = {
        key: value for key, value in payload.model_dump().items() if value is not None
    }
    user = await UserHelper().is_valid_user(current_user)
    ip_address = utility_obj.get_ip_address(request)
    data = await RawData().retrieve_raw_data_mandatory_fields(
        payload.get("offline_ids")
    )
    toml_data = utility_obj.read_current_toml_file()
    if toml_data.get("testing", {}).get("test") is False:
        # TODO: Not able to add student timeline data
        #  using celery task when environment is
        #  demo. We'll remove the condition when
        #  celery work fine.
        if settings.environment in ["demo"]:
            RawDataActivity().perform_action_on_raw_data_leads(
                email_preferences=email_preferences,
                action=action,
                payload=payload,
                data=data,
                user=user,
                ip_address=ip_address,
                current_user=current_user,
                template_id=template_id,
                college_id=college.get("id"),
            )
        else:
            if not is_testing_env():
                RawDataActivity().perform_action_on_raw_data_leads.delay(
                    email_preferences=email_preferences,
                    action=action,
                    payload=payload,
                    data=data,
                    user=user,
                    ip_address=ip_address,
                    current_user=current_user,
                    template_id=template_id,
                    college_id=college.get("id"),
                )
    return {"message": "Performed action on raw data"}


@manage.post("/delete_lead_offline_data/", summary="delete the lead offline data")
@requires_feature_permission("delete")
async def delete_lead_data(
    offline_ids: list[str],
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Delete the lead offline data and offline data from lead history collection
    params:
        offline_ids (list): Get the offline id as a string
        current_user (str): Get the current user automatically from the token

    return:
        response: raw data has beem deleted
    """
    await UserHelper().is_valid_user(current_user)
    for _id in offline_ids:
        await utility_obj.is_id_length_valid(_id, "offline_id")
    try:
        if not is_testing_env():
            RawDataActivity().delete_student_by_offline.delay(
                offline_ids, college_id=college.get("id")
            )
    except KombuError as celery_error:
        logger.error(f"error assign to the counselor raw data {celery_error}")
    except Exception as error:
        logger.error(f"error assign to the counselor raw data {error}")
    return {"data": "raw data has been deleted"}


@manage.put("/duplicate_failed_data/")
@requires_feature_permission("read")
async def duplicate_or_failed_data(
    offline_id: str,
    current_user: CurrentUser,
    data_type: str = Query("duplicate"),
    page_num: int = Query(1, gt=0),
    page_size: int = Query(25, gt=0),
    lead_upload: bool = False,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get duplicate and failed data from the offline database

    Params\n:
        - offline_ids (str): Get the offline id
        - current_user (str): Get the username of current user
        - data_type (str): Get the duplicate or failed string in these fields
        - college (dict): Get the details of current college
        - page_num (int): Get the integer number
        - page_size (int): Get the integer number for number of data to display

    Return\n:
        - A list contains of the duplicate and failed data

    Raises:
        - Exception: An exception with status code 500 when certain condition
        fails.
    """
    if not ObjectId.is_valid(offline_id):
        raise HTTPException(status_code=422,
                            detail=f"{offline_id} ObjectId is invalid")
    if data_type not in ["duplicate", "failed"]:
        raise HTTPException(status_code=422,
                            detail=f"{data_type} is not valid, duplicate or "
                                   f"failed are valid string")
    try:
        return await LeadUser().get_duplicate_or_failed_data(
            offline_id=offline_id, data_type=data_type,
            page_num=page_num, page_size=page_size, lead_upload=lead_upload
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Some error occur {error}")

