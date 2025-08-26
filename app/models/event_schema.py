"""
This file contain schemas related to event
"""
from typing import Optional

from pydantic import BaseModel, Field

from app.models.applications import DateRange


class AddUpdateEvent(BaseModel):
    """
    Schema for add or update event
    """
    event_name: str | None = Field(None, max_length=50)
    event_start_date: str | None = None
    event_end_date: str | None = None
    event_type: str | None = None
    event_description: str | None = Field(None, max_length=300)
    learning: str | None = None


class EventFilter(BaseModel):
    """
    Schema for filter event data
    """
    search_input: Optional[str | None] = None
    date_range: Optional[DateRange] = None
    event_type: Optional[list[str] | None] = None
    event_name: Optional[list[str] | None] = None
