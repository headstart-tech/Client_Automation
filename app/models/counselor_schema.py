"""
This file contain schemas related to counselor
"""
from pydantic import BaseModel

from app.models.applications import ApplicationFilterOptions


class counselor_mail_schema(BaseModel):
    """
    Schema for get list of emails of counselor
    """
    email_id: list = []
    interview_list: list = []
    data_segments_ids: list[str] | None = None
    filter_option: ApplicationFilterOptions | None = None


class course_name_helper(BaseModel):
    """
    Course name schema for specialization
    """
    course_name: str | None = None
    spec_name: str | None = None


class allocation_to_counselor(BaseModel):
    """
    Schema for allocation for counselor details like courses, state and source
    """
    course_name: list = []
    state_code: list = []
    source_name: list = []
    language: list[str] = None
    specialization_name: list[course_name_helper] = None
    fresh_lead_limit: int | None = None


class manual_counselor_allocation(BaseModel):
    """
    Manual counselor assign schema
    """
    offline_data_ids: list[str]
    counselor_id: str
