"""
This file contain class and functions related to key category
"""
from datetime import datetime
from app.core.custom_error import CustomError
from app.database.configuration import DatabaseConfiguration
from bson import ObjectId
from app.core.utils import utility_obj
from app.database.aggregation.admin_user import AdminUser


class Updates:
    """
    Contain functions related to send/get updates
    """

    async def user_update_helper(self, document):
        """
        Helper function for get user update details.
        """
        return {
            "_id": str(document.get("_id")),
            "title": document.get("title"),
            "selected_profiles": document.get("selected_profiles"),
            "created_at": utility_obj.get_local_time(
                document.get("created_at")),
            "last_updated_on": utility_obj.get_local_time(
                document.get("last_updated_on")),
            "created_by": str(document.get("created_by")),
            "created_by_name": document.get("created_by_name"),
            "content": document.get("content")
        }

    async def send_update_to_profiles(
            self, college_id: str, send_update_info: dict,
            user: dict) -> dict:
        """
        Send update to the selected profiles.

        Params:
            - college_id (str): A unique id/identifier of a college.
                e.g., 123456789012345678901234
            - send_update_info (dict): A dictionary which contains send update
                info. e.g., {"selected_profiles":
                ["super_admin", "college_admin"], "title": "Test update",
                "content": "Test content"}
            - user (dict): A dictionary which contains user information.
            - role_name (str): Current user role name.


        Returns:
            A dictionary which contains information about create key category.
        """
        role_name = user.get("role", {}).get("role_name")
        if (
                role := await DatabaseConfiguration().role_collection.find_one(
                    {"role_name": role_name})) is None:
            raise CustomError("Permissions not found. Please ensure that you "
                              "have the permission.")
        if not role.get("menus").get("resources", {}).get("resources", {}).get(
                "menu"):
            raise CustomError("Not enough permission to send update.")
        selected_profiles = send_update_info.get("selected_profiles")
        if (role_name == "college_super_admin" and
            "super_admin" in selected_profiles) or \
                (role_name == "college_admin" and
                 "college_super_admin" in selected_profiles):
            raise CustomError("Not able to send update to the super admin.")
        title = send_update_info.get("title", "").title()
        content = send_update_info.get("content")
        user_id = ObjectId(user.get("_id"))
        user_name = utility_obj.name_can(user)
        current_datetime = datetime.utcnow()
        inserted_data = await (DatabaseConfiguration().user_updates_collection.
        insert_one(
            {"title": title, "content": content,
             "selected_profiles": selected_profiles,
             "created_at": current_datetime,
             "last_updated_on": current_datetime,
             "created_by": user_id,
             "created_by_name": user_name
             }))
        update_id = inserted_data.inserted_id
        content = (f"Hey <span class='notification-inner'>{{name}}</span>, "
                   f"Here is a new update for you from "
                   f"<span class='notification-inner'>{user_name}"
                   f"({await utility_obj.get_role_name_in_proper_format(role_name)})"
                   f"</span>. {content}")
        notification_info = await AdminUser().get_notification_info_of_users(
            college_id, selected_profiles, content, current_datetime,
            update_id, title)
        if len(notification_info) >= 1:
            inserted_data = await (DatabaseConfiguration().
                                   notification_collection.insert_many(
                notification_info))
            inserted_ids = inserted_data.inserted_ids
            for new_id, info in zip(inserted_ids, notification_info):
                info["id"] = new_id
            await utility_obj.bulk_update_to_redis(notification_info)
            return {"message": "Send update to the selected profiles."}
        return {"detail": "No user found for send update."}
