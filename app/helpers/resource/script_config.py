"""
This file contain class and functions related to Script Query
"""
import datetime
from enum import Enum

from bson.objectid import ObjectId

from app.core.custom_error import CustomError, DataNotFoundError
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import cache_invalidation


class ScriptFields(Enum):
    SCRIPT_NAME = "script_name"
    PROGRAM_NAME = "program_name"
    SCRIPT_TEXT = "script_text"
    SAVE_OR_DRAFT = "save_or_draft"


class ScriptQuery:
    """
    Script related functions
    """

    async def update_script(self, script_dict: dict, script_id: str | None,
                            last_modified_timeline: list) -> dict:
        """
        Update the script by script_id.
        """

        await utility_obj.is_length_valid(script_id, name="Script id")
        if (await DatabaseConfiguration().scripts_details.find_one(
                {"_id": ObjectId(script_id)})) is None:
            # If invalid ID of the script.
            raise CustomError(f"Script not found by id: {script_id}")

        # Create data segment of which contains None if there is empty field
        # in place of blank.
        script_data = {key: value for key, value in script_dict.items() if
                       value is not None}

        if len(script_data) >= 1:
            '''
            validate if there is any data for updation or not.
            '''

            await DatabaseConfiguration().scripts_details.update_one(
                {'_id': ObjectId(script_id)},
                {
                    "$set": script_data,
                    "$push": {
                        "last_modified_timeline": {
                            "$each": [last_modified_timeline[0]],
                            "$position": 0
                        }
                    }
                }
            )
            await cache_invalidation(api_updated="resource/create_or_update_a_script")
            return {"message": "Script updated successfully."}

        return {"message": "There is nothing to update."}

    async def insert_script(self, script_dict: dict, user_name: str,
                            user_id: ObjectId, last_modified_timeline: list,
                            created_at) -> dict:
        """
        Add a new script in the database.
        """

        # Validation of mandatory fields
        if not (script_dict.get(
                ScriptFields.SCRIPT_NAME.value) and script_dict.get(
                ScriptFields.PROGRAM_NAME.value) and script_dict.get(
                ScriptFields.SCRIPT_TEXT.value) and script_dict.get(
                ScriptFields.SAVE_OR_DRAFT.value) in ['save', 'draft']):
            raise CustomError("Required fields has not passed.")

        script_dict.update(
            {
                "created_by": user_name,
                "created_by_id": user_id,
                "created_at": created_at,
                "last_modified_timeline": last_modified_timeline
            }
        )
        await DatabaseConfiguration().scripts_details.insert_one(script_dict)
        await cache_invalidation(api_updated="resource/create_or_update_a_script")
        return {"message": "Script created successfully."}

    async def create_or_update_script(self, script_dict: dict, user: dict,
                                      script_id: str | None) -> dict:
        """
        Create or Update script.

        Params:
            - script_dict (dict): A dictionary which contains script add data
                which want to add/update.
            - user (dict): A dictionary which contains user details.
            - script_id (str | None): script id which useful for update script
                data.

        Returns:
            dict: A dictionary which contains information about add/update
                script.
        """

        created_at = datetime.datetime.utcnow()  # current date time
        user_name = utility_obj.name_can(user)
        user_id = ObjectId(user.get("_id"))  # user id
        last_modified_timeline = [
            {
                "last_modified_at": created_at,
                "user_id": user_id,
                "user_name": user_name,
            }
        ]

        await cache_invalidation(api_updated="telephony/multiple_check_in_or_out")

        if script_id not in ['', None]:
            return await self.update_script(script_dict, script_id,
                                            last_modified_timeline)

        else:
            return await self.insert_script(script_dict, user_name, user_id,
                                            last_modified_timeline, created_at)

    async def get_all_scripts(
            self, all: bool, course: list, sort, sort_type, sort_field, tags,
            application_stage, lead_stage, source):
        """
        Returns all/ draft scripts.

        Params:
           - all (bool): If true return all scripts, if false return draft
                scripts
           - course (list): The course filter if required.

        Returns:
           dict : A dictionary of all scripts.
        """
        base_match = {"save_or_draft": "save"}
        if not all:
            base_match.update({"save_or_draft": "draft"})
        if course:
            base_match.update({"program_name": {"$in": course}})
        if application_stage not in ["", None]:
            base_match.update({"$or": [{"$and": [
                {"application_stage": {"$exists": True, "$ne": []}, },
                {"application_stage": {"$in": [application_stage]}}
            ]}, {"$and": [
                {"application_stage": {"$exists": True, "$eq": []}}
            ]}]})
        if lead_stage not in ["", None]:
            lead_match = {"$or": [{"$and": [
                {"lead_stage": {"$exists": True, "$ne": []}, },
                {"lead_stage": {"$in": [lead_stage]}}
            ]}, {"$and": [
                {"lead_stage": {"$exists": True, "$eq": []}}
            ]}]}
            if "$or" in base_match:
                base_match.update({"$and": [lead_match, {"$or": base_match.pop("$or")}]})
            else:
                base_match.update(lead_match)
        if source:
            source_match = {"$or": [{"$and": [
                {"source_name": {"$exists": True, "$ne": []}, },
                {"source_name": {"$in": source}}
            ]}, {"$and": [
                {"source_name": {"$exists": True, "$eq": []}}
            ]}]}
            if "$and" in base_match:
                multiple_stages = [source_match] + base_match.pop(
                    "$and")
                base_match.update({"$and": multiple_stages})
            elif "$or" in base_match:
                base_match.update({"$and": [source_match,
                                             {"$or": base_match.pop("$or")}]})
            else:
                base_match.update(source_match)
        if tags:
            tag_match = {"$or": [{"$and": [
                {"tags": {"$exists": True, "$ne": []}, },
                {"tags": {"$in": tags}}
            ]}, {"$and": [
                {"tags": {"$exists": True, "$eq": []}}
            ]}]}
            if "$and" in base_match:
                multiple_stages = [tag_match] + base_match.pop(
                    "$and")
                base_match.update({"$and": multiple_stages})
            elif "$or" in base_match:
                base_match.update({"$and": [tag_match,
                                            {"$or": base_match.pop("$or")}]})
            else:
                base_match.update(tag_match)
        pipeline = [
            {
                "$match": base_match
            },
            {
                "$addFields": {
                    "last_modified_timeline": {
                        "$arrayElemAt": ["$last_modified_timeline", 0]}
                }
            },
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "script_name": "$script_name",
                    "created_date": {
                        "$dateToString": {"format": "%Y-%m-%d %H:%M:%S",
                                          "date": "$created_at"}},
                    "last_updated_date": {
                        "$dateToString": {"format": "%Y-%m-%d %H:%M:%S",
                                          "date": "$last_modified_timeline.last_modified_at"}},
                    "source_name": "$source_name",
                    "program_name": "$program_name",
                    "application_stage": "$application_stage",
                    "lead_stage": {
                                "$ifNull": ["$lead_stage", "Fresh Lead"]
                            },
                    "tags": "$tags",
                    "content": "$script_text",
                    "edited_by": "$last_modified_timeline.user_name"
                }
            }
        ]
        if sort:
            pipeline.insert(1, {
                "$sort": {sort_field: -1 if sort_type == "dsc" else 1}})
        else:
            pipeline.insert(1, {
                "$sort": {"created_at": -1}})
        data = await DatabaseConfiguration().scripts_details.aggregate(
            pipeline).to_list(None)
        return data

    async def delete_script(self, script_id: str) -> str:
        """
        Delete a script by id.

        Params:
          - script_id (str): An unique id of a script.

        Returns:
            - str: information about a delete a script.
        """

        if (await DatabaseConfiguration().scripts_details.find_one(
                {"_id": ObjectId(script_id)})) is None:
            raise DataNotFoundError(message="Script", _id=script_id)
        DatabaseConfiguration().scripts_details.delete_one(
            {"_id": ObjectId(script_id)})
        return "Script deleted successfully!"
