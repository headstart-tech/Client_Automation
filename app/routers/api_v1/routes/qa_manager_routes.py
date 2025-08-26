"""
This file contains API routes related to QA and QA Manager
"""
from typing import Union
from app.core.log_config import get_logger
from fastapi import APIRouter, Depends, Query, Body
from fastapi.exceptions import HTTPException
from app.core.utils import utility_obj, requires_feature_permission
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import CurrentUser
from app.models.student_user_schema import User
from app.helpers.qa_manager_helper.counsellor_reviews import CounsellorReview
from app.helpers.qa_manager_helper.calls_list import CallsListReview
from app.helpers.qa_manager_helper.qa_reviews import QAReview
from app.helpers.qa_manager_helper.qc_details import QCReviewDetails
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.applications import DateRange
from app.models.qc_manager_schema import CallReview, QAList, CounsellorList, QCStatusList
from fastapi.encoders import jsonable_encoder
from app.helpers.qa_manager_helper.review_config import ReviewQuery
from app.core.custom_error import CustomError, ObjectIdInValid
from app.core.log_config import get_logger
from app.dependencies.oauth import cache_dependency, insert_data_in_cache

qa_manager_router = APIRouter()
logger = get_logger(name=__name__)


@qa_manager_router.post(
    "/counsellor/", summary="Get counsellors call quality according to the reviews."
)
@requires_feature_permission("read")
async def get_counsellor_details(
    current_user: CurrentUser,
    page_num: Union[int, None] = Query(None, gt=0),
    page_size: Union[int, None] = Query(None, gt=0),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    date_range: DateRange = Body(None)
) -> dict:
    """
    API for get the list of all counsellors with there reviews for Counsellor head and qa manager.

    Args:
        current_user (User, optional): Requested user for validate the authorization of data access. Defaults to Depends(get_current_user).
        page_num (Union[int, None], optional): Page no data. Defaults to Query(None, gt=0).
        page_size (Union[int, None], optional): No. of data in one page. Defaults to Query(None, gt=0).
        college (dict, optional): College id for validation of college. Defaults to Depends(get_college_id).
        date_range (DateRange, optional): start_date: "%Y-%m-%d" and end_date: "%Y-%m-%d" both field are optional but in case of null it returns all the data count. Defaults to Body(None).

    Returns:
        - dict: A dictionary which contains counselors review count information.

    Raises:
        - 401 (Not enough permissions): An error occurred when user don't have permission to get counselors review count information.
        - 404 (Not found): An error occurred when counselors data not found.
    """
    
    # Validation of user role - Only "head_qa", "college_head_counselor" and "college_super_admin" can access the data.
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") not in ["head_qa", "college_head_counselor", "college_super_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    
    date_range = await utility_obj.format_date_range(date_range)
    counsellors = await CounsellorReview().retrieve_counsellors(
        college.get("id"), page_num, page_size, date_range, route_name="/qa_manager/counsellor/"
    )

    if counsellors:
        if page_num and page_size:
            return counsellors
        return utility_obj.response_model(counsellors, "Counsellors data fetched successfully.")

    raise HTTPException(status_code=404, detail="No any counselor data exist.")


@qa_manager_router.post(
    "/qa/", summary="Get qa's reviews performance list."
)
@requires_feature_permission("read")
async def get_qa_details(
    current_user: CurrentUser,
    page_num: Union[int, None] = Query(None, gt=0),
    page_size: Union[int, None] = Query(None, gt=0),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    date_range: DateRange = Body(None)
) -> dict:
    """
    API for get the list of all qa with there reviews for Counsellors shown only to qa manager.

    Args:
        current_user (User, optional): Requested user for validate the authorization of data access. Defaults to Depends(get_current_user).
        page_num (Union[int, None], optional): Page no data. Defaults to Query(None, gt=0).
        page_size (Union[int, None], optional): No. of data in one page. Defaults to Query(None, gt=0).
        college (dict, optional): College id for validation of college. Defaults to Depends(get_college_id).
        date_range (DateRange, optional): start_date: "%Y-%m-%d" and end_date: "%Y-%m-%d" both field are optional but in case of null it returns all the data count. Defaults to Body(None).

    Returns:
        - dict: A dictionary which contains counselors review count information.

    Raises:
        - 401 (Not enough permissions): An error occurred when user don't have permission to get counselors review count information.
        - 404 (Not found): An error occurred when counselors data not found.

    """
    
    # Validation of user role - Only "head_qa" and "college_super_admin" can access the data.
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") not in ["head_qa", "college_super_admin", "college_admin", "super_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    
    date_range = await utility_obj.format_date_range(date_range)
    qas = await QAReview().retrieve_qa(
        page_num, page_size, date_range, route_name="/qa_manager/qa/"
    )

    if qas:
        if page_num and page_size:
            return qas
        return utility_obj.response_model(qas, "QA data fetched successfully.")

    raise HTTPException(status_code=404, detail="No any QA exist.")


@qa_manager_router.post(
    "/call_list_metrics/", summary="Get QC overview data."
)
@requires_feature_permission("read")
async def call_list_metrics(
    current_user: CurrentUser,
    cache_data = Depends(cache_dependency),
    qa_id: str|None = None,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    date_range: DateRange = Body(None)
) -> dict:
    """
    Get the data of all the matrix of header which is related to QC.

    Params:
        current_user (User, optional): Current logged in user (only QA, QA manager or College Super Admin). Defaults to Depends(get_current_user).
        cache_data (Cache): It is for the in memory data things which I retrive automatically from browser to improve there speed of request.
        qa_id (str): Pass 
        college (dict, optional): College ID validation for the current user college source. Defaults to Depends(get_college_id).
        date_range (DateRange, optional): start_date: "%Y-%m-%d" and end_date: "%Y-%m-%d" both field are optional but in case of null it returns all the data count. Defaults to Body(None).

    Returns:
        dict: Data set in the format of json.

    Raise:
        401 (Not enough permissions): An error occurred with status code 401 when user don't have permission to get call summary count data.
    """

    # Validation of user role - Only "head_qa" and "college_super_admin" can access the data.
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") not in ["head_qa", "college_head_counselor", "qa",  "college_super_admin", "college_admin", "super_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    
    cache_key, data = cache_data
    if data:
        return data

    date_range = await utility_obj.format_date_range(date_range)
    
    qc_details = await QCReviewDetails().retrieve_qc_details(date_range, qa_id)

    data = utility_obj.response_model(qc_details, "Call List Header Data Fetch Successfully")

    if cache_key:
        await insert_data_in_cache(cache_key, data, expiration_time=30)

    return data


@qa_manager_router.post(
    "/rejected_call_list_metrics/", summary="Get Rejected Call QC overview data."
)
@requires_feature_permission("read")
async def rejected_call_list_metrics(
    current_user: CurrentUser,
    cache_data = Depends(cache_dependency),
    counsellor_id: str|None = None,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    date_range: DateRange = Body(None)
) -> dict:
    """
    Get the data of all the matrix of header which is related to QC.

    Args:
        current_user (User, optional): Current logged in user (only QA, QA manager or College Super Admin). Defaults to Depends(get_current_user).
        cache_data (Cache): It is for the in memory data things which I retrive automatically from browser to improve there speed of request.
        college (dict, optional): College ID validation for the current user college source. Defaults to Depends(get_college_id).
        date_range (DateRange, optional): start_date: "%Y-%m-%d" and end_date: "%Y-%m-%d" both field are optional but in case of null it returns all the data count. Defaults to Body(None).

    Returns:
        dict: Data set in the format of json.
    
    Raise:
        401 (Not enough permissions): An error occurred with status code 401 when user don't have permission to get call summary count data.

    """

    # Validation of user role - Only "head_qa" and "college_super_admin" can access the data.
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") not in ["head_qa", "college_head_counselor", "qa",  "college_super_admin", "college_admin", "super_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    
    cache_key, data = cache_data
    if data:
        return data
    
    date_range = await utility_obj.format_date_range(date_range)
    
    rejected_qc_details = await QCReviewDetails().retrieve_rejected_qc_details(date_range, counsellor_id)

    data = utility_obj.response_model(rejected_qc_details, "Rejected Call List Header Data Fetch Successfully")

    if cache_key:
        await insert_data_in_cache(cache_key, data, expiration_time=30)

    return data


@qa_manager_router.post("/call_list/", summary="Get all calls for review")
@requires_feature_permission("read")
async def get_all_calls(
        current_user: CurrentUser,
        page_num: int = 1,
        page_size: int = 10,
        qa: QAList = Body(None),
        counsellor: CounsellorList = Body(None),
        call_type: str|None = None,
        qc_status: QCStatusList = Body(None),
        qc_date_range: DateRange = Body(None),
        call_date_range: DateRange = Body(None),
        cache_data = Depends(cache_dependency),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get the data of all calls of counsellors which will have to review or reviewed.

    Params:
        - page_num (int, optional): Page no which data has to be fetched. Defaults to 1.
        - page_size (int, optional): No. of data in one page. Defaults to 10.
        - qa (str | None, optional): QA for filtering the calls. Defaults to None.
        - counsellor (str | None, optional): Counsellor unique id for filteration of calls as per counsellor. Defaults to None.
        - call_type (str | None, optional): It must be "Outbound" or "Inbound". Defaults to None.
        - qc_status (str | None, optional): It must be 'Accepted', 'Rejected', 'Fatal Rejected' or 'Not QCed'. Defaults to None.
        - qc_date_range (DateRange, optional): start_date -> 'YYYY-mm-dd' or end_date -> 'YYYY-mm-dd'. Defaults to Body(None).
        - call_date_range (DateRange, optional): start_date -> 'YYYY-mm-dd' or end_date -> 'YYYY-mm-dd'. Defaults to Body(None).
        - current_user (User, optional): User must be "head_qa", "qa" or "college_super_admin". Defaults to Depends(get_current_user).
        - cache_data (_type_, optional): For improve performance. Defaults to Depends(cache_dependency).
        - college (dict, optional): Unique id of college which has to be requested for validation. Defaults to Depends(get_college_id).

    Returns:
        - dict: Data set in the format of json.
    
    Raise:
        - 401 (Not enough permissions): An error occurred with status code 401 when user don't have permission to get call summary count data.
        - Exception: An error occurred with status code 500 when something wrong happen in the code.
    """

    # Validation of user role - Only "QA", "head_qa" and "college_super_admin" can access the data.
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") not in ["head_qa", "qa",  "college_super_admin", "college_head_counselor"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")

    try:
        cache_key, data = cache_data
        if data:
            return data
        
        qc_date_range_dict = await utility_obj.format_date_range(qc_date_range)
        call_date_range_dict = await utility_obj.format_date_range(call_date_range)
        qa_dict = await utility_obj.format_filter_list(qa)
        counsellor_dict = await utility_obj.format_filter_list(counsellor)
        qc_status_dict = await utility_obj.format_filter_list(qc_status)

        data = await CallsListReview().retrieve_call_list(qc_date_range_dict, call_date_range_dict, qa_dict, counsellor_dict, call_type, qc_status_dict)

        response = await utility_obj.pagination_in_api(page_num, page_size, data, len(data),
                                            route_name="/qa_manager/call_list/")
        
        data = {
            "data": response["data"],
            "total": len(data),
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Get the calls.",
        }

        if cache_key:
            await insert_data_in_cache(cache_key, data, expiration_time=30)

        return data
    
    except Exception as error:
        logger.error(f"An error got when get calls. Error - {error}")


@qa_manager_router.post(
    "/call_review/", summary="Call QC review for QA in QA Module"
)
@requires_feature_permission("write")
async def call_review(
    current_user: CurrentUser,
    call_review_data: CallReview,
    call_id: str = Query(description="A unique id/identifier of call. e.g., 123456789012345678901241"),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
) -> dict:
    """
    Add a call review.

    Params:
        - call_id (str): An unique id/identifier of a call which helpful for add call review of a particular call. 
        - college_id (str): An unique id/identifier of a college.

    Request body params:\n
    - qc_status (str): Review status of a call. Possible values: 'pass', 'fail' and 'fatal'.
        product_knowledge (int): A integer value which represents product_knowledge score value for call.
        call_starting (int): A integer value which represents call_starting score value for call.
        call_closing (int): A integer value which represents call_closing score value for call.
        issue_handling (int): A integer value which represents issue_handling score value for call.
        engagement (int): A integer value which represents engagement score value for call.
        call_quality_score (int): A integer value which represents call_quality_score value for call.
        remarks (str | None). Default value: None. Either None or a string value which represents remarks for call.

    Returns:
        - dict: A dictionary which contains information about add a call review.

    Raises:
        ObjectIdInValid: An error occurred when call_id not valid.
        CustomError: An error occurred when call activity not found or score value invalid..
        Exception: An error occurred when something wrong happen in the backend code.
    """
    
    # Validation of user role - Only "head_qa", "qa" and "college_super_admin" can add the review.
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") not in ["head_qa", "qa",  "college_super_admin", "college_admin", "super_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    
    call_review_data = jsonable_encoder(call_review_data)
    try:
        return await ReviewQuery().create_review(
            call_review_data, user, call_id)
    
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    
    except Exception as error:
        logger.error(f"An error got when create a review. Error - {error}")
        raise HTTPException(status_code=500, detail=f"Error - {error}")
