"""
This file contain class and functions related to campaign rules
"""
from app.database.configuration import DatabaseConfiguration
from app.helpers.campaign.campaign_configuration import RuleHelper


class CampaignRule:
    """
    Contain functions related to campaign rule activities
    """

    async def get_all_rules(self, skip, limit):
        """
        Retrieve all rules from the collection named rule and return it
        """
        result = DatabaseConfiguration().rule_collection.aggregate(
            [
                {"$sort": {"updated_on": -1}},
                {"$skip": skip},
                {"$limit": limit},
            ]
        )
        return [await RuleHelper().rule_helper(document) async for document in result]
