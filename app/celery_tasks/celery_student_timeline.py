"""
This file contain class and functions related to student timeline
"""

import datetime
import time

from bson import ObjectId
from kombu.exceptions import KombuError

from app.core.celery_app import celery_app
from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj
from app.database.database_sync import DatabaseConfigurationSync

logger = get_logger(name=__name__)


class StudentActivity:
    """
    Contain functions related to student activity
    """

    @staticmethod
    @celery_app.task(ignore_result=True)
    def student_timeline(
            student_id,
            event_type=None,
            event_status=None,
            application_id=None,
            event_name=None,
            user_id=None,
            template_type=None,
            template_id=None,
            template_name=None,
            message=None,
            college_id=None,
    ):
        """
        Store student timeline
        """
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)
        if (
                student := DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(student_id)}
                )
        ) is not None:
            data = {
                "timestamp": datetime.datetime.utcnow(),
                "event_type": event_type,
                "event_status": event_status,
                "message": message,
                "template_name": template_name,
                "template_id": template_id,
                "template_type": template_type,
                "event_name": event_name,
            }

            if application_id:
                data.update(
                    {"application_id": ObjectId(application_id)}
                )
            if user_id:
                data.update({"user_id": ObjectId(user_id)})
            timeline = DatabaseConfigurationSync().studentTimeline.find_one(
                {"student_id": ObjectId(student.get("_id"))}
            )
            if timeline:
                DatabaseConfigurationSync().studentTimeline.update_one(
                    {"student_id": ObjectId(student.get("_id"))},
                    {"$push": {"timelines": {"$each": [data],
                                             "$position": 0}}},
                )
            else:
                timeline = {"timelines": [data],
                            "student_id": ObjectId(student_id)}
                DatabaseConfigurationSync().studentTimeline.insert_one(
                    timeline)

    @staticmethod
    @celery_app.task(ignore_result=True)
    def add_student_timeline(
            student_id,
            event_type="Application",
            event_status=None,
            message=None,
            college_id=None,
    ):
        """
        Helper function for add student timeline
        """
        time.sleep(5)
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)
        if (
                student := DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(student_id)}
                )
        ) is None:
            student = {}
        try:
            application = DatabaseConfigurationSync().studentApplicationForms.find_one(
                {"student_id": ObjectId(student.get("_id"))}
            )
        except Exception as error:
            logger.error(
                f"An error got when get application data at the time "
                f"of store timeline of student. Error - {error}"
            )
            application = {}
        if not application:
            application = {}
        try:
            course = DatabaseConfigurationSync().course_collection.find_one(
                {"_id": ObjectId(str(application.get("course_id")))}
            )
        except Exception as error:
            logger.error(
                f"An error got when get course data at the time "
                f"of store timeline of student. Error - {error}"
            )
            course = {}
        course_name = (
            (
                f"{course.get('course_name')}" f" in {application.get('spec_name1')}")
            if (application.get("spec_name1") != "" and application.get(
                "spec_name1"))
            else f"{course.get('course_name')} Program"
        )
        name = (
            f"{utility_obj.name_can(student.get('basic_details'))}"
            f" {message} "
            f"{course_name} whose Application Number is "
            f"{application.get('custom_application_id')}"
        )
        try:
            StudentActivity().student_timeline(
                student_id=str(student_id),
                event_type=event_type,
                event_status=event_status,
                message=name,
                application_id=str(application.get("_id"))
            )
        except KombuError as celery_error:
            logger.error(
                f"Got celery error when storing timeline of student. "
                f"Error - {celery_error}"
            )
        except Exception as error:
            logger.error(
                f"An error got when storing timeline of student. " f"Error - {error}"
            )
