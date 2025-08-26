"""
This file contains class and functions related to country, state and city
"""
from app.database.configuration import DatabaseConfiguration


class CountryStateCity:
    """
    Contains functions related to country, state and city
    """

    async def get_cities_based_on_states(self, payload: dict) -> dict:
        """
        Get cities based on multiple state codes.

        Params:
            payload (dict): A which contains filters which useful for get
                cities data based on country code and state codes.

        Returns:
             dict: A dictionary which contains cities data based on country
             code and state codes.
        """
        pipeline = [{"$match": {"country_code": payload.get("country_code"),
                                "state_code":
                                    {"$in": payload.get("state_code")}}},
                    {
                        "$group": {
                            "_id": "",
                            "cities": {
                                "$push": {
                                    "label": "$name",
                                    "value": "$name",
                                    "role": "$state_name"
                                }
                            }
                        }
                    }
                    ]
        async for document in DatabaseConfiguration().city_collection.aggregate(
                pipeline):
            return document.get("cities", [])
