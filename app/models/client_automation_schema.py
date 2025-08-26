"""
This file contains schemas related to client automation.
"""
from datetime import datetime
from enum import Enum
from typing import Literal, Optional, List

from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field, ConfigDict, HttpUrl, field_validator
from pydantic import model_validator

from app.models.course_schema import CourseSpecialization


class Course(BaseModel):
    course_name: str = Field(min_length=2, max_length=50),
    school_name: Optional[str] = None
    course_type: Optional[Literal["UG", "PG", "PHD"]]
    is_activated: bool = True
    course_activation_date: datetime
    course_deactivation_date: datetime
    do_you_want_different_form_for_each_specialization: bool = False
    banner_image_url: str = Field(default=None, alias="course_banner_url")
    fees: int = Field(gt=0, alias="course_fees")
    course_specialization: List[CourseSpecialization] = Field(default_factory=[], alias="specialization_names")
    duration: Optional[int] = Field(ge=1, le=10, default=1)
    course_description: str = Field(max_length=100, default="")
    course_counselor: Optional[List[str]] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

    @field_validator("banner_image_url", mode='before')
    @classmethod
    def validate_url(cls, v):
        """
        Validate the URL
        """
        if v:
            HttpUrl(v)
        return v

    @field_validator("course_activation_date", "course_deactivation_date", mode="before")
    @classmethod
    def validate_and_convert_date(cls, value):
        """Check YYYY-MM-DD format"""
        try:
            dt = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return dt


class PreferenceDetails(BaseModel):
    do_you_want_preference_based_system: Optional[bool] = False
    will_student_able_to_create_multiple_application: Optional[bool] = False
    maximum_fee_limit: Optional[int] = None
    how_many_preference_do_you_want: Optional[int] = None
    fees_of_trigger: Optional[dict] = None


class FetchFormThrough(Enum):
    college_wise = "college_wise"
    course_wise = "course_wise"
    category_wise = "category_wise"


class CollegeProgramModel(BaseModel):
    school_names: List[str] = None
    course_lists: List[Course] = None
    preference_details: Optional[PreferenceDetails] = None
    fetch_form_data_through: str = "college_wise"


class address_details(BaseModel):
    """
    Schema for get address details
    """
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    country_code: Optional[str] = None
    state_code: Optional[str] = None
    city_name: Optional[str] = None


class add_college_details(BaseModel):
    """
    Schema for add college details.
    """
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr = Field(...)
    phone_number: str = Field(..., pattern=r"^\d{10}$",
                              min_length=10, max_length=10)
    address: Optional[address_details] = None
    associated_client: Optional[str] = Field(None, description="Client id")

    @field_validator("associated_client")
    @classmethod
    def validate_associated_client(cls, v):
        if v:
            if not ObjectId.is_valid(v):
                raise ValueError("Invalid client id")
        return v


class permissions_helper(BaseModel):
    """
    Schema for permissions helper
    """
    read: bool = Field(False, description="Read permission")
    write: bool = Field(False, description="Write permission")
    delete: bool = Field(False, description="Delete permission")


class sub_functionalities_helper(BaseModel):
    """
    Schema for sub functionalities helper
    """
    sub_functionality_id: str = Field(None, description="unique sub functionality id")
    name: str = Field(None, description="Name of the sub functionality")
    description: str = Field(None, description="Description of the sub functionality")
    permission: Optional[permissions_helper] = Field(
        None, description="Permission of the sub functionality")


class functionalities_helper(BaseModel):
    """
    Schema for functionalities helper
    """
    functionality_id: str = Field(None, description="unique functionality id")
    name: str = Field(None, description="Name of the functionality")
    description: str = Field(None, description="Description of the functionality")
    sub_functionalities: List[sub_functionalities_helper] = Field(
        None, description="List of sub functionalities")


class sub_screen_schema(BaseModel):
    """
    Schema for sub screen
    """
    sub_screen_id: str = Field(None, description="unique sub screen id")
    name: str = Field(None, description="Name of the sub screen")
    description: str = Field(None, description="Description of the sub screen")
    functionalities: List[functionalities_helper] = Field(
        None, description="List of functionalities")


class screen_schema(BaseModel):
    """
    Schema for sub screen
    """
    screen_id: str = Field(None, description="unique screen id")
    name: str = Field(None, description="Name of the sub screen")
    description: str = Field(None, description="Description of the sub screen")
    sub_screen_bool: bool = Field(False, description="Boolean for sub screen")
    sub_screen: List[sub_screen_schema] = Field(None, description="List of sub screens")
    functionalities: List[functionalities_helper] = Field(
        None, description="List of functionalities")


class dashboard_helper(BaseModel):
    """
    Schema for master screen helper
    """
    dashboard_id: str = Field(None, description="unique dashboard id")
    name: str = Field(None, description="Name of the screen")
    description: str = Field(None, description="Description of the screen")
    screens: List[screen_schema] = Field(None, description="List of sub screens")


class client_screen(BaseModel):
    """
    Schema for master screen name and label
    """
    dashboard: List[dashboard_helper] = Field(None, description="List of screen details")


class FieldSchema(BaseModel):
    """
        Schema representing a field in the student registration form.
        Params:
            name (str): The unique name of the field.
            label (str): The display label for the field.
            type (str): The data type of the field (e.g., text, number, date).
            is_required (bool): Indicates whether the field is mandatory.
            description (str): A brief description of the field.
            locked (bool): Specifies if the field is locked and cannot be modified.
            is_custom (bool, optional): Determines if the field is custom-defined by the user. Defaults to False.
            depends_on (Optional[str], optional): Specifies if the field is dependent on another field. Defaults to None.
            value (str): The actual value entered for the field.
            error (str): Any validation error message related to the field.
        """
    key_name: str
    field_name: str
    field_type: str
    is_mandatory: bool = False
    description: str = None
    locked: bool = False
    is_custom: bool = False
    depends_on: Optional[str] = None
    value: Optional[str] = None
    error: Optional[str] = None
    editable: Optional[bool] = False
    can_remove: Optional[bool] = False
    options: Optional[list] = None
    model_config = ConfigDict(extra="allow")


class SignupFormRequest(BaseModel):
    """
      Request schema for storing student registration form fields in a college.
      Attributes:
          student_registration_form_fields (List[FieldSchema]): A list of fields representing
          the structure of the student registration form.
      """
    student_registration_form_fields: list[FieldSchema]


class ScreenName(str, Enum):
    """
    Enum representing different types of screens.
    """
    client_screen = "client_screen"
    college_screen = "college_screen"


class StatusInfo(BaseModel):
    is_activated: bool

class LeadStage(BaseModel):
    lead_stage_name: str = Field(..., description="Name of the lead stage")
    lead_sub_stages: List[str] = Field(
        ..., description="List of sub‐stage names under this lead stage"
    )

class CollegeAdditionalDetails(BaseModel):
    student_dashboard_title: Optional[str] = Field(None, description="Student dashboard title")
    admin_dashboard_title: Optional[str] = Field(None, description="Admin dashboard title")
    transparent_bg_logo_url: Optional[str] = Field(None, description="Transparent logo URL")
    fab_icon_url: Optional[str] = Field(None, description="FAB icon URL")
    student_dashboard_domain_url: Optional[str] = Field(None, description="Dashboard domain URL")
    student_dashboard_landing_url: Optional[str] = Field(None, description="Landing page URL")
    campus_tour_video_url: Optional[str] = Field(None, description="Campus tour video URL")
    brochure_url: Optional[str] = Field(None, description="Brochure download URL")

    google_tag_manager_id: Optional[str] = Field(
        None, description="Google Tag Manager container ID"
    )
    lead_tags: Optional[List[str]] = Field(
        None, description="Comma‐separated lead tags (will be split into a list)"
    )

    student_dashboard_meta_descriptions: Optional[str] = Field(
        None, description="Meta‐description for student dashboard"
    )
    admin_dashboard_meta_descriptions: Optional[str] = Field(
        None, description="Meta‐description for admin dashboard"
    )
    facebook_pixel_setup_code: Optional[str] = Field(
        None, description="Raw Facebook Pixel initialization code"
    )

    # — Lead Stages & Sub‐Stages —
    lead_stages: Optional[List[LeadStage]] = Field(
        None, description="A repeatable list of lead stages and their sub‐stages"
    )

    # — Payment Gateway —
    payment_method: Optional[Literal["razorpay", "easebuzz"]] = None

    # — Terms & Declaration —
    terms_and_conditions_text: Optional[str] = Field(
        None, description="Rich‐text terms and conditions"
    )
    declaration_text: Optional[str] = Field(
        None, description="Rich‐text declaration text"
    )

    @model_validator(mode='before')
    def validate_urls(cls, value):
        """
        Validate the URL
        """
        if value.get("transparent_bg_logo_url"):
            HttpUrl(value.get("transparent_bg_logo_url"))
        if value.get("fab_icon_url"):
            HttpUrl(value.get("fab_icon_url"))
        if value.get("student_dashboard_domain_url"):
            HttpUrl(value.get("student_dashboard_domain_url"))
        if value.get("student_dashboard_landing_url"):
            HttpUrl(value.get("student_dashboard_landing_url"))
        if value.get("campus_tour_video_url"):
            HttpUrl(value.get("campus_tour_video_url"))
        if value.get("brochure_url"):
            HttpUrl(value.get("brochure_url"))
        return value

class FormStatus(str, Enum):
    """
        Enum representing the possible status values for a college form.
        Params:
        - approved (str): Indicates that the college form has been approved.
        - declined (str): Indicates that the college form has been declined.
        - pending (str): Indicates that the college form is pending review or action.
        """
    approved = "Approved"
    declined = "Declined"
    pending = "Pending"

class BillingRequestModel(BaseModel):
    client_ids: Optional[List[str]] = []
    college_ids: Optional[List[str]] = []

    @model_validator(mode='before')
    def validate_ids(cls, values):
        """
        Validate that each provided client_id and college_id is a valid ObjectId.
        """
        client_ids = values.get("client_ids", [])
        college_ids = values.get("college_ids", [])

        for client_id in client_ids:
            if not ObjectId.is_valid(client_id):
                raise ValueError(f"Invalid client_id: {client_id}")

        for college_id in college_ids:
            if not ObjectId.is_valid(college_id):
                raise ValueError(f"Invalid college_id: {college_id}")

        return values