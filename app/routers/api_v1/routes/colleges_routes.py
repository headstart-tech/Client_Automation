"""
This file contains API routes related to college
"""

from datetime import datetime, timedelta
from typing import Union, Optional

from fastapi import APIRouter, Depends, Query, Body, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException

from app.background_task.college import CollegeActivity
from app.core.custom_error import CustomError, DataNotFoundError
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import (get_collection_from_cache,
                                    store_collection_in_cache, CurrentUser,
                                    Is_testing)
from app.helpers.client_curd.client_screen_helper import ClientScreenHelper
from app.helpers.college_configuration import CollegeHelper
from app.helpers.college_wrapper.college_helper import CollegeRout
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.applications import UtmMedium
from app.models.college_schema import (
    CollegeCreation,
    FormStatus,
    ComponentCharges,
    ReleaseType,
    Feature,
    UsePurpose,
    GeneralDetails,
    SeasonDetails,
    CollegeURLsModel,
    GetBillingDetailsModel,
    CollegeConfiguration,
)
from app.models.student_user_schema import User, ChangeIndicator

college_router = APIRouter()


@college_router.post("/create/", summary="Create new college")
@requires_feature_permission("write")
async def create_college(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        college: CollegeCreation,
        college_id: str = Query(
            None, description="Enter college id which data want to update"
        ),
        create_client: bool = True
):
    """
    Create New Course\n
    * :*param* **name**: e.g. GrowthTrack\n
    * :*param* **address_line_1**: e.g. SR.NO 22/2, Near Mavli Hospital\n
    * :*param* **address_line_2**: e.g. Swarget Pune - 411006\n
    * :*param* **country_code**: e.g. India\n
    * :*param* **state_code**: e.g. Maharashtra\n
    * :*param* **city**: e.g. Pune\n
    * :*param* **website_url**: e.g. https://www.shiftboolean.com\n
    * :*param* **name**: e.g. John Michel Doe\n
    * :*param* **email**: e.g. a@gmail.com\n
    * :*param* **mobile_number**: e.g. 5675676786\n
    * :*param* **raw_data_module**: e.g. true\n
    * :*param* **lead_management_system**: e.g. true\n
    * :*param* **app_management_system**: e.g. false\n
    * :*param* **lead_limit**: e.g. 10\n
    * :*param* **counselor_limit**: e.g. 5\n
    * :*param* **college_managerLimit**: e.g. 2\n
    * :*param* **publisher_account_limit**: e.g. 3\n
    * :*param* **activation_date**: e.g. 2022-04-04 07:20:55.944605\n
    * :*param* **deactivation_date**: e.g. 2022-04-04 07:20:55.944605\n
    * :*return* **Add new college data and return it with reply message 'New college data added successfully.'**:
    """
    college = jsonable_encoder(college)
    user = await UserHelper().is_valid_user(current_user)
    if college.get("name") not in ["", None]:
        college["name"] = college.pop(
            "name", ""
        ).title()
    if college_id:
        data = await CollegeHelper().update_details(college_id, college, user,
                                                    background_tasks, create_client)
        return data
    else:
        if college.get("name") in ["", None]:
            raise HTTPException(status_code=422,
                                detail="College name not provided.")
        if college.get("logo") in ["", None]:
            raise HTTPException(status_code=422, detail="Logo not provided.")
        find_college = await DatabaseConfiguration().college_collection.find_one(
            {"name": college.get("name")}
        )
        if find_college:
            raise HTTPException(400, detail="College data already exist.")
        college = await CollegeHelper().create_new_college(college, user,
                                                           create_client=create_client)
        background_tasks.add_task(CollegeActivity().create_courses,
                                  college.get('course_details', []),
                                  college.get('id'))
        return utility_obj.response_model(data=college,
                                          message="New college data added successfully.")


@college_router.get("/list_college/", summary="List of Colleges")
@requires_feature_permission("read")
async def get_list_of_colleges(
        current_user: CurrentUser,
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
        using_for: UsePurpose = None,
):
    """
    Admin can see list of all college created \n
    :return **List of colleges**:
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        colleges = await CollegeHelper().college_list(page_num, page_size,
                                                      route_name="/college/list_college/",
                                                      user=user,
                                                      using_for=using_for)
        if not colleges:
            raise DataNotFoundError("Colleges")
        return colleges
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@college_router.get(
    "/get_by_id_or_name/",
    summary="Get college_details by college_id or college_name"
)
@requires_feature_permission("read")
async def get_college_details_by_id_or_name(
        current_user: CurrentUser,
        id: str = Query(
            None,
            description="College ID \n* e.g.," "**624e8d6a92cc415f1f578a24**"
        ),
        name: str = Query(None, description="College name \n* e.g., **Test**"),
):
    """
    Get College Details by id or name\n
    * :*param* **id** e.g. 624e8d6a92cc415f1f578a24:
    * :*param* **name**: e.g., Test\n
    * :*return* **Get college_details by id or name**:
    """
    await UserHelper().is_valid_user(current_user)
    college = await CollegeHelper().college_details(id, name)
    if college:
        return utility_obj.response_model(college,
                                          "College details fetched successfully.")
    raise HTTPException(status_code=404, detail="College not found.")


@college_router.post("/get_colleges_by_client_ids/",
                     summary="Get College List by list of Client Ids")
@requires_feature_permission("read")
async def get_colleges_by_client_ids(
        current_user: CurrentUser,
        body: dict = Body(..., description="Client IDs"),
        page: Optional[int] = Query(None, gt=0),
        limit: Optional[int] = Query(None, gt=0),
):
    """
    Get College List by list of Client Ids

    ## Request Body
    - **client_ids**: A list containing the clients ids.

    ## Example Request Body
    ```json
    {
        "client_ids": ["624e8d6a92cc415f1f578a24", "624e8d6a92cc415f1f578a25"]
    }
    ```

    ## Response Body
    - **data**: Contains details about the colleges.
    - **message**: Response message ("Colleges details fetched successfully.").

    ## Raises
    - **404**: College not found.
    - **422**: Invalid client ids.
    - **500**: Internal Server Error.
    """
    await UserHelper().is_valid_user(current_user)
    client_ids = body.get("client_ids", [])
    try:
        colleges = await CollegeHelper().get_colleges_by_client_ids(
            client_ids,
            page,
            limit,
            route="/college/get_colleges_by_client_ids/"
        )
        if colleges:
            return utility_obj.response_model(
                colleges,
                "Colleges details fetched successfully."
            )
        else:
            raise DataNotFoundError("Colleges")
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@college_router.get("/season_list/",
                    summary="Get college season list by id or name")
@requires_feature_permission("read")
async def get_college_season_list_by_id_or_name(
        current_user: CurrentUser,
        id: str = Query(
            None,
            description="College ID \n* e.g.," "**624e8d6a92cc415f1f578a24**"
        ),
        name: str = Query(None, description="College name \n* e.g., **Test**"),
):
    """
    Get College season list by id or name\n
    * :*param* **id** e.g. 624e8d6a92cc415f1f578a24:
    * :*param* **name**: e.g., Test\n
    * :*return* **Get college_details by id or name**:
    """
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")})
    if not user:
        raise HTTPException(status_code=401, detail="Not enough permissions")
    season = await CollegeHelper().get_college_season_list(id, name)
    if season:
        return {"data": season, "message": "Get list of season."}
    raise HTTPException(status_code=404, detail="College not found.")


@college_router.get("/communication_info/",
                    summary="Get communication info of college")
@requires_feature_permission("read")
async def get_college_season_list_by_id_or_name(
        current_user: CurrentUser,
        college_id: str = Query(
            None,
            description="Enter college ID \n* e.g.," "**624e8d6a92cc415f1f578a24**"
        ),
        college_name: str = Query(None,
                                  description="Enter college name \n* e.g., **Test**"),
):
    """
    Get College season list by id or name\n
    * :*param* **id** e.g. 624e8d6a92cc415f1f578a24:
    * :*param* **name**: e.g., Test\n
    * :*return* **Get college_details by id or name**:
    """
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")})
    if not user:
        raise HTTPException(status_code=401, detail="Not enough permissions")
    communication_info, college = await CollegeHelper().get_communication_info(
        college_id, college_name)
    if communication_info:
        return {"data": communication_info,
                "message": "Get communication info of college."}
    return {
        'detail': "College not found. Make sure college_id or college_name is correct."}


@college_router.put("/update_status/")
@requires_feature_permission("edit")
async def update_status(background_tasks: BackgroundTasks, college_id: str,
                        status: FormStatus,
                        current_user: CurrentUser):
    """
    Update college status
    """
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") not in ["client_manager",
                                                     "super_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    data = await CollegeHelper().update_status(college_id, user, status,
                                               background_tasks)
    return data


@college_router.get("s/get_by_status/")
@requires_feature_permission("read")
async def get_by_status(
        current_user: CurrentUser,
        approved: bool = Query(False,
                               description="If you want to get approved colleges then send value True"),
        declined: bool = Query(False,
                               description="If you want to get declined colleges then send value True"),
        pending: bool = Query(False,
                              description="If you want to get pending colleges then send value True"),
        own_colleges: bool = False,
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0)):
    """
    Get colleges based on status
    """
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") not in ["client_manager",
                                                     "super_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    colleges = await CollegeHelper().colleges_based_on_status(approved,
                                                              declined,
                                                              pending,
                                                              own_colleges,
                                                              page_num,
                                                              page_size,
                                                              route_name=f"/college/forms_by_status/?approved={approved}&pending={pending}&declined={declined}&page_num={page_num}&page_size={page_size}",
                                                              user=user)
    if colleges:
        return colleges
    return {"detail": "Colleges data not found."}


@college_router.get("/get_course_details/",
                    response_description="Get course details by name")
async def get_course_details(
        course_name: str | None = None,
        specialization_name: str | None = None,
        college: dict = Depends(get_college_id)
):
    """
    Get course details. If a course/specialization name is given then giving
        form details which is specific to course/specialization.

    Params:
        - course_name (str | None): Either None or name of a course.
            e.g., B.Sc.
        - college: A dictionary which contains college information.
        - specialization_name (str | None): Either None or name of
            course specialization. e.g., Physician Assistant.

    Returns:
        dict: A dictionary which contains information of form or course.
    """
    return await CollegeHelper().get_course_details(course_name, college,
                                                    specialization_name)


@college_router.put("/component_charges/",
                    response_description="Add or update component charges")
async def component_charges(charges: ComponentCharges):
    """
    Add or update component charges
    """
    return await CollegeHelper().add_or_update_component_charges(charges)


@college_router.get("/get_component_charges/",
                    response_description="Get component charges")
async def get_component_charges():
    """
    Get component charges
    """
    return await CollegeHelper().get_component_charges()


@college_router.get("/estimation_bill/",
                    response_description="Get estimation bill of college")
@requires_feature_permission("read")
async def estimated_bill(current_user: CurrentUser,
                         page_num: Union[int, None] = Query(None, gt=0),
                         page_size: Union[int, None] = Query(None, gt=0)):
    """
    Get estimation bill of college
    """
    return await CollegeHelper().estimated_bill(current_user, page_num,
                                                page_size,
                                                route_name=f"/college/estimation_bill/?page_num={page_num}&page_size={page_size}")


@college_router.post("/get_billing_details/", )
@requires_feature_permission("read")
async def get_billing_details(
        current_user: CurrentUser,
        billing_details: Optional[GetBillingDetailsModel] = None,
        college_id: Optional[str] = None
):
    """
    Get Billing Details of College (Features, Email, SMS & Whatsapp)

    ### Params
    - **college_id** *(Optional)*: An unique identifier of a college.
        e.g., 123456789012345678901234

    ### Request Body
    - **filters** *(Optional)*: Filter the billing details of college. [last_week, last_month, last_year]
    - **from_date** *(Optional)*: Start date in YYYY-MM-DD
    - **to_date** *(Optional)*: End date in YYYY-MM-DD

    ### Example Request Body
    ```json
    {
        "from_date": "2023-01-01",
        "to_date": "2025-04-01"
    }
    ```

    ### Response Body
    - **feature_breakdown** *(list of {feature_id, name, monthly_total, college_count=1})*: List of features with their breakdown.
    - **feature_grand_total** *(int)*: Total cost of features.
    - **sms_count** *(int)*: Number of SMS sent.
    - **sms_cost** *(float)*: Cost of SMS.
    - **whatsapp_count** *(int)*: Number of Whatsapp sent.
    - **whatsapp_cost** *(float)*: Cost of Whatsapp.
    - **email_count** *(int)*: Number of Email sent.
    - **email_cost** *(float)*: Cost of Email.
    - **grand_total** *(float)*: Total cost of billing.

    ### Raises
    - **400**: Bad Request
    - **401**: Unauthorized
    - **404**: Not Found
    - **422**: Unprocessable Entity
    - **500**: Internal Server Error
    """
    user = await UserHelper().is_valid_user(current_user)
    if billing_details is None:
        billing_details = GetBillingDetailsModel()
    try:
        billing_details = jsonable_encoder(billing_details)
        # TODO: Add this When Users are able to Login
        # Checking if the user Associated with this college
        # if not college.get("id") in user.get("associated_colleges"):
        #     raise CustomError("You are not associated with this college")

        # Checking if the Request have Body
        if billing_details.get("filters"):
            # Converting filter into days to modify the from_date
            filter_into_days = {
                "last_7_days": 7,
                "last_15_days": 15,
                "last_30_days": 30,
                "last_365_days": 365
            }
            if billing_details["filters"] not in filter_into_days:
                raise CustomError("Invalid filter")

            # Modifying the from_date (CURRENT_DATE - filter_into_days)
            billing_details["from_date"] = (
                    datetime.now() - timedelta(days=filter_into_days[billing_details["filters"]])
            ).strftime("%Y-%m-%d")

        return await CollegeHelper().get_college_billing(college_id=college_id,
                                                         from_date=billing_details["from_date"],
                                                         to_date=billing_details["to_date"])
    except CustomError as e:
        raise HTTPException(422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@college_router.get("/get_form_details/",
                    response_description="Get form details")
async def get_form_field_details():
    """
    Get form details
    """
    return await CollegeHelper().get_form_details()


@college_router.get("/communication_performance_dashboard/")
@requires_feature_permission("read")
async def communication_performance_dashboard(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
        release_type: ReleaseType = None,
        change_indicator: ChangeIndicator = None):
    """
    Get the communication performance dashboard data
    """
    return await CollegeHelper().get_communication_performance_dashboard(
        current_user, release_type, change_indicator)


@college_router.post("/utm_medium_by_source_names/",
                     summary="Get utm medium list by source names")
@requires_feature_permission("read")
async def utm_medium_data_by_source_names(
        source_names: list[str],
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)):
    """
    Get the utm medium list by source names
    """
    return await CollegeHelper().get_utm_medium_data_by_source_names(
        current_user, source_names)


@college_router.put("/features/update/", summary="Add or update features")
@requires_feature_permission("write")
async def add_or_update_features(features: Feature,
                                 current_user: CurrentUser,
                                 college: dict = Depends(get_college_id)):
    """
    Add or update features
    """
    return await CollegeHelper().add_or_update_features(current_user, features,
                                                        college)


@college_router.get("/features/", summary="Get features")
@requires_feature_permission("read")
async def add_or_update_features(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)):
    """
    Get features data
    """
    return await CollegeHelper().get_features(current_user, college)


@college_router.get("/signup_form_extra_fields/",
                    summary="Get signup form extra fields")
async def get_signup_form_extra_fields(
        college_id: str = Query(None,
                                description="College ID \n* e.g.," "**624e8d6a92cc415f1f578a24**"),
        domain_url: str = Query(None,
                                description="Domain URL \n* e.g.," "https://test.com")):
    """
    Get signup form extra fields
    """
    return await CollegeHelper().get_signup_form_extra_fields(college_id,
                                                              domain_url)


@college_router.get("/existing_fields/",
                    response_description="Get existing fields names with key_names")
async def get_form_field_details():
    """
    Get existing fields names with key_names
    """
    return await CollegeHelper().get_existing_fields()


@college_router.get("/extra_filter_fields/",
                    summary="Get extra filter fields based on college id / domain url")
async def get_extra_filter_fields(
        college_id: str = Query(None,
                                description="College ID \n* e.g.," "**624e8d6a92cc415f1f578a24**"),
        domain_url: str = Query(None,
                                description="Domain URL \n* e.g.," "https://test.com")):
    """
    Get extra filter fields based on college id / domain url
    """
    return await CollegeHelper().get_extra_filter_fields(college_id,
                                                         domain_url)


@college_router.get("/lead_tags/", summary="Get lead tags")
@requires_feature_permission("read")
async def get_lead_tags(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)
):
    """
    Get lead tags based on college id.
    Params:
        - college_id (str): Required field. A unique identifier of college.
                    e.g., 123456789012345678901231.
    Returns:
        dict: A dictionary which contains information about get lead tags.
    """
    await UserHelper().is_valid_user(current_user)
    lead_tags = college.get("lead_tags", [])
    if lead_tags:
        return {"message": "Get the lead tags.", "data": lead_tags}
    return {"detail": "Lead tags not found."}


@college_router.get("/university_names")
async def get_university_names(
        diploma_university: str = None,
):
    """
    Get the university name or diploma name

    params:
        diploma_university (str): Get the string value like
         diploma or university
        e.g. = diploma, university or null
    return:
        response: a list of diploma or university
    """
    diploma_inventory = await get_collection_from_cache(collection_name="diploma_inventory")
    if diploma_inventory:
        university_details = diploma_inventory[0]
    else:
        university_details = await DatabaseConfiguration().Diploma_Inventory.find_one(
            {"stream_name": {"$exists": True}})
        await store_collection_in_cache([university_details], collection_name="diploma_inventory")
    if diploma_university not in ["", None]:
        if diploma_university.lower() == "diploma":
            return {"diploma_name": university_details.get("stream_name", [])}
        elif diploma_university.lower() == "university":
            return {"university_name": university_details.get(
                "diploma_college_name", [])}
    else:
        return {"university_name": university_details.get(
            "diploma_college_name", []),
            "diploma_name": university_details.get("stream_name", [])}


@college_router.put("/features/delete/", summary="Delete features")
@requires_feature_permission("delete")
async def delete_features(features: list[dict],
                          current_user: CurrentUser,
                          college: dict = Depends(get_college_id)):
    """
    Delete features for a college by college id.

    Params:\n
        - college_id (str): An unique identifier of a college.
            e.g., 123456789012345678901234

    Request body params:\n
        - features (list): A list which contains information about delete feature.
            e.g., [{"menu_name": {"sub_menu_name": []}}]

    Returns:\n
        - dict: A dictionary which contains information about delete feature.

    Raises:
        - HTTPException: An error occurred with status code 500 when something wrong happen in the backend code.
    """
    await UserHelper().check_user_has_permission(
        current_user, check_roles=["client_manager", "super_admin"],
        condition=False)
    try:
        return await CollegeHelper().delete_features(features, college)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Something went wrong. Error - {error}")


@college_router.post("/get_utm_campaign/",
                     summary="Get utm campaign list")
@requires_feature_permission("read")
async def get_utm_campaign_data(
        testing: Is_testing,
        payload: list[UtmMedium],
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)):
    """
    Get the utm campaign list.

    Params:\n
        - college_id (str): An unique id/identifier of a college. e.g., 123456789012345678901234

    Request body params:\n
        - payload (list): A list which contains dictionaries of source name and utm medium name.
            e.g., [{"source_name": "organic", "utm_medium": "test"}]

    Returns:\n
        - dict: A dictionary which contains information about campaign list along with message.

    Raises:\n
        - Exception: An error which occurred with status code 500 when something went wrong in the backend code.
    """
    await UserHelper().is_valid_user(current_user)
    if not testing:
        Reset_the_settings().check_college_mapped(college.get("id"))
    try:
        return await CollegeHelper().get_utm_campaign_data(payload)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred when get list of campaign. Error: {str(error)}"
        )


@college_router.post("/additional_details",
                     summary="Get general details")
@requires_feature_permission("write")
async def get_additional_data(
        payload: GeneralDetails,
        current_user: CurrentUser,
        approval_id: str | None = None,
        college: dict = Depends(get_college_id)
):
    """
    Upload the general additional details in the college collection

    Params:
        testing: Dependency function based on the test case running
        payload: Get the all data of general details as input from the user
        current_user: Get the current user email and
        college: Get the college details from the dependencies

    Return:
        return a success message to save this details
    """
    try:
        user = await UserHelper().is_valid_user(current_user)
        payload = jsonable_encoder(payload)
        return await CollegeRout().store_general_additional_details(
            payload=payload, college_id=college.get("id"), user=user, approval_id=approval_id)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@college_router.post("/add_college_configuration")
@requires_feature_permission("write")
async def add_college_configuration(
    payload: CollegeConfiguration,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id),
):
    """
    Upload the general additional details in the college collection
    Should be used only by Super Admin

    ## Request Parameters
    - **college_id**: College ID

    ## Request Body
    - **email_credentials**: Email credentials
    - **email_configurations**: Email configurations
    - **seasons**: Seasons
    - **university_details**: University details
    - **payment_gateways**: Payment gateways
    - **juno_erp**: Juno ERP
    - **payment_configurations**: Payment configurations
    - **preferred_payment_gateway**: Preferred payment gateway
    - **payment_successfully_mail_message**: Payment successfully mail message
    - **cache_redis**: Cache Redis
    - **enforcements**: Enforcements
    - **charges_per_release**: Charges per release
    - **users_limit**: Users limit
    - **publisher_bulk_lead_push_limit**: Publisher bulk lead push limit
    - **report_webhook_api_key**: Report webhook API key
    - **telephony_secret**: Telephony secret
    - **telephony_cred**: Telephony credentials
    - **email_display_name**: Email display name
    - **s3_base_folder**: S3 base folder

    ## Request Body Example

    ```json
    {
          "email_credentials": {
            "payload_username": "apollobot",
            "payload_password": "StrongPass!458",
            "payload_from": "no-reply@apollouni.edu",
            "source": "noreply@headstartmail.com"
          },
          "email_configurations": {
            "verification_email_subject": "Confirm Your Email Address",
            "contact_us_number": "1800-111-2222",
            "university_email_name": "ApolloConnect",
            "banner_image": "https://cdn.apollouni.edu/mailers/banners/banner3.png",
            "email_logo": "https://cdn.apollouni.edu/assets/logo-mail.png"
          },
          "seasons": [
            {
              "season_name": "2023-2024",
              "start_date": "2023-06-01",
              "end_date": "2024-05-31",
              "database": {
                "username": "seasonal_user_1",
                "password": "Y#s8nv4Kl#91",
                "url": "cluster1.mongodb.net",
                "db_name": "apollo_season23"
              }
            },
            {
              "season_name": "2024-2025",
              "start_date": "2024-06-01",
              "end_date": "2025-05-31",
              "database": {
                "username": "seasonal_user_2",
                "password": "XtL9*vk98Mb2",
                "url": "cluster2.mongodb.net",
                "db_name": "apollo_season24"
              }
            }
          ],
          "university_details": {
            "university_contact_us_mail": "connect@apollouni.edu",
            "university_website_url": "www.apollouni.edu",
            "university_prefix_name": "AU"
          },
          "payment_gateways": {
            "easy_buzz": {
              "base_url": "https://sandbox.easebuzz.in",
              "environment": "sandbox",
              "merchant_key": "KEY12345EZ",
              "merchant_salt": "SALT#EZ9988",
              "retrieve_url": "https://dashboard.sandbox.easebuzz.in"
            },
            "eazypay": {
              "encryption_key": "9900112233445566",
              "merchant_id": "A12345"
            },
            "hdfc": {
              "base_url": "https://uatgateway.hdfcbank.com/session",
              "customer_id": "APOLLO01",
              "environment": "uat",
              "key": "QWERTYUIOP1234567890==:TestEnv2025",
              "merchant_id": "HDFC1001",
              "retrieve_url": "https://uatgateway.hdfcbank.com/orders/"
            },
            "payu": {
              "merchant_key": "keyPAYU123",
              "merchant_salt": "SaltStringForPAYU123",
              "retrieve_url": "https://test.payu.in/merchant/postservice.php?form=3"
            },
            "razorpay": {
              "partner": true,
              "razorpay_api_key": "rzp_test_9876543210Abc",
              "razorpay_secret": "SecretRZP98765",
              "razorpay_webhook_secret": "whk#123secure",
              "x_razorpay_account": "acc_ABC123Xyz987"
            }
          },
          "juno_erp": {
            "first_url": {
              "authorization": "a1b2c3d4-e5f6-7890-gh12-ijklmnop4567",
              "juno_url": "https://erp.apollouni.edu/validateApplicant.json"
            },
            "prog_ref": 101,
            "second_url": {
              "authorization": "z9y8x7w6-v5u4-3210-tsrq-ponmlkji9876",
              "juno_url": "https://erp2.apollouni.edu/saveApplicantData.json"
            }
          },
          "payment_configurations": [
            {
              "allow_payment": true,
              "application_wise": false,
              "apply_promo_voucher": true,
              "apply_scholarship": true,
              "payment_gateway": [
                "razorpay",
                "payu"
              ],
              "payment_key": "registration",
              "payment_mode": {
                "offline": false,
                "online": true
              },
              "payment_name": "Registration Fee",
              "show_status": true
            }
          ],
          "preferred_payment_gateway": "RazorPay",
          "payment_successfully_mail_message": "Thank you for completing your application and payment. <br><br>Your next step is to upload all pending academic documents to proceed further. <br><br>Feel free to contact your admission counselor or visit https://www.apollouni.edu/support for queries. <br><br>You can view and download your receipt here: <br>",
          "cache_redis": {
            "host": "10.45.23.101",
            "port": 6380,
            "password": "SecUr3#Redis2025"
          },
          "enforcements": {
            "lead_limit": 80,
            "counselor_limit": 100,
            "client_manager_limit": 60,
            "publisher_account_limit": 30
          },
          "charges_per_release": {
            "forSMS": 1,
            "forEmail": 5,
            "forWhatsapp": 2,
            "forLead": 0.25
          },
          "users_limit": 500,
          "publisher_bulk_lead_push_limit": {
            "bulk_limit": 150,
            "daily_limit": 200
          },
          "report_webhook_api_key": "APIKEY2025XYZ",
          "telephony_secret": "telephonySecret@123456789",
          "telephony_cred": {
            "mcube": {
              "key": "apikey-mcube-2025",
              "outbound_url": "http://api.mcube.in/v1/callout"
            },
            "mcube2": {
              "tawk_secret": "s3cret4567tawkkey98273627387asdk",
              "key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
              "outbound_url": "https://api2.mcube.in/v2/outbound"
            }
          },
          "email_display_name": "Apollo Outreach",
          "s3_base_folder": "apollouni-2025"
        }
    ```

    ## Raises:
    - **404**: DataNotFoundError
    - **422**: CustomError
    - **500**: Exception

    Return:
        - **message**: Success message
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        await UserHelper().is_valid_user(current_user)
        data = await payload.to_db(college)
        payload = jsonable_encoder(data)
        return await CollegeRout().add_college_configuration(
            payload=payload, college_id=college.get("id"), user=user
        )
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")

@college_router.get("/college_configuration", summary="Get college configuration")
@requires_feature_permission("read")
async def get_college_configuration(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id),
):
    """
    Get the college configuration details

    Params:
        current_user: Get the current user email and
        college: Get the college details from the dependencies

    Return:
        Return the college configuration details
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await CollegeRout().get_college_configuration(college_id=college.get("id"))
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")

        
@college_router.post("/season_details",
                     summary="Create season details")
@requires_feature_permission("write")
async def get_season_data(
        payload: SeasonDetails,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)
):
    """
    Upload the general additional details in the college collection

    Params:
        payload: Get the all data of season details as input from the user
        current_user: Get the current user email and
        college: Get the college details from the dependencies

    Return:
        return a success message to save this details
    """
    try:
        await UserHelper().is_valid_user(current_user)
        payload = jsonable_encoder(payload)
        return await CollegeRout().store_season_details(
            payload=payload, college_id=college.get("id"))
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@college_router.get("/default_screen_by_client")
@requires_feature_permission("read")
async def get_default_screen_by_client(
        current_user: CurrentUser,
        testing: Is_testing,
):
    """
    Get the Default Screen for College Set by Client for Initial Selection

    ### Response Body:
        - dict: Return the client screen

    ### Raises:
        - 422: CustomError
        - 404: DataNotFoundError
    """
    # Todo: We will change this admin validation based on rbac implementation
    user = await UserHelper().is_valid_user(current_user)

    # Hard Coding it for now in Testing mode as in the Testing User doesnt have key associated_client
    if testing:
        user["associated_client"] = "67e674235128e7b3960907fb"

    try:
        # Checking if User is associated with any client
        if not user.get("associated_client"):
            raise CustomError(
                message="User is not associated with any client / You should be a College User")

        # Get the client screen
        return await ClientScreenHelper().get_client_screen_by_id(
            client_id=user.get("associated_client"))
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@college_router.get("/{college_id}/urls")
@requires_feature_permission("read")
async def get_college_urls(
        college_id: str,
        current_user: CurrentUser,
):
    """
    Get Student Dashboard & Admin Dashboard URLs

    ### Query Parameters
    - college_id: College ID

    ### Returns
    - student_dashboard_url (str): Student Dashboard URL
    - admin_dashboard_url (str): Admin Dashboard URL

    ### Raises
    - 422: CustomError
    - 404: DataNotFoundError
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await CollegeHelper().get_college_urls(college_id)
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@college_router.post("/{college_id}/set_urls")
@requires_feature_permission("write")
async def set_college_urls(
    current_user: CurrentUser,
    URLs: CollegeURLsModel,
    college: dict = Depends(get_college_id),
):
    """
    Set Student Dashboard & Admin Dashboard URLs will be Used by TeamCity

    ### Query Parameters
    - college_id: College ID

    ### Request Body
    - student_dashboard_url (str): Student Dashboard URL
    - admin_dashboard_url (str): Admin Dashboard URL

    ### Example Request Body
    ```
    {
      "student_dashboard_url": "https://student.example.com/",
      "admin_dashboard_url": "https://admin.example.com/"
    }
    ```

    ### Returns
    - message (str): Message

    ### Raises
    - 422: CustomError
    - 404: DataNotFoundError
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await CollegeHelper().set_college_urls(
            college, jsonable_encoder(URLs, by_alias=False)
        )
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@college_router.get("/application_tabs/{college_id}")
@requires_feature_permission("read")
async def fetch_from_tabs(
        current_user: CurrentUser,
        college_id: str,
        course_id: str = Query(..., description="Enter college id."),
        step_id: str = Query(None, description="Enter form stage id."),
):
    """
    Fetch application form tabs or a specific stage for a given college and course.

    This endpoint retrieves the complete list of form steps (tabs) or details of a specific
    step (if `step_id` is provided) for a given college and course. The response will only
    be returned if the current authenticated student is associated with the system.

    Params:
        current_user (CurrentUser): The currently authenticated user (student).
        college_id (str): The ID of the college.
        course_id (str): The ID of the course within the college.
        step_id (str, optional): The specific step (tab) ID to fetch. If not provided, all steps are returned.

    Returns:
        JSON response containing:
            - message: A success message.
            - data: The requested form step(s).

    Raises:
        HTTPException: If the user is unauthorized, or if an error occurs during processing.
    """
    # TODO: Ensure the logged-in student is associated with the provided college.
    if (student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"user_name": current_user.get("user_name")}
    )) is None:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    try:
        return await CollegeHelper().fetch_form_tabs_and_fields(college_id=college_id,
                                                                course_id=course_id,
                                                                step_id=step_id,
                                                                student_id=student.get("_id")
                                                                )
    except HTTPException as error:
        raise error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@college_router.get("/fetch_additional_upload_fields")
@requires_feature_permission("read")
async def fetch_additional_uploads(
        current_user: CurrentUser,
        client_id: str = Query(None, description="Enter client id."),
        college_id: str = Query(None, description="Enter college id."),
        course_id: str = Query(None, description="Enter form course id."),
):
    """
    Fetch additional upload fields for a specific college and course.

    This endpoint retrieves the additional fields that a student is required
    to upload during the form submission process based on the selected college and course.

    Params:
        current_user (CurrentUser): The currently logged-in user.
        client_id (str, optional): The client ID associated with the college.
        college_id (str, optional): The unique ID of the college.
        course_id (str, optional): The unique ID of the course.

    Returns:
        JSON response containing the additional upload fields required.

    Raises:
        HTTPException: If the user is not valid, or an internal server error occurs.
    """
    # TODO: Ensure the logged-in student is associated with the provided college.
    await UserHelper().is_valid_user(current_user)
    try:
        return await CollegeHelper().fetch_additional_upload_fields(client_id=client_id,
                                                                    college_id=college_id,
                                                                    course_id=course_id)
    except HTTPException as error:
        raise error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@college_router.post("/get_course_categories/",
                     summary="Get course categories")
async def get_course_categories(
        college: dict = Depends(get_college_id_short_version(short_version=True))):
    """
    Get course categories
    Params:
        college_id (str): The unique id of college
        current_user (str): The details of user
    Returns:
        The course categories of college
    Raises:
        HTTPException: An unexpected error occurred
    """
    course_categories = college.get("course_categories", [])
    try:
        return {
            "message": "Get Course Categories",
            "course_categories": course_categories if course_categories else ["UG", "PG"]
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Error: {str(error)}")


@college_router.get("/get_all_colleges/",
                     summary="Get all colleges")
@requires_feature_permission("read")
async def get_all_colleges(
        current_user: CurrentUser,
        page_num: Optional[int] = Query(None, gt=0),
        page_size: Optional[int] = Query(None, gt=0)
):
    """
        Retrieves a paginated list of colleges accessible to the current user.

        This function fetches college records based on the user's access permissions
        and returns the results using the provided pagination parameters.

        Args:
            current_user (CurrentUser): The authenticated user requesting the data.
            page_num (int, optional): The page number to retrieve (must be greater than 0).
            page_size (int, optional): The number of colleges per page (must be greater than 0).

        Returns:
            list: The list of colleges and pagination metadata.
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        data, total_count = await CollegeHelper().get_all_colleges(user=user, page_num=page_num, page_size=page_size)
        if page_num and page_size:
            response = await utility_obj.pagination_in_aggregation(
                page_num, page_size, total_count, route_name="/get_all_colleges/"
            )
            return {
                "data": data,
                "total": total_count,
                "count": len(data),
                "pagination": response.get("pagination", {}),
                "message": "Colleges Data fetched successfully",
            }
        return {
            "message": "Colleges Data fetched successfully",
            "data": data
        }
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"Error: {str(error)}"
        )


@college_router.get("/onboarding_details/",
                     summary="Get onboarding details")
@requires_feature_permission("read")
async def get_onboarding_details(
        current_user: CurrentUser,
        client_id: str = None,
        college_id: str = None
):
    """
        Retrieves onboarding details for a specific client or college.

        This function fetches the onboarding progress based on the provided client or college ID.
        It can be used to determine the status of various onboarding steps for the user.

        Args:
            current_user (CurrentUser): The user making the request, used for access control and filtering.
            client_id (str, optional): The ID of the client whose onboarding details are to be fetched.
            college_id (str, optional): The ID of the college whose onboarding details are to be fetched.

        Returns:
            dict: A dictionary containing onboarding data, including steps and statuses.
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        if not client_id and not college_id:
            raise CustomError(message="Client id or College id i required")
        data = await CollegeHelper().get_onboarding_details(user, client_id, college_id)
        return {
            "data": data,
            "message": "Onboarding Details"
        }
    except CustomError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Some thing went wrong!: {e}")
