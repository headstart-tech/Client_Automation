"""
This file contain schemas related to campaign
"""
from enum import Enum
from typing import Union, Optional

from pydantic import BaseModel


class CreateDataSegment(BaseModel):
    """
    Schema for create data segment
    """
    module_name: Optional[str] = None
    segment_type: Optional[str] = None
    data_segment_name: Optional[str] = None
    description: Optional[str] = None
    filters: Optional[dict] = None
    advance_filters: Optional[list] = None
    raw_data_name: Optional[list[str]] = None
    period: Optional[Union[dict, str]] = None
    enabled: Optional[bool] = None
    is_published: Optional[bool] = None
    count_at_origin: Optional[int | str] = None


class CommunicationType(str, Enum):
    """
    Schema of communication type
    """
    email = "email"
    sms = "sms"
    whatsapp = "whatsapp"


class sort_filter(BaseModel):
    """
    schema for verified, payment_status and lead_stage
    """
    verified: Optional[bool] = None
    payment_status: Optional[bool] = None
    lead_stage: Optional[bool] = None
