"""
This file contains API routes related to student timeline
"""
from typing import Union
from bson import ObjectId
from fastapi import APIRouter, Path, Query, Depends, Body
from fastapi.exceptions import HTTPException
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.helpers.admin_dashboard.lead_user import LeadUser
from app.models.applications import DateRange, ActionUser
from app.database.aggregation.student_timeline import StudentTimeline

timeline_router = APIRouter()


@timeline_router.post(
    "/{application_id}/",
    response_description="Get timeline of a student based on application id",
)
async def get_student_timeline(
        application_id: str = Path(..., description="Enter application id"),
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        date_range: DateRange | None = Body(None),
        action_user: list[ActionUser] = Body(None)
):
    """
    Get Timeline of a Student based on application id\n
    * :*param* **application_id** e.g., 6295e143e5a77d170cf91196:\n
    * :*return* **Timeline of student**:
    """
    student, application = await LeadUser().student_application_data(
        application_id)
    record = await DatabaseConfiguration().studentTimeline.find_one(
        {"student_id": ObjectId(student.get("_id"))}
    )
    if not record:
        raise HTTPException(status_code=404, detail="Student timeline not "
                                                    "found.")
    timelines, query_list = await StudentTimeline().get_student_timeline(
        date_range, student.get("_id"), action_user, utility_obj.name_can(
            student.get('basic_details'))
    )
    if timelines:
        if page_num and page_size:
            timelines_length = len(timelines)
            response = await utility_obj.pagination_in_api(
                page_num,
                page_size,
                timelines,
                timelines_length,
                route_name=f"/student_timeline/{application_id}/",
            )
            return {
                "data": response["data"],
                "total": response["total"],
                "count": page_size,
                "pagination": response["pagination"],
                "message": "Get the student timelines.",
            }
        data = {"student_timeline": timelines, "query_timeline": query_list}
        return utility_obj.response_model(data=data,
                                          message="Get the student timelines.")
    return {"data": [], "message": "Student timeline not found."}


@timeline_router.post("/followup_and_notes/{application_id}/")
async def timeline_of_followup_and_notes(
        application_id: str = Path(
            description="Get timeline of followup and notes"),
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        date_range: DateRange | None = Body(None),
        action_user: list[ActionUser] = Body(None)
):
    """
    Get timeline of followup and notes
    """
    student, application = await LeadUser().student_application_data(
        application_id)
    followups, notes = await StudentTimeline().get_followup_notes_timeline(
        date_range, ObjectId(application_id), action_user,
        utility_obj.name_can(student.get("basic_details", {})))
    if page_num and page_size:
        data = followups + notes
        records_length = len(data)
        response = await utility_obj.pagination_in_api(
            page_num,
            page_size,
            data,
            records_length,
            route_name=f"/student_timeline/followup_and_notes/"
                       f"{application_id}/"
        )
        followups, notes = [], []
        for item in response["data"]:
            if item.get("followup"):
                followups.append(item)
            else:
                notes.append(item)
        return {
            "followups": followups,
            "notes": notes,
            "total": response["total"],
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Get followup and notes.",
        }
    return {
        "followups": followups,
        "notes": notes,
        "message": "Get followup and notes.",
    }
