"""
This file contain schemas related to student application
"""
from typing import Optional
from pydantic import BaseModel
from enum import Enum


class UpdateStudentApplicationForm(BaseModel):
    """
    Schema for update student application details
    """
    student_id: Optional[str] = None
    course_id: Optional[str] = None
    specId_1: Optional[str] = None
    specId_2: Optional[str] = None
    specId_3: Optional[str] = None
    payment_done: Optional[bool] = None
    current_stage: Optional[int] = None
    declaration: Optional[bool] = None


class DocumentStatus(str, Enum):
    """
    Schema for update document status
    """
    Accepted = "Accepted"
    Rejected = "Rejected"
    Under_Review = "Under_Review"
