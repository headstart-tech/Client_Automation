"""
This file contain class and functions related to board details
"""


class BoardHelper:
    """
    Contain functions related to board details
    """

    def board_serialize(self, item):
        """
        Get the board details
        """
        return {
            "id": str(item.get("_id")),
            "tenth_board_name": item.get("tenth_board_name"),
            "inter_board_name": item.get("inter_board_name"),
        }

    def index_extract(self, item):
        """
        Get index
        """
        return {"index": int(item.get("index")), "id": str(item.get("_id"))}


def course_serialize(item):
    """course serialization"""
    return {
        "course_id": str(item.get("course_id")),
        "course_name": item.get("course_name"),
        "application_id": str(item.get("application_id")),
        "status": item.get("status"),
        "specs": item.get("specs"),
    }


def counselor_serialize(item):
    """counselor serialization"""
    return {
        "counselor_id": str(item.get("counselor_id")),
        "counselor_name": item.get("counselor_name"),
        "last_update": item.get("last_update")
    }


class address_serializer:
    """address serialize"""

    def __init__(self):
        """initialize the address serializer"""
        pass

    def country_serialize(self, item):
        """country serialize"""
        return {
            "country_id": str(item.get("country_id")),
            "country_code": item.get("country_code")
        }

    def state_serialize(self, item):
        """state serialize"""
        return {
            "state_id": str(item.get("state_id")),
            "state_code": item.get("state_code")
        }

    def city_serialize(self, item):
        """city serialize"""
        return {
            "city_id": str(item.get("city_id")),
            "city_name": item.get("city_name")
        }

    def deep_address(self, item):
        """get country , state and city serialize"""
        return {
            "country": self.country_serialize(item.get("country", {})),
            "state": self.state_serialize(item.get("state", {})),
            "city": self.city_serialize(item.get("city", {})),
            "address_line1": item.get("address_line1"),
            "address_line2": item.get("address_line2"),
            "pincode": item.get("pincode")
        }

    def communication_address(self, item):
        """communication address serialization"""
        return {
            "communication_address": self.deep_address(item.get("communication_address", {}))
        }


class student_helper:
    """serialize the student information as json"""

    @staticmethod
    async def student_serialization(item):
        """serialize the student information"""
        return {
            "_id": str(item.get("_id")),
            "user_name": item.get("user_name"),
            "basic_details": item.get("basic_details"),
            "course_details": course_serialize(item.get("course_details", {})),
            "allocation_to_counselor": counselor_serialize(item.get("allocation_to_counselor", {})),
            "address_details": address_serializer().communication_address(item.get("address_details", {})),
            "is_verify": item.get("is_verify"),
            "last_accessed": item.get("last_accessed"),
            "is_created_by_user": item.get("is_created_by_user"),
            "uploaded_by": str(item.get("uploaded_by")) if item.get("uploaded_by") != "NA" else item.get("uploaded_by"),
            "publisher_id": str(item.get("publisher_id")) if item.get("publisher_id") != "NA" else item.get(
                "publisher_id"),
            "is_created_by_publisher": item.get("is_created_by_publisher"),
            "college_id": str(item.get("college_id"))
        }

    async def application_serialize(self, item):
        """application serialize"""
        return {
            "_id": str(item.get("_id")),
            "spec_name1": item.get("spec_name1"),
            "spec_name2": item.get("spec_name2"),
            "student_id": str(item.get("student_id")),
            "course_id": str(item.get("course_id")),
            "college_id": str(item.get("college_id")),
            "payment_info": item.get("payment_info"),
            "enquiry_date": item.get("enquiry_date"),
            "last_updated_time": item.get("last_updated_time"),
            "school_name": item.get("school_name"),
            "is_created_by_publisher": item.get("is_created_by_publisher"),
            "is_created_by_user": item.get("is_created_by_user"),
            "custom_application_id": item.get("custom_application_id"),
            "current_stage": item.get("current_stage"),
            "declaration": item.get("declaration"),
            "payment_initiated": item.get("payment_initiated"),
            "allocate_to_counselor": counselor_serialize(item.get("allocate_to_counselor", {}))
        }
