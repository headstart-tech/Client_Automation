"""
This file contains APIs related to Exclusion list in admin profile.
"""
from fastapi import APIRouter, Depends, Body
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException

from app.core.custom_error import ObjectIdInValid, DataNotFoundError
from app.core.log_config import get_logger
from app.core.utils import utility_obj, requires_feature_permission
from app.dependencies.college import get_college_id_short_version
from app.dependencies.oauth import CurrentUser
from app.helpers.admin_dashboard.admin_board import AdminBoardHelper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.applications import SubscribeAction
from app.models.student_user_schema import User
from app.models.user_schema import Exclusionlist

router = APIRouter()
logger = get_logger(name=__name__)


@router.get("/header_details")
@requires_feature_permission("read")
async def get_headers(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True))
):
    """
    API to get Header details
    Params:
        current_user (User): The authenticated user object. This is obtained using dependency injection
                            through `get_current_user`.
        college (dict): College information dictionary fetched using the `get_college_id_short_version`
                       dependency with `short_version=True`.
    Returns (dict): Details of Exclusion list top header
    Raises:
        - User Not Found Error
        - HTTP Exception: When something unexpected happen
    """
    await UserHelper().is_valid_user(user_name=current_user)
    try:
        return {"data": await AdminBoardHelper().get_exclusion_list_headers(),
                "message":  "Return Exclusion list header details"}
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail="Something unexpected happened!"
                            )

@router.post("/list_of_students")
@requires_feature_permission("read")
async def get_list_of_students(
    current_user: CurrentUser,
    list_filter: Exclusionlist = {},
    page_num: int = 1,
    page_size: int = 10,
    searchText: str = None,
    college: dict = Depends(get_college_id_short_version(short_version=True))
):
    """
        Retrieves a paginated list of students based on provided filters and search criteria.

        Params:
            list_filter (Exclusionlist, optional): Dictionary containing filters to exclude specific data. Defaults to {}.
            page_num (int, optional): The page number for pagination. Defaults to 1.
            page_size (int, optional): The number of records per page. Defaults to 10.
            searchText (str, optional): Text to search within student records. Defaults to None.
            current_user (User): The currently authenticated user (retrieved via dependency).
            college (dict): Dictionary containing college-related information,
                            retrieved via dependency `get_college_id_short_version`.

        Returns:
            dict: A dictionary containing the paginated list of students, total count,
                  and any additional metadata if required.

        Raises:
            HTTPException: If authentication fails or an invalid request is made.
    """
    await UserHelper().is_valid_user(user_name=current_user)
    list_filter = jsonable_encoder(list_filter)
    if searchText:
        list_filter["search"] = searchText
    try:
        result, count = await AdminBoardHelper().get_exclusion_students_list(list_filter, page_num, page_size)
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, count,
            route_name="/exclusion_list/list_of_students"
        )
        return {
            "data": result,
            "total": count,
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Students data fetched successfully!",
        }
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail="Something unexpected happened!"
                            )


@router.post("/update_subscribe_status")
@requires_feature_permission("edit")
async def update_subscribe_status(
    current_user: CurrentUser,
    action: SubscribeAction,
    student_id: list[str] = Body(),
    college: dict = Depends(get_college_id_short_version(short_version=True))
):
    """
        Updates the subscription status of a student based on the specified action.

        Params:
            student_id (list): The unique identifier of the student whose subscription status needs to be updated.
            action (SubscribeAction): The action to perform on the student's subscription status.
                                      - "resume": Reactivates the student's subscription.
                                      - "exclude": Marks the student as unsubscribed/excluded.
            current_user (User): The authenticated user making the request (retrieved via dependency).
            college (dict): The college information associated with the student (retrieved via dependency).

        Returns:
            dict: A response indicating the success or failure of the subscription update.

        Raises:
            HTTPException (400): If an invalid action is provided.
            HTTPException (401): If the user is not authenticated.
            HTTPException (404): If the student is not found.
    """
    await UserHelper().is_valid_user(user_name=current_user)
    try:
        action = action.value
        await AdminBoardHelper().update_subscribe_status(student_id, action)
        return {
            "message": "Updated Successfully!"
        }
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
