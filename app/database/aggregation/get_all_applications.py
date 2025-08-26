"""
This file contains class and methods related to get application data.
"""

from datetime import datetime, timezone

from bson import ObjectId

from app.core.common_utils import Check_payload
from app.core.utils import utility_obj
from app.database.aggregation.student import Student
from app.database.configuration import DatabaseConfiguration
from app.helpers.advance_filter_configuration import AdvanceFilterHelper


class Application:
    """
    Contains functions related to application activities.
    """

    async def get_application_project_stage_info(self):
        """
        Get the project stage information for application collection.

        Params: None

        Returns:
            - dict: A dictionary which contains project stage information for
                application collection.
        """
        return {
            "_id": 1,
            "declaration": 1,
            "payment_info": 1,
            "last_updated_time": 1,
            "allocate_to_counselor": 1,
            "custom_application_id": 1,
            "student_id": 1,
            "dv_status": 1,
            "course_id": 1,
            "spec_name1": 1,
            "current_stage": 1,
            "enquiry_date": 1,
            "payment_initiated": 1,
            "school_name": 1,
            "payment_attempts": 1,
            "gd_status": 1,
            "pi_status": 1,
        }

    async def get_lead_project_stage_info(self):
        """
        Get the project stage information for lead collection.

        Params: None

        Returns:
            - dict: A dictionary which contains project stage information for
                lead collection.
        """
        return {
            "_id": 1,
            "user_name": 1,
            "basic_details": 1,
            "address_details": 1,
            "is_verify": 1,
            "is_email_verify": 1,
            "is_mobile_verify": 1,
            "last_accessed": 1,
            "course_details": 1,
            "created_at": 1,
            "last_modified_date": 1,
            "source": 1,
            "unsubscribe": 1,
            "tags": 1,
            "allocate_to_counselor": 1,
        }

    async def extend_pipeline_based_on_condition(
            self, payload, start_date, end_date, form_initiated=True,
            twelve_score_sort=None
    ):
        """
        Get pipeline for the collection named studentApplicationForms
        """
        lead_project_info = await self.get_lead_project_stage_info()
        lead_project_info.update(
            {"extra": "$extra",
             "extra_fields": {"$objectToArray": "$extra_fields"}}
        )
        pipeline = [
            {
                "$match": {
                    "college_id": ObjectId(payload.get("college_id")),
                    "enquiry_date": {"$gte": start_date, "$lte": end_date},
                }
            },
            {"$sort": {"enquiry_date": -1}},
            {"$project": await self.get_application_project_stage_info()},
            {
                "$lookup": {
                    "from": "studentsPrimaryDetails",
                    "let": {"id": "$student_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$id"]}}},
                        {"$addFields": {"extra": "$extra_fields"}},
                        {"$project": lead_project_info},
                    ],
                    "as": "student_primary",
                }
            },
            {"$unwind": {"path": "$student_primary"}},
        ]
        pipeline = await self.apply_lookup_on_student_secondary(pipeline)
        if twelve_score_sort is not None:
            order_decide = 1 if twelve_score_sort else -1
            pipeline.append(
                {
                    "$sort": {
                        "student_education_details.education_details"
                        ".inter_school_details.obtained_cgpa": order_decide
                    }
                }
            )
        if payload is None:
            payload = {}
        if form_initiated:
            pipeline[0].get("$match", {}).update(
                {"current_stage": {"$gte": 2}})
        if payload.get("application_filling_stage"):
            pipeline[0].get("$match", {}).update(
                {"$or": payload.get("application_filling_stage", [])}
            )
        if payload.get("course", {}).get("course_id", []):
            pipeline[0].get("$match").update(
                {
                    "course_id": {
                        "$in": [
                            ObjectId(item)
                            for item in
                            payload.get("course", {}).get("course_id", [])
                        ]
                    }
                }
            )
        if payload.get("course", {}).get("course_specialization", []):
            pipeline[0].get("$match").update(
                {
                    "spec_name1": {
                        "$in": payload.get("course", {}).get(
                            "course_specialization", []
                        )
                    }
                }
            )
        payment_status = payload.get("payment_status", [])
        if payment_status:
            payment_data = []
            if "not started" in payment_status:
                payment_data.append({"payment_initiated": False})
            if "started" in payment_status:
                payment_data.append(
                    {
                        "payment_initiated": True,
                        "payment_info.status": {"$ne": "captured"},
                    }
                )
            if (
                    "captured" in payment_status
                    or "failed" in payment_status
                    or "refunded" in payment_status
            ):
                pipeline[0].get("$match").pop("enquiry_date")
                pipeline[0].get("$match").update(
                    {"payment_info.created_at": {"$gte": start_date,
                                                 "$lte": end_date}}
                )
            if "captured" in payment_status:
                payment_data.append({"payment_info.status": "captured"})
            if "failed" in payment_status:
                payment_data.append({"payment_info.status": "failed"})
            if "refunded" in payment_status:
                payment_data.append({"payment_info.status": "refunded"})
            if payment_data:
                pipeline.append({"$match": {"$or": payment_data}})
        if payload.get("is_verify") is not None and payload.get(
                "is_verify") != "":
            if payload.get("is_verify", "").lower() == "verified":
                pipeline[3].get("$lookup").get("pipeline")[0].get(
                    "$match").update(
                    {"is_verify": True}
                )
            elif payload.get("is_verify").lower() == "unverified":
                pipeline[3].get("$lookup").get("pipeline")[0].get(
                    "$match").update(
                    {"is_verify": False}
                )
        if payload.get("state_code", []):
            pipeline.append(
                {
                    "$match": {
                        "student_primary.address_details"
                        ".communication_address.state.state_code": {
                            "$in": [x.upper() for x in
                                    payload.get("state_code", [])]
                        }
                    }
                }
            )
        if payload.get("city_name", []):
            pipeline.append(
                {
                    "$match": {
                        "student_primary.address_details"
                        ".communication_address.city.city_name": {
                            "$in": [x.title() for x in
                                    payload.get("city_name", [])]
                        }
                    }
                }
            )
        if payload.get("counselor_id", []):
            pipeline.append(
                {
                    "$match": {
                        "allocate_to_counselor.counselor_id": {
                            "$in": [
                                ObjectId(x) for x in
                                payload.get("counselor_id", [])
                            ]
                        }
                    }
                }
            )
        if (
                payload.get("application_stage_name") is not None
                and payload.get("application_stage_name") != ""
        ):
            pipeline.append(
                {
                    "$match": {
                        "declaration": (
                            False
                            if payload.get("application_stage_name").lower()
                               == "incomplete"
                            else True
                        )
                    }
                }
            )
        advance_filters = payload.get("advance_filters", [])
        if payload.get("lead_name", []) or advance_filters:
            pipeline = await self.apply_lookup_on_leadfollowup(
                pipeline, payload=payload
            )
        if advance_filters:
            pipeline = await self.apply_lookup_on_communication_log(pipeline)
            pipeline = await self.apply_lookup_on_queries(pipeline)
            pipeline = await AdvanceFilterHelper().apply_advance_filter(
                advance_filters,
                pipeline,
                student_primary="student_primary",
                courses="course_details",
                student_secondary="student_education_details",
                lead_followup="lead_details",
                communication_log="communication_log",
                queries="queries",
            )
        lead_stage_info = payload.get("lead_name", [])
        if lead_stage_info:
            temp_list = []
            for load in lead_stage_info:
                lead_stages = load.get("name", [])
                if "Fresh Lead" in lead_stages:
                    lead_stages.append(None)

                label_list = [
                    {"lead_details.lead_stage_label": label}
                    for label in load.get("label", [])
                ]

                if len(label_list) > 0:
                    temp_list.append(
                        {
                            "$and": [
                                {"lead_details.lead_stage": {
                                    "$in": lead_stages}},
                                {"$or": label_list},
                            ]
                        }
                    )
                else:
                    temp_list.append(
                        {"lead_details.lead_stage": {"$in": lead_stages}})
            if len(temp_list) > 0:
                pipeline.append({"$match": {"$or": temp_list}})

        if payload.get("utm_medium", []):
            temp_list = [
                {
                    "student_primary.source.primary_source.utm_source": utm_medium_data.get(
                        "source_name"
                    ),
                    "student_primary.source.primary_source.utm_medium": utm_medium_data.get(
                        "utm_medium"
                    ),
                }
                for utm_medium_data in payload.get("utm_medium", [])
            ]
            if len(temp_list) > 0:
                pipeline.append({"$match": {"$or": temp_list}})
        if payload.get("source_type", []):
            source_type = []
            if "primary" in payload.get("source_type"):
                source_type.append(
                    {"student_primary.source.primary_source": {
                        "$exists": True}}
                )
            if "secondary" in payload.get("source_type"):
                source_type.append(
                    {"student_primary.source.secondary_source": {
                        "$exists": True}}
                )
            if "tertiary" in payload.get("source_type"):
                source_type.append(
                    {"student_primary.source.tertiary_source": {
                        "$exists": True}}
                )
            pipeline.append({"$match": {"$and": source_type}})
        if payload.get("source_name", []):
            sources = []
            for x in payload.get("source_name", []):
                sources.append(x.lower())
            pipeline.append(
                {
                    "$match": {
                        "student_primary.source.primary_source.utm_source": {
                            "$in": sources
                        }
                    }
                }
            )
        if (
                payload.get("lead_type_name") is not None
                and payload.get("lead_type_name") != ""
        ):
            pipeline.append(
                {
                    "$match": {
                        "student_primary.source.primary_source.lead_type": payload.get(
                            "lead_type_name"
                        ).lower()
                    }
                }
            )
        if payload.get("twelve_board", {}).get("twelve_board_name"):
            pipeline.append(
                {
                    "$match": {
                        "student_education_details.education_details"
                        ".inter_school_details.board": {
                            "$in": payload.get("twelve_board", {}).get(
                                "twelve_board_name"
                            )
                        }
                    }
                }
            )
        if payload.get("form_filling_stage", {}).get(
                "form_filling_stage_name"):
            form_filling = []
            if "12th" in payload.get("form_filling_stage", {}).get(
                    "form_filling_stage_name"
            ):
                form_filling.append(
                    {
                        "student_education_details.education_details"
                        ".inter_school_details.is_pursuing": False
                    }
                )
            if "10th" in payload.get("form_filling_stage", {}).get(
                    "form_filling_stage_name"
            ):
                form_filling.append(
                    {
                        "student_education_details.education_details"
                        ".tenth_school_details": {"$exists": True}
                    }
                )
            if "Declaration" in payload.get("form_filling_stage", {}).get(
                    "form_filling_stage_name"
            ):
                form_filling.append({"declaration": True})
            pipeline.append({"$match": {"$and": form_filling}})
        if payload.get("twelve_marks", {}).get("twelve_marks_name"):
            twelve_details = [
                {
                    "$and": [
                        {
                            "student_education_details.education_details"
                            ".inter_school_details.marking_scheme": "Percentage"
                        },
                        {
                            "student_education_details.education_details"
                            ".inter_school_details.obtained_cgpa": {
                                "$gte": float(element.split("-")[0]),
                                "$lt": float(element.split("-")[-1]),
                            }
                        },
                    ]
                }
                for element in
                payload.get("twelve_marks", {}).get("twelve_marks_name")
                if "-" in element
            ]
            twelve_details.extend(
                [
                    {
                        "student_education_details.education_details"
                        ".inter_school_details.obtained_cgpa": element
                    }
                    for element in payload.get("twelve_marks", {}).get(
                    "twelve_marks_name"
                )
                    if "-" not in element
                ]
            )
            pipeline.append({"$match": {"$or": twelve_details}})
        if payload.get("extra_filters", []):
            extra_fields = [
                {
                    "student_primary.extra_fields": {
                        "$elemMatch": {
                            "k": condition.get("field_name"),
                            "v": condition.get("value"),
                        }
                    }
                }
                for condition in payload.get("extra_filters", [])
            ]

            pipeline.append({"$match": {"$or": extra_fields}})
        return pipeline

    async def get_aggregation_result(
            self,
            date_range,
            payload,
            publisher=False,
            user=None,
            form_initiated=True,
            twelve_score_sort=None,
    ):
        """
        Get aggregation result
        """
        date_range = await utility_obj.get_valid_date_range(date_range)
        start_date, end_date = await utility_obj.date_change_format(
            date_range.get("start_date"), date_range.get("end_date")
        )
        if publisher:
            result, total_data = await Application().get_all_leads_by_utm_source(
                payload=payload,
                start_date=start_date,
                end_date=end_date,
                utm_source=(
                    user.get("associated_source_value").lower()
                    if user.get("associated_source_value") is not None
                    else ""
                ),
                page_num=1,
                page_size=200,
                source_type="all",
                payment_status=payload.get("payment_status"),
                application=form_initiated,
            )
        else:
            pipeline = await self.extend_pipeline_based_on_condition(
                payload=payload,
                start_date=start_date,
                end_date=end_date,
                form_initiated=form_initiated,
                twelve_score_sort=twelve_score_sort,
            )
            result = DatabaseConfiguration().studentApplicationForms.aggregate(
                pipeline)
        return result

    async def get_values(self, page_num, page_size, start_date, end_date,
                         college_id):
        """
        Get skip and limit values
        """
        if page_num and page_size:
            skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                                  page_size)
        else:
            skip = 0
            limit = (
                await DatabaseConfiguration().studentApplicationForms.count_documents(
                    {
                        "college_id": ObjectId(college_id),
                        "enquiry_date": {"$gte": start_date, "$lte": end_date},
                    }
                )
            )
        return skip, limit

    async def aggregation_pipeline(
            self,
            payload,
            pipeline,
            skip=None,
            limit=None,
            payment_status=None,
            advance_filters=None,
            data_segment=None,
            twelve_score_sort=None,
    ):
        """
        Get pipeline of aggregation
        """
        if payload is None:
            payload = {}
        if (
                payload.get("application_stage", {}).get(
                    "application_stage_name")
                is not None
                and payload.get("application_stage", {}).get(
            "application_stage_name") != ""
        ):
            pipeline[0].get("$match").update(
                {
                    "declaration": (
                        False
                        if payload.get("application_stage", {}).get(
                            "application_stage_name"
                        )
                           == "incomplete"
                        else True
                    )
                }
            )
        if payment_status:
            payment_data = []
            if "not started" in payment_status:
                payment_data.append({"payment_initiated": False})
            if "started" in payment_status:
                payment_data.append(
                    {
                        "payment_initiated": True,
                        "payment_info.status": {"$ne": "captured"},
                    }
                )
            if "captured" in payment_status:
                payment_data.append({"payment_info.status": "captured"})
            if "failed" in payment_status:
                payment_data.append({"payment_info.status": "failed"})
            if "refunded" in payment_status:
                payment_data.append({"payment_info.status": "refunded"})
            if payment_data:
                payment_match = pipeline[0].get("$match", {})
                if "$or" in payment_match:
                    payment_match.update({"$and": [{"$or": payment_data}, {
                        "$or": payment_match.pop("$or")}]})
                else:
                    payment_match.update({"$or": payment_data})
        if twelve_score_sort is not None:
            order_decide = 1 if twelve_score_sort else -1
            pipeline.append(
                {
                    "$sort": {
                        "student_education_details.education_details"
                        ".inter_school_details.obtained_cgpa": order_decide
                    }
                }
            )
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "data_segment_student_mapping",
                        "let": {"student_id": "$student_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": ["$$student_id", "$student_id"]}
                                }
                            },
                            {
                                "$project": {
                                    "_id": 0,
                                    "student_id": 1,
                                    "automation": {
                                        "$size": {
                                            "$ifNull": ["$automation_id", []]}
                                    },
                                    "automation_names": {
                                        "$ifNull": ["$automation_names", []]}
                                }
                            },
                            {
                                "$group": {
                                    "_id": "$student_id",
                                    "automation": {
                                        "$sum": {"$ifNull": ["$automation", 0]}
                                    },
                                    "automation_names": {
                                        "$push": "$automation_names"}
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
        pipeline.append({"$sort": {"enquiry_date": -1}})
        if advance_filters:
            if skip is not None and limit is not None:
                pipeline = utility_obj.get_count_aggregation(
                    pipeline, skip=skip, limit=limit
                )
        if (skip is None or limit is None) and not advance_filters:
            pipeline = utility_obj.get_count_aggregation(pipeline)
        if data_segment:
            return pipeline
        return pipeline

    async def get_data_based_on_condition(self, payload, data, doc,
                                          source_data=False):
        """
        Return data based on condition
        """
        if payload.get("state", {}).get("state_b") is True:
            data["state_name"] = (
                doc.get("student_primary", {})
                .get("address_details", {})
                .get("communication_address", {})
                .get("state", {})
                .get("state_name")
            )
        if payload.get("city", {}).get("city_b") is True:
            data["city_name"] = (
                doc.get("student_primary", {})
                .get("address_details", {})
                .get("communication_address", {})
                .get("city", {})
                .get("city_name")
            )
        if payload.get("counselor", {}).get("counselor_b") is True:
            data["counselor_name"] = doc.get("allocate_to_counselor", {}).get(
                "counselor_name"
            )
        if (payload.get("application_stage", {}).get(
                "application_stage_b")) is True:
            data["application_status"] = (
                "Completed" if doc.get(
                    "declaration") is True else "In progress"
            )
        if payload.get("lead_stage", {}).get("lead_b") is True:
            data["lead_stage"] = doc.get("lead_details", {}).get(
                "lead_stage", "Fresh Lead"
            )
        if payload.get("lead_stage", {}).get("lead_sub_b") is True:
            data["lead_sub_stage"] = doc.get("lead_details", {}).get(
                "lead_stage_label", ""
            )
        if payload.get("source", {}).get("source_b") is True:
            data["source_name"] = (
                doc.get("student_primary", {})
                .get("source", {})
                .get("primary_source", {})
                .get("utm_source", "Organic")
            )
        if payload.get("source_type_b"):
            temp = []
            for source in ["primary", "secondary", "tertiary"]:
                if (
                        doc.get("student_primary", {})
                                .get("source", {})
                                .get(f"{source}_source")
                ):
                    temp.append(source)
            data["source_type"] = temp

        if payload.get("utm_medium_b") is True:
            data["utm_medium"] = (
                doc.get("student_primary", {})
                .get("source", {})
                .get("primary_source", {})
                .get("utm_medium")
            )
        if payload.get("utm_campaign_b") is True:
            data["utm_campaign"] = (
                doc.get("student_primary", {})
                .get("source", {})
                .get("primary_source", {})
                .get("utm_campaign")
            )
        if payload.get("lead_type", {}).get("lead_type_b") is True:
            data["lead_type"] = str(
                (
                    doc.get("student_primary", {})
                    .get("source", {})
                    .get("primary_source", {})
                    .get("lead_type", "")
                ).upper()
            )
        if payload.get("is_verify_b") is True:
            data["is_verify"] = (
                "verified"
                if doc.get("student_primary", {}).get("is_verify", False)
                else "unverified"
            )
        if payload.get("date") is True:
            data["date"] = utility_obj.get_local_time(doc.get("enquiry_date"))
        data["twelve_marks_name"] = (
            doc.get("student_education_details", {})
            .get("education_details", {})
            .get("inter_school_details", {})
            .get("obtained_cgpa")
        )
        if payload.get("form_filling_stage", {}).get(
                "form_filling_stage_b") is True:
            form_fill = []
            if (
                    doc.get("student_education_details", {})
                            .get("education_details", {})
                            .get("tenth_school_details")
                    is not None
            ):
                form_fill.append("10th")
            if (
                    doc.get("student_education_details", {})
                            .get("education_details", {})
                            .get("inter_school_details", {})
                            .get("is_pursuing")
                    is False
            ):
                form_fill.append("12th")
            if doc.get("declaration") is True:
                form_fill.append("Declaration")
            data["form_filling_stage"] = form_fill
        if payload.get("twelve_board", {}).get("twelve_board_b") is True:
            data["twelve_board_name"] = (
                doc.get("student_education_details", {})
                .get("education_details", {})
                .get("inter_school_details", {})
                .get("board")
            )
        return data

    async def get_data(
            self,
            payload=None,
            pipeline=None,
            skip=None,
            limit=None,
            source_data=None,
            payment_status=None,
            applications=True,
            publisher=False,
            start_date=None,
            end_date=None,
            advance_filters=None,
            twelve_score_sort=None,
    ):
        """Returns the application status of Student"""
        season = None
        if payload.get("season") not in ["", None]:
            season = payload.get("season")
        data_list, total_data = [], 0
        if applications:
            pipeline = await Application().aggregation_pipeline(
                payload=payload,
                pipeline=pipeline,
                payment_status=payment_status,
                skip=skip,
                limit=limit,
                advance_filters=advance_filters,
                twelve_score_sort=twelve_score_sort,
            )
            if source_data:
                result = DatabaseConfiguration(
                    season=season
                ).studentsPrimaryDetails.aggregate(pipeline)
            else:
                result = DatabaseConfiguration(
                    season=season
                ).studentApplicationForms.aggregate(pipeline)
            async for doc in result:
                try:
                    total_data = doc.get("totalCount", 0)
                except IndexError:
                    total_data = 0
                student_details = doc.get("student_primary", {})
                mobile_number = str(
                    student_details.get("basic_details", {}).get(
                        "mobile_number")
                )
                payment_status_value = doc.get("payment_info", {}).get(
                    "status", "")
                automation_names = doc.get("automation_details", {}).get(
                    "automation_names", []
                )
                data = {
                    "application_id": (
                        str(doc.get("_id"))
                        if not source_data
                        else str(
                            doc.get("student_applications", {}).get("_id"))
                    ),
                    "student_id": str(doc.get("student_id")),
                    "student_name": utility_obj.name_can(
                        student_details.get("basic_details", {})
                    ),
                    "custom_application_id": doc.get("custom_application_id"),
                    "course_name": (
                        f"{doc.get('course_details', {}).get('course_name')} in {doc.get('spec_name1')}"
                        if (doc.get("spec_name1") != "" and doc.get(
                            "spec_name1"))
                        else f"{doc.get('course_details', {}).get('course_name')}"
                    ),
                    "student_email_id": student_details.get("basic_details",
                                                            {}).get(
                        "email"
                    ),
                    "student_mobile_no": mobile_number,
                    "automation": doc.get("automation_details", {}).get(
                        "automation", None
                    ),
                    "automation_names": [item for sublist in automation_names
                                         if sublist for item in
                                         sublist] if automation_names else [],
                    "verification": await Student().get_lead_verification_info(
                        {
                            "student_verify": student_details.get("is_verify"),
                            "student_mobile_verify": student_details.get(
                                "is_mobile_verify"
                            ),
                            "student_email_verify": student_details.get(
                                "is_email_verify"
                            ),
                            "declaration": doc.get("declaration"),
                            "dv_status": doc.get("dv_status", "Not Verified"),
                        },
                        applications=applications,
                    ),
                    "payment_status": (
                        await Student().get_payment_status(
                            doc.get("payment_initiated", False)
                        )
                        if payment_status_value in ["", None]
                        else str(payment_status_value).title()
                    ),
                    "extra_fields": student_details.get("extra", {}),
                    "tags": student_details.get("tags"),
                }
                # TODO: Need to improve
                if payload.get("outbound_b"):
                    outbound_call = await DatabaseConfiguration().call_activity_collection.count_documents(
                        {"type": "Inbound", "call_from": mobile_number}
                    )
                    data.update({"outbound_call": outbound_call})
                if source_data:
                    data.update(
                        {
                            "application_status": doc.get("declaration"),
                            "application_stage": doc.get("current_stage"),
                            "course_fees": doc.get("fees"),
                            "submitted_on": utility_obj.get_local_time(
                                doc.get("last_updated_time", datetime.now(timezone.utc))
                            ),
                        }
                    )
                data = await self.get_data_based_on_condition(
                    payload, data, doc, source_data
                )
                data_list.append(data)
        else:
            data_list, total_data = await Student().get_leads_data_with_count(
                pipeline,
                payload,
                total_data,
                publisher=publisher,
            )
        return data_list, total_data

    async def all_applications_by_email(self, email, college_id):
        """
        Get all applications by email id
        """
        result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            [
                {
                    "$match": {
                        "basic_details.email": email.lower(),
                        "college_id": ObjectId(college_id),
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "basic_details": 1,
                        "address_details": 1,
                        "course_details": 1,
                    }
                },
                {
                    "$lookup": {
                        "from": "studentApplicationForms",
                        "let": {"id": "$_id"},
                        "pipeline": [
                            {"$match": {
                                "$expr": {"$eq": ["$student_id", "$$id"]}}},
                            {
                                "$project": {
                                    "_id": 1,
                                    "allocate_to_counselor": 1,
                                    "custom_application_id": 1,
                                    "course_id": 1,
                                    "college_id": 1,
                                    "payment_info": 1,
                                    "current_stage": 1,
                                    "last_updated_time": 1,
                                    "spec_name1": 1,
                                    "declaration": 1,
                                }
                            },
                        ],
                        "as": "student_applications",
                    }
                },
                {
                    "$replaceRoot": {
                        "newRoot": {
                            "$mergeObjects": [
                                {"$arrayElemAt": ["$student_applications", 0]},
                                "$$ROOT",
                            ]
                        }
                    }
                },
                {
                    "$unwind": {
                        "path": "$student_applications",
                        "includeArrayIndex": "arrayIndex",
                    }
                },
                {
                    "$lookup": {
                        "from": "courses",
                        "let": {"course_id": "$course_id"},
                        "pipeline": [
                            {"$match": {
                                "$expr": {"$eq": ["$_id", "$$course_id"]}}},
                            {"$project": {"fees": 1, "course_name": 1}},
                        ],
                        "as": "course_details",
                    }
                },
                {
                    "$replaceRoot": {
                        "newRoot": {
                            "$mergeObjects": [
                                {"$arrayElemAt": ["$course_details", 0]},
                                "$$ROOT",
                            ]
                        }
                    }
                },
                {
                    "$unwind": {
                        "path": "$course_details",
                        "includeArrayIndex": "arrayIndex",
                    }
                },
                {
                    "$project": {
                        "student_id": "$_id",
                        "student_basic_details": "$basic_details",
                        "_id": "$student_applications._id",
                        "custom_application_id": "$student_applications"
                                                 ".custom_application_id",
                        "course_name": "$course_details.course_name",
                        "course_spec": "$student_applications.spec_name1",
                        "student_email_id": "$basic_details.email",
                        "student_mobile_no": "$basic_details.mobile_number",
                        "application_status": "$student_applications" ".declaration",
                        "payment_status": "$student_applications"
                                          ".payment_info.status",
                        "course_fees": "$course_details.fees",
                        "application_stage": "$student_applications" ".current_stage",
                        "submitted_on": "$student_applications" ".last_updated_time",
                        "city_id": "$address_details.communication_address"
                                   ".city.city_id",
                    }
                },
            ]
        )
        return result

    async def get_all_applications_by_utm_source(
            self,
            source_type: str | None = None,
            lead_type: str | None = None,
            payment_status: list[str] | None = None,
            form_status: str | None = None,
            date_range: dict | None = None,
            utm_source: str = "",
            page_num: int = 1,
            page_size: int = 25
    ) -> list[dict]:
        """Get all applications data of to panelist

        Params:
            source_type (str | None, optional): Filter data accoring to the soruce existance - It should be 'primary', 'secondary' or 'tertiary'. Defaults to None.
            lead_type (str | None, optional): Filter data particularly as lead creates with Api or Online ('api', 'online'). Defaults to None.
            payment_status (list[str] | None, optional): Payment status can be any of the following: not started, started, captured, failed and refunded', example=['failed']. Defaults to None.
            form_status (str | None, optional): Filter application according to form status - "incomplete", "initiated" or "complete". Defaults to None.
            date_range (dict | None, optional): Date range which data has to be filter. Defaults to None.
            utm_source (str, optional): User associated with that source for filtering data. Defaults to "".
            page_num (int, optional): Current requested page no. Defaults to 1.
            page_size (int, optional): No of total data in one page. Defaults to 25.

        Returns:
            list[dict]: List of student application data.
        """

        skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                              page_size)

        sort = {}

        if source_type == "primary":
            match_stage = {
                "student.source.primary_source.utm_source": utm_source}
            sort.update(
                {"$sort": {"student.source.primary_source.utm_enq_date": -1}})
        elif source_type == "secondary":
            match_stage = {
                "student.source.secondary_source.utm_source": utm_source}
            sort.update({"$sort": {
                "student.source.secondary_source.utm_enq_date": -1}})
        elif source_type == "tertiary":
            match_stage = {
                "student.source.tertiary_source.utm_source": utm_source}
            sort.update(
                {"$sort": {"student.source.tertiary_source.utm_enq_date": -1}})
        else:
            match_stage = {
                "$or": [
                    {"student.source.primary_source.utm_source": utm_source},
                    {"student.source.secondary_source.utm_source": utm_source},
                    {"student.source.tertiary_source.utm_source": utm_source},
                ]
            }
            sort.update({"$sort": {"enquiry_date": -1}})

        if date_range and len(date_range) >= 2:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )

            if "captured" in payment_status:
                match_stage.update(
                    {"payment_info.created_at": {"$gte": start_date,
                                                 "$lte": end_date}}
                )
            else:
                match_stage.update(
                    {"enquiry_date": {"$gte": start_date, "$lte": end_date}}
                )

        if lead_type:
            match_stage.update(
                {
                    "student.source.primary_source.lead_type": lead_type
                }
            )

        if form_status:
            if form_status == "complete":
                match_stage.update({"declaration": True})
            elif form_status == "initiated":
                match_stage.update({"current_stage": {"$gte": 2}})
            else:
                match_stage.update({"declaration": False})

        if payment_status:
            payment_cond = []

            if "not started" in payment_status:
                payment_cond.append({"payment_initiated": False})

            if "started" in payment_status:
                payment_cond.append(
                    {
                        "payment_initiated": True,
                        "payment_info.status": {"$ne": "captured"},
                    }
                )

            status = ["captured", "failed", "refunded"]

            for st in status:
                if st in payment_status:
                    payment_cond.append({"payment_info.status": st})

            if payment_cond:
                temp = {"$and": [match_stage, {"$or": payment_cond}]}
                match_stage = temp

        pipeline = [
            {
                "$lookup": {
                    "from": "studentsPrimaryDetails",
                    "localField": "student_id",
                    "foreignField": "_id",
                    "as": "student",
                }
            },
            {"$unwind": "$student"},
            {"$match": match_stage},
            {
                "$lookup": {
                    "from": "courses",
                    "localField": "course_id",
                    "foreignField": "_id",
                    "as": "course",
                }
            },
            {"$unwind": "$course"},
            sort,
            {
                "$facet": {
                    "totalCount": [{"$count": "total"}],
                    "data": [{"$skip": skip}, {"$limit": limit}],
                }
            },
        ]

        results = (
            await DatabaseConfiguration()
            .studentApplicationForms.aggregate(pipeline)
            .to_list(None)
        )

        try:
            results = results[0]
            count = results.get("totalCount", [])
            results = results.get("data", [])
            total_count = count[0].get("total", 0)
        except IndexError:
            total_count = 0
            results = []

        data = []
        for result in results:
            course = result.get("course", {})
            student = result.get("student", {})
            payment_status_value = result.get("payment_info", {}).get("status")

            data.append(
                {
                    "application_id": str(result.get("_id")),
                    "student_id": str(student.get("_id")),
                    "student_name": utility_obj.name_can(
                        student.get("basic_details", {})
                    ),
                    "custom_application_id": utility_obj.mask_custom_format_string(
                        result.get("custom_application_id")),
                    "course_name": (
                        f"{course.get('course_name')} in {result.get('spec_name1')}"
                        if (result.get("spec_name1") != "" and result.get(
                            "spec_name1"))
                        else f"{course.get('course_name')}"
                    ),
                    "student_email_id": utility_obj.mask_email(
                        student.get("basic_details", {}).get("email")),
                    "student_mobile_no": utility_obj.mask_phone_number(
                        student.get("basic_details", {}).get(
                            "mobile_number"
                        )),
                    "payment_status": (
                        await Student().get_payment_status(
                            result.get("payment_initiated", False)
                        )
                        if payment_status_value in ["", None]
                        else str(payment_status_value).title()
                    ),
                    "form_status": "Completed" if result.get(
                        "declaration") else "In Progress",
                    "tags": student.get("tags", []),
                    "lead_type": student.get("source", {})
                    .get("primary_source", {})
                    .get("lead_type"),
                    "application_stage": utility_obj.get_application_stage(
                        result.get("current_stage")),
                    "course_fees": course.get("fees"),
                    "submitted_on": utility_obj.get_local_time(
                        result.get("enquiry_date")
                    ),
                    "utm_medium": student.get("source", {})
                    .get("primary_source", {})
                    .get("utm_medium"),
                    "utm_campaign": student.get("source", {})
                    .get("primary_source", {})
                    .get("utm_campaign"),
                }
            )
        return data, total_count

    async def get_all_leads_by_utm_source(
            self,
            payload,
            start_date,
            end_date,
            utm_source,
            source_type,
            page_num,
            page_size,
            payment_status=None,
            application=None,
            twelve_score_sort=None,
    ):
        """
        Get data based on publisher associated source value
        """
        skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                              page_size)

        pipeline = [
            {
                "$match": {
                    "created_at": {
                        "$gte": start_date,
                        "$lte": end_date,
                    }
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "primary_source": "$source.primary_source",
                    "basic_details": 1,
                }
            },
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": {"id": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": ["$student_id", "$$id"],
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 1,
                                "allocate_to_counselor": 1,
                                "custom_application_id": 1,
                                "course_id": 1,
                                "college_id": 1,
                                "payment_info": 1,
                                "payment_initiated": 1,
                                "current_stage": 1,
                                "last_updated_time": 1,
                                "spec_name1": 1,
                                "declaration": 1,
                            }
                        },
                    ],
                    "as": "student_applications",
                }
            },
            {
                "$replaceRoot": {
                    "newRoot": {
                        "$mergeObjects": [
                            {"$arrayElemAt": ["$student_applications", 0]},
                            "$$ROOT",
                        ]
                    }
                }
            },
            {
                "$unwind": {
                    "path": "$student_applications",
                    "includeArrayIndex": "arrayIndex",
                }
            },
            {
                "$lookup": {
                    "from": "courses",
                    "let": {"course_id": "$course_id"},
                    "pipeline": [
                        {"$match": {
                            "$expr": {"$eq": ["$_id", "$$course_id"]}}},
                        {"$project": {"fees": 1, "course_name": 1}},
                    ],
                    "as": "course_details",
                }
            },
            {
                "$replaceRoot": {
                    "newRoot": {
                        "$mergeObjects": [
                            {"$arrayElemAt": ["$course_details", 0]},
                            "$$ROOT",
                        ]
                    }
                }
            },
            {"$unwind": {"path": "$course_details",
                         "includeArrayIndex": "arrayIndex"}},
            {
                "$lookup": {
                    "from": "studentSecondaryDetails",
                    "let": {"id": "$student_id"},
                    "pipeline": [
                        {"$match": {
                            "$expr": {"$eq": ["$student_id", "$$id"]}}},
                        {"$project": {"education_details": 1}},
                    ],
                    "as": "student_education_details",
                }
            },
            {
                "$unwind": {
                    "path": "$student_education_details",
                    "preserveNullAndEmptyArrays": True,
                }
            },
        ]
        if twelve_score_sort is not None:
            order_decide = 1 if twelve_score_sort else -1
            pipeline.append(
                {
                    "$sort": {
                        "student_education_details.education_details."
                        "inter_school_details.obtained_cgpa": order_decide
                    }
                }
            )
        if payment_status:
            if (
                    "captured" in payment_status
                    or "failed" in payment_status
                    or "refunded" in payment_status
            ):
                pipeline[2].get("$lookup", {}).get("pipeline", [])[0].get(
                    "$match", {}
                ).update(
                    {"payment_info.created_at": {"$gte": start_date,
                                                 "$lte": end_date}}
                )
                pipeline[0].get("$match").pop(
                    "source.primary_source" ".utm_enq_date")
        if application:
            pipeline[2].get("$lookup", {}).get("pipeline", [])[0].get(
                "$match", {}
            ).update({"current_stage": {"$gte": 2}})
        if source_type == "secondary":
            pipeline[0].get("$match").update(
                {"source.secondary_source.utm_source": utm_source}
            )
            pipeline.insert(1, {
                "$sort": {"source.secondary_source.utm_enq_date": -1}})
        elif source_type == "tertiary":
            pipeline[0].get("$match").update(
                {"source.tertiary_source.utm_source": utm_source}
            )
            pipeline.insert(1, {
                "$sort": {"source.tertiary_source.utm_enq_date": -1}})
        elif source_type == "all":
            pipeline[0].get("$match").update(
                {
                    "$or": [
                        {"source.primary_source.utm_source": utm_source},
                        {"source.secondary_source.utm_source": utm_source},
                        {"source.tertiary_source.utm_source": utm_source},
                    ]
                }
            )
            pipeline.insert(1, {
                "$sort": {"source.primary_source.utm_enq_date": -1}})
        else:
            pipeline[0].get("$match").update(
                {"source.primary_source.utm_source": utm_source}
            )
            pipeline.insert(1, {
                "$sort": {"source.primary_source.utm_enq_date": -1}})
        data, total_data = await self.get_data(
            payload=payload,
            pipeline=pipeline,
            skip=skip,
            limit=limit,
            source_data=True,
            applications=False,
            payment_status=payment_status,
        )
        return data, total_data

    async def apply_lookup_on_leadfollowup(
            self,
            pipeline: list,
            foreign_field: str = "application_id",
            payload=None,
            collection_index=None,
            filter_index=None,
            skip=None,
            limit=None,
    ) -> list:
        """
        Update pipeline by apply lookup on leadsFollowUp.

        Params:
            - pipeline (list): A aggregation pipeline which want to update.
            - foreign_field (str): Default value: "application_id".
                A field value will be useful for get leadsFollowUp.

        Returns:
            list: A list which contains updated aggregation pipeline.
        """
        if payload is None:
            payload = {}
        pipeline.append(
            {
                "$lookup": {
                    "from": "leadsFollowUp",
                    "localField": "_id",
                    "foreignField": foreign_field,
                    "as": "lead_details",
                }
            }
        )
        if not payload.get("lead_stage", {}).get("lead_name", []):
            pipeline.append(
                {
                    "$unwind": {
                        "path": "$lead_details",
                        "preserveNullAndEmptyArrays": True,
                    }
                }
            )
        else:
            pipeline.append(
                {
                    "$unwind": {
                        "path": "$lead_details",
                    }
                }
            )
        temp_list = []
        if payload.get("lead_stage", {}).get("lead_name", []):
            for load in payload.get("lead_stage", {}).get("lead_name", []):
                label_list = [
                    {"lead_details.lead_stage_label": label}
                    for label in load.get("label", [])
                ]
                lead_stages = load.get("name", [])
                if "Fresh Lead" in lead_stages:
                    lead_stages.append(None)
                if len(label_list) > 0:
                    temp_list.append(
                        {
                            "$and": [
                                {
                                    "lead_details.lead_stage": {
                                        "$in": [
                                            item.title()
                                            for item in load.get("name", [])
                                        ]
                                    }
                                },
                                {"$or": label_list},
                            ]
                        }
                    )
                elif len(lead_stages) > 0:
                    temp_list.append(
                        {"lead_details.lead_stage": {"$in": lead_stages}})
        if len(temp_list) > 0:
            pipeline.append({"$match": {"$or": temp_list}})
        lead_stage_info = payload.get("lead_name", [])
        if lead_stage_info:
            lead_stage_names, lead_stage_labels, lead_stage_filter = [], [], {}
            for stage_data in lead_stage_info:
                if stage_data.get("name", []):
                    lead_stage_names.extend(stage_data.get("name", []))
                    if "Fresh Lead" in stage_data.get("name", []):
                        lead_stage_names.append(None)
                if stage_data.get("label", []):
                    lead_stage_labels.extend(stage_data.get("label", []))
            if lead_stage_names:
                lead_stage_filter = {
                    "lead_details.lead_stage": {"$in": lead_stage_names}
                }
            if lead_stage_labels:
                lead_stage_filter.update(
                    {"lead_details.lead_stage_label": {
                        "$in": lead_stage_labels}}
                )
            if lead_stage_filter:
                pipeline.append({"$match": lead_stage_filter})
        if collection_index:
            if filter_index is not None:
                if (
                        collection_index.get("leadsFollowUp", {}).get(
                            filter_index)
                        == "leadsFollowUp"
                ):
                    pipeline = utility_obj.get_count_aggregation(
                        pipeline, skip=skip, limit=limit
                    )
        return pipeline

    async def apply_lookup_on_communication_log(
            self, pipeline: list, local_field="student_id"
    ) -> list:
        """
        Update pipeline by apply lookup on communicationLog.

        Params:
            - pipeline (list): A aggregation pipeline which want to update.
            - local_field (str): Default value: "student_id".
                A field value will be useful for get communication log.

        Returns:
            list: A list which contains updated aggregation pipeline.
        """
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "communicationLog",
                        "localField": local_field,
                        "foreignField": "student_id",
                        "as": "communication_log",
                    }
                },
                {
                    "$addFields": {
                        "communication_log": {
                            "$arrayElemAt": ["$communication_log", 0]}
                    }
                },
            ]
        )
        return pipeline

    async def apply_lookup_on_queries(
            self, pipeline: list, local_field="student_id"
    ) -> list:
        """
        Update pipeline by apply lookup on queries.

        Params:
            - pipeline (list): A aggregation pipeline which want to update.
            - local_field (str): Default value: "student_id".
                A field value will be useful for get queries.

        Returns:
            list: A list which contains updated aggregation pipeline.
        """
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "queries",
                        "localField": local_field,
                        "foreignField": "student_id",
                        "as": "queries",
                    }
                },
                {"$unwind": {"path": "$queries",
                             "preserveNullAndEmptyArrays": True}},
            ]
        )
        return pipeline

    async def apply_lookup_on_student_secondary(
            self, pipeline: list, field: str = "student_id"
    ) -> list:
        """
        Update pipeline by apply lookup on queries.

        Params:
            - pipeline (list): A aggregation pipeline which want to update.
            - field (str): Default value: "$student_id". A field value will be
                useful for get secondary data.

        Returns:
            list: A list which contains updated aggregation pipeline.
        """
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "studentSecondaryDetails",
                        "localField": field,
                        "foreignField": "student_id",
                        "as": "student_education_details",
                    }
                },
                {
                    "$unwind": {
                        "path": "$student_education_details",
                        "preserveNullAndEmptyArrays": True,
                    },
                },
            ]
        )
        return pipeline

    # Todo : Work on merging Projection
    async def all_applications(
            self,
            payload=None,
            college_id=None,
            page_num=None,
            page_size=None,
            start_date=None,
            end_date=None,
            counselor_id=None,
            applications=True,
            source_name=None,
            publisher=False,
            form_initiated=True,
            twelve_score_sort=None,
            call_segments=False,
            application_ids=None,
            student_ids=None,
            data_segment=None,
            is_head_counselor=False,
    ):
        """
        Get all applications
        """
        skip = limit = None
        if payload is None:
            payload = {}
        if applications:
            collection_index = {
                "studentApplicationForms": {0: "studentApplicationForms"},
                "studentsPrimaryDetails": {1: "studentsPrimaryDetails"},
                "leadsFollowUp": {2: "leadsFollowUp"},
                "studentSecondaryDetails": {3: "studentSecondaryDetails"},
            }
        else:
            collection_index = {
                "studentsPrimaryDetails": {0: "studentsPrimaryDetails"},
                "studentApplicationForms": {1: "studentApplicationForms"},
                "leadsFollowUp": {2: "leadsFollowUp"},
                "studentSecondaryDetails": {3: "studentSecondaryDetails"},
            }
        filter_index = Check_payload(collection_index).get_meal(
            payload=payload, applications=applications
        )
        if page_num is not None and page_size is not None:
            skip, limit = await Application().get_values(
                page_num,
                page_size,
                start_date=start_date,
                end_date=end_date,
                college_id=college_id,
            )
        advance_filters = payload.get("advance_filters", [])
        if applications:
            pipeline = await self.initialize_pipeline_all_applications(
                college_id,
                start_date,
                end_date,
                skip=skip,
                limit=limit,
                application_ids=application_ids,
                filter_index=filter_index,
                collection_index=collection_index,
                counselor_id=counselor_id,
                is_head_counselor=is_head_counselor,
                advance_filter=advance_filters,
                payload=payload,
            )
            pipeline = await self.primary_lookup_pipeline(
                pipeline=pipeline,
                payload=payload,
                skip=skip,
                limit=limit,
                filter_index=filter_index,
                collection_index=collection_index,
                advance_filter=advance_filters
            )
            if (
                    payload.get("lead_stage", {}).get("lead_name", [])
                    or payload.get("lead_stage", {}).get("lead_b") is True
            ) and not advance_filters:
                pipeline = await self.apply_lookup_on_leadfollowup(
                    pipeline,
                    payload=payload,
                    collection_index=collection_index,
                    filter_index=filter_index,
                    skip=skip,
                    limit=limit,
                )
            pipeline = await self.course_pipeline(pipeline)
            pipeline = await self.apply_lookup_on_student_secondary(pipeline)
            if advance_filters:
                check = str(advance_filters)
                pipeline = await self.apply_lookup_on_leadfollowup(
                    pipeline, payload=payload
                )
                pipeline = await self.apply_lookup_on_communication_log(
                    pipeline)
                if "queries" in check:
                    pipeline = await self.apply_lookup_on_queries(pipeline)
                pipeline = await AdvanceFilterHelper().apply_advance_filter(
                    advance_filters,
                    pipeline,
                    student_primary="student_primary",
                    courses="course_details",
                    student_secondary="student_education_details",
                    lead_followup="lead_details",
                    communication_log="communication_log",
                    queries="queries",
                )
            pipeline = self.apply_twelve_board_form_initiated_application_filling_stage(
                form_initiated,
                pipeline,
                payload,
            )
            pipeline = await self.apply_course_filter(pipeline, payload)
            pipeline = self.apply_payment_status_filter(
                pipeline, payload, start_date, end_date
            )
            annual_income = payload.get("annual_income", [])
            if annual_income:
                pipeline.append(
                    {"$match":
                         {"student_education_details.family_annual_income": {"$in": annual_income}}
                     }
                )
        else:
            student_obj = Student()
            pipeline = await student_obj.pipeline_for_view_all_leads(
                start_date,
                end_date,
                payload,
                skip=skip,
                limit=limit,
                counselor_id=counselor_id,
                student_ids=student_ids,
                twelve_score_sort=twelve_score_sort,
                publisher=publisher,
                source_name=source_name,
                data_segment=data_segment,
                is_head_counselor=is_head_counselor,
                collection_index=collection_index,
                filter_index=filter_index,
            )
        if call_segments:
            return pipeline
        data, total_data = await self.get_data(
            payload=payload,
            pipeline=pipeline,
            skip=skip,
            limit=limit,
            applications=applications,
            publisher=publisher,
            start_date=start_date,
            end_date=end_date,
            advance_filters=advance_filters,
            twelve_score_sort=twelve_score_sort,
        )
        return data, total_data

    def apply_twelve_board_form_initiated_application_filling_stage(
            self,
            form_initiated: bool | None,
            pipeline: list,
            payload: dict,
    ):
        """
        Update the pipeline for filters: twelve_board , form_filling_stage,
            twelve_marks
        Params:
          - twelve_score_sort (bool): If true sort the twelve score  else don't
                sort
          - form_initiated (bool): get applications whose form is initiated
          - pipeline (list): the pipeline which has to be updated
          - Payload (dict): The dict that has all  filters
        Returns:
          The updated pipeline
        """
        if form_initiated:
            pipeline[0].get("$match", {}).update(
                {"current_stage": {"$gte": 2}})
        if payload.get("application_filling_stage"):
            match_stage = pipeline[0].get("$match", {})
            if "$or" in match_stage:
                match_stage.update({"$and": [
                    {"$or": payload.get("application_filling_stage", [])},
                    {"$or": match_stage.pop("$or")}]})
            else:
                match_stage.update(
                    {"$or": payload.get("application_filling_stage", [])}
                )
        return pipeline

    async def course_pipeline(self, pipeline: list) -> list:
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "courses",
                        "localField": "course_id",
                        "foreignField": "_id",
                        "as": "course_details",
                    }
                },
                {
                    "$addFields": {
                        "course_details": {
                            "$arrayElemAt": ["$course_details", 0]}
                    }
                },
            ]
        )
        return pipeline

    async def primary_lookup_pipeline(
            self,
            pipeline: list,
            payload: dict | None = None,
            skip=None,
            limit=None,
            filter_index=0,
            collection_index=None,
            advance_filter=None
    ):
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "studentsPrimaryDetails",
                        "localField": "student_id",
                        "foreignField": "_id",
                        "as": "student_primary",
                    }
                },
                {
                    "$addFields": {
                        "student_primary": {
                            "$arrayElemAt": ["$student_primary", 0]}
                    }
                },
                {
                    "$addFields": {
                        "student_primary.extra": "$student_primary.extra_fields",
                        "student_primary.lead_age": {
                            "$dateDiff": {
                                "startDate": "$student_primary.created_at",
                                "endDate": datetime.now(timezone.utc),
                                "unit": "day"
                            }
                        },
                        "student_primary.basic_details.whatsapp_no": {
                            "$cond": {
                                "if": {"$eq": ["$student_primary.basic_details.whatsapp_no", "Other"]},
                                "then": "$student_primary.basic_details.mention_whatsapp_no",
                                "else": "$student_primary.basic_details.whatsapp_no"
                            }
                        }
                    }
                },
            ]
        )
        match = {}
        if payload.get("state", {}).get("state_code", []):
            match.update(
                {
                    "student_primary.address_details.communication_address"
                    ".state.state_code": {
                        "$in": [
                            x.upper()
                            for x in
                            payload.get("state", {}).get("state_code", [])
                        ]
                    }
                }
            )
        gender_info = payload.get("gender", [])
        if gender_info:
            match.update(
                {
                    "student_primary.basic_details.gender": {
                        "$in": gender_info
                    }
                }
            )
        category_info = payload.get("category", [])
        if category_info:
            match.update(
                {
                    "student_primary.basic_details.category": {
                        "$in": category_info
                    }
                }
            )
        if payload.get("city", {}).get("city_name", []):
            match.update(
                {
                    "student_primary.address_details.communication_address"
                    ".city.city_name": {
                        "$in": [
                            x.title()
                            for x in
                            payload.get("city", {}).get("city_name", [])
                        ]
                    }
                }
            )
        if payload.get("is_verify") not in ["", None]:
            if payload.get("is_verify") == "verified":
                match.update({"student_primary.is_verify": True})
            elif payload.get("is_verify") == "unverified":
                match.update({"student_primary.is_verify": False})
        source_type_name = payload.get("source_type", [])
        if source_type_name:
            source_type = []
            if "primary" in source_type_name:
                source_type.append(
                    {"student_primary.source.primary_source": {
                        "$exists": True}}
                )
            if "secondary" in source_type_name:
                source_type.append(
                    {"student_primary.source.secondary_source": {
                        "$exists": True}}
                )
            if "tertiary" in source_type_name:
                source_type.append(
                    {"student_primary.source.tertiary_source": {
                        "$exists": True}}
                )
            if source_type:
                match.update({"$and": source_type})
        if payload.get("source", {}).get("source_name", []):
            sources = []
            for x in payload.get("source", {}).get("source_name", []):
                sources.append(str(x).lower())
            match.update(
                {"student_primary.source.primary_source.utm_source": {
                    "$in": sources}}
            )
        if payload.get("utm_medium", []):
            temp_list = [
                {
                    "student_primary.source.primary_source.utm_source": utm_medium_data.get(
                        "source_name"
                    ),
                    "student_primary.source.primary_source.utm_medium": utm_medium_data.get(
                        "utm_medium"
                    ),
                }
                for utm_medium_data in payload.get("utm_medium", [])
            ]
            if len(temp_list) > 0:
                match.update({"$or": temp_list})
        if (
                payload.get("lead_type", {}).get("lead_type_name") is not None
                and payload.get("lead_type", {}).get("lead_type_name") != ""
        ):
            match.update(
                {
                    "student_primary.source.primary_source.lead_type": payload.get(
                        "lead_type", {}
                    )
                    .get("lead_type_name")
                    .lower()
                }
            )
        if payload.get("extra_filters", []):
            extra_fields = [
                {
                    "student_primary.extra_fields": {
                        "$elemMatch": {
                            "k": condition.get("field_name"),
                            "v": condition.get("value"),
                        }
                    }
                }
                for condition in payload.get("extra_filters", [])
            ]
            match.update({"$or": extra_fields})
        if match:
            pipeline.append({"$match": match})
        if collection_index and not advance_filter:
            if filter_index is not None:
                if (
                        collection_index.get("studentsPrimaryDetails", {}).get(
                            filter_index)
                        == "studentsPrimaryDetails"
                ):
                    pipeline = utility_obj.get_count_aggregation(
                        pipeline, skip=skip, limit=limit
                    )
        return pipeline

    async def initialize_pipeline_all_applications(
            self,
            college_id: str,
            start_date,
            end_date,
            application_ids=None,
            filter_index=None,
            skip=None,
            limit=None,
            collection_index=None,
            counselor_id=None,
            is_head_counselor=None,
            advance_filter=None,
            paid_filter=None,
            payload=None,
    ):
        """
        Initialize the pipeline

        Params:
            - pipeline (list):  the pipeline that is to be updated
            - payload (dict): The dict that has filters
            - college_id (str): the unique id of  college
            - start_date (None | datetime): Either None or start datetime which
                useful for get data according to start date.
            - end_date (None | datetime): Either None or end datetime which
                useful for get data according to end date.

        Returns:
            - list: Updated pipeline of aggregation.
        """
        if payload is None:
            payload = {}
        lead_project_info = await self.get_lead_project_stage_info()
        lead_project_info.update(
            {"extra": "$extra",
             "extra_fields": {"$objectToArray": "$extra_fields"}}
        )
        pipeline = [
            {
                "$match": {
                    "college_id": ObjectId(college_id),
                }
            },
            {"$sort": {"enquiry_date": -1}},
        ]
        if paid_filter:
            pipeline[0].get("$match", {}).update(
                {"payment_info.status": "captured"})
        if collection_index and not advance_filter:
            if filter_index is not None:
                if (
                        collection_index.get("studentApplicationForms",
                                             {}).get(
                            filter_index
                        )
                        == "studentApplicationForms"
                ):
                    pipeline = utility_obj.get_count_aggregation(
                        pipeline, skip=skip, limit=limit
                    )
        if (
                payload.get("counselor", {}).get("counselor_id", [])
                or counselor_id is not None
                or is_head_counselor
        ):
            if payload.get("counselor", {}).get("counselor_id", []):
                counselor_id = [
                    ObjectId(x)
                    for x in
                    payload.get("counselor", {}).get("counselor_id", [])
                ]
            pipeline[0].get("$match", {}).update(
                {"allocate_to_counselor.counselor_id": {"$in": counselor_id}}
            )
        if start_date and end_date:
            pipeline[0].get("$match", {}).update(
                {"enquiry_date": {"$gte": start_date, "$lte": end_date}}
            )
        if application_ids:
            pipeline[0].get("$match", {}).update(
                {"_id": {"$in": application_ids}})
        return pipeline

    async def apply_course_filter(self, pipeline: list, payload: dict):
        """
        Updates the pipeline for course filter.

        Params:
            - Pipeline (list): the list which is to be updated
            - Payload (dict): the dict that has filters

        Returns:
            - list: Updated pipeline of aggregation.
        """
        course_payload = payload.get("course", {})
        if course_payload is None:
            course_payload = {}
        courses_info = course_payload.get("course_id", [])
        specializations_info = course_payload.get("course_specialization", [])
        if courses_info and specializations_info:
            course_filter = []
            for course_id, spec_name in zip(courses_info,
                                            specializations_info):
                if await utility_obj.is_length_valid(str(course_id),
                                                     "Course id"):
                    course_filter.append(
                        {"course_id": ObjectId(course_id),
                         "spec_name1": spec_name}
                    )
            if course_filter:
                match_stage = pipeline[0].get("$match", {})
                if "$or" in match_stage:
                    match_stage.update({"$and": [{"$or": course_filter}, {
                        "$or": match_stage.pop("$or")}]})
                else:
                    match_stage.update({"$or": course_filter})
        return pipeline

    def apply_payment_status_filter(
            self, pipeline: list, payload: dict, start_date, end_date
    ):
        """
        Update the pipeline for payment status filter.

        Params:
            - pipeline (list): the pipeline which is to be updated
            - payload (dict): The dict which has filters
            - start_date (str): the start date in date range
            - end_date (str): the end date in date range

        Returns:
            - list: Updated pipeline of aggregation.
        """
        payment_status = payload.get("payment_status", [])
        payment_data = []
        if payment_status:
            if "not started" in payment_status:
                payment_data.append({"payment_initiated": False})
            if "started" in payment_status:
                payment_data.append(
                    {
                        "payment_initiated": True,
                        "payment_info.status": {"$ne": "captured"},
                    }
                )
            if (
                    "captured" in payment_status
                    or "failed" in payment_status
                    or "refunded" in payment_status
            ):
                if start_date and end_date:
                    if pipeline[0].get("$match", {}).get("enquiry_date"):
                        pipeline[0].get("$match").pop("enquiry_date")
                    pipeline[0].get("$match").update(
                        {
                            "payment_info.created_at": {
                                "$gte": start_date,
                                "$lte": end_date,
                            }
                        }
                    )
                if "captured" in payment_status:
                    payment_data.append({"payment_info.status": "captured"})
                if "failed" in payment_status:
                    payment_data.append({"payment_info.status": "failed"})
                if "refunded" in payment_status:
                    payment_data.append({"payment_info.status": "refunded"})
            if payment_data:
                match_stage = pipeline[0].get("$match", {})
                if "$and" in match_stage:
                    multiple_stages = [{
                        "$or": payment_data}] + match_stage.pop(
                        "$and")
                    match_stage.update({"$and": multiple_stages})
                elif "$or" in match_stage:
                    match_stage.update({"$and": [{"$or": payment_data}, {
                        "$or": match_stage.pop("$or")}]})
                else:
                    match_stage.update({"$or": payment_data})
        return pipeline

    def apply_is_verify_filter(self, pipeline: list, payload: dict):
        """
        Update the pipeline for filter is_verify.

        Params:
            - pipeline (list): the pipeline which is to be updated
            - payload (dict):  the dict which has filters

        Returns:
            - list: Updated pipeline of aggregation.
        """
        if payload.get("is_verify") is not None and payload.get(
                "is_verify") != "":
            if payload.get("is_verify") == "verified":
                pipeline.append(
                    {"$match": {"student_primary.is_verify": True}})
            elif payload.get("is_verify") == "unverified":
                pipeline.append(
                    {"$match": {"student_primary.is_verify": False}})
        return pipeline

    async def apply_application_stage(
            self, application_stage: dict, basic_match: dict
    ) -> dict:
        """
        Apply application stage filter
        Params:
            application_stage (dict): Application stage filter
            basic_match (dict): basic match in pipeline
        Return:
            basic_match (dict): Return updated basic match
        """
        current_stage_cond = []
        app_stage_from = application_stage.get("stage_from")
        app_stage_to = application_stage.get("stage_to")
        current_stages = [2.5, 3.75, 5, 6.25, 7.5, 8.75, 10]
        app_stage_to_index = current_stages.index(app_stage_to)
        previous_stage = current_stages[app_stage_to_index - 1]
        if app_stage_to_index > 0 and app_stage_from in ["", None]:
            current_stage_cond.append({"current_stage": previous_stage})
        elif app_stage_from not in ["",
                                    None] and app_stage_from == previous_stage:
            current_stage_cond.append({"current_stage": app_stage_from})
        else:
            current_stage_cond.append({"current_stage": {"$lt": 2.5}})
        basic_match.update({"$and": current_stage_cond})
        return basic_match

    async def extend_pipeline_based_on_condition_for_automation(
            self,
            start_date,
            end_date,
            college_id,
            payload,
            skip=None,
            limit=None,
            advance_filters=None,
    ):
        """
        Get pipeline for the collection named studentApplicationForms
        """
        current_stage_cond = []
        if payload is None:
            payload = {}
        collection_index = {
            "studentApplicationForms": {0: "studentApplicationForms"},
            "studentsPrimaryDetails": {1: "studentsPrimaryDetails"},
            "leadsFollowUp": {2: "leadsFollowUp"},
            "studentSecondaryDetails": {3: "studentSecondaryDetails"},
        }
        filter_index = Check_payload(collection_index).get_meal(
            payload=payload, applications=True
        )
        basic_match = {}
        application_stage = payload.get("application_stage")
        if application_stage:
            basic_match = await self.apply_application_stage(
                application_stage, basic_match
            )
        basic_match.update({"college_id": ObjectId(college_id)})
        if start_date not in ["", None] and end_date not in ["", None]:
            basic_match.update(
                {"enquiry_date": {"$gte": start_date, "$lte": end_date}})
        elif start_date not in ["", None] and end_date in [None, ""]:
            basic_match.update({"enquiry_date": {"$gte": start_date}})
        app_filling_stage = payload.get("application_filling_stage", [])
        if app_filling_stage:
            basic_match.update({"$or": app_filling_stage})
        pipeline = [{"$match": basic_match}, {"$sort": {"enquiry_date": -1}}]
        if skip is not None and limit is not None:
            if collection_index and not advance_filters:
                if filter_index is not None:
                    if (
                            collection_index.get("studentApplicationForms",
                                                 {}).get(
                                filter_index
                            )
                            == "studentApplicationForms"
                    ):
                        pipeline = utility_obj.get_count_aggregation(
                            pipeline, skip=skip, limit=limit
                        )
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "studentsPrimaryDetails",
                        "let": {"id": "$student_id"},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$_id", "$$id"]}}},
                            {
                                "$project": await self.get_lead_project_stage_info()},
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
            ]
        ),
        primary_match = {}
        if payload.get("is_verify") is not None and payload.get(
                "is_verify") != "":
            if payload.get("is_verify", "").lower() == "verified":
                primary_match.update({"student_primary.is_verify": True})
            elif payload.get("is_verify").lower() == "unverified":
                primary_match.update({"student_primary.is_verify": False})
        if payload.get("state_code"):
            primary_match.update(
                {
                    "student_primary.address_details"
                    ".communication_address.state.state_code": {
                        "$in": [x.upper() for x in payload.get("state_code")]
                    }
                }
            )
        if payload.get("city_name"):
            primary_match.update(
                {
                    "student_primary.address_details.communication_address"
                    ".city.city_name": {
                        "$in": [x.title() for x in payload.get("city_name")]
                    }
                }
            )
        if payload.get("source_name"):
            sources = []
            for x in payload.get("source_name"):
                sources.append(x.lower())
            primary_match.update(
                {"student_primary.source.primary_source.utm_source": {
                    "$in": sources}}
            )
        if (
                payload.get("lead_type_name") is not None
                and payload.get("lead_type_name") != ""
        ):
            primary_match.update(
                {
                    "student_primary.source."
                    "primary_source.lead_type": payload.get(
                        "lead_type_name").lower()
                }
            )
        if primary_match:
            pipeline.append({"$match": primary_match})
        if skip is not None and limit is not None:
            if collection_index and not advance_filters:
                if filter_index is not None:
                    if (
                            collection_index.get("studentsPrimaryDetails",
                                                 {}).get(
                                filter_index
                            )
                            == "studentsPrimaryDetails"
                    ):
                        pipeline = utility_obj.get_count_aggregation(
                            pipeline, skip=skip, limit=limit
                        )
        pipeline = await self.apply_course_filter(pipeline, payload)
        pipeline = await self.apply_lookup_on_leadfollowup(
            pipeline=pipeline,
            payload=payload,
            collection_index=collection_index,
            filter_index=filter_index,
            skip=skip,
            limit=limit,
        )
        pipeline = await self.apply_lookup_on_student_secondary(pipeline)
        twelve_board = payload.get("twelve_board", [])
        secondary_match = {}
        if twelve_board:
            secondary_match.update(
                {
                    "student_education_details.education_details"
                    ".inter_school_details.board": {"$in": twelve_board}
                }
            )
        twelve_marks = payload.get("twelve_marks", [])
        if twelve_marks:
            twelve_marks = [
                {
                    "student_education_details.education_details."
                    "inter_school_details.obtained_cgpa": {
                        "$gte": float(element.split("-")[0]),
                        "$lt": float(element.split("-")[-1]),
                    }
                }
                for element in twelve_marks
                if "-" in element
            ]
            if twelve_marks:
                secondary_match.update({"$or": twelve_marks})
        form_filling_stage = payload.get("form_filling_stage", [])
        if form_filling_stage:
            form_filling = []
            if "12th" in form_filling_stage:
                form_filling.append(
                    {
                        "student_education_details.education_details"
                        ".inter_school_details.is_pursuing": False
                    }
                )
            if "10th" in form_filling_stage:
                form_filling.append(
                    {
                        "student_education_details.education_details"
                        ".tenth_school_details": {"$exists": True}
                    }
                )
            if "Declaration" in form_filling_stage:
                form_filling.append({"declaration": True})
            secondary_match.update({"$and": form_filling})
        if secondary_match:
            pipeline.append({"$match": secondary_match})
        if skip is not None and limit is not None:
            if collection_index and not advance_filters:
                if filter_index is not None:
                    if (
                            collection_index.get("studentSecondaryDetails",
                                                 {}).get(
                                filter_index
                            )
                            == "studentSecondaryDetails"
                    ):
                        pipeline = utility_obj.get_count_aggregation(
                            pipeline, skip=skip, limit=limit
                        )
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "courses",
                        "let": {"course_id": "$course_id"},
                        "pipeline": [
                            {"$match": {
                                "$expr": {"$eq": ["$_id", "$$course_id"]}}},
                            {"$project": {"_id": 0, "fees": 1,
                                          "course_name": 1}},
                        ],
                        "as": "course_details",
                    }
                },
                {
                    "$unwind": {
                        "path": "$course_details",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
            ]
        )
        if advance_filters:
            pipeline = await self.apply_lookup_on_communication_log(pipeline)
            check = str(advance_filters)
            if "queries" in check:
                pipeline = await self.apply_lookup_on_queries(pipeline)
            pipeline = await AdvanceFilterHelper().apply_advance_filter(
                advance_filters,
                pipeline,
                student_primary="student_primary",
                courses="course_details",
                student_secondary="student_education_details",
                lead_followup="lead_details",
                communication_log="communication_log",
                queries="queries",
            )
        if payload.get("counselor_id"):
            pipeline[0].get("$match", {}).update(
                {
                    "allocate_to_counselor.counselor_id": {
                        "$in": [ObjectId(x) for x in
                                payload.get("counselor_id")]
                    }
                }
            )
        if (
                payload.get("application_stage_name") is not None
                and payload.get("application_stage_name") != ""
        ):
            pipeline[0].get("$match", {}).update(
                {
                    "declaration": (
                        False
                        if payload.get(
                            "application_stage_name").lower() == "incomplete"
                        else True
                    )
                }
            )
        if advance_filters:
            if skip is not None and limit is not None:
                pipeline = utility_obj.get_count_aggregation(
                    pipeline, skip=skip, limit=limit
                )
        if skip is None or limit is None:
            pipeline = utility_obj.get_count_aggregation(pipeline)
        return pipeline

    async def get_applications_based_on_date_range(
            self, start_date: datetime, end_date: datetime
    ) -> list:
        """
        Get the applications based on date range.

        Params:
            start_date (datetime): Start date which
                useful for filter data.
            end_date (datetime): End date which
                useful for filter data.

        Returns:
            list: A list which contains application unique ids which can be
                useful for further operation.
        """
        pipeline = [
            {"$match": {
                "enquiry_date": {"$gte": start_date, "$lte": end_date}}},
            {
                "$group": {
                    "_id": "",
                    "applications": {"$addToSet": "$_id"},
                }
            },
        ]
        application_ids = []
        async for doc in DatabaseConfiguration(
                season=None
        ).studentApplicationForms.aggregate(pipeline):
            application_ids = doc["applications"]
        return application_ids
