"""
This file contain class and functions that useful for get followup notes data
"""

import datetime

from bson import ObjectId
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError

from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import is_testing_env
from app.helpers.counselor_deshboard.counselor import CounselorDashboardHelper

logger = get_logger(__name__)


class FollowupNotesHelper:
    """
    Contain functions related to followup notes
    """

    def followup_notes_helper(self, data):
        """
        Get follow-up and notes
        """
        return {
            "id": str(data["_id"]),
            "application_id": str(data["application_id"]),
            "student_id": str(data["student_id"]),
            "notes": (
                (
                    {
                        "note": item.get("note"),
                        "timestamp": utility_obj.get_local_time(item.get("timestamp")),
                        "user_id": str(item["user_id"]),
                        "added_by": item["added_by"],
                    }
                    for item in data.get("notes", [])
                )
                if data.get("notes")
                else None
            ),
            "followup": (
                (
                    {
                        "timestamp": utility_obj.get_local_time(item.get("timestamp")),
                        "user_id": str(item.get("user_id")),
                        "assigned_counselor_name": item.get("assigned_counselor_name"),
                        "assigned_counselor_id": str(item.get("assigned_counselor_id")),
                        "followup_date": utility_obj.get_local_time(
                            item.get("followup_date")
                        ),
                        "followup_note": item.get("followup_note"),
                        "added_by": item["added_by"],
                        "status": item.get("status"),
                    }
                    for item in data.get("followup")
                )
                if data.get("followup")
                else None
            ),
            "lead_stage": data.get("lead_stage"),
            "lead_stage_label": data.get("lead_stage_label", ""),
            "application_status": data.get("application_status"),
            "application_substage": data.get("application_substage"),
        }

    def followup_helper(self, data):
        """
        Get followup details
        """
        return {
            "assigned_counselor_id": str(data.get("assigned_counselor_id")),
            "assigned_counselor_name": data.get("assigned_counselor_name"),
            "followup_date": utility_obj.get_local_time(data.get("followup_date")),
            "followup_note": data.get("followup_note"),
            "timestamp": utility_obj.get_local_time(data.get("timestamp")),
            "user_id": str(data.get("user_id")),
            "added_by": data.get("added_by"),
            "status": data.get("status"),
        }

    def timeline_notes_helper(self, data):
        """
        Show timeline of notes
        """
        return {
            "note": data.get("note"),
            "added_by": data.get("added_by"),
            "timestamp": utility_obj.get_local_time(data.get("timestamp")),
        }

    def timeline_followup_helper(self, data, student_name):
        """
        Show timeline of followup
        """
        return {
            "followup": f"with {student_name}",
            "followup_note": data.get("followup_note"),
            "assigned_to": data.get("assigned_counselor_name"),
            "due": utility_obj.get_local_time(data.get("followup_date")),
            "created_by": str(data.get("added_by")),
            "status": data.get("status"),
            "timestamp": utility_obj.get_local_time(data.get("timestamp")),
        }

    def counselor_followup_helper(self, data):
        """
        Get counselor followup data in proper format
        """
        return {
            "application_id": str(data["application_id"]),
            "student_id": str(data["student_id"]),
            "followup": (
                (
                    {
                        "timestamp": utility_obj.get_local_time(item.get("timestamp")),
                        "user_id": str(item.get("user_id")),
                        "assigned_counselor_name": item.get("assigned_counselor_name"),
                        "assigned_counselor_id": str(item.get("assigned_counselor_id")),
                        "followup_date": utility_obj.get_local_time(
                            item.get("followup_date")
                        ),
                        "followup_note": item.get("followup_note"),
                        "added_by": item["added_by"],
                        "status": item.get("status"),
                    }
                    for item in data.get("followup")
                )
                if data.get("followup")
                else None
            ),
            "lead_stage": data.get("lead_stage"),
            "lead_stage_label": data.get("lead_stage_label", ""),
        }

    async def update_followup_info(
        self,
        assigned_counselor_id: str | None,
        application: dict,
        current_user: str,
        followup_date: str,
        user: dict,
        followup_note: str | None,
    ):
        """
        Update the followup information in the leadsFollowUp collection.

        Params:
            - assigned_counselor_id (str | None): Either None or a unique
                id/identifier of a counselor which useful for allocate
                counselor to followup.
            - application (dict): A dictionary which contains application data.
            - current_user (str): An email id of a current logged-in user.
            - followup_date (str): A string datetime in the following format:
                DD/MM/YYYY HH:MM PM/AM
            - user (dict): A dictionary which contains current user data.
            - followup_note (str | None): Either None or note of the followup.

        Returns:
            - None: No returning anything

        Raises:
            - ObjectIdInValid: An error occurred when counselor id is wrong.
        """
        if assigned_counselor_id not in [None, ""]:
            await utility_obj.is_length_valid(assigned_counselor_id, "Counselor id")
            counselor = await DatabaseConfiguration().user_collection.find_one(
                {"_id": ObjectId(assigned_counselor_id)}
            )
            if not counselor:
                counselor = {}
            counselor_name = utility_obj.name_can(counselor)
            await CounselorDashboardHelper().allocate_counselor(
                str(application.get("_id")), current_user, assigned_counselor_id
            )
            assigned_counselor_id = ObjectId(assigned_counselor_id)
        else:
            counselor_info = application.get("allocate_to_counselor", {})
            assigned_counselor_id = ObjectId(str(counselor_info.get("counselor_id")))
            counselor_name = counselor_info.get("counselor_name")
        date_utc = await utility_obj.date_change_utc(followup_date)
        lead_followup = await DatabaseConfiguration().leadsFollowUp.find_one(
            {
                "application_id": application.get("_id"),
                "student_id": application.get("student_id"),
            }
        )
        followup = [
            {
                "assigned_counselor_id": assigned_counselor_id,
                "assigned_counselor_name": counselor_name,
                "followup_date": date_utc,
                "followup_note": followup_note,
                "timestamp": datetime.datetime.utcnow(),
                "user_id": ObjectId(user.get("_id")),
                "added_by": utility_obj.name_can(user),
                "status": "Incomplete",
            }
        ]
        if lead_followup:
            if lead_followup.get("followup"):
                followup = followup + lead_followup.get("followup")
        await DatabaseConfiguration().leadsFollowUp.update_one(
            {
                "application_id": application.get("_id"),
                "student_id": application.get("student_id"),
            },
            {"$set": {"followup": followup}},
            upsert=True,
        )


class pending_followup:

    def __init__(self, current_user, start_date, end_date, page_num, page_size):
        """Initialize the variable"""
        self.current_user = current_user
        self.start_date = start_date
        self.end_date = end_date
        self.skip = page_num
        self.limit = page_size
        self.today = datetime.datetime.utcnow()

    async def checking_permission(self, user):
        """checking permission for this user"""
        if user.get("role", {}).get("role_name") in [
            "college_publisher_console",
            "college_counselor",
        ]:
            raise HTTPException(status_code=401, detail="Not enough permission")
        return user

    async def checking_user(self):
        """
        Check the user exists or not
        """
        if (
            user := await DatabaseConfiguration().user_collection.find_one(
                {"user_name": self.current_user}
            )
        ) is None:
            raise HTTPException(status_code=404, detail="user not found")
        return await self.checking_permission(user)

    async def head_counselor_result(self, pipeline, season=None):
        """
        Get head counselor final results
        """
        results = DatabaseConfiguration(season=season).user_collection.aggregate(
            pipeline
        )
        head_counselor = []
        async for data in results:
            head_counselor.append(
                {
                    "id": str(data.get("_id", {}).get("id")),
                    "email": data.get("_id", {}).get("email"),
                    "name": str(utility_obj.name_can(data.get("_id", {}))),
                    "mobile_number": data.get("_id", {}).get("mobile_number"),
                    "total_pending_followup": data.get("total_pending_followup", 0),
                }
            )
        response = await utility_obj.pagination_in_aggregation(
            self.skip,
            self.limit,
            len(head_counselor),
            route_name="/get_pending_followup/head_counselor_details/",
        )
        return {
            "data": head_counselor,
            "total": len(head_counselor),
            "count": self.limit,
            "pagination": response["pagination"],
            "message": "Get all head counselor details.",
        }

    async def counselor_pipeline(self, pipeline, counselor_id=False):
        """
        Ready for data as json for only counselor
        """
        results = DatabaseConfiguration().leadsFollowUp.aggregate(pipeline)
        followup_lst, count_followup = [], 0
        async for data in results:
            try:
                total_count = data.get("totalCount", [{}])[0].get("count")
            except IndexError:
                total_count = 0
            if counselor_id:
                count_followup = len(data.get("paginated_results", []))
            for counselor in data.get("paginated_results", []):
                followup_lst.append(
                    {
                        "student_id": str(counselor.get("student_id")),
                        "application_id": str(counselor.get("application_id")),
                        "student_name": utility_obj.name_can(
                            counselor.get("student_primary", {}).get(
                                "basic_details", {}
                            )
                        ),
                        "counselor_name": counselor.get("followup", {}).get(
                            "assigned_counselor_name"
                        ),
                        "followup_date": utility_obj.get_local_time(
                            counselor.get("followup", {}).get("followup_date")
                        ),
                        "status": "pending",
                        "created_by": counselor.get("followup", {}).get("added_by"),
                        "created_at": utility_obj.get_local_time(
                            counselor.get("followup", {}).get("timestamp")
                        ),
                        "updated_by": counselor.get("followup", {}).get(
                            "updated_by", ""
                        ),
                        "updated_date": (
                            utility_obj.get_local_time(
                                counselor.get("followup", {}).get("updated_date")
                            )
                            if counselor.get("followup", {}).get("updated_date", "")
                            != ""
                            else ""
                        ),
                        "counselor_email": counselor.get("counselor_details", {}).get(
                            "email"
                        ),
                        "course": (
                            f"{counselor.get('course_details', {}).get('course_name')} in "
                            f"{counselor.get('student_application', {}).get('spec_name1')}"
                            if counselor.get("student_application", {}).get(
                                "spec_name1", ""
                            )
                            != ""
                            else counselor.get("course_details", {}).get("course_name")
                        ),
                    }
                )
        response = await utility_obj.pagination_in_aggregation(
            self.skip,
            self.limit,
            total_count,
            route_name="/get_pending_followup/get_pending_followup/",
        )
        if counselor_id:
            return count_followup
        return {
            "data": followup_lst,
            "total": total_count,
            "count": self.limit,
            "pagination": response["pagination"],
            "message": "Get all pending leads.",
        }

    async def get_pending_followup_lead(
        self, head_counselor_id=None, counselor_id=False, user_id=None
    ):
        """get all lead which has status is pending"""
        if counselor_id:
            all_counselor_id = [user_id]
        else:
            user = await self.checking_user()
            if user.get("role", {}).get("role_name") == "college_head_counselor":
                counselors = await DatabaseConfiguration().user_collection.aggregate(
                    [{"$match": {"head_counselor_id": ObjectId(user.get("_id"))}}]
                ).to_list(length=None)
            elif head_counselor_id is not None:
                await utility_obj.is_id_length_valid(
                    head_counselor_id, "head counselor id"
                )
                counselors = await DatabaseConfiguration().user_collection.aggregate(
                    [{"$match": {"head_counselor_id": ObjectId(head_counselor_id)}}]
                ).to_list(length=None)
            else:
                raise HTTPException(
                    status_code=422, detail="head counselor id is missing"
                )
            all_counselor_id = [ObjectId(data.get("_id")) for data in counselors]
        return await self.pipeline_build(all_counselor_id, counselor_id)

    async def pipeline_build(self, all_counselor_id, counselor_id=False):
        """creating the pipeline for counselor only"""
        skip, limit = await utility_obj.return_skip_and_limit(
            page_num=self.skip, page_size=self.limit
        )
        pipeline = [
            {"$unwind": {"path": "$followup"}},
            {
                "$match": {
                    "followup": {"$exists": True},
                    "followup.followup_date": {
                        "$gte": self.today,
                        "$lte": self.end_date,
                    },
                    "followup.assigned_counselor_id": {"$in": all_counselor_id},
                    "followup.status": "Incomplete",
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "student_id": 1,
                    "application_id": 1,
                    "followup": 1,
                }
            },
            {
                "$lookup": {
                    "from": "studentsPrimaryDetails",
                    "let": {"student_id": "$student_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$student_id"]}}},
                        {"$project": {"_id": 0, "basic_details": 1}},
                    ],
                    "as": "student_primary",
                }
            },
            {
                "$unwind": {
                    "path": "$student_primary",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": {"application_id": "$application_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$application_id"]}}},
                        {
                            "$project": {
                                "_id": 0,
                                "course_id": 1,
                                "spec_name1": 1,
                                "spec_name2": 1,
                            }
                        },
                    ],
                    "as": "student_application",
                }
            },
            {"$unwind": {"path": "$student_application"}},
            {
                "$lookup": {
                    "from": "courses",
                    "let": {"course_id": "$student_application.course_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$course_id"]}}},
                        {
                            "$project": {
                                "_id": 0,
                                "course_name": 1,
                            }
                        },
                    ],
                    "as": "course_details",
                }
            },
            {"$unwind": {"path": "$course_details"}},
            {
                "$lookup": {
                    "from": "users",
                    "let": {"user_id": "$followup.assigned_counselor_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$user_id"]}}},
                        {"$project": {"_id": 0, "email": 1}},
                    ],
                    "as": "counselor_details",
                }
            },
            {"$unwind": {"path": "$counselor_details"}},
            {
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            },
        ]
        return await self.counselor_pipeline(pipeline, counselor_id)

    async def head_counselor_detail(self, season=None):
        """get head counselor details"""
        await self.checking_user()
        skip, limit = await utility_obj.return_skip_and_limit(
            page_num=self.skip, page_size=self.limit
        )
        pipeline = [
            {"$match": {"role.role_name": "college_head_counselor"}},
            {"$skip": skip},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 1,
                    "first_name": 1,
                    "middle_name": 1,
                    "last_name": 1,
                    "email": 1,
                    "mobile_number": 1,
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "let": {"head_id": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$head_counselor_id", "$$head_id"]}
                            }
                        },
                        {"$project": {"_id": 1, "head_counselor_name": 1}},
                    ],
                    "as": "counselor_details",
                }
            },
            {"$unwind": {"path": "$counselor_details"}},
            {
                "$lookup": {
                    "from": "leadsFollowUp",
                    "let": {"counselor_id": "$counselor_details._id"},
                    "pipeline": [
                        {"$unwind": {"path": "$followup"}},
                        {
                            "$match": {
                                "followup.followup_date": {
                                    "$gte": self.today,
                                    "$lte": self.end_date,
                                },
                                "followup.status": "Incomplete",
                                "$expr": {
                                    "$eq": [
                                        "$followup.assigned_counselor_id",
                                        "$$counselor_id",
                                    ]
                                },
                            }
                        },
                        {"$project": {"_id": 1}},
                    ],
                    "as": "pending_details",
                }
            },
            {
                "$unwind": {
                    "path": "$pending_details",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            {
                "$group": {
                    "_id": {
                        "id": "$_id",
                        "email": "$email",
                        "first_name": "$first_name",
                        "middle_name": "$middle_name",
                        "last_name": "$last_name",
                        "mobile_number": "$mobile_number",
                    },
                    "total_pending_followup": {
                        "$sum": {"$cond": ["$pending_details._id", 1, 0]}
                    },
                }
            },
        ]
        return await self.head_counselor_result(pipeline, season=season)


class lead_stage_label:

    def __init__(self):
        pass

    async def get_lead_stage(self, college_id):
        """
        Get all lead stages along with lead labels.
        """
        results = DatabaseConfiguration().college_collection.aggregate(
            [
                {"$match": {"_id": ObjectId(college_id)}},
                {"$project": {"lead_stage_label": 1}},
            ]
        )
        async for lead in results:
            return lead.get("lead_stage_label", [])
        return {}

    async def get_lead_stage_label(self, college_id):
        """get lead stage label"""
        results = DatabaseConfiguration().college_collection.aggregate(
            [
                {"$match": {"_id": ObjectId(college_id)}},
                {"$project": {"_id": 1, "lead_stage_label": 1}},
            ]
        )
        async for label in results:
            return label

    async def get_lead_stage_with_label(self, college_id):
        """
        get lead stage with label
        """
        lead_stage = await self.get_lead_stage(college_id)
        return lead_stage

    async def add_lead_stage_timeline(
        self,
        application: dict,
        current_lead_stage: str,
        previous_lead_stage: str | None = "Fresh Lead",
            user: dict | None = None,
    ) -> None:
        """
        Helper function for add lead stage timeline.
        """
        if not is_testing_env():
            if user is None:
                user = {}
                name = ""
            else:
                name = utility_obj.name_can(user)
            try:
                # TODO: Not able to add student timeline data
                #  using celery task when environment is
                #  demo. We'll remove the condition when
                #  celery work fine.
                if settings.environment in ["demo"]:
                    StudentActivity().student_timeline(
                        student_id=str(application.get("student_id")),
                        event_type="Application",
                        message=f"{name} has changed the lead stage from `{previous_lead_stage}` to "
                                f"`{current_lead_stage}`.",
                        user_id=str(user.get("_id")),
                        application_id=str(application.get("_id")),
                        college_id=str(application.get("college_id")),
                    )
                else:
                    StudentActivity().student_timeline.delay(
                        student_id=str(application.get("student_id")),
                        event_type="Application",
                        message=f"{name} has changed the lead stage from"
                                f" `{previous_lead_stage}` to `{current_lead_stage}`.",
                        application_id=str(application.get("_id")),
                        user_id=str(user.get("_id")),
                        college_id=str(application.get("college_id")),
                    )
            except KombuError as celery_error:
                logger.error(f"error add_student_timeline {celery_error}")
            except Exception as error:
                logger.error(f"error add_student_timeline {error}")
