"""
This file contains all functions regarding scholarship which will execute based on celery.
"""

from app.core.celery_app import celery_app
from app.database.configuration import DatabaseConfiguration
from app.core.utils import utility_obj
from bson import ObjectId
from app.background_task.scholarship import ScholarshipActivity
import asyncio
from app.core.reset_credentials import Reset_the_settings
from datetime import datetime, timezone


class ScholarshipCeleryTasks:
    """
    Contain functions related to scholarship celery task functions.
    """

    async def update_eligible_applicants_logic(
            self, programs_info: dict, normal_filters: dict, advance_filters: list, college_id: str,
            scholarship_id: str, user: dict) -> None:
        """
        Update eligible applications information in the DB.

        Params:
            - programs_info (dict): A dictionary which contains program (s) information.
            - normal_filters (dict): A dictionary which contains normal/pre-defined filters information.
            - advance_filters (list): A list of dictionaries which contains advance filters information.
            - college_id (str): An unique identifier/id of college.
            - scholarship_id (str): An unique identifier/id of scholarship.
            - user (dict): A dictionary containing user information.

        Returns: None
        """
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)

        eligible_applicants = await ScholarshipActivity().get_eligible_applicants_info(
            programs_info, normal_filters, advance_filters, college_id)

        if not isinstance(eligible_applicants, list):
            return

        await DatabaseConfiguration().scholarship_collection.update_one(
            {"_id": ObjectId(scholarship_id)}, {"$set": {"initial_eligible_applicants": eligible_applicants,
                                                "initial_eligible_applicants_count": len(eligible_applicants)}})

    @celery_app.task(bind=True, ignore_result=True)
    def update_eligible_applicants_info_in_db(
            self, programs_info: dict, normal_filters: dict, advance_filters: list, college_id: str,
            scholarship_id: str, user: dict) -> None:
        """
        Update eligible applications information in the DB.

        Params:
            - programs_info (dict): A dictionary which contains program (s) information.
            - normal_filters (dict): A dictionary which contains normal/pre-defined filters information.
            - advance_filters (list): A list of dictionaries which contains advance filters information.
            - college_id (str): An unique identifier/id of college.
            - scholarship_id (str): An unique identifier/id of scholarship.
            - user (dict): A dictionary containing user information.

        Returns: None
        """
        asyncio.run(ScholarshipCeleryTasks().update_eligible_applicants_logic(
            programs_info, normal_filters, advance_filters, college_id, scholarship_id, user
        ))
