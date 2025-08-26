"""
This file contain configuration related to database
"""

from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

from app.core.log_config import get_logger
from app.core.utils import settings
from app.database.motor_base import master_database, SeasonConnectionManager, pgsql_conn

logger = get_logger(name=__name__)


class DBConfigModel(BaseModel):
    """
    A Pydantic sub-model for data validation.
    """

    database_name: str
    user_name: str
    password: str
    url: str


app = APIRouter()


@app.post("/check_connections")
async def check_connection(some_data: DBConfigModel):
    """
    An async function that checks the database connection.

    :param some_data: An instance of Some_data class that contains database
        credentials.
    :type some_data: DBConfigModel
    :raises HTTPException 203: Non-Authoritative database.
    :raises HTTPException 404: User_name not found.
    :raises HTTPException 401: Unauthorized.
    :raises HTTPException 502: Bad gateway.
    :return: An instance of Some_data class.
    :rtype: DBConfigModel
    """
    if settings.db_name != some_data.database_name:
        raise HTTPException(status_code=203, detail="Non-Authoritative database")
    if settings.db_username != some_data.user_name:
        raise HTTPException(status_code=404, detail="User_name not found.")
    if settings.db_password != some_data.password:
        raise HTTPException(status_code=401, detail="Unauthorized.")
    if settings.db_url != some_data.url:
        raise HTTPException(status_code=502, detail="Bad gateway.")
    f"mongodb+srv://{settings.db_username}:{settings.db_password}@" f"{settings.db_url}/?retryWrites=true&w=majority"
    return some_data


class DatabaseConfiguration:
    def __init__(self, season=None):
        self.season_database = SeasonConnectionManager(season=season).get_db_client()
        self.master_database = master_database
        self.pgsql_database = pgsql_conn.get_sqlalchemy_session()
        self.initialize()

    def initialize(self):
        self.user_collection = self.master_database.users
        self.college_collection = self.master_database.colleges
        self.user_audit_collection = self.master_database.user_audit_log
        self.rbac_audit_collection = self.master_database.rbac_audit_logs
        self.extra_limit_ip_collection = self.master_database.extra_limit_ip_addresses
        self.role_collection = self.master_database.roles
        self.client_collection = self.master_database.client_configurations
        self.onboarding_details = self.master_database.onboarding_details
        self.provider_collection = self.master_database.providers
        self.master_screens = self.master_database.master_screens
        self.template_merge_fields_collection = (
            self.master_database.template_merge_fields
        )
        self.form_options = self.master_database.form_options
        self.approvals_collection = self.master_database.approvals
        self.college_course_collection = self.master_database.college_course_details
        self.approval_workflow_collection = self.master_database.approval_workflow
        self.approval_request_data_collection = self.master_database.approval_requested_data
        self.field_mapping_collection = self.master_database.FieldMapping
        self.refresh_token_collection = self.master_database.refreshToken
        self.country_collection = self.master_database.countries
        self.state_collection = self.master_database.states
        self.city_collection = self.master_database.cities
        self.cache_invalidations = self.master_database.cache_invalidations
        self.Diploma_Inventory = self.master_database.Diploma_Inventory
        self.comments_collection = self.season_database.query_comments
        self.college_form_details = self.master_database.application_form_details
        self.stages = self.master_database.stages
        self.college_roles = self.season_database.roles
        self.sub_stages = self.master_database.sub_stages
        self.student_registration_forms = self.master_database.student_registration_forms
        self.client_stages = self.master_database.client_stages
        self.client_sub_stages = self.master_database.client_sub_stages
        self.templates = self.master_database.templates
        self.college_course_collection = self.master_database.college_course_details
        self.custom_fields = self.master_database.custom_fields
        self.keyname_mapping = self.master_database.keyname_mapping
        self.questions = self.season_database.questions
        self.course_collection = self.season_database.courses
        self.studentApplicationForms = self.season_database.studentApplicationForms
        self.studentsPrimaryDetails = self.season_database.studentsPrimaryDetails
        self.studentSecondaryDetails = self.season_database.studentSecondaryDetails
        self.payment_collection = self.season_database.payments
        self.studentTimeline = self.season_database.studentTimeline
        self.queryCategories = self.season_database.queryCategories
        self.queries = self.season_database.queries
        self.selection_procedure_collection = (
            self.season_database.interviewSelectionProcedure
        )
        self.boardDetails = self.season_database.boardDetails
        self.leadsFollowUp = self.season_database.leadsFollowUp
        self.template_collection = self.season_database.templates
        self.tag_list_collection = self.season_database.tag_list
        self.counselor_management = self.season_database.counselor_management
        self.login_activity_collection = self.season_database.loginActivity
        self.activity_email = self.season_database.activity_email
        self.application_payment_invoice_collection = (
            self.season_database.application_payment_invoices
        )
        self.report_collection = self.season_database.reports
        self.raw_data = self.season_database.raw_data
        self.offline_data = self.season_database.offline_data
        self.sms_activity = self.season_database.sms_activity
        self.notification_collection = self.season_database.notifications
        self.sms_template = self.season_database.sms_template
        self.call_activity_collection = self.season_database.call_activity
        self.automation_collection = self.season_database.automation
        self.campaign_collection = self.season_database.campaign
        self.campaign_beta_collection = self.season_database.campaign_beta
        self.campaign_rule_collection = self.season_database.campaign_rule
        self.data_segment_collection = self.season_database.dataSegment
        self.rule_collection = self.season_database.rule
        self.communication_log_collection = self.season_database.communicationLog
        self.automation_activity_collection = self.season_database.automation_activity
        self.activity_download_request_collection = (
            self.season_database.activity_download_request
        )
        self.user_timeline_collection = self.season_database.userTimeline
        self.interview_list_collection = self.season_database.interviewLists
        self.lead_upload_history = self.season_database.leadUploadHistory
        self.whatsapp_sms_activity = self.season_database.whatsapp_sms_activity
        self.otp_template_collection = self.season_database.otpTemplates
        self.component_charges_collection = self.season_database.componentCharges
        self.form_details_collection = self.season_database.formDetails
        self.health_science_courses_collection = (
            self.season_database.healthScienceCourses
        )
        self.event_collection = self.season_database.events
        self.panel_collection = self.season_database.panels
        self.slot_collection = self.season_database.slots
        self.student_verification_collection = (
            self.season_database.email_or_mobile_verify
        )
        self.meeting_collection = self.season_database.meeting
        self.tenth_twelve_board_details = self.season_database.tenthTwelvthBoardDetails
        self.user_updates_collection = self.season_database.userUpdates
        self.data_segment_mapping_collection = (
            self.season_database.data_segment_student_mapping
        )
        self.advance_filter_field_collection = self.master_database.advanceFilterFields
        self.report_field_collection = self.master_database.reportFields
        self.scripts_details = self.season_database.scripts
        self.automation_communicationLog_details = (
            self.season_database.automation_communicationLog
        )
        self.tawk_chat = self.season_database.tawk_chat
        self.studentLoginActivity = self.season_database.studentLoginActivity
        self.promocode_collection = self.season_database.promocode
        self.check_out_reason = self.season_database.check_out_reason
        self.voucher_collection = self.season_database.vouchers
        self.check_in_out_log = self.season_database.checkInOutLog
        self.template_category = self.season_database.template_category
        self.template_gallery = self.season_database.template_gallery
        self.scholarship_collection = self.season_database.scholarships
        self.checkincheckout = self.season_database.checkincheckout
        self.offer_letter_list_collection = self.season_database.offerLetterlist
