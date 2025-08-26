"""
This file contains API routes/endpoints related to data segment
"""

from datetime import datetime
from typing import Union

from bson import ObjectId
from fastapi import APIRouter, Depends, Query, BackgroundTasks, Request, Body
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException

from app.background_task.admin_user import DownloadRequestActivity
from app.background_task.data_segment import DataSegmentActivity
from app.core.custom_error import ObjectIdInValid, DataNotFoundError, \
    CustomError
from app.core.log_config import get_logger
from app.core.utils import utility_obj, requires_feature_permission
from app.database.aggregation.admin_user import AdminUser
from app.database.aggregation.data_segment import DataSegment
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import CurrentUser
from app.helpers.data_segment.configuration import DataSegmentHelper
from app.helpers.data_segment.data_segment_helper import \
    data_segment_automation
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.applications import DateRange
from app.models.data_segment_schema import (
    CreateDataSegment,
    CommunicationType,
    sort_filter,
)
from app.models.student_user_schema import User, payload_data
from app.s3_events.s3_events_configuration import upload_csv_and_get_public_url

logger = get_logger(name=__name__)
data_segment_router = APIRouter()


@data_segment_router.post("/create/", summary="Create data segment")
@requires_feature_permission("write")
async def create_data_segment(
    background_tasks: BackgroundTasks,
    data_segment_create: CreateDataSegment,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    data_segment_id: str = Query(None, description="Enter data segment id"),
):
    """
    Create data segment
    Store data segment details in the collection named dataSegment
    """
    user = await UserHelper().is_valid_user(current_user)

    # Filter out None values from the data_segment_create dictionary
    data_segment_create = {
        key: value
        for key, value in data_segment_create.model_dump().items()
        if value is not None
    }

    # Clean and format the input values
    if data_segment_create.get("period") and isinstance(
        data_segment_create.get("period"), str
    ):
        data_segment_create["period"] = data_segment_create.get("period").title()

    if data_segment_create.get("module_name"):
        data_segment_create["module_name"] = data_segment_create.get(
            "module_name"
        ).title()

    if data_segment_create.get("segment_type"):
        data_segment_create["segment_type"] = data_segment_create.get(
            "segment_type"
        ).title()

    if data_segment_create.get("data_segment_name"):
        data_segment_create["data_segment_name"] = data_segment_create.get(
            "data_segment_name"
        ).title()

    if data_segment_create.get("raw_data_name"):
        data_segment_create["raw_data_name"] = data_segment_create.get("raw_data_name")

    # Update the data_segment_create dictionary with additional information
    data_segment_create.update(
        {
            "updated_by": ObjectId(user.get("_id")),
            "updated_by_name": utility_obj.name_can(user),
            "updated_on": datetime.utcnow(),
        }
    )

    # Convert counselor IDs to ObjectId instances
    if (
        data_segment_create.get("filters", {}).get("counselor_id")
        and len(data_segment_create.get("filters", {}).get("counselor_id")) > 0
    ):
        data_segment_create["filters"]["counselor_id"] = [
            ObjectId(ids)
            for ids in data_segment_create.get("filters", {}).get("counselor_id")
        ]

    # Convert course ID to ObjectId instance
    if data_segment_create.get("filters", {}).get("course", {}).get("course_id"):
        data_segment_create["filters"]["course"]["course_id"] = [
            ObjectId(course_id)
            for course_id in data_segment_create.get("filters", {})
            .get("course", {})
            .get("course_id")
        ]

    # Check if the data segment ID is provided and update the existing
    # data segment
    if data_segment_id:
        await utility_obj.is_id_length_valid(_id=data_segment_id, name="Rule id")
        data_segment = await DatabaseConfiguration().data_segment_collection.find_one(
            {"_id": ObjectId(data_segment_id)}
        )

        if not data_segment:
            return {
                "detail": "Rule not found. Make sure provided template id "
                "should be correct."
            }

        if data_segment_create.get("data_segment_name") != data_segment.get(
            "data_segment_name"
        ):
            if (
                await DatabaseConfiguration().data_segment_collection.find_one(
                    {
                        "data_segment_name": data_segment_create.get(
                            "data_segment_name"
                        ).title()
                    }
                )
                is not None
            ):
                return {"detail": "Data segment name already exists."}

        await DatabaseConfiguration().data_segment_collection.update_one(
            {"_id": data_segment.get("_id")}, {"$set": data_segment_create}
        )
        return {"message": "Data segment details updated."}

    # Check if the data segment name already exists
    if (
        await DatabaseConfiguration().data_segment_collection.find_one(
            {"data_segment_name": data_segment_create.get("data_segment_name").title()}
        )
        is not None
    ):
        return {"detail": "Data segment name already exists."}

    # Validate module_name and data_segment_name
    if data_segment_create.get("module_name") in ["", None]:
        return {"detail": "Module name should be valid."}
    elif data_segment_create.get("data_segment_name") in ["", None]:
        return {"detail": "Data segment name should be valid."}
    elif data_segment_create.get("segment_type") in ["", None]:
        return {"detail": "Segment Type should be valid."}

    # Add additional information to the data_segment_create dictionary
    user_id = ObjectId(user.get("_id"))
    created_by_name = utility_obj.name_can(user)
    created_on = datetime.utcnow()
    data_segment_create.update(
        {
            "created_by_id": user_id,
            "created_by_name": created_by_name,
            "created_on": created_on,
            "period": (
                data_segment_create.get("period")
                if data_segment_create.get("period")
                else "Real Time Data"
            ),
            "data_count": data_segment_create.get("count_at_origin"),
            "shared_with": [
                {
                    "user_id": user_id,
                    "email": user.get("email"),
                    "role": user.get("role", {}).get("role_name"),
                    "name": created_by_name,
                    "permission": "contributor",
                    "created_date": created_on
                }
            ]
        }
    )

    # Insert the data_segment_create dictionary into the
    # data_segment_collection
    created_data_segment = (
        await DatabaseConfiguration().data_segment_collection.insert_one(
            data_segment_create
        )
    )
    data_segment_create["_id"] = created_data_segment.inserted_id
    background_tasks.add_task(
        DataSegmentActivity().store_student_mapped_data,
        data_segment_id=str(data_segment_create.get("_id")),
        college_id=college.get("id"),
    )
    return {
        "data": await DataSegmentHelper().data_segment_helper(
            data_segment_create, college.get("id")
        ),
        "message": "Data segment created.",
    }


@data_segment_router.get("/")
@requires_feature_permission("read")
async def get_all_data_segment_names(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get data segment names
    """
    await UserHelper().is_valid_user(current_user)
    all_data_segment_names = await DataSegment().retrieve_all_data_segment_names()
    return {"data": all_data_segment_names, "message": "Get all campaign rules."}


@data_segment_router.delete("/delete/")
@requires_feature_permission("delete")
async def delete_segment_by_id_or_name(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id),
    data_segment_id: str = Query(None, description="Enter data segment id"),
    data_segment_name: str = Query(None, description="Enter data segment name"),
):
    """
    Delete data segment by id or name
    """
    user = await UserHelper().is_valid_user(current_user)
    if ObjectId(college.get("id")) not in user.get("associated_colleges"):
        raise HTTPException(status_code=401, detail="Not enough permissions")
    data_segment_deleted = await DataSegment().delete_segment_by_id_or_name(
        data_segment_id, data_segment_name, user, college, background_tasks
    )
    if data_segment_deleted:
        return {"message": "Data segment deleted."}
    return {
        "detail": "Data segment not found. Make sure you provided "
        "data_segment_id or data_segment_name is correct."
    }


@data_segment_router.get("/get_by_name_or_id/")
@requires_feature_permission("read")
async def get_segment_details_by_name_or_id(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    data_segment_id: str = Query(None, description="Enter data segment id"),
    data_segment_name: str = Query(None, description="Enter data segment name"),
):
    """
    Get data segment details by id or name
    """
    user = await UserHelper().is_valid_user(current_user)
    if str(college.get("id")) not in user.get("associated_colleges"):
        raise HTTPException(status_code=401, detail="Not enough permissions")
    data_segment = await DataSegment().get_segment_details_by_id_or_name(
        data_segment_id, data_segment_name
    )
    if data_segment:
        return {
            "data": await DataSegmentHelper().data_segment_helper(
                data_segment, college.get("id")
            ),
            "message": "Get data segment details.",
        }
    return {
        "detail": "Data segment not found. Make sure you provided "
        "data_segment_id or data_segment_name is correct."
    }


@data_segment_router.post("s/")
@requires_feature_permission("read")
async def get_segments_details(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    search_string: str = None,
    page_num: int = Query(gt=0),
    page_size: int = Query(gt=0),
    status: str | None = Query(
        None,
        description="Useful for filter data based on status. Status "
        "can be Active or Closed",
    ),
    data_types: list[str] | None = Body(None),
    segment_type: str | None = Body(None),
):
    """
    Get data segment details by id or name with/without filter.

    Params:\n
        - college_id (str): A unique id/identifier of a college.
                e.g., 123456789012345678901234
        - search_string (str | None): Optional field. Default value: None.
            A string which useful for get data segments based on search
            pattern.
        - page_num (int | None): Either None or page number where you want
                to data. e.g., 1
        - page_size (int | none): Either None or page size, useful for show
                data on page_num. e.g., 25.
                If we give page_num=1 and page_size=25 i.e., we want 25
                    records on page 1.
        - status (str | None): Optional field. A string which useful
            for get data segments based on status.

    Request body params:\n
        - data_types (list[str] | None): Optional field. Default value: None.
            A list which contains unique data type which useful for get data
            segments based on types. e,g., ["Lead", "Application"]
        - segment_type (str | None): Optional field. Default value: None.
            Name of the segment type which useful for get data segments based
            on segment type. e.g., "Dynamic"

    Returns:\n
        - dict - A dictionary which contains information about get data
        segments.

    Raises:
        - Exception: An error with status code 500 which occurred when
            something went wrong in the background code.
    """
    user = await UserHelper().is_valid_user(current_user)
    role_name = user.get("role", {}).get("role_name")
    counselor_id = None
    if role_name == "college_counselor":
        counselor_id = [ObjectId(user.get("_id"))]
    if role_name == "college_head_counselor":
        counselor_id = await AdminUser().get_users_ids_by_role_name(
            "college_counselor", college.get("id"), user.get("_id")
        )
    try:
        total_data, data_segments = await DataSegment().get_data_Segment(
            college_id=str(college.get("id")),
            page_num=page_num,
            page_size=page_size,
            status=status.title() if status else None,
            search_string=search_string,
            data_types=data_types,
            segment_type=segment_type,
            counselor_id=counselor_id,
        )
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, total_data, route_name="/data_segments/"
        )
        return {
            "data": data_segments,
            "total": total_data,
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Get data segments.",
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"An error got when get the "
            f"data segment details. Error - {error}",
        )


@data_segment_router.get("s/communication_performance_dashboard/")
@requires_feature_permission("read")
async def get_top_performing_data_segments_details(
    communication_type: CommunicationType,
    current_user: CurrentUser,
    page_num: Union[int, None] = Query(None, gt=0),
    page_size: Union[int, None] = Query(None, gt=0),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get top performing data segments details
    """
    await UserHelper().is_valid_user(current_user)
    return await DataSegment().get_top_performing_data_segment_details(
        communication_type, page_num, page_size
    )


@data_segment_router.post("s/download/")
@requires_feature_permission("download")
async def download_data_segments_details(
    data_segment_ids: list[str],
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Download data segment details by ids.

    Params:\n
        - college_id (str): A unique id/identifier of college.
            e.g., "123456789012345678901234"

    Request body params:\n
        - data_segment_ids (list[str]): A list which contains
            unique ids/identifiers of data segments in a string format.
            e.g., ["123456789012345678901231", "123456789012345678901232"]

    Returns:\n
        dict: A dictionary which contains downloadable url of csv file which
            contains data segments details.

    Raises:\n
        - 422: An exception raised with status code 422 when invalid
            operation happen like by pass invalid college_id/data_segment_id.
        - 404: An exception raised with status code 404 when data not found
            like data segments details not found based on ids.
        - 500: An exception raised with status code 500 when something failed
            in the code.
    """
    user = await UserHelper().is_valid_user(current_user)
    current_datetime = datetime.utcnow()
    try:
        data_segment_ids = [
            ObjectId(_id)
            for _id in data_segment_ids
            if await utility_obj.is_length_valid(_id, "Data segment id")
        ]
        unique_key, data_segments = await DataSegment().get_all_data_segments_detail(
            data_segment_ids=data_segment_ids,
            college_id=college.get("id")
        )
        background_tasks.add_task(
            DownloadRequestActivity().store_download_request_activity,
            request_type="Data Segment",
            requested_at=current_datetime,
            ip_address=utility_obj.get_ip_address(request),
            user=user,
            total_request_data=len(data_segments),
            is_status_completed=True,
            request_completed_at=datetime.utcnow(),
        )
        if data_segments:
            get_url = await upload_csv_and_get_public_url(
                fieldnames=unique_key, data=data_segments,
                name="applications_data"
            )
            return get_url
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as e:
        logger.exception(
            f"An error occurred when download data segments based on ids. "
            f"Error: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when download data "
            f"segments based on ids. Error: {str(e)}",
        )
    raise HTTPException(
        status_code=404, detail="Data segments not found by " "provided ids."
    )


@data_segment_router.get("s/quick_view_info/")
@requires_feature_permission("read")
async def get_quick_view_info(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    status: str | None = None,
):
    """
    Get quick view information of data segments.

    Params:\n
        - college_id (str): A unique id/identifier of college.
            e.g., "123456789012345678901234"
        - status (str): Status of data segments. Useful for get data segments
            quick view information based on data segment status.
            Possible values: ["Active", "Closed"]

    Returns:\n
        dict: A dictionary which contains quick view information of data
            segments.

    Raises:\n
        - 500: An exception raised with status code 500 when something failed
            in the code.
    """
    user = await UserHelper().is_valid_user(current_user)
    role_name = user.get("role", {}).get("role_name")
    counselor_id = None
    if role_name == "college_counselor":
        counselor_id = [ObjectId(user.get("_id"))]
    if role_name == "college_head_counselor":
        counselor_id = await AdminUser().get_users_ids_by_role_name(
            "college_counselor", college.get("id"), user.get("_id")
        )
    try:
        return {
            "data": await DataSegmentHelper().get_quick_view_info(
                status, counselor_id),
            "message": "Get the data segment quick view data.",
        }
    except Exception as e:
        logger.exception(
            f"An error occurred when get the quick view information of data "
            f"segments. Error: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the quick view information "
            f"of data segments. Error: {str(e)}",
        )


@data_segment_router.put("s/change_status/")
@requires_feature_permission("edit")
async def change_status_of_data_segments(
    current_user: CurrentUser,
    data_segments_ids: list[str],
    status: str = Body(
        description="Useful for change data based on status. "
        "Status can be Active or Closed"
    ),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Change status of data segments by ids.

    Params:\n
        - college_id (str): A unique id/identifier of college.
            e.g., "123456789012345678901234"

    Request body params:\n
        - data_segments_ids (list[str]): A list which contains
            unique ids/identifiers of data segments in a string format.
            e.g., ["123456789012345678901231", "123456789012345678901232"]

    Returns:\n
        dict: A dictionary which contains information about change status of
            data segments.

    Raises:\n
        - 422: An exception raised with status code 422 when invalid
            operation happen like by pass invalid college_id/data_segment_id.
        - 404: An exception raised with status code 404 when data not found
            like data segments details not found based on ids.
        - 500: An exception raised with status code 500 when something failed
            in the code.
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        data_segments_ids = [
            ObjectId(_id)
            for _id in data_segments_ids
            if await utility_obj.is_length_valid(_id, "Data segment id")
            and await DatabaseConfiguration().data_segment_collection.find_one(
                {"_id": ObjectId(_id)}
            )
            is not None
        ]
        if data_segments_ids:
            return await DataSegment().change_status_of_data_segments(
                data_segments_ids=data_segments_ids, status=status.title(), user=user
            )
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as e:
        logger.exception(
            f"An error occurred when change status of data segments based "
            f"on ids. Error: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when change status of data segments "
            f"based on ids. Error: {str(e)}",
        )
    raise HTTPException(
        status_code=404, detail="Data segments not found by " "provided ids."
    )


@data_segment_router.put("/header_view/")
@requires_feature_permission("read")
async def get_header_view_data_segment(
    current_user: CurrentUser,
    data_segment_id: str = None,
    token: str = None,
    date_range: DateRange = Body(None),
    college: dict = Depends(get_college_id_short_version(short_version=True))
):
    """
    Get the details of data segment based on data segment id

    params:
        current_user: Get Current user from the token automatically
        data_segment_id (str): Data segment id fetch the data according the id
        token (str): token which is sent my frontend which is needed while sharing
        date_range (dict): Get the date range format yyyy/mm/dd.
        college_id (dict): Get the college id from the user

    return
        response: A dictionary contains a details of one data segment.
    """
    if (
        await DatabaseConfiguration().user_collection.find_one(
            {"user_name": current_user.get("user_name")}
        )
        is None
    ):
        raise HTTPException(status_code=401, detail="Not enough permission")
    if not (data_segment_id or token):
        raise HTTPException(
            status_code=400, detail="data_segment_id or token is required"
        )
    if token:
        data_segment_id = (
            await data_segment_automation().get_data_segment_id_from_token(
                token, current_user
            )
        )
    try:
        return await data_segment_automation().get_segment_header(
            data_segment_id=data_segment_id,
            date_range=date_range,
            college_id=college.get("id"),
        )
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Error fetching{error}")


@data_segment_router.put("/student_mapped")
@requires_feature_permission("read")
async def get_student_mapped_details(
    current_user: CurrentUser,
    data_segment_id: str = None,
    page_num: int = Query(gt=0),
    page_size: int = Query(gt=0),
    payload: payload_data = Body(None),
    basic_filter: bool = None,
    search: str = Query(None),
    is_verify: bool = Body(False),
    token: str = None,
    payment_status: bool = Body(False),
    fresh_lead: bool = Body(False),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get student details which is mapped with data segment

    params:
        current_user (str): Gets the current user from token automatically
        token (str): token which is sent my frontend which is needed while sharing
        college (dict): Gets the college details based on college id

    return:
        response: A list contains the student details
    """
    if payload:
        payload = jsonable_encoder(payload)
    await UserHelper().is_valid_user(current_user)
    if not (data_segment_id or token):
        raise HTTPException(
            status_code=400, detail="data_segment_id or token is required"
        )
    if token:
        data_segment_id = (
            await data_segment_automation().get_data_segment_id_from_token(
                token=token, current_user=current_user
            )
        )
    try:
        return await data_segment_automation().student_mapped_details(
            data_segment_id=data_segment_id,
            is_verify=is_verify,
            payment_status=payment_status,
            fresh_lead=fresh_lead,
            search=search,
            page_num=page_num,
            page_size=page_size,
            payload=payload,
            basic_filter=basic_filter,
            user=current_user,
            college_id=college.get("id"),
        )
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An occur error {error}")


@data_segment_router.post(
    "/count_of_entities/", summary="Get the count of data segment entities."
)
@requires_feature_permission("read")
async def data_segment_entities_count(
    data_segment_info: CreateDataSegment,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get the count of data segment entities.

    Params:\n
        - college_id (str): An unique id/identifier of a college.

    Request body params:\n
        - data_segment_info (CreateDataSegment): An object of pydantic class
                `CreateDataSegment` which contains following field:
                - module_name (str | None): Either None or name of a module.
                    Possible values can be: Lead, Application and Raw Data.
                    Optional field. Default value: None
                - segment_type (str | None): Either None or data segment type.
                    Possible values can be: Static and Dynamic.
                    Optional field. Default value: None
                - data_segment_name (str | None): Either None or name of a
                    data segment. Optional field. Default value: None
                - description (str | None): Either None or description of a
                    data segment. Optional field. Default value: None
                - filters (dict | None): Either None or filter which useful
                    for get particular/filtered data.
                    Optional field. Default value: None
                - advance_filters (dict | None): Either None or advance filter
                    which useful for get particular/filtered data.
                    Optional field. Default value: None
                - raw_data_name (str | None): Either None or useful for get
                    data based on raw data.
                    Optional field. Default value: None
                - period (Union[dict, str] | None): Either None or dictionary
                    which contains start_data and end_date for filter data or
                    string value which represent period.
                    Optional field. Default value: None
                - enabled (bool | None): Either None or a boolean value which
                    represents status (Like Active or De-active) of data
                    segment. Optional field. Default value: None
                - is_published (bool | None): Either none or status
                    (Like draft or published) of data segment.
                    Optional field. Default value: None

    Returns:
        dict: A dictionary which contains information about count of data
            segment entities.
    """
    await UserHelper().is_valid_user(current_user)
    data_segment_info = data_segment_info.model_dump()
    try:
        return await DataSegmentHelper().get_count_of_entities(
            data_segment_info, college.get("id")
        )
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"An error got when get the count of data "
            f"segment entities. Error - {error}",
        )


@data_segment_router.post("/add_data_segment_student")
@requires_feature_permission("write")
async def add_data_segment_students(
    current_user: CurrentUser,
    data_segment_id: str,
    application_id: list[str] = Body(
        description="get the " "application/student id" " of the student"
    ),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Custom assign student to the data segment

    params:
        - current_user: Get the current user email address from the token,
        - college: Dictionary containing the college information
        - data_segment_id: An unique id/identifier of a data segment.
                e.g., 123456789012345678901231
        - application_id: An unique id/identifier of an application
                which useful for add student in the data segment.
                e.g., 123456789012345678901234

    return:
        response: A dictionary which contains information about add student
                in the data segment.

    Raises:
            ObjectIdInValid: An error occurred when
                            data_segment_id/application_id not valid.
            DataNotFoundError: An error occurred when
                        data_segment/application not found using id.
            CustomError: An error occurred when student already exists
                            in the data segment.
            Exception: An error occurred when something happen wrong
                        in the code.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await DataSegmentHelper().custom_student_assign(
            data_segment_id=data_segment_id, application_id=application_id
        )
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=201, detail=error.message)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"An error got when get the - {error}"
        )


@data_segment_router.put("/update_shared_user_permission")
@requires_feature_permission("edit")
async def update_shared_user(
    current_user: CurrentUser,
    data_segment_id: str,
    permission_type: str,
    email_id: str = None,
    user_id: str = None,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Update the data segment shared user permission

    params:
        current_user (str): Get the user_name from the token automatically,
        email_id (str): get email id of user for the change the permissions
        permission_type (str): get the permission_type for giving to the user
                e.q= viewer/contributor
        data_segment_id (str): get the data segment id for
                the fetch data segment details
        user_id (str): get the user id for the change the permissions
        college (dict): get the college details from the college id

    return:
        response: User permission has been updated successfully

    raise:
        notfound: user did not assign any data segment
        not_enough_permission: user not permission to call this API.
        ObjectIdInValid: An error occurred when
                            college_id not valid.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await DataSegmentHelper().get_update_user_shared_permission(
            email_id=email_id,
            user_id=user_id,
            data_segment_id=data_segment_id,
            permission=permission_type,
        )
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"An error got when get the - {error}"
        )


@data_segment_router.get("/dkper/{token}")
@requires_feature_permission("read")
async def get_data_segment_details_link(
    token: str,
    current_user: CurrentUser,
    page_num: int = Query(gt=0),
    page_size: int = Query(gt=0),
):
    """
    Get the details from the shared link from the data segment

    params:
        request (generator): get the details server side of the systems
        token (str): get the token which has details of dg type and segment id
        current_user (str): get the current user from the token,
        page_num (int): get the page number e.q. greater than 0
        page_size (int): Limit the data of the student mapped details
    return:
        response: A list containing the details of the data segment students
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await data_segment_automation().get_decrypted_data(
            token=token, page_num=page_num, page_size=page_size, user=user
        )
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"An error got when get the - {error}"
        )


@data_segment_router.post("/create_share_link_segment")
@requires_feature_permission("write")
async def create_data_segment_link(
    request: Request,
    background_task: BackgroundTasks,
    current_user: CurrentUser,
    data_segment_id: str,
    segment_permission: str,
    user_id: list[str] = Body(),
    message: str = Body(None),
    college: dict = Depends(get_college_id),
):
    """
    Create the link of data segment share segment and send to the user

    params:
        current_user (str): Get the current user from the token automatically
        data_segment_id (str): Get the data segment share segment id,
        college (dict): Get the college details from the college id
        segment_permission (str): Get the segment permissions
            e.q. "contributor", "viewer"
        message (str): Get the message from the user

    return:
        response: Data segment link has been created and sent to the user
    """
    if segment_permission.lower() not in ["contributor", "viewer"]:
        raise HTTPException(
            status_code=404, detail="segment permission not" " available in this system"
        )
    user = await UserHelper().is_valid_user(current_user)
    ip_address = utility_obj.get_ip_address(request)
    try:
        return await data_segment_automation().create_data_segment_link(
            user_id=user_id,
            data_segment_id=data_segment_id,
            segment_permission=segment_permission,
            current_user=current_user,
            college=college,
            ip_address=ip_address,
            message=message,
            background_task=background_task,
            user=user,
        )
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"An error got when get the - {error}"
        )


@data_segment_router.post("/search_for_add_data_segment")
@requires_feature_permission("read")
async def get_search_for_add_data_segment(
    current_user: CurrentUser,
    data_type: str,
    search_string: str = None,
    payload: sort_filter = Body(None),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    client=Depends(utility_obj.get_meili_client),
    page_num: int = Query(gt=0),
    page_size: int = Query(gt=0),
):
    """
    Get the all students details based on given data type

    params:
        - Data_type (str): Get the data type e.q. lead, application and raw data
        - Search_string (str): Get the search string for the searching students
        - college (dict): get the college details from college id
        - page_num (int): Get the integer number, e.q. 1,2,3
        - page_size (int): Get the integer number count of student showing,
                e.q. 1,2,3
        - client (generator): Create a connection with meili search server
        - current_user (str): Get the current user from the token automatically
        - payload (str): payload use for the filtering data based on verified,
                payment_status and lead_stage as boolean type

    returns:
        - A list containing all students details
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await data_segment_automation().get_student_details_for_search(
            data_type=data_type,
            search_string=search_string,
            college_id=str(college.get("id")),
            client=client,
            page_num=page_num,
            page_size=page_size,
            payload=payload,
        )
    except Exception as e:
        logger.error(f"Error - {str(e.args)}")
        raise HTTPException(status_code=500, detail=str(e.args))


@data_segment_router.get("/data_segment_shared_user_details")
@requires_feature_permission("read")
async def get_segment_shared_user_details(
    current_user: CurrentUser,
    data_segment_id: str,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get the user permission details for a segment shared

    params:
        - current_user (str): Get the current user from the token automatically
        - data_segment_id (str): Get the data segment id for user details
        - college (dict): Get the college details from college id

    return:
        - A list containing the shared user details
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await DataSegmentHelper().get_data_segment_shared_user(
            data_segment_id=data_segment_id
        )
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An occur error {error}")


@data_segment_router.get("/remove_data_segment_permission_access")
@requires_feature_permission("delete")
async def remove_data_segment_permission_access(
    current_user: CurrentUser,
    data_segment_id: str,
    user_id: str,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Remove data segment permission access

    Params:
        - current_user (str): Get the current user from the token automatically
        - data_segment_id (str): Unique id of data segment that is to be updated
        - user_id (str): Unique id of user to remove permission
        - college (dict): Get the college details from college id

    Return:
        - Dict: Message that data segment permission is removed

    Raises:
        - DataNotFound Exception: This occurs when data is not found
        - ObjectIdInvalid Exception: This occurs when the object id is invalid
        - Exception: An unexpected error occurred in code
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await DataSegmentHelper().remove_data_segment_permission_access(
            data_segment_id=data_segment_id, user_id=user_id
        )
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An occur error {error}")
