"""
This file contains API routes related to query
"""

from datetime import datetime, timezone
from typing import Optional, Union

from bson import ObjectId
from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError
from pydantic import BaseModel

from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.custom_error import ObjectIdInValid, DataNotFoundError
from app.core.utils import utility_obj, logger, settings, requires_feature_permission
from app.database.aggregation.query import AggregationQuery
from app.database.aggregation.student import Student
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import (
    CurrentUser,
    cache_dependency,
    insert_data_in_cache,
    cache_invalidation, is_testing_env,
)
from app.helpers.student_curd.student_query_configuration import QueryHelper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.query import GetQuery

queries_router = APIRouter()


class message_data(BaseModel):
    reply: Optional[str] = None


@queries_router.post("/list/", summary="Get all queries list")
@requires_feature_permission("read")
async def get_queries_list(
    current_user: CurrentUser,
    page_num: Union[int, None] = Query(None, gt=0),
    page_size: Union[int, None] = Query(None, gt=0),
    query_filter: GetQuery = None,
    cache_data=Depends(cache_dependency),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get list of Queries.

    Params:\n
        - page_num (int | None): Either None or page number where you want
                to show data. e.g., 1
        - page_size (int | none): Either None or page size, useful for show
            data on page_num. e.g., 25.
            If we give page_num=1 and page_size=25 i.e., we want 25
                records on page 1.
        - college_id (str): A unique id/identifier of a college.
                e.g., 123456789012345678901234

    Request body params:\n - query_filter (GetQuery): An object of pydantic
    class `GetQuery` which contains following field: - program_names (list[
    ProgramFilter] | None): Optional field. Either None or a list which
    contains program names. e.g., [{"course_name": "B.Sc.",
    "specialization_name": null}] - date_range (DateRange | None): Either
    None or a data range which useful for get queries based on start date
    and end date. e.g., {"start_date": "2023-12-01", "end_date":
    "2023-12-30"} - search (str | None): Either None or a string which
    useful for get queries based on search string. e.g, "test" - query_type
    (list[QueryType] | None): Either None or a list which contains type of
    queries. e.g., ["Other Query"] - name_sort (bool | None): Either None or
    a boolean value which useful for get queries by student name sorting. -
    email_sort (bool | None): Either None or a boolean value which useful
    for get queries by student email sorting. - created_on_sort (bool |
    None): Either None or a boolean value which useful for get queries by
    created at date sorting. - update_on_sort (bool | None): Either None or
    a boolean value which useful for get queries by updated at date sorting.
    - counselor_ids: (list[str] | None): Either None or a list which
    contains counselor ids, useful for get counselor based queries. e.g.,
    ["123456789012345678901234"] - season (str | None): Either None or a
    string value which useful for get queries from particular season. e.g,
    "test"

    Returns:\n
        - dict: A dictionary which contains information about create key
        category.

    Raises:\n
        - ObjectIdInValid: An error with status code 422 which occurred
            when counselor id will be wrong.
        - Exception: An error with status code 500 which occurred when
            something went wrong in the background code.
    """
    user = await UserHelper().is_valid_user(current_user)
    if not query_filter:
        query_filter = {}
    counselor_id = None
    try:
        cache_key, data = cache_data
        if data:
            return data
        if user.get("role", {}).get("role_name") == "college_counselor":
            counselor_id = [ObjectId(user.get("_id"))]
        elif user.get("role", {}).get("role_name") == "college_head_counselor":
            counselor_detail = await DatabaseConfiguration().user_collection.aggregate(
                [{"$match": {"head_counselor_id": ObjectId(user.get("_id"))}}]
            ).to_list(length=None)
            counselor_id = [
                ObjectId(counselor.get("_id")) for counselor in counselor_detail
            ]
        query_filter = jsonable_encoder(query_filter)
        queries_data, total_queries = await AggregationQuery().get_all_queries(
            query_filter, page_num, page_size, counselor_id
        )
        if queries_data:
            if page_num and page_size:
                response = await utility_obj.pagination_in_aggregation(
                    page_num,
                    page_size,
                    total_queries,
                    route_name="/query/list/",
                )
                all_data = {
                    "data": queries_data,
                    "total": total_queries,
                    "count": page_size,
                    "pagination": response["pagination"],
                    "message": "Get queries list successfully.",
                }
                if cache_key:
                    await insert_data_in_cache(cache_key, all_data)
                return all_data
            all_data = utility_obj.response_model(
                data=queries_data, message="Get queries list successfully."
            )
            if cache_key:
                await insert_data_in_cache(cache_key, all_data)
            return all_data
        all_data = {"data": [], "message": "Queries not found."}
        if cache_key:
            await insert_data_in_cache(cache_key, all_data)
        return all_data
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="An error occurred when get queries. " f"Error - {error}",
        )


@queries_router.post("/reply/", summary="Reply to query")
@requires_feature_permission("write")
async def reply_to_query(
    current_user: CurrentUser,
    message: message_data,
    query_id: str = Query(None, description="Enter query id"),
    ticket_id: str = Query(None, description="Enter ticket id"),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Reply to query\n
    * :*param* **query_id**:\n
    * :*param* **ticket_id**:\n
    * :*param* **message**:\n
    :return:
    """
    student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": current_user.get("user_name")}
    )
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if student:
        details = {
            "user_id": ObjectId(student["_id"]),
            "user_name": utility_obj.name_can(student.get("basic_details", {})),
            "is_replied_by_student": True,
        }
        update_field = "last_accessed"
    elif user:
        if (
            user.get("role", {}).get("role_name", {}) == "super_admin"
            or user.get("role", {}).get("role_name", {}) == "client_manager"
            or user.get("role", {}).get("role_name", {}) == "college_publisher_console"
        ):
            raise HTTPException(status_code=401, detail="Not enough permissions")
        details = {
            "user_id": ObjectId(user["_id"]),
            "user_name": utility_obj.name_can(user),
            "is_replied_by_student": False,
        }
        update_field = "last_user_activity_date"
    else:
        raise HTTPException(
            status_code=404, detail="You have not registered with us. Please register."
        )
    message = jsonable_encoder(message)
    details.update({"message": message.get("reply")})
    details.update({"timestamp": datetime.now(timezone.utc)})
    updated = ""
    if query_id:
        try:
            query = await DatabaseConfiguration().queries.find_one(
                {"_id": ObjectId(query_id)}
            )
        except Exception:
            raise HTTPException(
                status_code=422,
                detail="Query id must be a 12-byte input or "
                "a 24-character hex string.",
            )
        if query:
            details_list = [details]
            if query["replies"] is None:
                updated = await DatabaseConfiguration().queries.update_one(
                    {"_id": ObjectId(query["_id"])}, {"$set": {"replies": details_list}}
                )
            else:
                updated = await DatabaseConfiguration().queries.update_one(
                    {"_id": ObjectId(query["_id"])},
                    {"$set": {"replies": query["replies"] + details_list}},
                )
            category = await DatabaseConfiguration().queryCategories.find_one(
                {"_id": ObjectId(query["category_id"])}
            )
            if student:
                try:
                    student_name = utility_obj.name_can(student.get("basic_details"))
                    toml_data = utility_obj.read_current_toml_file()
                    if toml_data.get("testing", {}).get("test") is False:
                        # TODO: Not able to add student timeline data
                        #  using celery task when environment is
                        #  demo. We'll remove the condition when
                        #  celery work fine.
                        if settings.environment in ["demo"]:
                            StudentActivity().student_timeline(
                                student_id=str(query["student_id"]),
                                event_type="Query",
                                event_status=f"{student_name} has replied on the query - {str(query_id)}.",
                                event_name=f"Category Name: {category['name']}"
                                f" and query_id: {query['_id']}.",
                                college_id=college.get("id"),
                            )
                        else:
                            if not is_testing_env():
                                StudentActivity().student_timeline.delay(
                                    student_id=str(query["student_id"]),
                                    event_type="Query",
                                    event_status=f"{student_name} has replied on the query - {str(query_id)}.",
                                    event_name=f"Category Name: {category['name']}"
                                    f" and query_id: {query['_id']}.",
                                    college_id=college.get("id"),
                                )
                except KombuError as celery_error:
                    logger.error(f"error storing time line data {celery_error}")
                except Exception as error:
                    logger.error(f"error storing time line data {error}")
            else:
                try:
                    toml_data = utility_obj.read_current_toml_file()
                    current_datetime = datetime.now(timezone.utc)
                    student_id = ObjectId(query.get("student_id"))
                    update_info = {update_field: current_datetime}
                    student = await DatabaseConfiguration().studentsPrimaryDetails.find_one({"_id": student_id})
                    if (update_field == "last_user_activity_date" and student and
                            not student.get("first_lead_activity_date")):
                        update_info["first_lead_activity_date"] = current_datetime
                    await DatabaseConfiguration().studentsPrimaryDetails.update_one(
                        {"_id": student_id}, {"$set": update_info})
                    if toml_data.get("testing", {}).get("test") is False:
                        # TODO: Not able to add student timeline data
                        #  using celery task when environment is
                        #  demo. We'll remove the condition when
                        #  celery work fine.
                        if settings.environment in ["demo"]:
                            StudentActivity().student_timeline(
                                student_id=str(query["student_id"]),
                                event_type="Query",
                                event_status="Replied",
                                message=f"Category Name: {category['name']}"
                                f" and query_id: {query['_id']}.",
                                user_id=str(user["_id"]),
                                college_id=college.get("id"),
                            )
                        else:
                            if not is_testing_env():
                                StudentActivity().student_timeline.delay(
                                    student_id=str(query["student_id"]),
                                    event_type="Query",
                                    event_status="Replied",
                                    message=f"Category Name: {category['name']}"
                                    f" and query_id: {query['_id']}.",
                                    user_id=str(user["_id"]),
                                    college_id=college.get("id"),
                                )
                except KombuError as celery_error:
                    logger.error(f"error storing time line data {celery_error}")
                except Exception as error:
                    logger.error(f"error storing time line data {error}")
    elif ticket_id:
        query = await DatabaseConfiguration().queries.find_one({"ticket_id": ticket_id})
        if query:
            details_list = [details]
            if query["replies"] is None:
                updated = await DatabaseConfiguration().queries.update_one(
                    {"_id": ObjectId(query["_id"])}, {"$set": {"replies": details_list}}
                )
            else:
                updated = await DatabaseConfiguration().queries.update_one(
                    {"_id": ObjectId(query["_id"])},
                    {"$set": {"replies": query["replies"] + details_list}},
                )
            category = await DatabaseConfiguration().queryCategories.find_one(
                {"_id": ObjectId(query["category_id"])}
            )
            if student:
                try:
                    toml_data = utility_obj.read_current_toml_file()
                    if toml_data.get("testing", {}).get("test") is False:
                        # TODO: Not able to add student timeline data
                        #  using celery task when environment is
                        #  demo. We'll remove the condition when
                        #  celery work fine.
                        if settings.environment in ["demo"]:
                            StudentActivity().student_timeline(
                                student_id=str(query["student_id"]),
                                event_type="Query",
                                event_status="Replied",
                                message=f"Category Name: {category['name']}"
                                f" and query_id: {query['_id']}.",
                                college_id=college.get("id"),
                            )
                        else:
                            if not is_testing_env():
                                StudentActivity().student_timeline.delay(
                                    student_id=str(query["student_id"]),
                                    event_type="Query",
                                    event_status="Replied",
                                    message=f"Category Name: {category['name']}"
                                    f" and query_id: {query['_id']}.",
                                    college_id=college.get("id"),
                                )
                except KombuError as celery_error:
                    logger.error(f"error storing time line data {celery_error}")
                except Exception as error:
                    logger.error(f"error storing time line data {error}")
            else:
                try:
                    toml_data = utility_obj.read_current_toml_file()
                    if toml_data.get("testing", {}).get("test") is False:
                        # TODO: Not able to add student timeline data
                        #  using celery task when environment is
                        #  demo. We'll remove the condition when
                        #  celery work fine.
                        if settings.environment in ["demo"]:
                            StudentActivity().student_timeline(
                                student_id=str(query["student_id"]),
                                event_type="Query",
                                event_status="Replied",
                                message=f"Category Name: {category['name']}"
                                f" and query_id: {query['_id']}.",
                                user_id=str(user["_id"]),
                                college_id=college.get("id"),
                            )
                        else:
                            if not is_testing_env():
                                StudentActivity().student_timeline.delay(
                                    student_id=str(query["student_id"]),
                                    event_type="Query",
                                    event_status="Replied",
                                    message=f"Category Name: {category['name']}"
                                    f" and query_id: {query['_id']}.",
                                    user_id=str(user["_id"]),
                                    college_id=college.get("id"),
                                )
                except KombuError as celery_error:
                    logger.error(f"error storing time line data {celery_error}")
                except Exception as error:
                    logger.error(f"error storing time line data {error}")
    else:
        raise HTTPException(
            status_code=422, detail="Need to pass query id or ticket id"
        )
    if updated:
        return utility_obj.response_model(
            data=QueryHelper().query_replies(details), message="Reply sent."
        )
    raise HTTPException(status_code=404, detail="Query not found.")


@queries_router.put("/change_status/", summary="Change status of query/ticket")
@requires_feature_permission("edit")
async def change_status_of_query(
    current_user: CurrentUser,
    ticket_id: str = Query(..., description="Enter ticket id"),
    status: str = Query(
        ...,
        description="Enter status which will be any of following:"
        "\n* **TO DO** \n* **IN PROGRESS** \n* **DONE**",
    ),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Change Status of Query/Ticket\n
    * :*param* **status**:\n
    * :*param* **ticket_id**:
    :return:
    """
    status_list = ["TO DO", "IN PROGRESS", "DONE"]
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not user:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    if (
        user.get("role", {}).get("role_name", {}) == "super_admin"
        or user.get("role", {}).get("role_name", {}) == "client_manager"
        or user.get("role", {}).get("role_name", {}) == "college_publisher_console"
    ):
        raise HTTPException(status_code=401, detail="Not enough permissions")
    query = await DatabaseConfiguration().queries.find_one({"ticket_id": ticket_id})
    if query:
        if query.get("status") == status.upper():
            raise HTTPException(
                status_code=422, detail="Unable to update, no changes have been made."
            )
        if status.upper() not in status_list:
            raise HTTPException(
                status_code=422,
                detail="Status should be any of the following: "
                "TO DO, IN PROGRESS and DONE.",
            )
        if status.upper() == "DONE":
            category = await DatabaseConfiguration().queryCategories.find_one(
                {"_id": ObjectId(query["category_id"])}
            )
            try:
                toml_data = utility_obj.read_current_toml_file()
                if toml_data.get("testing", {}).get("test") is False:
                    # TODO: Not able to add student timeline data
                    #  using celery task when environment is
                    #  demo. We'll remove the condition when
                    #  celery work fine.
                    if settings.environment in ["demo"]:
                        StudentActivity().student_timeline(
                            student_id=query["student_id"],
                            event_type="Query",
                            event_status="Resolved",
                            message=f"{utility_obj.name_can(user)} has "
                            f"resolved the query - {ticket_id}",
                            user_id=user["_id"],
                            college_id=college.get("id"),
                        )
                    else:
                        if not is_testing_env():
                            StudentActivity().student_timeline.delay(
                                student_id=query["student_id"],
                                event_type="Query",
                                event_status="Resolved",
                                message=f"{utility_obj.name_can(user)} has "
                                f"resolved the query - {ticket_id}",
                                user_id=user["_id"],
                                college_id=college.get("id"),
                            )
            except KombuError as celery_error:
                logger.error(f"error storing time line data {celery_error}")
            except Exception as error:
                logger.error(f"error storing time line data {error}")
        await DatabaseConfiguration().queries.update_one(
            {"_id": ObjectId(query["_id"])},
            {
                "$set": {
                    "status": status.upper(),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        current_datetime = datetime.now(timezone.utc)
        student_id = ObjectId(query.get("student_id"))
        update_data = {"last_user_activity_date": current_datetime}
        student = await DatabaseConfiguration().studentsPrimaryDetails.find_one({"_id": student_id})
        if student and not student.get("first_lead_activity_date"):
            update_data["first_lead_activity_date"] = current_datetime
        await DatabaseConfiguration().studentsPrimaryDetails.update_one({"_id": student_id}, {"$set": update_data})
        await cache_invalidation(api_updated="query/change_status/")
        return utility_obj.response_model(data=True, message="Query status changed.")
    raise HTTPException(status_code=404, detail="Query not found.")


@queries_router.get(
    "/get/", summary="Get query details based on application id or ticket id"
)
@requires_feature_permission("read")
async def get_query_details(
    current_user: CurrentUser,
    application_id: str = Query(None, description="Enter application id"),
    ticket_id: str = Query(None, description="Enter ticket id"),
    page_num: Union[int, None] = Query(None, gt=0),
    page_size: Union[int, None] = Query(None, gt=0),
    college: dict = Depends(get_college_id_short_version(short_version=True))
):
    """
    Get Query Details based on student id or ticket id.
    """
    if application_id:
        try:
            application = (
                await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"_id": ObjectId(application_id)}
                )
            )
        except Exception:
            raise HTTPException(
                status_code=422,
                detail="Application id must be a 12-byte input or a "
                "24-character hex string.",
            )
        if not application:
            raise HTTPException(
                status_code=404,
                detail=f"Application not found. Enter correct application id.",
            )
        try:
            all_queries = DatabaseConfiguration().queries.aggregate(
                [{"$match": {"student_id": ObjectId(application["student_id"])}}]
            )
        except Exception:
            raise HTTPException(
                status_code=422,
                detail="Student id must be a 12-byte input or a "
                "24-character hex string.",
            )
        total_queries = await DatabaseConfiguration().queries.count_documents({})
        queries_list = [
            QueryHelper().query_helper(item)
            for item in await all_queries.to_list(length=total_queries)
        ]
        queries_list.reverse()
        if queries_list:
            if page_num and page_size:
                query_length = len(queries_list)
                response = await utility_obj.pagination_in_api(
                    page_num,
                    page_size,
                    queries_list,
                    query_length,
                    route_name="/query/get/",
                )
                return {
                    "data": response["data"],
                    "total": response["total"],
                    "count": page_size,
                    "pagination": response["pagination"],
                    "message": "Get all student queries.",
                }
            return utility_obj.response_model(
                data=queries_list, message="Get all student queries."
            )
    elif ticket_id:
        query = await DatabaseConfiguration().queries.find_one({"ticket_id": ticket_id})
        if query:
            return utility_obj.response_model(
                data=QueryHelper().query_helper(query),
                message="Get query details of ticket id.",
            )
    else:
        raise HTTPException(
            status_code=422, detail="Need to pass application id or ticket id."
        )
    raise HTTPException(status_code=404, detail="Query not found.")


@queries_router.put(
    "/assigned_counselor/", summary="Assigned query/ticket to counselor"
)
@requires_feature_permission("write")
async def assigned_query_to_counselor(
    current_user: CurrentUser,
    college_id: str = Query(
        ..., description="College ID \n", example="628dfd41ef796e8f757a5c13"
    ),
    ticket_id: str = Query(..., description="Enter ticket id", example="22-06-19"),
    counselor_id: str = Query(
        None,
        description="Enter counselor id for which you want to "
        "assigned query/ticket:",
        example="62aadac3040d039d95027fa7",
    ),
    counselor_username: str = Query(
        None,
        description="Enter counselor user_name for which you want "
        "to assigned query/ticket:",
        example="apollo@counselor2.com",
    ),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Assigned Query/Ticket to Counselor\n
    * :*param* **ticket_id** e.g., 22-06-19:\n
    * :*param* **counselor_id** e.g., 62aadac3040d039d95027fa7:\n
    * :*param* **counselor_username** e.g., apollo@counselor2.com:\n
    * :*return* ""Message - Query assigned to counselor.**:
    """
    query = await DatabaseConfiguration().queries.find_one({"ticket_id": ticket_id})
    if not query:
        raise HTTPException(status_code=404, detail="Query not found.")
    college = await DatabaseConfiguration().college_collection.find_one(
        {"_id": ObjectId(college_id)}
    )
    if not college:
        raise HTTPException(status_code=404, detail="College not found.")
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not user:
        raise HTTPException(status_code=401, detail="Not enough permissions")
    if (
        user.get("role", {}).get("role_name", {}) == "super_admin"
        or user.get("role", {}).get("role_name", {}) == "client_manager"
        or user.get("role", {}).get("role_name", {}) == "college_publisher_console"
    ):
        raise HTTPException(status_code=401, detail="Not enough permissions")
    if counselor_id:
        try:
            counselor = await DatabaseConfiguration().user_collection.find_one(
                {"_id": ObjectId(counselor_id)}
            )
        except Exception:
            raise HTTPException(
                status_code=422,
                detail="Counselor id must be a 12-byte input or a "
                "24-character hex string.",
            )
    elif counselor_username:
        counselor = await DatabaseConfiguration().user_collection.find_one(
            {"user_name": counselor_username}
        )
    else:
        raise HTTPException(status_code=422, detail="Enter counselor id or user_name.")
    if counselor.get("role", {}).get("role_name", {}) != "college_counselor":
        raise HTTPException(
            status_code=422, detail="You can only assign query/ticket to counselor."
        )
    if user.get("associated_colleges"):
        for i in user.get("associated_colleges"):
            if str(i) == str(college_id):
                if counselor.get("associated_colleges"):
                    for j in counselor.get("associated_colleges"):
                        if str(i) == str(j):
                            if str(query.get("assigned_counselor_id")) == str(
                                counselor["_id"]
                            ):
                                raise HTTPException(
                                    status_code=422,
                                    detail="Unable to update, no "
                                    "changes have been made.",
                                )
                            await DatabaseConfiguration().queries.update_one(
                                {"_id": ObjectId(query["_id"])},
                                {
                                    "$set": {
                                        "assigned_counselor_id": ObjectId(
                                            counselor["_id"]
                                        ),
                                        "assigned_counselor_name": utility_obj.name_can(
                                            counselor
                                        ),
                                        "updated_at": datetime.now(timezone.utc),
                                    }
                                },
                            )
                            utility_obj.update_notification_db(
                                event="Student query",
                                student_id=query.get("student_id"),
                                base_counselor=ObjectId(counselor["_id"]),
                            )
                            category = (
                                await DatabaseConfiguration().queryCategories.find_one(
                                    {"_id": ObjectId(query["category_id"])}
                                )
                            )
                            toml_data = utility_obj.read_current_toml_file()
                            if toml_data.get("testing", {}).get("test") is False:
                                try:
                                    # TODO: Not able to add student timeline data
                                    #  using celery task when environment is
                                    #  demo. We'll remove the condition when
                                    #  celery work fine.
                                    if settings.environment in ["demo"]:
                                        StudentActivity().student_timeline(
                                            student_id=str(query["student_id"]),
                                            event_type="Query",
                                            event_status="Assigned",
                                            event_name=f"Category Name: {category['name']} and query_id: {query['_id']}"
                                            f" to the counselor id: {counselor['_id']},"
                                            f" counselor name: {counselor['first_name'].title()}"
                                            f" {counselor['last_name'].title()}.",
                                            college_id=college.get("id"),
                                        )
                                    else:
                                        if not is_testing_env():
                                            StudentActivity().student_timeline.delay(
                                                student_id=str(query["student_id"]),
                                                event_type="Query",
                                                event_status="Assigned",
                                                event_name=f"Category Name: {category['name']} and query_id: {query['_id']}"
                                                f" to the counselor id: {counselor['_id']},"
                                                f" counselor name: {counselor['first_name'].title()}"
                                                f" {counselor['last_name'].title()}.",
                                                college_id=college.get("id"),
                                            )
                                except KombuError as celery_error:
                                    logger.error(
                                        f"error storing time line data {celery_error}"
                                    )
                                except Exception as error:
                                    logger.error(
                                        f"error storing time line data {error}"
                                    )
                            return utility_obj.response_model(
                                data=True, message="Query assigned to counselor"
                            )
                else:
                    raise HTTPException(
                        status_code=401, detail="Not enough permissions"
                    )
    else:
        raise HTTPException(status_code=401, detail="Not enough permissions")


@queries_router.post(
    "/based_on_program/",
    summary="Get query details based on application id or ticket id",
)
@requires_feature_permission("read")
async def get_query_details(
    current_user: CurrentUser,
    student_id: str = Query(description="Enter student id"),
    course_name: str = Query(description="Enter course name"),
    spec_name: str | None = Query(None, description="Enter specialization name"),
    cache_data=Depends(cache_dependency),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get student queries based on program name.

    Params:
        college_id (str): An unique identifier/id of college. Useful for get
            college data. e.g., 123456789012345678901234
        student_id (str): An unique identifier/id of student.
            Useful for get student queries only. e.g., 123456789012345678901231
        course_name (str): Required field. Name of a course.
                e.g., B.Sc.
        specialization_name (str | None): Optional field.
            Default value: None. Name of a course
            specialization. e.g., Physician Assistant.

    Returns:
        dict: A dictionary which contains PDF downloadable URL along with
        message.
    """
    await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    try:
        data = await Student().get_student_program_wise_queries(
            student_id, course_name, spec_name
        )
        if data:
            data = await QueryHelper().get_student_program_queries_pdf(data)
            if cache_key:
                await insert_data_in_cache(cache_key, data)
            return data
        return {"detail": "Student program-wise queries not found."}
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
