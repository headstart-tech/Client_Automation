"""
This file contain schemas related to telephony check-in or check-out
"""
from typing import Optional
from pydantic import BaseModel, Field, validator
from app.core.utils import utility_obj
import re


class Reason(BaseModel):
    """
    Schema for Reason of Check-out
    """
    title: str
    icon: str|None = None

class CheckInOut(BaseModel):
    '''
    Schema for check-in or check-out in telephony
    '''
    check_in_status: bool
    reason: Reason | None = None


class MultipleCheckInOut(BaseModel):
    '''
    Schema for check-in or check-out multiple user in telephony from admin side
    '''
    counsellor_ids: list[str]
    check_in_out: CheckInOut

    @validator("counsellor_ids")
    def validate_counsellor_id(cls, ids):
        if ids:
            for id in ids:
                if len(id) != 24:
                    raise ValueError(f"Counselor Id `{id}` must be a 12-byte input or a 24-character hex string.")
            return ids
        raise ValueError("counsellor_ids list must have atleast one counsellor id.")


class CallInitiateDetail(BaseModel):
    '''
    Schema for validate phone number.
    '''
    student_phone: str
    application_id: str|None = None

    @validator('student_phone')
    def validate_phone_number(cls, v):
        pattern = r"^\+91\d{10}$"
        if not re.match(pattern, v):
            raise ValueError('Phone number must be in the format +91XXXXXXXXXX')
        return v
    
class CallDisposeData(BaseModel):
    '''
    Schema for save call after disconnected
    '''
    application_id: str | None = Field(None, description="Application unique id. eg. - `65d87d07638282d4bfb0f461`")
    call_id: str = Field(..., description="Call unique id (_id). eg. - `65d87d07638282d4bfb0f461`")

    @validator("call_id", "application_id")
    def validate_id(cls, v):
        if v != None and len(v) != 24:
            raise ValueError("Id must be a 12-byte input or a 24-character hex string")
        return v
    

class ApplicationCallInfo(BaseModel):
    '''
    Application assgn on call payload
    '''
    phone_num: str|None
    call_id: str|None = Field(None, description="Call unique id (_id). eg. - `65d87d07638282d4bfb0f461`")
    application_id: str = Field(..., description="Application unique id (_id). eg. - `65d87d07638282d4bfb0f461`")

    @validator("call_id", "application_id")
    def validate_id(cls, v):
        if v and len(v) != 24:
            raise ValueError("Id must be a 12-byte input or a 24-character hex string")
        return v
    
    @validator('phone_num')
    def validate_phone_number(cls, v):
        pattern = r"^\+91\d{10}$"
        if v and not re.match(pattern, v):
            raise ValueError('Phone number must be in the format +91XXXXXXXXXX')
        return v
    

class AssignedCounsellorOnMissedCall(BaseModel):
    '''
    Assign counsellor on any missed call payload
    '''
    counsellor_id: str
    student_phone: list[str]

    @validator("counsellor_id")
    def validate_counsellor_id(cls, v):
        if len(v) != 24:
            raise ValueError("Id must be a 12-byte input or a 24-character hex string")
        return v
    
    @validator("student_phone")
    def validate_student_phone(cls, v):
        pattern = r"^\+91\d{10}$"
        for phone in v:
            if not re.match(pattern, phone):
                raise ValueError('Phone number must be in the format +91XXXXXXXXXX')
        return v