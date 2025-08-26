"""
This file contains API routes/endpoints related to student call logs
"""
from fastapi import APIRouter, Path, Depends

from app.core.utils import utility_obj
from app.database.aggregation.call_log import CallLog
from app.dependencies.college import get_college_id
from app.helpers.admin_dashboard.lead_user import LeadUser

call_log_router = APIRouter()


@call_log_router.get(
    "/{application_id}/", response_description="Get call logs of a student"
)
async def get_call_log(
        application_id: str = Path(..., description="Enter application id"),
        college: dict = Depends(get_college_id)
):
    """
    Get Communication Logs of a Student based on application id\n
    * :*param* **application_id** e.g., 6295e143e5a77d170cf91196:\n
    * :*return* **Call logs of a student**:
    """
    await utility_obj.is_id_length_valid(_id=application_id,
                                         name="Application id")
    student, application = await LeadUser(

    ).student_application_data(application_id)
    (total_outbound_call, total_inbound_call, inbound_call_duration,
     outbound_call_duration, call_timelines) = await CallLog(

    ).get_call_durations_and_timelines(
        student.get("basic_details", {}).get('mobile_number'))
    return utility_obj.response_model(data={
        "outbound_call": total_outbound_call,
        "inbound_call": total_inbound_call,
        "inbound_call_duration": inbound_call_duration,
        "outbound_call_duration": outbound_call_duration,
        "call_timelines": call_timelines if call_timelines else None,
    }, message="Get the call logs.")
