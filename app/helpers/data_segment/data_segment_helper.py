"""
This file contains
"""

import ast
from datetime import datetime

from bson import ObjectId
from fastapi import HTTPException
from fastapi import status
from fastapi.encoders import jsonable_encoder
from meilisearch.errors import MeilisearchCommunicationError, \
    MeilisearchApiError

from app.core.custom_error import DataNotFoundError, CustomError
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.database.configuration import DatabaseConfiguration
from app.dependencies.cryptography import EncryptionDecryption
from app.dependencies.jwttoken import Authentication
from app.dependencies.oauth import is_testing_env, cache_invalidation
from app.helpers.automation.automation_configuration import AutomationHelper

logger = get_logger(__name__)


class data_segment_automation:
    """
    A class contains all function related to the data segment
    """

    async def get_count_current_data(self, data, college_id, skip=None,
                                     limit=None):
        """
        Get the current data segment count of dynamic

        params:
            data (dict): Get the current data segment
            college_id (str): Get the college id of the college

        return:
            total_count of the current data segment
        """
        total_data, data_list = await AutomationHelper().get_data_from_db(
            data, college_id, call_segments=True, skip=skip, limit=limit
        )
        return total_data

    async def get_segment_header(
            self,
            data_segment_id: str,
            date_range=None,
            college_id=None,
    ):
        """
        Get the data segment header details

        params:
            data_segment_id (str): The data segment identifier for this segment
            college_id (dict): The college identifier for this segment
            date_range (dict): The date range for this segment for this segment

        return:
            response: A dictionary containing the data segment header details
        """
        await utility_obj.is_length_valid(data_segment_id, "data segment id")
        pipeline = [
            {"$match": {"_id": ObjectId(data_segment_id)}},
            {
                "$lookup": {
                    "from": "automation_communicationLog",
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": [
                                        ObjectId(data_segment_id),
                                        "$data_segment_id",
                                    ]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 1,
                                "whatsapp_sent": "$whatsapp_summary." "whatsapp_sent",
                                "sms_sent": "$sms_summary.sms_sent",
                                "email_sent": "$email_summary.email_sent",
                            }
                        },
                        {
                            "$group": {
                                "_id": "",
                                "whatsapp_sent": {
                                    "$sum": {"$ifNull": ["$whatsapp_sent", 0]}
                                },
                                "sms_sent": {
                                    "$sum": {"$ifNull": ["$sms_sent", 0]}},
                                "email_sent": {
                                    "$sum": {"$ifNull": ["$email_sent", 0]}},
                            }
                        },
                    ],
                    "as": "student_data_segment",
                }
            },
            {
                "$unwind": {
                    "path": "$student_data_segment",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            {
                "$lookup": {
                    "from": "rule",
                    "let": {"segment_id": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$in": [
                                        "$$segment_id",
                                        {"$ifNull": ["$data_segment_id", []]},
                                    ]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "automation_id": {"$toString": "$_id"},
                                "automation_name": "$rule_name",
                                "data_type": 1,
                            }
                        },
                    ],
                    "as": "automation_details",
                }
            },
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "linked_automations": {
                        "$ifNull": ["$automation_details", []]},
                    "automation_count": {
                        "$size": {"$ifNull": ["$automation_details", []]}
                    },
                    "data_segment_name": "$data_segment_name",
                    "data_segment_type": {"$ifNull": ["$segment_type", "--"]},
                    "module_name": {"$ifNull": ["$module_name", "--"]},
                    "raw_data_name": {"$ifNull": ["$raw_data_name", "--"]},
                    "created_on": {
                        "$dateToString": {
                            "format": "%Y-%m-%d %H:%M:%S",
                            "date": "$created_on",
                            "timezone": "+05:30",
                        }
                    },
                    "initial_count": {"$ifNull": ["$count_at_origin", 0]},
                    "current_data_count": {"$ifNull": ["$data_count", 0]},
                    "filters": "$filters",
                    "advance_filters": "$advance_filters",
                    "period": "$period",
                    "email_count": {
                        "$ifNull": ["$communication_count.email", 0]},
                    "sms_count": {"$ifNull": ["$communication_count.sms", 0]},
                    "whatsapp_count": {
                        "$ifNull": ["$communication_count.whatsapp", 0]
                    },
                }
            }
        ]
        if date_range is not None:
            date_range = jsonable_encoder(date_range)
            if len(date_range) > 1:
                start_date, end_date = await utility_obj.date_change_format(
                    date_range.get("start_date"), date_range.get("end_date")
                )
                pipeline[1].get("$lookup", {}).get("$pipeline", [{}])[0].get(
                    "$match", {}
                ).update(
                    {"created_on": {"$gte": start_date, "$lte": end_date}})
        result = DatabaseConfiguration().data_segment_collection.aggregate(
            pipeline)
        async for data in result:
            if data is None:
                return {}
            filters = data.get("filters", {})
            counselor_ids = filters.get("counselor_id")
            course_ids = filters.get("course", {}).get("course_id")
            if course_ids:
                data["filters"]["course"]["course_id"] = [
                    str(course_id) for course_id in course_ids
                ]
            if counselor_ids:
                data["filters"]["counselor_id"] = [
                    str(counselor_id) for counselor_id in counselor_ids
                ]
            if data.get("data_segment_type", "").lower() == "dynamic":
                data["current_data_count"] = await self.get_count_current_data(
                    data, college_id=college_id, skip=0, limit=10
                )
            return data
        return {}

    async def get_lead_application_wise_let_json(self, module_name):
        """
        Get the lead application

        param:
            module_name (str): Get the name of module name

        return:
             module type let json data
        """
        if module_name.lower() == "lead":
            return {"student_id": "$student_id"}
        else:
            return {"application_id": "$application_id"}

    async def get_lead_application_wise_match(self, module_name, db_name):
        """
        Get the aggregation part of the application or lead application

        param:
            module_name (str): the name of the module

        return:
            module type json
        """
        if module_name.lower() == "lead":
            if db_name == "application":
                return {"$match": {
                    "$expr": {"$eq": ["$student_id", "$$student_id"]}}}
            elif db_name == "lead_details":
                return {"$match": {
                    "$expr": {"$eq": ["$student_id", "$$student_id"]}}}
        else:
            if db_name == "application":
                return {
                    "$match": {"$expr": {"$eq": ["$_id", "$$application_id"]}}}
            elif db_name == "lead_details":
                return {
                    "$match": {
                        "$expr": {
                            "$eq": ["$application_id", "$$application_id"]}
                    }
                }

    async def project_static_data(self, module_name: str):
        """
        Get the project stage by module name.

        Params:\n
            - module_name (str): Name of the module.

        Returns:\n
           - dict: A dictionary which contains information about project
           stage which helpful further in the aggregation pipeline.
        """

        if module_name.lower() == "lead":
            project = {
                "$project": {
                    "_id": 0,
                    "application_id": {
                        "$map": {
                            "input": "$student_application",
                            "as": "app",
                            "in": {"$toString": "$$app._id"},
                        }
                    },
                    "student_id": {"$toString": "$student_primary._id"},
                    "email": "$student_primary.user_name",
                    "mobile_number": "$student_primary.basic_details.mobile_number",
                    "tags": "$student_primary.tags",
                    "custom_application_id": "$student_application"
                                             ".custom_application_id",
                    "lead_stage": "$lead_details.lead_stage",
                    "payment_status": "$student_application.payment_info.status",
                    "student_name": {
                        "$trim": {
                            "input": {
                                "$concat": [
                                    "$student_primary.basic_details.first_name",
                                    " ",
                                    "$student_primary.basic_details.middle_name",
                                    " ",
                                    "$student_primary.basic_details.last_name",
                                ]
                            }
                        }
                    },
                    "state": {
                        "$toString": "$student_primary.address_details."
                                     "communication_address.state.state_name"
                    },
                    "state_code": "$student_primary.address_details."
                                  "communication_address.state.state_code",
                    "city": "$student_primary.address_details."
                            "communication_address.city.city_name",
                    "source_name": "$student_primary.source."
                                   "primary_source.utm_source",
                    "source_type": "$student_primary.source."
                                   "primary_source.utm_source",
                    "registration_date": {
                        "$map": {
                            "input": "$student_application.enquiry_date",
                            "as": "datetime",
                            "in": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d %H:%M:%S",
                                    "date": "$$datetime",
                                    "timezone": "+05:30",
                                }
                            },
                        }
                    },
                    "lead_type": "$student_primary.source." "primary_source.lead_type",
                    "counselor_name": "$student_application."
                                      "allocate_to_counselor.counselor_name",
                    "application_stage": {
                        "$map": {
                            "input": "$student_application.declaration",
                            "as": "declarations",
                            "in": {
                                "$cond": ["$$declarations", "completed",
                                          "incomplete"]
                            },
                        }
                    },
                    "verification": {
                        "$cond": [
                            "$student_primary.is_verify",
                            "verified",
                            "unverified",
                        ]
                    },
                    "utm_campaign": "$student_primary.source"
                                    ".primary_source.utm_campaign",
                    "utm_medium": "$student_primary.source"
                                  ".primary_source.utm_medium",
                    "lead_sub_stage": {
                        "$ifNull": ["$lead_details.lead_stage_label", ""]
                    },
                    "course_name": {
                        "$map": {
                            "input": {
                                "$objectToArray": "$student_primary.course_details"
                            },
                            "as": "course",
                            "in": {
                                "$concat": [
                                    "$$course.k",
                                    {
                                        "$cond": [
                                            {
                                                "$eq": [
                                                    {
                                                        "$arrayElemAt": [
                                                            "$$course.v.specs"
                                                            ".spec_name",
                                                            0,
                                                        ]
                                                    },
                                                    None,
                                                ]
                                            },
                                            "",
                                            {
                                                "$cond": [
                                                    {
                                                        "$in": [
                                                            "$$course.k",
                                                            ["Master",
                                                             "Bachelor"],
                                                        ]
                                                    },
                                                    {
                                                        "$concat": [
                                                            " of ",
                                                            {
                                                                "$arrayElemAt": [
                                                                    "$$course.v"
                                                                    ".specs"
                                                                    ".spec_name",
                                                                    0,
                                                                ]
                                                            },
                                                        ]
                                                    },
                                                    {
                                                        "$concat": [
                                                            " in ",
                                                            {
                                                                "$arrayElemAt": [
                                                                    "$$course.v"
                                                                    ".specs"
                                                                    ".spec_name",
                                                                    0,
                                                                ]
                                                            },
                                                        ]
                                                    },
                                                ]
                                            },
                                        ]
                                    },
                                ]
                            },
                        }
                    },
                }
            }
        else:
            project = {
                "$project": {
                    "_id": 0,
                    "application_id": {
                        "$toString": "$student_application._id"},
                    "student_id": {"$toString": "$student_primary._id"},
                    "email": "$student_primary.user_name",
                    "mobile_number": "$student_primary.basic_details" ".mobile_number",
                    "tags": "$student_primary.tags",
                    "custom_application_id": "$student_application"
                                             ".custom_application_id",
                    "lead_stage": "$lead_details.lead_stage",
                    "payment_status": "$student_application.payment_info" ".status",
                    "student_name": {
                        "$trim": {
                            "input": {
                                "$concat": [
                                    "$student_primary.basic_details.first_name",
                                    " ",
                                    "$student_primary.basic_details" ".middle_name",
                                    " ",
                                    "$student_primary.basic_details.last_name",
                                ]
                            }
                        }
                    },
                    "course_name": {
                        "$concat": [
                            "$course_details.course_name",
                            " in ",
                            "$student_application.spec_name1",
                        ]
                    },
                    "state": {
                        "$toString": "$student_primary.address_details."
                                     "communication_address.state.state_name"
                    },
                    "state_code": "$student_primary.address_details."
                                  "communication_address.state.state_code",
                    "city": "$student_primary.address_details."
                            "communication_address.city.city_name",
                    "source_name": "$student_primary.source."
                                   "primary_source.utm_source",
                    "source_type": "$student_primary.source."
                                   "primary_source.utm_source",
                    "registration_date": {
                        "$dateToString": {
                            "format": "%Y-%m-%d %H:%M:%S",
                            "date": "$student_application" ".enquiry_date",
                        }
                    },
                    "lead_type": "$student_primary.source." "primary_source.lead_type",
                    "counselor_name": "$student_application."
                                      "allocate_to_counselor.counselor_name",
                    "application_stage": {
                        "$cond": [
                            "$student_application.declaration",
                            "completed",
                            "incomplete",
                        ]
                    },
                    "verification": {
                        "$cond": [
                            "$student_primary.is_verify",
                            "verified",
                            "unverified",
                        ]
                    },
                    "utm_campaign": "$student_primary.source"
                                    ".primary_source.utm_campaign",
                    "utm_medium": "$student_primary.source"
                                  ".primary_source.utm_medium",
                    "lead_sub_stage": {
                        "$ifNull": ["$lead_details.lead_stage_label", ""]
                    },
                }
            }
        return project

    async def course_lookup(self, module_name):
        """
        get the course aggregation based on the given module name
        """
        if module_name.lower() == "application":
            return {
                "$lookup": {
                    "from": "courses",
                    "let": {"course_id": "$student_application.course_id"},
                    "pipeline": [
                        {"$match": {
                            "$expr": {"$eq": ["$$course_id", "$_id"]}}},
                        {"$project": {"_id": 0, "course_name": 1}},
                    ],
                    "as": "course_details",
                }
            }
        return

    async def lead_followup_unwind(self, module_name, db_name):
        """
        Get the unwind aggregation based on module_name and db_name
        """
        if module_name.lower() == "application":
            if db_name == "lead_details":
                return {
                    "$unwind": {
                        "path": "$lead_details",
                        "preserveNullAndEmptyArrays": True,
                    }
                }
            if db_name == "course_details":
                return {
                    "$unwind": {
                        "path": "$course_details",
                        "preserveNullAndEmptyArrays": True,
                    }
                }
        return

    async def static_segment_details(
            self,
            data_segment_id,
            fresh_lead=None,
            payment_status=None,
            is_verify=None,
            search=None,
            skip=None,
            limit=None,
            basic_filter=None,
            payload=None,
            college_id=None,
            numbers=False,
            emails=False
    ):
        """
        Get the student details

        params:
            data_segment_id (str): Get the data segment id
            fresh_lead (bool): Get the filter status of the lead stage
            payment_status (bool): Get the payment status of the student filter
            is_verify (bool): Get the filter status of the student
            search (bool): Get the search term of the student
            skip (None): Number of the skip of the student
            limit (int): Number of the student
        """
        if (
                data_segment_details := await DatabaseConfiguration().data_segment_collection.find_one(
                    {"_id": ObjectId(data_segment_id)}
                )
        ) is None:
            data_segment_details = {}
        module_name = data_segment_details.get("module_name", "")
        pipeline = [
            {"$match": {"data_segment_id": ObjectId(data_segment_id)}},
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": await self.get_lead_application_wise_let_json(
                        module_name),
                    "pipeline": [
                        await self.get_lead_application_wise_match(
                            module_name, "application"
                        ),
                        {
                            "$project": {
                                "_id": 1,
                                "student_id": 1,
                                "custom_application_id": 1,
                                "payment_info": 1,
                                "allocate_to_counselor": 1,
                                "spec_name1": 1,
                                "course_id": 1,
                                "enquiry_date": 1,
                                "declaration": 1,
                            }
                        },
                    ],
                    "as": "student_application",
                }
            },
            {
                "$lookup": {
                    "from": "studentsPrimaryDetails",
                    "let": {"student_id": "$student_id"},
                    "pipeline": [
                        {"$match": {
                            "$expr": {"$eq": ["$_id", "$$student_id"]}}},
                        {
                            "$project": {
                                "_id": 1,
                                "basic_details": 1,
                                "address_details": 1,
                                "user_name": 1,
                                "is_verify": 1,
                                "tags": 1,
                                "source": 1,
                                "course_details": 1,
                                "allocate_to_counselor": 1,
                            }
                        },
                    ],
                    "as": "student_primary",
                }
            },
            {"$unwind": {"path": "$student_primary"}},
            {
                "$lookup": {
                    "from": "leadsFollowUp",
                    "let": await self.get_lead_application_wise_let_json(
                        module_name),
                    "pipeline": [
                        await self.get_lead_application_wise_match(
                            module_name, "lead_details"
                        ),
                        {
                            "$project": {
                                "_id": 0,
                                "lead_stage": 1,
                                "lead_stage_label": 1,
                            }
                        },
                    ],
                    "as": "lead_details",
                }
            },
        ]
        if module_name.lower() == "application":
            pipeline.append(
                await self.lead_followup_unwind(module_name, "lead_details")
            )
            pipeline.append(await self.course_lookup(module_name))
            pipeline.append(
                await self.lead_followup_unwind(module_name, "course_details")
            )
        pipeline.append(await self.project_static_data(module_name))

        if module_name.lower() == "application":
            pipeline.insert(2, {"$unwind": {"path": "$student_application"}})
        if is_verify:
            pipeline[3].get("$lookup", {}).get("pipeline", [{}])[0].get(
                "$match", {}
            ).update({"is_verify": True})
        if payment_status:
            pipeline[1].get("$lookup", {}).get("pipeline", [{}])[0].get(
                "$match", {}
            ).update({"payment_info.status": "captured"})
        if fresh_lead:
            pipeline[5].get("$lookup", {}).get("pipeline", [{}])[0].get(
                "$match", {}
            ).update({"lead_stage": "Fresh Lead"})
        if search:
            search_match = {
                "$match": {
                    "$or": [
                        {"student_name": {"$regex": search, "$options": "i"}},
                        {"email": {"$regex": search, "$options": "i"}},
                        {"mobile_number": {"$regex": search, "$options": "i"}},
                    ]
                }
            }
            pipeline.append(search_match)
        if basic_filter in [None, False]:
            if skip is not None and limit is not None:
                if fresh_lead or payment_status or is_verify or search:
                    pipeline.append(
                        {
                            "$facet": {
                                "paginated_results": [{"$skip": skip},
                                                      {"$limit": limit}],
                                "totalCount": [{"$count": "count"}],
                            }
                        }
                    )
                else:
                    pipeline.insert(1, {"$skip": skip})
                    pipeline.insert(2, {"$limit": limit})
                    pipeline.append(
                        {
                            "$facet": {
                                "paginated_results": [],
                                "totalCount": [{"$count": "count"}],
                            }
                        }
                    )
            else:
                pipeline.append(
                    {
                        "$facet": {
                            "paginated_results": [],
                            "totalCount": [{"$count": "count"}],
                        }
                    }
                )
        else:
            pipeline.append(
                {
                    "$facet": {
                        "paginated_results": [],
                        "totalCount": [{"$count": "count"}],
                    }
                }
            )
        result = DatabaseConfiguration().data_segment_mapping_collection.aggregate(
            pipeline
        )
        total_count, student_mapped_data = 0, []
        async for data in result:
            try:
                total_count = data.get("totalCount", [{}])[0].get("count", 0)
            except IndexError:
                total_count = 0
            if fresh_lead or payment_status or is_verify or search:
                pass
            else:
                total_count = await DatabaseConfiguration().data_segment_mapping_collection.count_documents(
                    {"data_segment_id": ObjectId(data_segment_id)}
                )

            if basic_filter:
                if module_name.lower() == "lead":
                    student_ids = [
                        ObjectId(x.get("student_id"))
                        for x in data.get("paginated_results", [])
                    ]
                    (
                        total_count,
                        student_mapped_data,
                    ) = await AutomationHelper().get_lead_details(
                        segment=data_segment_details,
                        college_id=college_id,
                        data_segments=True,
                        data_segment_id=data_segment_id,
                        skip=skip,
                        limit=limit,
                        search=search,
                        call_segments=True,
                        student_ids=student_ids,
                        basic_filter=basic_filter,
                        payload=payload,
                        static=True,
                    )
                if module_name.lower() == "application":
                    application_id = [
                        ObjectId(x.get("application_id"))
                        for x in data.get("paginated_results", [])
                        if len(x.get("application_id", "")) == 24
                    ]
                    (
                        total_count,
                        student_mapped_data,
                    ) = await AutomationHelper().get_application_details(
                        segment=data_segment_details,
                        college_id=college_id,
                        data_segments=True,
                        data_segment_id=data_segment_id,
                        skip=skip,
                        limit=limit,
                        search=search,
                        call_segments=True,
                        application_ids=application_id,
                        basic_filter=basic_filter,
                        payload=payload,
                        static=True,
                    )
            else:
                student_mapped_data = data.get("paginated_results", [])
        if emails:
            student_mapped_data = [data.get("email") for data in
                                   student_mapped_data
                                   if data.get("email") is not None]
        elif numbers:
            student_mapped_data = [data.get("mobile_number") for data in
                                   student_mapped_data
                                   if data.get("mobile_number") is not None]
        return total_count, student_mapped_data

    async def student_mapped_details(
            self,
            data_segment_id: str,
            page_num: int = None,
            page_size: int = None,
            is_verify: bool = False,
            payment_status: bool = False,
            fresh_lead: bool = False,
            search: str = None,
            route_name="/data_segment/student_mapped/",
            permission: str | None = None,
            user: str = None,
            payload=None,
            basic_filter: bool = None,
            college_id: str = None,
            numbers: bool = False,
            emails: bool = False,
            download: bool = None,
    ):
        """
        get the student mapped details who mapped with data segment
        params:
            data_segment_id (str): get the data segment id
            is_verify(bool): True if is_verify  filter is given
            payment_status(bool): True if required payment_filter
            fresh_lead(bool): True if required fresh lead filter
            search(str): The str which is searched for
            page_num(int): The page number for pagination
            page_size(int): The page size for pagination
            route_name(str): Route  name for pagination
        returns:
            response: A list contains the student mapped details
        """
        skip = limit = None
        if page_num is not None and page_size is not None:
            skip, limit = await utility_obj.return_skip_and_limit(
                page_num=page_num, page_size=page_size
            )
        await utility_obj.is_length_valid(data_segment_id, "data segment id")
        if (
                segment_details := await DatabaseConfiguration().data_segment_collection.find_one(
                    {"_id": ObjectId(data_segment_id)}
                )
        ) is None:
            raise DataNotFoundError(_id=data_segment_id,
                                    message="Data Segment id")
        data_type = segment_details.get("module_name", "")
        if not permission:
            permission = "".join(
                [
                    data.get("permission")
                    for data in segment_details.get("shared_with", [])
                    if str(data.get("email")) == user
                ]
            )
        if data_type.lower().replace(" ", "_") == "raw_data":
            (
                total_count,
                student_mapped_data,
            ) = await AutomationHelper().get_data_from_db(
                segment_details,
                college_id,
                skip=skip,
                limit=limit,
                basic_filter=basic_filter,
                payload=payload,
                search=search,
                call_segments=True,
                data_segments=True,
                numbers=numbers,
                emails=emails
            )
        elif segment_details.get("segment_type", "").lower() == "dynamic":
            if is_verify:
                segment_details["filters"]["is_verify"] = "verified"
            if payment_status:
                segment_details["filters"]["payment_status"] = (
                    segment_details.get("filters", {})
                    .get("payment_status", [])
                    .append("captured")
                )
            if fresh_lead:
                segment_details["filters"]["lead_name"].append(
                    {"name": "Fresh Lead"})
            (
                total_count,
                student_mapped_data,
            ) = await AutomationHelper().get_data_from_db(
                segment_details,
                college_id,
                skip=skip,
                limit=limit,
                basic_filter=basic_filter,
                payload=payload,
                search=search,
                call_segments=True,
                numbers=numbers,
                emails=emails
            )
        else:
            (total_count,
             student_mapped_data) = await self.static_segment_details(
                data_segment_id,
                fresh_lead=fresh_lead,
                college_id=college_id,
                payment_status=payment_status,
                is_verify=is_verify,
                search=search,
                skip=skip,
                limit=limit,
                basic_filter=basic_filter,
                payload=payload,
                numbers=numbers,
                emails=emails
            )
        if download is True:
            return student_mapped_data
        response = await utility_obj.pagination_in_aggregation(
            page_num=page_num,
            page_size=page_size,
            data_length=total_count,
            route_name=route_name,
        )
        return {
            "data": student_mapped_data,
            "total": total_count,
            "close": False if segment_details.get("enabled", True) else True,
            "permission": permission if permission not in [None,
                                                           ""] else "viewer",
            "data_type": data_type,
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Get users timeline.",
        }

    async def get_template(self, token, message: str | None):
        """
        Create a template for sending data segment link to the user
        params:
            token (str): Get the token for the segment to send to the user
            message (str): Message to send to the user

        return:
            response: Template (html) with data segment token
        """
        return """
            <html lang="en">
                <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Data segment link</title>
                </head>
                <body>
                <p>Link: {}</p>
                <p>Message: {}</p>
                </body>
                </html>
            """.format(
            token, message
        )

    async def encrypt_data_segment(
            self, data_segment_id: str | None, data_segment: dict | None
    ):
        """
        Encrypt data segment id with the Fernet cryptography

        params:
            data_segment_id (str): Get the data segment id for to encrypt
                and check the data segment already created data segment link
            data_segment (dict): Get the data segment details.

        return:
            response: return the encrypted data segment id
        """
        data_segment_url = data_segment.get("data_segment_url")
        if data_segment_url is None:
            data = {"dg": "data_segment",
                    "data_segment_id": str(data_segment_id)}
            token = await EncryptionDecryption().encrypt_message_no_time(
                str(data))
            token = token.decode("utf-8")
            data_segment_url = (
                f"https://{settings.base_path}/data_segment/dkper/{token}/"
            )
        return data_segment_url

    async def create_data_segment_link(
            self,
            user_id: list | None,
            data_segment_id: str | None,
            segment_permission: str | None,
            current_user: str | None,
            ip_address: str | None,
            college: dict | None,
            message: str | None,
            background_task=None,
            user=None,
    ):
        """
        Create a link to data segment for a user

        params:
            user_id (dict): Get the user details from the database.
            data_segment_id (str): Get the data segment id for
                    the particular data segment details.
            segment_permission (str): Get the data segment permission
                    for read and write the data segment
            college (dict): Get the details of the data segment
            current_user (dict): Get the current user.
            ip_address (str): Get the ip_address of who is accessing the API.
            message (str): Get the message send to the user

        returns:
            response: Data segment link has been created and sent to the user
        """
        await utility_obj.is_length_valid(data_segment_id, "Data segment Id")
        if (
                data_segment := await DatabaseConfiguration().data_segment_collection.find_one(
                    {"_id": ObjectId(data_segment_id)}
                )
        ) is None:
            raise DataNotFoundError(data_segment_id, "Data Segment Id")
        shared_with = data_segment.get("shared_with", [])
        authentication_obj = Authentication()
        token = await authentication_obj.create_access_token(
            data={"sub": str(data_segment_id)}
        )
        token = f"{settings.user_base_path}data-segment-details/{token}"
        message = f"<span class='notification-inner'>{utility_obj.name_can(user)} ({await utility_obj.get_role_name_in_proper_format(user.get('role', {}).get('role_name', ''))})</span> has shared a data-segment with you - <span class='notification-inner'>{data_segment.get('data_segment_name')}</span>"
        for _id in user_id:
            await utility_obj.is_length_valid(_id, "User Id")
            if (
                    user_details := await DatabaseConfiguration().user_collection.find_one(
                        {"_id": ObjectId(_id)}
                    )
            ) is None:
                raise DataNotFoundError(_id, "User Id")
            check_data = [
                data for data in shared_with if str(data.get("user_id")) == _id
            ]
            if len(check_data) == 0:
                shared_with.append(
                    {
                        "user_id": ObjectId(user_details.get("_id")),
                        "email": user_details.get("user_name"),
                        "role": user_details.get("role", {}).get("role_name"),
                        "name": utility_obj.name_can(user_details),
                        "permission": segment_permission.lower(),
                        "created_date": datetime.utcnow(),
                    }
                )
            else:
                raise CustomError("data_segment shared user already exists")
            data = {"shared_with": shared_with}
            if data_segment.get("data_segment_url") is None:
                data["data_segment_url"] = token
            await DatabaseConfiguration().data_segment_collection.update_one(
                {"_id": ObjectId(data_segment_id)}, {"$set": data}
            )
            segment_list = user_details.get("segment_list", [])
            segment_list.append(ObjectId(data_segment_id))
            segment_list = list(set(segment_list))
            await DatabaseConfiguration().user_collection.update_one(
                {_id: ObjectId(_id)},
                {"$set": {"data_segment_list": segment_list}}
            )
            await cache_invalidation(api_updated="updated_user", user_id=user_details.get("email"))
            template = await self.get_template(token=token, message=message)
            email_ids = [user_details.get("user_name")]
            if not is_testing_env():
                await utility_obj.publish_email_sending_on_queue(data={
                    "email_preferences": college.get("email_preferences", {}),
                    "email_type": "transactional",
                    "email_ids": email_ids,
                    "subject": "Data segment Link",
                    "template": template,
                    "event_type": "email",
                    "event_status": f"sent to {utility_obj.name_can(user_details)}",
                    "event_name": "Data Segment",
                    "current_user": current_user,
                    "ip_address": ip_address,
                    "payload": {
                            "content": "Data Segment Accessible Link",
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
            await utility_obj.update_notification_db(
                event="Data Segment Assignment",
                data={
                    "message": message,
                    "user_id": ObjectId(_id),
                    "data_segment_redirect_link": token,
                    "data_segment_id": ObjectId(data_segment_id)
                },
            )
        return {
            "data": "Data segment link has been created" " and sent to the user"}

    async def get_decrypted_data(self, token, page_num=0, page_size=25,
                                 user=None):
        """
        Get the decrypted data from the token

        params:
            token (str): get the token for decrypt the data.
            page_num: Get the page number of the data segment student list.
            page_size (int): Get the limit of the count of students.
            user (dict): get the user details of current user

        return:
            response: a list contain the student data based particular
             data segment.
        """
        try:
            dt = await EncryptionDecryption().decrypt_message_no_time(token)
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid token")
        dt = ast.literal_eval(dt)
        if dt.get("dg") != "data_segment":
            raise HTTPException(status_code=410, detail="url has expired")
        data_segment_id = dt.get("data_segment_id")
        if (
                segment_details := await DatabaseConfiguration().data_segment_collection.find_one(
                    {"_id": ObjectId(data_segment_id)}
                )
        ) is None:
            raise DataNotFoundError(data_segment_id, "Data Segment Id")
        data_permission = "".join(
            [
                data.get("permission")
                for data in segment_details.get("shared_with", [])
                if str(data.get("user_id")) == user.get("_id")
            ]
        )
        return await self.student_mapped_details(
            page_num=page_num,
            page_size=page_size,
            data_segment_id=data_segment_id,
            route_name="/data_segment/dkper",
            permission=data_permission,
        )

    async def get_raw_data_details(
            self, search_string: str | None, page_num: int | None,
            page_size: int | None
    ):
        """
        Get the raw data details and search the string

        params:
            - search_string (str): The search string to search for student
            - page_num (int): Get the integer number, e.q. 1,2,3
            - page_size (int): Get the integer number count of student showing,
                    e.q. 1,2,3

        return:
            - A list of the raw data details with pagination
        """
        pipeline = [
            {
                "$lookup": {
                    "from": "data_segment_student_mapping",
                    "let": {"student_id": "$_id"},
                    "pipeline": [
                        {"$match": {"$expr": {
                            "$eq": ["$student_id", "$$student_id"]}}},
                        {"$project": {"_id": 0, "automation_id": 1}},
                    ],
                    "as": "student_mapped_details",
                }
            },
            {
                "$unwind": {
                    "path": "$student_mapped_details",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "student_id": {"$toString": "$_id"},
                    "student_name": {
                        "$trim": {
                            "input": {
                                "$concat": [
                                    "$other_field.first_name",
                                    " ",
                                    "$other_field.last_name",
                                ]
                            }
                        }
                    },
                    "student_email_id": "$mandatory_field.email",
                    "student_mobile_no": {
                        "$toString": "$mandatory_field.mobile_number"
                    },
                    "automation_id": {
                        "$map": {
                            "input": {
                                "$ifNull": [
                                    "$student_mapped_details.automation_id",
                                    []]
                            },
                            "as": "cd",
                            "in": {"$toString": "$$cd"},
                        }
                    },
                    "automation_count": {
                        "$size": {
                            "$ifNull": [
                                "$student_mapped_details.automation_id", []]
                        }
                    },
                }
            },
        ]
        if search_string is not None:
            pipeline.append(
                {
                    "$match": {
                        "$or": [
                            {
                                "student_name": {
                                    "$regex": search_string,
                                    "$options": "i",
                                }
                            },
                            {
                                "student_email_id": {
                                    "$regex": search_string,
                                    "$options": "i",
                                }
                            },
                            {
                                "student_mobile_no": {
                                    "$regex": search_string,
                                    "$options": "i",
                                }
                            },
                        ]
                    }
                }
            )
        skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                              page_size)
        pipeline.append(
            {
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            }
        )
        result = DatabaseConfiguration().raw_data.aggregate(pipeline)
        total_data, raw_data = 0, []
        async for data in result:
            try:
                total_data = data.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
            raw_data = data.get("paginated_results", [])
        response = await utility_obj.pagination_in_aggregation(
            page_num=page_num,
            page_size=page_size,
            data_length=total_data,
            route_name="/data_segment/search_for_add_data_segment/",
        )
        return {
            "data": raw_data,
            "total": total_data,
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Get raw data details.",
        }

    async def get_student_details_for_search(
            self,
            data_type: str | None,
            college_id: str | None,
            search_string: str | None,
            page_num: int | None,
            page_size: int | None,
            payload=None,
            client=None,
    ):
        """
        Get the search student details from the meili search and
            database based on data type

        params:
            - search_string (str): The search string to search for student
            - College_id (str): Get the college id based on search based on
                college
            - data_type (str): The get and search student details based
               on data type
            - page_num (int): Get the integer number, e.q. 1,2,3
            - page_size (int): Get the integer number count of student showing,
                    e.q. 1,2,3
            - payload (dict): Payload containing filter parameters for
                lead_stage, verified and payment_status
            - client (generator): get the connection for meili search server

        return:
            - A list of student details based on data type
        """
        if payload is None:
            payload = {}
        payload = jsonable_encoder(payload)
        filters = []
        filters.append([f"college_id = {college_id}"])
        temp_dict = {
            "filter": filters,
            "showMatchesPosition": True,
            "attributesToHighlight": ["*"],
            "highlightPreTag": "<span class='search-query-highlight'>",
            "highlightPostTag": "</span>",
            "hitsPerPage": page_size,
            "page": page_num,
        }
        name = f"{settings.client_name.lower().replace(' ', '_')}_{settings.current_season.lower()}"
        if payload.get("verified"):
            filters.append([f"is_verified = verified"])
        try:
            if data_type.lower() in ["application", "lead"]:
                if payload.get("lead_stage"):
                    filters.append([f"lead_type = 'Fresh Lead'"])
                if payload.get("payment_status"):
                    filters.append([f"payment_status = captured"])
                data = client.index(f"{name}_student_application").search(
                    search_string, temp_dict
                )
            else:
                return await self.get_raw_data_details(
                    search_string=search_string, page_num=page_num,
                    page_size=page_size
                )

            return {
                "data": data.get("hits"),
                "total": data.get("totalHits"),
                "count": data.get("hitsPerPage"),
                "page_num": data.get("page"),
                "message": "Fetched student records successfully",
            }
        except MeilisearchCommunicationError as error:
            logger.error(f"Error - {str(error.args)}")
            raise HTTPException(
                status_code=404, detail="Meilisearch server is not running."
            )
        except MeilisearchApiError as error:
            logger.error(f"Error - {str(error.args)}")
            raise HTTPException(status_code=404, detail=str(error.args))

    async def get_data_segment_id_from_token(self, token: str,
                                             current_user: str):
        """
        This function is used to get data_segment id from given token

        Params:
            - token (str): encrypted token

        Return:
            - data_segment_id (str):  The unique id of data segment extracted from token

        Raises:
            - HTTPException : Token not valid exception
        """
        credentials_exception = HTTPException(
            detail="Token is not valid",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
        data = await Authentication().get_token_details(token,
                                                        credentials_exception)
        data_segment_id = data.get("sub")
        data_segment_data = await (
            DatabaseConfiguration().data_segment_collection.aggregate(
                [
                    {"$unwind": {"path": "$shared_with"}},
                    {
                        "$match": {
                            "_id": ObjectId(data_segment_id),
                            "shared_with.email": current_user,
                        }
                    },
                ]
            )
        ).to_list(
            None
        )
        if not data_segment_data:
            raise HTTPException(status_code=401,
                                detail="Not enough permissions")
        return data_segment_id
