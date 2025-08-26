"""
This file contain schemas related to followup notes
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class AddFollowup(BaseModel):
    """
    Schema for add Followup
    """
    assigned_counselor_id: str = Field(
        None, description="Enter counselor id", example="62aadb13040d039d95027faa"
    )
    followup_date: str = Field(
        None,
        description="Enter followup date and time (Format - dd/mm/yyyyy hh:mm am/pm)",
        example="06/06/2022 08:19 am",
    )
    followup_note: str = Field(
        None, description="Enter followup note", example="Take followup on time"
    )


class FollowupNotes(BaseModel):
    """
    Schema for FollowupNotes
    """
    note: str = Field(None, description="Add note", example="no answer Whats app sent")
    followup: AddFollowup = None
    lead_stage: Optional[str] = None
    lead_stage_label: Optional[str] = None
    application_substage: Optional[str] = None


class list_application(BaseModel):
    """
    Schema for list of application id
    """
    application_id: List
    followup_date: str | None = None
    followup_note: str | None = None
    assigned_counselor_id: str | None = None
