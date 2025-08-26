""" This File Contains Super Account Manager Routes """

from fastapi import APIRouter, HTTPException, Path, Query
from app.core.utils import requires_feature_permission
from app.dependencies.oauth import CurrentUser
from typing import Optional
from app.helpers.user_curd.user_configuration import UserHelper
from app.core.custom_error import CustomError, DataNotFoundError, NotEnoughPermission
from app.helpers.super_account_manager.sam_crud_operation import SAMCrudHelper
from app.models.super_account_manager import SuperAccountManagerCreationModel, SuperAccountManagerUpdateModel, AccountManagerIdsListModels


super_account_manager_router = APIRouter()


@super_account_manager_router.post("/create")
@requires_feature_permission("write")
async def create_super_account_manager(
        user: CurrentUser,
        super_account_manager_details: SuperAccountManagerCreationModel
    ):
    """
    Create Super Account Manager

    ### Request Body
    - **first_name (str)**: The first name of the super account manager
    - **middle_name (Optional[str])**: The middle name of the super account manager
    - **last_name (Optional[str])**: The last name of the super account manager
    - **email (str)**: The email of the super account manager
    - **mobile_number (str)**: The mobile number of the super account manager

    ### Example Request Body
    ```json
    {
      "email": "raj.kumar@domain.in",
      "first_name": "Raj",
      "middle_name": "Singh",
      "last_name": "Kumar",
      "mobile_number": "9876543210"
    }
    ```

    ### Raises
    - **401**: Unauthorized/Not Enough Permissions
    - **422**: Custom Error (Error will be mentioned in "detail")
    - **500**: Something went wrong Internally

    ### Response Body
    - **message** (str): The message of the response
    - **super_account_manager_id** (str): The id of the super account manager
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(user)
    try:
        return await SAMCrudHelper().create_super_account_manager(super_account_manager_details.model_dump(), user)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@super_account_manager_router.get("/get/{super_account_manager_id}")
@requires_feature_permission("read")
async def get_super_account_manager(
        current_user: CurrentUser,
        super_account_manager_id: str = Path(title="Super Account Manager Id")
    ):
    """
    This API is used to get super account manager details, This API can be Used by Super Admin, Admin &
    Super Account Manager only

    ### Path Parameters
    - **super_account_manager_id (str)**: The id of the super account manager

    ### Response Body
    - **super_account_manager_details** (dict): The details of the super account manager

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **401**: Unauthorized/Not Enough Permissions
    - **422**: Custom Error (Error will be mentioned in "detail")
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await SAMCrudHelper().get_sam_by_id(super_account_manager_id, user)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except NotEnoughPermission as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@super_account_manager_router.get("/get_all")
@requires_feature_permission("read")
async def get_all_super_account_manager(
        current_user: CurrentUser,
        page: Optional[int] = Query(None, gt=0),
        limit: Optional[int] = Query(None, gt=0),
    ):
    """
    This API is used to get all super account manager details, This API can be Used by Super Admin, Admin &
    Super Account Manager only

    ### Raises
    - **500**: Something went wrong Internally
    - **401**: Unauthorized/Not Enough Permissions
    - **404**: Data Not Found

    ### Response Body
    - **message** (str): The message of the response
    - **data** (list): The list of the super account manager
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    await UserHelper().is_valid_user(current_user)
    try:
        return await SAMCrudHelper().get_all_sam(route="get_all", page=page, limit=limit)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@super_account_manager_router.put("/update/{super_account_manager_id}")
@requires_feature_permission("edit")
async def update_super_account_manager(
        current_user: CurrentUser,
        super_account_manager_details: SuperAccountManagerUpdateModel,
        super_account_manager_id: str = Path(title="Super Account Manager Id")
    ):
    """
    This API is used to update super account manager details,
    This API can be Used by Super Admin, Admin & Super Account Manager

    ### Path Parameters
    - **super_account_manager_id (str)**: The id of the super account manager

    ### Request Body
    - **email (Optional[str])**: The email of the super account manager
    - **mobile_number (Optional[str])**: The mobile number of the super account manager

    ### Example Request Body
    ```json
    {
        "email": "lKZdM@example.com"
    }
    ```

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **401**: Unauthorized/Not Enough Permissions
    - **422**: Custom Error (Error will be mentioned in "detail")

    ### Response Body
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await SAMCrudHelper().update_sam(super_account_manager_id, super_account_manager_details.model_dump(exclude_defaults=True), user)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except NotEnoughPermission as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@super_account_manager_router.put("/activate/{super_account_manager_id}")
@requires_feature_permission("edit")
async def activate_super_account_manager(
        current_user: CurrentUser,
        super_account_manager_id: str = Path(title="Super Account Manager Id")
    ):
    """
    This API is used to activate super account manager, This API can be Used by Super Admin & Admin

    ### Path Parameters
    - **super_account_manager_id (str)**: The id of the super account manager

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **401**: Unauthorized/Not Enough Permissions
    - **422**: Custom Error (Error will be mentioned in "detail")

    ### Response Body
    - **message** (str): The message of the response
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    await UserHelper().is_valid_user(current_user)
    try:
        return await SAMCrudHelper().activate_sam(super_account_manager_id)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except NotEnoughPermission as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@super_account_manager_router.put("/deactivate/{super_account_manager_id}")
@requires_feature_permission("edit")
async def deactivate_super_account_manager(
        current_user: CurrentUser,
        super_account_manager_id: str = Path(title="Super Account Manager Id")
    ):
    """
    This API is used to deactivate super account manager, This API can be Used by Super Admin & Admin

    ### Path Parameters
    - **super_account_manager_id (str)**: The id of the super account manager

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **401**: Unauthorized/Not Enough Permissions
    - **422**: Custom Error (Error will be mentioned in "detail")

    ### Response Body
    - **message** (str): The message of the response
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    await UserHelper().is_valid_user(current_user)
    try:
        return await SAMCrudHelper().deactivate_sam(super_account_manager_id)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except NotEnoughPermission as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@super_account_manager_router.put("/assign-account-managers/{super_account_manager_id}")
@requires_feature_permission("edit")
async def assign_account_managers_to_super_account_manager(
        requested_data: AccountManagerIdsListModels,
        current_user: CurrentUser,
        super_account_manager_id: str = Path(title="Super Account Manager Id")
    ):
    """
    This API is used to assign account managers to super account manager,
    This API can be Used by Super Admin & Admin

    ### Path Parameters
    - **super_account_manager_id (str)**: The id of the super account manager

    ### Request Body
    - **account_manager_ids (List[str])**: The ids of the account managers

    ### Example Request Body
    ```json
    {
        "account_manager_ids": ["67e3fbafdbd1bab57a6a6f14", "67e3fbafdbd1bab57a6a6f15"]
    }
    ```

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **401**: Unauthorized/Not Enough Permissions
    - **422**: Custom Error (Error will be mentioned in "detail")

    ### Response Body
    - **message** (str): The message of the response
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    await UserHelper().is_valid_user(current_user)
    try:
        return await SAMCrudHelper().assign_account_managers_to_super_account_manager(super_account_manager_id, requested_data.model_dump().get("account_manager_ids"))
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except NotEnoughPermission as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))