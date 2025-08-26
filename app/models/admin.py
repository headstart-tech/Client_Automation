from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models.account_manager import SystemField_Role
from typing import Optional
from datetime import datetime
from bson import ObjectId
from app.core.custom_error import CustomError


class AdminCreationModel(BaseModel):
    email: EmailStr
    first_name: str
    middle_name: str = Field(default="")
    last_name: str = Field(default="")
    mobile_number: str = Field(pattern=r"^\d{10}$", min_length=10, max_length=10)

    class Config:
        extra = "forbid"


class AdminUpdateModel(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile_number: Optional[str] = Field(default=None, pattern=r"^\d{10}$", min_length=10, max_length=10)


class SystemFieldsModel(BaseModel):
    created_by: str
    user_name: str
    password: str
    role: SystemField_Role
    user_type: str = "admin"
    last_accessed: None = None
    created_on: Optional[datetime] = Field(default_factory=datetime.now)
    is_activated: Optional[bool] = True

    @field_validator("created_by")
    def validate_created_by(cls, value):
        if not ObjectId.is_valid(value):
            raise CustomError("Invalid created by id")
        return value