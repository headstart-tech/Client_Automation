"""
This file contains schemas related to country, state and city
"""
from pydantic import BaseModel
from typing import Optional


class StateCities(BaseModel):
    """
    Schema for get cities based on state codes
    """
    country_code: Optional[str] = "IN"
    state_code: list[str]
