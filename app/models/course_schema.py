""""
This file contain schemas related to course
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class CourseSpecialization(BaseModel):
    """
    Schema for course specialization
    """
    spec_name: Optional[str] = None
    is_activated: Optional[bool] = True
    spec_custom_id:  Optional[str] = None
    spec_fees: Optional[int] = None


class Course(BaseModel):
    """
    Schema for course details
    """
    course_name: str
    course_description: Optional[str] = None
    duration: float = None
    fees: float = None
    is_activated: Optional[bool] = True
    is_pg: Optional[bool] = False
    banner_image_url: Optional[str] = None
    course_specialization: Optional[list[CourseSpecialization]] = []


class UpdateCourseStatus(BaseModel):
    """
    Schema for update status of course
    """
    is_activated: Optional[bool] = None


class UpdateCourse(BaseModel):
    """
    Schema for update course details
    """
    course_name: Optional[str] = None
    course_description: Optional[str] = None
    duration: Optional[str] = None
    fees: Optional[str] = None
    is_activated: Optional[bool] = None
    is_pg: Optional[bool] = None
    banner_image_url: Optional[str] = None
    course_specialization: Optional[list[CourseSpecialization]] = None


class CourseCategory(str, Enum):
    """
    Schema of course category
    """
    health_science = "health_science"


class AcademicCategory(str, Enum):
    """
    Schema of academic category
    """
    ug = "ug"
    pg = "pg"
    phd = "phd"


class ProgramFilter(BaseModel):
    """
    Schema for program filter
    """
    course_name: Optional[str | None] = None
    spec_name: Optional[str | None] = None


class UpdateCourseSpecializations(BaseModel):
    """
    Schema for course specialization
    """
    spec_index: int
    spec_name: Optional[str] = None
    is_activated: Optional[bool] = None
