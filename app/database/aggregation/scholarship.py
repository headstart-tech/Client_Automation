"""
This file contains class and functions related to scholarship.
"""
from bson import ObjectId
from app.database.configuration import DatabaseConfiguration
from app.core.utils import utility_obj
from app.background_task.scholarship import ScholarshipActivity
from app.helpers.scholarship_configuration import Scholarship
from app.database.aggregation.admin_user import AdminUser
from app.database.aggregation.get_all_applications import Application
from app.s3_events.s3_events_configuration import upload_csv_and_get_public_url
from fastapi import BackgroundTasks, Request
from datetime import datetime, timezone
from app.background_task.admin_user import DownloadRequestActivity


class ScholarshipAggregation:
    """
    Contains functions related to get scholarship data based on aggregation.
    """

    async def get_scholarship_information(self, scholarship_id: str | None = None) -> list:
        """
        Get scholarship (s) information based on aggregation.

        Params:
            - scholarship_id (str | None): Optional field. Default value: None.
                Unique identifier of a scholarship.

        Returns:
            list: A list which contains scholarship (s) information.
        """
        aggregation_pipeline = [
            {"$sort": {"created_at": -1}},
            {
                "$project": {
                    "_id": {"$toString": "$_id"}, "name": 1,
                    "copy_scholarship_id": {"$toString": "$copy_scholarship_id"}, "copy_scholarship_name": 1,
                    "programs": {
                        "$map": {
                            "input": {
                                "$ifNull": ["$programs", []]
                            },
                            "in": {
                                "course_id": {"$toString": "$$this.course_id"},
                                "course_name": "$$this.course_name",
                                "specialization_name": "$$this.specialization_name",
                            },
                        }
                    }, "count": 1, "waiver_type": 1, "waiver_value": 1, "template_id": {"$toString": "$template_id"},
                    "template_name": 1, "status": 1, "filters": 1, "advance_filters": 1
                }
            }
        ]
        if scholarship_id:
            await utility_obj.is_length_valid(scholarship_id, "Scholarship id")
            aggregation_pipeline.insert(0, {"$match": {"_id": ObjectId(scholarship_id)}})
        return await DatabaseConfiguration().scholarship_collection.aggregate(aggregation_pipeline).to_list(None)

    async def get_scholarship_table_information(self, college_id: str, page_num: int | None,
                                                page_size: int | None, filter_parameters: dict | None) -> dict:
        """
        Get scholarship table information like scholarship name along program names, count, eligible count, offered count,
        availed_by count, available count, availed_amount.

        Params:
            - college_id (str): Unique identifier of a college.
            - page_num (int | None): Either None or page number where want to show selection
                procedures data.
            - page_size (int | None): Either None or page size means how many data want to show on page_num.
            - filter_parameters (dict | None): Either None or a dictionary which filter parameters along with values.

        Returns:
            - dict: A dictionary which contains scholarship table information.
        """
        match_stage = {"name": {"$ne": "Custom scholarship"}}
        search = filter_parameters.get("search")
        if search:
            match_stage.update({"$or": [
                {"name": {"$regex": f".*{search}.*", "$options": "i"}}]})
        aggregation_pipeline = [
            {"$sort": {"created_at": -1}},
            {"$match": match_stage},
            {
                "$project": {
                    "_id": {"$toString": "$_id"}, "name": 1,
                    "programs": {
                        "$map": {
                            "input": {
                                "$ifNull": ["$programs", []]
                            },
                            "in": {
                                "course_id": {"$toString": "$$this.course_id"},
                                "course_name": "$$this.course_name",
                                "specialization_name": "$$this.specialization_name",
                                "offered_applicants_count": {"$ifNull": ["$$this.offered_applicants_count", 0]},
                                "availed_applicants_count": {"$ifNull": ["$$this.availed_applicants_count", 0]},
                                "availed_amount": {"$ifNull": ["$$this.availed_amount", 0]},
                            },
                        }
                    }, "count": 1,
                    "offered_applicants_count": {"$ifNull": ["$offered_applicants_count", 0]},
                    "availed_applicants_count": {"$ifNull": ["$availed_applicants_count", 0]},
                    "available": {
                        "$subtract": [{"$ifNull": ["$count", 0]}, {"$ifNull": ["$availed_applicants_count", 0]}, ]},
                    "availed_amount": {"$ifNull": ["$availed_amount", 0]},
                    "status": 1, "filters": 1, "advance_filters": 1
                }
            }
        ]
        sort_type = filter_parameters.get("sort_type")
        column_name = filter_parameters.get("sort")
        if sort_type and column_name:
            sort_order = 1 if sort_type == "asc" else -1
            aggregation_pipeline.insert(2, {"$sort": {column_name: sort_order}})
        if page_num and page_size:
            skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                                  page_size)
            aggregation_pipeline = utility_obj.get_count_aggregation(
                aggregation_pipeline, skip=skip, limit=limit
            )
        aggregation_result = await DatabaseConfiguration().scholarship_collection.aggregate(
            aggregation_pipeline).to_list(None)
        total_data = 0
        for list_id, scholarship_information in enumerate(aggregation_result):
            if list_id == 0:
                try:
                    total_data = scholarship_information.get("totalCount", 0)
                except IndexError:
                    total_data = 0
                except Exception:
                    total_data = 0
            if isinstance(scholarship_information, dict):
                programs_info = scholarship_information.get("programs", [])
                course_ids, course_specializations_list, course_names, registration_fees = \
                    await Scholarship().get_validate_programs_information(programs_info, convert_course_id=False)
                normal_filters = scholarship_information.pop("filters", {})
                advance_filters = scholarship_information.pop("advance_filters", [])
                aggregation_result[list_id].update(
                    {"eligible_count": await ScholarshipActivity().get_eligible_applicants_info(
                        programs_info={"course_id": course_ids,
                                       "course_specialization": course_specializations_list,
                                       "course_name": course_names},
                        normal_filters=normal_filters, advance_filters=advance_filters,
                        college_id=college_id, get_count_only=True)})
                for _id, program_info in enumerate(programs_info):
                    programs_info[_id].update(
                        {"eligible_count":
                             await ScholarshipActivity().get_eligible_applicants_info(
                                 programs_info={"course_id": [program_info.get("course_id")],
                                                "course_specialization": [program_info.get("specialization_name")]},
                                 normal_filters=normal_filters,
                                 advance_filters=advance_filters,
                                 college_id=college_id,
                                 get_count_only=True)})
        custom_scholarship_info = await DatabaseConfiguration().scholarship_collection.find_one(
            {"name": "Custom scholarship"})
        if not custom_scholarship_info:
            custom_scholarship_info = {}
        return {"data": aggregation_result, "custom_scholarship_info":
            {"_id": str(custom_scholarship_info.get("_id")), "name": "Custom scholarship",
             "offered_applicants_count": custom_scholarship_info.get("offered_applicants_count", 0),
             "availed_applicants_count": custom_scholarship_info.get("availed_applicants_count", 0),
             "availed_amount": custom_scholarship_info.get("availed_amount", 0),
             "status": custom_scholarship_info.get("status", "Active")},
                "message": "Get scholarship table information.", "total_data": total_data}

    async def get_scholarship_summary_info(self) -> dict:
        """
        Get scholarship summary information like total scholarship count along with active/closed count,
        total availed count.

        Returns:
            dict: A list which contains scholarship (s) information.
        """
        aggregation_result = DatabaseConfiguration().scholarship_collection.aggregate([
            {"$match": {"name": {"$ne": "Custom scholarship"}}},
            {
                "$group": {
                    "_id": None,
                    "total_scholarships": {"$sum": 1},
                    "active_scholarships": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$status", "Active"]},
                                1,
                                0,
                            ]
                        }
                    },
                    "closed_scholarships": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$status", "Closed"]},
                                1,
                                0,
                            ]
                        }
                    },
                    "total_availed_amount": {
                        "$push": {"$ifNull": ["$availed_amount", 0]}
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total_scholarships": 1,
                    "active_scholarships": 1,
                    "closed_scholarships": 1,
                    "total_availed_amount": {"$sum": "$total_availed_amount"}
                }
            }
        ])
        scholarship_summary = {}
        async for scholarship_summary in aggregation_result:
            if scholarship_summary is None:
                scholarship_summary = {}
        return {"data": scholarship_summary, "message": "Get scholarship summary data."}

    async def give_custom_scholarship_table_data(self, college_id: str, user: dict, page_num: int, page_size: int,
                                                 search: str | None) -> dict:
        """
        Get give custom scholarship table data.

        Params:
            - college_id (str): Unique identifier of a college.
            - user (dict): A dictionary which contains user information.
            - page_num (int | None): Either None or page number where want to show selection
                procedures data.
            - page_size (int | None): Either None or page size means how many data want to show on page_num.
            - search (str | None): Either None or a string value which useful for get data based on student name.

        Returns:
            dict: A dictionary which contains give custom scholarship table information.
        """
        role_name = user.get("role", {}).get("role_name", "")
        counselor_ids = None

        if role_name == "college_counselor":
            counselor_ids = [ObjectId(user.get("_id"))]
        if role_name == "college_head_counselor":
            counselor_ids = await AdminUser().get_users_ids_by_role_name(
                "college_counselor", college_id, user.get("_id")
            )
            counselor_ids.append(ObjectId(user.get("_id")))
        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
        application_obj = Application()
        aggregation_pipeline = await application_obj.initialize_pipeline_all_applications(
            college_id,
            None,
            None,
            counselor_id=counselor_ids,
            paid_filter=True
        )
        aggregation_pipeline = await application_obj.primary_lookup_pipeline(
            pipeline=aggregation_pipeline,
            payload={}
        )
        aggregation_pipeline = await application_obj.apply_lookup_on_leadfollowup(aggregation_pipeline)
        aggregation_pipeline = await application_obj.course_pipeline(aggregation_pipeline)
        aggregation_pipeline.append({
            "$project": {
                "_id": 0,
                "application_id": {"$toString": "$_id"},
                "custom_application_id": {"$toString": "$custom_application_id"},
                "student_email": "$student_primary.basic_details.email",
                "student_mobile_number": "$student_primary.basic_details.mobile_number",
                "student_name": {
                    "$trim": {
                        "input": {
                            "$concat": [
                                "$student_primary.basic_details.first_name",
                                {
                                    "$cond": [
                                        {"$in": ["$student_primary.basic_details.middle_name", ["", None]]},
                                        "",
                                        " "
                                    ]
                                },
                                "$student_primary.basic_details.middle_name",
                                {
                                    "$cond": [
                                        {"$in": ["$student_primary.basic_details.last_name", ["", None]]},
                                        "",
                                        " "
                                    ]
                                },
                                "$student_primary.basic_details.last_name"
                            ]
                        }
                    }
                },
                "tags": "$student_primary.tags",
                "payment_status": {
                    "$cond": {
                        "if": {"$in": ["$payment_info.status", ["", None]]},
                        "then": {
                            "$cond": {
                                "if": "$payment_initiated",
                                "then": "Started",
                                "else": "Not Started",
                            }
                        },
                        "else": "$payment_info.status",
                    }
                },
                "offer_letter_sent": {
                    "$cond": {
                        "if": {"$in": ["$is_offer_letter_sent", [True]]},
                        "then": "Sent",
                        "else": "",
                    }
                },
                "lead_stage": {"$ifNull": ["$lead_details.lead_stage", "Fresh Lead"]},
                "student_verify": {
                    "$cond": {
                        "if": {"$in": ["$student_primary.is_verify", [True]]},
                        "then": "Verified",
                        "else": "Not verified",
                    }
                },
                "course_name": {
                    "$cond": {
                        "if": {
                            "$and": [
                                {"$ne": ["$spec_name1", ""]},
                                {"$ifNull": ["$spec_name1", False]}
                            ]
                        },
                        "then": {
                            "$cond": {
                                "if": {"$in": ["$course_details.course_name", ["Master", "Bachelor"]]},
                                "then": {"$concat": ["$course_details.course_name", " of ", "$spec_name1"]},
                                "else": {"$concat": ["$course_details.course_name", " in ", "$spec_name1"]}
                            }
                        },
                        "else": "$course_details.course_name"
                    }
                }
            }})
        if search:
            search_pattern = {"$regex": f".*{search}.*", "$options": "i"}
            aggregation_pipeline.append(
                {"$match": {"$or": [{"student_name": search_pattern}, {"student_email": search_pattern},
                                    {"student_mobile_number": search_pattern}]}})
        if page_num and page_size:
            aggregation_pipeline = utility_obj.get_count_aggregation(
                aggregation_pipeline, skip=skip, limit=limit
            )
        aggregation_result = await DatabaseConfiguration().studentApplicationForms.aggregate(
            aggregation_pipeline).to_list(None)
        paginated_result, total_data = [], 0
        for _id, doc in enumerate(aggregation_result):
            if _id == 0:
                try:
                    total_data = doc.get("totalCount", 0)
                except Exception:
                    total_data = 0
                break
        return {"data": aggregation_result, "total_data": total_data,
                "message": "Get give custom scholarship table data."}

    async def get_scholarship_applicants_data(
            self, college_id: str, scholarship_id: str, scholarship_data_type: str, page_num: int, page_size: int,
            filter_parameters: dict | None, download: bool, background_task: BackgroundTasks, request: Request,
            user: dict) -> dict:
        """
        Get the scholarship applicants data based on data type.

        Params:
            - college_id (str): Unique identifier of the college.
            - scholarship_id (str): A string value which represents unique identifier of scholarship.
            - A string value which represents the scholarship data type.
                Useful for get particular type of data. Possible values are eligible, availed and offered.
            - page_num (int | None): Either None or page number where want to show selection
                procedures data.
            - page_size (int | None): Either None or page size means how many data want to show on page_num.
            - filter_parameters (dict | None): Either None or a dictionary which filter parameters along with values.
            - request (Request): FastAPI request object for get ip address.
            - background_tasks (BackgroundTasks): Useful for perform tasks in the background.
            - user (dict): A dictionary which contains user information.

        Returns:
            - dict: A dictionary which contains information about scholarship applicants data based on data type.
        """
        requested_at = datetime.now(timezone.utc)
        await utility_obj.is_length_valid(scholarship_id, "Scholarship id")
        scholarship_helper_obj = Scholarship()
        scholarship_information = await scholarship_helper_obj.validate_scholarship_by_id(scholarship_id)
        common_project_stage = {
            "_id": 0,
            "application_id": {"$toString": "$_id"},
            "custom_application_id": 1,
            "student_id": {"$toString": "$student_id"},
            "student_name": {
                "$trim": {
                    "input": {
                        "$concat": [
                            "$student_primary.basic_details.first_name",
                            {
                                "$cond": [
                                    {"$in": ["$student_primary.basic_details.middle_name", ["", None]]},
                                    "",
                                    " "
                                ]
                            },
                            "$student_primary.basic_details.middle_name",
                            {
                                "$cond": [
                                    {"$in": ["$student_primary.basic_details.last_name", ["", None]]},
                                    "",
                                    " "
                                ]
                            },
                            "$student_primary.basic_details.last_name"
                        ]
                    }
                }
            },
            "course_name": {
                "$cond": {
                    "if": {
                        "$and": [
                            {"$ne": ["$spec_name1", ""]},
                            {"$ifNull": ["$spec_name1", False]}
                        ]
                    },
                    "then": {
                        "$cond": {
                            "if": {"$in": ["$course_details.course_name", ["Master", "Bachelor"]]},
                            "then": {"$concat": ["$course_details.course_name", " of ", "$spec_name1"]},
                            "else": {"$concat": ["$course_details.course_name", " in ", "$spec_name1"]}
                        }
                    },
                    "else": "$course_details.course_name"
                }
            },
            'program_fee': {
                "$let": {
                    "vars": {
                        "matched_spec": {
                            "$first": {
                                "$filter": {
                                    "input": {"$ifNull": ["$course_details.course_specialization", []]},
                                    "as": "spec",
                                    "cond": {"$eq": ["$$spec.spec_name", "$spec_name1"]}
                                }
                            }
                        }
                    },
                    "in": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$ne": ["$$matched_spec", None]},
                                    {"$ne": ["$$matched_spec.spec_fee_info", None]},
                                    {"$ne": ["$$matched_spec.spec_fee_info.registration_fee", None]}
                                ]
                            },
                            {
                                "$convert": {
                                    "input": "$$matched_spec.spec_fee_info.registration_fee",
                                    "to": "double",
                                    "onError": 0,
                                    "onNull": 0
                                }
                            },
                            0
                        ]
                    }
                }
            }
        }
        scholarship_data_type = scholarship_data_type.lower()
        scholarship_name = scholarship_information.get("name", "")
        if scholarship_data_type == "eligible":
            filter_programs_info = await scholarship_helper_obj.validate_scholarship_input_info(
                scholarship_information, is_scholarship_exists=True)
            application_ids = await ScholarshipActivity().get_eligible_applicants_info(
                programs_info=filter_programs_info,
                normal_filters=scholarship_information.get("filters", {}),
                advance_filters=scholarship_information.get("advance_filters"),
                college_id=college_id
            )
            project_stage = {
                "course_id": {"$toString": "$course_id"},
                "default_scholarship_id": "$offered_scholarship_info.default_scholarship_id",
                "spec_name": "$spec_name1",
                "payment_status": {
                    "$cond": {
                        "if": {"$in": ["$payment_info.status", ["", None]]},
                        "then": {
                            "$cond": {
                                "if": "$payment_initiated",
                                "then": "Started",
                                "else": "Not Started",
                            }
                        },
                        "else": "$payment_info.status",
                    }
                },
                "lead_stage": {"$ifNull": ["$lead_details.lead_stage", "Fresh Lead"]},
                "student_verify": {
                    "$cond": {
                        "if": {"$in": ["$student_primary.is_verify", [True]]},
                        "then": "Verified",
                        "else": "Not verified",
                    }
                },
                "scholarship_letter_count": {"$ifNull": ["$scholarship_letter_sent_count", ""]},
                "is_scholarship_letter_sent": {
                    "$cond": {
                        "if": {"$in": ["$is_scholarship_letter_sent", [True]]},
                        "then": "Sent",
                        "else": "",
                    }
                },
                "custom_scholarship_details": {
                    "custom_scholarship_applied": {
                        "$ifNull": ["$offered_scholarship_info.custom_scholarship_applied", False]},
                    "waiver_value": {
                        "$ifNull": ["$offered_scholarship_info.custom_scholarship_info.scholarship_waiver_value",
                                    None]},
                    "waiver_type": {
                        "$ifNull": ["$offered_scholarship_info.custom_scholarship_info.scholarship_waiver_type", None]},
                    "description": {
                        "$ifNull": ["$offered_scholarship_info.custom_scholarship_info.description", None]},
                },
                "scholarship_letter_info": {
                    "$map": {
                        "input": {
                            "$filter": {
                                "input": {"$ifNull": ["$offered_scholarship_info.all_scholarship_info", []]},
                                "as": "scholarship",
                                "cond": {"$and": [
                                    {"$ifNull": ["$$scholarship.template_id", False]},
                                    {"$ne": ["$$scholarship.template_id", None]}
                                ]}
                            }
                        },
                        "as": "scholarship",
                        "in": {
                            "template_id": {"$toString": "$$scholarship.template_id"},
                            "template_name": "$$scholarship.template_name",
                            "scholarship_letter_sent_on": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d %H:%M:%S",
                                    "date": "$$scholarship.scholarship_letter_sent_on",
                                    "timezone": "Asia/Kolkata"
                                }
                            },
                            "scholarship_letter_current_status": "$$scholarship.scholarship_letter_current_status"
                        }
                    }
                },
                **common_project_stage}
        else:
            if scholarship_name == "Custom scholarship":
                project_stage = {
                    "offered_scholarship_info": "$offered_scholarship_info",
                    "description": {"$ifNull": [f"$offered_scholarship_info.custom_scholarship_info.description", ""]},
                    **common_project_stage}
            else:
                project_stage = {
                    "description": {"$ifNull": [f"$offered_scholarship_info.description", ""]},
                    **common_project_stage}
            application_ids = scholarship_information.get(f"{scholarship_data_type}_applicants", [None])
        if not application_ids:
            application_ids = [None]
        application_obj = Application()
        aggregation_pipeline = await application_obj.initialize_pipeline_all_applications(
            college_id,
            None,
            None,
            application_ids=application_ids
        )
        aggregation_pipeline = await application_obj.primary_lookup_pipeline(
            pipeline=aggregation_pipeline,
            payload={}
        )
        aggregation_pipeline = await application_obj.course_pipeline(aggregation_pipeline)
        sort_type = filter_parameters.get("sort_type")
        column_name = filter_parameters.get("sort")
        programs_info = filter_parameters.get("programs")
        if scholarship_information:
            course_ids, course_specializations_list, course_names, registration_fees = \
                await scholarship_helper_obj.get_validate_programs_information(programs_info, False)
            aggregation_pipeline = await application_obj.apply_course_filter(
                aggregation_pipeline,
                {"course": {"course_id": course_ids, "course_specialization": course_specializations_list}})
        aggregation_pipeline.append({"$project": project_stage})

        if scholarship_data_type != "eligible":
            if scholarship_name == "Custom scholarship":
                field_name = "$offered_scholarship_info.custom_scholarship_info"
                waiver_type = f"{field_name}.scholarship_waiver_type"
                waiver_value = f"{field_name}.scholarship_waiver_value"
            else:
                waiver_type = scholarship_information.get("waiver_type")
                waiver_value = scholarship_information.get("waiver_value", 0)
            aggregation_pipeline.append({"$addFields": {"fees_after_waiver":
                {
                    "$cond": {
                        "if": {"$in": [waiver_type, ["Amount"]]},
                        "then": waiver_value,
                        "else": {
                            "$round": [
                                {
                                    "$multiply": [
                                        {"$divide": [
                                            waiver_value,
                                            100]},
                                        "$program_fee"
                                    ]
                                },
                                2
                            ]
                        }
                    }
                },
                "percentage": {
                    "$cond": {
                        "if": {"$in": [waiver_type, ["Percentage"]]},
                        "then": waiver_value,
                        "else": {
                            "$round": [
                                {
                                    "$multiply": [
                                        {"$divide": [waiver_value,
                                                     "$program_fee"]},
                                        100
                                    ]
                                },
                                2
                            ]
                        }
                    }
                }}})
        search = filter_parameters.get("search")
        if search:
            aggregation_pipeline.append(
                {"$match": {"student_name": {"$regex": f".*{search}.*", "$options": "i"}}}
            )
        if sort_type and column_name:
            sort_order = 1 if sort_type == "asc" else -1
            aggregation_pipeline.append({"$sort": {column_name: sort_order}})
        if page_num and page_size:
            skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
            aggregation_pipeline = utility_obj.get_count_aggregation(
                aggregation_pipeline, skip=skip, limit=limit
            )
        aggregation_result = await DatabaseConfiguration().studentApplicationForms.aggregate(
            aggregation_pipeline).to_list(None)
        total_data = 0
        for _id, doc in enumerate(aggregation_result):
            if _id == 0:
                try:
                    total_data = doc.get("totalCount", 0)
                except Exception:
                    total_data = 0
            if scholarship_data_type == "eligible":
                course_id = ObjectId(doc.pop("course_id", None))
                spec_name = doc.pop("spec_name", None)
                doc.pop("course_specializations", None)
                doc["scholarship_details"], doc["default_scholarship_name"], default_scholarship_amount = \
                    await scholarship_helper_obj.get_scholarship_details(
                        ObjectId(doc.get("application_id")), course_id, spec_name,
                        doc.get("program_fee", 0), college_id,
                        {"course_id": [course_id], "course_specialization": [spec_name]},
                        doc.pop("default_scholarship_id", None))
            elif scholarship_data_type != "eligible" and scholarship_name == "Custom scholarship":
                doc.pop("offered_scholarship_info", None)
        if download:
            if aggregation_result:
                background_task.add_task(
                    DownloadRequestActivity().store_download_request_activity,
                    request_type=f"Scholarship {scholarship_data_type} data",
                    requested_at=requested_at,
                    ip_address=utility_obj.get_ip_address(request),
                    user=user,
                    total_request_data=len(aggregation_result),
                    is_status_completed=True,
                    request_completed_at=datetime.now(timezone.utc),
                )
                return await upload_csv_and_get_public_url(
                    fieldnames=list(aggregation_result[0].keys()),
                    data=aggregation_result,
                    name="applications_data"
                )
            return {"message": "No data to download."}
        return {"data": aggregation_result, "total_data": total_data,
                "message": "Get applicants data."}
