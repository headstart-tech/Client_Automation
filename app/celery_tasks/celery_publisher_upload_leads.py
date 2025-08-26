"""
This file contain class and functions related to add lead data by publisher in the background
"""

import asyncio
import datetime

from bson import ObjectId
from email_validator import EmailNotValidError, validate_email
from fastapi import BackgroundTasks, HTTPException

from app.celery_tasks.celery_send_mail import send_mail_config
from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.celery_app import celery_app
from app.core.custom_error import CustomError
from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj
from app.database.database_sync import DatabaseConfigurationSync
from app.dependencies.hashing import Hash
from app.dependencies.oauth import is_testing_env, sync_cache_invalidation
from app.helpers.student_curd.student_user_crud_configuration import (
    StudentUserCrudHelper,
)

logger = get_logger(name=__name__)


class PublisherActivity:
    """
    Contain functions related to publisher activity
    """

    @staticmethod
    @celery_app.task(ignore_result=True)
    def process_uploaded_loads(
            user,
            data,
            filename,
            college,
            is_created_by_user=False,
            ip_address=None,
            counselor_id=None,
            data_name=None,
            college_id=None,
    ):
        """
        Process requested lead data, store lead data if not exists
        After complete request, send statistics of request to user through mail
        """
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)
        duplicate_data_lead, failed_data_lead = [], []
        lead_data = DatabaseConfigurationSync().lead_upload_history.insert_one(
            {
                "imported_by": ObjectId(user.get("_id")),
                "import_status": "pending",
                "data_name": data_name,
                "uploaded_on": datetime.datetime.utcnow(),
                "uploaded_by": utility_obj.name_can(user),
                "lead_processed": len(data.get("student_details", [])),
                "duplicate_leads": 0,
                "failed_lead": 0,
            }
        )
        email_wise_status = {}
        offline_id = lead_data.inserted_id
        student_ids, already_exist, errors = [], [], []
        registered_count, unregistered_count, already_exist_count = 0, 0, 0

        index = 0
        length = len(counselor_id) if counselor_id else 0

        for _id, item in enumerate(data.get("student_details", [])):
            if length > 0:
                counselor_id_assigned = counselor_id[index]
                index = (index + 1) % length
            else:
                counselor_id_assigned = None

            if item.get("full_name") != "" and item.get(
                    "full_name") is not None:
                item["full_name"] = item.get("full_name").strip()
                if len(item.get("full_name", "")) < 2:
                    item[
                        "error"] = "Full name must be greater than 2 characters."
                    failed_data_lead.append(item)
                    if filename.endswith(".csv"):
                        errors.append(
                            f"On line no {_id + 2}, "
                            f"full name of student whose email id "
                            f"'{item.get('email')}' must be "
                            f"greater than 2 characters."
                        )
                    else:
                        errors.append(
                            f"Full name of student whose email id"
                            f" '{item.get('email')}' must be greater than 2 "
                            f"characters."
                        )
                    unregistered_count += 1
                    email_wise_status.update(
                        {
                            item.get("email"): [
                                "Failed",
                                "Full name must be greater than 2 characters.",
                            ]
                        }
                    )
                    continue

            else:
                item["error"] = "Full name must be required and valid."
                failed_data_lead.append(item)
                if filename.endswith(".csv"):
                    errors.append(
                        f"On line no {_id + 2}, full name of "
                        f"student whose email id '{item.get('email')}' must be "
                        f"required and valid."
                    )
                else:
                    errors.append(
                        f"Full name of student whose email id "
                        f"'{item.get('email')}' must be required and valid."
                    )
                unregistered_count += 1
                email_wise_status.update(
                    {
                        item.get("email"): [
                            "Failed",
                            "Full name must be required and valid.",
                        ]
                    }
                )
                continue
            if item.get("email") != "" and item.get("email") is not None:
                item["email"] = item.get("email").lower()
                item["email"] = item.get("email").strip()
                try:
                    validate_email(item.get("email"))
                except EmailNotValidError as e:
                    logger.error("Some error occurred", e)
                    item["error"] = "Email must be valid."
                    failed_data_lead.append(item)
                    if filename.endswith(".csv"):
                        errors.append(
                            f"On line no {_id + 2}, email not valid."
                            f" Error - {str(e)}"
                        )
                    else:
                        errors.append(
                            f"Email address of student whose email id"
                            f" '{item.get('email')}' must be required and valid."
                            f" Error - {str(e)}"
                        )
                    unregistered_count += 1
                    email_wise_status.update(
                        {item.get("email"): ["Failed", "Email must be valid."]}
                    )
                    continue
            else:
                item["error"] = "Email must be required and valid."
                failed_data_lead.append(item)
                if filename.endswith(".csv"):
                    errors.append(
                        f"On line no {_id + 2}, email of student whose "
                        f"email id '{item.get('email')}' must required and"
                        f" valid."
                    )
                else:
                    errors.append(
                        f"Email of student whose email id "
                        f"'{item.get('email')}' must required and valid."
                    )
                unregistered_count += 1
                email_wise_status.update(
                    {item.get("email"): ["Failed",
                                         "Email must be required and valid."]}
                )
                continue
            if item.get("mobile_number"):
                item["mobile_number"] = str(
                    int(item.get("mobile_number"))).replace(
                    " ", ""
                )
                if len(str(item.get("mobile_number", ""))) != 10:
                    item["error"] = "Mobile number must be 10 digit."
                    failed_data_lead.append(item)
                    if filename.endswith(".csv"):
                        errors.append(
                            f"On line no {_id + 2}, mobile number of "
                            f"student whose email id '{item.get('email')}' "
                            f"must be 10 digit."
                        )
                    else:
                        errors.append(
                            f"Mobile number of student whose email id "
                            f"'{item.get('email')}' must be 10 digit."
                        )
                    unregistered_count += 1
                    email_wise_status.update(
                        {
                            item.get("email"): [
                                "Failed",
                                "Mobile number must be 10 digit.",
                            ]
                        }
                    )
                    continue
                try:
                    if type(item.get("mobile_number")) == str:
                        item.get("mobile_number").isnumeric()
                except Exception as e:
                    item["error"] = "Mobile number should be integer."
                    failed_data_lead.append(item)
                    if filename.endswith(".csv"):
                        errors.append(
                            f"On line no {_id + 2}, mobile number "
                            f"of student whose email id '{item.get('email')}' "
                            f"should be integer."
                        )
                        logger.error("Some error occurred", e)
                    else:
                        errors.append(
                            f"Mobile number of student whose email id "
                            f"'{item.get('email')}' should be integer."
                        )
                    unregistered_count += 1
                    email_wise_status.update(
                        {
                            item.get("email"): [
                                "Failed",
                                "Mobile number should be integer.",
                            ]
                        }
                    )
                    continue
            else:
                item["error"] = "Mobile number must be required and valid."
                failed_data_lead.append(item)
                if filename.endswith(".csv"):
                    errors.append(
                        f"On line no {_id + 2}, mobile number of "
                        f"student whose email id '{item.get('email')}' must be "
                        f"required and valid."
                    )
                else:
                    errors.append(
                        f"Mobile number of student whose email id "
                        f"'{item['email']}' must be required and valid."
                    )
                email_wise_status.update(
                    {
                        item.get("email"): [
                            "Failed",
                            "Mobile number must be required and valid.",
                        ]
                    }
                )
                unregistered_count += 1
                continue
            course = {"course_specialization": []}
            if item.get("course") != "" and item.get("course") is not None:
                item["course"] = item.get("course").strip()
                try:
                    if (
                            course := DatabaseConfigurationSync().course_collection.find_one(
                                {
                                    "college_id": (
                                            ObjectId(college.get("id"))
                                            if not is_created_by_user
                                            else ObjectId(college.get("id"))
                                    ),
                                    "course_name": item.get("course"),
                                }
                            )
                    ) is None:
                        item["error"] = "Course is not valid."
                        failed_data_lead.append(item)
                        if filename.endswith(".csv"):
                            errors.append(
                                f"On line no {_id + 2}, "
                                f"course for student whose email id "
                                f"'{item['email']}' not valid."
                            )
                        else:
                            errors.append(
                                f"Course for student whose email id "
                                f"'{item['email']}' not valid."
                            )
                        email_wise_status.update(
                            {item.get("email"): ["Failed",
                                                 "Course is not valid."]}
                        )
                        unregistered_count += 1
                        continue
                except TypeError as e:
                    item["error"] = f"Internal error: {e}."
                    failed_data_lead.append(item)
                    email_wise_status.update(
                        {item.get("email"): ["Failed", f"Internal error: {e}"]}
                    )
                    logger.error("Some error occurred. Error: ", e)
                except Exception as e:
                    failed_data_lead.append(item)
                    email_wise_status.update(
                        {item.get("email"): ["Failed",
                                             f"Internal error: {e}."]}
                    )
                    logger.error("Some error occurred. Error: ", e)

            else:
                item["error"] = "Course must be required and valid."
                failed_data_lead.append(item)
                if filename.endswith(".csv"):
                    errors.append(
                        f"On line no {_id + 2}, course for student whose"
                        f" email id '{item['email']}' must be required "
                        f"and valid."
                    )
                else:
                    errors.append(
                        f"Course for student whose email id '{item['email']}' "
                        f"must be required and valid."
                    )
                email_wise_status.update(
                    {
                        item.get("email"): [
                            "Failed",
                            "Course must be required and valid.",
                        ]
                    }
                )
                unregistered_count += 1
                continue
            main_course = [course for course in course.get("course_specialization", []) if
                           course.get("is_activated") is True]
            lst_main = [i.get("spec_name") for i in main_course]
            if (
                    item.get("main_specialization") != ""
                    and item.get("main_specialization") is not None
            ):
                item["main_specialization"] = item.get(
                    "main_specialization").strip()
                if item.get("course") == "" or item.get("course") is None:
                    item["error"] = "Course must be required and valid."
                    failed_data_lead.append(item)
                    if filename.endswith(".csv"):
                        errors.append(
                            f"On line no {_id + 2}, course for student whose"
                            f" email id '{item['email']}' must be "
                            f"required and valid."
                        )
                    else:
                        errors.append(
                            f"Course for student whose email id "
                            f"'{item['email']}' must be required and valid."
                        )
                    email_wise_status.update(
                        {
                            item.get("email"): [
                                "Failed",
                                "Course must be required and valid.",
                            ]
                        }
                    )
                    unregistered_count += 1
                    continue

                if item.get("main_specialization"):
                    if item.get("main_specialization") not in lst_main:
                        item["error"] = "Specialization not found."
                        failed_data_lead.append(item)
                        if filename.endswith(".csv"):
                            errors.append(
                                f"On line no {_id + 2}, course main"
                                f" specialization for student"
                                f" whose email id '{item['email']}' not found. "
                            )
                        else:
                            errors.append(
                                f"Course main specialization for student"
                                f" whose email id '{item['email']}' not found."
                            )
                        email_wise_status.update(
                            {item.get("email"): ["Failed",
                                                 "Specialization not found."]}
                        )
                        unregistered_count += 1
                        continue
            else:
                if None not in lst_main:
                    item["error"] = "Main Specialization is required"
                    failed_data_lead.append(item)
                    if filename.endswith(".csv"):
                        errors.append(
                            f"On line no {_id + 2}, main specialization for "
                            f"student whose email id '{item['email']}' is "
                            f" required."
                        )
                    else:
                        errors.append(
                            f"Main specialization for student whose email id"
                            f" '{item.get('email')}' is required."
                        )
                    email_wise_status.update(
                        {
                            item.get("email"): [
                                "Failed",
                                "Main specialization is not provided.",
                            ]
                        }
                    )
                    unregistered_count += 1
                    continue

            if item.get("country_code") != "" and item.get(
                    "country_code") is not None:
                item["country_code"] = item.get("country_code").strip()
                try:
                    if (
                            DatabaseConfigurationSync(
                                "master").country_collection.find_one(
                                {"iso2": item.get("country_code", "").upper()}
                            )
                            is None
                    ):
                        item["error"] = "Country Code is not valid."
                        failed_data_lead.append(item)
                        if filename.endswith(".csv"):
                            errors.append(
                                f"On line no {_id + 2}, country code for "
                                f"student whose email id '{item['email']}' not "
                                f"valid."
                            )
                        else:
                            errors.append(
                                f"Country code for student whose email id"
                                f" '{item.get('email')}' not valid."
                            )
                        email_wise_status.update(
                            {
                                item.get("email"): [
                                    "Failed",
                                    "Country Code is not valid.",
                                ]
                            }
                        )
                        unregistered_count += 1
                        continue
                except BaseException as e:
                    item["error"] = f"Internal error: {e}."
                    failed_data_lead.append(item)
                    email_wise_status.update(
                        {item.get("email"): ["Failed",
                                             f"Internal error: {e}."]}
                    )
                    logger.error("Some error occurred", e)

            else:
                item["error"] = "Country code must be required and valid."
                failed_data_lead.append(item)
                if filename.endswith(".csv"):
                    errors.append(
                        f"On line no {_id + 2}, Country code for student"
                        f" whose email id '{item.get('email')}' must be "
                        f"required and valid."
                    )
                else:
                    errors.append(
                        f"Country code for student whose email id"
                        f" '{item.get('email')}' must be required and valid."
                    )
                email_wise_status.update(
                    {
                        item.get("email"): [
                            "Failed",
                            "Country code must be required and valid.",
                        ]
                    }
                )
                unregistered_count += 1
                continue
            if item.get("state_code") != "" and item.get(
                    "state_code") is not None:
                item["state_code"] = item.get("state_code").strip()
                try:
                    if (
                            DatabaseConfigurationSync(
                                "master").state_collection.find_one(
                                {
                                    "state_code": item.get("state_code",
                                                           "").upper(),
                                    "country_code": item.get("country_code",
                                                             "").upper(),
                                }
                            )
                            is None
                    ):
                        item["error"] = "State code is not valid."
                        failed_data_lead.append(item)
                        if filename.endswith(".csv"):
                            errors.append(
                                f"On line no {_id + 2}, state code for"
                                f" student whose email id '{item.get('email')}' "
                                f"not valid."
                            )
                        else:
                            errors.append(
                                f"State code for student whose email id"
                                f" '{item.get('email')}' not valid."
                            )
                        email_wise_status.update(
                            {item.get("email"): ["Failed",
                                                 "State code is not valid."]}
                        )
                        unregistered_count += 1
                        continue
                except BaseException as e:
                    item["error"] = f"Internal error: {e}."
                    failed_data_lead.append(item)
                    email_wise_status.update(
                        {item.get("email"): ["Failed",
                                             f"Internal error: {e}."]}
                    )
                    logger.error("Some error occurred", e)

            else:
                item["error"] = "State Code must required and valid."
                failed_data_lead.append(item)
                if filename.endswith(".csv"):
                    errors.append(
                        f"On line no {_id + 2}, state code for student"
                        f" whose email id '{item.get('email')}' must be "
                        f"required and valid."
                    )
                else:
                    errors.append(
                        f"State code for student whose email id"
                        f" '{item.get('email')}' must be required and valid."
                    )
                email_wise_status.update(
                    {
                        item.get("email"): [
                            "Failed",
                            "State Code must required and valid.",
                        ]
                    }
                )
                unregistered_count += 1
                continue
            if item.get("city") != "" and item.get("city") is not None:
                item["city"] = item.get("city").strip()
                try:
                    if (
                            DatabaseConfigurationSync(
                                "master").city_collection.find_one(
                                {
                                    "name": item.get("city", "").title(),
                                    "state_code": item.get("state_code",
                                                           "").upper(),
                                    "country_code": item.get("country_code",
                                                             "").upper(),
                                }
                            )
                            is None
                    ):
                        item["error"] = "City is not valid."
                        failed_data_lead.append(item)
                        if filename.endswith(".csv"):
                            errors.append(
                                f"On line no {_id + 2}, City for student whose"
                                f" email id '{item.get('email')}' not valid."
                            )
                        else:
                            errors.append(
                                f"City for student whose email id"
                                f" '{item.get('email')}' not valid."
                            )
                        email_wise_status.update(
                            {item.get("email"): ["Failed",
                                                 "City is not valid."]}
                        )
                        unregistered_count += 1
                        continue
                except BaseException as e:
                    item["error"] = f"Internal error: {e}."
                    failed_data_lead.append(item)
                    email_wise_status.update(
                        {item.get("email"): ["Failed",
                                             f"Internal error: {e}."]}
                    )
                    logger.error("Some error occurred", e)

            else:
                item["error"] = "City must be required and valid."
                failed_data_lead.append(item)
                if filename.endswith(".csv"):
                    errors.append(
                        f"On line no {_id + 2}, City for student whose"
                        f" email id '{item.get('email')}' must be "
                        f"required and valid."
                    )
                else:
                    errors.append(
                        f"City for student whose email id '{item.get('email')}'"
                        f" must be required and valid."
                    )
                email_wise_status.update(
                    {item.get("email"): ["Failed",
                                         "City must be required and valid."]}
                )
                unregistered_count += 1
                continue
            item.update(
                {
                    "college_id": (
                        str(college.get("id"))
                        if not is_created_by_user
                        else college.get("id")
                    ),
                    "utm_source": (
                        user.get("associated_source_value")
                        if not is_created_by_user
                        else item.get("utm_source")
                    ),
                }
            )
            if (
                    find_student := DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                        {
                            "$or": [
                                {"user_name": item.get("email")},
                                {
                                    "basic_details.mobile_number": str(
                                        item.get("mobile_number")
                                    )
                                },
                            ]
                        }
                    )
            ) is None:
                pass
            if find_student:
                logger.warning(
                    f"This student {item.get('email')} is" f" duplicated")
                duplicate_data_lead.append(item)
                social = {
                    "utm_source": (
                        user.get("associated_source_value")
                        if not is_created_by_user
                        else item.get("utm_source")
                    ),
                    "utm_campaign": item.get("utm_campaign"),
                    "utm_keyword": item.get("utm_keyword"),
                    "utm_medium": item.get("utm_medium"),
                    "referal_url": item.get("referal_url"),
                    "utm_enq_date": datetime.datetime.utcnow(),
                    "lead_type": "api",
                    "publisher_id": (
                        str(user.get(
                            "_id")) if not is_created_by_user else "NA"
                    ),
                    "is_created_by_user": is_created_by_user,
                    "uploaded_by": (
                        {
                            "user_id": user.get("_id"),
                            "user_type": user.get("role", {}).get("role_name"),
                        }
                        if is_created_by_user
                        else "NA"
                    ),
                }
                StudentUserCrudHelper().utm_source_data(
                    social, str(find_student.get("_id"))
                )
                already_exist_count += 1
                already_exist.append(
                    f"Student with email {item.get('email')} already exist"
                )
                email_wise_status.update(
                    {item.get("email"): ["Already Exist", "No Error"]}
                )
            else:
                try:
                    student = PublisherActivity().student_register(
                        item,
                        is_created_by_publisher=(
                            True if not is_created_by_user else False
                        ),
                        lead_type="api",
                        publisher_id=(
                            str(user.get(
                                "_id")) if not is_created_by_user else "NA"
                        ),
                        utm_source=(
                            user.get("associated_source_value")
                            if not is_created_by_user
                            else None
                        ),
                        is_created_by_user=is_created_by_user,
                        user_details=user,
                        ip_address=ip_address,
                        imported_id=offline_id,
                        counselor_id=counselor_id_assigned,
                    )
                    if not student:
                        logger.error(f"An error occur")
                        already_exist_count += 1
                        already_exist.append(
                            f"Student with email {item.get('email')} already exist"
                        )
                        email_wise_status.update(
                            {item.get("email"): ["Already Exist", "No Error"]}
                        )
                        duplicate_data_lead.append(item)
                        continue
                    registered_count += 1
                    student_ids.append(student.get("id"))
                    email_wise_status.update(
                        {
                            student.get("data", {}).get("user_name"): [
                                "Created",
                                "No Error"
                            ]
                        }
                    )
                except CustomError as error:
                    item["error"] = error.message
                    failed_data_lead.append(item)
                    email_wise_status.update(
                        {item.get("email"): ["Failed",
                                             item.get("error")]}
                    )
                except Exception as error:
                    logger.error(f"An error occur {item.get('email')} {error}")
                    already_exist_count += 1
                    already_exist.append(
                        f"Student with email {item.get('email')} {error}"
                    )
                    email_wise_status.update({item.get("email"): ["Failed", error]})
                    failed_data_lead.append(item)
                    continue

        logger.info(
            {
                "total_registered_students": registered_count,
                "total_unregistered_students": unregistered_count,
                "total_already_exist_students": already_exist_count,
                "registered_students_ids": student_ids if student_ids else None,
                "already_exist_students": already_exist if already_exist else 0,
                "publisher_name": (
                    utility_obj.name_can(
                        user) if not is_created_by_user else "NA"
                ),
                "publisher_id": (
                    str(user.get("_id")) if not is_created_by_user else "NA"
                ),
                "college_name": college.get("name"),
                "errors": errors if errors else None,
                "is_created_by_user": is_created_by_user,
                "uploaded_by": (
                    {
                        "user_id": user.get("_id"),
                        "user_type": user.get("role", {}).get("role_name"),
                    }
                    if is_created_by_user
                    else "NA"
                ),
            }
        )

        html_table = (
            "<table>\n<tr>\n<th>Email</th>\n<th>Status</th>\n<th>Error</th>\n</tr>\n"
        )
        for email, status_value in email_wise_status.items():
            try:
                status, error = status_value
            except ValueError:
                status = ""
                error = ""
            html_table += (
                f"<tr>\n<td>{email}</td>\n<td>{status}</td>\n<td>{error}</td>\n</tr>\n"
            )
        html_table += "</table>"

        toml_data = utility_obj.read_current_toml_file()
        if toml_data.get("testing", {}).get("test") is False:
            action_type = (
                "counselor"
                if user.get("role", {}).get("role_name") == "college_counselor"
                else "system"
            )
            # Do not move position of below statement at top otherwise
            # we'll get circular ImportError
            from app.background_task.send_mail_configuration import \
                EmailActivity

            EmailActivity().send_upload_leads_details(
                email=user.get("user_name"),
                first_name=user.get("first_name"),
                data=f"{html_table}<br>Summary :- <br>"
                     f"Total "
                     f"Registered "
                     f"Students: "
                     f"{registered_count}<br>Total"
                     f" Unregistered Students: {unregistered_count}<br>Total Already Exist "
                     f"Students: {already_exist_count}<br>",
                email_preferences=college.get("email_preferences"),
                ip_address=ip_address,
                action_type=action_type,
                college_id=college.get("id"),
            )
        DatabaseConfigurationSync().lead_upload_history.update_one(
            {"_id": ObjectId(offline_id)},
            {
                "$set": {
                    "duplicate_leads": len(duplicate_data_lead),
                    "duplicate_lead_data": duplicate_data_lead,
                    "failed_lead": len(failed_data_lead),
                    "failed_lead_data": failed_data_lead,
                    "successful_lead_count": registered_count,
                    "import_status": "completed",
                }
            },
        )
        sync_cache_invalidation(api_updated="student_user_crud/signup")
        logger.info(f"{filename} is processed and request completed")

    def student_register(
            self,
            user,
            is_created_by_publisher=False,
            already_exist=False,
            lead_type="online",
            publisher_id="NA",
            utm_source=None,
            is_created_by_user=False,
            user_details=None,
            background_task=False,
            ip_address=None,
            imported_id=None,
            background_tasks: BackgroundTasks = None,
            counselor_id=None,
            application_data=False,
    ):
        """
        Register student
        """

        # extract email from user
        email = user["email"].lower()
        user["email"] = email
        date_of_birth = user.get("date_of_birth")
        if date_of_birth not in [None, ""]:
            try:
                user["date_of_birth_utc"] = utility_obj.sync_date_change_utc(date_of_birth, date_format="%d-%m-%Y")
            except Exception:
                raise CustomError("Not able to convert date_of_birth into utc format. "
                                  "Correct date_of_birth format is %d-%m-%Y.")

        social = {
            "utm_source": (
                user.pop("utm_source").lower()
                if user.get("utm_source") is not None
                else "organic"
            ),
            "utm_campaign": (
                user.pop("utm_campaign")
                if user.get("utm_campaign") is not None
                else None
            ),
            "utm_keyword": (
                user.pop("utm_keyword") if user.get(
                    "utm_keyword") is not None else None
            ),
            "utm_medium": (
                user.pop("utm_medium") if user.get(
                    "utm_medium") is not None else None
            ),
            "referal_url": (
                user.pop("referal_url") if user.get(
                    "referal_url") is not None else None
            ),
            "utm_enq_date": datetime.datetime.utcnow(),
            "lead_type": lead_type,
            "publisher_id": (
                ObjectId(
                    publisher_id) if publisher_id != "NA" else publisher_id
            ),
            "is_created_by_user": is_created_by_user,
            "uploaded_by": (
                {
                    "user_id": user_details.get("_id"),
                    "user_type": user_details.get("role", {}).get("role_name"),
                }
                if user_details
                else "NA"
            ),
        }
        if utm_source is not None:
            social["utm_source"] = utm_source.lower()
        if social.get("utm_source") and social.get("utm_source") != "":
            StudentUserCrudHelper().utm_source_data(
                social=social, user_id=None, email=email
            )
        else:
            social["utm_source"] = "organic"
        if (
                DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                    {"user_name": email}
                )
                is not None
        ):
            raise HTTPException(status_code=422,
                                detail=f"Email already exists.")
        if (
                DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                    {"basic_details.mobile_number": str(
                        user.get("mobile_number"))}
                )
                is not None
        ):
            raise HTTPException(
                status_code=422, detail=f"Mobile number already exists."
            )
        else:
            add = {
                "country_code": (
                    user.pop("country_code")
                    if user.get("country_code") is not None
                    else None
                ),
                "state_code": (
                    user.pop("state_code")
                    if user.get("state_code") is not None
                    else None
                ),
                "city": user.pop("city") if user.get(
                    "city") is not None else None,
                "address_line1": (
                    user.pop("address_line1")
                    if user.get("address_line1") is not None
                    else ""
                ),
                "address_line2": (
                    user.pop("address_line2")
                    if user.get("address_line2") is not None
                    else ""
                ),
                "pincode": (
                    user.pop("pincode") if user.get(
                        "pincode") is not None else ""
                ),
            }
            address = self.address_update(add)

            toml_data = utility_obj.read_current_toml_file()
            if toml_data.get("testing", {}).get("test") is True:
                # for testing , set hardcoded pwd during registration
                password1 = "getmein"
            else:
                # generate random password
                password1 = utility_obj.random_pass()
            # encrypt hash password
            password2 = Hash().get_password_hash(password1)
            # insert password in user
            college_id = (
                user.pop("college_id") if user.get(
                    "college_id") is not None else None
            )
            if len(college_id) != 24:
                raise HTTPException(
                    status_code=403,
                    detail="college_id must be a 12-byte input "
                           "or a 24-character hex string",
                )
            if (
                    college := DatabaseConfigurationSync(
                        "master"
                    ).college_collection.find_one(
                        {"_id": ObjectId(college_id)})
            ) is None:
                raise HTTPException(status_code=404,
                                    detail="college not found")
            course = {
                "course": (
                    user.pop("course") if user.get(
                        "course") is not None else None
                ),
                "main": (
                    user.pop("main_specialization")
                    if user.get("main_specialization") is not None
                    else None
                ),
            }
            self.checking_main_course(course)
            user = utility_obj.break_name(user)
            user["mobile_number"] = str(user.get("mobile_number"))
            data = {
                "user_name": email,
                "password": password2,
                "college_id": ObjectId(college_id),
                "basic_details": user,
                "address_details": {"communication_address": address},
                "is_verify": False,
                "last_accessed": datetime.datetime.utcnow(),
                "created_at": datetime.datetime.utcnow(),
                "is_created_by_publisher": is_created_by_publisher,
                "publisher_id": (
                    ObjectId(
                        publisher_id) if publisher_id != "NA" else publisher_id
                ),
                "unsubscribe": {"value": False},
                "is_created_by_user": is_created_by_user,
                "uploaded_by": (
                    {
                        "user_id": user_details.get("_id"),
                        "user_type": user_details.get("role", {}).get(
                            "role_name"),
                    }
                    if user_details
                    else "NA"
                ),
                "source": {"primary_source": social},
            }
            extra_fields = user.get("extra_fields", {})
            if len(extra_fields) > 0:
                data["extra_fields"] = extra_fields
            if imported_id is not None:
                data["lead_data_id"] = imported_id
            # insert data in database
            if (
                    check := DatabaseConfigurationSync().studentsPrimaryDetails.insert_one(
                        data
                    )
            ) is not None:
                # For Billing Dashboard
                DatabaseConfigurationSync("master").college_collection.update_one(
                    {"_id": ObjectId(college_id)}, {"$inc": {"usages.lead_registered": 1}}
                )
                data = {
                    "id": str(check.inserted_id),
                    "user_name": email,
                    "password": password1,
                    "first_name": user["first_name"],
                    "mobile_number": user["mobile_number"],
                }
                utm_source = social.get("utm_source")
                special = self.update_special_course(
                    str(check.inserted_id),
                    course["main"],
                    course["course"],
                    is_created_by_publisher=is_created_by_publisher,
                    college_id=college_id,
                    publisher_id=publisher_id,
                    is_created_by_user=is_created_by_user,
                    user_details=user_details,
                    round_robin=True,
                    state_code=address.get("state", {}).get("state_code"),
                    source_name=utm_source,
                    counselor_id=counselor_id,
                    is_signup=True,
                    system_preference=college.get("system_preference"),
                )
                if special:
                    toml_data = utility_obj.read_current_toml_file()
                    email_preferences = {
                        key: str(val)
                        for key, val in
                        college.get("email_preferences", {}).items()
                    }
                    if (
                            toml_data.get("testing", {}).get("test") is False
                            and background_tasks
                    ):
                        send_mail_config().send_mail(
                            data=data,
                            event_type="email",
                            event_status="sent",
                            event_name="Verification",
                            payload={
                                "content": "student signup send token for "
                                           "verification mail",
                                "email_list": [user.get("email")],
                            },
                            current_user=user.get("email"),
                            ip_address=ip_address,
                            email_preferences=email_preferences,
                            college_id=college_id,
                        )  # Send mail to user only in
                        # production code. skip for testcases
                    return {"id": str(check.inserted_id), "data": data}
                raise HTTPException(status_code=422,
                                    detail="course not inserted")
            return False

    def update_special_course(
            self,
            _id: str,
            main: str,
            course,
            secondary=None,
            is_created_by_publisher=False,
            college_id=None,
            publisher_id=None,
            is_created_by_user=False,
            user_details=None,
            round_robin=False,
            state_code=None,
            source_name=None,
            counselor_id=None,
            is_signup=False,
            system_preference: dict | None = None,
            preference_info: list | None = None,
            campaign=None,
            medium=None,
    ):
        """
        Update the details of special courses
        """
        new_app_create = False
        if (
                find_course := DatabaseConfigurationSync().course_collection.find_one(
                    {"course_name": course}
                )
        ) is None:
            raise HTTPException(status_code=404, detail="course not found.")
        data = {"spec_name1": "", "spec_name2": "", "spec_name3": ""}
        course_spec = []
        if system_preference and system_preference.get("preference") and not preference_info:
            preference_info = [main]
        if find_course.get("course_specialization"):
            main_course = find_course["course_specialization"]
            lst_main = [i["spec_name"] for i in main_course]
            all_main = [main, secondary]  if not preference_info \
                else preference_info
            if main:
                if main == secondary:
                    raise HTTPException(
                        status_code=422, detail="specialization is duplicated"
                    )
            for i in all_main:
                if i in lst_main:
                    d = [
                        main_course[core]
                        for core in range(len(main_course))
                        if i == main_course[core]["spec_name"]
                    ]
                    course_spec.append(d[0])
            if secondary is not None:
                if len(course_spec) < 2:
                    raise HTTPException(
                        status_code=404,
                        detail="special course not found in this course",
                    )
            spec = ["spec_name1", "spec_name2", "spec_name3"]
            for i in range(len(course_spec)):
                data[spec[i]] = course_spec[i].get("spec_name")
                for j in range(len(course_spec), 3):
                    data[spec[j]] = ""
        current_datetime = datetime.datetime.utcnow()
        application_query = {
            "course_id": ObjectId(find_course.get("_id")),
            "student_id": ObjectId(_id),
        }
        if not system_preference or (system_preference and
                                     system_preference.get(
                                         "preference") is False):
            application_query.update({"spec_name1": main})
        if preference_info:
            data["preference_info"] = preference_info
        if (
                check_application := DatabaseConfigurationSync().studentApplicationForms.find_one(
                    application_query
                )
        ) is not None:
            data["last_updated_time"] = current_datetime
            if check_application.get("spec_name1", "") != data.get(
                    "spec_name1", ""):
                data["custom_application_id"] = StudentUserCrudHelper().get_custom_application_id(
                   course, find_course["_id"], data.get("spec_name1", None)
                )
            DatabaseConfigurationSync().studentApplicationForms.update_one(
                {"_id": ObjectId(check_application["_id"])}, {"$set": data}
            )
            app_id = check_application["_id"]
            counselor_allocate = False
        else:
            data.update(
                {
                    "student_id": ObjectId(_id),
                    "course_id": ObjectId(find_course.get("_id")),
                    "college_id": ObjectId(college_id),
                    "current_stage": 1.25,
                    "declaration": False,
                    "payment_initiated": False,
                    "payment_info": {"payment_id": "", "status": ""},
                    "enquiry_date": current_datetime,
                    "last_updated_time": current_datetime,
                    "school_name": find_course.get("school_name", ""),
                    "is_created_by_publisher": is_created_by_publisher,
                    "is_created_by_user": is_created_by_user,
                    "custom_application_id": StudentUserCrudHelper().get_custom_application_id(
                        course, find_course["_id"], main
                    )
                }
            )
            if is_created_by_publisher:
                data["publisher_id"] = ObjectId(publisher_id)
            if is_created_by_user:
                data["uploaded_by"] = {
                    "user_id": user_details.get("_id"),
                    "user_type": user_details.get("role", {}).get("role_name"),
                }
            counselor_allocate = True
            if (
                    course_getting := DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                        {"_id": ObjectId(_id)}
                    )
            ) is None:
                raise HTTPException(
                    status_code=404,
                    detail="You have not registered with us, please register.",
                )
            data["source"] = course_getting.get("source")
            if (
                    check := DatabaseConfigurationSync().studentApplicationForms.insert_one(
                        data
                    )
            ) is not None:
                app_id = check.inserted_id
                new_app_create = True

        data1 = dict()
        data = {
            find_course["course_name"]: {
                "course_id": ObjectId(find_course["_id"]),
                "course_name": find_course["course_name"],
                "application_id": app_id,
                "status": "Incomplete",
                "specs": course_spec if course_spec is not None else None,
            }
        }
        data2 = course_getting.get("course_details", None)
        if data2 is not None:
            course_name = find_course.get("course_name")
            if course_name in data2:
                course_specs = data2.get(course_name).get("specs", [])
                add_spec = [course_spec[0]]
                spec_found = False
                for item in course_specs:
                    if add_spec[0].get("spec_name") == item.get("spec_name"):
                        spec_found = True
                        break
                if spec_found is False:
                    course_specs = add_spec + course_specs
                    data2.get(course_name).update({"specs": course_specs})
                data1["course_details"] = data2
            else:
                data2.update(data)
                data1["course_details"] = data2
        else:
            data1["course_details"] = data
        if preference_info:
            exist_preference_info = course_getting.get("preference_info")
            if exist_preference_info:
                exist_preference_info.update({find_course["course_name"]: course_spec})
                data1["preference_info"] = exist_preference_info
            else:
                data1["preference_info"] = {find_course["course_name"]: course_spec}
        store_data = DatabaseConfigurationSync().studentsPrimaryDetails.update_one(
            {"_id": ObjectId(_id)}, {"$set": data1}
        )
        if store_data:
            if round_robin:
                if counselor_allocate:
                    name = utility_obj.name_can(
                        course_getting.get("basic_details", {})
                    )
                    message = (
                        f"{name} has filled the enquiry form"
                        f" for the programme: {course}"
                        f" - {main} from "
                        f"{source_name} - {medium} - {campaign}"
                    )

                    StudentActivity().student_timeline(
                        student_id=_id,
                        event_status="enquiry",
                        message=message,
                        college_id=college_id,
                    )
            current_user = user_details.get("user_name")
            if not counselor_id:
                if user_details.get("role", {}).get("role_name") == "college_counselor":
                    counselor_id = user_details.get("_id")

            self.allocate_counselor(
                application_id=app_id,
                current_user=current_user,
                counselor_id=counselor_id,
                state_code=state_code,
                source_name=source_name,
                specialization=main,
                course=course,
            )
            if new_app_create and not is_signup:
                basic_details = course_getting.get("basic_details", {})
                loop = asyncio.get_running_loop()
                asyncio.run_coroutine_threadsafe(
                    utility_obj.update_notification_db(
                        event="New Application Form",
                        application_id=str(app_id),
                        data={
                            "message": f"<span class='notification-inner'>"
                                       f"{utility_obj.name_can(basic_details)}"
                                       f"</span> with mobile number "
                                       f"<span class='notification-inner'>"
                                       f"{basic_details.get('mobile_number')}"
                                       f"</span> started to fill a new "
                                       f"application"
                                       f" for "
                                       f"{course if main in ['', None] else f'{course} ({main})'}"
                        },
                    ),
                    loop,
                )
            return True
        return False

    def allocate_counselor(
            self,
            application_id: str,
            current_user=None,
            counselor_id=None,
            state_code=None,
            source_name=None,
            course=None,
            specialization=None
    ):
        """
        Allocate the counselor_id
        """
        try:
            if (
                    student_application := DatabaseConfigurationSync().studentApplicationForms.find_one(
                        {"_id": ObjectId(application_id)}
                    )
            ) is None:
                raise HTTPException(status_code=404,
                                    detail="application not found")
        except Exception:
            raise HTTPException(status_code=403,
                                detail="application_id not valid")
        if (
                student := DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(
                        str(student_application.get("student_id")))}
                )
        ) is None:
            raise HTTPException(status_code=404, detail="student not found")
        if counselor_id is None:
            if source_name == "organic":
                source_name = None
            counselors = []
            pipeline = [{"$match": {"is_activated": True, "$expr": {
                "$in": [ObjectId(student_application.get("college_id")),
                        {"$ifNull": ["$associated_colleges", []]}, ]}, }}]
            if course is not None:
                pipeline[0].get("$match", {}).update({"course_assign": course})
            if specialization is not None:
                pipeline[0].get("$match", {}).update(
                    {"specialization_name.spec_name": specialization})
            if source_name is not None:
                pipeline[0].get("$match", {}).update(
                    {"source_assign": source_name})
            counselor_details = DatabaseConfigurationSync(
                'master').user_collection.aggregate(
                pipeline)
            for data in counselor_details:
                count = DatabaseConfigurationSync().studentsPrimaryDetails.count_documents(
                    {"allocate_to_counselor.counselor_id": data.get("_id")})
                if data.get("fresh_lead_limit"):
                    if data.get("fresh_lead_limit", 0) > count:
                        counselors.append(data)
            if len(counselors) == 0:
                pipeline = [{"$match": {"is_activated": True,
                                        "fresh_lead_limit": {"$exists": True},
                                        "specialization_name.spec_name": {
                                            "$exists": False},
                                        "source_assign": {"$exists": False},
                                        "state_assign": {"$exists": False},
                                        "course_assign": {"$exists": False},
                                        "$expr": {"$in": [
                                            ObjectId(student_application.get(
                                                "college_id")),
                                            {"$ifNull": [
                                                "$associated_colleges",
                                                []]}, ]}, }}]
                counselor_details = DatabaseConfigurationSync(
                    'master').user_collection.aggregate(
                    pipeline)
                for data in counselor_details:
                    count = DatabaseConfigurationSync().studentsPrimaryDetails.count_documents(
                        {"allocate_to_counselor.counselor_id": data.get(
                            "_id")})
                    if data.get("fresh_lead_limit"):
                        if data.get("fresh_lead_limit", 0) > count:
                            counselors.append(data)
            if len(counselors) == 0:
                counselors = self.get_counselor_list(
                    student=student, state_code=state_code,
                    course=course, source_name=source_name,
                    specialization=specialization,
                    college_id=str(student_application.get("college_id")), )
            active_counselor = self.active_counselors(counselors,
                                                      state_code)
            if len(active_counselor) < 1:
                counselors = list(DatabaseConfigurationSync(
                    "master").user_collection.aggregate(
                    [
                        {
                            "$match": {
                                "course_assign ": {"$exists": False},
                                "role.role_name": "college_counselor",
                                "state_assign": {"$exists": False},
                                "is_activated": True,
                                "source_assign": {"$exists": False},
                                "$expr": {
                                    "$in": [
                                        ObjectId(
                                            student_application.get("college_id")),
                                        {"$ifNull": ["$associated_colleges", []]},
                                    ]
                                }
                            }
                        }
                    ]
                ))
                active_counselor = self.active_counselors(counselors)
            data = sorted(active_counselor,
                          key=lambda x: x.get("last_activity"))
            if len(data) == 0:
                return 0
            final_value = {"counselor_id": ObjectId(data[0].get("id")),
                           "counselor_name": data[0].get("name"),
                           "last_update": datetime.datetime.utcnow(), }
            DatabaseConfigurationSync('master').user_collection.update_one(
                {"_id": ObjectId(data[0].get("id"))},
                {"$set": {"last_activity": datetime.datetime.utcnow()}},
            )
            sync_cache_invalidation(api_updated="updated_user", user_id=data[0].get("email"))
            counselor = DatabaseConfigurationSync(
                "master").user_collection.find_one(
                {"_id": ObjectId(ObjectId(data[0].get("id")))}
            )
            data = {
                "assigned_counselor_id": ObjectId(data[0].get("id")),
                "assigned_counselor_name": data[0].get("name"),
                "lead_stage": "Fresh Lead",
                "timestamp": datetime.datetime.utcnow(),
                "user_id": ObjectId(str(student.get("_id"))),
                "added_by": utility_obj.name_can(student.get("basic_details")),
            }
            lead_followup_data = {
                "student_id": ObjectId(str(student.get("_id"))),
                "application_id": ObjectId(application_id),
                "lead_stage": "Fresh Lead",
            }
            if (
                    DatabaseConfigurationSync().leadsFollowUp.find_one(
                        lead_followup_data
                    )
            ) is None:
                DatabaseConfigurationSync().leadsFollowUp.insert_one(
                    lead_followup_data
                )
        else:
            if (
                    user := DatabaseConfigurationSync(
                        "master").user_collection.find_one(
                        {"user_name": current_user}
                    )
            ) is None:
                raise HTTPException(status_code=404, detail="user not found")
            if (
                    counselor := DatabaseConfigurationSync(
                        "master"
                    ).user_collection.find_one({"_id": ObjectId(counselor_id)})
            ) is None:
                raise HTTPException(status_code=404,
                                    detail="counselor not found")
            final_value = {
                "counselor_id": ObjectId(str(counselor.get("_id"))),
                "counselor_name": utility_obj.name_can(counselor),
                "last_update": datetime.datetime.utcnow(),
            }
            if (
                    lead := DatabaseConfigurationSync().leadsFollowUp.find_one(
                        {"application_id": ObjectId(application_id)}
                    )
            ) is not None:
                lead.get("counselor_timeline", []).insert(
                    0,
                    {
                        "assigned_counselor_id": ObjectId(
                            str(counselor.get("_id"))),
                        "assigned_counselor_name": utility_obj.name_can(
                            counselor),
                        "lead_stage": "Fresh Lead",
                        "timestamp": datetime.datetime.utcnow(),
                        "user_id": ObjectId(str(user.get("_id"))),
                        "added_by": utility_obj.name_can(user),
                    },
                )
                temp = lead.get("counselor_timeline", [])
                DatabaseConfigurationSync().leadsFollowUp.update_one(
                    {"application_id": ObjectId(application_id)},
                    {"$set": {"counselor_timeline": temp}},
                )
            else:
                data_temp = {
                    "assigned_counselor_id": ObjectId(counselor.get("_id")),
                    "assigned_counselor_name": utility_obj.name_can(counselor),
                    "lead_stage": "Fresh Lead",
                    "timestamp": datetime.datetime.utcnow(),
                    "user_id": ObjectId(str(user.get("_id"))),
                    "added_by": utility_obj.name_can(user)}
                DatabaseConfigurationSync().leadsFollowUp.insert_one(
                    {"student_id": ObjectId(str(student.get("_id"))),
                     "application_id": ObjectId(application_id),
                     "lead_stage": "Fresh Lead",
                     "counselor_timeline": [data_temp]})
        data = {"allocate_to_counselor": final_value}
        DatabaseConfigurationSync().studentsPrimaryDetails.update_one(
            {"_id": ObjectId(str(student.get("_id")))}, {"$set": data}
        )
        DatabaseConfigurationSync().studentApplicationForms.update_one(
            {"_id": ObjectId(application_id)}, {"$set": data}
        )
        course = DatabaseConfigurationSync().course_collection.find_one(
            {"_id": student_application.get("course_id")}
        )
        if course is None:
            course = {}

        course_name = (
            f"{course.get('course_name')} in {student_application.get('spec_name1')}"
            if student_application.get("spec_name1") not in ["", None]
            else f"{course.get('course_name')} Program"
        )
        if not is_testing_env():
            StudentActivity().student_timeline(
                student_id=str(student.get("_id")),
                event_type="Application",
                event_status=f"Allocated Counselor",
                application_id=str(student_application.get("_id")),
                message=f"Allocated Counselor whose name: "
                        f"{utility_obj.name_can(counselor)} "
                        f"Program name {course_name}",
                college_id=str(student_application.get("college_id")),
            )
        return True

    def address_update(self, address_detail: dict, dynamic=False):
        """
        Updates the address of user
        """
        if (
                find_country := DatabaseConfigurationSync(
                    "master"
                ).country_collection.find_one(
                    {"iso2": address_detail.get("country_code", "").upper()}
                )
        ) is None:
            raise HTTPException(status_code=422,
                                detail="Enter valid Country name.")
        if (
                find_state := DatabaseConfigurationSync(
                    "master").state_collection.find_one(
                    {
                        "state_code": address_detail.get("state_code",
                                                         "").upper(),
                        "country_code": address_detail.get("country_code",
                                                           "").upper(),
                    }
                )
        ) is None:
            if dynamic:
                find_state = {}
            else:
                raise HTTPException(status_code=422,
                                    detail="Enter valid State name.")
        if (
                find_city := DatabaseConfigurationSync(
                    "master").city_collection.find_one(
                    {
                        "name": address_detail.get("city", "").title(),
                        "country_code": address_detail.get("country_code",
                                                           "").upper(),
                        "state_code": address_detail.get("state_code",
                                                         "").upper(),
                    }
                )
        ) is None:
            if dynamic:
                find_city = {}
            else:
                raise HTTPException(status_code=422, detail="city not found.")
        address = {
            "country": {
                "country_id": find_country.get("_id"),
                "country_code": address_detail.get("country_code").upper(),
                "country_name": find_country.get("name", ""),
            },
            "state": {
                "state_id": find_state.get("_id", ""),
                "state_code": address_detail.get("state_code", "").upper(),
                "state_name": find_state.get("name", ""),
            },
            "city": {
                "city_id": find_city.get("_id"),
                "city_name": address_detail.get("city", "").title(),
            },
            "address_line1": address_detail.get("address_line1", ""),
            "address_line2": address_detail.get("address_line2", ""),
            "pincode": address_detail.get("pincode", ""),
        }
        return address

    def associated(self, item):
        """
        Get the list of data
        """
        return [str(i) for i in item]

    def college_counselor_serialize(self, item):
        """
        Get the details of college counselor
        """
        return {
            "id": str(item.get("_id")),
            "name": utility_obj.name_can(item),
            "last_activity": item.get(
                "last_activity",
                datetime.datetime.strptime("2022-08-15 01:55:19",
                                           "%Y-%m-%d %H:%M:%S"),
            ),
            "associated_colleges": self.associated(
                item.get("associated_colleges")),
        }

    def filter_counselor(self, item):
        """
        Filter all activated college counselor
        """
        today = str(
            utility_obj.local_time_for_compare(
                datetime.datetime.utcnow().strftime("%d-%m-%Y %H:%M:%S")
            ).date()
        )
        count = 0
        for index in range(len(item)):
            if (
                    counselor_man := DatabaseConfigurationSync().counselor_management.find_one(
                        {"counselor_id": ObjectId(item[count].get("id"))}
                    )
            ) is not None:
                if today in counselor_man.get("no_allocation_date", []):
                    item.pop(count)
                else:
                    count += 1
            else:
                count += 1
        return item

    def get_counselor_list(
            self,
            student,
            state_code=None,
            course=None,
            source_name=None,
            college_id=None,
            specialization=None
    ):
        """
        get counselor list based on state, course and source parameter
        """
        if state_code is not None:
            counselors = list(
                DatabaseConfigurationSync('master').user_collection.aggregate(
                    [{
                        "$match":
                            {"course_assign": {"$in": [course]},
                                "role.role_name": "college_counselor",
                                "state_assign": {"$in": [state_code]},
                                "is_activated": True,
                                "source_assign": {"$in": [source_name]}, "$expr": {
                                "$in": [ObjectId(college_id), {
                                    "$ifNull": ["$associated_colleges",
                                        []]}, ]}, }}]))
            if len(counselors) == 0:
                counselors = list(
                    DatabaseConfigurationSync('master').user_collection.aggregate(
                        [
                            {"$match":
                                {"course_assign": {"$exists": False},
                                    "role.role_name": "college_counselor",
                                    "state_assign": {"$exists": False},
                                    "is_activated": True,
                                    "specialization_name.spec_name": {"exists": False},
                                    "source_assign": {"$in": [source_name]}, "$expr": {
                                    "$in": [ObjectId(college_id), {
                                        "$ifNull": ["$associated_colleges",
                                            []]}, ]}, }}]))
                if len(counselors) == 0:
                    counselors = list(
                        DatabaseConfigurationSync("master").user_collection.aggregate(
                            [
                                {"$match": {"role.role_name": "college_counselor",
                                            "is_activated": True,
                                            "state_assign": {"$in": [state_code]},
                                            "course_assign": {"$exists": False},
                                            "source_assign": {"$in": [source_name]},
                                            "$expr": {
                                                "$in": [
                                                    ObjectId(college_id),
                                                    {"$ifNull": ["$associated_colleges",
                                                                    []]},
                                                    ]
                                                },
                                            }
                                }
                            ]
                        )
                    )
                    if len(counselors) == 0:
                        counselors = list(
                            DatabaseConfigurationSync(
                                "master").user_collection.aggregate(
                                [
                                    {"$match": {
                                        "role.role_name": "college_counselor",
                                        "is_activated": True,
                                        "state_assign": {"$in": [state_code]},
                                        "source_assign": {"$exists": False},
                                        "course_assign": {"$exists": False},
                                        "$expr": {
                                            "$in": [
                                                ObjectId(college_id),
                                                {"$ifNull": [
                                                    "$associated_colleges", []]},
                                            ]
                                        },
                                    }
                                    }
                                ]
                            )
                        )
                        if len(counselors) == 0:
                            counselors = list(
                                DatabaseConfigurationSync("master").user_collection.aggregate(
                                    [
                                        {"$match": {
                                            "role.role_name": "college_counselor",
                                            "is_activated": True,
                                            "course_assign": {"$in": [course]},
                                            "state_assign": {"$exists": False},
                                            "source_assign": {
                                                "$in": [source_name]},
                                            "$expr": {
                                                "$in": [
                                                    ObjectId(college_id),
                                                    {
                                                        "$ifNull": [
                                                            "$associated_colleges",
                                                            [],
                                                        ]
                                                    },
                                                ]
                                            },
                                        }
                                        }
                                    ]
                                )
                            )
                            if len(counselors) == 0:
                                counselors = list(
                                    DatabaseConfigurationSync("master").user_collection.aggregate(
                                        [
                                            {"$match": {
                                                "role.role_name": "college_counselor",
                                                "is_activated": True,
                                                "course_assign": {"$in": [course]},
                                                "state_assign": {"$exists": False},
                                                "source_assign": {
                                                    "$exists": False},
                                                "$expr": {
                                                    "$in": [
                                                        ObjectId(college_id),
                                                        {
                                                            "$ifNull": [
                                                                "$associated_colleges",
                                                                [],
                                                            ]
                                                        },
                                                    ]
                                                },
                                            }
                                            }
                                        ]
                                    )
                                )
                                if len(counselors) == 0:
                                    counselors = list(
                                        DatabaseConfigurationSync(
                                            "master"
                                        ).user_collection.aggregate(
                                            [
                                                {"$match":{
                                                    "role.role_name": "college_counselor",
                                                    "is_activated": True,
                                                    "source_assign": {
                                                        "$in": [source_name]},
                                                    "course_assign": {
                                                        "$exists": False},
                                                    "state_assign": {
                                                        "$exists": False},
                                                    "$expr": {
                                                        "$in": [
                                                            ObjectId(college_id),
                                                            {
                                                                "$ifNull": [
                                                                    "$associated_colleges",
                                                                    [],
                                                                ]
                                                            },
                                                        ]
                                                    },
                                                }
                                                }
                                            ]
                                        )
                                    )
                                if len(counselors) == 0:
                                    counselors = list(
                                        DatabaseConfigurationSync(
                                            'master').user_collection.aggregate(
                                            [
                                                {"$match": {
                                                    "role.role_name": "college_counselor",
                                                    "is_activated": True,
                                                    "course_assign": {
                                                        "$in": [course]},
                                                    "specialization_name.spec_name": {
                                                        "$in": [specialization]},
                                                    "state_assign": {
                                                        "$exists": False},
                                                    "source_assign": {
                                                        "$exists": False},
                                                    "$expr": {"$in": [
                                                        ObjectId(college_id), {
                                                            "$ifNull": [
                                                                "$associated_colleges",
                                                                [], ]}, ]}, }
                                                }
                                            ]))
                                    if len(counselors) == 0:
                                        counselors = list(
                                            DatabaseConfigurationSync(
                                                'master').user_collection.aggregate(
                                                [
                                                    {"$match": {
                                                        "role.role_name": "college_counselor",
                                                        "is_activated": True,
                                                        "course_assign": {
                                                            "$in": [course]},
                                                        "state_assign": {
                                                            "$exists": False},
                                                        "source_assign": {
                                                            "$exists": False},
                                                        "$expr": {"$in": [
                                                            ObjectId(college_id), {
                                                                "$ifNull": [
                                                                    "$associated_colleges",
                                                                    [], ]}, ]}, }
                                                    }
                                                ]))
                                        if len(counselors) == 0:
                                            counselors = list(
                                                DatabaseConfigurationSync(
                                                    'master').user_collection.aggregate(
                                                    [{"$match": {
                                                        "role.role_name": "college_counselor",
                                                        "is_activated": True,
                                                        "source_assign": {
                                                            "$in": [
                                                                source_name]},
                                                        "course_assign": {
                                                            "$exists": False},
                                                        "state_assign": {
                                                            "$exists": False},
                                                        "$expr": {"$in": [
                                                            ObjectId(
                                                                college_id), {
                                                                "$ifNull": [
                                                                    "$associated_colleges",
                                                                    [], ]}, ]}, }
                                                      }]))
                                            if len(counselors) == 0:
                                                counselors = list(
                                                    DatabaseConfigurationSync(
                                                        'master').user_collection.aggregate(
                                                    [{"$match": {"course_assign": {
                                                            "$exists": False},
                                                            "role.role_name": "college_counselor",
                                                            "state_assign": {
                                                                "$exists": False},
                                                            "is_activated": True,
                                                            "source_assign": {
                                                                "$exists": False},
                                                            "$expr": {"$in": [
                                                                ObjectId(
                                                                    college_id),
                                                                {"$ifNull": [
                                                                    "$associated_colleges",
                                                                    [], ]}, ]}, }
                                                      }
                                                    ]))
        else:
            course_name = list(student["course_details"].keys())[0]
            if (
                    course := DatabaseConfigurationSync().course_collection.find_one(
                        {"course_name": course_name,
                         "course_counselor": {"$exists": True}}
                    )
            ) is not None:
                course_counselors = course["course_counselor"]
                counselors = list(
                    DatabaseConfigurationSync('master').user_collection.aggregate(
                        [{"$match": {"_id": {"$in": course_counselors},
                         "is_activated": True, "$expr": {
                            "$in": [ObjectId(college_id), {
                                "$ifNull": ["$associated_colleges",
                                            []]}, ]}, }
                          }]))
            else:
                counselors = list(DatabaseConfigurationSync(
                    "master").user_collection.aggregate(
                    [{"$match": {
                        "role.role_name": "college_counselor",
                        "course_assign": {"$exists": False},
                        "is_activated": True,
                        "$expr": {
                            "$in": [
                                ObjectId(college_id),
                                {"$ifNull": ["$associated_colleges", []]},
                            ]
                        },
                    }
                    }]
                ))
        return counselors

    def active_counselors(self, counselors, state_code=None):
        """
        Get the active counselor list
        """
        college_counselor = [self.college_counselor_serialize(j) for j in
                             counselors]
        counselors = self.filter_counselor(college_counselor)
        return counselors

    def checking_main_course(self, course):
        """
        Check whether main_course is present in lst_main or not
        """
        course1 = course.get("course")
        main = course.get("main")
        if (
                find_course := DatabaseConfigurationSync().course_collection.find_one(
                    {"course_name": course1}
                )
        ) is None:
            raise HTTPException(status_code=404, detail="course not found.")
        main_course = find_course["course_specialization"]
        if main_course:
            lst_main = [i["spec_name"] for i in main_course]
            if main not in lst_main:
                raise HTTPException(
                    status_code=404,
                    detail="main specialization not found in this course",
                )
        elif main_course is None and (main is not None and main != ""):
            raise HTTPException(
                status_code=404,
                detail="main specialization not found in this course"
            )
        return True
