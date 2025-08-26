"""
This file contain class and  functions related to student user crud operations
"""
import asyncio
import json
from datetime import datetime

from bson.objectid import ObjectId
from email_validator import EmailNotValidError, validate_email
from fastapi import BackgroundTasks
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError
from pymongo.errors import DuplicateKeyError

from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.background_task_logging import background_task_wrapper
from app.core.custom_error import DataNotFoundError, CustomError, NotEnoughPermission
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.database.configuration import DatabaseConfiguration
from app.database.database_sync import DatabaseConfigurationSync
from app.database.motor_base_singleton import MotorBaseSingleton
from app.dependencies.hashing import Hash
from app.helpers.counselor_deshboard.counselor import CounselorDashboardHelper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.serialize import StudentCourse

logger = get_logger(__name__)

class StudentUserCrudHelper:
    """
    Contain functions related to student user CRUD operation configuration
    """

    async def address_update(self, address_detail: dict, dynamic=False):
        """
        Updates the address of user
        """
        from app.dependencies.oauth import (
            get_collection_from_cache,
            store_collection_in_cache,
        )

        countries = await get_collection_from_cache(collection_name="countries")
        if countries:
            find_country = utility_obj.search_for_document(
                countries,
                field="iso2",
                search_name=address_detail.get("country_code", "").upper(),
            )
        else:
            find_country = await DatabaseConfiguration().country_collection.find_one(
                {"iso2": address_detail.get("country_code", "").upper()}
            )
            countries = (
                await DatabaseConfiguration()
                .country_collection.aggregate([])
                .to_list(None)
            )
            await store_collection_in_cache(collection=countries, collection_name="countries")
        if not find_country:
            raise HTTPException(status_code=422, detail="Enter valid Country name.")
        states = await get_collection_from_cache(collection_name="states")
        if states:
            find_state = utility_obj.search_for_document_two_fields(
                states,
                field1="state_code",
                field1_search_name=address_detail.get("state_code",
                                                      "").upper(),
                field2="country_code",
                field2_search_name=address_detail.get("country_code",
                                                      "").upper(),
            )
        else:
            find_state = await DatabaseConfiguration().state_collection.find_one(
                {
                    "state_code": address_detail.get("state_code", "").upper(),
                    "country_code": address_detail.get("country_code", "").upper(),
                }
            )
            collection = (
                await DatabaseConfiguration()
                .state_collection.aggregate([])
                .to_list(None)
            )
            await store_collection_in_cache(collection, collection_name="states")

        if find_state is None:
            if dynamic:
                find_state = {}
            else:
                raise HTTPException(status_code=422, detail="Enter valid State name.")
        if (
            find_city := await DatabaseConfiguration().city_collection.find_one(
                {
                    "name": address_detail.get("city", "").title(),
                    "country_code": address_detail.get("country_code", "").upper(),
                    "state_code": address_detail.get("state_code", "").upper(),
                }
            )
        ) is None:
            if dynamic:
                find_city = {}
            else:
                raise HTTPException(status_code=422, detail="city not found.")
        address = {
            "country": {
                "country_id": ObjectId(find_country.get("_id")) if ObjectId.is_valid(find_country.get("_id")) else
                find_country.get("_id", ""),
                "country_code": address_detail.get("country_code").upper(),
                "country_name": find_country.get("name", ""),
            },
            "state": {
                "state_id":  ObjectId(find_state.get("_id")) if ObjectId.is_valid(find_state.get("_id")) else
                find_state.get("_id", ""),
                "state_code": address_detail.get("state_code", "").upper(),
                "state_name": find_state.get("name", ""),
            },
            "city": {
                "city_id": ObjectId(find_city.get("_id")) if ObjectId.is_valid(find_city.get("_id")) else
                find_city.get("_id", ""),
                "city_name": address_detail.get("city", "").title(),
            },
            "address_line1": address_detail.get("address_line1", ""),
            "address_line2": address_detail.get("address_line2", ""),
            "pincode": address_detail.get("pincode", ""),
        }
        return address

    async def address_insert(
        self,
        _id: str,
        address_detail: dict,
        key_value=None,
        course_name=None,
        dynamic=False,
        college_id=None
    ):
        """
        Get the address_details of student
        """
        if len(address_detail) >= 1:
            address = await self.address_update(address_detail, dynamic=True)
            data = {key_value: {"communication_address": address}}
            if address_detail.get("is_permanent_address_same") is False:
                address2 = await self.address_update(
                    address_detail.get("permanent_address"), dynamic=dynamic
                )
                data = {
                    key_value: {
                        "communication_address": address,
                        "permanent_address": address2,
                    }
                }
            store_data = (
                await DatabaseConfiguration().studentsPrimaryDetails.update_one(
                    {"_id": ObjectId(_id)}, {"$set": data}
                )
            )
            from app.helpers.student_curd.student_configuration import (
                StudentApplicationHelper,
            )

            if store_data:
                await StudentApplicationHelper().update_stage(_id, course_name, 5, college_id=college_id)
                if (
                    existing_student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                        {"_id": ObjectId(_id)}
                    )
                ) is not None:
                    existing_student = StudentCourse().student_primary(existing_student)
                    return existing_student.get("address_details")
        if (
            existing_student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                {"_id": ObjectId(_id)}
            )
        ) is not None:
            existing_student = StudentCourse().student_primary(existing_student)
            return existing_student.get("address_details")
        return False

    async def update_student_data(self, current_user, user: dict, college_id: ObjectId, season: str | None = None,
                                  student_id: str | None = None):
        """
        Update a student data using ID
        """
        if season == "":
            season = None
        if student_id not in ["", None]:
            await utility_obj.is_length_valid(student_id, "Student id")
            admin_user = await UserHelper().is_valid_user(current_user)
            if admin_user.get("role", {}).get("role_name") not in ["college_super_admin", "college_admin",
                                                                   "college_head_counselor", "college_counselor"]:
                raise NotEnoughPermission()
            student = await DatabaseConfiguration(season=season).studentsPrimaryDetails.find_one(
                {"_id": ObjectId(student_id), "college_id": college_id}
            )
        else:
            student = await DatabaseConfiguration(season=season).studentsPrimaryDetails.find_one(
                {"user_name": current_user, "college_id": college_id}
            )
        if student:
            if len(user) >= 1:
                if user.get("email") is not None:
                    user["email"] = str(user.get("email")).lower()
                    if (
                        await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                            {"user_name": user.get("email"), "college_id": college_id}
                        )
                        is not None
                    ):
                        if str(user.get("email")).lower() == student.get("user_name"):
                            pass
                        else:
                            raise CustomError("Email already exists.")
                if user.get("mobile_number") is not None:
                    user["mobile_number"] = str(user.get("mobile_number"))
                    if (
                        await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                            {
                                "basic_details.mobile_number": user.get(
                                    "mobile_number"
                                ),
                                "college_id": college_id,
                            }
                        )
                        is not None
                    ):
                        if user.get("mobile_number") == student.get(
                            "basic_details", {}
                        ).get("mobile_number"):
                            pass
                        else:
                            raise CustomError("Mobile number already exists.")
                old_data = student.get("basic_details", {})
                old_add = student.get("address_details", {}).get(
                    "communication_address"
                )
                if user.get("name", "") != "":
                    user["full_name"] = user.get("name")
                    user = utility_obj.break_name(user)
                    name = [user["first_name"], user["middle_name"], user["last_name"]]
                else:
                    name = [
                        old_data.get("first_name", ""),
                        old_data.get("middle_name", ""),
                        old_data.get("last_name", ""),
                    ]
                old_data.update(
                    {
                        "first_name": name[0],
                        "middle_name": name[1],
                        "last_name": name[2],
                        "email": user.get("email", student.get("user_name")),
                        "mobile_number": user.get(
                            "mobile_number", old_data.get("mobile_number")
                        ),
                        "alternate_number": user.get(
                            "alternate_number", old_data.get("alternate_number", "")
                        ),
                        "gender": user.get(
                            "gender", old_data.get("gender", "")
                        )
                    }
                )
                data = {"basic_details": old_data}
                if user.get("country_code", "") != "":
                    address = await self.address_update(
                        {
                            "country_code": user.get("country_code"),
                            "state_code": user.get("state_code"),
                            "city": user.get("city_name"),
                        }
                    )
                    address.update(
                        {
                            "address_line1": old_add.get("address_line1", ""),
                            "address_line2": old_add.get("address_line2", ""),
                            "pincode": old_add.get("pincode", ""),
                        }
                    )
                    student["address_details"]["communication_address"].update(address)
                    data["address_details"] = student["address_details"]
                data["user_name"] = user.get("email", student.get("user_name"))
                updated_student = (
                    await DatabaseConfiguration().studentsPrimaryDetails.update_one(
                        {"_id": student.get("_id")}, {"$set": data}
                    )
                )
                if updated_student.modified_count == 1:
                    if (
                        updated_student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                            {"_id": student.get("_id"), "college_id": college_id}
                        )
                    ) is not None:
                        return {"message": "Student primary data updated successfully."} if student_id else (
                            StudentCourse().student_update_serialize(updated_student))
            if (
                existing_student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(str(student.get("_id"))), "college_id": college_id}
                )
            ) is not None:
                return {"message": "Student primary data updated successfully."} if student_id else (
                    StudentCourse().student_update_serialize(existing_student))
        raise DataNotFoundError("Student not found.")

    async def delete_student(self, _id: str, college_id):
        """
        Delete a student from the database
        """
        student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"_id": ObjectId(_id), "college_id": college_id}
        )
        if student:
            await DatabaseConfiguration().studentsPrimaryDetails.delete_one(
                {"_id": ObjectId(_id), "college_id": college_id}
            )
            await DatabaseConfiguration().studentSecondaryDetails.delete_one(
                {"student_id": ObjectId(_id)}
            )
            await DatabaseConfiguration().studentApplicationForms.delete_many(
                {"student_id": ObjectId(_id), "college_id": college_id}
            )
            await DatabaseConfiguration().studentTimeline.delete_one(
                {"student_id": ObjectId(_id)}
            )
            await DatabaseConfiguration().queries.delete_many(
                {"student_id": ObjectId(_id)}
            )
            await DatabaseConfiguration().leadsFollowUp.delete_many(
                {"student_id": ObjectId(_id)}
            )
            return True

    def course_helper(self, course) -> dict:
        """
        Get course_details
        """
        return {"specId": course["_id"], "specName": course["name"]}

    async def checking_main_course(self, course, college_id):
        """
        Check whether main_course is present in lst_main or not
        """
        course1 = course.get("course")
        main = course.get("main")
        if (
            find_course := await DatabaseConfiguration().course_collection.find_one(
                {"course_name": course1,
                 "college_id": ObjectId(college_id)
                 }
            )
        ) is None:
            raise HTTPException(status_code=404, detail="course not found.")
        main_course = find_course.get("course_specialization", [])
        if main_course:
            lst_main = [i["spec_name"] for i in main_course]
            if main not in lst_main:
                raise HTTPException(
                    status_code=404,
                    detail="main specialization not found in this course",
                )
        return True

    def create_custom_application_id(self, c_application_id):
        """
        Create custom application id
        """
        if c_application_id is None or c_application_id == "":
            return False, False
        last_value = c_application_id[-4:]
        last_number = str(int(last_value) + 1)
        final = "0" * (4 - len(last_number)) + last_number
        final_id = c_application_id.replace(c_application_id[-4:], final)
        if (
            DatabaseConfigurationSync().studentApplicationForms.find_one(
                {"custom_application_id": final_id}
            )
            is None
        ):
            return (
                True,
                final_id,
            )
        return False, final_id

    async def get_short_form_of_spec_name(self, spec_name: str) -> str:
        """
        Get short form of specialization name based on full form.

        Params:
            spec_name (str): Full form of specialization name.

        Returns:
            shot_spec_name (str): Short form of specialization name.
        """
        shot_spec_name = ""
        if spec_name not in [None, ""]:
            spec = spec_name.replace("of", "")
            spec = spec.replace("and", "")
            spec = spec.replace("&", "")
            spec = spec.replace("CSE-", "")
            shot_spec_name = "".join([i[0].upper() for i in spec.split()])
        return shot_spec_name

    def get_custom_application_id(self, course, course_id, spec_course=None):
        """
        Get custom application_id
        """
        year = str(datetime.today().year)
        course_f = course.replace(".", "")
        if course_f.lower() == "master" or course_f.lower() == "bachelor":
            course_f = course_f[0]
        application_id = f"{settings.university_prefix_name}/{year}/{course_f}/0001"
        if spec_course:
            spec = spec_course.replace("of", "")
            spec = spec.replace("and", "")
            spec = spec.replace("&", "")
            spec = spec.replace("CSE-", "")
            spec = spec.replace("(", "")
            spec = spec.replace(")", "")
            spec_name = "".join([i[0].upper() for i in spec.split()])
            application_id = (
                f"{settings.university_prefix_name}/{year}/{course_f}{spec_name}/0001"
            )
        if (
            DatabaseConfigurationSync().studentApplicationForms.find_one(
                {"custom_application_id": application_id}
            )
            is None
        ):
            return application_id
        all_app_id = (
            DatabaseConfigurationSync()
            .studentApplicationForms.aggregate(
                [{"$match": {
                    "spec_name1": spec_course,
                    "course_id": ObjectId(course_id),
                }},
                    {"$sort": {"enquiry_date": -1}},
                    {"$limit": 1}
                ]
            )
        )
        for item in all_app_id:
            c_application_id = item.get("custom_application_id")
            create_id, final_id = self.create_custom_application_id(c_application_id)
            if create_id:
                return final_id

        date = f"{str(datetime.utcnow().year)}-01-01"  # This code will
        # run when previous
        # custom application id not found.
        start_date, end_date = utility_obj.date_change_format_sync(date, date)
        count_data = (
            DatabaseConfigurationSync().studentApplicationForms.count_documents(
                {
                    "spec_name1": spec_course,
                    "course_id": ObjectId(course_id),
                    "enquiry_date": {"$gte": start_date},
                }
            )
        )
        final = "0" * (4 - len(str(count_data))) + str(count_data + 1)
        final_id = application_id.replace(application_id[-4:], final)
        temp_custom_id = final_id
        for num in range(count_data):
            create_id, final_id = self.create_custom_application_id(final_id)
            if create_id:
                return final_id
        return temp_custom_id

    @background_task_wrapper
    async def run_background_task(
        self,
        _id: str,
        main: str | None,
        course: str,
        is_created_by_publisher: bool,
        college_id: str,
        publisher_id: str,
        is_created_by_user: bool,
        user_details: None | dict,
        state_code: str,
        source_name: str | None,
        round_robin: bool = False,
        application_id: ObjectId | None = None,
            is_signup=False,
            campaign=None,
            medium=None,
        system_preference=None
    ):
        """
        Helper function which add student application data, student timeline
        and allocation counselor info in the background for increase
        performance time of signup API.

        Params:
            - _id (str): An unique identifier of a student.
            - main (None | str): Either None or a string value which
                represents specialization of course.
            - course (str): A string value which represents course
                name.
            - is_created_by_publisher (bool): A boolean value which
                represents signup process perform by publisher or not.
            - college_id (str): An unique identifier of a college.
            - publisher_id (str): A string which represents unique
                identifier of a publisher.
            - is_created_by_user (bool): A boolean value which
                represents signup process is started by admin user or
                not.
            - user_details (None | dict): Either None or a dictionary
                which contains user information.
            - state_code (str): A unique code of a state.
            - source_name (str | None): Either None or a string value
                which represents source name.
            - round_robin (bool): A boolean value which useful for
                perform round_robin method when assign counselor to lead/application.
            - application_id (ObjectId): An unique identifier of an
                application.

        Returns: None
        """
        await self.update_special_course(
            _id=_id,
            main=main,
            course=course,
            is_created_by_publisher=is_created_by_publisher,
            college_id=college_id,
            publisher_id=publisher_id,
            is_created_by_user=is_created_by_user,
            user_details=user_details,
            round_robin=round_robin,
            state_code=state_code,
            source_name=source_name,
            application_id=application_id,
            is_signup=is_signup,
            campaign=campaign,
            medium=medium,
            system_preference=system_preference
        )

    async def update_special_course(
        self,
        _id: str,
        main: str | None = None,
        course: str | None = None,
        secondary=None,
        is_created_by_publisher=False,
        college_id=None,
        publisher_id=None,
        is_created_by_user=False,
        user_details=None,
        round_robin=False,
        state_code=None,
        source_name=None,
        application_id=None,
        student=None,
        is_signup=False,
        campaign=None,
        medium=None,
        system_preference: dict | None = None,
        preference_info: list | None = None
    ):
        """
        Update the details of special courses
        """
        new_app_create = False
        match = {"course_name": course}
        if college_id:
            match.update({"college_id": ObjectId(college_id)})
        if (
            find_course := await DatabaseConfiguration().course_collection.find_one(
               match
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
            all_main = [main, secondary] if not preference_info \
                else preference_info
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
                if i >= 3:
                    continue
                data[spec[i]] = course_spec[i].get("spec_name")
                for j in range(len(course_spec), 3):
                    data[spec[j]] = ""
        current_datetime = datetime.utcnow()
        application_query = {
            "course_id": ObjectId(find_course.get("_id")),
            "student_id": ObjectId(_id),
        }
        if not system_preference or (system_preference and
                                     system_preference.get("preference") is False):
            application_query.update({"spec_name1": main})
        if preference_info:
            data["preference_info"] = preference_info
        if (
            check_application := await DatabaseConfiguration().studentApplicationForms.find_one(
                application_query
            )
        ) is not None:
            data["last_updated_time"] = current_datetime
            if check_application.get("spec_name1", "") != data.get(
                    "spec_name1", ""):
                data["custom_application_id"] = self.get_custom_application_id(
                    course, find_course["_id"], data.get("spec_name1", None)
                )
            await DatabaseConfiguration().studentApplicationForms.update_one(
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
                    "dv_status": "To be verified",
                    "declaration": False,
                    "payment_initiated": False,
                    "payment_info": {"payment_id": "", "status": ""},
                    "enquiry_date": current_datetime,
                    "last_updated_time": current_datetime,
                    "school_name": find_course.get("school_name", ""),
                    "is_created_by_publisher": is_created_by_publisher,
                    "is_created_by_user": is_created_by_user,
                    "custom_application_id": self.get_custom_application_id(
                course=course, course_id=find_course.get("_id"),
                spec_course=data.get("spec_name1"))
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
            student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                {"_id": ObjectId(_id)}
            )
            data["source"] = student.get("source")
            if application_id is not None:
                data["_id"] = ObjectId(application_id)
            if (
                check := await DatabaseConfiguration().studentApplicationForms.insert_one(
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
                "specs": [course_spec[0]] if course_spec is not None else None,
            }
        }
        if (
            course_getting := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                {"_id": ObjectId(_id)}
            )
        ) is None:
            raise HTTPException(
                status_code=404,
                detail="You have not registered with us, please register.",
            )
        data2 = course_getting.get("course_details")
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
        store_data = await DatabaseConfiguration().studentsPrimaryDetails.update_one(
            {"_id": ObjectId(_id)}, {"$set": data1}
        )
        if store_data:
            if round_robin:
                if counselor_allocate:
                    toml_data = utility_obj.read_current_toml_file()
                    if toml_data.get("testing", {}).get("test") is False:
                        try:
                            name = utility_obj.name_can(
                                student.get("basic_details", {})
                            )
                            message = (
                                f"{name} has filled the enquiry form"
                                f" for the programme: {course}"
                                f" - {main} from "
                                f"{source_name} - {medium} - {campaign}"
                            )
                            # TODO: Not able to add student timeline data
                            #  using celery task when environment is
                            #  demo. We'll remove the condition when
                            #  celery work fine.
                            if settings.environment in ["demo"]:
                                StudentActivity().student_timeline(
                                    student_id=_id,
                                    event_status="enquiry",
                                    message=message,
                                    college_id=college_id,
                                )
                            else:
                                StudentActivity().student_timeline.delay(
                                    student_id=_id,
                                    event_status="enquiry",
                                    message=message,
                                    college_id=college_id,
                                )
                        except KombuError as celery_error:
                            logger.error(f"error add_student_timeline {celery_error}")
                        except Exception as error:
                            logger.error(f"error add_student_timeline {error}")
                    current_user = None
                    counselor_id = None
                    if (
                        counselor := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                            {"_id": ObjectId(_id)}
                        )
                    ) is not None:
                        counselor_id = counselor.get("allocate_to_counselor", {}).get(
                            "counselor_id"
                        )
                    if user_details is not None:
                        if (
                            user_details.get("role", {}).get("role_name")
                            == "college_counselor"
                        ):
                            current_user = user_details.get("user_name")
                            counselor_id = user_details.get("_id")
                    await CounselorDashboardHelper().allocate_counselor(
                        application_id=app_id,
                        current_user=current_user,
                        counselor_id=counselor_id,
                        state_code=state_code,
                        source_name=source_name,
                        course=course,
                        specialization=main,
                        student=student,
                    )
                    if new_app_create and not is_signup:
                        basic_details = course_getting.get("basic_details", {})
                        await utility_obj.update_notification_db(
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
                        )
            return True
        return False

    def update_registration_attempts_count(
            self, student_info: dict, extra_info: dict | None = None) -> None:
        """
        Update student registration attempts count.

        Params:
            - student_info (dict): A dictionary which contains student
                information.
            - extra_info (dict | None): Either None or extra
                information which want to update.

        Returns: None
        """
        registration_dates = student_info.get("registration_dates") if student_info.get("registration_dates", []) else []
        registration_attempts = student_info.get("registration_attempts", 0)
        registration_date = datetime.utcnow()
        registration_dates.insert(0, registration_date)
        data = {"registration_attempts": registration_attempts + 1,
                "last_registration_date": registration_date,
                "registration_dates": registration_dates}
        if extra_info:
            data.update({"source": extra_info})
        DatabaseConfigurationSync().studentsPrimaryDetails.update_one(
            {"_id": ObjectId(str(student_info.get("_id")))},
            {"$set": data},
        )

    def utm_source_data(self, social: dict, user_id: str | ObjectId | None = None, email: str | None = None) -> None:
        """
        Helper function which useful for add/update utm source related information in student primary collection.

        Params:
            - social (dict): A dictionary which contains information about source.
                e.g., {"utm_source": "facebook", "utm_campaign": "test", "utm_keyword": "test",
                    "utm_medium": "test", "referal_url": "https://test.com", "utm_enq_date": datetime.datetime.utcnow(),
                    "lead_type": "NA", "publisher_id": "NA",
                    "is_created_by_user": false, "uploaded_by": "NA"}
            - user_id (str | ObjectId | None): Either None or An unique identifier of user.
                e.g., 123456789012345678901234
            - email (str | None): Either None or An email id of a student.
                e.g., test@gmail.com

        Returns: None

        Raises: None
        """
        if email is None:
            if (
                student_info := DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(str(user_id))}
                )) is not None:
                data1 = {"source": {"primary_source": social}}
                DatabaseConfigurationSync().studentsPrimaryDetails.update_one(
                    {"_id": ObjectId(str(user_id))}, {"$set": data1}
                )
                DatabaseConfigurationSync().studentApplicationForms.update_many(
                    {"student_id": ObjectId(str(user_id))}, {"$set": data1},
                )
                self.update_registration_attempts_count(student_info)
        elif user_id is None:
            if (
                student_info := DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                    {"user_name": email}
                )
            ) is not None:
                if (
                        utm := student_info.get("source")
                ) is not None:
                    asyncio.create_task(utility_obj.update_notification_db(
                        event="Duplicate Enquiry Form",
                        student_id=str(student_info.get('_id'))
                    ))
                    if utm.get("secondary_source") is None:
                        utm.update({"secondary_source": social})
                        self.update_registration_attempts_count(
                            student_info, utm)
                    elif utm.get("tertiary_source") is None:
                        utm.update({"tertiary_source": social})
                        self.update_registration_attempts_count(
                            student_info, utm)
                    else:
                        self.update_registration_attempts_count(student_info)
                else:
                    registration_dates = student_info.get(
                        "registration_dates", [])
                    if not registration_dates:
                        registration_dates = []
                    registration_date = datetime.utcnow()
                    registration_dates.insert(0, registration_date)
                    (DatabaseConfigurationSync().studentsPrimaryDetails.
                    update_one(
                        {"_id": ObjectId(str(student_info.get("_id")))},
                        {"$set":
                             {"source": {"primary_source": social,
                                         "registration_attempts": 1,
                                         "last_registration_date":
                                             registration_date,
                                         "registration_dates":
                                             registration_dates}}}))

    async def check_duplicate_key_error_at_the_time_of_student_register(
        self, background_task: bool | None, data: dict
    ) -> None | dict:
        """
        Check duplicate key error at the time of student register
        """
        check = None
        try:
            check = await DatabaseConfiguration().studentsPrimaryDetails.insert_one(
                data
            )

            # For billing Dashboard
            if check and check.inserted_id:
                selected_college_id = MotorBaseSingleton.get_instance().master_data.get("client_id")
                await DatabaseConfiguration().college_collection.update_one(
                    {"_id": ObjectId(selected_college_id)}, {"$inc": {"usages.lead_registered": 1}}
                )

        except DuplicateKeyError as error:
            if background_task:
                pass
            else:
                raise HTTPException(
                    status_code=422,
                    detail=f"Email or mobile number already "
                    f"exists. Error - {error}",
                )
        return check

    async def student_register(
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
        request=None,
        imported_id=None,
        background_tasks: BackgroundTasks = None,
    ):
        """
        Register student
        """
        # extract email from user
        email = user.get("email", "").lower()
        user["email"] = email
        social = {
            "utm_source": (
                user.pop("utm_source", "").lower()
                if user.get("utm_source") is not None
                else user.pop("utm_source")
            ),
            "utm_campaign": user.pop("utm_campaign"),
            "utm_keyword": user.pop("utm_keyword"),
            "utm_medium": user.pop("utm_medium"),
            "referal_url": user.pop("referal_url"),
            "utm_enq_date": datetime.utcnow(),
            "lead_type": lead_type,
            "publisher_id": (
                ObjectId(publisher_id) if publisher_id != "NA" else publisher_id
            ),
            "is_created_by_user": is_created_by_user,
            "is_created_by_publisher": is_created_by_publisher,
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
        if social.get("utm_source") in ["", None]:
            social["utm_source"] = "organic"
        StudentUserCrudHelper().utm_source_data(
            social=social, user_id=None, email=email
        )
        toml_data = utility_obj.read_current_toml_file()
        source_medium_campaign = (f"{social.get('utm_source','organic')}-"
                                  f"{social.get('utm_medium', '')}-{social.get('utm_campaign','')}")
        if email:
            if (
                student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"user_name": email}
                )) is not None:
                if background_task:
                    already_exist = True
                    pass
                else:
                    if toml_data.get("testing", {}).get("test") is False:
                        StudentActivity().student_timeline.delay(
                            student_id=str(student.get("_id")),
                            event_type="Registered Again",
                            event_status="Registered Again",
                            message=f"{utility_obj.name_can(student.get('basic_details'))} tried to enquire again from "
                                    f"{source_medium_campaign}",
                            college_id=str(student.get("college_id")),
                        )
                    raise HTTPException(status_code=422, detail=f"Email already exists.")
        if user.get("mobile_number"):
            if (
                student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"basic_details.mobile_number": str(user.get("mobile_number"))}
                )
            )is not None:
                if background_task:
                    already_exist = True
                    pass
                else:
                    if toml_data.get("testing", {}).get("test") is False:
                        StudentActivity().student_timeline.delay(
                            student_id=str(student.get("_id")),
                            event_type="Registered Again",
                            event_status="Registered Again",
                            message=f"{utility_obj.name_can(student.get('basic_details'))} tried to enquire again from "
                                    f"{source_medium_campaign}",
                            college_id=str(student.get("college_id")),
                        )
                    raise HTTPException(
                        status_code=422, detail=f"Mobile number already exists."
                    )
        if user.get("date_of_birth"):
            date_of_birth = user.get("date_of_birth")
            if date_of_birth not in [None, ""]:
                try:
                    user["date_of_birth_utc"] = await utility_obj.date_change_utc(date_of_birth, date_format="%Y-%m-%d")
                except Exception:
                    if background_task:
                        already_exist = True
                        pass
                    else:
                        raise HTTPException(status_code=422, detail="Not able to convert date_of_birth into utc format.")
        if already_exist:
            return None
        else:
            add = {
                "country_code": user.pop("country_code") if user.get("country_code") else "",
                "state_code": user.pop("state_code") if user.get("state_code") else "",
                "city": user.pop("city") if user.get("city") else "",
                "address_line1": user.pop("address_line1", "") if user.get("address_line1") else "",
                "address_line2": user.pop("address_line2", "") if user.get("address_line2") else "",
                "pincode": user.pop("pincode", "") if user.get("pincode") else "",
            }
            address = await self.address_update(add, dynamic=True)
            if toml_data.get("testing", {}).get("test") is True or settings.environment == "demo":
                # for testing , set hardcoded pwd during registration
                password1 = "getmein"
            else:
                # generate random password
                password1 = utility_obj.random_pass()
            # encrypt hash password
            password2 = Hash().get_password_hash(password1)
            # insert password in user
            college_id = user.pop("college_id")
            if len(college_id) != 24:
                if background_task:
                    pass
                raise HTTPException(
                    status_code=422,
                    detail="college_id must be a 12-byte input"
                    " or a 24-character hex string",
                )
            if (
                college := await DatabaseConfiguration().college_collection.find_one(
                    {"_id": ObjectId(college_id)}
                )
            ) is None:
                if background_task:
                    pass
                raise HTTPException(status_code=404, detail="college not found")
            course = {}
            if user.get("course"):
                if isinstance(user.get("course"), str):
                    course = {
                        "course": user.pop("course"),
                        "main": user.pop("main_specialization")
                    }
                else:
                    course = user.pop("course")
                    course = {
                        "course": course.pop("course_name"),
                        "main": course.pop("specialization")
                    }
            if not background_task and course:
                await StudentUserCrudHelper().checking_main_course(course, college_id)
            user = utility_obj.break_name(user)
            user["mobile_number"] = str(user.get("mobile_number")) if user.get("mobile_number") else None
            is_email_verify = is_mobile_verify = accept_payment = None
            if user.get("is_email_verify") is not None:
                is_email_verify = user.pop("is_email_verify")
            if user.get("is_mobile_verify") is not None:
                is_mobile_verify = user.pop("is_mobile_verify")
            if is_email_verify is False or is_mobile_verify is False:
                raise HTTPException(
                    status_code=401,
                    detail="email or mobile number verification is pending",
                )
            is_verify = True if is_mobile_verify or is_email_verify else False
            if user.get("accept_payment") is True:
                accept_payment = user.pop("accept_payment")
            current_datetime = datetime.now()
            data = {
                "user_name": email,
                "password": password2,
                "college_id": ObjectId(college_id),
                "basic_details": user,
                "address_details": {"communication_address": address},
                "is_verify": is_verify,
                "accept_payment": True if accept_payment is True else False,
                "is_mobile_verify": is_mobile_verify,
                "is_email_verify": is_email_verify,
                "last_accessed": current_datetime,
                "created_at": current_datetime,
                "is_created_by_publisher": is_created_by_publisher,
                "publisher_id": (
                    ObjectId(publisher_id) if publisher_id != "NA" else publisher_id
                ),
                "unsubscribe": {"value": False},
                "is_created_by_user": is_created_by_user,
                "uploaded_by": (
                    {
                        "user_id": user_details.get("_id"),
                        "user_type": user_details.get("role", {}).get("role_name"),
                    }
                    if user_details
                    else "NA"
                ),
                "source": {"primary_source": social},
                "registration_attempts": 0,
                "last_registration_date": current_datetime,
                "registration_dates": [current_datetime],
                "dv_status": "To be verified"
            }
            extra_fields = user.get("extra_fields", {})
            if len(extra_fields) > 0:
                data["extra_fields"] = extra_fields
            if imported_id is not None:
                data["lead_data_id"] = imported_id
            utm_source = social.get("utm_source")
            # insert data in database
            check = (
                await self.check_duplicate_key_error_at_the_time_of_student_register(
                    background_task, data
                )
            )
            if check is not None:
                data_return = {
                    "id": str(check.inserted_id),
                    "password": password1,
                    "user_name": email,
                    "first_name": user.get("first_name"),
                    "mobile_number": user.get("mobile_number"),
                }
                auto_generated_application_id = ObjectId()
                special = True
                if course:
                    if background_tasks is not None:
                        background_tasks.add_task(
                            self.run_background_task,
                            _id=str(check.inserted_id),
                            main=course["main"],
                            course=course["course"],
                            is_created_by_publisher=is_created_by_publisher,
                            college_id=college_id,
                            publisher_id=publisher_id,
                            is_created_by_user=is_created_by_user,
                            user_details=user_details,
                            state_code=address.get("state", {}).get("state_code"),
                            source_name=utm_source,
                            round_robin=True,
                            application_id=auto_generated_application_id,
                            is_signup=True,
                            campaign=social.get("utm_campaign"),
                            medium=social.get("utm_medium"),
                            system_preference=college.get("system_preference")
                        )
                        special = True
                    else:
                        special = await self.update_special_course(
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
                            application_id=auto_generated_application_id,
                            is_signup=True,
                            campaign=social.get("utm_campaign"),
                            medium=social.get("utm_medium"),
                            system_preference=college.get("system_preference")
                        )
                if special:
                    email_preferences = {
                        key: str(val)
                        for key, val in college.get("email_preferences", {}).items()
                    }
                    if toml_data.get("testing", {}).get("test") is False:
                        ip_address = utility_obj.get_ip_address(request)
                        from app.celery_tasks.celery_send_mail import \
                            send_mail_config
                        try:
                            logger.debug(
                                "Sending verification mail" " through celery..."
                            )
                            # TODO: Not able to add student timeline data
                            #  using celery task when environment is
                            #  demo. We'll remove the condition when
                            #  celery work fine.
                            if settings.environment in ["demo"]:
                                send_mail_config().send_mail(
                                    data=data_return,
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
                                )
                            else:
                                send_mail_config().send_mail.delay(
                                    data=data_return,
                                    event_type="email",
                                    event_status="sent",
                                    event_name="Verification",
                                    payload={
                                        "content": "student signup send"
                                                   " token for verification"
                                                   " mail",
                                        "email_list": [user.get("email")],
                                    },
                                    current_user=user.get("email"),
                                    ip_address=ip_address,
                                    email_preferences=email_preferences,
                                    college_id=college_id,
                                )  # Send mail to user only in
                            logger.debug(
                                "Celery function of" " verification mail completed."
                            )
                        except KombuError as celery_error:
                            logger.error(f"error send mail function {celery_error}")
                        except Exception as error:
                            logger.error(f"error send mail function {error}")
                    if accept_payment:
                        from app.dependencies.oauth import AuthenticateUser

                        course_details = (
                            await DatabaseConfiguration().course_collection.find_one(
                                {
                                    "course_name": course.get("course"),
                                    "college_id": ObjectId(college_id),
                                }
                            )
                        )
                        data["_id"] = check.inserted_id
                        refresh_token = (
                            await AuthenticateUser().create_refresh_token_helper(
                                student=data, request=request, college=college
                            )
                        )
                        data_return.update(
                            {
                                "application_id": str(auto_generated_application_id),
                                "course_name": course.get("course"),
                                "specialization_name": course.get("main"),
                                "course_fee": course_details.get("fees"),
                                "access_token": refresh_token,
                            }
                        )
                    data_return.pop("password")
                    return {
                        "data": data_return,
                        "message": "Account Created Successfully.",
                        "code": 200,
                    }
                raise HTTPException(status_code=422, detail="course not inserted")
            return False

    async def add_student_data_into_database(
        self, csv_data, college_id, user_details, request
    ):
        """
        Insert student data into database if it doesn't exist
        """
        payload = json.loads(csv_data.to_json(orient="records"))
        data_list, email_list = [], []
        for i in payload:
            student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                {"user_name": i.get("email")}
            )
            if not student:
                if not i.get("first_name"):
                    raise HTTPException(
                        status_code=400, detail="First name should be exist in csv."
                    )
                if not i.get("last_name"):
                    raise HTTPException(
                        status_code=400, detail="Last name should be exist in csv."
                    )

                if 20 < len(i.get("first_name").strip()) > 2:
                    raise HTTPException(
                        status_code=400,
                        detail="First name should be minimum 2 "
                        "and maximum 20 characters.",
                    )
                if 20 < len(i.get("last_name").strip()) > 2:
                    raise HTTPException(
                        status_code=400,
                        detail="Last name should be minimum 2"
                        " and maximum 20 characters.",
                    )

                if str(i.get("mobile_number")).strip():
                    if len(str(i.get("mobile_number"))) == 10:
                        try:
                            mobile_number = int(i.get("mobile_number"))
                        except Exception as ex:
                            raise HTTPException(
                                status_code=400,
                                detail="Student mobile number must be integer.",
                            )
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="Student mobile must be 10 digit in csv.",
                        )

                if str(i.get("father_mobile_number")).strip():
                    if len(str(i.get("father_mobile_number"))) == 10:
                        try:
                            father_mobile_number = int(i.get("father_mobile_number"))
                        except Exception as ex:
                            raise HTTPException(
                                status_code=400,
                                detail="Father mobile number must be integer.",
                            )
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="Father mobile number must" " be 10 digit in csv.",
                        )

                if str(i.get("mother_mobile_number")).strip():
                    if len(str(i.get("mother_mobile_number"))) == 10:
                        try:
                            mother_mobile_number = int(i.get("mother_mobile_number"))
                        except Exception as ex:
                            # logger.error ("The user mobile number
                            # is not 10 digit")
                            raise HTTPException(
                                status_code=400,
                                detail="Mother mobile number must be integer.",
                            )
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="Mother mobile number must" " be 10 digit in csv.",
                        )

                if str(i.get("guardian_mobile_number")).strip():
                    if len(str(i.get("guardian_mobile_number"))) == 10:
                        try:
                            guardian_mobile_number = int(
                                i.get("guardian_mobile_number")
                            )
                        except Exception as ex:
                            raise HTTPException(
                                status_code=400,
                                detail="Guardian mobile number" " must be integer.",
                            )
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="Guardian mobile number" " must be 10 digit in csv.",
                        )

                try:
                    if i.get("email"):
                        validate_email(i.get("email"))
                    else:
                        raise HTTPException(
                            status_code=400, detail="Email must be in csv."
                        )
                    if i.get("father_email"):
                        validate_email(i.get("father_email"))
                    if i.get("mother_email"):
                        validate_email(i.get("mother_email"))
                    if i.get("guardian_email"):
                        validate_email(i.get("mother_email"))
                except EmailNotValidError as e:
                    raise HTTPException(status_code=400, detail=str(e))

                country_name = i.get("country_name")
                if country_name:
                    from app.dependencies.oauth import (
                        get_collection_from_cache,
                        store_collection_in_cache,
                    )

                    countries = await get_collection_from_cache(collection_name="countries")
                    if countries:
                        country = utility_obj.search_for_document(
                            countries,
                            field="name",
                            search_name=country_name.strip().title(),
                        )
                    else:
                        country = (
                            await DatabaseConfiguration().country_collection.find_one(
                                {"name": country_name.strip().title()}
                            )
                        )
                        countries = (
                            await DatabaseConfiguration()
                            .country_collection.aggregate([])
                            .to_list(None)
                        )
                        await store_collection_in_cache(
                            collection=countries, collection_name="countries"
                        )

                    if country:
                        country_code = country.get("iso2")
                    else:
                        raise HTTPException(
                            status_code=400, detail="Enter valid country name"
                        )
                state_name = i.get("state_name")
                if state_name:
                    state = await DatabaseConfiguration().state_collection.find_one(
                        {
                            "name": state_name.strip().title(),
                            "country_code": country_code,
                        }
                    )
                    if state:
                        state_code = state.get("state_code")
                    else:
                        raise HTTPException(
                            status_code=400, detail="Enter valid state name"
                        )
                city = i.get("city")
                if city:
                    found_city = await DatabaseConfiguration().city_collection.find_one(
                        {
                            "name": city.title().strip(),
                            "country_code": country_code,
                            "state_code": state_code,
                        }
                    )
                    if found_city:
                        city = found_city.get("name")
                    else:
                        raise HTTPException(
                            status_code=400, detail="Enter valid city name"
                        )

                # generate random password
                password1 = utility_obj.random_pass()
                # encrypt hash password
                password2 = Hash().get_password_hash(password1)

                add = {
                    "country_code": country_code if country_name else None,
                    "state_code": state_code if state_name else None,
                    "city": city,
                    "address_line1": i.get("address_line1"),
                    "address_line2": i.get("address_line2"),
                    "pincode": i.get("pincode"),
                }
                address = await self.address_update(add)
                user = {
                    "first_name": i.get("first_name"),
                    "middle_name": i.get("middle_name"),
                    "last_name": i.get("last_name"),
                    "email": i.get("email"),
                    "mobile_number": mobile_number if i.get("mobile_number") else None,
                }
                if len(college_id) != 24:
                    raise HTTPException(
                        status_code=403,
                        detail="college_id must be a 12-byte input "
                        "or a 24-character hex string",
                    )
                if (
                    college := await DatabaseConfiguration().college_collection.find_one(
                        {"_id": ObjectId(college_id)}
                    )
                ) is None:
                    raise HTTPException(status_code=404, detail="college not found")
                course = {
                    "course": i.get("course"),
                    "main": i.get("main_specialization"),
                }
                await self.checking_main_course(course, college_id)
                data = {
                    "user_name": i.get("email"),
                    "password": password2,
                    "college_id": ObjectId(college_id),
                    "basic_details": user,
                    "address_details": address,
                    "is_verify": False,
                    "last_accessed": datetime.utcnow(),
                    "created_at": datetime.utcnow(),
                    "dv_status": "To be verified"
                }

                # insert data in database
                if (
                    check := await DatabaseConfiguration().studentsPrimaryDetails.insert_one(
                        data
                    )
                ) is not None:
                    await DatabaseConfiguration().college_collection.update_one(
                        {"_id": ObjectId(college_id)}, {"$inc": {"usages.lead_registered": 1}}
                    )

                    social = {
                        "utm_source": "Organic",
                        "utm_campaign": "test",
                        "utm_keyword": "",
                        "utm_medium": "csv file",
                        "referal_url": "",
                        "utm_enq_date": datetime.utcnow(),
                    }
                    self.utm_source_data(social, str(check.inserted_id), None)
                    parent_details = {
                        "father_details": {
                            "salutation": i.get("father_salutation"),
                            "name": i.get("father_name"),
                            "email": i.get("father_email"),
                            "mobile_number": i.get("father_mobile_number"),
                        },
                        "mother_details": {
                            "salutation": i.get("mother_salutation"),
                            "name": i.get("mother_name"),
                            "email": i.get("mother_email"),
                            "mobile_number": i.get("mother_mobile_number"),
                        },
                        "guardian_details": {
                            "salutation": i.get("guardian_salutation"),
                            "name": i.get("guardian_name"),
                            "email": i.get("guardian_email"),
                            "mobile_number": i.get("guardian_mobile_number"),
                            "occupation": i.get("guardian_occupation"),
                            "designation": i.get("guardian_designation"),
                            "relationship_with_student": i.get(
                                "relationship_with_student"
                            ),
                        },
                        "family_annual_income": i.get("family_annual_income"),
                    }
                    education_details = {
                        "tenth_school_details": {
                            "school_name": i.get("10th_school_name"),
                            "board": i.get("10th_board"),
                            "year_of_passing": i.get("10th_year_of_passing"),
                            "marking_scheme": str(i.get("10th_marking_scheme")).title(),
                            "obtained_cgpa": (
                                float(i.get("10th_obtained_cgpa", 0))
                                if i.get("10th_marking_scheme").lower()
                                in ["cgpa", "percentage"]
                                else i.get("10th_obtained_cgpa", 0)
                            ),
                            "school_code": i.get("10th_school_code"),
                            "tenth_subject_wise_details": {
                                "english": i.get("english"),
                                "maths": i.get("maths"),
                                "science": i.get("science"),
                                "social_science": i.get("social_science"),
                                "language": i.get("language"),
                                "other_subject": i.get("other_subject"),
                            },
                        },
                        "inter_school_details": {
                            "school_name": i.get("12th_obtained_marks"),
                            "board": i.get("12th_board"),
                            "year_of_passing": i.get("12th_year_of_passing"),
                            "marking_scheme": str(i.get("12th_marking_scheme")).title(),
                            "obtained_cgpa": (
                                float(i.get("12th_obtained_cgpa", 0))
                                if i.get("12th_marking_scheme").lower()
                                in ["cgpa", "percentage"]
                                else i.get("12th_obtained_cgpa", 0)
                            ),
                            "stream": i.get("stream"),
                            "appeared_for_jee": i.get("appeared_for_jee"),
                        },
                    }
                    await DatabaseConfiguration().studentSecondaryDetails.insert_one(
                        {
                            "student_id": ObjectId(check.inserted_id),
                            "parent_details": parent_details,
                            "education_details": education_details,
                        }
                    )

                    data = {
                        "id": str(check.inserted_id),
                        "user_name": i.get("email"),
                        "password": password1,
                        "first_name": user["first_name"],
                        "mobile_number": user["mobile_number"],
                    }
                    email_list.append(i.get("email"))
                    special = await self.update_special_course(
                        str(check.inserted_id),
                        course["main"],
                        course["course"],
                        secondary=i.get("secondary_specialization"),
                        college_id=college_id
                    )
                    if special:
                        email_preferences = {
                            key: str(val)
                            for key, val in college.get("email_preferences", {}).items()
                        }
                        ip_address = utility_obj.get_ip_address(request)
                        toml_data = utility_obj.read_current_toml_file()
                        if toml_data.get("testing", {}).get("test") is False:
                            # Don't move below import statement in the top, otherwise it will
                            # give ImportError due to circular import
                            from app.celery_tasks.celery_send_mail import (
                                send_mail_config,
                            )

                            send_mail_config().send_mail.delay(
                                data,
                                event_type="email",
                                event_status="sent",
                                event_name="Verification",
                                payload={
                                    "content": "student signup send token for"
                                    " verification mail",
                                    "email_list": [user.get("email")],
                                },
                                current_user=user_details.get("email"),
                                ip_address=ip_address,
                                email_preferences=email_preferences,
                                college_id=college_id,
                            )  # send mail to user
                            # TODO: Not able to add student timeline data
                            #  using celery task when environment is
                            #  demo. We'll remove the condition when
                            #  celery work fine.
                            if settings.environment in ["demo"]:
                                StudentActivity().add_student_timeline(
                                    student_id=str(check.inserted_id),
                                    event_status="Started",
                                    message="has filled the enquiry form for the programme:",
                                    college_id=college_id,
                                )
                            else:
                                StudentActivity().add_student_timeline.delay(
                                    student_id=str(check.inserted_id),
                                    event_status="Started",
                                    message="has filled the enquiry form for the programme:",
                                    college_id=college_id,
                                )
                        data_list.append(data)

        if data_list:
            return data_list, email_list
        raise HTTPException(
            status_code=422, detail="Student data already exist in a database."
        )

    async def update_verification_status(self, student):
        """
        Update verification status of lead in DB.

        Params:
            student (dict): A dictionary containing student info.
        """
        update_status, today = {}, datetime.utcnow()
        for name in ["verify", "email_verify"]:
            if student.get(f"is_{name}") in [None, False]:
                update_status.update({f"is_{name}": True, f"{name}_at": today})
        if update_status:
            await DatabaseConfiguration().studentsPrimaryDetails.update_one(
                {"_id": student.get("_id")}, {"$set": update_status}
            )
