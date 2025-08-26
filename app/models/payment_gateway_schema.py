"""
This file contain schemas related to payment
"""
from typing import Optional
from pydantic import BaseModel


class UpdatePaymentDetails(BaseModel):
    """
    Schema for update payment details
    """
    status: Optional[str] = None
    error_code: Optional[str] = None
    error_description: Optional[str] = None
