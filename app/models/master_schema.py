"""
This file defines Pydantic schemas for validating and structuring data related to master stages and sub-stages.
"""
import re
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class SubStage(BaseModel):
    """
        Represents a sub stage within a master stage.

    Attributes:
        sub_stage_id (str): The unique identifier for the sub stage.
        sub_stage_order (int): The order of the sub stage within the master stage.
    """
    sub_stage_id: str
    sub_stage_order: int


class MasterStageCreate(BaseModel):
    """
        Schema for creating a new master stage.

    Attributes:
        stage_name (str): The name of the master stage.
        stage_order (int): The order of the master stage.
        sub_stages (List[SubStage]): A list of sub stage associated with the master stage.
    """
    stage_name: str
    stage_order: int
    sub_stages: List[SubStage]


class MasterStageUpdate(BaseModel):
    """
        Schema for updating an existing master stage.

    Attributes:
        stage_name (Optional[str]): The updated name of the master stage (optional).
        stage_order (Optional[int]): The updated order of the master stage (optional).
        sub_stages (Optional[List[SubStage]]): The updated list of sub stage (optional).
    """
    stage_name: Optional[str] = None
    stage_order: Optional[int] = None
    sub_stages: Optional[List[SubStage]] = None


class PermissionsHelper(BaseModel):
    """
    A simple permissions model (customize as needed)
    """
    read: Optional[bool] = Field(default=False, description="Can view the screen")
    write: Optional[bool] = Field(default=False, description="Can edit the screen")
    delete: Optional[bool] = Field(default=False, description="Can delete the screen")
    edit: Optional[bool] = Field(default=False, description="Can edit the screen")


class DashboardHelper(BaseModel):
    """
    Schema for a screen or nested feature
    """
    feature_id: Optional[str] = Field(None, description="Unique feature ID")
    name: Optional[str] = Field(None, description="Name of the screen")
    description: Optional[str] = Field(None, description="Description of the screen")
    icon: Optional[str] = Field(None, description="Optional icon name or path")
    amount: Optional[int] = Field(None, description="Pay amount or some metric for the screen")
    visibility: Optional[bool] = Field(default=False, description="Visibility of the screen")
    need_api: Optional[bool] = Field(default=False,
                                     description="Whether an API is required for the screen")
    permissions: Optional[PermissionsHelper] = Field(
        None, description="Permissions for the screen")
    features: Optional[List['DashboardHelper']] = Field(None,
                                                        description="List of nested sub-screens or features")
    required_role_ids: Optional[list] = Field(None,
                                              description="List of role IDs required to access this screen "
                                                          "or feature. Only users with at least one of these roles can view or interact with it.")

    class Config:
        extra = "allow"


# Required to support self-referencing models
DashboardHelper.model_rebuild()


class MasterScreen(BaseModel):
    """
    Schema for the master screen containing all dashboard screens
    """
    group_description: str = Field(None, description="Group description")
    screen_details: List[DashboardHelper] = Field(default_factory=list,
                                                  description="List of screen details")


class MasterScreenDelete(BaseModel):
    """
    Schema for the master screen containing all dashboard screens
    """
    feature_id: str = Field(None, description="Unique feature ID")


class FieldDetailSchema(BaseModel):
    """
        Represents the detailed configuration of a single form field.

        Attributes:
            field_name (str): The display name of the field (e.g., "First Name").
            field_type (str): The type of the field (e.g., "text", "select", "date").
            is_mandatory (bool): Indicates whether the field is required to be filled out.
            editable (bool): Determines if the field can be edited by the user.
            can_remove (bool): Specifies whether the field can be removed from the form.
            value (str): The current or default value assigned to the field.
            error (str): An error message associated with the field, if any.
            key_name (str): The internal key or identifier used for processing or mapping.
    """
    field_name: str = None
    field_type: str = None
    is_mandatory: bool = None
    editable: bool = None
    can_remove: bool = None
    value: str = None
    error: str = None
    key_name: str = None

    class Config:
        extra = "allow"


class LogicalFieldSchema(BaseModel):
    """
        Represents a group of logically related fields within a section or form.

        Attributes:
            fields (List[FieldDetailSchema]): A list of field definitions, each represented by a `FieldDetailSchema`.
                These fields are logically grouped together for conditional rendering or dependency handling.
    """
    fields: List[FieldDetailSchema]


class FieldsSchema(BaseModel):
    """
        Schema representing a field in a sub stage.

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
    field_name: str
    key_name: str
    field_type: str
    is_mandatory: bool
    editable: bool
    can_remove: bool
    description: str | None = None
    value: str
    error: str
    is_locked: bool = False
    is_readonly: bool = False
    options: list | None = None
    is_custom: bool = False
    dependent_fields: Optional[dict[str, dict | None | str] | str] = {}
    addOptionsFrom: Optional[str] | None = None
    apiFunction: Optional[str] | None = None
    fetch_through_id: Optional[str] | None = None
    with_field_upload_file: Optional[bool] | None = None
    separate_upload_API: Optional[bool] | None = None

    class Config:
        extra = "allow"

    @model_validator(mode="after")
    def validate_select_dependencies(self) -> "FieldsSchema":
        if self.field_type == "select":
            has_add_api = self.addOptionsFrom and self.apiFunction
            has_fetch_id = self.fetch_through_id
            has_options = isinstance(self.options, list) and len(self.options) > 0

            if not (has_add_api or has_fetch_id or has_options):
                raise ValueError(
                    f"For {self.field_name}, field being 'select' type, either 'addOptionsFrom' + 'apiFunction', "
                    "'fetch_through_id', or 'options' must be provided."
                )

            if has_options:
                if self.dependent_fields:

                    logical_fields = self.dependent_fields.get("logical_fields")
                    if not isinstance(logical_fields, dict):
                        raise ValueError(
                            f"For field {self.field_name}, 'dependent_fields.logical_fields' must be a dictionary.")

                    missing_keys = [opt for opt in self.options if opt not in logical_fields]
                    if missing_keys:
                        raise ValueError(
                            f"For field {self.field_name}, The following options are missing in 'dependent_fields.logical_fields': {missing_keys}"
                        )

        return self

    @model_validator(mode="after")
    def validate_key_name_slug_and_lock_edit_conflict(self) -> "FieldsSchema":
        if not re.match(r"^[a-z0-9][a-z0-9_\&/]*$", self.key_name):
            raise ValueError(
                f"key_name '{self.key_name}' must be in snake_case (lowercase, underscore-separated).")
        if self.is_locked and self.editable:
            raise ValueError(
                f"Field '{self.field_name}' cannot be both locked (is_locked=True) and editable (editable=True)."
            )
        return self


class SectionModel(BaseModel):
    """
        Represents a section within a step of the application form.

        Attributes:
            section_title (str): The main title of the section (e.g., "Contact Details").
            section_subtitle (Optional[str]): An optional subtitle providing additional context or instructions.
            fields (List[FieldsSchema]): A list of fields included in this section, each defined by a `FieldsSchema`.
    """
    section_title: str = ""
    section_subtitle: Optional[str] = ""
    is_locked: Optional[bool] = False
    is_custom: Optional[bool] = False
    fields: List[FieldsSchema] = False

    class Config:
        extra = "allow"


class StepModel(BaseModel):
    """
        Represents a single step in the application form.

        Attributes:
            step_name (str): The name or title of the step (e.g., "Personal Information").
            sections (List[SectionModel]): A list of sections included in this step.
                Each section contains grouped fields and is represented by a `SectionModel`.
    """
    step_name: str
    is_locked: Optional[bool] = False
    no_sections: Optional[bool] = False
    not_draggable: Optional[bool] = False
    sections: List[SectionModel] = None

    class Config:
        extra = "allow"


class ApplicationFormModel(BaseModel):
    """
        Pydantic model representing the structure of an application form.

        Attributes:
            application_form (List[StepModel]): A list of steps that make up the application form.
                Each step is represented by a `StepModel`, which contains the configuration and fields
                relevant to that step in the form process.
    """
    application_form: List[StepModel]

    @model_validator(mode="after")
    def validate_first_and_last_fields(self) -> "ApplicationFormModel":
        """
            Validates the first and last steps in the application form after model initialization.

            Ensures that the `application_form` list meets certain structural or logical requirements,
            such as verifying that required fields are present in the first and/or last steps.

            Returns:
                ApplicationFormModel: The validated model instance.

            Raises:
                ValueError: If the validation fails based on custom rules.
        """
        if not self.application_form:
            raise ValueError("application_form must contain at least one step.")

        first_step = self.application_form[0]
        last_step = self.application_form[-1]

        step_name_lower = first_step.step_name.lower()
        if any(keyword not in step_name_lower for keyword in ("program", "preference")):
            raise ValueError(
                f"The first step must be 'course_specialization'/ 'preference_details', got '{first_step.step_name}'.")

        if last_step.step_name.lower() != "declaration":
            raise ValueError(
                f"The last section must be 'declaration', got '{last_step.step_name}'.")

        return self

    @model_validator(mode="after")
    def validate_uniqueness(self) -> "ApplicationFormModel":
        """
            Validates that certain fields within the application form are unique.

            This method runs after model initialization and is used to enforce custom business rules,
            such as ensuring that step names, section identifiers, or field keys are not duplicated
            across the application form.

            Returns:
                ApplicationFormModel: The validated model instance.

            Raises:
                ValueError: If any uniqueness constraint is violated.
        """
        field_names, section_titles, step_names, key_names = set(), set(), set(), set()
        duplicate_sections, duplicate_steps, duplicate_keys = set(), set(), set()
        for step in self.application_form:
            if step.step_name in step_names:
                duplicate_steps.add(step.step_name)
            else:
                step_names.add(step.step_name)

            if not step.no_sections and (not step.sections or len(step.sections) == 0):
                raise ValueError(f"Step '{step.step_name}' must contain at least one Section.")
            if step.sections:
                for section in step.sections:
                    if section.section_title in section_titles:
                        duplicate_sections.add(section.section_title)
                    else:
                        section_titles.add(section.section_title)
                    if not section.fields or len(section.fields) == 0:
                        raise ValueError(
                            f"Section '{section.section_title}' must contain at least one field.")
                    # TODO Uncomment code once student dashboard is fixed!
                    # for field in section.fields:
                    # if field.key_name in key_names:
                    #     duplicate_keys.add(field.key_name)
                    # else:
                    #     key_names.add(field.key_name)

        error_messages = []
        if duplicate_steps:
            error_messages.append(f"Duplicate step_name(s): {', '.join(duplicate_steps)}")
        if duplicate_sections:
            error_messages.append(f"Duplicate section_title(s): {', '.join(duplicate_sections)}")
        if duplicate_keys:
            error_messages.append(f"Duplicate key_name(s): {', '.join(duplicate_keys)}")

        if error_messages:
            raise ValueError(" | ".join(error_messages))

        return self


class SubStageSchema(BaseModel):
    """
       Schema representing a sub-stage with multiple fields.

   Params:
       sub_stage_name (str): The name of the sub-stage.
       fields (List[FieldSchema]): A list of fields associated with the sub-stage.
   """
    sub_stage_name: str
    fields: List[FieldsSchema]


class RegistrationFields(BaseModel):
    """
    Student Registration Form Fields
    """
    field_name: str
    field_type: str
    is_mandatory: bool
    editable: bool = False
    can_remove: bool = False
    key_name: str
    options: Optional[List] = None
    dependent_fields: Optional[dict] = None


class StudentRegistrationFormModel(BaseModel):
    """
    Request Model for student Registration Form
    """
    student_registration_form_fields: List[RegistrationFields]


class RoleSchema(BaseModel):
    """
        Schema representing a role with multiple fields.

    Params:
        role_name (str): The name of the role.
        fields (List[FieldSchema]): A list of fields associated with the role.
    """
    role_name: Optional[str] = None
    role_id: Optional[str] = None
