"""
This file contain schemas related to role
"""
from typing import Optional
from pydantic import BaseModel


class Role(BaseModel):
    """
    Schema for Role collection
    """
    role_name: Optional[str] = None
