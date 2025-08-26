"""
This file contain helper functions related to student and course
"""
from app.core.utils import utility_obj
from app.helpers.college_configuration import CollegeHelper
from app.database.database_sync import DatabaseConfigurationSync


class StudentCourse:
    """
    Contain functions related to student and course
    """

    #  ---------------------------- student primary details schema to serialize schema -------------#

    def basic_detail(self, item, college_id: str | None = None):
        """
        Get basic details of student
        """
        if college_id:
            item["current_season"] = CollegeHelper().get_current_season_year(
                college_id)
        return {
            **item
        }

    def country_detail(self, item):
        """
        Get country details
        """
        return {
            "country_id": str(item.get("country_id")),
            "country_code": item.get("country_code"),
        }

    def state_detail(self, item):
        """
        Get state details
        """
        return {"state_id": str(item.get("state_id")),
                "state_code": item.get("state_code")}

    def city_detail(self, item):
        """
        Get city details
        """
        return {"city_id": str(item.get("city_id")),
                "city_name": item.get("city_name")}

    def address_rander(self, item):
        """
        Get address details
        """
        return {
            "country_code": self.country_detail(item.get("country", {})),
            "state_code": self.state_detail(item.get("state", {})),
            "city": self.city_detail(item.get("city", {})),
            "address_line1": item.get("address_line1", ""),
            "address_line2": item.get("address_line2", ""),
            "pincode": item.get("pincode", ""),
        }

    def address_detail(self, item):
        """
        Get address details of student
        """
        if item.get("permanent_address") is None:
            return {
                "communication_address": self.address_rander(
                    item.get("communication_address", {})
                ),
            }
        else:
            return {
                "communication_address": self.address_rander(
                    item.get("communication_address", {})
                ),
                "permanent_address": self.address_rander(
                    item.get("permanent_address", {})),
            }

    def courses(self, item, system_preference: dict | None = None,
                preference_info: dict | None = None) -> dict:
        """
        Get course details
        """
        specializations = item.get("specs")
        course_name = item.get("course_name")
        if (system_preference and isinstance(system_preference, dict) and
                system_preference.get("preference")):
            specializations = preference_info.get(course_name)
        return {
            "course_id": str(item.get("course_id")),
            "course_name": course_name,
            "application_id": str(item.get("application_id")),
            "status": item.get("status"),
            "specs": specializations,
        }

    def course_detail(self, item, system_preference: dict | None = None,
                      preference_info: dict | None = None):
        """
        Get course details
        """
        return {k: self.courses(v, system_preference, preference_info)
                for k, v in item.items()}

    def student_primary(
            self, item: dict, college_id: str | None = None,
            system_preference: dict | None = None) -> dict:
        """
        Primary details of Student
        """
        return {
            "id": str(item["_id"]),
            "user_name": item.get("user_name"),
            "basic_details": self.basic_detail(item.get("basic_details", {}),
                                               college_id),
            "address_details": self.address_detail(
                item.get("address_details", {})),
            "course_details": self.course_detail(
                item.get("course_details", {}),
                system_preference=system_preference,
                preference_info=item.get("preference_info", {}))
            if item.get("course_details") is not None
            else item.get("course_details"),
            "is_verify": item.get("is_verify"),
            "last_accessed": item["last_accessed"].strftime(
                "%d-%m-%Y %H:%M:%S") if item.get("last_accessed") else None,
            "created_at": item["created_at"].strftime(
                "%d-%m-%Y %H:%M:%S") if item.get("created_at") else None,
            "is_created_by_publisher": item.get("is_created_by_publisher"),
            "lead_offline_id": str(item.get("lead_data_id")) if item.get(
                "lead_data_id") is not None else ""
        }

    #   ------------------------end of student primary schema -------------------------------------#

    # ---------------------- student secondary schema  -----------------------#

    def tenth_detail(self, item):
        """
        Get 10th class details
        """
        return {
            "school_name": item["school_name"],
            "board": item["board"],
            "year_of_passing": item["year_of_passing"],
            "marking_scheme": item["marking_scheme"],
            "obtained_cgpa": item["obtained_cgpa"],
            "school_code": item["school_code"],
            "tenth_subject_wise": item["tenth_subject_wise"],
        }

    def inter_detail(self, item):
        """
        Get 12th class details
        """
        return {
            "school_name": item["school_name"],
            "board": item["board"],
            "year_of_passing": item["year_of_passing"],
            "marking_scheme": item["marking_scheme"],
            "obtained_cgpa": item["obtained_cgpa"],
            "stream": item["stream"],
            "appeared_for_jee": item["appeared_for_jee"],
        }

    def education_detail(self, item):
        """
        Get education details
        """
        return {
            "tenth_school_details": self.tenth_detail(
                item["tenth_school_details"]),
            "inter_school_details": self.inter_detail(
                item["inter_school_details"]),
        }

    def student_seconadry(self, item):
        """
        Get student secondary details
        """
        data = {}
        if item.get("_id"):
            data.update({"id": str(item.get('_id'))})
            item.pop("_id")
        if item.get("student_id"):
            data.update({"student_id": str(item.get('student_id'))})
            item.pop("student_id")
        if item.get("attachments"):
            # Do not move below import statement in the top otherwise we will
            # get circular import issue
            from app.helpers.student_curd.student_application_configuration import \
                StudentApplicationHelper
            data["attachments"] = StudentApplicationHelper().file_helper(
                item, data.get("student_id"))["attachments"]
            item.pop("attachments")
        data.update({k: v for k, v in item.items()})
        return {
            **data
        }

    # ------------------- course schema serialize    ---------------------#

    def course_serialize(self, item):
        return {
            "id": str(item["_id"]),
            "course_name": item.get("course_name"),
            "course_description": item.get("course_description"),
            "duration": item.get("duration"),
            "fees": item.get("fees"),
            "is_activated": item.get("is_activated"),
            "banner_image_url": item.get("banner_image_url"),
            "course_specialization": item.get("course_specialization"),
            "college_id": str(item.get("college_id")),
        }

    # ---------------------------update student serialize ---------------------------------#

    def mob_can(self, item):
        """
        Get mobile number
        """
        return item.get("mobile_number")

    def alter_can(self, item):
        """
        Get alternate number
        """
        return item.get("alternate_number")

    def country_can(self, item):
        """
        Get country code
        """
        return "".join(
            {val for key, val in item.get("country", {}).items() if
             key == "country_code"}
        )

    def state_can(self, item):
        """
        Get state code
        """
        return "".join({val for key, val in item.get("state", {}).items() if
                        key == "state_code"})

    def city_can(self, item):
        """
        Get city name
        """
        return "".join({val for key, val in item.get("city", {}).items() if
                        key == "city_name"})

    def student_update_serialize(self, item):
        """
        Get student basic details
        """
        return {
            "name": utility_obj.name_can(item.get("basic_details", {})),
            "email": item.get("user_name"),
            "phone_number": self.mob_can(item.get("basic_details")),
            "alternative_number": self.alter_can(item.get("basic_details")),
            "country_code": self.country_can(
                item.get("address_details", {}).get("communication_address",
                                                    {})
            ),
            "state_code": self.state_can(
                item.get("address_details", {}).get("communication_address",
                                                    {})
            ),
            "city_name": self.city_can(
                item.get("address_details", {}).get("communication_address",
                                                    {})),
        }

    def lead_source_serialize(self, item):
        """
        Get Source details of student
        """
        return {
            "id": str(item.get("_id")),
            "student_id": str(item.get("student_id")),
            "primary_source": item.get("primary_source"),
            "secondary_source": item.get("secondary_source"),
            "tertiary_source": item.get("tertiary_source"),
        }
