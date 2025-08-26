"""
This file contains API routes/endpoints related to lead/admin_user
"""

from bson import ObjectId
from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from app.background_task.send_mail_configuration import EmailActivity
from app.core.custom_error import DataNotFoundError, ObjectIdInValid
from app.core.log_config import get_logger
from app.core.utils import utility_obj, requires_feature_permission
from app.database.aggregation.admin_user import AdminUser
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import (
    CurrentUser,
    cache_dependency,
    insert_data_in_cache, is_testing_env, change_indicator_cache,
    Is_testing
)
from app.helpers.admin_dashboard.lead_admin import LeadAdmin
from app.helpers.admin_dashboard.lead_user import LeadUser
from app.helpers.admin_dashboard.lead_wrapper_helper import LeadWrapper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.applications import DateRange, lead_filter
from app.models.student_user_schema import (
    ChangeIndicator,
    AddLeadTag,
    DeleteLeadTag,
)
from app.models.template_schema import EmailType
from app.core.reset_credentials import Reset_the_settings

lead = APIRouter()
logger = get_logger(name=__name__)


@lead.get("/lead_profile_header/{application_id}")
@requires_feature_permission("read")
async def lead_profile_header(
    application_id: str,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    season: str = None,
):
    """
    * input student_id must
    * return List of lead profile header data:
    """
    await UserHelper().is_valid_user(current_user, season=season)
    await utility_obj.is_id_length_valid(_id=application_id, name="Application id")
    data = await LeadUser().user_header(application_id, season=season)
    if data:
        return utility_obj.response_model(data=data, message="data fetch successfully")
    raise HTTPException(status_code=404, detail="data not found")


@lead.get("/lead_details_user/{application_id}")
@requires_feature_permission("read")
async def lead_details(
    application_id: str,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    * input student_id must
    * return List of lead detail user data:
    """
    await utility_obj.is_id_length_valid(_id=application_id, name="Application id")
    if not is_testing_env():
        Reset_the_settings().check_college_mapped(college.get("id"))
    data = await LeadUser().lead_details_additional(application_id)
    if data:
        return utility_obj.response_model(data=data, message="data fetch successfully")
    raise HTTPException(status_code=404, detail="data not found")


@lead.get("/lead_notifications/{application_id}")
@requires_feature_permission("read")
async def lead_notifications(
    application_id: str,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Returns the application status of Student'application
     based on application_id
    """
    data = await LeadAdmin().lead_notification(application_id)
    return utility_obj.response_model(data=data, message="data fetch successfully")


@lead.post("/send_email_sidebar")
@requires_feature_permission("write")
async def send_email(
    current_user: CurrentUser,
    testing: Is_testing,
    request: Request,
    to: str = Query(..., description="Enter recipient email id"),
    template_id: str = None,
    subject: str = Query(..., description="Enter subject of email"),
    message: str = Body(None, description="Enter text for email body"),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    email_type: EmailType = Query(
        "default",
        description="Enter email type, it can be default,"
        " promotional and transactional",
    ),
):
    """
    send mail to recipient in background with message 'mail send successfully'
    """
    logger.debug("Started email sending process")
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not user:
        raise HTTPException(status_code=401, detail="Not enough permissions")
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    template = {}
    if template_id is not None:
        await utility_obj.is_id_length_valid(template_id, "Template_id")
        if (
            template := await DatabaseConfiguration().template_collection.find_one(
                {"_id": ObjectId(template_id)}
            )
        ) is None:
            raise HTTPException(status_code=404, detail="Template is not found")
        if message is None:
            message = template.get("content", "")
    if (student := DatabaseConfiguration().studentsPrimaryDetails.find_one({"user_name": to})) is None:
        raise HTTPException(status_code=404, detail="Student not found")
    ip_address = utility_obj.get_ip_address(request)
    email_ids = await EmailActivity().add_default_set_mails(to)
    await EmailActivity().send_message(
        to=email_ids,
        subject=subject,
        message=message,
        event_type="email",
        event_status=f"by {utility_obj.name_can(user)}"
        f" whose id: {str(user.get('_id'))}",
        event_name="Send",
        payload={"content": message, "email_list": email_ids},
        current_user=current_user,
        ip_address=ip_address,
        email_preferences=college.get("email_preferences", {}),
        email_type=email_type.lower(),
        college_id=college.get("id"),
        template_id=template_id if template_id else None,
        template=template if template else {}
    )

    return {"message": "mail send successfully"}


@lead.post(
    "/step_wise_data",
    summary="Get application steps count " "with/without counselor filter.",
)
@requires_feature_permission("read")
async def step_wise_data(
    current_user: CurrentUser,
    cache_data=Depends(cache_dependency),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    counselor_ids: list | None = Body(None),
    date_range: DateRange | None = Body(None),
    season: str | None = Body(
        None, description="Enter season value if want" " to get data season-wise"
    ),
    program_name: list | None = Body(
        None,
        description="Enter program details when want to get data " "based on program.",
    ),
    source: list | None = Body(None),
):
    """
    Get application steps count with/without counselor/program filter.

    Params:
        - college_id (str): An unique identifier of college for
         get college data.
            e.g., 123456789012345678901234

    Request body parameters:
        counselor_ids (list | None): Optional field. Default value: None.
            Value can be list of unique counselor ids.
            e.g., ["123456789012345678901111", "123456789012345678901112"]
        season (str | None): Optional field. Default value: None.
            Enter season id/value when want to get data season-wise data.
        program_name (list | None): Optional field.
            Default value: None. Enter program details when want to get
            data based on program. e.g., [{"course_id":
            "123456789012345678901234", "course_specialization": "xyx"}]
        source (list | None): Optional field.
            Default value: None. Enter source (s) names when want to get
            data based on source (s). e.g., ["organic", "twitter"]

    Returns:
        dict: A dict which contains application steps names and counts along
            with message.
            e.g., {"message": "Application steps count data fetch
                successfully."}
    """
    cache_key, data = cache_data
    if data:
        return data
    try:
        data = await LeadAdmin().step_wise_app(
            counselor_ids, date_range, season, program_name, source
        )
        data = utility_obj.response_model(
            data=data, message="Application steps count data fetch " "successfully."
        )
        if cache_key:
            await insert_data_in_cache(cache_key, data)
        return data
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"An internal error" f" occurred: {error}"
        )


@lead.get("/user_activity/")
@requires_feature_permission("read")
async def user_activities(
    current_user: CurrentUser,
    page_num: int = Query(..., gt=0),
    page_size: int = Query(..., gt=0),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    take input skip and limit
    return all users list based on last accessed
    """
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if user.get("role", {}).get("role_name") == "super_admin":
        raise HTTPException(status_code=401, detail="Not authenticated")
    skip, limit = await utility_obj.return_skip_and_limit(
        page_num=page_num, page_size=page_size
    )
    activity_data, total = await LeadAdmin().activity_of_users(
        skip=skip, limit=limit
    )
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total, route_name="/lead/user_activity/"
    )
    data = {
        "data": activity_data,
        "total": total,
        "count": len(activity_data),
        "pagination": response["pagination"],
        "message": "data fetched successfully",
    }
    return data


@lead.post("/add_tag/", summary="Add tag to student")
@requires_feature_permission("write")
async def add_tag_to_student(
    add_tag_data: AddLeadTag,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Add tag to student.

    Params:
        - college_id (str): Required field. A unique identifier of college.
                    e.g., 123456789012345678901231.

    Request body parameters:
            add_tag_data (AddLeadTag): An object of pydantic class
                `AddLeadTag` which contains following fields:
                - application_id (str): Required field. A unique identifier of
                    application. e.g., 123456789012345678901234.
                - tags (list[str]): A list which contains tags in a string
                    format. e.g., ["string", "test", "test1"]

    Returns:
        dict: A dictionary which contains information about add tags to
            student.

    Raises:
        ObjectIdInValid: An exception with status code 422 which occur when
            student id will be wrong.
        DataNotFoundError: An exception with status code 404 which occur
            when application not found based on application id.
        Exception: An exception with status code 500 which occur
            when error come in the code except ObjectIdInValid and
            DataNotFoundError.
    """
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not user:
        raise HTTPException(status_code=401, detail="Not enough permissions")
    add_tag_data = add_tag_data.model_dump()
    try:
        return await LeadAdmin().add_tags_to_application(
            add_tag_data=add_tag_data, user=user
        )
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as e:
        logger.error(f"{e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")


@lead.get("/show_today_lead_data/", summary="Showing current date lead")
@requires_feature_permission("read")
async def get_current_lead_stage_data(
    current_user: CurrentUser,
    cache_data=Depends(cache_dependency),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    season: str | None = Query(
        None, description="Enter season id if want to" " get data season-wise"
    ),
):
    """
    Get current lead stage data and assign counselor count

    Params:\n
        - college_id (str): Unique college identifier of college
            for get college data.
        - season (str | None): Either None or unique identifier of season
            which useful for get season-wise data.

    Returns:\n
        dict: A dictionary which contains lead stage count details.
    """
    if (
        await DatabaseConfiguration().user_collection.find_one(
            {"user_name": current_user.get("user_name")}
        )
        is None
    ):
        raise HTTPException(status_code=401, detail="Permission denied")
    user = await UserHelper().is_valid_user(current_user)
    key, data = cache_data
    if data:
        return data
    if user.get("role", {}).get("role_name") == "college_counselor":
        counselor_ids = [ObjectId(user.get("_id"))]
    else:
        if user.get("role", {}).get("role_name") == "college_head_counselor":
            counselor_ids = await AdminUser().get_users_ids_by_role_name(
                "college_counselor", college.get("id"), user.get("_id")
            )
        else:
            counselor_ids = None
    try:
        data = await LeadUser().current_date_lead_data(counselor_ids, season)
        if key:
            await insert_data_in_cache(key, data)
        return data
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"{error}")


@lead.put("/lead_header")
@requires_feature_permission("read")
async def lead_header_data(
    current_user: CurrentUser,
    lead_type: str,
    date_range: DateRange = Body(None),
    cache_data=Depends(cache_dependency),
    cache_change_indicator=Depends(change_indicator_cache),
    change_indicator: ChangeIndicator = None,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    season: str | None = Query(
        None, description="Enter season id if want to" " get data season-wise"
    ),
):
    """
    Get the lead header data for the lead dashboard.

    Params:\n
        - lead_type (str): Required field. The lead type will be API, Online,
            Offline lead, Organic, Chat, Telephony.
        - change_indicator (ChangeIndicator | None): Optional field.
            Either none or the values of change indicator can be: last_7_days,
            last_15_days and last_30_days.
        - season (str | None): Either None or unique identifier of season
            which useful for get season-wise data.

    Request body params:\n
        - date_range (DateRange | None): Optional field. Either none or
            daterange which useful for filter data based on date_range.
            e.g., {"start_date": "2023-09-07", "end_date": "2023-09-07"}

    Returns:\n
        - dict: A dictionary which contains lead header information.

    Raises:
        Exception: An exception with status code 500 when certain condition
        fails.
    """
    date_range = await utility_obj.format_date_range(date_range)
    cache_key, data = cache_data
    if data:
        return data
    if (
        user := await DatabaseConfiguration().user_collection.find_one(
            {"user_name": current_user.get("user_name")}
        )
    ) is None:
        raise HTTPException(status_code=401, detail="permission denied")
    counselor_id = None
    is_head_counselor = False
    role_name = user.get("role", {}).get("role_name", "")
    if role_name == "college_counselor":
        counselor_id = [user.get("_id")]
    if role_name == "college_head_counselor":
        is_head_counselor = True
        counselor_id = await AdminUser().get_users_ids_by_role_name(
            "college_counselor", college.get("id"), user.get("_id")
        )
    try:
        data = await LeadAdmin().lead_header_helper(
            lead_type=lead_type.lower(),
            date_range=date_range,
            change_indicator=change_indicator,
            counselor_id=counselor_id,
            season=season,
            is_head_counselor=is_head_counselor,
            cache_change_indicator=cache_change_indicator
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@lead.post("/add_tag/", summary="Add tag to student")
@requires_feature_permission("write")
async def add_tag_to_student(
    add_tag_data: AddLeadTag,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Add tags to students.

    Params:
        - college_id (str): Required field. A unique identifier of college.
                    e.g., 123456789012345678901231.

    Request body parameters:
            add_tag_data (AddLeadTag): An object of pydantic class
                `AddLeadTag` which contains following fields:
                - student_ids (list[str]): Required field.
                    Unique identifiers/ids of student.
                    e.g., ["123456789012345678901234"]
                - tags (list[str]): A list which contains tags in a string
                    format. e.g., ["string", "test", "test1"]

    Returns:
        dict: A dictionary which contains information about add tags to
            student.

    Raises:
        ObjectIdInValid: An exception with status code 422 which occur when
            student id will be wrong.
        DataNotFoundError: An exception with status code 404 which occur
            when student not found based on student id.
        Exception: An exception with status code 500 which occur
            when error come in the code except ObjectIdInValid and
            DataNotFoundError.
    """
    user = await UserHelper().is_valid_user(current_user)
    add_tag_data = add_tag_data.model_dump()
    try:
        return await LeadAdmin().add_tags_to_application(
            add_tag_data=add_tag_data, user=user
        )
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as e:
        logger.error(f"{e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")


@lead.post("/lead_data_count")
@requires_feature_permission("read")
async def get_lead_data_count(
    data_type: str,
    current_user: CurrentUser,
    cache_data=Depends(cache_dependency),
    payload: lead_filter = None,
    page_num: int = Query(1, gt=0),
    page_size: int = Query(25, gt=0),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    season: str | None = Query(
        None, description="Enter season id if want to" " get data season-wise"
    ),
):
    """
    Get the lead data based on counts

    Params:\n
        - data_type (str): Get the string value of the data type
         like: fresh_lead, admission_confirm, interested, follow_up,
          today_assigned
        college (dict): Unique identifier of a college for get college data.
        - season (str | None): Either None or unique identifier of season
            which useful for get season-wise data.

    Returns:\n
        dict: Get the dictionary containing the data by data type.
    """
    if (
        await DatabaseConfiguration().user_collection.find_one(
            {"user_name": current_user.get("user_name")}
        )
        is None
    ):
        raise HTTPException(status_code=401, detail="Permission denied")
    user = await UserHelper().is_valid_user(current_user)
    key, data = cache_data
    if data:
        return data
    if user.get("role", {}).get("role_name") == "college_counselor":
        counselor_ids = [ObjectId(user.get("_id"))]
    else:
        if user.get("role", {}).get("role_name") == "college_head_counselor":
            counselor_ids = await AdminUser().get_users_ids_by_role_name(
                "college_counselor", college.get("id"), user.get("_id")
            )
        else:
            counselor_ids = None
    if payload is None:
        payload = {}
    payload = jsonable_encoder(payload)
    try:
        data = await LeadWrapper().get_lead_wrapper(
            lead_data=data_type,
            counselor_ids=counselor_ids,
            payload=payload,
            page_num=page_num,
            page_size=page_size,
            season=season,
        )
        if key:
            await insert_data_in_cache(key,data)
        return data
    except Exception as error:
        raise HTTPException(status_code=500, detail=error)


@lead.post("/delete_tag/", summary="Delete tag from student")
@requires_feature_permission("delete")
async def delete_tag_from_student(
    delete_tag_data: DeleteLeadTag,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Delete tag from student.

    Params:
        - college_id (str): Required field. A unique identifier of college.
                    e.g., 123456789012345678901231.

    Request body parameters:
            delete_tag_data (DeleteLeadTag): An object of pydantic class
                `DeleteLeadTag` which contains following fields:
                - student_id (str): Required field.
                    Unique identifier/id of student.
                    e.g., "123456789012345678901234"
                - tags (str): Tag which want to remove. e.g., "string"

    Returns:
        dict: A dictionary which contains information about delete tag from
            student.

    Raises:
        ObjectIdInValid: An exception with status code 422 which occur when
            student id will be wrong.
        DataNotFoundError: An exception with status code 404 which occur
            when student not found based on student id.
        Exception: An exception with status code 500 which occur
            when error come in the code except ObjectIdInValid and
            DataNotFoundError.
    """
    await UserHelper().is_valid_user(current_user)
    delete_tag_data = delete_tag_data.model_dump()
    try:
        return await LeadAdmin().delete_tag_from_tag(delete_tag_data)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as e:
        logger.error(f"{e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")


@lead.get("/add_secondary_tertiary_email_phone/")
@requires_feature_permission("write")
async def add_secondary_tertiary_email_phone(
    current_user: CurrentUser,
    student_id: str,
    secondary: str = None,
    tertiary: str = None,
    set_as_default_secondary: bool = False,
    set_as_default_tertiary: bool = False,
    phone: bool = True,
    college_id: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    add secondary and tertiary email or phone number
    Params:
      student_id (str): unique id of student
      secondary (str): secondary mobile or email
      tertiary (str): tertiary mobile or email
      set_as_default_secondary (bool): true to set it default, else no
      set_as_default_tertiary(bool): true to set it  default, else no
      phone(bool): true if need to add phone number false if need to add email
      college_id (str): unique id of college
    Returns:
        A simple message "added number"/"added email".
    """
    await UserHelper().is_valid_user(current_user)
    await utility_obj.is_id_length_valid(_id=student_id, name="Student id")
    try:
        await LeadAdmin().add_secondary_tertiary_email_phone(
            student_id,
            secondary,
            tertiary,
            set_as_default_secondary,
            set_as_default_tertiary,
            phone,
        )
    except DataNotFoundError as e:
        logger.error(f"{e.message}")
        raise HTTPException(status_code=422, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"internal error occurred {e}")
    return {"message": "Added number"} if phone else {"message": "Added email"}
