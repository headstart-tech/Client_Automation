"""
This file contain classes and functions related admin user which we use for background tasks
"""

from app.core.background_task_logging import background_task_wrapper
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration


class DownloadRequestActivity:
    """
    Use for store/get download request activity details
    """

    @background_task_wrapper
    async def store_download_request_activity(
            self,
            request_type,
            requested_at,
            ip_address,
            user,
            total_request_data,
            is_status_completed,
            request_completed_at=None,
    ):
        """
        Use for store download request activity details
        """
        activity_download_request = await DatabaseConfiguration().activity_download_request_collection.insert_one(
            {
                "request_type": request_type,
                "requested_at": requested_at,
                "ip_address": ip_address,
                "user_id": user.get("_id"),
                "user_name": utility_obj.name_can(user),
                "total_request_data": total_request_data,
                "is_status_completed": is_status_completed,
                "user_role_name": user.get("role", {}).get("role_name"),
                "role_id": user.get("role", {}).get("role_id"),
                "request_completed_at": request_completed_at,
            }
        )
