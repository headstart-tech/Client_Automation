"""
This file contain schemas related to QA Manager
"""
from pydantic import BaseModel
from typing import Optional

class CallReview(BaseModel):
    '''
    Schema for call review
    '''
    qc_status : str
    product_knowledge : float
    call_starting : float
    call_closing : float
    issue_handling : float
    engagement : float
    call_quality_score : float
    remarks : str | None = None


class CounsellorList(BaseModel):
    '''
    Schema for filter in call list
    '''
    counsellor: Optional[list[str]] = None


class QAList(BaseModel):
    '''
    Schema for filter in call list
    '''
    qa: Optional[list[str]] = None


class QCStatusList(BaseModel):
    '''
    Schema for filter in call list
    '''
    qc_status: Optional[list[str]] = None


