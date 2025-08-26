"""
This module provides helper functions for managing client stages, sub-stages, and field operations.
"""
import re
from datetime import datetime
from typing import Optional
from fastapi.encoders import jsonable_encoder

from app.core.custom_error import CustomError, DataNotFoundError
from app.core.utils import utility_obj, Utility
from app.database.configuration import DatabaseConfiguration
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.client_student_dashboard_schema import ClientStageCreate, SubStageSchema, CustomFieldSchema
from fastapi import HTTPException
from bson import ObjectId

class Client:
    """
      A class to manage client-related operations.
      """
    async def default_client_stages(self, client_id: str,current_user):
        """
                Sets the default client stages for a given client ID.
                Params:
                    client_id (str): The ID of the client for whom the default stages need to be set.
                    current_user: The currently authenticated user.
                Returns:
                    dict: A success message if the stages are set successfully.
                Raises:
                    HTTPException: If no stages are found for the client (404).
                    HTTPException: If any exception occurs during execution (500).
                """
        await UserHelper().is_valid_user(current_user)
        try:
            client_object_id = ObjectId(client_id)
            pipeline=[
                {
                    "$project": {
                        "_id": 0,
                        "stage_name": 1,
                        "description": 1,
                        "stage_order": 1,
                        "sub_stages": 1,
                        "client_id": client_object_id
                    }
                }
            ]
            result = await DatabaseConfiguration().stages.aggregate(pipeline).to_list(None)
            if not result:
                raise DataNotFoundError(message="stages")
            await DatabaseConfiguration().client_stages.insert_many(result)
            return {"message": "Default client stages set successfully"}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def create_client_stage(self, client_id: str, client_stage: ClientStageCreate):
        """
        Creates client-specific stages based on master stages.
        Params:
        - client_id (str): The ID of the client inheriting the stages.
        - client_stage (ClientStageCreate): The stage details.
        Returns:
        - dict: Success message with the inserted stage ID.
        """
        existing_stage = await DatabaseConfiguration().client_stages.find_one({
            "client_id": ObjectId(client_id),
            "stage_name": client_stage.stage_name
        })
        if existing_stage:
            raise CustomError(message="Stage name already exists for this client")

        existing_stage_order = await DatabaseConfiguration().client_stages.find_one({
            "client_id": ObjectId(client_id),
            "stage_order": client_stage.stage_order
        })
        if existing_stage_order:
            raise CustomError(message="Stage order already exists for this client")
        stage_data = client_stage.dict()
        stage_data["client_id"] = ObjectId(client_id)
        stage_data["created_at"] = datetime.utcnow()
        stage_data["updated_at"] = datetime.utcnow()
        if "sub_stages" in stage_data:
            stage_data["sub_stages"] = [
                {"sub_stage_id":ObjectId(sub["sub_stage_id"]) , "sub_stage_order": sub["sub_stage_order"]}
                for sub in stage_data["sub_stages"]
            ]
        result = await DatabaseConfiguration().client_stages.insert_one(stage_data)
        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to insert client stage")

        return {"message": "Client stage created successfully", "id": str(result.inserted_id)}


    async def retrieve_all_client_stages(self, current_user):
        """
               Retrieves all client stages from the database based on the authenticated user's associated client.
               Params:
                   current_user: The currently authenticated user.
               Returns:
                   list: A list of formatted client stages, where each stage includes:
                       - `_id`: The string representation of the stage ID.
                       - `stage_name`: The name of the stage.
                       - `stage_order`: The order of the stage.
                       - `client_id`: The string representation of the client ID.
                       - `sub_stages`: A list of sub-stage details, including:
                           - `sub_stage_id`: The string representation of the sub-stage ID.
                           - `sub_stage_order`: The order of the sub-stage.
               Raises:
                   HTTPException: If the client ID is not found for the user (400).
                   HTTPException: If no client stages are found (404).
                   HTTPException: If any unexpected error occurs (500).
               """
        user = await UserHelper().is_valid_user(current_user)
        client_id = user.get("associated_client")
        if not client_id:
            raise DataNotFoundError(message="Client ID not found for user")
        try:
            pipeline = [
                {
                    "$project": {
                        "_id": {"$toString": "$_id"},
                        "stage_name": 1,
                        "stage_order": 1,
                        "client_id": {"$toString": "$client_id"},
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
            ]
            result = await DatabaseConfiguration().client_stages.aggregate(pipeline).to_list(None)
            if not result:
                raise DataNotFoundError(message="client stages")
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_client_stage_by_id(self, stage_id, current_user):
        """
               Retrieves a single client stage by its ID.
               Params:
                   stage_id (str): The ObjectId of the client stage as a string.
                   current_user: The currently authenticated user.
               Returns:
                   dict | None: A formatted client stage dictionary if found, otherwise None.
               Raises:
                   HTTPException: If the stage ID is invalid.
        """
        await UserHelper().is_valid_user(current_user)
        stage = await DatabaseConfiguration().client_stages.find_one({"_id": ObjectId(stage_id)})
        return self.format_client_stage(stage) if stage else None

    def format_client_stage(self, stage) -> dict:
        """
        Converts a MongoDB document into a formatted response.

        :param stage: dict - MongoDB document representing a client stage.
        :return: dict - Formatted dictionary containing client stage details.
        """
        return {
            "id": str(stage.get("_id", "")),
            "stage_name": stage.get("stage_name", ""),
            "stage_order": stage.get("stage_order", 0),
            "client_id": str(stage.get("client_id", "")),
            "sub_stages": [
                {
                    "sub_stage_id": str(sub.get("sub_stage_id", "")),
                    "sub_stage_order": sub.get("sub_stage_order", 0)
                }
                for sub in stage.get("sub_stages", [])
            ]
        }


    async def update_client_stages(self, stage_id: str, update_data: dict, current_user):
        """
               Updates an existing client stage.
               Params:
                   stage_id (str): The ObjectId of the client stage.
                   update_data (dict): Dictionary containing updated values.
                   current_user (dict): The currently authenticated user.
               Returns:
                   dict: A success message indicating the update status.
               Raises:
                   HTTPException: If the stage ID is invalid, stage does not exist, or update fails.
               """
        await UserHelper().is_valid_user(current_user)

        if not utility_obj.is_id_length_valid(stage_id, "stage_id"):
            raise CustomError(message=f"Invalid stage_id format: {stage_id}")

        stage_obj_id = ObjectId(stage_id)

        existing_stage = await DatabaseConfiguration().client_stages.find_one({"_id": stage_obj_id})
        if not existing_stage:
            raise DataNotFoundError(message="Client Stage")

        update_query = {}

        if "stage_order" in update_data and update_data["stage_order"] != existing_stage.get("stage_order"):
            new_stage_order = update_data["stage_order"]
            current_stage_order = existing_stage.get("stage_order")

            if new_stage_order != current_stage_order:
                existing_stage_with_order = await DatabaseConfiguration().client_stages.find_one(
                    {"stage_order": new_stage_order})
                if existing_stage_with_order:
                    await DatabaseConfiguration().client_stages.update_one(
                        {"_id": existing_stage_with_order["_id"]},
                        {"$set": {"stage_order": current_stage_order}}
                    )
                update_query["stage_order"] = new_stage_order
        if update_query:
            update_result = await DatabaseConfiguration().client_stages.update_one(
                {"_id": stage_obj_id},
                {"$set": update_query}
            )

            if update_result.modified_count == 0:
                raise CustomError(message="Update failed. No changes were made.")

        sub_stage_added = False

        if "stage_name" in update_data and update_data["stage_name"] != existing_stage.get("stage_name"):
            existing_stage_name = await DatabaseConfiguration().client_stages.find_one(
                {"stage_name": update_data["stage_name"]})
            if existing_stage_name:
                raise CustomError(message="Stage name already exists")
            update_query["stage_name"] = update_data["stage_name"]

        if "sub_stages" in update_data:
            existing_sub_stages = existing_stage.get("sub_stages", [])
            existing_orders = {sub["sub_stage_order"]: sub["sub_stage_id"] for sub in existing_sub_stages}
            existing_sub_stage_ids = {str(sub["sub_stage_id"]) for sub in existing_sub_stages}

            for sub in update_data["sub_stages"]:
                sub_stage_id_str = str(sub["sub_stage_id"])
                new_sub_stage_order = sub["sub_stage_order"]

                if not ObjectId.is_valid(sub_stage_id_str):
                    raise CustomError(message=f"Invalid sub_stage_id format: {sub_stage_id_str}")
                sub_stage_obj_id = ObjectId(sub_stage_id_str)


                sub_stage_exists = await DatabaseConfiguration().client_sub_stages.find_one({"_id": sub_stage_obj_id})
                if not sub_stage_exists:
                    raise DataNotFoundError(message=f"Sub-stage ID {sub_stage_id_str} in sub_stages collection")


                if new_sub_stage_order in existing_orders:
                    other_sub_stage_id = existing_orders[new_sub_stage_order]
                    found_elem = next((ind for ind, elem in enumerate(existing_sub_stages) if
                                       elem["sub_stage_id"] == ObjectId(other_sub_stage_id)), None)
                    p_found_elem, p_stage_order = next(
                        ((ind, elem.get("sub_stage_order")) for ind, elem in enumerate(existing_sub_stages) if
                         elem["sub_stage_id"] == ObjectId(sub_stage_obj_id)),
                        (None, None))
                    if p_stage_order is None:
                        p_stage_order = len(existing_orders) + 1

                    await DatabaseConfiguration().client_stages.update_one(
                        {"_id": stage_obj_id, f"sub_stages.{found_elem}.sub_stage_id": other_sub_stage_id},
                        {"$set": {f"sub_stages.{found_elem}.sub_stage_order": p_stage_order}}
                    )

                    if p_found_elem:
                        await DatabaseConfiguration().client_stages.update_one(
                            {"_id": stage_obj_id, f"sub_stages.{p_found_elem}.sub_stage_id": sub_stage_obj_id},
                            {"$set": {f"sub_stages.{p_found_elem}.sub_stage_order": new_sub_stage_order}}
                        )
                    else:
                        await DatabaseConfiguration().client_stages.update_one(
                            {"_id": stage_obj_id},
                            {"$push": {"sub_stages": {
                            "sub_stage_id": sub_stage_obj_id,
                            "sub_stage_order": new_sub_stage_order
                        }}}
                        )
                else:
                    await DatabaseConfiguration().client_stages.update_one(
                        {"_id": stage_obj_id},
                        {"$push": {"sub_stages": {
                        "sub_stage_id": sub_stage_obj_id,
                        "sub_stage_order": new_sub_stage_order
                    }}}
                    )
                    sub_stage_added = True

        if sub_stage_added:
            return {"message": "Sub-stage added successfully."}

        return {"message": "Client stage updated successfully"}

    async def delete_client_stage_by_id(self, client_id: str, stage_id: str, current_user):
        """
            Deletes a client stage using the client ID and stage ID.
            Params:
                client_id (str): The ObjectId of the client.
                stage_id (str): The ObjectId of the client stage.
                current_user (dict): The authenticated user performing the deletion.
            Raises:
                DataNotFoundError (404): If the client stage is not found.
            Returns:
                dict: A success message confirming the deletion.
            """
        await UserHelper().is_valid_user(current_user)
        if not ObjectId.is_valid(client_id):
            raise CustomError(message="Invalid client_id format")
        if not ObjectId.is_valid(stage_id):
            raise CustomError(message="Invalid stage_id format")
        client_exists = await DatabaseConfiguration().client_stages.find_one({"client_id": ObjectId(client_id)})
        if not client_exists:
            raise DataNotFoundError(message="Client ID")

        stage_exists = await DatabaseConfiguration().client_stages.find_one(
            {"_id": ObjectId(stage_id), "client_id": ObjectId(client_id)}
        )
        if not stage_exists:
            raise DataNotFoundError(message="Stage ID")
        result = await DatabaseConfiguration().client_stages.delete_one(
            {"_id": ObjectId(stage_id), "client_id": ObjectId(client_id)}
        )
        return {"message": "Client stage deleted successfully"}

    async def default_client_sub_stages(self, client_id: str, current_user):
        """
            This method retrieves all master sub-stages and assigns them to the specified client
            by inserting them into the `client_sub_stages` collection.
            Param:
                client_id (str): The ObjectId of the client as a string.
                current_user: The currently authenticated user.
            Raises:
                HTTPException (404): If no sub-stages are found.
                HTTPException (500): If an internal server error occurs.
            Returns:
                dict: A success message confirming that the default sub-stages were set.
            """
        await UserHelper().is_valid_user(current_user)

        try:
            client_object_id = ObjectId(client_id)
            pipeline = [
                {
                    "$project": {
                        "_id": 0,
                        "sub_stage_name": 1,
                        "fields": 1,
                        "stage_id": 1,
                        "client_id": client_object_id
                    }
                }
            ]

            result = await DatabaseConfiguration().sub_stages.aggregate(pipeline).to_list(None)

            if not result:
                raise DataNotFoundError(message="sub-stages")

            await DatabaseConfiguration().client_sub_stages.insert_many(result)

            return {"message": "Default client sub-stages set successfully"}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    async def create_sub_stage(self, client_id:str, sub_stage_data: dict, current_user) -> dict:
        """
            Creates a new client sub-stage in the database.
            Params:
                sub_stage_data (dict): Contains 'sub_stage_name', 'fields', and 'client_id' to create a sub-stage.
            Raises:
                HTTPException (400): If a sub-stage with the same name already exists for the client.
                HTTPException (500): If insertion fails.
            Returns:
                dict: Success message and inserted sub-stage ID.
        """
        await UserHelper().is_valid_user(current_user)
        client_obj_id = ObjectId(client_id)
        sub_stage_data["client_id"] = client_obj_id

        existing_sub_stage = await DatabaseConfiguration().client_sub_stages.find_one(
                {"sub_stage_name": {"$regex": f"^{sub_stage_data['sub_stage_name']}$", "$options": "i"},
                 "client_id": client_obj_id}
            )

        if existing_sub_stage:
            raise CustomError(message=f"Sub-stage '{sub_stage_data['sub_stage_name']}' already exists for this client.")
        for field in sub_stage_data.get("fields", []):
            field_name = field.get("name", "")
            if not re.fullmatch(r"^[a-z]+(_[a-z]+)*$", field_name):
                raise CustomError(message=f"Invalid format for field name '{field_name}'. Field name should be in snake_case (e.g., 'mother_name')."
                )
        sub_stage_data["created_at"] = datetime.utcnow()
        sub_stage_data["updated_at"] = datetime.utcnow()

        result = await DatabaseConfiguration().client_sub_stages.insert_one(sub_stage_data)

        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to insert client sub-stage.")

        return {"message": "Client sub-stage created successfully", "id": str(result.inserted_id)}


    async def get_all_sub_stages_for_client(self, current_user):
        """
        Retrieves all sub-stages for a specific client from the database.
        Params:
            current_user: The currently authenticated user.
        Raises:
            HTTPException (401): If the user is not valid.
        Returns:
            list[dict]: A list of sub-stage objects with formatted fields.
        """
        await UserHelper().is_valid_user(current_user)
        pipeline = [
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "client_id": {"$toString": "$client_id"},
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
        return await DatabaseConfiguration().client_sub_stages.aggregate(pipeline).to_list(None)

    async def get_client_sub_stage(self, sub_stage_id: str, current_user):
        """
           Retrieves a single client sub-stage by its ID.
           Params:
               sub_stage_id (str): The ObjectId of the sub-stage.
               current_user: The currently authenticated user.
           Raises:
               HTTPException (401): If the user is not valid.
           Returns:
               dict or None: A formatted sub-stage dictionary if found, otherwise None.
           """
        await UserHelper().is_valid_user(current_user)

        sub_stage = await DatabaseConfiguration().client_sub_stages.find_one({
            "_id": ObjectId(sub_stage_id)
        })

        return self.format_client_sub_stage(sub_stage) if sub_stage else None

    def format_client_sub_stage(self, sub_stage: dict) -> dict:
        """
        Converts a MongoDB document into a formatted response for a client sub-stage.
        Params:
            sub_stage: dict - MongoDB document representing a client sub-stage.
        Returns:
            dict - Formatted dictionary containing client sub-stage details.
        """
        return {
            "id": str(sub_stage.get("_id", "")),
            "client_id": str(sub_stage.get("client_id", "")),
            "sub_stage_name": sub_stage.get("sub_stage_name", ""),
            "fields": [
                {
                    "name": field.get("name", ""),
                    "label": field.get("label", ""),
                    "type": field.get("type", ""),
                    "is_required": field.get("is_required", False),
                    "description": field.get("description", ""),
                    "locked": field.get("locked", False),
                    "is_custom": field.get("is_custom", True),
                    "depends_on": field.get("depends_on")
                }
                for field in sub_stage.get("fields", [])
            ]
        }

    async def update_client_sub_stage(self, sub_stage_id: str, sub_stage_data: dict, current_user):
        """
        Updates an existing client sub-stage by its ID.
        Params:
            sub_stage_id (str): The ObjectId of the sub-stage.
            sub_stage_data (dict): The updated sub-stage data.
        Raises:
            HTTPException (400): If the ID format is invalid.
            HTTPException (404): If the sub-stage is not found.
            HTTPException (422): If duplicate fields are being inserted.
            HTTPException (500): If the update fails.
        Returns:
            dict: Success message.
        """
        await UserHelper().is_valid_user(current_user)

        if not ObjectId.is_valid(sub_stage_id):
            raise CustomError(message="Invalid sub_stage_id format")

        sub_stage = SubStageSchema(**sub_stage_data)

        existing_sub_stage = await DatabaseConfiguration().client_sub_stages.find_one({"_id": ObjectId(sub_stage_id)})
        if not existing_sub_stage:
            raise DataNotFoundError(message="Sub-stage")
        existing_fields_dict = {field["name"].strip().lower(): field for field in existing_sub_stage.get("fields", [])}

        updated_fields_dict = {}

        for field in sub_stage.fields:
            field_name = field.name.strip().lower()
            if not re.fullmatch(r"^[a-z]+(_[a-z]+)*$", field_name):
                raise CustomError(message=f"Invalid format for field name '{field_name}'. Field name should be in snake_case (e.g., 'mother_name')."
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
        result = await DatabaseConfiguration().client_sub_stages.update_one(
            {"_id": ObjectId(sub_stage_id)}, {"$set": update_data}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Update failed, please try again")

        return {"message": "Client sub-stage updated successfully"}

    async def delete_client_sub_stage_by_id(self, sub_stage_id: str, current_user):
        """
        Deletes a client sub-stage by ID.
        Params:
            sub_stage_id: str - The ObjectId of the client sub-stage.
            client_id: str - The ObjectId of the client.
            current_user: User - The currently authenticated user.
        Raises:
            HTTPException: If the sub-stage is not found.
        Returns:
            dict - Success message confirming deletion.
        """
        await UserHelper().is_valid_user(current_user)

        result = await DatabaseConfiguration().client_sub_stages.delete_one(
            {"_id": ObjectId(sub_stage_id)}
        )
        if result.deleted_count == 0:
            raise DataNotFoundError(message="Client sub-stage")

        return {"message": "Client sub-stage deleted successfully"}


    async def remove_fields_from_section(self, client_id: str, section_title: str, key_names: list[str], current_user):
        """
            Remove specific fields from a section in the client's application form.
            Params:
               client_id : str
                   The unique identifier of the client whose form is being modified.
               section_title : str
                   The title of the section from which fields should be removed.
               key_names : list[str]
                   A list of key names representing the fields that need to be removed.
            Raises:
               DataNotFoundError
                   If the client, section, or specified removable fields are not found.
               CustomError
                   If any of the fields are marked as non-removable or if the database update operation fails.
            Returns:
               dict
                   A dictionary containing a success message and the list of fields that were removed.
        """
        await UserHelper().is_valid_user(current_user)
        client_exists = await DatabaseConfiguration().stages.find_one({"client_id": ObjectId(client_id)})
        if not client_exists:
            raise DataNotFoundError(message="Client")

        application_forms = client_exists.get("application_form", [])
        section_found = False
        fields_to_remove = []
        non_removable_fields = []

        for form in application_forms:
            for section in form.get("sections", []):
                if section.get("section_title") == section_title:
                    section_found = True
                    existing_fields = {field["key_name"]: field for field in section.get("fields", [])}

                    for key_name in key_names:
                        if key_name in existing_fields:
                            field = existing_fields[key_name]
                            if field.get("can_remove", False):
                                fields_to_remove.append(key_name)
                            else:
                                non_removable_fields.append(key_name)
                    break
            if section_found:
                break

        if not section_found:
            raise DataNotFoundError(message="Section")

        if non_removable_fields:
            raise CustomError(
                message=f"The following fields cannot be removed: {', '.join(non_removable_fields)}"
            )

        if not fields_to_remove:
            raise DataNotFoundError(message="Specified fields in the section")
        result = await DatabaseConfiguration().stages.update_one(
            {
                "client_id": ObjectId(client_id),
                "application_form.sections.section_title": section_title,
            },
            {
                "$pull": {
                    "application_form.$[].sections.$[sec].fields": {
                        "key_name": {"$in": fields_to_remove}
                    }
                }
            },
            array_filters=[{"sec.section_title": section_title}]
        )
        if result.modified_count == 0:
            raise CustomError(message="Failed to remove fields")

        return {"message": "Fields removed successfully", "removed_fields": fields_to_remove}


    async def relocate_field_helper(self, request, client_id: str, college_id: str, current_user):
        """
        Moves a specified field from a source sub-stage to a destination sub-stage for a given client.
        Params:
            client_id (str): The ID of the client.
            college_id (str): The ID of the college.
            request: The request object containing source sub-stage name, destination sub-stage name, and the field name to move.
            current_user: The currently authenticated user.
        Raises:
            CustomError: If any provided ID is in an invalid format.
            DataNotFoundError: If the client, source sub-stage, or destination sub-stage is not found.
            HTTPException: If the specified field is not found in the source sub-stage (404).
            CustomError: If the specified field is locked and cannot be moved.
        Returns:
            dict: A message confirming successful field movement along with the field name.
        """

        await UserHelper().is_valid_user(current_user)
        client_exists = await DatabaseConfiguration().stages.find_one({"client_id": ObjectId(client_id)})
        if not client_exists:
            raise DataNotFoundError(message="Client")

        if college_id:
            college = await DatabaseConfiguration().stages.find_one({"college_id": ObjectId(college_id)})
            if not college:
                raise DataNotFoundError(message="College")

        if college_id and not client_id:
            raise CustomError(message="college_id requires client_id")

        query_filter = {"client_id": ObjectId(client_id)}
        if college_id:
            query_filter["college_id"] = ObjectId(college_id)

        schema_data = await DatabaseConfiguration().stages.find_one(query_filter)
        if not schema_data:
            raise DataNotFoundError(message="Schema not found")

        application_forms = schema_data.get("application_form", [])
        source_section = destination_section = None
        source_form_index = destination_form_index = None

        for idx, form in enumerate(application_forms):
            for section in form.get("sections", []):
                if section["section_title"] == request.source_section_name and not source_section:
                    source_section = section
                    source_form_index = idx
                if section["section_title"] == request.destination_section_name and not destination_section:
                    destination_section = section
                    destination_form_index = idx

        if source_section is None:
            raise DataNotFoundError(message="Source section")
        if destination_section is None:
            raise DataNotFoundError(message="Destination section")

        field_to_move = next(
            (field for field in source_section.get("fields", []) if field["key_name"] == request.key_name), None
        )
        if not field_to_move:
            raise DataNotFoundError(message=f"Field '{request.key_name}' not found in source section")
        if field_to_move.get("is_locked"):
            raise CustomError(message=f"Field '{request.key_name}' is locked")
        if field_to_move.get("dependent_fields") or field_to_move.get("logical_fields"):
            raise CustomError(message=f"Field '{request.key_name}' has dependencies")

        await DatabaseConfiguration().stages.update_one(
            query_filter,
            {
                "$pull": {
                    f"application_form.{source_form_index}.sections.$[section].fields": {"key_name": request.key_name}
                }
            },
            array_filters=[
                {"section.section_title": request.source_section_name}
            ]
        )
        await DatabaseConfiguration().stages.update_one(
            query_filter,
            {
                "$push": {
                    f"application_form.{destination_form_index}.sections.$[section].fields": field_to_move
                }
            },
            array_filters=[
                {"section.section_title": request.destination_section_name}
            ]
        )
        return {"message": "Field moved successfully", "field_name": request.key_name}


    async def get_all_fields(self, current_user, client_id=None, college_id=None, page_num=1, page_size=10,
                                    search=None):
        """
        Retrieves application form fields with optional search and pagination.
        Params:
            current_user (User): The currently authenticated user.
            client_id (str, optional): The client ID to filter the application fields.
            college_id (str, optional): The college ID to filter the application fields.
            page_num (int): The page number for pagination.
            page_size (int): The number of records per page.
            search (Optional[str]): A search keyword to filter fields by `key_name`. Default is None.
        Returns:
            Tuple[List[dict], int]: A tuple containing:
                - A list of paginated application form fields.
                - The total count of matching records.
        """
        await UserHelper().is_valid_user(current_user)
        utility_obj = Utility()
        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)

        if not client_id and not college_id:
            raise CustomError(message="Either client_id or college_id must be provided")
        try:
            filter_id = ObjectId(client_id or college_id)
        except Exception:
            raise CustomError(message="Invalid ID")

        id_field = "client_id" if client_id else "college_id"

        exists_filter = {id_field: filter_id}
        client_exists = await DatabaseConfiguration().college_form_details.find_one(exists_filter)
        if client_exists:
            filter_dashboard_type = (
                "client_student_dashboard" if id_field == "client_id" else "college_student_dashboard"
            )
        else:
            filter_dashboard_type = "student_dashboard"

        pipeline = [
            {"$match": {id_field: filter_id}},
            {"$sort": {"_id": -1}},
            {
                "$project": {
                    "field": {
                        "field_name": "$field_name",
                        "field_type": "$field_type",
                        "key_name": "$key_name",
                        "is_mandatory": "$is_mandatory",
                        "options": "$options",
                        "selectVerification": "$selectVerification",
                        "isReadonly": "$isReadonly",
                        "editable": "$editable",
                        "can_remove": "$can_remove",
                        "is_custom": "$is_custom",
                        "defaultValue": "$defaultValue",
                        "addOptionsFrom": "$addOptionsFrom",
                        "apiFunction": "$apiFunction",
                        "with_field_upload_file": "$with_field_upload_file",
                        "separate_upload_API": "$separate_upload_API",
                        "validations": "$validations",
                        "accepted_file_type": "$accepted_file_type",
                    }
                }
            },
            {
                "$unionWith": {
                    "coll": "application_form_details",
                    "pipeline": [
                        {
                            "$match": {
                                "$or": [
                                    {
                                        "dashboard_type": (
                                            "client_student_dashboard" if id_field == "client_id" else "college_student_dashboard"
                                        ),
                                        id_field: filter_id
                                    },
                                    {
                                        "dashboard_type": "student_dashboard"
                                    }
                                ]
                            }
                        },
                        {"$project": {"_id": 0, "application_form": 1}},
                        {"$unwind": "$application_form"},
                        {"$unwind": "$application_form.sections"},
                        {"$unwind": "$application_form.sections.fields"},
                        {"$project": {"field": "$application_form.sections.fields"}}
                    ]
                }
            },

            {
                "$unionWith": {
                    "coll": "application_form_details",
                    "pipeline": [
                        {
                            "$match": {
                                "$or": [
                                    {
                                        id_field: filter_id
                                    },
                                    {
                                        "dashboard_type": "student_dashboard"
                                    }
                                ]
                            }
                        },

                        {"$unwind": "$student_registration_form_fields"},
                        {"$project": {"_id": 0, "field": "$student_registration_form_fields"}}
                    ]
                }
            },
            {"$replaceRoot": {"newRoot": "$field"}}
        ]

        if search:
            pipeline.append(
                {
                    "$match": {
                        "$or": [
                            {"field_name": {"$regex": search, "$options": "i"}},
                            {"key_name": {"$regex": search, "$options": "i"}}
                        ]
                    }
                }
                )

        pipeline.append({
            "$facet": {
                "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                "totalCount": [{"$count": "count"}],
            }
        })

        result = await DatabaseConfiguration().custom_fields.aggregate(pipeline).to_list(length=None)
        result = result[0] if result else {}

        paginated_results = result.get("paginated_results", [])
        total_count = result.get("totalCount", [{}])[0].get("count", 0) if result.get("totalCount") else 0

        return paginated_results, total_count


    async def add_custom_field(
            self,
            client_id: str,
            field_data: CustomFieldSchema,
            college_id: str,
            existing_key_name: Optional[str] = None
    ):
        """
           Adds a new custom field or updates an existing custom field for a given client or college.

           Params:
               client_id (str): The ID of the client for whom the custom field is being added or updated.
               field_data (CustomFieldSchema): The schema containing data for the custom field to be added or updated.
               college_id (str): The ID of the college for whom the custom field is being added or updated.
               existing_key_name (Optional[str]): The key name of the existing field to be updated. If not provided, a new field will be added.
           Returns:
               dict: A dictionary containing:
                   - `message`: A message indicating the outcome of the operation (success or failure).
                   - `added_field` or `updated_field`: The custom field data that was successfully added or updated.
           Raises:
               CustomError:
                   - If neither `client_id` nor `college_id` is provided.
                   - If the `existing_key_name` is provided but no corresponding field exists for the client or college.
                   - If a field with the same `key_name` already exists for the client or college.
                   - If the `field_type` is "file" and neither `with_field_upload_file` nor `separate_upload_API` is provided, or if the field type is not "file" but these options are used.
               DataNotFoundError: If the field to be updated is not found for the specified client or college.
           """

        if not client_id and not college_id:
            raise CustomError(message="Either client_id or college_id must be provided.")

        client_obj_id = ObjectId(client_id) if client_id else None
        college_obj_id = ObjectId(college_id) if college_id else None
        if existing_key_name:
            query_filter = {"key_name": existing_key_name}
            if client_obj_id:
                query_filter["client_id"] = client_obj_id
            if college_obj_id:
                query_filter["college_id"] = college_obj_id

            existing_field = await DatabaseConfiguration().custom_fields.find_one(query_filter)
            if not existing_field:
                raise DataNotFoundError(message="custom field to update for this client/college")

            if field_data.key_name != existing_key_name:
                duplicate_check = {"key_name": field_data.key_name}
                if client_obj_id:
                    duplicate_check["client_id"] = client_obj_id
                if college_obj_id:
                    duplicate_check["college_id"] = college_obj_id

                duplicate_field = await DatabaseConfiguration().custom_fields.find_one(duplicate_check)
                if duplicate_field:
                    raise CustomError(message="Another field with this key_name already exists.")

            if field_data.field_type == "file":
                if not field_data.with_field_upload_file and not field_data.separate_upload_API:
                    raise CustomError(
                        message="For 'file' field_type, at least one of 'with_field_upload_file' or 'separate_upload_API' must be True."
                    )
            else:
                if field_data.with_field_upload_file or field_data.separate_upload_API:
                    raise CustomError(
                        message="'with_field_upload_file' and 'separate_upload_API' are only allowed when field_type is 'file'."
                    )

            field_dict = jsonable_encoder(field_data)
            field_dict = {k: v for k, v in field_dict.items() if v is not None}
            await DatabaseConfiguration().custom_fields.update_one(
                {"_id": existing_field["_id"]},
                {"$set": field_dict}
            )
            if "key_name" in field_dict:
                field_type = field_dict.get("field_type") if field_dict else existing_field.get("field_type")
                await DatabaseConfiguration().keyname_mapping.update_one({},
                                                                       {
                                                                           "$unset": {existing_field.get("key_name"): ""},
                                                                           "$set": {
                                                                           field_dict.get("key_name"): {
                                                                               "collection_name": "studentsPrimaryDetails"
                                                                               if field_type != "file" else "studentSecondaryDetails",
                                                                               "location": field_dict.get("key_name") if field_type != "file" else f"attachments.{field_dict.get('key_name')}",
                                                                           }
                                                                       }}
                                                                       )
            field_dict.update({
                "_id": str(existing_field["_id"]),
                "college_id": str(college_id) if college_id else None,
                "client_id": str(client_id) if client_id else None
            })
            return {
                "message": "Custom field updated successfully",
                "updated_field": field_dict
            }

        query_filter = {
            "key_name": field_data.key_name,
            "dashboard_type": "college_student_dashboard" if college_obj_id else "client_student_dashboard"
        }

        if client_obj_id:
            query_filter["client_id"] = client_obj_id
        if college_obj_id:
            query_filter["college_id"] = college_obj_id

        existing_field = await DatabaseConfiguration().custom_fields.find_one(query_filter)
        if existing_field:
            raise CustomError(message="Field with this key_name already exists.")

        pipeline = [
            {
                '$match': {
                    'dashboard_type': 'student_dashboard'
                }
            }, {
                '$unwind': '$application_form'
            }, {
                '$unwind': '$application_form.sections'
            }, {
                '$unwind': '$application_form.sections.fields'
            }, {
                '$project': {
                    'top_api': '$application_form.sections.fields.apiFunction',
                    'logical_fields': {
                        '$objectToArray': '$application_form.sections.fields.dependent_fields.logical_fields'
                    }
                }
            }, {
                '$unwind': {
                    'path': '$logical_fields',
                    'preserveNullAndEmptyArrays': True
                }
            }, {
                '$unwind': {
                    'path': '$logical_fields.v.fields',
                    'preserveNullAndEmptyArrays': True
                }
            }, {
                '$project': {
                    'apis': [
                        '$top_api', '$logical_fields.v.fields.key_name'
                    ]
                }
            }, {
                '$unwind': '$apis'
            }, {
                '$match': {
                    '$expr': {
                        '$eq': [
                            {
                                '$type': '$apis'
                            }, 'string'
                        ]
                    }
                }
            }, {
                '$group': {
                    '_id': None,
                    'key_names': {
                        '$addToSet': '$apis'
                    }
                }
            }, {
                '$project': {
                    '_id': 0,
                    'key_names': 1
                }
            }
        ]
        existing_fields_cursor = DatabaseConfiguration().custom_fields.aggregate(pipeline)
        existing_fields = [field["key_name"] for field in await existing_fields_cursor.to_list(length=None)]

        if field_data.key_name in existing_fields:
            raise CustomError(message="Field with this key_name already exists in application form.")

        if field_data.field_type == "file":
            if not field_data.with_field_upload_file and not field_data.separate_upload_API:
                raise CustomError(
                    message="For 'file' field_type, at least one of 'with_field_upload_file' or 'separate_upload_API' must be True."
                )
        else:
            if field_data.with_field_upload_file or field_data.separate_upload_API:
                raise CustomError(
                    message="'with_field_upload_file' and 'separate_upload_API' are only allowed when field_type is 'file'."
                )

        field_dict = jsonable_encoder(field_data)
        field_dict = {k: v for k, v in field_dict.items() if v is not None}
        if client_obj_id:
            field_dict["client_id"] = client_obj_id
            field_dict["dashboard_type"] = "client_student_dashboard"
        if college_obj_id:
            field_dict["college_id"] = college_obj_id
            field_dict["dashboard_type"] = "college_student_dashboard"
        inserted_field = await DatabaseConfiguration().custom_fields.insert_one(field_dict)
        field_type = field_dict.get("field_type")
        await DatabaseConfiguration().keyname_mapping.update_one({},
                                                                 {
                                                                     "$set": {
                                                                     field_dict.get("key_name"): {
                                                                         "collection_name": "studentsPrimaryDetails"
                                                                         if field_type != "file" else "studentSecondaryDetails",
                                                                         "location": field_dict.get(
                                                                             "key_name") if field_type != "file" else f"attachments.{field_dict.get('key_name')}",
                                                                     }
                                                                 }}
                                                                 )
        field_dict.update({
            "_id": str(inserted_field.inserted_id),
            "college_id": str(college_id) if college_id else None,
            "client_id": str(client_id) if client_id else None
        })
        return {
            "message": "Custom field added successfully",
            "added_field": field_dict
        }


    async def remove_fields(self, client_id: Optional[str] = None, college_id: Optional[str] = None,
                            key_name: str = None) -> dict:
        """
        Remove a specified field from the database based on the provided `key_name`.

        Params:
            client_id (Optional[str]): The ID of the client for whom the field is being removed. Either `client_id` or `college_id` must be provided.
            college_id (Optional[str]): The ID of the college for whom the field is being removed. Either `client_id` or `college_id` must be provided.
            key_name (str): The name of the field to be removed. This is the unique identifier of the field in the `custom_fields` collection.

        Returns:
            dict: A dictionary containing a `message` indicating the result of the operation and the `removed_field` that was processed.
        Raises:
            CustomError: If neither `client_id` nor `college_id` are provided, or if no `key_name` is specified.
            DataNotFoundError: If the `client_id` or `college_id` does not exist in the database.
        """

        if not client_id and not college_id:
            raise CustomError(message="Either client_id or college_id must be provided.")

        if not key_name:
            raise CustomError(message="No key name provided to remove.")

        if client_id:
            client = await DatabaseConfiguration().custom_fields.find_one({"client_id": ObjectId(client_id)})
            if not client:
                raise DataNotFoundError(message="Client")

        if college_id:
            college = await DatabaseConfiguration().custom_fields.find_one({"college_id": ObjectId(college_id)})
            if not college:
                raise DataNotFoundError(message="College")

        query_filter = {
            "key_name": key_name,
            "dashboard_type": "client_student_dashboard" if client_id else "college_student_dashboard"
        }
        if client_id:
            query_filter["client_id"] = ObjectId(client_id)
        else:
            query_filter["college_id"] = ObjectId(college_id)

        result = await DatabaseConfiguration().custom_fields.delete_many(query_filter)

        if result.deleted_count == 0:
            return {
                "message": "No fields found to remove",
            }

        return {
            "message": "Field removed successfully",
            "removed_field": key_name
        }

    async def validate_passing_years(self,
            tenth_passing_year: int,
            twelfth_passing_year: Optional[int],
            graduation_passing_year: Optional[int],
            post_graduation_passing_year: Optional[int],
            min_year: int,
            max_year: int,
            current_user
            ) -> dict:
        """
        Validates the academic passing year hierarchy based on logical academic progression
        and provided minimum and maximum year constraints.

        The validation follows these rules:
        - 10th passing year must be within the given min and max year range.
        - 12th passing year (if provided) must be at least 2 years after the 10th year
          and within the allowed range.
        - Graduation passing year (if provided) must be:
            - At least 2 years after 12th (if 12th is provided), or
            - At least 4 years after 10th (if 12th is not provided),
            and within the allowed range.
        - Post-graduation passing year (if provided) requires a valid graduation year,
          and must be at least 2 years after graduation and within the allowed range.
        Parameters:
            tenth_passing_year (int): The year the user passed 10th grade.
            twelfth_passing_year (Optional[int]): The year the user passed 12th grade.
            graduation_passing_year (Optional[int]): The year the user completed graduation.
            post_graduation_passing_year (Optional[int]): The year the user completed post-graduation.
            min_year (int): The minimum acceptable year for any academic milestone.
            max_year (int): The maximum acceptable year for any academic milestone.
        Returns:
            dict: A dictionary indicating if the provided years are valid:
        Raises:
            CustomError: If any academic year is not within the valid range or hierarchy.
            DataNotFoundError: If post-graduation year is provided without a graduation year.
        """
        await UserHelper().is_valid_user(current_user)
        if tenth_passing_year < min_year or tenth_passing_year > max_year:
            raise CustomError(message=f"10th passing year must be between {min_year} and {max_year}")

        if twelfth_passing_year:
            if twelfth_passing_year < tenth_passing_year + 2 or twelfth_passing_year > max_year:
                raise CustomError(message="12th passing year must be at least 2 years after 10th and within the allowed range")

        if graduation_passing_year:
            min_graduation_year = twelfth_passing_year + 2 if twelfth_passing_year else tenth_passing_year + 4
            if graduation_passing_year < min_graduation_year or graduation_passing_year > max_year:
                raise CustomError(
                    message="Graduation passing year must be at least 2 years after 12th or 4 years after 10th and within the allowed range"
                )
        if post_graduation_passing_year:
            if not graduation_passing_year:
                raise DataNotFoundError(
                    message="Post-graduation passing year requires a graduation passing year")
            if post_graduation_passing_year < graduation_passing_year + 2 or post_graduation_passing_year > max_year:
                raise CustomError(
                    message="Post-graduation passing year must be at least 2 years after graduation and within the allowed range"
                )

        return {"valid": True, "message": "Valid"}

