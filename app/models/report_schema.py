"""
This file contain schemas that will helpful for report routes
"""
from pydantic import BaseModel
from app.models.applications import DateRange
from typing import Union, Optional


class RecipientDetails(BaseModel):
    """
    Schema for recipient details.
    """
    recipient_name: Optional[str] = None
    recipient_email_id: Optional[str] = None
    recipient_cc_mail_id: Optional[str] = None


class GenerateAndReschedule(BaseModel):
    """
    Schema for recipient details.
    """
    trigger_by: Optional[str] = None
    interval: Optional[str | int] = None
    date_range: Optional[DateRange] = None
    recipient_details: Optional[list[RecipientDetails]] = None


class GenerateReport(BaseModel):
    """
    Schema for generate report.
    """
    report_type: Optional[str] = None
    report_name: Optional[str] = None
    format: Optional[str] = None
    report_details: str | None = None
    date_range: DateRange | None = None
    report_send_to: str | None = None
    schedule_value: int | None = 1
    schedule_type: str | None = None
    reschedule_report: Optional[bool] = None
    advance_filter: Optional[list[dict]] = None
    period: Optional[Union[dict, str]] = None
    sent_mail: Optional[bool] = None
    recipient_details: Optional[list[RecipientDetails]] = None
    add_column: Optional[list[str]] = None
    save_template: Optional[bool] = None
    generate_and_reschedule: Optional[GenerateAndReschedule] = None
    is_auto_schedule: Optional[bool] = None


class ReportFilter(BaseModel):
    """
    Schema for filter the report.
    """
    state_code: list[str] | None = []
    city_name: list[str] | None = []
    source_name: list | None = []
    lead_name: list | None = []
    lead_type_name: str | None = None
    application_filling_stage: list | None = []
    counselor_id: list[str] | None = []
    application_stage_name: str | None = None
    is_verify: str | None = None
    payment_status: list[str] | None = []
    source_type: list | None = []
    course: list | dict | None = None
    twelve_marks_name: Optional[list] = None
    twelve_board_name: Optional[list] = None
    form_filling_stage_name: Optional[list] = None
    utm_medium: Optional[list] = None
    utm_campaign: Optional[list] = None
    lead_owner: list[str] | None = []
    application_owner: list[str] | None = []
    payment_date: Optional[DateRange] = None
    payment_mode: list | None = []
    voucher_applied_status: bool | None = None
    promocode_applied_status: bool | None = None
    promocode_name: list | None = None
