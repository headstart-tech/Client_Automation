"""
This file contains APIs/Endpoints for get notifications and update notification status
"""
from bson import ObjectId
from fastapi import APIRouter, Path, Query, Depends
from fastapi.exceptions import HTTPException

from app.core.utils import utility_obj, requires_feature_permission
from app.database.aggregation.notification import Notification
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.helpers.user_curd.user_configuration import UserHelper
from app.dependencies.oauth import CurrentUser
from app.core.custom_error import ObjectIdInValid

notification = APIRouter()


@notification.get("/{user_email}/", summary="Get notifications of user by id")
async def get_user_notifications(
        user_email: str = Path(
            ..., description="Enter user email id whose notifications you want"
        ),
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        unread_notification: bool = Query(False,
                                          description="If want to get only unread notification then send value true"),
):
    """
    Get notifications of user by id
    """
    user = await UserHelper().is_valid_user(user_email)
    skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
    total_data, data = await Notification().user_notifications(user, skip, limit, unread_notification)
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total_data, f"/notifications/{user_email}"
    )
    total_unread = await DatabaseConfiguration().notification_collection.count_documents(
        {"send_to": ObjectId(str(user.get("_id"))), "mark_as_read": False}
    )
    return {
        "data": data,
        "total": total_data,
        "count": page_size,
        "pagination": response["pagination"],
        "total_unread": total_unread,
        "message": "Get users notifications.",
    }


@notification.put("/update/", summary="Update notification status by id")
async def get_user_notifications(
        notification_id: str = Query(
            None, description="Enter notification id which status you want to update"
        ),
        mark_as_read: bool = False,
        user_email: str = Query(
            None,
            description="Enter user email id whose notifications status you want to update",
        ), college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Update notification status by id
    """
    if notification_id:
        await utility_obj.is_id_length_valid(str(notification_id), "Notification id")
        notification_details = await DatabaseConfiguration().notification_collection.find_one(
            {"_id": ObjectId(notification_id)}
        )
        await DatabaseConfiguration().notification_collection.update_one(
            {"_id": ObjectId(notification_id)}, {"$set": {"mark_as_read": mark_as_read}}
        )
    elif user_email:
        user = await UserHelper().is_valid_user(user_email)
        notification_details = await DatabaseConfiguration().notification_collection.find_one(
            {"send_to": user.get("_id")}
        )
        await DatabaseConfiguration().notification_collection.update_many(
            {"send_to": ObjectId(user.get("_id"))}, {"$set": {"mark_as_read": mark_as_read}}
        )
    else:
        raise HTTPException(
            status_code=422, detail="Need to pass notification id or user email."
        )
    if not notification_details:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return {"message": "Notification status updated."}


@notification.put("/hide_by_id/",
                  summary="Hide notification by id")
@requires_feature_permission("edit")
async def hide_notification_by_id(
        current_user: CurrentUser,
        notification_id: str = Query(
            description="Enter notification id which want to hide."
        ),
        hide: bool = False,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Update notification hide status by id.

    Params:\n
        - college_id (str): Unique identifier of college which
            useful get college data.
        - notification_id (str): Unique identifier of notification which
            useful for update notification hide status.
        - hide (bool): A boolean value True for hide notification and False
            for un-hide notification.

    Returns:\n
        - dict: A dictionary which contains notification hide status
            information.

    Exceptions:\n
        - 401: An error occurred with status code 401 when user don't have
            permission to change hide status of notification.
        - ObjectIdInValid: An error occurred with status code 422 when
            notification id will be wrong.
        - Exception: An error occurred with status code 500 when
            something wrong happen in the backend code.
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        await utility_obj.is_length_valid(notification_id, "Notification id")
        updated_document = await (DatabaseConfiguration().
                                  notification_collection.
                                  find_one_and_update(
            {'_id': ObjectId(notification_id)},
            {"$set": {"hide": hide}}))
        if updated_document:
            return {"message": f"Notification {'hide' if hide else 'un-hide'} "
                               f"successfully."}
        else:
            return {"message": f"Either no permission to change hide status of"
                               f" notification or notification not found by "
                               f"id: {notification_id}."}
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail="An error occurred when update "
                                    f"notification hide status. Error - "
                                    f"{error}")
