"""
This file contain helper classes and functions related to application wrapper
"""
import datetime
from bson import ObjectId
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration


class ApplicationWrapper:
    """
    A class containing helper classes and functions related to application
    """

    def get_application_data(self):
        """
        get schema information for a student
        """
        return {
            "_id": 0,
            "student_id": {"$toString": "$student_id"},
            "application_id": {"$toString": "$_id"},
            "student_name": {
                "$trim": {
                    "input": {
                        "$concat": [
                            "$student_primary.basic_details.first_name",
                            " ",
                            "$student_primary.basic_details.middle_name",
                            " ",
                            "$student_primary.basic_details.last_name"
                        ]
                    }
                }
            },
            "student_email_id": "$student_primary.basic_details.email",
            "tags": {
                        "$ifNull": ["$student_primary.tags", []]
                    },
            "custom_application_id": "$custom_application_id",
            "mobile_number": "$student_primary.basic_details.mobile_number",
            "lead_stage": "$student_follow_up.lead_stage",
            "course_name": {
                "$concat": ["$course_details.course_name",
                            " in ",
                            "$spec_name1"]},
            "payment_status": "$payment_status"
        }

    async def today_application_count(self, counselor_ids: list,
                                      season: str | None) -> dict:
        """
        Get the count of application data.

        Params:
            - counselor_ids (list): List of counselor ids.
            - season (str | None): Either None or unique identifier of season
                which useful for get season-wise data.

        Returns:
            dict: A dictionary which contains application data.
        """
        today_date = datetime.date.today()
        start_date, end_date = await utility_obj.date_change_format(
            str(today_date), str(today_date))
        result = (DatabaseConfiguration(season=season).studentApplicationForms.
        aggregate(
            [
                {
                    "$match": {
                        "current_stage": {"$gte": 2},
                        **(
                            {"allocate_to_counselor.counselor_id":{"$in": counselor_ids}}
                           if counselor_ids else {}
                           )
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "gd_status": 1,
                        "meetingDetails": 1,
                        "approval_status": 1,
                        "offer_letter": 1
                    }
                },
                {
                    "$lookup": {
                        "from": "leadsFollowUp",
                        "let": {"application_id": "$_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": ["$application_id",
                                                "$$application_id"]
                                    }
                                }
                            },
                            {
                                "$project": {
                                    "_id": 0,
                                    "lead_stage": 1
                                }
                            }
                        ],
                        "as": "student_follow_up"
                    }
                },
                {
                    "$unwind": {
                        "path": "$student_follow_up",
                        "preserveNullAndEmptyArrays": True
                    }
                },
                {
                    "$group": {
                        "_id": "",
                        "from_initiated": {"$sum": 1},
                        "offer_letter": {"$sum": {
                            "$cond": [
                                {"$ifNull": [
                                    "$offer_letter",
                                    False]}, 1, 0]
                        }},
                        "interview_done": {"$sum": {
                            "$cond": [
                                {"$ifNull": [
                                    "$approval_status",
                                    False]}, 1, 0]
                        }},
                        "gd_done": {"$sum": {
                            "$cond": [
                                {"$eq": [
                                    "$gd_status.status",
                                    "Done"]}, 1, 0]
                        }},
                        "upcoming_interview": {"$sum": {
                            "$cond": [
                                {"$gte": [
                                    "$meetingDetails"
                                    ".booking_date", start_date]}, 1, 0
                            ]
                        }},
                        "upcoming_gd": {"$sum": {
                            "$cond": {
                                "if": {
                                    "$eq": [
                                        "$meetingDetails."
                                        "slot_type", "GD"]},
                                "then": {"$cond": {
                                    "if": {"$gte": ["meetingDetails"
                                                    ".booking_date",
                                                    start_date]},
                                    "then": 1,
                                    "else": 0
                                }},
                                "else": 0}}},
                        "untouched_lead": {"$sum": {
                            "$cond": {
                                "if": {
                                    "$eq": ["$student_follow_up.lead_stage",
                                            "Fresh Lead"]},
                                "then": 1,
                                "else": 0}}
                        }
                    }
                }
            ]
        ))
        async for data in result:
            if data is None:
                return {}
            return data
        return {}

    # ToDO - we can segregate below function
    async def get_application_data_count(self, lead_data: str,
                                         payload: dict | None = None,
                                         page_num: int | None = None,
                                         page_size: int | None = None,
                                         counselor_ids: list | None = None,
                                         season: str | None = None
                                         ):
        """
            Get the application data from the database based on lead data
            params:
                lead_data (str): Field recognize by the application data
                payload (dict): get the filter payload
                page_num (int): Get the page number
                page_size (int): Get the page size
                counselor_ids (list): List of counselor ids
                - season (str | None): Either None or unique identifier of
                    season which useful for get season-wise data.
            returns:
                response: A dictionary of lead data
        """
        skip, limit = await utility_obj.return_skip_and_limit(
            page_num, page_size)
        today_date = datetime.date.today()
        start_date, end_date = await utility_obj.date_change_format(
            str(today_date), str(today_date))
        base_match = {
                    "current_stage": {"$gte": 2}
                }
        if lead_data == "gd_done":
            base_match.update({"gd_status.status": "Done"})
        if lead_data == "interview_done":
            base_match.update({"approval_status": {"$exists": True}})
        if lead_data == "upcoming_interview":
            base_match.update(
                {"meetingDetails.booking_date": {"$gte": start_date}})
        if lead_data == "upcoming_gd":
            base_match.update(
                {"meetingDetails.booking_date": {"$gte": start_date},
                 "meetingDetails.slot_type": "GD"})
        if lead_data == "offer_letter":
            base_match.update({"offer_letter": {"$exists": True}})
        if payload.get("payment_status") not in ["", None, []]:
            base_match.update({"payment_info.status":
                                   payload.get("payment_status")})
        elif ((payload.get("lead_stage") not in ["", None, []]) or
              (payload.get("is_verify") not in ["", None])):
            base_match.update({"payment_info.status": {"$ne": "captured"}})
        if counselor_ids:
            base_match.update({"allocate_to_counselor.counselor_id":
                                   {"$in": counselor_ids}})
        if payload.get("course_wise") not in ["", None, []]:
            course_filter = []
            for course in payload.get("course_wise", []):
                course_lst = []
                if course.get("course_id") not in ["", None]:
                    course_lst.append(
                        {"course_id": {
                            "$eq": ObjectId(course.get("course_id"))}})
                if course.get("specialization") not in ["", None]:
                    course_lst.append(
                        {"spec_name1": {"$eq": course.get("specialization")}}
                    )
                course_filter.append({"$and": course_lst})
            if course_filter:
                base_match.update({"$or": course_filter})
        unwind_lead_followup = {
                    "path": "$student_follow_up"
                }
        lead_followup_match = {
                                "$expr": {
                                    "$eq": ["$application_id",
                                            "$$application_id"]
                                }
                            }
        if lead_data == "untouched_lead":
            lead_followup_match.update({"lead_stage": "Fresh Lead"})
        else:
            unwind_lead_followup.update({"preserveNullAndEmptyArrays": True})
        if payload.get("lead_stage") not in ["", None, []]:
            lead_followup_match.update(
                {"lead_stage": {"$in": f"{payload.get('lead_stage')}"}})
        elif ((payload.get("payment_status") not in ["", None, []])
              or (payload.get("is_verify") not in ["", None])):
            lead_followup_match.update(
                {"lead_stage": {"$nin": ["Fresh Lead"]}})
        student_primary_followup = {
                                "$expr": {
                                    "$eq": ["$_id", "$$student_id"]
                                }
                            }
        if payload.get("is_verify") not in ["", None]:
            data_bool = True if payload.get(
                "is_verify") == "verified" else False
            student_primary_followup.update({"is_verify": data_bool})
        elif ((payload.get("lead_stage") not in ["", None, []]) or
              (payload.get("payment_status") not in ["", None, []])):
            student_primary_followup.update(
                {"is_verify": False})
        pipeline = [
            {
                "$match": base_match
            },
            {
                "$project": {
                    "_id": 1,
                    "student_id": 1,
                    "course_id": 1,
                    "custom_application_id": 1,
                    "spec_name1": 1,
                    "gd_status": 1,
                    "meetingDetails": 1,
                    "approval_status": 1,
                    "offer_letter": 1,
                    "payment_status": {"$toUpper": {
                        "$ifNull": ["$payment_info.status", ""]
                    }}
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
                                    "$eq": ["$$course_id", "$_id"]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "course_name": 1
                            }
                        }
                    ],
                    "as": "course_details"
                }
            },
            {
                "$unwind": {
                    "path": "$course_details"
                }
            },
            {
                "$lookup": {
                    "from": "leadsFollowUp",
                    "let": {"application_id": "$_id"},
                    "pipeline": [
                        {
                            "$match": lead_followup_match
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "lead_stage": 1
                            }
                        }
                    ],
                    "as": "student_follow_up"
                }
            },
            {
                "$unwind": unwind_lead_followup
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
                        {
                            "$project": {
                                "_id": 0,
                                "basic_details": 1,
                                "tags": 1
                            }
                        }
                    ],
                    "as": "student_primary"
                }
            },
            {
                "$unwind": {
                    "path": "$student_primary"
                }
            },
            {
                "$project": self.get_application_data()
            },
            {
                "$facet": {
                    "paginated_results": [{"$skip": skip},
                                          {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            }
        ]
        result = (DatabaseConfiguration(season=season).studentApplicationForms.
        aggregate(pipeline))
        data_lst, total_data = [], 0
        async for app_data in result:
            if app_data is None:
                return {}
            try:
                total_data = app_data.get("totalCount", [{}])[0].get("count",
                                                                     0)
            except IndexError:
                total_data = 0
            except Exception:
                total_data = 0
            data_lst = app_data.get("paginated_results")
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, total_data,
            "/application_wrapper/application_data_count")
        return {
            "data": data_lst,
            "total": total_data,
            "count": page_size,
            "pagination": response.get("pagination"),
            'message': 'Get call history of counselor.'
        }
