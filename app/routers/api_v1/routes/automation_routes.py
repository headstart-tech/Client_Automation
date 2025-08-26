"""
This file contains API routes/endpoints related to automation
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query, BackgroundTasks, Request, Body
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException

from app.background_task.admin_user import DownloadRequestActivity
from app.core.utils import utility_obj, requires_feature_permission
from app.database.aggregation.automation import Automation
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import CurrentUser
from app.helpers.automation.automation_curd import Automation_operator
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.automation import CreateAutomationBeta
from app.s3_events.s3_events_configuration import upload_csv_and_get_public_url

automation_router = APIRouter()


@automation_router.post("_beta/create/", summary="Create automation")
@requires_feature_permission("write")
async def create_automation_beta(
        automation_create: CreateAutomationBeta,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Create automation and store it in the collection named automation
    """
    if automation_create is None:
        automation_create = {}
    user = await UserHelper().is_valid_user(current_user)
    automation_create = jsonable_encoder(automation_create)
    if automation_create.get("automation_details", {}).get(
            "automation_name") == "":
        raise HTTPException(status_code=422,
                            detail="Automation name should be valid.")
    return await Automation_operator().create_automation(
        user=user, payload=automation_create
    )


@automation_router.put("/rule_details/",
                       summary="Get automation rule details by id")
@requires_feature_permission("read")
async def get_automation_rule_details_by_id(
        current_user: CurrentUser,
        automation_id: str = Query(...,
                                   description="Enter automation rule id"),
        module_type: List[str] = Body(None, embed=True),
        data_segment_name: str = Query(None,
                                       description="Enter data segment name"),
        page_num: int = Query(
            ..., gt=0,
            description="Enter page number where you want to " "show data"
        ),
        page_size: int = Query(
            ...,
            gt=0,
            description="Enter page size means how many data "
                        "you want to show on page number",
        ),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get automation rule details by id
    """
    await UserHelper().is_valid_user(current_user)
    skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
    await utility_obj.is_id_length_valid(_id=automation_id,
                                         name="Automation id")
    automation_rule_details, total = await Automation().get_automation_rule_details(
        skip, limit, automation_id, module_type, data_segment_name
    )
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total, route_name="/automation/rule_details/"
    )
    return {
        "data": automation_rule_details,
        "total": total,
        "count": page_size,
        "pagination": response["pagination"],
        "message": "Get automation rule details.",
    }


@automation_router.get(
    "/job_delivery_details_by_id/",
    summary="Get automation job delivery details by id"
)
@requires_feature_permission("read")
async def get_automation_job_delivery_details_by_id(
        current_user: CurrentUser,
        automation_job_id: str = Query(...,
                                       description="Enter automation job id"),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get automation job delivery details by id
    """
    await UserHelper().is_valid_user(current_user)
    automation_job = await Automation().validate_automation_id(
        automation_job_id)
    if automation_job:
        email_details, sms_details, whatsapp_details = (
            await Automation().communication_details_of_job(automation_job)
        )
        return {
            "email": email_details,
            "sms": sms_details,
            "whatsapp": whatsapp_details,
            "message": "Get automation job delivery details.",
        }
    return {
        "detail": "Automation job not found. Make sure automation job id is correct."
    }


@automation_router.post("/download_job_details/")
@requires_feature_permission("download")
async def download_job_details(
        background_tasks: BackgroundTasks,
        current_user: CurrentUser,
        request: Request,
        job_ids: list[str] = None,
        module_type: str = Query(None, description="Enter module type"),
        data_segment_name: str = Query(None,
                                       description="Enter data segment name"),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Download automation rule jobs details data by ids and based on filter
    """
    current_datetime = datetime.utcnow()
    await UserHelper().is_valid_user(current_user)
    data = await Automation().get_automation_rule_jobs_details(
        job_ids, module_type, data_segment_name
    )
    background_tasks.add_task(
        DownloadRequestActivity().store_download_request_activity,
        request_type="Job details",
        requested_at=current_datetime,
        ip_address=utility_obj.get_ip_address(request),
        user=await UserHelper().check_user_has_permission(
            user_name=current_user),
        total_request_data=len(data),
        is_status_completed=True,
        request_completed_at=datetime.utcnow(),
    )
    if data:
        field_names = list(data[0].keys())
        get_url = await upload_csv_and_get_public_url(
            fieldnames=field_names, data=data, name="applications_data"
        )
        return get_url
    return {"detail": "Data not found."}


@automation_router.get(
    "/job_details_by_id/", summary="Get automation job details by id"
)
@requires_feature_permission("read")
async def get_automation_job_details_by_id(
        current_user: CurrentUser,
        automation_job_id: str = Query(...,
                                       description="Enter automation job id"),
        email_id: str = Query(None, description="Enter email id"),
        page_num: int = Query(
            ..., gt=0,
            description="Enter page number where you want to " "show data"
        ),
        page_size: int = Query(
            ...,
            gt=0,
            description="Enter page size means how many data "
                        "you want to show on page number",
        ),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get automation job details by id
    """
    await UserHelper().is_valid_user(current_user)
    automation_job = await Automation().validate_automation_id(
        automation_job_id)
    if automation_job:
        email_status, sms_status, whatsapp_status = (
            await Automation().communication_status_of_job(automation_job)
        )
        skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                              page_size)
        data, total = await Automation().job_details_by_id(
            skip, limit, automation_job, email_id
        )
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, total,
            route_name="/automation" "/job_details_by_id/"
        )
        return {
            "data": data,
            "email_status": email_status,
            "sms_status": sms_status,
            "whatsapp_status": whatsapp_status,
            "total": total,
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Get automation job details.",
        }
    return {
        "detail": "Automation job not found." " Make sure automation job id is correct."
    }


@automation_router.post("/download_job_data/")
@requires_feature_permission("download")
async def download_job_data(
        background_tasks: BackgroundTasks,
        current_user: CurrentUser,
        request: Request,
        automation_job_id: str = Query(...,
                                       description="Enter automation job id"),
        email_id: list[str] = None,
        action_type: list[str] = None,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Download automation job data by id and based on filter
    """
    current_datetime = datetime.utcnow()
    await UserHelper().is_valid_user(current_user)
    automation_job = await Automation().validate_automation_id(
        automation_job_id)
    if automation_job:
        data, total = await Automation().job_details_by_id(
            0,
            (
                len(automation_job.get("job_details"))
                if automation_job.get("job_details")
                else 1
            ),
            automation_job,
            email_id,
            action_type=action_type,
        )
        background_tasks.add_task(
            DownloadRequestActivity().store_download_request_activity,
            request_type=f"Job data of id {automation_job_id} with email_ids {email_id}",
            requested_at=current_datetime,
            ip_address=utility_obj.get_ip_address(request),
            user=await UserHelper().check_user_has_permission(
                user_name=current_user),
            total_request_data=len(data),
            is_status_completed=True,
            request_completed_at=datetime.utcnow(),
        )
        if data:
            field_names = list(data[0].keys())
            get_url = await upload_csv_and_get_public_url(
                fieldnames=field_names, data=data, name="applications_data"
            )
            return get_url
        return {"detail": "Data not found."}
    return {
        "detail": "Automation job not found. Make sure automation job id is correct."
    }
