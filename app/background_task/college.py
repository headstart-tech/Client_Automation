"""
This file contain class and functions related college which we use for background tasks
"""
from app.core.background_task_logging import background_task_wrapper
from app.core.log_config import get_logger
from app.helpers.course_configuration import CourseHelper

logger = get_logger(name=__name__)


class CollegeActivity:
    """
    Contain functions related to college activity
    """

    @background_task_wrapper
    async def create_courses(self, course_details, college_id):
        """
        Create courses
        """
        for course_data in course_details:
            await CourseHelper().create_new_course(
                {"course_name": course_data.get('courseName'), "course_description": None, "duration": None,
                 "fees": course_data.get("courseFees"), "is_activated": True,
                 "is_pg": course_data.get("isCoursePg"),
                 "school_name": course_data.get("school"),
                 'banner_image_url': None,
                 "course_activation_date": course_data.get(
                     "courseActivationDate"),
                 "course_deactivation_date": course_data.get(
                     "courseDeactivationDate"),
                 "course_specialization": [({"spec_name": item.strip(), "is_activated": True} if isinstance(item, str) else {"spec_name": item.get("spec_name", "").strip(), "is_activated": True, "lateral_entry": item.get("lateral", False)}) for item in
                                           course_data.get("courseSpecializations", [])]}, college_id)
        logger.info(f"Added courses for college whose id is {college_id}.")
