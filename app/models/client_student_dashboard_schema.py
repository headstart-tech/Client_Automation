"""
This module defines Pydantic models for managing client stages, sub-stages, and field operations.
"""
from typing import Optional, List, Union
from pydantic import BaseModel

class ClientSubStage(BaseModel):
    """
    Represents a sub-stage within a client-specific stage.

    Attributes:
        sub_stage_id (str): The unique identifier for the sub-stage.
        sub_stage_order (int): The order of the sub-stage within the client stage.
    """
    sub_stage_id: Optional[str] = None
    sub_stage_order: int

class ClientStageCreate(BaseModel):
    """
    Schema for creating a new client-specific stage.

    Attributes:
        stage_name (str): The name of the client stage.
        stage_order (int): The order of the client stage.
        sub_stages (List[ClientSubStage]): A list of sub-stages associated with the client stage.
    """
    stage_name: str
    stage_order: int
    sub_stages: Optional[List[ClientSubStage]] = None


class ClientStageUpdate(BaseModel):
    """
        Schema for updating an existing client stage.

        Attributes:
            stage_name (Optional[str]): The updated name of the client stage (optional).
            stage_order (Optional[int]): The updated order of the client stage (optional).
            sub_stages (Optional[List[ClientSubStage]]): The updated list of sub-stages (optional).
    """
    stage_name: Optional[str] = None
    stage_order: Optional[int] = None
    sub_stages: Optional[List[ClientSubStage]] = None


class FieldSchema(BaseModel):
    """
        Schema representing a field in a sub-stage.

        Params:
            name (str): The name of the field.
            label (str): The label for the field.
            type (str): The data type of the field (e.g., text, number, boolean).
            is_required (bool): Indicates whether the field is mandatory.
            description (str): A brief description of the field.
            locked (bool): Indicates whether the field is locked and cannot be modified.
            is_custom (bool, optional): Specifies if the field is custom-defined. Defaults to False.
            depends_on (Optional[str]): The field this one depends on, if any.
        """
    name: str
    label: str
    type: str
    is_required: bool = False
    description: str
    locked: bool
    is_custom: bool = True
    depends_on: Optional[str] = None

class SubStageSchema(BaseModel):
    """
       Schema representing a sub-stage with multiple fields.

       Params:
           sub_stage_name (str): The name of the sub-stage.
           fields (List[FieldSchema]): A list of fields associated with the sub-stage.
       """
    sub_stage_name: str
    fields: List[FieldSchema]


class RemoveFieldRequest(BaseModel):
    """
       Request model for removing fields from a section in the application form.
       Attributes:
           section_title (str): The title of the section from which fields should be removed.
           key_names (list[str]): A list of field key names that need to be removed.
    """
    section_title: str
    key_names: list[str]

class MoveFieldRequest(BaseModel):
    """
       Request model for moving a field from one section to another.

       Attributes:
           key_name (str): The name of the field to be moved.
           source_section_name (str): The name of the source section from which the field is being moved.
           destination_section_name (str): The name of the destination section to which the field is being moved.
       """
    key_name: str
    source_section_name: str
    destination_section_name: str


class ValidationItem(BaseModel):
    """
    Represents a validation rule or condition for a specific field.
    Params:
        type (str):
            The type of validation to be applied
        value (Union[str, int, float, bool, None]):
            The value to validate against, depending on the type.
        error_message (str):
            The error message to display or return if validation fails.
    """
    type: str = ""
    value: Union[str, int, float, bool, None] = ""
    error_message: str = ""

class CustomFieldSchema(BaseModel):
    """
          Schema representing a custom field definition for a client.
          Params:
              field_name (str): The display name of the custom field.
              field_type (str): The type of the field (e.g., text, number, dropdown).
              key_name (str): A unique key identifier for the custom field.
              is_mandatory (bool): Whether the field is required (default: False).
              options (List[str]): A list of options for dropdown or multi-select fields.
              selectVerification (Optional[str]): Verification type (if applicable).
              isReadonly (bool): Whether the field is read-only (default: False).
              editable (bool): Whether the field is editable (default: True).
              can_remove (bool): Whether the field can be removed (default: True).
              is_custom (bool): Whether this field is user-defined/custom (default: True).
              defaultValue (Optional[Union[str, int, float, bool]]): The default value of the field.
              addOptionsFrom (str): Specifies where options come from (default: "API").
              apiFunction (Optional[str]): The API function to fetch dynamic options.
              with_field_upload_file (bool): Whether the field supports file uploads (default: False).
              separate_upload_API (bool): Whether a separate API is used for file uploads (default: False).
              validations (Optional[List[ValidationItem]]): List of validations applied to the field.
              accepted_file_type (Optional[List[str]]): List of accepted file types for upload fields.
              """
    field_name: str
    field_type: str
    key_name: str
    is_mandatory: bool = False
    options: Optional[List[str]] = None
    selectVerification: Optional[str] = None
    isReadonly: bool = False
    editable: bool = True
    can_remove: bool = True
    is_custom: bool = True
    defaultValue: Optional[Union[str, int, float, bool]] = None
    addOptionsFrom: Optional[str] =None
    apiFunction: Optional[str] = None
    with_field_upload_file: bool = False
    separate_upload_API: bool = False
    validations: Optional[List[ValidationItem]] = None
    accepted_file_type: Optional[List[str]]=None



