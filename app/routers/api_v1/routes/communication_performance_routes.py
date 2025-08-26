"""
This file contains APIs related to Communication Performance module in admin profile.
"""
import datetime

from fastapi import APIRouter, Depends, Body, BackgroundTasks, Request
from fastapi.exceptions import HTTPException

from app.background_task.admin_user import DownloadRequestActivity
from app.core.custom_error import CustomError, ObjectIdInValid
from app.core.log_config import get_logger
from app.core.utils import utility_obj, requires_feature_permission
from app.dependencies.college import get_college_id_short_version
from app.dependencies.oauth import CurrentUser
from app.helpers.communication_performance_helpers import communication_performance_obj
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.student_user_schema import User, DateRange, ChangeIndicator, CommunicationType

from app.s3_events.s3_events_configuration import upload_csv_and_get_public_url

communication_performance = APIRouter()
logger = get_logger(name=__name__)


@communication_performance.post("/header_details")
@requires_feature_permission("read")
async def header_details(
    current_user: CurrentUser,
    date_range: DateRange | None = Body(None),
    change_indicator: ChangeIndicator = "last_7_days",
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
        Retrieves header details based on the specified date range, change indicator,
        current user, and college context.

        Args:
            date_range (DateRange | None): An optional DateRange object or `None`.
                                           If provided, it specifies the range of dates
                                           for which header details are to be retrieved.
                                           Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
            change_indicator (ChangeIndicator): A string or enumeration value indicating
                                                the time frame or type of change to analyze.
                                                Defaults to "last_7_days".
                                                Example: "last_15_days"
            current_user (User): The current authenticated user, injected via dependency.
                                 Provides context about the user making the request.
            college (dict): A dictionary containing college details, injected via dependency.
                            Includes the college's ID useful for scoping the data.

        Returns:
            dict: A dictionary containing the header details, such as counts, summaries, or
                  other contextual information based on the input parameters.

        Raises:
            HTTPException: If the user is unauthorized or does not have access to the requested data.
            ValueError: If `date_range` or `change_indicator` contains invalid values.
    """
    user = await UserHelper().check_user_has_permission(current_user, [
        "college_admin",
        "college_super_admin",
        "super_admin",
        "college_counselor",
        "college_head_counselor"
    ], False)
    try:
        date_range = await utility_obj.format_date_range(date_range)
        response = await communication_performance_obj.header_details(
            date_range, change_indicator, await communication_performance_obj.counselor_ids(user, college.get('id'))
        )
        data = {"data": response, "message": "Communication Performance dashboard header data."}
        return data
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the communication summary dashboard header data. Error: {error}.",
        )


@communication_performance.post("/date_wise_performance_graph")
@requires_feature_permission("read")
async def date_wise_performance_graph(
    current_user: CurrentUser,
    communication_type: CommunicationType,
    date_range: DateRange | None = Body(None),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
        Retrieves data for a date-wise performance graph based on the specified communication
        type, date range

        Params:
            communication_type (CommunicationType): The type of communication to analyze.
                                                    Example: "email", "sms", or "whatsapp".
            date_range (DateRange | None): An optional DateRange object or `None`. If provided,
                                           it specifies the range of dates for which the performance
                                           data is to be retrieved.
                                           Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
            current_user (User): The current authenticated user, injected via dependency.
                                 Provides context for filtering the data based on user permissions.
            college (dict): A dictionary containing college details, injected via dependency.
                            Includes the college's ID and short version, useful for scoping the data.

        Returns:
            dict: A dictionary containing date-wise performance data.
    """
    user = await UserHelper().check_user_has_permission(current_user,[
            "college_admin",
            "college_super_admin",
            "super_admin",
            "college_counselor",
            "college_head_counselor"
        ],False)
    try:
        date_range = await utility_obj.format_date_range(date_range)
        communication_type = communication_type.value
        response = await communication_performance_obj.date_wise_performance_graph(
            date_range, communication_type, await communication_performance_obj.counselor_ids(user, college.get('id'))
        )
        data = {"data": response, "message": "Communication Performance Date wise section data."}
        return data
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the communication summary dashboard Date wise section data. Error: {error}.",
        )


@communication_performance.post("/release_details")
@requires_feature_permission("read")
async def get_release_details(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    request: Request,
    communication_type: CommunicationType,
    date_range: DateRange | None = Body(None),
    download: bool = False,
    college: dict = Depends(get_college_id_short_version(short_version=True)),

):
    """
        Retrieves release details for a specific communication type within the given date range.
        Optionally allows downloading the details as a file.

        Params:
            background_tasks (BackgroundTasks): An object for managing background tasks
                                                during the request lifecycle, such as logging
                                                or file generation.
            request (Request): The HTTP request object containing metadata and context about
                               the incoming API call.
            communication_type (CommunicationType): The type of communication to analyze.
                                                    Example: "email", "sms", or "whatsapp".
            date_range (DateRange | None): An optional DateRange object or `None`. If provided,
                                           specifies the range of dates for which to retrieve
                                           release details.
                                           Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
            current_user (User): The currently authenticated user, injected via dependency.
                                 Used to scope the data based on user permissions.
            download (bool): A flag indicating whether the release details should be prepared
                             for download. Defaults to `False`.
            college (dict): A dictionary containing college details, injected via dependency.
                            Includes the college's ID and short version.

        Returns:
            dict: A dictionary containing release details. If `download` is `True`, the response
                  may include a file download URL or status of the background task.

        Raises:
            HTTPException: If the user is unauthorized or if there is an error in retrieving or processing data.
            ValueError: If `date_range` or `communication_type` contains invalid values.
    """
    user = await UserHelper().check_user_has_permission(current_user, [
        "college_admin",
        "college_super_admin",
        "super_admin",
        "college_counselor",
        "college_head_counselor"
    ], False)
    try:
        date_range = await utility_obj.format_date_range(date_range)
        communication_type = communication_type.value
        response = await communication_performance_obj.release_details(
            date_range, communication_type, await communication_performance_obj.counselor_ids(user, college.get('id'))
        )
        if download:
            data_keys = list(response[0].keys())
            get_url = await upload_csv_and_get_public_url(
                fieldnames=data_keys,
                data=response,
                name="utm",
            )
            background_tasks.add_task(
                DownloadRequestActivity().store_download_request_activity,
                request_type="applications_data",
                requested_at=datetime.datetime.utcnow(),
                ip_address=utility_obj.get_ip_address(request),
                user=await UserHelper().check_user_has_permission(
                    user_name=current_user),
                total_request_data=len(response),
                is_status_completed=True,
                request_completed_at=datetime.datetime.utcnow(),
            )
            return get_url
        data = {"data": response, "message": "Communication Performance Release details."}
        return data
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the communication summary dashboard Release details data. Error: {error}.",
        )


@communication_performance.post("/profile_wise_details")
@requires_feature_permission("read")
async def get_profile_wise_details(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    request: Request,
    communication_type: CommunicationType,
    date_range: DateRange | None = Body(None),
    sort: str = None,
    sort_type: str =None,
    download: bool = False,
    college: dict = Depends(get_college_id_short_version(short_version=True)),

):
    """
        Retrieves communication performance details categorized by user profiles within a specified date range.
        Supports optional sorting and allows data download.

        Params:
            background_tasks (BackgroundTasks): FastAPI background task manager for handling tasks such as file generation.
            request (Request): The incoming HTTP request object for accessing metadata or payload.
            communication_type (CommunicationType): The type of communication to analyze, such as "email", "SMS", or "notification".
            date_range (DateRange | None): Optional. Specifies the start and end dates for filtering the data.
                                           Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
            sort (str | None): Optional. The field to sort the results by.
                               Example: "sent", "opened", "clicked".
            sort_type (str | None): Optional. The sorting order, either "asc" (ascending) or "desc" (descending).
                                    Defaults to `None`.
            current_user (User): The current authenticated user extracted via dependency injection.
            download (bool): Flag to indicate if the data should be prepared for download (e.g., as a CSV or Excel file).
            college (dict): Context information about the college, derived from a dependency function.

        Returns:
            dict: A response containing communication performance details grouped by user profiles.
                  If `download` is `True`, a link to download the data will be included.

        Raises:
            HTTPException: If authentication fails, or if invalid parameters are provided.
    """
    user = await UserHelper().check_user_has_permission(current_user, [
        "college_admin",
        "college_super_admin",
        "super_admin",
        "college_counselor",
        "college_head_counselor"
    ], False)
    try:
        date_range = await utility_obj.format_date_range(date_range)
        communication_type = communication_type.value
        response = await communication_performance_obj.get_profile_wise_details(
            date_range, communication_type, sort, sort_type,
            await communication_performance_obj.counselor_ids(user, college.get('id'))
        )
        if download:
            data_keys = list(response[-1].keys())
            get_url = await upload_csv_and_get_public_url(
                fieldnames=data_keys,
                data=response,
                name="utm",
            )
            background_tasks.add_task(
                DownloadRequestActivity().store_download_request_activity,
                request_type="applications_data",
                requested_at=datetime.datetime.utcnow(),
                ip_address=utility_obj.get_ip_address(request),
                user=await UserHelper().check_user_has_permission(
                    user_name=current_user),
                total_request_data=len(response),
                is_status_completed=True,
                request_completed_at=datetime.datetime.utcnow(),
            )
            return get_url
        data = {"data": response, "message": "Communication Performance Profile wise details."}
        return data
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the communication summary dashboard Profile wise details. Error: {error}.",
        )


@communication_performance.post("/datasegment_wise_details")
@requires_feature_permission("read")
async def get_datasegmnet_wise_details(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    request: Request,
    communication_type: CommunicationType,
    date_range: DateRange | None = Body(None),
    sort: str = None,
    sort_type: str = None,
    data_type: list = Body(None),
    segment_type: str = None,
    download: bool = False,
    college: dict = Depends(get_college_id_short_version(short_version=True)),

):
    """
    Retrieves communication performance details grouped by data segments within a specified date range.
    Supports optional sorting, filtering by data type and segment type, and allows data download.

    Params:
        background_tasks (BackgroundTasks): FastAPI background task manager for handling tasks such as file generation.
        request (Request): The incoming HTTP request object for accessing metadata or payload.
        communication_type (CommunicationType): The type of communication to analyze, such as "email", "SMS", or "notification".
        date_range (DateRange | None): Optional. Specifies the start and end dates for filtering the data.
                                       Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
        sort (str | None): Optional. The field to sort the results by.
                           Example: "sent", "opened", "failed".
        sort_type (str | None): Optional. The sorting order, either "asc" (ascending) or "desc" (descending).
                                Defaults to `None`.
        data_type (str | None): Optional. The type of data to filter, such as "user", "activity", or "transaction".
        segment_type (str | None): Optional. The specific segment to filter, such as "region", "age_group", or "department".
        current_user (User): The current authenticated user extracted via dependency injection.
        download (bool): Flag to indicate if the data should be prepared for download (e.g., as a CSV or Excel file).
        college (dict): Context information about the college, derived from a dependency function.

    Returns:
        dict: A response containing communication performance details grouped by data segments.
              If `download` is `True`, a link to download the data will be included.

    Raises:
        HTTPException: If authentication fails, or if invalid parameters are provided.
    """

    user = await UserHelper().check_user_has_permission(current_user, [
        "college_admin",
        "college_super_admin",
        "super_admin",
        "college_counselor",
        "college_head_counselor"
    ], False)
    try:
        date_range = await utility_obj.format_date_range(date_range)
        communication_type = communication_type.value
        response = await communication_performance_obj.get_data_segment_wise_details(
            date_range, communication_type, sort, sort_type, data_type,
            segment_type, await communication_performance_obj.counselor_ids(user, college.get('id'))
        )
        if download:
            data_keys = list(response[-1].keys())
            get_url = await upload_csv_and_get_public_url(
                fieldnames=data_keys,
                data=response,
                name="utm",
            )
            background_tasks.add_task(
                DownloadRequestActivity().store_download_request_activity,
                request_type="applications_data",
                requested_at=datetime.datetime.utcnow(),
                ip_address=utility_obj.get_ip_address(request),
                user=await UserHelper().check_user_has_permission(
                    user_name=current_user),
                total_request_data=len(response),
                is_status_completed=True,
                request_completed_at=datetime.datetime.utcnow(),
            )
            return get_url
        data = {"data": response, "message": "Communication Performance Data segment wise details."}
        return data
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the communication summary dashboard Data segment wise details. Error: {error}.",
        )


@communication_performance.post("/offline_data_details")
@requires_feature_permission("read")
async def get_offline_data_details(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    request: Request,
    communication_type: CommunicationType,
    date_range: DateRange | None = Body(None),
    sort: str = None,
    sort_type: str = None,
    download: bool = False,
    college: dict = Depends(get_college_id_short_version(short_version=True)),

):
    """
        Retrieves offline communication data details grouped by relevant categories within a specified date range.
        Supports sorting and provides an option to download the results.

        Params:
            background_tasks (BackgroundTasks): FastAPI background task manager for handling asynchronous tasks like file generation.
            request (Request): The incoming HTTP request object for accessing metadata or payload.
            communication_type (CommunicationType): The type of communication to analyze, such as "email", "SMS", or "notification".
            date_range (DateRange | None): Optional. Specifies the start and end dates for filtering the offline data.
                                           Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
            sort (str | None): Optional. The field to sort the results by.
                               Example: "processed", "failed", "pending".
            sort_type (str | None): Optional. The sorting order, either "asc" (ascending) or "desc" (descending).
                                    Defaults to `None`.
            current_user (User): The current authenticated user extracted via dependency injection.
            download (bool): Flag to indicate if the data should be prepared for download (e.g., as a CSV or Excel file).
            college (dict): Context information about the college, derived from a dependency function.

        Returns:
            dict: A response containing offline communication details grouped by relevant categories.
                  If `download` is `True`, a link to download the data will be included.

        Raises:
            HTTPException: If authentication fails, or if invalid parameters are provided.
    """
    user = await UserHelper().check_user_has_permission(current_user, [
        "college_admin",
        "college_super_admin",
        "super_admin",
        "college_counselor",
        "college_head_counselor"
    ], False)
    try:
        date_range = await utility_obj.format_date_range(date_range)
        communication_type = communication_type.value
        response = await communication_performance_obj.get_offline_data_details(
            date_range, communication_type, sort, sort_type,
            await communication_performance_obj.counselor_ids(user, college.get('id'))
        )
        if download:
            data_keys = list(response[-1].keys())
            get_url = await upload_csv_and_get_public_url(
                fieldnames=data_keys,
                data=response,
                name="utm",
            )
            background_tasks.add_task(
                DownloadRequestActivity().store_download_request_activity,
                request_type="applications_data",
                requested_at=datetime.datetime.utcnow(),
                ip_address=utility_obj.get_ip_address(request),
                user=await UserHelper().check_user_has_permission(
                    user_name=current_user),
                total_request_data=len(response),
                is_status_completed=True,
                request_completed_at=datetime.datetime.utcnow(),
            )
            return get_url
        data = {"data": response, "message": "Communication Performance Offline data wise details."}
        return data
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the communication summary dashboard Offline data wise details. Error: {error}.",
        )


@communication_performance.post("/template_wise_details")
@requires_feature_permission("read")
async def get_template_wise_details(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    request: Request,
    communication_type: CommunicationType,
    date_range: DateRange | None = Body(None),
    sort: str = None,
    sort_type: str = None,
    download: bool = False,
    release_type: str = None,
    user_id: str = None,
    offline_data_id: str = None,
    data_segment_id: str = None,
    college: dict = Depends(get_college_id_short_version(short_version=True)),

):
    """
    Retrieves communication performance details grouped by templates within a specified date range.
    Supports optional sorting and the ability to download the data.

    Params:
        background_tasks (BackgroundTasks): FastAPI background task manager for handling tasks such as file generation.
        request (Request): The incoming HTTP request object for accessing metadata or payload.
        communication_type (CommunicationType): The type of communication to analyze.
                                                Example: "email", "SMS", or "notification".
        date_range (DateRange | None): Optional. Specifies the start and end dates for filtering the data.
                                       Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
        sort (str | None): Optional. The field to sort the results by.
                           Example: "sent", "opened", "failed".
        sort_type (str | None): Optional. The sorting order, either "asc" (ascending) or "desc" (descending).
                                Defaults to `None`.
        current_user (User): The current authenticated user extracted via dependency injection.
        download (bool): Flag to indicate if the data should be prepared for download (e.g., CSV or Excel file).
        release_type (str | None): Optional. Specifies the type of release to filter the data.
                                   Example: "Manual", "Automatic".
        user_id (str | None): Optional. Filters the data by the specific user's identifier.
        offline_data_id (str | None): Optional. Filters the data by a specific offline data identifier.
        data_segment_id (str | None): Optional. Filters the data by a specific data segment identifier.
        college (dict): Information about the college context, derived from a dependency function.

    Returns:
        dict: A response containing communication performance details grouped by template.
              If `download` is `True`, a link to download the data will be included.

    Raises:
        HTTPException: If authentication fails or invalid parameters are provided.
    """
    user = await UserHelper().check_user_has_permission(current_user, [
        "college_admin",
        "college_super_admin",
        "super_admin",
        "college_counselor",
        "college_head_counselor"
    ], False)
    try:
        date_range = await utility_obj.format_date_range(date_range)
        communication_type = communication_type.value
        response = await communication_performance_obj.get_template_wise_details(
            date_range, communication_type, sort, sort_type, release_type,
            user_id, offline_data_id, data_segment_id,
            await communication_performance_obj.counselor_ids(user, college.get('id'))
        )
        if download:
            data_keys = list(response[-1].keys())
            get_url = await upload_csv_and_get_public_url(
                fieldnames=data_keys,
                data=response,
                name="utm",
            )
            background_tasks.add_task(
                DownloadRequestActivity().store_download_request_activity,
                request_type="applications_data",
                requested_at=datetime.datetime.utcnow(),
                ip_address=utility_obj.get_ip_address(request),
                user=await UserHelper().check_user_has_permission(
                    user_name=current_user),
                total_request_data=len(response),
                is_status_completed=True,
                request_completed_at=datetime.datetime.utcnow(),
            )
            return get_url
        data = {"data": response, "message": "Communication Performance Template wise details."}
        return data
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the communication summary dashboard Template wise details. Error: {error}.",
        )


@communication_performance.post("/date_wise_details")
@requires_feature_permission("read")
async def get_date_wise_details(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    request: Request,
    communication_type: CommunicationType,
    date_range: DateRange | None = Body(None),
    dates: list[str] = Body(None),
    sort: str = None,
    sort_type: str = None,
    download: bool = False,
    college: dict = Depends(get_college_id_short_version(short_version=True)),

):
    """
        Retrieves communication details grouped by date, based on a specified date range or a list of specific dates.
        Supports sorting the results by a specified field and order, and allows for downloading the data.

        Params:
            background_tasks (BackgroundTasks): FastAPI background task manager for handling tasks like download history.
            request (Request): The incoming HTTP request object for accessing metadata or payload.
            communication_type (CommunicationType): The type of communication to analyze.
                                                    Example: "email", "SMS", or "notification".
            date_range (DateRange | None): Optional. Specifies the start and end dates for filtering the data.
                                           Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
            dates (list[str] | None): Optional. A list of specific dates to include in the results.
                                      If provided, overrides `date_range`.
                                      Example: ["2024-01-01", "2024-01-15", "2024-01-31"].
            sort (str | None): Optional. The field to sort the results by. Example: "sent", "failed", "opened".
            sort_type (str | None): Optional. The sorting order, either "asc" (ascending) or "desc" (descending).
                                    Defaults to `None`.
            current_user (User): The current authenticated user extracted via dependency injection.
            download (bool): Flag to indicate if the data should be prepared for download (e.g., CSV or Excel file).
            college (dict): Information about the college context, derived from a dependency function.

        Returns:
            dict: A response containing the communication details grouped by date.

        Raises:
            HTTPException: If authentication fails or invalid parameters are provided.
    """
    user = await UserHelper().check_user_has_permission(current_user, [
        "college_admin",
        "college_super_admin",
        "super_admin",
        "college_counselor",
        "college_head_counselor"
    ], False)
    try:
        communication_type = communication_type.value
        date_range = await utility_obj.format_date_range(date_range)
        response = await communication_performance_obj.get_date_wise_details(
            date_range, dates, communication_type, sort, sort_type,
            await communication_performance_obj.counselor_ids(user, college.get('id'))
        )
        if download:
            data_keys = list(response[-1].keys())
            get_url = await upload_csv_and_get_public_url(
                fieldnames=data_keys,
                data=response,
                name="utm",
            )
            background_tasks.add_task(
                DownloadRequestActivity().store_download_request_activity,
                request_type="applications_data",
                requested_at=datetime.datetime.utcnow(),
                ip_address=utility_obj.get_ip_address(request),
                user=await UserHelper().check_user_has_permission(
                    user_name=current_user),
                total_request_data=len(response),
                is_status_completed=True,
                request_completed_at=datetime.datetime.utcnow(),
            )
            return get_url
        data = {"data": response, "message": "Communication Performance Date wise details."}
        return data
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the communication summary dashboard Date wise details. Error: {error}.",
        )


@communication_performance.post("/get_student_communication_details")
@requires_feature_permission("read")
async def student_communication_details(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    request: Request,
    date: str,
    communication_type: CommunicationType,
    user_id: list = Body([]),
    data_segment_id: list = Body([]),
    template_id: list = Body([]),
    program_name: list = Body([]),
    page_num: int = 1,
    page_size: int = 7,
    search: str = None,
    download: bool = False,
    college: dict = Depends(get_college_id_short_version(short_version=True)),

):
    """
        Retrieves detailed communication records for students based on various filters and pagination settings.

        Params:
            date (str): The specific date for filtering communication details.
                        Example: "YYYY-MM-DD".
            communication_type (CommunicationType): The type of communication to analyze.
                                                    Example: "email", "SMS", or "notification".
            user_id (list): Optional. A list of user IDs to filter the communication details.
                            Example: ["user1", "user2"]. Defaults to an empty list.
            data_segment_id (list): Optional. A list of data segment IDs to filter the communication details.
                                    Example: ["segment1", "segment2"]. Defaults to an empty list.
            template_id (list): Optional. A list of template IDs to filter the communication details.
                                Example: ["template1", "template2"]. Defaults to an empty list.
            program_name (list): Optional. A list of program names to filter the communication details.
                                 Example: ["Program A", "Program B"]. Defaults to an empty list.
            current_user (User): The current authenticated user extracted via dependency injection.
            page_num (int): The page number for pagination.
                            Defaults to 1.
            page_size (int): The number of records to return per page.
                             Defaults to 7.
            college (dict): Information about the college context, derived from a dependency function.

        Returns:
            dict: A paginated response containing filtered student communication details, with metadata such as total records, current page, and page size.

        Raises:
            HTTPException: If authentication fails, required parameters are invalid, or no data is found for the provided filters.
    """
    user = await UserHelper().check_user_has_permission(current_user, [
        "college_admin",
        "college_super_admin",
        "super_admin",
        "college_counselor",
        "college_head_counselor"
    ], False)
    try:
        communication_type = communication_type.value
        data, total_count = await communication_performance_obj.get_student_communication_details(
            date, communication_type, user_id, data_segment_id, template_id, program_name, page_num, page_size, search,
            download, await communication_performance_obj.counselor_ids(user, college.get('id')))
        if download:
            if data:
                data_keys = list(data[0].keys())
                get_url = await upload_csv_and_get_public_url(
                    fieldnames=data_keys,
                    data=data,
                    name="utm",
                )
                background_tasks.add_task(
                    DownloadRequestActivity().store_download_request_activity,
                    request_type="Communication_data",
                    requested_at=datetime.datetime.utcnow(),
                    ip_address=utility_obj.get_ip_address(request),
                    user=await UserHelper().check_user_has_permission(
                        user_name=current_user),
                    total_request_data=total_count,
                    is_status_completed=True,
                    request_completed_at=datetime.datetime.utcnow(),
                )
                return get_url
            else:
                return {"message": "No data found"}
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, total_count, "/communication_performance/get_student_communication_details")

        return {
            "data": data,
            "total": total_count,
            "count": page_size,
            "pagination": response.get("pagination"),
            'message': 'Get communication data'
        }
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the communication summary dashboard student details. Error: {error}.",
        )
