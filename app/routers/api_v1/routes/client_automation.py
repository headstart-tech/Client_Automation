"""
This file contains API routes/endpoints related to client automation
"""
from typing import Annotated, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, Query, Body, Path
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException

from app.core import get_logger
from app.core.custom_error import CustomError, DataNotFoundError, ObjectIdInValid
from app.core.utils import utility_obj, Utility, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id_short_version, get_college_id
from app.dependencies.oauth import (
    CurrentUser,
    get_current_user_object,
)
from app.helpers.approval.approval_helper import ApprovalCRUDHelper, ApprovedRequestHandler
from app.helpers.client_automation.client_automation_helper import (
    college_details,
    Client_screens,
)
from app.helpers.client_automation.master_helper import Master_Service
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.client_automation_schema import (
    add_college_details,
    SignupFormRequest,
    CollegeProgramModel,
    StatusInfo,
    FormStatus, BillingRequestModel,
)
from app.models.master_schema import MasterScreen, DashboardHelper

client_router = APIRouter()

logger = get_logger(__name__)


@client_router.post("/add_college")
@requires_feature_permission("write")
async def add_college_info(payload: add_college_details, current_user: CurrentUser):
    """
    add college details by the admin or account manager

    Param:
        payload: Get the pydantic model for input the college data from the user
        current_user: get the current user email and validation exists or not

    Returns:
        Return success message

    Raises:
        HTTPException: if user not found
        HTTPException: if custom error occurs
        HTTPException: if any error occurs
    """
    # TODO: Pending the user authentication for super account manager or account manager
    #  because of currently authentication not doing in this sprint.
    if (
        user := await DatabaseConfiguration().user_collection.find_one(
            {"user_name": current_user.get("user_name")}
        )
    ) is None:
        raise HTTPException(status_code=404, detail="User not found")
    payload = jsonable_encoder(payload)
    try:
        return await college_details().add_college_by_admin(payload=payload, user=user)
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@client_router.post("/get_billing_details")
async def get_billing_details(
        current_user: CurrentUser,
        data: Optional[BillingRequestModel] = Body(default={}),
    ):
    """
    It Fetches Billing Details depending upon the Data Passed in Request Body

    ### Request Body
    - **client_ids (Optional[List[str]])**: List of Client Ids
    - **college_ids (Optional[List[str]])**: List of College Ids

    ### Request Body Example
    ```json
    {
        "client_ids": ["client_id_1", "client_id_2"],
        "college_ids": ["college_id_1", "college_id_2"]
    }
    ```
    ### Response Body
    - **lead_count (int)**: Total number of leads registered.
    - **lead_cost (float)**: Total cost incurred for leads.
    - **lead_limit (int)**: Sum of lead limits across the colleges.
    - **sms_count (int)**: Total number of SMS messages sent.
    - **sms_cost (float)**: Total cost incurred for SMS.
    - **whatsapp_count (int)**: Total number of WhatsApp messages sent.
    - **whatsapp_cost (float)**: Total cost incurred for WhatsApp.
    - **email_count (int)**: Total number of emails sent.
    - **email_cost (float)**: Total cost incurred for emails.
    - **grand_total (float)**: Sum of all costs (lead_cost + sms_cost + whatsapp_cost + email_cost).
    - **feature_breakdown (List[Dict])**: List of feature-wise usage:
      - **feature_id (str)**: Unique ID of the feature.
      - **name (str)**: Name of the feature.
      - **total_amount (float)**: Total amount billed for this feature.
      - **college_count (int)**: Number of colleges using this feature.
    - **feature_grand_total (float)**: Sum of all feature billing totals.

    ### Response Body Example
    ```json
    {
      "lead_count": 10,
      "lead_cost": 10.0,
      "lead_limit": 190,
      "sms_count": 10,
      "sms_cost": 29.0,
      "whatsapp_count": 10,
      "whatsapp_cost": 16.6,
      "email_count": 10,
      "email_cost": 11.0,
      "grand_total": 66.6,
      "feature_breakdown": [
        {
          "feature_id": "c2998ac6",
          "name": "Query manager",
          "total_amount": 105.0,
          "college_count": 1
        },
        {
          "feature_id": "aefd607c",
          "name": "Dashboard",
          "total_amount": 120.0,
          "college_count": 1
        }
      ],
      "feature_grand_total": 225.0
    }
    ```
    """
    await UserHelper().is_valid_user(current_user)
    data = jsonable_encoder(data)
    college_object_ids = set([ObjectId(cid) for cid in data.get("college_ids", [])])
    client_college_ids = set()
    if data.get("client_ids"):
        client_object_ids = [ObjectId(cid) for cid in data.get("client_ids")]
        pipeline = [
            {"$match": {
                "associated_client_id": {"$in": client_object_ids}
            }},
            {"$project": {
                "_id": 1
            }}
        ]

        result = await DatabaseConfiguration().college_collection.aggregate(pipeline).to_list(length=None)

        client_college_ids = set([doc["_id"] for doc in result])

    college_object_ids.update(client_college_ids)
    try:
        return await college_details().get_billing_details(list(college_object_ids))
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@client_router.get("/get_colleges")
@requires_feature_permission("read")
async def get_colleges(
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    current_user: dict = Depends(get_current_user_object),
):
    """
    API endpoint to fetch a paginated list of colleges based on the role of the logged-in user.
    Role-based access:
    - Super Account Manager: Retrieves colleges under clients managed by assigned account managers.
    - Account Manager: Retrieves colleges under their directly assigned clients.
    - Client Admin: Retrieves colleges associated with their linked client.
    - Super Admin / Admin: Retrieves all colleges without restriction.
    - Any other role: Access is denied.
    Params:
        page_num (int): Page number for pagination (default is 1).
        page_size (int): Number of items per page (default is 10).
        current_user (dict): The currently authenticated user, automatically injected via dependency.
    Returns:
        JSONResponse: Paginated list of colleges with metadata.
    Raises:
        HTTPException:
            - 401 if the user is unauthorized.
            - 404 if the user is not found.
            - 500 for any unexpected internal error.
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await college_details().fetch_college_by_role(
            user, page_num, page_size
        )
    except HTTPException as exc:
        raise exc
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@client_router.post("/{college_id}/add_course")
@requires_feature_permission("write")
async def add_course_info(
        college: Annotated[
            dict, Depends(get_college_id_short_version(short_version=True))
    ],
    payload: CollegeProgramModel,
    current_user: CurrentUser,
    approval_id: str = Query(None),
):
    """
    add course details

    ### Query Parameter
    **college_id**: Get the college id

    ### Request Body
    - **school_names** (list of strings):
      A list of school names offering the courses (e.g., ["CSE", "ECE"]).
    - **course_lists** (list of Course objects):
      A list of courses, where each course includes the following fields:
      - **course_name** (string):
        Name of the course (2-50 characters, required).
      - **school_name** (optional string):
        Name of the school offering the course (default: None).
      - **course_type** (optional string):
        Type of the course, must be one of "UG", "PG", or "PHD" (default: None).
      - **is_activated** (boolean):
        Whether the course is activated (default: True).
      - **course_activation_date** (string):
        Activation date in YYYY-MM-DD format (e.g., "2025/03/05"), converted to a datetime object.
      - **course_deactivation_date** (string):
        Deactivation date in YYYY-MM-DD format (e.g., "2028/03/28"), converted to a datetime object.
      - **do_you_want_different_form_for_each_specialization** (boolean):
        Whether each specialization requires a different form (default: False).
      - **course_banner_url** (string):
        URL of the course banner (must be a valid URL, e.g., "https://example.com/course_banner.jpg").
      - **course_fees** (float):
        Fees for the course (required, e.g., 5000.50).
      - **specialization_names** (list of CourseSpecialization objects):
        List of specializations, where each specialization includes:
        - **spec_name** (string): Name of the specialization (e.g., "Artificial Intelligence").
        - **is_activated** (boolean): Whether the specialization is activated (e.g., True).
        - **spec_custom_id** (string): Custom ID for the specialization with Branch (e.g., "AI").
      - **duration** (optional integer):
        Duration of the course in years (1-10, default: None).
      - **course_description** (string):
        Description of the course (5-100 characters, default: "").
    - **preference_details** (optional PreferenceDetails object):
      Optional details about the preference-based system:
      - **do_you_want_preference_based_system** (optional boolean):
        Whether to use a preference-based system (default: False).
      - **will_student_able_to_create_multiple_application** (optional boolean):
        Whether students can create multiple applications (default: False).
      - **maximum_fee_limit** (optional integer):
        Maximum fee limit (default: None).
      - **how_many_preference_do_you_want** (optional integer):
        Number of preferences allowed (default: None).
      - **fees_of_trigger** (optional dictionary):
        Fees associated with triggers (e.g., {"trigger_1": 100, "trigger_2": 100}, default: None).

    ### Example Request Body
    ```json
    {
       "school_names": ["CSE", "ECE"],
       "course_lists": [
          {
             "course_name": "BSc Computer Science",
             "school_name": "CSE",
             "course_type": "UG",
             "course_activation_date": "2023-05-03",
             "course_deactivation_date": "2025-05-03",
             "do_you_want_different_form_for_each_specialization": true,
             "course_banner_url": "https://example.com/course_banner.jpg",
             "course_fees": 5000.50,
             "duration": 3,
             "specialization_names": [
                {"spec_name": "Artificial Intelligence", "is_activated": true, "spec_custom_id": "BSAI"},
                {"spec_name": "Cyber Security", "is_activated": true, "spec_custom_id": "BSCY"}
             ],
             "course_description": "A comprehensive program covering computer science fundamentals."
          }
       ],
       "preference_details": {
          "do_you_want_preference_based_system": true,
          "will_student_able_to_create_multiple_application": true,
          "maximum_fee_limit": 20000,
          "how_many_preference_do_you_want": 2,
          "fees_of_trigger": {"trigger_1": 100, "trigger_2": 100}
       }
    }
    ```

    ### Response Body
    - **message**: Success message
    - **OR**
    - **approval_id**: approval request id

    ### Raises:
    HTTPException: if user or college not found
    HTTPException: if custom error occurs
    HTTPException: if any error occurs
    """
    # TODO: Pending the user authentication for super account manager or account manager
    #  because of currently authentication not doing in this sprint.
    if (
        await DatabaseConfiguration().user_collection.find_one(
            {"user_name": current_user.get("user_name")}
        )
        is None
    ):
        raise HTTPException(status_code=404, detail="User not found")
    try:
        return await college_details().add_college_course(
            payload=payload.model_dump(exclude_none=True),
            college=college,
            user=await UserHelper().is_valid_user(current_user),
            approval_id=approval_id,
        )
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except HTTPException as error:
        raise error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@client_router.post("/add_features_screen")
@requires_feature_permission("write")
async def add_client_screen_info(
    payload: MasterScreen,
    current_user: CurrentUser,
    client_id: str = None,
    college_id: str = None,
    approval_id: str = None,
    dashboard_type: str = Query(
        "admin_dashboard",
        description="Type of the dashboard",
        enum=["admin_dashboard", "student_dashboard"],
    ),
):
    """
    add client screen details by the admin or account manager

    Param:
        payload: Get the pydantic model for input the college data from the user
        current_user: Get the current user email and validation exists or not
        college_id (str): get the college id
        client_id: Get the client id
        dashboard_type: Get the dashboard type

    Returns:
        Return success message

    Raises:
        HTTPException: if user not found
        HTTPException: if custom error occurs
        HTTPException: if any error occurs
    """
    # Todo: This API fetch only client, right now this is valid for everyone will implement
    #  soon after the role and permission complete
    try:
        user = await UserHelper().is_valid_user(current_user)
        await utility_obj.check_dashboard_type(dashboard_type)
        if user.get("role", {}).get("role_name") in [
            "client_manager",
            "client_super_admin",
        ]:
            client_id = str(user.get("_id"))
        if college_id:
            await utility_obj.is_length_valid(_id=college_id, name="College id")
            if (
                await DatabaseConfiguration().college_collection.find_one(
                    {"_id": ObjectId(college_id)}
                )
                is None
            ):
                raise DataNotFoundError(message="College")
            screen_type = "college_screen"
        elif client_id:
            await utility_obj.is_length_valid(_id=client_id, name="Client id")
            screen_type = "client_screen"
        else:
            raise CustomError(message="Client id or college_id is mandatory")
        payload = jsonable_encoder(payload)
        payload = utility_obj.clean_data(payload)
        return await Client_screens().add_client_screen(
            payload=payload.get("screen_details", []),
            client_id=client_id,
            screen_type=screen_type,
            college_id=college_id,
            dashboard_type=dashboard_type,
            user=user,
            approval_id=approval_id,
        )
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@client_router.post("/update_feature_screen")
@requires_feature_permission("edit")
async def update_client_screen_info(
    payload: MasterScreen,
    current_user: CurrentUser,
    client_id: str = None,
    college_id: str = None,
    dashboard_type: str = Query("admin_dashboard", description="Type of the dashboard"),
):
    """
    update client screen details by the admin or account manager

    Param:
        payload: Get the pydantic model for input the college data from the user
        current_user: get the current user email and validation exists or not
        college_id (str): get the college id
        client_id: Get the client id
        dashboard_type: Get the dashboard type

    Returns:
        Return success message

    Raises:
        HTTPException: if user not found
        HTTPException: if custom error occurs
        HTTPException: if any error occurs
    """
    # Todo: We will do the user varify here after the role and permission implemented
    try:
        user = await UserHelper().is_valid_user(current_user)
        await utility_obj.check_dashboard_type(dashboard_type)
        if user.get("role", {}).get("role_name") in [
            "client_manager",
            "client_super_admin",
        ]:
            client_id = str(user.get("_id"))
        if college_id:
            await utility_obj.is_length_valid(_id=college_id, name="College id")
            if (
                await DatabaseConfiguration().college_collection.find_one(
                    {"_id": ObjectId(college_id)}
                )
                is None
            ):
                raise DataNotFoundError(message="College")
            screen_type = "college_screen"
        elif client_id:
            await utility_obj.is_length_valid(_id=client_id, name="Client id")
            screen_type = "client_screen"
        else:
            raise CustomError(message="Client id or college_id is mandatory")
        payload = jsonable_encoder(payload)
        payload = payload.get("screen_details", [])
        if not payload:
            raise CustomError(message="Screen detail mandatory")
        payload = utility_obj.clean_data(payload)
        field = f"master_screens/{college_id}/{dashboard_type}" \
            if college_id else f"master_screens/{client_id}/{dashboard_type}"
        return await Client_screens().update_client_screen(
            payload=payload,
            client_id=client_id,
            dashboard_type=dashboard_type,
            screen_type=screen_type,
            college_id=college_id,
            invalidation_route=field
        )
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@client_router.delete("/delete_feature_screen")
@requires_feature_permission("delete")
async def delete_master_screen_details(
    current_user: CurrentUser,
    client_id: str = None,
    college_id: str | None = None,
    feature_id: str = None,
    whole_screen: bool = False,
    dashboard_type: str = Query("admin_dashboard", description="Type of the dashboard"),
):
    """
    delete screen details by the super admin

    Param:
        current_user: get the current user email and validation exists
        client_id: Get the Client id
        college_id (str): Get the college id
        payload (dict): Get the feature id
        whole_screen (str): get the whole screen details

    Returns:
        Return success message

    Raises:
        HTTPException: if user not found
        HTTPException: if any error occurs
    """
    try:
        user = await UserHelper().is_valid_user(current_user)
        await utility_obj.check_dashboard_type(dashboard_type)
        if user.get("role", {}).get("role_name") in [
            "client_manager",
            "client_super_admin",
        ]:
            client_id = str(user.get("_id"))
        if college_id:
            screen_type = "college_screen"
            await utility_obj.is_length_valid(_id=feature_id, name="Feature id")
        elif client_id:
            await utility_obj.is_length_valid(_id=client_id, name="Client id")
            screen_type = "client_screen"
        else:
            raise CustomError(message="College id or client id is mandatory")
        field = f"master_screens/{college_id}/{dashboard_type}" \
            if college_id else f"master_screens/{client_id}/{dashboard_type}"
        return await Master_Service().delete_master_controller(
            feature_id=feature_id,
            client_id=client_id,
            screen_type=screen_type,
            whole_screen=whole_screen,
            college_id=college_id,
            dashboard_type=dashboard_type,
            invalidation_route=field
        )
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"Error in delete_screen_details {error}"
        )


@client_router.get("/get_feature_screen")
@requires_feature_permission("read")
async def get_master_screen_details(
        current_user: CurrentUser,
        client_id: str = None,
        college_id: str | None = None,
        feature_id: str | None = None,
        dashboard_type: str = Query("admin_dashboard", description="Type of the dashboard"),
        page_num: int = Query(None, ge=1),
        page_size: int = Query(None, ge=1),
):
    """
    get screen details by the super admin

    Param:
        current_user: get the current user email and validation exists
        client_id (str): Get the client id
        screen_type: get the screen type
        college_id (str): Get the college id
        feature_id (str): Get the feature id
        dashboard_type: Get the dashboard type
        page_num (int): Get the page number
        page_size (int): Get the page size

    Returns:
        Return success message

    Raises:
        HTTPException: if user not found
        HTTPException: if any error occurs
    """
    # Todo: Changes is pending cause of role and permission.

    try:
        user = await UserHelper().is_valid_user(current_user)
        await utility_obj.check_dashboard_type(dashboard_type)
        if user.get("role", {}).get("role_name") in [
            "client_manager",
            "client_super_admin",
        ]:
            client_id = str(user.get("_id"))
        if college_id:
            await utility_obj.is_length_valid(_id=college_id, name="College id")
            if (
                await DatabaseConfiguration().college_collection.find_one(
                    {"_id": ObjectId(college_id)}
                )
                is None
            ):
                raise DataNotFoundError(message="College")
            screen_type = "college_screen"
            message = "College screen controller details fetched successfully."
        elif client_id:
            await utility_obj.is_length_valid(_id=client_id, name="Client id")
            screen_type = "client_screen"
            message = "Client screen controller details fetched successfully."
        else:
            raise CustomError(message="Client id or college_id is mandatory")
        if not client_id and not college_id:
            raise CustomError(message="College id is mandatory")
        # Todo: This is pending to implement the cache
        # field = f"{college_id}/{dashboard_type}/{page_num}/{page_size}" \
        #     if college_id else f"{client_id}/{dashboard_type}/{page_num}/{page_size}"
        # data = await get_collection_from_cache(collection_name="master_screens", field=field)
        # if not data:
        data = await Master_Service().get_master_controller(
            feature_id=feature_id, client_id=client_id,
            screen_type=screen_type, dashboard_type=dashboard_type,
            college_id=college_id, page_size=page_size, page_num=page_num)
        # await store_collection_in_cache(
        #     collection=data, collection_name="master_screens", field=field)
        return {**data, "message": message}
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@client_router.get("/get_required_feature_roles")
@requires_feature_permission("read")
async def get_master_screen_details(
    current_user: CurrentUser,
    client_id: str = None,
    college_id: str | None = None,
):
    """
    Retrieves required role information for a client's or college's screen configuration.

    This endpoint checks user authorization, fetches screen configuration data from cache (or database if not cached),
    extracts the required role names, and returns them. Either `client_id` or `college_id` must be provided.

    Params:
        current_user (CurrentUser): The currently authenticated user.
        client_id (str, optional): The client identifier. Required if `college_id` is not provided.
        college_id (str | None, optional): The college identifier. Required if `client_id` is not provided.

    Returns:
        dict: A dictionary containing a list of role IDs and names, and a success message.

    Raises:
        HTTPException: With status code 404 if data is not found.
        HTTPException: With status code 422 for validation errors.
        HTTPException: With status code 500 for unexpected server errors.
    """

    # Todo: Current user validation is pending.
    from app.dependencies.oauth import (
        get_collection_from_cache,
        store_collection_in_cache,
    )

    try:
        user = await UserHelper().is_valid_user(current_user)
        if user.get("role", {}).get("role_name") in [
            "client_manager",
            "client_super_admin",
        ]:
            client_id = str(user.get("_id"))
        if not (client_id or college_id):
            raise HTTPException(
                status_code=400, detail="Client id or College id is mandatory"
            )
        if college_id:
            await utility_obj.is_length_valid(_id=college_id, name="College id")
            if (
                await DatabaseConfiguration().college_collection.find_one(
                    {"_id": ObjectId(college_id)}
                )
                is None
            ):
                raise DataNotFoundError(message="College")
            screen_type = "college_screen"
        else:
            await utility_obj.is_length_valid(_id=client_id, name="Client id")
            screen_type = "client_screen"

        data = await get_collection_from_cache(
            collection_name="master_screens",
            field=college_id if college_id else client_id,
        )
        if not data:
            data = await Master_Service().get_master_controller(
                client_id=client_id,
                screen_type=screen_type,
                college_id=college_id,
                get_roles=True
            )
            await store_collection_in_cache(
                collection=data, collection_name="master_screens",
                field=college_id if college_id else client_id)
        required_roles = data.get("roles_required")
        if required_roles is None:
            required_roles = await Client_screens().collect_required_role_names(data)
        return {
            "data": required_roles,
            "message": f"Required roles for the {screen_type.replace('_', ' ')} fetched successfully.",
        }
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except HTTPException as exc:
        raise exc
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@client_router.post("/save_signup_form/{college_id}")
@requires_feature_permission("write")
async def save_signup_form(
    current_user: CurrentUser,
    data: SignupFormRequest,
    college: dict = Depends(get_college_id),
):
    """
    Save student registration form fields into the colleges collection.
    This API endpoint allows a student to submit their registration form,
    which is then stored in the respective college's collection.
    Params:
        college_id (str): The unique identifier of the college where the signup form is being submitted.
        data (SignupFormRequest): The signup form data submitted by the student.
        current_user (User): The authenticated user making the request, retrieved using dependency injection.
    Returns:
        dict: A success response if the form is saved successfully.
              If an error occurs, an HTTPException with status code 400 is raised.
    Raises:
        HTTPException: If an error occurs while saving the form, a 400 status code is returned with an error message.
    """
    try:
        data = jsonable_encoder(data)
        return await college_details().save_signup_form_details(
            college_id=college.get("id"), data=data, current_user=current_user
        )
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@client_router.post("/update_activation_status_of_college")
@requires_feature_permission("edit")
async def update_activation_status_of_college(
    current_user: CurrentUser,
    data: StatusInfo,
    college_id: str = Query(..., description="ID of the college"),
):
    """
    Update the activation status of a college.
    This endpoint allows an authorized user to activate or deactivate a college
    Params:
        data (StatusInfo): Request body containing the `is_activated` status.
        college_id (str): Query parameter representing the college's ObjectId.
        current_user (User): The authenticated user making the request.
    Returns:
        dict: A success message indicating that the college status was updated.
    Raises:
        HTTPException:
            422 - If required fields are missing or invalid.
            404 - If the college is not found.
            500 - If an unexpected server error occurs.
    """
    # TODO:Only Super Account Manager can Perform this Action
    #  Based on RBAC the Authorization & Authentication will change
    try:
        return await college_details().update_activation_status(
            data=data.model_dump(),
            college_id=college_id,
            current_user=current_user
        )
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@client_router.get("/get_screen_details")
@requires_feature_permission("read")
async def get_screen_data(
        current_user: CurrentUser,
        college_id: str = None,
        client_id: str = None,
        page_num: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1),
        dashboard_type: str = Query("admin_dashboard", description="Type of the dashboard",
                                    enum=["admin_dashboard", "student_dashboard"]),
):
    """
    Get the student registration form fields for a specific college.
    This endpoint retrieves the signup form fields for a given college.
    Params:
         college_id (str): The unique identifier of the college.
         client_id (str): The unique identifier of the client (optional).
         current_user (User): The authenticated user making the request.
         page_num (int): The page number for pagination (default: 1).
         page_size (int): The number of items per page for pagination (default: 10).
         dashboard_type (str): The type of dashboard (default: "admin_dashboard").

    Returns:
        dict: A success response containing the signup form fields.
    Raises:
        HTTPException:
            422 - If required fields are missing or invalid.
            404 - If the college is not found.
            500 - If an unexpected server error occurs.
    """
    try:
        user = await UserHelper().is_valid_user(current_user)
        if user.get("role", {}).get("role_name") in [
            "client_manager",
            "client_super_admin",
        ]:
            client_id = user.get("_id")
        if college_id:
            await utility_obj.is_length_valid(_id=college_id, name="College id")
            screen_type = "college_screen"
        elif client_id:
            await utility_obj.is_length_valid(_id=client_id, name="Client id")
            screen_type = "client_screen"
        else:
            screen_type = "master_screen"
        return await Master_Service().get_master_screen_data(
            college_id=college_id,
            screen_type=screen_type,
            client_id=client_id,
            page_num=page_num,
            page_size=page_size,
            dashboard_type=dashboard_type,
        )
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@client_router.get("/list_of_all_colleges")
@requires_feature_permission("read")
async def list_of_all_colleges(
    current_user: CurrentUser,
    page_num: int = Query(1, alias="pageNum"),
    page_size: int = Query(7, alias="pageSize"),
):
    """
    Fetches application form fields along with college details, with pagination.

    Params:
        - page_num (int): The page number for pagination. Default is 1.
        - page_size (int): The number of items per page. Default is 7.
        - current_user (User): The currently authenticated user (retrieved using dependency injection).

    Returns:
        - dict: A dictionary containing:
            - `data` (list): The list of fetched application form fields along with college details.
            - `total` (int): The total number of matching records.
            - `count` (int): The number of records returned in the current page.
            - `pagination` (dict): Pagination details such as next/previous page URLs.
            - `message` (str): A success message.
    """
    try:
        if page_size < 1:
            raise CustomError(message="pageSize must be at least 1")
        college_instance = college_details()
        utility_obj = Utility()
        college_data, total_count = await college_instance.fetch_all_colleges_data(
            current_user, page_num, page_size
        )

        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, total_count, route_name="/list_of_all_colleges"
        )
        return {
            "data": college_data,
            "total": total_count,
            "count": len(college_data),
            "pagination": response.get("pagination", {}),
            "message": "Data fetched successfully",
        }
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@client_router.post("/update_status_of_college/")
@requires_feature_permission("edit")
async def update_status_of_college(
    current_user: CurrentUser,
    status: FormStatus = Query(..., description="Status to update"),
    college_ids: list[str] = Body(..., embed=True)
):
    """
    Update the status of one or more colleges.

    - status: The status to set (`Approved`, `Declined`, or `Pending`)
    - college_ids: List of college IDs to update
    - current_user: The currently authenticated user

    Returns a message indicating how many college(s) were updated.
    """
    try:
        updated_count = await college_details().update_college_status(
            college_ids, status, current_user
        )

        return {
            "message": f"Updated status for {updated_count} college(s) to '{status.value}'",
            "status": status,
            "college_ids": college_ids,
        }
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@client_router.post("/update_color_theme/")
@requires_feature_permission("edit")
async def update_color_theme(
    payload: dict,
    current_user: CurrentUser,
    college_id: dict = Depends(get_college_id_short_version(short_version=True)),
    approval_id: str | None = None
):
    """
    Update the color theme for a specific college.
    Params:
        payload (dict): A dictionary containing the new color theme values to be updated.
        college_id (dict): The ObjectId of the college (injected using dependency `get_college_id_short_version`).
        current_user (User): The currently authenticated user (injected using dependency `get_current_user_object`).
    Returns:
        dict: A success message indicating the color theme has been updated.
    Raises:
        HTTPException (422): If the user is not valid or the ObjectId is invalid.
        HTTPException (404): If the college document is not found in the database.
        HTTPException (500): For unexpected server errors during the update operation.
    """
    try:
        user = await UserHelper().is_valid_user(current_user)
        if user and user.get("role", {}).get("role_name") not in [
            "admin",
            "super_admin",
        ]:
            approval_request = await ApprovalCRUDHelper().create_approval_request(
                user=user,
                request_data={
                    "college_id": ObjectId(college_id.get("id")),
                    "approval_type": "college_color_theme",
                    "payload": payload,
                },
                approval_id=approval_id
            )
            await ApprovedRequestHandler().update_onboarding_details(
                college_id=college_id.get("id"), client_id=None, step_name="color_theme", status="In Progress",
                user=user, approval_request=approval_request,
                request_of="college_color_theme"
            )
            return {
                "message": "Color theme request created successfully.",
                "approval_id": approval_request.get("approval_id") if approval_request else None,
            }
        return {"message": "Color theme updated successfully."}
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@client_router.get("/get_color_theme/{college_id}")
async def get_color_theme(
    college_id: str = Path(..., description="The ID of the college")
):
    """
    Retrieve the color theme for a specific college.
    This endpoint fetches the `color_theme` field for a college based on the provided
    `college_id`. It returns the theme if found.
    Parameters:
        college_id : str
            The ObjectId of the college as a string, passed as a path parameter.
    Returns:
        dict
            A JSON response containing the `color_theme` of the college.
    Raises:
        HTTPException (422)
            If the provided `college_id` is not a valid ObjectId format.
        DataNotFoundError (404)
            If the college or its `color_theme` is not found.
        HTTPException (500)
            If an unexpected database or server error occurs.
    """
    try:
        if not ObjectId.is_valid(college_id):
            raise CustomError(message="Invalid college_id format")
        college = await DatabaseConfiguration().college_collection.find_one(
            {"_id": ObjectId(college_id)}
        )

        if not college:
            raise DataNotFoundError(message="College")

        return {"color_theme": college.get("color_theme", {})}
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@client_router.post("/update_specific_fields")
@requires_feature_permission("edit")
async def update_specific_fields(
        payload: DashboardHelper,
        current_user: CurrentUser,
        college_id: str = Query(None, description="ID of the college"),
        client_id: str = Query(None, description="ID of the client"),
        dashboard_type: str = Query("admin_dashboard", description="Type of the dashboard"),
):
    """
    Update specific fields in the feature.

    Params:
        payload (SpecificFieldUpdate): The fields to update.
        college_id (str): The ID of the college to update.
        client_id (str): The ID of the client to update.
        current_user (User): The currently authenticated user.

    Returns:
        dict: A success message indicating the fields were updated.
    Raises:
        HTTPException:
            422 - If required fields are missing or invalid.
            404 - If the college is not found.
            500 - If an unexpected server error occurs.
    """
    try:
        user = await UserHelper().is_valid_user(current_user)
        await utility_obj.check_dashboard_type(dashboard_type)
        if user.get("role", {}).get("role_name") in [
            "client_manager",
            "client_super_admin",
        ]:
            client_id = str(user.get("_id"))
        if college_id:
            await utility_obj.is_length_valid(_id=college_id, name="College id")
            if (
                    await DatabaseConfiguration().college_collection.find_one(
                        {"_id": ObjectId(college_id)}
                    )
                    is None
            ):
                raise DataNotFoundError(message="College")
            screen_type = "college_screen"
        elif client_id:
            await utility_obj.is_length_valid(_id=college_id, name="Client id")
            screen_type = "client_screen"
        else:
            raise CustomError(message="Client id or college_id is mandatory")
        payload = jsonable_encoder(payload)
        if not payload:
            raise CustomError(message="Screen detail mandatory")
        payload = utility_obj.clean_data(payload)
        return await Client_screens().update_specific_feature_field(
            payload=payload,
            client_id=client_id,
            dashboard_type=dashboard_type,
            screen_type=screen_type,
            college_id=college_id,
        )
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")
