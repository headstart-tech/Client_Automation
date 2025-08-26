"""
This file contain class and functions related to email activity
"""
from bson import ObjectId

from app.database.configuration import DatabaseConfiguration


class Email:
    """
    Contain functions related to email activities
    """

    async def email_sent_by_counselor_count(self, start_date, end_date, counselor_id):
        """
        Return count of email sent by counselor
        """
        result = DatabaseConfiguration().activity_email.aggregate(
            [
                {
                    "$match": {
                        "user_id": ObjectId(counselor_id),
                        "created_at": {"$gte": start_date, "$lte": end_date},
                    }
                },
                {"$facet": {"totalCount": [{"$count": "count"}]}},
            ]
        )
        total_data = 0
        async for data in result:
            try:
                total_data = data.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
        return total_data
