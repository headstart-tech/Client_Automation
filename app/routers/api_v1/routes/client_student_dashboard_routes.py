"""
This module defines API endpoints for managing client-specific stages and sub-stage
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder

from app.core.custom_error import CustomError, DataNotFoundError
from app.core.utils import utility_obj, requires_feature_permission
from app.dependencies.oauth import CurrentUser
from app.helpers.client_student_dashboard_helper import  Client
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.client_student_dashboard_schema import ClientStageCreate, \
    SubStageSchema, ClientStageUpdate, MoveFieldRequest, CustomFieldSchema, RemoveFieldRequest
from app.models.student_user_schema import User

client_router = APIRouter()


@client_router.post("/set_default_client_stages")
@requires_feature_permission("write")
async def set_default_client_stages(current_user: CurrentUser):
    """
        API to set default client stages.
        This endpoint sets the default client stages for the currently authenticated user.
        Params:
            current_user (User): The currently authenticated user, obtained via dependency injection.
        Returns:
            dict: A success message if the operation is successful.
        Raises:
            HTTPException: If the client ID is not found for the user (400).
            HTTPException: If there is an error while setting default client stages (500).
        """
    try:
        user = await UserHelper().is_valid_user(current_user)
        client_id = user.get("associated_client")
        if not client_id:
            raise DataNotFoundError(message="Client ID")
        result = await Client().default_client_stages(client_id,current_user)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@client_router.post("/create_client_stage")
@requires_feature_permission("write")
async def create_new_client_stage(
    client_stage: ClientStageCreate,
    current_user: CurrentUser
):
    """
    Creates client-specific stages by inheriting from master stages.

    - Fetches the `client_id` from the `current_user`
    - Copies master stages with unique `stage_id` for each client
    - Ensures no duplicate stage names/orders within the client's stages
    """
    try:
        user= await UserHelper().is_valid_user(current_user)
        client_id = user.get("associated_client")
        if not client_id:
            raise DataNotFoundError(message="Client ID")

        response = await Client().create_client_stage(client_id, client_stage)
        return response
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@client_router.get("/get_all_client_stages")
@requires_feature_permission("read")
async def get_all_client_stages(current_user: CurrentUser):
    """
        Retrieves all client-specific stages for the authenticated user.
        This API fetches all stages associated with the client's ID, along with sub-stage details.
        Params:
            current_user (User): The currently authenticated user, obtained via dependency injection.
        Returns:
            list: A list of client stages in a structured format.
        Raises:
            HTTPException (400): If the client ID is not found for the authenticated user.
            HTTPException (422): If there is a validation or business logic error.
            HTTPException (500): If an unexpected server error occurs.
    """
    try:
        return await Client().retrieve_all_client_stages(current_user)
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@client_router.get("/get_client_stage/{stage_id}")
@requires_feature_permission("read")
async def get_client_stage(stage_id: str, current_user: CurrentUser):
    """
       Retrieves a specific client stage by ID.
       Params:
           stage_id (str): The ID of the client stage.
           current_user (User): The currently authenticated user, obtained via dependency injection.
       Returns:
           dict: The client stage details.
       Raises:
           HTTPException: If the client stage is not found (404).
           HTTPException: If any unexpected error occurs (500).
       """
    try:
        stage = await Client().get_client_stage_by_id(stage_id, current_user)
        if not stage:
            raise DataNotFoundError(message="Client stage")
        return stage
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@client_router.put("/update_client_stage/{stage_id}")
@requires_feature_permission("edit")
async def update_client_stage(stage_id: str, update_data: ClientStageUpdate, current_user: CurrentUser):
    """
        Updates client stage details based on provided data.
        Params:
            stage_id (str): The ID of the client stage.
            update_data (ClientStageUpdate): The data to update the client stage.
            current_user (dict): The currently authenticated user.
        Returns:
            dict: Success message after updating.
        Raises:
            HTTPException: If the stage ID is invalid, does not exist, or update fails.
        """
    try:
        update_data_dict = update_data.model_dump(exclude_unset=True)
        response = await Client().update_client_stages(stage_id, update_data_dict, current_user)
        return response
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@client_router.delete("/delete_client_stage/")
@requires_feature_permission("delete")
async def delete_client_stage(client_id: str, stage_id: str, current_user: CurrentUser):
    """
       Deletes a client stage by client ID and stage ID.
       Params:
           client_id (str): The ID of the client.
           stage_id (str): The ID of the client stage to delete.
           current_user (User): The authenticated user performing the deletion.
       Raises:
           HTTPException (404): If the client stage is not found.
           HTTPException (401): If the user is unauthorized.
       Returns:
           dict: A success message confirming the deletion.
       """
    try:
        return await Client().delete_client_stage_by_id(client_id, stage_id, current_user)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@client_router.post("/set_default_client_sub_stages")
@requires_feature_permission("write")
async def set_default_client_sub_stages(current_user: CurrentUser):
    """
       API to set default client sub-stages.
       This endpoint sets the default sub-stages for a client associated with the authenticated user.
       Params:
           current_user (User): The authenticated user making the request.
       Raises:
           HTTPException (400): If the client ID is not found for the user.
           HTTPException (500): If an error occurs while setting default sub-stages.
       Returns:
           dict: A success message or error details.
       """
    try:
        user = await UserHelper().is_valid_user(current_user)
        client_id = user.get("associated_client")
        if not client_id:
            raise DataNotFoundError(message="Client ID")
        result = await Client().default_client_sub_stages(client_id, current_user)
        if "error" in result:
            raise CustomError(result["error"])
        return result
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in setting default Client sub stages: {str(e)}")


@client_router.post("/create_client_sub_stage")
@requires_feature_permission("write")
async def create_client_sub_stage(sub_stage: SubStageSchema, current_user: CurrentUser):
    """
        Creates a new client sub-stage.
        Params:
         sub_stage: SubStageSchema - The sub-stage data to be created.
        Raises:
         HTTPException: If sub-stage creation fails.
        Return: dict - Success message with the created sub-stage ID.
    """
    try:
        user = await UserHelper().is_valid_user(current_user)
        client_id = user.get("associated_client")
        if not client_id:
            raise CustomError(message="Client ID not found for the user.")
        sub_stage_data = jsonable_encoder(sub_stage)
        response = await Client().create_sub_stage(client_id, sub_stage_data, current_user)
        return response
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@client_router.get("/get_all_client_sub_stages/")
@requires_feature_permission("read")
async def get_all_client_sub_stages(current_user: CurrentUser):
    """
        Retrieves all sub-stages for a specific client.
        Returns:
         list[dict]: A list of sub-stage objects with formatted fields.
    """
    # TODO: Authorization & Authentication based on RBAC
    try:
        return await Client().get_all_sub_stages_for_client(current_user)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@client_router.get("/get_client_sub_stage/")
@requires_feature_permission("read")
async def get_client_sub_stage(sub_stage_id: str, current_user: CurrentUser):
    """
        Retrieves a specific client sub-stage by its ID.
        This endpoint fetches details of a client sub-stage using the provided sub-stage ID.
        Params:
            sub_stage_id (str): The ID of the sub-stage to retrieve.
            current_user (User): The authenticated user making the request.
        Raises:
            HTTPException (404): If the sub-stage is not found.
        Returns:
            dict: The details of the requested sub-stage.
        """
    try:
        sub_stage = await Client().get_client_sub_stage(sub_stage_id, current_user)

        if not sub_stage:
            raise DataNotFoundError(message="Client sub-stage")
        return sub_stage
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@client_router.put("/update_client_sub_stage/{sub_stage_id}")
@requires_feature_permission("edit")
async def update_client_sub_stages(
    sub_stage_id: str,
    update_data: SubStageSchema,
    current_user: CurrentUser
):
    """
    Updates client sub-stage details based on provided data.
    Params:
        sub_stage_id: str - The ID of the client sub-stage.
        update_data: SubStageSchema - The data to update the client sub-stage.
    Raises:
        HTTPException: If the sub-stage ID is invalid, does not exist, or update fails.
    Returns:
        dict - Success message after updating.
    """
    try:
        update_data_dict = update_data.model_dump(exclude_unset=True)
        response = await Client().update_client_sub_stage(sub_stage_id, update_data_dict, current_user)
        return response
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@client_router.delete("/delete_client_sub_stage/")
@requires_feature_permission("delete")
async def delete_client_sub_stage(sub_stage_id: str, current_user: CurrentUser):
    """
    Deletes a client sub-stage by ID.
    Params:
        sub_stage_id: str - The ID of the client sub-stage to delete.
        client_id: str - The ID of the client.
        current_user: User - The currently authenticated user.
    Raises:
        HTTPException: If the client sub-stage is not found.
    Returns:
        dict - Success message confirming deletion.
    """
    try:
        return await Client().delete_client_sub_stage_by_id(sub_stage_id, current_user)
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@client_router.post("/remove_fields")
@requires_feature_permission("edit")
async def remove_fields(client_id: str, request: RemoveFieldRequest, current_user: CurrentUser):
    """
        Removes specified fields from a client record.
        Params:
            client_id (str): The ID of the client whose fields need to be removed.
            request (RemoveFieldRequest): A request object containing the fields to be removed.
        Returns:
            dict: A success message or an error response.
        """
    try:
        return await Client().remove_fields_from_section(client_id, request.section_title, request.key_names,
                                                         current_user)
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@client_router.patch("/relocate_field")
@requires_feature_permission("edit")
async def relocate_field(request: MoveFieldRequest, current_user: CurrentUser,
                         client_id: str, college_id:str=None):
    """
        Relocates a specific field within a client's record.
        Params:
            client_id (str): The ID of the client whose field needs to be relocated.
            college_id (str): The ID of the college whose field needs to be relocated.
            request (MoveFieldRequest): A request object containing details of the field relocation.
        Returns:
            dict: A success message or an error response.
        """
    if not client_id and not college_id:
        raise CustomError(message="Either client_id or college_id must be provided")

    if college_id and not client_id:
        raise CustomError(message="college_id requires client_id")
    try:
        return await Client().relocate_field_helper(request, client_id, college_id ,current_user)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=f"{error.message}")
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@client_router.get("/fetch_list_of_all_fields")
@requires_feature_permission("read")
async def fetch_list_of_all_fields(
    current_user: CurrentUser,
    page_num: int = Query(1, alias="pageNum"),
    page_size: int = Query(7, alias="pageSize"),
    search: Optional[str] = None,
    client_id: Optional[str] = Query(None, alias="clientId"),
    college_id: Optional[str] = Query(None, alias="collegeId"),
):
    """
    Fetches application form fields from the database with optional search and pagination.
    Params:
        page_num (int): The page number for pagination. Default is 1.
        page_size (int): The number of items per page. Default is 7.
        search (Optional[str]): A search keyword to filter the results. Default is None.
        client_id (Optional[str]): The client ID to filter application form fields.
        college_id (Optional[str]): The college ID to filter application form fields.
        current_user (User): The currently authenticated user.
    Returns:
        dict: A dictionary containing:
            - `data` (list): The list of fetched application form fields.
            - `total` (int): The total number of matching records.
            - `count` (int): The number of records returned in the current page.
            - `pagination` (dict): Pagination details such as next/previous page URLs.
            - `message` (str): A success message.
    """
    try:
        if not client_id and not college_id:
            raise CustomError(message="Either clientId or collegeId must be provided")

        client_instance = Client()
        result, count = await client_instance.get_all_fields(
            current_user=current_user,
            client_id=client_id,
            college_id=college_id,
            page_num=page_num,
            page_size=page_size,
            search=search,
        )
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
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@client_router.post("/custom_field/")
@requires_feature_permission("write")
async def create_custom_field(
    current_user: CurrentUser,
    field_data: CustomFieldSchema,
    client_id: str = Query(None, description="The unique identifier of the client"),
    college_id: str = Query(None, description="The unique identifier of the college"),
    existing_key_name: str = Query(None, description="Optional: Provide this to update an existing custom field"),
):
    """
    API endpoint to create a custom field for a client or college.

    Parameters:
        field_data (CustomFieldSchema): The schema containing the details of the custom field to be created.
        client_id (str): The unique identifier of the client.
        college_id (str, optional): The unique identifier of the college. Defaults to None.
        current_user (CurrentUser): The authenticated user making the request.

    Returns:
        dict: A dictionary containing a success message and the newly added custom field.

    Raises:
        HTTPException (422): If neither `client_id` nor `college_id` is provided.
        HTTPException (422): If `college_id` is provided without `client_id`.
        HTTPException (422): If the custom field creation fails.
        HTTPException (404): If the specified client or college is not found.
        HTTPException (500): If an unexpected server error occurs.
    """
    await UserHelper().is_valid_user(current_user)
    if not client_id and not college_id:
        raise HTTPException(status_code=422, detail="Either client_id or college_id must be provided.")
    try:
        result = await Client().add_custom_field(client_id, field_data, college_id, existing_key_name)
        if result is None:
            raise HTTPException(status_code=422, detail="Failed to add custom field.")
        return result
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@client_router.delete("/remove_custom_field")
@requires_feature_permission("delete")
async def remove_custom_field(
    current_user:CurrentUser,
    key_name: str = Query(..., description="Key name to delete"),
    client_id: Optional[str] = Query(None, description="Client ID"),
    college_id: Optional[str] = Query(None, description="College ID"),
):
    """
        Deletes a specific custom field from a client or college's form schema.

        Params:
            key_name (str): The key name of the custom field to delete.
            client_id (Optional[str]): The client ID associated with the field to be removed (optional, must be provided with `college_id`).
            college_id (Optional[str]): The college ID associated with the field to be removed (optional, must be provided with `client_id`).
            current_user (CurrentUser): The authenticated user making the request.
        Returns:
            dict: A dictionary with the following keys:
                - `message`: A message indicating the result of the operation (success or failure).
                - `removed_field`: The `key_name` of the field that was successfully removed.
        Raises:
            HTTPException (422): If the provided `key_name` is invalid or a related error occurs.
            HTTPException (404): If no client or college is found with the provided `client_id` or `college_id`.
            HTTPException (500): If an unexpected error occurs during the deletion process.

        """
    await UserHelper().is_valid_user(current_user)
    try:
        return await Client().remove_fields(
            client_id=client_id,
            college_id=college_id,
            key_name=key_name
        )
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@client_router.post("/validate_passing_year")
@requires_feature_permission("read")
async def validate_passing_year(
        tenth_passing_year: int,
        current_user: CurrentUser,
        twelfth_passing_year: Optional[int] = None,
        graduation_passing_year: Optional[int] = None,
        post_graduation_passing_year: Optional[int] = None
):
    """
        API endpoint to validate the logical correctness of academic passing years provided by the user.
        Parameters:
            tenth_passing_year (int): The year the user completed their 10th grade.
            twelfth_passing_year (Optional[int]): The year the user completed their 12th grade (if applicable).
            graduation_passing_year (Optional[int]): The year the user completed graduation (if applicable).
            post_graduation_passing_year (Optional[int]): The year the user completed post-graduation (if applicable).
            current_user (User): The currently authenticated user (dependency-injected).
        Returns:
            dict: A success message indicating valid year input.
        Raises:
            HTTPException (422): If any year input fails the validation logic.
            HTTPException (404): If post-graduation year is provided without a graduation year.
            HTTPException (500): For any unexpected server-side errors.
        """
    try:
        current_year = datetime.now().year
        min_year = current_year - 15
        max_year = current_year

        min_tenth_year = current_year - 1
        if tenth_passing_year >= current_year or tenth_passing_year >= min_tenth_year:
            raise CustomError(message=f"10th passing year must be at least 1 year before {current_year}. (e.g., {min_tenth_year - 1} or earlier)")

        validation_result = await Client().validate_passing_years(
            tenth_passing_year, twelfth_passing_year, graduation_passing_year, post_graduation_passing_year, min_year, max_year,
            current_user)

        if not validation_result["valid"]:
            raise CustomError(message=validation_result["message"])

        return {"message": "Valid passing year selection"}
    except CustomError as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")