"""
This file contain courses related class and functions
"""
from bson import ObjectId

from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.database.no_auth_connection_db import NoAuthDatabaseConfiguration


class Course:
    """
    Contain functions related to course activities
    """

    def myfunc(self, course):
        """
        Sort the course based on course names
        """
        course_name = course.get("course_name").replace(".", "").lower()
        if course_name in ["btech", "mtech"]:
            return 0
        elif course_name == "master" or course_name == "bachelor":
            return 5
        elif course_name == "mba" or course_name == "bba":
            return 2
        elif course_name == "msc":
            return 3
        elif course_name == "bpharma":
            return 1
        else:
            return 4

    async def college_courses(self, college_id, course_names, category,
                              show_disable_courses=None, academic_category=None):
        """
        Get list of college courses by id
        """
        base_match = {"college_id": ObjectId(college_id)}
        if academic_category:
            base_match.update({f"is_{academic_category.lower()}": True})
        if category:
            courses = (
                NoAuthDatabaseConfiguration(college_id).
                health_science_courses_collection
                .aggregate([{"$match": base_match}]))

            data = [{
                "_id": str(course.get("_id")),
                "client_id": str(course.get("client_id")),
                "college_id": str(course.get("college_id")),
                "course_name": course.get("course_name"),
                "course_description": course.get("course_description"),
                "duration": course.get("duration"),
                "fees": course.get("fees"),
                "is_activated": course.get("is_activated"),
                "is_pg": course.get("is_pg"),
                "banner_image_url": course.get("banner_image_url"),
                "course_specialization": ([
                                              {"index": _id,
                                               "spec_name": spec.get(
                                                   "spec_name"),
                                               "is_activated": spec.get(
                                                   "is_activated"),
                                               "lateral_entry": spec.get(
                                                   "lateral_entry", False)}
                                              for _id, spec in enumerate(
                        course.get("course_specialization",
                                   [])) if (spec.get("spec_name") is None and
                                            spec.get("is_activated"))
                                           or (spec.get(
                        "spec_name") is not None)] if course.get(
                    "course_specialization",
                    [])
                                          else None) if show_disable_courses
                else [{"index": _id, "spec_name": spec.get("spec_name"),
                       "is_activated": spec.get("is_activated"),
                       "lateral_entry": spec.get("lateral_entry", False)}
                      for _id, spec in
                      enumerate(course.get("course_specialization", []))
                      if spec.get("is_activated")] if course.get(
                    "course_specialization", []) else None,
            } async for course in courses]

        else:
            if not show_disable_courses:
                base_match.update({'is_activated': True})
            if course_names:
                course_names = course_names.split(',')
                base_match.update({'course_name': {"$in": course_names}})
            pipeline = [
                {"$match": base_match},
                {"$sort": {"course_name": 1}}
            ]
            toml_data = utility_obj.read_current_toml_file()
            if toml_data.get('testing', {}).get('test') is False:
                result = (
                    NoAuthDatabaseConfiguration(college_id).course_collection
                    .aggregate(pipeline))
            else:
                result = DatabaseConfiguration().course_collection.aggregate(
                    pipeline)
            data = []
            async for course in result:
                course_specialization = course.get("course_specialization", [])
                if not course_specialization:
                    course_specialization = []
                course.update({"_id": str(course.get("_id")),
                               "college_id": str(course.get("college_id")),
                               "client_id": str(course.get("client_id")),
                               "course_specialization": [
                                   {"index": _id,
                                    "spec_name": spec.get("spec_name"),
                                    "is_activated": spec.get("is_activated"),
                                    "lateral_entry": spec.get("lateral_entry",
                                                              False)}
                                   for _id, spec in
                                   enumerate(
                                       course_specialization) if
                                   (spec.get("spec_name") is None and
                                    spec.get("is_activated") is True)
                                   or (spec.get(
                                       "spec_name") is not None)] if show_disable_courses
                               else [{"index": _id,
                                      "spec_name": spec.get("spec_name"),
                                      "is_activated": spec.get("is_activated"),
                                      "lateral_entry": spec.get(
                                          "lateral_entry", False)}
                                     for _id, spec in
                                     enumerate(course_specialization)
                                     if spec.get("is_activated")]})
                if course.get("course_counselor") is not None:
                    course.pop("course_counselor")
                data.append(course)
            data.sort(key=self.myfunc)
        return data

    async def get_courses_data_by_school_names(self) -> dict:
        """
        Get courses data by school names.

        Returns:
              dict: A dictionary which contains courses data by school names.
        """
        pipeline = [
            {
                '$group': {
                    '_id': '$school_name',
                    'courses': {
                        '$push': {
                            'course_name': '$course_name',
                            'course_specialization': '$course_specialization'
                        }
                    }
                }
            }, {
                '$project': {
                    'courses': {
                        '$map': {
                            'input': '$courses',
                            'as': 'course',
                            'in': {
                                'course_name': '$$course.course_name',
                                'course_specialization': {
                                    '$filter': {
                                        'input': '$$course.course_specialization',
                                        'cond': {
                                            '$eq': [
                                                '$$this.is_activated', True
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ]

        return {document.get("_id"): document.get("courses") async
                for document in
                DatabaseConfiguration().course_collection.aggregate(
                    pipeline)}
