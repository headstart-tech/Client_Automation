"""
This file contains schema related to promocode and vouchers
"""

from typing import Optional
from pydantic import BaseModel
from app.models.applications import DateRange


class create_promocode_payload(BaseModel):
    """
    Schema to create promo code
    """
    name: str
    discount: int
    code: str
    units: int
    duration: DateRange
    data_segment_ids: Optional[list] = None


class update_promocode(BaseModel):
    """
    Schema to update promo code
    """
    status: bool | None = None
    duration: DateRange | None = None
    units: int | None = None
    name: str | None = None
    code: str | None = None
    discount: int | None = None
    status_value: str | None = None
    data_segments: list | None = None


class ProgramName(BaseModel):
    """
    Schema for program name
    """
    course_id: str
    spec_name: str | None = None


class CreateVoucherPayload(BaseModel):
    """
    Schema to create voucher
    """
    name: str
    quantity: int
    cost_per_voucher: int
    duration: DateRange
    program_name: list[ProgramName]
    assign_to: str


class UpdateVoucher(BaseModel):
    """
    Schema to update voucher
    """
    status: bool | None = None
    status_value: str | None = None
    name: str | None = None
    quantity: int | None = None
    cost_per_voucher: int | None = None
    duration: DateRange | None = None
    program_name: list[ProgramName] | None = None
    assign_to: str | None = None
