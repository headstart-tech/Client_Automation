"""
This file contain schemas related to automation
"""
from typing import Optional

from pydantic import BaseModel


class AutomationExecution(BaseModel):
    """
    Schema for when execute automation
    """
    schedule_value: int = 1
    schedule_type: Optional[str] = None


class PerformAutomationBeta(BaseModel):
    """
    Schema for script of automation
    """
    action: Optional[str] = None
    condition_exec: Optional[dict] = None
    when_exec: AutomationExecution
    selected_template_id: str
    email_subject: Optional[str] = None
    action_type: str


class release_window_helper(BaseModel):
    """
    Release window have start time and end time of automation
    """
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class date_helper(BaseModel):
    """
    date helper for start date and end date of automation
    """
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class lead_stage_form_helper(BaseModel):
    """
    Lead stage form helper schema
    """
    lead_stage: Optional[str] = None
    lead_stage_label: Optional[str] = None


class lead_stage_helper(BaseModel):
    """
    Lead stage schema for automation
    """
    lead_stage_from: Optional[lead_stage_form_helper] = None
    lead_stage_to: Optional[lead_stage_form_helper] = None


class application_stage_helper(BaseModel):
    """
    Schema for application stage
    """
    stage_from: Optional[float] = None
    stage_to: Optional[float] = None


class lead_name_helper(BaseModel):
    """
    schema for lead name
    """
    name: Optional[list] = None
    label: Optional[list] = None


class course_helper(BaseModel):
    """
    schema for course
    """
    course_id: Optional[list] = None
    course_specialization: Optional[list | None] = None
    course_name: Optional[list] = None


class filters_helper(BaseModel):
    """
    schema for basic filters
    """
    source_name: Optional[list] = None
    state_code: Optional[list] = None
    lead_name: Optional[list[lead_name_helper]] = None
    lead_type_name: Optional[str] = None
    counselor_id: Optional[list] = None
    application_stage_name: Optional[str] = None
    is_verify: Optional[str] = None
    payment_status: Optional[list] = None
    course: Optional[course_helper] = None


class selected_filters_helper(BaseModel):
    """
    schema for selected filter
    """
    filters: Optional[filters_helper] = None
    advance_filters: Optional[list] = None
    date_range: Optional[date_helper] = None


class basic_filter(BaseModel):
    """
    Basic filter for automation
    """
    lead_stage_change: Optional[lead_stage_helper] = None
    application_stage: Optional[application_stage_helper] = None
    source_name: Optional[list] = None
    selected_filters: Optional[selected_filters_helper] = None
    date_range: Optional[dict] = None


class data_segment_helper(BaseModel):
    """
    Schema for counsellor schema
    """
    data_segment_id: Optional[str] = None
    data_segment_name: Optional[str] = None


class automation_details_helper(BaseModel):
    """
    a Schema for automation details
    """
    automation_name: str
    data_type: Optional[str] = None
    automation_description: Optional[str] = None
    releaseWindow: Optional[release_window_helper] = None
    date: Optional[date_helper] = None
    days: list[str] = None
    data_segment: list[data_segment_helper] = None
    filters: Optional[basic_filter] = None
    data_count: Optional[int] = None


class CreateAutomationBeta(BaseModel):
    """
    Schema for create automation
    """
    automation_details: Optional[automation_details_helper] = None
    automation_node_edge_details: Optional[dict] = None
    template: bool
    automation_status: Optional[str] = None


class PerformAutomation(BaseModel):
    """
    Schema for script of automation
    """
    condition_exec: Optional[dict] = None
    when_exec: AutomationExecution = None
    selected_template_id: Optional[list] = None
    email_subject: Optional[str] = None
    dlt_content_id: Optional[str] = None
    action_type: Optional[list] = None
