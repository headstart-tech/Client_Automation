"""
This file contains API route/endpoint related to communication log
"""
from fastapi import APIRouter, Path, Depends, Query, Body
from app.core.utils import utility_obj
from app.database.aggregation.communication_timeline import CommunicationLog
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.helpers.admin_dashboard.lead_user import LeadUser
from app.models.applications import DateRange
from app.database.aggregation.call_log import CallLog

communication_router = APIRouter()


@communication_router.post(
    "/{application_id}/", summary="Get communication log data of a student"
)
async def get_communication_log(
        application_id: str = Path(description="Enter application id"),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        email: bool = Query(False, description="Value will be True when want "
                                               "email communication log."),
        sms: bool = Query(False, description="Value will be True when want "
                                             "sms communication log."),
        whatsapp: bool = Query(False,
                               description="Value will be True when want "
                                           "whatsapp communication log."),
        date_range: DateRange = Body(None)
):
    """
    Get Communication Logs of a Student based on application id.

    Params:
        - college_id (str): Required field. A unique id/identifier of
            college. e.g., 6295e143e5a77d170cf91191
        - application_id (str): Required field. A unique id/identifier of
            application. e.g., 6295e143e5a77d170cf91196
        - email (bool): Optional field. Value will be True when want
            email communication log.
        - sms (bool): Optional field. Value will be True when want
            sms communication log.
        - whatsapp (bool): Optional field. Value will be True when want
            whatsapp communication log.

    Request body parameters:
        - date_range (DateRange): Optional field.
            Object of pydantic model/class `DateRange`.
            e.g., {"start_date": "2023-10-19", "end_date": "2023-10-19"}

    Response:
        dict: A dict which contains communication logs details of a student.
    """
    await utility_obj.is_id_length_valid(_id=application_id,
                                         name="Application id")
    student, application = await LeadUser().student_application_data(
        application_id)
    date_range = await utility_obj.format_date_range(date_range)
    start_date, end_date = None, None
    if len(date_range) == 2:
        start_date, end_date = await utility_obj.date_change_format(
            date_range.get("start_date"), date_range.get("end_date")
        )
    if email or sms or whatsapp:
        event_type = "email" if email else "sms" if sms else "whatsapp"
        communication_timeline = await CommunicationLog(). \
            get_communication_timeline(
            student.get('_id'), event_type=event_type,
            start_date=start_date, end_date=end_date)
        if not (start_date and end_date):
            communication_log = await DatabaseConfiguration(). \
                communication_log_collection.find_one(
                {'student_id': student.get('_id')})
            if not communication_log:
                communication_log = {}
            if email:
                email_summary = communication_log.get('email_summary', {})
                if email_summary:
                    email_sent = email_summary.get('email_sent')
                    email_delivered = email_summary.get('email_delivered')
                    email_open_rate = utility_obj.get_percentage_result(
                        email_summary.get('open_rate', 0), email_summary.get(
                            'email_sent', 0))
                    email_click_rate = utility_obj.get_percentage_result(
                        email_summary.get('click_rate', 0),
                        email_summary.get('email_sent', 0))
                    email_delivered_rate = utility_obj.get_percentage_result(
                        email_summary.get('email_delivered', 0),
                        email_summary.get('email_sent', 0))
                else:
                    email_sent = email_delivered = email_open_rate = email_click_rate = \
                        email_delivered_rate = 0
                return {"data": {
                    "sent": email_sent,
                    "delivered": email_delivered,
                    "open_rate": email_open_rate,
                    "click_rate": email_click_rate,
                    "complaint_rate": 0,
                    "bounce_rate": 0,
                    "unsubscribe_rate": 0,
                    "delivered_rate": email_delivered_rate,
                    "communication_timelines": communication_timeline
                }, "message": "Get the email logs."}
            elif sms:
                sms_summary = communication_log.get('sms_summary', {})
                if sms_summary:
                    sms_sent = sms_summary.get('sms_sent', 0)
                    sms_delivered = sms_summary.get('sms_delivered', 0)
                else:
                    sms_sent = sms_delivered = 0
                return {"data": {
                    "sent": sms_sent,
                    "delivered": sms_delivered,
                    "communication_timelines": communication_timeline
                }, "message": "Get the sms logs."}
            else:
                whatsapp_summary = communication_log.get('whatsapp_summary', {})
                if whatsapp_summary:
                    whatsapp_sent = whatsapp_summary.get('whatsapp_sent', 0)
                    whatsapp_delivered = whatsapp_summary.get('whatsapp_delivered',
                                                              0)
                    auto_reply = whatsapp_summary.get('auto_reply', 0)
                    whatsapp_click_rate = utility_obj.get_percentage_result(
                        whatsapp_summary.get('click_rate', 0),
                        whatsapp_summary.get('whatsapp_sent', 0))
                else:
                    whatsapp_sent = whatsapp_delivered = whatsapp_click_rate = auto_reply \
                        = 0
                return {"data":{
                        "sent": whatsapp_sent,
                        "delivered": whatsapp_delivered,
                        "auto_apply": auto_reply,
                        "click_rate": whatsapp_click_rate,
                        "communication_timelines": communication_timeline
                }, "message": "Get the whatsapp logs."}
        else:
            response = await CommunicationLog(). \
                get_timeline_based_on_event(
                student.get('_id'), event_type=event_type,
                start_date=start_date, end_date=end_date)
            response.get("data", {}).update({"communication_timelines": communication_timeline})
            return response
    else:
        total_outbound_call, total_inbound_call, inbound_call_duration, \
            outbound_call_duration, call_timelines = \
            await CallLog().get_call_durations_and_timelines(
                str(student.get("basic_details", {}).get('mobile_number')),
                start_date, end_date)
        return {"data": {
            "outbound_call": total_outbound_call,
            "outbound_call_duration": outbound_call_duration,
            "inbound_call": total_inbound_call,
            "inbound_call_duration": inbound_call_duration,
            "call_timelines": call_timelines if call_timelines else None,
        }, "message": "Get the call logs."}
