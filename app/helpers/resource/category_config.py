"""
This file contain class and functions related to key category
"""
import datetime
from bson.objectid import ObjectId
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.core.custom_error import CustomError
from app.dependencies.oauth import cache_invalidation


class KeyCategory:
    """
    Contain functions related to key category
    """

    async def get_question_helper(self, document):
        """
        Helper function for get question details.
        """
        program_list = document.get("program_list", [])
        if program_list:
            program_list = [{"course_name": program.get("course_name"),
                             "course_specialization":
                                 program.get("course_specialization")}
                            for program in program_list]
        last_modified_timeline = document.get("last_modified_timeline")[0]
        return {
            "_id": str(document.get("_id")),
            "question": document.get("question"),
            "answer": document.get("answer"),
            "tags": document.get("tags"),
            "created_by": document.get("created_by"),
            "created_by_id": str(document.get("created_by_id")),
            "created_at": utility_obj.get_local_time(
                document.get("created_at")),
            "last_updated_on": utility_obj.get_local_time(
                last_modified_timeline.get("last_modified_at")),
            "last_updated_by": last_modified_timeline.get("user_name"),
            "last_updated_by_id": str(last_modified_timeline.get("user_id")),
            "school_name": document.get("school_name"),
            "program_list": program_list,
            "is_visible_to_student": document.get("is_visible_to_student",
                                                  False)
        }

    async def create_key_category(self, college: dict, category_info: dict,
                                  user: dict,
                                  index_number: int | None) -> dict:
        """
        Create key category.

        Params:
            - college (dict): A dictionary which contains college information.
            - category_info (dict): A dictionary which contains category info.
                e.g., {"category_name": "test"}
            - user (dict): A dictionary which contains user information.
            - index_number (int | None): Required in case of update key category name.
                A unique index of key category. e.g., 0


        Returns:
            A dictionary which contains information about create key category.
        """
        exist_key_categories = college.get("key_categories", [])
        category_name = category_info.get("category_name", "")
        if exist_key_categories is None:
            exist_key_categories = []
        created_at = datetime.datetime.utcnow()
        user_name = utility_obj.name_can(user)
        user_id = ObjectId(user.get("_id"))
        last_modified_timeline = [
            {
                "last_modified_at": created_at,
                "user_id": user_id,
                "user_name": user_name
            }
        ]
        key_categories = [category_info.get("category_name", "").lower()
                          for category_info in exist_key_categories]
        if index_number is not None:
            if index_number >= len(exist_key_categories):
                raise CustomError("Please provide a valid index number.")
            if (category_name.lower() in key_categories and
                    index_number != key_categories.index(
                        category_name.lower())):
                return {"detail": f"Key category `{category_name}` already "
                                  f"exist."}
            exist_key_categories[index_number]. \
                get('last_modified_timeline', []).insert(
                0, last_modified_timeline[0])
            exist_key_categories[index_number].update(
                {
                    "last_modified_timeline":
                        exist_key_categories[index_number].get(
                            'last_modified_timeline', []),
                    "category_name": category_name,
                }
            )
            await DatabaseConfiguration().college_collection.update_one(
                {"_id": ObjectId(college.get("id"))}, {
                    "$set": {"key_categories": exist_key_categories}})
            await cache_invalidation(api_updated="updated_college", user_id=college.get("id"))
            return {"message": "Key category name successfully updated."}
        else:
            if category_name.lower() in key_categories:
                return {"detail": f"Key category `{category_name}` already "
                                  f"exist."}
            exist_key_categories.insert(
                0, {"category_name": category_name,
                    "created_by": user_name,
                    "created_by_id": user_id,
                    "created_at": created_at,
                    "last_modified_timeline": last_modified_timeline
                    })
            await DatabaseConfiguration().college_collection.update_one(
                {"_id": ObjectId(college.get("id"))}, {
                    "$set": {"key_categories": exist_key_categories}})
            await cache_invalidation(api_updated="updated_college", user_id=college.get("id"))
            return {"message": "Key category successfully created."}

    async def create_or_update_a_question(
            self, question_info: dict, user: dict,
            question_id: str | None) -> dict:
        """
        Create or update a question.

        Params:
            - question_info (dict): A dictionary which can contains question
                info.
                e.g., {"question": "Eligibility criteria of course B.Sc.?",
                "answer": Candidate must completed 10th.",
                "tags": ["Eligibility", "Course"]}
            - user (dict): A dictionary which contains user information.
            - question_id (str | None): Required in case of update
                question info. A unique id/identifier of a question.
                e.g., 123456789012345678901241


        Returns:
            A dictionary which contains information about create or update
                a question.
        """
        created_at = datetime.datetime.utcnow()
        user_name = utility_obj.name_can(user)
        user_id = ObjectId(user.get("_id"))
        last_modified_timeline = [
            {
                "last_modified_at": created_at,
                "user_id": user_id,
                "user_name": user_name,
            }
        ]
        program_list = question_info.get("program_list")
        if program_list:
            temp_program_list = []
            for program in program_list:
                course_name = program.get("course_name")
                temp_dict = {"course_name": course_name,
                 "course_specialization": program.get("course_specialization")}
                if (
                        course := await DatabaseConfiguration().
                                course_collection.find_one(
                            {"course_name": course_name})) is not None:
                    temp_dict.update({"course_id": course.get("_id")})
                temp_program_list.append(temp_dict)
            question_info["program_list"] = temp_program_list
        if question_id not in ["", None]:
            await utility_obj.is_length_valid(question_id, name="Question id")
            if (question := await DatabaseConfiguration().questions.find_one(
                    {"_id": ObjectId(question_id)})) is None:
                raise CustomError(f"Question not found by id: {question_id}")
            question_info = {key: value for key, value in question_info.items()
                             if value is not None}
            if len(question_info) >= 1:
                exist_last_modified_timeline = \
                    question.get("last_modified_timeline")
                exist_last_modified_timeline.insert(0,
                                                    last_modified_timeline[0])
                question_info.update({"last_modified_timeline":
                                          exist_last_modified_timeline})
                await DatabaseConfiguration().questions.update_one(
                    {'_id': ObjectId(question_id)}, {"$set": question_info})
                return {"message": "Question information updated "
                                   "successfully."}
            return {"message": "There is nothing to update."}
        else:
            question_info.update(
                {
                    "created_by": user_name,
                    "created_by_id": user_id,
                    "created_at": created_at,
                    "last_modified_timeline": last_modified_timeline
                })
            await DatabaseConfiguration().questions.insert_one(question_info)
            return {"message": "Question created successfully."}

    async def delete_questions(self, questions_ids: list[str]) -> dict:
        """
        Delete questions based on ids.

        Params:
            - questions_ids (list[str]): A list which contains questions unique
                ids/identifiers.

        Returns:
            dict : A dictionary which contains information about delete
                questions.
        """
        questions_ids = [ObjectId(question_id) for question_id in questions_ids
                         if await utility_obj.is_length_valid(
                question_id, "Question id") and await DatabaseConfiguration().
            questions.find_one({"_id": ObjectId(question_id)}) is not None]
        if questions_ids:
            await DatabaseConfiguration().questions.delete_many(
                {"_id": {"$in": questions_ids}})
            return {"message": "Questions deleted successfully."}
        return {"detail": "Make sure provided questions ids are correct."}

    async def delete_key_category(
            self, index_number: int, college: dict) -> dict:
        """
        Delete a key category by index number.

        Params:
            - index_number (int): A unique index number of key
                category. e.g., 0
            - college (dict): A dictionary which contains college information.

        Returns:
            dict : A dictionary which contains information about delete key
                category.
        """
        exist_key_categories = college.get("key_categories", [])
        if not exist_key_categories:
            exist_key_categories = []
        if index_number >= len(exist_key_categories):
            raise CustomError("Please provide a valid index number.")
        category_name = exist_key_categories[index_number].get(
            "category_name")
        exist_key_categories.pop(index_number)
        await DatabaseConfiguration().college_collection.update_one(
            {"_id": ObjectId(college.get("id"))}, {
                "$set": {"key_categories": exist_key_categories}})
        await cache_invalidation(api_updated="updated_college", user_id=college.get("id"))
        await DatabaseConfiguration().questions. \
            update_many({"tags": {"$in": [category_name]}},
                        {"$pull": {'tags': category_name}})
        return {"message": "Key category deleted successfully."}
