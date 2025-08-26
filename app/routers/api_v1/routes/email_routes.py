"""
This file contain API routes/endpoints related to email functionality
"""
from bson import ObjectId
from fastapi import APIRouter, Request, HTTPException, status

from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.database.aggregation.communication_timeline import CommunicationLog
from app.database.configuration import DatabaseConfiguration
from app.dependencies.jwttoken import Authentication
from app.dependencies.oauth import cache_invalidation
from app.helpers.email_activity.email_unsubscribe import unsubscribe
from app.models.email_schema import EmailWebhook

logger = get_logger(name=__name__)

email_router = APIRouter()


@email_router.post('/webhook/', summary="Webhook for capture email status")
async def capture_email_status(request: Request, payload: EmailWebhook):
    """
    Webhook for capture email status by karix
    """
    await CommunicationLog().capture_email_status_karix(request, payload)


@email_router.get("/unsubscribe/{token}")
async def unsubscribe_the_email(token: str,
                                unsubscribe_status: bool = False,
                                is_raw_data: str = "false",
                                data_segment_id: str = None,
                                release_type: str = None,
                                template_id: str = None,
                                user_id: str = None,
                                reason: str = None,
                                category: str = None,
                                release_date: str = None
                                ):
    """
    Unsubscribe a user from promotional email notifications.

    Params:
        token (str): Unique token identifying the user.
        unsubscribe_status (bool, optional): Flag indicating whether to unsubscribe. Defaults to False.
        is_raw_data (str, optional): Indicates if raw data is included. Defaults to "false".
        data_segment_id (str, optional): ID of the data segment (if applicable). Defaults to None.
        release_type (str, optional): Type of release associated with the email. Defaults to None.
        template_id (str, optional): ID of the email template. Defaults to None.
        user_id (str, optional): ID of the user who sent the mail. Defaults to None.
        reason (str, optional): Reason for unsubscribing. Defaults to None.
        category (str, optional): Category of the email being unsubscribed from. Defaults to None.
        release_date (str, optional): Date of email release. Defaults to None.

    Returns:
        dict: A message indicating the result of the unsubscribe action.
            - {"message": "Promotional email notification has been updated"} if successful.
            - {"message": "There was some problem updating it. Please try later!"} if unsuccessful.
    """
    email_unsubscribe_status = await unsubscribe().\
        unsubscribe_promotional_email(token, unsubscribe_status, is_raw_data,
                                      data_segment_id, release_type, template_id, user_id, reason, category, release_date)
    await cache_invalidation(api_updated="lead/add_tag/")
    if email_unsubscribe_status:
        if unsubscribe_status is True:
            return {"message": "Promotional email notification has been updated"}
        else:
            return {"message": "There was some problem updating it. Please try later!"}


@email_router.post("/webook/amazon_ses/")
async def capture_email_status_by_amazon_ses(request: Request):
    """
    Webhook for capture email status by amazon ses
    """
    await CommunicationLog().capture_email_status_amazon_ses(request)


@email_router.get("/unsubscribe/reason_list/{token}")
async def get_unsubscribe_reason_list(token: str):
    """
    Retrieve the list of reasons for unsubscribing.

    Args:
        token (str): Authentication token to verify the request.

    Returns:
        JSON response containing the list of unsubscribe reasons.
    """
    credentials_exception = HTTPException(
        detail="Token is not valid", status_code=status.HTTP_401_UNAUTHORIZED
    )
    data = await Authentication().get_token_details(token, credentials_exception)
    college_info = data.get("college_info")
    college_id = college_info[0].get("_id") if college_info else None
    if college_id:
        Reset_the_settings().check_college_mapped(college_id=college_id)
        Reset_the_settings().get_user_database(college_id)
        college = await DatabaseConfiguration().college_collection.find_one({"_id": ObjectId(college_id)})
        if college:
            return {"data": college.get("unsubscribe_reason_list", ["others"]), "message": "Unsubscribe Reason list"}
    return {"data": ["others"], "message": "Unsubscribe Reason List"}

