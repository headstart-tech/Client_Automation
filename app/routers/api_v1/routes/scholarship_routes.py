"""
This file contains API routes/endpoints related to scholarship.
"""
from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks, Query
from app.core.log_config import get_logger
from app.core.utils import requires_feature_permission
from app.models.scholarship_schema import (CreateScholarship, ActivationStatus, FilterParameters, CustomScholarship,
                                           ScholarshipDataType, SendLetterInfo, ChangeDefaultScholarship, WaiverType)
from app.dependencies.oauth import Is_testing, CurrentUser, insert_data_in_cache, cache_dependency
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.helpers.user_curd.user_configuration import UserHelper
from app.helpers.scholarship_configuration import Scholarship
from app.core.reset_credentials import Reset_the_settings
from app.core.custom_error import CustomError, DataNotFoundError, ObjectIdInValid
from app.database.aggregation.scholarship import ScholarshipAggregation

logger = get_logger(__name__)
scholarship_router = APIRouter()


@scholarship_router.post("/create/")
@requires_feature_permission("write")
async def create_scholarship(
        testing: Is_testing,
        request: Request,
        current_user: CurrentUser,
        scholarship_information: CreateScholarship,
        college: dict = Depends(get_college_id),
        ):
    """
    Create a Scholarship.

    Params:
    * **college_id** (str): Unique identifier of college. e.g., 123456789012345678901234

    Request body params:
    * **scholarship_information** (dict): Request body containing details of scholarship.
        The dictionary which contains following fields:
        - name (str): Name of scholarship.
        - copy_scholarship_id (str | None): Optional field. Unique identifier of existing scholarship.
            Required when copy existing scholarship information.
        - programs (list): A list which contains object (s). An object will contain following fields:
            - course_id (str): Unique identifier of course. e.g., 123456789012345678901231
            - course_name (str): Name of course. e.g., B.Sc.
            - specialization_name (str | None): Name of specialization. e.g., Physician Assistant
        - count (int): Number of scholarships which need to be offered.
        - waiver_type (str): Type of scholarship waiver. Possible values are Percentage and Amount.
        - waiver_value (float): Percentage/Amount of waiver.
        - template_id (str | None): Optional field. Unique identifier of template. e.g., 123456789012345678901232
        - status (str): A string value which represents the status of the scholarship. Possible values are Active and Closed.
        - filters (dict | None): Optional field. A dictionary which contains normal filters information.
        - advance_filters (list): Optional field. A list which contains information about advance filter fields.

    Returns:
    * dict: A dictionary which contains information about create scholarship.

    Raises:
    * HTTPException:
        An error occurred with status code 400 when validation of input failed.
        An error occurred with status code 404 when course/template not found by course_id/template_id.
        An error with status code 500 when something wrong happened in the code.
    """
    user = await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"], condition=False)
    try:
        college_id = college.get("id")
        if not testing:
            Reset_the_settings().check_college_mapped(college_id)
        return await Scholarship().create_scholarship(
            request, scholarship_information.model_dump(), user, college_id)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Something wrong happened in the code. Error:{error}")


@scholarship_router.post('/programs_fee_and_eligible_count_info/')
@requires_feature_permission("read")
async def programs_fee_and_eligible_count_info(
        current_user: CurrentUser,
        testing: Is_testing,
        scholarship_information: CreateScholarship,
        college: dict = Depends(get_college_id)):
    """
    Get programs fee and eligible count information based on scholarship information.

    Params:
    * **college_id** (str): Unique identifier of college. e.g., 123456789012345678901234
    * **scholarship_name** (str): Name of scholarship.

    Request body params:
    * **scholarship_information** (dict): Request body containing details of scholarship.
        The dictionary which contains following fields:
        - name (str): Name of scholarship.
        - copy_scholarship_id (str | None): Optional field. Unique identifier of existing scholarship.
            Required when copy existing scholarship information.
        - programs (list): A list which contains object (s). An object will contain following fields:
            - course_id (str): Unique identifier of course. e.g., 123456789012345678901231
            - course_name (str): Name of course. e.g., B.Sc.
            - specialization_name (str | None): Name of specialization. e.g., Physician Assistant
        - count (int): Number of scholarships which need to be offered.
        - waiver_type (str): Type of scholarship waiver. Possible values are Percentage and Amount.
        - waiver_value (float): Percentage/Amount of waiver.
        - template_id (str | None): Optional field. Unique identifier of template. e.g., 123456789012345678901232
        - status (str): A string value which represents the status of the scholarship. Possible values are Active and Closed.
        - filters (dict | None): Optional field. A dictionary which contains normal filters information.
        - advance_filters (list): Optional field. A list which contains information about advance filter fields.

    Returns:
    * dict: A dictionary which contains information about programs fee and eligible count.

    Raises:
    * HTTPException:
        An error occurred with status code 400 when validation of input failed.
        An error occurred with status code 404 when course/template not found by course_id/template_id.
        An error occurred with status code 500 when something wrong happened in the code.
    """
    await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"], condition=False)
    try:
        college_id = college.get("id")
        if not testing:
            Reset_the_settings().check_college_mapped(college_id)
        return await Scholarship().get_programs_fee_and_eligible_count_info(
            scholarship_information.model_dump(), college_id)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Something wrong happened in the code. Error:{error}")


@scholarship_router.put('/update_status/')
@requires_feature_permission("edit")
async def update_scholarship_status(
        current_user: CurrentUser,
        testing: Is_testing,
        status: ActivationStatus,
        scholarship_id: str = Query(description="Enter scholarship id"),
        college: dict = Depends(get_college_id)):
    """
    Update scholarship status.

    Params:
    * **college_id** (str): Unique identifier of college. e.g., 123456789012345678901234
    * **scholarship_id** (str): Unique identifier of scholarship.
    * **status** (str): A string value which represents the status of the scholarship.
        Possible values are Active and Closed.

    Returns:
    * dict: A dictionary which contains information about update scholarship status.

    Raises:
    * HTTPException:
        An error occurred with status code 422 when scholarship id is invalid.
        An error occurred with status code 404 when scholarship not found.
        An error occurred with status code 400 when validation of input failed.
        An error with status code 500 when something wrong happened in the code.
    """
    await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"], condition=False)
    try:
        if not testing:
            Reset_the_settings().check_college_mapped(college.get("id"))
        return await Scholarship().update_scholarship_status(scholarship_id, status)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Something wrong happened in the code. Error:{error}")


@scholarship_router.get('s/get_information/')
@requires_feature_permission("read")
async def get_scholarships_information(
        current_user: CurrentUser,
        testing: Is_testing,
        college: dict = Depends(get_college_id),
        scholarship_id: str | None = Query(None, description="Enter scholarship id"),
):
    """
    Get scholarships information.

    Params:
    * **college_id** (str): Unique identifier of college. e.g., 123456789012345678901234
    * **scholarship_id** (str | None): Optional field. Default value: None.
        Unique identifier of scholarship.

    Returns:
    * dict: A dictionary which contains information about scholarships.

    Raises:
    * HTTPException:
        An error occurred with status code 400 when validation of input failed.
        An error occurred with status code 422 when scholarship id is invalid.
        An error occurred with status code 500 when something wrong happened in the code.
    """
    await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"], condition=False)
    try:
        if not testing:
            Reset_the_settings().check_college_mapped(college.get("id"))
        return {"data": await ScholarshipAggregation().get_scholarship_information(scholarship_id),
                "message": "Get scholarships information."}
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Something wrong happened in the code. Error:{error}")


@scholarship_router.post('/table_information/')
@requires_feature_permission("read")
async def get_scholarship_table_information(
        current_user: CurrentUser,
        testing: Is_testing,
        college: dict = Depends(get_college_id),
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0),
        filter_parameters: FilterParameters | None = None,
):
    """
    Get scholarship table information like scholarship name along program names, count, eligible count, offered count,
        availed_by count, available count, availed_amount.


    Params:
    * **college_id** (str): Unique identifier of college. e.g., 123456789012345678901234
    * **page_num** (int): Enter page number where want to show scholarship table data.
    * **page_size** (int): Enter page size means how many data want to show on page_num.

    Request body Params:
    * **filter_parameters** (dict | None): Optional field.
        A dictionary which contains following fields:
        - search (str | None): Either None or a string which useful for get scholarship table data
            based on scholarship name.
        - sort (str | None): Either None or a string represents column name which useful for sort scholarship table.
        - sort_type (str | None): Either None or a string which represents sort type. Possible values are asc
            (For sort in Ascending order) and dsc (For sort in Descending order).
        - programs (list | None): Optional field, Either None or A list which contains object (s).
            An object will contain following fields:
            - course_id (str): Unique identifier of course. e.g., 123456789012345678901231
            - course_name (str): Name of course. e.g., B.Sc.
            - specialization_name (str | None): Name of specialization. e.g., Physician Assistant

    Returns:
    * dict: A dictionary which contains information about scholarships.

    Raises:
    * HTTPException:
        An error occurred with status code 400 when validation of input failed.
        An error occurred with status code 500 when something wrong happened in the code.
    """
    await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"], condition=False)
    try:
        college_id = college.get("id")
        if not testing:
            Reset_the_settings().check_college_mapped(college_id)
        return await ScholarshipAggregation().get_scholarship_table_information(
            college_id, page_num, page_size, filter_parameters.model_dump() if filter_parameters else {})
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Something wrong happened in the code. Error:{error}")


@scholarship_router.post('/get_summary_data/')
@requires_feature_permission("read")
async def get_scholarship_summary_data(
        current_user: CurrentUser,
        testing: Is_testing,
        college: dict = Depends(get_college_id)
):
    """
    Get scholarship summary information like total scholarship count along with active/closed count,
        total availed count.

    Params:
    * **college_id** (str): Unique identifier of college. e.g., 123456789012345678901234

    Returns:
    * dict: A dictionary which contains information about get scholarship summary data.

    Raises:
    * HTTPException:
        An error occurred with status code 400 when validation of input failed.
        An error occurred with status code 500 when something wrong happened in the code.
    """
    await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"], condition=False)
    try:
        college_id = college.get("id")
        if not testing:
            Reset_the_settings().check_college_mapped(college_id)
        return await ScholarshipAggregation().get_scholarship_summary_info()
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Something wrong happened in the code. Error:{error}")


@scholarship_router.post('/give_custom_scholarship/')
@requires_feature_permission("write")
async def give_custom_scholarship(
        request: Request,
        current_user: CurrentUser,
        testing: Is_testing,
        custom_scholarship_info: CustomScholarship,
        college: dict = Depends(get_college_id),
):
    """
    Give custom scholarship to applicants.

    Params:
    * **college_id** (str): Unique identifier of college. e.g., 123456789012345678901234

    Request body Params:
    * **custom_scholarship_info** (dict | None): A dictionary which contains following fields:
        - application_ids (list[str]): A list which contains application ids.
        - waiver_type (str): Type of custom scholarship waiver. Possible values are Percentage and Amount.
        - waiver_value (float): Percentage/Amount of waiver.
        - template_id (str): Unique identifier of template. e.g., 123456789012345678901232
        - description (str): Optional field. Description of custom scholarship.

    Returns:
    * dict: A dictionary which contains information about give custom scholarship.

    Raises:
    * HTTPException:
        An error occurred with status code 400 when validation of input failed.
        An error occurred with status code 404 when application/template not found by id.
        An error occurred with status code 500 when something wrong happened in the code.
    """
    user = await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"], condition=False)
    try:
        college_id = college.get("id")
        if not testing:
            Reset_the_settings().check_college_mapped(college_id)
        return await Scholarship().give_custom_scholarship(
            testing, request, custom_scholarship_info.model_dump(), user, college_id, college.get("email_preferences", {}))
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Something wrong happened in the code. Error:{error}")


@scholarship_router.post("/get_give_custom_scholarship_table_data/")
@requires_feature_permission("read")
async def get_give_custom_scholarship_table_data(
        current_user: CurrentUser,
        testing: Is_testing,
        cache_data=Depends(cache_dependency),
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0),
        search: str | None = None,
        college: dict = Depends(get_college_id_short_version(short_version=True))
):
    """
    Get give custom scholarship table data.

    Params:
    * **college_id** (str): Unique identifier of college. e.g., 123456789012345678901234
    * **page_num** (int): Enter page number where want to show custom scholarship table data.
    * **page_size** (int): Enter page size means how many data want to show on page_num.
    * **search** (str | None): Either None or a string which useful for get custom scholarship table data
            based on student name.

    Returns:
    * dict: A dictionary which contains information about give custom scholarship table data.

    Raises:
    * HTTPException:
        An error occurred with status code 400 when validation of input failed.
        An error occurred with status code 500 when something wrong happened in the code.
    """
    user = await UserHelper().check_user_has_permission(
        current_user, check_roles=["super_admin", "client_manager", "college_publisher_console"])
    try:
        cache_key, data = cache_data
        if data:
            return data
        college_id = college.get("id")
        if not testing:
            Reset_the_settings().check_college_mapped(college_id)
        scholarships_data = await ScholarshipAggregation().give_custom_scholarship_table_data(
            college_id, user, page_num, page_size, search)
        if cache_key:
            await insert_data_in_cache(cache_key, scholarships_data)
        return scholarships_data
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"An error got when get the give custom scholarship table data. Error - {error}")


@scholarship_router.post('/applicants_data/')
@requires_feature_permission("read")
async def scholarship_applicants_data(
        current_user: CurrentUser,
        testing: Is_testing,
        request: Request,
        background_task: BackgroundTasks,
        scholarship_data_type: ScholarshipDataType,
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0),
        scholarship_id: str = Query(description="Enter scholarship id"),
        download: bool = False,
        filter_parameters: FilterParameters | None = None,
        college: dict = Depends(get_college_id)):
    """
    Get the scholarship applicants data based on scholarship data type.

    Params:
    * **college_id** (str): Unique identifier of college. e.g., 123456789012345678901234
    * **scholarship_id** (str): Unique identifier of scholarship.
    * **scholarship_data_type** (str): A string value which represents the scholarship data type.
        Useful for get particular type of data. Possible values are eligible, availed and offered.
    * **download** (bool): True If want to download the data else false.

    Request body Params:
    * **filter_parameters** (dict | None): Optional field.
        A dictionary which contains following fields:
        - search (str | None): Either None or a string which useful for get scholarship table data
            based on scholarship name.
        - sort (str | None): Either None or a string represents column name which useful for sort scholarship table.
        - sort_type (str | None): Either None or a string which represents sort type. Possible values are asc
            (For sort in Ascending order) and dsc (For sort in Descending order).
        - programs (list | None): Optional field, Either None or A list which contains object (s).
            An object will contain following fields:
            - course_id (str): Unique identifier of course. e.g., 123456789012345678901231
            - course_name (str): Name of course. e.g., B.Sc.
            - specialization_name (str | None): Name of specialization. e.g., Physician Assistant

    Returns:
    * dict: A dictionary which contains information about scholarship applicants data based on data type.

    Raises:
    * HTTPException:
        An error occurred with status code 400 when validation of input failed.
        An error occurred with status code 422 when scholarship id is invalid.
        An error occurred with status code 404 when scholarship not found.
        An error with status code 500 when something wrong happened in the code.
    """
    user = await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"], condition=False)
    try:
        college_id = college.get("id")
        if not testing:
            Reset_the_settings().check_college_mapped(college_id)
        return await ScholarshipAggregation().get_scholarship_applicants_data(
            college_id, scholarship_id, scholarship_data_type, page_num, page_size,
            filter_parameters.model_dump() if filter_parameters else {}, download, background_task, request, user)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Something wrong happened in the code. Error:{error}")


@scholarship_router.post('/send_letter_to_applicants/')
@requires_feature_permission("write")
async def send_scholarship_letter_to_applicants(
        request: Request,
        current_user: CurrentUser,
        testing: Is_testing,
        send_letter_info: SendLetterInfo,
        college: dict = Depends(get_college_id),
):
    """
    Send scholarship letter to applicants.

    Params:
    * **college_id** (str): Unique identifier of college. e.g., 123456789012345678901234

    Request body Params:
    * **send_letter_info** (dict | None): A dictionary which contains following fields:
        - scholarship_id (str): Unique identifier of scholarship. e.g., 123456789012345678901231
        - application_ids (list[str]): A list which contains application ids.
        - template_id (str): Unique identifier of template. e.g., 123456789012345678901232

    Returns:
    * dict: A dictionary which contains information about send scholarship letter.

    Raises:
    * HTTPException:
        An error occurred with status code 400 when validation of input failed.
        An error occurred with status code 404 when scholarship/application/template not found by id.
        An error occurred with status code 500 when something wrong happened in the code.
    """
    user = await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"], condition=False)
    try:
        college_id = college.get("id")
        if not testing:
            Reset_the_settings().check_college_mapped(college_id)
        return await Scholarship().send_scholarship_letter_to_applicants(
            testing, request, send_letter_info.model_dump(), user, college_id, college.get("email_preferences", {}))
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Something wrong happened in the code. Error:{error}")


@scholarship_router.post("/delist_applicants/")
@requires_feature_permission("read")
async def delist_applicants_from_scholarship_list(
        current_user: CurrentUser,
        testing: Is_testing,
        scholarship_id: str,
        application_ids: list[str],
        college: dict = Depends(get_college_id),
):
    """
    De-list applicants from scholarship list.

    Params:
    * **college_id** (str): Unique identifier of college. e.g., 123456789012345678901234
    * **scholarship_id** (str): Unique identifier of scholarship. e.g., 123456789012345678901231

    Request body Params:
    * **application_ids** (list[str]): A list which contains application ids.

    Returns:
    * dict: A dictionary which contains information about de-list applicants from list.

    Raises:
    * HTTPException:
        An error occurred with status code 400 when validation of input failed.
        An error occurred with status code 422 when scholarship id is invalid.
        An error occurred with status code 404 when scholarship not found by id.
        An error occurred with status code 500 when something wrong happened in the code.
    """
    await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"], condition=False)
    try:
        college_id = college.get("id")
        if not testing:
            Reset_the_settings().check_college_mapped(college_id)
        return await Scholarship().delist_applicants_from_scholarship(scholarship_id, application_ids)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Something wrong happened in the code. Error:{error}")


@scholarship_router.post("/change_default_scholarship/")
@requires_feature_permission("edit")
async def change_default_scholarship(
        testing: Is_testing,
        current_user: CurrentUser,
        change_default_scholarship_info: ChangeDefaultScholarship,
        college: dict = Depends(get_college_id),
):
    """
    Change default scholarship of applicant.

    Params:
    * **college_id** (str): Unique identifier of college. e.g., 123456789012345678901234

    Request body Params:
    * **change_default_scholarship_info** (dict): A dictionary which contains following fields:
        - application_id (str): An unique identifier of application.
        - default_scholarship_id (str): Unique identifier of scholarship. e.g., 123456789012345678901231
        - set_custom_scholarship (bool): Optional field. Default value: False.
            Value will be true when admin user want to set custom scholarship as default scholarship.
        - waiver_type (str | None): Optional field. Default value: None.
            Either None or type of custom scholarship waiver.
        - waiver_value (float | None): Optional field. Either None or Percentage/Amount of waiver.
        - description (str | None): Optional field. Either None or description of custom scholarship.

    Returns:
    * dict: A dictionary which contains information about change default scholarship.

    Raises:
    * HTTPException:
        An error occurred with status code 400 when validation of input failed.
        An error occurred with status code 422 when scholarship id is invalid.
        An error occurred with status code 404 when scholarship/application not found by id.
        An error occurred with status code 500 when something wrong happened in the code.
    """
    user = await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"], condition=False)
    try:
        if not testing:
            Reset_the_settings().check_college_mapped(college.get("id"))
        return await Scholarship().change_default_scholarship(change_default_scholarship_info.model_dump(), user)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Something wrong happened in the code. Error:{error}")


@scholarship_router.post("/overview_details/")
@requires_feature_permission("read")
async def get_scholarship_overview_details(
        testing: Is_testing,
        current_user: CurrentUser,
        application_id: str,
        default_scholarship_id: str,
        waiver_type: WaiverType | None = None,
        waiver_value: float | None = Query(None, gt=0),
        college: dict = Depends(get_college_id),
):
    """
    Get the scholarship overview details.

    Params:
    * **college_id** (str): Unique identifier of college. e.g., 123456789012345678901234
    * **application_id** (str): Unique identifier of an application. e.g., 123456789012345678901231
    * **default_scholarship_id** (str): Unique identifier of a scholarship. e.g., 123456789012345678901232
    * **waiver_type** (str | None): Either None or type of waiver, required in case of custom scholarship.
    * **waiver_value** (float | None): Either None or value of waiver, required in case of custom scholarship.

    Returns:
    * dict: A dictionary which contains information about scholarship overview details.

    Raises:
    * HTTPException:
        An error occurred with status code 400 when validation of input failed.
        An error occurred with status code 422 when application id is invalid.
        An error occurred with status code 404 when application not found by id.
        An error occurred with status code 500 when something wrong happened in the code.
    """
    await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"], condition=False)
    try:
        college_id = college.get("id")
        if not testing:
            Reset_the_settings().check_college_mapped(college_id)
        return await Scholarship().get_scholarship_overview_details(
            application_id, default_scholarship_id, waiver_type, waiver_value, college_id)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Something wrong happened in the code. Error:{error}")
