"""
This file contains functions related to application specific
"""
from bson import ObjectId
from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException

from app.core.utils import requires_feature_permission
from app.database.aggregation.admin_user import AdminUser
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import CurrentUser, cache_dependency, \
    insert_data_in_cache
from app.helpers.application_whopper.application_wrapper_helper import \
    ApplicationWrapper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.applications import lead_filter

application_wrapper = APIRouter()


@application_wrapper.get("/today_application_count")
@requires_feature_permission("read")
async def today_application_counts(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        season: str | None = Query(None,
                                   description="Enter season id if want to"
                                               " get data season-wise")
):
    """
    Get the count of the application data.

    Params:\n
        - college_id (str): An unique identifier/id of a college for
            get the college data.
        - season (str | None): Either None or unique identifier of season
            which useful for get season-wise data.

    Returns:\n
        - dict: A dictionary which contains count of the various application
            data.

    Exception:\n
        - HTTPException: An error occurred with status code 500 when something
            went wrong in backend code.
    """
    user = await UserHelper().is_valid_user(current_user)
    if current_user.get("allowed_features").get("read") is False:
        raise HTTPException(status_code=401, detail="Permission denied")
    try:
        counselor_ids = []
        role_name = user.get("role", {}).get("role_name")
        if role_name == "college_counselor":
            counselor_ids = [ObjectId(user.get('_id'))]
        elif role_name == "college_head_counselor":
                counselor_ids = await AdminUser().get_users_ids_by_role_name(
                    "college_counselor", college.get("id"),
                    user.get("_id"))
                counselor_ids.append(ObjectId(user.get('_id')))

        return await ApplicationWrapper().today_application_count(
            counselor_ids, season)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"{error}")


@application_wrapper.post("/application_data_count")
@requires_feature_permission("read")
async def get_today_application_data(
        data_type: str,
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        payload: lead_filter = None,
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        season: str | None = Query(None,
                                   description="Enter season id if want to"
                                               " get data season-wise")
):
    """
    Get the lead data based on counts

    Params:\n
        - data_type (str): Get the string value of the data type
         like: fresh_lead, admission_confirm, interested, follow_up,
          today_assigned
        - college_id (str): Unique identifier of college for get college data.
        - season (str | None): Either None or unique identifier of season
            which useful for get season-wise data.

    Returns:\n
        dict: A dictionary which contains the data by data type.
    """
    if (user := await DatabaseConfiguration().user_collection.find_one(
            {"user_name": current_user.get("user_name")})) is None:
        raise HTTPException(status_code=401, detail="Permission denied")
    role_name = user.get("role", {}).get("role_name")
    counselor_ids =[]
    if role_name == "college_counselor":
        counselor_ids = [ObjectId(user.get('_id'))]
    elif role_name == "college_head_counselor":
            counselor_ids = await AdminUser().get_users_ids_by_role_name(
                "college_counselor", college.get("id"), user.get("_id"))
            counselor_ids.append(ObjectId(user.get('_id')))
    cache_key, data = cache_data
    if data:
        return data
    if payload is None:
        payload = {}
    payload = jsonable_encoder(payload)
    try:
        data = await ApplicationWrapper().get_application_data_count(
            lead_data=data_type, payload=payload,
            page_num=page_num, page_size=page_size,
            counselor_ids=counselor_ids, season=season)
        if cache_key:
            await insert_data_in_cache(cache_key, data)
        return data
    except Exception as error:
        raise HTTPException(status_code=500, detail=error)
