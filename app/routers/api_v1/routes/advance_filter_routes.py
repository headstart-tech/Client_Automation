"""
This file contains API routes related to advance filter
"""
from fastapi import APIRouter, Depends, Query
from app.core.log_config import get_logger
from app.dependencies.oauth import CurrentUser, cache_dependency, \
    insert_data_in_cache
from app.dependencies.college import get_college_id_short_version
from app.models.student_user_schema import User
from app.helpers.user_curd.user_configuration import UserHelper
from app.database.aggregation.advance_filter import AdvanceFilter
from typing import Union
from app.core.utils import utility_obj, requires_feature_permission
from fastapi.exceptions import HTTPException

advance_filter_router = APIRouter()
logger = get_logger(name=__name__)


@advance_filter_router.get(
    "/categories_or_fields/", response_description="Get the advance filter categories.")
@requires_feature_permission("read")
async def get_advance_filter_categories(
        current_user: CurrentUser,
        category_name: str | None = None,
        college_data: User = Depends(get_college_id_short_version(short_version=True)),
        cache_data=Depends(cache_dependency),
        search_pattern: str | None = Query(
            None, description="Enter search pattern. Useful for get advance "
                              "filter categories based on search_pattern."),
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0)
):
    """
    Get the advance filter categories.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        cache_key, data = cache_data
        if data:
            return data
        data, total = await AdvanceFilter().get_categories_or_fields(
            college_data.get("id"), search_pattern, category_name=category_name)
        if page_num and page_size:
            response = await utility_obj.pagination_in_api(
                page_num, page_size, data, total, "/categories/")
            data = response.get("data")
        all_data = {"total": total, "data": data,
                    "message": "Get the advance filter categories."}
        if cache_key:
            await insert_data_in_cache(cache_key, all_data)
        return all_data
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Error - {error}")
