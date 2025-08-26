"""
This file contains class and functions related to followup lead stage
"""
from bson import ObjectId

from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import cache_invalidation
from app.helpers.followup_queries.followup_notes_configuration import lead_stage_label


class add_lead_stage_label(lead_stage_label):
    """
    Contain functions related to followup stage
    """

    async def add_lead_stage_label_data(self, lead_stage, label, college_id):
        lead_stage_with_label = await self.get_lead_stage_label(college_id)
        if lead_stage in list(lead_stage_with_label.get("lead_stage_label", {}).keys()):
            label_lst = lead_stage_with_label.get("lead_stage_label", {}).get(lead_stage)
            label_lst.append(label)
            label_lst = list(set(label_lst))
            lead_stage_with_label["lead_stage_label"][lead_stage] = label_lst
            await DatabaseConfiguration().college_collection.update_one(
                {"_id": ObjectId(lead_stage_with_label.get("_id"))},
                {"$set": {
                    "lead_stage_label": lead_stage_with_label.get("lead_stage_label")}})
        elif lead_stage_with_label.get("lead_stage_label") is not None:
            lead_stage_with_label["lead_stage_label"][lead_stage] = [label]
            await DatabaseConfiguration().college_collection.update_one(
                {"_id": ObjectId(lead_stage_with_label.get("_id"))},
                {"$set": {
                    "lead_stage_label": lead_stage_with_label.get("lead_stage_label")}})
        else:
            await DatabaseConfiguration().college_collection.update_one(
                {"_id": ObjectId(lead_stage_with_label.get("_id"))},
                {"$set": {
                    "lead_stage_label": {lead_stage: [label]}}})
        await cache_invalidation(api_updated="updated_college", user_id=college_id)
        return await self.get_lead_stage_label(college_id)
