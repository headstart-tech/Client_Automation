"""
This file contain class and methods which helpful for API in the file named
lead_user_router.py
"""

from datetime import datetime, timezone, date

from bson.objectid import ObjectId
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError

from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.custom_error import DataNotFoundError
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import cache_invalidation, is_testing_env, insert_data_in_cache
from app.helpers.admin_dashboard.lead_user import LeadUser
from app.models.applications import DateRange
from app.database.aggregation.student import Student

logger = get_logger(__name__)


class LeadAdmin:
    """
    Contain helper functions related to lead admin
    """

    async def lead_notification(self, application_id: str):
        """
        Get the application status of student's application
        """
        try:
            student, application = await LeadUser().student_application_data(
                application_id
            )
        except:
            raise HTTPException(status_code=404,
                                detail="Application not found")
        if (
                course := await DatabaseConfiguration().course_collection.find_one(
                    {"_id": ObjectId(str(application.get("course_id")))}
                )
        ) is None:
            raise HTTPException(status_code=404, detail="course not found")
        total_paid = (
            1 if application.get("payment_info", {}).get(
                "status") == "captured" else 0
        )
        total_submit = 1 if application.get("declaration") is True else 0
        course_name = (
            f"{course.get('course_name')} in {application.get('spec_name1')}"
            if application.get("spec_name1")
            else course.get("course_name")
        )
        return {
            "verify": student.get("is_verify"),
            "application_started": 1 if application.get(
                "current_stage") > 2 else 0,
            "course": course_name,
            "payment_approved": total_paid,
            "application_submitted": total_submit,
            "application_stage": application.get("current_stage") * 10,
        }

    async def step_wise_app(
            self, counselor_ids: list | None, date_range: DateRange | None,
            season: str | None, program_filter: list | None,
            source: list | None) -> list:
        """
        Get the step-wise details.

        Params:
            - counselor_ids (list | None): Optional field. Default value: None.
                Value can be list of unique counselor ids.
                e.g., ["123456789012345678901111", "123456789012345678901112"]
            - season (str | None): Optional field. Default value: None.
                Enter season id/value when want to get data season-wise data.
            - program_name (list | None): Optional field.
                Default value: None. Enter program details when want to get
                data based on program. e.g., [{"course_id":
                "123456789012345678901234", "course_specialization": "xyx"}]
            - source (list | None): Optional field.
                Default value: None. Enter source (s) names when want to get
                data based on source (s). e.g., ["organic", "twitter"]

        Returns:
            - list: A list which contains step-wise information.
        """
        date_range = await utility_obj.format_date_range(date_range)
        match_stage_conditions = [{"current_stage": {"$ne": 1.25}}]
        if season == "":
            season = None
        if len(date_range) >= 2:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
            match_stage_conditions.append(
                {"enquiry_date": {"$gte": start_date, "$lte": end_date}}
            )
        if counselor_ids:
            match_stage_conditions.append(
                {
                    "allocate_to_counselor.counselor_id": {
                        "$in": [
                            ObjectId(counselor_id)
                            for counselor_id in counselor_ids
                            if await utility_obj.is_length_valid(
                                counselor_id, "Counselor id"
                            )
                        ]
                    }
                }
            )
        if program_filter:
            course_filter_list = [
                {
                    "course_id": ObjectId(course_info.get("course_id")),
                    "spec_name1": course_info.get("course_specialization"),
                }
                for course_info in program_filter
                if course_info.get("course_id") not in ["", None]
                   and await utility_obj.is_length_valid(
                    course_info.get("course_id"), "Course id"
                )
            ]

            if course_filter_list:
                match_stage_conditions.append({"$or": course_filter_list})
        if source:
            student_ids = await Student().get_students_based_on_source(
                source=source, season=season
            )
            match_stage_conditions.append({"student_id": {"$in": student_ids}})
        pipeline = [
            {"$match": {"$and": match_stage_conditions}},
            {
                "$group": {
                    "_id": "$current_stage",
                    "students": {"$push": {"student_id": "$student_id"}},
                }
            },
            {"$sort": {"_id": 1}}
        ]
        result = DatabaseConfiguration(
            season=season).studentApplicationForms.aggregate(
            pipeline
        )
        names = {
            2.5: "basic_and_preference_details",
            3.75: "parent_details",
            5.0: "address_details",
            6.25: "education_details",
            7.5: "payment",
            8.75: "upload_document",
            10.0: "declaration",
        }
        names_sort = list(names.values())
        lst = []
        async for i in result:
            dct = {
                "step": names.pop(i.get("_id")),
                "application": len(i.get("students")),
            }
            lst.append(dct)

        for name in names.values():
            dct = {"step": name, "application": 0}
            lst.append(dct)
        lst = sorted(lst, key=lambda x: names_sort.index(x.get("step")))
        return lst

    async def activity_of_users(self, skip, limit):
        """
        Get paginated user activity logs.

        Parameters:
        skip (int): The number of records to skip.
        limit (int): The maximum number of records to return.

        Returns:
        tuple: A tuple containing a list of user details and the total count of users.
        """

        db_config = DatabaseConfiguration()
        login_activities = await db_config.login_activity_collection.aggregate(
            [
                {
                    "$facet": {
                        "paginated_results": [{"$skip": skip},
                                              {"$limit": limit}],
                        "totalCount": [{"$count": "count"}],
                    }
                }
            ]).to_list(None)

        try:
            total_user = login_activities[0]['totalCount'][0]['count']
        except (IndexError, KeyError):
            total_user = 0

        user_ids = [activity['user_id'] for activity in
                    login_activities[0]['paginated_results']]
        users = await db_config.user_collection.aggregate(
            [{"$match": {"_id": {"$in": user_ids}}}]).to_list(None)
        users_dict = {user['_id']: user for user in users}

        all_user_detail = []
        for activity in login_activities[0]['paginated_results']:
            user = users_dict.get(activity['user_id'], {})
            role_name = await utility_obj.get_role_name_in_proper_format(
                user.get("role", {}).get("role_name")
            ) if user else None

            user_data = {
                "name": activity.get("user_name"),
                "email_id": user.get("email"),
                "role": role_name,
                "ip_address": activity.get("ip_address"),
                "last_activity": f"{activity['user_name']} [{role_name}] logged in at "
                                 f"{utility_obj.get_local_time(activity['created_at'])} "
                                 f"from IP {activity['ip_address']}"
            }
            all_user_detail.append(user_data)

        return all_user_detail, total_user

    async def add_tags_to_application(self, add_tag_data: dict,
                                      user: dict) -> dict:
        """
        Add tags to student based on application.

        Params:
            add_tag_data (dict): A dictionary which contains tags and
                application id.
                e.g., {"student_ids": ["123456789012345678901231",
                    "123456789012345678901232"],
                    "tags": ["string", "test", "test1"]}

        Returns:
            dict: A dictionary which contains information about add tags to
            application.

        Raises:
            ObjectIdInValid: An exception which occur when application id will
                be wrong.
            DataNotFoundError: An exception which occur when application not
                found based on application id.
        """
        student_ids = [
            ObjectId(student_id)
            for student_id in add_tag_data.get("student_ids", [])
            if await utility_obj.is_length_valid(student_id, "Student id")
        ]
        for stud_id in student_ids:
            if (
                    student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                        {"_id": stud_id}
                    )
            ) is None:
                raise DataNotFoundError(message="Student", _id=str(stud_id))
            app_tags = student.get("tags", [])
            tags = add_tag_data.get("tags")
            if app_tags:
                tags = [tag for tag in tags if tag not in app_tags]
            if tags:
                update_tags = tags + app_tags
                current_datetime = datetime.now(timezone.utc)
                update_dict = {"tags": update_tags,
                               "last_user_activity_date": current_datetime
                               }
                if not student.get("first_lead_activity_date"):
                    update_dict["first_lead_activity_date"] = current_datetime
                if "DND" in tags:
                    update_dict.update({"unsubscribe": True})
                await DatabaseConfiguration().studentsPrimaryDetails.update_one(
                    {"_id": stud_id}, {"$set": update_dict}
                )
                await cache_invalidation(api_updated="lead/add_tag/")
                try:
                    toml_data = utility_obj.read_current_toml_file()
                    if toml_data.get("testing", {}).get("test") is False:
                        # TODO: Not able to add student timeline data
                        #  using celery task when environment is
                        #  demo. We'll remove the condition when
                        #  celery work fine.
                        if settings.environment in ["demo"]:
                            StudentActivity().student_timeline(
                                student_id=str(student.get("_id")),
                                event_type="Tag",
                                event_status="Assign tag",
                                message=f"{utility_obj.name_can(user)} "
                                        f"has added a tag of {tags}",
                                college_id=str(student.get("college_id")),
                            )
                        else:
                            if not is_testing_env():
                                StudentActivity().student_timeline.delay(
                                    student_id=str(student.get("_id")),
                                    event_type="Tag",
                                    event_status="Assign tag",
                                    message=f"{utility_obj.name_can(user)} "
                                            f"has added a tag of {tags}",
                                    college_id=str(student.get("college_id")),
                                )
                except KombuError as celery_error:
                    logger.error(
                        f"error add tags" f" timeline data {celery_error}")
                except Exception as error:
                    logger.error(f"error add tags" f" timeline data {error}")
        return {"message": "Tags added to the leads."}

    async def get_contact_and_not_contact_lead_count(
            self,
            date_range: dict | None = None,
            counselor_id: list | None = None,
            season: str | None = None,
            is_head_counselor: bool = False,
            students=None
    ) -> dict:
        """
        Get the lead header Contact and Not Contacted Lead Count.

        Params:
            - date_range (dict | None): Get the date range or None.
            - counselor_id (list | None): Either None or a list of counselor
                ids which  useful for get lead header information based on
                counselor ids.
            - season (str | None): Either None or unique identifier of season
                which useful for get season-wise data.
            - is_head_counselor (bool): True if the requested user is college_head_counselor. Default: False

        Returns:
            response: A dictionary which contains lead header details.
        """
        pipeline = [
            {
                "$match": {
                    "call_to": {'$in': students}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "contact_lead_count": {
                        "$cond": {
                            "if":
                                {"$or": [{"$gt": [
                                 {"$sum": "$duration"}, 0]},
                                 {"$gt": [
                                    {"$sum": "$call_duration"}, 0]}]},
                            "then": 1,
                            "else": 0,
                        }
                    },
                    "not_contact_lead_count": {
                        "$cond": {
                            "if": {"$or": [{"$eq": [
                                {"$sum": "$duration"}, 0]},
                                {"$eq": [
                                    {"$sum": "$call_duration"}, 0]}]},
                            "then": 1,
                            "else": 0,
                        }
                    },
                }
            },
            {
                "$group": {
                    "_id": None,
                    "contact_lead_count": {"$sum": "$contact_lead_count"},
                    "not_contact_lead_count": {
                        "$sum": "$not_contact_lead_count"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "contact_lead_count": 1,
                    "not_contact_lead_count": 1,
                }
            }
        ]

        result = await (DatabaseConfiguration(
            season=season).call_activity_collection.aggregate(
            pipeline
        )).to_list(None)
        result = result[0] if result else {}
        return result

    async def get_lead_header_aggregate(
            self,
            date_range: dict | None = None,
            lead_type: str | None = None,
            counselor_id: list | None = None,
            season: str | None = None,
            is_head_counselor: bool = False,
    ) -> tuple:
        """
        Get the lead header information.

        Params:
            - date_range (dict | None): Get the date range or None.
            - lead_type (str | None): Either None or lead type which useful
                for get lead header information based on lead type.
            - counselor_id (list | None): Either None or a list of counselor
                ids which  useful for get lead header information based on
                counselor ids.
            - season (str | None): Either None or unique identifier of season
                which useful for get season-wise data.

        Returns:
            response: Tuple
            A dictionary which contains lead header details.
            List of student ids
        """
        match_stage, app_match, lead_base_match = {}, {}, {}
        if counselor_id or is_head_counselor:
            match_stage.update(
                {"allocate_to_counselor.counselor_id": {"$in": counselor_id}})
            app_match.update(
                {"allocate_to_counselor.counselor_id": {"$in": counselor_id}})
        payment_match = match_stage.copy()
        if date_range is not None and len(date_range) >= 2:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
            match_stage.update(
                {"created_at": {"$gte": start_date, "$lte": end_date}})
            payment_match.update(
                {"payment_info.created_at": {"$gte": start_date,
                                             "$lte": end_date}})
            app_match.update({"enquiry_date": {"$gte": start_date,
                                               "$lte": end_date}})
        payment_match.update({"payment_info.status": "captured"})
        paid_applications_count = await DatabaseConfiguration(
            season=season).studentApplicationForms.count_documents(
            payment_match)
        app_base_match = {"$expr": {
            "$eq": ["$student_id", "$$student_id"]}
        }
        if app_match:
            app_base_match.update(app_match)

        primary_pipeline = [
            {
                "$group": {
                    "_id": "",
                    "students": {"$addToSet": "$_id"},
                    "total_lead": {"$sum": 1},
                    "primary_source": {
                        "$sum": {
                            "$cond": [
                                {"$ifNull": ["$source.primary_source",
                                             False]}, 1, 0]
                        }
                    },
                    "secondary_source": {
                        "$sum": {
                            "$cond": [
                                {"$ifNull": ["$source.secondary_source",
                                             False]}, 1, 0]
                        }
                    },
                    "tertiary_source": {
                        "$sum": {
                            "$cond": [
                                {"$ifNull": ["$source.tertiary_source",
                                             False]}, 1, 0]
                        }
                    },
                    "api_lead": {
                        "$sum": {
                            "$cond": [
                                {"$eq": [
                                    "$source.primary_source.lead_type",
                                    "api"]},
                                1,
                                0,
                            ]
                        }
                    },
                    "offline_lead": {
                        "$sum": {
                            "$cond": [
                                {"$eq": [
                                    "$source.primary_source.lead_type",
                                    "offline"]},
                                1,
                                0,
                            ]
                        }
                    },
                    "online_lead": {
                        "$sum": {
                            "$cond": [
                                {"$eq": [
                                    "$source.primary_source.lead_type",
                                    "online"]},
                                1,
                                0,
                            ]
                        }
                    },
                    "telephony_lead": {
                        "$sum": {
                            "$cond": [
                                {"$eq": [
                                    "$source.primary_source.lead_type",
                                    "telephony"]},
                                1,
                                0,
                            ]
                        }
                    },
                    "application": {
                        "$sum": {
                            "$cond": {
                                "if": {
                                    "$eq": [
                                        "$source.primary_source.lead_type",
                                        f"{lead_type}",
                                    ]
                                },
                                "then": 1,
                                "else": {
                                    "$cond": {
                                        "if": {
                                            "$eq": [
                                                "$source.primary_source.utm_source",
                                                f"{lead_type}",
                                            ]
                                        },
                                        "then": 1,
                                        "else": 0,
                                    }
                                },
                            }
                        }
                    },
                }
            }
        ]
        if match_stage:
            primary_pipeline.insert(0, {"$match": match_stage})
        primary_data = await (DatabaseConfiguration(season=season).studentsPrimaryDetails.
                  aggregate(primary_pipeline)).to_list(None)
        result = primary_data[0] if primary_data else {}
        students_ids = result.get("students", [])
        if students_ids:
            result.pop("students")
        if students_ids:
            lead_base_match.update({"student_id": {"$in": students_ids}})
        application_pipeline = [
            {
                "$group": {
                    "_id": "",
                    "total_application": {"$sum": 1},
                    "form_initiated": {
                        "$sum": {
                            "$cond": [{"$gte": [
                                "$current_stage", 2]}, 1,
                                0]
                        }
                    },
                    "paid_application": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$payment_info.status",
                                        "captured",
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "paid_application_lead_type": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {
                                            "$eq": [
                                                "$payment_info.status",
                                                "captured",
                                            ]
                                        },
                                        {
                                            "$eq": [
                                                "$source.primary_source.lead_type",
                                                lead_type,
                                            ]
                                        },
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "total_leads_lead_type": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$source.primary_source.lead_type",
                                        lead_type,
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "application_submitted": {
                        "$sum": {
                            "$cond": [{"$eq": [
                                "$declaration", True]}, 1,
                                0]
                        }
                    },
                    "provisional_admission": {
                        "$sum": {
                            "$cond": [{"$eq": [
                                "$declaration", True]}, 1,
                                0]
                        }
                    },
                    "application_not_submitted": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$declaration",
                                         False]},
                                1,
                                0,
                            ]
                        }
                    },
                    "offer_letter": {
                        "$sum": {
                            "$cond": [
                                {"$ifNull": [
                                    "$offer_letter",
                                    False]},
                                1,
                                0,
                            ]
                        }
                    },
                    "payment_initiated": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {
                                            "$eq": [
                                                "$payment_initiated",
                                                True,
                                            ]
                                        },
                                        {
                                            "$ne": [
                                                "$payment_info.status",
                                                "captured",
                                            ]
                                        },
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "application_to_provisions": {
                        "$sum": {
                            "$cond": {
                                "if": {"$ifNull": [
                                    "$declaration",
                                    False]},
                                "then": {
                                    "$cond": {
                                        "if": {
                                            "$eq": [
                                                "$source.primary_source"
                                                ".lead_type",
                                                f"{lead_type}",
                                            ]
                                        },
                                        "then": 1,
                                        "else": {
                                            "$cond": {
                                                "if": {
                                                    "$eq": [
                                                        "$source.primary_source"
                                                        ".utm_source",
                                                        f"{lead_type}",
                                                    ]
                                                },
                                                "then": 1,
                                                "else": 0,
                                            }
                                        },
                                    }
                                },
                                "else": 0,
                            }
                        }
                    },
                }
            }

        ]
        if app_match:
            application_pipeline.insert(0, {"$match": app_match})
        application_data = await (DatabaseConfiguration(season=season).studentApplicationForms.aggregate(application_pipeline)).to_list(None)
        application_data = application_data[0] if application_data else {}
        result.update(application_data)
        followup_pipeline = [
            {"$project": {"_id": 0, "lead_stage":
                {"$ifNull": ["$lead_stage",
                             "Fresh Lead"]}}},
            {
                "$group": {
                    "_id": "",
                    "fresh_lead": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$lead_stage",
                                        "Fresh Lead",
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "interested_lead": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$lead_stage",
                                        "Interested",
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "follow_up_lead": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$lead_stage",
                                        "Follow-up",
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "closed": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$lead_stage",
                                        "Closed",
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                }
            }
        ]
        if lead_base_match:
            followup_pipeline.insert(0, {"$match": lead_base_match})
        followup_data = await (DatabaseConfiguration(season=season).leadsFollowUp.aggregate(followup_pipeline)).to_list(None)
        followup_data = followup_data[0] if followup_data else {}
        result.update({
            **followup_data,
            "paid_application": paid_applications_count})
        return result, students_ids

    async def get_lead_data_aggregate(self, start_date, end_date, lead_type):
        """
        get data based on start date and end date
        params:
            start_date (datetime): Get the start date
            end_date (datetime): get the end date
        return:
            response: A dictionary of result
        """
        result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            [
                {"$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date}}},
                {"$project": {"_id": 1,
                              "primary_source": "$source.primary_source"}},
                {
                    "$lookup": {
                        "from": "leadsFollowUp",
                        "let": {"student_id": "$_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": ["$student_id", "$$student_id"]}
                                }
                            },
                            {"$project": {"_id": 0, "lead_stage": 1}},
                        ],
                        "as": "student_follow_up",
                    }
                },
                {
                    "$unwind": {
                        "path": "$student_follow_up",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
                {
                    "$lookup": {
                        "from": "studentApplicationForms",
                        "let": {"student_id": "$_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {"$eq": ["$$student_id",
                                                      "$student_id"]},
                                    "current_stage": {"$gte": 2},
                                }
                            },
                            {"$project": {"_id": 0, "current_stage": 1}},
                            {"$group": {"_id": "",
                                        "application": {"$sum": 1}}},
                        ],
                        "as": "student_application",
                    }
                },
                {
                    "$unwind": {
                        "path": "$student_application",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
                {
                    "$group": {
                        "_id": "",
                        "total_lead": {"$sum": 1},
                        "primary_lead": {
                            "$sum": {
                                "$cond": [
                                    {"$ifNull": ["$primary_source", False]}, 1,
                                    0]
                            }
                        },
                        "application": {
                            "$sum": {
                                "$cond": {
                                    "if": {
                                        "$eq": [
                                            "$primary_source" ".lead_type",
                                            f"{lead_type}",
                                        ]
                                    },
                                    "then": "$student_application.application",
                                    "else": {
                                        "$cond": {
                                            "if": {
                                                "$eq": [
                                                    "$student_follow_up" ".lead_stage",
                                                    f"{lead_type}",
                                                ]
                                            },
                                            "then": "$student_application"
                                                    ".application",
                                            "else": 0,
                                        }
                                    },
                                }
                            }
                        },
                    }
                },
            ]
        )
        async for data in result:
            if data is None:
                return {}
            return data
        return {}

    async def get_lead_data(
            self,
            previous_start_date: str,
            previous_end_date: str,
            current_start_date: str,
            current_end_date: str,
            lead_type: str | None,
            counselor_id: list | None = None,
            season: str | None = None,
            is_head_counselor: bool = False,
    ) -> dict:
        """
        Get the result of lead count information based on change indicator.

        Params:
            - previous_start_date (str): The previous start date range.
            - previous_end_date (str): The previous end date range.
            - current_start_date (str): The current start date range.
            - current_end_date (str): The current end date range.
            - lead_type (str | None): Either None or lead type which
                useful for get lead count information based on lead type.
            - counselor_id (list | None): Either None or a list of counselor
                ids which  useful for get lead header information based on
                counselor ids.
            - season (str | None): Either None or unique identifier of season
                which useful for get season-wise data.

        Returns:
            response: A dictionary which contains lead count information
                based on change indicator.
        """
        previous_lead_data, student_ids = await self.get_lead_header_aggregate(
            date_range={
                "start_date": previous_start_date,
                "end_date": previous_end_date,
            },
            lead_type=lead_type,
            counselor_id=counselor_id,
            season=season,
            is_head_counselor=is_head_counselor,
        )
        current_lead_data, student_ids = await self.get_lead_header_aggregate(
            date_range={"start_date": current_start_date,
                        "end_date": current_end_date},
            lead_type=lead_type,
            counselor_id=counselor_id,
            season=season,
            is_head_counselor=is_head_counselor,
        )
        prev_filter_application_perc = utility_obj.get_percentage_result(
            previous_lead_data.get("paid_application_lead_type", 0),
            previous_lead_data.get("total_leads_lead_type", 0),
        )
        curr_filter_application_perc = utility_obj.get_percentage_result(
            current_lead_data.get("paid_application_lead_type", 0),
            current_lead_data.get("total_leads_lead_type", 0),
        )
        total_lead_perc_pos = await utility_obj.get_percentage_difference_with_position(
            previous_lead_data.get("total_lead", 0),
            current_lead_data.get("total_lead", 0),
        )
        lead_to_application_filter = (
            await utility_obj.get_percentage_difference_with_position(
                prev_filter_application_perc, curr_filter_application_perc
            )
        )
        paid_application_perc_pos = (
            await utility_obj.get_percentage_difference_with_position(
                previous_lead_data.get("paid_application", 0),
                current_lead_data.get("paid_application", 0),
            )
        )
        total_application_perc_pos = (
            await utility_obj.get_percentage_difference_with_position(
                previous_lead_data.get("total_application", 0),
                current_lead_data.get("total_application", 0),
            )
        )
        application_to_provisions_perc_pos = (
            await utility_obj.get_percentage_difference_with_position(
                previous_lead_data.get("application_to_provisions", 0),
                current_lead_data.get("application_to_provisions", 0),
            )
        )
        form_initiated_to_perc_pos = (
            await utility_obj.get_percentage_difference_with_position(
                previous_lead_data.get("form_initiated", 0),
                current_lead_data.get("form_initiated", 0),
            )
        )
        payment_initiated_to_perc_pos = (
            await utility_obj.get_percentage_difference_with_position(
                previous_lead_data.get("payment_initiated", 0),
                current_lead_data.get("payment_initiated", 0),
            )
        )
        return {
            "lead_percentage": total_lead_perc_pos.get("percentage", 0),
            "lead_position": total_lead_perc_pos.get("position", "equal"),
            "lead_to_application_percentage_indicator": lead_to_application_filter.get(
                "percentage", 0
            ),
            "lead_to_application_position_indicator": lead_to_application_filter.get(
                "position", "equal"
            ),
            "form_paid_app_perc_diff": paid_application_perc_pos.get(
                "percentage", 0),
            "form_paid_app_position": paid_application_perc_pos.get(
                "position", "equal"
            ),
            "total_application_percentage": total_application_perc_pos.get(
                "percentage", 0
            ),
            "total_application_position": total_application_perc_pos.get(
                "position", "equal"
            ),
            "application_to_provisions_percentage"
            "_indicator": application_to_provisions_perc_pos.get("percentage",
                                                                 0),
            "application_to_provisions"
            "_position": application_to_provisions_perc_pos.get("position",
                                                                "equal"),
            "form_initiated_percentage_indicator": form_initiated_to_perc_pos.get(
                "percentage", 0
            ),
            "form_initiated_position_indicator": form_initiated_to_perc_pos.get(
                "position", "equal"
            ),
            "payment_initiated_percent_indicator": payment_initiated_to_perc_pos.get(
                "percentage", 0
            ),
            "payment_initiated_position_indicator": payment_initiated_to_perc_pos.get(
                "position", "equal"
            ),
        }

    async def get_lead_change_indicator(
            self,
            change_indicator: str | None = None,
            lead_type: str | None = None,
            counselor_id: list | None = None,
            season: str | None = None,
            is_head_counselor: bool = False,
    ):
        """
        Get the result of basis of change indicator

        Params:
            - change_indicator (ChangeIndicator | None): Either none or the
                values of change indicator can be: last_7_days, last_15_days
                and last_30_days.
            - lead_type (str): The lead type will be API, Online, Offline lead,
                            Organic, Chat, Telephony.
            - counselor_id (list | None): Either None or a list of counselor
                ids which  useful for get lead header information based on
                counselor ids.
            - season (str | None): Either None or unique identifier of season
                which useful for get season-wise data.
            - is_head_counselor (bool): True if the requested user is is_head_counselor. Default is False

        """
        if change_indicator is not None:
            (
                start_date_indicate,
                middle_date,
                previous_date,
            ) = await utility_obj.get_start_date_and_end_date_by_change_indicator(
                change_indicator
            )
            return await self.get_lead_data(
                str(start_date_indicate),
                str(middle_date),
                str(previous_date),
                str(date.today()),
                lead_type,
                counselor_id=counselor_id,
                season=season,
                is_head_counselor=is_head_counselor,
            )

    async def lead_header_helper(
            self,
            lead_type: str | None = None,
            change_indicator: str | None = None,
            date_range: DateRange | None = None,
            counselor_id: list | None = None,
            season: str | None = None,
            is_head_counselor: bool = False,
            cache_change_indicator=None
    ) -> dict:
        """
        Get the lead header data for the lead dashboard.

        Params:
            - lead_type (str): The lead type will be API, Online, Offline lead,
                            Organic, Chat, Telephony.
            - date_range (DateRange | None): Either none or daterange which
                    useful for filter data based on date_range.
                    e.g., {"start_date": "2023-09-07",
                        "end_date": "2023-09-07"}
            - change_indicator (ChangeIndicator | None): Either none or the
                values of change indicator can be: last_7_days, last_15_days
                and last_30_days.
            - counselor_id (list | None): Either None or a list of counselor
                ids which  useful for get lead header information based on
                counselor ids.
            - season (str | None): Either None or unique identifier of season which useful for
                get season-wise data.

        Returns:
            dict: A dictionary which contains lead header information.
        """
        leads_details, students = await self.get_lead_header_aggregate(
            date_range=date_range,
            lead_type=lead_type,
            counselor_id=counselor_id,
            season=season,
            is_head_counselor=is_head_counselor,
        )
        contact_and_not_contact_lead = (
            await self.get_contact_and_not_contact_lead_count(
                date_range=date_range,
                counselor_id=counselor_id,
                season=season,
                is_head_counselor=is_head_counselor,
                students=students
            )
        )
        leads_details.update(contact_and_not_contact_lead)

        filter_application_perc = utility_obj.get_percentage_result(
            leads_details.get("paid_application_lead_type", 0),
            leads_details.get("total_leads_lead_type", 0),
        )
        application_to_provisions_percentage = utility_obj.get_percentage_result(
            leads_details.get("application_to_provisions", 0),
            leads_details.get("form_initiated", 0),
        )
        form_initiated_percentage = utility_obj.get_percentage_result(
            leads_details.get("form_initiated", 0),
            leads_details.get("application", 0)
        )
        payment_initiated_percentage = utility_obj.get_percentage_result(
            leads_details.get("payment_initiated", 0),
            leads_details.get("application", 0),
        )
        leads_details.update(
            {
                "lead_to_application_percentage": filter_application_perc,
                "application_to_provisions_percentage": application_to_provisions_percentage,
                "form_initiated_percentage": form_initiated_percentage,
                "payment_initiated_percentage": payment_initiated_percentage,
            }
        )
        cache_ci_key, ci_data = None, None
        if cache_change_indicator:
            cache_ci_key, ci_data = cache_change_indicator
        if ci_data:
            lead_percentage = ci_data
        else:
            lead_percentage = await self.get_lead_change_indicator(
                change_indicator=change_indicator,
                lead_type=lead_type,
                counselor_id=counselor_id,
                season=season,
                is_head_counselor=is_head_counselor,
            )
            if cache_ci_key:
                await insert_data_in_cache(cache_ci_key, lead_percentage, change_indicator=True)
        if lead_percentage:
            leads_details.update(lead_percentage)
        return leads_details

    async def delete_tag_from_tag(self, delete_tag_data: dict) -> dict:
        """
        Delete tag from student based on student id.

        Params:
            delete_tag_data (dict): A dictionary which contains tag name and
                student id.
                e.g., {"student_id": "123456789012345678901231",
                    "tag": "string"}

        Returns:
            dict: A dictionary which contains information about delete tag from
                student.

        Raises:
            ObjectIdInValid: An exception which occur when student id will
                be wrong.
            DataNotFoundError: An exception which occur when student not
                found based on student id.
        """
        student_id = delete_tag_data.get("student_id", "")
        await utility_obj.is_length_valid(student_id, "Student id")
        student_id = ObjectId(student_id)
        if (
                student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": student_id}
                )
        ) is None:
            raise DataNotFoundError(message="Student", _id=str(student_id))
        lead_tags = student.get("tags", [])
        delete_tag = delete_tag_data.get("tag")
        if not lead_tags:
            return {"message": "No any tag present for student."}
        if delete_tag in lead_tags:
            lead_tags.remove(delete_tag)
            await DatabaseConfiguration().studentsPrimaryDetails.update_one(
                {"_id": student_id}, {"$set": {"tags": lead_tags}}
            )
            await cache_invalidation(api_updated="lead/delete_tag/")
            return {"message": "Tag deleted."}
        return {"message": f"Tag `{delete_tag}` not found for student."}

    async def add_secondary_tertiary_email_phone(
            self,
            student_id: str,
            secondary: str | None,
            tertiary: str | None,
            set_as_default_secondary: bool,
            set_as_default_tertiary: bool,
            phone: bool,
    ) -> None:
        """
        Add secondary and tertiary email or phone number.

        Params:
          - student_id (str): Unique id of student.
          - secondary (str): Secondary email or phone.
          - tertiary (str): Tertiary email or phone.
          - set_as_default_secondary (bool): A boolean value which useful for
            set secondary email or mobile as default.
          - set_as_default_tertiary (bool): A boolean value which useful for
                set tertiary email or mobile as default.
          - phone(bool): True if you need to add phone number false if you need
            to add email.

        Returns: None
        """
        if (
                student_data := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(student_id)}
                )
        ) is None:
            raise DataNotFoundError(student_id, "Student")
        basic_details = student_data.get("basic_details", {})
        basic_details.update(
            {
                "alternate_mobile_number" if phone else "alternate_email": (
                    secondary
                    if secondary is not None
                    else (
                        basic_details.get("alternate_mobile_number", "")
                        if phone
                        else basic_details.get("alternate_email", "")
                    )
                ),
                "tertiary_mobile_number" if phone else "tertiary_email": (
                    tertiary
                    if tertiary is not None
                    else (
                        basic_details.get("tertiary_mobile_number", "")
                        if phone
                        else basic_details.get("teritiary_email", "")
                    )
                ),
                (
                    "secondary_number_set_as_default"
                    if phone
                    else "secondary_email_set_as_default"
                ): (
                    set_as_default_secondary
                    if set_as_default_secondary is not None
                    else (
                        basic_details.get("secondary_number_set_as_default",
                                          False)
                        if phone
                        else basic_details.get(
                            "secondary_email_set_as_default", False)
                    )
                ),
                (
                    "tertiary_number_set_as_default"
                    if phone
                    else "tertiary_email_set_as_default"
                ): (
                    set_as_default_tertiary
                    if set_as_default_tertiary is not None
                    else (
                        basic_details.get("tertiary_number_set_as_default",
                                          False)
                        if phone
                        else basic_details.get("tertiary_email_set_as_default",
                                               False)
                    )
                ),
            }
        )
        current_datetime = datetime.now(timezone.utc)
        student_data["last_user_activity_date"] = current_datetime
        if not student_data.get("first_lead_activity_date"):
            student_data["first_lead_activity_date"] = current_datetime
        await DatabaseConfiguration().studentsPrimaryDetails.update_one(
            {"_id": ObjectId(student_id)}, {"$set": student_data}
        )
