"""
This file contains routes/APIs that will be used for generate report,
get reports, get download url of report and call webhook to update
report status.
"""
import datetime
from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, Query, Request, Body, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings, requires_feature_permission
from app.database.aggregation.reports import Report
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import Is_testing, cache_dependency, insert_data_in_cache, CurrentUser
from app.helpers.report.update_report_status import ReportStatusHelper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.applications import DateRange
from app.models.report_schema import GenerateReport, ReportFilter
from app.models.student_user_schema import User
from app.core.custom_error import DataNotFoundError, ObjectIdInValid, \
    CustomError
from app.helpers.report.report_configuration import ReportHelper
from app.background_task.admin_user import DownloadRequestActivity
from app.core.reset_credentials import Reset_the_settings

logger = get_logger(name=__name__)
report_router = APIRouter()


async def unique_code_for_reports(date_range):
    date_range = jsonable_encoder(date_range)
    if date_range is None:
        date_range = {}
    start_date, end_date = await utility_obj.get_start_and_end_date(date_range)
    return start_date, end_date


@report_router.get("/get_saved_report_templates/",
                   summary="Get all saved Report Templates")
@requires_feature_permission("read")
async def get_saved_report_templates(
        testing: Is_testing,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """
    API for saved report template calling from database.

    Params:
        - college_id (str): An unique id/identifier of a college.
            e.g., 123456789012345678901234

    Returns:
        - dict: A dictionary which contains information about saved reports.

    Raises:
        - ObjectIdInValid: An error occurred with status code 422
            when college_id not valid.
        - Exception: An error occurred with status code 500
            when something wrong in backend code.
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    await UserHelper().is_valid_user(current_user)
    try:
        data = await ReportHelper().get_all_saved_report_templates()

        return {
            "data": data,
            "total": len(data),
            "message": "Get the saved report template.",
        }
    except Exception as error:
        logger.error(
            f"An error got when get list of report templates. Error - {error}")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@report_router.post(
    "/generate_request_data/", summary="Generate?update report based on "
                                       "request data"
)
@requires_feature_permission("write")
async def generate_report(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        testing: Is_testing,
        request: Request,
        request_data: GenerateReport,
        payload: ReportFilter = None,
        report_id: str | None = Query(
            None, description="Enter report id when want to update data of "
                              "saved_template/report."),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Generate/Update Report Based on Request Data.

    Params:\n
        - report_id (str | None): Either None or a unique id/identifier of a
            report. e.g., 123456789012345678901231
        - college_id (str): An unique id/identifier of a college.
            e.g., 123456789012345678901234


    Request body params:\n
        - request_data (GenerateReport): An object of pydantic class
            `GenerateReport` which contains following fields:
            - report_type (str | None): Either None or type of report.
            - report_name (str | None): Either None or name of report.
            - format (str | None): Either None or format of a report.
            - report_details (str | None): Either None or details/description
                of report.
            - date_range (DateRange | None): Either None or date range which
                useful for get data based on date_range.
                e.g.,{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}
            - report_send_to (str | None): Either None or email id which
                useful for send report data.
            - schedule_value (int | None): Either None or schedule value.
            - schedule_type (str | None): Either None or type of schedule
                report.
            - reschedule_report (bool | None): Either None or boolean value
                True for reschedule report.
            - advance_filter (list | None): Either None list of
                dictionary which contains information about advance filter.

            - period (Union[dict, str] | None): Either None or string or
                dictionary about period of report.
            - sent_mail (bool | None): Either None or boolean value True for
                send mail to recipients.
            - recipient_details (list[RecipientDetails] | None): Either None
                or list of recipients data.
            - add_column (list[str] | None): Either None or list of column
                which want to add in the report.
            - save_template (bool | None): Either None or boolean value `True`
                which useful for save report.
            - generate_and_reschedule (GenerateAndReschedule | None): Either
                None or details of generate and reschedule report.
            - is_auto_schedule (bool | None): Either None or boolean value
                `True` which useful auto schedule report.

    Returns:\n
        - dict: A dictionary which contains information about add/update
            report.

    Raises:\n
        - ObjectIdInValid: An error occurred with status code 422
            when report_id not valid.
        - CustomError: An error occurred with status code 422
            when report type is invalid.
        - DataNotFoundError: An error occurred with status code 404
            when report not found by id.
        - Exception: An error occurred with status code 500
            when something wrong in backend code.
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    current_datetime = datetime.datetime.utcnow()
    user = await UserHelper().is_valid_user(current_user)
    try:
        report_helper_obj = ReportHelper()
        request_data, report_type, report_format = await report_helper_obj. \
            validate_and_format_report_data(request_data)
        if report_id:
            return await report_helper_obj.update_report_data(
                report_id, user, request_data, payload)
        else:
            return await report_helper_obj.generate_or_save_report(
                payload, request, request_data, report_type, report_format,
                current_datetime, user, college.get('id'), background_tasks)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@report_router.post(
    "/current_user/",
    summary="Get reports of current user based on date range and pagination",
)
@requires_feature_permission("read")
async def reports_of_current_user(
        current_user: CurrentUser,
        request: Request,
        testing: Is_testing,
        date_range: DateRange = None,
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0),
        college: dict = Depends(get_college_id),
        reschedule_report: bool = Query(
            False, description="Want reschedule report of current user then "
                               "send value True"),
        auto_schedule_reports: bool = Query(
            False, description="Want auto schedule report of current user "
                               "then send value True"),
        search_pattern: str | None = Query(
            None, description="Enter search pattern which useful for get "
                              "current user reports by search_pattern.")
):
    """
    Get reports of current user based on date range and pagination\n

    Params:\n
        - page_num (int): Enter page number where you want to show
            reports data. e.g., 1
        - page_size: Enter page size means how many data you want to show on
            page_num. e.g., 25
        - college_id (str): A string which represents unique id/identifier
            of college. e.g., 123456789012345678901234.
        - reschedule_report (bool): Default value: False. When value is True then
            user will get reschedule reports.
        - auto_schedule_reports (bool): Default value: False. When value is
            True then user will get auto schedule reports.
        - search_pattern (str | None): Either None or string which useful
                for get current user reports by search_pattern.

    Request body params:\n
        - date_range (DateRange | None): Either None or date_range which
            useful for get data based on date_range.
            Start & end date format will be YYYY-MM-DD".
            e.g., {'start_date': '2022-05-24', 'end_date': '2022-05-24'}

    Returns:\n
        dict: A dictionary which contains current user reports.
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    user = await UserHelper().is_valid_user(current_user)
    action_type = "counselor" \
        if user.get('role', {}).get(
        'role_name') == "college_counselor" else "system"
    start_date, end_date = await unique_code_for_reports(date_range)
    reports, total_reports = await Report().current_user_reports(
        page_num, page_size, start_date, end_date, str(user.get("_id")),
        ObjectId(college.get('id')), reschedule_report,
        request, college, action_type=action_type,
        auto_schedule_reports=auto_schedule_reports,
        search_pattern=search_pattern
    )
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total_reports, "/reports/current_user/"
    )
    return {
        "data": reports,
        "total": total_reports,
        "count": page_size,
        "pagination": {
            "next": response.get("pagination", {}).get("next"),
            "previous": response.get("pagination", {}).get("previous"),
        },
        "message": "Get reports of current user.",
    }


@report_router.post("/",
                    summary="Get reports based on date range and pagination")
@requires_feature_permission("read")
async def get_all_reports(
        current_user: CurrentUser,
        request: Request,
        testing: Is_testing,
        date_range: DateRange = None,
        user_name: str = Body(None),
        report_type: str = Body(None),
        user_type: List[str] = Body(None),
        user_id: str = Body(None),
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0),
        college: dict = Depends(get_college_id),
        reschedule_report: bool = Query(
            False, description="Want reschedule report then send value True"),
        auto_schedule_reports: bool = Query(
            False, description="Want auto schedule report of current user "
                               "then send value True"),
        search_pattern: str | None = Query(
            None, description="Enter search pattern which useful for get "
                              "current user reports by search_pattern.")
):
    """
    Get all reports based on date range and pagination

    Params:\n
        - page_num (int): Enter page number where you want to show
            reports data. e.g., 1
        - page_size: Enter page size means how many data you want to show on
            page_num. e.g., 25
        - college_id (str): A string which represents unique id/identifier
            of college. e.g., 123456789012345678901234.
        - reschedule_report (bool): Default value: False. When value is True then
            user will get reschedule reports.
        - auto_schedule_reports (bool): Default value: False. When value is
            True then user will get auto schedule reports.
        - search_pattern (str | None): Either None or string which useful
                for get current user reports by search_pattern.

    Request body params:\n
        - date_range (DateRange | None): Either None or date_range which
            useful for get data based on date_range.
            Start & end date format will be YYYY-MM-DD".
            e.g., {'start_date': '2022-05-24', 'end_date': '2022-05-24'}
        - user_name (str | None): Either None or user_name which useful for get
            reports based on user_name.
        - report_type (str | None): Either None or report_type which useful for
            get data based on report_type.
        - user_type (List[str] | None): Either None or user_type which useful
            for get data based on user_type.
        - user_id (str | None): Either None or unique user id which useful
            for get data based on user_id.

    Returns:\n
        - dict: A dictionary which contains all reports data with message
            Get reports.
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    await UserHelper().is_valid_user(current_user)
    start_date, end_date = await unique_code_for_reports(date_range)
    reports, total_reports = await Report().get_reports(
        page_num, page_size, start_date, end_date, user_type, user_id,
        user_name, report_type, ObjectId(college.get('id')), reschedule_report,
        request, college, auto_schedule_reports=auto_schedule_reports,
        search_pattern=search_pattern
    )
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total_reports, "/reports/"
    )
    return {
        "data": reports,
        "total": total_reports,
        "count": page_size,
        "pagination": {
            "next": response.get("pagination", {}).get("next"),
            "previous": response.get("pagination", {}).get("previous"),
        },
        "message": "Get reports.",
    }


@report_router.post(
    "/get_download_url_by_request_id/",
    summary="Download reports data by report id (s)"
)
@requires_feature_permission("download")
async def get_download_url_by_request_id(
        background_tasks: BackgroundTasks,
        testing: Is_testing,
        request: Request,
        report_ids: list[str],
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)
):
    """
    Download reports data by request ids.

    Params:\n
        - report_ids (list[str]): A list which contains unique report ids.
        - college_id (str): An unique id/identifier of a college.
                e.g., 123456789012345678901234

    Returns:\n
        - dict: A dictionary which contains report data downloadable URL along
            with successful message.

    Raises:\n
        - ObjectIdInValid: An error occurred when report_id is not valid.
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    current_datetime = datetime.datetime.utcnow()
    await UserHelper().is_valid_user(current_user)
    try:
        data = await Report().get_reports_data_by_ids(report_ids)
        if data:
            background_tasks.add_task(
                DownloadRequestActivity().store_download_request_activity,
                request_type="Report Data",
                requested_at=current_datetime,
                ip_address=utility_obj.get_ip_address(request),
                user=await UserHelper().check_user_has_permission(
                    user_name=current_user),
                total_request_data=data.get("data_length"),
                is_status_completed=True,
                request_completed_at=datetime.datetime.utcnow())
            return data
        return {"detail": "No any report data found to download."}
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"An error occurred when get the download "
                                    f"url of reports. Error - {error}")


@report_router.post("/webhook/",
                    summary="Update report result based on request id")
async def update_report_result_using_request_id(
        request: Request,
        testing: Is_testing,
        request_id: int = Query(..., description="Enter request id"),
        college: dict = Depends(get_college_id),
        token=Query(None, description="Enter token"),
        timestamp=Query(None, description="Enter timestamp"),
        signature: str = Query(..., description="Enter the signature"),
):
    """
    Update report result based on request id\n
    * :return: Message - Updated report result.
    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    verify = await utility_obj.verify_signature(
        settings.report_webhook_api_key.encode("utf-8"), token, timestamp,
        signature
    )
    if verify:
        await ReportStatusHelper().update_status_report_by_request_id(
            request_id=request_id, request=request,
            college=college)
    else:
        logger.info("Signature verification failed.")
        raise HTTPException(status_code=422,
                            detail="Signature verification failed.")


@report_router.post("/delete_report_by_id/",
                    summary="Delete report by id.")
@requires_feature_permission("delete")
async def delete_report_by_id(
        report_ids: list[str],
        testing: Is_testing,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)
):
    """
    Delete report API by the using of ID.

    Params:
        report_ids (list[str]): Report unique ID's
        current_user (User, optional): User details of Requested user. Defaults to Depends(get_current_user).
        college (dict, optional): For validation of the correct college request. Defaults to Depends(get_college_id).

    Returns:
        - dict: A dictionary which contains information about delete a report templates.

    Raises:
        - ObjectIdInValid: An error occurred with status code 422 when report template id is wrong.
        - DataNotFoundError: An error occurred with status code 404 when report template not found.
        - Exception: An error occurred with status code 500 when s something wrong happen in the backend code.

    """
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    await UserHelper().is_valid_user(current_user)
    try:
        return await ReportHelper().delete_report_template_by_id(report_ids)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        logger.error("An error got when delete the reports template "
                     "in the report section.")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@report_router.get(
    "/header_info/", response_description="Get the report header information based on report type.")
@requires_feature_permission("read")
async def get_header_info(
        report_type: str,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
        cache_data=Depends(cache_dependency),
        search_pattern: str | None = Query(
            None, description="Enter search pattern. Useful for get report headers based on search_pattern.")
):
    """
    Get the report header information based on report type.

    Params:
        - report_type (str): Type of report. Possible values are: Leads, Applications and Forms.
        - college_id (str): An unique identifier of college. e.g., 123456789012345678901234
        - search_pattern (str): Default value: None. A string value which useful for get fields based on search_pattern.

    Returns:
        - dict: A dictionary which contains information about report headers.

    Raises:
        - 401: An error occurred with status code 401 when user don't have permission.
        - Exception: An error occurred with status code 500 when s something wrong happen in the backend code.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        cache_key, data = cache_data
        if data:
            return data
        data, total = await ReportHelper().get_headers_info(
            college.get("id"), search_pattern, report_type)
        all_data = {"total": total, "data": data,
                    "message": "Get the report header list."}
        if cache_key:
            await insert_data_in_cache(cache_key, all_data)
        return all_data
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occurred when get the report headers information. "
                                                    f"Error - {error}")
