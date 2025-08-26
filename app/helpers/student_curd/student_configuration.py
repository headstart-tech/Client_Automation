"""
This file contain class and functions related to student
"""

import csv

import xlrd
from bson.objectid import ObjectId
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError

from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.database.configuration import DatabaseConfiguration
from app.helpers.student_curd.student_application_configuration import (
    StudentApplicationHelper,
)
from app.helpers.student_curd.student_user_crud_configuration import (
    StudentUserCrudHelper,
)
from app.models.serialize import StudentCourse
from app.models.student_serialize import BoardHelper

logger = get_logger(__name__)


class StudentHelper:
    """
    Contain functions related to student configuration
    """

    async def retrieve_students(self, current_user):
        """
        Retrieve all student data from the database
        """
        if (
            user_dct := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                {"user_name": current_user}
            )
        ) is None:
            raise HTTPException(status_code=404, detail="user not found")
        data = StudentCourse().student_primary(user_dct)
        if (
            user_detail := await DatabaseConfiguration().studentSecondaryDetails.find_one(
                {"student_id": ObjectId(user_dct.get("_id"))}
            )
        ) is None:
            user_detail = {}
        data1 = StudentCourse().student_seconadry(user_detail)
        data["secondary_details"] = data1
        return data

    async def get_applied_course(self, current_user):
        """
        Get applied course
        """
        if (
            user := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                {"user_name": current_user}
            )
        ) is None:
            raise HTTPException(status_code=404, detail="user not found")
        lst, lst2 = [], []
        if (
            courses_submitted := DatabaseConfiguration().studentApplicationForms.find(
                {"student_id": ObjectId(user["_id"]), "declaration": True}
            )
        ) is not None:
            total_courses = (
                await DatabaseConfiguration().course_collection.count_documents({})
            )
            course_submit = [
                StudentApplicationHelper().student_application_helper(i)
                for i in await courses_submitted.to_list(length=total_courses)
            ]
            for i in range(len(course_submit)):
                course = DatabaseConfiguration().course_collection.find_one(
                    {"_id": ObjectId(course_submit[i]["course_id"])}
                )
                dct = {
                    "application_form": course["course_name"],
                    "course_id": course_submit[i]["id"],
                    "application_submitted": course_submit["last_updated_time"],
                    "fees": course["fees"],
                }
                lst.append(dct)
        if (
            courses_pending := await DatabaseConfiguration().studentApplicationForms.aggregate(
                [{"$match": {"student_id": ObjectId(user["_id"]), "declaration": False}}]
            ).to_list(length=None)
        ) is not None:
            total_courses = (
                await DatabaseConfiguration().course_collection.count_documents({})
            )
            course_pending = [
                StudentApplicationHelper().student_application_helper(i)
                for i in await courses_pending.to_list(length=total_courses)
            ]
            for i in range(len(course_pending)):
                course = await DatabaseConfiguration().course_collection.find_one(
                    {"_id": ObjectId(course_pending[i]["course_id"])}
                )
                dct = {
                    "application_form": course["course_name"],
                    "course_id": course_pending[i]["id"],
                    "application_submitted": "-",
                    "fees": course["fees"],
                }
                lst2.append(dct)
        course = {"course_submitted": lst, "course_pending": lst2}
        return course

    async def update_add_student(self, current_user: str, data: dict):
        """
        Update a student data using ID
        Return false if an empty request body is sent.
        """
        if len(data) < 1:
            return False

        student = DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"user_name": current_user}
        )
        if (
            DatabaseConfiguration().studentSecondaryDetails.find_one(
                {"student_id": ObjectId(student.get("_id"))}
            )
            is not None
        ):
            updated_student = (
                await DatabaseConfiguration().studentSecondaryDetails.update_one(
                    {"student_id": ObjectId(student.get("_id"))}, {"$set": data}
                )
            )
            if updated_student:
                return True
        data["student_id"] = ObjectId(student.get("_id"))
        updated_student = (
            await DatabaseConfiguration().studentSecondaryDetails.insert_one(data)
        )
        if updated_student:
            return True
        return False

    async def update_basic_details(
        self,
        _id: str,
        basic_detail: dict,
        course_name: str,
        college_id=None,
        student=None,
        system_preference: dict | None = None
    ):
        """asynchronous function for update student basic details"""
        if len(basic_detail) >= 1:
            try:
                # TODO: Not able to add student timeline data
                #  using celery task when environment is
                #  demo. We'll remove the condition when
                #  celery work fine.
                if settings.environment in ["demo"]:
                    StudentActivity().add_student_timeline(
                        student_id=_id,
                        event_status="started",
                        message="has started filling the Application Form for",
                        college_id=college_id,
                    )
                else:
                    StudentActivity().add_student_timeline.delay(
                        student_id=_id,
                        event_status="started",
                        message="has started filling the Application Form for",
                        college_id=college_id,
                    )
            except KombuError as celery_error:
                logger.error(f"error add_student_timeline {celery_error}")
            except Exception as error:
                logger.error(f"error add_student_timeline {error}")
            basic_detail = dict(basic_detail)
            main = basic_detail.pop("main_specialization", None)
            secondary = basic_detail.pop("secondary_specialization", "")
            student_data = (
                await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(_id)}
                )
            )
            source = None
            if (
                source_details := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(_id)}
                )
            ) is not None:
                source = (
                    source_details.get("source", {})
                    .get("primary_source", {})
                    .get("utm_source")
                )
            if secondary != "":
                await StudentUserCrudHelper().update_special_course(
                    _id=_id,
                    main=main,
                    course=course_name,
                    secondary=secondary,
                    college_id=college_id,
                    round_robin=True,
                    state_code=student_data.get("address_details", {})
                    .get("communication_address", {})
                    .get("state", {})
                    .get("state_code", None),
                    source_name=source,
                    student=student,
                    system_preference=system_preference,
                    preference_info=basic_detail.pop("preference_info", None)
                )
            else:
                await StudentUserCrudHelper().update_special_course(
                    _id=_id,
                    main=main,
                    course=course_name,
                    college_id=college_id,
                    round_robin=True,
                    state_code=student_data.get("address_details", {})
                    .get("communication_address", {})
                    .get("state", {})
                    .get("state_code", None),
                    source_name=source,
                    student=student,
                    system_preference=system_preference,
                    preference_info=basic_detail.pop("preference_info", None)
                )
            date_of_birth = basic_detail.get("date_of_birth")
            if date_of_birth not in [None, ""]:
                basic_detail["date_of_birth_utc"] = await utility_obj.date_change_utc(date_of_birth, date_format="%Y-%m-%d")
            if basic_detail.get("email", None) is not None:
                basic_detail["email"] = str(basic_detail.get("email"))
                if (
                    await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                        {"user_name": basic_detail.get("email")}
                    )
                    is not None
                ):
                    current_user = (
                        await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                            {"_id": ObjectId(_id)}
                        )
                    )
                    if basic_detail.get("email") == current_user["user_name"]:
                        pass
                    else:
                        raise HTTPException(
                            status_code=422, detail="username already exists"
                        )
            if basic_detail.get("mobile_number", None) is not None:
                basic_detail["mobile_number"] = str(basic_detail.get("mobile_number"))
                if (
                    await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                        {
                            "basic_details.mobile_number": basic_detail.get(
                                "mobile_number"
                            )
                        }
                    )
                    is not None
                ):
                    current_user = (
                        await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                            {"_id": ObjectId(_id)}
                        )
                    )
                    if basic_detail["mobile_number"] == current_user.get(
                        "basic_details", {}
                    ).get("mobile_number"):
                        pass
                    else:
                        raise HTTPException(
                            status_code=422, detail="Mobile number already exist."
                        )
            if (
                data1 := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(_id)}
                )
            ) is not None:
                data1.get("course_details", {}).get(course_name, {}).get(
                    "specs", [{}])[0].update({"spec_name": main})
                data1["basic_details"].update(basic_detail)
                data1["user_name"] = basic_detail.get("email", data1.get("user_name"))
                updated_student = (
                    await DatabaseConfiguration().studentsPrimaryDetails.update_one(
                        {"_id": ObjectId(_id)}, {"$set": data1}
                    )
                )
                if updated_student:
                    await StudentApplicationHelper().update_stage(
                        _id, course_name, 2.50, main, college_id=college_id
                    )
                    data = (
                        await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                            {"_id": ObjectId(_id)}
                        )
                    )
                    return StudentCourse().student_primary(
                        data, system_preference=system_preference)
        if (
            data := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                {"_id": ObjectId(_id)}
            )
        ) is not None:
            return StudentCourse().student_primary(
                data, system_preference=system_preference)
        raise HTTPException(status_code=404, detail="user_name not found.")

    async def insert_some(
        self,
        _id: str,
        basic_detail: dict,
        key_value: str,
        course_name: str,
        dynamic=False,
        college_id=None
    ):
        """
        Add student patents/guardian/address/education details
        """
        if len(basic_detail) >= 1:
            basic_detail = dict(basic_detail)
            data = {key_value: basic_detail}
            if key_value == "parents_details":
                gurd = basic_detail.pop("guardian_details", "")
                income = basic_detail.pop("family_annual_income", "")
                if dynamic and basic_detail.get("mother_details", {}).get(
                    "family_annual_income"
                ):
                    data["family_annual_income"] = basic_detail.get(
                        "mother_details", {}
                    ).get("family_annual_income", "")
                else:
                    data["family_annual_income"] = income
                data["guardian_details"] = gurd
            minimum = 6.25
            if key_value == "parents_details":
                minimum = 3.75
            if key_value == "education_details":
                for name in [
                    "tenth_school_details",
                    "inter_school_details",
                    "diploma_academic_details",
                    "graduation_details",
                ]:
                    score = basic_detail.get(f"{name}", {}).get("obtained_cgpa")
                    if score not in ["", None]:
                        basic_detail[name]["normalize_score"] = (
                            utility_obj.normalize_score(
                                basic_detail[name]["marking_scheme"], score
                            )
                        )
                entrance_exam_details = basic_detail.get("entrance_exam_details")
                if entrance_exam_details and isinstance(entrance_exam_details, dict):
                    entrance_exam_info = entrance_exam_details.get("inputFields", [])
                    if isinstance(entrance_exam_info, list):
                        data["total_entrance_exam"] = len(entrance_exam_info)
                    else:
                        data["total_entrance_exam"] = 0
            if (
                await DatabaseConfiguration().studentSecondaryDetails.find_one(
                    {"student_id": ObjectId(_id)}
                )
                is not None
            ):
                updated_student = (
                    await DatabaseConfiguration().studentSecondaryDetails.update_one(
                        {"student_id": ObjectId(_id)}, {"$set": data}
                    )
                )
                if updated_student:
                    await StudentApplicationHelper().update_stage(
                        _id, course_name, minimum, college_id=college_id
                    )
                    if (
                        data := await DatabaseConfiguration().studentSecondaryDetails.find_one(
                            {"student_id": ObjectId(_id)}
                        )
                    ) is not None:
                        return StudentCourse().student_seconadry(data)
            else:
                data["student_id"] = ObjectId(_id)
                updated_student = (
                    await DatabaseConfiguration().studentSecondaryDetails.insert_one(
                        data
                    )
                )
                if updated_student:
                    await StudentApplicationHelper().update_stage(
                        _id, course_name, minimum, college_id=college_id
                    )
                    if (
                        data := await DatabaseConfiguration().studentSecondaryDetails.find_one(
                            {"student_id": ObjectId(_id)}
                        )
                    ) is not None:
                        return StudentCourse().student_seconadry(data)
        if (
            data := await DatabaseConfiguration().studentSecondaryDetails.find_one(
                {"student_id": ObjectId(_id)}
            )
        ) is not None:
            return StudentCourse().student_seconadry(data)
        return False

    async def check_payment(self, application_id: str):
        """
        Check payment
        """
        if (
            application := await DatabaseConfiguration().studentApplicationForms.find_one(
                {"_id": ObjectId(application_id)}
            )
        ) is not None:
            if (
                    course := await DatabaseConfiguration().course_collection.find_one(
                        {"_id": application.get("course_id")}
                    )
            ) is None:
                raise HTTPException(status_code=404, detail="course not found.")
            if application.get("payment_info").get("status") == "captured":
                return True, course.get("course_name")
            else:
                return False, course.get("course_name")
        raise HTTPException(status_code=404, detail="Application not found")

    async def upload_data_in_db(self, file, background_tasks, college):
        """
        Upload student all data in db
        """
        filename = file.filename
        file_copy = await utility_obj.temporary_path(file)
        if filename.endswith(".csv"):
            with open(file_copy.name, mode="r") as infile:
                reader = csv.reader(infile)
                data = [rows for rows in reader]
                colm = data[0]
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            wb = xlrd.open_workbook(file_copy.name)
            sheet = wb.sheet_by_index(0)
            sheet.cell_value(0, 0)
            trows = sheet.nrows
            data = [sheet.row_values(i) for i in range(trows)]
            colm = data[0]
        else:
            raise HTTPException(
                status_code=422, detail="Allow only csv and excel file."
            )

        for i in range(1, len(data)):
            (
                student_p,
                annual,
                spec,
                guardian,
                father,
                mother,
                tenth_school,
                tenth_mark,
                inter_col,
            ) = ({}, {}, {}, {}, {}, {}, {}, {}, {})
            for j in range(len(data[i])):
                if j <= 16:
                    student_p[colm[j]] = data[i][j]
                elif j <= 17:
                    student_p[colm[j]] = data[i][j]
                    spec[colm[j]] = data[i][j]
                elif j <= 18:
                    spec[colm[j]] = data[i][j]
                elif 19 < j <= 24:
                    tenth_school[colm[j]] = data[i][j]
                elif 25 < j <= 31:
                    tenth_mark[colm[j]] = data[i][j]
                elif 32 < j <= 39:
                    inter_col[colm[j]] = data[i][j]
                elif 40 < j <= 44:
                    father[colm[j]] = data[i][j]
                elif 45 < j <= 49:
                    mother[colm[j]] = data[i][j]
                elif 50 < j <= 57:
                    guardian[colm[j]] = data[i][j]
                elif j == 58:
                    annual[colm[j]] = data[i][j]
            para = {
                "is_disable": student_p.pop("is_disable"),
                "name_of_disability": student_p.pop("name_of_disability"),
            }
            student_p["para_ability"] = para
            student = await StudentUserCrudHelper().student_register(
                student_p, background_tasks=background_tasks
            )
            if student:
                await StudentUserCrudHelper().update_special_course(
                    student["id"],
                    spec["main_specialization"],
                    student_p["course"],
                    spec["secondary_specialization"],
                    college_id=college.get("id")
                )
                tenth_school["tenth_subject_wise_details"] = tenth_mark
                edu = {
                    "tenth_school_details": tenth_school,
                    "inter_school_details": inter_col,
                }
                parent = {"father_details": father, "mother_details": mother}
                final = {
                    "student_id": ObjectId(student["id"]),
                    "education_details": edu,
                    "parents_details": parent,
                    "guardian_details": guardian,
                    "family_annual_income": annual["family_annual_income"],
                }
                if (
                    await DatabaseConfiguration().studentSecondaryDetails.find_one(
                        {"student_id": ObjectId(student["id"])}
                    )
                    is not None
                ):
                    raise HTTPException(status_code=422, detail="student already exist")
                data = await DatabaseConfiguration().studentSecondaryDetails.insert_one(
                    final
                )
        if data:
            return True
        return False

    async def tenth_inter_board_name(
        self, page_num=None, page_size=None, route_name=None
    ):
        """
        Get board details
        """
        total_boards = await DatabaseConfiguration().boardDetails.count_documents({})
        board_name = [
            BoardHelper().board_serialize(i)
            for i in await DatabaseConfiguration()
            .boardDetails.aggregate([])
            .to_list(length=total_boards)
        ]
        if len(board_name) < 1:
            raise HTTPException(status_code=404, detail="Board not found.")
        if page_num and page_size:
            board_length = len(board_name)
            response = await utility_obj.pagination_in_api(
                page_num, page_size, board_name, board_length, route_name
            )
        if board_name:
            if page_num and page_size:
                return {
                    "data": response["data"],
                    "total": response["total"],
                    "count": page_size,
                    "pagination": response["pagination"],
                    "message": "data fetch successfully",
                }
            return board_name

    async def format_education_details(self, education_details):
        if education_details is None:
            education_details = {}
        for key_name in ["tenth_school_details", "inter_school_details",
                         "diploma_academic_details", "graduation_details"]:
            if (
                education_details.get(key_name, {}).get("obtained_cgpa")
                not in [None, ""]
            ):
                education_details[key_name]["obtained_cgpa"] = (
                    float(education_details.get(key_name, {}).get(
                        "obtained_cgpa"))
                    if str(education_details.get(key_name, {}).get(
                        "marking_scheme")).lower() in ["cgpa", "percentage"]
                    else education_details.get(key_name, {}).get(
                        "obtained_cgpa"))
        return education_details
