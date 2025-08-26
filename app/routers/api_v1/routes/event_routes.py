"""
This file contain API routes/endpoint related to event functionality
"""
from typing import Union
from fastapi import APIRouter, Depends, Query, BackgroundTasks, Body, Request
from fastapi.encoders import jsonable_encoder
from app.core.utils import utility_obj, requires_feature_permission
from app.database.aggregation.event import Event
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import CurrentUser
from app.helpers.event.configuration import EventHelper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.event_schema import AddUpdateEvent, EventFilter
from app.models.student_user_schema import User
from datetime import datetime
from app.background_task.admin_user import DownloadRequestActivity
from app.s3_events.s3_events_configuration import upload_csv_and_get_public_url
from fastapi.exceptions import HTTPException

event_router = APIRouter()


@event_router.post("/type/add_or_update/",
                   summary="Add event types in the database")
@requires_feature_permission("write")
async def add_event_types(event_types: list[str],
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)):
    """
    Add event types in the database
    """
    return await EventHelper().add_event_types_into_database(
        current_user, college, event_types)


@event_router.get("/types", summary="Get event types from the database")
@requires_feature_permission("read")
async def get_event_types(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)):
    """
    Get event types from the database
    """
    return {"data": dict(await EventHelper().get_event_types(
        college.get('id'), current_user)).get('event_types', []),
            "message": "Get event types."}


@event_router.post("/add_or_update/", summary="Add event data in the database")
@requires_feature_permission("write")
async def add_event_data(payload: AddUpdateEvent,
                        current_user: CurrentUser,
                         college: dict = Depends(get_college_id),
                         event_id: str = Query(None,
                                               description="Enter event id")):
    """
    Add event data in the database
    Event start/end date format will be dd/mm/YYYY
    """
    return await EventHelper().add_event_data_into_database(
        current_user, college, payload, event_id)


@event_router.delete("/delete_by_name_or_id/",
                     summary="Delete event data from database")
@requires_feature_permission("delete")
async def delete_event_by_name_or_id(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        college: dict = Depends(get_college_id),
        event_id: str = Query(None, description="Enter event id"),
        event_name: str = Query(None, description="Enter event name")):
    """
    Delete event from database by name or id
    """
    return await EventHelper().delete_event_from_database(
        background_tasks, current_user, event_name, event_id)


@event_router.get("/get_by_name_or_id/",
                  summary="Delete event data from database")
@requires_feature_permission("read")
async def get_event_data_by_name_or_id(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        college: dict = Depends(get_college_id),
        event_id: str = Query(None, description="Enter event id"),
        event_name: str = Query(None, description="Enter event name")):
    """
    Get event data by name or id
    """
    return await EventHelper().get_event_data_by_name_or_id(
        background_tasks, current_user, event_name, event_id)


@event_router.post("s/", summary="Get events data from database")
@requires_feature_permission("read")
async def get_events_data(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        request: Request,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        season: str = Body(
            None, description="Enter season value if want to get data "
                              "season-wise"),
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
        event_filter: EventFilter = None,
        download_data: bool = False
):
    """
    Get events data
    """
    current_datetime = datetime.utcnow()
    user = await UserHelper().is_valid_user(current_user)
    if event_filter is not None:
        event_filter = {key: value for key, value in
                        event_filter.model_dump().items() if value is not None}
    else:
        event_filter = {}
    event_filter = jsonable_encoder(event_filter)
    if season == "":
        season = None
    total_data, data = await Event().get_events_data(
        page_num, page_size, event_filter, season=season)
    response = {}
    if page_num and page_size:
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, total_data, route_name="/events/"
        )
    if download_data:
        background_tasks.add_task(
            DownloadRequestActivity().store_download_request_activity,
            request_type="Applications data", requested_at=current_datetime,
            ip_address=utility_obj.get_ip_address(request),
            user=user,
            total_request_data=len(data), is_status_completed=True,
            request_completed_at=datetime.utcnow())
        if data:
            data_keys = list(data[0].keys())
            get_url = await upload_csv_and_get_public_url(
                fieldnames=data_keys, data=data, name="applications_data"
            )
            return get_url
        raise HTTPException(status_code=404, detail="Event data not found.")
    return {
        "data": data,
        "total": total_data,
        "count": page_size,
        "pagination": response.get("pagination", {}),
        "message": "Get all events data."
    }
