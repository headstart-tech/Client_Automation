"""
This file contain class and functions related to student application
"""
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import PurePath

from bson import ObjectId
from fastapi import Request, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException

from app.background_task.doc_text_extraction import DocExtraction
from app.background_task.send_mail_configuration import EmailActivity
from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.custom_error import DataNotFoundError, CustomError
from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, settings
from app.database.aggregation.get_all_applications import Application
from app.database.aggregation.planner import PlannerAggregation
from app.database.aggregation.student import Student
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache, \
    cache_invalidation, is_testing_env
from app.helpers.student_curd.student_user_crud_configuration import (
    StudentUserCrudHelper,
)
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.serialize import StudentCourse
from app.models.student_user_schema import User

logger = get_logger(name=__name__)


class StudentApplicationHelper:
    """
    Contain functions related to student application configuration
    """

    async def get_application_data(self, application_id):
        """
        Helper function to fetch the application data from the database based
        on id.

        Params:
            application_id (str): An unique identifier/id of application.

        Returns:
            dict: A dictionary which contains application data.
        """
        await utility_obj.is_id_length_valid(application_id, "Application id")
        if (
                application := await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"_id": ObjectId(application_id)}
                )
        ) is None:
            raise HTTPException(status_code=404, detail="Application not found.")
        return application

    async def update_stage(self, student_id: str, course_name: str,
                           minimum: float, spec_name: str | None = None,
                           upload_files: bool | None = False, college_id=None) -> bool:
        """
        Update stage and progress bar when application stage completed
        """
        if (
                find_course := await DatabaseConfiguration().
                        course_collection.find_one(
                    {"course_name": course_name}
                )
        ) is None:
            raise HTTPException(status_code=404,
                                detail="course not found.")
        if spec_name:
            if (
                    find_app := await DatabaseConfiguration().studentApplicationForms.find_one(
                        {"student_id": ObjectId(student_id),
                         "course_id": ObjectId(find_course.get("_id")),
                         "spec_name1": spec_name}
                    )
            ) is None:
                find_app = await StudentUserCrudHelper().update_special_course(
                    student_id, find_course["course_specialization"],
                    course_name, college_id=college_id
                )
            if minimum > find_app.get("current_stage"):
                if (
                        await DatabaseConfiguration().studentApplicationForms.
                                update_one(
                            {"_id": ObjectId(find_app["_id"])},
                            {"$set": {"current_stage": minimum}}
                        )
                        is not None
                ):
                    return True
                raise HTTPException(status_code=422, detail="stage not update")
            return False
        else:
            applications_information = await (DatabaseConfiguration().
                                              studentApplicationForms.find(
                {"student_id": ObjectId(student_id)}).to_list(length=None))
            update_document = False
            for application_document in applications_information:
                if minimum > application_document.get("current_stage") \
                        if not upload_files else (application_document.get("current_stage") == 7.50
                                                  and minimum > application_document.get("current_stage")):
                    if (
                            await DatabaseConfiguration().
                                    studentApplicationForms.update_one(
                                {"_id": ObjectId(
                                    application_document.get("_id"))},
                                {"$set": {"current_stage": minimum}}
                            )
                            is not None
                    ):
                        update_document = True
            if update_document:
                return True
            return False

    def student_application_helper(self, item):
        """
        Get student application details
        """
        return {
            "id": str(item.get("_id")),
            "student_id": str(item.get("student_id")),
            "course_id": str(item.get("course_id")),
            "custom_application_id": item.get("custom_application_id"),
            "spec_name1": item.get("spec_name1", ""),
            "spec_name2": item.get("spec_name2", ""),
            "spec_name3": item.get("spec_name3", ""),
            "payment_initiated": item.get("payment_initiated"),
            "payment_info": item.get("payment_info"),
            "payment_id": item.get("payment_info.payment_id"),
            "payment_status": item.get("payment_info.status"),
            "current_stage": item.get("current_stage"),
            "declaration": item.get("declaration"),
            "enquiry_date": utility_obj.get_local_time(item.get("enquiry_date")),
            "last_updated_time": utility_obj.get_local_time(
                item.get("last_updated_time")
            ),
            "interview_details": item.get("interview_details"),
            "meetingDetails": item.get("meetingDetails"),
            "application_download_url": item.get("application_download_url"),
            "dv_status": item.get("dv_status"),
            "preference_info": item.get("preference_info", [])
        }

    def application_details_helper(self, data):
        """
        Get all application details
        """
        return {
            "application_id": str(data.get("_id")),
            "student_id": str(data.get("student_id")),
            "student_name": utility_obj.name_can(data.get("student_basic_details")),
            "custom_application_id": data.get("custom_application_id"),
            "course_name": (
                f"{data.get('course_name')} in {data.get('course_spec')}"
                if (data.get("course_spec") != "" and data.get("course_spec"))
                else f"{data.get('course_name')} Program"
            ),
            "student_email_id": data.get("student_email_id"),
            "student_mobile_no": data.get("student_mobile_no"),
            "application_status": data.get("application_status"),
            "payment_status": data.get("payment_status"),
            "application_stage": data.get("application_stage"),
            "course_fees": data.get("course_fees"),
            "submitted_on": str(data.get("submitted_on")),
            "state_name": data.get("state_name"),
            "city_name": data.get("city_name"),
            "lead_type": data.get("lead_type"),
        }

    def file_helper(self, item: dict, student_id: str, season=None) -> dict:
        """
        Get student attached document details.

        Params:
            item (dict): A dict which contains student secondary details.
            student_id (str): Unique id of student
        Returns:
             dict: A dictionary which contains student documents details along with id.
        """
        season = utility_obj.get_year_based_on_season(season)
        data = item.get("attachments", {})
        aws_env = settings.aws_env
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        base_bucket_url = getattr(settings, f"s3_{aws_env}_base_bucket_url")
        for key in data:
            if data[key].get("file_s3_url", ""):
                if not data[key].get("file_s3_url", "").startswith("https"):
                    data[key]["file_s3_url"] = (
                        f"{base_bucket_url}{utility_obj.get_university_name_s3_folder()}/{season}/{settings.s3_student_documents_bucket_name}/"
                        f'{student_id}/{key}/{data[key]["file_s3_url"]}'
                    )
                data[key]["file_s3_url"] = settings.s3_client.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": base_bucket,
                        "Key": f"{utility_obj.get_university_name_s3_folder()}/{season}/{settings.s3_student_documents_bucket_name}/{student_id}/"
                               f"{key}/{data[key]['file_s3_url'].split('/')[8]}",
                    },
                    ExpiresIn=600,
                )
            comments = data[key].get("comments", [])
            if comments:
                data[key]["comments"] = [
                    {
                        "message": comment.get("message"),
                        "timestamp": utility_obj.get_local_time(
                            comment.get("timestamp", datetime.now(timezone.utc))
                        ),
                        "user_name": comment.get("user_name"),
                        "user_id": str(comment.get("user_id")),
                        "comment_id": _id,
                    }
                    for _id, comment in enumerate(comments)
                ]
        return {
            "id": str(item.get("_id")),
            "student_id": str(item.get("student_id")),
            "attachments": data,
        }

    async def get_data(self, all_applicants, column_names=None, user=None) -> list:
        """
        Get data set for the CSV file creation

        Args:
            all_applicants (_type_): Valid unique id of all Applicant students
            column_names (_type_, optional): Name of column which is inserted in csv file. Defaults to None.
            user (_type_, optional): Current requested user. Defaults to None.

        Returns:
            list: List of data set of all applicants student
        """

        lst = []
        for applicant in all_applicants:
            application = (
                await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"_id": ObjectId(applicant.get("id"))}
                )
            )
            if (
                    student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                        {"_id": ObjectId(application.get("student_id"))}
                    )
            ) is None:
                continue
            if (
                    secondary_details := await DatabaseConfiguration().studentSecondaryDetails.find_one(
                        {"student_id": student.get("_id")}
                    )
            ) is None:
                secondary_details = {}
            payment = (
                "success"
                if application.get("payment_info", {}).get("status") == "captured"
                else "pending"
            )
            if (
                    course := await DatabaseConfiguration().course_collection.find_one(
                        {"_id": ObjectId(application.get("course_id"))}
                    )
            ) is not None:
                if (
                        lead_followup := await DatabaseConfiguration().leadsFollowUp.find_one(
                            {"application_id": ObjectId(application.get("_id"))}
                        )
                ) is None:
                    lead_followup = {}
                dummy_dict = {
                    "student_id": application.get("student_id"),
                    "student_name": utility_obj.name_can(student.get("basic_details")),
                    "application_id": application.get("_id"),
                    "custom_application_id": application.get("custom_application_id"),
                    "course_name": (
                        f"{course.get('course_name')}"
                        f" in {application.get('spec_name1')}"
                        if application.get("spec_name1") != ""
                        else f"{course.get('course_name')} Program"
                    ),
                    "student_email_id": student.get("user_name"),
                    "student_mobile_no": student.get("basic_details", {}).get(
                        "mobile_number"
                    ),
                    "verification": await Student().get_lead_verification_info(
                        {
                            "student_verify": student.get("is_verify"),
                            "student_mobile_verify": student.get("is_mobile_verify"),
                            "student_email_verify": student.get("is_email_verify"),
                            "declaration": application.get("declaration"),
                            "dv_status": application.get("dv_status", "Not Verified"),
                        },
                        applications=True,
                    ),
                    "payment_status": payment,
                    "lead_stage": (
                        lead_followup.get("lead_stage", None) if lead_followup else None
                    ),
                    "automation": "0",
                    "extra_fields": student.get("extra_fields", {}),
                }
                if user.get("role", {}).get("role_name") == "college_publisher_console":
                    stage_count = application.get("current_stage")
                    stage_count = float(stage_count) * 10
                    stage_lst = str(stage_count) + "%"
                    dummy_dict.update(
                        {
                            "application_status": (
                                "completed"
                                if application.get("declaration") is True
                                else "In progress"
                            ),
                            "application_stage": stage_lst,
                            "course_fees": course.get("fees"),
                            "submitted_on": utility_obj.get_local_time(
                                application.get("enquiry_date")
                            ),
                        }
                    )
                if column_names:
                    if "12th marks" in column_names:
                        dummy_dict.update(
                            {
                                "twelve_marks": secondary_details.get(
                                    "education_details", {}
                                )
                                .get("inter_school_details", {})
                                .get("obtained_cgpa")
                            }
                        )

                    if "12th board" in column_names:
                        dummy_dict.update(
                            {
                                "twelve_board": secondary_details.get(
                                    "education_details", {}
                                )
                                .get("inter_school_details", {})
                                .get("board")
                            }
                        )

                    if "registration date" in column_names:
                        dummy_dict.update(
                            {
                                "registration date": utility_obj.get_local_time(
                                    application.get("enquiry_date")
                                )
                            }
                        )

                    if "lead sub stage" in column_names:
                        dummy_dict.update(
                            {
                                "lead sub stage": lead_followup.get(
                                    "lead_stage_label", None
                                )
                            }
                        )

                    if "verification status" in column_names:
                        dummy_dict.update(
                            {
                                "verification status": (
                                    "verified"
                                    if student.get("is_verify")
                                    else "unverified"
                                )
                            }
                        )

                    if "outbound calls count" in column_names:
                        dummy_dict.update(
                            {
                                "outbound calls count": await DatabaseConfiguration().call_activity_collection.count_documents(
                                    {
                                        "type": "Outbound",
                                        "call_from": student.get(
                                            "basic_details", {}
                                        ).get("mobile_number", ""),
                                    }
                                )
                            }
                        )

                    if "city" in column_names:
                        dummy_dict.update({"city": student.get("address_details", {}).get("communication_address", {})
                                          .get("city", {})
                                          .get("city_name")})
                    if "state" in column_names:
                        dummy_dict.update({"state": student.get("address_details", {})
                                          .get("communication_address", {})
                                          .get("state", {})
                                          .get("state_name")})
                    if "application date" in column_names:
                        dummy_dict.update(
                            {
                                "submitted_on": utility_obj.get_local_time(
                                    application.get("enquiry_date")
                                )
                            }
                        )
                    if "application stage" in column_names:
                        dummy_dict.update(
                            {
                                "application_status": (
                                    "completed"
                                    if application.get("declaration") is True
                                    else "In progress"
                                )
                            }
                        )
                    if "source" in column_names:
                        lead = (
                            await (
                                DatabaseConfiguration().studentsPrimaryDetails.find_one(
                                    {"_id": ObjectId(application.get("student_id"))}
                                )
                            )
                        )
                        lead_source = "NA"
                        if lead:
                            lead_source = (
                                lead.get("source", {})
                                .get("primary_source", {})
                                .get("utm_source")
                            )
                        dummy_dict.update({"lead_source": lead_source})
                    if "lead type" in column_names:
                        lead = (
                            await (
                                DatabaseConfiguration().studentsPrimaryDetails.find_one(
                                    {"_id": ObjectId(application.get("student_id"))}
                                )
                            )
                        )
                        lead_type = "NA"
                        if lead:
                            lead_type = (
                                lead.get("source", {})
                                .get("primary_source", {})
                                .get("lead_type")
                            )
                        dummy_dict.update({"lead_type": lead_type})
                    if "lead stage" in column_names:
                        lead = await DatabaseConfiguration().leadsFollowUp.find_one(
                            {"student_id": ObjectId(application.get("student_id"))}
                        )
                        lead_stage = "fresh lead"
                        if lead:
                            lead_stage = lead.get("lead_stage")
                        dummy_dict.update({"lead_stage": lead_stage})
                    if "counselor name" in column_names:
                        dummy_dict.update(
                            {
                                "counselor_name": application.get(
                                    "allocate_to_counselor", {}
                                ).get("counselor_name")
                            }
                        )
                    if "twelve board" in column_names:
                        dummy_dict.update(
                            {
                                "twelve_board": secondary_details.get(
                                    "education_details", {}
                                )
                                .get("inter_school_details", {})
                                .get("board")
                            }
                        )
                    if "form filling stage" in column_names:
                        form_fill = []
                        if (
                                secondary_details.get("education_details", {}).get(
                                    "tenth_school_details"
                                )
                                is not None
                        ):
                            form_fill.append("10th")
                        if (
                                secondary_details.get("education_details", {})
                                        .get("inter_school_details", {})
                                        .get("is_pursuing")
                                is False
                        ):
                            form_fill.append("12th")
                        if application.get("declaration") is True:
                            form_fill.append("Declaration")
                        dummy_dict.update({"form_filling_stage": form_fill})
                    if "source type" in column_names:
                        source_type = []
                        source_details = student.get("source", {})
                        if (
                                source_details.get("primary_details") is not None
                                or source_details.get("primary_details") is None
                        ):
                            source_type.append("Primary")
                        for item in ["secondary_details", "tertiary_details"]:
                            if source_details.get(item):
                                source_type.append((item.split("_")[0]).title())
                        dummy_dict.update({"source_type": source_type})
                    if "outbound call" in column_names:
                        outbound_call = await DatabaseConfiguration().call_activity_collection.count_documents(
                            {
                                "type": "Inbound",
                                "call_from": str(dummy_dict.get("student_mobile_no")),
                            }
                        )
                        dummy_dict.update({"outbound_call": outbound_call})
                    if "utm medium" in column_names:
                        lead = (
                            await (
                                DatabaseConfiguration().studentsPrimaryDetails.find_one(
                                    {"_id": ObjectId(application.get("student_id"))}
                                )
                            )
                        )
                        utm_medium = "NA"
                        if lead:
                            utm_medium = (
                                lead.get("source", {})
                                .get("primary_source", {})
                                .get("utm_medium")
                            )
                        dummy_dict.update({"utm_medium": utm_medium})
                    if "utm campaign" in column_names:
                        lead = (
                            await (
                                DatabaseConfiguration().studentsPrimaryDetails.find_one(
                                    {"_id": ObjectId(application.get("student_id"))}
                                )
                            )
                        )
                        utm_campaign = "NA"
                        if lead:
                            utm_campaign = (
                                lead.get("source", {})
                                .get("primary_source", {})
                                .get("utm_campaign")
                            )
                        dummy_dict.update({"utm_campaign": utm_campaign})
                lst.append(dummy_dict)
        return lst

    async def get_all_application(
            self,
            payload,
            page_num=None,
            page_size=None,
            college_id=None,
            counselor_id=None,
            applications=True,
            source_name=None,
            publisher=False,
            form_initiated=True,
            twelve_score_sort=None,
            is_head_counselor=False
    ):
        """
        get all application
        id , stage, submit dates
        course fees
        """
        if payload is None:
            payload = {}
        start_date = end_date = None
        if payload.get("date_range") not in [{}, None]:
            date_range = payload.pop("date_range", {})
            start_date, end_date = await self.get_start_end_dates(date_range)
        all_applicant, total = await Application().all_applications(
            payload=payload,
            college_id=college_id,
            page_num=page_num,
            page_size=page_size,
            start_date=start_date,
            end_date=end_date,
            counselor_id=counselor_id,
            applications=applications,
            source_name=source_name,
            publisher=publisher,
            form_initiated=form_initiated,
            twelve_score_sort=twelve_score_sort,
            is_head_counselor=is_head_counselor
        )
        name = "applications" if applications else "leads"
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, total, route_name=f"/admin/all_{name}/"
        )
        return {
            "data": all_applicant,
            "total": total,
            "count": page_size,
            "pagination": response["pagination"],
            "message": f"{name.title()} data fetched successfully!",
        }

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

    async def calculate_application_fee(
            self, preferences: list[str], fee_rules: dict,
            course_name: str) -> tuple:
        """
        Calculate the fee based on preferences.

        Params:
            - preferences (list[str]): A list which contains preferences
                information. like ["Preference1", "Preference2"]
            - fee_rules: A dictionary which contains fee rules.
            - course_name (str): Name of a course which useful for get course
                specialization fee.

        Returns:
            - tuple: A tuple value which represent total fee of application and
                one preference fee.
        """
        base_fees = fee_rules.get("base_fees", {})
        additional_fees = fee_rules.get("additional_fees", [])
        fee_cap = fee_rules.get("fee_cap")
        total_fee = 0
        number_of_specializations = len(preferences)

        # Calculate base fees
        for _id, preference_name in enumerate(preferences):
            if preference_name in [None, '']:
                preference_name = 'null'
            if _id == 0:
                total_fee += base_fees.get(course_name, {}).get(preference_name, 0)
                break

        # Apply additional fees based on dynamic rules
        preference_fee = 0
        for rule in additional_fees:
            if number_of_specializations <= rule.get("trigger_count", 0):
                preference_fee += rule.get("amount", 0)
                total_fee += (number_of_specializations - 1) * rule.get("amount", 0)
                break

        # Apply fee cap if applicable
        if fee_cap and total_fee > fee_cap:
            total_fee = fee_cap
        return total_fee, preference_fee

    async def get_detail_of_student_application(
            self, _id: str, page_num=None, page_size=None, route_name=None, season=None,
            system_preference: None | dict = None,
            fee_rules: None | dict = None
    ):
        """
        Get details of student application
        """
        if (
                all_application := await DatabaseConfiguration().studentApplicationForms.aggregate(
                    [{"$match": {"student_id": ObjectId(_id)}}]
                ).to_list(length=None)
        ) is None:
            raise HTTPException(status_code=404, detail="Application not found")
        await DatabaseConfiguration().studentApplicationForms.count_documents({})
        application = [
            self.student_application_helper(i)
            for i in all_application
        ]
        if page_num and page_size:
            application_length = len(application)
            response = await utility_obj.pagination_in_api(
                page_num, page_size, application, application_length, route_name
            )
            application = response["data"]
        data = []
        for i in range(len(application)):
            if (
                    course := await DatabaseConfiguration().course_collection.find_one(
                        {"_id": ObjectId(application[i]["course_id"])}
                    )
            ) is None:
                raise HTTPException(status_code=404, detail="course not found.")
            if (
                    student_app := await DatabaseConfiguration().studentSecondaryDetails.find_one(
                        {"student_id": ObjectId(_id)}
                    )
            ) is None:
                student_app = {}
            re_upload_documents = False
            document_analysis = student_app.get("document_analysis")
            if document_analysis and isinstance(document_analysis, dict):
                for item in document_analysis.values():
                    if isinstance(item, dict) and item.get("count") >= 1:
                        re_upload_documents = True
                        break
            is_pursuing = (
                student_app.get("education_details", {})
                .get("inter_school_details", {})
                .get("is_pursuing")
            )
            if course.get("is_pg") is True:
                is_pursuing = (
                    student_app.get("education_details", {})
                    .get("graduation_details", {})
                    .get("is_pursuing")
                )
            is_pursuing_diploma = (
                student_app.get("education_details", {})
                .get("diploma_academic_details", {})
                .get("is_pursuing")
            )
            spec_name = application[i].get("spec_name1")
            short_spec_name = await StudentUserCrudHelper().get_short_form_of_spec_name(
                spec_name
            )
            paid_amount = None
            payment_info = application[i].get("payment_info", {})
            payment_method = payment_info.get("payment_method", "")
            if payment_method == "Promocode":
                paid_amount = payment_info.get("paid_amount", None)
            payment_status = application[i].get("payment_info", {}).get("status")
            detailed_status = (
                "Completed"
                if application[i]["declaration"] is True
                else "In progress"
            )
            course_name = course.get("course_name")
            d = {
                "application_id": application[i]["id"],
                "custom_application_id": application[i].get("custom_application_id"),
                "application_payment_status": payment_status,
                "course_name": course_name,
                "specialization_name": spec_name,
                "short_form_spec_name": short_spec_name,
                "course_id": application[i]["course_id"],
                "application_stage": str(float(application[i]["current_stage"]) * 10)
                                     + "%",
                "course_fees": course.get("fees"),
                "paid_amount": paid_amount,
                "is_pursuing": is_pursuing,
                "is_pursuing_diploma": is_pursuing_diploma,
                "applied_on": application[i]["enquiry_date"],
                "submitted_on": application[i]["last_updated_time"],
                "status": detailed_status,
                "application_url": application[i].get("application_download_url")
            }
            interview_info = application[i].get("meetingDetails", {})
            d = await self.update_data_based_on_interview_status(interview_info, d)
            d = await self.update_failed_documents_info(
                ObjectId(_id),
                d,
                application[i]["application_download_url"],
                season=season,
            )
            if d.get("is_document_failed"):
                detailed_status = "Re-upload document"
            elif application[i].get("current_stage") == 8.75:
                detailed_status = "Document submitted"
            elif detailed_status != "Completed" and payment_status == "captured":
                detailed_status = "Application fee paid"
            d["detailed_status"] = detailed_status
            if system_preference and isinstance(system_preference, dict):
                if system_preference.get("preference"):
                    preference_info = []
                    temp_preference_info = application[i].get("preference_info", [])
                    if temp_preference_info:
                        total_fee, preference_fee = await self.calculate_application_fee(temp_preference_info,
                                                                                         fee_rules, course_name)
                        d["course_fees"] = f"Rs.{total_fee}/-"
                        preference_info = [
                            {"specialization_name": preference,
                             "course_fees": f"Rs.{fee_rules.get('base_fees', {}).get(course_name, {}).get(preference, 0)}/-"}
                            if preference_id == 0
                            else {"specialization_name": preference,
                                  "course_fees": f"Rs.{preference_fee}/-"}
                            for preference_id, preference in enumerate(
                                temp_preference_info)]
                    d["preference_info"] = preference_info
            data.append(d)

        if data:
            if page_num and page_size:
                return {
                    "data": data,
                    "total": response["total"],
                    "count": page_size,
                    "pagination": response["pagination"],
                    "message": "Applications data fetched successfully.",
                }
            return data
        return False

    async def form_status(self, _id: str, short: bool, application: dict, course: dict):
        """
        Update form status of student application
        """
        if application["payment_info"]["status"] == "captured":
            if (
                    await DatabaseConfiguration().studentApplicationForms.update_one(
                        {"_id": ObjectId(str(application.get("_id")))},
                        {
                            "$set": {
                                "declaration": short,
                                "last_updated_time": datetime.now(timezone.utc),
                            }
                        },
                    )
                    is not None
            ):
                await DatabaseConfiguration().studentsPrimaryDetails.update_one({
                    "_id": ObjectId(application.get("student_id"))},
                    {
                        "$set": {"last_accessed": datetime.now(timezone.utc)}
                    }
                )
                await self.update_stage(
                    _id, course.get("course_name"), 10,
                    application.get("spec_name1"), college_id=str(application.get("college_id")))
                return True
        raise HTTPException(status_code=422, detail="payment has pending")

    async def check_form_status_of_student(self, _id: str, application_id: str):
        """
        Check form status of student application
        """
        if (
                student_app := await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"_id": ObjectId(application_id), "student_id": ObjectId(_id)}
                )
        ) is None:
            raise HTTPException(status_code=404, detail="Application not found")
        if student_app["declaration"] is True:
            return True
        return False

    async def get_application_stage_name_by_value(
            self, application_stage_value: float
    ) -> str | None:
        """
        Get the application stage name based on application stage value.

        Params:
            application_stage_value (float): Value of application stage in float
                format. e.g., 25

        Returns:
            stage_name (str): Application stage name.
        """
        stage_name = None
        if application_stage_value <= 50:
            stage_name = "Basic Details"
        elif application_stage_value <= 62.5:
            stage_name = "Educational Details"
        elif application_stage_value <= 75:
            stage_name = "Payment"
        elif application_stage_value <= 87.5:
            stage_name = "Documentation"
        elif application_stage_value <= 100:
            stage_name = "Application Submitted"
        return stage_name

    async def update_data_based_on_interview_status(
            self, interview_info: dict | None, data: dict,
            preference_info: list | None = None
    ) -> dict:
        """
        Update data dictionary when interview details are available.

        Params:
            interview_info (dict | None): Either None or a dictionary which
                contains interview info.
            data (dict): A dictionary which can be modified when
                interview data present.

        Returns:
            dict: A dictionary which can contains interview data when
                interview data present.
        """
        spec_name, temp_data = None, {}
        if interview_info:
            interview_status = interview_info.get("status")
            interview_status_in_lower = interview_status.lower()
            today = datetime.now(timezone.utc)
            interview_date = interview_info.get(
                f"{interview_status_in_lower}_date", today
            )
            interview_duration = interview_info.get("duration", 0)
            if preference_info:
                if (
                        slot := await DatabaseConfiguration().slot_collection.find_one(
                            {"_id": interview_info.get("slot_id")})) is None:
                    slot = {}
                if (
                        interview_list := await DatabaseConfiguration().interview_list_collection.find_one(
                            {"_id": slot.get("interview_list_id")})) is None:
                    interview_list = {}
                spec_name = interview_list.get("specialization_name")
            if interview_status == "Scheduled":
                if interview_duration:
                    interview_date = interview_date + timedelta(
                        minutes=interview_duration
                    )
                if today <= interview_date:
                    temp_data.update(
                        {
                            "interview_time_remaining": (
                                                                interview_date - today
                                                        ).total_seconds()
                                                        * 1000
                        }
                    )
                temp_data.update({"zoom_link": interview_info.get("zoom_link")})
            temp_data.update({
                "interview_status": interview_status,
                f"interview_{interview_status_in_lower}_on": utility_obj.get_local_time(
                    interview_info.get(f"{interview_status_in_lower}" f"_date"),
                    season=True,
                    hour_minute=True
                ),
                "interview_end_on": utility_obj.get_local_time(
                    interview_info.get("scheduled_date", datetime.now(timezone.utc)) + timedelta(minutes=interview_duration),
                    season=True,
                    hour_minute=True)
            })
            if not preference_info:
                data.update(temp_data)
        if preference_info:
            data["preferenceDetailsInfo"] = [{**temp_data,
                                              "specialization_name": pref_info} if spec_name == pref_info else {
                "specialization_name": pref_info} for pref_info in
                                             preference_info]
        return data

    async def all_course_status(
            self,
            _id: str,
            college_id: str | None = None,
            page_num: int | None = None,
            page_size: int | None = None,
            route_name: str | None = None,
            season=None
    ):
        """
        Get student applications data with respect to college.

        Params:
            _id (str): An unique id of current logged in student.
                e.g., 123456789012345678901234
            page_num (int | None): Either None or the page number where want
                to show application data. Useful for pagination.
                e.g., 1 or None
            page_size (int | None): Either None or the number of records per
                page. Useful for pagination.. e.g., 25 or None
            college (str): An unique id of college.
                e.g., 123456789012345678901211
            route_name (str): Name of a route.
                e.g., "/student_application/get_all_course_of_current_user".
                Useful for pagination.
        Returns:
            dict: Student applications data with respect to college.
        """

        # Get the count of all applications
        total_applications = (
            await DatabaseConfiguration().studentApplicationForms.count_documents({})
        )

        # Get student applied applications data
        applied_course = [
            self.student_application_helper(i)
            for i in await DatabaseConfiguration()
            .studentApplicationForms.aggregate([{"$match": {"student_id": ObjectId(_id)}}])
            .to_list(length=total_applications)
        ]

        # Perform pagination on student applied applications data if send
        # page number and page size
        if page_num and page_size:
            application_length = len(applied_course)
            response = await utility_obj.pagination_in_api(
                page_num, page_size, applied_course, application_length, route_name
            )
            applied_course = response.get("data")

        # Store all applied application course id in a list format
        lst_of_applied = [i.get("course_id") for i in applied_course]

        # Get the count of all courses
        total_courses = await DatabaseConfiguration().course_collection.count_documents(
            {}
        )

        # Get the all courses of college
        all_courses = await DatabaseConfiguration().course_collection.aggregate(
            [{"$match": {"college_id": ObjectId(college_id)}}]
        ).to_list(length=None)
        all_course = [
            StudentCourse().course_serialize(i)
            for i in all_courses
        ]
        # Raising error when course not found for college
        if len(all_course) < 1:
            raise HTTPException(status_code=404, detail="college not found")

        final, course_length, course_response = [], 0, {}

        # Perform pagination on student applied applications data if send
        # page number and page size
        if page_num and page_size:
            course_length = len(all_course)
            course_response = await utility_obj.pagination_in_api(
                page_num, page_size, all_course, course_length, route_name
            )
            all_course = course_response.get("data")

        # Get applications data in a respective format
        for course_info in all_course:
            course_id = course_info.get("id")
            data = {
                "course_id": course_id,
                "course_name": course_info.get("course_name"),
                "college_id": college_id,
            }
            if course_id in lst_of_applied:
                for j in applied_course:
                    if j.get("course_id") == course_id:
                        application = {"info": j}
                        application_info = application.get("info", {})
                        application_stage_value = (
                                float(application_info.get("current_stage", 0)) * 10
                        )

                        stage_name = await self.get_application_stage_name_by_value(
                            application_stage_value
                        )
                        spec_name = application_info.get("spec_name1")
                        short_spec_name = (
                            await StudentUserCrudHelper().get_short_form_of_spec_name(spec_name)
                        )
                        app_id = application_info.get("id")
                        temp_dict = data.copy()
                        show_book_interview = await PlannerAggregation().check_slots_available(
                            app_id)
                        declaration = application_info.get("declaration")
                        temp_dict.update(
                            {
                                "specialization_name": spec_name,
                                "short_form_spec_name": short_spec_name,
                                "applied_on": application_info.get("enquiry_date"),
                                "status": (
                                    "Completed"
                                    if declaration
                                    else "In progress"
                                ),
                                "application_stage": application_stage_value,
                                "custom_application_id": application_info.get(
                                    "custom_application_id"
                                ),
                                "application_id": app_id,
                                "stage_name": stage_name,
                                "show_book_interview": True if show_book_interview and declaration else False
                            }
                        )
                        interview_info = application_info.get("meetingDetails", {})
                        temp_dict = await self.update_data_based_on_interview_status(
                            interview_info, temp_dict, application_info.get("preference_info")
                        )
                        temp_dict = await self.update_failed_documents_info(
                            ObjectId(_id),
                            temp_dict,
                            application_info.get("application_download_url"),
                            season=season,
                        )
                        final.append(temp_dict)
            else:
                data.update(
                    {
                        "specialization_name": "",
                        "short_form_spec_name": "",
                        "applied_on": "",
                        "status": "NA",
                        "application_stage": "",
                        "custom_application_id": "",
                        "application_id": "",
                    }
                )
                final.append(data)

        # Return respective format data if send page number and page size
        if page_num and page_size:
            return {
                "data": final,
                "total": course_length,
                "count": page_size,
                "pagination": course_response.get("pagination"),
                "message": "Student applications data found.",
            }

        return final

    async def failed_document_helper(
            self, document_name, document_info, app_download_url, student_id, season=None
    ):
        season_year = utility_obj.get_year_based_on_season(season)
        file_s3_url = document_info.get("file_s3_url", "")
        if document_name == "application":
            document_info["file_s3_url"] = app_download_url
        aws_env = settings.aws_env
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        base_bucket_url = getattr(settings, f"s3_{aws_env}_base_bucket_url")
        if file_s3_url:
            if not file_s3_url.startswith("https"):
                document_info["file_s3_url"] = (
                    f"{base_bucket_url}{utility_obj.get_university_name_s3_folder()}/{season_year}/{settings.s3_student_documents_bucket_name}/"
                    f'{student_id}/{document_name}/{document_info["file_s3_url"]}'
                )
            s3_client = settings.s3_client
            document_info["file_s3_url"] = s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": base_bucket,
                    "Key": f"{utility_obj.get_university_name_s3_folder()}/{season_year}/{settings.s3_student_documents_bucket_name}/{student_id}/"
                           f"{document_name}/{document_info['file_s3_url'].split('/')[8]}",
                },
                ExpiresIn=1200,
            )
        comments = document_info.get("comments", [])
        return {
            "document_name": document_name,
            "file_name": document_info.get("file_name"),
            "file_s3_url": document_info.get("file_s3_url"),
            "rejection_reason": comments[0]["message"] if comments else "NA",
        }

    async def update_failed_documents_info(
            self, student_id: ObjectId, result_dict: dict, app_download_url, season=None
    ) -> dict:
        """
        Update failed documents info in the result

        Params:
            student_id (ObjectId): A unique id of a student.
                e.g., ObjectId("123456789012345678901234")
            result_dict (dict): A dictionary which will be modified based on
                failed documents.

        Returns:
            result_dict (dict): Final resultant dictionary will be returned.
        """
        is_document_failed, failed_documents, failed_document_count = False, [], 0
        student_secondary_data = (
            await DatabaseConfiguration().studentSecondaryDetails.find_one(
                {"student_id": student_id}
            )
        )
        if student_secondary_data:
            dv_status_values = [
                await self.failed_document_helper(
                    document_name,
                    document_info,
                    app_download_url,
                    student_id,
                    season=season,
                )
                for document_name, document_info in student_secondary_data.get(
                    "attachments", {}
                ).items()
                if document_info.get("status") == "Rejected"
            ]
            if len(dv_status_values) >= 1:
                is_document_failed = True
                failed_documents = dv_status_values
                failed_document_count = len(dv_status_values)
        result_dict.update(
            {
                "is_document_failed": is_document_failed,
                "failed_documents": failed_documents,
                "failed_document_count": failed_document_count,
            }
        )
        return result_dict

    async def post_application_stages_info(
            self, application_id: str, season=None
    ) -> dict:
        """
        Get post application stages info.

        Params:
            application_id (int | None): An unique application id for
             get post application stages info.
            current_user (str): An user_name of current user.
        Returns:
            dict: Post application stages info.
        """
        await utility_obj.is_id_length_valid(application_id, "Application id")
        application = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.find_one({"_id": ObjectId(application_id)})
        if application is None:
            raise HTTPException(status_code=404, detail="Application not found.")
        post_application_stages = {
            "document_verification": False,
            "application_selection": False,
            "interview": False,
            "offer_letter_release": False,
        }
        if application.get("dv_status") == "Verified":
            post_application_stages.update({"document_verification": True})
        if application.get("interview_list_id"):
            post_application_stages.update({"application_selection": True})
        if application.get("approval_status") == "Under Review":
            post_application_stages.update({"interview": True})
        if application.get("offer_letter") is not None:
            post_application_stages.update({"offer_letter_release": True})
        post_application_stages = await self.update_failed_documents_info(
            application.get("student_id"),
            post_application_stages,
            application.get("application_download_url"),
            season=season,
        )
        return post_application_stages

    async def get_student_data_by_id(self, student_id):
        """
        Get student data by id.

        Params:
            student_id (str): An unique id of student.

        Returns:
            dict: A dictionary contains student data.
        """
        await utility_obj.is_id_length_valid(student_id, "Student id")
        if (
                student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(student_id)}
                )
        ) is None:
            raise HTTPException(status_code=404, detail="Student not found.")
        return student

    async def get_student_secondary_data(self, data, student):
        """
        Check student document exists or not and return student secondary
         details if document exists.

        Params:
            data (upload_docs): Payload useful for get document name.
            student (dict): A dictionary which contains student data.

        Returns:
                dict: A dictionary which contains student secondary details.
        """
        data = jsonable_encoder(data)
        if data.get("title"):
            data.update({data.pop("title"): "title"})
        field_name = next((key for key, value in data.items() if value), None)
        student_secondary_data = (
            await DatabaseConfiguration().studentSecondaryDetails.find_one(
                {"student_id": student.get("_id")}
            )
        )
        if (
                await DatabaseConfiguration().studentSecondaryDetails.find_one(
                    {
                        "student_id": student.get("_id"),
                        f"attachments.{field_name}": {"$exists": True},
                    }
                )
        ) is None and str(field_name).lower() != "application":
            raise HTTPException(status_code=404, detail="Student document not found.")
        return student_secondary_data, field_name

    async def comment_on_document(
            self, student_id: str, current_user, data, comment, college
    ) -> dict:
        """
        Add comment for a document.

        Params:
            student_id (str): An unique student id.
            current_user (str): An user_name of current user.
            data (upload_docs): Payload useful for get document name.
            comment (str): A comment which want to add for document.
            college (dict): Details of college

        Returns:
            dict: A dictionary contains message.
        """
        counselor = False
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
            counselor = True
        student = await self.get_student_data_by_id(student_id)
        student_secondary_data, field_name = await self.get_student_secondary_data(
            data, student
        )
        if student_secondary_data.get("attachments", {}).get(field_name) is None:
            student_secondary_data["attachments"][field_name] = {}
        if (
                student_secondary_data.get("attachments", {})
                        .get(field_name, {})
                        .get("comments")
                is None
        ):
            student_secondary_data["attachments"][field_name]["comments"] = []
        student_secondary_data.get("attachments", {}).get(field_name, {}).get(
            "comments", []
        ).insert(
            0,
            {
                "message": comment,
                "timestamp": datetime.now(timezone.utc),
                "user_name": (
                    utility_obj.name_can(user.get("basic_details"))
                    if is_student
                    else utility_obj.name_can(user)
                ),
                "user_id": user.get("_id"),
            },
        )
        student_id = ObjectId(student_secondary_data.get("student_id"))
        current_datetime = datetime.now(timezone.utc)
        update_data = {"last_user_activity_date": current_datetime}
        if student and not student.get("first_lead_activity_date"):
            update_data["first_lead_activity_date"] = current_datetime
        await DatabaseConfiguration().studentsPrimaryDetails.update_one({"_id": student_id}, {"$set": update_data})
        await DatabaseConfiguration().studentSecondaryDetails.update_one(
            {"student_id": student_id},
            {
                "$set": {
                    f"attachments.{field_name}.comments": student_secondary_data.get(
                        "attachments", {}
                    )
                    .get(field_name, {})
                    .get("comments")
                }
            },
        )
        if counselor:
            if not is_testing_env():
                StudentActivity().student_timeline.delay(
                    student_id=str(student_id),
                    event_type="Document remarks",
                    event_status="Document remarks",
                    message=f"{utility_obj.name_can(user)} has updated a remarks in {field_name} Document",
                    college_id=college.get("id"),
                )
        return {"message": "Comment added."}

    async def get_document_comments(self, student_id: str, current_user, data) -> dict:
        """
        Get comments of a document.

        Params:
            student_id (str): An unique student id.
            current_user (str): An user_name of current user.
            data (upload_docs): Payload useful for get document name.

        Returns:
            dict: Get comments of a document.
        """
        user = await DatabaseConfiguration().user_collection.find_one(
            {"user_name": current_user})
        student = await self.get_student_data_by_id(student_id)
        student_secondary_data, field_name = await self.get_student_secondary_data(
            data, student
        )
        comments = (
            student_secondary_data.get("attachments", {})
            .get(field_name, {})
            .get("comments", [])
        )

        for _id, comment in enumerate(comments):
            if user:
                comment["timeline_type"] = "Counselor" if user.get("role", {}).get(
                    "role_name") == "college_counselor" else "System"
            elif await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"student_id": ObjectId(comment.get("user_id"))}
            ):
                comment["timeline_type"] = "Student"
            else:
                comment["timeline_type"] = "System"
            comment["id"] = _id
            current_time_str = comment.get(
                "timestamp", datetime.now(timezone.utc)
            ).strftime("%d %b %Y %I:%M:%S %p")
            current_time = datetime.strptime(
                current_time_str, "%d %b %Y %I:%M:%S %p"
            )

            if _id < len(comments) - 1:
                next_time_str = comments[_id + 1]["timestamp"].strftime(
                    "%d %b %Y %I:%M:%S %p"
                )
                next_time = datetime.strptime(
                    next_time_str, "%d %b %Y %I:%M:%S %p"
                )
                time_diff = utility_obj.calculate_time_diff(next_time, current_time)
                comment["duration1"] = time_diff
            comment["timestamp"] = utility_obj.get_local_time(comment.get("timestamp"))
            comment.pop("user_name")
            comment.pop("user_id")
        return {"message": "Get document comments.", "document_comments": comments}

    async def update_document_status(
            self, application_id: str, current_user, data, status
    ) -> dict:
        """
        Update status of a document.

        Params:
            application_id (str): An unique application id.
            current_user (str): An user_name of current user.
            data (upload_docs): Payload useful for get document name.
            status (DocumentStatus): A status of a document which want to update.
            college (dict): College data.
        Returns:
            dict: A dictionary contains message.
        """
        await UserHelper().is_valid_user(current_user)
        application = await self.get_application_data(application_id)
        student = await self.get_student_data_by_id(str(application.get("student_id")))
        student_secondary_data, field_name = await self.get_student_secondary_data(
            data, student
        )
        if status == "unset":
            await DatabaseConfiguration().studentSecondaryDetails.update_one(
                {"student_id": student_secondary_data.get("student_id")},
                {"$unset": {f"attachments.{field_name}.status": True}},
            )
        else:
            await DatabaseConfiguration().studentSecondaryDetails.update_one(
                {"student_id": student_secondary_data.get("student_id")},
                {"$set": {f"attachments.{field_name}.status": status.title()}},
            )
        student_secondary_data = (
            await DatabaseConfiguration().studentSecondaryDetails.find_one(
                {"student_id": student.get("_id")}
            )
        )
        dv_status_values = [
            value.get("status")
            for key, value in student_secondary_data.get("attachments", {}).items()
        ]
        dv_status = "Not Accepted"
        if "Rejected" in dv_status_values:
            dv_status = "Rejected"
        elif "Accepted" in dv_status_values and ("Rejected" not in dv_status_values):
            dv_status = "Partially Accepted"
        elif all(value == "Accepted" for value in dv_status_values):
            dv_status = "Accepted"
        await DatabaseConfiguration().studentApplicationForms.update_many(
            {"student_id": student_secondary_data.get("student_id")},
            {"$set": {"dv_status": dv_status}},
        )
        current_datetime = datetime.now(timezone.utc)
        update_data = {"dv_status": dv_status, "last_user_activity_date": current_datetime}
        if student and not student.get("first_lead_activity_date"):
            update_data["first_lead_activity_date"] = current_datetime
        await DatabaseConfiguration().studentsPrimaryDetails.update_one(
            {"_id": student_secondary_data.get("student_id")}, {"$set": update_data})
        await cache_invalidation(api_updated="admin/update_status_of_document")
        return {"message": "Updated status of a document."}

    async def update_comment(
            self, student_id: str, current_user, data, comment, comment_id
    ) -> dict:
        """
        Update comment of a document.

        Params:
            student_id (str): An unique student id.
            current_user (str): An user_name of current user.
            data (upload_docs): Payload useful for get document name.
            comment (int): A comment which want to update.
            comment_id (str): A comment id which helpful for update particular comment.

        Returns:
            dict: A dictionary contains message.
        """
        user = await UserHelper().is_valid_user(current_user)
        student = await self.get_student_data_by_id(student_id)
        student_secondary_data, field_name = await self.get_student_secondary_data(
            data, student
        )
        comment_data = (
            student_secondary_data.get("attachments", {})
            .get(field_name)
            .get("comments")[comment_id]
        )
        if comment_data:
            if ObjectId(user.get("_id")) != comment_data.get("user_id") or user.get(
                    "role", {}
            ).get("role_name") not in ["college_super_admin", "college_admin"]:
                raise HTTPException(status_code=401, detail="Not enough permissions")
        if (
                student_secondary_data.get("attachments", {})
                        .get(field_name, {})
                        .get("comments", [])[comment_id]
                        .get("edit")
                is None
        ):
            student_secondary_data["attachments"][field_name]["comments"][comment_id][
                "edit"
            ] = []
        student_secondary_data.get("attachments", {}).get(field_name, {}).get(
            "comments", []
        )[0].get("edit").insert(
            0, {"timestamp": datetime.now(timezone.utc), "user_id": user.get("_id")}
        )
        await DatabaseConfiguration().studentSecondaryDetails.update_one(
            {"student_id": student_secondary_data.get("student_id")},
            {
                "$set": {
                    f"attachments.{field_name}.comments.{comment_id}.message": comment,
                    f"attachments.{field_name}.comments.{comment_id}.edit": student_secondary_data[
                        "attachments"
                    ][
                        field_name
                    ][
                        "comments"
                    ][
                        comment_id
                    ][
                        "edit"
                    ],
                }
            },
        )
        return {"message": "Comment updated."}

    async def delete_comment(
            self, student_id: str, current_user, data, comment_id
    ) -> dict:
        """
        Delete comment of a document.

        Params:
            student_id (str): An unique student id.
            current_user (str): An user_name of current user.
            data (upload_docs): Payload useful for get document name.
            comment_id (str): A comment id which helpful for delete particular comment.

        Returns:
            dict: A dictionary contains message.
        """
        user = await UserHelper().is_valid_user(current_user)
        student = await self.get_student_data_by_id(student_id)
        student_secondary_data, field_name = await self.get_student_secondary_data(
            data, student
        )
        comments: list = (
            student_secondary_data.get("attachments", {})
            .get(field_name)
            .get("comments", [])
        )
        comment_data = comments[comment_id]
        if comment_data:
            if ObjectId(user.get("_id")) != comment_data.get("user_id") or user.get(
                    "role", {}
            ).get("role_name") not in ["college_super_admin", "college_admin"]:
                raise HTTPException(status_code=401, detail="Not enough permissions")
        comments.pop(comment_id)
        await DatabaseConfiguration().studentSecondaryDetails.update_one(
            {"student_id": ObjectId(student_id)},
            {"$set": {f"attachments.{field_name}.comments": comments}},
        )
        return {"message": "Comment deleted."}

    async def send_student_document_to_board(
            self,
            current_user: str,
            application_id: str,
            request: Request,
            data: any,
            college: dict,
            background_tasks: BackgroundTasks,
            season=None,
            college_id=None,
    ) -> dict:
        """
        Send document to respective board through mail for verification
        purpose.

        Params:
            current_user (str): An user_name of current user.
            application_id (str): An unique identifier/id of application.
            request:
            request (Request): An object useful for get ip address of user.
            data (any): Useful for get document.
            college (dict): A dictionary which contains college data.

        Returns:
            dict: A dictionary send mail info message.
        """
        user = await UserHelper().is_valid_user(current_user)
        application = await self.get_application_data(application_id)
        toml_data = utility_obj.read_current_toml_file()
        if toml_data.get("testing", {}).get("test") is False:
            student = await self.get_student_data_by_id(
                str(application.get("student_id"))
            )
            student_secondary_data, field_name = await self.get_student_secondary_data(
                data, student
            )
            field_name = str(field_name)
            if field_name == "application":
                file = application.get("application_download_url")
            else:
                file = (
                    student_secondary_data.get("attachments")
                    .get(field_name)
                    .get("file_s3_url")
                )
            if file is None:
                raise HTTPException(status_code=404, detail="Document not found.")
            if field_name not in ["tenth", "inter"]:
                raise HTTPException(
                    status_code=422,
                    detail="Currently, only able to send "
                           " 10th or 12th document to board.",
                )
            board_name = (
                student_secondary_data.get("education_details", {})
                .get(f"{field_name}_school_details", {})
                .get("board")
            )
            if field_name == "tenth":
                email_field_name = "tenth_document_verification_email"
            else:
                email_field_name = "twelve_document_verification_email"
            board_details = await get_collection_from_cache(collection_name="board_details")
            if board_details:
                board_data = utility_obj.search_for_document(
                    collection=board_details,
                    field="board_name",
                    search_name=board_name
                )
            else:
                board_data = await DatabaseConfiguration().tenth_twelve_board_details.find_one(
                    {"board_name": board_name, email_field_name: {"$exists": True}})
                collections = await DatabaseConfiguration().tenth_twelve_board_details.aggregate([]).to_list(None)
                await store_collection_in_cache(collections, collection_name="board_details")
            if board_data and board_data.get(email_field_name):
                board_email = board_data.get(email_field_name)
                action_type = (
                    "counselor"
                    if user.get("role", {}).get("role_name") == "college_counselor"
                    else "system"
                )
                await EmailActivity().send_document_to_respective_board(
                    file,
                    college,
                    current_user,
                    request,
                    board_email,
                    action_type=action_type,
                    field_name=field_name,
                    student_id=application.get("student_id"),
                    season=season,
                    college_id=college_id,
                )
            else:
                raise HTTPException(
                    status_code=422,
                    detail="Board document verification " "email address not found",
                )
        return {"message": "Send document to respective board."}

    async def get_external_links_of_student_documents(
            self, current_user: str, application_id: str
    ) -> dict:
        """
        Get external links of student documents.

        Params:
            current_user (str): An user_name of current user.
            application_id (str): An unique identifier/id of application.
            request:

        Returns:
            dict: A dictionary contains external links of student documents.

        Raises:
            401 (Not enough permissions)- Unauthourized user try to login.
            404 (Not found)- When data not found.
        """
        await UserHelper().is_valid_user(current_user)
        application = await self.get_application_data(application_id)
        student = await self.get_student_data_by_id(str(application.get("student_id")))
        if (
                student_secondary_data := await DatabaseConfiguration().studentSecondaryDetails.find_one(
                    {"student_id": student.get("_id"), "attachments": {"$exists": True}}
                )
        ) is None:
            raise HTTPException(
                status_code=404, detail="Student " "documents not found."
            )

        data, website_url = {}, None
        board_details = await get_collection_from_cache(collection_name="board_details")
        for key in student_secondary_data.get("attachments", {}).keys():
            if key in ["tenth", "high_school"]:
                board_name = (
                    student_secondary_data.get("education_details", {})
                    .get(f"{key}_school_details", {})
                    .get("school_name")
                )
                if key == "tenth":
                    email_field_name = "tenth_document_verification_website"
                else:
                    email_field_name = "twelve_document_verification_website"
                if board_details:
                    board_data = utility_obj.search_for_document(
                        collection=board_details,
                        field="board_name",
                        search_name=board_name
                    )
                else:
                    board_data = await DatabaseConfiguration().tenth_twelve_board_details.find_one(
                        {"board_name": board_name, email_field_name: {"$exists": True}})

                if board_data and board_data.get(email_field_name):
                    website_url = board_data.get(email_field_name)
            data.update({key: website_url})
        if not board_details:
            collections = await DatabaseConfiguration().tenth_twelve_board_details.aggregate([]).to_list(None)
            await store_collection_in_cache(collections, collection_name="board_details")
        if application.get("application_download_url"):
            data.update({"application": website_url})
        return {"message": "Get external links of student documents.", "data": data}

    async def manage_preference_order(
            self, application_id: str, change_preference: str,
            change_preference_with: str, season: str | None, college_id: str,
            testing: bool) -> dict:
        """
        Change the preference order.

        Params:
            - application_id (str): An unique application id which useful for get
                application information.
            - change_preference (str): Preference name which order want to change.
            - change_preference_with (str): Preference name which order want to
                replace with order of change_preference.
            - season (str | None): Either None or season id which useful for change
                particular
            - college_id (str): An unique college id which useful for get
                college information.
            - testing (bool): A boolean value which represent current mode
                is testing or not.

        Returns:
            - dict: A dictionary which contains information about change order of
            preference.

        Raises:
            - ObjectIdInValid: An error with status code 422 which occurred
                when application id will be wrong.
            - DataNotFoundError: An error with status code 404 which occurred
            when application not found.
            - CustomError: An error occurred with status code 400
                when provide incorrect preference information or preference
                information not found.
            - Exception: An error with status code 500 which occurred when
                something went wrong in the background code.
        """
        await utility_obj.is_length_valid(application_id, "Application id")
        if not testing:
            Reset_the_settings().check_college_mapped(college_id)
        if (application := await DatabaseConfiguration(
                season=season).studentApplicationForms.find_one(
            {"_id": ObjectId(application_id)})) is None:
            raise DataNotFoundError(message="Application")
        preference_info = application.get("preference_info", [])
        if preference_info in [None, []]:
            raise CustomError("Preference information not found.")
        prev_preference_info = preference_info.copy()
        if (change_preference not in preference_info or
                change_preference_with not in preference_info):
            raise CustomError("Make sure provided correct change preference "
                              "order information.")
        change_pref_index = preference_info.index(change_preference)
        change_pref_with_index = preference_info.index(change_preference_with)
        preference_info[change_pref_index] = change_preference_with
        preference_info[change_pref_with_index] = change_preference
        if change_pref_index == 0 or change_pref_with_index == 0:
            spec_name = change_preference_with if change_pref_index == 0 else change_preference
            application["spec_name1"] = spec_name
            if (course := await DatabaseConfiguration(
                    season=season).course_collection.find_one(
                {"_id": ObjectId(application.get("course_id"))})) is None:
                raise CustomError("Application course not found.")
            application["custom_application_id"] = (StudentUserCrudHelper().
            get_custom_application_id(
                course=course.get("course_name"), course_id=str(course.get("_id")),
                spec_course=spec_name))
        preference_history = application.get("preference_history", [])
        if preference_history is None:
            preference_history = []
        action_timestamp = datetime.now(timezone.utc)
        preference_history.insert(0, {"prev_preference_info": prev_preference_info,
                                      "updated_preference_info": preference_info, "timestamp": action_timestamp})
        await DatabaseConfiguration(
            season=season).studentApplicationForms.update_one(
            {"_id": ObjectId(application_id)},
            {"$set": {"preference_info": preference_info,
                      "spec_name1": application.get("spec_name1"),
                      "custom_application_id": application.get("custom_application_id"),
                      "last_updated_time": action_timestamp,
                      "preference_history": preference_history}})
        return {"message": "Preference order updated"}

    async def filter_by_preference(
            self, preference: list[str], course_id: ObjectId | str,
            specialization_name: str | None) -> dict:
        """
        Helper function for filter data by preference.

        Params:
            - preference (list[str]): A list which contains information about
                filter data by preference.
            - course_id (ObjectId | str): Either string or ObjectId value which
                represent unique identification of course.
            - specialization_name (str): A string value which course
                specialization/preference name.

       Returns:
            - dict: A dictionary which contains filter which useful in
                aggregation pipeline.
        """
        match_stage = {}
        if "Any Preference" in preference:
            match_stage.update({
                "$expr": {
                    "$and": [{"$eq": ["$course_id", course_id]},
                             {"$in": [specialization_name, {
                                 "$ifNull": ["$preference_info", []]}]}]
                }
            })
        else:
            preference_info = []
            for preference_name in preference:
                temp_preference = preference_name.split(" ")
                preference_info.append({
                    "$expr": {
                        "$and": [
                            {"$eq": ["$course_id", course_id]}, {
                                "$eq": [{"$arrayElemAt": [
                                    "$preference_info",
                                    (int(temp_preference[1]) - 1)]},
                                    specialization_name]}]
                    }})
            match_stage.update({"$or": preference_info})
        return match_stage

    async def update_student_application(self, current_user: User, payload: dict, attachments: list,
                                         attachment_details: dict, section: str, college: dict, course_name: str,
                                         last_stage: bool
                                         ):

        """
            Updates a student's application with new data and attachments for a specific section.

            Args:
                current_user (User): The currently authenticated user performing the update.
                payload (dict): The updated application data for the specified section.
                attachments (list): A list of new attachment files or references to be added.
                attachment_details (dict): Metadata or additional information related to the attachments.
                section (str): The section of the application being updated (e.g., 'personal_info', 'education').
                college (dict): Information about the college associated with the application.
                course_name (str): The course which student want to enroll
                last_stage (bool): If it is the last stage then value will be True else False

            Returns:
                None

            Raises:
                HTTPException: If the application is not found, user is unauthorized, or update fails due to validation or other reasons.
        """
        from app.s3_events.s3_events_configuration import upload_file
        if ((student := await DatabaseConfiguration().studentsPrimaryDetails.find_one({"user_name": current_user}))
                is None):
            raise DataNotFoundError(message="Student")

        if ((course := await DatabaseConfiguration().course_collection.find_one({"course_name": course_name,
                                                                                 "college_id": ObjectId(college.get("id"))
                                                                                }))
            is None):
            raise DataNotFoundError(message="Course")
        student_id = student.get("_id")
        source = student.get("source", {}).get("primary_source", {}).get("utm_source")
        if ((application := await DatabaseConfiguration().studentApplicationForms.find_one({"student_id": ObjectId(student_id),
                                                                                            "course_id": ObjectId(course.get("_id"))
                                                                                            }))) is None:
            specialization, preference = None, None
            if section == "Program / Preference Details":
                StudentActivity().add_student_timeline.delay(
                    student_id=str(student_id),
                    event_status="started",
                    message="has started filling the Application Form for",
                    college_id=str(college.get("id"))
                )
                system_preference = college.get("system_preference", {})
                if system_preference and system_preference.get("preference"):
                    preference = []
                    for i in range(1, system_preference.get("preference_count") + 1):
                        ith_preference = payload.get(f"Preference_{i}")
                        if ith_preference:
                            preference.append(payload.get(f"Preference_{i}"))
                        else:
                            break
                else:
                    specialization = payload.get("specialization")
                await StudentUserCrudHelper().update_special_course(
                    _id=student_id,
                    main=specialization,
                    course=course_name,
                    secondary=payload.get("secondary"),
                    college_id=college.get("id"),
                    round_robin=True,
                    state_code=student.get("address_details", {})
                    .get("communication_address", {})
                    .get("state", {})
                    .get("state_code", None),
                    source_name=source if source else "Organic",
                    student=student,
                    system_preference=college.get("system_preference", {}),
                    preference_info=preference
                )
                application = await DatabaseConfiguration().studentApplicationForms.find_one({"student_id": ObjectId(student_id),
                                                                                            "course_id": ObjectId(course.get("_id"))
                                                                                            })
            else:
                raise DataNotFoundError(message="Application")
        all_keys = payload.keys()
        collection_updates, current_address, permanent_address = {}, None, None
        collection_updates.setdefault("studentApplicationForms", {})["application_initiated"]: True
        field_map = await DatabaseConfiguration().keyname_mapping.find_one({})
        aws_env = settings.aws_env
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        base_bucket_url = getattr(settings, f"s3_{aws_env}_base_bucket_url")
        for key in ["graduation_total_fields", "twelfth_total_fields", "pg_total_fields"]:
            payload.update(payload.pop(key, {}))
        for key, value in payload.items():
            if key not in field_map:
                logger.error(f"Major issue: Unable to find key mapping to key: {key}")
            if key == "email":
                collection_updates.setdefault("studentsPrimaryDetails", {})["user_name"] = value
            collection = field_map.get(key, {}).get("collection_name")
            location = field_map.get(key, {}).get("location")
            if collection and location and not location.startswith('address_details'):
                collection_updates.setdefault(collection, {})[location] = value
        if "country_code" in all_keys:
            current_address = await StudentUserCrudHelper().address_update(payload, dynamic=True)
        is_same_address = False
        if payload.get("permanent_address_same_as_address_for_communication", None):
            permanent = payload.get("permanent_address_same_as_address_for_communication")
            if permanent.lower() == "yes":
                is_same_address = True
                permanent_address = await StudentUserCrudHelper().address_update(payload, dynamic=True)
            else:
                details = {
                    "country_code": payload.get("permanent_country_code"),
                    "state_code": payload.get("permanent_state_code"),
                    "city": payload.get("permanent_city"),
                    "address_line1": payload.get("permanent_address_line1"),
                    "address_line2": payload.get("permanent_address_line2"),
                    "pincode": payload.get("permanent_pincode")
                }
                permanent_address = await StudentUserCrudHelper().address_update(details, dynamic=True)
        if current_address or permanent_address:
            collection_updates.setdefault("studentsPrimaryDetails", {})["address_details"] = {
                "communication_address": current_address if current_address else student.get("address_details", {})
                .get("communication_address"),
                "permanent_address": permanent_address if permanent_address else student.get("address_details", {})
                .get("permanent_address"),
                "permanent_address_same_as_address_for_communication": is_same_address
            }
        for exam in ["tenth", "twelfth", "diploma", "graduation", "pg"]:
            obtained_key = f"{exam}_obtained_mark"
            marking_scheme_key = f"{exam}_marking_scheme"
            normalize_key = f"{exam}_normalize_score"

            if obtained_key in all_keys:
                score = payload.get(obtained_key)
                if score not in ["", None]:
                    normalized_score = utility_obj.normalize_score(payload.get(marking_scheme_key), score)
                    field_data = field_map.get(normalize_key, {})
                    collection = field_data.get("collection_name")
                    location = field_data.get("location")
                    if collection and location:
                        collection_updates.setdefault(collection, {})[location] = normalized_score
        if attachments:
            for file in attachments:
                file_key_name = attachment_details.get(file.filename)
                key_data = field_map.get(file_key_name, {})

                collection, location = key_data.get("collection_name"), key_data.get("location")
                extension = PurePath(file.filename).suffix
                unique_filename = utility_obj.create_unique_filename(
                    extension=extension)
                season = utility_obj.get_year_based_on_season()
                object_key = (f"{utility_obj.get_university_name_s3_folder()}/{season}/"
                              f"{settings.s3_student_documents_bucket_name}/{str(student_id)}/{file_key_name}/"
                              f"{unique_filename}")
                await upload_file(
                    file=file, bucket_name=base_bucket, object_name=object_key)
                value = {
                    "file_s3_url": f"{base_bucket_url}{object_key}",
                    "file_name": file.filename,
                }
                if collection and location:
                    collection_updates.setdefault(collection, {})[location] = value
                else:
                    logger.error(f"Major issue: Unable to find key mapping to key: {file_key_name}")
                if settings.environment != "demo":
                    DocExtraction().text_extraction.delay(student_id=str(student_id))
        collection_updates.setdefault("studentsPrimaryDetails", {})["last_accessed"] = datetime.utcnow()
        stage_values = college.get("stage_values", {})
        if stage_values and last_stage:
            stage = stage_values.get(section)
            if stage and application.get("current_stage", 0) < stage:
                collection_updates.setdefault("studentApplicationForms", {})["current_stage"] = stage
        for collection_name, updates in collection_updates.items():
            update_payload = {"$set": updates}
            db_config = DatabaseConfiguration()
            collection = getattr(db_config, collection_name)
            if collection_name == "studentApplicationForms":
                collection.update_one({"_id": application.get("_id")}, update_payload, upsert=True)
            elif collection_name == "studentsPrimaryDetails":
                collection.update_one({"_id": student.get("_id")}, update_payload, upsert=True)
            else:
                collection.update_one({"student_id": student.get("_id")}, update_payload, upsert=True)
        StudentActivity().add_student_timeline.delay(
            student_id=str(student_id),
            event_type="Application",
            event_status=f"Updated {section}",
            message=f"has updated its {section.title().replace('_', ' ')}"
                    f" for programme:",
            college_id=college.get("id"),
        )

    async def get_student_application_details(self, college_id: str, user_name: User, course_name: str) -> dict:
        """

        """
        if ((student := await DatabaseConfiguration().studentsPrimaryDetails.find_one({"user_name": user_name}))
                is None):
            raise DataNotFoundError(message="Student")

        if ((course := await DatabaseConfiguration().course_collection.find_one({"course_name": course_name,
                                                                                 "college_id": ObjectId(college_id)
                                                                                }))
            is None):
            raise DataNotFoundError(message="Course")
        student_id = student.get("_id")
        if ((application := await DatabaseConfiguration().studentApplicationForms.find_one({"student_id": ObjectId(student_id),
                                                                                            "course_id": ObjectId(course.get("_id"))
                                                                                            }))) is None:
            raise DataNotFoundError(message="Application")
        pipeline = [
            {
                '$match': {
                    "college_id": ObjectId(college_id)
                }
            }, {
                '$unwind': '$application_form'
            }, {
                '$unwind': '$application_form.sections'
            }, {
                '$unwind': '$application_form.sections.fields'
            }, {
                '$project': {
                    'top_api': '$application_form.sections.fields.key_name',
                    'logical_fields': {
                        '$objectToArray': '$application_form.sections.fields.dependent_fields.logical_fields'
                    }
                }
            }, {
                '$unwind': {
                    'path': '$logical_fields',
                    'preserveNullAndEmptyArrays': True
                }
            }, {
                '$unwind': {
                    'path': '$logical_fields.v.fields',
                    'preserveNullAndEmptyArrays': True
                }
            }, {
                '$project': {
                    'apis': [
                        '$top_api', '$logical_fields.v.fields.key_name'
                    ]
                }
            }, {
                '$unwind': '$apis'
            }, {
                '$match': {
                    '$expr': {
                        '$eq': [
                            {
                                '$type': '$apis'
                            }, 'string'
                        ]
                    }
                }
            }, {
                '$group': {
                    '_id': None,
                    'key_names': {
                        '$addToSet': '$apis'
                    }
                }
            }, {
                '$project': {
                    '_id': 0,
                    'key_names': 1
                }
            }
        ]
        key_names = await DatabaseConfiguration().college_form_details.aggregate(pipeline).to_list(None)
        key_names = key_names[0] if key_names else []
        key_names = key_names.get("key_names")
        key_mapping_dict = await DatabaseConfiguration().keyname_mapping.find_one({})
        collection_fields = defaultdict(list)
        for key in key_names:
            if key in key_mapping_dict:
                fetch_key = {
                    "country_code": "country_name",
                    "state_code": "state_name",
                    "permanent_country_code": "permanent_country_name",
                    "permanent_state_code": "permanent_state_name"
                }.get(key, key)
                entry = key_mapping_dict.get(fetch_key, {})
                collection_name = entry.get('collection_name')
                location = entry.get('location')
                if collection_name and location:
                    collection_fields[collection_name].append((key, location))
        collection_fields["studentsPrimaryDetails"].extend([
            ("country_code", {
                "iso2": f"${key_mapping_dict.get('country_code', {}).get('location')}",
                "name": f"${key_mapping_dict.get('country_name', {}).get('location')}"
            }),
            ("state_code", {
                "iso2": f"${key_mapping_dict.get('state_code', {}).get('location')}",
                "name": f"${key_mapping_dict.get('state_name', {}).get('location')}"
            }),
            ("permanent_country_code", {
                "iso2": f"${key_mapping_dict.get('permanent_country_code', {}).get('location')}",
                "name": f"${key_mapping_dict.get('permanent_country_name', {}).get('location')}"
            }),
            ("permanent_state_code", {
                "iso2": f"${key_mapping_dict.get('permanent_state_code', {}).get('location')}",
                "name": f"${key_mapping_dict.get('permanent_state_name', {}).get('location')}"
            }),
        ])
        collection_fields["studentSecondaryDetails"].extend([
            ("graduation_result_details", "education_details.graduation_details.graduation_result_details"),
            ("twelfth_result_details", "education_details.inter_school_details.inter_subject_wise_details"),
            ("pg_result_details", "education_details.post_graduation_details.pg_result_details"),
            ("graduation_total_fields", {
                                "graduation_total_marks_scored": "$education_details.graduation_details.graduation_total_obtained_mark",
                                "graduation_total_maximum_marks": "$education_details.graduation_details.graduation_total_max_mark",
                                "graduation_aggregate_marks_%": "$education_details.graduation_details.graduation_aggregate_mark_percentage"
                            }),
            ("twelfth_total_fields", {
                "twelfth_total_marks_scored": "$education_details.inter_school_details.inter_total_obtained_mark",
                "twelfth_total_maximum_marks": "$education_details.inter_school_details.inter_total_max_mark",
                "twelfth_aggregate_marks_%": "$education_details.inter_school_details.inter_aggregate_mark_percentage"
            }),
            ("pg_total_fields", {
                "pg_total_marks_scored": "$education_details.post_graduation_details.pg_total_obtained_mark",
                "pg_total_maximum_marks": "$education_details.post_graduation_details.pg_total_max_mark",
                "pg_aggregate_marks_%": "$education_details.post_graduation_details.pg_aggregate_marks_percentage"
            })

        ])
        result = {}
        for collection_name, fields in collection_fields.items():
            project_stage = {
                key: {"$ifNull": [f"${location}", None]} if not isinstance(location, dict) else location
                for key, location in fields
            }
            if collection_name == "studentsPrimaryDetails":
                filter_query = {"_id": ObjectId(student_id)}
            elif collection_name == "studentApplicationForms":
                filter_query = {"_id": ObjectId(application.get("_id"))}
            else:
                filter_query = {"student_id": ObjectId(student_id)}
            db_config = DatabaseConfiguration()
            collection = getattr(db_config, collection_name)
            pipeline = [
                {"$match": filter_query},
                {"$project": project_stage}
            ]
            docs = await collection.aggregate(pipeline).to_list(None)
            if docs:
                result.update(docs[0])
            else:
                for key, _ in fields:
                    result[key] = None
        result.pop("_id")
        return result
