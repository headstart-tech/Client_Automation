"""
This file contains API routes related to student query
"""

import datetime

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, Query, UploadFile
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError

from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.utils import utility_obj, settings, logger, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import CurrentUser, cache_invalidation, is_testing_env
from app.helpers.student_curd.student_query_configuration import QueryHelper
from app.s3_events.s3_events_configuration import upload_multiple_files, validate_file

query_router = APIRouter()


@query_router.post("/create/", summary="Create student query")
@requires_feature_permission("write")
async def create_query(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    title: str = Query(..., description="Enter title"),
    description: str = Query(None, description="Enter description"),
    category_name: str = Query(
        ...,
        description="Enter category name which will be any of "
        "following:\n*"
        "**General Query** \n* **Payment Related "
        "Query** \n* **Application Query** \n* **Other Query**",
    ),
    attachments: list[UploadFile] = [],
    course_name: str = Query(description="Enter course name. e.g., B.Sc."),
    specialization_name: str = Query(
        None, description="Enter specialization name. e.g., " "Physician Assistant"
    ),
    season: str = None,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Create student query\n
    * :*param* **description** e.g., test:\n
    * :*param* **title** e.g., test:\n
    * :*param* **category_name** e.g., Other Query:\n
    * :*return* **Message - Query added.**:
    """
    season_year = utility_obj.get_year_based_on_season(season)
    category_list = [
        "General Query",
        "Payment Related Query",
        "Application Query",
        "Other Query",
    ]
    if category_name.title() not in category_list:
        raise HTTPException(
            status_code=422,
            detail="Category name should be any of the following: General "
            "Query, Payment Related Query, Application Query and "
            "Other Query.",
        )
    if (
        course := await DatabaseConfiguration().course_collection.find_one(
            {"course_name": course_name}
        )
    ) is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    query_details = {
        "title": title,
        "description": description,
        "course_name": course_name,
        "specialization_name": specialization_name,
    }
    app_id = None
    student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if course:
        application = await DatabaseConfiguration().studentApplicationForms.find_one(
            {"student_id": student.get("_id"), "course_id": course.get("_id")}
        )
        if not application:
            application = {}
        app_id = application.get("_id") if application else None
    category = await DatabaseConfiguration().queryCategories.find_one(
        {"name": category_name.title()}
    )
    aws_env = settings.aws_env
    base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
    base_bucket_url = getattr(settings, f"s3_{aws_env}_base_bucket_url")
    if not attachments:
        query_details["attachments"] = None
    else:
        await validate_file(attachments=attachments, college_id=college.get('id'))
        upload_files = await upload_multiple_files(
            files=attachments,
            bucket_name=base_bucket,
            base_url=base_bucket_url,
            path=f"{utility_obj.get_university_name_s3_folder()}/"
            f"{season_year}/{settings.s3_student_documents_bucket_name}/"
            f"{student.get('_id')}/queries/",
        )
        query_details["attachments"] = upload_files

    if category:
        timestamp = datetime.datetime.utcnow()
        date = timestamp.strftime("%y-%m-%d")
        count_queries = await DatabaseConfiguration().queries.count_documents({})
        if await DatabaseConfiguration().queries.find_one({"ticket_id": date}) is None:
            query_details["ticket_id"] = date
        else:
            count = 0
            for query in (
                await DatabaseConfiguration()
                .queries.aggregate([])
                .to_list(length=count_queries)
            ):
                count += 1
            for i in range(1, count):
                if (
                    await DatabaseConfiguration().queries.find_one(
                        {"ticket_id": f"{date}{i}"}
                    )
                    is None
                ):
                    query_details["ticket_id"] = f"{date}{i}"
                    break
        current_datetime = datetime.datetime.utcnow()
        allocate_to_counselor = student.get("allocate_to_counselor", {})
        query_details.update(
            {
                "student_id": ObjectId(str(student["_id"])),
                "student_name": utility_obj.name_can(student.get("basic_details")),
                "student_email_id": student.get("user_name"),
                "category_id": ObjectId(str(category["_id"])),
                "category_name": category["name"],
                "status": "TO DO",
                "created_at": current_datetime,
                "replies": None,
                "assigned_counselor_id": allocate_to_counselor.get("counselor_id"),
                "assigned_counselor_name": allocate_to_counselor.get("counselor_name"),
                "application_id": app_id,
            }
        )
        query_inserted = await DatabaseConfiguration().queries.insert_one(query_details)
        await DatabaseConfiguration().studentsPrimaryDetails.update_one({
            "_id": ObjectId(student.get("_id"))},
            {
                "$set": {"last_accessed": datetime.datetime.utcnow()}
            }
        )
        await utility_obj.update_notification_db(
            event="Student query", student_id=student.get("_id")
        )
        await cache_invalidation(api_updated="student_query/create")
        try:
            toml_data = utility_obj.read_current_toml_file()
            if toml_data.get("testing", {}).get("test") is False:
                query = (
                    f"{query_details.get('student_name')} has raised a "
                    f"query regarding {category_name}"
                )
                # TODO: Not able to add student timeline data
                #  using celery task when environment is
                #  demo. We'll remove the condition when
                #  celery work fine.
                if settings.environment in ["demo"]:
                    StudentActivity().student_timeline(
                        student_id=str(query_details["student_id"]),
                        event_type="Query",
                        event_status=query,
                        event_name=f"Category Name: {category_name}"
                        f" and query_id: "
                        f"{query_inserted.inserted_id}.",
                        college_id=college.get("id"),
                    )
                else:
                    if not is_testing_env():
                        StudentActivity().student_timeline.delay(
                            student_id=str(query_details["student_id"]),
                            event_type="Query",
                            event_status=query,
                            event_name=f"Category Name: {category_name}"
                            f" and query_id: "
                            f"{query_inserted.inserted_id}.",
                            college_id=college.get("id"),
                        )
        except KombuError as celery_error:
            logger.error(f"error storing time line data {celery_error}")
        except Exception as error:
            logger.error(f"error storing time line data {error}")
        return utility_obj.response_model(
            data=QueryHelper().query_helper(query_details), message="Query added."
        )
    else:
        raise HTTPException(
            status_code=422,
            detail="Invalid category name. Categories will be of 4 types: "
            "General Query, Payment Related Query, "
            "Application Query, Other Query",
        )
