"""
This file contain class and functions related to course
"""
import json

from bson import ObjectId
from fastapi.exceptions import HTTPException
from app.core.custom_error import CustomError, DataNotFoundError
from app.core.utils import utility_obj
from app.database.aggregation.course import Course
from app.database.configuration import DatabaseConfiguration


class CourseHelper:
    """
    Contain functions related to course
    """

    def course_helper(self, course) -> dict:
        """
        Get course details
        """
        course_spec = course.get("course_specialization", [])
        return {
            "id": str(course.get("_id")),
            "college_id": str(course.get("college_id")),
            "course_name": course.get("course_name"),
            "course_description": course.get("course_description"),
            "duration": course.get("duration"),
            "fees": course.get("fees"),
            "is_activated": course.get("is_activated"),
            "is_pg": course.get("is_pg"),
            "banner_image_url": course.get("banner_image_url"),
            "course_specialization":
                [{"index": _id, "spec_name": spec.get("spec_name"),
                  "is_activated": spec.get("is_activated")}
                 for _id, spec in enumerate(course_spec)] if course_spec
                else None
        }

    async def course_specialization_helper(
            self, course_information: dict, student_id: str | None) -> dict:
        """
        Course specialization details.

        Params:
            - course_information (dict): A dictionary which
                contains course information.
            - student_id (str | None): Either None or student unique
                identifier which useful for get information about
                student enroll for particular course specialization or not.

        Returns:
            - dict: A dictionary which contains course and course
                specialization (s) information.
        """
        course_spec = course_information.get("course_specialization", [])
        course_id = course_information.get("_id")
        if student_id:
            student_id = ObjectId(student_id)
        if course_spec:
            course_spec = [
                {"index": _id, "spec_name": spec.get("spec_name"),
                 "is_activated": spec.get("is_activated"),
                 "lateral_entry": spec.get("lateral_entry", False),
                 "available_for_user": False}
                if student_id and (
                            await DatabaseConfiguration().studentApplicationForms.find_one(
                                {
                                    "course_id": course_id,
                                    "student_id": student_id,
                                    "spec_name1": spec.get("spec_name")
                                }
                            ) is not None) else {"index": _id,
                                                 "spec_name": spec.get(
                                                     "spec_name"),
                                                 "is_activated": spec.get(
                                                     "is_activated"),
                                                 "lateral_entry": spec.get(
                                                     "lateral_entry",
                                                     False)}
                for _id, spec in
                enumerate(course_spec) if spec.get("is_activated")]
        return {
            "college_id": str(course_information.get("college_id")),
            "course_id": str(course_id),
            "course_description": course_information.get("course_description"),
            "course_specialization": course_spec,
            "fees": course_information.get("fees"),
            "is_activated": course_information.get("is_activated"),
            "banner_image_url": course_information.get("banner_image_url"),
        }

    async def retrieve_courses(self, college_id, page_num=None, page_size=None,
                               route_name=None, course_names=None,
                               category=None, show_disable_courses=None,
                               academic_category=None):
        """
        Retrieve list of course
        """
        courses = await Course().college_courses(
            college_id, course_names, category, show_disable_courses, academic_category)
        if courses:
            courses = json.loads(json.dumps(courses, default=str))
            if page_num and page_size:
                courses_length = len(courses)
                response = await utility_obj.pagination_in_api(
                    page_num, page_size, courses, courses_length, route_name
                )
                return {
                    "data": response["data"],
                    "total": response["total"],
                    "count": page_size,
                    "pagination": response["pagination"],
                    "message": "Courses data fetched successfully.",
                }
            return utility_obj.response_model(
                courses, "Courses data fetched successfully.")
        return [[]]

    async def update_course_status(self, data: dict, college_id,
                                   course_id: str):
        """
        Update course status
        """
        course = await DatabaseConfiguration().course_collection.find_one(
            {"_id": ObjectId(course_id), "college_id": ObjectId(college_id)}
        )
        if not course:
            raise HTTPException(status_code=404, detail="course not found.")
        if course.get("is_activated") == data.get("is_activated"):
            raise HTTPException(
                status_code=422,
                detail="Unable to update, no changes have been made."
            )
        updated_course = await DatabaseConfiguration().course_collection.update_one(
            {"_id": ObjectId(course_id)}, {"$set": data}
        )
        if updated_course:
            return True, course

    async def retrieve_specialization_list(
            self, college_id: str, course_id: str | None = None,
            course_name: str | None = None, student_id: str | None = None) \
            -> list:
        """
        Retrieve list of specialization.

        Params:\n
        - college_id: Required field. Useful for get particular college
            course specialization (s) information.
            e.g., 624e8d6a92cc415f1f578a24\n
        - course_id: Optional field. Useful for get college course
            specialization (s) information by course_id.
            e.g. 62551f6d7a3f3d06d4196b7f\n
        - course_name: Optional field. Useful for get college course
            specialization (s) information by course_id.
            e.g., b.tech\n
        - student_id: Optional field. Useful when want to show course
            specialization (s) list based on student.
            e.g. 62551f6d7a3f3d06d4196b72\n

        Returns:\n
            - list: List of course specializations.
        """
        if course_id:
            await utility_obj.is_length_valid(course_id, "Course id")
            course_information = await (
                DatabaseConfiguration().course_collection
                .find_one({"_id": ObjectId(course_id),
                           "college_id": ObjectId(college_id)}))
        elif course_name:
            course_information = await (DatabaseConfiguration()
            .course_collection.find_one({
                "course_name": course_name,
                "college_id": ObjectId(college_id)}))
        else:
            raise CustomError("Course id or name must be required to get "
                              "course specialization (s) information.")
        if not course_information:
            raise DataNotFoundError(message="Course")
        return [await self.course_specialization_helper(course_information,
                                                        student_id)]

    async def create_new_course(self, course_data: dict, college_id: str):
        """
        Create new course
        """
        college_id = ObjectId(college_id)
        course_name = course_data.get("course_name")
        course = await DatabaseConfiguration().course_collection.find_one(
            {"college_id": college_id, "course_name": course_name}
        )
        if not course:
            course_specs = course_data.get("course_specialization", [])
            temp_spec = {
                "spec_name": None,
                "is_activated": False if isinstance(course_specs, list) and
                                         len(course_specs) > 1 else True
            }
            if course_specs:
                course_specs.insert(0, temp_spec)
                course_data["course_specialization"] = course_specs
            else:
                course_data["course_specialization"] = [
                    temp_spec
                ]
            course_duration = course_data.get("duration")
            course_fees = course_data.get("fees")
            if course_duration:
                course_duration = f"{course_duration} Years"
            if course_fees:
                course_fees = f"Rs.{course_data.get('fees')}/-"
            course_data.update({"college_id": college_id,
                                "course_name": course_name,
                                "duration": course_duration,
                                "fees": course_fees})
            course = await DatabaseConfiguration().course_collection. \
                insert_one(course_data)
            new_course = await DatabaseConfiguration().course_collection. \
                find_one({"_id": course.inserted_id})
            return self.course_helper(new_course)

    async def add_course_data_into_database(self, csv_data, college_id):
        """
        Add course data into database
        """
        payload = json.loads(csv_data.to_json(orient="records"))
        data_list = []
        for i in payload:
            if not i.get("course_name"):
                raise HTTPException(
                    status_code=400,
                    detail="Course name should be exist in csv."
                )

            course_specialization = []
            if (
                    i.get("course_specialization") is not None
                    and i.get("course_specialization") != ""
            ):
                if i.get("course_specialization").find(","):
                    for item in i.get("course_specialization").split(","):
                        course_specialization.append(
                            {"spec_name": item.strip(), "is_activated": True}
                        )

            data = {
                "college_id": ObjectId(college_id),
                "course_name": i.get("course_name"),
                "course_description": i.get("course_description"),
                "duration": f"{i.get('duration')} Years",
                "fees": f"Rs.{i.get('Application_fees')}.0/-",
                "is_activated": i.get("is_activated"),
                "banner_image_url": i.get("banner_image_url"),
                "course_specialization": course_specialization
                if course_specialization
                else None,
            }
            course = await DatabaseConfiguration().course_collection.find_one(
                {"college_id": ObjectId(college_id),
                 "course_name": i["course_name"]}
            )
            if not course:
                checked = await DatabaseConfiguration().course_collection.insert_one(
                    data)
                course_data = await DatabaseConfiguration().course_collection.find_one(
                    {"_id": checked.inserted_id})
                data_list.append(self.course_helper(course_data))
            else:
                for item in course_specialization:
                    if item not in course.get("course_specialization"):
                        if course.get("course_specialization") is None:
                            await DatabaseConfiguration().course_collection.update_one(
                                {"_id": ObjectId(course.get("_id"))},
                                {"$set": {
                                    "course_specialization": course_specialization}},
                            )
                        else:
                            try:
                                await DatabaseConfiguration().course_collection.update_one(
                                    {"_id": ObjectId(course.get("_id"))},
                                    {
                                        "$set": {
                                            "course_specialization": course.get(
                                                "course_specialization"
                                            )
                                                                     + course_specialization
                                        }
                                    },
                                )
                            except:
                                continue
                    continue
        if data_list:
            return data_list
        raise HTTPException(
            status_code=422, detail="Courses data already exist in a database."
        )

    async def update_course(self, course_data, college_id, course_id):
        """
        Update course data
        """
        find_course = await DatabaseConfiguration().course_collection.find_one(
            {"_id": ObjectId(course_id), "college_id": ObjectId(college_id)}
        )
        if not find_course:
            raise HTTPException(404, detail="Course not exist.")
        if course_data.get("duration"):
            course_data.update(
                {"duration": f"{course_data.get('duration')} Years"})
        if course_data.get("fees"):
            course_data.update({"fees": f"Rs.{course_data.get('fees')}/-"})
        if course_data.get("course_specialization"):
            if find_course.get("course_specialization") is None:
                course_data.update(
                    {"course_specialization": course_data.get(
                        "course_specialization")}
                )
            else:
                for item in course_data.get("course_specialization"):
                    if item not in find_course.get("course_specialization"):
                        find_course.update(
                            {
                                "course_specialization": find_course.get(
                                    "course_specialization"
                                )
                                                         + item
                            }
                        )
        updated_course = await DatabaseConfiguration().course_collection.update_one(
            {"_id": ObjectId(course_id)}, {"$set": course_data}
        )
        if updated_course:
            return course_data

    async def get_course_info(self, course_name: str | None,
                              course_id: str | None,
                              college_id: ObjectId) -> dict | bool:
        """
        Get the course data based on id or name and college id.

        Params:
            course_name (str): Name of a course. e.g., B.Tech.
            course_id (str): A unique id of a course. e.g.,
                123456789012345678901234
            college_id (ObjectId): A unique id of a college.
                e.g., 123456789012345678901211

        Returns:
            dict: A dictionary which contains course info when provide correct
            input values.

        Raises:
            ObjectIdInValid: An exception which occur when course id will
                be wrong.
        """
        if course_id:
            await utility_obj.is_length_valid(_id=course_id,
                                              name="Course id")
            course = await DatabaseConfiguration().course_collection.find_one(
                {"_id": ObjectId(course_id),
                 "college_id": college_id})
        elif course_name:
            course = await DatabaseConfiguration().course_collection.find_one(
                {"course_name": course_name,
                 "college_id": college_id})
        else:
            return False
        return course

    async def add_course_specs(
            self, course_id: str, course_name: str,
            new_course_specs: list[dict], college_id: ObjectId) -> dict:
        """
        Add course specializations.

        Params:
            course_id (str): A unique id of a course. e.g.,
                123456789012345678901234
            course_name (str): Name of a course. e.g., B.Tech.
            new_course_specs (list[dict]): A list which contains
                specializations in a dictionary format.
                e.g., [{"spec_name": "test", "is_activated": False}]
            college_id (ObjectId): A unique id of a college.
                e.g., 123456789012345678901211

        Raises:
            ObjectIdInValid: An exception which occur when course id will
                be wrong.
            CustomError: An exception which occur when certain condition fails.
        """
        course = await self.get_course_info(course_name, course_id, college_id)
        if course:
            if new_course_specs:
                pre_course_specs = course.get("course_specialization", [])
                if not pre_course_specs:
                    pre_course_specs = []
                course_specs = [spec_info.get("spec_name")
                                for spec_info in pre_course_specs]
                temp_specs = []
                for new_spec in new_course_specs:
                    new_spec_name = new_spec.get("spec_name")
                    if new_spec.get("is_activated") is None:
                        new_spec["is_activated"] = True
                    if not new_spec_name:
                        raise CustomError(
                            message="Specialization name not provided in "
                                    "correct way.")
                    if new_spec_name in course_specs:
                        raise CustomError(message="Specialization name "
                                                  "already exists.")
                    if new_spec in temp_specs:
                        continue
                    temp_specs.append(new_spec)
                course_spec = pre_course_specs + temp_specs
                await DatabaseConfiguration().course_collection.update_one(
                    {"_id": course.get("_id")},
                    {'$set': {"course_specialization": course_spec}})
                return {"message": "Course specializations added."}
            return {
                "detail": "Course specializations data not provided."}
        return {"detail": "Course not found. Make sure course id"
                          " or name is correct."}

    async def update_course_specs(
            self, course_id: str, course_name: str,
            update_course_specs: list[dict], college_id: ObjectId) -> dict:
        """
        Update course specializations.

        Params:
            course_id (str): A unique id of a course. e.g.,
                123456789012345678901234
            course_name (str): Name of a course. e.g., B.Tech.
            new_course_specs (list[dict]): A list which contains
                specializations in a dictionary format.
                e.g., [{"current_spec_name": "spec_name": "test", "is_activated": False}]
            college_id (ObjectId): A unique id of a college.
                e.g., 123456789012345678901211

        Raises:
            ObjectIdInValid: An exception which occur when course id will
                be wrong.
            CustomError: An exception which occur when certain condition fails.
        """
        course = await self.get_course_info(course_name, course_id, college_id)
        if course:
            pre_course_specs = course.get("course_specialization", [])
            if not pre_course_specs:
                pre_course_specs = []
            temp_specs, is_spec_updated = [], False
            activated_specialization = [
                {"spec_name": course_spec.get("spec_name")} for course_spec in
                pre_course_specs
                if course_spec.get("is_activated")]
            for new_spec in update_course_specs:
                index_number = new_spec.get("spec_index")
                if len(pre_course_specs) <= index_number:
                    raise CustomError(
                        message="Specialization index not found. "
                                "Make sure provided specialization index is "
                                "correct.")
                copy_dict = new_spec.copy()
                copy_dict.pop("spec_index")
                copy_dict = {key: value for key, value in
                             copy_dict.items() if value is not None}
                if pre_course_specs[index_number]["spec_name"] is None:
                    if copy_dict.get("spec_name"):
                        copy_dict.pop("spec_name")
                if len(copy_dict) >= 1:
                    pre_course_specs[index_number].update(copy_dict)
                    if len(activated_specialization) == 1 and \
                            copy_dict.get("is_activated") == False and \
                            pre_course_specs[index_number]["spec_name"] == \
                            activated_specialization[0]["spec_name"]:
                        raise CustomError(
                            message="Can not change activation status of "
                                    f"specialization `{pre_course_specs[index_number]['spec_name']}` because "
                                    f"atleast one specialization should be "
                                    f"active. You can disable course if want "
                                    f"to disable all specializations.")
                    is_spec_updated = True
            if is_spec_updated:
                await DatabaseConfiguration().course_collection.update_one(
                    {"_id": course.get("_id")},
                    {'$set': {"course_specialization": pre_course_specs}})
                return {"message": "Course specializations updated."}
            return {"message": "Course specializations not updated."}
        return {'detail': 'Course not found. Make sure course id or name is'
                          ' correct.'}
