"""
This file contains class and functions related to roles and permissions.
"""
import json
from datetime import datetime, timezone
from typing import Literal, Union

from bson import ObjectId
from fastapi import status
from fastapi.exceptions import HTTPException
from sqlalchemy import text, delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.core.log_config import get_logger
from app.core.utils import utility_obj, CustomJSONEncoder
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import get_cache_roles_permissions, get_redis_client, is_testing_env
from app.models.role_permission_schema import (
    PermissionCreate, RolePermission, Roles, GroupPermission, GroupPermissionBase, GroupUpdateBase,
    RoleCreate, RoleUpdate, PermissionUpdate)

logger = get_logger(name=__name__)


class RolePermissionHelper:

    async def has_permission(self, permissions: dict, scope: str, required_permission: str) -> bool:
        """
        Check if the user has the required permission based on the scope.

        Params:
        permissions: User's permissions dict (with keys 'global_permissions' and 'college_permissions')
        scope: The scope to check ('global' or 'college')
        required_permission: The permission to validate

        Returns:
            True if the user has the required permission, otherwise False
        """
        permission_list = permissions.get(f"{scope}_permissions", [])
        return required_permission in permission_list

    async def _fetch_entity(self, model, entity_id, db: AsyncSession, model_obj: str = "Role"):
        """
        Fetch an entity (Role or Permission) from the database by its ID.

        For the "Roles" model, the method validates the `mongo_id` and queries using it.
        For other models (e.g., "Permission"), it fetches the entity by its primary key (assumed to be an integer).

        Params:
            model: The SQLAlchemy model class (e.g., Roles or Permission).
            entity_id (str | int): The ID of the entity to fetch.
            db (AsyncSession): The async database session.
            model_obj (str): Model name for ID validation

        Returns:
            The matched model instance or None if not found.

        Raises:
            HTTPException (400): If the Role ID is invalid.
        """
        if model.__name__ == "Roles" and model_obj == "Role":
            await utility_obj.is_id_length_valid(entity_id, f"{model_obj} ID")
            return (await db.execute(
                select(model).where(model.mongo_id == entity_id))).scalar_one_or_none()
        return await db.get(model, int(entity_id))

    async def _check_permission(self, current_user, model_name, scope, action):
        """
        Validate that the current user has the required permission to perform an action.

        This method checks whether the user has the necessary permission based on the
        model type (Roles or Permission), the action being performed (e.g., 'create',
        'update', 'delete'), and the scope ('global' or 'college').

        Params:
            current_user (dict): The authenticated user object, including permissions.
            model_name (str): The name of the model, either 'Roles' or 'Permission'.
            scope (str): The scope of the operation, either 'global' or 'college'.
            action (str): The action to be performed (e.g., 'create', 'delete').

        Raises:
            HTTPException (401): If the user does not have the required permission.
        """
        permissions = current_user.get("permissions", {})
        associated_colleges = current_user.get("associated_colleges", [])
        if associated_colleges:
            raise HTTPException(
                status_code=403,
                detail=f"{scope.capitalize()} {model_name.lower()} management is restricted to system-level "
                       f"users for '{action}' operations."
            )
        permission_map = {
            "Roles": {
                "global": f"{action}_role",
                "college": f"{action}_college_role"
            },
            "Permission": {
                "global": f"{action}_permission",
                "college": f"{action}_college_permission"
            },
            "Groups": {
                "global": f"{action}_group",
                "college": f"{action}_college_group"
            }
        }
        required_permission = permission_map.get(model_name, {}).get(scope)
        if not required_permission or not await self.has_permission(permissions, scope,
                                                                    required_permission):
            raise HTTPException(status_code=401, detail="Not enough permissions")

    async def fetch_role_descendants(self, role_id: str) -> list[str]:
        """
        Retrieves the list of descendant role Mongo IDs for a given role. First attempts to load from
        Redis cache. If not found, regenerates and updates the cache.

        Params:
            role_id (str): The Mongo ID of the role whose descendants are needed.

        Returns:
            list[str]: A list of descendant role Mongo IDs.
        """
        redis_key = "role_descendants"
        cached_data = await get_cache_roles_permissions(collection_name=redis_key, field=role_id)
        if not cached_data:
            cached_data = await utility_obj.cache_descendant_mongo_ids(role_id=role_id)
        allowed_roles = cached_data.get("descendant_ids")
        return allowed_roles or []

    async def create_pgsql_entity(self, model, current_user,
                                  request_data: PermissionCreate | RoleCreate, db: AsyncSession):
        """
        Creates a new PostgresSQL entity (Role or Permission) based on the provided model and request data.

        This method:
        - Validates the user's permissions based on the scope ('college' or 'global') and model type.
        - Checks for existing entries with the same name and scope to prevent duplicates.
        - Adds metadata such as `created_by`, `created_at`, and optionally a `mongo_id`.
        - Commits the new entry to the PostgresSQL database.
        - For Roles:
            - Inserts a corresponding document into the MongoDB collection.
            - Triggers a roles and permissions cache refresh.
        - For Permissions:
            - Automatically assigns the new permission to the super_admin role.
            - Updates the permissions cache.

        Params:
            model: SQLAlchemy model class (e.g., Roles, Permission, Groups).
            current_user (dict): Authenticated user object containing permission details.
            request_data (RoleCreate | PermissionCreate): Pydantic object containing request payload.
            db (AsyncSession): SQLAlchemy asynchronous database session.

        Returns:
            JSONResponse: A success message with the created entity's data.

        Raises:
            HTTPException: If scope is missing, permission is denied, entry already exists, or creation fails.
        """
        try:
            model_name = model.__name__
            data = request_data.model_dump()
            scope = data.get("scope")

            model_obj = "role" if model_name == "Roles" else "permission"
            if not scope:
                raise HTTPException(status_code=400,
                                    detail=f"Scope is required for {model_obj} creation.")

            await self._check_permission(current_user, model_name, scope, action="create")
            if model_name == "Roles":
                current_user_role_id = current_user.get("role_id").get("mongo_id")
                if not current_user_role_id:
                    raise HTTPException(status_code=403, detail="User role not found")

                parent_id = data.get("parent_id")
                allowed_roles = await self.fetch_role_descendants(current_user_role_id)
                if parent_id is not None:
                    await utility_obj.is_id_length_valid(parent_id, "Parent ID")
                    if parent_id not in allowed_roles and parent_id != current_user_role_id:
                        raise HTTPException(
                            status_code=403,
                            detail="You can only assign roles under your own role or its children. "
                                   f"Invalid parent_id '{parent_id}'."
                        )
                    parent_role_data = await get_cache_roles_permissions(
                        collection_name="roles_permissions", field=parent_id)
                    if not parent_role_data:
                        roles = (await utility_obj.cache_roles_and_permissions()).get("data", {})
                        parent_role_data = json.loads(roles.get(str(parent_id)))
                    if parent_role_data.get("scope") == "college" and scope == "global":
                        raise HTTPException(
                            status_code=400,
                            detail="Global roles cannot be nested under college roles.")
                    data["parent_id"] = parent_role_data.get("id")
                else:
                    data["parent_id"] = current_user.get("role_id").get("pgsql_id")

            key_value = model_obj.title()
            # Check for existing entry
            existing_entry = (await db.execute(select(model).where(
                model.name == data.get("name")))).scalar_one_or_none()
            if existing_entry:
                raise HTTPException(
                    status_code=400,
                    detail=f"{key_value} already exists with name '{data['name']}' and scope '{existing_entry.scope}'."
                )
            date_obj = datetime.now(timezone.utc)
            mongo_id = ObjectId()
            data.update({"created_by": current_user.get("user_id"), "created_at": date_obj,
                         "last_modified_at": date_obj})
            if model_name == "Roles":
                data.update({"mongo_id": str(mongo_id)})
            # Create and store new entry
            new_entry = model(**data)
            db.add(new_entry)
            await db.commit()
            await db.refresh(new_entry)
            if model_name == "Roles":
                data_obj = data.copy()
                data_obj['role_name'] = data_obj.pop('name')
                data_obj.pop('parent_id')
                data_obj.update(
                    {"_id": ObjectId(data_obj.pop('mongo_id')), "permission": {}, "menus": {},
                     "student_menus": None, "pgsql_id": new_entry.id,
                     "created_by": ObjectId(current_user.get("user_id"))})
                await DatabaseConfiguration().role_collection.insert_one(data_obj)
                await utility_obj.cache_descendant_mongo_ids()
            elif model_name == "Permission":
                # Todo: instead of cacheing the all roles and permission objects, we can cache the target object only
                if super_admin_role := (
                        await db.execute(
                            select(Roles).where(Roles.name == "super_admin"))).scalar_one_or_none():
                    db.add(RolePermission(role_id=super_admin_role.id, permission_id=new_entry.id))
                    await db.commit()
                await utility_obj.cache_permissions(collection="system_permissions")

            await utility_obj.cache_roles_and_permissions()

            data = json.dumps(data, cls=CustomJSONEncoder)
            return JSONResponse(
                status_code=201,
                content={"message": f"{key_value} created successfully.", "data": json.loads(data)}
            )
        except HTTPException as exc:
            raise exc
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400,
                                detail=f"Something went wrong while creating {model.__name__}: {e}")

    async def _validate_permission_assignment(self, scope, current_user, permission_ids):
        """
        Validate permission IDs and ensure the current user is authorized to assign them based on scope.

        This method checks that all provided permission IDs exist in the system, are appropriate for the
        specified scope ('global' or 'college'), and that the current user has the authority to assign them.
        Global groups can have both global and college permissions, but college groups can only have
        college-level permissions.

        Parameters:
            scope (str): The target scope of the group ('global' or 'college').
            current_user (dict): The authenticated user performing the assignment.
            permission_ids (list): List of permission IDs to assign.

        Raises:
            HTTPException (400): If a global permission is being assigned to a college scope group.
            HTTPException (403): If the user lacks permission to assign college or global level permissions.
        """
        redis_client = get_redis_client()
        existing_permissions = current_user.get("permissions", {})
        cached_permissions = await self.fetch_cached_permissions(redis_client)
        permission_ids = self.validate_permission_ids(permission_ids, cached_permissions)

        if scope == "college" and not await self.has_permission(
                existing_permissions, "college", "read_college_permissions"):
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to assign permissions to a 'college' scope group."
            )

        for pid in permission_ids:
            perm = cached_permissions.get(pid)
            if not perm:
                continue  # Already validated earlier, safe fallback
            perm_scope = perm.get("scope")
            if scope == "college" and perm_scope == "global":
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot assign global permissions to 'college' scope group."
                )
            if scope == "global":
                if perm_scope == "global" and not await self.has_permission(
                        existing_permissions, "global", "read_permissions"):
                    raise HTTPException(
                        status_code=403,
                        detail="You are not allowed to assign 'global' level permissions."
                    )
                if perm_scope == "college" and not await self.has_permission(
                        existing_permissions, "college", "read_college_permissions"):
                    raise HTTPException(
                        status_code=403,
                        detail="You are not allowed to assign 'college' level permissions."
                    )

    async def create_group(self, model, current_user, request_data: GroupPermissionBase,
                           db: AsyncSession):
        """
        Create a new group with associated permissions.

        This method handles the creation of a group based on the specified scope (global or college),
        validates permissions, checks for duplicates, and stores the new entity in the database.

        Parameters:
            model (DeclarativeMeta): The SQLAlchemy model to be used (either Group or Role).
            current_user (User): The authenticated user creating the group.
            request_data (GroupPermissionBase): The request payload containing group details and permission IDs.
            db (AsyncSession): SQLAlchemy async database session.

        Returns:
            JSONResponse: A success response with the created group details.

        Raises:
            HTTPException (400): If scope is missing, a duplicate group exists, or a general error occurs.
            HTTPException (401): If the user does not have the required permission.
            HTTPException (403): If the user is not allowed to create a group for the specified scope.
            HTTPException (404): If the specified college does not exist.
        """
        try:
            model_name = model.__name__
            data = request_data.model_dump()
            scope = data.get("scope")
            permission_ids = data.pop("permission_ids", None)

            if not scope:
                raise HTTPException(status_code=400,
                                    detail=f"Scope is required for group creation.")

            await self._check_permission(current_user, model_name, scope, action="create")
            if scope == "global":
                data.pop("college_id", None)
            else:
                college_id = data.get("college_id")
                if college_id:
                    await utility_obj.is_id_length_valid(college_id, "College ID")
                    college = await DatabaseConfiguration().college_collection.find_one(
                        {"_id": ObjectId(college_id)})
                    if not college:
                        raise HTTPException(status_code=404, detail="College not found")
            if permission_ids:
                await self._validate_permission_assignment(scope, current_user, permission_ids)

            # Check for existing entry
            group_name = data.get("name").title()
            if (
                    await db.execute(
                        select(model).where(model.name == group_name))).scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail=f"Group already exists with name '{group_name}'."
                )
            now = datetime.now(timezone.utc)
            data.update({
                "name": group_name,
                "created_by": current_user.get("user_id"),
                "created_at": now,
                "last_modified_at": now
            })
            # Create and store new entry
            new_entry = model(**data)
            db.add(new_entry)
            await db.commit()
            await db.refresh(new_entry)

            if permission_ids:
                values = [{"target_id": new_entry.id, "permission_id": int(pid)} for pid in
                          permission_ids]
                query = text(f"""
                    INSERT INTO group_permissions (group_id, permission_id)
                    VALUES (:target_id, :permission_id) ON CONFLICT DO NOTHING
                """)

                await db.execute(query, values)
                await db.commit()
            # Todo: Instead of all object initialization, we can just initialize newly created object
            await utility_obj.cache_groups_and_permissions(data=new_entry)
            data = json.dumps(data, cls=CustomJSONEncoder)
            return JSONResponse(
                status_code=201,
                content={"message": "Group created successfully.", "data": json.loads(data)}
            )
        except HTTPException as exc:
            raise exc
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400,
                                detail=f"Something went wrong while creating {model.__name__}: {e}")

    async def update_pgsql_entity(self, model, current_user, entity_id,
                                  request_data: RoleUpdate | PermissionUpdate, db: AsyncSession):
        """
        Update a PostgreSQL entity (Role or Permission) after validating permissions, uniqueness,
        and entity existence.

        Params:
            model: The SQLAlchemy model class (Roles or Permission) to be updated.
            current_user (dict): The currently authenticated user's information, including permissions.
            entity_id (str|int): The ID of the entity to update (Mongo ID for Roles, integer for Permissions).
            request_data (RoleUpdate | PermissionUpdate): The validated data for updating the entity.
            db (AsyncSession): SQLAlchemy asynchronous database session.

        Returns:
            JSONResponse: A success message along with the updated fields.

        Raises:
            HTTPException:
                - 404: If the entity is not found.
                - 401: If the user lacks the required permissions.
                - 400: If a duplicate name exists in the same scope or on general failure.
        """
        try:
            model_name = model.__name__
            data = request_data.model_dump(exclude_none=True)
            model_obj = "role" if model_name == "Roles" else "permission"

            if not data:
                raise HTTPException(
                    status_code=400,
                    detail=f"No valid fields provided for {model_obj}."
                )

            existing_entry = await self._fetch_entity(model, entity_id, db)
            if not existing_entry:
                raise HTTPException(status_code=404, detail=f"{model_obj.title()} not found.")

            scope = existing_entry.scope
            await self._check_permission(current_user, model_name, scope, action="update")

            if "name" in data:
                duplicate_query = select(model).where(model.name == data.get("name"))
                id_field = model.mongo_id if model_name == "Roles" else model.id
                duplicate_query = duplicate_query.where(
                    id_field != (entity_id if model_name == "Roles" else int(entity_id)))
                duplicate = (await db.execute(duplicate_query)).scalar_one_or_none()
                if duplicate:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{model_obj.title()} already exists with name '{data['name']}'."
                    )

            for key, value in data.items():
                setattr(existing_entry, key, value)
            existing_entry.last_modified_at = datetime.now(timezone.utc)

            await db.commit()
            await db.refresh(existing_entry)
            if model_name == "Roles":
                if data.get("parent_id"):
                    await utility_obj.cache_descendant_mongo_ids()
                await DatabaseConfiguration().role_collection.update_one(
                    {"_id": ObjectId(entity_id)},
                    {"$set": {
                        "role_name": data.get("name", existing_entry.name),
                        "description": data.get("description", existing_entry.description),
                        "scope": data.get("scope", existing_entry.scope),
                        "last_modified_at": existing_entry.last_modified_at
                    }}
                )
            elif model_name == "Permission":
                # Todo: instead of cacheing the all objects, we can cache the required object only
                await utility_obj.cache_permissions(collection="system_permissions")
            await utility_obj.cache_roles_and_permissions()

            data = json.dumps(data, cls=CustomJSONEncoder)
            return JSONResponse(
                status_code=200,
                content={"message": f"{model_obj.title()} updated successfully.",
                         "data": json.loads(data)}
            )
        except HTTPException as exc:
            raise exc
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400,
                                detail=f"Something went wrong while updating {model.__name__}: {e}")

    async def update_group_entity(self, model, current_user, entity_id: int,
                                  request_data: GroupUpdateBase,
                                  db: AsyncSession):
        """
        Update a PostgreSQL entity (Permission).

        This method allows authorized users to update an existing Permission record in the
        PostgresSQL database. It performs validation checks, including authorization, record existence, and
        name uniqueness, and then applies the update.

        Params:
            model (Base): The SQLAlchemy model class to update (e.g., `Roles`, `Groups`, or `Permission`).
            current_user (dict): Authenticated user object containing role and permission information.
            entity_id (int): The unique identifier of the record to be updated.
            request_data (RolePermissionUpdate): The request payload containing fields to update.
            db (AsyncSession): The async SQLAlchemy database session.

        Raises:
            HTTPException (401): If the user is not authorized to perform the update action.
            HTTPException (404): If the specified role/group/permission does not exist.
            HTTPException (400): If a record with the provided 'name' already exists.
            HTTPException (500): If an internal server error occurs during the update process.

        Returns:
            JSONResponse: A response object with:
                - status_code (200): On successful update.
                - message (str): Confirmation message for the update.
                - id (int): The ID of the updated record.
                - data (dict): The updated data fields.
        """
        try:
            model_name = model.__name__
            data = request_data.model_dump(exclude_none=True)
            scope = data.get("scope")

            if not data:
                raise HTTPException(
                    status_code=400,
                    detail=f"No valid fields provided for group."
                )

            existing_entry = await self._fetch_entity(model, entity_id, db)
            if not existing_entry:
                raise HTTPException(status_code=404, detail=f"Group not found.")

            existing_permissions = (await get_cache_roles_permissions(
                "groups_and_permissions", existing_entry.id)).get("permissions", {})
            if not existing_permissions:
                groups = await utility_obj.cache_groups_and_permissions()
                groups = groups.get("data", {})
                group = json.loads(groups.get(str(existing_entry.id)))
                existing_permissions = group.get("permissions", {})

            existing_scope = existing_entry.scope
            await self._check_permission(current_user, model_name, existing_scope, action="update")

            if scope and scope == "college":
                college_id = data.get("college_id")

                if existing_scope == "global" and existing_permissions.get("global_permissions",
                                                                           []):
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot convert a global group to college, it contains global-level permissions."
                    )

                if college_id:
                    await utility_obj.is_id_length_valid(college_id, "College ID")
                    college = await DatabaseConfiguration().college_collection.find_one(
                        {"_id": ObjectId(college_id)})
                    if not college:
                        raise HTTPException(status_code=404, detail="College not found")
                else:
                    data["college_id"] = None
            else:
                data["college_id"] = None

            if "name" in data and data.get("name").title() != existing_entry.name:
                request_name = data.get("name").title()
                if (await db.execute(select(model).where(
                        model.name == request_name, model.id != entity_id
                ))).scalar_one_or_none():
                    raise HTTPException(
                        status_code=400,
                        detail=f"Group already exists with name '{request_name}'."
                    )
            for key, value in data.items():
                setattr(existing_entry, key, value)
            existing_entry.last_modified_at = datetime.now(timezone.utc)

            await db.commit()
            await db.refresh(existing_entry)
            # Todo: Instead of initializing whole object we can update the required object only
            await utility_obj.cache_groups_and_permissions()
            return JSONResponse(
                status_code=200,
                content={"message": f"Group updated successfully.", "id": entity_id, "data": data}
            )
        except HTTPException as exc:
            raise exc
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500,
                                detail=f"Something went wrong while updating {model.__name__}: {str(e)}")

    async def fetch_pgsql_entity(
            self, current_user, data_type: Literal["roles", "permissions", "groups"],
            item_id: Union[str, int, None] = None, scope: str | None = None,
            college_id: str | None = None, page_num: int | None = None, page_size: int | None = None
    ):
        """
        Fetch roles or permissions or groups based on user scope and permissions.

        Parameters:
            current_user (User): The current user.
            data_type (str): Either "roles" or "permissions".
            item_id (str | int | None): Role ID (str) or Permission ID (int).
            scope (str | None): 'global' or 'college'.
            college_id (str | None): College ID.
            page_num (int | None): Pagination page number.
            page_size (int | None): Pagination page size.

        Returns:
            JSONResponse: Role or permission data with optional pagination.

        Raises:
            HTTPException: On authorization errors or data not found.
        """
        try:
            valid_scopes = ["global", "college"]
            mapping = {
                "roles": ("read_roles", "roles_permissions"),
                "permissions": ("read_permissions", "system_permissions"),
                "groups": ("read_groups", "groups_and_permissions")
            }
            action_key, collection_name = mapping.get(data_type, (None, None))
            user_colleges = current_user.get("associated_colleges", [])
            permissions = current_user.get("permissions", {})
            role_obj = current_user.get("role_id")
            current_role_id = role_obj.get("mongo_id") if role_obj else None
            if not current_role_id:
                raise HTTPException(status_code=403, detail="User role not found.")

            if user_colleges:
                if data_type == "permissions":
                    raise HTTPException(
                        status_code=403,
                        detail="College-level users are not allowed to fetch permissions."
                    )
                # Only allow college roles
                allowed_scopes = ["college"]
            else:
                allowed_scopes = [
                    s for s in valid_scopes
                    if await self.has_permission(
                        permissions, s,
                        f"read_{s}_{data_type}" if s == "college" else action_key
                    )
                ]
                if not allowed_scopes:
                    raise HTTPException(status_code=401, detail="Not enough permissions")

            if scope:
                if scope not in valid_scopes:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid scope '{scope}'. Allowed values are 'global' or 'college'."
                    )
                if scope not in allowed_scopes:
                    raise HTTPException(status_code=401, detail="Not enough permissions")
                filter_scopes = [scope]
            else:
                filter_scopes = allowed_scopes

            if data_type == "groups" and college_id:
                await utility_obj.is_id_length_valid(college_id, "College ID")
                if user_colleges and college_id not in user_colleges:
                    raise HTTPException(status_code=401, detail="Not enough permissions")
                college = await DatabaseConfiguration().college_collection.find_one(
                    {"_id": ObjectId(college_id)})
                if not college:
                    raise HTTPException(status_code=404, detail="College not found")

            # Apply descendant filter for roles
            descendant_ids = None
            if data_type == "roles":
                descendant_ids = await self.fetch_role_descendants(role_id=current_role_id)
                if item_id:
                    await utility_obj.is_id_length_valid(item_id, "Role ID")
                    if item_id not in descendant_ids:
                        raise HTTPException(status_code=401, detail="Not enough permissions")

            data = await get_cache_roles_permissions(
                collection_name=collection_name, field=item_id, scope=filter_scopes)
            if not data:
                cached = (
                    await utility_obj.cache_roles_and_permissions() if data_type == "roles"
                    else await utility_obj.cache_groups_and_permissions() if data_type == "groups"
                    else await utility_obj.cache_permissions(collection_name)
                )
                all_data = cached.get("data", {})
                if item_id is not None:
                    raw = all_data.get(str(item_id))
                    data = json.loads(raw) if raw else None
                else:
                    parsed = [json.loads(v) for v in all_data.values()]
                    data = sorted(
                        [entry for entry in parsed if entry.get("scope") in filter_scopes],
                        key=lambda x: x["name"].lower()
                    )
            if item_id and isinstance(data, dict) and data.get("scope") not in filter_scopes:
                raise HTTPException(status_code=401, detail="Not enough permissions")

            if not data:
                raise HTTPException(status_code=404,
                                    detail=f"{data_type[:-1].capitalize()} not found")
            if data_type == "roles" and descendant_ids is not None and not item_id:
                data = [d for d in data if d.get("mongo_id") in descendant_ids]
            if data_type == "groups" and isinstance(data, list):
                if user_colleges:
                    # If college_id is passed, filter by it only if it's allowed
                    if college_id:
                        data = [d for d in data if
                                d.get("college_id") is None or d.get("college_id") == college_id]
                    else:
                        # No specific filter, show all accessible
                        data = [
                            d for d in data
                            if d.get("college_id") is None or d.get("college_id") in user_colleges
                        ]
                elif "college" in allowed_scopes:
                    # Global user with college read access: filter by passed college_id if given
                    if scope == "college" and college_id:
                        data = [
                            d for d in data
                            if d.get("scope") == "college" and (
                                    d.get("college_id") is None or d.get("college_id") == college_id
                            )
                        ]
                else:
                    # Global user without college read access: show only global groups
                    data = [d for d in data if d.get("college_id") is None]
            if page_num and page_size:
                route_name = f"/role_permissions/{data_type}"
                total = len(data)
                paginated = await utility_obj.pagination_in_api(page_num, page_size, data, total,
                                                                route_name)
                return JSONResponse(status_code=200, content={
                    "message": f"{data_type.capitalize()} Fetched Successfully",
                    "data": paginated["data"],
                    "total": total,
                    "count": len(paginated["data"]),
                    "pagination": paginated["pagination"]
                })
            return JSONResponse(status_code=200,
                                content={
                                    "message": f"{data_type[:-1].capitalize()} Fetched Successfully",
                                    "data": data})
        except HTTPException as exc:
            raise exc
        except Exception as e:
            raise HTTPException(status_code=400,
                                detail=f"Something went wrong while fetching {data_type}: {e}")

    async def validate_and_fetch_target_data(self, target_type: str, target_id: str | int,
                                             db: AsyncSession, redis_client) -> dict:
        """
        Validate existence and fetch role/group data from cache or database.

        Checks Redis cache for data. If not found, queries the database, caches result, and returns data.

        Params:
            target_type (str): Either 'role' or 'group'.
            target_id (int|str): ID of the role or group.
            db (AsyncSession): Database session.
            redis_client: Redis client instance.

        Returns:
            dict: Data including entity information and associated permissions.

        Raises:
            HTTPException (404): If the specified entity does not exist.
            HTTPException (400): If the target_type is invalid.
        """
        if target_type not in {"role", "group"}:
            raise HTTPException(status_code=400,
                                detail="Invalid target_type. Must be 'role' or 'group'.")

        if target_type == "role":
            await utility_obj.is_id_length_valid(target_id, "Role ID")

        redis_key = "roles_permissions" if target_type == "role" else "groups_and_permissions"
        entity_id = str(target_id)

        entity_data = await redis_client.hget(redis_key,
                                              entity_id) if not is_testing_env() else None

        if not entity_data:
            lookup_column = "mongo_id" if target_type == "role" else "id"
            query = text(f"""
                SELECT 
                    row_to_json(r) AS entity, 
                    JSONB_BUILD_OBJECT(
                        'college_permissions', COALESCE(
                            JSONB_AGG(DISTINCT p.name) FILTER (WHERE p.name IS NOT NULL AND p.scope = 'college'
                        ), '[]'::jsonb),
                        'global_permissions', COALESCE(
                            JSONB_AGG(DISTINCT p.name) FILTER (WHERE p.name IS NOT NULL AND p.scope = 'global'
                        ), '[]'::jsonb)
                    ) AS permissions
                FROM {target_type}s r
                LEFT JOIN {target_type}_permissions rp ON r.id = rp.{target_type}_id
                LEFT JOIN permissions p ON rp.permission_id = p.id
                WHERE r.{lookup_column} = :id
                GROUP BY r.id
            """)
            result = (await db.execute(query, {"id": target_id})).mappings().first()

            if not result:
                raise HTTPException(status_code=404,
                                    detail=f"{target_type.capitalize()} with id '{target_id}' doesn't exist.")

            entity_data = result.get("entity")
            entity_data["permissions"] = result.get("permissions")

            if target_type == "group":
                pipeline = [
                    {"$match": {"group_ids": target_id}},
                    {"$project": {"_id": {"$toString": "$_id"}}},
                    {"$group": {"_id": None, "user_ids": {"$push": "$_id"}}}
                ]
                users = await DatabaseConfiguration().user_collection.aggregate(pipeline).to_list(
                    length=None)
                entity_data["users"] = users[0].get("user_ids", []) if users else []
            if not is_testing_env():
                await redis_client.hset(redis_key, entity_id, json.dumps(entity_data))
        else:
            entity_data = json.loads(entity_data)

        return entity_data

    async def fetch_cached_permissions(self, redis_client) -> dict:
        """
        Fetch system permissions from cache.

        This method retrieves system permissions from the Redis cache. If the cache is empty,
        it triggers a refresh by calling the `cache_permissions` method and returns the updated data.

        Params:
            redis_client: The Redis client instance used to interact with the cache.

        Returns:
            dict: A dictionary containing permission data where the keys represent permission names
                  and the values contain permission details.

        Raises:
            Exception: If there are issues with cache retrieval or data parsing.
        """
        redis_permission_key = "system_permissions"
        cached_permissions = await redis_client.hgetall(
            redis_permission_key) if not is_testing_env() else None

        if not cached_permissions:
            cache_data = await utility_obj.cache_permissions(redis_permission_key)
            cached_permissions = cache_data.get("data", {})

        return {
            (key.decode() if isinstance(key, bytes) else key): json.loads(value)
            for key, value in cached_permissions.items()
        }

    def validate_permission_ids(self, permission_ids: list[int],
                                cached_permissions: dict[str, dict]) -> set[str]:
        """
        Validate provided permission IDs against cached permissions.

        This method checks whether all provided permission IDs exist within the cached permissions.
        If any invalid permissions are found, it raises an HTTPException.

        Params:
            permission_ids (list[int]): A list of permission IDs to validate.
            cached_permissions (dict[str, dict]): A dictionary of cached permissions where keys are permission IDs as strings.

        Returns:
            set[str]: A set of valid permission IDs that match the cache.

        Raises:
            HTTPException: If any permission ID is not found in the cached permissions.
        """
        valid_permission_ids = set(cached_permissions.keys())
        requested_permissions = set(map(str, permission_ids))

        invalid_permissions = requested_permissions - valid_permission_ids
        if invalid_permissions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid permission(s): {list(invalid_permissions)}"
            )

        return requested_permissions

    async def assign_revoke_permissions(self, action, current_user, model, target_id: str | int,
                                        db: AsyncSession, request):
        """
        Assigns or revokes permissions for a given role or group.

        This function allows system-level users to assign or revoke a set of permissions
        for a specific role or group based on their scope and the requesting user's permissions.

        Params:
            action (str): Either 'assign' or 'revoke', specifying the desired operation.
            current_user (dict): The user performing the operation, including permission and scope data.
            model (Union[Roles, Groups]): The target model instance (role or group class).
            target_id (str): The ID of the role or group whose permissions are being modified.
            db (AsyncSession): The SQLAlchemy asynchronous session for DB operations.
            request (BaseModel): The request object containing `permission_ids`.

        Returns:
            JSONResponse: A success message indicating the result of the operation along with
                          affected permission IDs and the role/group ID.

        Raises:
            HTTPException: If the user lacks permissions, input is invalid, the role/group is not found,
                           or if a database or logic error occurs.
        """
        # TODO: Before assigning permissions, validate whether the user is authorized to fetch permissions or not.

        try:
            model_obj = "role" if model.__name__ == "Roles" else "group"
            request_data = request.model_dump(exclude_none=True)
            permission_ids = request_data.get("permission_ids", [])
            current_user_role_id = current_user.get("role_id").get("mongo_id")
            if not current_user_role_id:
                raise HTTPException(status_code=403, detail="User role not found")

            if action not in ["assign", "revoke"]:
                raise ValueError("Invalid action. Must be 'assign' or 'revoke'.")
            if current_user.get("associated_colleges", []):
                raise HTTPException(
                    status_code=403,
                    detail=f"{model_obj.title()}-permission management is restricted to system-level users."
                )

            permissions = current_user.get("permissions", {})
            if not await self.has_permission(permissions, "global", "assign_permission"):
                raise HTTPException(status_code=401, detail="Not enough permissions")

            redis_client = get_redis_client()
            target_data = await self.validate_and_fetch_target_data(model_obj, target_id, db,
                                                                    redis_client)
            if not target_data:
                raise HTTPException(status_code=404, detail=f"{model_obj.title()} not found")
            target_id = target_data.get("id") if model_obj == "role" else target_id
            if not permission_ids:
                action_noun = "added" if action == "assign" else "removed"
                return JSONResponse(status_code=200,
                                    content={"message": f"No permissions were {action_noun}."})
            if model_obj == "role":
                allowed_roles = await self.fetch_role_descendants(current_user_role_id)
                if target_data.get("mongo_id") not in allowed_roles:
                    raise HTTPException(
                        status_code=403,
                        detail=f"You can only {action} roles under your own role or its children. "
                               f"Invalid parent_id '{target_id}'.")
            cached_permissions = await self.fetch_cached_permissions(redis_client)
            permission_ids = self.validate_permission_ids(permission_ids, cached_permissions)

            role_scope = target_data.get("scope")
            if not role_scope:
                raise HTTPException(status_code=400, detail="Target role scope not found.")
            if action == "assign":
                # Validate permission scopes according to role scope
                for pid in permission_ids:
                    perm = cached_permissions.get(pid)
                    if not perm:
                        continue  # Already validated earlier, safe fallback
                    perm_scope = perm.get("scope")
                    if role_scope == "college" and perm_scope == "global":
                        raise HTTPException(
                            status_code=400,
                            detail=f"Cannot assign global permissions to 'college' scope {model_obj}."
                        )

            assigned = set(
                map(str, target_data.get("permissions", {}).get("global_permissions", [])))
            assigned.update(
                map(str, target_data.get("permissions", {}).get("college_permissions", [])))
            existing_permission_ids = {
                str(p["id"]) for p in cached_permissions.values() if p["name"] in assigned}
            table_name = "role_permissions" if model_obj == "role" else "group_permissions"
            id_col = "role_id" if model_obj == "role" else "group_id"
            if action == "assign":
                permissions_to_modify = permission_ids - existing_permission_ids
                if not permissions_to_modify:
                    return JSONResponse(status_code=200,
                                        content={"message": "No permissions were added."})

                values = [{"target_id": target_id, "permission_id": int(pid)} for pid in
                          permissions_to_modify]
                query = text(f"""
                    INSERT INTO {table_name} ({id_col}, permission_id)
                    VALUES (:target_id, :permission_id) ON CONFLICT DO NOTHING
                """)

                await db.execute(query, values)

            else:  # revoke
                permissions_to_modify = permission_ids & existing_permission_ids
                if not permissions_to_modify:
                    return JSONResponse(status_code=200,
                                        content={"message": "No permissions were removed."})

                query = text(f"""
                    DELETE FROM {table_name}
                    WHERE {id_col} = :target_id AND permission_id = ANY(:permission_ids)
                """)
                await db.execute(query, {"target_id": target_id,
                                         "permission_ids": list(map(int, permissions_to_modify))})

            await db.commit()
            # Todo: Instead of initializing whole roles_and_permissions object, we can update the request object only
            if model_obj == "role":
                await utility_obj.cache_roles_and_permissions()
            else:
                await utility_obj.cache_groups_and_permissions()
            return JSONResponse(
                status_code=200,
                content={
                    "message": f"Permissions {'assigned' if action == 'assign' else 'revoked'} successfully.",
                    f"{model_obj}_id": target_id,
                    f"{action}ed_permissions": list(permissions_to_modify),
                }
            )
        except HTTPException as exc:
            raise exc
        except Exception as e:
            action_obj = ["assigning", "to"] if action == "assign" else ["revoking", "from"]
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while {action_obj[0]} the permissions, {action_obj[1]} "
                       f"{model}, Error: {e}."
            )

    async def delete_pgsql_entity(self, model, current_user, entity_id, db: AsyncSession):
        """
        Delete a role or group or permission from the system.

        This method allows authorized users to delete a specified role or permission. It performs
        the following operations based on the provided input:

        - Validates the user's authorization to delete roles or permissions.
        - Deletes the role or permission and associated records from the database.
        - Updates user roles by setting their "role" field to `None` if the role is deleted.
        - Removes the corresponding cache entries from Redis and refreshes the cache if necessary.

        Params:
            model: SQLAlchemy model class (Roles or Permission).
            current_user (dict): The currently authenticated user object, containing user permissions.
            db (AsyncSession): The async database session or collection object for MongoDB operations.
            entity_id (int | str): The ID of the entity to be deleted.

        Returns:
            JSONResponse: A JSON response indicating the success of the operation, along with the deleted
            `role_id` or `permission_id`.

        Raises:
            HTTPException (401): If the user is not authorized to delete the specified resource.
            HTTPException (404): If the specified role or permission does not exist.
            HTTPException (400): If an unexpected error occurs during the deletion process.
        """
        try:
            model_name = model.__name__
            model_obj = {"Roles": "role", "Permissions": "permission", "Groups": "group"}.get(
                model_name, "object")
            current_user_role_id = current_user.get("role_id").get("mongo_id")
            if not current_user_role_id:
                raise HTTPException(status_code=403, detail="User role not found")

            with db.no_autoflush:
                existing_entry = await self._fetch_entity(model, entity_id, db)
                if not existing_entry:
                    raise HTTPException(status_code=404, detail=f"{model_obj.title()} not found.")

                await self._check_permission(current_user, model_name, existing_entry.scope,
                                             action="delete")

                if model_name == "Roles":
                    allowed_roles = await self.fetch_role_descendants(current_user_role_id)
                    if entity_id not in allowed_roles:
                        raise HTTPException(
                            status_code=403,
                            detail="You can only delete roles under your own role or its children. "
                                   f"Invalid role_id '{entity_id}'.")
                    await DatabaseConfiguration().user_collection.update_many(
                        {"role.role_id": ObjectId(entity_id)},
                        {"$set": {"role": None}}
                    )
                    await DatabaseConfiguration().role_collection.delete_one(
                        {"_id": ObjectId(entity_id)})
                    await db.execute(
                        delete(RolePermission).where(RolePermission.role_id == existing_entry.id))
                    update_query = (update(Roles).where(Roles.parent_id == existing_entry.id)
                                    .values(parent_id=existing_entry.parent_id))
                    await db.execute(update_query)
                elif model_name == "Permission":
                    await db.execute(delete(RolePermission).where(
                        RolePermission.permission_id == existing_entry.id))
                elif model_name == "Groups":
                    await DatabaseConfiguration().user_collection.update_many(
                        {"group_ids": entity_id},
                        {"$pull": {"group_ids": entity_id}}
                    )
                    await db.execute(delete(GroupPermission).where(
                        GroupPermission.group_id == existing_entry.id))
                await db.delete(existing_entry)
            await db.commit()
            if not is_testing_env():
                redis_client = get_redis_client()
                cache_key_mapping = {
                    "Roles": "roles_permissions",
                    "Groups": "groups_and_permissions",
                    "Permission": "system_permissions"
                }
                cache_key = cache_key_mapping.get(model_name, "system_permissions")
                deleted_count = await redis_client.hdel(cache_key, str(entity_id))
                if deleted_count == 0:
                    if model_name == "Roles":
                        await utility_obj.cache_descendant_mongo_ids()
                    elif model_name == "Permission":
                        await utility_obj.cache_permissions(collection="system_permissions")
                    elif model_name == "Groups":
                        await utility_obj.cache_groups_and_permissions()
                    if model_name in ["Roles", "Permission"]:
                        await utility_obj.cache_roles_and_permissions()

            return JSONResponse(
                status_code=200,
                content={"message": f"{model_obj.title()} deleted successfully.", "id": entity_id}
            )
        except HTTPException as exc:
            raise exc
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(status_code=400,
                                detail=f"Deletion failed due to related records. Error: {e}")
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400,
                                detail=f"Something went wrong while deleting {model.__name__}: {e}")

    async def validate_user_ids_exist(self, user_ids: set) -> dict:
        """
        Validates whether the provided user IDs exist in the database.

        This method checks if each user ID provided is valid and exists in the database.
        If any of the provided user IDs do not exist, it raises an HTTPException with a detailed message.

        Params:
            user_ids (set): A set of user IDs to validate. Each ID should be a string.

        Raises:
            HTTPException: If no user IDs are provided, or if any of the user IDs do not exist in the database.

        Returns:
            set: A set of existing user IDs that were found in the database.
        """

        if not user_ids:
            raise HTTPException(status_code=400, detail="No user IDs provided.")

        user_ids = set(user_ids)

        user_id_objs = []
        for user_id in user_ids:
            await utility_obj.is_id_length_valid(_id=user_id, name="User ID")
            user_id_objs.append(ObjectId(user_id))
        user_data_list = await DatabaseConfiguration().user_collection.find(
            {"_id": {"$in": user_id_objs}}).to_list(length=None)
        user_data = {str(user["_id"]): user for user in user_data_list}
        existing_user_ids = set(user_data.keys())

        missing_ids = user_ids - existing_user_ids
        if missing_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid or non-existing User IDs: {', '.join(missing_ids)}"
            )

        return {
            "user_ids": existing_user_ids,
            "user_data": user_data
        }

    async def assign_revoke_group_user(self, action: str, current_user: dict, group_id: int,
                                       db: AsyncSession, request) -> JSONResponse:
        """
        Assign or revoke users from a specific group based on the action ('add' or 'remove').

        This method handles adding or removing users from a group and updates the database accordingly.
        It also ensures that only users with an "admin" or "super_admin" role can perform this action.
        The group data is updated in both the database and Redis cache.

        Params:
            action (str): The action to be performed. It must be either 'add' or 'remove'.
            current_user (dict): The current user initiating the action. The user's role must be checked.
            group_id (int): The ID of the group to modify.
            db (AsyncSession): The database session used for queries.
            request: The request object containing user IDs to be added or removed.

        Raises:
            HTTPException: If the action is invalid or if the user does not have the necessary role.

        Returns:
            JSONResponse: A response indicating whether users were successfully added or removed,
                          along with a list of affected user IDs and the group ID.

        Notes:
            - Users will only be added if they are not already in the group.
            - Users will only be removed if they are already part of the group.
            - The group data is updated in the Redis cache to reflect the changes.
        """
        try:
            if action not in ["add", "remove"]:
                raise ValueError("Invalid action. Must be 'add' or 'remove'.")

            if current_user.get("associated_colleges", []):
                raise HTTPException(
                    status_code=403,
                    detail="Group-user management is restricted to system-level users."
                )
            permissions = current_user.get("permissions", {})
            if not await self.has_permission(permissions, "global", "add_group_user"):
                raise HTTPException(status_code=401, detail="Not enough permissions")

            redis_client = get_redis_client()
            group_data = await self.validate_and_fetch_target_data("group", group_id, db,
                                                                   redis_client)
            request_data = request.model_dump(exclude_none=True)
            user_ids = request_data.get("user_ids", [])
            if not user_ids:
                action_noun = "added" if action == "add" else "removed"
                return JSONResponse(status_code=200,
                                    content={"message": f"No users were {action_noun}."})

            requested_users = await self.validate_user_ids_exist(user_ids)
            user_ids = requested_users.get("user_ids")
            group_scope = group_data.get("scope")
            if not group_scope:
                raise HTTPException(status_code=400, detail="Group scope not found.")
            existing_user_ids_in_group = set(map(str, group_data.get("users", [])))
            if action == "add":
                # Validate permission scopes according to role scope
                requested_users_data = requested_users.get("user_data")
                for uid in user_ids:
                    user_obj = requested_users_data.get(uid)
                    if not user_obj:
                        continue  # Already validated earlier, safe fallback
                    user_scope = "college" if user_obj.get("associated_colleges") else "global"
                    if group_scope == "college" and user_scope == "global":
                        raise HTTPException(
                            status_code=400,
                            detail=f"Cannot assign global users to 'college' scope group."
                        )
                users_to_modify = user_ids - existing_user_ids_in_group
                if not users_to_modify:
                    return JSONResponse(status_code=200,
                                        content={"message": "No users were added."})

                await DatabaseConfiguration().user_collection.update_many(
                    {"_id": {"$in": [ObjectId(uid) for uid in users_to_modify]}},
                    {"$addToSet": {"group_ids": group_id}}
                )

            else:  # remove
                users_to_modify = user_ids & existing_user_ids_in_group
                if not users_to_modify:
                    return JSONResponse(status_code=200,
                                        content={"message": "No users were removed."})

                await DatabaseConfiguration().user_collection.update_many(
                    {"_id": {"$in": [ObjectId(uid) for uid in users_to_modify]}},
                    {"$pull": {"group_ids": group_id}}
                )

            if action == "add":
                group_data.setdefault("users", []).extend(users_to_modify)
            else:
                group_data["users"] = [uid for uid in group_data.get("users", []) if
                                       uid not in users_to_modify]
            if redis_client:
                await redis_client.hset("groups_and_permissions", str(group_id),
                                        json.dumps(group_data))

            actioned = "added" if action == "add" else "removed"
            return JSONResponse(
                status_code=200,
                content={
                    "message": f"Users were successfully {actioned}.",
                    f"group_id": group_id,
                    f"{actioned}_users": list(users_to_modify),
                }
            )
        except HTTPException as exc:
            raise exc
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while {'adding' if action == 'add' else 'removing'} "
                       f"users from group. Error: {e}")
