"""
This file contain class and functions related to master routes
"""
import ipaddress
import json
import uuid
from datetime import datetime, timezone
from itertools import islice

from bson import ObjectId
from fastapi import HTTPException

from app.core.custom_error import CustomError, DataNotFoundError
from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import CustomJSONEncoder, utility_obj
from app.database.configuration import DatabaseConfiguration, settings
from app.dependencies.hashing import Hash
from app.dependencies.oauth import cache_invalidation
from app.helpers.approval.approval_helper import ApprovalCRUDHelper, ApprovedRequestHandler

logger = get_logger(__name__)

ROLE_CREATION_RULES = {
    "super_admin": ["super_admin", "admin", "super_account_manager", "account_manager",
                    "client_manager", "college_super_admin"],
    "admin": ["super_account_manager", "account_manager", "client_manager", "college_super_admin"],
    "super_account_manager": ["account_manager", "client_manager", "college_super_admin"],
    "account_manager": ["client_manager", "college_super_admin"],
    "client_manager": ["college_super_admin"],
    "college_super_admin": []
}


class Master_Service:

    async def generate_uuid(self, length: int):
        """
        Create a random UUID of the given length

        Param:
            length (int): Length of the UUID

        Return:
            Return the UUID
        """
        return str(uuid.uuid4())[:length]

    async def insert_data(self,
                          reformatted_data: dict,
                          update: bool = False,
                          invalidation_route: str | None = None):
        """
        Insert the data into the master screen

        Param:
            reformatted_data (dict): Get the formatted data
            screen_type (str): Get the screen type
            invalidation_route (str): Route for cache invalidation

        Return:
            Return the success message
        """
        if update:
            await DatabaseConfiguration().master_screens.update_one(
                {"screen_type": reformatted_data.get("screen_type"),
                 "dashboard_type": reformatted_data.get("dashboard_type")},
                {"$set": reformatted_data})
            await cache_invalidation(api_updated=invalidation_route)
        else:
            await DatabaseConfiguration().master_screens.insert_one(reformatted_data)
        return {"message": "Master screen controller created successfully."}

    async def update_data_helper(
            self, payload: list,
            reformatted_data: dict
    ):
        """
        Update the data into the master screen

        Param:
            reformatted_data (dict): Get the formatted data
            screen_type (str): Get the screen type

        Return:
            Return the success message
        """
        for count_screen, screen in enumerate(payload):
            feature_id = await self.generate_uuid(8)
            temp_payload = []
            if count_screen == 0:
                reformatted_data["features"] = {}
            if screen.get("features", []):
                temp_payload = screen.pop("features", [])
            reformatted_data["features"][feature_id] = screen
            reformatted_data["features"][feature_id].update({"feature_id": feature_id})
            if temp_payload:
                await self.update_data_helper(
                    reformatted_data=reformatted_data["features"][feature_id],
                    payload=temp_payload
                )

    async def update_data(self, reformatted_data: dict, payload: list):
        """
        Update the data into the master screen

        Param:
            reformatted_data (dict): Get the formatted data
            screen_type (str): Get the screen type

        Return:
            Return the success message
        """
        for screen_detail in payload:
            feature_id = await self.generate_uuid(8)
            temp_payload = []
            if screen_detail.get("features", []):
                temp_payload = screen_detail.pop("features", [])
            reformatted_data[feature_id] = screen_detail
            reformatted_data[feature_id].update({"feature_id": feature_id})
            if temp_payload:
                await self.update_data_helper(
                    reformatted_data=reformatted_data[feature_id],
                    payload=temp_payload
                )

    async def create_master_controller(self, payload: list | None = None,
                                       screen_type: str | None = None,
                                       dashboard_type: str | None = None,
                                       invalidation_route: str | None = None):
        """
        Create the master screen controller data by the super admin

        Param:
            payload (list): Get the details of the master screen
            screen_type (str): Get the screen type
            dashboard_type (str): Get the dashboard type
            invalidation_route (str): Cache invalidation

        Return:
            Return success message

        Raises:
            CustomError: if any error occurs
        """
        update = True
        if (reformatted_data := await DatabaseConfiguration().master_screens.find_one(
                {"screen_type": screen_type, "dashboard_type": dashboard_type})) is None:
            update = False
            reformatted_data = {"created_at": datetime.utcnow(),
                                "dashboard_type": dashboard_type,
                                "screen_type": screen_type}

        await self.update_data(reformatted_data=reformatted_data, payload=payload)
        reformatted_data.update({"updated_at": datetime.utcnow()})
        return await self.insert_data(reformatted_data, update=update,
                                      invalidation_route=invalidation_route)

    async def update_dashboard_controller(
            self, payload: list,
            reformatted_data: dict
    ):
        """
        Update the dashboard controller data by the super admin

        Param:
            payload (list): Get the details of the dashboard
            reformatted_data (dict): Get the reformatted data

        Return:
            Return success message
        """
        for data in payload:
            temp_list = None
            if not data.get('feature_id'):
                await self.update_data(
                    reformatted_data=reformatted_data,
                    payload=[data]
                )
            if reformatted_data.get(data.get("feature_id")):
                feature_id = data.get('feature_id')
                if data.get("features", []):
                    temp_list = data.pop("features", [])
                if not reformatted_data.get(feature_id):
                    reformatted_data[feature_id] = {}
                reformatted_data[feature_id].update(data)
            else:
                raise DataNotFoundError(message=f"This key '{data.get('feature_id')}' is")
            if temp_list:
                if not reformatted_data[data.get("feature_id")].get("features"):
                    reformatted_data[data.get("feature_id")]["features"] = {}
                await self.update_dashboard_controller(
                    payload=temp_list,
                    reformatted_data=reformatted_data[data.get("feature_id")]["features"]
                )

    async def update_master_controller(
            self, payload: dict | None = None,
            screen_type: str | None = None,
            dashboard_type: str | None = None,
            invalidation_route: str | None = None
    ):
        """
        Update the master screen controller data by the super admin

        Param:
            payload (list): Get the details of the master screen
            screen_type (str): Get the screen type
            dashboard_type (str): Get the dashboard type

        Return:
            Return success message

        Raises:
            CustomError: if any error occurs
        """
        payload = payload.get("screen_details", [])
        if not payload:
            raise CustomError("Screen details must be required")
        if (reformatted_data := await DatabaseConfiguration().master_screens.find_one(
                {"screen_type": screen_type, "dashboard_type": dashboard_type})) is None:
            raise CustomError("Master screen controller not exists.")

        for temp_data in payload:
            if not temp_data.get("feature_id"):
                await self.update_data(reformatted_data=reformatted_data, payload=[temp_data])
            else:
                await self.update_dashboard_controller(
                    payload=[temp_data],
                    reformatted_data=reformatted_data
                )
        reformatted_data.update({"updated_at": datetime.utcnow()})
        await DatabaseConfiguration().master_screens.update_one(
            {"screen_type": screen_type, "dashboard_type": dashboard_type},
            {"$set": reformatted_data})
        await cache_invalidation(api_updated=invalidation_route)
        return {"message": "Master screen controller updated successfully."}

    async def recursive_check(
            self,
            data: dict,
            target_id: str,
            update_data: dict | None = None
    ) -> bool:
        """
        Recursively check if a feature_id exists in the nested dictionary.
        If found, update the data with the new value.

        Params:
            data (dict): The nested dictionary of features.
            target_id (str): The feature_id to check for.
            update_data (dict | None): The new data to set if the feature_id is found.

        Returns:
            bool: True if the feature_id was found and updated, False otherwise.
        """
        if not isinstance(data, dict):
            return False

        if target_id in data:
            if update_data:
                data[target_id].update(update_data)
            else:
                del data[target_id]
            return True

        for key, value in data.items():
            if isinstance(value, dict) and "features" in value:
                deleted = await self.recursive_check(value["features"], target_id, update_data)
                if deleted:
                    return True
        return False

    async def delete_helper(
            self,
            reformatted_data: dict,
            feature_id: str,
            update_filter: dict,
    ):
        """
        Recursively delete a feature from reformatted_data by feature_id.

        Parameters:
            reformatted_data (dict): The nested dictionary of features.
            feature_id (str): Dictionary with 'feature_id' key to delete.
            update_filter (dict): MongoDB-style update dict to record changes
        """
        target_id = feature_id
        if not target_id:
            raise CustomError(message="Feature id is required")

        # Recursive search and delete
        deleted = await self.recursive_check(reformatted_data, target_id)

        if deleted:
            update_filter.update({"$set": reformatted_data})
        else:
            raise DataNotFoundError(message=f"Feature ID '{target_id}'")

    async def delete_master_controller(
            self,
            screen_type: str | None = None,
            feature_id: str | None = None,
            whole_screen: bool = False,
            client_id: str | None = None,
            college_id: str | None = None,
            dashboard_type: str | None = None,
            invalidation_route: str | None = None
    ):
        """
        Delete the master screen controller data by the super admin

        Param:
            screen_type (str): Get the screen type
            payload (dict): Get the details of the master screen
            whole_screen (bool): Get the whole screen
            dashboard_type (str): Get the dashboard type

        Return:
            Return success message
        """
        if screen_type != "master_screen":
            if not client_id:
                if not college_id:
                    raise CustomError(message="College id is mandatory")
                if await DatabaseConfiguration().college_collection.find_one(
                        {"_id": ObjectId(college_id)}) is None:
                    raise DataNotFoundError(message="College")
        query_filter = {"screen_type": screen_type, "dashboard_type": dashboard_type}
        message = "Master screen controller not exists."
        response_query = "Master screen controller deleted successfully."
        if client_id:
            message = "Client screen controller not exists."
            response_query = "Client screen controller deleted successfully."
            query_filter.update({"client_id": ObjectId(client_id)})
        if college_id:
            if screen_type != "college_screen":
                raise CustomError(message="please set screen_type as college_screen")
            message = "College screen controller not exists."
            response_query = "College screen controller deleted successfully."
            query_filter.update({"college_id": ObjectId(college_id)})
        if (reformatted_data := await DatabaseConfiguration().master_screens.find_one(
                query_filter)) is None:
            raise CustomError(message)
        if not feature_id:
            if whole_screen:
                await DatabaseConfiguration().master_screens.delete_one(
                    query_filter)
            else:
                raise CustomError("If you want to delete the whole screen,"
                                  " please set whole_screen as True.")
        else:
            update_filter = {}
            if feature_id:
                if feature_id in list(reformatted_data.keys()):
                    update_filter.update({"$unset": {feature_id: ""}})
                else:
                    await self.delete_helper(
                        reformatted_data=reformatted_data,
                        feature_id=feature_id,
                        update_filter=update_filter
                    )
            else:
                raise CustomError(message="Feature id is required")
            await DatabaseConfiguration().master_screens.update_one(
                query_filter, update_filter)
        await cache_invalidation(api_updated=invalidation_route)
        return {"message": response_query}

    async def find_feature_by_id(self, data: dict, target_id: str) -> dict | None:
        """
        Recursively search for a feature_id in nested dicts and return the data if found.
        """
        for key, value in data.items():
            if key == target_id:
                return value
            if isinstance(value, dict) and "features" in value:
                if value.get("features"):
                    found = await self.find_feature_by_id(value["features"], target_id)
                    if found:
                        return found
        raise CustomError(message=f"Feature ID '{target_id}' not found.")

    async def temp_data_func(self, items):
        """
        Recursively processes feature data by extracting and transforming
         'features' from nested dictionaries.

        Args:
            items: Dictionary containing items with potential 'features' data

        Returns:
            List of processed items with transformed features
        """
        processed_items = []
        for key, item in items.items():
            # Extract features if they exist
            features = item.pop("features", None)
            if features:
                # Recursively process nested features
                item["features"] = await self.temp_data_func(features)
            processed_items.append(item)
        return processed_items

    async def process_data(self, data):
        """
        Processes input data to extract and transform
         feature information into a standardized format.

        Args:
            data: Input dictionary containing college data with potential feature information

        Returns:
            Dictionary containing processed data in standardized format with:
            - college_id
            - screen_type
            - dashboard_type
            - processed feature data
        """
        final_data = []

        # Process each item that contains feature data
        for key, value in data.items():
            if isinstance(value, dict) and "feature_id" in value:
                if value.get("features"):
                    value["features"] = await self.temp_data_func(value["features"])
                final_data.append(value)

        return {
            "college_id": str(data.get("college_id")),
            "screen_type": data.get("screen_type"),
            "dashboard_type": data.get("dashboard_type"),
            "data": final_data
        }

    async def add_pagination(self, reformatted_data: dict, page_num: int, page_size: int):
        """
        Add pagination to the reformatted data.

        Args:
            reformatted_data (dict): The data to be paginated.
            page_num (int): The current page number.
            page_size (int): The number of items per page.

        Returns:
            dict: The paginated data.
        """
        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
        features_dict = {
            k: v for k, v in reformatted_data.items()
            if isinstance(v, dict) and "feature_id" in v
        }
        total = len(features_dict)
        sliced_items = islice(features_dict.items(), skip, limit)
        return dict(sliced_items), total

    async def get_master_controller(
            self,
            screen_type: str | None = None,
            feature_id: str | None = None,
            client_id: str | None = None,
            college_id: str | None = None,
            dashboard_type: str | None = None,
            get_roles: bool = False,
            page_num: int | None = None,
            page_size: int | None = None
    ):
        """
        Get the master screen controller data by the super admin

        Param:
            screen_type (str): Get the screen type
            feature_id (str): Get the feature id
            client_id (str): Get the client id
            college_id (str): Get the college id
            dashboard_type (str): Get the dashboard type
            get_roles (bool): Get the roles
            page_num (int): Get the page number
            page_size (int): Get the page size

        Return:
            Return the success message
        """
        filter_data = {"screen_type": screen_type, "dashboard_type": dashboard_type}
        from app.helpers.client_automation.client_automation_helper import Client_screens
        error_message = "Master screen controller not exists."
        if client_id and not college_id:
            if screen_type != "client_screen":
                raise CustomError(message="please set screen_type as client_screen")
            filter_data.update({"client_id": ObjectId(client_id)})
            error_message = "Client screen controller not exists."
        if college_id:
            if screen_type != "college_screen":
                raise CustomError(message="please set screen_type as college_screen")
            filter_data.update({"college_id": ObjectId(college_id)})
            error_message = "College screen controller not exists."
        if (reformatted_data := await DatabaseConfiguration().master_screens.find_one(
                filter_data)) is None:
            raise CustomError(message=error_message)
        total = 0
        if feature_id is None:
            if get_roles:
                role_data = await Client_screens().collect_required_role_names(reformatted_data)
                reformatted_data.update({"roles_required": role_data})
            if page_num is not None and page_size is not None:
                data, total = await self.add_pagination(reformatted_data,
                                                        page_num=page_num, page_size=page_size)
                reformatted_data = {
                    "college_id": str(reformatted_data.get("college_id")),
                    "screen_type": reformatted_data.get("screen_type"),
                    "dashboard_type": reformatted_data.get("dashboard_type"),
                    "_id": str(reformatted_data.get("_id")),
                    **data
                }
            data = json.dumps(reformatted_data, cls=CustomJSONEncoder)
            data = json.loads(data)
        else:
            try:
                total = 1
                data = await self.find_feature_by_id(
                    data=reformatted_data, target_id=feature_id)
            except KeyError as error:
                raise DataNotFoundError(message=f"This key '{error.args[0]}' is")
        data = await self.process_data(data)
        if page_num is not None and page_size is not None:
            response = await utility_obj.pagination_in_aggregation(
                page_num=page_num, page_size=page_size, data_length=total,
                route_name="client_automation/add_feature_screen")
            return {
                "data": data,
                "page_num": page_num,
                "page_size": page_size,
                "total": total,
                "pagination": response.get("pagination"),
            }
        else:
            return data

    async def get_stages_data(self, college_id: str | None | ObjectId,
                              client_id: str | None | ObjectId) -> dict:
        """
            Retrieves all stages and sub-stages for the student dashboard.

            This method fetches the complete stage structure associated with either a client or a college.
            It is typically used to populate the student dashboard with relevant progress stages.

            Args:
                college_id (str | None | ObjectId): The unique identifier of the college (optional).
                client_id (str | None | ObjectId): The unique identifier of the client (optional).

            Returns:
                dict: A dictionary containing all the stage and sub-stage data.

            Raises:
                ValueError: If both `college_id` and `client_id` are None.
                Exception: For unexpected errors during data retrieval.
        """
        client_id = ObjectId(client_id) if ObjectId.is_valid(client_id) else client_id
        college_id = ObjectId(college_id) if ObjectId.is_valid(college_id) else college_id
        query_options, form_data = [], None
        if college_id is not None:
            query_options.append({"college_id": college_id,
                                  "application_form": {"$exists": True}
                                  })
        if client_id is not None:
            query_options.append({"client_id": client_id,
                                  "application_form": {"$exists": True}
                                  })
        query_options.append({"dashboard_type": "student_dashboard"})
        for query in query_options:
            form_data = await DatabaseConfiguration().college_form_details.find_one(query)
            if form_data:
                break
        if form_data:
            return json.loads(json.dumps(form_data, cls=CustomJSONEncoder))
        else:
            raise CustomError(message="No Form Data Found!")

    async def build_lookup(self, schema: dict, add_id: bool=False) -> tuple:
        """
            Built lookup and fetch the required data.

            Args:
                schema (dict): A dictionary representing the schema, where each key is
                               a field name and its value is a dictionary of field properties.
                               Fields that require a `$lookup` must include a 'ref' key
                               indicating the target collection for the lookup.
                add_id (bool): If True then add step id which is unique

            Returns:
                tuple: A tuple containing:
                    - steps: All steps dicts
                    - sections: All Sections dicts
                    - fields: All Fields dicts
        """
        steps = {}
        sections = {}
        fields = {}

        for step in schema.get("application_form", []):
            if add_id:
                step["step_id"] = await self.generate_uuid(8)
            step_name = step["step_name"]
            steps[step_name] = step
            if step.get("sections"):
                for section in step.get("sections", []):
                    if add_id:
                        section["section_id"] = await self.generate_uuid(8)
                    sec_key = (step_name, section["section_title"])
                    sections[sec_key] = section
                    for field in section.get("fields", []):
                        fld_key = (step_name, section["section_title"], field["key_name"])
                        fields[fld_key] = field
        return steps, sections, fields

    def divide_stages_equally(self, stages: list[str]) -> dict[str, float]:
        """
        This function divides the given stages equally giving stage value that fall between 1 to 10
        Params:
            stages (list): All the stages in form
        Returns:
            dict: The details of stages and stage values
        """
        n = len(stages)
        if n == 0:
            return {}
        if n == 1:
            return {stages[0]: 10.0}
        step = 10 / n
        result = {
            stage: round((i + 1) * step, 2) for i, stage in enumerate(stages)
        }
        return result

    async def validate_external_schema_changes(self, standard: dict, incoming: dict) -> bool:
        """
            Validates that changes between a standard schema and an incoming schema
            comply with external schema constraints.

            This method enforces rules such as:
                - Fields or sections marked with `is_locked=True` in the standard schema
                  cannot be modified, moved, or deleted.
                - New fields or sections can only be added if `is_custom=True`.
                - Existing fields or sections with `is_custom=False` must remain unchanged
                  in structure and position.
                - Ensures integrity of step names, section titles, field key names, etc.


            Params:
                standard (dict): The original schema representing the approved or baseline structure.
                incoming (dict): The new schema that needs to be validated against the standard.

            Returns:
                bool: True if the incoming schema adheres to the external change rules,
                      False otherwise.
        """
        errors = []
        std_steps, std_sections, std_fields = await self.build_lookup(standard)
        new_steps, new_sections, new_fields = await self.build_lookup(incoming, add_id=True)

        std_field_map = {f["key_name"]: (s, sec, f) for (s, sec, k), f in std_fields.items()}
        new_field_map = {f["key_name"]: (s, sec, f) for (s, sec, k), f in new_fields.items()}

        all_field_keys = set(std_field_map.keys()).union(new_field_map.keys())

        for key in all_field_keys:
            std_info = std_field_map.get(key)
            new_info = new_field_map.get(key)

            if std_info and not new_info:
                if not std_info[2].get("is_custom", False):
                    errors.append(f"Field '{key}' cannot be removed as it is not Custom field!")
            elif not std_info and new_info:
                if not new_info[2].get("is_custom", False):
                    errors.append(f"Field '{key}' added but is_custom field is not mentioned!")
            elif std_info and new_info:
                old_step, old_sec, std_field = std_info
                new_step, new_sec, _ = new_info
                if (old_step != new_step or old_sec != new_sec) and std_field.get("is_locked",
                                                                                  False):
                    errors.append(
                        f"Field '{key}' is locked and cannot be moved from '{old_sec}' to '{new_sec}'."
                    )

        std_section_map = {title: (step, sec) for (step, title), sec in std_sections.items()}
        new_section_map = {title: (step, sec) for (step, title), sec in new_sections.items()}
        all_section_titles = set(std_section_map.keys()).union(new_section_map.keys())

        for title in all_section_titles:
            std_info = std_section_map.get(title)
            new_info = new_section_map.get(title)

            if std_info and not new_info:
                if not std_info[1].get("is_custom", False):
                    errors.append(
                        f"Section '{title}' cannot be removed as it is not Custom Section!")
            elif not std_info and new_info:
                if not new_info[1].get("is_custom", False):
                    errors.append(f"Section '{title}' added but is_custom field is not mentioned!")
            elif std_info and new_info:
                old_step = std_info[0]
                new_step = new_info[0]
                if old_step != new_step and std_info[1].get("is_locked", False):
                    errors.append(
                        f"Section '{title}' is locked and cannot be moved from '{old_step}' to '{new_step}'."
                    )
        if errors:
            raise CustomError(" | ".join(errors))
        return True

    async def append_if_file_and_separate(self, field_obj: dict, target_list: list) -> None:
        """
        Appends the given field object to the target list if it is a file field
        and marked to be stored separately.

        Params:
            field_obj (dict): The field object to evaluate.
            target_list (list): The list to append the field object to if conditions are met.

        Returns:
            None
        """
        if field_obj.get("field_type") == "file" and field_obj.get("separate_upload_API", False):
            target_list.append(field_obj)

    async def process_logic_values(self, logic_values: dict, target_list: list) -> None:
        """
        Recursively processes logical dependent fields to extract file-type fields
        that are marked to be stored separately, and appends them to the target list.

        This function handles:
        - Direct fields inside logical values
        - Nested dependent logical fields within those fields
        - File fields inside tables (both "Row" and "fields" keys)

        Params:
            logic_values (dict): A dictionary containing logical condition mappings with their respective fields.
            target_list (list): The list to append qualifying file field objects to.

        Returns:
            None
        """
        for logic_value in logic_values.values():
            if not logic_value:
                continue

            # Check direct fields
            for logic_field in logic_value.get("fields", []):
                await self.append_if_file_and_separate(logic_field, target_list)

                # Recurse if field has nested logic
                nested_logic = logic_field.get("dependent_fields", {}).get("logical_fields", {})
                if nested_logic:
                    await self.process_logic_values(nested_logic, target_list)

            # Check table values
            table = logic_value.get("table", {})
            row = table.get("Row", {}).get("fields", [])
            for row_field in row:
                await self.append_if_file_and_separate(row_field, target_list)
            for table_field in table.get("fields") or []:
                await self.append_if_file_and_separate(table_field, target_list)

    async def update_registration_data(self, college_id: str | None, client_id: str | None,
                                       registration_form: dict) -> dict:
        """
        Update the registration form data in the database.

        Args:
            college_id (str | None): The college ID.
            client_id (str | None): The client ID.
            registration_form (dict): The registration form data.

        Returns:
            message: A message indicating the success or failure of the operation.
        """
        registration_form = registration_form.get("student_registration_form_fields")
        client_id = ObjectId(client_id) if ObjectId.is_valid(client_id) else client_id
        college_id = ObjectId(college_id) if ObjectId.is_valid(college_id) else college_id
        key_names = [field["key_name"] for field in registration_form if field.get("key_name")]
        if len(key_names) != len(set(key_names)):
            raise CustomError("Duplicate field found in the form.")
        key_names = set(key_names)
        if "full_name" not in key_names:
            raise CustomError("Missing required field: full_name")
        if not {"email", "mobile_no"} & key_names:
            raise CustomError("Either 'email' or 'mobile_no' must be present.")

        data = {"updated_at": datetime.utcnow()}
        if registration_form:
            data.update({"student_registration_form_fields": registration_form})
        if client_id and not college_id:
            data.update({"dashboard_type": "client_student_dashboard"})
            await DatabaseConfiguration().college_form_details.update_one(
                {"client_id": client_id},
                {"$set": data},
                upsert=True
            )
        else:
            data.update({"dashboard_type": "college_student_dashboard"})
            await DatabaseConfiguration().college_form_details.update_one(
                {"client_id": client_id, "college_id": college_id},
                {"$set": data},
                upsert=True
            )
        await ApprovedRequestHandler().update_onboarding_details(
            college_id=college_id, client_id=client_id, step_name="registration_form", status="Approved",
            user={},
            request_of="college_student_registration_form" if college_id else "client_student_registration_form"
        )
        await cache_invalidation(api_updated="form_details_update")
        return {"message": "Student Signup Form Updated Successfully!"}

    async def update_client_or_college_form_data(self, college_id: str | None,
                                                 client_id: str | None,
                                                 application_form: dict, request: str, user: dict, approval_id: str = None):
        """
            Updates the application form data for a client or a college.

            This method handles updating the form data associated with either a client or a college,
            depending on which ID is provided. It expects a dictionary containing the updated form
            fields and values.


            Params:
                college_id (str | None): The unique identifier of the college. Can be None if updating for a client.
                client_id (str | None): The unique identifier of the client. Can be None if updating for a college.
                application_form (dict): A dictionary containing the updated form data.
                request (str): This would be either 'validate' or 'update
                user (dict): The details of user who hit this API

            Returns:
                dict: A response indicating the status of the update operation, including success or failure details.

            Raises:
                ValueError: If both `college_id` and `client_id` are None.
                Exception: For other unexpected errors during update.
        """
        client_id = ObjectId(client_id) if ObjectId.is_valid(client_id) else client_id
        college_id = ObjectId(college_id) if ObjectId.is_valid(college_id) else college_id
        standard = await self.get_stages_data(college_id=college_id, client_id=client_id)
        validated = await self.validate_external_schema_changes(standard, application_form)
        if validated:
            if user and user.get("role", {}).get("role_name") in [
                "admin",
                "super_admin",
            ]:
                request = "update"
            if request == "validate":
                approval_request = await ApprovalCRUDHelper().create_approval_request(user, {
                    "payload": application_form,
                    "approval_type": "college_student_application_form" if college_id else "client_student_application_form",
                    **({"client_id": ObjectId(client_id)} if client_id is not None else {}),
                    **({"college_id": ObjectId(college_id)} if college_id is not None else {}),
                }, approval_id=approval_id)
                await ApprovedRequestHandler().update_onboarding_details(
                    college_id=college_id, client_id=client_id, step_name="application_form", status="In Progress",
                    user=user, approval_request=approval_request,
                    request_of="college_student_application_form" if college_id else "client_student_application_form",
                )
                return {"message": "Validation successful and sent the request!", "approval_id": approval_request.get("approval_id")}
            else:
                data = {"updated_at": datetime.utcnow()}
                all_stages = []
                if application_form:
                    external_uploads = []
                    application_data = application_form.get("application_form")
                    for stage in application_data:
                        all_stages.append(stage.get("step_name"))
                        if not stage.get("no_sections", False):
                            for sub_stage in stage.get("sections", []):
                                for field in sub_stage.get("fields", []):
                                    await self.append_if_file_and_separate(field, external_uploads)
                                    dependent_fields = field.get("dependent_fields", {})
                                    if dependent_fields:
                                        logical_fields = dependent_fields.get(
                                        "logical_fields", {})
                                        if logical_fields:
                                            await self.process_logic_values(logical_fields,
                                                                        external_uploads)
                    if category := application_form.get("category", None) is not None:
                        data.update({"category": category})
                    if application_form.get("course_name", None) is not None:
                        try:
                            Reset_the_settings().get_user_database(ObjectId(college_id))
                        except Exception as e:
                            raise CustomError(message="Unable to Establish Connection with Season Db: " + str(e))
                        course_name = application_form.get("course_name", None)
                        if (course := await DatabaseConfiguration().course_collection.find_one({"course_name": course_name, "college_id": college_id})) is None:
                            raise CustomError(message=f"Course {course_name} is not approved! "
                                                      f"Hence cannot update details!")
                        data.update({"course_id": course.get("_id")})
                    data.update({"application_form": application_data,
                                 "additional_upload_fields": external_uploads})

                if client_id:
                    data.update({"dashboard_type": "client_student_dashboard"})
                    await DatabaseConfiguration().college_form_details.update_one(
                        {"client_id": client_id},
                        {"$set": data},
                        upsert=True
                    )
                else:
                    data.update({"dashboard_type": "college_student_dashboard"})
                    await DatabaseConfiguration().college_form_details.update_one(
                        {"client_id": client_id, "college_id": college_id},
                        {"$set": data},
                        upsert=True
                    )
                if application_form:
                    stage_values = self.divide_stages_equally(all_stages)
                    await DatabaseConfiguration().college_collection.update_one({"_id": ObjectId(college_id)},
                                                                                {"$set": {
                                                                                    "stage_values": stage_values
                                                                                }}
                                                                                )
                await ApprovedRequestHandler().update_onboarding_details(
                    college_id=college_id, client_id=client_id, step_name="application_form", status="Approved",
                    user=user,
                    request_of="college_student_application_form" if college_id else "client_student_application_form",
                )
                await cache_invalidation(api_updated="form_details_update")
                return {"message": "Updated Successfully!"}
        return {"message": "Something went Wrong"}

    async def get_master_screen_data(self,
                                     page_num: int,
                                     page_size: int,
                                     screen_type: str | None = None,
                                     client_id: str | None = None,
                                     college_id: str | None = None,
                                     dashboard_type: str | None = None
                                     ):
        """
        Get the master screen data

        Param:
            screen_type (str): Get the screen type
            client_id (str): Get the client id
            college_id (str): Get the college id
            page_num (int): Get the page number
            page_size (int): Get the page size
            dashboard_type (str): Get the dashboard type

        Return:
            Return the success message
        """
        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
        filter_data = {"screen_type": screen_type, "dashboard_type": dashboard_type}
        if college_id:
            filter_data.update({"college_id": ObjectId(college_id)})
            error_message = "College screen controller not exists."
        elif client_id:
            filter_data.update({"client_id": ObjectId(client_id)})
            error_message = "Client screen controller not exists."
        else:
            error_message = "Master screen controller not exists."
            filter_data.update({"screen_type": "master_screen"})
        if not await DatabaseConfiguration().master_screens.find_one(filter_data):
            if college_id:
                if (client_data := await DatabaseConfiguration().client_collection.find_one(
                        {"college_ids": {"$in": [ObjectId(college_id)]}})):
                    filter_data = {"client_id": ObjectId(client_data.get("client_id")),
                                   "screen_type": "client_screen", "dashboard_type": dashboard_type}
                    if await DatabaseConfiguration().master_screens.find_one(filter_data):
                        pass
                    else:
                        filter_data = {"screen_type": "master_screen",
                                       "dashboard_type": dashboard_type}
            if not await DatabaseConfiguration().master_screens.find_one(filter_data):
                raise CustomError(message=error_message)
        data = await DatabaseConfiguration().master_screens.aggregate(
            [
                {
                    "$match": filter_data
                },
                {
                    "$addFields": {
                        "all_data": {"$objectToArray": "$$ROOT"}
                    }
                },
                {
                    "$facet": {
                        "modules": [
                            {"$unwind": "$all_data"},
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": [{"$type": "$all_data.v"}, "object"]
                                    }
                                }
                            },
                            {
                                "$skip": skip
                            },
                            {
                                "$limit": limit
                            },
                            {
                                "$project": {
                                    "_id": 0,
                                    "id": "$all_data.k",
                                    "module_name": "$all_data.v.name",
                                    "description": "$all_data.v.description",
                                    "amount": "$all_data.v.amount",
                                    "features": {
                                        "$cond": {
                                            "if": {"$ifNull": ["$all_data.v.features", False]},
                                            "then": {
                                                "$map": {
                                                    "input": {
                                                        "$objectToArray": "$all_data.v.features"},
                                                    "as": "feature",
                                                    "in": {
                                                        "id": "$$feature.k",
                                                        "module_name": "$$feature.v.name",
                                                        "description": "$$feature.v.description",
                                                        "amount": "$$feature.v.amount"
                                                    }
                                                }
                                            },
                                            "else": []
                                        }
                                    }
                                }
                            }
                        ],
                        "totalCount": [
                            {"$unwind": "$all_data"},
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": [{"$type": "$all_data.v"}, "object"]
                                    }
                                }
                            },
                            {"$count": "count"}
                        ],
                        "meta": [
                            {
                                "$project": {
                                    "_id": {"$toString": "$_id"},
                                    "college_id": {"$toString": "$college_id"},
                                    "client_id": {"$toString": "$client_id"},
                                    "screen_type": "$screen_type",
                                }
                            }
                        ]
                    }
                },
                {
                    "$project": {
                        "data": "$modules",
                        "totalCount": {"$arrayElemAt": ["$totalCount.count", 0]},
                        "_id": {"$arrayElemAt": ["$meta._id", 0]},
                        "college_id": {"$arrayElemAt": ["$meta.college_id", 0]},
                        "client_id": {"$arrayElemAt": ["$meta.client_id", 0]},
                        "screen_type": {"$arrayElemAt": ["$meta.screen_type", 0]}
                    }
                }
            ]
        ).to_list(None)
        data = json.dumps(data, cls=CustomJSONEncoder)
        data = json.loads(data)
        if len(data) == 0:
            total_count = 0
            data = {}
        else:
            data = data[0]
            total_count = data.get("totalCount")

        response = await utility_obj.pagination_in_aggregation(
            page_num,
            page_size,
            total_count,
            "/client_automation/get_screen_details/",
        )
        return {
            "data": data,
            "total": total_count,
            "count": len(data.get("data", [])),
            "pagination": response.get("pagination"),
            "message": "Get Screen details."
        }

    async def get_api_functions(self, client_id: str | None, college_id: str | None) -> dict:
        """
            Extracts all unique `apiFunction` values used within the application form fields,
            including those nested inside dependent fields, for a given client and college.

            Args:
                client_id (str | None): The client identifier to filter the application form (if applicable).
                college_id (str | None): The college identifier to filter the application form (if applicable).

            Returns:
                dict: A dictionary containing a list of unique API function names used in the form.
                      Format: { "apiFunctions": ["fetchCountry", "fetchState", ...] }
        """
        match = {}
        if client_id and ObjectId.is_valid(client_id):
            match.update({"client_id": ObjectId(client_id)})
        if college_id and ObjectId.is_valid(college_id):
            match.update({"college_id": ObjectId(college_id)})
        if not match:
            match.update({'dashboard_type': "student_dashboard"})
        pipeline = [
            {
                '$match': match
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
                        '$top_api', '$logical_fields.v.fields.apiFunction'
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
                    'apiFunctions': {
                        '$addToSet': '$apis'
                    }
                }
            }, {
                '$project': {
                    '_id': 0,
                    'apiFunctions': 1
                }
            }
        ]
        result = await DatabaseConfiguration().college_form_details.aggregate(pipeline).to_list(
            None)
        if not result:
            pipeline[0] = {"$match": {'dashboard_type': "student_dashboard"}}
            result = await DatabaseConfiguration().college_form_details.aggregate(pipeline).to_list(
                None)
        result = result[0] if result else {}
        return result

    async def get_fields_by_role(self, role_id: int | None = None) -> dict:
        """
        Retrieve user registration fields based on the provided role ID.

        - Always returns common user registration fields.
        - If `role_id` is provided, role-specific fields are also included.
        - Validates if the role exists before including its fields.

        Params:
            role_id (int | None): Optional role ID to fetch role-specific fields.

        Returns:
            dict: A success response containing a list of all required fields.

        Raises:
            HTTPException: If common fields are not configured or role is not found.
        """
        field_mapping = await DatabaseConfiguration().field_mapping_collection.find_one()
        all_fields = field_mapping.get("user_registration_common_fields", [])
        if not field_mapping or not all_fields:
            raise HTTPException(status_code=500, detail="Common fields not configured.")

        if role_id is not None:
            role = await DatabaseConfiguration().role_collection.find_one({"pgsql_id": role_id})
            if not role:
                raise HTTPException(status_code=404, detail="Role not found.")

            role_fields = role.get("role_specific_fields", [])
            all_fields += role_fields

        return {"message": "Fields fetched successfully.", "data": all_fields}

    async def validate_field_type(self, key: str, value, expected_type: str):
        """
        Validates the type of a given field value against the expected field type.

        Params:
            key (str): The name of the field being validated.
            value: The value of the field to validate.
            expected_type (str): The expected data type for the field.
                                 Supported types: "text", "number", "boolean", "email", "list", "object_id".

        Raises:
            HTTPException: If the value does not match the expected type or format.
        """
        if expected_type == "text":
            if not isinstance(value, str):
                raise HTTPException(status_code=400, detail=f"Field '{key}' must be a string.")
        elif expected_type == "number":
            if not isinstance(value, int):
                raise HTTPException(status_code=400, detail=f"Field '{key}' must be an integer.")
        elif expected_type == "boolean":
            if not isinstance(value, bool):
                raise HTTPException(status_code=400, detail=f"Field '{key}' must be a boolean.")
        elif expected_type == "email":
            if not isinstance(value, str) or "@" not in value:
                raise HTTPException(status_code=400, detail=f"Field '{key}' must be a valid email.")
        elif expected_type == "list":
            if not isinstance(value, list):
                raise HTTPException(status_code=400, detail=f"Field '{key}' must be a list.")
        elif expected_type == "object_id":
            try:
                ObjectId(value)
            except:
                raise HTTPException(status_code=400,
                                    detail=f"Field '{key}' must be a valid ObjectId.")

    async def _validate_object_ids(self, ids: list[str], collection, filter_extra=None,
                                   not_found_msg: str = "Some IDs were not found in the database."):
        """
        Validates a list of ObjectIds by checking their existence in a specified MongoDB collection.

        Params:
            ids (list[str]): A list of ObjectId strings to validate.
            collection: The MongoDB collection to query for the ObjectIds.
            filter_extra (dict, optional): Additional filter criteria to apply to the query. Defaults to None.
            not_found_msg (str, optional): Custom message to include if some IDs are not found. Defaults to
                                           "Some IDs were not found in the database."

        Raises:
            HTTPException: If one or more of the provided IDs are invalid or if any IDs are not found in the database.

        Returns:
            None: If all provided IDs are valid and exist in the database.
        """
        try:
            object_ids = [ObjectId(_id) for _id in ids]
        except Exception:
            raise HTTPException(status_code=404,
                                detail="One or more provided IDs are invalid ObjectId format.")

        filter_query = {"_id": {"$in": object_ids}}
        if filter_extra:
            filter_query.update(filter_extra)

        valid_items = await collection.find(filter_query).to_list(length=None)
        found_ids = {str(doc["_id"]) for doc in valid_items}
        missing_ids = [str(_id) for _id in object_ids if str(_id) not in found_ids]
        if missing_ids:
            raise HTTPException(status_code=404,
                                detail={"message": not_found_msg, "missing_ids": missing_ids})

    async def validate_role_specific_fields(self, role_name: str, user_data: dict):
        """
        Validates role-specific fields in the provided user data based on the role.

        This method checks that required fields for different roles are present and valid. For each role,
        it validates object IDs and ensures that fields such as `super_account_manager_id`, `assigned_client_ids`,
        `assigned_account_managers`, and `associated_colleges` are in the correct format and exist in the
        database collections. Additionally, for the "super_admin" role, it validates the IP addresses in
        the `allowed_ips` field.

        Params:
            role_name (str): The role of the user (e.g., "account_manager", "super_account_manager",
                              "client_manager", "super_admin").
            user_data (dict): The user data containing fields specific to the role being validated.

        Raises:
            HTTPException:
                - If required fields are missing or invalid (e.g., `super_account_manager_id`).
                - If provided object IDs are not found or are in an invalid format.
                - If any IP addresses in `allowed_ips` are invalid.

        Returns:
            None: If all role-specific fields are valid and no exceptions are raised.
        """

        async def validate_ids(ids, collection, filter_extra=None, err_msg="Some IDs are invalid.",
                               name="ID") -> list:
            """
            Validates a list of IDs, checks their length, and ensures they exist in the specified database collection.
            """
            ids = list(set(ids))
            if not isinstance(ids, list):
                raise HTTPException(status_code=400, detail=f"{name} must be a list.")
            for _id in ids:
                await utility_obj.is_length_valid(_id=_id, name=name)
            await self._validate_object_ids(ids, collection, filter_extra, err_msg)
            return [ObjectId(_id) for _id in ids]

        db = DatabaseConfiguration()

        if role_name == "account_manager":
            super_id = user_data.get("super_account_manager_id")
            if not super_id:
                raise HTTPException(status_code=400, detail="super_account_manager_id is required.")
            await utility_obj.is_length_valid(_id=super_id, name="Super Account Manager ID")
            await self._validate_object_ids([super_id], db.user_collection,
                                            {"user_type": "super_account_manager"},
                                            "Invalid super_account_manager_id provided.")
            user_data["super_account_manager_id"] = ObjectId(super_id)

            client_ids = user_data.get("assigned_client_ids", [])
            user_data["assigned_client_ids"] = (
                await validate_ids(client_ids, db.client_collection, name="Assigned Client ID",
                                   err_msg="Some provided IDs for 'assigned_client_ids' are invalid or not found.")
                if client_ids else []
            )

        elif role_name == "super_account_manager":
            manager_ids = user_data.get("assigned_account_managers", [])
            user_data["assigned_account_managers"] = (
                await validate_ids(manager_ids, db.user_collection,
                                   filter_extra={"user_type": "account_manager"},
                                   name="Assigned Account Manager ID",
                                   err_msg="Some provided IDs for 'assigned_account_managers' are invalid or not found.")
                if manager_ids else []
            )

        elif role_name == "client_manager":
            college_ids = user_data.get("associated_colleges", [])
            user_data["associated_colleges"] = (
                await validate_ids(college_ids, db.college_collection, name="College ID",
                                   err_msg="Some provided IDs for 'associated_colleges' are invalid or not found.")
                if college_ids else []
            )

        elif role_name == "super_admin":
            allowed_ips = user_data.get("allowed_ips", [])
            if not allowed_ips:
                user_data["allowed_ips"] = []
                allowed_ips = []
            for ip in allowed_ips:
                try:
                    ipaddress.ip_address(ip)
                except Exception:
                    raise HTTPException(status_code=400, detail=f"Invalid IP address: {ip}")

    async def create_user_dynamically(self, current_user: dict, role_id: str, user_data: dict):
        """
        Dynamically creates a new user based on the provided role, ensuring all required validations are performed
        for role permissions, required fields, and role-specific data.

        Params:
        - `current_user (dict)`: The user making the request, used to check permissions and assign the creator's ID.
        - `role_id (str)`: The ID of the role to which the new user will be assigned.
        - `user_data (dict)`: A dictionary containing the data of the new user, including required fields specific to the target role.

        Raises:
        - HTTPException: If any of the following conditions are met:
            - The current user is not authorized to create the specified role.
            - Required fields are missing or invalid.
            - The email address is already registered.
            - Role-specific data is invalid.
        """
        user_role = current_user.get("role")

        allowed_roles = ROLE_CREATION_RULES.get(user_role, [])
        await utility_obj.is_length_valid(_id=role_id, name="Role Id")
        target_role = await DatabaseConfiguration().role_collection.find_one(
            {"_id": ObjectId(role_id)})
        if not target_role:
            raise HTTPException(status_code=404, detail="Role not found.")

        target_role_name = target_role.get("role_name")
        if target_role_name not in allowed_roles:
            raise HTTPException(status_code=403,
                                detail=f"{user_role} is not authorized to create a {target_role_name} user.")

        pgsql_id = target_role.get("pgsql_id")
        if not isinstance(pgsql_id, int):
            raise HTTPException(status_code=400,
                                detail="Invalid or missing 'pgsql_id' in the target role. Expected an integer.")
        required_fields = await Master_Service().get_fields_by_role(pgsql_id)
        field_definitions = required_fields.get("data", [])

        allowed_keys = {field.get("key_name") for field in field_definitions}
        provided_keys = set(user_data.keys())
        extra_fields = provided_keys - allowed_keys
        if extra_fields:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": f"Unwanted fields provided in user_data for role {target_role_name}.",
                    "extra_fields": list(extra_fields)
                }
            )

        missing_fields = []
        for field in field_definitions:
            key = field.get("key_name")
            is_mandatory = field.get("is_mandatory", False)
            field_type = field.get("field_type", "text")
            value = user_data.get(key)

            if key not in user_data:
                user_data[key] = None
                value = None
            if is_mandatory and (value in [None, ""]):
                missing_fields.append(key)
                continue

            if value is not None:
                await self.validate_field_type(key, value, field_type)

        if missing_fields:
            raise HTTPException(status_code=400,
                                detail=f"Missing mandatory fields: {', '.join(missing_fields)}")

        if user_data.get("role_name") != target_role_name:
            raise HTTPException(status_code=400, detail=f"Role Name must be required and valid.")
        email = user_data.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email is required.")
        existing_user = await DatabaseConfiguration().user_collection.find_one({"user_name": email})
        if existing_user:
            raise HTTPException(status_code=400,
                                detail=f"Username '{email}' is already registered.")
        await self.validate_role_specific_fields(target_role_name, user_data)
        toml_data = utility_obj.read_current_toml_file()
        if toml_data.get('testing', {}).get('test') is True or settings.environment == "demo":
            # for testing , set hardcoded pwd during registration
            random_password = "getmein"
        else:
            # generate random password
            random_password = utility_obj.random_pass()

        date_obj = datetime.now(timezone.utc)
        user_data.pop("role_name", None)
        user_data.update(
            {"password": Hash().get_password_hash(random_password), "last_accessed": date_obj,
             "created_on": date_obj, "is_activated": True, "user_name": email,
             "created_by": ObjectId(current_user.get("user_id")), "user_type": target_role_name,
             "role": {"role_name": target_role_name, "role_id": ObjectId(role_id)}})

        await DatabaseConfiguration().user_collection.insert_one(user_data)
        await cache_invalidation(api_updated="updated_user")
        return {"message": f"{target_role_name} user created successfully."}
