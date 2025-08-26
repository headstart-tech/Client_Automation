"""
This file contains class and functions related to interview list data.
"""
from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import OperationFailure
from app.core.log_config import get_logger
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.helpers.advance_filter_configuration import AdvanceFilterHelper
from app.helpers.student_curd.student_application_configuration import (
    StudentApplicationHelper)

logger = get_logger(name=__name__)


class InterviewListAggregation:
    """
    Contains functions related to get interview list data.
    """

    SORT_FIELDS = {
        "exam_name_sort": "student_secondary_details.education_details."
                          "inter_school_details.appeared_for_jee",
        "twelve_marks_sort": "student_secondary_details.education_details."
                             "inter_school_details.obtained_cgpa",
        "ug_marks_sort": "student_secondary_details.education_details."
                         "graduation_details.aggregate_mark",
        "interview_marks_sort": "interview_marks"
    }

    LIMIT = "$limit"
    SORT = "$sort"
    UNWIND = "$unwind"
    PROJECT = "$project"
    MATCH = "$match"
    LOOKUP = "$lookup"
    EXPRESSION = "$expr"
    IF_NULL = "$ifNull"
    TO_STRING = "$toString"

    async def paginated_data(
            self, page_num: int | None, page_size: int | None) -> dict:
        """
        Get facet stage which useful for data with/without pagination.

        Params:
            page_num (int | None): Either None or page number where you want
                to data. e.g., 1
            page_size (int | none): Either None or page size, useful for show
                data on page_num. e.g., 25.
                If we give page_num=1 and page_size=25 i.e., we want 25
                    records on page 1.

        Returns:
            facet_stage (dict): A dictionary which useful for get data
                with/without pagination.
        """
        final_data = []
        if page_num and page_size:
            skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                                  page_size)
            final_data.extend(
                [{"$skip": skip}, {self.LIMIT: limit}])
        facet_stage = {
            "$facet": {
                "applicants_data": final_data,
                "total_data": [{"$count": "count"}]
            }
        }
        return facet_stage

    async def unwind_stage(self, path: str = "$student_primary_details",
                           preserve_null: bool = False) -> dict:
        """
        Get unwind stage which will be useful in aggregation.

        Params:
            path (list): Default value: "$student_primary_details".
                A list element which need to unwind in aggregation.
            preserve_null (bool): Useful for get empty array when data not
                get in lookup stage.

        Returns:
            unwind_stage (dict): A dictionary which contains unwind stage
                info.
        """
        try:
            unwind_stage = {
                self.UNWIND: {
                    "path": path
                }
            }
            if preserve_null:
                unwind_stage.get(self.UNWIND, {}).update(
                    {"preserveNullAndEmptyArrays": True})
            return unwind_stage
        except OperationFailure as error:
            logger.error(f"Pymongo operation failed. Error - {error}")
            raise HTTPException(status_code=500,
                                detail=f"Pymongo operation failed. Error - {error}")
        except Exception as e:
            logger.error(f"Internal server error. Error - {e}")
            raise HTTPException(status_code=500,
                                detail=f"Internal server error. Error - {e}")

    async def project_stage_for_application_data(
            self, is_selected_applicants: bool = False,
            is_course: bool = False) -> dict:
        """
        Get project stage which useful for get required application data
         in the aggregation pipeline.

         Params:
            is_selected_applicants (bool): Default value: False.
                Value will be True when fetching interview list selected
                applicants' data.
            is_course (bool): Default value: False.
                Value will be True when want fields course_id and spec_name1
                in the project stage of application.

        Returns:
             project_stage (dict): A dictionary which useful in aggregation
                for get required applications fields.
        """
        project_stage = {
            self.PROJECT: {
                "_id": {self.TO_STRING: "$_id"},
                "custom_application_id": 1,
                "student_id": 1
            }
        }
        if is_selected_applicants:
            project_stage.get(self.PROJECT, {}).update({
                "interview_score": 1, "interview_list_id":
                    {self.TO_STRING: "$interview_list_data.interview_list_id"},
                "interview_list_name":
                    "$interview_list_data.interview_list_name"})

        if is_course:
            project_stage.get(self.PROJECT, {}).update({"course_id": 1,
                                                        "spec_name1": 1})
        return project_stage

    async def project_stage_for_student_data(self, email=False):
        """
        Return project stage which useful for get required student data
         in the aggregation pipeline.
        """
        project_stage = {
            self.PROJECT: {
                "_id": 0,
                "source": 1,
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
                }
            }
        }
        if email:
            project_stage.get(self.PROJECT, {}).update(
                {"user_name": 1, "mobile_number":
                    "$basic_details.mobile_number"})
        return project_stage

    async def sort_data_by_condition(self, pipeline: list, payload):
        """
        Sort data by condition in a pipeline.

        Params:
            pipeline (list): A pipeline list which need to extend for add
                sort stage.
            payload (dict): Useful for sort data and add sort stage in a
                pipeline.

        Returns:
            pipeline (list): An extended pipeline.
        """
        for sort_field, sort_key in self.SORT_FIELDS.items():
            sort_value = payload.get(sort_field)
            if sort_value is not None:
                order_decide = 1 if sort_value else -1
                pipeline.append({self.SORT: {sort_key: order_decide}})
        return pipeline

    async def extend_pipeline_based_on_source_name(self, pipeline: list,
                                                   source_names: list) -> list:
        """
        Extend original aggregation pipeline based on source name.

        Params:
            pipeline (list): Aggregation pipeline which want to extend.
            sources_names (list): A list which source names. Useful for filter
             data based on source names.

         Returns:
             list: Updated aggregation pipeline which useful for
             further operations.
        """
        sources = []
        for x in source_names:
            sources.append(x.lower())
        pipeline[4].get(
            "$lookup", {}).get("pipeline", [{}])[0].get(
            "$match", {}).update({"source.primary_source.utm_source": {
            "$in": sources}})
        return pipeline

    async def get_basic_and_application_filter(
            self, payload: dict, specialization_name: str, filters: dict) \
            -> tuple:
        """
        Get basic and application filters dictionaries with
            total applicants count program-wise.

        Params:
            payload (dict): A dictionary which contains
                    filterable fields and their values. Contains course based
                    and other filters.
            specialization_name: Name of specialization. Useful for get data
                based on specialization.
            filters (dict): A dictionary which contains
                    filterable fields and their values. Does not contain course
                    based filters.

        Returns:
            tuple: A tuple which contains basic and application filter with
            total applicants count program-wise.
        """
        course_name = payload.get("course_name")
        basic_filter = {
            "course_name": course_name
        }

        application_filter = {
            self.EXPRESSION: {
                "$eq": ["$$course_id", "$course_id"]
            }
        }
        if (selection_procedure := await DatabaseConfiguration().
                selection_procedure_collection.find_one(
            {"course_name": course_name,
             "specialization_name": specialization_name})) is None:
            selection_procedure = {"gd_parameters_weightage": True,
                                   "pi_parameters_weightage": True}
        gd_parameters = selection_procedure.get("gd_parameters_weightage")
        pi_parameters = selection_procedure.get("pi_parameters_"
                                                "weightage")
        last_action = "pi" if gd_parameters and pi_parameters else "gd" if \
            gd_parameters else "pi"
        application_filter.update({"meetingDetails.status":
                                       {"$ne": "Scheduled"},
                                   f"{last_action}_status.status":
                                       {"$ne": "Done"}
                                   })
        if (course := await DatabaseConfiguration().course_collection.find_one(
                basic_filter)) is None:
            course = {}
        if specialization_name not in [None, ""]:
            basic_filter.update({"course_specialization.spec_name":
                                     specialization_name})
            application_filter.update({"spec_name1": specialization_name})
        preference = payload.get("preference", [])
        if preference:
            preference_filter = (
                StudentApplicationHelper().filter_by_preference(
                preference, course.get("_id"), specialization_name))
            if preference_filter and isinstance(preference_filter, dict):
                application_filter.update(preference_filter)
        application_stage = filters.get("application_stage_name")
        remove_application_ids = filters.get("remove_application_ids")
        if remove_application_ids:
            remove_application_ids = [ObjectId(app_id)
                                      for app_id in remove_application_ids
                                      if await utility_obj.is_length_valid(
                    app_id, "Application id")]
            application_filter.update({
                "_id": {"$nin": remove_application_ids}
            })
        if application_stage not in [None, ""]:
            application_stage = False \
                if application_stage == "incomplete" else True
            application_filter.update({
                "declaration": application_stage
            })
        total_program_applicants = await DatabaseConfiguration().studentApplicationForms. \
            count_documents({"course_id": course.get("_id"),
                             "spec_name1": specialization_name})
        return basic_filter, application_filter, total_program_applicants

    async def get_student_filter(self, filters: dict) -> dict:
        """
        Get student filter, useful for get data based on student data.

        Params:
            filters (dict): A dictionary which contains
                    filterable fields and their values. Does not contain course
                    based filters.

        Returns:
              dict: A dictionary which contains student filter which useful
              for get data based on student filter.
        """
        student_filter = {
            self.EXPRESSION: {
                "$eq": ["$$student_id", "$_id"]
            }
        }
        categories = filters.get("category", [])
        nationalities = filters.get("nationality", [])
        state_codes = filters.get("state_code", [])
        city_names = filters.get("city_name", [])
        if categories:
            student_filter.update(
                {"basic_details.category": categories}
            )
        if nationalities:
            student_filter.update(
                {"basic_details.nationality": nationalities}
            )
        if state_codes:
            student_filter.update(
                {"address_details.communication_address.state.state_code":
                    {
                        "$in": [x.upper() for x in
                                state_codes]
                    }
                }
            )
        if city_names:
            student_filter.update(
                {"address_details.communication_address.city.city_name":
                    {
                        "$in": [x.title() for x in
                                city_names]
                    }
                }
            )
        return student_filter

    async def get_education_filter(self, filters: dict) -> dict:
        """
        Get education filter, useful for get data based on education data.

        Params:
            filters (dict): A dictionary which contains
                    filterable fields and their values. Does not contain course
                    based filters.

        Returns:
            dict: A dictionary which contains education filter, useful for
            get data based on education filter.
        """
        education_filter = {
            self.EXPRESSION: {
                "$eq": ["$$student_id", "$student_id"]
            }
        }
        twelve_marks = filters.get("twelve_marks", [])
        twelve_board_names = filters.get("twelve_board", [])
        ug_marks = filters.get("ug_marks", [])
        if twelve_marks:
            twelve_details = [
                {"education_details.inter_school_details.obtained_cgpa":
                     {"$gte": float(element.split('-')[0]),
                      "$lt": float(element.split('-')[-1])}}
                for element in twelve_marks if '-' in element]
            education_filter.update({"$or": twelve_details})
        if ug_marks:
            ug_details = [
                {"education_details.graduation_details.aggregate_mark":
                     {"$gte": float(element.split('-')[0]),
                      "$lt": float(element.split('-')[-1])}}
                for element in ug_marks if '-' in element]
            education_filter.update({"$or": ug_details})
        if twelve_board_names:
            education_filter.update({
                "education_details.inter_school_details.board":
                    {"$in": twelve_board_names}})
        return education_filter

    async def get_interview_list_applications_data_based_on_program(
            self, page_num, page_size, payload, add_applications=False) -> \
            tuple | list:
        """
        Get interview list applications data based on program using
        aggregation.

        Params:
            - page_num (int): Enter page number where you want to interview list
                applicants data. For example, 1
            - page_size (int): Enter page size means how many data you want to
                show on page_num. For example, 25
            - payload (dict): A dictionary which contains
                filterable fields and their values

        Returns:
            tuple: A tuple contains interview list applications data along
            with total count.
        """
        total_data, applications_data = 0, []
        specialization_name = payload.get("specialization_name")
        filters = payload.get("filters", {})
        if filters is None:
            filters = {}
        source_names = filters.get("source_name")
        pick_top = payload.get("pick_top")

        basic_filter, application_filter, total_program_applicants = await \
            self.get_basic_and_application_filter(payload, specialization_name,
                                                  filters)
        student_filter = await self.get_student_filter(filters)
        education_filter = await self.get_education_filter(filters)
        student_project_stage = await self.project_stage_for_student_data()
        application_project_stage = await self. \
            project_stage_for_application_data()
        application_unwind = await self.unwind_stage(
            path="$student_applications_data")
        student_unwind = await self.unwind_stage()
        student_secondary_unwind = await self.unwind_stage(
            path="$student_secondary_details", preserve_null=True)
        pipeline = [
            {
                self.MATCH: basic_filter
            },
            {
                self.PROJECT: {
                    "_id": 1
                }
            },
            {
                self.LOOKUP: {
                    "from": "studentApplicationForms",
                    "let": {"course_id": "$_id"},
                    "pipeline": [
                        {
                            self.MATCH: application_filter
                        },
                        {self.SORT: {"enquiry_date": -1}},
                        application_project_stage
                    ],
                    "as": "student_applications_data"
                }
            },
            application_unwind,
            {
                self.LOOKUP: {
                    "from": "studentsPrimaryDetails",
                    "let": {
                        "student_id":
                            "$student_applications_data.student_id"},
                    "pipeline": [
                        {
                            self.MATCH: student_filter
                        },
                        student_project_stage
                    ],
                    "as": "student_primary_details"
                }
            },
            student_unwind,
            {
                self.LOOKUP: {
                    "from": "studentSecondaryDetails",
                    "let": {
                        "student_id":
                            "$student_applications_data.student_id"},
                    "pipeline": [
                        {
                            self.MATCH: education_filter
                        },
                        {
                            self.PROJECT: {
                                "_id": 0,
                                "pg_marks": None,
                                "education_details": 1,
                                "ug_marks":
                                    "$education_details"
                                    ".graduation_details.aggregate_mark",
                                "entrance_exam": {
                                    "$cond": {
                                        "if": {"$eq": [
                                            "$education_details"
                                            ".inter_school_details"
                                            ".appeared_for_jee",
                                            True]},
                                        "then": "JEE",
                                        "else": None
                                    }
                                },
                                "entrance_exam_marks": None
                            }
                        }
                    ],
                    "as": "student_secondary_details"
                }
            },
            student_secondary_unwind]
        advance_filters = payload.get("advance_filters", [])

        if advance_filters:
            lead_followup_unwind = await self.unwind_stage(
                path="$lead_details", preserve_null=True)
            queries_unwind = await self.unwind_stage(
                path="$queries", preserve_null=True)
            communication_log_unwind = await self.unwind_stage(
                path="$communication_log", preserve_null=True)
            pipeline.extend([
                {
                    "$lookup": {
                        "from": "leadsFollowUp",
                        "let": {
                            "lead_id": "$student_applications_data.student_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {"$eq": ["$$lead_id",
                                                      "$student_id"]}
                                }
                            },
                            {"$project": {"_id": 0, "lead_stage": 1,
                                          "lead_stage_label": 1}},
                        ],
                        "as": "lead_details",
                    }
                },
                lead_followup_unwind,
                {
                    "$lookup": {
                        "from": "queries",
                        "localField": "student_applications_data.student_id",
                        "foreignField": "student_id",
                        "as": "queries"
                    }
                },
                queries_unwind,
                {
                    "$lookup": {
                        "from": "communicationLog",
                        "localField": "student_applications_data.student_id",
                        "foreignField": "student_id",
                        "as": "communication_log"
                    }
                },
                communication_log_unwind
            ])
            pipeline = await AdvanceFilterHelper().apply_advance_filter(
                advance_filters, pipeline,
                student_primary="student_primary_details",
                student_secondary="student_secondary_details",
                lead_followup="lead_details",
                communication_log="communication_log", queries="queries")
        pipeline = await self.sort_data_by_condition(pipeline, filters)

        if source_names:
            pipeline = await self.extend_pipeline_based_on_source_name(
                pipeline, source_names)

        facet_stage = await self.paginated_data(page_num, page_size)

        if pick_top:
            facet_stage.get("$facet").get("applicants_data", []).insert(
                0, {self.LIMIT: pick_top})

        pipeline.extend([{
            self.PROJECT: {
                "_id": 0,
                "student_name": "$student_primary_details.student_name",
                "student_id": {
                    self.TO_STRING:
                        "$student_applications_data.student_id"},
                "application_id": "$student_applications_data._id",
                "custom_application_id":
                    "$student_applications_data.custom_application_id",
                "pg_marks": "$student_secondary_details.pg_marks",
                "ug_marks": "$student_secondary_details.ug_marks",
                "entrance_exam":
                    "$student_secondary_details.entrance_exam",
                "entrance_exam_marks":
                    "$student_secondary_details.entrance_exam_marks"
            }
        },
            facet_stage])
        result = DatabaseConfiguration().course_collection.aggregate(pipeline)
        async for documents in result:
            if add_applications:
                applications_ids = [ObjectId(document.get("application_id"))
                                    for document in documents.get(
                        "applicants_data", [])]
                return applications_ids
            try:
                total_data = documents.get("total_data")[0].get("count")
            except IndexError:
                total_data = 0
            applications_data = documents.get("applicants_data")
        return total_data, applications_data, total_program_applicants

    async def interview_list_selected_applicants_data(
            self, page_num: int | None = None, page_size: int | None = None,
            payload: dict | None = None, get_applicant_ids: bool = False,
            application_ids: None | list = None) -> tuple:
        """
        Get interview list selected applicants data based on interview list id.

        Params:
            page_num (int | None): Either None or page number where you want
                to interview list selected applicants. e.g., 1
            page_size (int): Either None or page size means how many data you
                want to show on page_num. e.g., 25
            payload (dict): A dictionary which contains
                filterable fields with their values.
            application_ids (None | list): Either None or a list which contains
                application ids.

        Returns:
            tuple: A tuple contains interview list selected applicants` data.
        """
        interview_list_id = payload.get("interview_list_id")
        await utility_obj.is_length_valid(
            interview_list_id, name="Interview list id")
        student_project_stage = await self.project_stage_for_student_data()
        application_project_stage = await self. \
            project_stage_for_application_data(is_selected_applicants=True)
        student_unwind = await self.unwind_stage()
        student_secondary_unwind = await self.unwind_stage(
            path="$student_secondary_details", preserve_null=True
        )
        education_filter = await self.get_education_filter(payload)
        interview_marks = payload.get("interview_marks", [])
        basic_filter = {"interview_list_data.interview_list_id":
                            ObjectId(interview_list_id),
                        "approval_status": "Selected"}
        if interview_marks:
            twelve_details = [
                {"interview_score":
                     {"$gte": float(element.split('-')[0]),
                      "$lt": float(element.split('-')[-1])}}
                for element in interview_marks if '-' in element]
            basic_filter.update({"$or": twelve_details})
        if get_applicant_ids:
            basic_filter.update({"_id": {"$in": application_ids}})
        pipeline = [
            {self.MATCH: basic_filter},
            {self.SORT: {"enquiry_date": -1}},
            application_project_stage,
            {
                self.LOOKUP: {
                    "from": "studentsPrimaryDetails",
                    "let": {
                        "student_id": "$student_id"},
                    "pipeline": [
                        {
                            self.MATCH: {
                                self.EXPRESSION: {
                                    "$eq": ["$$student_id", "$_id"]
                                }
                            }
                        },
                        student_project_stage
                    ],
                    "as": "student_primary_details"
                }
            },
            student_unwind,
            {
                self.LOOKUP: {
                    "from": "studentSecondaryDetails",
                    "let": {
                        "student_id": "$student_id"},
                    "pipeline": [
                        {
                            self.MATCH: education_filter
                        },
                        {
                            self.PROJECT: {
                                "_id": 0,
                                "twelve_marks": "$education_details"
                                                ".inter_school_details"
                                                ".obtained_cgpa",
                                "ug_marks": "$education_details"
                                            ".graduation_details"
                                            ".obtained_cgpa",
                                "education_details": 1
                            }
                        }
                    ],
                    "as": "student_secondary_details"
                }
            },
            student_secondary_unwind
        ]

        pipeline = await self.sort_data_by_condition(pipeline, payload)
        if get_applicant_ids:
            pipeline.append({
                "$group": {
                    "_id": "",
                    "application_ids": {
                        "$push": "$_id"
                    }
                }
            })
            result = DatabaseConfiguration().studentApplicationForms.aggregate(
                pipeline)
            application_ids = []
            async for document in result:
                _ids = document.get("application_ids", [])
                if document and _ids:
                    application_ids = document.get("application_ids", [])
            return application_ids
        facet_stage = await self.paginated_data(page_num, page_size)
        pipeline.extend([{
            self.PROJECT: {
                "_id": 0,
                "student_name": "$student_primary_details.student_name"
                , "student_id": {
                    self.TO_STRING: "$student_id"},
                "application_id": "$_id",
                "custom_application_id": "$custom_application_id",
                "twelve_marks": {self.IF_NULL: ["$student_secondary_details"
                                                ".twelve_marks", "NA"]},
                "ug_marks": {
                    self.IF_NULL: ["$student_secondary_details.ug_marks",
                                   "NA"]},
                "interview_marks": {self.IF_NULL: ["$interview_score",
                                                   "NA"]}
            }
        },
            facet_stage])

        result = DatabaseConfiguration().studentApplicationForms.aggregate(
            pipeline)
        total_data, applications_data = 0, []
        async for documents in result:
            try:
                total_data = documents.get("total_data")[0].get("count")
            except IndexError:
                total_data = 0
            applications_data = documents.get("applicants_data")
        return total_data, applications_data

    async def lookup_stage_for_student_data(self, email=False):
        student_project_stage = await self.project_stage_for_student_data(
            email)
        return {
            self.LOOKUP: {
                "from": "studentsPrimaryDetails",
                "let": {
                    "student_id": "$student_id"},
                "pipeline": [
                    {
                        self.MATCH: {
                            self.EXPRESSION: {
                                "$eq": ["$$student_id", "$_id"]
                            }
                        }
                    },
                    student_project_stage
                ],
                "as": "student_primary_details"
            }
        }

    async def approval_pending_applicants_data(
            self, page_num, page_size) -> tuple:
        """
        Get approval pending applicants' data with/without pagination.

        Params:
            page_num (int): Page number where you want to show approval
                pending applicants. e.g., 1
            page_size (int): Page size means records want to
                show on page_num. e.g., 25

        Returns:
            tuple: A tuple contains approval pending applicants` data.
        """
        lookup_stage_for_student = await self.lookup_stage_for_student_data()
        application_project_stage = await self. \
            project_stage_for_application_data(is_selected_applicants=True,
                                               is_course=True)
        student_unwind = await self.unwind_stage()
        course_unwind = await self.unwind_stage(path="$course_data",
                                                preserve_null=True)
        student_secondary_unwind = await self.unwind_stage(
            path="$student_secondary_details", preserve_null=True
        )
        pipeline = [
            {self.MATCH: {"approval_status": "Under Review"}},
            {self.SORT: {"enquiry_date": -1}},
            application_project_stage,
            lookup_stage_for_student,
            student_unwind,
            {
                self.LOOKUP: {
                    "from": "studentSecondaryDetails",
                    "let": {
                        "student_id": "$student_id"},
                    "pipeline": [
                        {
                            self.MATCH: {
                                self.EXPRESSION: {
                                    "$eq": ["$$student_id", "$student_id"]
                                }
                            }
                        },
                        {
                            self.PROJECT: {
                                "_id": 0,
                                "tenth_marks":
                                    "$education_details.tenth_school_details."
                                    "obtained_cgpa",
                                "twelve_marks":
                                    "$education_details.inter_school_details"
                                    ".obtained_cgpa",
                                "ug_marks":
                                    "$education_details.graduation_details"
                                    ".aggregate_mark"
                            }
                        }
                    ],
                    "as": "student_secondary_details"
                }
            },
            student_secondary_unwind,
            {
                self.LOOKUP: {
                    "from": "courses",
                    "let": {"course_id": "$course_id"},
                    "pipeline": [
                        {
                            self.MATCH: {
                                self.EXPRESSION: {
                                    "$eq": ["$$course_id", "$_id"]
                                }
                            }
                        },
                        {
                            self.PROJECT: {
                                "course_name": 1,
                            }
                        }
                    ],
                    "as": "course_data"
                }
            },
            course_unwind,
        ]

        facet_stage = await self.paginated_data(page_num, page_size)
        pipeline.extend([{
            self.PROJECT: {
                "_id": 0,
                "student_name": "$student_primary_details.student_name"
                , "student_id": {self.TO_STRING: "$student_id"},
                "application_id": "$_id",
                "custom_application_id": "$custom_application_id",
                "course_name": {
                    self.IF_NULL: ["$course_data.course_name", "NA"]},
                "specialization_name": "$spec_name1",
                "tenth_score": {
                    self.IF_NULL: ["$student_secondary_details.tenth_marks",
                                   "NA"]},
                "twelve_marks": {self.IF_NULL: ["$student_secondary_details"
                                                ".twelve_marks", "NA"]},
                "ug_marks": {
                    self.IF_NULL: ["$student_secondary_details.ug_marks",
                                   "NA"]},
                "interview_marks": {self.IF_NULL: ["$interview_score",
                                                   "NA"]},
                "interview_list_id": {self.IF_NULL: ["$interview_list_id",
                                                     "NA"]},
                "interview_list_name": {self.IF_NULL: ["$interview_list_name",
                                                       "NA"]}
            }
        },
            facet_stage])

        result = DatabaseConfiguration().studentApplicationForms.aggregate(
            pipeline)
        total_data, applications_data = 0, []
        async for documents in result:
            try:
                total_data = documents.get("total_data")[0].get("count")
            except IndexError:
                total_data = 0
            applications_data = documents.get("applicants_data")
        return total_data, applications_data

    async def reviewed_applicants_data(
            self, page_num, page_size) -> tuple:
        """
        Get reviewed applicants' data with pagination.

        Params:
            page_num (int): Page number where you want to show reviewed
                applicants. e.g., 1
            page_size (int): Page size means records want to
                show on page_num. e.g., 25

        Returns:
            tuple: A tuple contains reviewed applicants` data along with
                total count.
        """
        lookup_stage_for_student = await self.lookup_stage_for_student_data(
            email=True)
        student_unwind = await self.unwind_stage()
        pipeline = [
            {self.MATCH: {"$and": [
                {"approval_status": {"$ne": "Under Review"}},
                {"approval_status": {"$exists": True}}]}},
            {self.SORT: {"enquiry_date": -1}},
            {
                self.PROJECT: {
                    "_id": {self.TO_STRING: "$_id"},
                    "custom_application_id": 1,
                    "student_id": 1,
                    "approval_status": 1,
                    "seat_blocked": 1,
                    "hold_date": {self.IF_NULL: ["$hold_date", "NA"]},
                    "selected_date": {self.IF_NULL: ["$selected_date", "NA"]},
                    "rejected_date": {self.IF_NULL: ["$rejected_date", "NA"]},
                    "shortlisted_date": {self.IF_NULL: ["$shortlisted_date",
                                                        "NA"]},

                }
            },
            lookup_stage_for_student,
            student_unwind
        ]

        facet_stage = await self.paginated_data(page_num, page_size)
        pipeline.extend([{
            self.PROJECT: {
                "_id": 0,
                "student_name": "$student_primary_details.student_name"
                , "student_id": {self.TO_STRING: "$student_id"},
                "student_email": "$student_primary_details.user_name",
                "student_mobile_number": "$student_primary_details.mobile_number",
                "application_id": "$_id",
                "custom_application_id": "$custom_application_id",
                "approval_status": "$approval_status",
                "seat_blocked": {self.IF_NULL: ["$seat_blocked", "NA"]},
                "action_date": {
                    "$switch": {
                        "branches": [
                            {
                                "case": {"$eq": ["$approval_status",
                                                 "Selected"]},
                                "then": {"$dateToString":
                                             {"format": "%d-%m-%Y", "date":
                                                 "$selected_date",
                                              "timezone": "Asia/Kolkata"}}
                            },
                            {
                                "case": {"$eq": ["$approval_status",
                                                 "Rejected"]},
                                "then": {"$dateToString":
                                             {"format": "%d-%m-%Y", "date":
                                                 "$rejected_date",
                                              "timezone": "Asia/Kolkata"}}
                            },
                            {
                                "case": {"$eq": ["$approval_status", "Hold"]},
                                "then": {"$dateToString":
                                             {"format": "%d-%m-%Y", "date":
                                                 "$hold_date",
                                              "timezone": "Asia/Kolkata"}}
                            },
                            {
                                "case": {"$eq": ["$approval_status",
                                                 "Shortlisted"]},
                                "then": {"$dateToString":
                                             {"format": "%d-%m-%Y", "date":
                                                 "$shortlisted_date",
                                              "timezone": "Asia/Kolkata"}}
                            }
                        ],
                        "default": "NA"
                    }
                }
            }
        },
            facet_stage])

        result = DatabaseConfiguration().studentApplicationForms.aggregate(
            pipeline)
        total_data, applications_data = 0, []
        async for documents in result:
            try:
                total_data = documents.get("total_data")[0].get("count")
            except IndexError:
                total_data = 0
            applications_data = documents.get("applicants_data")
        return total_data, applications_data
