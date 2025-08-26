"""
This file contain student related schemas
"""
from enum import Enum

from pydantic import field_validator, BaseModel, EmailStr, Field


class check_ability(BaseModel):
    """
    Schema for para ability
    """
    is_disable: bool | None = None
    name_of_disability: str | None = None


class CandidateBasicPreference(BaseModel):
    """
    Schema for student basic details
    """
    main_specialization: str | None = None
    secondary_specialization: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    email: EmailStr | None = None
    alternate_email: str | None = None
    nationality: str | None = None
    mobile_number: str | None = None
    alternate_mobile_number: str | None = None
    date_of_birth: str | None = None
    admission_year: str | None = None
    admission_type: str | None = None
    gender: str | None = None
    caste: str | None = None
    category: str | None = None
    para_ability: check_ability | None = None


class father_Details(BaseModel):
    """
    Schema for father details
    """
    salutation: str | None = None
    name: str | None = None
    email: str | None = None
    mobile_number: str | None = None
    father_occupation: str | None = None


class mother_Details(BaseModel):
    """
    Schema for mother details
    """
    salutation: str | None = None
    name: str | None = None
    email: str | None = None
    mobile_number: str | None = None


class ParentsDetails(BaseModel):
    """
    Schema for parent details
    """
    father_details: father_Details | None = None
    mother_details: mother_Details | None = None


class guardian_Details(BaseModel):
    """
    Schema fir guardian details
    """
    salutation: str | None = None
    name: str | None = None
    email: str | None = None
    mobile_number: str = None
    occupation: str | None = None
    designation: str | None = None
    relationship_with_student: str | None = None


class updateParentsDetails(BaseModel):
    """
    Schema for update parent details
    """
    father_details: father_Details | None = None
    mother_details: mother_Details | None = None
    guardian_details: guardian_Details | None = None
    family_annual_income: str | None = None


class permanent_address1(BaseModel):
    """
    Schema for permanent Address details
    """
    country_code: str | None = None
    state_code: str | None = None
    city: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    pincode: str | None = None


class AddressDetails(BaseModel):
    """
    Schema for full address details
    """
    country_code: str | None = None
    state_code: str | None = None
    city: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    pincode: str | None = None
    is_permanent_address_same: bool
    permanent_address: permanent_address1 | None = None


class TenthSubjectWiseDetails(BaseModel):
    """
    Schema for tenth subject wise details
    """
    english: str | None = None
    maths: str | None = None
    science: str | None = None
    social_science: str | None = None
    language: str | None = None


class TenthSchoolDetails(BaseModel):
    """
    Schema for 10th details
    """
    school_name: str | None = None
    board: str | None = None
    year_of_passing: str | None = None
    marking_scheme: str | None = None
    obtained_cgpa: str | None = None
    max_marks: str | None = None
    tenth_subject_wise_details: TenthSubjectWiseDetails | None = None
    tenth_registration_number: str | None = None


class interSubjectWiseDetails(BaseModel):
    """
    Schema for inter subject details
    """
    subject_name: str | None = None
    max_marks: str | None = None
    obtained_marks: str | None = None
    percentage: str | None = None
    month_of_year_passing: str | None = None


class InterSchoolDetails(BaseModel):
    """
    Schema for inter_school details
    """
    school_name: str | None = None
    board: str | None = None
    year_of_passing: str | None = None
    marking_scheme: str | None = None
    obtained_cgpa: str | None = None
    is_pursuing: bool | None = None
    stream: str | None = None
    max_mark: str | None = None
    appeared_for_jee: bool | None = None
    inter_registration_number: str | None = None
    inter_subject_wise_details: list[interSubjectWiseDetails] | None = None


class GraduationDetails(BaseModel):
    """
    Schema for graduation details
    """
    ug_registration_number: str | None = None
    ug_course_name: str | None = None
    year_of_passing: str | None = None
    marking_scheme: str | None = None
    obtained_cgpa: str | None = None
    name_of_institute: str | None = None
    max_mark: str | None = None
    aggregate_mark: str | None = None
    is_pursuing: bool | None = None


class DiplomaAcademicDetails(BaseModel):
    """
    Schema for diploma academic details for students
    """
    is_pursuing: bool | None = None
    diploma_college_name: str | None = None
    diploma_stream: str | None = None
    year_of_passing: str | None = None
    marking_scheme: str | None = None
    obtained_cgpa: str | None = None
    max_mark: str | None = None
    registration_number: str | None = None


class EducationDetails(BaseModel):
    """
    Schema for education details
    """
    tenth_school_details: TenthSchoolDetails | None = None
    inter_school_details: InterSchoolDetails | None = None
    diploma_academic_details: DiplomaAcademicDetails | None = None
    graduation_details: GraduationDetails | None = None


#   -------------------------- end of secondary schema ----------------------#


#  -------------------------- student sign up schema  --------------------#
class StudentUser(BaseModel):
    """
    Schema for student user details
    """
    full_name: str = Field(..., max_length=50, min_length=2)
    email: EmailStr = Field(...)
    mobile_number: int
    course: str = Field(...)
    main_specialization: str | None = Field(None)
    country_code: str = Field(...)
    state_code: str = Field(...)
    city: str = Field(...)
    college_id: str = Field()
    utm_source: str | None = None
    utm_campaign: str | None = None
    utm_keyword: str | None = None
    utm_medium: str | None = None
    referal_url: str | None = None
    is_email_verify: bool | None = None
    is_mobile_verify: bool | None = None
    accept_payment: bool | None = None
    extra_fields: dict = {}

    @field_validator("mobile_number")
    @classmethod
    def phone_number_must_have_10_digit(cls, v):
        if len(str(v)) != 10:
            raise ValueError("Phone number must have 10 digit")
        return v


class UpdateStudentUser(BaseModel):
    """
    Schema for student user details
    """
    name: str | None = None
    email: EmailStr | None = None
    mobile_number: int | None = None
    alternate_number: int | None = None
    country_code: str | None = None
    state_code: str | None = None
    city_name: str | None = None
    gender: str | None = None

    @field_validator("mobile_number")
    def phone_number_must_10_digit(cls, v):
        if len(str(v)) != 10:
            raise ValueError("Phone number must have 10 digit")
        return v

    @field_validator("alternate_number")
    def phone_number_10_digit(cls, v):
        if len(str(v)) != 10:
            raise ValueError("Phone number must have 10 digit")
        return v


class VerifyReCaptcha(BaseModel):
    """
    Schema for verify captcha
    """
    response: str


class FormStageName(str, Enum):
    """
    Schema for form_stage name
    """
    basic_details = "basic_details"
    parents_details = "parents_details"
    address_details = "address_details"
    education_details = "education_details"
    others = "others"
