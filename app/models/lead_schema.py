"""
This file used for contain schemas of counselor and user_lead
"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.applications import DateRange
from app.models.template_schema import EmailType, EmailProvider


class lead_helper(BaseModel):
    """
    Schema for lead name and label
    """
    name: Optional[list] = None
    label: Optional[list] = None


class course_helper(BaseModel):
    """
    schema for course id and specialization name
    """
    course_id: Optional[str] = None
    specialization_name: Optional[str] = None


class counselor_filter(BaseModel):
    """
    Schema for counselor filter
    """
    counselor_id: Optional[list] = []
    lead_stage: Optional[list[lead_helper]] = None
    course: Optional[list[course_helper]] = None


class counselor_leave_schema(BaseModel):
    """
    Schema for counselor leave
    """

    counselor_id: Optional[str] = None
    dates: List[str] = None
    remove_dates: List[str] = None


class offline_schema(BaseModel):
    """
    Schema for display offline data
    """
    date_range: Optional[DateRange] = None
    imported_by: Optional[list] = []
    import_status: Optional[str] = None


class program_base(BaseModel):
    """Schema for map data filter based on program
    """
    date_range: Optional[DateRange] = None
    course_id: Optional[str] = None
    spec_name: Optional[str] = None
    source_name: Optional[list[str]] = None
    mode: Optional[str] = None


class Action(str, Enum):
    """
    Schema of perform action
    """
    email = "email"
    sms = "sms"
    whatsapp = "whatsapp"


class ActionPayload(BaseModel):
    """
    Schema of perform action on raw data
    """
    offline_ids: list[str]
    template: str = None
    subject: str = None
    sms_content: str = None
    dlt_content_id: str = None
    sms_type: str = None
    sender_name: str = None
    whatsapp_text: str = None
    email_type: EmailType = Field(None,
                                  description="Enter email type, it can be default, promotional and transactional")
    email_provider: EmailProvider = Field(None,
                                          description="Enter email provider, it can be default, karix and amazon_ses")


class DvStatus(str, Enum):
    """
    Schema for update document status
    """
    Accepted = "Accepted"
    Rejected = "Rejected"
