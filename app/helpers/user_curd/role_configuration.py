"""
This file contain class and functions related to role
"""
from fastapi.exceptions import HTTPException

from app.database.configuration import DatabaseConfiguration


class RoleHelper:
    """
    Contain functions related to role
    """

    def role_serialize(self, item):
        """
        Get the permissions and menus of user according to role_type
        """
        return {"permission": item.get("permission"), "menus": item.get("menus"),
                "student_menus": item.get("student_menus")}

    def role_helper(self, item):
        """
        Get role details
        """
        return {
            "user_type": item.get("role_name"),
            "permission": item.get("permission"),
            "menus": item.get("menus"),
            "student_menus": item.get("student_menus")
        }

    def permission_helper(self, item):
        """
        Get permission
        """
        return {"permission": item.get("permission")}

    async def create_new_role(self, role: dict) -> dict:
        """
        Create new role
        """
        role_name = role.get("role_name", "").lower()
        find_role = await DatabaseConfiguration().role_collection.find_one({"role_name": role_name})
        if find_role:
            raise HTTPException(
                status_code=422,
                detail=f"Role name '{role.get('role_name')}' already exist.",
            )
        if role_name in ["super_admin", "client_manager"]:
            role = {
                "role_name": role_name,
                "permission": {
                    "add_client": True,
                    "delete_client": True,
                    "purge_client_data": True,
                },
            }
        else:
            role = {
                "role_name": role_name,
                "permission": {
                    "add_client": False,
                    "delete_client": False,
                    "purge_client_data": False,
                },
            }
        await DatabaseConfiguration().role_collection.insert_one(role)
        return {"message": True}
