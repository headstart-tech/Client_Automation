"""
This file contain class and functions related to lead wrapper routes
"""
import datetime

from bson.objectid import ObjectId

from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration


class LeadWrapper:
    """
    A class representing a lead wrapper,
    """

    def get_student_data(self):
        """
        get schema information for a student
        """
        return {
            "_id": 0,
            "student_id": {"$toString": "$_id"},
            "totalCount": 1,
            "student_name": {
                "$trim": {
                    "input": {
                        "$concat": [
                            "$basic_details.first_name",
                            " ",
                            "$basic_details.middle_name",
                            " ",
                            "$basic_details.last_name"
                        ]
                    }
                }
            },
            "student_email_id": "$user_name",
            "application_id": {"$toString": "$student_application._id"},
            "custom_application_id": "$student_application"
                                     ".custom_application_id",
            "mobile_number": "$basic_details.mobile_number",
            "lead_stage": {
                                "$ifNull": ["$student_follow_up.lead_stage", "Fresh Lead"]
                            },
            "tags": {
                        "$ifNull": ["$tags", []]
                    },
            "is_verify": "$is_verify",
            "payment_status": "$student_application.payment_status",
            "course_name": {
                "$concat": ["$course_details.course_name",
                            " in ",
                            "$student_application.spec_name1"]},
        }

    async def get_data_val(self):
        """
        return the results of lead data validation
        """
        today_date = datetime.date.today()
        start_date, end_date = await utility_obj.date_change_format(
            str(today_date), str(today_date))
        return {"fresh_lead": "Fresh Lead",
                "admission_confirm": "Admission confirmed",
                "interested": "Interested",
                "follow_up": "Follow-up",
                "today_assigned": {"$gte": start_date, "$lte": end_date}}

    async def get_lead_wrapper(self, lead_data: str, counselor_ids: list,
                               payload: dict | None = None,
                               page_num: int | None = None,
                               page_size: int | None = None,
                               season: str | None = None):
        """
        Get the lead data from the database based on lead data
        params:
            lead_data (str): Field recognize by the lead data
            payload (dict): get the filter payload
            page_num (int): Get the page number
            page_size (int): Get the page size
            - season (str | None): Either None or unique identifier of season
                which useful for get season-wise data.
        returns:
            response: A dictionary of lead data
        """
        skip, limit = await utility_obj.return_skip_and_limit(
            page_num, page_size)
        facet = 1
        facet_pipeline = [
            {"$facet": {"totalCount": [{"$count": "value"}], "pipelineResults": [{"$skip": skip}, {"$limit": limit}]}},
            {"$unwind": "$pipelineResults"},
            {"$unwind": "$totalCount"},
            {
                "$replaceRoot": {
                    "newRoot": {
                        "$mergeObjects": [
                            "$pipelineResults",
                            {"totalCount": "$totalCount.value"},
                        ]
                    }
                }
            }
        ]
        data1 = await self.get_data_val()
        data = data1.get(lead_data.lower())
        base_match = {}
        if counselor_ids:
            base_match.update({
                    "allocate_to_counselor.counselor_id":
                        {"$in": counselor_ids}
                })
        lead_stage = payload.get("lead_stage")
        payment_status = payload.get("payment_status")
        is_verify = payload.get("is_verify")
        if is_verify not in ["", None]:
            base_match.update({
                "is_verify": True if payload.get("is_verify") == "verified"
                else False
            })
        lead_followup_match = {
                                "$expr": {
                                    "$eq": ["$student_id", "$$student_id"]
                                }
                            }
        if lead_data is not None:
            if lead_data.lower() == "today_assigned":
                base_match.update(
                    {"allocate_to_counselor.last_update":
                         data1.get("today_assigned")})
            else:
                lead_followup_match.update({"lead_stage": f"{data}"})
            facet = 4
        if lead_stage not in ["", None, []]:
            lead_followup_match.update(
                {"lead_stage": {"$in": lead_stage}})
            facet = 4
        application_match = {
                                "$expr": {
                                    "$eq": ["$_id", "$$app_id"]
                                }
                            }
        if payment_status not in ["", None, []]:
            application_match.update({"payment_info.status": payment_status})
            facet = 6
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
                application_match.update({"$or": course_filter})
            facet = 8
        pipeline = [
            {
                "$project": {
                    "_id": 1,
                    "user_name": 1,
                    "basic_details": 1,
                    "allocate_to_counselor": 1,
                    "tags": 1
                }
            },
            {
                "$lookup": {
                    "from": "leadsFollowUp",
                    "let": {"student_id": "$_id"},
                    "pipeline": [
                        {
                            "$match": lead_followup_match
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "lead_stage": {
                                "$ifNull": ["$lead_stage", "Fresh Lead"]
                            },
                                "application_id": 1
                            }
                        }
                    ],
                    "as": "student_follow_up"
                }
            },
            {
                "$unwind": {
                    "path": "$student_follow_up"
                }
            },
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": {"app_id": "$student_follow_up.application_id"},
                    "pipeline": [
                        {
                            "$match": application_match
                        },
                        {
                            "$project": {
                                "_id": 1,
                                "custom_application_id": 1,
                                "allocate_to_counselor": 1,
                                "course_id": 1,
                                "spec_name1": 1,
                                "payment_status": {"$toUpper": {
                                    "$ifNull": ["$payment_info.status", ""]
                                }}
                            }
                        }
                    ],
                    "as": "student_application"
                }
            },
            {
                "$unwind": {
                    "path": "$student_application"
                }
            },
            {
                "$lookup": {
                    "from": "courses",
                    "let": {"course_id": "$student_application.course_id"},
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
                "$limit": limit
            },
            {
                "$project": self.get_student_data()
            },
        ]
        if base_match:
            pipeline.insert(0, {
                "$match": base_match
            })
        pipeline = pipeline[:facet] + facet_pipeline + pipeline[facet:]
        result = await (DatabaseConfiguration(season=season).studentsPrimaryDetails.
        aggregate(pipeline)).to_list(None)
        data_lst, total_data = result, 0
        for data in result:
            try:
                total_data = data.get("totalCount", 0)
                break
            except IndexError:
                total_data = 0
            except Exception:
                total_data = 0
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, total_data, "/lead/lead_data_count")
        return {
            "data": data_lst,
            "total": total_data,
            "count": page_size,
            "pagination": response.get("pagination"),
            'message': 'Get call history of counselor.'
        }
