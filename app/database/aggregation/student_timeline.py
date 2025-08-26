"""
This file contain class and methods for get student timeline information.
"""

from bson import ObjectId

from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.helpers.followup_queries.followup_notes_configuration import (
    FollowupNotesHelper,
)
from app.models.applications import DateRange


class StudentTimeline:
    """
    Contain functions related to student timeline
    """

    async def get_start_date_and_end_date(self, date_range: DateRange | None) -> tuple:
        """
        Get the start date and end date

        Params:
            date_range (DateRange | None): Either none or daterange which
                useful for filter data based on date_range.
                e.g., {"start_date": "2023-09-07",
                    "end_date": "2023-09-07"}

        Returns:
              tuple: A tuple which contains start date and end date.
        """
        date_range = await utility_obj.format_date_range(date_range)
        start_date, end_date = None, None
        if len(date_range) >= 2:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
        return start_date, end_date

    async def get_student_timeline(
        self,
        date_range: DateRange | None,
        student_id: ObjectId,
        action_user: list | None,
        student_name: str,
    ) -> tuple:
        """
        Get the student timeline with/without filter.

        Params:
            date_range (DateRange | None): Either none or daterange which
                useful for filter data based on date_range.
                e.g., {"start_date": "2023-09-07",
                    "end_date": "2023-09-07"}
            student_id (ObjectId): A unique id of a student.
                e.g., ObjectId("123456789012345678901234")
            action_type (list | None): Either none or list which contains
                action user type. e.g., ["counselor", "user"]
            student_name (str): Name of a student. e.g., test

        Returns:
            tuple: A tuple which contains timeline list and query list.
        """
        start_date, end_date = await self.get_start_date_and_end_date(date_range)
        pipeline = [
            {"$match": {"student_id": student_id}},
            {"$unwind": {"path": "$timelines"}},
            {"$sort": {"timelines.timestamp": -1}},
        ]
        if start_date and end_date:
            pipeline.append(
                {
                    "$match": {
                        "timelines.timestamp": {"$gte": start_date, "$lte": end_date}
                    }
                }
            )
        if action_user is None:
            action_user = []
        result = DatabaseConfiguration().studentTimeline.aggregate(pipeline)
        timelines, query_list, gap_between_timeline, prev_date = [], [], 0, None
        async for document in result:
            item = document.get("timelines", {})
            temp_timestamp = (
                await utility_obj.date_change_utc(
                    item.get("timestamp"), date_format="%d %b %Y %I:%M:%S %p"
                )
                if type(item.get("timestamp")) == str
                else item.get("timestamp")
            )
            if prev_date is not None:
                days_gap = abs(temp_timestamp - prev_date)
                gap_between_timeline = days_gap.days
                timelines[-1].update({"gap_bet_timeline": gap_between_timeline})
            event_type = item.get("event_type")
            if event_type == "Payment":
                if action_user != [] and "user" not in action_user:
                    continue
                if not item.get("message"):
                    message = (
                        f"{student_name}"
                        f" {item.get('event_status')} {event_type}"
                        f" of Application Name: {item.get('event_name')}"
                    )
                else:
                    message = item.get("message")
                action_type = "user"
            elif event_type == "Query":
                if not item.get("message"):
                    user = await DatabaseConfiguration().user_collection.find_one(
                        {"_id": ObjectId(item.get("user_id"))}
                    )
                    action_type = (
                        "counselor"
                        if user
                           and user.get("role", {}).get(
                            "role_name") == "college_counselor"
                        else "system"
                    )
                    if action_user != [] and action_type not in action_user:
                        continue
                    if not item.get("message"):
                        message = item.get('event_status')
                    else:
                        message = item.get("message")
                else:
                    if action_user != [] and "user" not in action_user:
                        continue
                    if not item.get("message"):
                        message = item.get('event_status')
                    else:
                        message = item.get("message")
                    action_type = "user"
                query_list.append(
                    {
                        "timeline_type": event_type,
                        "action_type": action_type,
                        "gap_bet_timeline": gap_between_timeline,
                        "template_id": item.get("template_id"),
                        "template_type": item.get("template_type"),
                        "template_name": item.get("template_name"),
                        "message": message,
                        "timestamp": (
                            item.get("timestamp")
                            if type(item.get("timestamp")) == str
                            else utility_obj.get_local_time(item.get("timestamp"))
                        ),
                        "MessageID": item.get("MessageID"),
                        "student_id": str(student_id)
                    }
                )
            else:
                if str(item.get("event_status")).startswith("Allocated Counselor"):
                    if action_user != [] and "system" not in action_user:
                        continue
                    if not item.get("message"):
                        message = f"{item.get('event_status')} to {event_type} whose application name: {item.get('event_name')}"
                    else:
                        message = item.get("message")
                    action_type = "system"
                elif str(item.get("event_status")).startswith("Lead stage"):
                    if (
                        user := await DatabaseConfiguration().user_collection.find_one(
                            {"_id": ObjectId(item.get("user_id"))}
                        )
                    ) is not None:
                        action_type = (
                            "counselor"
                            if user.get("role", {}).get("role_name")
                            == "college_counselor"
                            else "system"
                        )
                    else:
                        action_type = "system"
                    if action_user != [] and action_type not in action_user:
                        continue
                    if not item.get("message"):
                        message = f"{item.get('event_status')}"
                    else:
                        message = item.get("message")
                else:
                    if action_user != [] and "user" not in action_user:
                        continue
                    if not item.get("message"):
                        message = f"{student_name} has {item.get('event_status')} {event_type} for application name: {item.get('event_name')}"
                    else:
                        message = item.get("message")
                    action_type = "user"
            timelines.append(
                {
                    "timeline_type": event_type,
                    "action_type": action_type,
                    "message": message,
                    "template_id": item.get("template_id"),
                    "template_type": item.get("template_type"),
                    "template_name": item.get("template_name"),
                    "timestamp": (
                        item.get("timestamp")
                        if type(item.get("timestamp")) == str
                        else utility_obj.get_local_time(item.get("timestamp"))
                    ),
                    "MessageID": item.get("MessageID"),
                    "student_id": str(student_id)
                }
            )
            prev_date = (
                await utility_obj.date_change_utc(
                    item.get("timestamp"), date_format="%d %b %Y %I:%M:%S %p"
                )
                if type(item.get("timestamp")) == str
                else item.get("timestamp")
            )
        return timelines, query_list

    async def get_followup_notes_timeline(
        self,
        date_range: DateRange | None,
        application_id: ObjectId,
        action_user: list | None,
        student_name: str,
    ) -> tuple:
        """
        Get the student timeline with/without filter.

        Params:
            date_range (DateRange | None): Either none or daterange which
                useful for filter data based on date_range.
                e.g., {"start_date": "2023-09-07",
                    "end_date": "2023-09-07"}
            application_id (ObjectId): A unique id of an application.
                e.g., ObjectId("123456789012345678901234")
            action_type (list | None): Either none or list which contains
                action user type. e.g., ["counselor", "user"]
            student_name (str): Name of a student. e.g., test

        Returns:
            tuple: A tuple which contains followup and notes timeline lists.
        """
        start_date, end_date = await self.get_start_date_and_end_date(date_range)
        if action_user is None:
            action_user = []
        pipeline = [
            {"$match": {"application_id": application_id}},
            {
                "$project": {
                    "record_list": {
                        "$concatArrays": [
                            {"$ifNull": ["$followup", []]},
                            {"$ifNull": ["$notes", []]},
                        ]
                    }
                }
            },
            {"$unwind": {"path": "$record_list"}},
            {"$sort": {"record_list.timestamp": -1}},
        ]
        if start_date and end_date:
            pipeline.append(
                {
                    "$match": {
                        "record_list.timestamp": {"$gte": start_date, "$lte": end_date}
                    }
                }
            )
        result = DatabaseConfiguration().leadsFollowUp.aggregate(pipeline)
        (
            followups,
            notes,
            count,
            prev_followup_date,
            prev_note_date,
            followup_gap_bet_timeline,
            note_gap_bet_timeline,
        ) = ([], [], 0, None, None, 0, 0)
        async for document in result:
            record_list = document.get("record_list", {})
            user_id = record_list.get("user_id")
            user = await DatabaseConfiguration().user_collection.find_one(
                {"_id": user_id}
            )
            action_type = (
                "counselor"
                if user.get("role", {}).get("role_name") == "college_counselor"
                else "system"
            )
            if action_user != [] and action_type not in action_user:
                continue
            temp_data = {"action_type": action_type}
            if record_list.get("followup_date"):
                temp_followup_timestamp = record_list.get("timestamp")
                if prev_followup_date is not None:
                    days_gap = abs(temp_followup_timestamp - prev_followup_date)
                    followup_gap_bet_timeline = days_gap.days
                    followups[-1].update(
                        {"gap_bet_timeline": followup_gap_bet_timeline}
                    )
                temp_data.update(
                    FollowupNotesHelper().timeline_followup_helper(
                        record_list, student_name
                    )
                )
                temp_data.update({"index_number": count})
                followups.append(temp_data)
                count += 1
                prev_followup_date = record_list.get("timestamp")
            else:
                temp_note_timestamp = record_list.get("timestamp")
                if prev_note_date is not None:
                    days_gap = abs(temp_note_timestamp - prev_note_date)
                    note_gap_bet_timeline = days_gap.days
                    notes[-1].update({"gap_bet_timeline": note_gap_bet_timeline})
                temp_data.update(
                    FollowupNotesHelper().timeline_notes_helper(record_list)
                )
                notes.append(temp_data)
                prev_note_date = record_list.get("timestamp")
        return followups, notes
