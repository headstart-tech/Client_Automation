"""
    This file contains CRUD operations for managing master stages in MongoDB.
"""
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime, timezone

from app.core.custom_error import CustomError, DataNotFoundError
from app.core.utils import utility_obj, Utility
from app.database.configuration import DatabaseConfiguration
from app.helpers.client_student_dashboard_helper import Client
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.master_schema import SubStageSchema


class Master:
    def format_master_stage(self, stage) -> dict:
        """
            Converts a MongoDB document into a formatted response.

            params:
                stage: dict - MongoDB document representing a master stage.
            Returns:
                 dict - Formatted dictionary containing master stage details.
        """
        return {
            "id": str(stage.get("_id", "")),
            "stage_name": stage.get("stage_name", ""),
            "stage_order": stage.get("stage_order", 0),
            "sub_stages": [
                {
                    "sub_stage_id": str(sub.get("sub_stage_id", "")),
                    "sub_stage_order": sub.get("sub_stage_order", 0)
                }
                for sub in stage.get("sub_stages", [])
            ]
        }

    async def create_master_stage(self, stage_data: Dict[str, Any], current_user) -> Dict[str, Any]:
        """
           Creates a new master stage in the database.

           Params:
            stage_data: dict - Contains 'stage_name', 'stage_order', and optional 'sub_stages'.
           Raises:
            HTTPException: If the stage name or stage order already exists or insertion fails.
           Returns:
                dict - Success message and inserted stage ID.
        """
        await UserHelper().is_valid_user(current_user)

        stage_name = stage_data.get("stage_name")
        stage_order = stage_data.get("stage_order")

        if not stage_name or stage_order is None:
            raise CustomError(message="Stage name and stage order are required")

        existing_stage = await DatabaseConfiguration().stages.find_one({"stage_name": stage_name})
        if existing_stage:
            raise CustomError(message="Stage name already exists")

        existing_stage_order = await DatabaseConfiguration().stages.find_one(
            {"stage_order": stage_order})
        if existing_stage_order:
            raise CustomError(message="Stage order already exists")

        if "sub_stages" in stage_data:
            valid_sub_stages = []
            for sub in stage_data.get("sub_stages", []):
                sub_stage_id = sub.get("sub_stage_id")
                sub_stage_order = sub.get("sub_stage_order", 0)
                if sub_stage_id:
                    is_valid = await utility_obj.is_length_valid(sub_stage_id, "Sub Stage ID")
                    if not is_valid:
                        raise CustomError(message=f"Invalid sub_stage_id format: {sub_stage_id}")
                    try:
                        sub_stage_obj_id = ObjectId(sub_stage_id)
                    except Exception:
                        raise CustomError(message=f"Invalid sub_stage_id format: {sub_stage_id}")

                    existing_sub_stage = await DatabaseConfiguration().sub_stages.find_one(
                        {"_id": sub_stage_obj_id})
                    if not existing_sub_stage:
                        raise CustomError(message=f"Sub-stage with id {sub_stage_id} not found")

                    valid_sub_stages.append({
                        "sub_stage_id": sub_stage_obj_id,
                        "sub_stage_order": sub_stage_order
                    })
            stage_data["sub_stages"] = valid_sub_stages
        current_timestamp = datetime.now(timezone.utc)
        stage_data["created_at"] = current_timestamp
        stage_data["updated_at"] = current_timestamp

        result = await DatabaseConfiguration().stages.insert_one(stage_data)

        if not result.inserted_id:
            raise CustomError(message="Failed to insert stage")

        return {"message": "Stage created successfully", "id": str(result.inserted_id)}

    async def retrieve_all_master_stages(self, current_user):
        """
           Retrieves all master stages from the database.

           Returns:
                list - A list of formatted master stages.
           """
        await UserHelper().is_valid_user(current_user)
        return await DatabaseConfiguration().stages.aggregate([
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "stage_name": 1,
                    "stage_order": 1,
                    "sub_stages": {
                        "$map": {
                            "input": "$sub_stages",
                            "as": "sub_stage",
                            "in": {
                                "sub_stage_id": {"$toString": "$$sub_stage.sub_stage_id"},
                                "sub_stage_order": "$$sub_stage.sub_stage_order"
                            }
                        }
                    }
                }
            }
        ]).to_list(None)

    async def get_master_stage_by_id(self, stage_id, current_user):
        """
            Retrieves a single master stage by its ID.

            Params:
             stage_id: str - The ObjectId of the master stage.
            Return:
                 dict - Formatted master stage dictionary or None if not found.
            """
        await UserHelper().is_valid_user(current_user)
        stage = await DatabaseConfiguration().stages.find_one({"_id": ObjectId(stage_id)})
        return self.format_master_stage(stage) if stage else None

    async def update_master_stage(self, stage_id: str, update_data: dict, current_user):
        """
           Updates an existing master stage.

           Params:
            stage_id: str - The ObjectId of the master stage.
            update_data: dict - Dictionary containing updated values.
           Raises:
            HTTPException: If stage ID is invalid, stage does not exist, or update fails.
           Return: dict - Success message.
        """
        await UserHelper().is_valid_user(current_user)

        if not utility_obj.is_id_length_valid(stage_id, "stage_id"):
            raise CustomError(message=f"Invalid stage_id format: {stage_id}")

        stage_obj_id = ObjectId(stage_id)

        existing_stage = await DatabaseConfiguration().stages.find_one({"_id": stage_obj_id})
        if not existing_stage:
            raise DataNotFoundError(message="Stage")

        update_query = {}
        sub_stages_to_add = []

        if "stage_name" in update_data and update_data["stage_name"] != existing_stage.get(
                "stage_name"):
            existing_stage_name = await DatabaseConfiguration().stages.find_one(
                {"stage_name": update_data["stage_name"]}
            )
            if existing_stage_name:
                raise CustomError(message="Stage name already exists")
            update_query["stage_name"] = update_data["stage_name"]

        if "stage_order" in update_data and update_data["stage_order"] != existing_stage.get(
                "stage_order"):
            new_stage_order = update_data["stage_order"]
            current_stage_order = existing_stage.get("stage_order")

            if new_stage_order != current_stage_order:
                existing_stage_with_order = await DatabaseConfiguration().stages.find_one(
                    {"stage_order": new_stage_order}
                )
                if existing_stage_with_order:
                    update_query["stage_order"] = new_stage_order
                    update_query["previous_stage_order"] = current_stage_order
                    await DatabaseConfiguration().stages.update_one(
                        {"_id": existing_stage_with_order["_id"]},
                        {"$set": {"stage_order": current_stage_order}}
                    )
        if "sub_stages" in update_data:
            existing_sub_stages = existing_stage.get("sub_stages", [])
            existing_orders = {sub["sub_stage_order"]: sub["sub_stage_id"] for sub in
                               existing_sub_stages}

            for sub in update_data["sub_stages"]:
                sub_stage_id_str = str(sub["sub_stage_id"])
                new_sub_stage_order = sub["sub_stage_order"]

                if not ObjectId.is_valid(sub_stage_id_str):
                    raise CustomError(message=f"Invalid sub_stage_id format: {sub_stage_id_str}")

                sub_stage_obj_id = ObjectId(sub_stage_id_str)

                sub_stage_exists = await DatabaseConfiguration().sub_stages.find_one(
                    {"_id": sub_stage_obj_id})
                if not sub_stage_exists:
                    raise DataNotFoundError(message=f"Sub-stage ID {sub_stage_id_str} not found.")

                if new_sub_stage_order in existing_orders:
                    other_sub_stage_id = existing_orders[new_sub_stage_order]
                    existing_index = next(
                        (ind for ind, elem in enumerate(existing_sub_stages) if
                         elem["sub_stage_id"] == ObjectId(other_sub_stage_id)),
                        None
                    )
                    sub_index = next(
                        (ind for ind, elem in enumerate(existing_sub_stages) if
                         elem["sub_stage_id"] == ObjectId(sub_stage_obj_id)),
                        None
                    )

                    if existing_index is not None:
                        update_query[f"sub_stages.{existing_index}.sub_stage_order"] = len(
                            existing_orders) + 1

                    if sub_index is not None:
                        update_query[
                            f"sub_stages.{sub_index}.sub_stage_order"] = new_sub_stage_order
                    else:
                        sub_stages_to_add.append(
                            {"sub_stage_id": sub_stage_obj_id,
                             "sub_stage_order": new_sub_stage_order})
                else:
                    sub_stages_to_add.append(
                        {"sub_stage_id": sub_stage_obj_id, "sub_stage_order": new_sub_stage_order})
        bulk_update = {}
        if update_query:
            bulk_update["$set"] = update_query

        if sub_stages_to_add:
            bulk_update["$push"] = {"sub_stages": {"$each": sub_stages_to_add}}

        if bulk_update:
            update_result = await DatabaseConfiguration().stages.update_one({"_id": stage_obj_id},
                                                                            bulk_update)
            if update_result.modified_count == 0:
                raise CustomError(message="Update failed. No changes were made.")

        return {"message": "Master stage updated successfully"}

    async def delete_master_stage_by_id(self, stage_id, current_user):
        """
            Deletes a master stage by ID.

            Params:
             stage_id: str - The ObjectId of the master stage.
            Raises:
             HTTPException: If stage is not found.
            Return: dict - Success message.
            """
        await UserHelper().is_valid_user(current_user)
        result = await DatabaseConfiguration().stages.delete_one({"_id": ObjectId(stage_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Stage not found")

        return {"message": "Stage deleted successfully"}

    def format_master_sub_stage(self, sub_stage: dict) -> dict:
        """
        Converts a MongoDB document into a formatted response for a master sub-stage.

        Params:
            sub_stage: dict - MongoDB document representing a master sub-stage.

        Returns:
            dict - Formatted dictionary containing master sub-stage details.
        """
        return {
            "id": str(sub_stage.get("_id", "")),
            "sub_stage_name": sub_stage.get("sub_stage_name", ""),
            "fields": [
                {
                    "name": field.get("name", ""),
                    "label": field.get("label", ""),
                    "type": field.get("type", ""),
                    "is_required": field.get("is_required", False),
                    "description": field.get("description", ""),
                    "locked": field.get("locked", False),
                    "is_custom": field.get("is_custom", False),
                    "depends_on": field.get("depends_on")
                }
                for field in sub_stage.get("fields", [])
            ]
        }

    async def create_sub_stage(self, sub_stage_data: dict, current_user) -> dict:
        """
            Creates a new sub-stage in the database.

            Params:
                sub_stage_data (dict): Contains 'sub_stage_name' and 'fields' to create a sub-stage.

            Raises:
                HTTPException (400): If a sub-stage with the same name already exists.
                HTTPException (500): If insertion fails.

            Returns:
                dict: Success message and inserted sub-stage ID.
            """
        await UserHelper().is_valid_user(current_user)
        existing_sub_stage = await DatabaseConfiguration().sub_stages.find_one(
            {"sub_stage_name": {"$regex": f"^{sub_stage_data['sub_stage_name']}$", "$options": "i"}}
        )
        if existing_sub_stage:
            raise CustomError(
                message=f"Sub-stage '{sub_stage_data['sub_stage_name']}' already exists.")
        for field in sub_stage_data.get("fields", []):
            key_name = field.get("key_name", "")

            if not re.fullmatch(r"^[a-z]+(_[a-z]+)*$", key_name):
                raise CustomError(
                    message=f"Invalid format for key name '{key_name}'. Key name should be in snake_case (e.g., 'mother_name')."
                    )
        current_timestamp = datetime.now(timezone.utc)
        sub_stage_data["created_at"] = current_timestamp
        sub_stage_data["updated_at"] = current_timestamp

        result = await DatabaseConfiguration().sub_stages.insert_one(sub_stage_data)

        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to insert sub-stage.")

        return {"message": "Sub-stage created successfully", "id": str(result.inserted_id)}

    async def get_sub_stage(self, sub_stage_id, current_user):
        """
            Retrieves a single sub-stage by its ID.
            Params:
                sub_stage_id (str): The ObjectId of the sub-stage.
            Returns:
                dict: Formatted sub-stage dictionary or None if not found.
            """
        await UserHelper().is_valid_user(current_user)
        sub_stage = await DatabaseConfiguration().sub_stages.find_one(
            {"_id": ObjectId(sub_stage_id)})
        return self.format_master_sub_stage(sub_stage) if sub_stage else None

    async def get_all_sub_stages(self, current_user):
        """
            Retrieves all sub-stages from the database.

            Returns:
                list[dict]: A list of sub-stage objects with formatted fields.
            """
        await UserHelper().is_valid_user(current_user)
        pipeline = [
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "sub_stage_name": 1,
                    "fields": {
                        "$map": {
                            "input": "$fields",
                            "as": "field",
                            "in": {
                                "name": "$$field.name",
                                "label": "$$field.label",
                                "type": "$$field.type",
                                "is_required": "$$field.is_required",
                                "description": "$$field.description",
                                "locked": "$$field.locked",
                                "is_custom": "$$field.is_custom",
                                "depends_on": "$$field.depends_on"
                            }
                        }
                    }
                }
            }
        ]
        sub_stages = await DatabaseConfiguration().sub_stages.aggregate(pipeline).to_list(None)
        return sub_stages

    async def update_master_sub_stage(self, sub_stage_id: str, sub_stage_data: dict, current_user):
        """
            Updates an existing sub-stage by its ID.

            Params:
                sub_stage_id (str): The ObjectId of the sub-stage.
                sub_stage_data (dict): The updated sub-stage data.
            Raises:
                HTTPException (400): If the ID format is invalid.
                HTTPException (404): If the sub-stage is not found.
                HTTPException (400): If duplicate fields are being inserted.
                HTTPException (500): If the update fails.
            Returns:
                dict: Success message.
            """
        await UserHelper().is_valid_user(current_user)
        if not ObjectId.is_valid(sub_stage_id):
            raise CustomError(message="Invalid sub_stage_id format")

        sub_stage = SubStageSchema(**sub_stage_data)

        existing_sub_stage = await DatabaseConfiguration().sub_stages.find_one(
            {"_id": ObjectId(sub_stage_id)})
        if not existing_sub_stage:
            raise DataNotFoundError(message="Sub-stage")

        existing_fields_dict = {field["name"].strip().lower(): field for field in
                                existing_sub_stage.get("fields", [])}

        updated_fields_dict = {}

        for field in sub_stage.fields:
            field_name = field.name.strip().lower()
            if not re.fullmatch(r"^[a-z]+(_[a-z]+)*$", field_name):
                raise CustomError(
                    message=f"Invalid format for field name '{field_name}'. Field name should be in snake_case (e.g., 'mother_name')."
                )

            if field_name in updated_fields_dict:
                raise CustomError(message=f"Duplicate field '{field.name}' is being inserted.")

            existing_fields_dict[field_name] = {
                "name": field.name,
                "label": field.label,
                "type": field.type,
                "is_required": field.is_required,
                "description": field.description,
                "locked": field.locked,
                "is_custom": field.is_custom,
                "depends_on": field.depends_on,
            }

            updated_fields_dict[field_name] = True
        updated_fields = list(existing_fields_dict.values())

        update_data = {
            "sub_stage_name": sub_stage.sub_stage_name,
            "fields": updated_fields,
            "updated_at": datetime.utcnow()
        }
        if (
                sub_stage.sub_stage_name == existing_sub_stage.get("sub_stage_name")
                and updated_fields == existing_sub_stage.get("fields")
        ):
            return {"message": "No changes detected, sub-stage remains the same."}
        result = await DatabaseConfiguration().sub_stages.update_one(
            {"_id": ObjectId(sub_stage_id)}, {"$set": update_data}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Update failed, please try again")

        return {"message": "Sub-stage updated successfully"}

    async def delete_master_sub_stage_by_id(self, sub_stage_id, current_user):
        """
            Deletes a master sub stage by ID.

            Params:
             sub_stage_id: str - The ObjectId of the master sub stage.
            Raises:
             HTTPException: If sub_stage is not found.
            Return: dict - Success message.
            """
        await UserHelper().is_valid_user(current_user)
        result = await DatabaseConfiguration().sub_stages.delete_one(
            {"_id": ObjectId(sub_stage_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Sub Stage not found")

        return {"message": "Sub Stage deleted successfully"}


    async def check_key_name_uniqueness(self, key_name: str, current_user, client_id: Optional[str] = None, college_id: Optional[str] = None) -> dict:
        """
        Validates the uniqueness and format of a given key name for custom application fields.

        Parameters:
            key_name (str): The key name to validate. It must be in snake_case format
                            (e.g., 'name_1', 'father_name').
            current_user (User): The authenticated user performing the validation.
            client_id (Optional[str]): The client ID (required if college_id is not provided).
            college_id (Optional[str]): The college ID (required if client_id is not provided).

        Returns:
            dict: A message indicating whether the key name is unique.

        Raises:
            CustomError: If the key name format is invalid (not snake_case).
            CustomError: If neither client_id nor college_id is provided.
            CustomError: If the key name already exists.
            HTTPException (403): If the user is not valid.
        """
        await UserHelper().is_valid_user(current_user)
        if not re.match(r"^[a-z][a-z0-9_]*[a-z0-9]$", key_name):
            raise CustomError(message="Invalid format. Key name should be in snake_case format (e.g., 'name_1')."
            )
        if not client_id and not college_id:
            raise CustomError(message="Either clientId or collegeId must be provided"
            )

        client_instance = Client()
        fields_list, total_count = await client_instance.get_all_fields(
            current_user=current_user,
            client_id=client_id,
            college_id=college_id,
            page_num=1,
            page_size=1000000,
            search=None
        )

        existing_key_names = {
            field.get("key_name", "").lower()
            for field in fields_list if "key_name" in field
        }

        if key_name.lower() in existing_key_names:
            raise CustomError(message="Key name already exists")

        return {"message": "Key name is unique"}

    async def get_stages_sub_stages_data(self, current_user):
        """
           Retrieve all master stages along with their associated sub-stages and fields.
           Params:
               current_user (User): The authenticated user making the request.
           Returns:
               list: A list of dictionaries containing stage details, including sub-stage names and associated fields.
           Raises:
               HTTPException (403): If the user is not valid.
               HTTPException (500): If an error occurs while fetching data from the database.
        """
        await UserHelper().is_valid_user(current_user)
        pipeline = [
            {
                '$lookup': {
                    'from': 'sub_stages',
                    'localField': 'sub_stages.sub_stage_id',
                    'foreignField': '_id',
                    'as': 'sub_stage_details'
                }
            }, {
                '$sort': {
                    'stage_order': 1,
                    'sub_stages.sub_stage_order': 1
                }
            }, {
                '$project': {
                    '_id': 0,
                    'stage_name': 1,
                    'fields': {
                        '$map': {
                            'input': '$sub_stage_details',
                            'as': 'sub_stage',
                            'in': {
                                'sub_stage': '$$sub_stage.sub_stage_name',
                                'fields': '$$sub_stage.fields'
                            }
                        }
                    }
                }
            }
        ]
        stages_data = await DatabaseConfiguration().stages.aggregate(pipeline).to_list(None)
        form_details = await DatabaseConfiguration().student_registration_forms.find_one({}, {
            "student_registration_form_fields": 1, "_id": 0})
        return {
            "application_form": stages_data,
            "student_registration_form_fields": form_details
        }


    async def get_application_form_templates(self, current_user):
        """
           Retrieve all application form templates from the database.
           Params:
               current_user (User): The authenticated user making the request.
           Returns:
               List[Dict]: A list of templates, each containing:
                   - template_name (str): Name of the template.
                   - template_type (str): Type/category of the template.
                   - template_details (List[Dict]): A list of sections in the template with:
                       - section_title (str): Title of the section.
                       - is_template (bool): Indicates if it is a reusable template.
                       - can_repeat_template (bool): Indicates if the template can repeat.
                       - repeat_count (int): Number of times the template can be repeated.
                       - fields (List[Dict]): Field details for each section.
           Raises:
               UnauthorizedError: If the user is not valid.
           """
        await UserHelper().is_valid_user(current_user)
        return await DatabaseConfiguration().templates.aggregate([
            {
                "$project": {
                    "_id": 0,
                    "template_name": 1,
                    "template_type": 1,
                    "template_details.section_title": 1,
                    "template_details.is_template": 1,
                    "template_details.can_repeat_template": 1,
                    "template_details.repeat_count": 1,
                    "template_details.fields": 1,
                    "template_details.table.result_mode_fields": 1,
                    "template_details.table.headers": 1,
                    "template_details.table.rows": 1,
                    "template_details.table.fields": 1,
                    "template_details.table.can_repeat_template": 1,
                    "template_details.table.repeat_count": 1,
                    "template_details.table.initial_row_count": 1,
                    "template_details.table.mandatory_row": 1,
                }
            }
        ]).to_list(None)