"""
This file contain class and methods for get data regarding payment
"""
from bson import ObjectId
from app.database.configuration import DatabaseConfiguration
from app.core.utils import Utility


class Payment:
    """
    Contain functions related to payment activities
    """

    async def payment_pipeline_based_on_condition(
            self, start_date, end_date, payload, emails=False, numbers=False):
        """
        Get pipeline of payments status
        """
        pipeline = [
            {
                "$project": {
                    "_id": 1,
                    "payment_id": 1,
                    "user_id": 1,
                    "details": 1,
                    "error": 1,
                    "status": 1,
                }
            },
            {
                "$lookup": {
                    "from": "studentsPrimaryDetails",
                    "let": {"id": "$user_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$id"]}}},
                        {"$project": {
                            "_id": 1,
                            "basic_details": 1,
                            "source": 1
                        }},
                    ],
                    "as": "student_primary",
                }
            },
            {
                "$unwind": {
                    "path": "$student_primary"
                }
            },
            {
                "$lookup": {
                    "from": "leadsFollowUp",
                    "let": {"id": "$student_primary._id"},
                    "pipeline": [
                        {"$match": {
                            "$expr": {"$eq": ["$student_id", "$$id"]}}},
                        {
                            "$project": {
                                "_id": 0,
                                "lead_stage": 1
                            }
                        },
                    ],
                    "as": "student_lead_stage"
                }
            },
            {
                "$unwind": {
                    "path": "$student_lead_stage",
                    "preserveNullAndEmptyArrays": True
                }
            }
        ]
        if payload is None:
            payload = {}
        if start_date not in ["", None] and end_date not in ["", None]:
            pipeline.insert(0, {
                "$match": {
                    "error.created_at": {"$gte": start_date, "$lte": end_date}
                }
            })
        elif start_date not in ["", None] and end_date in [None, ""]:
            pipeline.insert(0, {
                "$match": {
                    "error.created_at": {"$gte": start_date}
                }
            })
        if payload.get("payment_status", []):
            payment_data = []
            if "Successful" in payload.get("payment_status", []):
                payment_data.append({"payment_info.status": "captured"})
            if "Failed" in payload.get("payment_status", []):
                payment_data.append({"payment_info.status": "failed"})
            if "In Progress" in payload.get("payment_status", []):
                payment_data.append({"$and": [{"payment_initiated": True},
                                              {"payment_info.status": {
                                                  "$ne": "captured"}}]})
            pipeline.insert(0,
                            {"$match": {"$or": payment_data}}
                            )
        paginated_results = [{"$limit": 15}]
        if emails or numbers:
            paginated_results = []
        pipeline.append(
            {
                "$facet": {
                    "paginated_results": paginated_results,
                    "totalCount": [{"$count": "count"}],
                }
            }
        )
        return pipeline

    async def get_payment_details_by_app_id(self, application_id: ObjectId) \
            -> list:
        """
        Get the payment details by application id.

        Params:
            - application_id (ObjectId): An unique identifier of application
                id in the form of ObjectId.

        Returns:
            - list: A list which contains payments details by application id.
        """
        result = DatabaseConfiguration().payment_collection.aggregate(
            [{"$match": {"details.application_id": application_id}},
             {
                 "$project": {
                     "_id": 0,
                     "payment_id": 1,
                     "order_id": 1,
                     "date": "$error.created_at",
                     "status": 1,
                     "payment_method": {
                         "$ifNull": ["$payment_method", "As per Flow"]
                     }
                 }
             }
             ]
        )
        payments_data = []
        async for data in result:
            payment_date = data.get("date")
            if payment_date:
                data["date"] = Utility().get_local_time(payment_date)
            payments_data.append(data)
        return payments_data
