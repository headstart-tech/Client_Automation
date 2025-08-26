"""
This file contain class and functions related to automation
"""

import datetime

import pandas as pd
from bson import ObjectId

from app.core.common_utils import Check_payload
from app.core.custom_error import DataNotFoundError
from app.core.utils import utility_obj
from app.database.aggregation.get_all_applications import Application
from app.database.aggregation.student import Student
from app.database.configuration import DatabaseConfiguration
from app.helpers.automation.segment_automation_data import data_segment_info


class AutomationHelper:
    """
    Contain functions related automation data
    """

    async def automation_beta_helper(self, data):
        """
        Get automation rule (beta) details
        """
        return {
            "automation_id": str(data.get("_id")),
            "automation_name": data.get("automation_name"),
            "automation_description": data.get("automation_description"),
            "module_name": data.get("module_name"),
            "script": {
                "action": data.get("script", {}).get("action"),
                "action_type": data.get("script", {}).get("action_type"),
                "condition_exec": data.get("script", {}).get("condition_exec"),
                "when_exec": data.get("script", {}).get("when_exec"),
                "instant_action": data.get("script", {}).get("instant_action"),
                "selected_template": str(
                    data.get("script", {}).get("selected_template")
                ),
                "email_subject": str(data.get("script", {}).get("email_subject")),
            },
            "enabled": data.get("enabled"),
            "is_published": data.get("is_published"),
            "created_on": utility_obj.get_local_time(data.get("created_on")),
            "created_by_id": str(data.get("created_by_id")),
            "created_by_name": data.get("created_by_name"),
            "updated_on": utility_obj.get_local_time(data.get("updated_on")),
            "updated_by": str(data.get("updated_by")),
            "updated_by_name": data.get("updated_by_name"),
        }

    async def automation_helper(self, data):
        """
        Get automation rule details
        """
        return {
            "automation_id": str(data.get("_id")),
            "automation_name": data.get("automation_name"),
            "automation_description": data.get("automation_description"),
            "module_name": data.get("module_name"),
            "script": {
                "action_type": data.get("script", {}).get("action_type"),
                "condition_exec": data.get("script", {}).get("condition_exec"),
                "when_exec": data.get("script", {}).get("when_exec"),
                "instant_action": data.get("script", {}).get("instant_action"),
                "selected_template_ids": [
                    str(item)
                    for item in data.get("script", {}).get("selected_template_id")
                ],
                "template_content": [
                    str(item) for item in data.get("script", {}).get("template_content")
                ],
                "email_subject": str(data.get("script", {}).get("email_subject")),
                "dlt_content_id": str(data.get("script", {}).get("dlt_content_id")),
            },
            "enabled": data.get("enabled"),
            "is_published": data.get("is_published"),
            "created_on": utility_obj.get_local_time(data.get("created_on")),
            "created_by_id": str(data.get("created_by_id")),
            "created_by_name": data.get("created_by_name"),
            "updated_on": utility_obj.get_local_time(data.get("updated_on")),
            "updated_by": str(data.get("updated_by")),
            "updated_by_name": data.get("updated_by_name"),
        }

    async def return_data_with_count(
        self,
        result,
        emails=False,
        numbers=False,
        call_segments=False,
        data_segments=None,
        data_segment_id=None,
    ):
        """
        Get data with count
        """
        total_data, data = 0, []
        async for documents in result:
            try:
                total_data = documents.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
            if emails and numbers:
                data = [
                    {
                        "application_id": None,
                        "student_id": None,
                        "student_name": doc.get("other_field", {}).get("full_name", ""),
                        "email_id": doc.get("mandatory_field", {}).get("email"),
                        "added_on": datetime.datetime.utcnow(),
                        "data_segment_id": (
                            ObjectId(data_segment_id)
                            if data_segment_id and len(data_segment_id) == 24
                            else None
                        ),
                        "mobile_number": doc.get("mandatory_field", {}).get(
                            "mobile_number"
                        ),
                    }
                    for doc in documents.get("paginated_results")
                ]
            elif (emails and call_segments is False) or emails:
                data = [
                    doc.get("mandatory_field", {}).get("email")
                    for doc in documents.get("paginated_results")
                ]
            elif numbers:
                data = [
                    doc.get("mandatory_field", {}).get("mobile_number")
                    for doc in documents.get("paginated_results")
                ]
            if data_segments is True and emails is False:
                data = []
                for doc in documents.get("paginated_results", []):
                    student_name = ""
                    if doc.get("other_field", {}).get("full_name"):
                        student_name = doc.get("other_field", {}).get("full_name")
                    elif doc.get("other_field", {}).get("first_name"):
                        student_name = utility_obj.name_can(doc.get("other_field", {}))
                    elif doc.get("other_field", {}).get("name"):
                        student_name = doc.get("other_field", {}).get("name")
                    course_name = (
                        f"{doc.get('other_field', {}).get('course')} in {doc.get('other_field', {}).get('main_specialization')}"
                        if doc.get("other_field", {}).get("main_specialization")
                        is not None
                        else doc.get("other_field", {}).get("course")
                    )
                    data_dict = {
                        "application_id": "",
                        "student_id": "",
                        "student_name": student_name,
                        "email": doc.get("mandatory_field", {}).get("email"),
                        "offline_data_id": str(doc.get("offline_data_id")),
                        "added_on": utility_obj.get_local_time(doc.get("created_at")),
                        "mobile_number": doc.get("mandatory_field", {}).get(
                            "mobile_number"
                        ),
                        "course_name": course_name,
                    }
                    for key, value in doc.get("other_field", {}).items():
                        data_dict.update({key: value})
                    data.append(data_dict)
        return total_data, data

    async def get_custom_added_data(
        self,
        payload,
        data_segment_id,
        segment,
        college_id,
        search=None,
        skip=None,
        limit=None,
    ):
        """
        Get the custom added data

        params:
            data_segment_id (str): Get the segment id

        return:
            return list of custom added data
        """
        if payload is None:
            payload = {}
        if data_segment_id is None:
            data_segment_id = segment.get("_id")
        if segment is None and data_segment_id is not None:
            segment = await DatabaseConfiguration().data_segment_collection.find_one(
                {"_id": ObjectId(data_segment_id)}
            )

        temp_pipeline = [
            {
                "$match": {
                    "data_segment_id": ObjectId(data_segment_id),
                    "custom_added": True,
                }
            },
            {
                "$group": {
                    "_id": "",
                    "application_id": {"$push": "$application_id"},
                    "student_id": {"$push": "$student_id"},
                }
            },
        ]
        result = (
            await DatabaseConfiguration()
            .data_segment_mapping_collection.aggregate(temp_pipeline)
            .to_list(None)
        )
        if segment.get("module_name", "").lower() == "application":
            if len(result) != 0:
                application_id = result[0].get("application_id")
                pipeline = await Application().all_applications(
                    payload=payload,
                    college_id=college_id,
                    applications=True,
                    page_num=skip + 1 if skip is not None else 1,
                    page_size=limit,
                    form_initiated=False,
                    application_ids=application_id,
                    call_segments=True,
                    data_segment=True,
                )
                pipeline = await Application().aggregation_pipeline(
                    payload=payload,
                    pipeline=pipeline,
                    skip=skip,
                    limit=limit,
                    advance_filters=payload.get("advance_filters"),
                    data_segment=True,
                )
                pipeline = await data_segment_info().application_segment_info(
                    pipeline,
                    search=search,
                    lead_type="application",
                    skip=skip,
                    limit=limit,
                )
                return (
                    await DatabaseConfiguration()
                    .studentApplicationForms.aggregate(pipeline)
                    .to_list(None)
                )
            else:
                return []
        if segment.get("module_name", "").lower() == "lead":
            if len(result) != 0:
                collection_index = {
                    "studentsPrimaryDetails": {0: "studentsPrimaryDetails"},
                    "studentApplicationForms": {1: "studentApplicationForms"},
                    "leadsFollowUp": {2: "leadsFollowUp"},
                    "studentSecondaryDetails": {3: "studentSecondaryDetails"},
                }
                filter_index = Check_payload(collection_index).get_meal(
                    payload=payload, applications=False
                )
                student_id = result[0].get("student_id")
                pipeline = await Student().pipeline_for_view_all_leads(
                    payload=payload,
                    student_ids=student_id,
                    data_segment=True,
                    skip=skip,
                    limit=limit,
                    collection_index=collection_index,
                    filter_index=filter_index,
                )
                pipeline = await data_segment_info().application_segment_info(
                    pipeline,
                    search=search,
                    lead_type="lead",
                )
                return (
                    await DatabaseConfiguration()
                    .studentsPrimaryDetails.aggregate(pipeline)
                    .to_list(None)
                )
            else:
                return []
        else:
            return []

    async def get_lead_details(
        self,
        segment=None,
        date_range=None,
        college_id=None,
        data_segments=False,
        emails=False,
        numbers=False,
        data_segment_id=None,
        skip=None,
        limit=None,
        search=None,
        call_segments=None,
        basic_filter=None,
        payload=None,
        student_ids=None,
        static=None,
    ):
        """
        Get count of data based on filters
        """
        payloads = payload
        if segment is None:
            segment = {}
        if date_range is None:
            date_range = {}
        payload = segment.get("filters", {})
        if payload is None:
            payload = {}
        payload["advance_filters"] = segment.get("advance_filters")
        pipeline = []
        if static is None:
            collection_index = {
                "studentsPrimaryDetails": {0: "studentsPrimaryDetails"},
                "studentApplicationForms": {1: "studentApplicationForms"},
                "leadsFollowUp": {2: "leadsFollowUp"},
                "studentSecondaryDetails": {3: "studentSecondaryDetails"},
            }
            filter_index = Check_payload(collection_index).get_meal(
                payload=payload, applications=False
            )
            if basic_filter:
                filter_index = collection_index = None
            pipeline = await Student().pipeline_for_view_all_leads(
                start_date=date_range.get("start_date"),
                end_date=date_range.get("end_date"),
                payload=payload,
                skip=skip,
                limit=None if basic_filter else limit,
                collection_index=collection_index,
                filter_index=filter_index,
                data_segment=True,
            )
        if call_segments:
            pipeline = await data_segment_info().application_segment_info(
                pipeline=pipeline,
                search=search,
                lead_type="lead",
                call_segments=call_segments,
                college_id=college_id,
                basic_filter=basic_filter,
                payload=payloads,
                student_ids=student_ids,
                static=static,
                skip=skip,
                limit=limit,
            )
        else:
            target_sequence = [
                {'$facet': {'pipelineResults': [], 'totalCount': [{'$count': 'value'}]}},
                {'$unwind': '$pipelineResults'},
                {'$unwind': '$totalCount'},
                {'$replaceRoot': {
                    'newRoot': {'$mergeObjects': ['$pipelineResults', {'totalCount': '$totalCount.value'}]}}}
            ]
            if pipeline[-len(target_sequence):] == target_sequence:
                del pipeline[-len(target_sequence):]
        results = (
            await DatabaseConfiguration()
            .studentsPrimaryDetails.aggregate(pipeline)
            .to_list(None)
        )
        if call_segments:
            if static is True:
                custom_data = []
            else:
                custom_data = await self.get_custom_added_data(
                    payload=payloads,
                    data_segment_id=data_segment_id,
                    segment=segment,
                    college_id=college_id,
                    search=search,
                    skip=skip,
                    limit=limit,
                )
            try:
                custom_count = custom_data[0].get("totalCount", 0)
            except IndexError:
                custom_count = 0
            except Exception:
                custom_count = 0
            try:
                total_count = results[0].get("totalCount", 0)
            except IndexError:
                total_count = 0
            student_data = results
            if limit is not None:
                if len(student_data) < limit:
                    temp = limit - len(student_data)
                    student_data = student_data + custom_data[:temp]
            else:
                student_data = student_data + custom_data
            total_count = total_count + custom_count
            if emails:
                student_data = [
                    doc.get("email")
                    for doc in student_data
                    if doc.get("email") is not None
                ]
            elif numbers:
                student_data = [
                    doc.get("mobile_number")
                    for doc in student_data
                    if doc.get("mobile_number") is not None
                ]
            return total_count, student_data
        elif emails and numbers:
            return [
                {
                    "application_id": [
                        ObjectId(dt.get("_id")) for dt in doc.get("applications", [])
                    ],
                    "student_id": ObjectId(doc.get("_id")),
                    "student_name": utility_obj.name_can(doc.get("basic_details", {})),
                    "email_id": doc.get("user_name"),
                    "added_on": datetime.datetime.utcnow(),
                    "data_segment_id": (
                        ObjectId(data_segment_id)
                        if data_segment_id and len(data_segment_id) == 24
                        else None
                    ),
                    "mobile_number": doc.get("basic_details", {}).get("mobile_number"),
                }
                for doc in results
            ]

    async def get_filtered_pipeline(self, pipeline, filters):
        """
        Get the pipeline for a given pipeline
        params:
            pipeline (list): Get the pipeline for a given pipeline
        """
        if filters is None:
            filters = {}
        basic_list = []
        if filters.get("state_code"):
            basic_list.append(
                {"other_field.state_code": {"$in": filters.get("state_code", [])}}
            )
        if filters.get("state", {}).get("state_code"):
            basic_list.append(
                {
                    "other_field.state_code": {
                        "$in": filters.get("state", {}).get("state_code", [])
                    }
                }
            )
        if filters.get("city_name"):
            basic_list.append(
                {"other_field.city": {"$in": filters.get("city_name", [])}}
            )
        if filters.get("city", {}).get("city_name"):
            basic_list.append(
                {
                    "other_field.city": {
                        "$in": filters.get("city", {}).get("city_name", [])
                    }
                }
            )
        if filters.get("source_name"):
            basic_list.append(
                {"other_field.utm_source": {"$in": filters.get("source_name", [])}}
            )
        if filters.get("source", {}).get("source_name"):
            basic_list.append(
                {
                    "other_field.utm_source": {
                        "$in": filters.get("source", {}).get("source_name", [])
                    }
                }
            )
        lead = filters.get("lead_name", [])
        if lead:
            lead_filter = []
            for lead_data in lead:
                if lead_data.get("lead"):
                    lead_filter.append(
                        {"other_field.lead_stage": {"$in": lead_data.get("lead", [])}}
                    )
                if lead_data.get("label"):
                    lead_filter.append(
                        {
                            "other_field.lead_stage_label": {
                                "$in": lead_data.get("label", [])
                            }
                        }
                    )
            if lead_filter:
                basic_list.append({"$or": lead_filter})
        if filters.get("lead_type_name") not in ["", None]:
            basic_list.append({"other_field.lead_type": filters.get("lead_type_name")})
        course = filters.get("course")
        if course:
            if course.get("course_name"):
                basic_list.append(
                    {"other_field.course": {"$in": course.get("course_name", [])}}
                )
            if course.get("course_specialization"):
                basic_list.append(
                    {
                        "other_field.main_specialization": {
                            "$in": course.get("course_specialization", [])
                        }
                    }
                )
        if filters.get("course", {}).get("course_id"):
            temp = [
                {
                    "$match": {
                        "_id": {
                            "$in": [
                                ObjectId(_id)
                                for _id in filters.get("course", {}).get(
                                    "course_id", []
                                )
                            ]
                        }
                    }
                }
            ]
            course_detail = (
                await DatabaseConfiguration()
                .course_collection.aggregate(temp)
                .to_list(None)
            )
            basic_list.append(
                {
                    "other_field.course": {
                        "$in": [course.get("course_name") for course in course_detail]
                    }
                }
            )
        if filters.get("course", {}).get("course_specialization"):
            basic_list.append(
                {
                    "other_field.main_specialization": {
                        "$in": filters.get("course", {}).get(
                            "course_specialization", []
                        )
                    }
                }
            )
        if filters.get("twelve_board"):
            basic_list.append({"other_field.twelve_board": filters.get("twelve_board")})
        if filters.get("twelve_marks"):
            basic_list.append({"other_field.twelve_marks": filters.get("twelve_marks")})
        if filters.get("city"):
            if type(filters.get("city")) == list:
                basic_list.append(
                    {"other_field.city": {"$in": filters.get("city", [])}}
                )
        if basic_list:
            pipeline.append({"$match": {"$and": basic_list}})
        if filters.get("date_range"):
            date_range = filters.get("date_range", {})
            if date_range.get("start_date") and date_range.get("end_date"):
                start_date, end_date = await utility_obj.date_change_format(
                    start_date=date_range("start_date"), end_date=date_range("end_date")
                )
                pipeline[0].get("$match", {}).update(
                    {"created_at": {"$gte": start_date, "$lte": end_date}}
                )
            if date_range.get("start_date") and date_range.get("end_date") is None:
                start_date = utility_obj.single_date_format(
                    date_range.get("start_date")
                )
                pipeline[0].get("$match", {}).update(
                    {"created_at": {"$gte": start_date}}
                )
        return pipeline

    async def get_raw_data_details(
        self,
        segment,
        date_range,
        college_id,
        data_segments=False,
        emails=False,
        numbers=False,
        data_segment_id=None,
        call_segments=False,
        skip=None,
        limit=None,
        payload=None,
        basic_filter=None,
        search=None,
    ):
        """
        Get raw data from raw collection
        """
        filters = segment.get("filters", {})
        if filters is None:
            filters = {}
        raw_data_id = []
        for seg_data in segment.get("raw_data_name", []):
            offline = await DatabaseConfiguration().offline_data.find_one(
                {"data_name": seg_data}
            )
            if not offline:
                raise DataNotFoundError(message="raw data not found")
            raw_data_id.append(ObjectId(offline.get("_id")))
        pipeline = [
            {"$match": {"offline_data_id": {"$in": raw_data_id}}},
            {
                "$project": {
                    "_id": 1,
                    "mandatory_field": 1,
                    "created_at": 1,
                    "other_field": 1,
                    "mobile_number": {
                        "$toString": {"$ifNull": ["$mandatory_field.mobile_number", ""]}
                    },
                }
            },
        ]
        pipeline = await self.get_filtered_pipeline(pipeline=pipeline, filters=filters)
        start_date, end_date = date_range.get("start_date"), date_range.get("end_date")
        if start_date not in ["", None] and end_date not in ["", None]:
            pipeline[0].get("$match", {}).update(
                {"created_at": {"$gte": start_date, "$lte": end_date}}
            )
        elif start_date not in ["", None] and end_date in [None, ""]:
            pipeline[0].get("$match", {}).update({"created_at": {"$gte": start_date}})
        if basic_filter is True:
            result = DatabaseConfiguration().raw_data.aggregate(pipeline)
            raw_id = [ObjectId(raw.get("_id")) async for raw in result]
            pipeline = [
                {"$match": {"_id": {"$in": raw_id}}},
                {
                    "$project": {
                        "_id": 1,
                        "mandatory_field": 1,
                        "created_at": 1,
                        "other_field": 1,
                        "mobile_number": {
                            "$toString": {
                                "$ifNull": ["$mandatory_field.mobile_number", ""]
                            }
                        },
                    }
                },
            ]
            pipeline = await self.get_filtered_pipeline(
                pipeline=pipeline, filters=payload
            )
        if search is not None:
            search_match = {
                "$match": {
                    "$or": [
                        {"other_field.full_name": {"$regex": search, "$options": "i"}},
                        {"other_field.name": {"$regex": search, "$options": "i"}},
                        {"other_field.first_name": {"$regex": search, "$options": "i"}},
                        {"mandatory_field.email": {"$regex": search, "$options": "i"}},
                        {"mobile_number": {"$regex": search, "$options": "i"}},
                    ]
                }
            }
            pipeline.append(search_match)
        paginated_results = []
        if skip is not None and limit is not None:
            paginated_results = [{"$skip": skip}, {"$limit": limit}]
        if emails or numbers:
            paginated_results = []
        pipeline.append(
            {
                "$facet": {
                    "paginated_results": paginated_results,
                    "totalCount": [{"$count": "count"}],
                }
            }
        )
        result = DatabaseConfiguration().raw_data.aggregate(pipeline)
        return await self.return_data_with_count(
            result,
            emails=emails,
            numbers=numbers,
            data_segments=data_segments,
            call_segments=call_segments,
            data_segment_id=data_segment_id,
        )

    async def get_application_details(
        self,
        segment=None,
        date_range=None,
        college_id=None,
        data_segments=False,
        emails=False,
        numbers=False,
        data_segment_id=None,
        skip=None,
        limit=None,
        search=None,
        call_segments=None,
        payload: dict | None = None,
        application_ids=None,
        basic_filter: bool = None,
        static=None,
    ):
        """
        Get application details
        """
        pipeline = []
        if static is None:
            pipeline = (
                await (
                    Application().extend_pipeline_based_on_condition_for_automation(
                        start_date=date_range.get("start_date"),
                        end_date=date_range.get("end_date"),
                        college_id=college_id,
                        payload=segment.get("filters"),
                        skip=skip,
                        limit=None if basic_filter else limit,
                        advance_filters=segment.get("advance_filters"),
                    )
                )
            )
        if call_segments:
            pipeline = await data_segment_info().application_segment_info(
                pipeline,
                search=search,
                lead_type="application",
                application_ids=application_ids,
                static=static,
                basic_filter=basic_filter,
                college_id=college_id,
                payload=payload,
                call_segments=call_segments,
                skip=skip,
                limit=limit,
            )
        else:
            target_sequence = [
                {'$facet': {'pipelineResults': [], 'totalCount': [{'$count': 'value'}]}},
                {'$unwind': '$pipelineResults'},
                {'$unwind': '$totalCount'},
                {'$replaceRoot': {
                    'newRoot': {'$mergeObjects': ['$pipelineResults', {'totalCount': '$totalCount.value'}]}}}
            ]
            if pipeline[-len(target_sequence):] == target_sequence:
                del pipeline[-len(target_sequence):]
        result = (
            await DatabaseConfiguration()
            .studentApplicationForms.aggregate(pipeline)
            .to_list(None)
        )
        if call_segments:
            if static is True:
                custom_data = []
            else:
                custom_data = await self.get_custom_added_data(
                    data_segment_id=data_segment_id,
                    segment=segment,
                    college_id=college_id,
                    search=search,
                    payload=payload,
                    skip=skip,
                    limit=limit,
                )
            try:
                custom_count = custom_data[0].get("totalCount", 0)
            except IndexError:
                custom_count = 0
            except Exception:
                custom_count = 0
            try:
                total_count = result[0].get("totalCount", 0)
            except IndexError:
                total_count = 0
            student_data = result
            if limit is not None:
                if len(student_data) < limit:
                    temp = limit - len(student_data)
                    student_data = student_data + custom_data[:temp]
            else:
                student_data = student_data + custom_data
            total_count = total_count + custom_count
            if emails:
                student_data = [
                    doc.get("email")
                    for doc in student_data
                    if doc.get("email") is not None
                ]
            elif numbers:
                student_data = [
                    doc.get("mobile_number")
                    for doc in student_data
                    if doc.get("mobile_number") is not None
                ]
            return total_count, student_data
        elif emails and numbers:
            return [
                {
                    "application_id": ObjectId(doc.get("_id")),
                    "student_id": ObjectId(doc.get("student_id")),
                    "student_name": utility_obj.name_can(
                        doc.get("student_primary", {}).get("basic_details", {})
                    ),
                    "email_id": doc.get("student_primary", {})
                    .get("basic_details", {})
                    .get("email"),
                    "added_on": datetime.datetime.utcnow(),
                    "data_segment_id": ObjectId(data_segment_id),
                    "mobile_number": doc.get("student_primary", {})
                    .get("basic_details", {})
                    .get("mobile_number"),
                }
                for doc in result
            ]

    async def get_lead(
        self,
        segment,
        date_range,
        college_id,
        data_segments=False,
        emails=False,
        numbers=False,
        data_segment_id=None,
        skip=None,
        limit=None,
        search=None,
        call_segments=None,
        basic_filter=None,
        payload=None,
    ):
        """
        Fetch lead data from student primary collection
        """
        return await self.get_lead_details(
            segment=segment,
            date_range=date_range,
            college_id=college_id,
            data_segments=data_segments,
            emails=emails,
            numbers=numbers,
            data_segment_id=data_segment_id,
            skip=skip,
            limit=limit,
            search=search,
            call_segments=call_segments,
            basic_filter=basic_filter,
            payload=payload,
        )

    async def get_application(
        self,
        segment,
        date_range,
        college_id,
        data_segments=False,
        emails=False,
        numbers=False,
        data_segment_id=None,
        skip=None,
        limit=None,
        search=None,
        call_segments=None,
        payload: dict | None = None,
        basic_filter: bool = None,
    ):
        """
        Fetch application data from application collection
        """
        return await self.get_application_details(
            segment,
            date_range,
            college_id,
            data_segments=data_segments,
            emails=emails,
            numbers=numbers,
            data_segment_id=data_segment_id,
            skip=skip,
            limit=limit,
            search=search,
            call_segments=call_segments,
            basic_filter=basic_filter,
            payload=payload,
        )

    async def get_raw_data(
        self,
        segment,
        date_range,
        college_id,
        data_segments=False,
        emails=False,
        numbers=False,
        data_segment_id=None,
        skip=None,
        limit=None,
        call_segments=False,
        payload=None,
        basic_filter=None,
        search=None,
    ):
        """
        Fetch data from raw data collection
        return id, email and mobile  number of student
        """
        return await self.get_raw_data_details(
            segment,
            date_range,
            college_id,
            data_segments=data_segments,
            emails=emails,
            numbers=numbers,
            data_segment_id=data_segment_id,
            call_segments=call_segments,
            payload=payload,
            basic_filter=basic_filter,
            skip=skip,
            limit=limit,
            search=search,
        )

    async def today_datetime(cls):
        """
        Today datetime start_date & end_date
        """
        current_datetime = str(datetime.date.today())
        start_date, end_date = await utility_obj.date_change_format(
            current_datetime, current_datetime
        )
        return {"start_date": start_date, "end_date": end_date}

    async def last_7_days_datetime(self):
        """
        Last 7 day datetime
        """
        date_range = await utility_obj.week()
        start_date, end_date = await utility_obj.date_change_format(
            date_range.get("start_date"), date_range.get("end_date")
        )
        return {"start_date": start_date, "end_date": end_date}

    async def last_month_datetime(self):
        """
        Last month datetime
        """
        end_date = datetime.datetime.utcnow()
        start_date = end_date - pd.offsets.DateOffset(months=1)
        start_date, end_date = await utility_obj.date_change_format(
            start_date.to_pydatetime().strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
        )
        return {"start_date": start_date, "end_date": end_date}

    async def real_time_data_datetime(cls):
        """
        Sending None in start and end date
        """
        return {"start_date": None, "end_date": None}

    async def yesterday_datetime(cls):
        """
        Yesterday datetime
        """
        date_range = await utility_obj.yesterday()
        start_date, end_date = await utility_obj.date_change_format(
            date_range.get("start_date"), date_range.get("end_date")
        )
        return {"start_date": start_date, "end_date": end_date}

    async def get_data_from_db(
        self,
        segment,
        college_id,
        data_segments=False,
        emails=False,
        numbers=False,
        data_segment_id=None,
        payload: dict | None = None,
        basic_filter: bool = None,
        skip=None,
        limit=None,
        search=None,
        call_segments=None,
    ):
        """
        Get data from  database based on filter
        """
        date_type, date_range = None, {}
        if type(segment.get("period")) == str:
            date_type = (
                segment.get("period", "real_time_data").lower().replace(" ", "_")
            )
        elif type(segment.get("period")) == dict:
            start_date = segment.get("period", {}).get("start_date")
            end_date = segment.get("period", {}).get("end_date")
            if start_date not in ["", None] and end_date not in ["", None]:
                start_date, end_date = await utility_obj.date_change_format(
                    start_date, end_date
                )
            elif start_date not in ["", None] and end_date in ["", None]:
                start_date, end_date = await utility_obj.date_change_format(
                    start_date, start_date
                )
                end_date = datetime.datetime.utcnow()
            date_range = {"start_date": start_date, "end_date": end_date}
        module_name = segment.get("module_name").lower().replace(" ", "_")
        if date_type == "today":
            date_range = await self.today_datetime()
        elif date_type in ["real_time_data", "all_time"]:
            date_range = await self.real_time_data_datetime()
        elif date_type == "yesterday":
            date_range = await self.yesterday_datetime()
        elif date_type == "last_7_days":
            date_range = await self.last_7_days_datetime()
        elif date_type == "last_month":
            date_range = await self.last_month_datetime()
        elif date_type == "last_30_days":
            date_range = await self.last_month_datetime()
        elif date_type == "last_3_months":
            date_range = await self.last_month_datetime()
        if module_name == "application":
            return await self.get_application(
                segment,
                date_range,
                college_id,
                data_segments=data_segments,
                emails=emails,
                numbers=numbers,
                data_segment_id=data_segment_id,
                skip=skip,
                limit=limit,
                search=search,
                basic_filter=basic_filter,
                payload=payload,
                call_segments=call_segments,
            )
        elif module_name == "lead":
            return await self.get_lead(
                segment=segment,
                date_range=date_range,
                college_id=college_id,
                data_segments=data_segments,
                emails=emails,
                numbers=numbers,
                data_segment_id=data_segment_id,
                basic_filter=basic_filter,
                payload=payload,
                skip=skip,
                limit=limit,
                search=search,
                call_segments=call_segments,
            )
        elif module_name == "raw_data":
            return await self.get_raw_data(
                segment,
                date_range,
                college_id,
                data_segments=data_segments,
                emails=emails,
                numbers=numbers,
                data_segment_id=data_segment_id,
                payload=payload,
                basic_filter=basic_filter,
                call_segments=call_segments,
                skip=skip,
                limit=limit,
                search=search,
            )
        return 0, []
