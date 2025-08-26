"""
This file contains API routes related to publisher
"""

import csv
import json
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    Path,
    Query,
    UploadFile,
    Request,
)
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from fastapi.param_functions import File
from kombu.exceptions import KombuError

from app.celery_tasks.celery_publisher_upload_leads import PublisherActivity
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings, requires_feature_permission
from app.database.aggregation.get_all_applications import Application
from app.database.aggregation.publisher import Publisher
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id
from app.dependencies.oauth import (
    CurrentUser,
    cache_dependency,
    insert_data_in_cache,
    cache_invalidation
)
from app.helpers.college_configuration import CollegeHelper
from app.helpers.student_curd.student_user_crud_configuration import (
    StudentUserCrudHelper,
)
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.publisher_schema import AddStudent
from app.models.student_user_schema import User, payload_data, DateRange, \
    ChangeIndicator
from app.core.custom_error import CustomError, ObjectIdInValid

logger = get_logger(name=__name__)
publisher_router = APIRouter()


@publisher_router.post(
    "/add_leads_using_json_or_csv/{college_id}/",
    summary="Add leads using json file"
)
@requires_feature_permission("write")
async def add_leads_using_json_or_csv(
        current_user: CurrentUser,
        request: Request,
        college_id: str = Path(..., description="Enter college id"),
        file: UploadFile = File(...),
):
    """
    Add leads using json file\n
    * :*param* **college_id** e.g., e.g. 624e8d6a92cc415f1f578a24:\n
    * :*return* **Message - Leads Added**:
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        college = await DatabaseConfiguration().college_collection.find_one(
            {"_id": ObjectId(college_id)}
        )
    except InvalidId:
        raise HTTPException(
            status_code=422,
            detail="Invalid college id.",
        )
    except Exception as e:
        logger.error("Some error occurred. ", e)
        raise HTTPException(
            status_code=422,
            detail="College id must be a 12-byte input or a 24-character hex string.",
        )
    if not college:
        raise HTTPException(status_code=404, detail=f"College not found.")
    college = CollegeHelper().college_helper(college)
    if college_id not in [str(i) for i in user.get("associated_colleges", [])]:
        raise HTTPException(status_code=401, detail="Not enough permission because you are not associated with college.")
    filename = file.filename
    file_format = utility_obj.is_valid_extension(filename)
    if not file_format:
        raise HTTPException(status_code=422,
                            detail="file format is not supported")
    file_copy = await utility_obj.temporary_path(file)
    if filename.endswith(".json"):
        with open(file_copy.name) as f:
            try:
                data = json.load(f)
            except Exception as e:
                logger.error("Some error occurred. ", e)
                data = None
    else:
        with open(file_copy.name) as f:
            reader = csv.reader(f, delimiter=",")
            line_count = 0
            data_list = []
            for row in reader:
                if line_count == 0:
                    line_count += 1
                else:
                    full_name = row[0]
                    email = row[1]
                    mobile_number = row[2]
                    course = row[3]
                    main_specialization = row[4]
                    country_code = row[5]
                    state_code = row[6]
                    city = row[7]
                    try:
                        utm_campaign = row[8]
                    except Exception as e:
                        logger.error("Some error occurred", e)
                        utm_campaign = None
                    try:
                        utm_keyword = row[9]
                    except Exception as e:
                        logger.error("Some error occurred", e)
                        utm_keyword = None
                    try:
                        utm_medium = row[10]
                    except Exception as e:
                        logger.error("Some error occurred", e)
                        utm_medium = None
                    try:
                        referal_url = row[11]
                    except Exception as e:
                        logger.error("Some error occurred", e)
                        referal_url = None
                    line_count += 1
                    student_data = {
                        "full_name": full_name,
                        "email": email,
                        "course": course,
                        "mobile_number": mobile_number,
                        "main_specialization": main_specialization,
                        "country_code": country_code,
                        "state_code": state_code,
                        "city": city,
                        "utm_source": user.get("associated_source_value"),
                        "utm_campaign": utm_campaign,
                        "utm_keyword": utm_keyword,
                        "utm_medium": utm_medium,
                        "referal_url": referal_url,
                    }
                    data_list.append(student_data)
            if data_list:
                data = {"student_details": data_list}
            else:
                data = None
    if data:
        uploaded_leads_count = await Publisher().get_uploaded_leads_count(
            user.get("_id")
        )
        data_length = len(data.get("student_details", []))
        user_details = await DatabaseConfiguration().user_collection.find_one({"_id": ObjectId(user.get("_id"))})
        bulk_lead_push_limit = user_details.get("bulk_lead_push_limit", settings.publisher_bulk_lead_push_limit)
        if uploaded_leads_count+data_length >= bulk_lead_push_limit.get("daily_limit", 0):
            logger.error("Reached maximum limit of per day for upload leads")
            raise HTTPException(
                status_code=422,
                detail="You have reached maximum limit of per day for upload leads.",
            )
        elif data_length >= bulk_lead_push_limit.get("bulk_limit", 0):
            logger.error("Reached maximum limit of bulk upload leads")
            raise HTTPException(
                status_code=422,
                detail="You have reached maximum limit of bulk upload leads.",
            )
        elif len(data.get("student_details", [])) == 0:
            logger.error("Student details not found.")
            raise HTTPException(status_code=422,
                                detail="Student details not found.")

        ip_address = utility_obj.get_ip_address(request)
        try:
            toml_data = utility_obj.read_current_toml_file()
            if toml_data.get("testing", {}).get("test") is False:
                PublisherActivity().process_uploaded_loads.delay(
                    user=user,
                    data=data,
                    filename=filename,
                    college=college,
                    ip_address=ip_address,
                    college_id=college_id,
                )
        except KombuError as celery_error:
            logger.error(f"error add student by publisher {celery_error}")
        except Exception as error:
            logger.error(f"error add student by publisher {error}")
        await cache_invalidation(api_updated="publisher/add_leads_using_json_or_csv")
        return {
            "message": "Received Request will be processed in the background once finished you will receive an "
                       "email. Data processing might take anywhere between 2 min - 1 hour depending on the data "
                       "volume."
        }
    else:
        raise HTTPException(status_code=404, detail="File is empty.")


@publisher_router.post(
    "/get_all_leads/",
    summary="Get all leads of publisher based on publisher associated source value"
)
@requires_feature_permission("read")
async def get_all_leads(
        current_user: CurrentUser,
        source_type: str | None = None,
        lead_type: str | None = None,
        payment_status: list[str] | None = None,
        form_status: str | None = None,
        date_range: DateRange | None = Body(None),
        page_num: int = 1,
        page_size: int = 25,
        cache_data=Depends(cache_dependency),
        college: dict = Depends(get_college_id)
) -> dict:
    """\nGet All Application Details Created by Publisher Based on Publisher Associated Source Value\n

    Body Params:\n
        * payment_status (list[str] | None, optional): Payment status can be any of the following: not started, started, captured, failed and refunded', example='failed'. Defaults to None.
        * date_range (DateRange | None, optional): Date range which data has to be filter. Defaults to Body(None).

    Params:\n
        * source_type (str | None, optional): Filter data accoring to the soruce existance - It should be 'primary', 'secondary' or 'tertiary'. Defaults to None.
        * lead_type (str | None, optional): Filter data particularly as lead creates with Api or Online ('api', 'online')
        * form_status (str | None, optional): Filter application according to form status - "incomplete", "initiated" or "complete". Defaults to None - It shows all type of data.
        * page_num (int, optional): Current page no. Defaults to Query(gt=0).
        * page_size (int, optional): No of data in one page. Defaults to Query(gt=0).
        * college (dict, optional): College unique id - 'college_id'. Defaults to Depends(get_college_id).

    Raises:\n
        CustomError: Raise when any parameter data is missing or invalid
        HTTPException: Raise when the systax error raised or database data missmatch

    Returns:\n
        dict: Set of applications data
    """
    cache_key, data = cache_data
    if data:
        return data

    try:
        date_range = await utility_obj.format_date_range(date_range)
        if (
                user := await DatabaseConfiguration().user_collection.find_one(
                    {"user_name": current_user.get("user_name")}
                )
        ) is None or user.get("role", {}).get("role_name",
                                              "") != "college_publisher_console":
            raise CustomError("permission denied")

        if source_type and source_type not in ['primary', 'secondary',
                                               'tertiary']:
            raise CustomError(
                "source_type value must be any of the following: primary, secondary and tertiary.")

        if lead_type and lead_type not in ['online', 'api']:
            raise CustomError(
                "lead_type value must be any of the following: online and api.")

        if payment_status:
            for status in payment_status:
                if status not in ['not started', 'started', 'captured',
                                  'failed', 'refunded']:
                    raise CustomError(
                        "Possible values of payment_status will be: not started, started, captured, failed and refunded")

        if form_status and form_status not in ['complete', 'incomplete',
                                               'initiated']:
            raise CustomError(
                "Possible values of form_status will be: complete, incomplete and initiate.")

        all_applicants_data, total_data = await Application().get_all_applications_by_utm_source(
            source_type=source_type,
            lead_type=lead_type,
            payment_status=payment_status,
            form_status=form_status,
            date_range=date_range,
            utm_source=(
                user.get("associated_source_value").lower()
                if user.get("associated_source_value") is not None
                else ""
            ),
            page_num=page_num,
            page_size=page_size
        )
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, total_data,
            route_name="/publisher/get_all_leads/"
        )
        data = {
            "data": all_applicants_data,
            "total": total_data,
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Applications data fetched successfully!",
        }

        if cache_key:
            await insert_data_in_cache(cache_key, data)

        return data

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the call activity dashboard data. Error: {error}.",
        )


@publisher_router.post("/add_student/")
@requires_feature_permission("write")
async def add_student(
        request: Request,
        add_data: AddStudent,
        background_tasks: BackgroundTasks,
        current_user: CurrentUser,
):
    """
    Add student data\n
    * :*param* **source_type** e.g., secondary/tertiary Dow:\n
    * :*param* **application_detail** e.g., true/false:\n
    * :*param* **full_name** e.g., John Michel Dow:\n
    * :*param* **email** e.g., john@example.com:\n
    * :*param* **mobile_number** e.g., 1234567890:\n
    * :*param* **country_code** e.g., IN:\n
    * :*param* **state_code** e.g., UP:\n
    * :*param* **city** e.g., Mathura:\n
    * :*param* **course** e.g., Bsc:\n
    * :*param* **main_specialization** e.g., Medical Lab Technology:\n
    * :*param* **college_id** e.g., 123456789012345678901234:\n
    * :*return* **Message - Student added Successfully.**:
    """
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    add_data = jsonable_encoder(add_data)
    add_data["utm_source"] = user.get("associated_source_value")
    if add_data.get("college_id") not in [str(i) for i in user.get("associated_colleges", [])]:
        raise HTTPException(status_code=401, detail="Not enough permission because you are not associated with college.")
    st_reg = await StudentUserCrudHelper().student_register(
        add_data,
        publisher_id=str(user.get("_id")),
        lead_type="api",
        request=request,
        background_tasks=background_tasks,
        is_created_by_publisher=True
    )
    if st_reg:
        await cache_invalidation(
            api_updated="publisher/add_student")
        return {
            "data": {
                "student_id": st_reg.get("id"),
                "student_username": st_reg.get("data", {}).get("user_name"),
            },
            "message": "Student added.",
        }


@publisher_router.post("/get_publisher_percentage_data")
@requires_feature_permission("read")
async def get_publisher_leads_percentage_source(
        current_user: CurrentUser,
        date_range: DateRange | None = Body(None),
        change_indicator: ChangeIndicator = "last_7_days",
        college: dict = Depends(get_college_id)
) -> dict:
    """API for publisher dashboard header section

    Params:
        date_range (DateRange | None, optional): Date range filter (start_date and end_date). Defaults to Body(None).
        change_indicator (ChangeIndicator, optional): Change indicator filter. Defaults to "last_7_days".
        current_user (User, optional): Current requested user (It should be publisher only). Defaults to Depends(get_current_user).
        college (dict, optional): College unique id. Defaults to Depends(get_college_id).

    Returns:
        json: Response json with data and message.
    """
    if (
            user := await DatabaseConfiguration().user_collection.find_one(
                {"user_name": current_user.get("user_name"),
                 "role.role_name": "college_publisher_console"}
            )
    ) is None:
        raise HTTPException(status_code=401, detail="Not enough permissions")
    date_range = await utility_obj.format_date_range(date_range)
    source_name = user.get("associated_source_value", "").lower()
    try:
        response = await Publisher().leads_count_based_on_publisher(
            source_name=source_name, date_range=date_range,
            change_indicator=change_indicator
        )
        return utility_obj.response_model(
            data=response, message="fetch all count of sources successfully"
        )

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the lead application count header data. Error: {error}.",
        )


@publisher_router.get("/get_publisher_leads_count_by_source_for_graph")
@requires_feature_permission("read")
async def get_publisher_leads_source(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
):
    """
    get publisher leads source
    """
    if (
            user := await DatabaseConfiguration().user_collection.find_one(
                {"user_name": current_user.get("user_name"),
                 "role.role_name": "college_publisher_console"}
            )
    ) is None:
        raise HTTPException(status_code=401, detail="Not enough permissions")
    leads_count = await Publisher().leads_count_based_on_publisher_source(
        user=user)
    return utility_obj.response_model(
        data=leads_count, message="fetch all count of sources successfully"
    )
