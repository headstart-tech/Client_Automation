"""
This file contains class and functions related to document verification.
"""

import csv
import inspect
import logging
from pathlib import PurePath, Path
from typing import List
from zipfile import ZipFile
import boto3
from boto3 import s3
from botocore.exceptions import ClientError
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException
from app.core import get_logger
from app.core.utils import utility_obj, settings
from app.database.aggregation.get_all_applications import Application
from app.database.configuration import DatabaseConfiguration
import datetime
from app.dependencies.oauth import insert_data_in_cache, cache_invalidation
from app.helpers.advance_filter_configuration import AdvanceFilterHelper
from app.helpers.student_curd.student_application_configuration import StudentApplicationHelper
from app.helpers.student_curd.student_user_crud_configuration import StudentUserCrudHelper
from app.helpers.user_curd.user_configuration import UserHelper
from app.s3_events.s3_events_configuration import get_download_url


logger = get_logger(name=__name__)


class DocumentVerification:
    """
    This class Contains functions related to verification of documents
    """

    async def get_document_verification_details(
            self,
            date_range: dict | None = None,
            change_indicator: str | None = None,
            counselor_ids: list | None = None,
            cache_change_indicator: tuple | None = None
    ):
        """
        Get document verification status for a specified date range and change indicator.
         Parameters:
        - date_range (dict): A dictionary containing 'start_date' and 'end_date'.
        - change_indicator (str): A string that indicates if a change in the verification status should be tracked.
        - counselor_ids (list): A list of counselor IDs
        - cache_change_indicator (tuple): Change indicator key and cached value
        Returns:
        - Dict: Updates the `result` dictionary with verification statistics and change indicator information.
        """
        start_date, end_date = None, None
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date"))
        result = await self.quick_view(start_date, end_date, counselor_ids)
        if change_indicator:
            cache_key, ci_data = None, None
            if cache_change_indicator:
                cache_key, ci_data = cache_change_indicator
            if ci_data:
                previous_results = ci_data.get("previous_results", {})
                current_results = ci_data.get("current_results", {})
            else:
                today = datetime.date.today()
                start_date, middle_date, previous_date = (
                    await utility_obj.get_start_date_and_end_date_by_change_indicator(
                        change_indicator
                    )
                )
                previous_start_date, previous_end_date = await utility_obj.date_change_format(
                    str(start_date), str(middle_date)
                )
                current_start_date, current_end_date = await utility_obj.date_change_format(
                    str(previous_date), str(today)
                )
                previous_results = await self.quick_view(start_date=previous_start_date, end_date=previous_end_date,
                                                         counselor_ids=counselor_ids)
                current_results = await self.quick_view(start_date=current_start_date, end_date=current_end_date,
                                                        counselor_ids=counselor_ids)
                ci_result = {
                    "previous_result": previous_results,
                    "current_results": current_results
                }
                if cache_key:
                    await insert_data_in_cache(cache_key, ci_result, change_indicator=True)
            for field in ["total_applications", "dv_accepted", "dv_rejected", "partially_accepted", "to_be_verified",
                          "re_verification_pending"]:
                ci_result = await utility_obj.get_percentage_difference_with_position(
                    previous_results.get(field, 0),
                    current_results.get(field, 0),
                )
                result.update({
                    f"{field}_percentage": ci_result.get("percentage"),
                    f"{field}_position": ci_result.get("position")})
            return result

    async def quick_view(
            self,
            start_date: datetime = None,
            end_date: datetime = None,
            counselor_ids: list | None = None
    ):
        """
        Retrieve the application status for a specific date range.
        Parameters:
        - start_date (datetime): The start date for filtering applications.
        - end_date (datetime): The end date for filtering applications.
        - counselor_ids (list): A list of counselor IDs
        Returns:
        - dict: A dictionary containing counts for different document verification statuses
                and the total number of applications within the date range.
        """
        match = {}
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'dv_accepted': {
                        '$sum': {
                            '$cond': [
                                {
                                    '$eq': [
                                        '$dv_status', 'Accepted'
                                    ]
                                }, 1, 0
                            ]
                        }
                    },
                    'dv_rejected': {
                        '$sum': {
                            '$cond': [
                                {
                                    '$eq': [
                                        '$dv_status', 'Rejected'
                                    ]
                                }, 1, 0
                            ]
                        }
                    },
                    'partially_accepted': {
                        '$sum': {
                            '$cond': [
                                {
                                    '$eq': [
                                        '$dv_status', 'Partially Accepted'
                                    ]
                                }, 1, 0
                            ]
                        }
                    },
                    'to_be_verified': {
                        '$sum': {
                            '$cond': [
                                {
                                    '$eq': [
                                        '$documents.status', 'To be verified'
                                    ]
                                }, 1, 0
                            ]
                        }
                    },
                    're_verification_pending': {
                        '$sum': {
                            '$cond': [
                                {
                                    '$eq': [
                                        '$documents.status', 'Re uploaded'
                                    ]
                                }, 1, 0
                            ]
                        }
                    }
                }
            }
        ]
        pipeline_match = {}
        if start_date and end_date:
            match.update(
                {"enquiry_date": {"$gte": start_date, "$lte": end_date}})
            pipeline_match.update({
                "created_at": {"$gte": start_date, "$lte": end_date}
            })
        if counselor_ids:
            match.update({
                "allocate_to_counselor.counselor_id": {"$in": counselor_ids}
            })
            pipeline_match.update({
                "allocate_to_counselor.counselor_id": {"$in": counselor_ids}
            })
        if pipeline_match:
            pipeline.insert(0, {"$match": pipeline_match})
        total_applications = await DatabaseConfiguration().studentApplicationForms.count_documents(match)
        result = await DatabaseConfiguration().studentsPrimaryDetails.aggregate(pipeline).to_list(None)
        result = result[0] if result else {}
        result.update({"total_applications": total_applications})
        return result

    async def update_document_status(self, application_id: str, current_user, status
                                     ):
        """
        Updates the document verification status (dv_status) for the provided application.
        Params:
             - application_id (str): The unique identifier of the student's application.
             - current_user (str): An user_name of current user
             - status (DvStatus): A status of a document to be updated.
        Returns:
            - dict: A success message indicating that the document verification status was updated.
        Raises:
            - HTTPException: If any of the ID is invalid and no matching is found.
        """
        await UserHelper().is_valid_user(current_user)
        application = await StudentApplicationHelper().get_application_data(application_id)
        if not application:
            raise HTTPException(status_code=404, detail=f"Invalid application_id: {application_id} not found.")
        student_id = application.get("student_id")
        student = await StudentApplicationHelper().get_student_data_by_id(str(student_id))
        if not student:
            raise HTTPException(status_code=404, detail=f"Invalid student_id: {student_id} not found.")
        await DatabaseConfiguration().studentApplicationForms.update_many(
            {"student_id": student_id},
            {"$set": {"dv_status": status}},
        )
        await DatabaseConfiguration().studentsPrimaryDetails.update_one(
            {"_id": student_id},
            {"$set": {"dv_status": status}},
        )
        if (student_secondary_details := await DatabaseConfiguration().studentSecondaryDetails.find_one(
                {"student_id": student_id})) is None:
            raise HTTPException(status_code=404,
                                detail="Student secondary details not found for the provided student_id.")
        attachments = student_secondary_details.get("attachments")
        if not attachments:
            raise HTTPException(status_code=404,
                                detail="No attachments found in the student's secondary details.")
        await DatabaseConfiguration().studentSecondaryDetails.update_one(
            {"student_id": ObjectId(student_id)},
            [
                {
                    "$set": {
                        "attachments": {
                            "$map": {
                                "input": {"$objectToArray": "$attachments"},
                                "as": "item",
                                "in": {
                                    "k": "$$item.k",
                                    "v": {
                                        "$mergeObjects": [
                                            "$$item.v",
                                            {"status": status}
                                        ]
                                    }
                                }
                            }
                        }
                    }
                },
                {
                    "$set": {
                        "attachments": {"$arrayToObject": "$attachments"}
                    }
                }
            ]
        )

        await cache_invalidation(api_updated="admin/update_status_of_document")
        return {"message": "Updated dv_status of a document."}

    async def get_document_remarks(self, student_id: str, current_user) -> dict:
        """
        Get remarks of a document.

        Params:
            student_id (str): An unique student id.
            current_user (str): An user_name of current user.

        Returns:
            dict: Get remarks of documents.
        """
        user = await DatabaseConfiguration().user_collection.find_one(
            {"user_name": current_user})
        student = await StudentApplicationHelper().get_student_data_by_id(student_id)
        if ((student_secondary_data := await DatabaseConfiguration().studentSecondaryDetails.find_one(
                {"student_id": ObjectId(student_id)})) is None):
            raise HTTPException(status_code=404, detail=f"Secondary data not found for student with ID: {student_id}")
        remarks = (
            student_secondary_data.get("auditor_remarks", [])
        )

        for _id, remark in enumerate(remarks):
            if user:
                remark["timeline_type"] = "Counselor" if user.get("role", {}).get(
                    "role_name") == "college_counselor" else "System"
            elif await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"student_id": ObjectId(remark.get("user_id"))}
            ):
                remark["timeline_type"] = "Student"
            else:
                remark["timeline_type"] = "System"
            remark["id"] = _id
            current_time_str = remark.get(
                "timestamp", datetime.datetime.utcnow()
            ).strftime("%d %b %Y %I:%M:%S %p")
            current_time = datetime.datetime.strptime(
                current_time_str, "%d %b %Y %I:%M:%S %p"
            )

            if _id < len(remarks) - 1:
                next_time_str = remarks[_id + 1]["timestamp"].strftime(
                    "%d %b %Y %I:%M:%S %p"
                )
                next_time = datetime.datetime.strptime(
                    next_time_str, "%d %b %Y %I:%M:%S %p"
                )
                time_diff = utility_obj.calculate_time_diff(next_time, current_time)
                remark["duration1"] = time_diff
            remark["timestamp"] = utility_obj.get_local_time(remark.get("timestamp"))
            remark.pop("user_name")
            remark.pop("user_id")
        return {"message": "Get Auditor Remarks.", "remarks": remarks}

    async def auditor_remark(
            self, student_id: str, current_user: str, remark: str,
    ) -> dict:

        """
        Add an overall auditor remark for document.

        Params:
            student_id (str): A unique student ID.
            current_user (str): The user name of the current user (auditor).
            remark (str): The auditor's comment or remark.

        Returns:
            dict: A dictionary containing the message.
        """

        if (
                is_student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"user_name": current_user}
                )
        ) is not None:
            user = is_student
        elif (
                is_user := await DatabaseConfiguration().user_collection.find_one(
                    {"user_name": current_user}
                )
        ) is not None:
            user = is_user
        student = await StudentApplicationHelper().get_student_data_by_id(student_id)
        if student is None:
            raise HTTPException(status_code=404, detail=f"Student not found with ID: {student_id}")
        if ((student_secondary_data := await DatabaseConfiguration().studentSecondaryDetails.find_one(
                {"student_id": ObjectId(student_id)}))
                is None):
            raise HTTPException(status_code=404, detail=f"Secondary data not found for student with ID: {student_id}")

        if "attachments" not in student_secondary_data:
            raise HTTPException(status_code=400, detail="Attachments not found in student secondary data.")
        auditory_remarks = student_secondary_data.get("auditor_remarks", [])
        auditory_remarks.insert(0, {
            "message": remark,
            "timestamp": datetime.datetime.utcnow(),
            "user_name": (
                utility_obj.name_can(user.get("basic_details"))
                if is_student
                else utility_obj.name_can(user)
            ),
            "user_id": user.get("_id"),
        })

        await DatabaseConfiguration().studentSecondaryDetails.update_one(
            {"student_id": student_secondary_data.get("student_id")},
            {
                "$set": {
                    "auditor_remarks": auditory_remarks
                }
            },
        )

        return {"message": "Auditor Remarks added."}

    async def get_application_data(self, payload: dict | None = None,
                                   page_num: int | None = None,
                                   page_size: int | None = None,
                                   season: str | None = None,
                                   counselor_ids: list | None = None,
                                   sort_type: str | None = None,
                                   column_name: str | None = None,
                                   search_condition: dict | None = None
                                   ):

        """
            Retrieves paginated application data for document verification.
            Params:
                payload (dict, optional): Filters for the query (e.g., dv_status, tenth_board, etc.).
                page_num (int, optional): The page number for pagination.
                page_size (int, optional): The number of records per page.
                season (str, optional): Admission season to filter applications.
                counselor_ids (list, optional): List of counselor IDs to filter results.
                sort_type (str, optional) : sort based on the given string asc, dsc
                column_name (str, optional) : Return data based on sorting of this column
                search_condition(dict, optional): Return data based on matching with email, name, phone number
            Returns:
                dict: Contains 'data', 'total', 'count', 'pagination', and a status 'message'.
        """

        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
        match_conditions = {'current_stage': {'$gte': 8.75}}
        if counselor_ids:
            match_conditions["allocate_to_counselor.counselor_id"] = {"$in": counselor_ids}
        pipeline = [
            {'$match': match_conditions},
            {
                '$lookup': {
                    'from': 'studentsPrimaryDetails',
                    'localField': 'student_id',
                    'foreignField': '_id',
                    'as': 'result'
                }
            },
            {'$unwind': '$result'},
            {
                '$lookup': {
                    'from': 'studentSecondaryDetails',
                    'localField': 'student_id',
                    'foreignField': 'student_id',
                    'as': 'education'
                }
            },
            {'$unwind': {"path": '$education',
             "preserveNullAndEmptyArrays": True }
             },
            {
                '$lookup': {
                    'from': 'leadsFollowUp',
                    'localField': '_id',
                    'foreignField': 'application_id',
                    'as': 'leads'
                }
            },
            {
                '$unwind': {"path": '$leads',
                "preserveNullAndEmptyArrays": True}
            },
            {
                '$addFields': {
                    'source_type': {
                        '$concatArrays': [
                            {
                                '$cond': {
                                    'if': {
                                        '$gt': [
                                            {
                                                '$type': '$source.primary_source'
                                            }, 'missing'
                                        ]
                                    },
                                    'then': [
                                        'primary'
                                    ],
                                    'else': []
                                }
                            }, {
                                '$cond': {
                                    'if': {
                                        '$gt': [
                                            {
                                                '$type': '$source.secondary_source'
                                            }, 'missing'
                                        ]
                                    },
                                    'then': [
                                        'secondary'
                                    ],
                                    'else': []
                                }
                            }, {
                                '$cond': {
                                    'if': {
                                        '$gt': [
                                            {
                                                '$type': '$source.tertiary_source'
                                            }, 'missing'
                                        ]
                                    },
                                    'then': [
                                        'tertiary'
                                    ],
                                    'else': []
                                }
                            }
                        ]
                    }
                }
            }
        ]
        search_condition = search_condition or {}
        conditions = search_condition

        course_ids = []
        specializations = []

        form_name_list = payload.get("form_name", [])
        if form_name_list:
            for form in form_name_list:
                course_id = form.get("course_id")
                if course_id and course_id.strip():
                    course_ids.append(ObjectId(course_id))

                course_specialization = form.get("course_specialization")
                if course_specialization and course_specialization.strip():
                    specializations.append(course_specialization)

        check = False
        if payload.get("dv_status"):
            conditions['dv_status'] = {"$in": payload['dv_status']}
            check = True
        if payload.get("tenth_board") and payload.get("tenth_board", {}).get("tenth_board_name"):
            conditions['education.education_details.tenth_school_details.board'] = {
                "$in": payload.get("tenth_board").get("tenth_board_name")}
            check = True
        if course_ids:
            conditions['course_id'] = {"$in": course_ids}
            check = True
        if specializations:
            conditions['spec_name1'] = {"$in": specializations}
            check = True
        if payload.get("tenth_passing_year") not in [None, ""]:
            conditions['education.education_details.tenth_school_details.year_of_passing'] = {
                "$eq": int(payload['tenth_passing_year'])}
            check = True
        if payload.get("twelve_board") and payload.get("twelve_board", {}).get("twelve_board_name"):
            conditions['education.education_details.inter_school_details.board'] = {
                "$in": payload.get("twelfth_board").get("twelve_board_name")}
            check = True
        if payload.get("twelve_passing_year") not in [None, ""]:
            conditions['education.education_details.inter_school_details.year_of_passing'] = {
                "$eq": int(payload['twelfth_passing_year'])}
            check = True

        if payload.get("form_submission_date") not in [{}, None]:
            date_range = payload.pop("form_submission_date", {})
            start_date, end_date = await StudentApplicationHelper().get_start_end_dates(date_range)
            if start_date and end_date:
                conditions['enquiry_date'] = {
                    "$gte": start_date,
                    "$lte": end_date
                }
                check = True

        if check or search_condition:
            pipeline.append({'$match': conditions})

        advance_filters = payload.get("advance_filters", [])
        if advance_filters:
            check = str(advance_filters)

            pipeline = await Application().apply_lookup_on_communication_log(
                pipeline)
            if "queries" in check:
                pipeline = await Application().apply_lookup_on_queries(pipeline)
            pipeline = await AdvanceFilterHelper().apply_advance_filter(
                advance_filters,
                pipeline,
                student_primary="result",
                courses="course_details",
                student_secondary="education",
                lead_followup="leads",
                communication_log="communication_log",
                queries="queries",
            )

        pagination_stage = [
            {'$sort': {'enquiry_date': -1}
             }, {
                '$facet': {'totalCount': [{'$count': 'value'}
                                          ],
                           'pipelineResults': [
                               {'$skip': skip},
                               {'$limit': limit}
                           ]
                           }
            }, {
                '$unwind': '$pipelineResults'
            }, {
                '$unwind': '$totalCount'
            }, {
                '$replaceRoot': {
                    'newRoot': {
                        '$mergeObjects': [
                            '$pipelineResults', {
                                'totalCount': '$totalCount.value'
                            }
                        ]
                    }
                }
            }
        ]
        pipeline2 = [
            {
                '$project': {
                    '_id': 0,
                    'application_id': {'$toString': '$_id'},
                    'student_id': {'$toString': '$student_id'},
                    'totalCount': 1,
                    'student_name': {
                        '$concat': [
                            '$result.basic_details.first_name', ' ',
                            {'$ifNull': ['$result.basic_details.middle_name', '']},
                            {
                                '$cond': {
                                    'if': {'$eq': ['$result.basic_details.middle_name', '']},
                                    'then': '',
                                    'else': ' '
                                }
                            },
                            '$result.basic_details.last_name'
                        ]
                    },
                    'student_email': '$result.basic_details.email',
                    'student_mobile_no': '$result.basic_details.mobile_number',
                    'dv_status': {'$ifNull': ['$dv_status', 'To be verified']},
                    'course_name': {
                        '$let': {
                            'vars': {
                                'course_data': {
                                    '$arrayElemAt': [
                                        {
                                            '$filter': {
                                                'input': {'$objectToArray': '$result.course_details'},
                                                'as': 'course',
                                                'cond': {'$ne': ['$$course.v', None]}
                                            }
                                        }, 0
                                    ]
                                }
                            },
                            'in': {
                                '$concat': [
                                    '$$course_data.v.course_name', ' in ',
                                    {'$arrayElemAt': ['$$course_data.v.specs.spec_name', 0]}
                                ]
                            }
                        }
                    },
                    'auditor_name': {'$arrayElemAt': ["$education.auditor_remarks.user_name", 0]},
                    'auditor_remark': {'$arrayElemAt': ['$education.auditor_remarks.message', 0]},
                    'last_update': {
                        "$dateToString": {
                            "format": "%H:%M:%S %d %b %Y",
                            "date": {"$arrayElemAt": ["$education.auditor_remarks.timestamp", 0]},
                            "timezone": "Asia/Kolkata"
                        }
                    },
                    'custom_application_id': '$custom_application_id',
                    'state_name': '$result.address_details.communication_address.state.state_name',
                    'cite_name': '$result.address_details.communication_address.city.city_name',
                    'counselor_name': {'$ifNull': ['$allocate_to_counselor.counselor_name', '']},
                    'utm_campaign': '$source.primary_source.utm_campaign',
                    'utm_medium': '$source.primary_source.utm_medium',
                    'lead_type': '$source.primary_source.lead_type',
                    'source_name': '$source.primary_source.utm_source',
                    "reupload_status": {"$ifNull": ["$education.documents_reuploaded", False]},
                    'verification_status': {
                        "$cond": {
                            "if": {"$eq": ['$result.is_verify', True]},
                            "then": "verified",
                            "else": "unverified"
                        }
                    },
                    'current_application_stage': {
                        '$switch': {
                            'branches': [
                                {
                                    'case': {
                                        '$ifNull': [
                                            '$offer_letter', False
                                        ]
                                    },
                                    'then': 'Offer Letter Sent'
                                }, {
                                    'case': {
                                        '$eq': [
                                            '$interviewStatus.status', 'Done'
                                        ]
                                    },
                                    'then': 'Interview Done'
                                }, {
                                    'case': {
                                        '$eq': [
                                            '$interviewStatus.status', 'Scheduled'
                                        ]
                                    },
                                    'then': 'Interview Scheduled'
                                }, {
                                    'case': {
                                        '$eq': [
                                            '$dv_status', 'Accepted'
                                        ]
                                    },
                                    'then': 'Accepted'
                                }, {
                                    'case': {
                                        '$eq': [
                                            '$dv_status', 'Rejected'
                                        ]
                                    },
                                    'then': 'Rejected'
                                }, {
                                    'case': {
                                        '$eq': [
                                            '$declaration', True
                                        ]
                                    },
                                    'then': 'Submitted'
                                }, {
                                    'case': {
                                        '$eq': [
                                            '$payment_info.status', 'captured'
                                        ]
                                    },
                                    'then': 'Captured'
                                }
                            ],
                            'default': ''
                        }
                    },
                    'source_type': 1,
                    'lead_sub_stage': {'$ifNull': ['$leads.lead_stage_label', '']},
                    'application_stage': {"$cond": {
                        "if": {"$eq": ['$declaration', True]},
                        "then": "Completed",
                        "else": "In progress"
                    }
                    },
                    'registration_date': {
                        "$dateToString": {
                            "format": "%H:%M:%S %d %b %Y",
                            "date": '$enquiry_date',
                            "timezone": "Asia/Kolkata"
                        }
                    },
                    'tags': {"$ifNull": ["$result.tags", []]}
                }
            }
        ]

        if payload.get("tenth_board") and payload.get("tenth_board", {}).get("tenth_board_b") is True:
            pipeline2[0]['$project']['tenth_board_name'] = '$education.education_details.tenth_school_details.board'

        if payload.get("twelve_board") and payload.get("twelve_board", {}).get("twelve_board_b") is True:
            pipeline2[0]['$project']['twelve_board_name'] = '$education.education_details.inter_school_details.board'

        if sort_type and column_name:
            sort_order = 1 if sort_type == "asc" else -1
            pipeline2.append({"$sort": {column_name: sort_order}})

        pipeline.extend(pipeline2)

        if check or search_condition:
            pipeline.extend(pagination_stage)
        else:
            pipeline[1:1] = pagination_stage
        data = await DatabaseConfiguration(season=season).studentApplicationForms.aggregate(pipeline).to_list(None)

        if data and "totalCount" in data[0]:
            total = data[0]["totalCount"]
        else:
            total = 0
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, total, "/document_verification/all_applications/")

        return {
            "data": data,
            "total": total,
            "count": page_size,
            "pagination": response.get("pagination"),
            'message': 'Get document verification data'
        }


    async def get_student_application(
            self, student_ids: list[str],
    ):
        """
        Get details of student applications for a list of student IDs.
        Params:
            student_ids (List[str]): List of student IDs for which applications are to be retrieved.
        Returns:
           str: A URL to download the zip file containing the applications
        Raises:
            HTTPException: If no applications are found for a student.
        """
        path = Path(inspect.getfile(inspect.currentframe())).resolve()
        pth = PurePath(path).parent
        ext_zip = PurePath(pth, Path(f"sample.zip"))
        s3_res = boto3.resource(
            "s3", aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.region_name)
        s3 = settings.s3_client
        aws_env = settings.aws_env
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        download_application = False
        with ZipFile(str(ext_zip), "w") as extzipObj:
            for student_id in student_ids:
                student = await DatabaseConfiguration().studentsPrimaryDetails.find_one({"_id": ObjectId(student_id)})
                if student is None:
                    raise HTTPException(status_code=404, detail=f"Student not found with ID {student_id}")
                if (
                        all_applications := await DatabaseConfiguration().studentApplicationForms.aggregate(
                            [{"$match": {"student_id": ObjectId(student_id)}}]
                        ).to_list(length=None)
                ) is None:
                    raise HTTPException(status_code=404, detail=f"Application not found for student {student_id}")
                for application in all_applications:
                    file = application.get("application_download_url", "")
                    if file:
                        download_application = True
                        object_name = PurePath(file).name
                        path = PurePath(pth, Path(object_name))
                        season = utility_obj.get_year_based_on_season()
                        object_key = f"{utility_obj.get_university_name_s3_folder()}/{season}/{settings.s3_student_documents_bucket_name}/{student_id}/application/{object_name}"
                        try:
                            s3_res.Bucket(
                                base_bucket).download_file(
                                object_key, str(path)
                            )
                        except Exception as error:
                            logger.error(f"Error downloading file %s: %s", object_name,
                                         error)
                        try:
                            extzipObj.write(str(path),
                                            arcname=f"{utility_obj.name_can(student.get('basic_details', {}))}/application/{object_name}")
                        except FileNotFoundError as error:
                            logger.error(f"Error write the file inn zipObj {error}", )
                        if Path(str(path)).is_file():
                            Path(str(path)).unlink()
        zip_s3_url = None
        try:
            if download_application:
                unique_filename = utility_obj.create_unique_filename(extension=".zip")
                path_to_unique_filename = f"{utility_obj.get_university_name_s3_folder()}/{settings.s3_download_bucket_name}/{unique_filename}"
                with open(str(ext_zip), "rb") as f:
                    s3.upload_fileobj(
                        f, base_bucket, path_to_unique_filename
                    )
                zip_s3_url = await get_download_url(
                    base_bucket, path_to_unique_filename
                )
        except ClientError as e:
            logging.error(e)
            raise HTTPException(status_code=400, detail=f"Something went wrong in s3")
        finally:
            if Path(str(ext_zip)).is_file():
                Path(str(ext_zip)).unlink()
        return {
              "file_url": zip_s3_url,
              "message": "Get zip URL"} if zip_s3_url else {"message": "Found no documents to download"}

    async def get_primary_sec_download_links(self, student_ids: List[str], college_id: str):
        """
        Get Document Download link for List of student IDs
        Params:
            student_ids (List[str]): List of student IDs for which documents are to be downloaded.
            college_id (str): The college ID associated with the students.
        Returns:
            str: A URL to download the zip file containing the student's documents.
        Raises:
            HTTPException: If a student or their documents are not found
        """
        path = Path(inspect.getfile(inspect.currentframe())).resolve()
        pth = PurePath(path).parent
        ext_zip = PurePath(pth, Path(f"sample.zip"))
        s3_res = boto3.resource(
            "s3", aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.region_name)
        s3 = settings.s3_client
        flag, zip_s3_url = False, None
        with ZipFile(str(ext_zip), "w") as extzipObj:
            for student_id in student_ids:
                await utility_obj.is_id_length_valid(_id=student_id, name="Student id")
                student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(student_id)})
                if not student:
                    raise HTTPException(status_code=404, detail="Student not found.")
                documents = await DatabaseConfiguration().studentSecondaryDetails.find_one(
                    {"student_id": ObjectId(student_id), "attachments": {"$exists": True}}
                )
                if documents:
                    path = PurePath(pth, Path("primary_detail.csv"))
                    primary_detail_filename = PurePath(path).name
                    fieldnames = list(student.keys())
                    with open(str(path), "w", encoding="UTF8", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerow(student)
                    aws_env = settings.aws_env
                    base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
                    attachments = documents.get("attachments", {})
                    extzipObj.write(str(path),
                                    arcname=f"{utility_obj.name_can(student.get('basic_details', {}))}/{primary_detail_filename}")
                    if Path(str(path)).is_file():
                        Path(str(path)).unlink()
                    for document_name, document in attachments.items():
                        if document is not None:
                            file = document.get("file_s3_url")
                            object_name = PurePath(file).name
                            path = PurePath(pth, Path(object_name))
                            season = utility_obj.get_year_based_on_season()
                            object_key = f"{utility_obj.get_university_name_s3_folder()}/{season}/{settings.s3_student_documents_bucket_name}/{student_id}/{document_name}/{object_name}"
                            try:
                                s3_res.Bucket(
                                    base_bucket).download_file(
                                    object_key, str(path)
                                )
                            except Exception as error:
                                logger.error(f"Error downloading file %s: %s", object_name,
                                             error)
                            try:
                                extzipObj.write(str(path),
                                                arcname=f"{utility_obj.name_can(student.get('basic_details', {}))}/{document_name}/{object_name}")
                                flag = True
                            except FileNotFoundError as error:
                                logger.error(f"Error write the file inn zipObj {error}", )
                            if Path(str(path)).is_file():
                                Path(str(path)).unlink()
        if flag:
            unique_filename = utility_obj.create_unique_filename(extension=".zip")
            path_to_unique_filename = f"{utility_obj.get_university_name_s3_folder()}/{settings.s3_download_bucket_name}/{unique_filename}"
            try:
                with open(str(ext_zip), "rb") as f:
                    s3.upload_fileobj(
                        f, base_bucket, path_to_unique_filename
                    )
            except ClientError as e:
                logging.error(e)
                return False
            finally:
                if Path(str(ext_zip)).is_file():
                    Path(str(ext_zip)).unlink()
            zip_s3_url = await get_download_url(
                base_bucket, path_to_unique_filename
            )
        return {
              "file_url": zip_s3_url,
              "message": "Get zip URL"} if zip_s3_url else {"message": "Found no documents to download"}


doc_verification_obj = DocumentVerification()
