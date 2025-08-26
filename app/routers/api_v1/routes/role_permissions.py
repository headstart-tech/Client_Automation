"""
This file contains API routes related to permissions
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Path, HTTPException, Body
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.core.custom_error import CustomError, NotEnoughPermission, DataNotFoundError, \
    ObjectIdInValid
from app.core.log_config import get_logger
from app.core.utils import utility_obj, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import get_db, get_current_user_object, CurrentUser, \
    get_collection_from_cache, \
    store_collection_in_cache, get_current_user
from app.helpers.roles.role_permission_helper import RolePermissionHelper
from app.helpers.roles.roles_wrapper import RolePermissionFeature
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.master_schema import MasterScreen, DashboardHelper
from app.models.role_permission_schema import (
    PermissionCreate, Permission, Roles, Groups, \
    AssignRemoveGroupUser, GroupPermissionBase, AssignRemovePermissions,
    GroupUpdateBase, group_assign, RoleCreate, RoleUpdate, PermissionUpdate)
from app.models.student_user_schema import User

logger = get_logger(__name__)

router = APIRouter()


@router.post("/create_role/", summary="Create a new role")
@requires_feature_permission("write")
async def create_role(
        role_request: RoleCreate,
        current_user: User = Depends(get_current_user_object),
        db: AsyncSession = Depends(get_db)
):
    """
    Create a new role in the system.

    This endpoint allows authorized users to create a new role.
    It validates the request, checks if the role already exists,
    and then stores it in the database.

    Params:
        role_request (RoleCreate): The request body containing role details.
        current_user (User): The currently authenticated user.
        db (AsyncSession): The async database session.

    Returns:
        JSONResponse: A response indicating success or failure of the operation.

    Raises:
        HTTPException: If the user is unauthorized or the role already exists.
    """
    return await RolePermissionHelper().create_pgsql_entity(Roles, current_user, role_request, db)


@router.get(
    "/roles",
    summary="Fetch all roles with their associated permissions.",
)
@requires_feature_permission("read")
async def get_roles(
        page_num: int = Query(1, gt=0, description="Page number, starting from 1"),
        page_size: int = Query(10, gt=0, description="Number of items per page"),
        scope: Optional[str] = Query(None,
                                     description="Filter roles by scope: 'global' or 'college'"),
        current_user: User = Depends(get_current_user_object)
) -> JSONResponse:
    """
    Retrieve a paginated list of all roles along with their associated permissions.

    This endpoint fetches all roles and their assigned permissions, supporting pagination
    to limit the number of results per request. Only authorized users with the appropriate
    permissions can access this information.

    Params:
        page_num (int): The page number, starting from 1.
        page_size (int): The number of roles per page.
        scope (str): Optional filter for role scope (e.g., 'global', 'college').
        current_user (User): The currently authenticated user.

    Returns:
        JSONResponse: A response containing a paginated list of roles and their permissions.

    Raises:
        HTTPException: If the user is unauthorized.
    """
    return await RolePermissionHelper().fetch_pgsql_entity(
        current_user, data_type="roles", scope=scope, page_num=page_num, page_size=page_size)


@router.get(
    "/roles/{role_id}",
    summary="Fetch a specific role by ID along with its permissions.",
)
@requires_feature_permission("read")
async def get_roles(
        role_id: str = Path(..., description="Enter role id"),
        current_user: User = Depends(get_current_user_object)
) -> JSONResponse:
    """
    Retrieve a specific role by its ID along with its associated permissions.

    This endpoint fetches the details of a role, including its assigned permissions.
    Only authorized users with the appropriate permissions can access this information.

    Params:
        role_id (str): The unique identifier of the role.
        current_user (User): The currently authenticated user.

    Returns:
        JSONResponse: A response containing the role details and associated permissions.

    Raises:
        HTTPException: If the user is unauthorized or the role is not found.
    """
    return await RolePermissionHelper().fetch_pgsql_entity(current_user, data_type="roles",
                                                           item_id=role_id)


@router.put(
    "/update_role/{role_id}",
    summary="Update an existing role.",
)
@requires_feature_permission("edit")
async def update_roles(
        role_request: RoleUpdate,
        role_id: str = Path(..., description="Enter role id"),
        current_user: User = Depends(get_current_user_object),
        db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Update an existing role.

    Params:
        role_request (RoleUpdate): Data to update the role.
        role_id (int): ID of the role to be updated (> 0).
        current_user (User): Authenticated user with required permissions.
        db (AsyncSession): Async database session.

    Returns:
        JSONResponse: Success message with updated role data.

    Raises:
        HTTPException (401): If the user lacks the required permission.
        HTTPException (404): If no role is found with the provided `role_id`.
        HTTPException (400): If a role with the provided `name` already exists.
        HTTPException (500): If an internal error occurs during the update process.
    """

    return await RolePermissionHelper().update_pgsql_entity(Roles, current_user, role_id,
                                                            role_request, db)


@router.delete(
    "/delete_role/{role_id}",
    summary="Delete an existing role.",
)
@requires_feature_permission("delete")
async def delete_role(
        role_id: str = Path(..., description="Enter role id"),
        current_user: User = Depends(get_current_user_object),
        db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Delete an existing role by its ID.

    This endpoint allows users with the appropriate permission to delete a specific
    role from the system.

    Params:
        role_id (int): The ID of the role to be deleted (must be greater than 0).
        current_user (User): The authenticated user object obtained via dependency injection.
        db (AsyncSession): The async database session object.

    Returns:
        JSONResponse: A success message with the deleted `role_id` if the operation is successful.

    Raises:
        HTTPException (401): If the user is not authorized to perform the deletion.
        HTTPException (404): If the specified role does not exist.
        HTTPException (400): For other errors encountered during the deletion process.

    """

    return await RolePermissionHelper().delete_pgsql_entity(Roles, current_user, role_id, db)


@router.post("/create_permission/", summary="Create a new permission")
@requires_feature_permission("write")
async def create_permission(
        permission_request: PermissionCreate,
        current_user: User = Depends(get_current_user_object),
        db: AsyncSession = Depends(get_db)
):
    """
    Create a new permission in the system.

    This endpoint allows authorized users to create a new permission.
    It validates the request, checks if the permission already exists,
    and then stores it in the database.

    Params:
        permission_request (PermissionCreate): The request body containing permission details.
        current_user (User): The currently authenticated user.
        db (AsyncSession): The async database session.

    Returns:
        JSONResponse: A response indicating success or failure of the operation.

    Raises:
        HTTPException: If the user is unauthorized or the permission already exists.
    """
    return await RolePermissionHelper().create_pgsql_entity(Permission, current_user,
                                                            permission_request, db)


@router.get(
    "/permissions",
    summary="Fetch all permissions.",
)
@requires_feature_permission("read")
async def get_permissions(
        page_num: int = Query(1, gt=0, description="Page number, starting from 1"),
        page_size: int = Query(10, gt=0, description="Number of items per page"),
        scope: Optional[str] = Query(None,
                                     description="Filter permissions by scope: 'global' or 'college'"),
        current_user: User = Depends(get_current_user_object)
) -> JSONResponse:
    """
    Retrieve a paginated list of all permissions.

    This endpoint fetches all permissions, supporting pagination to limit the number of
    results per request. Only authorized users with the appropriate permissions can
    access this information.

    Params:
        page_num (int): The page number, starting from 1.
        page_size (int): The number of roles per page.
        current_user (User): The currently authenticated user.

    Returns:
        JSONResponse: A response containing a paginated list of sorted permissions.

    Raises:
        HTTPException: If the user is unauthorized.
    """
    return await RolePermissionHelper().fetch_pgsql_entity(
        current_user, data_type="permissions", scope=scope, page_num=page_num, page_size=page_size)


@router.get(
    "/permissions/{permission_id}",
    summary="Fetch a specific permission by ID.",
)
@requires_feature_permission("read")
async def get_permission(
        permission_id: int = Path(..., gt=0, description="permission ID must be greater than 0"),
        current_user: User = Depends(get_current_user_object)
) -> JSONResponse:
    """
    Retrieve a specific permission by its ID.

    Only authorized users with the appropriate permissions can access this information.

    Params:
        permission_id (int): The unique identifier of the permission.
        current_user (User): The currently authenticated user.

    Returns:
        JSONResponse: A response containing the permissions.

    Raises:
        HTTPException: If the user is unauthorized or the role is not found.
    """
    return await RolePermissionHelper().fetch_pgsql_entity(
        current_user, data_type="permissions", item_id=permission_id)


@router.put(
    "/update_permission/{permission_id}",
    summary="Update an existing permission.",
)
@requires_feature_permission("edit")
async def update_permission(
        role_request: PermissionUpdate,
        permission_id: int = Path(..., gt=0, description="Permission ID must be greater than 0"),
        current_user: User = Depends(get_current_user_object),
        db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Update an existing permission.

    Params:
        role_request (PermissionUpdate): Request body containing updated permission fields.
        permission_id (int): The unique identifier of the permission to be updated (must be > 0).
        current_user (User): The currently authenticated user (injected via dependency).
        db (AsyncSession): The async database session (injected via dependency).

    Returns:
        JSONResponse: Success message with updated permission data.

    Raises:
        HTTPException (401): If the user lacks the required permission.
        HTTPException (404): If no permission is found with the provided `permission_id`.
        HTTPException (400): If a permission with the provided `name` already exists.
        HTTPException (500): If an internal error occurs during the update process.
    """
    return await RolePermissionHelper().update_pgsql_entity(
        Permission, current_user, permission_id, role_request, db)


@router.post(
    "/assign_permission/{role_id}",
    summary="Assign permissions to a role.",
)
@requires_feature_permission("write")
async def assign_permission_to_role(
        request: AssignRemovePermissions,
        role_id: str = Path(..., description="Enter role id"),
        current_user=Depends(get_current_user_object),
        db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Assign permissions to a specific role.

    This endpoint allows authorized users to assign multiple permissions to a role.

    Params:
        role_id (int): The ID of the role to which permissions will be assigned.
        request (AssignRemovePermissions): The request body containing permission_ids to be assigned to role.
        current_user: The authenticated user performing the action.
        db (AsyncSession): The async database session dependency.

    Returns:
        JSONResponse: Confirmation of successful permission assignment.

    Raises:
        HTTPException: If the user is not authorized, the role or permissions are invalid.
    """
    return await RolePermissionHelper().assign_revoke_permissions("assign", current_user, Roles,
                                                                  role_id, db, request)


@router.post(
    "/revoke_permissions/{role_id}",
    summary="Revoke permissions from a role.",
)
@requires_feature_permission("write")
async def revoke_permissions_from_role(
        request: AssignRemovePermissions,
        role_id: str = Path(..., description="Enter role id"),
        current_user=Depends(get_current_user_object),
        db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Revoke specified permissions from a given role.

    Params:
        role_id (int): The ID of the role from which permissions will be revoked. Must be greater than 0.
        request (AssignRemovePermissions): The request body containing permission_ids to be revoked from role.
        current_user (User): The currently authenticated user, retrieved via dependency injection.
        db (AsyncSession): Async database session dependency for executing queries.

    Returns:
        JSONResponse: A JSON response indicating the success or failure of the operation.

    Raises:
        HTTPException: If the user is unauthorized or the role/permissions are invalid.
    """
    return await RolePermissionHelper().assign_revoke_permissions("revoke", current_user, Roles,
                                                                  role_id, db, request)


@router.delete(
    "/delete_permission/{permission_id}",
    summary="Delete an existing permission.",
)
@requires_feature_permission("delete")
async def delete_role(
        permission_id: int = Path(..., gt=0, description="Permission ID must be greater than 0"),
        current_user: User = Depends(get_current_user_object),
        db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Delete an existing permission by its ID.

    This endpoint allows users with the appropriate permissions to delete a specific
    permission from the system.

    Params:
        permission_id (int): The ID of the permission to be deleted (must be greater than 0).
        current_user (User): The authenticated user object obtained via dependency injection.
        db (AsyncSession): The async database session object.

    Returns:
        JSONResponse: A success message with the deleted `permission_id` if the operation is successful.

    Raises:
        HTTPException (401): If the user is not authorized to perform the deletion.
        HTTPException (404): If the specified permission does not exist.
        HTTPException (400): For other errors encountered during the deletion process.

    """

    return await RolePermissionHelper().delete_pgsql_entity(Permission, current_user, permission_id,
                                                            db)


@router.post("/create_group/", summary="Create a new group")
@requires_feature_permission("write")
async def create_group(
        group_request: GroupPermissionBase,
        current_user: User = Depends(get_current_user_object),
        db: AsyncSession = Depends(get_db)
):
    """
    Create a new user-defined group.

    This endpoint allows users with appropriate roles (Admin or SuperAdmin) to create a new group.
    Each group can be associated with a list of permissions.

    Params:
        group_request (GroupPermissionBase): Group creation request containing name, description, and permissions.
        current_user (User): The currently authenticated user, injected via dependency.
        db (AsyncSession): The asynchronous database session, injected via dependency.

    Returns:
        JSONResponse: A response containing a success message and group data, or an error message if creation fails.
    """

    return await RolePermissionHelper().create_group(Groups, current_user, group_request, db)


@router.get(
    "/groups",
    summary="Fetch all groups with their associated permissions.",
)
@requires_feature_permission("read")
async def get_groups(
        page_num: int = Query(1, gt=0, description="Page number, starting from 1"),
        page_size: int = Query(10, gt=0, description="Number of items per page"),
        scope: Optional[str] = Query(None,
                                     description="Filter permissions by scope: 'global' or 'college'"),
        college_id: Optional[str] = Query(None, description="Enter college id."),
        current_user: User = Depends(get_current_user_object)
) -> JSONResponse:
    """
    Retrieve a paginated list of all groups along with their associated permissions.

    This endpoint fetches all groups and their assigned permissions, supporting pagination
    to limit the number of results per request. Only authorized users with the appropriate
    permissions can access this information.

    Params:
        page_num (int): The page number, starting from 1.
        page_size (int): The number of groups per page.
        current_user (User): The currently authenticated user.

    Returns:
        JSONResponse: A response containing a paginated list of groups and their permissions.

    Raises:
        HTTPException: If the user is unauthorized.
    """
    return await RolePermissionHelper().fetch_pgsql_entity(
        current_user, data_type="groups", scope=scope, college_id=college_id, page_num=page_num,
        page_size=page_size)


@router.get(
    "/groups/{group_id}",
    summary="Fetch a specific group by ID along with its permissions.",
)
@requires_feature_permission("read")
async def get_group(
        group_id: int = Path(..., gt=0, description="Group ID must be greater than 0"),
        current_user: User = Depends(get_current_user_object)
) -> JSONResponse:
    """
    Retrieve a specific group by its ID along with its associated permissions.

    This endpoint fetches the details of a group, including its assigned permissions.
    Only authorized users with the appropriate permissions can access this information.

    Params:
        group_id (int): The unique identifier of the group.
        current_user (User): The currently authenticated user.

    Returns:
        JSONResponse: A response containing the group details and associated permissions.

    Raises:
        HTTPException: If the user is unauthorized or the group is not found.
    """
    return await RolePermissionHelper().fetch_pgsql_entity(current_user, data_type="groups",
                                                           item_id=group_id)


@router.put(
    "/update_group/{group_id}",
    summary="Update an existing group.",
)
@requires_feature_permission("edit")
async def update_groups(
        group_request: GroupUpdateBase,
        group_id: int = Path(..., gt=0, description="Group ID must be greater than 0"),
        current_user: User = Depends(get_current_user_object),
        db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Update an existing group.

    Params:
        group_request (RolePermissionUpdate): Data to update the group.
        group_id (int): ID of the group to be updated (> 0).
        current_user (User): Authenticated user with required permissions.
        db (AsyncSession): Async database session.

    Returns:
        JSONResponse: Success message with updated group data.

    Raises:
        HTTPException (401): If the user lacks the required permission.
        HTTPException (404): If no group is found with the provided `group_id`.
        HTTPException (400): If a group with the provided `name` already exists.
        HTTPException (500): If an internal error occurs during the update process.
    """

    return await RolePermissionHelper().update_group_entity(Groups, current_user, group_id,
                                                            group_request, db)


@router.delete(
    "/delete_group/{group_id}",
    summary="Delete an existing group.",
)
@requires_feature_permission("delete")
async def delete_group(
        group_id: int = Path(..., gt=0, description="Group ID must be greater than 0"),
        current_user: User = Depends(get_current_user_object),
        db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Delete an existing group by its ID.

    This endpoint allows users with the appropriate permission to delete a specific
    group from the system.

    Params:
        group_id (int): The ID of the group to be deleted (must be greater than 0).
        current_user (User): The authenticated user object obtained via dependency injection.
        db (AsyncSession): The async database session object.

    Returns:
        JSONResponse: A success message with the deleted `group_id` if the operation is successful.

    Raises:
        HTTPException (401): If the user is not authorized to perform the deletion.
        HTTPException (404): If the specified group does not exist.
        HTTPException (400): For other errors encountered during the deletion process.

    """

    return await RolePermissionHelper().delete_pgsql_entity(Groups, current_user, group_id, db)


@router.post(
    "/assign_permission/group/{group_id}",
    summary="Assign permissions to a group.",
)
@requires_feature_permission("write")
async def assign_permission_to_group(
        request: AssignRemovePermissions,
        group_id: int = Path(..., gt=0, description="Group ID to assign permissions to."),
        current_user=Depends(get_current_user_object),
        db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Assign permissions to a specific group.

    This endpoint allows authorized users to assign multiple permissions to a group.

    Params:
        group_id (int): The ID of the group to which permissions will be assigned.
        request (AssignRemovePermissions): The request body containing permission_ids to be assigned to group.
        current_user: The authenticated user performing the action.
        db (AsyncSession): The async database session dependency.

    Returns:
        JSONResponse: Confirmation of successful permission assignment.

    Raises:
        HTTPException: If the user is not authorized, the group or permissions are invalid.
    """
    return await RolePermissionHelper().assign_revoke_permissions("assign", current_user, Groups,
                                                                  group_id, db, request)


@router.post(
    "/revoke_permissions/group/{group_id}",
    summary="Revoke permissions from a group.",
)
@requires_feature_permission("write")
async def revoke_permissions_from_group(
        request: AssignRemovePermissions,
        group_id: int = Path(..., gt=0, description="Group ID to assign permissions to."),
        current_user=Depends(get_current_user_object),
        db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Revoke specified permissions from a given group.

    Params:
        group_id (int): The ID of the group from which permissions will be revoked. Must be greater than 0.
        request (AssignRemovePermissions): The request body containing permission_ids to be revoked from group.
        current_user (User): The currently authenticated user, retrieved via dependency injection.
        db (AsyncSession): Async database session dependency for executing queries.

    Returns:
        JSONResponse: A JSON response indicating the success or failure of the operation.

    Raises:
        HTTPException: If the user is unauthorized or the group/permissions are invalid.
    """
    return await RolePermissionHelper().assign_revoke_permissions("revoke", current_user, Groups,
                                                                  group_id, db, request)


@router.post(
    "/group/add_user/{group_id}",
    summary="Add user to a group.",
)
@requires_feature_permission("write")
async def add_user_to_group(
        request: AssignRemoveGroupUser,
        group_id: int = Path(..., gt=0, description="Group ID to assign permissions to."),
        current_user=Depends(get_current_user_object),
        db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Add a user to a specified group.

    This endpoint allows an authorized user (admin or super admin) to add one or more users
    to a group. The user IDs to be added must be specified in the request body.

    Params:
        request (AssignRemoveGroupUser): Request object containing user IDs to be added to the group.
        group_id (int): ID of the group to which users will be added.
        current_user (dict): The currently authenticated user requesting the action.
        db (AsyncSession): Database session for querying and updating the database.

    Returns:
        JSONResponse: Response containing a success message and details about the users added.

    Raises:
        HTTPException: If the user is unauthorized or invalid user IDs are provided.
    """
    return await RolePermissionHelper().assign_revoke_group_user("add", current_user,
                                                                 group_id, db, request)


@router.post(
    "/group/remove_user/{group_id}",
    summary="Remove user from a group.",
)
@requires_feature_permission("write")
async def remove_user_from_group(
        request: AssignRemoveGroupUser,
        group_id: int = Path(..., gt=0, description="Group ID to assign permissions to."),
        current_user=Depends(get_current_user_object),
        db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Remove a user from a specified group.

    This endpoint allows an authorized user (admin or super admin) to remove one or more users
    from a group. The user IDs to be removed must be specified in the request body.

    Params:
        request (AssignRemoveGroupUser): Request object containing user IDs to be removed from the group.
        group_id (int): ID of the group from which users will be removed.
        current_user (dict): The currently authenticated user requesting the action.
        db (AsyncSession): Database session for querying and updating the database.

    Returns:
        JSONResponse: Response containing a success message and details about the users removed.

    Raises:
        HTTPException: If the user is unauthorized or invalid user IDs are provided.
    """
    return await RolePermissionHelper().assign_revoke_group_user("remove", current_user,
                                                                 group_id, db, request)


@router.post("/create_feature_group")
@requires_feature_permission("write")
async def create_feature_group(
        payload: MasterScreen,
        current_user: CurrentUser,
        group_name: str = Query(..., description="Name of the feature group"),
        update: bool = Query(False, description="Update existing feature group")
):
    """
    Create a new feature group in the system.

    This endpoint allows authorized users to create a new feature group.
    It validates the request, checks if the feature group already exists,
    and then stores it in the database.

    Params:
        payload (MasterScreen): The request body containing feature group details.
        current_user (User): The currently authenticated user.
        group_name (str): The name of the feature group to be created.

    Returns:
        JSONResponse: A response indicating success or failure of the operation.

    Raises:
        HTTPException: If the user is unauthorized or the feature group already exists.
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        payload = jsonable_encoder(payload)
        payload = utility_obj.clean_data(payload)
        group_description = payload.get("group_description")
        payload = payload.get("screen_details", [])
        if not payload:
            raise CustomError("No screen details found in the payload")
        return await RolePermissionFeature().create_feature_group(
            payload=payload, group_name=group_name, user=user,
            group_description=group_description, update=update)
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error {e}")


@router.put("/update_feature_group")
@requires_feature_permission("edit")
async def update_feature_group(
        payload: DashboardHelper,
        current_user: CurrentUser,
        group_id: str = Query(..., description="Name of the feature group"),
):
    """
    Create a new feature group in the system.

    This endpoint allows authorized users to create a new feature group.
    It validates the request, checks if the feature group already exists,
    and then stores it in the database.

    Params:
        payload (DashboardHelper): The request body containing feature group details.
        current_user (User): The currently authenticated user.
        group_id (str): The name of the feature group to be created.

    Returns:
        JSONResponse: A response indicating success or failure of the operation.

    Raises:
        HTTPException: If the user is unauthorized or the feature group already exists.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        payload = jsonable_encoder(payload)
        payload = utility_obj.clean_data(payload)
        if not payload:
            raise CustomError("No group details found in the payload")
        return await RolePermissionFeature().update_role_specific_fields(
            payload=payload, _id=group_id, field_name="Group")
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error {e}")


@router.post("/create_role_feature")
@requires_feature_permission("write")
async def add_role_info(
        payload: MasterScreen,
        current_user: CurrentUser,
        role_id: str = Query(..., alias="role_id"),
        dashboard_type: str = Query("admin_dashboard", alias="dashboard_type"),
        college_id: Optional[str] = Query(None, alias="college_id")
):
    """
        Adds a new role to the system.

    Params:
        role_name: - The role name to be added.
        current_user: User - The authenticated user making the request.
        payload: MasterScreen - The role data to be added.
        dashboard_type: str - The type of dashboard (admin_dashboard or student_dashboard).
        college_id: str - The ID of the college to filter roles (optional).

    Raises:
         HTTPException: An error occur.
         CustomError: If the role creation fails.

    Return:
        dict - Success message with the created role ID.
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        if user.get("role", {}).get("role_name") != "super_admin":
            raise NotEnoughPermission("You are not authorized to update a role.")
        payload = jsonable_encoder(payload)
        if payload.get("screen_details") is None:
            raise CustomError("Screen details must be required")
        payload = utility_obj.clean_data(payload)
        payload = payload.get("screen_details", [])
        return await RolePermissionFeature().update_role_feature(
            role_id=role_id,
            payload=payload,
            dashboard_type=dashboard_type,
            college_id=college_id
        )
    except NotEnoughPermission as error:
        raise HTTPException(status_code=403, detail=f"{error.message}")
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@router.put("/update_role_feature")
@requires_feature_permission("edit")
async def update_role_info(
        current_user: CurrentUser,
        payload: DashboardHelper,
        role_id: str = Query(..., alias="role_id"),
        college_id: Optional[str] = Query(None, alias="college_id")
):
    """
        Updates an existing role in the system.

    Params:
        role_id: str - The ID of the role to be updated.
        current_user: User - The authenticated user making the request.
        payload: MasterScreen - The role data to be updated.
        college_id: str - The ID of the college to filter roles (optional).

    Raises:
         HTTPException: An error occur.
         CustomError: If the role update fails.

    Return:
        dict - Success message with the updated role ID.
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        if user.get("role", {}).get("role_name") != "super_admin":
            raise NotEnoughPermission("You are not authorized to update a role.")
        payload = jsonable_encoder(payload)
        payload = utility_obj.clean_data(payload)
        field = f"permissions/admin_dashboard/{current_user.get('user_name')}"
        return await RolePermissionFeature().update_role_specific_fields(
            _id=role_id,
            payload=payload,
            field_name="Role",
            invalidation_route=field,
            college_id=college_id
        )
    except NotEnoughPermission as error:
        raise HTTPException(status_code=403, detail=f"{error.message}")
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@router.get("/get_specific_roles")
@requires_feature_permission("read")
async def get_role_info(
        current_user: CurrentUser,
        role_id: Optional[str] = Query(None, alias="role_id"),
        college_id: Optional[str] = Query(None, alias="college_id")
):
    """
        Retrieves all roles in the system.

    Params:
        current_user: User - The authenticated user making the request.
        role_id: str - The ID of the specific role to be retrieved (optional).
        college_id: str - The ID of the college to filter roles (optional).

    Raises:
         HTTPException: An error occur.

    Return:
        dict - Success message with the list of roles.
    """
    try:
        await UserHelper().is_valid_user(current_user)
        return await RolePermissionFeature().get_role_features(
            _id=role_id, field_name="Role", college_id=college_id)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@router.get("/get_specific_group")
@requires_feature_permission("read")
async def get_group_info(
        current_user: CurrentUser,
        group_id: Optional[str] = Query(None, alias="role_id"),
):
    """
        Retrieves all roles in the system.

    Params:
        current_user: User - The authenticated user making the request.
        group_id: str - The ID of the specific role to be retrieved (optional).

    Raises:
         HTTPException: An error occur.

    Return:
        dict - Success message with the list of roles.
    """
    try:
        await UserHelper().is_valid_user(current_user)
        return await RolePermissionFeature().get_role_features(_id=group_id, field_name="Group")
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@router.get("/get_all_group")
@requires_feature_permission("read")
async def get_group_info(
        current_user: CurrentUser,
        page_num: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1),
):
    """
        Retrieves all roles in the system.

    Params:
        current_user: User - The authenticated user making the request.
        page_num: The page number
        page_size: A page size of the document

    Raises:
         HTTPException: An error occur.

    Return:
        dict - Success message with the list of roles.
    """
    try:
        await UserHelper().is_valid_user(current_user)
        return await RolePermissionFeature().get_all_role(page_num=page_num, page_size=page_size)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@router.post("/assigned_permissions")
@requires_feature_permission("write")
async def get_assigned_permissions(
        current_user: CurrentUser,
        payload: group_assign
):
    """
    Fetch the assigned permissions for a specific role.

    Params:
        current_user (User): The currently authenticated user.
        role_id (str): The ID of the role to fetch assigned permissions for.

    Returns:
        JSONResponse: A response containing the assigned permissions for the specified role.

    Raises:
        HTTPException: If the user is unauthorized or the role is not found.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        payload = jsonable_encoder(payload)
        payload = utility_obj.clean_data(payload)
        return await RolePermissionFeature().get_assigned_permissions(payload=payload)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@router.put("/remove_feature_group")
@requires_feature_permission("edit")
async def remove_feature_group(
        current_user: CurrentUser,
        user_id: str = Query(..., description="Id of particular user"),
        group_ids: list = Body(..., description="List of group ids to be removed")
):
    """
        Removes a feature group or role from the system.

    Params:
        current_user: User - The authenticated user making the request.
        user_id: str - The name of the feature group or role to be removed.
        group_ids: list - The list of group IDs to be removed.

    Raises:
         HTTPException: An error occur.

    Return:
        dict - Success message with the removed feature group or role ID.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await RolePermissionFeature().remove_feature_group(
            user_id=user_id,
            group_ids=group_ids,
            current_user=current_user
        )
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@router.delete("/delete_feature_group")
@requires_feature_permission("delete")
async def delete_feature_role(
        current_user: CurrentUser,
        _id: str = Query(..., description="Name of the feature group or role"),
        feature_id: str = Query(None, description="ID of the feature group or role"),
):
    """
        Deletes a feature group or role from the system.

    Params:
        current_user: User - The authenticated user making the request.
        _id: str - The name of the feature group or role to be deleted.
        feature_id: str - The ID of the feature group or role to be deleted.

    Raises:
         HTTPException: An error occur.

    Return:
        dict - Success message with the deleted feature group or role ID.
    """
    try:
        await UserHelper().is_valid_user(current_user)
        return await RolePermissionFeature().delete_feature_group(
            _id=_id,
            feature_id=feature_id
        )
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@router.get("/get_user_permissions")
@requires_feature_permission("read")
async def get_user_permissions(
        current_user: str = Depends(get_current_user),
        dashboard_type: str = Query("admin_dashboard", description="Type of dashboard")
):
    """
        Retrieves all permissions for the current user.

    Params:
        current_user: User - The authenticated user making the request.

    Raises:
         HTTPException: An error occur.

    Return:
        dict - Success message with the list of permissions.
    """
    try:
        if dashboard_type not in ["admin_dashboard", "student_dashboard"]:
            raise CustomError("Invalid dashboard type. Must be"
                              " 'admin_dashboard' or 'student_dashboard'.")
        if dashboard_type == "admin_dashboard":
            user = await UserHelper().is_valid_user(current_user)
        else:
            if (user := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"user_name": current_user})) is None:
                raise DataNotFoundError("Student")
        field = f"{dashboard_type}/{str(user.get('college_id'))}" if user.get(
            "college_id") else f"{dashboard_type}/{current_user}"
        # Todo: We will do it later after testing
        # data = await get_collection_from_cache(collection_name="permissions", field=field)
        # if data:
        #     return data
        data = await RolePermissionFeature().get_role_permissions(
            user=user, dashboard_type=dashboard_type)
        # if data:
        #     await store_collection_in_cache(collection=data,
        #                                     collection_name="permissions", field=field)
        return data
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@router.get("/user_group_details")
@requires_feature_permission("read")
async def get_user_group_details(
        current_user: CurrentUser,
        user_id: Optional[str] = Query(None, description="Group ID to fetch details for"),
        page_num: int = Query(1, ge=1, description="Page number for pagination"),
        page_size: int = Query(10, ge=1, description="Number of items per page"),
):
    """
    Retrieves the details of a specific user group.

    Params:
        current_user (User): The currently authenticated user.
        group_id (str): The ID of the group to fetch details for (optional).
        page_num (int): The page number for pagination (default is 1).
        page_size (int): The number of items per page for pagination (default is 10).

    Returns:
        JSONResponse: A response containing the group details.

    Raises:
        HTTPException: If the user is unauthorized or the group is not found.
    """
    try:
        return await RolePermissionFeature().get_user_group_details(
            user_id=user_id, page_num=page_num, page_size=page_size)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occurred: {error}")


# Todo: This is for testing purpose only, we will remove it later
@router.get("/get_user_permissions_2")
@requires_feature_permission("read")
async def get_user_permissions(
        current_user=Depends(get_current_user_object),
        dashboard_type: str = Query("admin_dashboard", description="Type of dashboard")
):
    """
    Retrieves all permissions for the current user supported with cache.

    Params:
        current_user: User - The authenticated user making the request.

    Raises:
         HTTPException: An error occur.

    Return:
        dict - Success message with the list of permissions.
    """
    try:
        if dashboard_type not in ["admin_dashboard", "student_dashboard"]:
            raise CustomError("Invalid dashboard type. Must be"
                              " 'admin_dashboard' or 'student_dashboard'.")
        data = await get_collection_from_cache(f"allowed_features/{dashboard_type}",
                                               current_user.get("user_name"))
        if not data:
            data = await utility_obj.get_user_feature_permissions(
                user=current_user, dashboard_type=dashboard_type)
            if data:
                await store_collection_in_cache(
                    collection=data, collection_name=f"allowed_features/{dashboard_type}",
                    field=current_user.get("user_name"))
        college_id = current_user.get("college_id")
        return {"message": f"Role permissions fetched successfully.",
                "data": data,
                "dashboard_type": dashboard_type,
                "college_id": str(college_id) if college_id else None
                }
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.message}")
    except (CustomError, ObjectIdInValid) as error:
        raise HTTPException(status_code=422, detail=f"{error.message}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")
