"""
This file contains schemas related to college.
"""
from datetime import datetime, date
from enum import Enum
from typing import Optional, Union, List, Literal, Any, Dict

from pydantic import BaseModel, EmailStr, Field, HttpUrl, model_validator


class CollegeAddress(BaseModel):
    """
    Schema for college address.
    """
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    country_code: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None


class CollegePOC(BaseModel):
    """
    Schema for college POC.
    """
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_number: Optional[int] = None


class CollegeSubscription(BaseModel):
    """
    Schema for college subscription.
    """
    raw_data_module: bool = False
    lead_management_system: bool = False
    app_management_system: bool = False


class CollegeEnforcement(BaseModel):
    """
    Schema for college enforcement.
    """
    lead_limit: int = Field(default=200000, gt=0)
    counselor_limit: int = Field(default=15, gt=0)
    client_manager_limit: int = Field(default=4, gt=0)
    publisher_account_limit: int = Field(default=8, gt=0)

    class Config:
        arbitrary_types_allowed = True


class CollegeLead(BaseModel):
    """
    Schema for college lead.
    """
    verification_type: Optional[str] = None
    lead_api_enabled: Optional[bool] = False


class RazorpayCredentials(BaseModel):
    """
    Schema for razorpay credentials.
    """
    razorpay_api_key: Optional[str] = None
    razorpay_secret: Optional[str] = None
    razorpay_webhook_secret: Optional[str] = None
    partner: Optional[bool] = False
    x_razorpay_account: Optional[str] = None


class EmailCredentials(BaseModel):
    """
    Schema for email credentials.
    """
    source: Optional[str] = None
    contact_us_number: Optional[str] = None
    university_email_name: Optional[str] = None
    verification_email_subject: Optional[str] = None


class SmsCredentials(BaseModel):
    """
    Schema for sms credentials.
    """
    username_trans: Optional[str] = None
    username_pro: Optional[str] = None
    password: Optional[str] = None
    authorization: Optional[str] = None
    sms_send_to_prefix: Optional[str] = None


class WhatsappCredentials(BaseModel):
    """
    Schema for whatsapp credentials.
    """
    send_whatsapp_url: Optional[str] = None
    generate_whatsapp_token: Optional[str] = None
    whatsapp_username: Optional[str] = None
    whatsapp_password: Optional[str] = None
    whatsapp_sender: Optional[str] = None


class RedisCacheCredentials(BaseModel):
    """
    Schema for redis cache credentials.
    """
    host: Optional[str] = None
    port: Optional[int] = None
    password: Optional[str] = None


class MeilisearchCredentials(BaseModel):
    """
    Schema for meilisearch credentials.
    """
    meili_server_host: Optional[str] = None
    meili_server_master_key: Optional[str] = None


class IntegrationsInfo(BaseModel):
    """
    Schema for integration credentials.
    """
    with_erp: Optional[bool] = None
    with_3rd_party_app: Optional[bool] = None
    with_3rd_party_telephony: Optional[bool] = None
    collpoll_integration: Optional[bool] = None


class UniversityInfo(BaseModel):
    """
    Schema for integration credentials.
    """
    university_name: Optional[str] = None
    university_logo: Optional[str] = None
    payment_successfully_mail_message: Optional[str] = None
    university_contact_us_mail: Optional[str] = None
    university_website_url: Optional[str] = None
    university_admission_website_url: Optional[str] = None


class EmailPreferenceInfo(BaseModel):
    """
    Schema for integration credentials.
    """
    default_provider: Optional[str] = None
    transactional_provider: Optional[str] = None
    promotional_provider: Optional[str] = None


class SeasonDatabaseInfo(BaseModel):
    """
    Schema for season database credentials.
    """
    username: Optional[str] = None
    password: Optional[str] = None
    url: Optional[str] = None
    db_name: Optional[str] = None


class SeasonInfo(BaseModel):
    """
    Schema for season credentials.
    """
    season_id: Optional[str] = None
    season_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    database: Optional[SeasonDatabaseInfo | dict] = None


class CollpollCredentials(BaseModel):
    """
    Schema for coll-poll credentials.
    """
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    region_name: Optional[str] = None
    s3_bucket_name: Optional[str] = None
    collpoll_url: Optional[str] = None
    collpoll_auth_security_key: Optional[str] = None


class AwsCredentials(BaseModel):
    """
    Schema for aws credentials.
    """
    textract_aws_access_key_id: Optional[str] = None
    textract_aws_secret_access_key: Optional[str] = None
    textract_aws_region_name: Optional[str] = None


class LeadsInfo(BaseModel):
    """
    Schema for leads information.
    """
    verification_type: Optional[str] = None
    lead_api_enabled: Optional[str] = None


class S3Credentials(BaseModel):
    """
    Schema for s3 credentials.
    """
    username: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    textract_aws_region_name: Optional[str] = None


class CollegeStatusInfo(BaseModel):
    """
    Schema for college status.
    """
    activation_date: Union[str, datetime] = datetime.utcnow()
    deactivation_date: Union[str, datetime] = datetime.utcnow()


class CollegeCreation(BaseModel):
    """
    Schema for create college.
    """
    name: Optional[str] = None
    client_name: Optional[str] = None
    logo: Optional[str] = None
    background_image: Optional[str] = None
    favicon_url: Optional[str] = None
    admin_dashboard_logo: Optional[str] = None
    admin_dashboard_background_image: Optional[str] = None
    student_dashboard_domain: Optional[str] = None
    admin_dashboard_domain: Optional[str] = None
    student_dashboard_design_layout: Optional[str] = None
    admin_dashboard_design_layout: Optional[str] = None
    address: Optional[CollegeAddress] = None
    website_url: Optional[str] = None
    pocs: Optional[list[CollegePOC]] = None
    subscriptions: Optional[CollegeSubscription] = None
    enforcements: Optional[CollegeEnforcement] = None
    status_info: Optional[CollegeStatusInfo] = None
    college_manager_name: Optional[list] = None
    client_manager_name: Optional[list] = None
    extra_fields: dict = {}
    course_details: list = []
    is_different_forms: bool = False
    form_details: dict = {}
    charges_per_release: dict = {}
    current_crm_usage: Optional[str | bool] = None
    name_of_current_crm: Optional[str] = None
    old_data_migration: Optional[str | bool] = None
    data_storage_preference: Optional[str | bool] = None
    leads: Optional[LeadsInfo | dict] = None
    number_of_forms: Optional[int] = None
    lead_stage_label: Optional[dict] = None
    want_student_dashboard: Optional[str | bool] = None
    thank_you_page_url: Optional[str] = None
    school_names: Optional[list] = None
    system_preference: Optional[dict | str] = None
    razorpay_credentials: Optional[RazorpayCredentials | dict] = None
    email_credentials: Optional[EmailCredentials | dict] = None
    sms_credentials: Optional[SmsCredentials | dict] = None
    whatsapp_credentials: Optional[WhatsappCredentials | dict] = None
    aws_s3_credentials: Optional[S3Credentials | dict] = None
    redis_cache_credentials: Optional[RedisCacheCredentials | dict] = None
    aws_textract_credentials: Optional[AwsCredentials | dict] = None
    tawk_secret: Optional[str] = None
    telephony_secret: Optional[str] = None
    report_webhook_api_key: Optional[str] = None
    meilisearch_credentials: Optional[MeilisearchCredentials | dict] = None
    integrations: Optional[IntegrationsInfo | dict] = None
    university_info: Optional[UniversityInfo | dict] = None
    email_preferences: Optional[EmailPreferenceInfo | dict] = None
    lead_tags: Optional[list] = None
    languages: Optional[list] = None
    current_season: Optional[str] = None
    season_info: Optional[list[SeasonInfo] | list] = None
    brochure_url: Optional[str] = None
    campus_tour_video_url: Optional[str] = None
    website_widget_url: Optional[str] = None
    website_html_url: Optional[str] = None
    google_tag_manager_id: Optional[str] = None
    project_title: Optional[str] = None
    project_meta_description: Optional[str] = None
    fee_rules: Optional[dict] = None
    multiple_application_mode: Optional[bool] = None
    dashboard_domain: Optional[str] = None


class FormStatus(str, Enum):
    """
    Schema of form status.
    """
    approved = "approved"
    declined = "declined"
    pending = "pending"


class ComponentCharges(BaseModel):
    """
    Schema for component charges.
    """
    raw_data_module: int = 1000
    lead_management_system: int = 1000
    app_management_system: int = 1000
    lead: int = 2000
    counselor_account: int = 150
    client_manager_account: int = 50
    publisher_account: int = 100
    email: int = 1
    sms: int = 1
    whatsapp: int = 2


class ReleaseType(str, Enum):
    """
    Schema of release type.
    """
    automated = "automated"
    manual = "manual"


class Dashboard(BaseModel):
    """
    Schema for admin dashboard.
    """
    admin_dashboard: Optional[dict] = None
    traffic_dashboard: Optional[dict] = None
    counselor_dashboard: Optional[dict] = None
    brench_marking_dashboard: Optional[dict] = None
    publisher_dashboard: Optional[dict] = None
    panelist_dashboard: Optional[dict] = None
    authorized_approver_dashboard: Optional[dict] = None
    trend_analysis: Optional[dict] = None
    student_quality_index: Optional[dict] = None
    qa_manager: Optional[dict] = None
    communication_performance: Optional[dict] = None
    telephony_dashboard: Optional[dict] = None


class DataSegmentManager(BaseModel):
    """
    Schema for data segment manager feature.
    """
    data_segment_manager: Optional[dict] = None


class Resources(BaseModel):
    """
    Schema for resource features.
    """
    resources: Optional[dict] = None


class CallManager(BaseModel):
    """
    Schema for call manager feature.
    """
    call_list: Optional[dict] = None
    qcd_call_list: Optional[dict] = None


class Communication(BaseModel):
    """
    Schema for communication.
    """
    in_app_call_logs: Optional[dict] = None


class LeadManager(BaseModel):
    """
    Schema for lead manager.
    """
    manage_leads: Optional[dict] = None
    view_all_forms: Optional[dict] = None
    scoring: Optional[dict] = None
    user_profile: Optional[dict] = None
    create_lead: Optional[dict] = None
    lead_upload: Optional[dict] = None


class ApplicationManager(BaseModel):
    """
    Schema for application manager.
    """
    manage_applications: Optional[dict] = None
    paid_applications: Optional[dict] = None


class CampaignManager(BaseModel):
    """
    Schema for campaign manager.
    """
    campaign_manager: Optional[dict] = None
    event_mapping: Optional[dict] = None
    all_source_leads: Optional[dict] = None


class CampaignPerformance(BaseModel):
    """
    Schema for campaign performance.
    """
    all_source_leads: Optional[dict] = None


class InterviewManager(BaseModel):
    """
    Schema for interview manager.
    """
    interview_list: Optional[dict] = None
    panelist_manager: Optional[dict] = None
    planner: Optional[dict] = None
    selection_procedure: Optional[dict] = None


class VoucherManager(BaseModel):
    """
    Schema for voucher manager.
    """
    voucher_manager: Optional[dict] = None


class Setting(BaseModel):
    """
    Schema for setting.
    """
    setting: Optional[dict] = None
    voucher_promocode_manager: Optional[dict] = None
    scholarship_configuration: Optional[dict] = None


class CourseManagement(BaseModel):
    """
    Schema for course management.
    """
    manage_course: Optional[dict] = None


class TelephonyDashboard(BaseModel):
    """
    Schema for telephony dashboard feature.
    """
    telephony_dashboard: Optional[dict] = None


class AdmissionManager(BaseModel):
    """
    Schema for admission manager submenu feature update.
    """
    admission_dashboard: Optional[dict] = None
    offer_letter_list: Optional[dict] = None
    configure_offer_letter: Optional[dict] = None


class Others(BaseModel):
    """
    Schema for others.
    """
    manage_otp: Optional[dict] = None
    navbar_search: Optional[dict] = None
    add_lead_stage_label: Optional[dict] = None
    email_category: Optional[dict] = None


class ClientManager(BaseModel):
    """
    Schema for client manager.
    """
    pending_approval: Optional[dict] = None
    list_of_colleges: Optional[dict] = None
    billing: Optional[dict] = None


class UserAccessControl(BaseModel):
    """
    Schema for user access control.
    """
    user_manager: Optional[dict] = None
    download_request_list: Optional[dict] = None
    manage_sessions: Optional[dict] = None
    user_activity: Optional[dict] = None
    client_registration: Optional[dict] = None
    create_user: Optional[dict] = None
    user_permission: Optional[dict] = None
    counsellor_manager: Optional[dict] = None


class Reports(BaseModel):
    """
    Schema for report menu.
    """
    reports: Optional[dict] = None


class Marketing(BaseModel):
    """
    Schema for marketing.
    """
    marketing: Optional[dict] = None


class QueryManager(BaseModel):
    """
    Schema for query manager.
    """
    query_manager: Optional[dict] = None


class FormDesk(BaseModel):
    """
    Schema for form desk.
    """
    document_listing: Optional[dict] = None
    manage_form: Optional[dict] = None
    manage_documents: Optional[dict] = None
    manage_exams: Optional[dict] = None


class Automation(BaseModel):
    """
    Schema for automation.
    """
    automation_details: Optional[dict] = None
    automation_beta: Optional[dict] = None
    create_automation: Optional[dict] = None
    automation_manager: Optional[dict] = None


class TemplateManager(BaseModel):
    """
    Schema for template manager.
    """
    create_widget: Optional[dict] = None
    create_template: Optional[dict] = None
    manage_communication_template: Optional[dict] = None
    script_automation: Optional[dict] = None
    media_gallery: Optional[dict] = None


class OfflineData(BaseModel):
    """
    Schema for offline data.
    """
    upload_raw_data: Optional[dict] = None
    view_raw_data: Optional[dict] = None
    raw_data_upload_history: Optional[dict] = None


class Feature(BaseModel):
    """
    Schema for feature.
    """
    dashboard: Optional[Dashboard] = None
    data_segment_manager: Optional[DataSegmentManager] = None
    resources: Optional[Resources] = None
    call_manager: Optional[CallManager] = None
    communication: Optional[Communication] = None
    client_manager: Optional[ClientManager] = None
    lead_manager: Optional[LeadManager] = None
    application_manager: Optional[ApplicationManager] = None
    campaign_manager: Optional[CampaignManager] = None
    user_access_control: Optional[UserAccessControl] = None
    form_desk: Optional[FormDesk] = None
    marketing: Optional[Marketing] = None
    query_manager: Optional[QueryManager] = None
    report_and_analytics: Optional[Reports] = None
    automation: Optional[Automation] = None
    template_manager: Optional[TemplateManager] = None
    offline_data: Optional[OfflineData] = None
    campaign_performance: Optional[CampaignPerformance] = None
    interview_manager: Optional[InterviewManager] = None
    voucher_manager: Optional[VoucherManager] = None
    setting: Optional[Setting] = None
    course_management: Optional[CourseManagement] = None
    telephony_dashboard: Optional[TelephonyDashboard] = None
    admission_manager: Optional[AdmissionManager] = None
    others: Optional[Others] = None


class UsePurpose(str, Enum):
    """
    Schema for use purpose of get college API.
    """
    authentication = "authentication"


class payment_method_helper(str, Enum):
    """
    Schema for use purpose of get college API.
    """
    icici_bank = "icici_bank"
    razorpay = "razorpay"


class LeadStageHelper(BaseModel):
    """
    Schema for lead stage and sub lead stage
    """
    stage_name: Optional[str] = None
    sub_lead_stage: Optional[list] = None


class GeneralDetails(BaseModel):
    """
    Schema for general details with proper validation and optional fields.
    """

    logo_transparent: Optional[HttpUrl] = Field(
        None, description="URL or path to the transparent logo")
    fab_icon: Optional[HttpUrl] = Field(None, description="URL or path to the favicon icon")
    student_dashboard_landing_page_link: Optional[HttpUrl] = Field(
        None, description="Landing page link for student dashboard")
    google_tag_manager_id: Optional[str] = Field(
        None, description="Google Tag Manager ID for tracking")
    student_dashboard_meta_description: Optional[str] = Field(
        None, description="Meta description for the student dashboard")
    admin_dashboard_meta_description: Optional[str] = Field(
        None, description="Meta description for the admin dashboard")
    facebook_pixel_setup_code: Optional[str] = Field(
        None, description="Facebook Pixel setup code for tracking")
    student_dashboard_project_title: Optional[str] = Field(
        None, description="Title of the student dashboard project")
    admin_dashboard_project_title: Optional[str] = Field(
        None, description="Title of the admin dashboard project")
    lead_stages: List[LeadStageHelper] = Field(
        None, description="Details related to lead stages")
    lead_tags: Optional[List[str]] = Field(None, description="List of lead tags")
    student_dashboard_domain: Optional[HttpUrl] = Field(
        None, description="Domain URL for the student dashboard")
    campus_tour_video_url: Optional[HttpUrl] = Field(
        None, description="URL to campus tour video")
    brochure_url: Optional[HttpUrl] = Field(None, description="URL to brochure")
    payment_method: Optional[payment_method_helper]
    declaration_text: Optional[str] = Field(
        None, description="Declaration text for the college")
    terms_and_condition_text: Optional[str] = Field(
        None, description="Terms and conditions text for the college")


class DatabaseHelper(BaseModel):
    """
    Schema for database helper, containing connection details.
    """
    username: Optional[str] = Field(None, description="Database username")
    password: Optional[str] = Field(None, description="Database password")
    url: Optional[HttpUrl] = Field(None, description="Database connection URL")
    db_name: Optional[str] = Field(None, description="Database name")


class SeasonDetails(BaseModel):
    """
    Schema for season details, containing metadata about a season.
    """
    season_name: Optional[str] = Field(None, description="Name of the season")
    season_id: Optional[str] = Field(None, description="Unique identifier for the season")
    is_current_season: Optional[bool] = Field(
        False, description="Flag indicating if it is the current season")
    start_date: Optional[str] = Field(None, description="Start date of the season")
    end_date: Optional[str] = Field(None, description="End date of the season")
    database: Optional[DatabaseHelper] = Field(
        None, description="Database connection details for the season")


class CollegeURLsModel(BaseModel):
    dashboard_domain: Optional[HttpUrl] = Field(
        None, description="URL of the student dashboard", alias="student_dashboard_url"
    )
    admin_dashboard_url: Optional[HttpUrl] = Field(
        None, description="URL of the admin dashboard"
    )

    class Config:
        populate_by_name = True


class GetBillingDetailsModel(BaseModel):
    filters: Optional[Literal["last_7_days", "last_15_days", "last_30_days", "last_365_days"]] = None
    from_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD")
    to_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD")

    @model_validator(mode="before")
    def check_filters_or_dates(cls, values):
        filters = values.get("filters")
        fd = values.get("from_date")
        td = values.get("to_date")

        # If both from_date and to_date are provided, validate format
        if fd is not None and td is not None:
            for name, date_str in (("from_date", fd), ("to_date", td)):
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    raise ValueError(f"Invalid format for `{name}`: '{date_str}', expected YYYY-MM-DD")
        elif not filters:
            # If neither filters nor dates are provided, set filters to "last_30_days"
            values["filters"] = "last_30_days"

        return values


class PublisherBulkLeadPushLimit(BaseModel):
    bulk_limit: int
    daily_limit: int


class EazyPayConfig(BaseModel):
    merchant_id: Optional[str] = None
    encryption_key: Optional[str] = None


class EasyBuzzConfig(BaseModel):
    merchant_key: Optional[str] = None
    merchant_salt: Optional[str] = None
    base_url: Optional[HttpUrl] = None
    environment: Optional[str] = None
    retrieve_url: Optional[HttpUrl] = None


class HDFCConfig(BaseModel):
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    key: Optional[str] = None
    base_url: Optional[HttpUrl] = None
    environment: Optional[str] = None
    retrieve_url: Optional[HttpUrl] = None


class PayUConfig(BaseModel):
    retrieve_url: Optional[HttpUrl] = None
    merchant_key: Optional[str] = None
    merchant_salt: Optional[str] = None


class GatewaysConfig(BaseModel):
    razorpay: Optional[RazorpayCredentials] = None
    easy_buzz: Optional[EasyBuzzConfig] = None
    eazypay: Optional[EazyPayConfig] = None
    hdfc: Optional[HDFCConfig] = None
    payu: Optional[PayUConfig] = None


class PaymentMode(BaseModel):
    online: bool
    offline: bool


class PaymentConfiguration(BaseModel):
    payment_name: str
    payment_key: str
    application_wise: bool
    allow_payment: bool
    payment_gateway: List[str]
    payment_mode: PaymentMode
    show_status: bool
    apply_scholarship: bool
    apply_promo_voucher: bool


class FirstUrlConfig(BaseModel):
    authorization: Optional[str] = None
    juno_url: Optional[HttpUrl] = None


class JunoErpConfig(BaseModel):
    first_url: Optional[FirstUrlConfig] = None
    second_url: Optional[FirstUrlConfig] = None
    prog_ref: Any = None


class RawDataStatusConfig(BaseModel):
    status_1: str
    status_2: str
    status_3: str


class TelephonyCredential(BaseModel):
    key: str
    outbound_url: HttpUrl


class TelephonyCredConfig(BaseModel):
    mcube: TelephonyCredential
    mcube2: TelephonyCredential


class EmailCredential(BaseModel):
    payload_username: str
    payload_password: str
    payload_from: EmailStr
    source: EmailStr


class EmailConfigurations(BaseModel):
    verification_email_subject: str
    contact_us_number: str
    university_email_name: str
    banner_image: HttpUrl
    email_logo: HttpUrl


class DatabaseConfig(BaseModel):
    username: str
    password: str
    url: str
    db_name: str


class Season(BaseModel):
    season_name: str
    start_date: date  # in YYYY-MM-DD format
    end_date: date  # in YYYY-MM-DD format
    database: DatabaseConfig

    @model_validator(mode='before')
    @classmethod
    def parse_dates(cls, values):
        """
        Ensures 'start_date' and 'end_date' strings are parsed as date in YYYY-MM-DD format.
        """
        for field in ('start_date', 'end_date'):
            v = values.get(field)
            if isinstance(v, str):
                try:
                    values[field] = datetime.strptime(v, '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError(f"'{field}' must be in YYYY-MM-DD format")
        return values


class UniversityDetails(BaseModel):
    university_contact_us_mail: EmailStr
    university_website_url: HttpUrl
    university_prefix_name: str


class ChargesPerRelease(BaseModel):
    forSMS: float = Field(2.35, gt=0)
    forEmail: float = Field(1.11, gt=0)
    forWhatsapp: float = Field(3.66, gt=0)
    forLead: float = Field(1.25, gt=0)


class CollegeConfiguration(BaseModel):
    email_credentials: EmailCredential
    email_configurations: EmailConfigurations
    seasons: List[Season]
    university_details: UniversityDetails
    payment_gateways: GatewaysConfig
    juno_erp: JunoErpConfig
    payment_configurations: List[PaymentConfiguration]
    preferred_payment_gateway: str
    payment_successfully_mail_message: str
    cache_redis: RedisCacheCredentials
    enforcements: CollegeEnforcement
    charges_per_release: ChargesPerRelease
    users_limit: int
    publisher_bulk_lead_push_limit: PublisherBulkLeadPushLimit
    report_webhook_api_key: str
    telephony_secret: str
    telephony_cred: TelephonyCredConfig
    email_display_name: str
    s3_base_folder: str

    async def to_db(self, college: dict) -> Dict[str, Any]:
        # 1) Merge email credentials + configurations
        email = {
            **self.email_credentials.model_dump(),
            **self.email_configurations.model_dump()
        }

        # 2) Build seasons list with generated season_id and determine current
        db_seasons = []
        for s in self.seasons:
            start_dt = s.start_date
            season_id = f"season_{start_dt.year}"
            db_seasons.append({
                "season_id": season_id,
                "season_name": s.season_name,
                "start_date": s.start_date,
                "end_date": s.end_date,
                "database": s.database,
            })

        today = date.today()
        current = None
        for season in db_seasons:
            sd = datetime.strptime(str(season["start_date"]), "%Y-%m-%d").date()
            ed = datetime.strptime(str(season["end_date"]), "%Y-%m-%d").date()
            if sd <= today <= ed:
                current = season["season_id"]
                break
        if current is None and db_seasons:
            current = db_seasons[0]["season_id"]

        # 3) Prepare gateways (only non-empty)
        gateways = {
            name: cfg
            for name, cfg in self.payment_gateways.model_dump(exclude_defaults=True).items()
            if cfg
        }

        # 5) Charges per release
        charges = self.charges_per_release.model_dump()

        # Assemble DB payload
        db_payload = {
            "email": email,
            "current_season": current,
            "seasons": db_seasons,
            "university_prefix_name": self.university_details.university_prefix_name,
            "university": {
                "university_admission_website_url": None,
                "university_logo": None,
                "university_name": college.get("name"),
                "university_contact_us_mail": self.university_details.university_contact_us_mail,
                "university_website_url": self.university_details.university_website_url,
                "payment_successfully_mail_message": self.payment_successfully_mail_message,
            },
            "cache_redis": self.cache_redis.model_dump(),
            "gateways": gateways,
            "juno_erp": self.juno_erp.model_dump() if self.juno_erp else None,
            "payment_configurations": [pc.model_dump() for pc in self.payment_configurations],
            "payment_gateway": self.preferred_payment_gateway,
            "enforcements": self.enforcements.model_dump(),
            "charges_per_release": charges,
            "users_limit": self.users_limit,
            "publisher_bulk_lead_push_limit": self.publisher_bulk_lead_push_limit.model_dump(),
            "report_webhook_api_key": self.report_webhook_api_key,
            "telephony_secret": self.telephony_secret,
            "telephony_cred": self.telephony_cred.model_dump() if self.telephony_cred else None,
            "email_display_name": self.email_display_name,
            "s3_base_folder": self.s3_base_folder,
            "eazypay": self.payment_gateways.eazypay.model_dump() if self.payment_gateways.eazypay else None,
            "razorpay": self.payment_gateways.razorpay.model_dump() if self.payment_gateways.razorpay else None,
        }

        return db_payload

    class Config:
        arbitrary_types_allowed = True
