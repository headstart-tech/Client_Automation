"""
This file contain schemas related to permissions
"""
from typing import Optional, Literal

from pydantic import BaseModel, field_validator, Field
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Permission(Base):
    """Represents a system permission."""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    scope = Column(String, nullable=False, default="college")
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_modified_at = Column(DateTime(timezone=True), server_default=func.now())


class Roles(Base):
    """Represents a user role."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    scope = Column(String, nullable=False, default="college")
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_modified_at = Column(DateTime(timezone=True), server_default=func.now())
    mongo_id = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("roles.id"), nullable=True)

    parent = relationship("Roles", remote_side=[id], backref="children")


class RolePermission(Base):
    """Maps roles to permissions."""
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)


class Groups(Base):
    """Represents the user created groups."""
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    scope = Column(String, nullable=False, default="college")
    college_id = Column(String, nullable=True)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_modified_at = Column(DateTime(timezone=True), server_default=func.now())


class GroupPermission(Base):
    """Maps groups to permissions."""
    __tablename__ = "group_permissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)


class RolePermissionBase(BaseModel):
    """Base schema for creating/updating a role or permission."""
    name: str
    description: Optional[str] = None
    scope: Literal["global", "college"]

    @field_validator("name", mode="before")
    @classmethod
    def name_to_lower(cls, value: Optional[str]) -> str | ValueError:
        """Ensure that the name is always stored in lowercase."""
        if not isinstance(value, str):
            raise ValueError("name must be a string")
        return value.lower().replace(" ", "_")

    @field_validator("scope", mode="before")
    @classmethod
    def validate_scope(cls, value: Optional[str]) -> str:
        """Ensure valid scope value."""
        if value not in ["global", "college"]:
            raise ValueError("Invalid scope value")
        return value


class PermissionCreate(RolePermissionBase):
    """Schema for creating a role or permission or group."""
    name: str

class RoleCreate(RolePermissionBase):
    """Schema for creating a role or permission or group."""
    name: str
    parent_id: Optional[str] = None

class GroupPermissionBase(BaseModel):
    """Base schema for creating/updating a role or permission."""
    name: str
    description: Optional[str] = None
    scope: Literal["global", "college"]
    college_id: Optional[str] = None
    permission_ids: Optional[list[int]] = None

    @field_validator("scope", mode="before")
    @classmethod
    def validate_scope(cls, value: Optional[str]) -> str:
        """Ensure valid scope value."""
        if value not in ["global", "college"]:
            raise ValueError("Invalid scope value")
        return value


class GroupUpdateBase(BaseModel):
    """Base schema for creating/updating a role or permission."""
    name: Optional[str] = None
    description: Optional[str] = None
    scope: Optional[Literal["global", "college"]] = None
    college_id: Optional[str] = None

    @field_validator("scope", mode="before")
    @classmethod
    def validate_scope(cls, value: Optional[str]) -> str:
        """Ensure valid scope value."""
        if value and value not in ["global", "college"]:
            raise ValueError("Invalid scope value")
        return value


class RolePermissionUpdate(BaseModel):
    """Schema for updating a role or permission."""
    name: Optional[str] = None
    description: Optional[str] = None
    scope: Optional[Literal["global", "college"]] = None

    @field_validator("name", mode="before")
    @classmethod
    def name_to_lower(cls, value: Optional[str]) -> str | ValueError:
        """Ensure that the name is always stored in lowercase."""
        if value is None or isinstance(value, str):
            return value.lower().replace(" ", "_") if value else value
        return ValueError("name must be a string or None")

    @field_validator("scope", mode="before")
    @classmethod
    def validate_scope(cls, value: Optional[str]) -> str:
        """Ensure valid scope value."""
        if value and value not in ["global", "college"]:
            raise ValueError("Invalid scope value")
        return value

class PermissionUpdate(RolePermissionUpdate):
    """Schema for updating a role or permission or group."""
    pass

class RoleUpdate(RolePermissionUpdate):
    """Schema for updating a role or permission or group."""
    parent_id: Optional[str] = None


class AssignRemoveGroupUser(BaseModel):
    """Schema for assigning/removing user to/from a group."""
    user_ids: Optional[list[str]] = None


class AssignRemovePermissions(BaseModel):
    """Schema for assigning/removing permission to/from a role/group."""
    permission_ids: Optional[list[int]] = None


class group_assign(BaseModel):
    """Schema for assigning a group to a user."""
    group_ids: list[str] = Field(..., description="List of group IDs")
    user_id: str = Field(..., description="User ID")
