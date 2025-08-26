"""
This file contain class and functions related to role
"""
from app.database.configuration import DatabaseConfiguration


class Role:
    """
    Contain functions related to role activities
    """

    async def retrieve_all_menus_and_permissions(self):
        """
        Get all leads based on associated_source_value
        """
        result = DatabaseConfiguration().role_collection.aggregate(
            [{"$project": {"_id": 0, "role_name": 1, "permission": 1, "menus": 1, "student_menus": 1}}]
        )
        return result
