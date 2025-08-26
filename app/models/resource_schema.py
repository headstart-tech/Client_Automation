"""
This file contain schemas related to resource
"""
from typing import Optional

from pydantic import BaseModel


class CreateKeyCategory(BaseModel):
    """
    Schema for create key category
    """
    category_name: str


class SendUpdateToProfile(BaseModel):
    """
    Schema for send update to the selected profiles
    """
    selected_profiles: list[str]
    title: str
    content: str


class program_name_helper(BaseModel):
    """
    Schema for get program name
    """
    course_name: Optional[str] = None
    course_id: Optional[str] = None
    course_specialization: Optional[str] = None


class QuestionFilter(BaseModel):
    """
    Schema for get question
    """
    search_pattern: Optional[str] = None
    tags: Optional[list[str]] = None
    program_list: Optional[list[program_name_helper]] = None


class ScriptField(BaseModel):
    """
    Schema for script field
    """
    script_name: str | None = None
    program_name: Optional[list[program_name_helper]] = None
    source_name: Optional[list[str]] = None
    lead_stage: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    application_stage: Optional[list[str]] = None
    script_text: str | None = None
    save_or_draft: str | None = None


class CreateQuestion(BaseModel):
    """
    Schema for create a question
    """
    question: Optional[str] = None
    answer: Optional[str] = None
    tags: Optional[list[str]] = None
    program_list: Optional[list[program_name_helper]] = None
    school_name: Optional[str] = None
    is_visible_to_student: Optional[bool] = None
