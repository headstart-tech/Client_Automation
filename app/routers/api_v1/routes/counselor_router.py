"""
This file contains API routes related to counselor
"""

import datetime
import json
from typing import Union

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Body, Depends, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError

from app.background_task.admin_user import DownloadRequestActivity
from app.background_task.counselor_task import CounselorActivity
from app.background_task.send_mail_configuration import EmailActivity
from app.celery_tasks.celery_send_mail import send_mail_config
from app.core.custom_error import ObjectIdInValid
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings, requires_feature_permission
from app.database.aggregation.admin_user import AdminUser
from app.database.aggregation.college_counselor import Counselor
from app.database.aggregation.email_activity import Email
from app.database.aggregation.followup_notes import FollowupNotes
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import (
    CurrentUser,
    cache_dependency,
    insert_data_in_cache,
    cache_invalidation, is_testing_env, change_indicator_cache, get_redis_client
)
from app.helpers.counselor_deshboard.counselor import CounselorDashboardHelper
from app.helpers.counselor_deshboard.counselor_allocation import \
    manual_allocation
from app.helpers.counselor_deshboard.counselor_help_wrapper import \
    counselor_wrapper
from app.helpers.counselor_deshboard.source import SourceHelper
from app.helpers.sms_activity.sms_configuration import SMSHelper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.applications import DateRange
from app.models.counselor_schema import (
    counselor_mail_schema,
    allocation_to_counselor,
    manual_counselor_allocation,
)
from app.models.followup_notes_schema import list_application
from app.models.lead_schema import counselor_filter, counselor_leave_schema
from app.models.student_user_schema import User, SortType, ChangeIndicator
from app.models.template_schema import EmailType
from app.routers.api_v1.routes.admin_routes import \
    upload_csv_and_get_public_url

logger = get_logger(__name__)

counselor = APIRouter()


async def get_data(
    college_id, current_user, name=None, date_range=None, column_names=None, season=None
):
    """
    Returns the details of counselor based on college id
    """
    all_data = []
    await utility_obj.is_id_length_valid(college_id, name="College id")
    college = await DatabaseConfiguration().college_collection.find_one(
        {"_id": ObjectId(college_id)}
    )
    if not college:
        raise HTTPException(
            status_code=404, detail="College not found. Enter correct college id."
        )
    user = await UserHelper().check_user_has_permission(current_user)
    associated_colleges = [str(i) for i in user.get("associated_colleges")]
    if college_id not in associated_colleges:
        raise HTTPException(
            status_code=401,
            detail="You do not have access to get counselors of the college",
        )
    counselors = await CounselorDashboardHelper().list_counselor(
        current_user, college_id, season=season
    )
    if len(counselors) < 1:
        raise HTTPException(status_code=404, detail="College counselor not found")
    counselor_names = [item.get("name") for item in counselors]
    counselor_ids = [item.get("id") for item in counselors]
    if name:
        if name.title() == "Yesterday":
            date_range = await utility_obj.yesterday()
        elif name.title() == "Week":
            date_range = await utility_obj.week()
    elif date_range:
        date_range = jsonable_encoder(date_range)
        if len(date_range) < 2:
            date_range = await utility_obj.last_30_days(days=28)
        else:
            start_date = datetime.datetime.strptime(
                date_range.get("start_date"), "%Y-%m-%d"
            )
            end_date = datetime.datetime.strptime(
                date_range.get("end_date"), "%Y-%m-%d"
            )
            if start_date <= datetime.datetime.utcnow() <= end_date:
                date_range = await utility_obj.last_30_days(days=28)
            else:
                start_date = end_date - datetime.timedelta(days=28)
                date_range["start_date"] = start_date.strftime("%Y-%m-%d")
                date_range["end_date"] = end_date.strftime("%Y-%m-%d")
    else:
        date_range = await utility_obj.last_30_days(days=28)
    start_date, end_date = await utility_obj.date_change_format(
        date_range.get("start_date"), date_range.get("end_date")
    )
    for _id, name in zip(counselor_ids, counselor_names):
        leads_count = await DatabaseConfiguration(
            season=season
        ).studentsPrimaryDetails.count_documents(
            {
                "college_id": ObjectId(college_id),
                "created_at": {"$gte": start_date, "$lte": end_date},
                "allocate_to_counselor.counselor_id": ObjectId(_id),
            }
        )
        approved_payments_count = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(
            {
                "college_id": ObjectId(college_id),
                "current_stage": {"$gte": 2},
                "payment_info.created_at": {"$gte": start_date, "$lte": end_date},
                "allocate_to_counselor.counselor_id": ObjectId(_id),
                "payment_info.status": "captured",
            }
        )
        submitted_applications_count = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(
            {
                "college_id": ObjectId(college_id),
                "current_stage": {"$gte": 2},
                "enquiry_date": {"$gte": start_date, "$lte": end_date},
                "allocate_to_counselor.counselor_id": ObjectId(_id),
                "declaration": True,
            }
        )
        assigned_queries_count = await DatabaseConfiguration(
            season=season
        ).queries.count_documents(
            {
                "created_at": {"$gte": start_date, "$lte": end_date},
                "assigned_counselor_id": ObjectId(_id),
            }
        )
        data = {
            "counselor_id": _id,
            "counselor_name": name,
            "lead_assigned": leads_count,
            "payment_approved": approved_payments_count,
            "application_submitted": submitted_applications_count,
            "queries": assigned_queries_count,
        }
        if column_names:
            if "Overall Activities" in column_names:
                total_email_sent_by_counselor_count = (
                    await Email().email_sent_by_counselor_count(
                        start_date=start_date, end_date=end_date, counselor_id=_id
                    )
                )
                total_followups_of_counselor_count = (
                    await FollowupNotes().total_followup_count_of_counselor(
                        start_date=start_date, end_date=end_date, counselor_id=_id
                    )
                )
                total_notes_of_counselor_count = (
                    await FollowupNotes().total_notes_count_of_counselor(
                        start_date=start_date, end_date=end_date, counselor_id=_id
                    )
                )
                overall_activities = (
                    total_email_sent_by_counselor_count
                    + total_followups_of_counselor_count
                    + total_notes_of_counselor_count
                )
                data.update({"overall_activities": overall_activities})
            if "Lead Engaged Overall" in column_names:
                lead_engaged_overall = await FollowupNotes().total_engaged_lead_count(
                    start_date=start_date, end_date=end_date, counselor_id=_id
                )
                data.update({"lead_engaged_overall": lead_engaged_overall})
            if "Leads Not Engaged" in column_names:
                leads_not_engaged = await FollowupNotes().total_engaged_lead_count(
                    start_date=start_date,
                    end_date=end_date,
                    counselor_id=_id,
                    not_engaged_leads=True,
                )
                data.update({"leads_not_engaged": leads_not_engaged})
            if "Leads Engagement Percentage" in column_names:
                (
                    total_lead_of_counselor,
                    total_engaged_lead_of_counselor,
                ) = await FollowupNotes().total_engaged_lead_count(
                    start_date=start_date,
                    end_date=end_date,
                    counselor_id=id,
                    leads_engagement_percentage=True,
                )
                percentage_of_leads_engagement = utility_obj.get_percentage_result(
                    dividend=total_engaged_lead_of_counselor,
                    divisor=total_lead_of_counselor,
                )
                data.update(
                    {"percentage_of_leads_engagement": percentage_of_leads_engagement}
                )
            if "Untouched Stage" in column_names:
                untouched_stage_count = (
                    await FollowupNotes().total_untouched_stage_count(
                        start_date=start_date, end_date=end_date, counselor_id=_id
                    )
                )
                data.update({"untouched_stage": untouched_stage_count})
            if "Email Sent" in column_names:
                total_email_sent_by_counselor_count = (
                    await Email().email_sent_by_counselor_count(
                        start_date=start_date, end_date=end_date, counselor_id=_id
                    )
                )
                data.update({"email_sent": total_email_sent_by_counselor_count})
        all_data.append(data)
    return all_data, user


@counselor.post(
    "/manual_counselor",
    summary="allocated manual counselor to student",
)
@requires_feature_permission("write")
async def manual_counselor(
    application_id: str,
    counselor_id: str,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    allocated manual counselor to student, with message 'counselor update successfully'
    """
    await UserHelper().is_valid_user(current_user)
    data = await CounselorDashboardHelper().allocate_counselor(
        application_id, current_user, counselor_id
    )
    return utility_obj.response_model(
        data=data, message="counselor update successfully"
    )


@counselor.get("/college_counselor_list/")
@requires_feature_permission("read")
async def list_of_counselor(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    holiday: bool = False,
):
    """
    Returns the list of counselor
    """
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") == "college_head_counselor":
        result = DatabaseConfiguration().user_collection.aggregate(
            [{"$match": {"role.role_name": "college_counselor",
                         "head_counselor_id": ObjectId(user.get("_id")),
                         "is_activated": True}}])
        data = []
        counselor_obj = CounselorDashboardHelper()
        async for document in result:
            data.append(counselor_obj.college_counselor_serialize(
                document))
        if holiday:
            data = await counselor_obj.filter_counselor(data)
    else:
        data = await CounselorDashboardHelper().list_counselor(
            current_user, ObjectId(college.get("id")), holiday
        )
    return utility_obj.response_model(data=data,
                                      message="data fetch successfully")


@counselor.get("/lead_allocated_counselor/")
@requires_feature_permission("read")
async def lead_allocated_student(
    current_user: CurrentUser,
    page_num: Union[int, None] = Query(None, gt=0),
    page_size: Union[int, None] = Query(None, gt=0),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Returns the list of counselor allocated to lead
    """
    await UserHelper().is_valid_user(current_user)
    data = await CounselorDashboardHelper().list_of_counselor_allocated_to_lead(
        current_user,
        page_num,
        page_size,
        route_name="/counselor/lead_allocated_counselor/",
        college_id=ObjectId(college.get("id")),
    )
    return utility_obj.response_model(data=data, message="data fetch successfully")


@counselor.post("/counselor_wise_lead")
@requires_feature_permission("read")
async def counselor_lead_wise(
    current_user: CurrentUser,
    date_range: DateRange = Body(None),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    return total_lead,
     total_paid and counselor_name
    """
    await UserHelper().is_valid_user(current_user)
    date_range = await utility_obj.format_date_range(date_range)
    data = await CounselorDashboardHelper().counselor_wise_lead(
        current_user.get("user_name"), date_range, ObjectId(college.get("id"))
    )
    return utility_obj.response_model(data=data, message="data fetch successfully")


@counselor.post(
    "/counselor_productivity_report/", summary="Get counselor productivity report"
)
@requires_feature_permission("read")
async def counselor_productivity_report(
    current_user: CurrentUser,
    date_range: DateRange = Body(None),
    season: str = Body(
        None, description="Enter season value if want" " to get data season-wise"
    ),
    name: Union[str, None] = Query(
        None,
        description="Name for get data based on date filter,"
        " it can be any of the following: Yesterday and Week",
    ),
    column_names: list[str] = Query(
        None,
        description="Add columns names, it can be any of the following: "
        "Overall Activities, Lead Engaged Overall, Leads Not Engaged, "
        "Leads Engagement Percentage, Untouched Stage and Email Sent",
    ),
    page_num: int = Query(gt=0),
    page_size: int = Query(gt=0),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get Counselor Productivity Report\n
    * :*param* **date_range** description="Get data based on date_range, pass sub-param start_date and sub-param end_date, date format will be YYYY-MM-DD", example='start_date': '2022-05-24' 'end_date': '2022-05-24' :\n
    * :*param* **name** description="Name for get data based on date filter, it can be any of the following: Yesterday and Week":\n
    * :*param* **column_names** description="Add columns names, it can be any of the following: Overall Activities, Lead Engaged Overall, Leads Not Engaged, Leads Engagement Percentage, Untouched Stage and Email Sent":\n
    * :*return* **Message - Get counselor productivity report.**:
    """
    data, user = await get_data(
        college_id=college.get("id"),
        current_user=current_user,
        name=name,
        date_range=date_range,
        column_names=column_names,
        season=season,
    )
    if data:
        response = await utility_obj.pagination_in_api(
            page_num=page_num,
            page_size=page_size,
            data=data,
            data_length=len(data),
            route_name="/counselor/counselor_productivity_report/",
        )
        return {
            "data": response.get("data"),
            "total": len(data),
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Get counselor productivity report.",
        }
    raise HTTPException(status_code=404, detail="Data not found.")


@counselor.post(
    "/download_counselors_productivity_report/",
    summary="Download counselors productivity report",
)
@requires_feature_permission("download")
async def download_counselor_productivity_report(
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: CurrentUser,
    season: str = Body(
        None, description="Enter season value if want to get " "data season-wise"
    ),
    date_range: DateRange = Body(None),
    name: Union[str, None] = Query(
        None,
        description="Name for get data based on date filter, it can be "
        "any of the following: Yesterday and Week",
    ),
    column_names: list[str] = Query(
        None,
        description="Add columns names, it can be any of the following: "
        "Overall Activities, Lead Engaged Overall, Leads Not "
        "Engaged, Leads Engagement Percentage, Untouched "
        "Stage and Email Sent",
    ),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Download Counselor Productivity Report\n
    * :*param* **date_range** description="Get data based on date_range,
        pass sub-param start_date and sub-param end_date, date format will be
         YYYY-MM-DD", example='start_date': '2022-05-24'
          'end_date': '2022-05-24' :\n
    * :*param* **name** description="Name for get data based on date filter,
        it can be any of the following: Yesterday and Week":\n
    * :*param* **column_names** description="Add columns names, it can be any
        of the following: Overall Activities, Lead Engaged Overall,
            Leads Not Engaged, Leads Engagement Percentage,
             Untouched Stage and Email Sent":\n
    * :*return* **Get public url of csv file which contain counselor
        productivity report**:
    """
    current_datetime = datetime.datetime.utcnow()
    if season == "":
        season = None
    data, user = await get_data(
        college_id=college.get("id"),
        current_user=current_user,
        name=name,
        date_range=date_range,
        column_names=column_names,
        season=season,
    )
    background_tasks.add_task(
        DownloadRequestActivity().store_download_request_activity,
        request_type="Counselors productivity report",
        requested_at=current_datetime,
        ip_address=utility_obj.get_ip_address(request),
        user=user,
        total_request_data=len(data),
        is_status_completed=True,
        request_completed_at=datetime.datetime.utcnow(),
    )
    if data:
        data_keys = list(data[0].keys())
        get_url = await upload_csv_and_get_public_url(
            fieldnames=data_keys, data=data, name="counselors_data"
        )
        return get_url
    raise HTTPException(status_code=404, detail="Data not found.")


@counselor.put("/followup_report/")
@requires_feature_permission("read")
async def followup_report(
    current_user: CurrentUser,
    counselor_filter: counselor_filter = Body(None),
    date_range: DateRange = Body(None),
    page_num: int = Query(gt=0),
    page_size: int = Query(gt=0),
    search: str = None,
    todays_followup: bool = False,
    upcoming_followup: bool = False,
    overdue_followup: bool = False,
    completed_followup: bool = False,
    sort: bool = Body(None),
    sort_name: str = Body(None),
    sort_type: str = Body(None),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    **date_rage get as string**\n
    **counselor_id get as counselor_id str form**\n
    **sort_name should be 'followup_date', 'lead_activity', "created_on", 'status' or "overdue_days"**\n
    **sort_type should be 'asc' or 'dsc'.**\n
    **sort should be true or false.**\n
    **return followup report**\n
    """
    await UserHelper().is_valid_user(current_user)
    data, data_length = await CounselorDashboardHelper().followup_reports(
        current_user,
        date_range,
        counselor_filter,
        todays_followup,
        upcoming_followup,
        overdue_followup,
        completed_followup,
        [ObjectId(college.get("id"))],
        search=search,
        sort=sort,
        sort_name=sort_name,
        sort_type=sort_type
    )
    response = await utility_obj.pagination_in_api(
        page_num, page_size, data, data_length, route_name="/counselor/followup_report/"
    )
    return {
        "data": response.get("data"),
        "total": data_length,
        "count": page_size,
        "pagination": response["pagination"],
        "message": "data fetch successfully",
    }


@counselor.put("/multiple_application_to_one_counselor")
@requires_feature_permission("read")
async def multi_app_to_console(
    *,
    application_id: list_application,
    counselor_id: str,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    **application_id get in list form**
    **counselor_id get as counselor_id str form
    **counselor assign to bulk applications**
    """
    user = await UserHelper().is_valid_user(current_user)
    application_id = jsonable_encoder(application_id)
    application_id = application_id.get("application_id")
    (
        result,
        counselor_data,
    ) = await CounselorDashboardHelper().counselor_allocate_to_multiple(
        application_id, counselor_id, user
    )
    await cache_invalidation(
        api_updated="counselor/multiple_application_to_one_counselor"
    )
    return utility_obj.response_model(data=result, message="data update successfully")


@counselor.post("/send_email_to_multiple_lead/")
@requires_feature_permission("write")
async def send_mail_to_multiple_lead(
    current_user: CurrentUser,
    request: Request,
    payload: counselor_mail_schema,
    template_id: str = None,
    template: str = Body(description="Enter template body"),
    email_type: EmailType = Body(
        "default",
        description="Enter email type, it can be default, "
        "promotional and transactional"),
    data_segment_id: str = None,
    subject: str = Query(description="Enter subject of email"),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    form_initiated: bool = Query(True, description="Get application based on stage"),
):
    """
    Send mail to multiple leads
    params:
     payload (pydantic model),
     template (str) : the template required,
     email_type (str) : type of email required,
     subject(str) : the subject of email which should be sent
     form_initiated (bool)
    """
    user = await UserHelper().is_valid_user(current_user)
    toml_data = utility_obj.read_current_toml_file()
    if toml_data.get("testing", {}).get("test") is False:
        try:
            payload = jsonable_encoder(payload)
            publisher, data_segments = False, {}
            filter_option = payload.get("filter_option")
            if payload.get("interview_list"):
                payload["email_id"] = await SMSHelper().get_email_ids(
                    payload.get("interview_list")
                )
            if payload.get("data_segments_ids"):
                (
                    payload["email_id"],
                    data_segments
                ) = await EmailActivity().update_list_by_data_segments_ids(
                    payload.get("data_segments_ids"),
                    payload["email_id"],
                    data_segments,
                    college.get("id"),
                    emails=True,
                    numbers=False,
                    get_emails=True
                )
                for _id in data_segments:
                    await DatabaseConfiguration(
                    ).data_segment_collection.update_one(
                        {"_id": ObjectId(_id)},
                        {"$inc": {"communication_count.email": len(
                            data_segments.get(_id, []))}})
            if filter_option:
                payload["filter_option"]["college_id"] = college.get("id")
                if user.get("role", {}).get("role_name") == "college_counselor":
                    payload["filter_option"]["counselor_id"] = [str(user.get("_id"))]
                elif (
                    user.get("role", {}).get("role_name") == "college_publisher_console"
                ):
                    publisher = True
                date_range = {}
                if filter_option.get("date_range"):
                    date_range = {
                        k: v
                        for k, v in filter_option.get("date_range", {}).items()
                        if v is not None
                    }
                payload["email_id"] = await CounselorDashboardHelper().get_email_ids(
                    payload=filter_option,
                    date_range=date_range,
                    publisher=publisher,
                    user=user,
                    form_initiated=form_initiated,
                )
            final_emails = []
            for email_id in payload["email_id"]:
                extra_emails = await EmailActivity().add_default_set_mails(email_id)
                final_emails.extend(extra_emails)
            payload["email_id"] = final_emails
            if data_segment_id is not None:
                if not ObjectId.is_valid(data_segment_id):
                    raise ValueError("Invalid data segment ObjectId")
                if (
                await DatabaseConfiguration().data_segment_collection.find_one(
                        {
                            "_id": ObjectId(data_segment_id)}
                )) is not None:
                    await DatabaseConfiguration(
                    ).data_segment_collection.update_one(
                        {"_id": ObjectId(data_segment_id)},
                        {"$inc": {"communication_count.email": len(
                            payload.get("email_id", []))}})
            ip_address = utility_obj.get_ip_address(request)
            action_type = (
                "counselor"
                if user.get("role", {}).get("role_name", "") == "college_counselor"
                else "system"
            )
            await send_mail_config().counselor_send_bulk_email(
                payload=payload,
                template=template,
                template_id=template_id,
                email_type=email_type.lower(),
                subject=subject,
                event_type="email",
                event_status=f"sent by {utility_obj.name_can(user)} whose id: {str(user.get('_id'))}",
                event_name="Bulk",
                email_activity_payload={
                    "content": "send templates",
                    "email_list": payload.get("email_id", []),
                },
                current_user=current_user,
                ip_address=ip_address,
                email_preferences=college.get("email_preferences", {}),
                action_type=action_type,
                college_id=college.get("id"),
                data_segments=data_segments,
            )
        except ObjectIdInValid as error:
            raise HTTPException(status_code=422, detail=error.message)
        except KombuError as celery_error:
            logger.error(f"error send bulk mail to student {celery_error}")
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred when send bulk mail to students. "
                f"Error - {celery_error}",
            )
        except Exception as error:
            logger.error(f"error send bulk mail to student {error}")
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred when send bulk "
                f"mail to students. Error - {error}",
            )
    return {"data": True, "message": "email sent"}


@counselor.put("/counselor_wise_lead_stage")
@requires_feature_permission("read")
async def counselor_wise_lead_stage(
    current_user: CurrentUser,
    date_range: DateRange = None,
    season: str = Body(
        None, description="Enter season value if want to get data season-wise"
    ),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    lead_stage shown by counselor name
    Can be filtered by date range according this format 2022-07-25
    """
    if season == "":
        season = None
    await UserHelper().is_valid_user(current_user)
    date_range = await utility_obj.format_date_range(date_range)
    data = await CounselorDashboardHelper().counselor_wise_data(
        date_range, college.get("id"), season=season
    )
    return utility_obj.response_model(data=data, message="data fetched successfully")


@counselor.put("/counsellor_performance_report")
@requires_feature_permission("read")
async def counsellor_performance_reports(
    current_user: CurrentUser,
    date_range: DateRange = Body(None),
    cache_data=Depends(cache_dependency),
    cache_change_indicator=Depends(change_indicator_cache),
    change_indicator: ChangeIndicator = None,
    season: str = Body(
        None, description="Enter season value if want" " to get data season-wise"
    ),
    counselor_Id: list = Body(None),
    mode: str | None = Body(None),
    sort: str = None,
    sort_type: str = Query(None, description="Sort_type can be 'asc' or 'dsc'"),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get counselor performance report
    Params:
      counselor_search (str):  The counselor name which is searched for
      sort (str): The column which is to be sorted
      sort_type (str): Can have values asc,dsc
      college_id: Unique id of college
      date_range: Filter used.
      Change_indicator: This can have values last_7_days/last_15_days/last_30_days
    """
    if season == "":
        season = None
    user = await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    date_range = await utility_obj.format_date_range(date_range)
    if user.get("role", {}).get("role_name") == "college_counselor":
        counselor_Id = [ObjectId(user.get("_id"))]
    elif user.get("role", {}).get("role_name") == "college_head_counselor":
        counselors = await DatabaseConfiguration().user_collection.aggregate(
            [{"$match": {"head_counselor_id": ObjectId(user.get("_id"))}}]
        ).to_list(length=None)
        counselor_Id = [ObjectId(temp.get("_id")) for temp in counselors]
    headers, data, total_data = await CounselorDashboardHelper().counselor_performance(
        date_range,
        college.get("id"),
        change_indicator,
        season=season,
        counselor_ids=counselor_Id,
        mode=mode
    )
    if sort:
        data = (
            sorted(data, key=lambda x: x[sort], reverse=True)
            if sort_type == "dsc"
            else sorted(data, key=lambda x: x[sort])
        )
    data = {"headers": headers, "data": data, "total": total_data, "message": "data fetched successfully"}
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@counselor.put("/download_counselor_performance_report")
@requires_feature_permission("download")
async def download_counselor_performance_data(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    request: Request,
    season: str = Body(
        None, description="Enter season value if want to get data season-wise"
    ),
    date_range: DateRange = Body(None),
    counselor_Id: list = Body(None),
    mode: str | None = Body(None),
    change_indicator: ChangeIndicator = None,
    counselor_search: str = None,
    sort: str = None,
    sort_type: str = Query(None, description="Sort_type can be 'asc' or 'dsc'"),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Downloads the counselor performance report in form of csv file
    college_id: str
    date range format:- 2022-05-24
    """
    user = await UserHelper().is_valid_user(user_name=current_user)
    current_datetime = datetime.datetime.utcnow()
    date_range = await utility_obj.format_date_range(date_range)
    if user.get("role", {}).get("role_name") == "college_counselor":
        counselor_Id = [ObjectId(user.get("_id"))]
    elif user.get("role", {}).get("role_name") == "college_head_counselor":
        counselors = await DatabaseConfiguration().user_collection.aggregate(
            [{"$match": {"head_counselor_id": ObjectId(user.get("_id"))}}]
        ).to_list(length=None)
        counselor_Id = [ObjectId(temp.get("_id")) for temp in counselors]
    headers, data, total_data = await CounselorDashboardHelper().counselor_performance(
        date_range,
        college.get("id"),
        change_indicator,
        season=season,
        counselor_ids=counselor_Id,
        mode=mode
    )
    if sort:
        data = (
            sorted(data, key=lambda x: x[sort], reverse=True)
            if sort_type == "dsc"
            else sorted(data, key=lambda x: x[sort])
        )
    data_keys = list(data[0].keys())
    get_url = await upload_csv_and_get_public_url(
        fieldnames=data_keys, data=data, name="counselors_data"
    )
    background_tasks.add_task(
        DownloadRequestActivity().store_download_request_activity,
        request_type="Counselor performance report",
        requested_at=current_datetime,
        ip_address=utility_obj.get_ip_address(request),
        user=await UserHelper().check_user_has_permission(user_name=current_user),
        total_request_data=1,
        is_status_completed=True,
        request_completed_at=datetime.datetime.utcnow(),
    )
    return get_url


@counselor.post("/leave_college_counselor")
@requires_feature_permission("read")
async def leave_college_counselors(
    background_tasks: BackgroundTasks,
    counselor_leave: counselor_leave_schema,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    leave of counselor store in database according to date and name
    remove previous date from counselor management database"""
    await UserHelper().is_valid_user(current_user)
    counselor_leave = jsonable_encoder(counselor_leave)
    (
        data,
        counselor_id,
        counselor_data,
    ) = await CounselorDashboardHelper().leave_counselor(
        counselor_leave, [ObjectId(college.get("id"))]
    )
    toml_data = utility_obj.read_current_toml_file()
    if toml_data.get("testing", {}).get("test") is False:
        background_tasks.add_task(
            CounselorActivity().remove_pre_leave_counselor, counselor_id=counselor_id
        )
    return utility_obj.response_model(data=data, message="data inserted successfully")


@counselor.get("/source_lead_performing")
@requires_feature_permission("read")
async def source_performance_reports(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    get source performance reports"""
    await UserHelper().is_valid_user(current_user)
    data = await SourceHelper().source_lead_performing()
    return utility_obj.response_model(data=data, message="data fetched successfully")


@counselor.post("/change_status")
@requires_feature_permission("edit")
async def counselor_status(
    counselor_id: str,
    status: bool,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    change counselor is_activated is true or false/n
    counselor_id: id/n
    status: True/False
    """
    await UserHelper().is_valid_user(current_user)
    data, counselor_data = await CounselorDashboardHelper().change_counselor_behave(
        counselor_id=counselor_id,
        status=status,
        college_id=[ObjectId(college.get("id"))],
    )
    return utility_obj.response_model(data=data, message="status update successfully")


@counselor.post("/assign_course")
@requires_feature_permission("write")
async def add_course_tag(
    background_tasks: BackgroundTasks,
    counselor_id: str,
    payload: allocation_to_counselor,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Add course_tag to college counselor

    params:
            - state_code (list): get the list of state code to allocate to
                counselor
            - source_name (list): Get the list of source data allocate to the
                counselor
            - counselor_id (str): Get the counselor id of the counselor
            - state_name (list): get the state name of the state allocate to
                the counselor
            - fresh_lead_limit (int): Get the fresh lead limit assign
                to counselor
            - langauge (list): Get the list of language name
            - college (dict): get the college details from college id
            - current_user (str): get the current user from the token
                automatically
    return:
        - counselor assign successfully
    """
    payload = jsonable_encoder(payload)
    if (
        user := await DatabaseConfiguration().user_collection.find_one(
            {"user_name": current_user.get("user_name")}
        )
    ) is None:
        raise HTTPException(status_code=401, detail="Not enough permissions")
    if user.get("role", {}).get("role_name") in [
        "super_admin",
        "client_manager",
        "college_counselor",
        "college_publisher_console",
    ]:
        raise HTTPException(status_code=401, detail="Not enough permissions")
    state_name = []
    for state_code in payload.get("state_code", []):
        if (
            state := await DatabaseConfiguration().state_collection.find_one(
                {"country_code": "IN", "state_code": state_code.upper()}
            )
        ) is not None:
            state_name.append(state.get("name"))
        else:
            raise HTTPException(status_code=404, detail="State not found")
    data, counselor_data = await SourceHelper().course_assign_counselor(
        counselor_id=counselor_id,
        course_name=payload.get("course_name"),
        college_id=[ObjectId(college.get("id"))],
    )
    background_tasks.add_task(
        CounselorActivity().remove_assign_course,
        course_name=payload.get("course_name"),
        counselor_id=counselor_id,
        college_id=[ObjectId(college.get("id"))],
    )
    await CounselorActivity().allocate_details_to_counselor(
        state_code=payload.get("state_code", []),
        source_name=payload.get("source_name", []),
        fresh_lead_limit=payload.get("fresh_lead_limit"),
        counselor_id=counselor_id,
        state_name=state_name,
        language=payload.get("language"),
        specialization=payload.get("specialization_name"),
    )
    return utility_obj.response_model(
        data=data, message="counselor assign successfully"
    )


@counselor.get("/absent")
@requires_feature_permission("read")
async def get_absent_counselor(
    counselor_id: str,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    This function returns the detail of absent counselor
    """
    await UserHelper().check_user_has_permission(current_user)
    await utility_obj.is_id_length_valid(counselor_id, "counselor_id")
    if (
        counselor_data := await DatabaseConfiguration().user_collection.find_one(
            {"_id": ObjectId(counselor_id)}
        )
    ) is None:
        raise HTTPException(status_code=404, detail="Counselor not found")
    if (
        counselor_leave_data := await DatabaseConfiguration().counselor_management.find_one(
            {"counselor_id": ObjectId(counselor_id)}
        )
    ) is None:
        counselor_leave_data = {}
    counselor_name = utility_obj.name_can(counselor_data)
    return {
        "data": {
            "counselor_name": counselor_name,
            "leave_dates": counselor_leave_data.get("no_allocation_date", []),
            "last_update": (
                utility_obj.get_local_time(counselor_leave_data.get("last_update"))
                if len(counselor_leave_data) > 0
                else None
            ),
        },
        "message": "data fetch successfully",
    }


@counselor.post("/all_counselor_list")
@requires_feature_permission("read")
async def college_counselors_list(
    current_user: CurrentUser,
    page_num: int = Query(..., gt=0),
    page_size: int = Query(..., gt=0),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    search_string: str = None,
    source: list = Body(None),
    state: list = Body(None),
):
    """
    This function returns the list of college_counselor with their
    id, counselor_name, email, allocate_courses
    """
    await UserHelper().check_user_has_permission(current_user)
    skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
    data, total = await Counselor().get_college_counselors(
        skip,
        limit,
        [ObjectId(college.get("id"))],
        source,
        state,
        search_string=search_string,
    )
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total, route_name="/counselor/all_counselor_list"
    )
    return {
        "data": data,
        "total": total,
        "count": page_size,
        "pagination": response["pagination"],
        "message": "data fetch successfully",
    }


@counselor.get("/get_head_counselors_list/")
@requires_feature_permission("read")
async def college_head_counselors_list(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    This function returns the list of college_head_counselors
    """
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") not in [
        "college_super_admin",
        "college_admin",
    ]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    data = await Counselor().get_college_head_counselors(ObjectId(college.get("id")))
    return {"data": data, "message": "Get head counselors list."}


@counselor.put("/map_with_head_counselor/")
@requires_feature_permission("read")
async def counselor_map_with_head_counselor(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    counselor_id: str,
    head_counselor_id: str = Query(
        None,
        description="Enter head_counselor ID \n* e.g.," "**624e8d6a92cc415f1f578a24**",
    ),
    head_counselor_email_id: str = Query(
        None, description="Enter head_counselor email id \n* e.g., **test@example.com**"
    ),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    This function returns the list of college_head_counselors
    """

    user = await UserHelper().is_valid_user(current_user)
    if (
        user.get("role", {}).get("role_name")
        not in ["college_super_admin", "college_admin"]
    ) or (college.get("id") not in [str(i) for i in user.get("associated_colleges")]):
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    data = await Counselor().map_head_counselor_to_counselor(
        head_counselor_id,
        head_counselor_email_id,
        counselor_id,
        user,
        college,
        background_tasks,
    )
    return data


@counselor.put("/manual_counselor_assign")
@requires_feature_permission("write")
async def manual_counselor_assign(
    payload: manual_counselor_allocation, current_user: CurrentUser
):
    """
    counselor manually assign to the lead
    params:
        offline_line_id: The id of the offline line identifier
        counselor_id: the id of the counselor id
        current_user: The current user that owns the assignment

    return:
        response: successfully assign to the counselor
    """
    if (
        await DatabaseConfiguration().user_collection({"user_name": current_user.get("user_name")})
        is None
    ):
        raise HTTPException(status_code=404, detail="permission denied")
    payload = jsonable_encoder(payload)
    await utility_obj.is_length_valid(str(payload.get("counselor_id")), "counselor_id")
    for offline_id in payload.get("offline_line_id"):
        await utility_obj.is_length_valid(str(offline_id), "offline_id")
    try:
        if not is_testing_env():
            manual_allocation().counselor_allocation_helper.delay(
                offline_data_id=payload.get("offline_data_id"),
                counselor_id=payload.get("counselor_id"),
            )
    except KombuError as celery_error:
        logger.error(f"error assign to the counselor raw data {celery_error}")
    except Exception as error:
        logger.error(f"error assign to the counselor raw data {error}")
    return {"message": "counselor successfully assigned"}


@counselor.put("/counselor_performance")
@requires_feature_permission("read")
async def get_counselor_performance(
    current_user: CurrentUser,
    counselor_id: list | None = Body(None),
    date_range: DateRange | None = Body(None),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get the counselor wise performance report data.

    Params:\n
        - counselor_id (list): A list which contains unique counselor
                identifiers which useful for get performance report of
                counselors.
        - college_id (dict): An unique identifier of a college which useful
            for get college data.

    Returns:\n
        - dict: A dictionary which contains counselor performance data.

    Raises:\n
        - Exception: An error occurred when status code 500 when something went
            wrong happen in the backend code.
    """
    user = await UserHelper().check_user_has_permission(
        current_user, ["college_counselor", "college_head_counselor"], False
    )
    role_name = user.get("role", {}).get("role_name")
    if role_name == "college_counselor":
        counselor_id = [ObjectId(user.get("_id"))]
    elif role_name == "college_head_counselor":
        counselor_id = await AdminUser().get_users_ids_by_role_name(
            "college_counselor", college.get("id"), user.get("_id")
        )
    try:
        return await counselor_wrapper().counselor_performance_helper(
            counselor_id=counselor_id,
            date_range=date_range,
            college_id=college.get("id"),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="An error occurred when get counselor "
            f"performance data. Error - {error}",
        )


@counselor.put("/counselor_performance_download")
@requires_feature_permission("download")
async def get_counselor_performance(
    current_user: CurrentUser,
    counselor_id: list | None = Body(None),
    date_range: DateRange | None = Body(None),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Download the counselor wise performance report data.

    Params:\n
        - counselor_id (list): A list which contains unique counselor
                identifiers which useful for get performance report of
                counselors.
        - college_id (dict): An unique identifier of a college which useful
            for get college data.

    Returns:\n
        - dict: A dictionary which contains counselor performance report
         download URL with message.

     Raises:\n
        - Exception: An error occurred when status code 500 when something went
            wrong happen in the backend code.
    """
    user = await UserHelper().check_user_has_permission(
        current_user, ["college_counselor", "college_head_counselor"], False
    )
    role_name = user.get("role", {}).get("role_name")
    if role_name == "college_counselor":
        counselor_id = [ObjectId(user.get("_id"))]
    elif role_name == "college_head_counselor":
        counselor_id = await AdminUser().get_users_ids_by_role_name(
            "college_counselor", college.get("id"), user.get("_id")
        )
    try:
        data = await counselor_wrapper().counselor_performance_helper(
            counselor_id=counselor_id,
            date_range=date_range,
            college_id=college.get("id"),
        )
        if data:
            data_keys = list(data.keys())
            get_url = await upload_csv_and_get_public_url(
                fieldnames=data_keys, data=data, name="counselors_performance_report"
            )
            return get_url
    except Exception as error:
        raise HTTPException(status_code=500, detail=error)


@counselor.get("/get_calendar_info/")
@requires_feature_permission("read")
async def get_calendar_info(
    current_user: CurrentUser,
    college_id: dict = Depends(get_college_id_short_version(short_version=True)),
    date: int = Query(
        description="Enter date in DD format ie, an integer value eg:12", ge=1, le=31
    ),
    month: int = Query(
        description="Enter month in MM format ie, an integer value eg:12", ge=1, le=12
    ),
    year: int = Query(
        description="Enter year in YYYY format ie, an integer value " "eg:2023",
        ge=1990,
        lt=10000,
    ),
):
    """
    This function returns the day wise calendar data
    """
    user = await UserHelper().is_valid_user(current_user)
    role = user.get("role", {}).get("role_name")
    if role not in ["college_counselor", "college_head_counselor"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    try:
        datetime.datetime(year, month, date)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"InCorrect date")

    if role == "college_counselor":
        users = [ObjectId(user.get("_id"))]

    else:
        users = await AdminUser().get_users_ids_by_role_name(
            "college_counselor", college_id.get("id"), user.get("_id")
        )

    data = await CounselorDashboardHelper().get_calendar_info(
        date=date, month=month, year=year, users=users
    )
    return {"data": data, "message": "Get Calender Info"}


@counselor.get("/key_indicators/")
@requires_feature_permission("read")
async def get_key_indicators(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    lcr_type: str | None = "Not picked",
    change_indicator: ChangeIndicator | None = None,
):
    """
    Get key indicator section information by counselor id (s).

    Params:\n
      - college_id(str): Unique identifier of college which useful for get
        college data.
      - lcr_type (str): Type of lead stage. Possible values are "Interested",
        "Not Interested", "Not picked", "Number Switched Off", "Not Reachable".
      - change_indicator (ChangeIndicator): An object of class
            `ChangeIndicator` which useful for show percentage comparison.
            Default showing "last_7_days" comparison of data.
            Possible values: last_7_days, last_15_days and last_30_days.

    Returns:\n
        - dict: A dictionary which contains key indicator section information
            for counselor.
    """
    user = await UserHelper().is_valid_user(current_user)
    user_role = user.get("role", {}).get("role_name")
    if user_role not in ["college_head_counselor", "college_counselor"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    try:
        user_id = user.get("_id")
        if user_role == "college_head_counselor":
            counselor_ids = await AdminUser().get_users_ids_by_role_name(
                "college_counselor", college.get("id"), user_id
            )
        else:
            counselor_ids = [ObjectId(user_id)]
        return {
            "data": await CounselorDashboardHelper().get_key_indicators_for_counselor(
                counselor_ids=counselor_ids,
                change_indicator=change_indicator,
                lcr_type=lcr_type,
            ),
            "message": "Get key indicators",
        }
    except Exception as error:
        logger.error(
            f"An error got when get key indicators data in counselor "
            f"dashboard. Error - {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"An error got when get key indicators "
            f"data in counselor dashboard. "
            f"Error - {error}",
        )


@counselor.post("/quick_view/")
@requires_feature_permission("read")
async def quick_view_details(
    current_user: CurrentUser,
    college_id: dict = Depends(get_college_id_short_version(short_version=True)),
    date_range: DateRange = Body(None),
    season: str = Body(None),
    change_indicator: ChangeIndicator = None,
):
    """Returns the data of Admission status based on route 'score_board' and college_id and date_range
    college_id: str Unique college id
    date range format:- 2022-05-24
    Change indicator
    """
    user = await UserHelper().is_valid_user(current_user)
    counselor_id = [ObjectId(user.get("_id"))]
    counselor_role = user.get("role", {}).get("role_name")
    if counselor_role not in ["college_head_counselor", "college_counselor"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    date_range = await utility_obj.format_date_range(date_range)
    try:
        if counselor_role == "college_head_counselor":
            cursor = DatabaseConfiguration().user_collection.aggregate(
                [{"$match": {"head_counselor_id": {"$in": counselor_id}}}]
            )
            counselor_id = [doc["_id"] async for doc in cursor]
        data = await CounselorDashboardHelper().get_quick_view_for_counselor(
            college_id=college_id.get("id"),
            counselor_id=counselor_id,
            change_indicator=change_indicator,
            date_range=date_range,
        )
        return {"data": data, "message": "Get the counselor quick view data."}
    except Exception as error:
        logger.error(
            f"An error got when get quick view data in counselor "
            f"dashboard. Error - {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"An error got when get quick view data in counselor dashaboard. "
            f"Error - {error}",
        )


@counselor.post(
    "/followup_details_summary/", summary="Get the followup details summary."
)
@requires_feature_permission("read")
async def get_followup_details(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    change_indicator: ChangeIndicator = None,
    date_range: DateRange | None = Body(None),
):
    """
    Get follow-up details summary information.

    Params:
        college_id (str): A unique identifier/id of a college.
            e.g., "123456789012345678901234"
        change_indicator (ChangeIndicator | str | None): Useful for get
            comparison total followup count and call related data.

    Request body parameters:
        date_range (DateRange | None): Either none or a dictionary which
            contains start date  and end date which useful for filter data
            according to date range.
            e.g., {"start_date": "2023-10-27", "end_date": "2023-10-27"}

    Returns:
        dict: A dictionary which contains followup details summary
            information.

    Raises:
        Exception: An exception which occur when any condition fails.
    """
    user = await UserHelper().is_valid_user(current_user)
    role_name = user.get("role", {}).get("role_name")
    if role_name not in ["college_counselor", "college_head_counselor", "college_admin", "college_super_admin", "super_admin"]:
        raise HTTPException(status_code=401, detail="Not enough permissions")
    date_range = await utility_obj.format_date_range(date_range)

    if role_name in ["college_admin", "college_super_admin", "super_admin"]:
        counsellors = await DatabaseConfiguration().user_collection.aggregate([{
            "$match": {
                "role.role_name": "college_counselor",
                "is_activated": True,
                "associated_colleges": {"$in": [ObjectId(college.get("id"))]}
            }
        }]).to_list(None)
        counselor_ids = [counsellor.get("_id") for counsellor in counsellors]

    elif role_name == "college_head_counselor":
        counselors = await DatabaseConfiguration().user_collection.aggregate(
            [{"$match": {"head_counselor_id": ObjectId(user.get("_id")), "associated_colleges": {"$in": [ObjectId(college.get("id"))]}}}]
        ).to_list(length=None)
        counselor_ids = [ObjectId(data.get("_id")) for data in counselors]
    else:
        counselor_ids = [ObjectId(user.get("_id"))]

    try:
        return await CounselorDashboardHelper().get_followup_details(
            counselor_ids, date_range, change_indicator
        )

    except Exception as error:
        logger.error(
            f"An error got when get followup details summary. Error -" f" {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"An error got when get followup "
            f"details summary. Error - {error}",
        )


@counselor.post(
    "/lead_stage_count_summary/", summary="Get lead stage count summary information."
)
@requires_feature_permission("read")
async def get_lead_stage_count_summary(
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    sort_type: SortType | None | str = None,
    column_name: str | None = Query(
        None,
        description="Column name which useful for sort data based "
        "on sort type. Column name can be: "
        "lead_stage and total.",
    ),
    date_range: DateRange | None = Body(None),
    source_names: list[str] | None = Body(None),
    download_data: bool = False,
):
    """
    Get or download lead stage count summary information.

    Params:
        college_id (str): A unique identifier/id of a college.
            e.g., "123456789012345678901234"
        sort_type (SortType | str | None): Useful for sort
            data by column name.
        column_name (str | None): Column name which useful for sort data
            based on sort type. Column name can be: lead_stage and total.

    Request body parameters:
        date_range (DateRange | None): Either none or a dictionary which
            contains start date  and end date which useful for filter data
            according to date range.
            e.g., {"start_date": "2023-10-27", "end_date": "2023-10-27"}
        source_names (list[str] | None): Either none or a list which
            contains source names.
            e.g., ["Organic", "google"]

    Returns:
        dict: A dictionary which contains lead stage count summary information.

    Raises:
        Exception: An exception which occur when any condition fails.
    """
    current_datetime = datetime.datetime.utcnow()
    user = await UserHelper().is_valid_user(current_user)
    date_range = await utility_obj.format_date_range(date_range)
    user_id = user.get("_id")
    user_role = user.get("role", {}).get("role_name")
    counselor_id = None
    is_head_counselor = False
    if user_role in ["college_head_counselor", "college_counselor"]:
        if user_role == "college_head_counselor":
            is_head_counselor = True
            counselor_id = await AdminUser().get_users_ids_by_role_name(
                "college_counselor", college.get("id"), user_id
            )
        else:
            counselor_id = [ObjectId(user_id)]
    try:
        data = await CounselorDashboardHelper().lead_stage_count_summary(
            source_names, date_range, sort_type, column_name, counselor_id, is_head_counselor
        )
        if data:
            if download_data:
                background_tasks.add_task(
                    DownloadRequestActivity().store_download_request_activity,
                    request_type="Applications data",
                    requested_at=current_datetime,
                    ip_address=utility_obj.get_ip_address(request),
                    user=user,
                    total_request_data=len(data),
                    is_status_completed=True,
                    request_completed_at=datetime.datetime.utcnow(),
                )
                data_keys = list(data[0].keys())
                get_url = await upload_csv_and_get_public_url(
                    fieldnames=data_keys, data=data, name="applications_data"
                )
                return get_url
            return {
                "data": data,
                "message": "Get the lead stage count summary" " information.",
            }
        return {"data": [], "message": "Lead stage data not found."}
    except Exception as error:
        logger.error(
            f"An error got when get lead stage count summary "
            f"information. Error - {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"An error got when get lead stage count "
            f"summary information. Error - {error}",
        )


@counselor.post("/get_pending_followup/")
@requires_feature_permission("read")
async def get_pending_followup(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    date_range: DateRange = Body(None),
    season: str = Body(
        None, description="Enter season value if want to get "
                          "data season-wise"
    ),
    counselor_Id: list = Body(None),
    sort: str = None,
    sort_type: str = Query(None, description="Sort_type can be 'asc' or 'dsc'"),
    page_num: int = Query(gt=0),
    page_size: int = Query(gt=0),
):
    """
    Returns the pending followup details.

    Params:
        - counselor_search (str):  The counselor name which is searched.
        - sort (str): The column which is to be sorted.
        - sort_type (str): Can have values asc,dsc.
        - college_id: Unique id of college
        - date_range: Filter used.
        - Change_indicator: This can have values
            last_7_days/last_15_days/last_30_days

    Returns:
        - dict: A dictionary which contains information about pending followups
            along with message.

    Raises:
        - Exception: An error occurred with status code 500 when something
            wrong happen in the backend code.
    """
    user = await UserHelper().is_valid_user(current_user)
    counselor_id = user.get("_id")
    user_role = user.get("role", {}).get("role_name")
    if user_role not in [
        "college_head_counselor",
        "college_super_admin",
        "college_counselor",
        "college_admin"
    ]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    if user_role in ["college_super_admin", "college_admin"]:
        counselor_ids = await AdminUser().get_users_ids_by_role_name(
            "college_counselor", college.get("id"))
    elif user_role == "college_counselor":
        counselor_ids = [ObjectId(counselor_id)]
    else:
        counselor_ids = await AdminUser().get_users_ids_by_role_name(
            "college_counselor", college.get("id"), user.get("_id")
        )
    try:
        data = await CounselorDashboardHelper().get_pending_followups(
            counselor_ids=counselor_ids, date_range=date_range, season=season
        )
        if counselor_Id:
            data = [
                counselor
                for counselor in data
                if any(
                    search.lower() in counselor["_id"].lower()
                    for search in counselor_Id
                )
            ]
        if sort:
            data = (
                sorted(data, key=lambda x: x[sort], reverse=True)
                if sort_type == "dsc"
                else sorted(data, key=lambda x: x[sort])
            )
        total = len(data)

        response = await utility_obj.pagination_in_api(
            page_num,
            page_size,
            data,
            total,
            route_name="/counselor/get_pending_followup/",
        )
        return {
            "data": response["data"],
            "total": total,
            "count": page_size,
            "pagination": response["pagination"],
            "message": "data fetched successfully",
        }
    except Exception as error:
        logger.error(
            f"An error got when get pending followups details" f"Error - {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"An error got when get pending followups details"
            f"Error - {error}",
        )


@counselor.get("/get_leads_application_data")
@requires_feature_permission("read")
async def get_leads_application_data(
    current_user: CurrentUser,
    date: str = Query(
        description="the  date should be in format" " 2023-12-30 i.e; YYYY-MM-DD"
    ),
    college_id: dict = Depends(get_college_id_short_version(short_version=True)),
    lead_data: bool = True,
):
    """
    API to get leads and application data in counselor dashboard
    Params:
      date (str): date should be in format YYYY-MM-DD
      college_id (str): unique id of college
      lead_data (bool): if true return lead related data else return
       application related data
    returns:
      final dictionary with the collection of different hour wise dictionaries.
    """

    user = await UserHelper().is_valid_user(current_user)
    counselor_id = user.get("_id")
    counselor_role = user.get("role", {}).get("role_name")
    if counselor_role not in ["college_head_counselor", "college_counselor"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    try:
        datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"InCorrect date")
    try:
        head_counselor = False
        if counselor_role == "college_head_counselor":
            head_counselor = True
            cursor = await DatabaseConfiguration().user_collection.aggregate(
                [{"$match": {"head_counselor_id": ObjectId(counselor_id)}}]
            ).to_list(length=None)
            counselor_id = [doc["_id"] for doc in cursor]
        if lead_data:
            result = await CounselorDashboardHelper().get_lead_day_wise_data(
                counselor_id, date, head_counselor
            )
        else:
            result = await CounselorDashboardHelper().get_application_day_wise_data(
                counselor_id, date, head_counselor
            )
        result.update({"message": "Get leads and application data."})
    except Exception as error:
        logger.error(
            f"An error occurred when trying to get lead and application data"
            f"Error - {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when trying to get "
            f"lead and application data"
            f"Error - {error}",
        )
    return result


@counselor.get("/get_human_languages/")
@requires_feature_permission("read")
async def get_leads_application_data(
    current_user: CurrentUser,
    cache_data=Depends(cache_dependency),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    API to get return the languages
    Params:
      college_id (str): unique id of college
    returns:
      array of languages
    """
    await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    try:
        result = {"data": college.get("languages", []), "message": "Get languages"}
    except Exception as error:
        logger.error(
            f"An error occurred when trying to get languages" f"Error - {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when trying to get languages" f"Error - {error}",
        )
    if cache_key:
        await insert_data_in_cache(cache_key, result)
    return result


@counselor.get("/get_counselors_list/")
@requires_feature_permission("read")
async def get_counselors_list(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    API to return counselors list
    Params:
        college_id (str): Unique id of college
    Return:
        dict: Data of counselors
    """
    user = await UserHelper().is_valid_user(current_user)
    head_counselor = None
    if user.get("role").get("role_name") in ["college_head_counselor"]:
        head_counselor = user.get("_id")
    try:
        result = await CounselorDashboardHelper().get_counselors_list(college, head_counselor)
        return result
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while returning counselors information" f"Error - {error}",
        )


@counselor.get("/update_active_status/")
@requires_feature_permission("edit")
async def update_active_status(
    current_user: CurrentUser,
    activate: bool,
    user_email: str,
    college: dict = Depends(get_college_id),

):
    """
    Update status of counselor
    Params:
        activate (bool): If True then active else Inactive
        user_email (str): email of user
        college_id (str): Unique id of college
    Return:
        dict: Data of counselors
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        await DatabaseConfiguration().user_collection.update_one({"email": user_email},
                                                                 {"$set": {"status_active": activate}})
        await cache_invalidation(api_updated="updated_user", user_id=user_email)
        redis_client = get_redis_client()
        if redis_client:
            data = {
                "status": activate,
                "name": utility_obj.name_can(user),
                "mobile_number": user.get("mobile_number")
            }
            redis_key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/{str(user.get('_id'))}/check_in_status"
            await redis_client.set(redis_key, json.dumps(data))
            await redis_client.publish(redis_key, json.dumps(data))
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        user_data = await DatabaseConfiguration().checkincheckout.find_one({"user_id": ObjectId(user.get("_id")),
                                                                            "date": date})
        if user_data:
            if activate:
                update_data = {}
                if "check_in_details" in user_data and user_data.get("check_in_details"):
                    last_entry = user_data.get("check_in_details", [])[-1]
                    if "check_out" not in last_entry:
                        last_entry["check_out"] = datetime.datetime.utcnow()
                        last_entry["total_mins"] = (last_entry["check_out"] - last_entry[
                            "check_in"]).total_seconds() // 60
                    user_data.get("check_in_details", []).append({"check_in": datetime.datetime.utcnow()})
                    update_data.update({
                        "check_in_details": user_data.get("check_in_details")
                    })
                else:
                    update_data.update({
                        "check_in_details": [{
                            "check_in": datetime.datetime.utcnow()
                        }]
                    })
                await DatabaseConfiguration().checkincheckout.update_one({"_id": user_data.get("_id")},
                {
                    "$set": {
                        "current_stage": "CheckIn",
                        "first_checkin": datetime.datetime.utcnow() if not user_data.get("first_checkin") else user_data.get("first_checkin"),
                        **update_data,
                        "last_checkout": None
                }})
            else:
                present_time = datetime.datetime.utcnow()
                await utility_obj.update_checkout_details(user_data, present_time)
        return {"message": "Updated the status accordingly!"}
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while returning counselors information" f"Error - {error}",
        )