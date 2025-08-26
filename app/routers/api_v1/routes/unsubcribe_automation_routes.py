"""
This file contains API route related to unsubscribe automation
"""

from fastapi import APIRouter
from app.core.log_config import get_logger
from app.dependencies.oauth import insert_data_in_cache
from app.helpers.unsubscribe_cache_helper import UnsubscribeHelper

logger = get_logger(name=__name__)
unsubscribe = APIRouter()


@unsubscribe.get("/collect_unsubscribed_students/")
async def collect_unsubscribed_students():
    """
    This API stores unsubscribed students list into the cache
    This API is called for every one hour,
    For every call it will
    search for unsubscribed students in database and also validate
    and fetch students whose mails are hard bounced and list all of them
    After this the list is stored in cache systems.
    """
    try:
        result_list = await UnsubscribeHelper().check_unsubscribe()
        result_list.extend(await UnsubscribeHelper().check_last_opened_hard_bounce(result_list))
        mails = await UnsubscribeHelper().get_email_ids(result_list)
        await insert_data_in_cache(cache_key="unsubscribed_student_list", data=mails, expiration_time=21600, set=True)
        return "Done Successfully"
    except Exception as error:
        logger.error(f"Some error occurred which inserting data in redis cache: {error}")
