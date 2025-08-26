"""
This file contain schemas related to publisher
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class AddStudent(BaseModel):
    """
    Schema for add student
    """
    full_name: str = Field(..., max_length=30, min_length=2)
    email: EmailStr = Field(...)
    mobile_number: int
    course: str = Field(...)
    main_specialization: str = Field(None)
    country_code: str = Field(...)
    state_code: str = Field(...)
    city: str = Field(...)
    college_id: str = Field()
    utm_campaign: Optional[str] = None
    utm_keyword: Optional[str] = None
    utm_medium: Optional[str] = None
    referal_url: Optional[str] = None
