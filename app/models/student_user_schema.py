"""
This file contain schemas related to user or student
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from app.models.applications import (
    DateRange,
    CourseFilter,
    TwelveMarksFilter,
    TwelveBoardFilter,
    FormFillFilter,
    UtmMedium,
)


class User(BaseModel):
    """
    Schema for user_name
    """

    user_name: str


class Login(BaseModel):
    """
    Schema for login user
    """

    user_name: str
    password: str


class Token(BaseModel):
    """
    Schema for token
    """

    access_token: str
    token_type: str
    last_payment: dict


class RefreshToken(BaseModel):
    """
    Schema for refresh token
    """

    refresh_token: str
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Schema Related to token_data
    """

    user_name: Optional[str] = None
    scopes: List[str] = []
    college_info: List[dict] = [{}]
    role_id: int | str | None
    groups: List[int] = []


class upload_docs(BaseModel):
    """
    Schema for upload documents
    """

    recent_photo: Optional[bool] = None
    tenth: Optional[bool] = None
    inter: Optional[bool] = None
    adhar_card: Optional[bool] = None
    diploma_marksheet: Optional[bool] = None
    diploma_certificate: Optional[bool] = None
    graduation: Optional[bool] = None
    ug_consolidated_mark_sheet: Optional[bool] = None
    title: Optional[str] = None


class state_halper(BaseModel):
    """
    Schema related to state
    """

    state_b: Optional[bool] = False
    state_code: Optional[list[str]] = None


class source_halper(BaseModel):
    """
    Schema related to source
    """

    source_b: Optional[bool] = False
    source_name: Optional[list[str]] = None


class lead_label(BaseModel):
    """
    Schema for get data with lead label
    """

    name: Optional[list[str]] = None
    label: Optional[list] = None


class lead_halper(BaseModel):
    """
    Schema related to lead
    """

    lead_b: Optional[bool] = False
    lead_sub_b: Optional[bool] = False
    lead_name: Optional[list[lead_label]] = None


class counselor_halper(BaseModel):
    """
    Schema related to counselor
    """

    counselor_b: Optional[bool] = False
    counselor_id: Optional[list[str]] = None


class city_halper(BaseModel):
    """
    Schema related to city"""

    city_b: Optional[bool] = False
    city_name: Optional[list[str]] = None


class application_stage_halper(BaseModel):
    """
    Schema for application stage
    """

    application_stage_b: Optional[bool] = False
    application_stage_name: Optional[str] = None


class lead_type_halper(BaseModel):
    """
    Schema for lead_type related info
    """

    lead_type_b: Optional[bool] = False
    lead_type_name: Optional[str] = None


class payload_data(BaseModel):
    """
    Schema for payload_data
    """

    date_range: Optional[DateRange] = None
    state: Optional[state_halper] = None
    city: Optional[city_halper] = None
    source: Optional[source_halper] = None
    lead_stage: Optional[lead_halper] = None
    lead_type: Optional[lead_type_halper] = None
    counselor: Optional[counselor_halper] = None
    application_stage: Optional[application_stage_halper] = None
    course: Optional[CourseFilter] = None
    payment_status: Optional[list[str]] = None
    is_verify_b: Optional[bool] = False
    is_verify: Optional[str] = None
    date: Optional[bool] = False
    season: Optional[str] = None
    application_filling_stage: Optional[list] = []
    source_type_b: Optional[bool] = False
    source_type: Optional[list] = None
    utm_medium: Optional[list[UtmMedium]] = None
    utm_medium_b: Optional[bool] = False
    utm_campaign_b: Optional[bool] = False
    outbound_b: Optional[bool] = False
    extra_filters: Optional[list] = None
    advance_filters: Optional[list] = None


class paid_application_payload(BaseModel):
    """
    Schema for filter paid applications
    """

    date_range: Optional[DateRange] = None
    state: Optional[state_halper] = None
    city: Optional[city_halper] = None
    source: Optional[source_halper] = None
    lead_type: Optional[lead_type_halper] = None
    lead_stage: Optional[lead_halper] = None
    is_verify_b: Optional[bool] = False
    is_verify: Optional[str] = None
    payment_status: Optional[list[str]] = None
    counselor: Optional[counselor_halper] = None
    application_stage: Optional[application_stage_halper] = None
    course: Optional[CourseFilter] = None
    date: Optional[bool] = False
    season: Optional[str] = None
    application_filling_stage: Optional[list] = []
    source_type_b: Optional[bool] = False
    twelve_marks: TwelveMarksFilter = None
    twelve_board: TwelveBoardFilter = None
    form_filling_stage: FormFillFilter = None
    utm_medium: Optional[list[UtmMedium]] = None
    utm_medium_b: Optional[bool] = False
    utm_campaign_b: Optional[bool] = False
    advance_filters: Optional[list] = None


class ChangeIndicator(str, Enum):
    """
    Schema of change indicator
    """

    last_7_days = "last_7_days"
    last_15_days = "last_15_days"
    last_30_days = "last_30_days"


class AddLeadTag(BaseModel):
    """
    Schema for add lead tag
    """

    student_ids: List[str]
    tags: List[str]


class DeleteLeadTag(BaseModel):
    """
    Schema for delete lead tag
    """

    student_id: str
    tag: str


class SortType(str, Enum):
    """
    Schema of sort type
    """

    asc = "asc"
    dsc = "dsc"


class CommunicationType(str, Enum):
    """
    Schema of Communication Type
    """

    email = "email"
    sms = "sms"
    whatsapp = "whatsapp"


class UpdateApplication(BaseModel):
    """
    Schema of Application Update
    """
    payload: dict = {}
    attachment_details: dict = {}
