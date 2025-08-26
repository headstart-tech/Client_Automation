"""
This file contain class and methods for get data regarding student
"""

from bson import ObjectId
from app.core.custom_error import DataNotFoundError
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.helpers.advance_filter_configuration import AdvanceFilterHelper
from app.helpers.student_curd.student_query_configuration import QueryHelper
from datetime import datetime, timezone


class Student:
    """
    Contain functions related to student activities
    """

    async def update_app_basic_match_by_course_info(
            self, course_info: dict | None, app_basic_match: dict
    ) -> dict:
        """
         Update application basic match information by course info.

         Params:
             - course_info (dict | None): Either None or a dictionary which
                 contains course information like course_id (in list format) and
                 course_specialization (in list format).
             - app_basic_match (dict): A application basic match dictionary
                 which want to update.

        Returns:
             - app_basic_match (dict): A dictionary which represents
                 application basic match dictionary.
        """
        course_data = []
        if course_info.get("course_id", []):
            course_data.append(
                {
                    "course_id": {
                        "$in": [
                            ObjectId(item) for item in course_info.get("course_id", [])
                        ]
                    }
                }
            )
        if course_info.get("course_specialization", []):
            course_data.append(
                {"spec_name1": {"$in": course_info.get("course_specialization", [])}}
            )
        if course_data:
            app_basic_match.update({"$and": course_data})
        return app_basic_match

    async def get_payment_status(
            self, payment_initiated: bool, payment_status: str = "Started"
    ) -> str:
        """
        Get payment status by payment initiated value.

        Params:
            - payment_initiated (bool): A boolean value which represents
                payment initiated or not.
            - payment_status (str): A string value which represents status of
                payment.

        Returns:
            str: A string value which represents status of payment.
        """
        if payment_initiated is False:
            payment_status = "Not Started"
        return payment_status

    async def update_app_basic_match_by_payment_status(
            self, payment_status: list | None, app_basic_match: dict
    ) -> dict:
        """
         Update application basic match information by payment status.

         Params:
             - payment_status (list | None): Either None or a list which
                 contains payment statuses.
             - app_basic_match (dict): A application basic match dictionary
                 which want to update.

        Returns:
             - app_basic_match (dict): A dictionary which represents
                 application basic match dictionary.
        """
        payment_data = []
        if "Successful" in payment_status or "captured" in payment_status:
            payment_data.append({"payment_info.status": "captured"})
        if "Failed" in payment_status or "failed" in payment_status:
            payment_data.append({"payment_info.status": "failed"})
        if "In Progress" in payment_status or "started" in payment_status:
            payment_data.append(
                {
                    "$and": [
                        {"payment_initiated": True},
                        {"payment_info.status": {"$ne": "captured"}},
                    ]
                }
            )
        if "not started" in payment_status:
            payment_data.append({"payment_initiated": False})
        if "refunded" in payment_status:
            payment_data.append({"payment_info.status": "refunded"})

        if payment_data:
            app_basic_match.update({"$or": payment_data})
        return app_basic_match

    async def get_app_basic_match(
            self,
            payment_status: list | None,
            course_info: dict | None,
            app_filling_stage: list | None,
    ) -> dict:
        """
         Get application basic match information.

         Params:
             - payment_status (list | None): Either None or a list which
                 contains payment statuses.
             - course_info (dict | None): Either None or a dictionary which
                 contains course information like course_id (in list format) and
                 course_specialization (in list format).
             - app_filling_stage (list | None): Either None or a list which
                 contains application filling stage information.

        Returns:
             - app_basic_match (dict): A dictionary which represents
                 application basic match dictionary.
        """
        app_basic_match = {"$expr": {"$eq": ["$student_id", "$$id"]}}
        if payment_status:
            app_basic_match = await self.update_app_basic_match_by_payment_status(
                payment_status, app_basic_match
            )
        if course_info:
            app_basic_match = await self.update_app_basic_match_by_course_info(
                course_info, app_basic_match
            )
        if app_filling_stage:
            app_basic_match.update({"$or": app_filling_stage})
        return app_basic_match

    # Todo - We'll separate the below function into multiple sub functions
    async def student_pipeline_based_on_condition(
            self,
            start_date,
            end_date,
            college_id,
            payload,
            emails=False,
            numbers=False,
            advance_filters=None,
    ):
        """
        Get pipeline for get student data
        """
        from app.database.aggregation.get_all_applications import Application

        application_obj = Application()
        lead_followup_unwind = True
        lead_followup_match = {"$expr": {"$eq": ["$student_id", "$$id"]}}
        if payload is None:
            payload = {}
        lead_stage_change = payload.get("lead_stage_change")
        if lead_stage_change:
            lead_stage_from = lead_stage_change.get("lead_stage_from")
            lead_stage_to = lead_stage_change.get("lead_stage_to")
            prev_lead_stage = lead_stage_from.get("lead_stage")
            curr_lead_stage = lead_stage_to.get("lead_stage")
            prev_stage_label = lead_stage_from.get("lead_stage_label")
            curr_stage_label = lead_stage_to.get("lead_stage_label")
            if prev_lead_stage:
                lead_followup_match.update({"previous_lead_stage": prev_lead_stage})
            if curr_lead_stage:
                lead_followup_match.update({"lead_stage": curr_lead_stage})
            if prev_stage_label:
                lead_followup_match.update(
                    {"previous_lead_stage_label": prev_stage_label}
                )
            if curr_stage_label:
                lead_followup_match.update({"lead_stage_label": curr_stage_label})
            lead_followup_unwind = False
        app_basic_match = await self.get_app_basic_match(
            payload.get("payment_status", []),
            payload.get("course", {}),
            payload.get("application_filling_stage", []),
        )
        pipeline = [
            {"$match": {"college_id": ObjectId(college_id)}},
            {"$sort": {"created_at": -1}},
            {"$project": await application_obj.get_lead_project_stage_info()},
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": {"id": "$_id"},
                    "pipeline": [
                        {"$match": app_basic_match},
                        {
                            "$project": await application_obj.get_application_project_stage_info()
                        },
                    ],
                    "as": "student_application",
                }
            },
            {
                "$lookup": {
                    "from": "leadsFollowUp",
                    "let": {"id": "$_id"},
                    "pipeline": [
                        {"$match": lead_followup_match},
                        {
                            "$project": {
                                "_id": 0,
                                "lead_stage": 1,
                                "lead_stage_label": 1,
                                "lead_stage_history": 1,
                            }
                        },
                    ],
                    "as": "lead_details",
                }
            },
            {
                "$lookup": {
                    "from": "courses",
                    "let": {"course_id": "$student_application.course_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$course_id"]}}},
                        {"$project": {"_id": 0, "fees": 1, "course_name": 1}},
                    ],
                    "as": "course_details",
                }
            },
        ]
        if advance_filters:
            check = str(advance_filters)
            pipeline = await application_obj.apply_lookup_on_student_secondary(
                pipeline, field="_id"
            )
            pipeline = await application_obj.apply_lookup_on_communication_log(pipeline)
            if "queries" in check:
                pipeline = await application_obj.apply_lookup_on_queries(pipeline)
            pipeline = await AdvanceFilterHelper().apply_advance_filter(
                advance_filters,
                pipeline,
                student_application="student_application",
                courses="course_details",
                student_secondary="student_education_details",
                lead_followup="lead_details",
                communication_log="communication_log",
                queries="queries",
            )
        if start_date not in ["", None] and end_date not in ["", None]:
            pipeline[0].get("$match", {}).update(
                {"created_at": {"$gte": start_date, "$lte": end_date}}
            )
        elif start_date not in ["", None] and end_date in [None, ""]:
            pipeline[0].get("$match", {}).update({"created_at": {"$gte": start_date}})
        if payload.get("is_verify") is not None and payload.get("is_verify") != "":
            if payload.get("is_verify", "").lower() == "verified":
                pipeline[0].get("$match").update({"is_verify": True})
            elif payload.get("is_verify").lower() == "unverified":
                pipeline[0].get("$match").update({"is_verify": False})
        if payload.get("state_code"):
            pipeline[0].get("$match").update(
                {
                    "address_details.communication_address.state.state_code": {
                        "$in": [x.upper() for x in payload.get("state_code")]
                    }
                }
            )
        if payload.get("city_name"):
            pipeline[0].get("$match").update(
                {
                    "address_details.communication_address.city.city_name": {
                        "$in": [x.title() for x in payload.get("city_name")]
                    }
                }
            )
        if payload.get("counselor_id"):
            pipeline[0].get("$match").update(
                {
                    "allocate_to_counselor.counselor_id": {
                        "$in": [ObjectId(x) for x in payload.get("counselor_id")]
                    }
                }
            )
        if (
                payload.get("application_stage_name") is not None
                and payload.get("application_stage_name") != ""
        ):
            pipeline[3].get("$lookup").get("pipeline")[0].get("$match").update(
                {
                    "declaration": (
                        False
                        if payload.get("application_stage_name").lower() == "incomplete"
                        else True
                    )
                }
            )
        if payload.get("source_name"):
            sources = []
            for x in payload.get("source_name"):
                sources.append(x.lower())
            pipeline[0].get("$match", {}).update(
                {"source.primary_source.utm_source": {"$in": sources}}
            )
        if (
                payload.get("lead_type_name") is not None
                and payload.get("lead_type_name") != ""
        ):
            pipeline[0].get("$match", {}).update(
                {
                    "source.primary_source.lead_type": payload.get(
                        "lead_type_name"
                    ).lower()
                }
            )
        lead_stage_info = payload.get("lead_name", [])
        if lead_stage_info:
            lead_stage_names, lead_stage_labels, lead_stage_filter = [], [], {}
            for stage_data in lead_stage_info:
                if stage_data.get("name", []):
                    lead_stage_names.extend(stage_data.get("name", []))
                if stage_data.get("label", []):
                    lead_stage_labels.extend(stage_data.get("label", []))
            if lead_stage_names:
                lead_stage_filter = {"lead_stage.lead_stage": {"$in": lead_stage_names}}
            if lead_stage_labels:
                lead_stage_filter.update(
                    {"lead_details.lead_stage_label": {"$in": lead_stage_labels}}
                )
            if lead_stage_filter:
                pipeline.append({"$match": lead_stage_filter})
        return pipeline

    async def pipeline_for_view_all_leads(
            self,
            start_date=None,
            end_date=None,
            payload=None,
            skip=None,
            limit=None,
            counselor_id=None,
            student_ids=None,
            twelve_score_sort=None,
            publisher=False,
            source_name=None,
            data_segment=None,
            is_head_counselor=False,
            collection_index=None,
            filter_index=None,
    ):
        # Do not move below import statement at the top of file
        # otherwise we'll get circular ImportError
        from app.database.aggregation.get_all_applications import Application

        application_obj = Application()
        if payload is None:
            payload = {}
        pipeline = []

        # Match stages
        match_stages = {}
        advance_filters = payload.get("advance_filters")
        # Insert student_id based match at the beginning
        if student_ids:
            student_ids.reverse()
            match_stages.update(
                {"_id": {"$in": [ObjectId(student_id) for student_id in student_ids]}}
            )
        if payload.get("state_code"):
            if type(payload.get("state_code", [])) == list:
                match_stages.update(
                    {
                        "address_details.communication_address.state"
                        ".state_code": {
                            "$in": [
                                state.upper() for state in payload.get("state_code", [])
                            ]
                        }
                    }
                )

        if payload.get("state"):
            if type(payload.get("state", [])) == list:
                match_stages.update(
                    {
                        "address_details.communication_address.state"
                        ".state_code": {"$in": payload["state"]}
                    }
                )
            elif payload.get("state", {}).get("state_code"):
                match_stages.update(
                    {
                        "address_details.communication_address.state"
                        ".state_code": {"$in": payload["state"]["state_code"]}
                    }
                )

        if source_name:
            match_stages.update({"source.primary_source.utm_source": source_name})
        elif payload.get("source_name", []):
            match_stages.update(
                {
                    "source.primary_source.utm_source": {
                        "$in": [
                            source.lower() for source in payload.get("source_name", [])
                        ]
                    }
                }
            )

        if start_date is not None and end_date is not None:
            match_stages.update({"created_at": {"$gte": start_date, "$lte": end_date}})

        if payload.get("is_verify"):
            is_verified = payload.get("is_verify", "").lower() == "verified"
            match_stages.update({"is_verify": is_verified})
        if counselor_id or is_head_counselor:
            match_stages.update(
                {"allocate_to_counselor.counselor_id": {"$in": counselor_id}}
            )
        elif payload.get("counselor_id", []):
            match_stages.update(
                {
                    "allocate_to_counselor.counselor_id": {
                        "$in": [
                            ObjectId(counselor)
                            for counselor in payload.get("counselor_id", [])
                        ]
                    }
                }
            )

        # UTMs
        if payload.get("utm_medium", []):
            temp_list = [
                {
                    "source.primary_source.utm_source": utm_medium_data.get(
                        "source_name"
                    ),
                    "source.primary_source.utm_medium": utm_medium_data.get(
                        "utm_medium"
                    ),
                }
                for utm_medium_data in payload.get("utm_medium", [])
            ]
            if temp_list:
                match_stages.update({"$or": temp_list})

        # Lead Type
        if payload.get("lead_type", {}):
            if payload.get("lead_type", {}).get("lead_type_name"):
                match_stages.update(
                    {
                        "source.primary_source.lead_type": payload.get("lead_type", {})
                        .get("lead_type_name")
                        .lower()
                    }
                )
        if payload.get("lead_type_name") not in ["", None]:
            match_stages.update(
                {
                    "source.primary_source.lead_type": payload.get(
                        "lead_type_name"
                    ).lower()
                }
            )

        # Source Name
        if payload.get("source", {}):
            source = []
            if payload.get("source", []) == list:
                source = [source.lower() for source in payload.get("source", [])]
            elif payload.get("source", {}).get("source_name", []):
                for x in payload.get("source", {}).get("source_name", []):
                    source.append(x.lower())
            if len(source) > 0:
                match_stages.update(
                    {"source.primary_source.utm_source": {"$in": source}}
                )

        # Source Type
        if payload.get("source_type", []):
            source_type = []
            source_field = payload["source_type"]
            if "primary" in source_field:
                source_type.append({"source.primary_source": {"$exists": True}})

            if "secondary" in source_field:
                source_type.append({"source.secondary_source": {"$exists": True}})

            if "tertiary" in source_field:
                source_type.append({"source.tertiary_source": {"$exists": True}})

            # Combine match stages into a single $match stage
            if source_type:
                pipeline.append({"$match": {"$and": source_type}})
        # Combine match stages into a single $match stage
        if match_stages:
            pipeline.append({"$match": match_stages})
        pipeline.append({"$sort": {"created_at": -1}})
        if skip is not None and limit is not None:
            if collection_index is not None and not advance_filters:
                if filter_index is not None:
                    if (
                            collection_index.get("studentsPrimaryDetails", {}).get(
                                filter_index
                            )
                            == "studentsPrimaryDetails"
                    ):
                        pipeline = utility_obj.get_count_aggregation(
                            pipeline, skip=skip, limit=limit
                        )
        pipeline.append(
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "localField": "_id",
                    "foreignField": "student_id",
                    "as": "applications",
                }
            }
        )
        payment_status = payload.get("payment_status", [])
        if payment_status:
            payment_data = []
            if "not started" in payment_status:
                payment_data.append(
                    {"applications.payment_initiated": {"$in": [False]}}
                )
            if "started" in payment_status:
                payment_data.append(
                    {
                        "applications.payment_initiated": {"$in": [True]},
                        "applications.payment_info.status": {"$nin": ["captured"]},
                    }
                )

            for status in ["captured", "failed", "refunded"]:
                if status in payment_status:
                    payment_data.append(
                        {"applications.payment_info.status": {"$in": [status]}}
                    )
            if payment_data:
                pipeline.append({"$match": {"$or": payment_data}})
        if skip is not None and limit is not None:
            if collection_index is not None and not advance_filters:
                if filter_index is not None:
                    if (
                            collection_index.get("studentApplicationForms", {}).get(
                                filter_index
                            )
                            == "studentApplicationForms"
                    ):
                        pipeline = utility_obj.get_count_aggregation(
                            pipeline, skip=skip, limit=limit
                        )
        pipeline.append(
            {
                "$lookup": {
                    "from": "leadsFollowUp",
                    "localField": "_id",
                    "foreignField": "student_id",
                    "as": "lead_details",
                }
            }
        )
        lead_stage = payload.get("lead_stage_change", {})
        if (
                lead_stage.get("lead_stage_from", {}).get("lead_stage") is not None
                or lead_stage.get("lead_stage_to", {}).get("lead_stage") is not None
        ):
            match_lead = []
            if lead_stage.get("lead_stage_from", {}).get("lead_stage") not in [
                "",
                None,
            ]:
                match_lead.append(
                    {
                        "lead_details.previous_lead_stage": lead_stage.get(
                            "lead_stage_from", {}
                        ).get("lead_stage")
                    }
                )
            if lead_stage.get("lead_stage_from", {}).get("lead_stage_label") not in [
                "",
                None,
            ]:
                match_lead.append(
                    {
                        "lead_details.previous_lead_stage_label": lead_stage.get(
                            "lead_stage_from", {}
                        ).get("lead_stage_label")
                    }
                )
            if lead_stage.get("lead_stage_to", {}).get("lead_stage") not in ["", None]:
                match_lead.append(
                    {
                        "lead_details.lead_stage": lead_stage.get(
                            "lead_stage_to", {}
                        ).get("lead_stage")
                    }
                )
            if lead_stage.get("lead_stage_to", {}).get("lead_stage_label") not in [
                "",
                None,
            ]:
                match_lead.append(
                    {
                        "lead_details.lead_stage_label": lead_stage.get(
                            "lead_stage_to", {}
                        ).get("lead_stage_label")
                    }
                )
            if match_lead:
                pipeline.append({"$match": {"$and": match_lead}})
        if skip is not None and limit is not None:
            if collection_index is not None and not advance_filters:
                if filter_index is not None:
                    if (
                            collection_index.get("leadsFollowUp", {}).get(filter_index)
                            == "leadsFollowUp"
                    ):
                        pipeline = utility_obj.get_count_aggregation(
                            pipeline, skip=skip, limit=limit
                        )

        pipeline = await application_obj.apply_lookup_on_student_secondary(
            pipeline, field="_id"
        )
        if advance_filters:
            check = str(advance_filters)
            pipeline.append({
                "$addFields": {
                    "lead_age": {
                        "$dateDiff": {
                            "startDate": "$created_at",
                            "endDate": datetime.now(timezone.utc),
                            "unit": "day"
                        }
                    },
                    "basic_details.whatsapp_no": {
                        "$cond": {
                            "if": {"$eq": ["$basic_details.whatsapp_no", "Other"]},
                            "then": "$basic_details.mention_whatsapp_no",
                            "else": "$basic_details.whatsapp_no"
                        }
                    }
                }
            })
            if "queries" in check:
                pipeline = await application_obj.apply_lookup_on_queries(
                    pipeline, local_field="_id"
                )
            pipeline = await application_obj.apply_lookup_on_communication_log(
                pipeline, local_field="_id"
            )
            pipeline = await AdvanceFilterHelper().apply_advance_filter(
                advance_filters,
                pipeline,
                student_application="applications",
                courses="course_details",
                student_secondary="student_education_details",
                lead_followup="lead_details",
                communication_log="communication_log",
                queries="queries",
            )
            if collection_index is not None:
                if filter_index is not None:
                    pipeline = utility_obj.get_count_aggregation(
                        pipeline, skip=skip, limit=limit
                    )
        if twelve_score_sort is not None:
            order_decide = 1 if twelve_score_sort else -1
            pipeline.append(
                {
                    "$sort": {
                        "student_education_details.education_details"
                        ".inter_school_details.obtained_cgpa": order_decide
                    }
                },
            )
        if (skip is None or limit is None) and not advance_filters:
            pipeline = utility_obj.get_count_aggregation(
                pipeline, skip=skip, limit=limit
            )

        if data_segment:
            return pipeline
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "data_segment_student_mapping",
                        "let": {"student_id": "$_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {"$eq": ["$$student_id", "$student_id"]}
                                }
                            },
                            {
                                "$project": {
                                    "_id": 0,
                                    "student_id": 1,
                                    "automation": {
                                        "$size": {"$ifNull": ["$automation_id", []]}
                                    },
                                    "automation_names": {"$ifNull": ["$automation_names", []]}
                                }
                            },
                            {
                                "$group": {
                                    "_id": "$student_id",
                                    "automation": {
                                        "$sum": {"$ifNull": ["$automation", 0]}
                                    },
                                    "automation_names": {"$push": "$automation_names"}
                                }
                            },
                        ],
                        "as": "automation_details",
                    }
                },
                {
                    "$unwind": {
                        "path": "$automation_details",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
            ]
        )

        project_phase = {
            "_id": 0,
            "application_id": {
                "$map": {
                    "input": "$applications",
                    "as": "app",
                    "in": {"$toString": "$$app._id"},
                }
            },
            "student_id": {"$toString": "$_id"},
            "student_name": {
                "$trim": {
                    "input": {
                        "$concat": [
                            "$basic_details.first_name",
                            " ",
                            "$basic_details.middle_name",
                            " ",
                            "$basic_details.last_name",
                        ]
                    }
                }
            },
            "custom_application_id": {
                "$map": {
                    "input": "$applications",
                    "as": "app",
                    "in": "$$app.custom_application_id",
                }
            },
            "automation": {"$ifNull": ["$automation_details.automation", None]},
            "automation_names": {"$ifNull": ["$automation_details.automation_names", []]},
            "payment_statuses": "$applications.payment_info.status",
            "payment_initiates": "$applications.payment_initiated",
            "application_stages": {
                "$map": {
                    "input": "$applications",
                    "as": "app",
                    "in": {"$cond": ["$$app.declaration", "Completed", "In progress"]},
                }
            },
            "totalCount": "$totalCount",
            "course_name": {
                "$reduce": {
                    "input": {
                        "$map": {
                            "input": {
                                "$objectToArray": "$course_details"
                            },
                            "as": "course",
                            "in": {
                                "$let": {
                                    "vars": {
                                        "specNames": {
                                            "$filter": {
                                                "input": "$$course.v.specs.spec_name",
                                                "as": "spec",
                                                "cond": {"$ne": ["$$spec", None]}
                                            }
                                        }
                                    },
                                    "in": {
                                        "$cond": [
                                            {"$eq": [{"$size": "$$specNames"}, 0]},
                                            ["$$course.k"],
                                            {
                                                "$map": {
                                                    "input": "$$specNames",
                                                    "as": "specName",
                                                    "in": {
                                                        "$concat": [
                                                            "$$course.k",
                                                            {
                                                                "$cond": [
                                                                    {"$in": ["$$course.k", ["Master", "Bachelor"]]},
                                                                    " of ",
                                                                    " in "
                                                                ]
                                                            },
                                                            "$$specName"
                                                        ]
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    "initialValue": [],
                    "in": {
                        "$concatArrays": ["$$value", "$$this"]
                    }
                }
            },
            "tags": {"$ifNull": ["$tags", None]},
            "payment_status": {
                "$map": {
                    "input": "$applications",
                    "as": "app",
                    "in": {
                        "$cond": {
                            "if": {"$in": ["$$app.payment_info.status", ["", None]]},
                            "then": {
                                "$cond": {
                                    "if": "$$app.payment_initiated",
                                    "then": "Started",
                                    "else": "Not Started",
                                }
                            },
                            "else": "$$app.payment_info.status",
                        }
                    },
                }
            },
            "student_email_id": "$user_name",
            "student_mobile_no": "$basic_details.mobile_number",
            "verification": {
                "lead": {
                    "$switch": {
                        "branches": [
                            {
                                "case": {"$eq": ["$is_verify", False]},
                                "then": "Unverified",
                            },
                            {
                                "case": {
                                    "$and": [
                                        "$is_verify",
                                        "$is_mobile_verify",
                                        "$is_email_verify",
                                    ]
                                },
                                "then": "Lead Verified by Email and Sms",
                            },
                            {
                                "case": {"$eq": ["$is_verify", True]},
                                "then": "Lead Verified by Email or Sms",
                            },
                        ],
                        "default": "Untouched",
                    }
                },
                "application_submitted": {
                    "$map": {
                        "input": "$applications",
                        "as": "app",
                        "in": {
                            "$cond": {
                                "if": "$$app.declaration",
                                "then": "Completed",
                                "else": "In progress",
                            }
                        },
                    }
                },
                "dv_status": {"$ifNull": ["$dv_status", "Not Verified"]},
            },
            "extra_fields": {"$ifNull": ["$extra", {}]},
            "twelve_marks_name": {
                "$ifNull": [
                    "$student_education_details.education_details"
                    ".inter_school_details.obtained_cgpa",
                    None,
                ]
            },
        }
        if payload.get("state", {}).get("state_b") is True:
            project_phase.update(
                {
                    "state_name": "$address_details.communication_address"
                                  ".state.state_name"
                }
            )
        if payload.get("city", {}).get("city_b") is True:
            project_phase.update(
                {
                    "city_name": "$address_details.communication_address"
                                 ".city.city_name"
                }
            )
        if payload.get("counselor", {}).get("counselor_b") is True:
            project_phase.update(
                {
                    "counselor_name": {
                        "$map": {
                            "input": "$applications",
                            "as": "app",
                            "in": "$$app.allocate_to_counselor.counselor_name",
                        },
                    }
                }
            )
        if payload.get("source_type_b"):
            project_phase.update(
                {
                    "source_type": {
                        "$filter": {
                            "input": ["primary", "secondary", "tertiary"],
                            "as": "source_type",
                            "cond": {
                                "$switch": {
                                    "branches": [
                                        {
                                            "case": {
                                                "$ifNull": [
                                                    "$source.primary_source",
                                                    False,
                                                ]
                                            },
                                            "then": {
                                                "$eq": ["$$source_type", "primary"]
                                            },
                                        },
                                        {
                                            "case": {
                                                "$ifNull": [
                                                    "$source.secondary_source",
                                                    False,
                                                ]
                                            },
                                            "then": {
                                                "$eq": ["$$source_type", "secondary"]
                                            },
                                        },
                                        {
                                            "case": {
                                                "$ifNull": [
                                                    "$source.tertiary_source",
                                                    False,
                                                ]
                                            },
                                            "then": {
                                                "$eq": ["$$source_type", "tertiary"]
                                            },
                                        },
                                    ],
                                    "default": False,
                                }
                            },
                        }
                    }
                }
            )
        if (payload.get("application_stage", {}).get("application_stage_b")) is True:
            project_phase.update(
                {
                    "application_status": {
                        "$map": {
                            "input": "$applications",
                            "as": "app",
                            "in": {
                                "$cond": {
                                    "if": "$$app.declaration",
                                    "then": "Completed",
                                    "else": "In progress",
                                }
                            },
                        }
                    }
                }
            )
        if payload.get("is_verify_b") is True:
            project_phase.update(
                {
                    "is_verify": {
                        "$cond": {
                            "if": {"$eq": [True, "$is_verify"]},
                            "then": "verified",
                            "else": "unverified",
                        }
                    }
                }
            )
        if payload.get("lead_stage", {}).get("lead_b") is True:
            project_phase.update(
                {
                    "lead_stage": {
                        "$map": {
                            "input": "$applications",
                            "as": "app",
                            "in": {
                                "$let": {
                                    "vars": {
                                        "followup": {
                                            "$first": {
                                                "$filter": {
                                                    "input": "$lead_details",
                                                    "as": "follow",
                                                    "cond": {
                                                        "$eq": [
                                                            "$$follow.application_id",
                                                            "$$app._id",
                                                        ]
                                                    },
                                                }
                                            }
                                        }
                                    },
                                    "in": {
                                        "$ifNull": [
                                            "$$followup.lead_stage",
                                            "Fresh Lead",
                                        ]
                                    },
                                }
                            },
                        }
                    }
                }
            )
        if payload.get("lead_stage", {}).get("lead_sub_b") is True:
            project_phase.update(
                {
                    "lead_sub_stage": {
                        "$map": {
                            "input": "$applications",
                            "as": "app",
                            "in": {
                                "$let": {
                                    "vars": {
                                        "followup": {
                                            "$arrayElemAt": [
                                                {
                                                    "$filter": {
                                                        "input": "$lead_details",
                                                        "as": "followup",
                                                        "cond": {
                                                            "$eq": [
                                                                "$$followup.application_id",
                                                                "$$app._id",
                                                            ]
                                                        },
                                                    }
                                                },
                                                0,
                                            ]
                                        }
                                    },
                                    "in": {
                                        "$ifNull": ["$$followup.lead_sub_stage", ""]
                                    },
                                }
                            },
                        }
                    }
                }
            )

        if payload.get("source", {}).get("source_b") is True:
            project_phase.update(
                {
                    "source_name": {
                        "$ifNull": ["$source.primary_source.utm_source", "Organic"]
                    }
                }
            )
        if payload.get("utm_medium_b") is True:
            project_phase.update({"utm_medium": "$source.primary_source.utm_medium"})
        if payload.get("utm_campaign_b") is True:
            project_phase.update(
                {"utm_campaign": "$source.primary_source.utm_campaign"}
            )
        if payload.get("date") is True:
            project_phase.update(
                {
                    "date": {
                        "$map": {
                            "input": "$applications.last_updated_time",
                            "as": "datetime",
                            "in": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d %H:%M:%S",
                                    "date": "$$datetime",
                                    "timezone": "+05:30",
                                }
                            },
                        }
                    }
                }
            )
        if payload.get("lead_type", {}).get("lead_type_b") is True:
            project_phase.update({"lead_type": "$source.primary_source.lead_type"})
        pipeline.append({"$project": project_phase})
        return pipeline

    async def get_leads_data(self, payload, data, doc):
        """
        Get leads data

        Params:
            payload (dict | None): Payload for filter data.
            data (dict): Leads data which need to show in the response.
            doc (dict): Useful for get required data.

        Returns:
            data (dict): Useful for return leads data.
        """
        from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache
        if payload.get("state", {}).get("state_b") is True:
            city = await DatabaseConfiguration().city_collection.find_one(
                {
                    "state_code": doc.get("state_code"),
                    "name": doc.get("city_name"),
                }
            )
            data["state_name"] = city.get("state_name")
        if payload.get("city", {}).get("city_b") is True:
            data["city_name"] = doc.get("city_name")
        if payload.get("counselor", {}).get("counselor_b") is True:
            data["counselor_name"] = [
                app_dict.get("allocate_to_counselor", {}).get("counselor_name")
                for app_dict in doc.get("applications", [])
                if app_dict.get("student_id") == doc.get("student_id")
            ]
        if (payload.get("application_stage", {}).get("application_stage_b")) is True:
            data["application_status"] = data.get("verification", {}).get(
                "application_submitted"
            )
        if payload.get("lead_stage", {}).get("lead_b") is True:
            lead_stages = []
            for app_dict in doc.get("applications", []):
                if app_dict.get("student_id") == doc.get("student_id"):
                    lead_stage = await DatabaseConfiguration().leadsFollowUp.find_one(
                        {
                            "application_id": app_dict.get("_id"),
                            "student_id": doc.get("student_id"),
                        }
                    )
                    if not lead_stage:
                        lead_stage = {}
                    lead_stages.append(lead_stage.get("lead_stage", "Fresh Lead"))
            data["lead_stage"] = lead_stages
        if payload.get("lead_stage", {}).get("lead_sub_b") is True:
            lead_sub_stages = []
            for app_dict in doc.get("applications", []):
                if app_dict.get("student_id") == doc.get("student_id"):
                    lead_stage = await DatabaseConfiguration().leadsFollowUp.find_one(
                        {
                            "application_id": app_dict.get("_id"),
                            "student_id": doc.get("student_id"),
                        }
                    )
                    if not lead_stage:
                        lead_stage = {}
                    lead_sub_stages.append(lead_stage.get("lead_stage_label", ""))
            data["lead_sub_stage"] = lead_sub_stages
        if payload.get("source_type_b"):
            temp = []
            for source in ["primary", "secondary", "tertiary"]:
                if doc.get("source_details", {}).get(f"{source}_source"):
                    temp.append(source)
            data["source_type"] = temp
        if payload.get("is_verify_b") is True:
            data["is_verify"] = (
                "verified" if doc.get("is_verify", False) else "unverified"
            )
        if payload.get("source", {}).get("source_b") is True:
            data["source_name"] = (
                doc.get("source_details", {})
                .get("primary_source", {})
                .get("utm_source", "Organic")
            )
        if payload.get("utm_medium_b") is True:
            data["utm_medium"] = (
                doc.get("source_details", {})
                .get("primary_source", {})
                .get("utm_medium")
            )
        if payload.get("utm_campaign_b") is True:
            data["utm_campaign"] = (
                doc.get("source_details", {})
                .get("primary_source", {})
                .get("utm_campaign")
            )
        if payload.get("lead_type", {}).get("lead_type_b") is True:
            data["lead_type"] = str(
                (
                    doc.get("source_details", {})
                    .get("primary_source", {})
                    .get("lead_type", "")
                ).upper()
            )
        if payload.get("date") is True:
            data["date"] = doc.get("application_dates")
        student_edu_details = doc.get("student_education_details", {}).get(
            "education_details", {}
        )
        data["twelve_marks_name"] = student_edu_details.get(
            "inter_school_details", {}
        ).get("obtained_cgpa")
        if (
                payload.get("form_filling_stage", {}).get("form_filling_stage_b") is True
                or payload.get("twelve_board", {}).get("twelve_board_b") is True
                or payload.get("twelve_marks", {}).get("twelve_marks_b") is True
        ):
            if (
                    payload.get("form_filling_stage", {}).get("form_filling_stage_b")
                    is True
            ):
                form_fill = []
                if student_edu_details.get("tenth_school_details") is not None:
                    form_fill.append("10th")
                if (
                        student_edu_details.get("inter_school_details", {}).get(
                            "is_pursuing"
                        )
                        is False
                ):
                    form_fill.append("12th")
                if doc.get("declaration") is True:
                    form_fill.append("Declaration")
                data["form_filling_stage"] = form_fill
            if payload.get("twelve_board", {}).get("twelve_board_b") is True:
                data["twelve_board_name"] = student_edu_details.get(
                    "inter_school_details", {}
                ).get("board")
        return data

    async def get_lead_verification_info(self, doc, applications=False) -> dict:
        """
        Get lead verification info.

        Params: doc: A document which contains student primary and
        application details. applications: A value will be True when
        fetching data based on application.

        Returns:
            dict: A dictionary which contains lead verification info.
        """
        verify_status = doc.get("student_verify")
        if verify_status is False:
            lead_verify = "Unverified"
        elif (
                verify_status
                and doc.get("student_mobile_verify")
                and doc.get("student_email_verify")
        ):
            lead_verify = "Lead Verified by Email and Sms"
        elif verify_status:
            lead_verify = "Lead Verified by Email or Sms"
        else:
            lead_verify = "Untouched"
        application_submitted = (
            [
                ("Completed" if app_dict.get("declaration") is True else "In progress")
                for app_dict in doc.get("applications", [])
                if app_dict.get("student_id") == doc.get("student_id")
            ]
            if not applications
            else doc.get("declaration")
        )
        return {
            "lead": lead_verify,
            "application_submitted": application_submitted,
            "dv_status": doc.get("dv_status", "Not Verified"),
        }

    async def combine_leads_data(self, doc: dict, payload: dict) -> dict:
        """
        Combine leads data

        Params:
            doc (dict): Student data in a dictionary format
            payload (dict): A dictionary which contains filter information.

        Returns:
            dict: A dictionary which contains leads data.
        """
        data = {
            "application_id": doc.get("application_ids"),
            "student_id": str(doc.get("student_id")),
            "student_name": doc.get("student_name"),
            "custom_application_id": [
                app_dict.get("custom_application_id")
                for app_dict in doc.get("applications", [])
                if app_dict.get("student_id") == doc.get("student_id")
            ],
            "course_name": doc.get("course_names"),
            "is_verify": doc.get("is_verify"),
            "tags": doc.get("tags"),
            "automation": "0",
            "student_email_id": doc.get("student_email"),
            "student_mobile_no": doc.get("student_mobile_number"),
            "verification": await self.get_lead_verification_info(doc),
            "payment_status": [
                (
                    await Student().get_payment_status(initiate_value)
                    if status in ["", None]
                    else str(status).title()
                )
                for status, initiate_value in zip(
                    doc.get("payment_statuses", []), doc.get("payment_initiates", [])
                )
            ],
            "extra_fields": doc.get("extra", {}),
        }
        data = await self.get_leads_data(payload, data, doc)
        return data

    async def get_leads_data_with_count(
            self,
            pipeline: list,
            payload: dict,
            total_data: int,
            publisher: bool = False,
    ) -> tuple:
        """
        Get leads data with count using pipeline.

        Params:
            pipeline (list): Useful for fetch leads data from DB.
            payload (dict): Useful for filters and show columns.
            data_list (list): A list which useful for get leads data.
            total_data (int): Count of total leads data.

        Returns: data_list, total_data (tuple): A tuple contains data_list
            and total_data.
        """

        season = None
        if payload.get("season") not in ["", None]:
            season = payload.get("season")
        result = DatabaseConfiguration(season=season).studentsPrimaryDetails.aggregate(
            pipeline
        )
        paginated_result = []
        async for doc in result:
            try:
                total_data = doc.get("totalCount", 0)
            except IndexError:
                total_data = 0
            except Exception:
                total_data = 0
            automation_names = doc.get("automation_names", [])
            automation_names = [item for sublist in automation_names if isinstance(sublist, list) for item in
                                sublist] if automation_names else [],
            doc["automation_names"] = automation_names[0] if len(automation_names) >= 1 else []
            paginated_result.append(doc)
        return paginated_result, total_data

    async def get_students_based_on_source(
            self,
            source: list[str] | None,
            season: str | None,
            counselor_id: list[ObjectId] | None = None,
            is_head_counselor: bool = False,
    ) -> list:
        """
        Get the students based on source.

        Params:
            source (list[str] | None): Either None or A list which contains
                source names in a string format.
            season (str): Season name/id which useful for get season-wise
                students data based on source list.

        Returns:
            list: A list which contains student unique ids which can be useful
                for further operation.
        """
        match_stage = []
        if source:
            sources = [str(x).lower() for x in source]
            if sources:
                match_stage.append(
                    {"source.primary_source.utm_source": {"$in": sources}}
                )
        if counselor_id or is_head_counselor:
            match_stage.append(
                {"allocate_to_counselor.counselor_id": {"$in": counselor_id}}
            )
        pipeline = [
            {
                "$group": {
                    "_id": "",
                    "students": {"$addToSet": "$_id"},
                }
            }
        ]
        if match_stage:
            pipeline.insert(0, {"$match": {"$and": match_stage}})
        student_ids = []
        async for doc in DatabaseConfiguration(
                season=season
        ).studentsPrimaryDetails.aggregate(pipeline):
            student_ids = doc["students"]
        return student_ids

    async def get_student_queries(
            self,
            season,
            program_names,
            date_range,
            page_num,
            page_size,
            query_type,
            search,
            counselor_ids,
    ):
        """
        Get summary of student queries based on counselor.

        Returns:
            list: A list which contains counselor wise student queries
                summary data.
        """
        base_match = {"role.role_name": "college_counselor"}
        if search not in ["", None]:
            base_match.update(
                {
                    "$or": [
                        {"first_name": {"$regex": f"^{search}", "$options": "i"}},
                        {"last_name": {"$regex": f"^{search}", "$options": "i"}},
                    ]
                }
            )
        if counselor_ids:
            counselor_ids = [
                ObjectId(counselor_id)
                for counselor_id in counselor_ids
                if await utility_obj.is_length_valid(counselor_id, "Counselor id")
            ]
            base_match.update({"_id": {"$in": counselor_ids}})
        query_match = {"$expr": {"$eq": ["$assigned_counselor_id", "$$counselor_id"]}}
        if len(date_range) >= 2:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
            query_match.update({"created_at": {"$gte": start_date, "$lte": end_date}})
        if program_names:
            program_filter = [
                {
                    "course_name": program.get("course_name"),
                    "specialization_name": program.get("spec_name"),
                }
                for program in program_names
            ]
            query_match.update({"$or": program_filter})
        if query_type:
            query_match.update({"category_name": {"$in": query_type}})
        pipeline = [
            {"$match": base_match},
            {"$sort": {"first_name": 1}},
            {
                "$group": {
                    "_id": "$_id",
                    "first_name": {"$first": "$first_name"},
                    "middle_name": {"$first": "$middle_name"},
                    "last_name": {"$first": "$last_name"},
                }
            },
            {
                "$lookup": {
                    "from": "queries",
                    "let": {"counselor_id": "$_id"},
                    "pipeline": [
                        {"$match": query_match},
                        {"$project": {"_id": 0, "status": 1}},
                        {
                            "$group": {
                                "_id": "",
                                "open_query": {
                                    "$sum": {
                                        "$cond": [{"$eq": ["$status", "TO DO"]}, 1, 0]
                                    }
                                },
                                "resolved_query": {
                                    "$sum": {
                                        "$cond": [{"$eq": ["$status", "DONE"]}, 1, 0]
                                    }
                                },
                                "unresolved_query": {
                                    "$sum": {
                                        "$cond": [
                                            {"$eq": ["$status", "IN PROGRESS"]},
                                            1,
                                            0,
                                        ]
                                    }
                                },
                            }
                        },
                    ],
                    "as": "query_data",
                }
            },
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "counselor_name": {
                        "$trim": {
                            "input": {
                                "$concat": [
                                    "$first_name",
                                    " ",
                                    "$middle_name",
                                    " ",
                                    "$last_name",
                                ]
                            }
                        }
                    },
                    "open_query": {
                        "$ifNull": [{"$first": "$query_data.open_query"}, 0]
                    },
                    "resolved_query": {
                        "$ifNull": [{"$first": "$query_data.resolved_query"}, 0]
                    },
                    "unresolved_query": {
                        "$ifNull": [{"$first": "$query_data.unresolved_query"}, 0]
                    },
                }
            },
        ]
        if page_num and page_size:
            skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
            pipeline.insert(2, {"$skip": skip})
            pipeline.insert(3, {"$limit": limit})
            # Following line added because we're getting following error -
            # Limit code returned unexpected value
            # Reference link: https://jira.mongodb.org/browse/SERVER-87324
            pipeline.insert(4, {"$addFields": {"v": 0}})
        if season == "":
            season = None
        result = DatabaseConfiguration(season=season).user_collection.aggregate(
            pipeline
        )
        return [doc async for doc in result]

    async def get_student_program_wise_queries(
            self, student_id: str, course_name: str, spec_name: str | None
    ) -> list:
        """
        Get student queries based on program name.

        Params:
            student_id (str): An unique identifier/id of student.
                Useful for get student queries only.
                e.g., 123456789012345678901231
            course_name (str): Required field. Name of a course.
                e.g., B.Sc.
            specialization_name (str | None): Optional field.
                Default value: None. Name of a course
                specialization. e.g., Physician Assistant.

        Returns:
            list: A list which contains student program-wise queries.
        """
        await utility_obj.is_length_valid(student_id, "Student id")
        if (
                await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(student_id)}
                )
        ) is None:
            raise DataNotFoundError(message="Student")
        if (
                await DatabaseConfiguration().course_collection.find_one(
                    {"course_name": course_name}
                )
        ) is None:
            raise DataNotFoundError(message="Course")
        base_match = {"student_id": ObjectId(student_id), "course_name": course_name}
        if spec_name not in [None, ""]:
            base_match.update({"specialization_name": spec_name})
        pipeline = [{"$match": base_match}]
        aggregation_result = DatabaseConfiguration().queries.aggregate(pipeline)
        return [QueryHelper().query_helper(doc) async for doc in aggregation_result]
