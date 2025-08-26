"""
This file contains the information about the current data of the application
"""

from bson import ObjectId

from app.core.utils import utility_obj
from app.database.aggregation.get_all_applications import Application
from app.database.configuration import DatabaseConfiguration


class data_segment_info:
    """
    A class representing the segment information of a segment
    """

    async def application_segment_info(
        self,
        pipeline,
        search=None,
        lead_type=None,
        basic_filter=None,
        payload=None,
        call_segments=None,
        college_id=None,
        student_ids=None,
        static=None,
        application_ids=None,
        skip=None,
        limit=None,
    ):
        """
        Get the segment information of the current segment

        params:
            search (str): The search string to search for the segment name,
             email and mobile number
             skip (int): The number of the segment
             limit (int): The number of the segment limit

        returns:
            A data segment information
        """
        target_sequence = [
            {'$facet': {'pipelineResults': [], 'totalCount': [{'$count': 'value'}]}},
            {'$unwind': '$pipelineResults'},
            {'$unwind': '$totalCount'},
            {'$replaceRoot': {
                'newRoot': {'$mergeObjects': ['$pipelineResults', {'totalCount': '$totalCount.value'}]}}}
        ]
        if lead_type == "application":
            if basic_filter:
                if static is None:
                    result = DatabaseConfiguration().studentApplicationForms.aggregate(
                        pipeline
                    )
                    application_ids = [
                        ObjectId(x.get("_id"))
                        async for x in result
                        if len(str(x.get("_id", ""))) == 24
                    ]
                if payload is None:
                    payload = {}
                start_date = end_date = None
                if payload.get("date_range") not in [{}, None]:
                    date_range = payload.pop("date_range", {})
                    start_date, end_date = await utility_obj.get_start_and_end_date(
                        date_range
                    )
                pipeline = await Application().all_applications(
                    payload=payload,
                    college_id=college_id,
                    page_num=skip + 1 if skip is not None else 1,
                    page_size=limit,
                    start_date=start_date,
                    end_date=end_date,
                    counselor_id=None,
                    applications=True,
                    application_ids=application_ids,
                    form_initiated=False,
                    call_segments=call_segments,
                )
                pipeline = await Application().aggregation_pipeline(
                    payload=payload,
                    pipeline=pipeline,
                    skip=skip,
                    limit=limit,
                    advance_filters=payload.get("advance_filters"),
                    data_segment=True,
                )
            project_phase = {
                "$project": {
                    "_id": 0,
                    "application_id": {"$toString": "$_id"},
                    "student_id": {"$toString": "$student_id"},
                    "email": "$student_primary.user_name",
                    "mobile_number": "$student_primary.basic_details"
                    ".mobile_number",
                    "tags": "$student_primary.tags",
                    "totalCount": "$totalCount",
                    "custom_application_id": "$custom_application_id",
                    "lead_stage": {
                        "$ifNull": ["$lead_details.lead_stage", "Fresh Lead"]
                    },
                    "payment_status": "$payment_info.status",
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
                            "$spec_name1",
                        ]
                    },
                    "state": "$student_primary.address_details."
                    "communication_address.state.state_name",
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
                            "date": "$enquiry_date",
                        }
                    },
                    "lead_type": "$student_primary.source."
                    "primary_source.lead_type",
                    "counselor_name": "$student_primary."
                    "allocate_to_counselor.counselor_name",
                    "application_stage": (
                        "completed" if "$declaration" else "incomplete"
                    ),
                    "verification": "$student_primary.is_verify",
                    "utm_campaign": "$student_primary.source"
                    ".primary_source.utm_campaign",
                    "utm_medium": "$student_primary.source"
                    ".primary_source.utm_medium",
                    "lead_sub_stage": {
                        "$ifNull": ["$lead_details.lead_stage_label", ""]
                    },
                }
            }
            if pipeline[-len(target_sequence):] == target_sequence:
                pipeline.insert(-len(target_sequence), project_phase)
            else:
                pipeline.append(project_phase)
        else:
            if basic_filter:
                if static is None:
                    result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
                        pipeline
                    )
                    student_ids = [x.get("_id") async for x in result]
                if payload is None:
                    payload = {}
                start_date = end_date = None
                if payload.get("date_range") not in [{}, None]:
                    date_range = payload.pop("date_range", {})
                    start_date, end_date = await utility_obj.get_start_and_end_date(
                        date_range
                    )
                pipeline = await Application().all_applications(
                    payload=payload,
                    college_id=college_id,
                    page_num=skip + 1 if skip is not None else 1,
                    page_size=limit,
                    start_date=start_date,
                    end_date=end_date,
                    counselor_id=None,
                    applications=False,
                    student_ids=student_ids,
                    form_initiated=False,
                    call_segments=call_segments,
                    data_segment=True,
                )
            project_phase = {
                "$project": {
                    "_id": 0,
                    "application_id": {
                        "$map": {
                            "input": "$applications",
                            "as": "app",
                            "in": {"$toString": "$$app._id"},
                        }
                    },
                    "student_id": {"$toString": "$_id"},
                    "totalCount": "$totalCount",
                    "student_name": {
                        "$trim": {
                            "input": {
                                "$concat": [
                                    "$basic_details.first_name",
                                    {
                                        "$cond": [
                                            "$basic_details.middle_name",
                                            " ",
                                            "",
                                        ]
                                    },
                                    "$basic_details.middle_name",
                                    {
                                        "$cond": [
                                            "$basic_details.last_name",
                                            " ",
                                            "",
                                        ]
                                    },
                                    "$basic_details.last_name",
                                ]
                            }
                        }
                    },
                    "state": "$address_details."
                    "communication_address.state.state_name",
                    "email": "$user_name",
                    "mobile_number": "$basic_details.mobile_number",
                    "tags": "$tags",
                    "custom_application_id": "$student_application"
                    ".custom_application_id",
                    "lead_stage": {
                        "$ifNull": ["$lead_details.lead_stage", ["Fresh Lead"]]
                    },
                    "payment_status": "$student_application.payment_info.status",
                    "city": "$city_name",
                    "counselor_name": "$counselor_name",
                    "source_name": "source" ".primary_source.utm_source",
                    "registration_date": "$application_dates",
                    "lead_type": "$source_details.primary_source.lead_type",
                    "payment_initiates": "$payment_initiates",
                    "application_stage": "$application_stages",
                    "verification": {
                        "$cond": ["$is_verify", "verified", "unverified"]
                    },
                    "utm_campaign": "$source.primary_source.utm_campaign",
                    "utm_medium": "$source.primary_source.utm_medium",
                    "lead_sub_stage": {
                        "$ifNull": ["$lead_details.lead_stage_label", []]
                    },
                    "course_name": {
                        "$map": {
                            "input": {"$objectToArray": "$course_details"},
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
                                                            ["Master", "Bachelor"],
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
            if pipeline[-len(target_sequence):] == target_sequence:
                pipeline.insert(-len(target_sequence), project_phase)
            else:
                pipeline.append(project_phase)
        if search is not None:
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
        return pipeline
