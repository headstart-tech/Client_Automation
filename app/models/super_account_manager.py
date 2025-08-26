""" This File Contains Schema Related to Super Account Manager CURD Operation """
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from app.models.account_manager import SystemField_Role
from app.core.custom_error import CustomError
from bson import ObjectId
from datetime import datetime


class SuperAccountManagerCreationModel(BaseModel):
    email: EmailStr
    first_name: str
    middle_name: str = None
    last_name: str = None
    mobile_number: str = Field(..., pattern=r"^\d{10}$",min_length=10, max_length=10)

    class Config:
        extra = "forbid"

class SuperAccountManagerUpdateModel(BaseModel):
    email: Optional[EmailStr] = None
    mobile_number: str = Field(default=None, pattern=r"^\d{10}$",min_length=10, max_length=10)


class SystemFieldsModel(BaseModel):
    created_by: str
    user_name: str
    password: str
    role: SystemField_Role
    user_type: str = "super_account_manager"
    assigned_account_managers: Optional[list] = []
    last_accessed: None = None
    created_on: Optional[datetime] = Field(default_factory=datetime.now)
    is_activated: Optional[bool] = True

    @field_validator("created_by")
    def validate_created_by(cls, value):
        if not ObjectId.is_valid(value):
            raise CustomError("Invalid created by id")
        return value

class AccountManagerIdsListModels(BaseModel):
    account_manager_ids: list[str]

    @field_validator("account_manager_ids")
    def validate_account_manager_ids(cls, value):
        for account_manager_id in value:
            if not ObjectId.is_valid(account_manager_id):
                raise CustomError("Invalid account manager id")
        return value