"""
This file contain schema that helpful for store call activity data
"""
from pydantic import BaseModel


class CallActivity(BaseModel):
    """
    Schema of call activity data
    """
    type: list
    mobile_numbers: list
    call_started_datetimes: list
    call_durations: list
