"""
This file contain class and methods related to paid application data.
"""

from bson.objectid import ObjectId

from app.core.common_utils import Check_payload
from app.core.utils import utility_obj
from app.database.aggregation.get_all_applications import Application
from app.database.aggregation.student import Student
from app.database.configuration import DatabaseConfiguration
from app.helpers.advance_filter_configuration import AdvanceFilterHelper


class PaidApplication:
    """
    Contain functions related to paid application activities.
    """

    async def all_paid_applications(
        self,
        payload,
        page_num,
        page_size,
        date_range,
        season,
        college_id,
        counselor_id,
        twelve_score_sort=None,
    ):
        """
        This function return all paid applications base on filter and
        date range.
        """
        application_obj = Application()
        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
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
        start_date, end_date = await self.get_start_end_dates(date_range)
        if season == "":
            season = None
        advance_filters = payload.get("advance_filters", [])
        pipeline = await application_obj.initialize_pipeline_all_applications(
            college_id=college_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
            counselor_id=counselor_id,
            is_head_counselor=None,
            collection_index=collection_index,
            filter_index=filter_index,
            paid_filter=True,
            payload=payload,
            advance_filter=advance_filters
        )
        pipeline = await application_obj.primary_lookup_pipeline(
            pipeline=pipeline,
            payload=payload,
            skip=skip,
            limit=limit,
            filter_index=filter_index,
            collection_index=collection_index,
        )
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
        if (
            payload.get("lead_stage", {}).get("lead_name", [])
            or payload.get("lead_stage", {}).get("lead_b") is True
        ) and not advance_filters:
            pipeline = await application_obj.apply_lookup_on_leadfollowup(
                pipeline,
                payload=payload,
                collection_index=collection_index,
                filter_index=filter_index,
                skip=skip,
                limit=limit,
            )
        pipeline = await application_obj.apply_lookup_on_student_secondary(
            pipeline=pipeline
        )
        pipeline = self.apply_twelve_board_form_filling_stage_twelve_marks(
            pipeline=pipeline,
            payload=payload,
            skip=skip,
            limit=limit,
            collection_index=collection_index,
            filter_index=filter_index,
        )
        pipeline = await application_obj.course_pipeline(pipeline)
        if advance_filters:
            pipeline = await application_obj.apply_lookup_on_leadfollowup(
                pipeline=pipeline, payload=payload
            )
            pipeline = await application_obj.apply_lookup_on_communication_log(
                pipeline=pipeline
            )
            check = str(advance_filters)
            if "queries" in check:
                pipeline = await application_obj.apply_lookup_on_queries(pipeline)
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
        pipeline = self.apply_twelve_score_sort_and_application_filling_stage(
            twelve_score_sort=twelve_score_sort, pipeline=pipeline, payload=payload
        )
        pipeline = await application_obj.apply_course_filter(pipeline, payload)
        pipeline = application_obj.apply_payment_status_filter(
            pipeline, payload, start_date, end_date
        )

        pipeline = await Application().aggregation_pipeline(
            payload=payload,
            pipeline=pipeline,
            skip=skip,
            limit=limit,
            advance_filters=advance_filters,
        )
        if (
            (
                payload.get("course", {}).get("course_id") is not None
                and payload.get("course", {}).get("course_id") != ""
            )
            or (
                payload.get("course", {}).get("course_specialization") is not None
                and payload.get("course", {}).get("course_specialization") != ""
            )
            or (
                payload.get("state", {}).get("state_code") is not None
                and payload.get("state", {}).get("state_code") != ""
            )
            or (
                payload.get("city", {}).get("city_name") is not None
                and payload.get("city", {}).get("city_name") != ""
            )
            or (
                payload.get("application_stage", {}).get("application_stage_name")
                is not None
                and payload.get("application_stage", {}).get("application_stage_name")
                != ""
            )
            or (
                payload.get("lead_stage", {}).get("lead_name") is not None
                and payload.get("lead_stage", {}).get("lead_name") != ""
            )
            or (
                payload.get("lead_stage", {}).get("lead_name") is not None
                and payload.get("lead_stage", {}).get("lead_name") != ""
            )
            or (
                payload.get("source", {}).get("source_name") is not None
                and payload.get("source", {}).get("source_name") != ""
            )
            or (
                payload.get("lead_type", {}).get("lead_type_name") is not None
                and payload.get("lead_type", {}).get("lead_type_name") != ""
            )
            or (
                payload.get("counselor", {}).get("counselor_id") is not None
                and payload.get("counselor", {}).get("counselor_id") != ""
            )
            or counselor_id is not None
        ):
            pass
        return await self.process_aggregation_result(pipeline, payload, season)

    async def get_start_end_dates(self, date_range):
        """
        returns the start date and end date from given date range
        params:
         date_range: the date range filter
        """
        start_date, end_date = date_range.get("start_date"), date_range.get("end_date")
        if start_date and end_date:
            start_date, end_date = await utility_obj.date_change_format(
                start_date, end_date
            )
        return start_date, end_date

    async def initialize_pipeline(
        self,
        college_id,
        start_date,
        end_date,
        collection_index=None,
        filter_index=None,
    ):
        """
        Returns the initial pipeline
        Params:
          College_id (str): the unique id of college
          start_date (str) : the given start date filter
          end_date (str): the given end date filter
        """
        application_obj = Application()
        pipeline = [
            {
                "$match": {
                    "college_id": ObjectId(college_id),
                    "payment_info.status": "captured",
                }
            },
            {"$sort": {"enquiry_date": -1}},
        ]

        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "studentsPrimaryDetails",
                        "let": {"id": "$student_id"},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$_id", "$$id"]}}},
                        ],
                        "as": "student_primary",
                    }
                },
                {"$unwind": {"path": "$student_primary"}},
            ]
        )
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "courses",
                        "let": {"course_id": "$course_id"},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$_id", "$$course_id"]}}},
                            {"$project": {"_id": 0, "fees": 1, "course_name": 1}},
                        ],
                        "as": "course_details",
                    }
                },
                {"$unwind": {"path": "$course_details"}},
            ]
        )
        pipeline = await application_obj.apply_lookup_on_student_secondary(pipeline)
        if start_date and end_date:
            pipeline[0].get("$match", {}).update(
                {"payment_info.created_at": {"$gte": start_date, "$lte": end_date}}
            )
        return pipeline

    def apply_twelve_score_sort_and_application_filling_stage(
        self, twelve_score_sort, pipeline, payload
    ):
        """
        add twelve sorting and application filling stage to pipeline accordingly
        Params:
         twelve_score_sort (bool): True if need to sort False if no need
         pipeline (list): the pipeline to be changed
         payload(dict): Payload of API which has all filters
        """
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
        if payload.get("application_filling_stage"):
            pipeline[0].get("$match", {}).update(
                {"$or": payload.get("application_filling_stage", [])}
            )
        return pipeline

    def apply_twelve_board_form_filling_stage_twelve_marks(
        self,
        pipeline: list,
        payload: dict,
        skip=None,
        limit=None,
        collection_index=None,
        filter_index=None,
    ):
        """
        Update the pipeline for filters: twelve_board , form_filling_stage,
        twelve_marks.

        Params:
          pipeline (list): the pipeline which has to be update.
          Payload (dict): The dict that has all  filters.
        """
        if payload.get("twelve_board", {}).get("twelve_board_name"):
            pipeline.append(
                {
                    "$match": {
                        "student_education_details.education_details."
                        "inter_school_details.board": {
                            "$in": payload.get("twelve_board", {}).get(
                                "twelve_board_name"
                            )
                        }
                    }
                }
            )
        if payload.get("form_filling_stage", {}).get("form_filling_stage_name"):
            form_filling = []
            if "12th" in payload.get("form_filling_stage", {}).get(
                "form_filling_stage_name"
            ):
                form_filling.append(
                    {
                        "student_education_details.education_details."
                        "inter_school_details.is_pursuing": False
                    }
                )
            if "10th" in payload.get("form_filling_stage", {}).get(
                "form_filling_stage_name"
            ):
                form_filling.append(
                    {
                        "student_education_details.education_details."
                        "tenth_school_details": {"$exists": True}
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
                            "student_education_details.education_details."
                            "inter_school_details.marking_scheme": "Percentage"
                        },
                        {
                            "student_education_details.education_details."
                            "inter_school_details.obtained_cgpa": {
                                "$gte": float(element.split("-")[0]),
                                "$lt": float(element.split("-")[-1]),
                            }
                        },
                    ]
                }
                for element in payload.get("twelve_marks", {}).get("twelve_marks_name")
                if "-" in element
            ]
            twelve_details.extend(
                [
                    {
                        "student_education_details.education_details."
                        "inter_school_details.obtained_cgpa": element
                    }
                    for element in payload.get("twelve_marks", {}).get(
                        "twelve_marks_name"
                    )
                    if "-" not in element
                ]
            )
            pipeline.append({"$match": {"$or": twelve_details}})
        if collection_index:
            if filter_index is not None:
                if (
                    collection_index.get("studentSecondaryDetails", {}).get(
                        filter_index
                    )
                    == "studentSecondaryDetails"
                ):
                    pipeline = utility_obj.get_count_aggregation(
                        pipeline, skip=skip, limit=limit
                    )
        return pipeline

    async def process_aggregation_result(self, pipeline: list, payload: dict, season):
        """
        Process the aggregation pipeline and return the result
        Params:
         pipeline (list): the pipeline that is to be updated
        """
        result = DatabaseConfiguration(season=season).studentApplicationForms.aggregate(
            pipeline
        )
        data_list = []
        total_data = 0
        async for doc in result:
            try:
                total_data = doc.get("totalCount", 0)
            except IndexError:
                total_data = 0
            student_details = doc.get("student_primary", {})
            automation_names = doc.get("automation_details", {}).get(
                "automation_names", []
            )
            data = {
                "application_id": str(doc.get("_id")),
                "student_id": str(doc.get("student_id")),
                "student_name": utility_obj.name_can(
                    student_details.get("basic_details")
                ),
                "custom_application_id": doc.get("custom_application_id"),
                "tags": student_details.get("tags"),
                "course_name": (
                    f"{doc.get('course_details', {}).get('course_name')} "
                    f"in {doc.get('spec_name1')}"
                    if (doc.get("spec_name1") != "" and doc.get("spec_name1"))
                    else f"{doc.get('course_details').get('course_name')}"
                ),
                "student_email_id": student_details.get("basic_details", {}).get(
                    "email"
                ),
                "student_mobile_no": student_details.get("basic_details", {}).get(
                    "mobile_number"
                ),
                "automation": doc.get("automation_details", {}).get(
                        "automation", None
                    ),
                "automation_names": [item for sublist in automation_names if sublist for item in sublist] if automation_names else [],
                "verification": await Student().get_lead_verification_info(
                    {
                        "student_verify": student_details.get("is_verify"),
                        "student_mobile_verify": student_details.get(
                            "is_mobile_verify"
                        ),
                        "student_email_verify": student_details.get("is_email_verify"),
                        "declaration": doc.get("declaration"),
                        "dv_status": doc.get("dv_status"),
                    },
                    applications=True,
                ),
                "payment_status": doc.get("payment_info", {}).get("status"),
            }
            data = await Application().get_data_based_on_condition(payload, data, doc)
            data_list.append(data)
        return data_list, total_data
