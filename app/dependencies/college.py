"""
This file contain functions related to college dependency
"""
from bson import ObjectId
from fastapi.exceptions import HTTPException

from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache
from app.helpers.college_configuration import CollegeHelper


async def get_college_id(college_id: str, short_version: bool= False):
    """
    Get college dependency
    """
    await utility_obj.is_id_length_valid(college_id, name="College id")
    collection_name = "colleges/short_version" if short_version else "colleges"
    college = await get_collection_from_cache(collection_name=collection_name, field=college_id)
    if not college:
        match = {"_id": ObjectId(college_id)}
        if short_version and short_version not in ["false"]:
            college = await DatabaseConfiguration().college_collection.find_one(
                match,
                {
                    "_id": 1,
                    "associated_client_id": 1,
                    "lead_stage_label": 1,
                    "system_preference": 1,
                    "email_preferences": 1,
                    "languages": 1,
                    "fee_rules": 1,
                    "enforcements": 1,
                    "course_categories": 1,
                    "stage_values": 1,
                    "file_format": 1
                })
        else:
            college = await DatabaseConfiguration().college_collection.find_one(
                match)
        if college:
            await store_collection_in_cache(collection=college,
                                            collection_name=collection_name, expiration_time=10800, field=college_id)
    if not college:
        raise HTTPException(status_code=422, detail="College not found.")
    return CollegeHelper().college_helper(college)


def get_college_id_short_version(short_version: bool):
    async def dependency(college_id: str):
        return await get_college_id(college_id, short_version=short_version)
    return dependency
