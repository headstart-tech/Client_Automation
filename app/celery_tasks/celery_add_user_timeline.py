"""
this file contains all function of add user timeline using celery.
"""

import datetime

from app.core.celery_app import celery_app
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import logger
from app.database.database_sync import DatabaseConfigurationSync


class UserActivity:
    """
    Contain functions related to user activity
    """

    @staticmethod
    @celery_app.task(ignore_result=True)
    def add_user_timeline(user, event_type, event_status, college_id=None):
        """
        Store student timeline
        this is used to in test cases
        """
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)
        try:
            if user is None:
                user = {}
            data = {
                "timelines": [
                    {
                        "timestamp": datetime.datetime.utcnow(),
                        "event_type": event_type,
                        "event_status": event_status,
                    }
                ]
            }
            timeline = DatabaseConfigurationSync(
                "master"
            ).user_timeline_collection.find_one({"user_id": user.get("_id")})
            if timeline:
                timeline.get("timelines", []).insert(0, data.get("timelines", [])[0])
                DatabaseConfigurationSync("master").user_timeline_collection.update_one(
                    {"user_id": user.get("_id")},
                    {"$set": {"timelines": timeline.get("timelines")}},
                )
            else:
                data.update(
                    {
                        "user_id": user.get("_id"),
                        "user_type": user.get("role", {}).get("role_name"),
                    }
                )
                DatabaseConfigurationSync("master").user_timeline_collection.insert_one(
                    data
                )
        except Exception as e:
            logger.error(f"Something went wrong. {e}")
