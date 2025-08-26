"""
This file contains schemas related to document verification.
"""

from typing import Optional, List
from pydantic import BaseModel
from app.models.applications import DateRange, TwelveBoardFilter, TenthBoardFilter


class ApplicationDetailsSchema(BaseModel):
    """
        Schema for Application details
    """
    form_name: Optional[List[dict]] = None
    dv_status: Optional[List[str]] = None
    tenth_board: TenthBoardFilter = None
    tenth_passing_year: Optional[str] = None
    twelve_board: TwelveBoardFilter = None
    twelve_passing_year: Optional[str] = None
    form_submission_date: Optional[DateRange] = None
    advance_filters: Optional[list] = None
