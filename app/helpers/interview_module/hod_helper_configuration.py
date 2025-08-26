"""
This file contains class and functions related to interview list
"""
import datetime

from pymongo.errors import PyMongoError

from app.core.utils import logger, utility_obj
from app.database.configuration import DatabaseConfiguration


class hod_helper:
    """A class for interacting with the hod interview details functionality"""

    def __init__(self):
        """Initialize the custom variables"""
        self.active = "Active"
        self.closed = "Closed"
        self.selected = "Selected"
        self.rejected = "Rejected"
        self.pending = "Under Review"
        self.hold = "Hold"

    async def get_hod_header_interviews(self):
        """
        Get summary of interview applicants.

        Returns:
            data (dict): A dictionary which contains summary of interview applicants.
                e.g., {"interview_done": 0, "selected_candidate": 0,
                    "pending_for_review": 0, "rejected_candidate": 0}

        Raises:
            PyMongoError: Raises error when performing aggregation in db.
        """
        pipeline = [
            {
                "$group": {
                    "_id": "",
                    "interview_done": {"$sum": {"$cond": [
                        {"$in": [
                            "$interviewStatus.status",
                            [self.selected, self.rejected, "Shortlisted"]]},
                        1, 0]}},
                    "selected_candidate": {"$sum": {"$cond": [
                        {"$eq": [
                            "$approval_status",
                            self.selected]},
                        1, 0]}},
                    "pending_for_review": {"$sum": {"$cond": [
                        {"$eq": [
                            "$approval_status",
                            self.pending]},
                        1, 0]}},
                    "rejected_candidate": {"$sum": {"$cond": [
                        {"$eq": [
                            "$approval_status",
                            self.rejected]},
                        1, 0]}}
                }
            }
        ]
        try:
            result = DatabaseConfiguration().studentApplicationForms.aggregate(
                pipeline)
            async for data in result:
                return data
        except PyMongoError as error:
            logger.error(f"An error occurred while trying "
                         f"to execute the query: {error}")

    async def get_interview_list_count(self, archive: bool | None = None):
        """
            Get GD PI header interview list count details.
            params:
                archive (bool): Optional field. Default value: None.
             Useful value for get Archived interview lists when value is True.

            Returns:
                data (dict): A dictionary with total_interview_list,
                active_interview_list, close_interview_list fields.
        """
        pipeline_interview_list = [
            {
                "$group": {
                    "_id": {"interview_id": "$_id",
                            "eligible_applications": {
                                "$ifNull": ["$eligible_applications", []]}},
                    "total_interview_list": {"$sum": 1},
                    "active_interview_list": {"$sum": {"$cond": [
                        {"$eq": ["$status", self.active]}, 1, 0]}},
                    "close_interview_list": {"$sum": {"$cond": [
                        {"$eq": ["$status", self.closed]}, 1, 0]}}
                }
            },
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": {"application_id": "$_id.eligible_applications"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$in": ["$_id", "$$application_id"]
                                }
                            }
                        },
                        {
                            "$group": {
                                "_id": "",
                                "total_candidate_count": {
                                    "$sum": {"$cond": [
                                        {"approval_status": {"exists": True}},
                                        1,
                                        0]}},
                                "selected_candidate_count": {
                                    "$sum": {"$cond": [
                                        {"$eq": ["$approval_status",
                                                 self.selected]}, 1, 0]}},
                                "rejected_candidate_count": {
                                    "$sum": {"$cond": [
                                        {"$eq": ["$approval_status",
                                                 self.rejected]}, 1, 0]}},
                                "hold_candidate_count": {
                                    "$sum": {"$cond": [
                                        {"$eq": ["$approval_status",
                                                 self.hold]}, 1, 0]}},
                            }
                        }
                    ],
                    "as": "application_details"
                }
            },
            {
                "$unwind": {
                    "path": "$application_details",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$lookup": {
                    "from": "slots",
                    "let": {"interview_id": "$_id.interview_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "time": {"$gt": datetime.datetime.utcnow()},
                                "$expr": {
                                    "$eq": ["$interview_list_id",
                                            "$$interview_id"]
                                }
                            }
                        },
                        {
                            "$group": {
                                "_id": "",
                                "available_slot": {
                                    "$sum": {"$cond": [{"$eq": [
                                        "$available_slot", "Open"]}, 1, 0]}}
                            }
                        }
                    ],
                    "as": "slots_details"
                }
            },
            {
                "$unwind": {
                    "path": "$slots_details",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$group": {
                    "_id": "",
                    "total_interview_list": {"$sum": "$total_interview_list"},
                    "active_interview_list": {
                        "$sum": "$active_interview_list"},
                    "close_interview_list": {"$sum": "$close_interview_list"},
                    "total_candidate_count": {"$sum": "$application_details."
                                                      "total_candidate_count"},
                    "selected_candidate_count": {
                        "$sum": "$application_details."
                                "selected_candidate_count"},
                    "rejected_candidate_count": {
                        "$sum": "$application_details."
                                "rejected_candidate_count"},
                    "hold_candidate_count": {"$sum": "$application_details."
                                                     "hold_candidate_count"},
                    "slot_available": {"$sum": "$slots_details.available_slot"}
                }
            }
        ]
        if archive:
            pipeline_interview_list.insert(0,
                                           {"$match": {
                                               "status": "Archived"}})
        try:
            async for data in DatabaseConfiguration(
            ).interview_list_collection.aggregate(pipeline_interview_list):
                if data is None:
                    return {}
                return data
            return {}
        except Exception as e:
            logger.error(f"Failed to aggregate pipeline {e}")

    async def get_hod_header_data(self):
        """
        Get summary of interview applicants.

        Returns:
            dict: A dictionary which contains summary of interview applicants.
                e.g., {"interview_done": 0, "selected_candidate": 0,
                    "pending_for_review": 0, "rejected_candidate": 0}
        """
        return await self.get_hod_header_interviews()

    async def get_gd_pi_header_data(self, archive: bool | None = None):
        """
            Get GD PI header interview details.
            params:
             archive (bool): Optional field. Default value: None.
             Useful value for get Archived interview lists when value is True.

            Returns:
                data (dict): A dictionary which contains data.
        """
        interview_list = await self.get_interview_list_count(archive=archive)
        percentage_available_slot = utility_obj.get_percentage_result(
            interview_list.get("slot_available", 0), interview_list.get(
                "total_candidate_count", 0)
        )
        if len(interview_list) == 0:
            return {}
        interview_list.update(
            {"percentage_available_slot": percentage_available_slot})
        return interview_list
