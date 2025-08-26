"""
This file contains schemas related to roles and permissions.
"""
import json
from datetime import datetime

from bson import ObjectId
from pymongo import UpdateOne

from app.core import get_logger
from app.core.custom_error import CustomError, DataNotFoundError, ObjectIdInValid
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache, \
    cache_invalidation
from app.helpers.client_automation.master_helper import Master_Service

logger = get_logger(__name__)


class RolePermissionFeature:
    """
    This class is used to represent the role permission method
    """

    async def create_feature_group(
            self,
            payload: list,
            group_name: str,
            user: dict | None = None,
            group_description: str | None = None,
            update: bool = False
    ):
        """
        Create a new feature group.

        Params:
            payload (list): List of features to be added to the group.
            group_name (str): Name of the group.

        Returns:
            dict: Dictionary containing the group name and features.
        """
        if (reformatted := await DatabaseConfiguration().role_collection.find_one(
                {"name": group_name})):
            if not update:
                raise CustomError("Group already exists")

        reformatted_data = {}

        if not payload:
            raise CustomError("Payload is empty")

        if (master_details := await DatabaseConfiguration().master_screens.find_one(
                {"screen_type": "master_screen", "dashboard_type": "admin_dashboard"})
        ) is None:
            raise CustomError(message="Master screen controller not exists.")

        await self.update_role_controller(payload=payload,
                                          reformatted_data=reformatted_data,
                                          master_details=master_details)
        if reformatted_data:
            if update:
                if reformatted:
                    reformatted.get("menus", {}).update(reformatted_data)
                if group_description:
                    reformatted["group_description"] = group_description
                reformatted["updated_at"] = datetime.utcnow()
                await DatabaseConfiguration().role_collection.update_one(
                    {"name": group_name}, {"$set": reformatted})
            else:
                await DatabaseConfiguration().role_collection.insert_one(
                    {"name": group_name, "scope": "group", "is_activated": True,
                     "menus": reformatted_data, "created_by": user.get("user_name"),
                     "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(),
                     "group_description": group_description}
                )
            return {"message": f"Group {group_name} {'updated' if update else 'created'} "
                               f"successfully."}

    async def update_role_controller(
            self, payload: list,
            reformatted_data: dict,
            master_details: dict | None = None,
    ):
        """
        Update the dashboard controller data by the super admin

        Param:
            payload (list): Get the details of the dashboard
            reformatted_data (dict): Get the reformatted data
            master_details (dict): Get the master details

        Return:
            Return success message
        """
        for data in payload:
            temp_list = None
            if master_details.get(data.get("feature_id")):
                feature_id = data.get('feature_id')
                if data.get("features", []):
                    temp_list = data.pop("features", [])
                if not reformatted_data.get(feature_id):
                    reformatted_data[feature_id] = {}
                reformatted_data[feature_id].update(data)
            else:
                raise DataNotFoundError(message=f"This key '{data.get('feature_id')}' is")
            if temp_list:
                if not reformatted_data[data.get("feature_id")].get("features"):
                    reformatted_data[data.get("feature_id")]["features"] = {}
                if not master_details[data.get("feature_id")].get("features"):
                    master_details[data.get("feature_id")]["features"] = {}
                await self.update_role_controller(
                    payload=temp_list,
                    reformatted_data=reformatted_data[data.get("feature_id")]["features"],
                    master_details=master_details[data.get("feature_id")]["features"]
                )

    async def update_role_feature(
            self, role_id: str,
            payload: list,
            dashboard_type: str = "admin_dashboard",
            college_id: str | None = None
    ):
        """
        Update the role feature in the database.

        Params:
            role_id (str): The id of the role to update.
            payload (list): A list of dictionaries containing the feature details to be updated.
            dashboard_type (str): The type of dashboard to update. Default is "admin_dashboard".
            college_id (str | None): The id of the college, if applicable.

        Returns:
            dict: A dictionary containing the success message.
        """
        if not ObjectId.is_valid(role_id):
            raise ObjectIdInValid(_id=role_id, name="Role ID")
        role_details = None
        temp_role = False
        if college_id:
            if not ObjectId.is_valid(college_id):
                raise ObjectIdInValid(_id=college_id, name="College ID")

            if await DatabaseConfiguration().college_collection.find_one(
                    {"_id": ObjectId(college_id)}) is None:
                raise DataNotFoundError(message="College")

            Reset_the_settings().check_college_mapped(college_id=college_id)

            role_details = await DatabaseConfiguration().college_roles.find_one(
                {"_id": ObjectId(role_id)})

            if role_details is None:
                temp_role = True

        if not (role_details and college_id):
            if (role_details := await DatabaseConfiguration().role_collection.find_one(
                    {"_id": ObjectId(role_id)})) is None:
                raise DataNotFoundError("Role")

        if (master_details := await DatabaseConfiguration().master_screens.find_one(
                {"screen_type": "master_screen", "dashboard_type": dashboard_type})
        ) is None:
            raise DataNotFoundError(message="Master screen controller not exists.")

        reformatted_data = {}
        if role_details.get("menus", {}):
            reformatted_data = role_details.get("menus", {})
            if temp_role:
                reformatted_data = {}

        await self.update_role_controller(
            reformatted_data=reformatted_data, payload=payload, master_details=master_details)
        if reformatted_data:
            role_details["menus"] = reformatted_data

            if college_id:
                await DatabaseConfiguration().college_roles.update_one(
                    {"_id": ObjectId(role_id)},
                    {"$set": {**role_details, "updated_at": datetime.utcnow()}},
                    upsert=True
                )
            else:
                await DatabaseConfiguration().role_collection.update_one(
                    {"_id": ObjectId(role_id)},
                    {"$set": {**role_details, "updated_at": datetime.utcnow()}},
                    upsert=True
                )
            return {"message": f"Role {role_details.get('role_name')}"
                               f" feature created successfully."}

    async def update_role_specific_fields(
            self, _id: str, payload: dict,
            field_name: str,
            invalidation_route: str,
            college_id: str | None = None
    ):
        """
        Update the role-specific fields for a user.

        Params:
            role_id (str): The ID of the role to update.
            payload (dict): A dictionary containing the updated user data.
            field_name (str): The name of the field to update.
            invalidation_route (str): The route for cache invalidation.

        Returns:
            dict: A dictionary containing the success message.
        """
        if not ObjectId.is_valid(_id):
            raise ObjectIdInValid(_id=f"{field_name}_id", name=f"{field_name} ID")

        if not payload.get("feature_id"):
            raise CustomError(message="Feature ID is required.")

        if college_id:
            if not ObjectId.is_valid(college_id):
                raise ObjectIdInValid(_id=college_id, name="College ID")

            if await DatabaseConfiguration().college_collection.find_one(
                    {"_id": ObjectId(college_id)}) is None:
                raise DataNotFoundError(message="College")

            Reset_the_settings().check_college_mapped(college_id=college_id)

            if (reformatted_data := await DatabaseConfiguration().college_roles.find_one(
                    {"_id": ObjectId(_id)},
            )) is None:
                raise DataNotFoundError(message=field_name)

        else:
            if (reformatted_data := await DatabaseConfiguration().role_collection.find_one(
                    {"_id": ObjectId(_id)},
            )) is None:
                raise DataNotFoundError(message=field_name)

        data = reformatted_data.get("menus", {})

        await Master_Service().recursive_check(data=data, target_id=payload.get("feature_id"),
                                               update_data=payload)

        if college_id:
            await DatabaseConfiguration().college_roles.update_one(
                {"_id": ObjectId(_id)},
                {"$set": {"menus": data, "updated_at": datetime.utcnow()}}
            )
        else:
            await DatabaseConfiguration().role_collection.update_one(
                {"_id": ObjectId(_id)},
                {"$set": {"menus": data, "updated_at": datetime.utcnow()}}
            )

        await cache_invalidation(api_updated=invalidation_route)
        await utility_obj.update_role_features(role_id=_id)

        return {"message": f"{field_name}-specific fields updated successfully."}

    async def get_role_features(
            self,
            _id: str,
            field_name: str,
            college_id: str | None = None
    ):
        """
        Get the role features by role id

        Params:
            role_id (str): The id of the role
            field_name (str): The name of the field to get.
            college_id (str | None): The id of the college, if applicable.

        Returns:
            dict: A dictionary containing the role features
        """
        if not ObjectId.is_valid(_id):
            raise ObjectIdInValid(_id=f"{field_name}_id", name=f"{field_name} ID")

        if college_id:
            if not ObjectId.is_valid(_id):
                raise ObjectIdInValid(_id=f"{field_name}_id", name=f"{field_name} ID")

            if await DatabaseConfiguration().college_collection.find_one(
                    {"_id": ObjectId(college_id)}) is None:
                raise DataNotFoundError(message="College")

            Reset_the_settings().check_college_mapped(college_id=college_id)

            if (reformatted_data := await DatabaseConfiguration().college_roles.find_one(
                    {"_id": ObjectId(_id)},
            )) is None:
                raise DataNotFoundError(message=field_name)

        else:
            if (reformatted_data := await DatabaseConfiguration().role_collection.find_one(
                    {"_id": ObjectId(_id)},
            )) is None:
                raise DataNotFoundError(message=field_name)

        data = reformatted_data.get("menus", {})

        final_data = []
        for key, value in data.items():
            if isinstance(value, dict) and "feature_id" in value:
                if value.get("features"):
                    value["features"] = await Master_Service().temp_data_func(value["features"])
                final_data.append(value)
        field = field_name.lower()
        return {"message": f"{field_name} features fetched successfully.",
                "data": final_data,
                f"{field}_name": reformatted_data.get("name"),
                f"{field}_description": reformatted_data.get(f"{field}_description"),
                f"{field}_id": str(reformatted_data.get("_id"))}

    async def get_all_role(
            self,
            page_num: int,
            page_size: int
    ):
        """
        Get all roles from the database.

        Params:
            page_num (int): A page number of the document
            page_size (int): A page size of the document

        Returns:
            list: A list of dictionaries containing all roles.
        """
        skip, limit = await utility_obj.return_skip_and_limit(
            page_num=page_num, page_size=page_size)
        roles = await DatabaseConfiguration().role_collection.aggregate([
            {
                "$match": {
                    "scope": "group"
                }
            },
            {
                "$facet": {
                    "totalCount": [{"$count": "count"}],
                    "paginatedResults": [
                        {"$skip": skip},
                        {"$limit": limit},
                        {
                            "$project": {
                                "_id": {"$toString": "$_id"},
                                "name": 1,
                                "group_description": 1
                            }
                        }
                    ]
                }
            },
            {
                "$project": {
                    "totalCount": {"$arrayElemAt": ["$totalCount.count", 0]},
                    "results": "$paginatedResults"
                }
            }
        ]).to_list(length=None)
        if not roles:
            raise DataNotFoundError(message="Group")
        data = roles[0]
        if not data.get("results"):
            raise DataNotFoundError(message="Group")
        response = await utility_obj.pagination_in_aggregation(
            page_num,
            page_size,
            data.get("totalCount", 0),
            route_name="roles/get_all_role")
        return {
            "data": data.get("results", []),
            "total": data.get("totalCount", 0),
            "count": len(data.get("results", [])),
            "pagination": response["pagination"],
            "message": "data fetch successfully"
        }

    async def get_assigned_permissions(self, payload: dict):
        """
        Get the assigned permissions for a role.

        Params:
            payload (dict): A dictionary containing the role ID.

        Returns:
            dict: A dictionary containing the assigned permissions.
        """
        if not ObjectId.is_valid(payload.get("user_id")):
            raise ObjectIdInValid(_id=payload.get("user_id"), name="User ID")

        if (user := await DatabaseConfiguration().user_collection.find_one(
                {"_id": ObjectId(payload.get("user_id"))}
        )) is None:
            raise DataNotFoundError(message="User")
        group_permissions_ids = []
        group_permissions = []
        if user.get("assign_group_permissions", []):
            group_permissions = user.get("assign_group_permissions", [])
            group_permissions_ids = [str(group_permission.get("group_id"))
                                     for group_permission in group_permissions]

        for group_id in payload.get("group_ids", []):
            if not ObjectId.is_valid(group_id):
                raise ObjectIdInValid(_id=group_id, name="Group ID")

            if (group_details := await DatabaseConfiguration().role_collection.find_one(
                    {"_id": ObjectId(group_id)})) is None:
                raise DataNotFoundError(message=f"Group {group_id}")

            if group_details.get("user_permissions", []):
                group_details["user_permissions"].append(ObjectId(payload.get("user_id")))
            else:
                group_details["user_permissions"] = [ObjectId(payload.get("user_id"))]

            await DatabaseConfiguration().role_collection.update_one(
                {"_id": ObjectId(group_id)},
                {"$set": {"user_permissions": group_details["user_permissions"],
                          "updated_at": datetime.utcnow()}}
            )

            if group_id not in group_permissions_ids:
                group_permissions.append({"group_id": ObjectId(group_id),
                                          "name": group_details.get("name"),
                                          "description": group_details.get("group_description"),
                                          "created_at": datetime.utcnow()})

        await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(payload.get("user_id"))},
            {"$set": {"assign_group_permissions": group_permissions,
                      "updated_at": datetime.utcnow()}}
        )

        return {"message": "permission has been assigned."}

    async def delete_feature_group(
            self,
            _id: str,
            feature_id: str | None = None,
    ):
        """
        Delete a feature group.

        Params:
            _id (str): The ID of the group to delete.
            feature_id (str): The ID of the feature to delete.

        Returns:
            dict: A dictionary containing the success message.
        """
        if not ObjectId.is_valid(_id):
            raise ObjectIdInValid(_id=_id, name="Group or  Role")

        if (group_details := await DatabaseConfiguration().role_collection.find_one(
                {"_id": ObjectId(_id)}
        )) is None:
            raise DataNotFoundError(message="Group")

        if not feature_id:
            await DatabaseConfiguration().role_collection.delete_one(
                {"_id": ObjectId(_id)})
            return {"message": f"Role and Group id {_id} deleted successfully"}

        data = group_details.get("menus", {})

        response = await Master_Service().recursive_check(data=data, target_id=feature_id)

        if response:
            await DatabaseConfiguration().role_collection.update_one(
                {"_id": ObjectId(_id)},
                {"$set": {"menus": data, "updated_at": datetime.utcnow()}}
            )
            return {"message": f"Feature id {feature_id} deleted successfully."}
        raise CustomError(message=f"Feature ID {feature_id} "
                                  f"not found in group {group_details.get('name')}.")

    async def mapped_role_permissions(
            self,
            data: dict,
            user: dict,
    ):
        """
        Map the role permissions for a user.

        Params:
            data (dict): A dictionary containing the role permissions.
            user (dict): A dictionary containing the user details.

        Returns:
            dict: A dictionary containing the mapped role permissions.
        """
        from app.database.motor_base_singleton import MotorBaseSingleton
        master_data = MotorBaseSingleton.get_instance().master_data
        is_college = False
        college_data = {}
        if user.get("associated_colleges", []):

            college_id_master = master_data.get("college_id")

            for college_id in user.get("associated_colleges", []):
                if str(college_id) == str(college_id_master):
                    is_college = True
                    break

            if not is_college:
                raise CustomError(message="College ID not found in associated colleges.")
            field = f"admin_dashboard/{str(college_id_master)}"
            college_data = await get_collection_from_cache(
                collection_name="master_screen", field=field)

            if not college_data:
                college_details = await DatabaseConfiguration().master_screens.find_one(
                    {"college_id": ObjectId(college_id_master),
                     "screen_type": "college_screen",
                     "dashboard_type": "admin_dashboard"})

                if not college_details:
                    raise CustomError(
                        message=f"College screen not available for college id {college_id_master}")

                college_data = {}
                if college_details:
                    for key, value in college_details.items():
                        if isinstance(value, dict) and "feature_id" in value:
                            college_data[key] = value

                if college_data:
                    await store_collection_in_cache(collection=college_data,
                                                    collection_name="master_screen", field=field)

        if user.get("assign_group_permissions", []):
            for group in user.get("assign_group_permissions", []):
                if (group_details := await DatabaseConfiguration().role_collection.find_one(
                        {"_id": ObjectId(group.get("group_id"))})) is None:
                    raise DataNotFoundError(message="Group")
                group_menus = group_details.get("menus", {})
                data = await utility_obj.merge_values(
                    data=data, data2=group_menus, bool_check=True)

        if is_college and college_data:
            data = await utility_obj.merge_values(data=data, data2=college_data, bool_check=False)

        return data

    async def get_role_permissions(
            self,
            user: dict,
            dashboard_type: str = "admin_dashboard"
    ):
        """
        Get the role permissions for a user.

        Params:
            user (dict): A dictionary containing the user details.

        Returns:
            dict: A dictionary containing the role permissions.
        """
        college_id = None
        if dashboard_type == "admin_dashboard":
            if user.get("associated_colleges", []):
                result = await DatabaseConfiguration().college_roles.find_one(
                    {"_id": ObjectId(user.get("role", {}).get("role_id"))},
                    {"_id": 0, "name": 1, "menus": 1})

            else:
                result = await DatabaseConfiguration().role_collection.find_one(
                    {"_id": ObjectId(user.get("role", {}).get("role_id"))},
                    {"_id": 0, "name": 1, "menus": 1})
            if result is None:
                raise DataNotFoundError(message="Role")
            roles_features = result.get("menus", {})
            roles_features = await self.mapped_role_permissions(
                data=roles_features, user=user)
        else:
            college_id = str(user.get("college_id"))
            if (result := await DatabaseConfiguration().master_screens.find_one(
                    {"dashboard_type": dashboard_type, "screen_type": "college_screen",
                     "college_id": ObjectId(college_id)})) is None:
                raise DataNotFoundError(message="College screen")
            roles_features = {}
            for key, value in result.items():
                if isinstance(value, dict) and "feature_id" in value:
                    roles_features[key] = value

        if not roles_features:
            raise DataNotFoundError(message="Role permissions")

        data = json.dumps(roles_features, default=str)
        data = json.loads(data)

        return {"message": f"Role permissions fetched successfully.",
                "data": data,
                "dashboard_type": dashboard_type,
                "college_id": college_id
                }

    async def get_user_group_details(
            self,
            user_id: str,
            page_num: int = 1,
            page_size: int = 10
    ):
        """
        Get the user group details.

        Params:
            user_id (str): The ID of the user.
            page_num (int): The page number for pagination.
            page_size (int): The number of items per page.

        Returns:
            dict: A dictionary containing the user group details.
        """
        if not ObjectId.is_valid(user_id):
            raise ObjectIdInValid(_id=user_id, name="User ID")

        skip, limit = await utility_obj.return_skip_and_limit(
            page_num=page_num, page_size=page_size)

        result = await DatabaseConfiguration().user_collection.aggregate([
            {
                "$match": {
                    "_id": ObjectId(user_id)
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total_count": {
                        "$size": {"$ifNull": ["$assign_group_permissions", []]}
                    },
                    "assign_group_permissions": {
                        "$map": {
                            "input": {
                                "$slice": [
                                    "$assign_group_permissions",
                                    skip,
                                    limit
                                ]
                            },
                            "as": "permission",
                            "in": {
                                "group_id": {"$toString": "$$permission.group_id"},
                                "name": "$$permission.name",
                                "description": {"$ifNull": [
                                    "$$permission.description", {"$literal": ""}]},
                                "created_at": {
                                    "$cond": {
                                        "if": {"$ne": ["$$permission.created_at", None]},
                                        "then": {"$dateToString": {
                                            "format": "%Y-%m-%d %H:%M:%S",
                                            "date": "$$permission.created_at",
                                            "timezone": "Asia/Kolkata"
                                        }},
                                        "else": None
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ]).next()

        if not result:
            raise DataNotFoundError(message="User")

        permissions = result.get("assign_group_permissions", [])
        total = result.get("total_count", 0)

        response = await utility_obj.pagination_in_aggregation(
            page_num,
            page_size,
            total,
            route_name="roles/get_all_role")
        return {
            "data": permissions,
            "total": total,
            "count": len(permissions),
            "pagination": response["pagination"],
            "message": "data fetch successfully"
        }

    async def remove_feature_group(
            self,
            user_id: str,
            group_ids: list[str],
            current_user: str
    ) -> dict:
        """
        Remove a user from one or more groups and update permissions accordingly.

        Args:
            user_id: ID of the user to remove from groups
            group_ids: List of group IDs to remove the user from
            current_user: ID of the user performing this action (for audit purposes)

        Returns:
            dict: Success message with operation result

        Raises:
            ObjectIdInValid: If any provided ID is invalid
            DataNotFoundError: If user or any group is not found
            CustomError: If permission validation fails for any group
        """
        # Validate all IDs upfront
        if not ObjectId.is_valid(user_id):
            raise ObjectIdInValid(_id=user_id, name="User ID")

        invalid_groups = [gid for gid in group_ids if not ObjectId.is_valid(gid)]
        if invalid_groups:
            raise ObjectIdInValid(_id=invalid_groups[0], name="Group ID")

        # Get user with only necessary fields
        user = await DatabaseConfiguration().user_collection.find_one(
            {"_id": ObjectId(user_id)},
            {"assign_group_permissions": 1}
        )
        if not user:
            raise DataNotFoundError(message="User")

        user_perms = user.get("assign_group_permissions", [])
        if not user_perms:
            raise CustomError(message="User has no assigned group permissions")

        # Convert to sets for efficient comparison
        user_group_ids = {str(perm.get("group_id")) for perm in user_perms}
        requested_groups = set(group_ids)

        # Validate all groups at once
        missing_user_groups = requested_groups - user_group_ids
        if missing_user_groups:
            raise CustomError(
                message=f"User not assigned to groups: {', '.join(missing_user_groups)}"
            )

        # Check group existence and permissions in bulk
        existing_groups = await DatabaseConfiguration().role_collection.find(
            {"_id": {"$in": [ObjectId(gid) for gid in group_ids]}},
            {"user_permissions": 1}
        ).to_list(length=None)

        existing_group_ids = {str(g["_id"]) for g in existing_groups}
        missing_groups = requested_groups - existing_group_ids
        if missing_groups:
            raise DataNotFoundError(message=f"Groups not found: {', '.join(missing_groups)}")

        # Check user membership in all groups
        oid_user_id = ObjectId(user_id)
        invalid_memberships = [
            str(g["_id"]) for g in existing_groups
            if oid_user_id not in g.get("user_permissions", [])
        ]
        if invalid_memberships:
            raise CustomError(
                message=f"User not member of groups: {', '.join(invalid_memberships)}"
            )

        # Prepare bulk operations
        bulk_ops = []
        current_time = datetime.utcnow()

        # Group updates
        for group_id in group_ids:
            bulk_ops.append(UpdateOne(
                {"_id": ObjectId(group_id)},
                {
                    "$pull": {"user_permissions": oid_user_id},
                    "$set": {"updated_at": current_time}
                }
            ))

        # User permission updates
        updated_perms = [
            perm for perm in user_perms
            if str(perm.get("group_id")) not in group_ids
        ]

        await DatabaseConfiguration().user_collection.update_one(
            {"_id": oid_user_id},
            {
                "$set": {
                    "assign_group_permissions": updated_perms,
                    "updated_at": current_time
                }
            }
        )

        # Execute all operations in a single batch
        await DatabaseConfiguration().role_collection.bulk_write(bulk_ops)

        return {
            "message": f"Successfully removed user from {len(group_ids)} group(s)",
            "removed_groups": group_ids
        }
