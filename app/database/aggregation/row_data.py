"""
This file contain class and methods for get all raw data by aggregation on the collection named raw_data or offline_data
"""
from bson import ObjectId

from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.models.serialize import StudentCourse


class RawData:
    """
    Contain functions related to raw data activities
    """

    async def retrieve_raw_data(self, skip, limit):
        """
        Retrieve all raw data from the collection raw_data
        """
        result = DatabaseConfiguration().raw_data.aggregate(
            [
                {"$match": {"mandatory_field": {"$ne": False}}},
                {"$sort": {"created_at": -1}},
                {"$skip": skip},
                {"$limit": limit},
            ]
        )
        return [{
            "id": str(document.get("_id")),
            "mandatory_field": {
                key: str(value)
                for key, value in document.get("mandatory_field").items()
                if value is not None
            },
            "offline_data_id": str(document.get("offline_data_id")),
            "duplicate_data": document.get("duplicate_data"),
            "other_field": {
                key: value
                for key, value in document.get("other_field").items()
                if value is not None
            },
            "created_at": f"{utility_obj.get_local_time(document.get('created_at'))}",
        } async for document in result]

    async def retrieve_raw_data_names(self):
        """
        Retrieve all raw data names from the collection offline_data
        """
        result = DatabaseConfiguration().offline_data.aggregate(
            [
                {"$sort": {"uploaded_on": -1}},
                {
                    '$project': {
                        'data_name': 1,
                        "successful_lead_count": 1
                    }
                }
            ]
        )
        return [{"raw_data_name": document.get('data_name'),
                 "count": document.get("successful_lead_count")}
                async for document in result]

    async def retrieve_successful_lead(self, skip, limit, offline_id):
        """
        Get successful leads data
        """
        data = DatabaseConfiguration().raw_data.aggregate(
            [
                {"$match": {"offline_data_id": ObjectId(offline_id)}},
                {"$skip": skip},
                {"$limit": limit}
            ]
        )
        return [{
            "id": str(document.get("_id")),
            "mandatory_field": {
                key: str(value)
                for key, value in document.get("mandatory_field").items()
                if value is not None
            },
            "offline_data_id": str(document.get("offline_data_id")),
            "other_field": {
                key: value
                for key, value in document.get("other_field").items()
                if value is not None
            },
            "created_at": f"{utility_obj.get_local_time(document.get('created_at'))}",
        } async for document in data]

    async def system_retrieve_successful_lead(self, skip, limit, offline_id):
        """
        Get system lead data who upload by user by csv file
        """
        data = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            [
                {"$match": {"lead_data_id": ObjectId(offline_id)}},
                {"$skip": skip},
                {"$limit": limit}
            ]
        )
        return [StudentCourse().student_primary(item) async for item in data]

    async def retrieve_raw_data_mandatory_fields(self, offline_ids):
        """
        Retrieve all raw data names from the collection offline_data
        """
        result = DatabaseConfiguration().raw_data.aggregate(
            [
                {"$match": {"offline_data_id": {
                    "$in": [ObjectId(offline_id) for offline_id in offline_ids]}
                }},
                {
                    '$project': {
                        '_id': 0,
                        'mandatory_field': 1
                    }
                }
            ]
        )
        return [document async for document in result]
