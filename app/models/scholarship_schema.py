"""
This file contains schemas related to scholarship.
"""
from pydantic import BaseModel, field_validator, ValidationInfo, Field
from enum import Enum
from app.models.student_user_schema import SortType


class BaseSchema(BaseModel):
    """
    Base schema with common validation logic.
    """

    @staticmethod
    def validate_object_id(value: str, field_name: str) -> str:
        """
        Validates a MongoDB-style ObjectId.
        """
        if value and len(value) != 24:
            raise ValueError(f"{field_name.replace('_', ' ').title()} must be required and valid.")
        return value

    @staticmethod
    def validate_application_ids(values: list[str]) -> list[str]:
        """
        Validates application IDs.
        """
        for application_id in values:
            if len(application_id) != 24:
                raise ValueError(f"Application Id `{application_id}` must be a 12-byte input or a "
                                 f"24-character hex string")
        return values


class ProgramInfo(BaseSchema):
    """
    Schema for program information.
    """
    course_name: str
    course_id: str
    specialization_name: str | None = None

    @field_validator("course_id")
    @classmethod
    def validate_course_id(cls, value):
        return cls.validate_object_id(value, "course_id")


class WaiverType(str, Enum):
    """
    Schema of scholarship waiver types.
    """
    percentage = "Percentage"
    amount = "Amount"


class ActivationStatus(str, Enum):
    """
    Schema of scholarship status.
    """
    active = "Active"
    closed = "Closed"


class DefaultScholarshipFilters(BaseModel):
    """
    Schema for default scholarship filters.
    """
    annual_income: list = []
    category: list = []
    gender: list = []
    state_code: list = []
    city_name: list = []


class CreateScholarship(BaseSchema):
    """
    Schema for create a scholarship.
    """
    name: str
    copy_scholarship_id: str | None = None
    programs: list[ProgramInfo]
    count: int = Field(gt=0)
    waiver_type: WaiverType
    waiver_value: float = Field(gt=0)
    template_id: str | None = None
    status: ActivationStatus = "Closed"
    filters: DefaultScholarshipFilters | None = None
    advance_filters: list = []

    @field_validator("copy_scholarship_id", "template_id")
    @classmethod
    def validate_ids(cls, value, info: ValidationInfo):
        return cls.validate_object_id(value, info.field_name)

    @field_validator("name")
    @classmethod
    def validate_scholarship_name(cls, v):
        if v == "":
            raise ValueError("Name must be required and valid.")
        return v


class FilterParameters(BaseModel):
    """
    Schema for filters.
    """
    search: str | None = None
    sort: str | None = None
    sort_type: SortType | None = None
    programs: list[ProgramInfo] | None = None


class CustomScholarship(BaseSchema):
    """
    Schema for provide a custom scholarship.
    """
    application_ids: list[str]
    waiver_type: WaiverType
    waiver_value: float = Field(gt=0)
    template_id: str
    description: str | None = None

    @field_validator("template_id")
    @classmethod
    def validate_template_id(cls, value):
        return cls.validate_object_id(value, "template_id")

    @field_validator("application_ids")
    @classmethod
    def validate_application_id(cls, value):
        return cls.validate_application_ids(value)


class ScholarshipDataType(str, Enum):
    """
    Schema of scholarship data type.
    """
    eligible = "eligible"
    offered = "offered"
    availed = "availed"


class SendLetterInfo(BaseSchema):
    """
    Schema for send a scholarship letter.
    """
    scholarship_id: str
    application_ids: list[str]
    template_id: str

    @field_validator("scholarship_id", "template_id")
    @classmethod
    def validate_ids(cls, value, info: ValidationInfo):
        return cls.validate_object_id(value, info.field_name)

    @field_validator("application_ids")
    @classmethod
    def validate_application_id(cls, value):
        return cls.validate_application_ids(value)


class ChangeDefaultScholarship(BaseSchema):
    """
    Schema for change a default scholarship.
    """
    application_id: str
    default_scholarship_id: str | None = None
    set_custom_scholarship: bool = False
    waiver_type: WaiverType | None = None
    waiver_value: float | None = Field(None, gt=0)
    description: str | None = None

    @field_validator("default_scholarship_id", "application_id")
    @classmethod
    def validate_scholarship_id(cls, value, info: ValidationInfo):
        return cls.validate_object_id(value, info.field_name)
