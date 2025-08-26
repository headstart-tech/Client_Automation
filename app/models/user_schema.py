"""
This file contains user related schemas.
"""
from typing import Optional, List

from pydantic import field_validator, BaseModel, EmailStr, Field

from app.models.applications import DateRange


class UserCreation(BaseModel):
    """
    Schema for create user.
    """
    email: EmailStr
    full_name: str = Field(..., min_length=2)
    mobile_number: int = None
    associated_colleges: list = []
    associated_source_value: str = None
    designation: str = None
    school_name: str = None
    selected_programs: list = None
    daily_limit: int|None = None
    bulk_limit: int|None = None
    fresh_lead_limit: int | None = None

    @field_validator("mobile_number")
    @classmethod
    def phone_number_must_have_10_digit(cls, v):
        if len(str(v)) != 10:
            raise ValueError("Phone number must have 10 digit")
        return v


class UpdatePassword(BaseModel):
    """
    Schema for update password.
    """
    password: Optional[str] = None


class MenuAndFeatures(BaseModel):
    """
    Schema related to admin dashboard menu and features.
    """
    menu: bool = False
    features: Optional[dict] = None


class DashboardMenu(BaseModel):
    """
    Schema related to dashboard menu.
    """
    admin_dashboard: Optional[MenuAndFeatures] = None
    traffic_dashboard: Optional[MenuAndFeatures] = None
    counselor_dashboard: Optional[MenuAndFeatures] = None
    brench_marking_dashboard: Optional[MenuAndFeatures] = None
    publisher_dashboard: Optional[MenuAndFeatures] = None
    panelist_dashboard: Optional[MenuAndFeatures] = None
    authorized_approver_dashboard: Optional[MenuAndFeatures] = None
    trend_analysis: Optional[MenuAndFeatures] = None
    student_quality_index: Optional[MenuAndFeatures] = None
    qa_manager: Optional[MenuAndFeatures] = None
    communication_performance: Optional[MenuAndFeatures] = None
    telephony_dashboard: Optional[MenuAndFeatures] = None


class DataSegmentManager(BaseModel):
    """
    Schema related to data segment manager menu.
    """
    data_segment_manager: Optional[MenuAndFeatures] = None


class Resources(BaseModel):
    """
    Schema related to resources menu.
    """
    resources: Optional[MenuAndFeatures] = None


class CallManagerMenu(BaseModel):
    """
    Schema related to call manager menu.
    """
    call_list: Optional[MenuAndFeatures] = None
    qcd_call_list: Optional[MenuAndFeatures] = None


class ApplicationFormMenu(BaseModel):
    """
    Schema related to application form.
    """
    in_app_call_logs: Optional[MenuAndFeatures] = None


class LeadManagerMenu(BaseModel):
    """
    Schema related to lead manager menu.
    """
    manage_leads: Optional[MenuAndFeatures] = None
    view_all_forms: Optional[MenuAndFeatures] = None
    scoring: Optional[MenuAndFeatures] = None
    user_profile: Optional[MenuAndFeatures] = None
    create_lead: Optional[MenuAndFeatures] = None
    lead_upload: Optional[MenuAndFeatures] = None


class ApplicationManagerMenu(BaseModel):
    """
    Schema related to application manager menu.
    """
    manage_applications: Optional[MenuAndFeatures] = None
    paid_applications: Optional[MenuAndFeatures] = None


class CampaignManagerMenu(BaseModel):
    """
    Schema for campaign manager menu.
    """
    campaign_manager: Optional[MenuAndFeatures] = None
    event_mapping: Optional[MenuAndFeatures] = None
    all_source_leads: Optional[MenuAndFeatures] = None


class UserAccessControlMenu(BaseModel):
    """
    Schema for user access control menu.
    """
    user_manager: Optional[MenuAndFeatures] = None
    download_request_list: Optional[MenuAndFeatures] = None
    manage_sessions: Optional[MenuAndFeatures] = None
    user_activity: Optional[MenuAndFeatures] = None
    client_registration: Optional[MenuAndFeatures] = None
    create_user: Optional[MenuAndFeatures] = None
    user_permission: Optional[MenuAndFeatures] = None
    counsellor_manager: Optional[MenuAndFeatures] = None


class FormDeskMenu(BaseModel):
    """
    Schema related to form desk menu.
    """
    document_listing: Optional[MenuAndFeatures] = None
    manage_form: Optional[MenuAndFeatures] = None
    manage_documents: Optional[MenuAndFeatures] = None
    manage_exams: Optional[MenuAndFeatures] = None


class MarketingMenu(BaseModel):
    """
    Schema related to marketing menu.
    """
    marketing: Optional[MenuAndFeatures] = None


class QueryManagerMenu(BaseModel):
    """
    Schema related to query manager menu.
    """
    query_manager: Optional[MenuAndFeatures] = None


class ReportFeature(BaseModel):
    """
    Schema related to report features.
    """
    report_scheduling: bool = False


class ReportAndAnalyticsMenu(BaseModel):
    """
    Schema related to reports menu.
    """
    reports: Optional[MenuAndFeatures] = None


class ManageCommunicationFeature(BaseModel):
    """
    Schema related to manage communication features.
    """
    manage_category: bool = False


class ManageCommunicationMenuAndFeature(BaseModel):
    """
    Schema related to manage communication menu and features.
    """
    menu: bool = False
    features: Optional[ManageCommunicationFeature] = None


class TemplateManagerMenu(BaseModel):
    """
    Schema related to template manager menu.
    """
    create_widget: Optional[MenuAndFeatures] = None
    create_template: Optional[MenuAndFeatures] = None
    manage_communication_template: Optional[ManageCommunicationMenuAndFeature] = None
    script_automation: Optional[MenuAndFeatures] = None
    media_gallery: Optional[MenuAndFeatures] = None


class SettingMenu(BaseModel):
    """
    Schema for setting menu.
    """
    setting: Optional[MenuAndFeatures] = None
    voucher_promocode_manager: Optional[MenuAndFeatures] = None
    scholarship_configuration: Optional[MenuAndFeatures] = None


class CourseManagement(BaseModel):
    """
    Schema for course management.
    """
    manage_course: Optional[MenuAndFeatures] = None


class TelephonyDashboard(BaseModel):
    """
    Schema for telephony dashboard menu.
    """
    telephony_dashboard: Optional[MenuAndFeatures] = None


class AdmissionManager(BaseModel):
    """
    Schema for admission manager menu.
    """
    admission_dashboard: Optional[MenuAndFeatures] = None
    offer_letter_list: Optional[MenuAndFeatures] = None
    configure_offer_letter: Optional[MenuAndFeatures] = None


class OfflineDataMenu(BaseModel):
    """
    Schema for offline data menu.
    """
    upload_raw_data: Optional[MenuAndFeatures] = None
    view_raw_data: Optional[MenuAndFeatures] = None
    raw_data_upload_history: Optional[MenuAndFeatures] = None


class CampaignPerformance(BaseModel):
    """
    Schema for campaign performance menu.
    """
    all_source_leads: Optional[MenuAndFeatures] = None


class InterviewManager(BaseModel):
    """
    Schema for interview manager menu.
    """
    interview_list: Optional[MenuAndFeatures] = None
    panelist_manager: Optional[MenuAndFeatures] = None
    planner: Optional[MenuAndFeatures] = None
    selection_procedure: Optional[MenuAndFeatures] = None


class VoucherManager(BaseModel):
    """
    Schema for interview manager menu.
    """
    voucher_manager: Optional[MenuAndFeatures] = None


class Automation(BaseModel):
    """
    Schema for campaign performance menu.
    """
    automation_details: Optional[MenuAndFeatures] = None
    automation_beta: Optional[MenuAndFeatures] = None
    create_automation: Optional[MenuAndFeatures] = None
    automation_manager: Optional[MenuAndFeatures] = None


class ClientManager(BaseModel):
    """
    Schema for client manager menu.
    """
    pending_approval: Optional[MenuAndFeatures] = None
    list_of_colleges: Optional[MenuAndFeatures] = None
    billing: Optional[MenuAndFeatures] = None


class ExtraSchema(BaseModel):
    """
    Schema for extra fields.
    """
    manage_otp: Optional[MenuAndFeatures] = None
    navbar_search: Optional[MenuAndFeatures] = None
    add_lead_stage_label: Optional[MenuAndFeatures] = None
    email_category: Optional[MenuAndFeatures] = None


class SubFeature(BaseModel):
    """
    Schema for sub features.
    """
    menu: bool = False
    features: Optional[dict] = None


class Feature(BaseModel):
    """
    Schema for features.
    """
    features: Optional[SubFeature] = None


class UserPermissionSchema(BaseModel):
    """
    User permission schema.
    """
    dashboard: Optional[DashboardMenu] = None
    data_segment_manager: Optional[DataSegmentManager] = None
    resources: Optional[Resources] = None
    call_manager: Optional[CallManagerMenu] = None
    communication: Optional[ApplicationFormMenu] = None
    client_manager: Optional[ClientManager] = None
    lead_manager: Optional[LeadManagerMenu] = None
    application_manager: Optional[ApplicationManagerMenu] = None
    campaign_manager: Optional[CampaignManagerMenu] = None
    user_access_control: Optional[UserAccessControlMenu] = None
    form_desk: Optional[FormDeskMenu] = None
    marketing: Optional[MarketingMenu] = None
    query_manager: Optional[QueryManagerMenu] = None
    report_and_analytics: Optional[ReportAndAnalyticsMenu] = None
    automation: Optional[Automation] = None
    template_manager: Optional[TemplateManagerMenu] = None
    offline_data: Optional[OfflineDataMenu] = None
    campaign_performance: Optional[CampaignPerformance] = None
    interview_manager: Optional[InterviewManager] = None
    voucher_manager: Optional[VoucherManager] = None
    setting: Optional[SettingMenu] = None
    course_management: Optional[CourseManagement] = None
    telephony_dashboard: Optional[TelephonyDashboard] = None
    admission_manager: Optional[AdmissionManager] = None
    others: Optional[ExtraSchema] = None
    features: Optional[Feature] = None


class UserPermission(BaseModel):
    """
    Schema for user permission.
    """
    add_client: Optional[bool] = None
    delete_client: Optional[bool] = None
    purge_client_data: Optional[bool] = None
    add_client_manager: Optional[bool] = None
    delete_client_manager: Optional[bool] = None
    create_enquiry_form: Optional[bool] = None
    update_enquiry_form: Optional[bool] = None
    select_verification_type: Optional[bool] = None
    add_college_super_admin: Optional[bool] = None
    delete_college_super_admin: Optional[bool] = None
    add_college_admin: Optional[bool] = None
    delete_college_admin: Optional[bool] = None
    add_college_head_counselor: Optional[bool] = None
    delete_college_head_counselor: Optional[bool] = None
    add_college_counselor: Optional[bool] = None
    delete_college_counselor: Optional[bool] = None
    add_college_publisher_console: Optional[bool] = None
    delete_college_publisher_console: Optional[bool] = None
    add_moderator: Optional[bool] = None
    add_panelist: Optional[bool] = None
    delete_moderator: Optional[bool] = None
    delete_panelist: Optional[bool] = None
    add_authorized_approver: Optional[bool] = None
    delete_authorized_approver: Optional[bool] = None


class StudentDashboardMenu(BaseModel):
    """
    Schema related to student dashboard menu.
    """
    dashboard: Optional[MenuAndFeatures] = None


class MyApplicationMenu(BaseModel):
    """
    Schema related to my applications menu.
    """
    my_applications: Optional[MenuAndFeatures] = None


class MyQueriesMenu(BaseModel):
    """
    Schema related to my queries menu.
    """
    my_queries: Optional[MenuAndFeatures] = None


class DownloadBrochureMenu(BaseModel):
    """
    Schema related to download brochure menu.
    """
    download_brochure: Optional[MenuAndFeatures] = None


class VirtualCampusMenu(BaseModel):
    """
    Schema related to virtual campus menu.
    """
    download_brochure: Optional[MenuAndFeatures] = None


class FaqMenu(BaseModel):
    """
    Schema related to faq menu.
    """
    faq: Optional[MenuAndFeatures] = None


class PaymentsMenu(BaseModel):
    """
    Schema related to payments menu.
    """
    payments: Optional[MenuAndFeatures] = None


class ExamAdmitCardMenu(BaseModel):
    """
    Schema related to exam admit card menu.
    """
    exam_admit_card: Optional[MenuAndFeatures] = None


class ResultsMenu(BaseModel):
    """
    Schema related to result menu.
    """
    results: Optional[MenuAndFeatures] = None


class CallCounselorMenu(BaseModel):
    """
    Schema related to call counselor menu.
    """
    call_counselor: Optional[MenuAndFeatures] = None


class StudentMenu(BaseModel):
    """
    Schema for student menu.
    """
    dashboard: Optional[StudentDashboardMenu] = None
    my_applications: Optional[MyApplicationMenu] = None
    my_queries: Optional[MyQueriesMenu] = None
    download_brochure: Optional[DownloadBrochureMenu] = None
    virtual_campus_tour: Optional[VirtualCampusMenu] = None
    faq: Optional[FaqMenu] = None
    payments: Optional[PaymentsMenu] = None
    exam_admit_card: Optional[ExamAdmitCardMenu] = None
    results: Optional[ResultsMenu] = None
    call_counselor: Optional[CallCounselorMenu] = None


class UserMenuPermission(BaseModel):
    """
    Schema for user menu and permission.
    """
    user_type: str
    permission: Optional[UserPermission] = None
    menus: Optional[UserPermissionSchema] = None
    student_menus: Optional[StudentMenu] = None


class UpdateUserInfo(BaseModel):
    """
    Schema for user info.
    """
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile_number: Optional[int] = None
    associated_colleges: Optional[List[str]] = None
    associated_source_value: Optional[str] = None
    designation: Optional[str] = None
    school_name: Optional[str] = None
    selected_programs: Optional[List[str]] = None
    is_activated: Optional[bool] = None
    daily_limit: int|None = None
    bulk_limit: int|None = None


class programFilter(BaseModel):
    """
    Schema for get panelist data based on filter.
    """
    course_name: Optional[str | None] = None
    specialization_name: Optional[str | None] = None


class getPanelist(BaseModel):
    """
    Schema for get panelist data based on filter.
    """
    program: Optional[list[programFilter] | None] = None
    is_activated: Optional[bool | None] = None
    interview_list_id: Optional[str | None] = None
    start_time: Optional[str | None] = None
    end_time: Optional[str | None] = None
    search_input: Optional[str | None] = None


class Exclusionlist(BaseModel):
    """
    Schema to get exclusion list data filter
    """
    application_stage: str = None
    exclusion_category: list[str] = None
    lead_stage: list[str] = None
    automation: list[str] = None
    source_list: list[str] = None
    utm_medium: list[dict] = None
    state: list[str] = None
    program_name: list[dict] = None
    templateName: list[str] = None
