"""
This file contains API routes/endpoints related to master routes for the client automation
Add and update the data in the master schema which will be used by client and admin
"""
import json
from typing import Optional, Dict, Any, List

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.encoders import jsonable_encoder

from app.core import get_logger
from app.core.custom_error import CustomError, DataNotFoundError, ObjectIdInValid
from app.core.utils import utility_obj, CustomJSONEncoder, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import CurrentUser, get_current_user_object
from app.helpers.approval.approval_helper import ApprovalCRUDHelper, ApprovedRequestHandler
from app.helpers.client_automation.master_helper import Master_Service
from app.helpers.master_helper import Master
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.master_schema import MasterStageCreate, MasterStageUpdate, SubStageSchema, \
    ApplicationFormModel, \
    StudentRegistrationFormModel, MasterScreen, StepModel
from app.models.student_user_schema import User

master_router = APIRouter()

logger = get_logger(__name__)


@master_router.post("/create_master_stage")
@requires_feature_permission("write")
async def create_new_master_stage(
        stage: MasterStageCreate,
        current_user: CurrentUser,
) -> Dict[str, Any]:
    """
        Creates a new master stage.
    Params:
         stage: MasterStageCreate - The master stage data to be created.
         current_user: User - The authenticated user making the request.
    Raises:
        CustomError: If the stage creation fails.
        HTTPException: An error occur.
    Return:
        dict - Success message with the created stage ID.
    """
    # TODO:Authorization & Authentication based on RBAC
    try:
        await UserHelper().is_valid_user(current_user)
        stage_data = jsonable_encoder(stage)
        return await Master().create_master_stage(stage_data, current_user)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@master_router.get("/get_all_master_stages")
@requires_feature_permission("read")
async def get_all_master_stages(
        current_user: CurrentUser
):
    """
        Retrieves all master stages.
    Params:
        current_user: User - The authenticated user making the request.
    Return:
        list - A list of all master stages.
    Raises:
        HTTPException: If an error occurs while fetching data.
        DataNotFoundError: If no master stages are found.
    """
    # TODO:Authorization & Authentication based on RBAC
    return await Master().retrieve_all_master_stages(current_user)


@master_router.get("/get_master_stage/{stage_id}")
@requires_feature_permission("read")
async def get_master_stage(
        stage_id: str,
        current_user: CurrentUser
):
    """
        Retrieves a specific master stage by ID.

    Param:
        stage_id: str - The ID of the master stage.
        current_user: User - The authenticated user making the request.
    Raises:
        HTTPException: AN error occur.
        DataNotFoundError: If the master stage is not found.
    Return:
         dict - The master stage details.
    """
    # TODO:Authorization & Authentication based on RBAC
    try:
        stage = await Master().get_master_stage_by_id(stage_id, current_user)
        if not stage:
            raise DataNotFoundError(message="Master stage")
        return stage
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@master_router.put("/update_master_stage/{stage_id}")
@requires_feature_permission("edit")
async def update_master_stages(
        stage_id: str,
        update_data: MasterStageUpdate,
        current_user: CurrentUser
) -> Dict[str, Any]:
    """
       Updates master stage details based on provided data.
    Params:
        stage_id: str - The ID of the master stage.
        update_data: MasterStageUpdate - The data to update the master stage.
        current_user: User - The authenticated user making the request.
    Raises:
        HTTPException: If the stage ID is invalid, does not exist, or update fails.
    Return:
        dict - Success message after updating.
    """
    # TODO:Authorization & Authentication based on RBAC
    try:
        update_data_dict = update_data.model_dump(exclude_unset=True)
        response = await Master().update_master_stage(stage_id, update_data_dict, current_user)
        return response
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")

    except CustomError as error:
        raise HTTPException(status_code=400, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@master_router.delete("/delete_master_stage/{stage_id}")
@requires_feature_permission("delete")
async def delete_master_stage(
        stage_id: str,
        current_user: CurrentUser
):
    """
        Deletes a master stage by ID.

    Params:
         stage_id: str - The ID of the master stage to delete.
        current_user: User - The authenticated user making the request.
    Raises:
         HTTPException: If the master stage is not found.
    Return:
        dict - Success message confirming deletion.
    """
    # TODO:Authorization & Authentication based on RBAC
    return await Master().delete_master_stage_by_id(stage_id, current_user)


@master_router.post("/create_master_sub_stage")
@requires_feature_permission("write")
async def create_master_sub_stage(
        sub_stage: SubStageSchema,
        current_user: CurrentUser):
    """
        Creates a new sub stage.
    Params:
        sub_stage: SubStageSchema - The sub stage data to be created.
        current_user: User - The authenticated user making the request.
    Raises:
         HTTPException: An error occur.
         DataNotFoundError: If the master stage is not found.
         CustomError: If the sub stage creation fails.
    Return:
        dict - Success message with the created sub stage ID.
    """
    # TODO: Authorization & Authentication based on RBAC
    try:
        sub_stage_data = jsonable_encoder(sub_stage)
        response = await Master().create_sub_stage(sub_stage_data, current_user)
        return response
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except CustomError as error:
        raise HTTPException(status_code=400, detail=f"{error.message}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(exc)}")


@master_router.get("/get_master_sub_stage/{sub_stage_id}")
@requires_feature_permission("read")
async def get_master_sub_stage(
        sub_stage_id: str,
        current_user: CurrentUser
):
    """
        Retrieves a specific master stage by ID.

    Param:
        sub_stage_id: str - The ID of the master stage.
        current_user: User - The authenticated user making the request.

    Raises
        DataNotFoundError : If the master stage is not found.
        HTTPException: An error occur.
    Return:
        dict - The master stage details.
    """
    # TODO:Authorization & Authentication based on RBAC
    sub_stage = await Master().get_sub_stage(sub_stage_id, current_user)
    try:
        if not sub_stage:
            raise DataNotFoundError(message="Master stage")
        return sub_stage
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@master_router.get("/get_all_master_sub_stages")
@requires_feature_permission("read")
async def get_all_master_sub_stages(current_user: CurrentUser):
    """
        Retrieves all master sub stage.
    Params:
        current_user: User - The authenticated user making the request.
    Raises:
        HTTPException: An error occur.
    Return:
        list - A list of all master sub stage.
    """
    # TODO:Authorization & Authentication based on RBAC
    return await Master().get_all_sub_stages(current_user)


@master_router.put("/update_master_sub_stage/{sub_stage_id}")
@requires_feature_permission("edit")
async def update_master_sub_stages(sub_stage_id: str, update_data: SubStageSchema,
                                   current_user: CurrentUser):
    """
       Updates master sub stage details based on provided data.

    Params:
        sub_stage_id: str - The ID of the master sub stage.
        update_data: MasterStageUpdate - The data to update the master sub stage.
        current_user: User - The authenticated user making the request.
    Raises:
        HTTPException: An error occur.
        DataNotFoundError: If the master sub stage is not found.
        CustomError: If the update fails.
    Return:
        dict - Success message after updating.
    """
    # TODO:Authorization & Authentication based on RBAC
    try:
        update_data_dict = update_data.model_dump(exclude_unset=True)
        response = await Master().update_master_sub_stage(sub_stage_id, update_data_dict,
                                                          current_user)
        return response
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except CustomError as error:
        raise HTTPException(status_code=400, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@master_router.delete("/delete_master_sub_stage/{sub_stage_id}")
@requires_feature_permission("delete")
async def delete_master_sub_stage(sub_stage_id: str,
                                  current_user: CurrentUser):
    """
        Deletes a master stage by ID.
    Params:
        stage_id: str - The ID of the master stage to delete.
        current_user: User - The authenticated user making the request.
    Raises:
         HTTPException: An error occur
    Return:
         dict - Success message confirming deletion.
    """
    # TODO:Authorization & Authentication
    return await Master().delete_master_sub_stage_by_id(sub_stage_id, current_user)


@master_router.post("/validate_key_name")
@requires_feature_permission("edit")
async def validate_key_name(
    current_user: CurrentUser,
    key_name: str,
    client_id: Optional[str] = Query(None, alias="clientId"),
    college_id: Optional[str] = Query(None, alias="collegeId"),
    ):
    """
        Endpoint to validate the uniqueness and format of a given key name used for application fields.
        Parameters:
            key_name (str): The key name to validate. It must follow snake_case format
                            (e.g., 'father_name', 'tenth_marks').
            client_id (Optional[str]): The client identifier. Required if college_id is not provided.
            college_id (Optional[str]): The college identifier. Required if client_id is not provided.
            current_user (User): The currently authenticated user making the request.
        Returns:
            dict: A message indicating whether the key name is unique.
        Raises:
            HTTPException 404: If no related data is found during validation.
            HTTPException 422: If the key name format is invalid, already exists, or if both client_id
                               and college_id are missing.
            HTTPException 500: For any unexpected server-side error.
        """
    try:
        return await Master().check_key_name_uniqueness(key_name=key_name,
                                                        current_user=current_user,
                                                        client_id=client_id,
                                                        college_id=college_id)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@master_router.get("/Retrieve_all_stages_and_sub_stages", summary="Get all stages and sub-stages")
@requires_feature_permission("read")
async def fetch_stages_and_sub_stages_data(current_user: CurrentUser):
    """
       Retrieve all master stages and their associated sub stage.
    Params:
        current_user (User): The authenticated user making the request.
    Returns:
        dict: A dictionary containing all stages and sub stage.
    Raises:
        HTTPException: If an error occurs while fetching data from the database.
    """
    try:
        result = await Master().get_stages_sub_stages_data(current_user)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@master_router.post("/add_master_screen")
@requires_feature_permission("write")
async def add_screen_info(
        current_user: CurrentUser,
        payload: MasterScreen,
        dashboard_type: str = Query("admin_dashboard", alias="dashboard_type"),
):
    """
    add screen details by the super admin

    Param:
        payload: Get the pydantic model for input the screen data from the user
        current_user: get the current user email and validation exists or not
        dashboard_type: get the dashboard type (admin_dashboard or student_dashboard)

    Returns:
        Return success message

    Raises:
        HTTPException: if user not found
        HTTPException: if any error occurs
    """
    # TODO: We will change this admin validation based on rbac implementation
    await UserHelper().is_valid_user(current_user)
    try:
        await utility_obj.check_dashboard_type(dashboard_type)
        payload = jsonable_encoder(payload)
        payload = utility_obj.clean_data(payload)
        screen_info = payload.get("screen_details", [])
        if screen_info:
            return await Master_Service().create_master_controller(
                payload=screen_info, screen_type="master_screen",
                dashboard_type=dashboard_type,
                invalidation_route=f"master_screens/{dashboard_type}")
        else:
            raise CustomError("Screen details must be required")
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Error in add_screen_info {error}")


@master_router.post("/update_master_screen")
@requires_feature_permission("edit")
async def update_screen_info(
        current_user: CurrentUser,
        payload: MasterScreen,
        dashboard_type: str = Query("admin_dashboard", alias="dashboard_type"),
):
    """
    update screen details by the super admin

    Param:
        payload: Get the pydantic model for input the screen data from the user
        current_user: get the current user email and validation exists or not
        dashboard_type: get the dashboard type admin_dashboard or student_dashboard

    Returns:
        Return success message

    Raises:
        HTTPException: if user not found
        HTTPException: if any error occurs
    """
    try:
        await UserHelper().is_valid_user(current_user)
        await utility_obj.check_dashboard_type(dashboard_type)
        payload = jsonable_encoder(payload)
        payload = utility_obj.clean_data(payload)
        return await Master_Service().update_master_controller(
            payload=payload, screen_type="master_screen",
            dashboard_type=dashboard_type,
            invalidation_route=f"master_screens/{dashboard_type}")
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Error in update_screen_info {error}")


@master_router.delete("/delete_master_screen")
@requires_feature_permission("delete")
async def delete_master_screen_details(
        current_user: CurrentUser,
        feature_id: str = None,
        dashboard_type: str = Query("admin_dashboard", alias="dashboard_type"),
        whole_screen: bool = False
):
    """
    delete screen details by the super admin

    Param:
        current_user: get the current user email and validation exists
        whole_screen: get the whole screen details
        dashboard_type: get the dashboard type admin_dashboard or student_dashboard

    Returns:
        Return success message

    Raises:
        HTTPException: if user not found
        HTTPException: if any error occurs
    """
    try:
        await UserHelper().is_valid_user(current_user)
        await utility_obj.check_dashboard_type(dashboard_type)
        return await Master_Service().delete_master_controller(
            screen_type="master_screen",
            feature_id=feature_id,
            whole_screen=whole_screen,
            dashboard_type=dashboard_type,
            invalidation_route=f"master_screens/{dashboard_type}")
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(status_code=500,
                            detail=f"Error in delete_master_screen_details {error}")


@master_router.get("/get_master_screen")
@requires_feature_permission("read")
async def get_master_screen_details(
        current_user: CurrentUser,
        feature_id: str | None = None,
        dashboard_type: str = Query("admin_dashboard", alias="dashboard_type"),
):
    """
    get screen details by the super admin

    Param:
        current_user: get the current user email and validation exists
        feature_id: get the dashboard id
        dashboard_type: get the dashboard type admin_dashboard or student_dashboard

    Returns:
        Return success message

    Raises:
        HTTPException: if user not found
        HTTPException: if any error occurs
    """
    try:
        await UserHelper().is_valid_user(current_user)
        await utility_obj.check_dashboard_type(dashboard_type)
        # Todo: Uncomment this when we implement the cache
        # data = await get_collection_from_cache(
        #     collection_name="master_screens", field=f"{dashboard_type}")
        # if not data:
        data = await Master_Service().get_master_controller(
            feature_id=feature_id, screen_type="master_screen",
            dashboard_type=dashboard_type)
        # await store_collection_in_cache(
        #     collection=data, collection_name="master_screens",
        #     field=f"{dashboard_type}")
        return {"data": data, "message": "Master screen controller details fetched successfully."}
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(status_code=500,
                            detail=f"Error in get_master_screen_details {error}")


@master_router.get("/retrieve_all_stages")
@requires_feature_permission("read")
async def get_retrieve_all_stages(
        current_user: CurrentUser, client_id: str = None,
        college_id: str = None,
):
    """
        Retrieves all stages and sub-stages for a given client or college.

        This endpoint returns a structured representation of the stages and sub-stages,
        typically used to display progress tracking or workflow steps on the student dashboard.

        Params:
            current_user (CurrentUser): The currently authenticated user.
            client_id (str): The unique identifier of the client.
            college_id (str, optional): The unique identifier of the college, if applicable.

        Returns:
            dict: A dictionary containing all stages and their corresponding sub-stages.

        Raises:
            HTTPException: If the user is unauthorized or the data cannot be retrieved.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await Master_Service().get_stages_data(college_id, client_id)
    except CustomError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@master_router.get("/fetch_list_of_all_fields")
@requires_feature_permission("read")
async def fetch_list_of_all_fields(
        current_user: CurrentUser,
        page_num: int = Query(1, alias="pageNum"),
        page_size: int = Query(7, alias="pageSize"),
        search: Optional[str] = None,
):
    """
       Fetches application form fields from the database with optional search and pagination.
       Params:
           page_num (int): The page number for pagination. Default is 1.
           page_size (int): The number of items per page. Default is 7.
           search (Optional[str]): A search keyword to filter the results. Default is None.
           current_user (User): The currently authenticated user (retrieved using dependency injection).
       Returns:
           dict: A dictionary containing:
               - `data` (list): The list of fetched application form fields.
               - `total` (int): The total number of matching records.
               - `count` (int): The number of records returned in the current page.
               - `pagination` (dict): Pagination details such as next/previous page URLs.
               - `message` (str): A success message.
    """
    master_instance = Master()
    result, count = await master_instance.get_application_fields(current_user, page_num, page_size,
                                                                 search)

    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, count, route_name="/fetch_list_of_all_fields"
    )

    return {
        "data": result,
        "total": count,
        "count": len(result),
        "pagination": response["pagination"],
        "message": "Data fetched successfully",
    }


@master_router.post("/validate_registration_form")
@requires_feature_permission("edit")
async def update_client_or_college_registration_form_Data(
        current_user: CurrentUser,
        registration_data: StudentRegistrationFormModel = Body(...),
        client_id: str = None,
        college_id: str = None,
        approval_id: str = None
):
    """
        Validates the Registration form for a specific client or college.

        This endpoint allows an authenticated user to update the Registration form data
        for either a client or a college, depending on the provided identifiers.

        Params:
            client_id (str): The unique identifier of the client whose form data is to be updated.
            form_data (ApplicationFormModel): The updated application form data sent in the request body.
            college_id (str, optional): The unique identifier of the college, if applicable.
            current_user (User): The currently authenticated user, injected via dependency.

        Returns:
            dict: A response indicating the success or failure of the Validation operation.

        Raises:
            HTTPException: If the client or college is not found or the user is unauthorized.
    """
    user = await UserHelper().is_valid_user(current_user)
    application_form = jsonable_encoder(registration_data)
    application_form = application_form.get("student_registration_form_fields", [])
    try:
        key_names = [field["key_name"] for field in application_form if field.get("key_name")]
        if len(key_names) != len(set(key_names)):
            return {"valid": False, "error": "Duplicate field found in the form."}
        key_names = set(key_names)
        if "full_name" not in key_names:
            return {"valid": False, "error": "Missing required field: full_name"}

        if not {"email"} & key_names:
            return {"valid": False, "error": "Either 'email' must be present."}
        # if not {"email", "mobile_number"}.issubset(key_names):
        #     return {"valid": False, "error": "Both 'email' and 'mobile_number' must be present."}
        if user and user.get("role", {}).get("role_name") not in [
            "admin",
            "super_admin",
        ]:
            approval_request = await ApprovalCRUDHelper().create_approval_request(user, {
                "payload": jsonable_encoder(registration_data, exclude_none=False),
                **({"client_id": ObjectId(client_id)} if client_id is not None else {}),
                **({"college_id": ObjectId(college_id)} if college_id is not None else {}),
                "approval_type": "college_student_registration_form" if college_id else
                "client_student_registration_form"
            }, approval_id=approval_id)
            await ApprovedRequestHandler().update_onboarding_details(
                college_id=college_id, client_id=client_id, step_name="registration_form", status="In Progress",
                user=user, approval_request=approval_request,
                request_of="college_student_registration_form" if college_id else "client_student_registration_form"
            )
            return {"valid": True, "message": "Field validation passed and Request Sent Successfully.",
                    "approval_id": approval_request.get("approval_id")}
        else:
            await Master_Service().update_registration_data(college_id, client_id,
                                                            {"student_registration_form_fields": application_form})

            return {"valid": True, "message": "Field validation passed and Updated Details."}
    except CustomError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@master_router.post("/validate_client_or_college_form_data")
@requires_feature_permission("edit")
async def update_client_or_college_form_Data(
        current_user: CurrentUser,
        client_id: str = None,
        application_form: List[StepModel] = Body(...),
        course_name: str = Body(None),
        category: str = Body(None),
        college_id: str = None,
        approval_id: str = None,
):
    """
        Validates the form data for a specific client or college.

        This endpoint allows an authenticated user to update the application form data
        for either a client or a college, depending on the provided identifiers.

        Params:
            client_id (str): The unique identifier of the client whose form data is to be updated.
            form_data (ApplicationFormModel): The updated application form data sent in the request body.
            college_id (str, optional): The unique identifier of the college, if applicable.
            current_user (User): The currently authenticated user, injected via dependency.
            course_name (str): The name of course on which form is being saved
            category (str): The category on which form is being saved

        Returns:
            dict: A response indicating the success or failure of the update operation.

        Raises:
            HTTPException: If the client or college is not found or the user is unauthorized.
    """
    user = await UserHelper().is_valid_user(current_user)
    application_form = jsonable_encoder(application_form)
    application_form = {
        "application_form": application_form,
        "course_name": course_name,
        "category": category
    }
    try:
        return await Master_Service().update_client_or_college_form_data(college_id, client_id,
                                                                         application_form,
                                                                         request="validate",
                                                                         user=user,
                                                                         approval_id=approval_id
                                                                         )
    except CustomError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@master_router.post("/update_client_or_college_form_data")
@requires_feature_permission("edit")
async def update_client_or_college_form_Data(
        current_user: CurrentUser,
        client_id: str,
        form_data: ApplicationFormModel = Body(...),
        college_id: str = None,
):
    """
        Updates the form data for a specific client or college.

        This endpoint allows an authenticated user to update the application form data
        for either a client or a college, depending on the provided identifiers.

        Params:
            client_id (str): The unique identifier of the client whose form data is to be updated.
            form_data (ApplicationFormModel): The updated application form data sent in the request body.
            college_id (str, optional): The unique identifier of the college, if applicable.
            current_user (User): The currently authenticated user, injected via dependency.

        Returns:
            dict: A response indicating the success or failure of the update operation.

        Raises:
            HTTPException: If the client or college is not found or the user is unauthorized.
    """
    user = await UserHelper().is_valid_user(current_user)
    application_form = jsonable_encoder(form_data)
    try:
        return await Master_Service().update_client_or_college_form_data(college_id, client_id,
                                                                         application_form,
                                                                         request="update", user=user,
                                                                         )
    except CustomError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@master_router.get("/get_form_options")
@requires_feature_permission("read")
async def get_form_options(
        option_id: str,
        current_user: CurrentUser,
):
    """
        Retrieves a specific form option configuration by its ID.

        This endpoint fetches the details of a form option associated with the given `option_id`.
        The user must be authenticated to access this endpoint.

        Params:
            option_id (str): The unique identifier of the form option to retrieve.
            current_user (User): The currently authenticated user, injected via dependency.

        Returns:
            dict: A dictionary containing the form option details if found.

        Raises:
            HTTPException: If the form option does not exist or the user is unauthorized.
    """
    await utility_obj.is_id_length_valid(option_id, name="Form Option")
    try:
        if (data := await DatabaseConfiguration().form_options.find_one(
                {"_id": ObjectId(option_id)})) is not None:
            return json.loads(json.dumps(data, cls=CustomJSONEncoder))
        raise CustomError(message="Data not Found!")
    except CustomError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@master_router.post("/create_form_option")
@requires_feature_permission("write")
async def create_form_options(
        current_user: CurrentUser,
        name: str,
        data: list = Body(),
):
    """
        Creates a new form option based on the provided field data.
        This endpoint allows authenticated users to define a new form option set,
        associated with a given name, and based on a list of field definitions or values.

        Params:
            name (str): The name identifier for the form option set.
            data (list): A list of field options or configurations (passed in request body).
            current_user (User): The currently authenticated user, injected via dependency.

        Returns:
            dict: A confirmation message or the created form option details.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        data = await DatabaseConfiguration().form_options.insert_one({
            "name": name,
            "data": data
        })
        return {
            "message": "Inserted Form Option Data!",
            "_id": str(data.inserted_id)
        }
    except CustomError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@master_router.get("/return_api_functions")
@requires_feature_permission("read")
async def return_api_function(
        current_user: CurrentUser,
        client_id: str = None,
        college_id: str = None,
):
    """
        Creates a new form option based on the provided field data.
        This endpoint allows authenticated users to define a new form option set,
        associated with a given name, and based on a list of field definitions or values.

        Params:
            client_id (str): Unique id of client
            college_id (str): Unique id of college
            current_user (User): The currently authenticated user, injected via dependency.

        Returns:
            dict: A confirmation message or the created form option details.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return {"data": await Master_Service().get_api_functions(college_id, client_id),
                "message": "API Functions"}
    except CustomError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@master_router.get("/get_all_templates/")
@requires_feature_permission("read")
async def get_all_templates(current_user: CurrentUser):
    """
       Retrieve all application form templates.
       Params:
           current_user (User): The authenticated user object injected by FastAPI's dependency system.
       Returns:
           List[Dict]: A list of application form templates containing step names, sections, and field details.
       Raises:
           HTTPException (404): If no templates are found in the database.
           HTTPException (422): If a custom application-level error occurs.
           HTTPException (500): If any unexpected server error occurs.
    """
    try:
        return await Master().get_application_form_templates(current_user)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@master_router.get("/get_user_registration_fields")
@requires_feature_permission("read")
async def fetch_registration_fields(
        current_user: CurrentUser,
        role_id: Optional[int] = Query(default=None, gt=0),
):
    """
    Fetch user registration fields based on role.

    - If `role_id` is provided, returns both common fields and role-specific fields.
    - If `role_id` is not provided, returns only the common fields.
    - Ensures that the current user is authenticated and valid.

    Params:
        role_id (Optional[int]): Role ID to fetch role-specific fields (optional).
        current_user (User): Authenticated user, injected via dependency.

    Returns:
        List[dict]: List of fields required for user registration.

    Raises:
        HTTPException: If user is invalid or an error occurs during field retrieval.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await Master_Service().get_fields_by_role(role_id)
    except HTTPException as exr:
        raise exr
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@master_router.post("/create_user")
@requires_feature_permission("write")
async def create_user(
        role_id: str,
        user_data: dict = Body(...),
        current_user=Depends(get_current_user_object)
):
    """
    Create a new user based on dynamic fields associated with the target role.

    - Validates the role ID and permissions based on the current user's role.
    - Retrieves and validates dynamic fields for the target role.
    - Saves the user with appropriate field data.

    Params:
        role_id (str): The ID of the target role to assign to the new user.
        user_data (Dict): Key-value pairs representing dynamic user fields.
        current_user (Dict): The authenticated user's data.

    Returns:
        dict: A success message if the user is created.
    """
    try:
        return await Master_Service().create_user_dynamically(current_user, role_id, user_data)
    except HTTPException as exc:
        raise exc
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Something went wrong: {e}")
