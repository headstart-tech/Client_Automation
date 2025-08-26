"""
This file contain schemas related to applications or student secondary details
"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class UtmMedium(BaseModel):
    """
    Schema for lead_type related info
    """
    source_name: Optional[str] = None
    utm_medium: Optional[str] = None


class lead_label(BaseModel):
    """
    Schema for get data with lead label
    """
    name: Optional[list[str]] = None
    label: Optional[list] = None


class TwelveMarksFilter(BaseModel):
    """
    Schema for filter data based on twelve class marks
    """
    twelve_marks_b: bool = False
    twelve_marks_name: Optional[list] = None


class TenthMarksFilter(BaseModel):
    """
    Schema for filter data based on twelve class marks
    """
    tenth_marks_b: bool = False
    tenth_marks_name: Optional[list] = None


class TwelveBoardFilter(BaseModel):
    """
    Schema for filter data based on twelve class details
    """
    twelve_board_b: bool = False
    twelve_board_name: Optional[list] = None


class TenthBoardFilter(BaseModel):
    """
    Schema for filter data based on twelve class details
    """
    tenth_board_b: bool = False
    tenth_board_name: Optional[list] = None


class FormFillFilter(BaseModel):
    """
    Schema for filter data based on twelve class details
    """
    form_filling_stage_b: bool = False
    form_filling_stage_name: Optional[list] = None


class EmailSchema(BaseModel):
    """
    Schema for get email ids
    """
    email: List[EmailStr]


class DateRange(BaseModel):
    """
    Schema for get start date and end date
    """
    start_date: str | None = None
    end_date: str | None = None


class CourseFilter(BaseModel):
    """
    Schema for basic course info
    """
    course_id: Optional[list[str | None]] = None
    course_specialization: Optional[list[str | None]] = None


class ApplicationFilterOptions(BaseModel):
    """
    Schema for filter the data
    """
    state_code: Optional[list[str]] = None
    city_name: Optional[list[str]] = None
    source_name: Optional[list[str]] = None
    lead_name: Optional[list[lead_label]] = None
    lead_type_name: Optional[str] = None
    counselor_id: Optional[list[str]] = None
    application_stage_name: Optional[str] = None
    is_verify: Optional[str] = None
    date_range: Optional[DateRange] = None
    application_filling_stage: list = []
    twelve_marks: Optional[TwelveMarksFilter] = None
    twelve_board: Optional[TwelveBoardFilter] = None
    form_filling_stage: Optional[FormFillFilter] = None
    source_type: Optional[list] = None
    utm_medium: Optional[list[UtmMedium]] = None
    extra_filters: Optional[list] = []
    advance_filters: Optional[list] = None


class call_activity(BaseModel):
    """
    Schema for filter call activity details
    """
    search: str | None = None
    lead_status: str | None = None
    call_status: str | None = None


class course_detail(BaseModel):
    """
    Schema for taking course and specialization details
    """
    course_id: Optional[str | None] = None
    specialization: Optional[str | None] = None


class lead_filter(BaseModel):
    """
    schema for filter the lead and application status
    """
    lead_stage: Optional[list[str]] = None
    course_wise: Optional[list[course_detail]] = None
    payment_status: Optional[str] = None
    is_verify: Optional[str] = None


class ActionUser(str, Enum):
    """
    Schema of filter data based on action user
    """
    user = "user"
    counselor = "counselor"
    system = "system"

class UpdateAction(str, Enum):
    """
    Schema to update checkin status
    """
    CheckOut = "CheckOut"
    LogOut = "LogOut"


class SubscribeAction(str, Enum):
    """
    Schema to update Subscribe action
    """
    Resume = "Resume"
    Exclude = "Exclude"
