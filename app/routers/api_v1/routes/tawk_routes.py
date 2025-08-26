"""
This file contains APIs related to Tawk chat bot data integration in CRM.
"""

from fastapi import APIRouter, Depends, Request
from app.core.log_config import get_logger
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.core.custom_error import CustomError
from fastapi.exceptions import HTTPException
from app.helpers.tawk_webhook.tawk_chat_insertion_helper import TawkChatWebhook
from app.helpers.tawk_webhook.get_tawk_chat_data import GetTawkChatData
from app.dependencies.oauth import cache_dependency, insert_data_in_cache, cache_invalidation
from app.helpers.user_curd.user_configuration import UserHelper
from app.dependencies.oauth import CurrentUser
from app.models.student_user_schema import User
from app.core.utils import utility_obj, requires_feature_permission

tawk_webhook_routers = APIRouter()
logger = get_logger(name=__name__)


@tawk_webhook_routers.post("/webhook",
                           summary="Webhook API for store tawk chat data in "
                                   "our database.")
async def create_tawk_chat_data(
        request: Request,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """
    Webhook API for store chat data in our database.

    Params:
        - college_id (str): Unique id of college.

    Returns:
        - dict: A dictionary which contains information about store chat data.
    """
    try:
        raw_body = await request.body()
        signature = request.headers.get('x-tawk-signature')
        data = await TawkChatWebhook().chat_data_insertion(raw_body, signature)
        await cache_invalidation(api_updated="tawk/")
        return data
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        logger.error(
            "An error got when storing the tawk chat data in the database.")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@tawk_webhook_routers.get("/get_all_data",
                          summary="Get all chat data from the database.")
@requires_feature_permission("read")
async def get_tawk_chat_data(
        current_user: CurrentUser,
        page_num: int = 1,
        page_size: int = 10,
        cache_data=Depends(cache_dependency),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """
    API for getting all the users chat data information which is saved by the
    webhook of Tawk.

    Params:
        - page_num (int, optional): Page no which data has to be fetched.
            Defaults to 1.
        - page_size (int, optional): No. of data in one page.
            Defaults to 10.
        - college_id (str): Unique id of college.

    Returns:
        - dict: User chat data set in the format of json.
    
    Raise:
        - 401 (Not enough permissions): An error occurred with status
            code 401 when user don't have permission to get chat count data. -
        - Exception: An error occurred with status code 500 when something wrong
            happen in the code.
    """
    await UserHelper().is_valid_user(current_user)

    try:
        cache_key, data = cache_data
        if data:
            return data

        data = await GetTawkChatData().get_chat_data()

        response = await utility_obj.pagination_in_api(
            page_num, page_size, data, len(data),
            route_name="/tawk/get_all_data")

        data = {
            "data": response["data"],
            "total": len(data),
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Get all Tawk chat data.",
        }

        if cache_key:
            await insert_data_in_cache(cache_key, data)

        return data

    except Exception as error:
        logger.error(f"Error - {error}")
