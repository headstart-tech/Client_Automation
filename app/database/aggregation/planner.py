"""
This file contains class and functions which helpful to perform aggregation
on planner module.
"""
from calendar import monthrange
from datetime import datetime, timedelta

from bson import ObjectId

from app.core.custom_error import DataNotFoundError
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration


class PlannerAggregation:
    """
    Contains functions helpful to perform aggregation on planner module.
    """

    async def format_slot_panel_data(self, data: dict, slot: bool,
                                     panel: bool) -> dict:
        """
        Get formatted slot/panel data.

        Params:
            data (dict): slot/panel data which want to format.
            slot (bool): Useful for get extra information of slot like
                slot available or not.
            panel (bool): Useful for get extra information of panel like
                panel deletable or not.

        Returns:
            temp_data (dict): A dictionary which contains formatted slot/panel
            data.
        """
        temp_data = {"id": data.get("id"),
                     "name": data.get("name"),
                     "activeSchedule": data.get(
                         "activeSchedule"),
                     "time": data.get("time"),
                     "pi": data.get("pi"),
                     "gd": data.get("gd"),
                     "publish": data.get("publish")}
        if slot:
            temp_data.update({"is_available": data.get("is_available"),
                              "can_delete": data.get("can_delete")})
        if panel:
            can_delete = True
            slots = await DatabaseConfiguration().slot_collection.aggregate(
                [{"$match": {"panel_id": ObjectId(temp_data.get("id"))}}]).to_list(
                length=None)
            for slot_doc in slots:
                if slot_doc.get("take_slot", {}).get("application"):
                    can_delete = False
                    break
            temp_data.update({"can_delete": can_delete})
        return temp_data

    async def get_time_slots(self, date: str) -> tuple:
        """
        Get start datetime and end datetime of two dates.
        By default, get today start and end datetime along with next
        date start and end datetime.

        Params:
            date (str): A specific date. Useful for get day-wise slot data.

        Returns:
            tuple: A start and end datetime of two dates.
        """
        if not date:
            date = (datetime.utcnow() + timedelta(
                hours=5, minutes=30)).strftime("%Y-%m-%d")
        date_utc = await utility_obj.date_change_utc(date,
                                                     date_format="%Y-%m-%d")
        next_date = (date_utc + timedelta(days=1, hours=5,
                                          minutes=30)).strftime(
            "%Y-%m-%d")
        previous_date = (date_utc + timedelta(days=1)).strftime(
            "%Y-%m-%d")
        start_date, first_date = await utility_obj.date_change_format(
            date, previous_date)
        second_date, end_date = await utility_obj.date_change_format(
            next_date, next_date)
        return start_date, first_date, second_date, end_date

    async def update_filter_slot_match(
            self, match_stage: dict, filter_slot: list | None,
            slot_state: str | None, slot_status: list | None):
        """
        Update match stage if you want data based on filter.

        Params:
            match_stage (dict): A dictionary which can contains updated match
             stage info.
             filter_slot (list | None): Either None or a list which can
                contains filterable values.
            slot_state (str | None): Either None or a string which represents
                slot state.
            slot_status (list | None): Either None or a list which can
                contains statuses of slots.

        Returns:
            match_stage (dict): A match stage data useful for get slots/panels.
        """
        if filter_slot:
            if "GD" in filter_slot and "PI" in filter_slot:
                match_stage.update({"slot_type": {"$in": ["GD", "PI"]}})
            elif "GD" in filter_slot:
                match_stage.update({"slot_type": "GD"})
            elif "PI" in filter_slot:
                match_stage.update({"slot_type": "PI"})
        if slot_state not in [None, ""]:
            publish_status = "published" if slot_state == "Published" \
                else "Draft"
            match_stage.update({"status": publish_status})
        if slot_status:
            if "Available" in slot_status and "Booked" in slot_status:
                match_stage.update({"$or": [
                    {"available_slot": {"$in": ["Open", None, "Closed"]}},
                    {"status": {"$in": ["booked", "published"]}}]})
            elif "Available" in slot_status:
                match_stage.update({"$or": [
                    {"available_slot": {"$in": ["Open", None]}},
                    {"status": "published"}]})
            elif "Booked" in slot_status:
                match_stage.update({"$or": [{"available_slot": "Closed"},
                                            {"status": "booked"}]})
        return match_stage

    async def update_pipeline_based_on_cond(
            self, pipeline: list, moderator: list | None,
            program_name: list | None) -> list:
        """
        Update aggregation pipeline for get slots/panels based on filters.

        Params:
            moderator (list | None): Either None or a list which can
                contains moderator unique identifiers/ids.
            program_name (list | None): Either None or a list which can
                contains program names.
                Each program name contains course name and specialization name.

        Returns:
            pipeline (list): An aggregation pipeline which useful for get data.
        """
        if moderator or program_name:
            lookup_match = {"$expr": {"$eq": ["$_id",
                                              "$$interview_id"]}}
            if moderator:
                lookup_match.update({"moderator_id": {"$in": moderator}})
            if program_name:
                lookup_match.update({"$or": program_name})
            pipeline.extend([{"$lookup": {
                "from": "interviewLists",
                "let": {"interview_id": "$interview_list_id"},
                "pipeline": [
                    {"$match": lookup_match}],
                "as": "interview_details"}
            }, {
                "$unwind": {
                    "path": "$interview_details"
                }
            }])
        return pipeline

    async def get_slots_panels_data(self, start_time: datetime,
                                    end_time: datetime, user: dict,
                                    filter_slot: list | None,
                                    slot_status: list | None,
                                    moderator: list | None,
                                    slot_state: str | None,
                                    program_name: list | None) -> tuple:
        """
        Get slots/panels data based on date range.

        Params:
            start_time (datetime): A start datetime for get slots/panels data.
            end_time(datetime): An end datetime for get slots/panel data.
            user (dict): A dictionary which contains logged-in user
                information.
            filter_slot (list | None): Either None or a list which can
                contains filterable values.
            slot_status (list | None): Either None or a list which can
                contains statuses of slots.
            moderator (list | None): Either None or a list which can
                contains moderator unique identifiers/ids.
            slot_state (str | None): Either None or a string which represents
                slot state.
            program_name (list | None): Either None or a list which can
                contains program names.
                Each program name contains course name and specialization name.

        Returns:
            tuple: A tuple contains slots data and panels data.
        """
        slots_data, panels_data = [], []
        match_stage = {
            "time": {"$gte": start_time, "$lte": end_time}
        }
        match_stage = await self.update_filter_slot_match(
            match_stage, filter_slot, slot_state, slot_status)
        role_name = user.get("role", {}).get("role_name")
        if role_name == "panelist":
            program = user.get("selected_programs", [])
            if program:
                interview_lists = await DatabaseConfiguration(). \
                    interview_list_collection.find({"$or": program}). \
                    to_list(length=None)
                interview_list_ids = [interview_list_doc.get('_id')
                                      for interview_list_doc in
                                      interview_lists]
                if interview_list_ids:
                    match_stage.update({"interview_list_id":
                                            {"$in": interview_list_ids}})
            match_stage.update({
                "status": "published"
            })
        pipeline = [
            {
                "$match": match_stage
            },
            {
                "$project": {
                    "_id": 0,
                    "id": {"$toString": "$_id"},
                    "name": "$name",
                    "interview_list_id": 1,
                    "start_time": {
                        "$dateToString": {"format": "%H:%M", "date": "$time",
                                          "timezone": "+05:30"}},
                    "end_time": {"$dateToString": {"format": "%H:%M",
                                                   "date": "$end_time",
                                                   "timezone": "+05:30"}},
                    "activeSchedule": {"$and": ["$take_slot.application",
                                                "$take_slot.panelist"]},
                    "publish": {"$eq": ["$status", "published"]},
                    "pi": {"$eq": ["$slot_type", "PI"]},
                    "gd": {"$eq": ["$slot_type", "GD"]}
                }
            }
        ]
        pipeline = await self.update_pipeline_based_on_cond(
            pipeline, moderator, program_name)
        filter_length = len(filter_slot)
        if role_name != "panelist":
            if (not ("Slot" in filter_slot and filter_length == 1) and
                'Panel' in filter_slot) or filter_length < 1 or \
                    'PI' in filter_slot or 'GD' in filter_slot:
                panels_data = [document async for document in
                               DatabaseConfiguration().panel_collection.aggregate(
                                   pipeline)]
        if (not ("Panel" in filter_slot and filter_length == 1) and
            'Slot' in filter_slot) or filter_length < 1 or \
                'PI' in filter_slot or 'GD' in filter_slot:
            if role_name != "panelist":
                pipeline[0].get("$match", {}).update({"panel_id":
                                                          {"$in": [None, ""]}})
            pipeline[1].get("$project", {}).update(
                {"is_available": {"$and": [{"$eq": [{"$ifNull": [
                    "$available_slot",
                    "Open"]}, "Open"]},
                    {"$lt": [{"$size": {
                        "$setIntersection": [{
                            "$ifNull": ["$take_slot.panelist_ids", []]},
                            [ObjectId(user.get('_id'))]]}}, 1]}]},
                    "can_delete": {
                        "$cond": {
                            "if": {"$eq": ["$take_slot.application", True]},
                            "then": False,
                            "else": True
                        }
                    }
                })
            slots_data = [document async for document in
                          DatabaseConfiguration().slot_collection.aggregate(
                              pipeline)]
        return panels_data, slots_data

    async def get_pi_gd_count_data(self, start_time: datetime,
                                   end_time: datetime,
                                   filter_slot: list | None) -> dict:
        """
        Get PI and GD count data.

        Params:
            start_time (datetime): A start datetime for get slots/panels data.
            end_time(datetime): An end datetime for get slots/panels data.
            filter_slot (list | None): Either None or a list which can
                contains filterable values.

        Returns:
            count_info_dict (dict): A dictionary contains PI and GD count info.
        """
        count_info_dict = {}
        for slot_type in ["PI", "GD"]:
            count_filter = {'slot_type': slot_type,
                            "time": {"$gte": start_time, "$lte": end_time}}

            if filter_slot:
                if ("Slot" in filter_slot and "Panel" in filter_slot) or \
                        ("Slot" in filter_slot):
                    pass
                elif "Panel" in filter_slot:
                    count_filter.update({"panel_id": {"$nin": [None, ""]}})
            slot_count = await DatabaseConfiguration().slot_collection.count_documents(
                count_filter)
            active_count_filter = count_filter.copy()
            active_count_filter.update({'status': "published"})
            active_slot_count = await DatabaseConfiguration().slot_collection. \
                count_documents(active_count_filter)
            count_info_dict.update({slot_type:
                                        {"total_count": slot_count,
                                         "active_count": active_slot_count}})
        return count_info_dict

    async def get_time_slot_data(self, entity_data: list, start_time_int: int,
                                 slot: bool = False, without_format=False,
                                 panel: bool = False) -> list:
        """
        Get the slots/panels data for particular time slot.
        For example, for 12 PM whatever the slots/panels available, get
        those data in a list format.

        Params:
            entity_data (list): A list which contains slots/panels data.
            start_time_int (int): Time slot in a list format.
                For example, 12
            slot (bool): Useful for get extra information of slot like
                slot available or not.
            panel (bool): Useful for get extra information of panel like
                panel deletable or not.

        Returns:
            list: A list which contains formatted slots/panels data.
        """
        formatted_data = []
        for data in entity_data:
            temp_data_time = data["start_time"].split(':')
            data_end_time = data["end_time"].split(':')
            data_time_int = utility_obj.format_hour(
                int(temp_data_time[0]))
            if start_time_int <= data_time_int < start_time_int + 1:
                if without_format:
                    formatted_data.append({"id": data.get('id'),
                                           "booked": data.get("booked")})
                else:
                    data_end_time_int = utility_obj.format_hour(
                        int(data_end_time[0]))
                    data["time"] = f"{data_time_int}:{temp_data_time[1]} - " \
                                   f"{data_end_time_int}:{data_end_time[1]}"
                    formatted_data.append(
                        await self.format_slot_panel_data(data, slot, panel))
        return formatted_data

    async def get_slots_data(
            self, start_time: datetime, end_time: datetime,
            slot_type: list | None, location: str | None,
            application_id: ObjectId, interview_list_ids: list[ObjectId],
            check_slots: bool | None = False) -> list | bool:
        """
        Get slots data based on date range and slot_type.

        Params:
            start_time (datetime): A start datetime for get slots data.
            end_time(datetime): An end datetime for get slots data.
            slot_type (list): Type of slot.
            location (str): Useful for get slots based on location.
            application_id (ObjectId): A unique identifier/id of application.
            interview_list_ids (list[ObjectId]): A list which contains unique
                identifiers/ids of interview list.

        Returns:
            list: A list which contains slots data.
        """
        base_match = {
            "time": {"$gte": start_time, "$lte": end_time},
            "slot_type": {"$in": slot_type},
            "status": "published",
            "interview_list_id": {"$in": interview_list_ids}
        }
        if location:
            base_match.update({"city": location})
        if check_slots:
            pipeline = [
                {
                    "$match": base_match
                },
                {"$count": "count"}]
            month_slots = (
                await DatabaseConfiguration().slot_collection.aggregate(
                    pipeline).to_list(None)
            )
            return True if month_slots and month_slots[0].get("count", 0) > 0 \
                else False
        else:
            pipeline = [
                {
                    "$match": base_match
                },
                {"$sort": {"time": -1}},
                {
                    "$project": {
                        "_id": 0,
                        "id": {"$toString": "$_id"},
                        "booked": {"$in": [application_id,
                                           {"$ifNull": [
                                               "$take_slot.application_ids",
                                               []]}]},
                        "time": 1
                    }
                }
        ]
        slot_data = []
        async for slot_doc in DatabaseConfiguration().slot_collection.aggregate(
                pipeline):
            temp_start_time = utility_obj.get_local_time(
                slot_doc.get("time"), hour_minute=True)
            temp_start_time = temp_start_time.replace(" ", "")
            slot_data.append(
                {"time": temp_start_time, "id": slot_doc.get('id'),
                 "booked": slot_doc.get("booked")})
        return slot_data

    async def gather_day_wise_slots_data(
            self, start_time: datetime, end_time: datetime, slot_type: list,
            location: str, application_id: ObjectId, interview_list_ids: list,
            check_slots: bool | None = False) -> dict | bool:
        """
        Get day-wise slots data based on provided start datetime,
            end datetime, application id and location.

        Params:
            start_time (datetime): A start datetime for get slot data.
            end_time(datetime): An end datetime for get slot data.
            slot_type(list): Type of a slots in a list format.
            location (str): Useful for get slots based on location.
            application_id (ObjectId): A unique identifier/id of application.
            interview_list_ids (list): A list which contains unique
                identifiers/ids of interview list.

        Returns:
            temp_data (dict): A dictionary contains day wise slots data.
        """
        slots_data = await self.get_slots_data(
            start_time, end_time, slot_type, location, application_id,
            interview_list_ids, check_slots=check_slots)
        if check_slots:
            return slots_data
        day_str = end_time.strftime("%a").upper()
        temp_data = {
            "date": end_time.strftime("%d"),
            "day": day_str,
            "interViewSlots": slots_data
        }
        today_date = utility_obj.get_local_time(start_time, season=True)
        current_date = utility_obj.get_local_time(season=True)
        temp_data["is_current_date"] = True if current_date == today_date \
            else False
        return temp_data

    async def get_day_wise_slots_and_panels_data(
            self, date: str, user: dict,
            slot_panel_filters: dict | None) -> list:
        """
        Get day wise slots and panels data along with next day by perform
        aggregation.
        By default, current date and next date slots/panels data can get.

        Params:
            date (str): Optional field. Useful for get particular date slots
                and panels data.
                For example, 2023-12-31.
            user (dict): A dictionary which logged-in user information.
            slot_panel_filters (list | None): Either value will be None or
                list of filters which helpful for get slots/panels data.

        Returns:
           list: A list which contains info about day wise slots and
           panels data.
        """
        data = []
        filter_slot = slot_panel_filters.get('filter_slot', [])
        slot_status = slot_panel_filters.get('slot_status', [])
        moderator = slot_panel_filters.get('moderator', [])
        slot_state = slot_panel_filters.get('slot_state')
        program_name = slot_panel_filters.get('program_name', [])
        moderator = [ObjectId(_id) for _id in moderator
                     if await utility_obj.is_length_valid(_id=_id,
                                                          name="Moderator id")]
        start_date, end_first_date, second_date, end_second_date = \
            await self.get_time_slots(date)

        for start_time, end_time in [(start_date, end_first_date),
                                     (second_date, end_second_date)]:
            data.append(await self.gather_day_wise_panels_slots_data(
                start_time, end_time, user, filter_slot,
                slot_status, moderator, slot_state, program_name))
        return data

    async def gather_day_wise_panels_slots_data(
            self, start_time: datetime, end_time: datetime, user: dict,
            filter_slot: list | None, slot_status: list | None,
            moderator: list | None, slot_state: str | None,
            program_name: list | None):
        """
        Get day wise panels and slots data based on start and end datetime.

        Params:
            start_time (datetime): A start datetime for get slot data.
            end_time(datetime): An end datetime for get slot data.
            user (dict): A dictionary which contains logged-in user
                information.
            filter_slot (list | None): Either None or a list which can
                contains filterable values.
            slot_status (list | None): Either None or a list which can
                contains statuses of slots.
            moderator (list | None): Either None or a list which can
                contains moderator unique identifiers/ids.
            slot_state (str | None): Either None or a string which represents
                slot state.
            program_name (list | None): Either None or a list which can
                contains program names.
                Each program name contains course name and specialization name.

        Returns:
            temp_data (dict): A dictionary contains day wise slots and panels
            info.
        """
        panels_data, slots_data = await self.get_slots_panels_data(
            start_time, end_time, user, filter_slot, slot_status,
            moderator, slot_state, program_name)
        count_data = await self.get_pi_gd_count_data(start_time, end_time,
                                                     filter_slot)
        pi_count_info = count_data.get("PI", {})
        gd_count_info = count_data.get("GD", {})
        time_slots = []
        date_str = end_time.strftime("%a, %b %d, %Y")
        start_time += timedelta(hours=8)
        end_time = start_time + timedelta(hours=11)
        while start_time < end_time:
            start_time_int = int(
                utility_obj.get_local_time(start_time, only_hour=True))

            # Filter slots and panels data for the current time slot
            filtered_slots_data = await self.get_time_slot_data(
                slots_data, start_time_int, slot=True)
            filtered_panels_data = await self.get_time_slot_data(
                panels_data, start_time_int, panel=True)

            start_time += timedelta(hours=1)

            time_slots.append({
                "time": f"{start_time_int}:00",
                "allPanel": filtered_panels_data,
                "allSlot": filtered_slots_data
            })

        temp_data = {
            "date": date_str,
            "allTime": time_slots,
            "activePI": pi_count_info.get("active_count"),
            "activeGD": gd_count_info.get("active_count"),
            "totalPI": pi_count_info.get("total_count"),
            "totalGD": gd_count_info.get("total_count")
        }
        return temp_data

    async def perform_next_action(
            self, slot_status: dict | None, slot_type: str,
            next_action: str | None) -> str:
        """
        Get slot_type for performed next option.

        Params:
            slot_status (dict | None): Either None or a dictionary which
                slot status data.
            slot_type (str): Type of slot.
            next_action (str | None): Either None or next action which useful
                for get slot details.

        Returns:
            slot_type (str): Type of slot.
        """
        if slot_status is not None:
            status = slot_status.get("status")
            if status == "Done":
                slot_type = next_action
            if status == "Scheduled":
                slot_type = None
        return slot_type

    async def get_slot_type(self, application: dict | None,
                            selection_procedure: dict) -> str:
        """
        Get slot_type which useful for slot data.

        Params:
            application (dict | None): Either None or a dictionary which
                contains application data.
            selection_procedure (dict): A dictionary which contains selection
                procedure data.

        Returns:
            slot_type (str): Type of slot.
        """
        gd_parameters = selection_procedure.get("gd_parameters_weightage")
        pi_parameters = selection_procedure.get("pi_parameters_"
                                                "weightage")
        if gd_parameters and pi_parameters:
            slot_type = "GD"
            next_action = "PI"
            slot_type = await self.perform_next_action(
                application.get("gd_status"), slot_type, next_action)
            if slot_type == "PI":
                slot_type = await self.perform_next_action(
                    application.get("pi_status"), slot_type, None)
        elif gd_parameters:
            slot_type = "GD"
            slot_type = await self.perform_next_action(
                application.get("gd_status"), slot_type, None)
        else:
            slot_type = "PI"
            slot_type = await self.perform_next_action(
                application.get("pi_status"), slot_type, None)
        return slot_type

    async def check_slots_available(self, application_id: str) -> bool:
        """
        Check slots available or not for particular student by application id.
        Params:
            application_id (str): Unique identifier of an application.
                e.g., "123456789012345678901212"
        Returns:
           bool: A boolean value which represent slots available or not.
        """
        if (
                application := await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"_id": ObjectId(application_id)}
                )) is None:
            raise DataNotFoundError(application_id, "Application")
        interview_list_id = application.get("interview_list_id")
        slot_type, interview_list_ids = [], []
        if interview_list_id:
            interview_list_ids = interview_list_id
            interview_lists = await DatabaseConfiguration(). \
                interview_list_collection.aggregate(
                [{"$match": {"_id": {"$in": interview_list_id}}}]).to_list(length=None)
            for interview_list_doc in interview_lists:
                temp_selection_process = interview_list_doc. \
                    get("selection_procedure")
                if temp_selection_process is None:
                    slot_type = ["GD", "PI"]
                    break
                else:
                    gd = temp_selection_process.get("gd_parameters_weightage")
                    pi = temp_selection_process.get("pi_parameters_weightage")
                    if gd and pi:
                        slot_type = ["GD", "PI"]
                        break
                    elif pi:
                        slot_type.append("PI")
                    else:
                        slot_type.append("GD")
        else:
            slot_type = ["GD", "PI"]
        current_date = datetime.utcnow()
        month = current_date.month
        YEAR = current_date.year
        num_days = monthrange(YEAR, month)[1]
        start_date, end_date = await utility_obj.date_change_format(
            f"{YEAR}-{month}-01", f"{YEAR}-{month}-{num_days}")
        return await self.gather_day_wise_slots_data(
            start_date, end_date, slot_type, None, application_id,
            interview_list_ids, check_slots=True)

    async def month_wise_slots_info(self, month_wise_slots_data: dict) -> list:
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
        APPLICATION_ID = month_wise_slots_data.pop("application_id")
        await utility_obj.is_length_valid(
            _id=APPLICATION_ID, name="Application id")
        application_id = ObjectId(APPLICATION_ID)
        if (
        application := await DatabaseConfiguration().studentApplicationForms.find_one(
                {"_id": application_id}
        )) is None:
            raise DataNotFoundError(APPLICATION_ID, "Application")
        interview_list_id = application.get("interview_list_id")
        slot_type, interview_list_ids = [], []
        if interview_list_id:
            interview_list_ids = interview_list_id
            interview_lists = await DatabaseConfiguration(). \
                interview_list_collection.aggregate(
                [{"$match": {"_id": {"$in": interview_list_id}}}]).to_list(length=None)
            for interview_list_doc in interview_lists:
                temp_selection_process = interview_list_doc.\
                    get("selection_procedure")
                if temp_selection_process is None:
                    slot_type = ["GD", "PI"]
                    break
                else:
                    gd = temp_selection_process.get("gd_parameters_weightage")
                    pi = temp_selection_process.get("pi_parameters_weightage")
                    if gd and pi:
                        slot_type = ["GD", "PI"]
                        break
                    elif pi:
                        slot_type.append("PI")
                    else:
                        slot_type.append("GD")
        else:
            slot_type = ["GD", "PI"]
        LOCATION = month_wise_slots_data.pop("location")
        current_date = datetime.utcnow()
        month = month_wise_slots_data.pop("month")
        YEAR = current_date.year
        if not month:
            month = current_date.month
        num_days = monthrange(YEAR, month)[1]
        days = [await utility_obj.date_change_format(
            f"{YEAR}-{month}-{day}", f"{YEAR}-{month}-{day}") for day in
                range(1, num_days + 1)]
        data = []
        for date in days:
            start_time, end_time = date[0], date[1]
            data.append(await self.gather_day_wise_slots_data(
                start_time, end_time, slot_type, LOCATION, application_id,
                interview_list_ids))
        return data

    async def applicants_and_panelist_project_stage(self):
        return {"$project": {
            "_id": {"$toString": "$_id"},
            "panelist_ids": {"$ifNull": ["$take_slot.panelist_ids", []]},
            "application_ids": {
                "$ifNull": ["$take_slot.application_ids", []]},
            "slot_duration": {
                "$ifNull": ["$slot_duration", "NA"]},
            "booked_user": {
                "$ifNull": ["$booked_user", "NA"]},
            "user_limit": {
                "$ifNull": ["$user_limit", "NA"]},
            "start_time": "$time",
            "end_time": "$end_time",
            "status": 1
        }}

    async def name_project_stage(
            self, first_name="$basic_details.first_name",
            middle_name="$basic_details.middle_name",
            last_name="$basic_details.last_name", id_in_string=False):
        project_stage = {
            "_id": 0,
            "name": {
                "$trim": {
                    "input": {
                        "$concat": [
                            first_name,
                            " ",
                            middle_name,
                            " ",
                            last_name
                        ]
                    }
                }
            }
        }
        if id_in_string:
            project_stage.update({"_id": {"$toString": "$_id"}})
        return {"$project": project_stage}

    async def get_panelist_data(self, panelist_ids):
        """

        """
        user_project_stage = await self.name_project_stage(
            first_name="$first_name", middle_name="$middle_name",
            last_name="$last_name", id_in_string=True)
        pipeline = [{
            "$match": {
                "$expr": {
                    "$in": ["$_id", panelist_ids]
                }
            }
        },
        user_project_stage]
        result = DatabaseConfiguration().user_collection.aggregate(pipeline)
        return [document async for document in result]


    async def slot_applicants_and_panelists_data(self, slot_ids: list):
        """
        Get slot taken applicants and panelist data based on slot_ids.

        Params:
            slot_ids (list): A list which contains unique identifiers/ids of
                slot. e.g., ["123456789012345678901232",
                "123456789012345678901231"]

        Returns:
            slot_documents (list): A list which contains each slot data.
        """
        basic_project_stage = await self.applicants_and_panelist_project_stage(
        )
        student_project_stage = await self.name_project_stage()
        pipeline = [
            {
                "$match": {
                    "_id": {"$in": slot_ids}
                }
            },
            basic_project_stage,
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": {"application_id": "$application_ids"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$in": ["$_id", "$$application_id"]
                                }
                            }
                        },
                        {
                            "$project": {
                                "application_id": {"$toString": "$_id"},
                                "_id": 0,
                                "student_id": 1
                            }
                        },
                        {
                            "$lookup": {
                                "from": "studentsPrimaryDetails",
                                "let": {"student_id": "$student_id"},
                                "pipeline": [
                                    {
                                        "$match": {
                                            "$expr": {
                                                "$eq": ["$_id", "$$student_id"]
                                            }
                                        }
                                    },
                                    student_project_stage
                                ], "as": "student_details"
                            }
                        },
                        {
                            "$unwind": {
                                "path": "$student_details"}},
                        {"$project": {
                            "student_id": {"$toString": "$student_id"},
                            "application_id": 1,
                            "student_name": "$student_details.name"
                        }}
                    ],
                    "as": "application_details"
                }
            },
            {"$project": {"_id": 1, "booked_user": 1,
                          "start_time": 1, "end_time": 1,
                          "status": 1,
                          "application_details": 1,
                          "panelist_ids": 1, "slot_duration": 1,
                          "user_limit": 1}}
        ]
        result = DatabaseConfiguration().slot_collection.aggregate(pipeline)
        slot_documents = []
        async for document in result:
            if document.get("panelist_ids", []):
                document["panelist_details"] = await self.\
                    get_panelist_data(document.get("panelist_ids", []))
                document.pop("panelist_ids")
            start_time = utility_obj.get_local_time(
                document.get('start_time'), hour_minute=True)
            end_time = utility_obj.get_local_time(
                document.get('end_time'), hour_minute=True)
            document["time"] = f"{start_time} - {end_time}"
            for item in ["start_time", "end_time"]:
                if document.get(item):
                    document.pop(item)
            slot_documents.append(document)
        return slot_documents

    async def get_interview_applicants(
            self, application_ids: list, filter_slot_panel: None | dict,
            page_num: int | None, page_size: int | None,
            slot_type: str | None, interview_list: dict | None) -> tuple:
        """
        Get interview list eligible applicants` data.

        Params:
            application_ids (list): A list which contains application ids.
            filter_slot_panel (None | dict): Either or a dictionary which
                useful for get applicants data based on filters.
            page_num (int | None): Page number will be only useful for show
                applicants data. e.g., 1
            page_size (int | None):
                Page size means how many data you want to show on page_num.
                e.g., 25
            slot_type (str | None): Either None or type of slot.
                Possible values are GD and PI.
            interview_list (dict | None): Either None or a dictionary which
                interview list data.

        Returns:
            tuple: A tuple which contains interview applicants data along
                total count.
        """
        student_basic_stage = await self.name_project_stage()
        base_match = {"_id": {"$in": application_ids}, "meetingDetails.status":
                                       {"$ne": "Scheduled"}}
        if slot_type:
            if (selection_procedure := interview_list.get(
                    "selection_procedure")) is None:
                selection_procedure = {"gd_parameters_weightage": True,
                                       "pi_parameters_weightage": True}
            gd_parameters = selection_procedure.get("gd_parameters_weightage")
            pi_parameters = selection_procedure.get("pi_parameters_weightage")
            if gd_parameters and pi_parameters:
                if slot_type == "GD":
                    base_match.update({"gd_status.status": None})
                else:
                    base_match.update({f"gd_status.status": "Done"})
            elif gd_parameters:
                if slot_type == "GD":
                    base_match.update({"gd_status.status": None})
                else:
                    return [], 0
            else:
                if slot_type == "PI":
                    base_match.update({"pi_status.status": None})
                else:
                    return [], 0
        student_primary_match = {
            "$expr": {
                "$eq": ["$_id", "$$student_id"]
            }
        }
        if filter_slot_panel:
            name_query = filter_slot_panel.get("search_by_applicant")
            if name_query:
                name_pattern = f".*{name_query}.*"
                student_primary_match.update({"$or": [
                    {"basic_details.first_name": {"$regex": name_pattern,
                                                  "$options": "i"}},
                    {"basic_details.last_name": {"$regex": name_pattern,
                                                 "$options": "i"}}]})
        pipeline = [
            {"$match": base_match},
            {"$project": {"_id": 0, "application_id": {"$toString": "$_id"},
                          "student_id": 1, "course_id": 1,
                          "spec_name": "$spec_name1", "spec_name1": {
                    "$reduce": {
                        "input": {"$split": ["$spec_name1", " "]},
                        "initialValue": "",
                        "in": {"$concat": ["$$value",
                                           {"$substr": ["$$this", 0, 1]}]}
                    }}}},
            {
                "$lookup": {
                    "from": "studentsPrimaryDetails",
                    "let": {"student_id": "$student_id"},
                    "pipeline": [
                        {
                            "$match": student_primary_match
                        },
                        student_basic_stage,
                    ], "as": "student_details"
                }
            },
            {
                "$lookup": {
                    "from": "courses",
                    "let": {"course_id": "$course_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$in": ["$_id", ["$$course_id"]]
                                }
                            }
                        },
                        {"$project": {
                            "_id": 0,
                            "name": "$course_name"
                        }},
                    ], "as": "course_details"
                }
            },
            {
                "$lookup": {
                    "from": "studentSecondaryDetails",
                    "let": {"student_id": "$student_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": ["$student_id", "$$student_id"]
                                }
                            }
                        },
                        {"$project": {
                            "_id": 0,
                            "twelve_score":
                                {"$ifNull": [
                                    "$education_details.inter_school_details."
                                    "obtained_cgpa",
                                    "NA"]}
                        }},
                    ], "as": "student_secondary_details"
                }
            },
            {
                "$unwind": {
                    "path": "$student_details"}},
            {
                "$unwind": {
                    "path": "$course_details"}},
            {
                "$unwind": {
                    "path": "$student_secondary_details",
                    "preserveNullAndEmptyArrays": True}},
            {"$project": {"application_id": "$application_id",
                          "student_name": "$student_details.name",
                          "course_name": {
                              "$trim": {
                                  "input": {
                                      "$concat": [
                                          "$course_details.name",
                                          " ",
                                          "$spec_name1"
                                      ]
                                  }
                              }
                          },
                          "spec_name": "$spec_name",
                          "twelve_score":
                              {"$ifNull": ["$student_secondary_details."
                                           "twelve_score",
                                           "NA"]}
                          }}
        ]
        if filter_slot_panel:
            twelve_score_sort = filter_slot_panel.get("sort_by_twelve_marks")
            if twelve_score_sort is not None:
                order_decide = 1 if twelve_score_sort else -1
                pipeline.append({"$sort": {"twelve_score": order_decide}})
        final_data = []
        if page_num and page_size:
            skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                                  page_size)
            final_data.extend(
                [{"$skip": skip}, {"$limit": limit}])
        pipeline.append({
            "$facet": {
                "paginated_results": final_data,
                "totalCount": [{"$count": "count"}]
            }
        })
        result = DatabaseConfiguration().studentApplicationForms.aggregate(
            pipeline)
        data, total_data = [], 0
        async for documents in result:
            try:
                total_data = documents.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
            data = [document for document in documents.get("paginated_results")
                    ]
        return data, total_data

    async def get_panel_names(self, filters: dict | None) -> list:
        """
        Get panel names with/without filters.

        Params:
            filters (dict | None): A dictionary which contains filterable
                fields with their values.

        Returns:
            list: A list which contains panel names.
        """
        base_match = {}
        if filters:
            slot_type = filters.get('slot_type', "")
            interview_list_id = filters.get('interview_list_id')
            start_time = filters.get('start_time')
            end_time = filters.get('end_time')
            if slot_type:
                base_match.update(
                    {"slot_type": slot_type.upper()})
            if interview_list_id:
                await utility_obj.is_length_valid(
                    _id=interview_list_id, name="Interview list id")
                base_match.update(
                    {"interview_list_id": ObjectId(interview_list_id)})
            if start_time and end_time:
                start_time = await utility_obj.date_change_utc(start_time)
                end_time = await utility_obj.date_change_utc(end_time)
                base_match.update({
                    "time": {"$gte": start_time, "$lte": end_time}
                })
        pipeline = [
            {"$match": base_match},
            {"$sort": {"created_at": -1}},
            {"$project": {
                "_id": {"$toString": "$_id"},
                "name": "$name"
            }}
        ]
        result = DatabaseConfiguration().panel_collection.aggregate(pipeline)
        return [document async for document in result]
