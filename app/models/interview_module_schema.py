"""
This file contain schemas related to interview module
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OfferLetter(BaseModel):
    template: Optional[str] = None
    authorized_approver: Optional[str] = None


class SelectionProcedure(BaseModel):
    """
    Schema for create selection procedure for course
    """
    course_name: Optional[str] = None
    specialization_name: Optional[str] = None
    eligibility_criteria: Optional[dict] = None
    gd_parameters_weightage: Optional[dict] = None
    pi_parameters_weightage: Optional[dict] = None
    offer_letter: Optional[OfferLetter] = None
    advance_filters: Optional[list] = None


class InterviewApplicationsFilters(BaseModel):
    """
    Schema for get interview list applicants.
    """
    remove_application_ids: Optional[list[str]] = None
    state_code: Optional[list[str]] = None
    city_name: Optional[list[str]] = None
    application_stage_name: Optional[str] = None
    twelve_board: Optional[list[str]] = None
    pg_marks: Optional[list] = None
    pg_university: Optional[list[str]] = None
    source_name: Optional[list[str]] = None
    exam_name: Optional[list[str]] = None
    twelve_marks: Optional[list] = None
    ug_marks: Optional[list] = None
    experience: Optional[list[str]] = None
    exam_score: Optional[list] = None
    category: Optional[list[str]] = None
    nationality: Optional[list[str]] = None
    pg_marks_sort: Optional[bool] = None
    ug_marks_sort: Optional[bool] = None
    exam_score_sort: Optional[bool] = None
    exam_name_sort: Optional[bool] = None


class InterviewList(BaseModel):
    """
    Schema for create/update interview list
    """
    school_name: Optional[str] = None
    course_name: Optional[str] = None
    specialization_name: Optional[str] = None
    list_name: Optional[str] = None
    description: Optional[str] = None
    moderator_id: Optional[str] = None
    status: Optional[str] = None
    pick_top: Optional[int] = None
    filters: Optional[InterviewApplicationsFilters] = None
    advance_filters: Optional[list] = None
    preference: Optional[list] = None


class GetInterviewListApplications(BaseModel):
    """
    Schema for get interview list applications.
    """
    course_name: str
    specialization_name: Optional[str] = None
    pick_top: Optional[int] = None
    filters: Optional[InterviewApplicationsFilters] = None
    advance_filters: Optional[list] = None
    preference: Optional[list] = None


class Interview_view_list(BaseModel):
    """
    Schema for filtering the view interview list
    """
    interview_status: Optional[str] = None
    gd_status: Optional[str] = None
    pi_status: Optional[str] = None
    selection_status: Optional[str] = None


class CandidateStatus(str, Enum):
    """
    Schema of course category
    """
    shortlisted = "Shortlisted"
    interviewed = "Interviewed"
    selected = "Selected"
    rejected = "Rejected"
    offer_letter_sent = "Offer Letter Sent"
    hold = "Hold"
    seat_blocked = "Seat Blocked"


class InterviewStatus(BaseModel):
    """
    Schema useful for change interview status of candidates
    """
    interview_list_id: str
    application_ids: list[str]
    status: CandidateStatus | None


class SlotsPanels(BaseModel):
    """
    Schema useful for delete/publish slots or panels
    """
    slots_panels_ids: list[str]

      
class FeedBackSchema(BaseModel):
    """
    Schema for feedback of interview
    """
    scores: list
    status: CandidateStatus
    comments: Optional[str] = None
    overall_rating: Optional[float] = 0


class InterviewListSelectedApplications(BaseModel):
    """
    Schema for get interview list selected applicants.
    """
    interview_list_id: str
    twelve_marks: Optional[list] = None
    ug_marks: Optional[list] = None
    interview_marks: Optional[list] = None
    twelve_marks_sort: Optional[bool] = None
    ug_marks_sort: Optional[bool] = None
    interview_marks_sort: Optional[bool] = None


class MonthWiseSlots(BaseModel):
    """
    Schema for get month wise slots data
    """
    application_id: str
    location: list[str] = None
    month: int | None = Field(default=None, ge=1, le=12)


class search_interview_filter(BaseModel):
    """
        Search interview filters for interview list
    """
    interview_status: Optional[str] = None
    gd_status: Optional[str] = None
    pi_status: Optional[str] = None
    secondary_score: Optional[list] = None
    ug_score: Optional[list] = None
    interview_score: Optional[list] = None


class slot_time_schema(BaseModel):
    """
        Get value for the slot time
    """
    slot_id: str
    slot_duration: int


class slot_time_update_schema(BaseModel):
    """
        Get the slot time update schema
    """

    panel_id: str
    gap_between_slot: int = None
    updated_slot: list[slot_time_schema]


class whatsapp_webhook_schema(BaseModel):
    """
        Whatsapp webhook schema
    """
    TO: Optional[str] = None
    FROM: Optional[str] = None
    TIME: Optional[str] = None
    MESSAGE_STATUS: Optional[str] = None
    REASON_STATUS: Optional[str] = None
    DELIVERED_DATE: Optional[str] = None
    STATUS_ERROR: Optional[str] = None
    MESSAGE_ID: Optional[str] = None
    CLIENT_GUID: Optional[str] = None
    TEXT_MESSAGE: Optional[str] = None
    SUBMIT_DATE: Optional[str] = None
    MSG_STATUS: Optional[str] = None
    OPERATOR: Optional[str] = None


class whatsapp_webhook_schema(BaseModel):
    """
        Whatsapp webhook schema
    """
    TO: Optional[str] = None
    FROM: Optional[str] = None
    TIME: Optional[str] = None
    MESSAGE_STATUS: Optional[str] = None
    REASON_STATUS: Optional[str] = None
    DELIVERED_DATE: Optional[str] = None
    STATUS_ERROR: Optional[str] = None
    MESSAGE_ID: Optional[str] = None
    CLIENT_GUID: Optional[str] = None
    TEXT_MESSAGE: Optional[str] = None
    SUBMIT_DATE: Optional[str] = None
    MSG_STATUS: Optional[str] = None
    OPERATOR: Optional[str] = None
