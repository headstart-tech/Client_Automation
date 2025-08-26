"""
this file is contains function of the following signature for run add user timeline
"""

import datetime

from app.core import get_logger
from app.core.celery_app import celery_app
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj
from app.database.database_sync import DatabaseConfigurationSync
from app.dependencies.oauth import sync_cache_invalidation

logger = get_logger(name=__name__)

class login_activity:
    """a class storing login activity information"""

    @staticmethod
    @celery_app.task(ignore_result=True)
    def store_login_activity(user_name, ip_address, college_id=None):
        """
        Store login activity details of user
        """
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)
        if (
            user := DatabaseConfigurationSync("master").user_collection.find_one(
                {"user_name": user_name}
            )
        ) is not None:
            user_name = utility_obj.name_can(user)
            DatabaseConfigurationSync("master").user_collection.update_one(
                {"_id": user.get("_id")},
                {"$set": {"last_accessed": datetime.datetime.utcnow()}},
            )
        elif (
            user := DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                {"user_name": user_name}
            )
        ) is not None:
            user_name = utility_obj.name_can(user.get("basic_details", {}))
            DatabaseConfigurationSync().studentsPrimaryDetails.update_one(
                {"_id": user.get("_id")},
                {"$set": {"last_accessed": datetime.datetime.utcnow()}},
            )
        else:
            user = {}
        DatabaseConfigurationSync().login_activity_collection.insert_one(
            {
                "user_name": user_name,
                "user_id": user.get("_id"),
                "ip_address": ip_address,
                "created_at": datetime.datetime.utcnow(),
            }
        )
        sync_cache_invalidation(api_updated="updated_user", user_id=user.get("email"))
