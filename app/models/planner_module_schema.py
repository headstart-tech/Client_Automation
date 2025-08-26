"""
This file contain schemas related to planner module
"""
from typing import Optional
from pydantic import BaseModel, Field
from app.models.user_schema import programFilter


class Panel(BaseModel):
    """
    Schema for create or update panel
    """
    name: Optional[str] = None
    description: Optional[str] = None
    slot_type: Optional[str] = None
    panel_type: Optional[str] = None
    user_limit: Optional[int] = Field(None, ge=2, le=10)
    interview_list_id: Optional[str] = None
    panelists: Optional[list] = None
    panel_duration: Optional[str] = None
    gap_between_slots: Optional[str] = None
    slot_count: Optional[int] = None
    slot_duration: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None
    time: Optional[str] = None
    end_time: Optional[str] = None


class Slot(BaseModel):
    """
    Schema for create or update slot
    """
    slot_type: Optional[str] = None
    user_limit: Optional[int] = Field(None, ge=2, le=10)
    panel_id: Optional[str] = None
    interview_mode: Optional[str] = None
    panelists: Optional[list] = None
    interview_list_id: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None
    time: Optional[str] = None
    end_time: Optional[str] = None


class slotPanelFilters(BaseModel):
    """
    Schema for filter slot/panel data.
    """
    filter_slot: Optional[list[str] | None] = None
    slot_status: Optional[list[str] | None] = None
    moderator: Optional[list[str] | None] = None
    slot_state: Optional[str | None] = None
    program_name: Optional[list[programFilter] | None] = None


class getSlotPanelFilter(BaseModel):
    """
    Schema for get slot or panel.
    """
    search_by_applicant: str | None = None
    search_by_panelist: str | None = None
    sort_by_twelve_marks: bool | None = None


class getPanelNames(BaseModel):
    """
    Schema for get panel names.
    """
    slot_type: Optional[str | None] = None
    interview_list_id: Optional[str | None] = None
    start_time: Optional[str | None] = None
    end_time: Optional[str | None] = None
