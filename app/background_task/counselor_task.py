"""
This file contain class and functions related to remove/add mark as absent to counselor, store login/email activity and
remove assign course
"""
import datetime

from bson import ObjectId
from fastapi.exceptions import HTTPException

from app.core.background_task_logging import background_task_wrapper
from app.core.log_config import get_logger
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import cache_invalidation

logger = get_logger(name=__name__)


class CounselorActivity:
    """
    Contain functions related to counselor activity
    """

    @background_task_wrapper
    async def remove_pre_leave_counselor(self, counselor_id):
        """
        Update the no_allocation_date in counselor_management if current_date<list(no_allocation_date)
        """
        today = datetime.datetime.utcnow().date()
        if (
                counselor := await DatabaseConfiguration().counselor_management.find_one(
                    {"_id": ObjectId(counselor_id)})
        ) is None:
            logger.info("Counselor holiday details not found")
            counselor = {}
        for leave_date in counselor.get("no_allocation_date", []):
            if leave_date < str(today):
                counselor.get("no_allocation_date", []).remove(leave_date)
        await DatabaseConfiguration().counselor_management.update_one(
            {"_id": ObjectId(counselor_id)},
            {"$set": {"no_allocation_date": counselor.get("no_allocation_date",
                                                          [])}},
        )

    @background_task_wrapper
    async def remove_assign_course(self, course_name,
                                   counselor_id, college_id):
        """
        Check and remove assign counselor from course and remove course
         from counselor
        """
        user = await DatabaseConfiguration().user_collection.find_one(
            {"_id": ObjectId(counselor_id)})
        all_course = []
        if len(course_name) < 1:
            if user.get("course_assign"):
                all_course = user.get("course_assign")
                await DatabaseConfiguration().user_collection.update_one(
                    {"_id": ObjectId(counselor_id)},
                    {"$unset": {"course_assign": ""}})
        else:
            if user.get("course_assign"):
                all_course = user.get("course_assign")
                all_course = [cor for cor in all_course if
                              cor not in course_name]
                await DatabaseConfiguration().user_collection.update_one(
                    {"_id": ObjectId(counselor_id)},
                    {"$set": {"course_assign": course_name}})
        for course in all_course:
            if (course_detail := await DatabaseConfiguration()
                    .course_collection.find_one(
                {"course_name": course,
                 "college_id": {
                     "$in": college_id}})) is not None:
                course_counselor = course_detail.get("course_counselor")
                if ObjectId(counselor_id) in course_counselor:
                    course_counselor.remove(ObjectId(counselor_id))
                    if len(course_counselor) < 1:
                        await DatabaseConfiguration().course_collection.update_one(
                            {"_id": ObjectId(course_detail.get("_id"))},
                            {"$unset": {"course_counselor": ""}})
                    else:
                        await DatabaseConfiguration().course_collection.update_one(
                            {"_id": ObjectId(course_detail.get("_id"))},
                            {"$set": {"course_counselor": course_counselor}})
        await cache_invalidation(api_updated="updated_user", user_id=user.get("email") if user else None)

    async def state_allocation_to_counselor(self, state_code, user,
                                            state_name):
        """
        allocation and remove state to counselor
        """
        if len(state_code) < 1:
            if user.get("state_assign"):
                await DatabaseConfiguration().user_collection.update_one(
                    {"_id": ObjectId(user.get("_id"))},
                    {"$unset": {"state_assign": "",
                                "state_name": ""}})
        else:
            await DatabaseConfiguration().user_collection.update_one(
                {"_id": ObjectId(user.get("_id"))},
                {"$set": {"state_assign": state_code,
                          "state_name": state_name}})
        await cache_invalidation(api_updated="updated_user", user_id=user.get("email") if user else None)

    async def source_allocation_to_counselor(self, source_name, user):
        """
        allocate and remove the source from user
        """
        source_name = [source.lower() for source in source_name]
        if len(source_name) < 1:
            if user.get("source_assign"):
                await DatabaseConfiguration().user_collection.update_one(
                    {"_id": ObjectId(user.get("_id"))},
                    {"$unset": {"source_assign": ""}})
        else:
            await DatabaseConfiguration().user_collection.update_one(
                {"_id": ObjectId(user.get("_id"))},
                {"$set": {"source_assign": source_name}})
        await cache_invalidation(api_updated="updated_user", user_id=user.get("email") if user else None)

    async def fresh_lead_allocation_to_counselor(self,
                                                 fresh_lead_limit: int | None,
                                                 user: dict | None,
                                                 language=None):
        """
        Store the fresh lead limit in the counselor details

        params:
            - fresh_lead_limit (int): Get the fresh lead limit number
            - user (dict): Get the user details
            - langauge (dict): Get the list of langauge
        return:
            None
        """
        if fresh_lead_limit is None:
            pass
        elif fresh_lead_limit == 0:
            await DatabaseConfiguration().user_collection.update_one(
                {"_id": ObjectId(user.get("_id"))},
                {"$unset": {"fresh_lead_limit": ""}})
        elif fresh_lead_limit > 0:
            await DatabaseConfiguration().user_collection.update_one(
                {"_id": ObjectId(user.get("_id"))},
                {"$set": {"fresh_lead_limit": fresh_lead_limit}})
        if language is None:
            pass
        elif language:
            await DatabaseConfiguration().user_collection.update_one(
                {"_id": ObjectId(user.get("_id"))},
                {"$set": {"language": language}})
        elif language == []:
            await DatabaseConfiguration().user_collection.update_one(
                {"_id": ObjectId(user.get("_id"))},
                {"$unset": {"language": ""}})
        await cache_invalidation(api_updated="updated_user", user_id=user.get("email") if user else None)

    async def specialization_allocation_to_counselor(
            self, specialization: list | None, user: dict | None):
        """
        Allocation specialization to the counselor

        params:
            - specialization (list): Get the specialization of course e.q.
                course name and their specialization name
            - user (dict): Get the user details

        return:
            - None
        """
        if specialization is None:
            pass
        elif specialization:
            for data in specialization:
                if (await DatabaseConfiguration().course_collection.find_one(
                        {"course_name": data.get("course_name"),
                         "course_specialization.spec_name": data.get(
                             "spec_name")}
                )) is None:
                    raise HTTPException(status_code=404,
                                        detail="specialization is not found")
            await DatabaseConfiguration().user_collection.update_one(
                {"_id": ObjectId(user.get("_id"))},
                {"$set": {"specialization_name": specialization}})

        elif specialization == []:
            await DatabaseConfiguration().user_collection.update_one(
                {"_id": ObjectId(user.get("_id"))},
                {"$unset": {"specialization_name": ""}})
        await cache_invalidation(api_updated="updated_user", user_id=user.get("email") if user else None)

    async def allocate_details_to_counselor(self,
                                            state_code: list | None = None,
                                            source_name: list | None = None,
                                            counselor_id: str | None = None,
                                            state_name: list | None = None,
                                            fresh_lead_limit: int = None,
                                            language: list | None = None,
                                            specialization: list | None = None):
        """
        Allocate state, fresh_lead_limit, language and source to the counselor

        params:
            - state_code (list): get the list of state code to allocate to
                counselor
            - source_name (list): Get the list of source data allocate to the
                counselor
            - counselor_id (str): Get the counselor id of the counselor
            - state_name (list): get the state name of the state allocate to
                the counselor
            - fresh_lead_limit (int): Get the fresh lead limit assign
                to counselor
            - langauge (list): Get the list of language name

        return:
            - None

        """
        user = await DatabaseConfiguration().user_collection.find_one(
            {"_id": ObjectId(counselor_id)})
        await self.state_allocation_to_counselor(state_code, user, state_name)
        await self.source_allocation_to_counselor(source_name, user)
        await self.fresh_lead_allocation_to_counselor(
            fresh_lead_limit=fresh_lead_limit, user=user, language=language)
        await self.specialization_allocation_to_counselor(
            specialization=specialization, user=user)
