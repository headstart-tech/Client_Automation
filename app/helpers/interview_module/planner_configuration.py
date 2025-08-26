"""
This file contains class and functions related to planner module.
"""

from datetime import datetime, timedelta

from bson import ObjectId
from fastapi import Request
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError
from pymongo.errors import PyMongoError

from app.background_task.send_mail_configuration import EmailActivity
from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.custom_error import DataNotFoundError
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.database.aggregation.admin_user import AdminUser
from app.database.aggregation.planner import PlannerAggregation
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import is_testing_env, get_collection_from_cache, store_collection_in_cache
from app.helpers.template.template_configuration import TemplateActivity
from app.helpers.user_curd.user_configuration import UserHelper

logger = get_logger(name=__name__)


class Planner:
    """
    Contains functions related to planner module.
    """

    async def common_data_update(
        self,
        data: dict,
        user: dict,
        current_datetime: datetime,
        last_modified_timeline: list,
    ) -> dict:
        """
        Update user info in the data.

        Params:
            data: A data where user info want to update.
            user (dict): A dictionary which contains user info.
            current_datetime (datetime): An current datetime.
            last_modified_time (list): A list which contains last modified user info.

         Returns:
             data (dict): A dictionary which contains updated data.
        """
        user_limit = data.get("user_limit")
        slot_type = data.get("slot_type", "").upper()
        if not user_limit:
            user_limit = 10 if slot_type == "GD" else 3
        data.update(
            {
                "slot_type": slot_type,
                "user_limit": user_limit,
                "created_by": user.get("_id"),
                "created_by_name": utility_obj.name_can(user),
                "created_at": current_datetime,
                "last_modified_timeline": last_modified_timeline,
            }
        )
        return data

    async def validate_panel_slot_create(
        self, time: datetime, end_time: datetime, panel_id: ObjectId
    ):
        """
        Validate panel slot start time and end time.

        Params:
            time (datetime): A start time of a slot.
            end_time (datetime): An end time of a slot.
            panel_id (ObjectId): A unique identifier/id of panel.

        Raises:
            422: Raise exception with status code 422 when not able to create
                slot.
        """
        result = DatabaseConfiguration().panel_collection.aggregate(
            [
                {"$match": {"panel_id": panel_id}},
                {"$sort": {"end_time": -1}},
                {"$limit": 1},
            ]
        )
        async for data in result:
            if data:
                panel_time = data.get("time")
                panel_end_time = data.get("end_time")
                if not (
                    (panel_time < time > panel_end_time)
                    or (panel_time < end_time > panel_end_time)
                ):
                    raise HTTPException(
                        status_code=422,
                        detail="Not able to create slot because overlapping "
                        "with existing panel slot time.",
                    )
                return panel_end_time

    async def common_create_update(self, current_user: str, data: dict) -> tuple:
        """
        Validate user, get current_datetime/last_modified_time and
        convert interview_list_id/panelist_ids from str to ObjectId depending
            on whether the
        interview_list_id/panelist_ids is provided.

        Params:
            current_user (str): An user_name of current user.
            data (dict): A dictionary which contains data for create/update.
            is_slot (bool): Useful for perform operation of slot.

        Returns:
              tuple: A tuple which contains user info, current datetime, last
                modified timeline and data.
        """
        user = await UserHelper().is_valid_user(current_user)
        current_datetime = datetime.utcnow()
        last_modified_timeline = await TemplateActivity().get_last_timeline(user)
        time = data.get("time")
        end_time = data.get("end_time")
        for field, key in [(time, "time"), (end_time, "end_time")]:
            if field:
                data[key] = await utility_obj.date_change_utc(field)
        interview_list_id = data.get("interview_list_id")
        if interview_list_id:
            await utility_obj.is_length_valid(
                _id=interview_list_id, name="Interview list id"
            )
            data["interview_list_id"] = ObjectId(interview_list_id)
        panelists = [
            ObjectId(_id)
            for _id in data.get("panelists", [])
            if await utility_obj.is_length_valid(_id=_id, name="Panelist " "id")
        ]
        if panelists:
            data["panelists"] = panelists
        return user, current_datetime, last_modified_timeline, data

    async def update_take_slot_info(
        self,
        slot_data: dict,
        user: dict,
        user_type: str,
        application_id: str | None,
        assign: bool = False,
        college_id=None,
    ) -> dict | None:
        """
         Update take slot info in the DB.

         Params:
             slot_data (dict): A dictionary which contains slot data.
             user (dict): A dictionary which contains user data.
             user_type (str): Type of user.
             application_id (str): An unique identifier/id of application.
                 e.g., 123456789012345678901214.
             assign (bool): A boolean value will be useful for don't raise
                 error.

         Returns:
            None: Not return anything.

        Raises:
            Exception: Raise exception with status code 500 when certain
            condition failed.
        """
        if slot_data.get("take_slot") is None:
            slot_data["take_slot"] = {}
        if slot_data.get("take_slot", {}).get(f"{user_type}_ids") is None:
            slot_data["take_slot"][f"{user_type}_ids"] = []
        user_id = ObjectId(user.get("_id"))
        if application_id:
            await utility_obj.is_length_valid(application_id, name="Application id")
            user_id = ObjectId(application_id)
        user_ids = slot_data["take_slot"][f"{user_type}_ids"]
        if user_id in user_ids:
            if assign:
                return {"detail": "Slot is already assigned."}
            raise HTTPException(status_code=422, detail="Slot is already taken.")
        user_ids.insert(0, user_id)
        if user_type == "panelist":
            if len(user_ids) > 2:
                return {"detail": "Maximum 2 panelists can be assign to a " "slot."}
        await DatabaseConfiguration().slot_collection.update_one(
            {"_id": slot_data.get("_id")},
            {
                "$set": {
                    f"take_slot.{user_type}": True,
                    "available_slot": slot_data.get("available_slot"),
                    "booked_user": slot_data.get("booked_user"),
                    f"take_slot.{user_type}_ids": user_ids,
                }
            },
        )
        if application_id:
            if (
                application := await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"_id": user_id}
                )
            ) is None:
                return None
            allocated_interview_lists = application.get("interview_list_id")
            interview_list_id = slot_data.get("interview_list_id")
            removed_lists = []
            if allocated_interview_lists:
                for interview_list in allocated_interview_lists:
                    if interview_list_id != interview_list:
                        allocated_interview_lists.remove(interview_list)
                        removed_lists.append(interview_list)
                await DatabaseConfiguration().interview_list_collection.update_many(
                    {
                        "_id": {"$in": removed_lists},
                        "application_ids": {"$eq": application_id},
                    },
                    {
                        "$pull": {
                            "application_ids": application_id,
                            "eligible_applications": application_id,
                        }
                    },
                )
            try:
                toml_data = utility_obj.read_current_toml_file()
                if toml_data.get("testing", {}).get("test") is False:
                    # TODO: Not able to add student timeline data
                    #  using celery task when environment is
                    #  demo. We'll remove the condition when
                    #  celery work fine.
                    if settings.environment in ["demo"]:
                        StudentActivity().student_timeline(
                            student_id=str(user.get("_id")),
                            event_type="Interview",
                            event_status="Booked",
                            message=f"{utility_obj.name_can(user.get('basic_details', {}))} has booked an Interview Slot with"
                            f" following details: Date - {slot_data.get('time').date()}"
                            f" Time - {utility_obj.get_local_time(slot_data.get('time'))}"
                            f" Venue - {slot_data.get('interview_mode')}",
                            college_id=college_id,
                        )
                    else:
                        if not is_testing_env():
                            StudentActivity().student_timeline.delay(
                                student_id=str(user.get("_id")),
                                event_type="Interview",
                                event_status="Booked",
                                message=f"{utility_obj.name_can(user.get('basic_details', {}))} has booked an Interview Slot with"
                                f" following details: Date - {slot_data.get('time').date()}"
                                f" Time - {utility_obj.get_local_time(slot_data.get('time'))}"
                                f" Venue - {slot_data.get('interview_mode')}",
                                college_id=college_id,
                            )
            except KombuError as celery_error:
                logger.error(f"error storing login by otp data " f"{celery_error}")
            except Exception as error:
                logger.error(f"error storing otp data {error}")

    async def get_user_data_with_type(
        self, is_student: bool, current_user: str
    ) -> tuple:
        """
        Get user data along with type.

        Params:
            is_student (bool): Optional field. By default, value will be false.
                It will be True if student try to take slot.
            current_user: An unique user_name/email of user.
                For example, apollo@example.com

        Returns:
           tuple: A tuple which contains user data along with type.

        """
        if is_student:
            if (
                user := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"user_name": current_user}
                )
            ) is None:
                raise HTTPException(status_code=404, detail="Student not found.")
            user_type = "application"
        else:
            user = await UserHelper().is_valid_user(user_name=current_user)
            if user.get("role", {}).get("role_name") != "panelist":
                raise HTTPException(
                    status_code=401, detail="Only panelist can take a slot."
                )
            user_type = "panelist"
        return user, user_type

    async def get_slot_data(self, slot_id):
        """
        Helper function to fetch the slot data from the database based on id.

        Params:
            slot_id (str): An unique slot id for update slot data.

        Returns:
            dict: A dictionary which contains slot data.
        """
        await utility_obj.is_id_length_valid(_id=slot_id, name="Slot id")
        if (
            slot_data := await DatabaseConfiguration().slot_collection.find_one(
                {"_id": ObjectId(slot_id)}
            )
        ) is None:
            raise HTTPException(
                status_code=404,
                detail="Slot not found. Make sure provided slot id "
                "should be correct.",
            )
        return slot_data

    async def get_panel_data(self, panel_id):
        """
        Helper function to fetch the panel data from the database based on id.

        Params:
            panel_id (str): An unique panel id for update panel data.

        Returns:
            dict: A dictionary which contains panel data.
        """
        await utility_obj.is_id_length_valid(_id=panel_id, name="Panel id")
        if (
            panel_data := await DatabaseConfiguration().panel_collection.find_one(
                {"_id": ObjectId(panel_id)}
            )
        ) is None:
            raise HTTPException(
                status_code=404,
                detail="Panel not found. Make sure provided panel id should be correct.",
            )
        return panel_data

    async def update_panel_data(
        self, panel_id: str, panel_data: dict, last_modified_timeline: list
    ) -> dict:
        """
        Update panel data based on id.

        Params:
            panel_id (str): An unique panel id for update panel data.
            panel_data (dict): A data which useful for update panel.
            last_modified_timeline (list): A list which contains last modified timeline data such user_id,
                                           user_name and datetime.

        Returns:
            dict: A dictionary which contains update panel data info.
        """
        panel = await self.get_panel_data(panel_id)
        name = panel_data.get("name")
        if name and name != panel.get("name"):
            if (
                await DatabaseConfiguration().panel_collection.find_one(
                    {"name": panel_data.get("name")}
                )
                is not None
            ):
                return {"detail": "Panel name already exists."}
        panel.get("last_modified_timeline", []).insert(0, last_modified_timeline[0])
        panel_data.update(
            {"last_modified_timeline": panel.get("last_modified_timeline")}
        )
        await DatabaseConfiguration().panel_collection.update_one(
            {"_id": ObjectId(panel_id)}, {"$set": panel_data}
        )
        return {"message": "Panel data updated."}

    async def update_slot_data(
        self, slot_id: str, slot_data: dict, last_modified_timeline: list
    ) -> dict:
        """
        Update slot data based on id.

        Params:
            slot_id (str): An unique slot id for update slot data.
            slot_data (dict): A data which useful for update slot.
            last_modified_timeline (list): A list which contains last modified timeline data such user_id,
                                           user_name and datetime.

        Returns:
            dict: A dictionary which contains update slot data info.
        """
        slot = await self.get_slot_data(slot_id)
        slot.get("last_modified_timeline", []).insert(0, last_modified_timeline[0])
        slot_data.update({"last_modified_timeline": slot.get("last_modified_timeline")})
        await DatabaseConfiguration().slot_collection.update_one(
            {"_id": ObjectId(slot_id)}, {"$set": slot_data}
        )
        return {"message": "Slot data updated."}

    async def create_panel_slots(self, panel_data: dict, panel_id: ObjectId) -> None:
        """
        Create slots of panels in the DB.

        Params:
            panel_data (dict): A dictionary which contains panel data.
            panel_id (ObjectId): An unique identifier/id of panel.

        Returns:
            None: Not returning anything.
        """
        start_time = panel_data.get("time")
        slot_duration = panel_data.get("slot_duration")
        end_time = start_time + timedelta(minutes=slot_duration)
        count = 1
        insert_slot_data = {
            "panel_id": panel_id,
            "slot_type": panel_data.get("slot_type"),
            "interview_mode": panel_data.get("panel_type"),
            "panelists": panel_data.get("panelists"),
            "interview_list_id": panel_data.get("interview_list_id"),
            "slot_duration": slot_duration,
            "status": panel_data.get("status"),
            "created_by": panel_data.get("created_by"),
            "created_by_name": panel_data.get("created_by_name"),
            "created_at": panel_data.get("created_at"),
            "last_modified_timeline": panel_data.get("last_modified_timeline"),
            "available_slot": "Open",
            "booked_user": 0,
            "take_slot": {},
            "user_limit": panel_data.get("user_limit"),
        }
        while count <= panel_data.get("slot_count"):
            if insert_slot_data.get("_id"):
                insert_slot_data.pop("_id")
            insert_slot_data.update({"time": start_time, "end_time": end_time})
            await DatabaseConfiguration().slot_collection.insert_one(insert_slot_data)
            count += 1
            start_time = end_time + timedelta(
                minutes=panel_data.get("gap_between_slots")
            )
            end_time = start_time + timedelta(minutes=slot_duration)

    async def validate_create_possible_slots(self, panel_data: dict):
        """
        Validate create panel data.

        Params:
            panel_data (dict): A dictionary which contains panel data.

        Returns:
            tuple: A tuple which contains total_slot_duration,
                total_gap_between_slots and slot_gap_duration.
        """
        panel_duration = panel_data.get("panel_duration")
        slot_count = panel_data.get("slot_count")
        total_gap_between_slots = (slot_count - 1) * panel_data.get("gap_between_slots")
        total_slot_duration = slot_count * panel_data.get("slot_duration")
        slot_gap_duration = total_slot_duration + total_gap_between_slots
        panel_time_duration = (
            panel_data.get("end_time") - panel_data.get("time")
        ).total_seconds() // 60
        total_diff = panel_duration - slot_gap_duration
        if total_diff < 0:
            raise HTTPException(
                status_code=422, detail="Not able to create " "possible slot count."
            )
        if panel_duration != panel_time_duration:
            raise HTTPException(
                status_code=422,
                detail="Panel duration is not match with "
                "panel start time and end time.",
            )
        return total_slot_duration, total_gap_between_slots, slot_gap_duration

    async def add_panel_data(
        self,
        panel_data: dict,
        current_datetime: datetime,
        last_modified_timeline: list,
        user: dict,
    ) -> dict:
        """
        Add panel data.

        Params:
            panel_data (dict): A data which useful for create panel.
            current_datetime (datetime): current date and time in utc format.
            last_modified_timeline (list): A list which contains last modified timeline data such user_id,
                user_name and datetime.
            user (dict): A dictionary which contains user data.

        Returns:
            dict: A dictionary which contains add panel info.
        """
        for field in [
            "slot_type",
            "panel_type",
            "interview_list_id",
            "panelists",
            "time",
            "end_time",
            "gap_between_slots",
            "slot_duration",
            "slot_count",
            "panel_duration",
        ]:
            if panel_data.get(field) in ["", None]:
                raise HTTPException(
                    status_code=422, detail=f"{field} must be required and " f"valid."
                )
        panel_duration = int(panel_data.get("panel_duration"))
        panel_data.update(
            {
                "slot_duration": int(panel_data.get("slot_duration")),
                "slot_count": int(panel_data.get("slot_count")),
                "gap_between_slots": int(panel_data.get("gap_between_slots")),
                "panel_duration": panel_duration,
            }
        )
        total_slot_duration, total_gap_between_slots, slot_gap_duration = (
            await self.validate_create_possible_slots(panel_data)
        )
        panel_data.update(
            {
                "total_slot_duration": total_slot_duration,
                "total_gap_between_slots": total_gap_between_slots,
                "slot_gap_duration": slot_gap_duration,
            }
        )
        panel_data = await self.common_data_update(
            panel_data, user, current_datetime, last_modified_timeline
        )
        panel_data.update(
            {
                "total_slot_duration": total_slot_duration,
                "total_gap_between_slots": total_gap_between_slots,
                "slot_gap_duration": slot_gap_duration,
                "available_time": panel_duration - slot_gap_duration,
            }
        )
        panel = await DatabaseConfiguration().panel_collection.insert_one(panel_data)
        panel_id = panel.inserted_id
        await self.create_panel_slots(panel_data, panel_id)
        return {
            "message": "Panel data added.",
            "panel_id": str(panel_id),
            "slot_type": panel_data.get("slot_type"),
            "date": utility_obj.get_local_time(
                panel_data.get("time", current_datetime)
            ),
        }

    async def update_slot_duration(self, slot_data: dict):
        """
        Update slot duration in the slot data based on start and time of slot.

        Params:
            slot_data (dict): A dictionary which contains slot data.

        Returns:
            slot_data (dict): A dictionary which can contains slot data
            along with duration.
        """
        end_time = slot_data.get("end_time")
        time = slot_data.get("time")
        if time and end_time:
            slot_duration = (end_time - time).total_seconds() // 60
            slot_data["slot_duration"] = slot_duration
        return slot_data

    async def validate_create_panel_slot(self, panel_data: dict, slot_data: dict):
        """
        Validate create panel slot.

        Params:
            panel_data (dict): A dictionary which contains panel data.

        Returns:
            tuple: A tuple which contains total_slot_duration,
                total_gap_between_slots and slot_gap_duration.
        """
        available_time = panel_data.get("available_time")
        gap_between_slots = panel_data.get("gap_between_slots")
        slot_duration = slot_data["slot_duration"]
        create_slot_gap_duration = gap_between_slots + slot_duration
        if available_time < create_slot_gap_duration:
            raise HTTPException(
                status_code=422,
                detail="Not able to create slot of panel "
                "because of insufficient panel "
                "available time.",
            )
        panel_slot_end_time = await self.validate_panel_slot_create(
            slot_data["time"], slot_data["end_time"], slot_data["panel_id"]
        )
        if panel_slot_end_time:
            slot_data["time"] = panel_slot_end_time + timedelta(
                minutes=gap_between_slots
            )
            slot_data["end_time"] = slot_data["time"] + timedelta(minutes=slot_duration)
        total_slot_duration = panel_data.get("total_slot_duration") + slot_duration
        slot_count = panel_data.get("slot_count") + 1
        total_gap_between_slots = (slot_count - 1) * panel_data.get("gap_between_slots")
        slot_gap_duration = total_slot_duration + total_gap_between_slots
        await DatabaseConfiguration().panel_collection.update_one(
            {"_id": panel_data.get("_id")},
            {
                "$set": {
                    "slot_count": slot_count,
                    "total_slot_duration": total_slot_duration,
                    "total_gap_between_slots": total_gap_between_slots,
                    "slot_gap_duration": slot_gap_duration,
                }
            },
        )
        return total_slot_duration, total_gap_between_slots, slot_gap_duration

    async def add_slot_data(
        self,
        slot_data: dict,
        current_datetime: datetime,
        last_modified_timeline: list,
        user: dict,
    ) -> dict:
        """
        Add slot data.

        Params:
            slot_data (dict): A data which useful for create slot.
            current_datetime (datetime): current date and time in utc format.
            last_modified_timeline (list): A list which contains last modified timeline data such user_id,
                user_name and datetime.
            user (dict): A dictionary which contains user data.

        Returns:
            dict: A dictionary which contains add slot info.
        """

        slot_data = await self.common_data_update(
            slot_data, user, current_datetime, last_modified_timeline
        )
        for field in ["slot_type", "interview_mode", "panelists", "time", "end_time"]:
            if slot_data.get(field) in ["", None]:
                raise HTTPException(
                    status_code=422, detail=f"{field} must be required and " f"valid."
                )
        panel_id = slot_data.get("panel_id")
        if panel_id not in [None, ""]:
            panel_data = await self.get_panel_data(panel_id)
            slot_data["panel_id"] = ObjectId(panel_id)
            await self.validate_create_panel_slot(panel_data, slot_data)
        await DatabaseConfiguration().slot_collection.insert_one(slot_data)
        return {"message": "Slot data added."}

    async def create_or_update_panel(
        self, current_user: str, panel_data: dict, panel_id: str | None
    ) -> dict:
        """
        Either create a new panel or update existing panel depending on whether the panel_id is provided.

        Params:
            current_user (str): An user_name of current user.
            panel_data (dict): A data which useful for create/update panel.
            panel_id (str): An unique panel id for update panel data.

        Returns:
            dict: A dictionary which contains create/update panel data.
        """
        user, current_datetime, last_modified_timeline, panel_data = (
            await self.common_create_update(current_user, panel_data)
        )
        if panel_id:
            return await self.update_panel_data(
                panel_id, panel_data, last_modified_timeline
            )
        return await self.add_panel_data(
            panel_data, current_datetime, last_modified_timeline, user
        )

    async def create_or_update_slot(
        self, current_user: str, slot_data: dict, slot_id: str | None
    ) -> dict:
        """
        Either create a new slot or update existing slot depending on whether the slot_id is provided.

        Params:
            current_user (str): An user_name of current user.
            slot_data (dict): A data which useful for create/update slot.
            slot_id (str): An unique slot id for update slot data.

        Returns:
            dict: A dictionary which contains create/update slot data.
        """
        user, current_datetime, last_modified_timeline, panel_data = (
            await self.common_create_update(current_user, slot_data)
        )
        slot_data = await self.update_slot_duration(slot_data)
        if slot_id:
            return await self.update_slot_data(
                slot_id, slot_data, last_modified_timeline
            )
        return await self.add_slot_data(
            slot_data, current_datetime, last_modified_timeline, user
        )

    def format_slot_data(self, slot: dict) -> dict:
        """
        Get formatted slot data.

        Params:
            slot (dict): A dictionary contains slot data.

        Returns:
            dict: A dictionary which contains formatted slot data.
        """
        if not all(key in slot for key in ["_id", "interview_list_id"]):
            raise ValueError("Missing required slot keys")

        return {
            "id": str(slot["_id"]),
            "slot_type": slot.get("slot_type"),
            "user_limit": slot.get("user_limit"),
            "panel_id": str(slot.get("panel_id")),
            "interview_mode": slot.get("interview_mode"),
            "panelists": [str(_id) for _id in slot.get("panelists", [])],
            "interview_list_id": str(slot.get("interview_list_id")),
            "state": slot.get("state"),
            "city": slot.get("city"),
            "status": slot.get("status"),
            "time": utility_obj.get_local_time(slot.get("time")),
            "end_time": utility_obj.get_local_time(slot.get("end_time")),
            "slot_duration": slot.get("duration"),
            "created_by": slot.get("created_by"),
            "created_by_name": slot.get("created_by_name"),
            "created_at": utility_obj.get_local_time(slot.get("created_at")),
            "last_modified_timeline": [
                {
                    "last_modified_at": utility_obj.get_local_time(
                        timeline.get("last_modified_at")
                    ),
                    "user_id": str(timeline.get("user_id")),
                    "user_name": timeline.get("user_name"),
                }
                for timeline in slot.get("last_modified_timeline", [])
            ],
        }

    async def get_slot_details_by_id(self, current_user: str, slot_id: str) -> dict:
        """
        Get slot details based on id.

        Params:
        current_user (str): An user_name of user.Useful for validate login user.
            For example, test@gmail.com
        slot_id (str): A unique identifier/id of slot.
            For example, 123456789012345678901234

        Returns:
            dict: A dictionary which contains slot data.
        """
        await UserHelper().is_valid_user(user_name=current_user)
        slot_data = await self.get_slot_data(slot_id)
        return self.format_slot_data(slot_data)

    def format_panel_data(self, panel_data: dict) -> dict:
        """
        Get formatted panel data.

        Params:
            panel_data (dict): A dictionary contains panel data.

        Returns:
                dict: A dictionary which contains formatted panel data.
        """
        if not all(key in panel_data for key in ["_id", "interview_list_id"]):
            raise ValueError("Missing required slot keys")
        panel_duration = int(panel_data.get("panel_duration"))
        slot_gap_duration = panel_data.get("slot_gap_duration")
        return {
            "id": str(panel_data.get("_id")),
            "name": panel_data.get("name"),
            "description": panel_data.get("description"),
            "slot_type": panel_data.get("slot_type"),
            "panel_type": panel_data.get("panel_type"),
            "user_limit": panel_data.get("user_limit"),
            "interview_list_id": str(panel_data.get("interview_list_id")),
            "panelists": [str(_id) for _id in panel_data.get("panelists", [])],
            "panel_duration": panel_duration,
            "gap_between_slots": panel_data.get("gap_between_slots"),
            "slot_count": panel_data.get("slot_count"),
            "slot_duration": panel_data.get("slot_duration"),
            "total_slot_duration": panel_data.get("total_slot_duration"),
            "available_time": panel_duration - slot_gap_duration,
            "total_gap_between_slots": panel_data.get("total_gap_between_slots"),
            "slot_gap_duration": slot_gap_duration,
            "status": panel_data.get("status"),
            "time": utility_obj.get_local_time(panel_data.get("time")),
            "end_time": utility_obj.get_local_time(panel_data.get("end_time")),
            "created_by": panel_data.get("created_by"),
            "created_by_name": panel_data.get("created_by_name"),
            "created_at": utility_obj.get_local_time(panel_data.get("created_at")),
            "last_modified_timeline": [
                {
                    "last_modified_at": utility_obj.get_local_time(
                        timeline.get("last_modified_at")
                    ),
                    "user_id": str(timeline.get("user_id")),
                    "user_name": timeline.get("user_name"),
                }
                for timeline in panel_data.get("last_modified_timeline", [])
            ],
        }

    async def get_panel_details_by_id(self, current_user: str, panel_id: str) -> dict:
        """
        Get panel details based on id.

        Params:
        current_user (str): An user_name of user.Useful for validate login user.
            For example, test@gmail.com
        panel_id (str): A unique identifier/id of panel.
            For example, 123456789012345678901234

        Returns:
            dict: A dictionary which contains panel data.
        """
        await UserHelper().is_valid_user(user_name=current_user)
        panel_data = await self.get_panel_data(panel_id)
        return self.format_panel_data(panel_data)

    async def extend_pipeline_based_on_condition(
        self, pipeline: list, moderator: list | None, program_name: None | list
    ) -> list:
        """
        updates pipeline if moderator and program_name filter is added , else returns the same
        """
        if moderator or program_name:
            lookup_stage_match = {"$expr": {"$eq": ["$_id", "$$interview_id"]}}
            if moderator:
                moderator_ids = [ObjectId(m_id) for m_id in moderator]
                lookup_stage_match.update({"moderator_id": {"$in": moderator_ids}})
            if program_name:
                lookup_stage_match.update({"$or": program_name})
            pipeline.extend(
                [
                    {
                        "$lookup": {
                            "from": "interviewLists",
                            "let": {"interview_id": "$interview_list_id"},
                            "pipeline": [{"$match": lookup_stage_match}],
                            "as": "interview_details",
                        }
                    },
                    {"$unwind": {"path": "$interview_details"}},
                ]
            )
        return pipeline

    async def get_pi_gd_details_per_day(
        self,
        date,
        month,
        year,
        filter_slot,
        slot_status,
        moderator,
        program_name,
        slot_state,
    ):
        """
        get pi gd details per day
        this also include filters
        depending on the filter given the result changes

        Params:\n
            date (int): particular date
            month (int): given month
            year (int): given year
            filter_slot(list) : to filter the slot (PI/GD/slot/panel)
            slot_status (list) :this may have two values(available/booked)
            moderator (list) : Depending on the given moderator the result should be filtered
            program_name (list) : Depending on the given program name the result should be filtered
            slot_state (str) : this may have two values(published/not_published)

        Returns:
            res (dict): A dictionary which contains details of day wise information of
                        pi/gd data
        """
        res = {"date": datetime(year, month, date).date()}
        pipeline = [
            {
                "$match": {
                    "$expr": {
                        "$and": [
                            {"$eq": [{"$month": "$time"}, month]},
                            {"$eq": [{"$year": "$time"}, year]},
                        ]
                    }
                }
            }
        ]
        pipeline = await self.extend_pipeline_based_on_condition(
            pipeline, moderator, program_name
        )
        pipeline_2 = pipeline.copy()
        pipeline_2.extend([{"$match": {"panel_id": {"$exists": True, "$ne": ""}}}])
        for item in ["PI", "GD"]:
            try:
                matched_documents_slots = (
                    DatabaseConfiguration().slot_collection.aggregate(pipeline)
                )
                matched_documents_panels = (
                    DatabaseConfiguration().slot_collection.aggregate(pipeline_2)
                )
            except PyMongoError as error:
                logger.error(
                    f"An error occurred while trying " f"to execute the query: {error}"
                )
            filtered_documents_slots = [
                doc
                async for doc in matched_documents_slots
                if doc["slot_type"] == item and doc["time"].day == date
            ]
            filtered_documents_panels = [
                doc
                async for doc in matched_documents_panels
                if doc["slot_type"] == item and doc["time"].day == date
            ]
            total_documents_slots = len(
                list(filter(lambda d: d["status"] != "draft", filtered_documents_slots))
            )
            total_documents_panels = len(
                list(
                    filter(lambda d: d["status"] != "draft", filtered_documents_panels)
                )
            )
            total_documents = total_documents_slots
            if slot_state != "published":
                total_documents = len(filtered_documents_slots)
            total_published_documents_slots = len(
                [
                    doc
                    for doc in filtered_documents_slots
                    if doc["status"] == "published"
                ]
            )
            total_booked_documents_slots = len(
                [doc for doc in filtered_documents_slots if doc["status"] == "booked"]
            )
            total_published_documents_panels = len(
                [
                    doc
                    for doc in filtered_documents_panels
                    if doc["status"] == "published"
                ]
            )
            total_booked_documents_panels = len(
                [doc for doc in filtered_documents_panels if doc["status"] == "booked"]
            )
            total_published_documents = total_published_documents_slots
            total_booked_documents = total_booked_documents_slots
            common_data = {}

            if filter_slot:
                filter_slot = [element.lower() for element in filter_slot]
                if "panel" in filter_slot and "slot" in filter_slot:
                    common_data.update(
                        {
                            "Total": total_documents,
                            "available": total_published_documents
                            + total_published_documents_panels,
                            "booked": total_booked_documents
                            + total_booked_documents_panels,
                        }
                    )
                for filter_item in filter_slot:
                    if filter_item == "panel" and "slot" not in filter_slot:
                        common_data.update(
                            {
                                "Total": total_documents_panels,
                                "available": total_published_documents_panels,
                                "booked": total_booked_documents_panels,
                            }
                        )
                    elif filter_item == "slot" and "panel" not in filter_slot:
                        common_data.update(
                            {
                                "Total": total_documents_slots,
                                "available": total_published_documents_slots,
                                "booked": total_booked_documents_slots,
                            }
                        )
                    elif filter_item == item.lower():
                        common_data.update(
                            {
                                "Total": total_documents,
                                "available": total_published_documents,
                                "booked": total_booked_documents,
                            }
                        )
                    if slot_status is not None:
                        if len(slot_status) == 1:
                            if slot_status[0].lower() == "available":
                                common_data.pop("booked", None)
                            elif slot_status[0].lower() == "booked":
                                common_data.pop("available", None)
                    if ("panel" in filter_slot or "slot" in filter_slot) and (
                        "pi" not in filter_slot and "gd" not in filter_slot
                    ):
                        res.update(
                            {
                                f"{item.lower().capitalize()}{key}": value
                                for key, value in common_data.items()
                            }
                        )
                    if filter_item is None or filter_item == item.lower():
                        res.update(
                            {
                                f"{item.lower().capitalize()}{key}": value
                                for key, value in common_data.items()
                            }
                        )
            else:
                common_data.update(
                    {
                        "Total": total_documents,
                        "available": total_published_documents,
                        "booked": total_booked_documents,
                    }
                )
                res.update(
                    {
                        f"{item.lower().capitalize()}{key}": value
                        for key, value in common_data.items()
                    }
                )
        return res

    async def day_wise_slots_and_panels_data(
        self, current_user: str, date: str, slot_panel_filters: dict | None
    ):
        """
        Check user has permission for get slots and panels data or not
        then get day wise slots and panels data along with next day by perform
        aggregation.
        By default, current date and next date slots/panels data can get.

        Params:
            current_user: An unique user_name/email of user.
                For example, apollo@example.com
            date (str): Optional field. Useful for get particular date slots
                and panels data.
                For example, 2023-12-31.
            slot_panel_filters (dict | None): Either value will be None or
                list of filters which helpful for get slots/panels data.

        Returns:
           list: A list which contains info about day wise slots and
           panels data.
        """
        user = await UserHelper().is_valid_user(user_name=current_user)
        return await PlannerAggregation().get_day_wise_slots_and_panels_data(
            date, user, slot_panel_filters
        )

    async def assign_take_slot(
        self,
        slot_data: dict,
        user: dict,
        user_type: str,
        application_id: str | None,
        is_student: bool,
        college: dict,
        request: Request,
        current_user: str,
        assign: bool = False,
        action_type="system",
    ):
        """
         Update take slot info and send mail to user.

         Params:
             slot_dict (dict): A dictionary which contains slot data.
             user (dict): A dictionary which contains user data.
             user_type (str): type of user helpful for update slot.
             application_id (str): An unique identifier of application.
                 For example, 123456789012345678901214.
             background_tasks (BackgroundTasks): Useful for perform
                 background tasks.
             is_student (bool): A boolean value will be useful when sending
                 mail.
             college (dict): A dictionary which contains college data.
                 e.g., 123456789012345678901234.
             request (Request): An object of class `Request`,
                 useful for get user info.
             current_user: An unique user_name/email of user.
                 For example, apollo@example.com
             assign (bool): A boolean value will be useful for don't raise
                 error.

         Returns:
            None: Not returning anything

        Raises:
            Exception: Raise exception with status code 500 when certain
            condition failed.
        """
        if user_type == "application":
            booked_user = slot_data.get("booked_user", 0)
            if not booked_user:
                slot_data["booked_user"] = 0
                booked_user = 0
            user_limit = slot_data.get("user_limit")

            if booked_user == user_limit:
                await DatabaseConfiguration().slot_collection.update_one(
                    {"_id": slot_data.get("_id")},
                    {"$set": {f"available_slot": "Closed"}},
                )
                if assign:
                    return {
                        "detail": "Slot is fully occupied. " "Not able to take slot."
                    }
                raise HTTPException(
                    status_code=422,
                    detail="Slot is fully occupied. " "Not able to take a slot.",
                )
            elif booked_user < user_limit:
                slot_data["booked_user"] = slot_data["booked_user"] + 1
                slot_data["available_slot"] = "Open"
        update_slot_info = await self.update_take_slot_info(
            slot_data,
            user,
            user_type,
            application_id,
            assign,
            college_id=college.get("id"),
        )
        if update_slot_info:
            return update_slot_info
        toml_data = utility_obj.read_current_toml_file()
        if toml_data.get("testing", {}).get("test") is False:
            if slot_data.get("status") == "published":
                await EmailActivity().create_zoom_meet_and_send_mail(
                    is_student,
                    [application_id],
                    slot_data,
                    college,
                    user,
                    request,
                    current_user,
                    action_type=action_type,
                    college_id=college.get("id"),
                )

    async def take_a_slot(
        self,
        current_user: str,
        slot_id: str,
        is_student: bool,
        application_id: str | None,
        college: dict,
        request: Request,
    ) -> dict:
        """
         Panelist/Student can accept/take the slot.

         Params:
             current_user: An unique user_name/email of user.
                 For example, apollo@example.com
             slot_id (str): An unique identifier of slot.
                 For example, 123456789012345678901212.
             is_student (bool): Optional field. By default, value will be false.
                 It will be True if student try to take slot.
             application_id (str): An unique identifier of application.
                 For example, 123456789012345678901214.
                 Send application id when student try to take slot.
             - background_tasks (BackgroundTasks): Useful for perform
                 background tasks.
             - request (Request): An object of class `Request`,
                 useful for get user info.
             - college (dict): A dictionary which contains college data.
                 e.g., 123456789012345678901234.

         Returns:
            dict: A dictionary which contains info about take slot.

        Raises:
            Exception: Raise exception with status code 500 when certain
            condition failed.
        """
        slot_data = await self.get_slot_data(slot_id)
        if is_student and application_id is None:
            raise HTTPException(
                status_code=422, detail="Application id must be required and " "valid."
            )
        user, user_type = await self.get_user_data_with_type(is_student, current_user)
        await self.assign_take_slot(
            slot_data,
            user,
            user_type,
            application_id,
            is_student,
            college,
            request,
            current_user,
            action_type="system" if user_type == "panelist" else "user",
        )
        return {"message": "Slot is booked successfully."}

    async def are_all_slots_published(
        self,
        slot_id: ObjectId | None,
        request: Request,
        college: dict,
        current_user: str,
        action_type="system",
    ) -> bool | ObjectId:
        """
        Check all panel slots are published or not.

        Params:
            slot_id (ObjectId | None): Either None or a unique identifier/id
                of slot. e.g., 123456789012345678901234

        Returns:
             bool | ObjectId: If all panel slots are published then return
             panel_id else False.
        """
        if (
            slot := await DatabaseConfiguration().slot_collection.find_one(
                {"_id": slot_id}
            )
        ) is not None:
            slots = (
                await DatabaseConfiguration()
                .slot_collection.aggregate([{"$match": {"panel_id": slot.get("panel_id")}}])
                .to_list(length=None)
            )
            take_slot = slot.get("take_slot", {})
            if slot.get("status", "") == "published" and take_slot:
                if take_slot.get("application"):
                    application_id = take_slot.get("application_ids", [])[0]
                    application = (
                        await DatabaseConfiguration().studentApplicationForms.find_one(
                            {"_id": application_id}
                        )
                    )
                    if application:
                        user = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                            {"_id": application.get("student_id")}
                        )
                        if user:
                            await EmailActivity().create_zoom_meet_and_send_mail(
                                True,
                                take_slot.get("application_ids", []),
                                slot,
                                college,
                                user,
                                request,
                                current_user,
                                action_type=action_type,
                                college_id=college.get("id")
                            )
            if slots:
                for slot_doc in slots:
                    if slot_doc.get("status", "") != "published":
                        return False
                return slot.get("panel_id")
        return False

    async def update_panel_status(
        self,
        slot_id: ObjectId,
        request: Request,
        college: dict,
        current_user: str,
        action_type="system",
    ) -> None:
        """
        Update panel status to published if all slots are published.

        Params:
            - slot_id (ObjectId | None): Either None or a unique identifier/id
                of slot. e.g., 123456789012345678901234
            - request (Request): Useful for get ip_address of client.
            - background_tasks (BackgroundTasks): Useful for perform
                background tasks.
            - college (dict): A dictionary which contains college data.
            - current_user (str): An user_name of current user.

        Returns:
            None: Not returning anything.
        """
        panel_id = await self.are_all_slots_published(
            slot_id, request, college, current_user, action_type=action_type
        )
        if panel_id:
            await DatabaseConfiguration().panel_collection.update_one(
                {"_id": panel_id}, {"$set": {"status": "published"}}
            )

    async def change_slots_or_panels_status(
        self,
        slots_panels_ids: list[str],
        date: None | str,
        request: Request,
        college: dict,
        current_user: str,
        status="published",
        action_type="system",
    ):
        """
        Change status of slots or panels based on ids.

        Params:\n
            - slots_panels_ids (list[str]): A list which contains
                slots/panels ids in a string format.
                e.g., {"slot_ids": ["123456789012345678901212"],
                        "panel_ids": [], "date": None}
            - date (None | str): Either None or a date (format: YYYY-MM-DD)
                which useful for publish particular date slots or panels.
            - request (Request): Useful for get ip_address of client.
            - background_tasks (BackgroundTasks): Useful for perform
                background tasks.
            - college (dict): A dictionary which contains college data.
            - current_user (str): An user_name of current user.

        Returns:
            None: Not returning anything.
        """
        publishable_ids = []
        if slots_panels_ids:
            publishable_ids = [
                ObjectId(_id)
                for _id in slots_panels_ids
                if await utility_obj.is_id_length_valid(_id, name=f"Id `{_id}`")
            ]
        if date:
            current_date = datetime.strptime(date, "%Y-%m-%d")
            next_date = current_date + timedelta(days=1)
            pipeline = [
                {"$match": {"time": {"$gte": current_date, "$lt": next_date}}},
                {"$group": {"_id": "", "data": {"$push": "$_id"}}},
            ]
            async for document in DatabaseConfiguration().slot_collection.aggregate(
                pipeline
            ):
                publishable_ids.extend(document.get("data"))
            async for document in DatabaseConfiguration().panel_collection.aggregate(
                pipeline
            ):
                publishable_ids.extend(document.get("data"))
        filter_dict = {"_id": {"$in": publishable_ids}}
        status_update_dict = {"$set": {"status": status}}
        await DatabaseConfiguration().slot_collection.update_many(
            filter_dict, status_update_dict
        )
        await DatabaseConfiguration().panel_collection.update_many(
            filter_dict, status_update_dict
        )
        await DatabaseConfiguration().slot_collection.update_many(
            {"panel_id": {"$in": publishable_ids}}, status_update_dict
        )

        for slot_id in publishable_ids:
            await self.update_panel_status(
                slot_id, request, college, current_user, action_type=action_type
            )

    async def publish_slots_or_panels(
        self,
        current_user: str,
        payload: dict,
        date: str | None,
        request: Request,
        college: dict,
    ) -> dict:
        """
        Publish slots or panels based on ids. Able to publish specified date
            slots and panels if date specified/provided.

        Params:
            - current_user (str): An user_name of current user.
                e.g., test@gmail.com
            - payload (dict): A dictionary which contains publish
                slots/panels ids.
                e.g., {"slots_panels_ids": ["123456789012345678901212"]}
            - date (str | None): Date format: YYYY-MM-DD.
                Useful for publish slots or panels of a specified date.
            - request (Request): Useful for get ip_address of client.
            - background_tasks (BackgroundTasks): Useful for perform
                background tasks.
            - college (dict): A dictionary which contains college data.

        Returns:
            dict: A dictionary contains info about publish slots or panels.
        """
        user = await UserHelper().is_valid_user(current_user)
        action_type = (
            "counselor"
            if user.get("role", {}).get("role_name") == "college_counselor"
            else "system"
        )
        slots_panels_ids = payload.get("slots_panels_ids", [])
        await self.change_slots_or_panels_status(
            slots_panels_ids,
            date,
            request,
            college,
            current_user,
            action_type=action_type,
        )
        return {"message": "Published slots/panels."}

    async def get_marking_parameters_with_weightage(self, parameters_info: dict):
        """
        Get marking paramters along with weightage based on interview type.

        Params:
            parameters_info (dict): A dictionary which contains paramters information along with weightage.

        Returns:
            list: A list which contains marking paramters with weightage.
        """

        return [
            {"name": name, "weight": weight} for name, weight in parameters_info.items()
        ]

    async def marking_details(self, interview_list_id, slot_type: str | None):
        """
        Marking details of given program_name
        Params:\n
            interview_list_id (str): unique id of interview list
            slot_type (str): this can be pi/gd(it can also be none)
        Returns:
            result (tuple) : that contains marking scheme(details),
            course_name and specialization name.
        """
        marking_scheme = [
            {"name": "communication_skills", "weight": 20},
            {"name": "domain_knowledge", "weight": 20},
            {"name": "behavioural_traits", "weight": 20},
            {"name": "etiquette", "weight": 20},
            {"name": "attitude", "weight": 20},
        ]
        if (
            interview_list := await DatabaseConfiguration().interview_list_collection.find_one(
                {"_id": ObjectId(interview_list_id)}
            )
        ) is None:
            return marking_scheme, None, None
        course_name, specialization_name = (interview_list.get("course_name"),
                                  interview_list.get("specialization_name"))
        if (selection_procedure := interview_list.get("selection_procedure")) is None:
            return marking_scheme, course_name, specialization_name
        slot_type = slot_type.lower()
        gd_weightage = selection_procedure.get("gd_parameters_weightage")
        pi_weightage = selection_procedure.get("pi_parameters_weightage")
        if (gd_weightage and slot_type == "gd") or (pi_weightage and slot_type == "pi"):
            if slot_type == "pi":
                marking_scheme = await self.get_marking_parameters_with_weightage(
                    pi_weightage
                )
            elif slot_type == "gd":
                marking_scheme = await self.get_marking_parameters_with_weightage(
                    gd_weightage
                )
        return marking_scheme, course_name, specialization_name

    async def marking_details_both_gd_pi(self, interview_list_id: str):
        """
        Marking details of given program_name
        Params:\n
            interview_list_id (str): unique id of interview list
        Returns:
            result (dict) : that contains marking scheme(details)
        """
        marking_scheme = {}
        if (
            interview_list := await DatabaseConfiguration().interview_list_collection.find_one(
                {"_id": ObjectId(interview_list_id)}
            )
        ) is None:
            return marking_scheme
        if (selection_procedure := interview_list.get("selection_procedure")) is None:
            return marking_scheme
        gd_weightage = selection_procedure.get("gd_parameters_weightage")
        pi_weightage = selection_procedure.get("pi_parameters_weightage")
        if gd_weightage:
            marking_scheme["gd"] = await self.get_marking_parameters_with_weightage(
                gd_weightage
            )
        if pi_weightage:
            marking_scheme["pi"] = await self.get_marking_parameters_with_weightage(
                pi_weightage
            )
        return marking_scheme

    async def display_profile_marking(self, slot_id, season=None):
        """
        Able to return student profile details and marking scheme

        Params:
            - slot_id (str) : given slot id

        Returns:
            dict: A dictionary contains info about student profile and marking scheme
        """
        if (
            slots := await DatabaseConfiguration().slot_collection.find_one(
                {"_id": ObjectId(slot_id)}
            )
        ) is None:
            raise DataNotFoundError(slot_id, "Slot")
        applications = slots.get("take_slot", {}).get("application_ids", [])
        interview_list_id = slots.get("interview_list_id")
        if applications:
            app_id = applications[0]
            if (
                app_doc := await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"_id": ObjectId(app_id)}
                )
            ) is None:
                raise DataNotFoundError(app_id, "Application")
            if (meet := app_doc.get("meetingDetails")) is None:
                zoom_link = ""
            else:
                zoom_link = meet.get("zoom_link")
            result = {"student_profile": []}
            for app_id in applications:
                profile = await planner_obj.display_student_basic_profile(
                    str(app_id), season=season
                )
                student_profile = {
                    "applicationId": str(app_id),
                    "studentId": str(profile.get("studentId")),
                    "name": profile.get("student_name"),
                    "ug_info": profile.get("ug_info"),
                    "tenth_info": profile.get("tenth_info"),
                    "inter_info": profile.get("inter_info"),
                    "attachments": profile.get("attachments"),
                }
                result.get("student_profile").append(student_profile)
            slot_type = slots.get("slot_type")
            marking_scheme, course_name, specialization_name = \
                await self.marking_details(interview_list_id, slot_type)
            result.update(
                {
                    "marking_scheme": marking_scheme,
                    "course_Name": course_name,
                    "specialization_name": specialization_name,
                    "join_link": zoom_link,
                }
            )
            return result
        else:
            return {"message": "no applications present."}

    async def month_wise_slots_info(self, month_wise_slots_data):
        """
        Get month wise slots info with/without filter according to program.

        Params:
            month_wise_slots_data: A dictionary which contains application is
                along with filterable fields.
                e.g., {"application_id": "123456789012345678901212",
                    "location": None, "month": None}

        Returns:
           list: A list interview slots data according to program.
        """
        return await PlannerAggregation().month_wise_slots_info(month_wise_slots_data)

    async def invite_student_to_meeting(
        self,
        slot_data: dict,
        application_id: str,
        request: Request,
        college: dict,
        action_type="system",
    ):
        """
        Send meeting information to student through mail.

        Params:
            - slot_data (dict): A dictionary which contains slot data.
            - application_id (dict): An unique identifier/id of
                application. Useful for get student data.
                e.g., 123456789012345678901222.
            - request (Request): An object of class `Request`,
                useful for get user info.
            - college (dict): A dictionary which contains college data.
                e.g., 123456789012345678901234.
            - background_tasks (BackgroundTasks): Useful for perform
                background tasks.

        Returns:
            dict: A dictionary which contains invite student mail info.
        """
        await utility_obj.is_length_valid(application_id, "Application id")
        if (
            application := await DatabaseConfiguration().studentApplicationForms.find_one(
                {"_id": ObjectId(application_id)}
            )
        ) is None:
            raise DataNotFoundError(message="Application")
        if (
            meeting_details := await DatabaseConfiguration().meeting_collection.find_one(
                {"slot_id": slot_data.get("_id")}
            )
        ) is None:
            raise DataNotFoundError(message="Interview meeting details not" " found.")
        if (
            student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                {"_id": application.get("student_id")}
            )
        ) is None:
            raise DataNotFoundError(message="Student not found.")
        meeting_link = meeting_details.get("zoom_link")
        meeting_id = meeting_details.get("meeting_id")
        passcode = meeting_details.get("passcode")
        time = slot_data.get("time")
        minutes = (slot_data.get("end_time") - time).total_seconds() // 60
        user_name = student.get("user_name")
        toml_data = utility_obj.read_current_toml_file()
        if toml_data.get("testing", {}).get("test") is False:
            await EmailActivity().send_interview_invitation_through_mail(
                request,
                time,
                minutes,
                meeting_id,
                passcode,
                meeting_link,
                college,
                [user_name],
                user_name,
                action_type=action_type
            )

        return {"message": "Email send to student."}

    async def average_scores_comments(self, app_doc, interview_list_id):
        """
           To return the average of scores which is in feedback field , default this
           will  consider below given permanent fields, this will also dynamically add fields
           in feedback which are not in permanent fields dict
        Params:\n
            app_doc (dict): details of given application id
            interview_list_id (str) : id of interview list
        Returns:
            result (dict) : average of all individual scores,combination of comments
        """
        gd_params_weightage, pi_params_weightage = {}, {}
        if (
            interview_list := await DatabaseConfiguration().interview_list_collection.find_one(
                {"_id": ObjectId(interview_list_id)}
            )
        ) is None:
            gd_params = True
            pi_params = True
        elif (selection_procedure := interview_list.get("selection_procedure")) is None:
            gd_params = True
            pi_params = True
        else:
            gd_params_weightage = selection_procedure.get("gd_parameters_weightage")
            pi_params_weightage = selection_procedure.get("pi_parameters_weightage")
            gd_params = True if gd_params_weightage else False
            pi_params = True if pi_params_weightage else False
        permanent_fields = {
            "communication_skills": 0.0,
            "domain_knowledge": 0.0,
            "behavioral_traits": 0.0,
            "attitude": 0.0,
            "etiquette": 0.0,
            "comments": "",
            "overall_rating": 0,
        }
        permanent_fields = [
            {"name": key, "point": value} for key, value in permanent_fields.items()
        ]
        if gd_params_weightage:
            gd_params_weightage.update({"comments": "", "overall_rating": 0})
            gd_params_weightage = [
                {"name": key, "point": "" if key == "comments" else 0}
                for key in gd_params_weightage.keys()
            ]
        else:
            gd_params_weightage = permanent_fields
        if pi_params_weightage:
            pi_params_weightage.update({"comments": "", "overall_rating": 0})
            pi_params_weightage = [
                {"name": key, "point": "" if key == "comments" else 0}
                for key in pi_params_weightage.keys()
            ]
        else:
            pi_params_weightage = permanent_fields
        feedback_ = app_doc.get("feedback", {})
        if not feedback_:
            scores_list = {}
            overall_rating = {}
            if gd_params:
                gd = {"not_reviewed": gd_params_weightage}
                scores_list["gd"] = gd
                overall_rating["gd"] = 0
            if pi_params:
                pi = {"not_reviewed": pi_params_weightage}
                scores_list["pi"] = pi
                overall_rating["pi"] = 0
            return {"scores": scores_list, "overall_rating": overall_rating}
        interview_list_id = ObjectId(interview_list_id)
        pipeline = [
            {
                "$match": {
                    "_id": app_doc.get("_id"),
                    "feedback.interview_list_id": interview_list_id,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "feedback": {
                        "$filter": {
                            "input": "$feedback",
                            "as": "feedback_item",
                            "cond": {
                                "$eq": [
                                    "$$feedback_item.interview_list_id",
                                    interview_list_id,
                                ]
                            },
                        }
                    },
                }
            },
        ]
        total_scores = {}
        result = {}
        cursor = DatabaseConfiguration().studentApplicationForms.aggregate(pipeline)
        feedbacks = await cursor.to_list(length=None)
        feedbacks = feedbacks[0].get("feedback")
        result["gd"], result["pi"], gd_sum, pi_sum, gd_total, pi_total = (
            {},
            {},
            0,
            0,
            0,
            0,
        )
        overall_rating = {}
        for f_b in feedbacks:
            rating = f_b.get("overall_rating")
            scores = f_b.get("scores")
            for score_key, score_value in scores.items():
                if score_key not in total_scores:
                    total_scores[score_key] = 0.0
                if score_value is not None:
                    total_scores[score_key] = score_value
            total_scores["comments"] = f_b.get("comments")
            total_scores["overall_rating"] = round(rating, 2)
            scores_list = [
                {"name": key, "point": value} for key, value in total_scores.items()
            ]
            if f_b.get("slot_type") == "PI":
                pi_sum += rating
                pi_total += 1
                result["pi"].update({f_b.get("interviewer_name"): scores_list})
            elif f_b.get("slot_type") == "GD":
                gd_sum += rating
                gd_total += 1
                result["gd"].update({f_b.get("interviewer_name"): scores_list})
        try:
            gd_overall = round(gd_sum / gd_total, 2)
        except ZeroDivisionError:
            gd_overall = 0
        try:
            pi_overall = round(pi_sum / pi_total, 2)
        except ZeroDivisionError:
            pi_overall = 0
        overall_rating.update({"gd": gd_overall, "pi": pi_overall})
        if gd_params and result["gd"] == {}:
            gd = {"not_reviewed": gd_params_weightage}
            result["gd"] = gd
            overall_rating["gd"] = 0
        elif result["gd"] == {}:
            del result["gd"]
            del overall_rating["gd"]
        if pi_params and result["pi"] == {}:
            pi = {"not_reviewed": pi_params_weightage}
            result["pi"] = pi
            overall_rating["pi"] = 0
        elif result["pi"] == {}:
            del result["pi"]
            del overall_rating["pi"]
        res = {"scores": result, "overall_rating": overall_rating}
        return res

    async def get_document_presigned_url(
        self, file_s3_url: str | None, file_name, student_id, season=None
    ):
        """
        Get the temporary document accessible URL.

        Params:
            file_s3_url (str | None): Either None or document s3 non-accessible
                URL.
            file_name (str): here file name may be(tenth/inter/graduation/recent_photo
            student_id(str): unique id of student

        Returns:
            Get the temporary document accessible URL.
        """
        season_year = utility_obj.get_year_based_on_season(season)
        aws_env = settings.aws_env
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        base_bucket_url = getattr(settings, f"s3_{aws_env}_base_bucket_url")
        path = f"{utility_obj.get_university_name_s3_folder()}/{season_year}/{settings.s3_student_documents_bucket_name}/{student_id}/{file_name}"
        if not file_s3_url.startswith("https"):
            file_s3_url = f"{base_bucket_url}{path}/{file_s3_url}"
        file_s3_url = settings.s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": base_bucket,
                "Key": f"{path}/{file_s3_url.split('/')[8]}",
            },
            ExpiresIn=1200,
        )
        return file_s3_url

    async def display_student_basic_profile(self, application_id, season=None):
        """
            display the basic Details of student which are in different databases
        Params:\n
            application_id (str) : the id of the application
        Returns:
            result (dict) : student details
        """
        app_doc = await DatabaseConfiguration().studentApplicationForms.find_one(
            {"_id": ObjectId(application_id)}
        )
        if app_doc is None:
            raise DataNotFoundError(application_id, "Application")

        student_id = app_doc.get("student_id")
        stu_doc = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"_id": student_id}
        )
        if (
            stu_sec_doc := await DatabaseConfiguration().studentSecondaryDetails.find_one(
                {"student_id": student_id}
            )
        ) is None:
            stu_sec_doc = {}
        if stu_doc is None:
            raise DataNotFoundError(student_id, "Student")

        basic_details = stu_doc.get("basic_details", {})
        address_details = stu_doc.get("address_details", {}).get(
            "communication_address", {}
        )
        state_id = address_details.get("state", {}).get("state_id")
        states = await get_collection_from_cache(collection_name="states")
        if states:
            state = utility_obj.search_for_document(states, field="_id", search_name=str(state_id))
        else:
            state = await DatabaseConfiguration().state_collection.find_one(
                {"_id": state_id})
            collection = await DatabaseConfiguration().state_collection.aggregate([]).to_list(None)
            await store_collection_in_cache(collection, collection_name="states")
        if state is None:
            state = {}

        course_id = app_doc.get("course_id")
        if (
            course := await DatabaseConfiguration().course_collection.find_one(
                {"_id": course_id}
            )
        ) is None:
            course = {}

        edu_details = stu_sec_doc.get("education_details", {})
        attachments = stu_sec_doc.get("attachments", {})
        tenth_info = edu_details.get("tenth_school_details", {})
        inter_info = edu_details.get("inter_school_details", {})
        grad = edu_details.get("graduation_details", {})
        course_name = course.get("course_name")
        spec_name = app_doc.get("spec_name1")
        program_name = f"{course_name} in " f"{spec_name}"
        interview_status = app_doc.get("approval_status")
        status = interview_status if interview_status else ""
        result = {
            "studentId": str(student_id),
            "applicationId": str(application_id),
            "student_name": f"{basic_details.get('first_name')} {basic_details.get('middle_name')} {basic_details.get('last_name')}",
            "state": state.get("name"),
            "city": address_details.get("city", {}).get("city_name"),
            "phone_number": basic_details.get("mobile_number"),
            "email": basic_details.get("email"),
            "programme_level": (
                "post graduate" if course.get("is_pg") else "under graduate"
            ),
            "download_application": app_doc.get("application_download_url"),
            "course": program_name,
            "status": status,
            "ug_info": {
                "program_name": grad.get("ug_course_name"),
                "college_name": grad.get("name_of_institute"),
                "year": grad.get("year_of_passing"),
                "marks": grad.get("aggregate_mark"),
            },
            "attachments": {
                "tenth_url": (
                    await self.get_document_presigned_url(
                        attachments.get("tenth", {}).get("file_s3_url"),
                        "tenth",
                        student_id,
                        season=season,
                    )
                    if attachments.get("tenth")
                    else ""
                ),
                "recent_photo": (
                    await self.get_document_presigned_url(
                        attachments.get("recent_photo", {}).get("file_s3_url"),
                        "recent_photo",
                        student_id,
                        season=season,
                    )
                    if attachments.get("recent_photo")
                    else ""
                ),
                "twelth_url": (
                    await self.get_document_presigned_url(
                        attachments.get("inter", {}).get("file_s3_url"),
                        "inter",
                        student_id,
                        season=season,
                    )
                    if attachments.get("inter")
                    else ""
                ),
                "grad_url": (
                    await self.get_document_presigned_url(
                        attachments.get("graduation", {}).get("file_s3_url"),
                        "graduation",
                        student_id,
                        season=season,
                    )
                    if attachments.get("graduation")
                    else ""
                ),
            },
        }

        for std_key, std_info in [
            ("tenth_info", tenth_info),
            ("inter_info", inter_info),
        ]:
            grade_details = {
                "board": std_info.get("board"),
                "school_name": std_info.get("school_name"),
                "year": std_info.get("year_of_passing"),
                "marks": std_info.get("obtained_cgpa"),
            }
            result[std_key] = grade_details

        return result

    async def display_student_profile(
        self, application_id, interview_list_id, season=None
    ):
        """
            display the Details of student which are in different databases
        Params:\n
            application_id (str) : the id of the application
            interview_list_id (str) : unique id of interview list
        Returns:
            result (dict) : student details
        """
        app_doc = await DatabaseConfiguration().studentApplicationForms.find_one(
            {"_id": ObjectId(application_id)}
        )
        if app_doc is None:
            raise DataNotFoundError(application_id, "Application")
        interview_doc = (
            await DatabaseConfiguration().interview_list_collection.find_one(
                {"_id": ObjectId(interview_list_id)}
            )
        )
        if interview_doc is None:
            raise DataNotFoundError(interview_list_id, "Interview List")
        basic_details = await self.display_student_basic_profile(
            application_id, season=season
        )
        result = basic_details
        result.update({"interview_list_id": str(interview_list_id)})
        marking_scheme = await self.marking_details_both_gd_pi(interview_list_id)
        result.update({"marking_scheme": marking_scheme})
        scores = await self.average_scores_comments(app_doc, interview_list_id)
        result.update(scores)
        return result

    async def date_wise_panels_slots_hours(self, target_date):
        """
            return the count of panels, slots and no.of hours booked
        Params:\n
            target_date (str) : Given date
        Returns:
            result (dict) : panel_slot_hours information along with date and day
        """
        filter_query = [
            {
                "$match": {
                    "$expr": {
                        "$and": [
                            {"$eq": [{"$dayOfMonth": "$time"}, target_date.day]},
                            {"$eq": [{"$month": "$time"}, target_date.month]},
                            {"$eq": [{"$year": "$time"}, target_date.year]},
                        ]
                    }
                }
            }
        ]
        slot_data = DatabaseConfiguration().slot_collection.aggregate(filter_query)
        slot_documents = await slot_data.to_list(length=None)
        slot_count = len(slot_documents)
        panel_data = DatabaseConfiguration().panel_collection.aggregate(filter_query)
        documents = await panel_data.to_list(length=None)
        panel_count = len(documents)
        durations = [doc["end_time"] - doc["time"] for doc in slot_documents]
        total_hours = int(
            sum(duration.total_seconds() / 3600 for duration in durations)
        )
        result = {
            "date": target_date.day,
            "day": target_date.strftime("%A")[0:3],
            "slot_count": slot_count,
            "panel_count": panel_count,
            "time": total_hours,
        }
        return result

    async def panels_slots_hours(self, date, is_slot):
        """
            return the count of panels and slots
            on given and previous and upcoming dates,
            also no.of hours booked
        Params:\n
            date (str) : Given date
            is_slot(bool):If true send slot data else send panel data.
        Returns:
            result (dict) : panel_slot_hours information
        """
        date = datetime.strptime(date, "%d/%m/%Y")
        result = []
        previous_date = date - timedelta(days=1)
        next_dates = [date + timedelta(days=i) for i in range(1, 5)]
        for target_date in [previous_date, date, next_dates[0]]:
            data = await self.date_wise_panels_slots_hours(target_date)
            result.append(data)
        result[1].update({"isActive": True})
        next_dates.pop(0)
        if is_slot:
            for target_date in next_dates:
                data = await self.date_wise_panels_slots_hours(target_date)
                result.append(data)
        return result

    async def get_required_slot_panel_data(
        self, panel: dict | None, slot: dict | None, data: dict
    ) -> tuple:
        """
        Get required slot or panel data.

        Params:
            panel (dict | None): Either None or a dictionary which contains
                panel data.
            slot (dict | None): Either None or a dictionary which contains
                slot data.
            data (dict): A dictionary which can contains updated slot / panel
             data.

        Returns:
            tuple: A tuple which contains data which further useful for get
                slot/panel data.
        """
        if panel:
            interview_list_id = panel.get("interview_list_id")
            start_time = panel.get("time")
            end_time = panel.get("end_time")
            slots = (
                await DatabaseConfiguration()
                .slot_collection.aggregate([{"$match": {"panel_id": panel.get("_id")}}])
                .to_list(length=None)
            )
            slot_ids = [slot_doc.get("_id") for slot_doc in slots]
        else:
            interview_list_id = slot.get("interview_list_id")
            start_time = slot.get("time")
            end_time = slot.get("end_time")
            slot_ids = [slot.get("_id")]
            panelists = (
                await DatabaseConfiguration()
                .user_collection.aggregate([{"$match": {"panel_id": {"$in": slot.get("panelists", [])}}}])
                .to_list(length=None)
            )
            panelist_names = [
                {
                    "_id": str(panelist_doc.get("_id")),
                    "name": utility_obj.name_can(panelist_doc),
                }
                for panelist_doc in panelists
            ]
            data.update({"panelist_names": panelist_names})
        return start_time, end_time, interview_list_id, slot_ids, data

    async def get_slot_or_panel_data_based_on_id(
        self,
        slot_or_panel_id: str,
        filter_slot_panel: None | dict,
        page_num: int | None,
        page_size: int | None,
    ) -> dict:
        """
        Get slot or panel data by id along with available panelist data and
            applicants data.

        Params:
            slot_or_panel_id (str): An unique identifier/id of
                a slot or panel. e.g., 123456789012345678901212
            filter_slot_panel (None | dict): Either none or a dictionary
                which contains filterable field with their values.
            page_num (int | None): Page number will be only useful for
                show applicants data. e.g., 1
            page_size (int | None): Page size means how many data you want to
                show on page_num. e.g., 25

        Returns:
            result (dict) : A dictionary which contains Slot or panel data.
        """
        await utility_obj.is_length_valid(_id=slot_or_panel_id, name="Slot or Panel Id")
        slot_or_panel_id, slot = ObjectId(slot_or_panel_id), {}
        if (
            panel := await DatabaseConfiguration().panel_collection.find_one(
                {"_id": slot_or_panel_id}
            )
        ) is None:
            if (
                slot := await DatabaseConfiguration().slot_collection.find_one(
                    {"_id": slot_or_panel_id}
                )
            ) is None:
                return {"detail": "Slot or Panel id is not correct."}
        data = self.format_panel_data(panel) if panel else self.format_slot_data(slot)
        for key in [
            "created_by",
            "created_by_name",
            "created_at",
            "last_modified_timeline",
        ]:
            if data.get(key):
                data.pop(key)
        start_time, end_time, interview_list_id, slot_ids, data = (
            await self.get_required_slot_panel_data(panel, slot, data)
        )
        planner_aggr_obj = PlannerAggregation()
        slots_data = (
            await planner_aggr_obj.slot_applicants_and_panelists_data(slot_ids)
            if slot_ids
            else []
        )
        if (
            interview_list := await DatabaseConfiguration().interview_list_collection.find_one(
                {"_id": interview_list_id}
            )
        ) is None:
            raise DataNotFoundError(message="Interview list")
        application_ids = interview_list.get("eligible_applications")
        if application_ids:
            applicants, total_applicants = (
                await planner_aggr_obj.get_interview_applicants(
                    application_ids,
                    filter_slot_panel,
                    page_num,
                    page_size,
                    data.get("slot_type"),
                    interview_list,
                )
            )
        else:
            applicants, total_applicants = [], 0
        available_panelists = [
            ObjectId(panelist_id) for panelist_id in data.get("panelists", [])
        ]
        available_panelists = await AdminUser().available_panelist_by_filters(
            filters={
                "panelist_ids": available_panelists,
                "filter_slot_panel": filter_slot_panel,
            }
        )

        data.update(
            {
                "interview_list_name": interview_list.get("list_name"),
                "moderator_name": interview_list.get("moderator_name"),
                "slots": slots_data,
                "panelists": available_panelists,
                "applicants": [applicants],
                "total_applicants": total_applicants,
            }
        )
        return data

    async def send_mail_to_unassign_users(
        self,
        slot: dict,
        email_ids: list,
        college: dict,
        user_email: str,
        user_name: str,
        user_id: str,
        ip_address: str,
    ):
        """
        Send mail to unassigned users.

        Params:
            slot (dict): A dictionary which contains slot data.
            email_ids (list): A list which contains email ids of applicants.
            college (dict): A dictionary which contains college data.
            user_email (str): Email id of user.
            user_name (name): A name of a user.
            user_id (str): Unique identifier/id of a user.
            ip_address (str): IP address of a user.
            background_tasks (BackgroundTasks): Useful for perform tasks in
                the background.

        Returns:
            None: not returning anything.
        """

        time = slot.get("time")
        minutes = (slot.get("end_time") - time).total_seconds() // 60
        TEMPLATE = (
            f"Dear user"
            f", your interview is cancelled. <br><br>"
            "<b>Interview details are given "
            "below:</b><br>Interview time: "
            f"{utility_obj.get_local_time(time)}"
            f"<br>Duration: {minutes} minutes<br><br>"
            f"Thank you & Regards,<br>"
            f"{college.get('name')}, "
            f"{college.get('address', {}).get('city')}"
        )
        final_emails = []
        for email_id in email_ids:
            extra_emails = await EmailActivity().add_default_set_mails(email_id)
            final_emails.extend(extra_emails)
        email_ids = final_emails
        if not is_testing_env():
            await utility_obj.publish_email_sending_on_queue(data={
                "email_preferences": college.get("email_preferences", {}),
                "email_type": "transactional",
                "email_ids": email_ids,
                "subject": "Un-assign Slot Info",
                "template": TEMPLATE,
                "event_type": "email",
                "event_status": f"sent by {user_name} whose id: {user_id}",
                "event_name": "Un-assign applicant",
                "current_user": user_email,
                "ip_address": ip_address,
                "payload": {
                        "content": "Un-assign applicant email",
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
            }, priority=20)

    async def validate_and_update_slot(self, slot_id: str) -> None | tuple:
        """
        Validate and update slot based on un-assign applicants.
        After un-assign applicants from slot, send mail to applicants about
            interview cancelled.

        Params:
          slot_id (str): A unique identifier/id of a slot. Useful for
          un-assign applicants from slot.

        Returns:
            None | tuple: Either None or a tuple which contains email ids
                which useful for send mail to un-assign applicants and
                slot info.
        """
        await utility_obj.is_id_length_valid(slot_id, "Slot id")
        if (
            slot := await DatabaseConfiguration().slot_collection.find_one(
                {"_id": ObjectId(slot_id)}
            )
        ) is None:
            raise DataNotFoundError(slot_id, "Slot")
        if (take_slot := slot.get("take_slot", {})) is None:
            return
        email_ids = []
        if take_slot.get("application"):
            application_ids = take_slot.get("application_ids", [])
            updated_slot = await DatabaseConfiguration().slot_collection.update_one(
                {"_id": slot.get("_id")},
                {
                    "$set": {"booked_user": 0, "take_slot.application": False},
                    "$unset": {"take_slot.application_ids": True},
                },
            )
            if updated_slot:
                await DatabaseConfiguration().studentApplicationForms.update_many(
                    {
                        "_id": {"$in": application_ids},
                        "meetingDetails.slot_id": ObjectId(slot_id),
                    },
                    {"$unset": {"meetingDetails": True}},
                )
                for application_id in application_ids:
                    if (
                        application := await DatabaseConfiguration().studentApplicationForms.find_one(
                            {"_id": application_id}
                        )
                    ) is None:
                        continue
                    if (
                        student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                            {"_id": application.get("student_id")}
                        )
                    ) is None:
                        continue
                    email_ids.append(student.get("user_name"))
        return email_ids, slot

    async def remove_all_applicants_from_slots(
        self, slot_ids: list, college: dict, user: dict, request: Request
    ):
        """
        Un-assign/Remove all applicant from given slots.
        After un-assign applicants from slot, send mail to applicants
        about interview cancelled.

        Params:
            slot_ids(list): A list which contains unique identifiers/ids of
                slots.
                e.g., ["123456789012345678901232", "123456789012345678901222"]
            background_tasks (BackgroundTasks): Useful for perform tasks in
                the background.
            college (dict): A dictionary which contains college data.
                e.g., 123456789012345678901211
            user (dict): A dictionary which contains user data.
            request (Request): Useful for get ip address of user.

        Returns:
            dict: A dictionary which contains unassigned applicants' info.
        """
        user_email = user.get("user_name")
        user_name = utility_obj.name_can(user)
        user_id = user.get("_id")
        ip_address = utility_obj.get_ip_address(request)
        for slot_id in slot_ids:
            email_ids, slot_info = await self.validate_and_update_slot(slot_id)
            if email_ids and slot_info:
                toml_data = utility_obj.read_current_toml_file()
                if toml_data.get("testing", {}).get("test") is False:
                    await self.send_mail_to_unassign_users(
                        slot_info,
                        email_ids,
                        college,
                        user_email,
                        user_name,
                        user_id,
                        ip_address,
                    )
        return {"message": "All applicants are unassigned from given slots."}


planner_obj = Planner()
