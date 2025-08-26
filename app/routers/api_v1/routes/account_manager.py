"""  This File contains the API routes for Account Manager """
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query

from app.core.custom_error import CustomError, DataNotFoundError, NotEnoughPermission
from app.core.utils import requires_feature_permission
from app.dependencies.oauth import CurrentUser
from app.helpers.account_manager.account_manager_crud_helper import AccountManagerCRUDHelper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.account_manager import NewAccountManager, UpdateAccountManager, \
    ChangeSuperAccountManager, ListofClientsIdModel, ClientIdModel

account_manager_router = APIRouter()


@account_manager_router.post("/create")
@requires_feature_permission("write")
async def create_account_manager(
        current_user: CurrentUser,
        details: NewAccountManager
):
    """
    This API is used to create account manager, This API can be Used by Super Admin, Admin & Super Account Manager only

    ### Request Body
    - **first_name (str)**: The first name of the account manager
    - **middle_name (Optional[str])**: The middle name of the account manager
    - **last_name (Optional[str])**: The last name of the account manager
    - **email (str)**: The email of the account manager
    - **mobile_number (str)**: The mobile number of the account manager
    - **associated_super_account_manager (str)**: The super account manager Object id

    ### Example Request Body
    ```json
    {
      "first_name": "Sanjeev",
      "middle_name": "",
      "last_name": "Yadav",
      "email": "sanjeev@example.com",
      "mobile_number": "8754016652",
      "associated_super_account_manager": "67da51e38de294bf7040af95"
    }
    ```

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **422**: Custom Error (Error will be mentioned in `detail`)
    - **401**: Unauthorized/Not Enough Permissions
    - **400**: Bad Request

    ### Response Body
    - message (str): The message of the response
    - account_manager_id (str): The id of the created account manager
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        value = await AccountManagerCRUDHelper().create_account_manager_helper(details.model_dump(),
                                                                               user)
        return value
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@account_manager_router.get("/get/{account_manager_id}")
@requires_feature_permission("read")
async def get_account_manager(
        current_user: CurrentUser,
        account_manager_id: str = Path(title="Account Manager Id")
):
    """
    This API is used to get account manager details, This API can be Used by Super Admin, Admin &
    Super Account Manager & Account Manager only

    ### Path Parameters
    - **account_manager_id (str)**: The id of the account manager

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **401**: Unauthorized/Not Enough Permissions
    - **422**: Custom Error (Error will be mentioned in `detail`)

    ### Response Body
    - **data** (dict): The data of the account manager
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await AccountManagerCRUDHelper().get_account_manager_by_id(account_manager_id, user)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except NotEnoughPermission as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@account_manager_router.get("/get_all")
@requires_feature_permission("read")
async def get_all_account_manager(
        current_user: CurrentUser,
        page: Optional[int] = Query(None, gt=0),
        limit: Optional[int] = Query(None, gt=0),
):
    """
    This API is used to get all account manager details, This API can be Used by Super Admin, Admin &
    Super Account Manager only

    ### Raises
    - **500**: Something went wrong Internally
    - **401**: Unauthorized/Not Enough Permissions
    - **404**: Data Not Found

    ### Response Body
    - **message** (str): The message of the response
    - **data** (list): The list of the account manager
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await AccountManagerCRUDHelper().get_all_account_manager(
            user=user, page=page, limit=limit, route="/account_manager/get_all"
        )
    except NotEnoughPermission as e:
        raise HTTPException(status_code=401, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@account_manager_router.put("/update/{account_manager_id}")
@requires_feature_permission("edit")
async def update_account_manager(
        current_user: CurrentUser,
        details: UpdateAccountManager,
        account_manager_id: str = Path(title="Account Manager Id")
):
    """
    This API is used to update account manager details, This API can be Used by Super Admin, Admin &
    Super Account Manager & Account Manager only

    ### Path Parameters
    - **account_manager_id (str)**: The id of the account manager

    ### Request Body
    - **first_name (Optional[str])**: The first name of the account manager
    - **middle_name (Optional[str])**: The middle name of the account manager
    - **last_name (Optional[str])**: The last name of the account manager
    - **email (Optional[str])**: The email of the account manager
    - **mobile_number (Optional[str])**: The mobile number of the account manager

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
    - **422**: Custom Error (Error will be mentioned in `detail`)

    ### Response Body
    - **message** (str): The message of the response
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await AccountManagerCRUDHelper().update_account_manager(
            account_manager_id, details.model_dump(exclude_defaults=True), user
        )
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except NotEnoughPermission as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@account_manager_router.put("/change_super_account_manager/{account_manager_id}")
@requires_feature_permission("edit")
async def change_super_account_manager(
        current_user: CurrentUser,
        details: ChangeSuperAccountManager,
        account_manager_id: str = Path(title="Account Manager Id")
):
    """
    This API is used to change super account manager, This API can be Used by Super Admin, Admin &
    Super Account Manager only

    ### Path Parameters
    - **account_manager_id (str)**: The id of the account manager

    ### Request Body
    - **super_account_manager_id (str)**: The id of the super account manager

    ### Example Request Body
    ```json
    {
        "super_account_manager_id": "67e3fbafdbd1bab57a6a6f14"
    }
    ```

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **401**: Unauthorized/Not Enough Permissions
    - **422**: Custom Error (Error will be mentioned in `detail`)

    ### Response Body
    - **message** (str): The message of the response
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await AccountManagerCRUDHelper().change_super_account_manager(
            account_manager_id, details.model_dump().get("super_account_manager_id"), user
        )
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except NotEnoughPermission as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@account_manager_router.put("/add_clients/{account_manager_id}")
@requires_feature_permission("edit")
async def add_clients(
        current_user: CurrentUser,
        details: ListofClientsIdModel,
        account_manager_id: str = Path(title="Account Manager Id")
):
    """
    This API is used to add clients, This API can be Used by Super Admin, Admin &
    Super Account Manager

    ### Path Parameters
    - **account_manager_id (str)**: The id of the account manager

    ### Request Body
    - **client_ids (List[str])**: The id of the clients

    ### Example Request Body
    ```json
    {
        "client_ids": ["67e44a085cfea479960cdc5b"]
    }
    ```

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **401**: Unauthorized/Not Enough Permissions
    - **422**: Custom Error (Error will be mentioned in `detail`)

    ### Response Body
    - **message** (str): The message of the response
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await AccountManagerCRUDHelper().add_clients(
            account_manager_id, details.model_dump().get("client_ids"), user
        )
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except NotEnoughPermission as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@account_manager_router.put("/remove_client/{account_manager_id}")
@requires_feature_permission("edit")
async def remove_client(
        current_user: CurrentUser,
        details: ClientIdModel,
        account_manager_id: str = Path(title="Account Manager Id")
):
    """
    This API is used to remove clients, This API can be Used by Super Admin, Admin &
    Super Account Manager

    ### Path Parameters
    - **account_manager_id (str)**: The id of the account manager

    ### Request Body
    - **client_id (str)**: The id of the clients

    ### Example Request Body
    ```json
    {
        "clients_id": "67e44a085cfea479960cdc5b"
    }
    ```

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **401**: Unauthorized/Not Enough Permissions
    - **422**: Custom Error (Error will be mentioned in `detail`)

    ### Response Body
    - **message** (str): The message of the response
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await AccountManagerCRUDHelper().remove_clients(
            account_manager_id, details.model_dump().get("client_id"), user
        )
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except NotEnoughPermission as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@account_manager_router.put("/activate/{account_manager_id}")
@requires_feature_permission("edit")
async def activate_account_manager(
        current_user: CurrentUser,
        account_manager_id: str = Path(title="Account Manager Id")
):
    """
    This API is used to activate account manager, This API can be Used by Super Admin, Admin &
    Super Account Manager only

    ### Path Parameters
    - **account_manager_id (str)**: The id of the account manager

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **401**: Unauthorized/Not Enough Permissions
    - **422**: Custom Error (Error will be mentioned in `detail`)

    ### Response Body
    - **message** (str): The message of the response
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await AccountManagerCRUDHelper().activate_account_manager(account_manager_id, user)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except NotEnoughPermission as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@account_manager_router.put("/deactivate/{account_manager_id}")
@requires_feature_permission("edit")
async def deactivate_account_manager(
        current_user: CurrentUser,
        account_manager_id: str = Path(title="Account Manager Id")
):
    """
    This API is used to deactivate account manager, This API can be Used by Super Admin, Admin &
    Super Account Manager only

    ### Path Parameters
    - **account_manager_id (str)**: The id of the account manager

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **401**: Unauthorized/Not Enough Permissions
    - **422**: Custom Error (Error will be mentioned in `detail`)

    ### Response Body
    - **message** (str): The message of the response
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await AccountManagerCRUDHelper().deactivate_account_manager(account_manager_id, user)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except NotEnoughPermission as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))
