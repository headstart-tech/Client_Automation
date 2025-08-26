"""
This file contains class and functions related to interview list
"""

from datetime import timedelta, datetime

from bson import ObjectId
from fastapi import Request
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError
from pymongo.errors import PyMongoError

from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.custom_error import DataNotFoundError, UserLimitExceeded
from app.core.utils import logger, utility_obj, settings
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import is_testing_env
from app.helpers.interview_module.planner_configuration import Planner
from app.s3_events.s3_events_configuration import upload_csv_and_get_public_url


class Interview_list_details:
    """Gets the interview list details for a given user"""

    def __init__(self):
        self.GD = "GD"
        self.PI = "PI"
        self.done = "Done"
        self.selected = "Selected"
        self.rejected = "Rejected"

    async def _get_interview_list_header_detail(self, _id):
        """
        Get interview list header details.

        Params:
            _id: _id contains an interview list id in string format.

        Returns:
            data (list): A List which contains data.
        """
        pipeline = [
            {"$match": {"_id": ObjectId(_id)}},
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": {
                        "application_id": {"$ifNull": ["$eligible_applications", []]}
                    },
                    "pipeline": [
                        {"$match": {"$expr": {"$in": ["$_id", "$$application_id"]}}},
                        {
                            "$project": {
                                "_id": 1,
                                "student_id": 1,
                                "custom_application_id": 1,
                                "interviewStatus": 1,
                                "meetingDetails": 1,
                                "gd_status": 1,
                                "pi_status": 1,
                            }
                        },
                    ],
                    "as": "application_details",
                }
            },
            {
                "$unwind": {
                    "path": "$application_details",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            {
                "$group": {
                    "_id": {
                        "interview_id": "$_id",
                        "course_name": "$course_name",
                        "specialization_name": "$specialization_name",
                        "list_name": "$list_name",
                        "created_at": "$created_at",
                        "application_ids": "$application_ids",
                        "eligible_application": "$eligible_applications",
                        "slot_type": [
                            {
                                "$cond": [
                                    {
                                        "$ifNull": [
                                            "$selection_procedure"
                                            ".gd_parameters_weightage",
                                            False,
                                        ]
                                    },
                                    "GD",
                                    None,
                                ]
                            },
                            {
                                "$cond": [
                                    {
                                        "$ifNull": [
                                            "$selection_procedure"
                                            ".pi_parameters_weightage",
                                            False,
                                        ]
                                    },
                                    "PI",
                                    None,
                                ]
                            },
                        ],
                    },
                    "total_gd_count": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$application_details.gd_status.status",
                                        "Done",
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "completed_gd": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$application_details.gd_status.interview_result",
                                        self.selected,
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "total_pi_count": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$application_details.pi_status.status",
                                        "Done",
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "completed_pi": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$application_details.pi_status.interview_result",
                                        self.selected,
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "interview_id": {"$toString": "$_id.interview_id"},
                    "course_name": "$_id.course_name",
                    "specialization_name": "$_id.specialization_name",
                    "list_name": "$_id.list_name",
                    "created_at": {
                        "$dateToString": {
                            "format": "%Y-%m-%d %H:%M:%S",
                            "date": "$_id.created_at",
                            "timezone": "Asia/Kolkata",
                        }
                    },
                    "total_application_ids": {
                        "$cond": {
                            "if": {"$isArray": "$_id" ".application_ids"},
                            "then": {"$size": "$_id.application_ids"},
                            "else": "NA",
                        }
                    },
                    "total_eligible_ids": {
                        "$cond": {
                            "if": {"$isArray": "$_id." "eligible_application"},
                            "then": {"$size": "$_id." "eligible_application"},
                            "else": "NA",
                        }
                    },
                    "total_gd_count": "$total_gd_count",
                    "completed_gd": "$completed_gd",
                    "total_pi_count": "$total_pi_count",
                    "completed_pi": "$completed_pi",
                    "is_gd_eligible": {
                        "$cond": [{"$in": [self.GD, "$_id.slot_type"]}, True, False]
                    },
                    "is_pi_eligible": {
                        "$cond": [{"$in": [self.PI, "$_id.slot_type"]}, True, False]
                    },
                }
            },
        ]
        try:
            return [
                data
                async for data in DatabaseConfiguration().interview_list_collection.aggregate(
                    pipeline
                )
            ]
        except PyMongoError as error:
            logger.error(
                f"An error occurred while trying " f"to execute the query: {error}"
            )

    async def _download_interview_view_data(self, _id):
        """
        Download the data of application interview list details.

        Params:
            _id: _id contains an application list id in string format.

        Returns:
            data (list): A List which contains data.
        """
        pipeline = [
            {"$match": {"_id": {"$in": _id}}},
            {
                "$project": {
                    "_id": 1,
                    "student_id": 1,
                    "custom_application_id": 1,
                    "interviewStatus": 1,
                    "meetingDetails": 1,
                }
            },
            {
                "$lookup": {
                    "from": "studentsPrimaryDetails",
                    "let": {"student_id": "$student_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$student_id"]}}},
                        {
                            "$project": {
                                "_id": 0,
                                "user_name": 1,
                                "basic_details": 1,
                            }
                        },
                    ],
                    "as": "student_details",
                }
            },
            {"$unwind": {"path": "$student_details"}},
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "email_id": "$student_details.user_name",
                    "student_name": {
                        "$trim": {
                            "input": {
                                "$concat": [
                                    "$student_details.basic_details" ".first_name",
                                    " ",
                                    "$student_details.basic_details" ".middle_name",
                                    " ",
                                    "$student_details.basic_details" ".last_name",
                                ]
                            }
                        }
                    },
                    "mobile_number": "$student_details.basic_details.mobile_number",
                    "custom_application_id": "$custom_application_id",
                    "gd_status": {
                        "$ifNull": ["$meetingDetails.slot_type", "Slot Not Booked "]
                    },
                    "interview_status": {
                        "$ifNull": ["$meetingDetails.slot_status", "Slot Not Booked "]
                    },
                    "selection_status": {
                        "$ifNull": ["$interviewStatus.status", "Slot Not Booked "]
                    },
                }
            },
        ]
        try:
            return [
                data
                async for data in DatabaseConfiguration().studentApplicationForms.aggregate(
                    pipeline
                )
            ]
        except PyMongoError as error:
            logger.error(
                f"An error occurred while trying " f"to execute the query: {error}"
            )

    async def _get_interview_view_data(self, _id, payload, skip, limit):
        """
        Get the data of interview list details.

        Params:
            _id: _id contains an interview list id in string format.
            payload (dict): The data of the dict filtered
            page_num (int): The number of page to retrieve the data
            page_size (int): The size of page to retrieve the data

        Returns:
            data (list): A List which contains data.
        """
        pipeline = [
            {"$match": {"_id": ObjectId(_id)}},
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": {"application_id": "$eligible_applications"},
                    "pipeline": [
                        {"$match": {"$expr": {"$in": ["$_id", "$$application_id"]}}},
                        {
                            "$project": {
                                "_id": 1,
                                "student_id": 1,
                                "custom_application_id": 1,
                                "interviewStatus": 1,
                                "meetingDetails": 1,
                                "approval_status": 1,
                                "gd_status": 1,
                                "pi_status": 1,
                            }
                        },
                    ],
                    "as": "application_details",
                }
            },
            {"$unwind": {"path": "$application_details"}},
            {
                "$lookup": {
                    "from": "studentsPrimaryDetails",
                    "let": {"student_id": "$application_details.student_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$$student_id", "$_id"]}}},
                        {
                            "$project": {
                                "_id": 0,
                                "user_name": 1,
                                "basic_details": 1,
                            }
                        },
                    ],
                    "as": "student_details",
                }
            },
            {"$unwind": {"path": "$student_details"}},
            {
                "$addFields": {
                    "selection_producer": {
                        "pi_interview": {
                            "$cond": [
                                {
                                    "$ifNull": [
                                        "$selection_procedure"
                                        ".pi_parameters_weightage",
                                        False,
                                    ]
                                },
                                "PI",
                                None,
                            ]
                        },
                        "gd_interview": {
                            "$cond": [
                                {
                                    "$ifNull": [
                                        "$selection_procedure"
                                        ".gd_parameters_weightage",
                                        False,
                                    ]
                                },
                                "GD",
                                None,
                            ]
                        },
                    }
                }
            },
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "application_id": {"$toString": "$application_details._id"},
                    "email_id": "$student_details.user_name",
                    "student_name": {
                        "$trim": {
                            "input": {
                                "$concat": [
                                    "$student_details.basic_details" ".first_name",
                                    " ",
                                    "$student_details.basic_details" ".middle_name",
                                    " ",
                                    "$student_details.basic_details" ".last_name",
                                ]
                            }
                        }
                    },
                    "mobile_number": "$student_details.basic_details.mobile_number",
                    "custom_application_id": "$application_details.custom_application_id",
                    "gd_status": {
                        "$cond": {
                            "if": {"$ne": ["$selection_producer.gd_interview", "GD"]},
                            "then": {
                                "$cond": {
                                    "if": {
                                        "$eq": [
                                            "$selection_producer" ".pi_interview",
                                            "PI",
                                        ]
                                    },
                                    "then": "$gd",
                                    "else": {
                                        "$cond": {
                                            "if": {
                                                "$eq": [
                                                    "$application_details."
                                                    "gd_status.status",
                                                    "Done",
                                                ]
                                            },
                                            "then": "Done",
                                            "else": {
                                                "$cond": {
                                                    "if": {
                                                        "$and": [
                                                            {
                                                                "$eq": [
                                                                    "$application_details"
                                                                    ".meetingDetails"
                                                                    ".slot_status",
                                                                    "Done",
                                                                ]
                                                            },
                                                            {
                                                                "$eq": [
                                                                    "$application_details"
                                                                    ".meetingDetails"
                                                                    ".slot_type",
                                                                    "GD",
                                                                ]
                                                            },
                                                        ]
                                                    },
                                                    "then": "Done",
                                                    "else": {
                                                        "$cond": {
                                                            "if": {
                                                                "$eq": [
                                                                    "$application_details"
                                                                    ".meetingDetails"
                                                                    ".slot_type",
                                                                    "GD",
                                                                ]
                                                            },
                                                            "then": "$application_details"
                                                            ".meetingDetails"
                                                            ".slot_status",
                                                            "else": "Slot Not Booked",
                                                        }
                                                    },
                                                }
                                            },
                                        }
                                    },
                                }
                            },
                            "else": {
                                "$cond": {
                                    "if": {
                                        "$eq": [
                                            "$application_details." "gd_status.status",
                                            "Done",
                                        ]
                                    },
                                    "then": "Done",
                                    "else": {
                                        "$cond": {
                                            "if": {
                                                "$and": [
                                                    {
                                                        "$eq": [
                                                            "$application_details"
                                                            ".meetingDetails"
                                                            ".slot_status",
                                                            "Done",
                                                        ]
                                                    },
                                                    {
                                                        "$eq": [
                                                            "$application_details"
                                                            ".meetingDetails"
                                                            ".slot_type",
                                                            "GD",
                                                        ]
                                                    },
                                                ]
                                            },
                                            "then": "Done",
                                            "else": {
                                                "$cond": {
                                                    "if": {
                                                        "$eq": [
                                                            "$application_details"
                                                            ".meetingDetails"
                                                            ".slot_type",
                                                            "GD",
                                                        ]
                                                    },
                                                    "then": "$application_details"
                                                    ".meetingDetails"
                                                    ".slot_status",
                                                    "else": "Slot Not Booked",
                                                }
                                            },
                                        }
                                    },
                                }
                            },
                        }
                    },
                    "pi_status": {
                        "$cond": {
                            "if": {"$ne": ["$selection_producer.pi_interview", "PI"]},
                            "then": {
                                "$cond": {
                                    "if": {
                                        "$eq": [
                                            "$selection_producer" ".gd_interview",
                                            "GD",
                                        ]
                                    },
                                    "then": "$pi",
                                    "else": {
                                        "$cond": {
                                            "if": {
                                                "$eq": [
                                                    "$application_details"
                                                    ".pi_status.status",
                                                    "Done",
                                                ]
                                            },
                                            "then": "Done",
                                            "else": {
                                                "$cond": {
                                                    "if": {
                                                        "$and": [
                                                            {
                                                                "$eq": [
                                                                    "$application_details"
                                                                    ".meetingDetails"
                                                                    ".slot_status",
                                                                    "Done",
                                                                ]
                                                            },
                                                            {
                                                                "$eq": [
                                                                    "$application_details"
                                                                    ".meetingDetails"
                                                                    ".slot_type",
                                                                    "PI",
                                                                ]
                                                            },
                                                        ]
                                                    },
                                                    "then": "Done",
                                                    "else": {
                                                        "$cond": {
                                                            "if": {
                                                                "$eq": [
                                                                    "$application_details"
                                                                    ".meetingDetails"
                                                                    ".slot_type",
                                                                    "PI",
                                                                ]
                                                            },
                                                            "then": "$application_details"
                                                            ".meetingDetails"
                                                            ".slot_status",
                                                            "else": "Slot Not Booked",
                                                        }
                                                    },
                                                }
                                            },
                                        }
                                    },
                                }
                            },
                            "else": {
                                "$cond": {
                                    "if": {
                                        "$eq": [
                                            "$application_details" ".pi_status.status",
                                            "Done",
                                        ]
                                    },
                                    "then": "Done",
                                    "else": {
                                        "$cond": {
                                            "if": {
                                                "$and": [
                                                    {
                                                        "$eq": [
                                                            "$application_details"
                                                            ".meetingDetails"
                                                            ".slot_status",
                                                            "Done",
                                                        ]
                                                    },
                                                    {
                                                        "$eq": [
                                                            "$application_details"
                                                            ".meetingDetails"
                                                            ".slot_type",
                                                            "PI",
                                                        ]
                                                    },
                                                ]
                                            },
                                            "then": "Done",
                                            "else": {
                                                "$cond": {
                                                    "if": {
                                                        "$eq": [
                                                            "$application_details"
                                                            ".meetingDetails"
                                                            ".slot_type",
                                                            "PI",
                                                        ]
                                                    },
                                                    "then": "$application_details"
                                                    ".meetingDetails"
                                                    ".slot_status",
                                                    "else": "Slot Not Booked",
                                                }
                                            },
                                        }
                                    },
                                }
                            },
                        }
                    },
                    "interview_status": {
                        "$cond": {
                            "if": {
                                "$ifNull": [
                                    "$application_details.interviewStatus.status",
                                    False,
                                ]
                            },
                            "then": {
                                "$cond": {
                                    "if": {
                                        "$in": [
                                            "$application_details.interviewStatus"
                                            ".status",
                                            [
                                                "Selected",
                                                "Shortlisted",
                                                "Rejected",
                                                "Accepted",
                                            ],
                                        ]
                                    },
                                    "then": "Done",
                                    "else": "$application_details"
                                    ".interviewStatus.status",
                                }
                            },
                            "else": "Slot Not Booked",
                        }
                    },
                    "selection_status": {
                        "$ifNull": [
                            "$application_details.approval_status",
                            "Slot Not Booked",
                        ]
                    },
                }
            },
            {
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            },
        ]
        temp_pipeline = (
            pipeline[1].get("$lookup", {}).get("pipeline", [{}])[0].get("$match", {})
        )
        if payload.get("interview_status") is not None:
            pipeline.insert(
                7,
                {
                    "$match": {
                        "interview_status": payload.get("interview_status").title()
                    }
                },
            )
        if payload.get("selection_status") not in ["", None]:
            temp_pipeline.update(
                {"approval_status": payload.get("selection_status").title()}
            )
        match = {"$match": {}}
        if payload.get("gd_status") not in ["", None]:
            match.get("$match", {}).update(
                {"gd_status": payload.get("gd_status").title()}
            )
        if payload.get("pi_status") is not None:
            match.get("$match", {}).update(
                {"pi_status": payload.get("pi_status").title()}
            )
        if payload.get("gd_status") not in ["", None] or payload.get(
            "pi_status"
        ) not in ["", None]:
            pipeline.insert(7, match)
        result = DatabaseConfiguration().interview_list_collection.aggregate(pipeline)
        async for data in result:
            try:
                total = data.get("totalCount", [{}])[0].get("count")
            except IndexError:
                total = 0
            except Exception:
                total = 0
            return data.get("paginated_results"), total

    async def get_view_interview_list_detail(self, _id, payload, page_num, page_size):
        """
        Get the data of interview list details.

        Params:
            _id: _id contains an interview list id in string format.
            payload (dict): The data containing the dict with filtered
            page_num (int): The number of page to retrieve the data
            page_size (int): The size of page to retrieve the data

         Returns:
            data (list): A list which contains data.
        """
        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
        if (
            interview_list_doc := await DatabaseConfiguration().interview_list_collection.find_one(
                {"_id": ObjectId(_id)}
            )
        ) is None:
            raise DataNotFoundError(_id, "Interview list")
        if interview_list_doc.get("application_ids") is None:
            raise DataNotFoundError("Interview list applicants")
        interview_list_data, total = await self._get_interview_view_data(
            _id, payload, skip, limit
        )
        response = await utility_obj.pagination_in_aggregation(
            skip, limit, total, route_name="/interview/view_interview_detail/"
        )
        return {
            "data": interview_list_data,
            "total": total,
            "count": limit,
            "pagination": response["pagination"],
            "message": "data fetch successfully",
        }

    async def download_view_interview_list_detail(self, _id):
        """
        Get the data of application based interview details.

        Params:
            _id: _id contains an application list id in string format.

        Returns:
            data (list): A list which contains data.
        """
        interview_header = await self._download_interview_view_data(_id)
        if interview_header:
            data_keys = list(interview_header[0].keys())
            get_url = await upload_csv_and_get_public_url(
                fieldnames=data_keys, data=interview_header, name="counselors_data"
            )
        else:
            raise DataNotFoundError
        return get_url

    async def get_interview_list_header_detail(self, _id):
        """
        Get the data of interview list details.

        Params:
            _id: _id contains an interview list id in string format.

        Returns:
            data (list): A list which contains data.
        """
        if (
            interview_list_doc := await DatabaseConfiguration().interview_list_collection.find_one(
                {"_id": ObjectId(_id)}
            )
        ) is None:
            raise DataNotFoundError(_id, "Interview list")
        return await self._get_interview_list_header_detail(_id)

    async def validate_reschedule_data(self, slot_id=None, application_id=None):
        """
        Get the details of slot, application and interview list

        params:
            slot_id (str): I'd of the slot to retrieve the details
            application_id (str): I'd of the application to retrieve the
            details
        returns:
            dict: the details of the slot, application and interview list
        """
        if (
            slot := await DatabaseConfiguration().slot_collection.find_one(
                {"_id": ObjectId(slot_id)}
            )
        ) is None:
            raise DataNotFoundError(slot_id, "Slot")
        if (
            application := await DatabaseConfiguration().studentApplicationForms.find_one(
                {"_id": ObjectId(application_id)}
            )
        ) is None:
            raise DataNotFoundError(application_id, "Application")
        if (
            interview := await DatabaseConfiguration().interview_list_collection.find_one(
                {"_id": ObjectId(slot.get("interview_list_id"))}
            )
        ) is None:
            raise DataNotFoundError(
                str(slot.get("interview_list_id")), "Interview list"
            )
        return application, interview, slot

    async def get_rescheduled_interview_list(
        self, origin_slot_id: str, reschedule_slot_id: str, application_id: str
    ):
        """
        Interview rescheduled of application with slot

        params:
        - slot_id (str): unique identifier of the slot id
        - reschedule_slot_id (str): unique identifier of the slot_id
        - application_id (str): unique identifier of the application id

        returns:
            Response-> Interview has been rescheduled
        """
        application, interview, slot = await self.validate_reschedule_data(
            slot_id=origin_slot_id, application_id=application_id
        )
        if (
            reschedule_slot := await DatabaseConfiguration().slot_collection.find_one(
                {"_id": ObjectId(reschedule_slot_id)}
            )
        ) is None:
            raise DataNotFoundError(reschedule_slot_id, "requested_slot_id")
        if (
            reschedule_interview := await DatabaseConfiguration().interview_list_collection.find_one(
                {"_id": ObjectId(reschedule_slot.get("interview_list_id"))}
            )
        ) is None:
            raise DataNotFoundError(
                reschedule_slot.get("interview_list_id"), "interview_list"
            )
        take_slot = slot.get("take_slot", {}).get("application_ids", [])
        origin_slot = [str(_id) for _id in take_slot]
        if len(origin_slot) == 0:
            raise DataNotFoundError(origin_slot_id, message="Application")
        elif str(application_id) not in origin_slot:
            raise DataNotFoundError(origin_slot_id, message="Applications")
        elif application_id in origin_slot:
            origin_slot.remove(application_id)
            take_slot = [ObjectId(_id) for _id in origin_slot]
        await DatabaseConfiguration().slot_collection.update_one(
            {"_id": ObjectId(origin_slot_id)},
            {"$set": {"take_slot.application_ids": take_slot}},
        )
        reschedule_take_slot = reschedule_slot.get("take_slot", {}).get(
            "application_ids", []
        )
        if reschedule_take_slot:
            if len(reschedule_take_slot) >= reschedule_slot.get("user_limit"):
                raise UserLimitExceeded()
            reschedule_take_slot.append(ObjectId(application_id))
            reschedule_take_slot = list(set(reschedule_take_slot))
        else:
            reschedule_take_slot = [ObjectId(application_id)]
        interview_list = application.get("interview_list_id", [])
        interview_list.append(reschedule_slot.get("interview_list_id"))
        interview_reschedule = list(set(interview_list))
        if slot.get("interview_list_id") in interview_reschedule:
            interview_reschedule.remove(ObjectId(slot.get("interview_list_id")))
        await DatabaseConfiguration().studentApplicationForms.update_one(
            {"_id": ObjectId(application_id)},
            {"$set": {"interview_list_id": interview_reschedule}},
        )
        await DatabaseConfiguration().slot_collection.update_one(
            {"_id": ObjectId(ObjectId(reschedule_slot_id))},
            {"$set": {"take_slot.application_ids": reschedule_take_slot}},
        )
        application_ids = interview.get("application_ids", [])
        if ObjectId(application_id) in application_ids:
            application_ids.remove(ObjectId(application_id))
        eligible = interview.get("eligible_applications", [])
        if ObjectId(application_id) in eligible:
            eligible.remove(ObjectId(application_id))
        reschedule_application_ids = reschedule_interview.get("application_ids", [])
        reschedule_eligible = reschedule_interview.get("eligible_applications", [])
        reschedule_application_ids.append(ObjectId(application_id))
        reschedule_eligible.append(ObjectId(application_id))
        await DatabaseConfiguration().interview_list_collection.update_one(
            {"_id": ObjectId(slot.get("interview_list_id"))},
            {
                "$set": {
                    "application_ids": list(set(application_ids)),
                    "eligible_applications": list(set(eligible)),
                }
            },
        )
        await DatabaseConfiguration().interview_list_collection.update_one(
            {"_id": ObjectId(reschedule_slot.get("interview_list_id"))},
            {
                "$set": {
                    "application_ids": list(set(reschedule_application_ids)),
                    "eligible_applications": list(set(reschedule_eligible)),
                }
            },
        )
        try:
            toml_data = utility_obj.read_current_toml_file()
            if toml_data.get("testing", {}).get("test") is False:
                student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(application.get("student_id"))}
                )
                # TODO: Not able to add student timeline data
                #  using celery task when environment is
                #  demo. We'll remove the condition when
                #  celery work fine.
                if settings.environment in ["demo"]:
                    StudentActivity().student_timeline(
                        student_id=str(student.get("_id")),
                        event_type="Interview",
                        event_status="Rescheduled",
                        message=f"{utility_obj.name_can(student.get('basic_details', {}))} has raised a request to reschedule the Interview Slot.",
                        college_id=str(student.get("college_id")),
                    )
                else:
                    if not is_testing_env():
                        StudentActivity().student_timeline.delay(
                            student_id=str(student.get("_id")),
                            event_type="Interview",
                            event_status="Rescheduled",
                            message=f"{utility_obj.name_can(student.get('basic_details', {}))} has raised a request to reschedule the Interview Slot.",
                            college_id=str(student.get("college_id")),
                        )
        except KombuError as celery_error:
            logger.error(f"error rescheduling the interview" f"{celery_error}")
        except Exception as error:
            logger.error(f"error rescheduling the interview {error}")
        return {"message": "Interview has been rescheduled"}

    async def get_assign_application(
        self,
        slot_data: dict,
        current_user: str,
        college: dict,
        request: Request,
        application_id: str | None,
        panelist_id: str | None,
        action_type="system",
    ):
        """
        Assign applicant/panelist to the slot. After assign slot user will get
        interview details through mail.

        Params:
            - slot_data (dict): A dictionary which contains slot data.
            - current_user (str): User email of logged-in user.
            - college (dict): A dictionary which contains college data.
            - request (Request): Useful for get ip_address of client.
            - background_tasks (BackgroundTasks): Useful for perform tasks in
                the background.
            - application_id (str | None): Either None or a unique identifier
                of application. e.g., 123456789012345678901222
            - panelist_id (str | None): Either None or a unique identifier of
                panelist. e.g., 123456789012345678901233

        Returns:
            dict: A dictionary which contains information about slot assigned
                to user.
        """
        if panelist_id is not None:
            if (
                user := await DatabaseConfiguration().user_collection.find_one(
                    {"_id": ObjectId(panelist_id), "role.role_name": "panelist"}
                )
            ) is None:
                raise DataNotFoundError(panelist_id, "Panelist")
            user_type = "panelist"
            is_student = False
        else:
            if (
                application := await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"_id": ObjectId(application_id)}
                )
            ) is None:
                raise DataNotFoundError(application_id, "Application")
            if (
                user := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": application.get("student_id")}
                )
            ) is None:
                student_id = str(application.get("student_id"))
                raise DataNotFoundError(student_id, "Student")
            user_type = "application"
            is_student = True
        assign_slot_resp = await Planner().assign_take_slot(
            slot_data,
            user,
            user_type,
            application_id,
            is_student,
            college,
            request,
            current_user,
            assign=True,
            action_type=action_type,
        )
        if assign_slot_resp:
            return assign_slot_resp
        return {"message": f"Assigned the {user_type} to the slot"}

    async def get_unassign_data(self, application_id: str, panelist_id: str) -> tuple:
        """
        Get the un-assign data.

        Params:
            application_id (str): A unique identifier/id of an application.
            panelist_id (str): A unique identifier/id of a panelist.

        Returns:
              tuple: A tuple which contains user id, type of user and email of
               user.
        """
        if application_id:
            _id = ObjectId(application_id)
            if (
                application := await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"_id": _id}
                )
            ) is None:
                raise DataNotFoundError(application_id, "Application")
            user_type = "application"
            if (
                student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": application.get("student_id")}
                )
            ) is None:
                student = {}
            email = student.get("user_name")
        else:
            _id = ObjectId(panelist_id)
            if (
                user := await DatabaseConfiguration().user_collection.find_one(
                    {"_id": _id, "role.role_name": "panelist"}
                )
            ) is None:
                raise DataNotFoundError(panelist_id, "Panelist")
            user_type = "panelist"
            email = user.get("user_name")
        return _id, user_type, email

    async def unassigned_applicant_from_slot(
        self,
        application_id: str | None,
        panelist_id: str | None,
        slot_id: str,
        college: dict,
        user: dict,
        request: Request,
    ) -> dict:
        """
        Unassigned/Remove applicant/panelist from a slot.

        Params:
            application_id (str): A unique identifier/id of
                an application. e.g., 123456789012345678901234
            panelist_id (str): A unique identifier/id of
                an panelist. e.g., 123456789012345678901233
            slot_id (str): A unique identifier/id of
                a slot. e.g., 123456789012345678901232
            background_tasks (BackgroundTasks): Useful for perform tasks in
                the background.
            college (dict): A dictionary which contains college data.
                e.g., 123456789012345678901211
            user (dict): A dictionary which contains user data.
            request (Request): Useful for get ip address of user.

        Returns:
            dict: A dictionary which contains unassigned applicants'/panelist
                info.
        """
        if (
            slot := await DatabaseConfiguration().slot_collection.find_one(
                {"_id": ObjectId(slot_id)}
            )
        ) is None:
            raise DataNotFoundError(slot_id, "Slot")
        _id, user_type, email = await self.get_unassign_data(
            application_id, panelist_id
        )
        if _id in slot.get("take_slot", {}).get(f"{user_type}_ids"):
            slot.get("take_slot", {}).get(f"{user_type}_ids", []).remove(_id)
        slot_type = slot.get("slot_type", "")
        booked_user = slot.get("booked_user")
        user_ids = slot.get("take_slot", {}).get(f"{user_type}_ids")
        if user_type == "application":
            if booked_user:
                booked_user = booked_user - 1
        updated_slot = await DatabaseConfiguration().slot_collection.update_one(
            {"_id": slot.get("_id")},
            {
                "$set": {
                    f"take_slot.{user_type}_ids": user_ids,
                    "booked_user": booked_user,
                    f"take_slot.{user_type}": False if len(user_ids) == 0 else True,
                }
            },
        )
        if updated_slot:
            if user_type == "application":
                await DatabaseConfiguration().studentApplicationForms.update_one(
                    {
                        "_id": ObjectId(application_id),
                        "meetingDetails.slot_id": ObjectId(slot_id),
                    },
                    {
                        "$unset": {
                            "meetingDetails": True,
                            f"{slot_type.lower()}_status": True,
                        }
                    },
                )
            toml_data = utility_obj.read_current_toml_file()
            if toml_data.get("testing", {}).get("test") is False:
                ip_address = utility_obj.get_ip_address(request)
                user_email = user.get("user_name")
                user_name = utility_obj.name_can(user)
                user_id = str(user.get("_id"))
                await Planner().send_mail_to_unassign_users(
                    slot, [email], college, user_email, user_name, user_id, ip_address
                )
        return {"message": "User has unassigned from a slot."}

    async def update_slot_time(
        self,
        start_time: None | datetime = None,
        slot_id: str | None = None,
        slot_duration: int | None = None,
    ):
        """
        Update time and end time in slot collection

        params:
        - slot_id (str): unique identifier of the slot id
        - start_time (date): datetime from the database
        - slot_duration (int): slot duration in minutes.
        returns:
            Response (date)-> end_time
        """
        end_time = start_time + timedelta(minutes=int(slot_duration))
        await DatabaseConfiguration().slot_collection.update_one(
            {"_id": ObjectId(slot_id)},
            {
                "$set": {
                    "time": start_time,
                    "end_time": end_time,
                    "slot_duration": int(slot_duration),
                }
            },
        )
        return end_time

    async def get_all_slot_details(
        self, panel_id: str | None = None, current_slot_time: datetime | None = None
    ):
        """
        Get all slot details sorted by time

        params:
            panel_id (str): The panel id of the current slot
            current_slot_time (datetime): The start time from the slot
        returns:
         response: A generator of the slot details
        """
        pipeline = [
            {"$match": {"panel_id": ObjectId(panel_id)}},
            {"$sort": {"time": 1}},
        ]
        if current_slot_time is not None:
            pipeline[0].get("$match", {}).update({"time": {"$gte": current_slot_time}})
        return DatabaseConfiguration().slot_collection.aggregate(pipeline)

    async def initial_slot_management(self, payload: dict):
        """
        Update every slot time manage
        """
        gap_between_slot = payload.get("gap_between_slot")
        if gap_between_slot:
            all_slots = await self.get_all_slot_details(payload.get("panel_id"))
        else:
            try:
                slot = DatabaseConfiguration().slot_collection.find_one(
                    {"_id": ObjectId(payload.get("updated_slot")[0].get("slot_id"))}
                )
            except IndexError as error:
                raise HTTPException(status_code=404, detail=f"Index error " f"{error}")
            except Exception as error:
                raise HTTPException(
                    status_code=422, detail=f"An error occur " f"{error}"
                )
            all_slots = await self.get_all_slot_details(
                payload.get("panel_id"), current_slot_time=slot.get("time")
            )
        index = 0
        async for slot_data in all_slots:
            if index == 0:
                start_time = slot_data.get("time")
                index += 1
            for slot in payload.get("updated_slot", []):
                if str(slot_data.get("_id")) == slot.get("slot_id"):
                    end_time = await self.update_slot_time(
                        slot_id=str(slot.get("slot_id")),
                        start_time=start_time,
                        slot_duration=slot.get("slot_duration"),
                    )
                    break
            else:
                duration = slot_data.get("end_time") - slot_data.get("time")
                slot_gap = divmod(duration.total_seconds(), 60)
                slot_gap = int(slot_gap[0])
                end_time = await self.update_slot_time(
                    slot_id=str(slot_data.get("_id")),
                    start_time=start_time,
                    slot_duration=slot_gap,
                )
            start_time = end_time + timedelta(minutes=int(gap_between_slot))

    async def update_panel_details(self, payload: dict, panel: dict | None = None):
        """
        Update the panel details for the given payload

        params:
         payload: The details of panel and slot in payload object
        """
        if payload.get("gap_between_slot") is not None:
            gap_between_slot = int(payload.get("gap_between_slot"))
        else:
            gap_between_slot = int(panel.get("gap_between_slots"))
        get_slot_details = await self.get_all_slot_details(payload.get("panel_id"))
        total_slot_duration = slot_count = 0
        async for slot in get_slot_details:
            slot_duration = int(slot.get("slot_duration"))
            total_slot_duration += slot_duration
            slot_count += 1
        total_panel_duration = int(panel.get("panel_duration"))
        total_gap_duration = gap_between_slot * (slot_count - 1)
        remaining_time = total_panel_duration - (
            total_gap_duration + total_slot_duration
        )
        slot_gap_duration = total_gap_duration + total_slot_duration
        await DatabaseConfiguration().panel_collection.update_one(
            {"_id": ObjectId(panel.get("_id"))},
            {
                "$set": {
                    "gap_between_slots": gap_between_slot,
                    "total_slot_duration": total_slot_duration,
                    "total_gap_between_slots": total_gap_duration,
                    "slot_gap_duration": slot_gap_duration,
                    "slot_count": slot_count,
                    "available_time": remaining_time,
                }
            },
        )

    async def panel_time_management(self, payload: dict):
        """
        Interview rescheduled of application with slot

        params:
        - slot_id (str): unique identifier of the slot id
        - panel_id (str): unique identifier of the application id
        - slot_duration (int): slot duration in minutes.
        returns:
            Response-> Assigned the application to the slot
        """
        if (
            panel_details := await DatabaseConfiguration().panel_collection.find_one(
                {"_id": ObjectId(payload.get("panel_id"))}
            )
        ) is None:
            raise DataNotFoundError(payload.get("panel_id"), "Panelist")
        await self.initial_slot_management(payload)
        await self.update_panel_details(payload, panel_details)
        return {"message": "panel has been updated"}
