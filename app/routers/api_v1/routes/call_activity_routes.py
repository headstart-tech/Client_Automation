"""
This file contains API routes related to call activity
"""

import functools
from datetime import datetime
from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, Body, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError
from meilisearch.errors import MeilisearchCommunicationError, \
    MeilisearchApiError

from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.database.aggregation.college_counselor import (
    CounselorCallHistory,
    CounselorLead,
)
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import CurrentUser, is_testing_env
from app.helpers.call_activity.call_activity_glance import call_activity_glance
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.applications import DateRange, call_activity
from app.models.call_activity_schema import CallActivity

logger = get_logger(name=__name__)
call_activities = APIRouter()


@call_activities.get(
    "/counselor_leads_details/",
    summary="Get counselor leads details like name and mobile number",
)
async def counselor_leads_details(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    page_num: int | None = Query(None, gt=0),
    page_size: int | None = Query(None, gt=0),
    search_input: str = Query(None, description="Enter search pattern"),
):
    """
    Get counselor leads details
    """
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") != "college_counselor":
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    data, total_data = await CounselorLead().get_counselor_leads_details(
        ObjectId(user.get("_id")), page_num, page_size, search_input
    )
    response = {}
    if page_num is not None and page_size is not None:
        response = await utility_obj.pagination_in_aggregation(
            page_num,
            page_size,
            total_data,
            route_name="/call_activities/counselor_leads_details/",
        )
    return {
        "data": data,
        "total": total_data,
        "count": page_size,
        "pagination": response.get("pagination"),
        "message": "Get counselor leads details.",
    }


@call_activities.post("/add/", summary="Store call activity data")
async def add_call_activity(
    request: Request,
    call_activity: CallActivity,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Add call activity data in the database collection
    """
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") != "college_counselor":
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    call_activity = jsonable_encoder(call_activity)
    if not call_activity.get("type"):
        raise HTTPException(status_code=422, detail="Call type not provided.")
    elif not call_activity.get("mobile_numbers"):
        raise HTTPException(
            status_code=422, detail="Student mobile numbers not provided."
        )
    elif not call_activity.get("call_started_datetimes"):
        raise HTTPException(
            status_code=422, detail="Call started datetimes not provided."
        )
    elif not call_activity.get("call_durations"):
        raise HTTPException(status_code=422, detail="Call durations not provided.")
    
    if any(
        isinstance(call_activity.get(field), list) and len(call_activity.get(field)) > 50
        for field in ["type", "mobile_numbers", "call_started_datetimes", "call_durations"]
    ):
        raise HTTPException(status_code=422, detail="Multiple data items are not allowed.") 

    errors = []

    for call_type, student_mobile_number, call_started_datetime, call_duration in zip(
        call_activity.get("type"),
        call_activity.get("mobile_numbers"),
        call_activity.get("call_started_datetimes"),
        call_activity.get("call_durations"),
    ):

        student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"basic_details.mobile_number": str(student_mobile_number)}
        )
        if not student:
            continue
        if str(call_type).title() not in ["Inbound", "Outbound"]:
            errors.append(
                f"Call type should be any of the following: Inbound and Outbound for mobile number "
                f'{student_mobile_number} and student name {utility_obj.name_can(student.get("basic_details", {}))}'
            )
            continue
        if "am" not in call_started_datetime and "pm" not in call_started_datetime:
            try:
                # Convert string to datetime object
                datetime_obj = datetime.strptime(
                    call_started_datetime, "%d-%b-%Y %H:%M:%S"
                )

                # Format the datetime object in 12-hour format
                call_started_datetime = datetime_obj.strftime("%d-%b-%Y %I:%M:%S %p")
            except Exception:
                pass
        if " " in call_started_datetime:
            call_started_datetime = call_started_datetime.replace(" ", " ")
        if str(call_type).title() == "Inbound":
            call_to = ObjectId(user.get("_id"))
            call_from = str(student_mobile_number)
            call_to_name = utility_obj.name_can(user)
            call_from_name = utility_obj.name_can(student.get("basic_details", {}))
        else:
            call_to = str(student_mobile_number)
            call_from = ObjectId(user.get("_id"))
            call_to_name = utility_obj.name_can(student.get("basic_details", {}))
            call_from_name = utility_obj.name_can(user)

        data = {
            "type": str(call_type).title(),
            "call_to": call_to,
            "call_from": call_from,
            "call_started_at": call_started_datetime,
            "call_duration": call_duration,
        }

        if await DatabaseConfiguration().call_activity_collection.find_one(data):
            continue

        data.update({
            "call_to_name": call_to_name,
            "call_from_name": call_from_name,
            "created_at": datetime.utcnow(),
        })

        await DatabaseConfiguration().call_activity_collection.insert_one(data)

        try:
            toml_data = utility_obj.read_current_toml_file()
            if toml_data.get("testing", {}).get("test") is False:
                # TODO: Not able to add student timeline data in the
                #  DB when performing celery task so added condition
                #  which add student timeline when environment is
                #  not development. We'll remove the condition when
                #  celery work fine.
                if str(call_type).title() == "Inbound":
                    if call_duration == 0:
                        # TODO: Not able to add student timeline data
                        #  using celery task when environment is
                        #  demo. We'll remove the condition when
                        #  celery work fine.
                        if settings.environment in ["demo"]:
                            StudentActivity().student_timeline(
                                student_id=str(student.get("_id")),
                                event_type="Call Activity",
                                event_status="Update call details",
                                message=f"{utility_obj.name_can(student.get('basic_details', {}))} "
                                f"made an Inbound call but is missed by {utility_obj.name_can(user)}",
                                college_id=str(student.get("college_id")),
                            )
                        else:
                            if not is_testing_env():
                                StudentActivity().student_timeline.delay(
                                    student_id=str(student.get("_id")),
                                    event_type="Call Activity",
                                    event_status="Update call details",
                                    message=f"{utility_obj.name_can(student.get('basic_details', {}))} "
                                    f"made an Inbound call but is missed by {utility_obj.name_can(user)}",
                                    college_id=str(student.get("college_id")),
                                )
                    else:
                        # TODO: Not able to add student timeline data
                        #  using celery task when environment is
                        #  demo. We'll remove the condition when
                        #  celery work fine.
                        if settings.environment in ["demo"]:
                            StudentActivity().student_timeline(
                                student_id=str(student.get("_id")),
                                event_type="Call Activity",
                                event_status="Update call details",
                                message=f"Inbound Call of duration: "
                                f"{call_duration // 60}:{call_duration % 60}"
                                f" received by {utility_obj.name_can(user)}",
                                college_id=str(student.get("college_id")),
                            )
                        else:
                            if not is_testing_env():
                                StudentActivity().student_timeline.delay(
                                    student_id=str(student.get("_id")),
                                    event_type="Call Activity",
                                    event_status="Update call details",
                                    message=f"Inbound Call of duration: "
                                    f"{call_duration // 60}:{call_duration % 60}"
                                    f" received by {utility_obj.name_can(user)}",
                                    college_id=str(student.get("college_id")),
                                )
                else:
                    if call_duration != 0:
                        # TODO: Not able to add student timeline data
                        #  using celery task when environment is
                        #  demo. We'll remove the condition when
                        #  celery work fine.
                        if settings.environment in ["demo"]:
                            StudentActivity().student_timeline(
                                student_id=str(student.get("_id")),
                                event_type="Call Activity",
                                event_status="Update call details",
                                message=f"Outbound Call of duration: "
                                f"{call_duration // 60}:{call_duration % 60}"
                                f" made by {utility_obj.name_can(user)}",
                                college_id=str(student.get("college_id")),
                            )
                        else:
                            if not is_testing_env():
                                StudentActivity().student_timeline.delay(
                                    student_id=str(student.get("_id")),
                                    event_type="Call Activity",
                                    event_status="Update call details",
                                    message=f"Outbound Call of duration: "
                                    f"{call_duration // 60}:{call_duration % 60}"
                                    f" made by {utility_obj.name_can(user)}",
                                    college_id=str(student.get("college_id")),
                                )
                    else:
                        # TODO: Not able to add student timeline data
                        #  using celery task when environment is
                        #  demo. We'll remove the condition when
                        #  celery work fine.
                        if settings.environment in ["demo"]:
                            StudentActivity().student_timeline(
                                student_id=str(student.get("_id")),
                                event_type="Call Activity",
                                event_status="Update call details",
                                message=f"Outbound Call of duration: "
                                f"{utility_obj.name_can(user)} made a"
                                f" call but {utility_obj.name_can(student.get('basic_details', {}))}"
                                f" did not pick",
                                college_id=str(student.get("college_id")),
                            )
                        else:
                            if not is_testing_env():
                                StudentActivity().student_timeline.delay(
                                    student_id=str(student.get("_id")),
                                    event_type="Call Activity",
                                    event_status="Update call details",
                                    message=f"Outbound Call of duration: "
                                    f"{utility_obj.name_can(user)} made a"
                                    f" call but {utility_obj.name_can(student.get('basic_details', {}))}"
                                    f" did not pick",
                                    college_id=str(student.get("college_id")),
                                )

        except KombuError as celery_error:
            logger.error(
                f"error storing inbound details" f" timeline data {celery_error}"
            )
        except Exception as error:
            logger.error(f"error storing inbound details" f" timeline data {error}")
    call_activity["call_from"] = utility_obj.name_can(user)
    return {
        "data": call_activity,
        "message": "Call activities added.",
        "errors": errors,
    }


@call_activities.get("/history/", summary="Get counselor call history")
async def counselor_call_history(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    page_num: int | None = Query(None, gt=0),
    page_size: int | None = Query(None, gt=0),
    search_input: str = Query(None, description="Enter search pattern"),
):
    """
    Get counselor call history
    """
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") != "college_counselor":
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    data, total_data = await CounselorCallHistory().get_counselor_call_history(
        user.get("_id"),
        page_num=page_num,
        page_size=page_size,
        search_input=search_input,
    )
    response = {}
    if page_num is not None and page_size is not None:
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, total_data, route_name="/call_activities/history/"
        )
    return {
        "data": data,
        "total": total_data,
        "count": page_size,
        "pagination": response.get("pagination"),
        "message": "Get call history of counselor.",
    }


@call_activities.put("/counselor_wise_outbound_report")
async def counselor_wise_outbound_activity(
    page_num: int,
    current_user: CurrentUser,
    counselor_id: List[str] | None = Body(None),
    date_range: DateRange | None = Body(None),
    payload: call_activity = Depends(functools.partial(call_activity)),
    page_size: int = Query(gt=0),
    client=Depends(utility_obj.get_meili_client),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    get all counselor wise outbound call activity details
    """
    user = await UserHelper().check_user_has_permission(current_user)
    filters = [f"type = Outbound"]
    date_range = await utility_obj.format_date_range(date_range)
    start_date, end_date = date_range.get("start_date"), date_range.get("end_date")
    if start_date and end_date:
        start_date, end_date = await utility_obj.date_change_format_unix_time(
            date_range.get("start_date"), date_range.get("end_date")
        )
        filters.append([f"created_at >= {start_date} AND created_at <= {end_date}"])
    payload = jsonable_encoder(payload)
    user_role = user.get("role", {}).get("role_name")
    if counselor_id:
        filters.append(f"counselor_id IN {counselor_id}")
    if payload.get("lead_status") and payload.get("lead_status") != "":
        filters.append([f"lead_status = {payload.get('lead_status')}"])
    if payload.get("call_status") and payload.get("call_status") != "":
        filters.append([f"call_status = {payload.get('call_status')}"])
    if user_role == "college_publisher_console":
        filters.append([f"source={str(user.get('associated_source_value'))}"])
    elif user_role == "college_head_counselor":
        result = DatabaseConfiguration().user_collection.aggregate(
            [{"$match": {"head_counselor_id": ObjectId(user.get("_id"))}}]
        )
        counselor_list = [str(data.get("_id")) async for data in result]
        filters.append([f"counselor_id IN {counselor_list}"])
    elif user_role == "college_counselor":
        filters.append([f"counselor_id={str(user.get('_id'))}"])
    name = f"{settings.client_name.lower().replace(' ', '_')}_{settings.current_season.lower()}"
    try:
        all_call_record = client.index(f"{name}_call_activity").search(
            payload.get("search"),
            {
                "filter": filters,
                "sort": ["created_at:desc"],
                "showMatchesPosition": True,
                "attributesToHighlight": ["*"],
                "highlightPreTag": "<span class='search-query-highlight'>",
                "highlightPostTag": "</span>",
                "hitsPerPage": page_size,
                "page": page_num,
            },
        )
        return {
            "data": all_call_record.get("hits"),
            "total": all_call_record.get("totalHits"),
            "count": all_call_record.get("hitsPerPage"),
            "page_num": all_call_record.get("page"),
            "message": "Fetched calls data successfully",
        }
    except MeilisearchCommunicationError as meil_error:
        logger.error(f"Error - {str(meil_error.args)}")
        raise HTTPException(status_code=404, detail="meilisearch server is not running")
    except MeilisearchApiError as meil_error:
        logger.error(f"Error - {str(meil_error.args)}")
        raise HTTPException(status_code=404, detail="Something went wrong")


@call_activities.get("/one_glance_view")
async def one_glance_view_call(
    current_user: CurrentUser, college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    this collect all call and total duration
    """
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") in [
        "college_head_counselor",
        "college_counselor",
        "college_publisher_console",
    ]:
        raise HTTPException(status_code=401, detail="Not enough permissions")
    return await call_activity_glance().get_total_call_duration()


@call_activities.put("/counselor_wise_inbound_report")
async def counselor_wise_inbound_activity(
    page_num: int,
    current_user: CurrentUser,
    client=Depends(utility_obj.get_meili_client),
    counselor_id: List[str] | None = Body(None),
    date_range: DateRange | None = Body(None),
    payload: call_activity = Depends(functools.partial(call_activity)),
    page_size: int = Query(gt=0),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    get all counselor wise inbound call activity details
    """
    user = await UserHelper().check_user_has_permission(current_user)
    user_role = user.get("role", {}).get("role_name")
    filters = [f"type = Inbound"]
    date_range = await utility_obj.format_date_range(date_range)
    start_date, end_date = date_range.get("start_date"), date_range.get("end_date")
    if start_date and end_date:
        start_date, end_date = await utility_obj.date_change_format_unix_time(
            date_range.get("start_date"), date_range.get("end_date")
        )
        filters.append([f"created_at >= {start_date} AND created_at <= {end_date}"])
    payload = jsonable_encoder(payload)
    if counselor_id:
        filters.append(f"counselor_id IN {counselor_id}")
    if payload.get("lead_status") and payload.get("lead_status") != "":
        filters.append([f"lead_status = {payload.get('lead_status')}"])
    if payload.get("call_status") and payload.get("call_status") != "":
        filters.append([f"call_status = {payload.get('call_status')}"])
    if user_role == "college_publisher_console":
        filters.append([f"source={str(user.get('associated_source_value'))}"])
    elif user_role == "college_head_counselor":
        result = DatabaseConfiguration().user_collection.aggregate(
            [{"$match": {"head_counselor_id": ObjectId(user.get("_id"))}}]
        )
        counselor_list = [str(data.get("_id")) async for data in result]
        filters.append([f"counselor_id IN {counselor_list}"])
    elif user_role == "college_counselor":
        filters.append([f"counselor_id={str(user.get('_id'))}"])
    name = f"{settings.client_name.lower().replace(' ', '_')}" f"_{settings.current_season.lower()}"
    try:
        all_call_record = client.index(f"{name}_call_activity").search(
            payload.get("search"),
            {
                "filter": filters,
                "sort": ["created_at:desc"],
                "showMatchesPosition": True,
                "attributesToHighlight": ["*"],
                "highlightPreTag": "<span class='search-" "query-highlight'>",
                "highlightPostTag": "</span>",
                "hitsPerPage": page_size,
                "page": page_num,
            },
        )
        return {
            "data": all_call_record.get("hits"),
            "total": all_call_record.get("totalHits"),
            "count": all_call_record.get("hitsPerPage"),
            "page_num": all_call_record.get("page"),
            "message": "Fetched calls data successfully",
        }
    except MeilisearchCommunicationError as meil_error:
        logger.error(f"Error - {str(meil_error.args)}")
        raise HTTPException(status_code=404, detail="meilisearch server is not running")
    except MeilisearchApiError as meil_error:
        logger.error(f"Error - {str(meil_error.args)}")
        raise HTTPException(status_code=404, detail="Something went wrong")


@call_activities.post(
    "/counselor_wise_data/",
    summary="Get the counselor-wise call activity data count" ".",
)
async def counselor_wise_call_activity_data(
    current_user: CurrentUser,
    date_range: DateRange | None = Body(None),
    college: dict = Depends(get_college_id),
    page_num: int = Query(gt=0),
    page_size: int = Query(gt=0),
) -> dict:
    """
    Get counselor wise call activity data count.

    Params:
        - college_id (str): An unique identifier of a college.
            e.g., 123456789012345678901234
        - page_num (int): A integer number which represents page number where
            want to show data. e.g., 1
        - page_size (int): A integer number which represents data count per
            page. e.g., 25

    Request body parameters:
        - date_range (DateRange | None): Either none or a dictionary which
            contains start date and end date which useful for filter data
            according to date range.
            e.g., {"start_date": "2023-10-27", "end_date": "2023-10-27"}

    Returns:
        - dict: A dictionary which contains counselor-wise call activity data
            count.

    Raises:
        - Exception: An exception which occur when any condition fails.
    """
    user = await UserHelper().is_valid_user(current_user)
    date_range = await utility_obj.format_date_range(date_range)
    try:
        return await CounselorCallHistory().counselor_wise_call_activity_data(
            user, date_range, page_num, page_size, college
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")
