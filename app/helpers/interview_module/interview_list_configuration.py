"""
This file contains class and functions related to interview list
"""

import asyncio
import datetime

from bson import ObjectId
from fastapi import Request
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError
from pymongo.errors import PyMongoError

from app.background_task.send_mail_configuration import EmailActivity
from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.background_task_logging import background_task_wrapper
from app.core.custom_error import DataNotFoundError, CustomError
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.database.aggregation.interview_list import InterviewListAggregation
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import is_testing_env
from app.helpers.interview_module.interview_list_conf_aggregation import (
    Interview_aggregation,
)
from app.helpers.interview_module.selection_procedure_configuration import (
    SelectionProcedure,
)
from app.helpers.template.template_configuration import TemplateActivity
from app.helpers.user_curd.user_configuration import UserHelper
from app.s3_events.s3_events_configuration import upload_csv_and_get_public_url

logger = get_logger(name=__name__)


class InterviewList:
    """
    Contains functions related to interview list
    """

    async def is_valid_interview_list(self, interview_list_id):
        """
        Helper function to fetch the interview list data from the database based on id.

        Params:
            interview_list_id (str): An unique id for get interview list data.

        Returns:
            dict: A dictionary which contains interview list data.
        """
        await utility_obj.is_id_length_valid(
            _id=interview_list_id, name="Interview list id"
        )
        if (
            interview_list := await DatabaseConfiguration().interview_list_collection.find_one(
                {"_id": ObjectId(interview_list_id)}
            )
        ) is None:
            raise HTTPException(
                status_code=404,
                detail="Interview list not found. Make sure provided interview list id should be correct.",
            )
        return interview_list

    async def update_interview_list_data(
        self,
        interview_list_id: str,
        interview_list_data: dict,
        last_modified_timeline: list,
    ) -> dict:
        """
        Update interview list data.

        Params:
            interview_list_id (str): An unique id for update interview list data.
            interview_list_data (dict): A data which useful for update interview list.
            user (dict): A dictionary which contains user data.
            current_datetime (datetime): current date and time in utc format.
            last_modified_timeline (list): A list which contains last modified timeline data such user_id,
                                           user_name and datetime.

        Returns:
            dict: A dictionary which contains update interview list data info.
        """
        interview_list = await self.is_valid_interview_list(interview_list_id)
        list_name = interview_list_data.get("list_name")
        if list_name and list_name != interview_list.get("list_name"):
            if (
                await DatabaseConfiguration().interview_list_collection.find_one(
                    {"list_name": interview_list_data.get("list_name")}
                )
                is not None
            ):
                return {"detail": "Interview list name already exists."}
        course_name = interview_list_data.get("course_name")
        if course_name and course_name != interview_list.get("course_name"):
            if (
                await DatabaseConfiguration().interview_list_collection.find_one(
                    {
                        "course_name": interview_list_data.get("course_name"),
                        "specialization_name": interview_list_data.get(
                            "specialization_name"
                        ),
                    }
                )
                is not None
            ):
                return {"detail": "Interview list for course already exists."}
        status = interview_list_data.get("status")
        if interview_list_data.get("status"):
            interview_list_data["status"] = status.title()
        interview_list.get("last_modified_timeline", []).insert(
            0, last_modified_timeline[0]
        )
        interview_list_data.update(
            {"last_modified_timeline": interview_list.get("last_modified_timeline")}
        )
        await DatabaseConfiguration().interview_list_collection.update_one(
            {"_id": ObjectId(interview_list_id)}, {"$set": interview_list_data}
        )
        return {"message": "Interview list data updated."}

    async def add_interview_list_data(
        self,
        interview_list_data: dict,
        current_datetime: datetime,
        last_modified_timeline: list,
        user: dict,
        current_user,
    ) -> dict:
        """
        Add interview list data.

        Params:
            interview_list_data (dict): A data which useful for create interview list.
            current_datetime (datetime): current date and time in utc format.
            last_modified_timeline (list): A list which contains last modified timeline data such user_id,
            user_name and datetime.
            user (dict): A dictionary which contains user data.

        Returns:
            dict: A dictionary which contains add interview list data info.
        """
        for name in ["school_name", "list_name", "course_name", "moderator_id"]:
            if interview_list_data.get(name) in ["", None]:
                raise HTTPException(
                    status_code=422, detail=f"{name} must be required and valid."
                )
        if await DatabaseConfiguration().interview_list_collection.find_one(
            {"list_name": interview_list_data.get("list_name")}
        ):
            raise HTTPException(
                status_code=422, detail="Interview list name already exist."
            )
        interview_list_data.update(
            {
                "created_by": user.get("_id"),
                "created_by_name": utility_obj.name_can(user),
                "created_at": current_datetime,
                "last_modified_timeline": last_modified_timeline,
                "status": "Active",
            }
        )
        if (
            selection_procedure := await DatabaseConfiguration().selection_procedure_collection.find_one(
                {
                    "course_name": interview_list_data.get("course_name"),
                    "specialization_name": interview_list_data.get(
                        "specialization_name"
                    ),
                }
            )
        ) is not None:
            for item in ["course_name", "specialization_name", "_id"]:
                if selection_procedure.get(item):
                    selection_procedure.pop(item)
            interview_list_data.update({"selection_procedure": selection_procedure})
        await DatabaseConfiguration().interview_list_collection.insert_one(
            interview_list_data
        )
        await self.add_applications_into_list(interview_list_data)
        return {"message": "Interview list added."}

    async def create_or_update_interview_list(
        self,
        current_user: str,
        interview_list_data: dict,
        interview_list_id: str | None,
    ) -> dict:
        """
        Create or update interview list data.

        Params:
            current_user (str): An user_name of current user.
            interview_list_data (dict): A data which useful for create/update interview list.
            interview_list_id (str): An unique id for update interview list data.

        Returns:
            dict: A dictionary which contains create/update interview list data.
        """
        user = await SelectionProcedure().is_valid_user_and_role(current_user)
        current_datetime = datetime.datetime.utcnow()
        last_modified_timeline = await TemplateActivity().get_last_timeline(user)
        moderator_id = interview_list_data.get("moderator_id")
        if moderator_id:
            moderator = await DatabaseConfiguration().user_collection.find_one(
                {"_id": ObjectId(moderator_id)}
            )
            interview_list_data["moderator_id"] = ObjectId(moderator_id)
            interview_list_data["moderator_name"] = utility_obj.name_can(moderator)
        if interview_list_id:
            return await self.update_interview_list_data(
                interview_list_id, interview_list_data, last_modified_timeline
            )
        else:
            return await self.add_interview_list_data(
                interview_list_data,
                current_datetime,
                last_modified_timeline,
                user,
                current_user,
            )

    async def add_students_into_interview_list(
        self, current_user: str, application_ids: list, interview_list_id: str
    ) -> dict:
        """
        Add students into interview list.

        Params:\n
            current_user (str): An user_name of current user.
            application_ids (list): A list which contains application ids in a string format.\n
            interview_list_id (str): An unique interview list id.

        Returns:
            dict: A dictionary which contains add students related info.
        """
        user = await SelectionProcedure().is_valid_user_and_role(current_user)
        interview_list = await self.is_valid_interview_list(interview_list_id)
        list_application_ids = interview_list.get("application_ids", [])
        eligible_application_ids = interview_list.get("eligible_applications", [])
        if not eligible_application_ids:
            eligible_application_ids = []
        if not list_application_ids:
            list_application_ids = []
        application_ids = [
            ObjectId(_id)
            for _id in application_ids
            if ObjectId(_id) not in list_application_ids
        ]
        list_application_ids = application_ids + list_application_ids
        eligible_application_ids = application_ids + eligible_application_ids
        last_modified_timeline = await TemplateActivity().get_last_timeline(user)
        interview_list.get("last_modified_timeline", []).insert(
            0, last_modified_timeline[0]
        )
        await DatabaseConfiguration().interview_list_collection.update_one(
            {"_id": ObjectId(interview_list_id)},
            {
                "$set": {
                    "application_ids": list_application_ids,
                    "eligible_applications": eligible_application_ids,
                    "last_modified_timeline": interview_list.get(
                        "last_modified_timeline", []
                    ),
                }
            },
        )
        await DatabaseConfiguration().studentApplicationForms.update_many(
            {
                "_id": {"$in": application_ids},
                "interview_list_id": {"$ne": ObjectId(interview_list_id)},
            },
            {"$push": {"interview_list_id": ObjectId(interview_list_id)}},
        )
        return {"message": "Students added into interview list."}

    async def delete_students_from_interview_list(
        self, current_user: str, application_ids: list, interview_list_id: str
    ) -> dict:
        """
        Delete students from interview list.

        Params:\n
            current_user (str): An user_name of current user.
            application_ids (list): A list which contains application ids
            in a string format.\n
            interview_list_id (str): An unique interview list id.

        Returns:
            dict: A dictionary which contains delete students related info.
        """
        user = await UserHelper().is_valid_user(current_user)
        if user.get("role", {}).get("role_name") not in [
            "college_super_admin",
            "college_admin",
            "moderator",
        ]:
            raise HTTPException(status_code=401, detail=f"Not enough permissions")
        interview_list = await self.is_valid_interview_list(interview_list_id)
        application_ids = [
            ObjectId(_id)
            for _id in application_ids
            if await utility_obj.is_id_length_valid(_id, name=f"Application id {_id}")
        ]
        list_application_ids = interview_list.get("application_ids", [])
        list_eligible_ids = interview_list.get("eligible_applications", [])
        for application_id in application_ids:
            for name in [list_application_ids, list_eligible_ids]:
                if application_id in name:
                    name.remove(application_id)
        last_modified_timeline = await TemplateActivity().get_last_timeline(user)
        interview_list.get("last_modified_timeline", []).insert(
            0, last_modified_timeline[0]
        )
        await DatabaseConfiguration().interview_list_collection.update_one(
            {"_id": ObjectId(interview_list_id)},
            {
                "$set": {
                    "application_ids": list_application_ids,
                    "eligible_applications": list_eligible_ids,
                    "last_modified_timeline": interview_list.get(
                        "last_modified_timeline", []
                    ),
                }
            },
        )
        await DatabaseConfiguration().studentApplicationForms.update_many(
            {
                "_id": {"$in": application_ids},
                "interview_list_id": {"$in": [ObjectId(interview_list_id)]},
            },
            {"$pull": {"interview_list_id": ObjectId(interview_list_id)}},
        )
        return {"message": "Students deleted from interview list."}

    async def update_status_of_interview_lists(
        self, current_user: str, interview_list_ids: list[str], status
    ) -> dict:
        """
        Change status of interview lists by ids.

        Params:\n
            current_user (str): An user_name of current user.
                For example, test@gmail.com
            interview_list_ids (list): A list which contains
                interview list ids in a string format.\n
                For example, ["64b4d5036605c8470f4bb123",
                        "64b4d5036605c8470f4bb124"]
            status: A status want to update for interview lists.
                For example, Closed.

        Returns:
            dict: A dictionary which contains change status of interview
                list ids.
            Successful Response: {"message": "Interview lists status updated."}
        """
        _ids = []
        for _id in interview_list_ids:
            await utility_obj.is_length_valid(_id=_id, name="Interview list id")
            if status.title() == "Archived":
                await self.check_interview_list_future_slot(_id)
            _ids.append(ObjectId(_id))
        await DatabaseConfiguration().interview_list_collection.update_many(
            {"_id": {"$in": _ids}}, {"$set": {"status": status.title()}}
        )
        return {"message": "Interview lists status updated."}

    async def check_interview_list_future_slot(self, interview_list_id: str):
        """
        Check interview list associated with future slot of not and
            raised error if interview list associated with future slot.

        Params:
            interview_list_id (str): An unique id/identifier of interview list.

        Raises:
            DataNotFoundError: An exception occurred when interview list not
                found.
            CustomError: An exception occurred when certain condition fails.
        """
        if (
            interview_list := await DatabaseConfiguration().interview_list_collection.find_one(
                {"_id": ObjectId(interview_list_id)}
            )
        ) is None:
            raise DataNotFoundError(_id=interview_list_id, message="Interview list")
        current_datetime = datetime.datetime.utcnow()
        if (
            await DatabaseConfiguration().slot_collection.find_one(
                {
                    "interview_list_id": ObjectId(interview_list_id),
                    "time": {"$gt": current_datetime},
                }
            )
        ) is not None:
            raise CustomError(
                message=f"Not able to delete interview list "
                f"`{interview_list.get('list_name')}` "
                f"because it is associated with future slot."
            )

    async def delete_interview_list(self, _id):
        """
        Delete interview list

        Params:\n
            _id (list): A list which contains interview_list ids in a
            string format.\n

        Returns:
            message: Interview list has been deleted successfully.
        """
        interview_ids = []
        for ids in _id:
            await utility_obj.is_length_valid(ids, "interview_id")
            await self.check_interview_list_future_slot(ids)
            interview_ids.append(
                DatabaseConfiguration().interview_list_collection.delete_many(
                    {"_id": ObjectId(ids)}
                )
            )
            await DatabaseConfiguration().studentApplicationForms.update_many(
                {"interview_list_id": {"$in": [ObjectId(ids)]}},
                {"$pull": {"interview_list_id": ObjectId(ids)}},
            )
        try:
            await asyncio.gather(*interview_ids)
        except Exception:
            return {"message": "Interview list is not delete."}
        return {"message": "Interview list has been deleted successfully."}

    async def download_interview_list(self, _id, type=None):
        """
        download interview list

        Params:\n
            _id (list): A list which contains interview_list ids in a
            string format.\n
            type (string): A string describing the type of the string
            that will be None or grid

        Returns:
            message: Interview lists download.
        """
        interview_ids = []
        for ids in _id:
            await utility_obj.is_length_valid(ids, "interview_id")
            if (
                await DatabaseConfiguration().interview_list_collection.find_one(
                    {"_id": ObjectId(ids)}
                )
                is None
            ):
                raise DataNotFoundError(ids, "Interview list")
            interview_ids.append(ObjectId(ids))
        if type == "grid":
            interview_detail = await Interview_aggregation().get_grid_interview_list(
                interview_ids
            )
        else:
            interview_detail = await Interview_aggregation().get_detail_interview_list(
                interview_ids
            )
        if interview_detail:
            data_keys = list(interview_detail[0].keys())
            get_url = await upload_csv_and_get_public_url(
                fieldnames=data_keys, data=interview_detail, name="counselors_data"
            )
        else:
            raise DataNotFoundError
        return get_url

    async def get_gd_pi_interview_detail(
        self, scope=None, page_num=None, page_size=None
    ):
        """
        Get interview list details

        Returns:
            message: Get GD PI Interview lists.
        """
        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
        if scope == "grid":
            pipeline = await Interview_aggregation().get_grid_interview_list(
                skip=skip, limit=limit
            )
        else:
            pipeline = await Interview_aggregation().get_detail_interview_list(
                skip=skip, limit=limit
            )
        try:
            result = DatabaseConfiguration().interview_list_collection.aggregate(
                pipeline
            )
        except PyMongoError as error:
            logger.error(f"Error getting {error.args}")
        total = 0
        interview_details = []
        async for data in result:
            try:
                total = data.get("totalCount")[0].get("count")
            except IndexError:
                total = 0
            except Exception:
                total = 0
            interview_details = data.get("paginated_results")
        response = await utility_obj.pagination_in_aggregation(
            skip, limit, total, route_name="/interview/gd_pi_interview_list/"
        )
        return {
            "data": interview_details,
            "total": total,
            "count": len(interview_details),
            "pagination": response["pagination"],
            "message": "data fetch successfully",
        }

    async def get_interview_list_applications_data_based_on_program(
        self,
        current_user: str,
        page_num: int | None,
        page_size: int | None,
        payload: dict,
    ) -> dict:
        """
        Get interview list applicants data based on program with/without
        filters. For example, Program `B.Sc.` applicants data with/without
        data.

        Params:
            current_user (str): An user_name of current user.
                    For example, test@gmail.com
            page_num (int | None): Useful for show applications data "
                        "of program on a particular page. For example, 1
        page_size (int | None): Useful for show limited data on "
                        "particular page. For example, 25
            payload (dict): A dictionary which contains
                filterable fields and their values

        Returns:
            dict: A dictionary which contains interview list
             applicants data along with total count.
        """
        await UserHelper().is_valid_user(current_user)
        (
            total_data,
            applications_data,
            total_program_applicants,
        ) = await InterviewListAggregation().get_interview_list_applications_data_based_on_program(
            page_num, page_size, payload
        )
        response = await utility_obj.pagination_in_aggregation(
            page_num,
            page_size,
            total_data,
            "/interview_list/applications_data_based_on_program/",
        )
        return {
            "data": applications_data,
            "total": total_data,
            "count": page_size,
            "pagination": response.get("pagination"),
            "message": "Get interview list applicants data.",
            "total_program_applicants": total_program_applicants,
        }

    @background_task_wrapper
    async def send_offer_letter_to_candidate(
        self, application_ids, user, request, college, current_user
    ):
        """
        Send offer letter to candidate.

        Params:
            applicants_ids (list): A list which contains unique identifier/id
                of application.
        """
        try:
            ip_address = utility_obj.get_ip_address(request)
            for application_id in application_ids:
                if (
                    application := await DatabaseConfiguration().studentApplicationForms.find_one(
                        {"_id": application_id}
                    )
                ) is None:
                    application = {}
                if (
                    student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                        {"_id": application.get("student_id")}
                    )
                ) is None:
                    student = {}
                if (
                    interview_list := await DatabaseConfiguration().interview_list_collection.find_one(
                        {"_id": application.get("interview_list_data", {}).get("interview_list_id")}
                    )
                ) is None:
                    interview_list = {}
                if (
                    selection_procedure := interview_list.get("selection_procedure", {})
                ) is None:
                    selection_procedure = {}
                if user.get("_id") != str(
                    selection_procedure.get("offer_letter", {}).get(
                        "authorized_approver"
                    )
                ):
                    logger.error("User don't have permission to send offer letter.")
                    return
                email_id = student.get("user_name")
                email_ids = await EmailActivity().add_default_set_mails(email_id)
                template = selection_procedure.get("offer_letter", {}).get("template")
                if not is_testing_env():
                    await utility_obj.publish_email_sending_on_queue(data={
                        "email_preferences": college.get("email_preferences", {}),
                        "email_type": "transactional",
                        "email_ids": email_ids,
                        "subject": "Offer Letter",
                        "template": template,
                        "event_type": "email",
                        "event_status": f"sent by {utility_obj.name_can(user)}",
                        "event_name": "Offer letter",
                        "current_user": current_user,
                        "ip_address": ip_address,
                        "payload": {
                                "content": "Offer letter template",
                                "email_list": email_ids,
                            },
                        "attachments": None,
                        "action_type": "system",
                        "college_id": college.get("id"),
                        "priority": True,
                        "data_segments": None,
                        "template_id": None,
                        "add_timeline": True,
                        "environment": settings.environment
                    }, priority=10)
                await DatabaseConfiguration().studentApplicationForms.update_one(
                    {"_id": application_id},
                    {
                        "$set": {
                            "offer_letter": {
                                "issued_date": datetime.datetime.utcnow(),
                                "letter_details": template,
                            }
                        }
                    },
                )
                try:
                    toml_data = utility_obj.read_current_toml_file()
                    if toml_data.get("testing", {}).get("test") is False:
                        # TODO: Not able to add student timeline data in the
                        #  DB when performing celery task so added condition
                        #  which add student timeline when environment is
                        #  not development. We'll remove the condition when
                        #  celery work fine.
                        if (
                            course := await DatabaseConfiguration().course_collection.find_one(
                                {"_id": application.get("course_id")}
                            )
                        ) is None:
                            course = {}
                        course_name = (
                            (
                                f"{course.get('course_name')} "
                                f"{application.get('spec_name1')}"
                            )
                            if application.get("spec_name1") is not None
                            else f"{course.get('course_name')} program"
                        )
                        # TODO: Not able to add student timeline data
                        #  using celery task when environment is
                        #  demo. We'll remove the condition when
                        #  celery work fine.
                        if settings.environment in ["demo"]:
                            StudentActivity().student_timeline(
                                student_id=str(student.get("_id")),
                                event_type="Interview",
                                event_status="Sent offer letter",
                                message=f"{utility_obj.name_can(student.get('basic_details', {}))} "
                                f"has received offer letter "
                                f"for {course_name}",
                                college_id=str(student.get("college_id")),
                            )
                        else:
                            if not is_testing_env():
                                StudentActivity().student_timeline.delay(
                                    student_id=str(student.get("_id")),
                                    event_type="Interview",
                                    event_status="Sent offer letter",
                                    message=f"{utility_obj.name_can(student.get('basic_details', {}))} "
                                    f"has received offer letter "
                                    f"for {course_name}",
                                    college_id=str(student.get("college_id")),
                                )
                except KombuError as celery_error:
                    logger.error(
                        f"error sending offer letter" f" timeline data {celery_error}"
                    )
                except Exception as error:
                    logger.error(
                        f"error sending offer letter" f" timeline data {error}"
                    )
        except Exception as e:
            logger.error(
                "Error got at the time of send offer letter to "
                f"candidate. Error - {str(e)}"
            )

    async def change_interview_status_of_candidates(
        self,
        current_user: str,
        interview_status_data: dict,
        is_approval_status: bool,
        request: Request,
        college: dict,
    ) -> dict:
        """
        Change the status of interview candidates, useful for
        further/next process.

        Params:\n
            current_user (str): An user_name of current user.
                e.g., test@gmail.com
            interview_status_data (dict): A dictionary which contains
                applicants ids and status in a string format.\n
                e.g., {"application_ids":
                ["64b4d5036605c8470f4bb123", "64b4d5036605c8470f4bb124"],
                "status": "Shortlisted"}

        Returns:
            dict: A dictionary which contains information about change
                interview status of candidates.

        Raises:
            401 (No permission): Raised error with status code 401
                when student and unauthorized user try to change interview
                candidates status.
            422 (Invalid value): Raised error with status code 422
                when invalid condition matched.
        """
        user = await UserHelper().is_valid_user(current_user)
        interview_list_id = interview_status_data.get("interview_list_id")
        await utility_obj.is_length_valid(
            _id=interview_list_id, name=f"Interview list id"
        )
        interview_list_id = ObjectId(interview_list_id)
        if (
            interview_list := await DatabaseConfiguration().interview_list_collection.find_one(
                {"_id": interview_list_id}
            )
        ) is None:
            raise DataNotFoundError(message="Interview list")
        application_ids = interview_status_data.get("application_ids", [])
        application_ids = [
            ObjectId(_id)
            for _id in application_ids
            if await utility_obj.is_length_valid(_id=_id, name=f"Application id")
        ]
        status = interview_status_data.get("status")
        name = "interviewStatus.status"
        if is_approval_status:
            name = "approval_status"
        else:
            await InterviewList().update_the_status_of_student(
                application_ids=application_ids, status=status
            )
        if status == "Seat Blocked":
            name = "seat_blocked"
        if status is None:
            await DatabaseConfiguration().studentApplicationForms.update_many(
                {"_id": {"$in": application_ids}}, {"$unset": {name: True}}
            )
        else:
            status_date = interview_status_data.get("status").replace(" ", "_").lower()
            await DatabaseConfiguration().studentApplicationForms.update_many(
                {"_id": {"$in": application_ids}},
                {
                    "$set": {
                        name: status,
                        f"{status_date}_date": datetime.datetime.utcnow(),
                        "interview_list_data": {
                            "interview_list_id": interview_list_id,
                            "interview_list_name": interview_list.get("list_name"),
                        },
                    }
                },
            )
        if name == "approval_status" and status == "Selected":
            await self.send_offer_letter_to_candidate(
                application_ids, user, request, college, current_user
            )

        return {"message": "Updated the status of candidates."}

    async def delete_operation_on_slots_panels(
        self, filter_dict: dict, panel_filter: dict
    ) -> None:
        """
        Delete linked data before delete the panels or slots.

        Params:
            filter_dict: A common filter dictionary which useful for get slots
                or panels data.
            panel_filter: A which useful for get data.

        Returns:
            None: Not returning anything.
        """
        panels = await DatabaseConfiguration().panel_collection.aggregate([{"$match": panel_filter}]).to_list(length=None)
        for panel_doc in panels:
            await DatabaseConfiguration().slot_collection.delete_many(
                {"panel_id": panel_doc.get("_id")}
            )
        slot_dict = {"panel_id": {"$nin": [None, ""]}, "take_slot.application": False}
        slot_dict.update(filter_dict)
        slots = await DatabaseConfiguration().slot_collection.aggregate([{"$match": slot_dict}]).to_list(length=None)

        for slot_doc in slots:
            panel_id = slot_doc.get("panel_id")
            if (
                panel_data := await DatabaseConfiguration().panel_collection.find_one(
                    {"_id": panel_id}
                )
            ) is not None:
                slot_duration = slot_doc.get("slot_duration")
                total_slot_duration = (
                    panel_data.get("total_slot_duration") - slot_duration
                )
                slot_count = panel_data.get("slot_count") - 1
                total_gap = (slot_count - 1) * panel_data.get("gap_between_slots")
                total_gap_between_slots = 0 if total_gap <= 0 else total_gap
                slot_gap_duration = total_slot_duration + total_gap_between_slots
                await DatabaseConfiguration().panel_collection.update_one(
                    {"_id": panel_data.get("_id")},
                    {
                        "$set": {
                            "slot_count": slot_count,
                            "total_slot_duration": total_slot_duration,
                            "total_gap_between_slots": total_gap_between_slots,
                            "slot_gap_duration": slot_gap_duration,
                            "available_time": panel_data.get("available_time")
                            + slot_duration,
                        }
                    },
                )

    async def delete_slots_or_panels(self, delete_info: dict) -> dict:
        """
        Delete slots or panels by slot/panel ids
            (not able to delete both slots/panels at the same time).

        Params:\n
            delete_info (dict): A dictionary which contains delete slots/panels
                info. For example, {"_ids":
                ["64b4d5036605c8470f4bb123", "64b4d5036605c8470f4bb124"]}

        Returns:
            dict: A dictionary contains info about delete slots and panels.
        """
        slots_panels_ids = delete_info.get("slots_panels_ids", [])
        deletable_ids = [
            ObjectId(_id)
            for _id in slots_panels_ids
            if await utility_obj.is_length_valid(_id, name=f"Id")
        ]
        filter_dict = {"_id": {"$in": deletable_ids}}
        panel_filter: dict = {"status": {"$ne": "published"}}
        panel_filter.update(filter_dict)
        await self.delete_operation_on_slots_panels(filter_dict, panel_filter)
        await DatabaseConfiguration().panel_collection.delete_many(panel_filter)
        filter_dict.update({"take_slot.application": {"$in": [False, None]}})
        await DatabaseConfiguration().slot_collection.delete_many(filter_dict)
        return {"message": "Operation successfully done."}

    async def add_applications_into_list(self, interview_list_data):
        """
        Add applicants to the interview list, useful for show data whenever
            required.

        Params:
            interview_list_data (dict): A dictionary which useful for get
                interview list applicants ids.

        Returns:
            None: Not returning anything.

        Raises:
            Exception: Raise exception when certain condition failed.
        """
        try:
            applications_ids = await InterviewListAggregation().get_interview_list_applications_data_based_on_program(
                None, None, interview_list_data, add_applications=True
            )
            await DatabaseConfiguration().interview_list_collection.update_one(
                {"list_name": interview_list_data.get("list_name")},
                {
                    "$set": {
                        "application_ids": applications_ids,
                        "eligible_applications": applications_ids,
                    }
                },
            )
            interview_list = (
                await DatabaseConfiguration().interview_list_collection.find_one(
                    {"list_name": interview_list_data.get("list_name")}
                )
            )
            if not interview_list:
                interview_list = {}
            interview_list_id = interview_list.get("_id")
            await DatabaseConfiguration().studentApplicationForms.update_many(
                {
                    "_id": {"$in": applications_ids},
                    "interview_list_id": {"$ne": interview_list_id},
                },
                {"$push": {"interview_list_id": interview_list_id}},
            )
        except Exception as e:
            logger.error(
                f"Error got at the time of add applicants to the "
                f"list. Error - {str(e)}"
            )

    async def interview_list_selected_applicants_data(
        self, current_user: str, page_num: int, page_size: int, payload: dict
    ) -> dict:
        """
        Get interview list selected applicants data based on interview list id.

        Params:
            current_user (str): An user_name of current user.
                    e.g., test@gmail.com
            page_num (int): Useful for show interview list selected applicants'
                    data on a particular page. e.g., 1
        page_size (int): Useful for show limited data on
                    particular page. e.g., 25
            payload (dict): A dictionary which contains
                filterable fields with their values.

        Returns:
            dict: A dictionary which contains interview list
             selected applicants data along with its summary.
        """
        (
            total_data,
            selected_applicants_data,
        ) = await InterviewListAggregation().interview_list_selected_applicants_data(
            page_num, page_size, payload
        )
        response = await utility_obj.pagination_in_aggregation(
            page_num,
            page_size,
            total_data,
            "/interview_list/selected_student_applications_data/",
        )
        return {
            "data": selected_applicants_data,
            "total": total_data,
            "count": page_size,
            "pagination": response.get("pagination"),
            "message": "Get interview list selected applicants data.",
        }

    @background_task_wrapper
    async def update_the_status_of_student(self, application_ids, status):
        """
        Update the status of application

        params:
            application_ids (list): list of application ids
            status (str): the status of the application
        """
        for _id in application_ids:
            if (
                application := await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"_id": ObjectId(_id)}
                )
            ) is None:
                continue
            slot_type = application.get("meetingDetails.slot_type", "")
            await DatabaseConfiguration().studentApplicationForms.update_one(
                {"_id": ObjectId(_id)},
                {"$set": {f"{slot_type.lower()}_status.interview_result": status}},
            )

    async def send_applicants_for_approval(
        self, application_ids: list[str], payload: dict
    ) -> dict:
        """
        Send applicants for approval.
        When applicants selected for interview, user can send applicants for final
        review/approval.

        Params:\n
            current_user (str): An user_name of current user.
                e.g., test@gmail.com
            application_ids (list[str]): A list which contains application
                ids in a string format.
                e.g., ["64b4d5036605c8470f4bb123", "64b4d5036605c8470f4bb124"]
            payload (dict): A dictionary which contains filters. Useful
                for get applications ids.

        Returns:
            dict: A dictionary which contains information about send approval
                applicants.

        Raises:
            401 (No permission): Raised error with status code 401
                when student and unauthorized user try to change interview
                candidates status.
            422 (Invalid value): Raised error with status code 422
                when invalid condition matched.
        """
        interview_list_id = payload.get("interview_list_id")
        await utility_obj.is_length_valid(interview_list_id, name="Interview list id")
        if (
            interview_list := await DatabaseConfiguration().interview_list_collection.find_one(
                {"_id": ObjectId(interview_list_id)}
            )
        ) is None:
            raise DataNotFoundError(message="Interview list")
        if not application_ids:
            application_ids = interview_list.get("eligible_applications", [])
            if application_ids:
                application_ids = await InterviewListAggregation().interview_list_selected_applicants_data(
                    None,
                    None,
                    payload,
                    get_applicant_ids=True,
                    application_ids=application_ids,
                )
        application_ids = [
            ObjectId(_id)
            for _id in application_ids
            if await utility_obj.is_length_valid(_id, name=f"Application id")
        ]
        await self.update_the_status_of_student(
            application_ids=application_ids, status="Under Review"
        )
        if application_ids:
            await DatabaseConfiguration().studentApplicationForms.update_many(
                {"_id": {"$in": application_ids}},
                {
                    "$set": {
                        "approval_status": "Under Review",
                        "interview_list_data": {
                            "interview_list_id": interview_list.get("_id"),
                            "interview_list_name": interview_list.get("list_name"),
                        },
                        "send_approval_date": datetime.datetime.utcnow(),
                    }
                },
            )
        return {"message": "Send applicants for approval."}

    async def approval_pending_applicants_data(
        self, current_user: str, page_num: int, page_size: int
    ) -> dict:
        """
        Get approval pending applicants' data with/without pagination.

        Params:
            current_user (str): An user_name of current user.
                    e.g., test@gmail.com
            page_num (int): Useful for show approval pending applicants'
                    data on a particular page. e.g., 1
            page_size (int): Useful for show limited data on
                    particular page. e.g., 25

        Returns:
            dict: A dictionary which contains approval pending applicants'
                data.
        """
        (
            total_data,
            approval_pending_applicants_data,
        ) = await InterviewListAggregation().approval_pending_applicants_data(
            page_num, page_size
        )
        response = await utility_obj.pagination_in_aggregation(
            page_num,
            page_size,
            total_data,
            "/interview_list/approval_pending_applicants_data/",
        )
        return {
            "data": approval_pending_applicants_data,
            "total": total_data,
            "count": page_size,
            "pagination": response.get("pagination"),
            "message": "Get approval pending applicants data.",
        }

    async def reviewed_applicants_data(
        self, current_user: str, page_num: int, page_size: int
    ) -> dict:
        """
        Get reviewed applicants' data with pagination.

        Params:
            current_user (str): An user_name of current user.
                    e.g., test@gmail.com
            page_num (int): Useful for show reviewed applicants' data on a
                    particular page. e.g., 1
            page_size (int): Useful for show limited data on
                    particular page. e.g., 25

        Returns:
            dict: A dictionary which contains reviewed applicants' data.
        """
        (
            total_data,
            reviewed_applicants_data,
        ) = await InterviewListAggregation().reviewed_applicants_data(
            page_num, page_size
        )
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, total_data, "/interview_list/reviewed_applicants_data/"
        )
        return {
            "data": reviewed_applicants_data,
            "total": total_data,
            "count": page_size,
            "pagination": response.get("pagination"),
            "message": "Get reviewed applicants data.",
        }


interview_list_obj = InterviewList()
