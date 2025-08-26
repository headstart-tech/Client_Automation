"""
this contains information about the current database connection
"""
from typing import Optional

from fastapi.exceptions import HTTPException
from pymongo import MongoClient
from pymongo.database import Database

from app.core.log_config import get_logger
from app.core.utils import settings, utility_obj
from app.database.master_db_connection import singleton_client, \
    CreateConnection
from app.database.motor_base_singleton import MotorBaseSingleton

logger = get_logger(__name__)

toml_data = utility_obj.read_current_toml_file()


class PyMongoBase:
    """
        Manages synchronous MongoDB connections with master and season-specific databases.

        Features:
        - Connection pooling and reuse
        - Automatic season database selection
        - Testing environment support
        - Clean connection management
    """

    def __init__(self, db: Optional[str] = None):
        """
        Initialize the database connection manager.

        Args:
            db: Optional database name override
        """
        self.client = None
        self.season_db = {}
        self._season_client = None
        self._master_database = None
        self._season_database = None

        # Set database name based on testing mode
        self.db_name = "test" if toml_data.get("testing", {}).get("test") else settings.db_name
        self._db = db or self.db_name

    def get_client_uri(self, db_username: str, db_password: str, db_url: str) -> MongoClient:
        """
        Create MongoDB client connection using credentials.

        Args:
            db_username: Database username
            db_password: Database password
            db_url: Database host URL

        Returns:
            MongoClient instance
        """
        uri = f"mongodb+srv://{db_username}:{db_password}@{db_url}/?retryWrites=true&w=majority"
        return CreateConnection().create_mongo_client(uri=uri)

    @property
    def master_client(self) -> MongoClient:
        """Get or create the master database client instance."""
        if self.client is None:
            self.client = singleton_client
        return self.client

    def get_season_db(self, all_seasons: list, season: Optional[str] = None) -> dict:
        """
        Find season database credentials from available seasons.

        Args:
            all_seasons: List of all available seasons
            season: Optional season identifier

        Returns:
            Dictionary of database credentials
        """
        return next(
            (data.get("database", {})
             for data in all_seasons
             if data.get("season_id") == season),
            {}
        )

    def create_client_with_master(self) -> Database:
        """Establish and return master database connection."""
        if self.client is None:
            self.client = self.master_client
        self._master_database = self.client[self.db_name]
        return self._master_database

    def get_season_credentials(self, season: Optional[str] = None) -> dict:
        """
        Get credentials for a specific season.

        Args:
            season: Optional season identifier

        Returns:
            Dictionary of season credentials

        Raises:
            HTTPException: If season not found
        """
        master_data = MotorBaseSingleton.get_instance().master_data
        season = season or master_data.get("current_season")
        credentials = self.get_season_db(master_data.get("seasons", []), season=season)

        if not credentials:
            raise HTTPException(
                status_code=404,
                detail=f"{season} not found in our system"
            )
        return credentials

    def get_season_connection(self, season: Optional[str] = None) -> Database:
        """
        Get or create a season-specific database connection.

        Args:
            season: Optional season identifier

        Returns:
            Database instance for the specified season

        Raises:
            HTTPException: If season configuration not found
        """
        master_data = MotorBaseSingleton.get_instance().master_data
        season = season or master_data.get("current_season")
        credentials = self.get_season_credentials(season)

        if not credentials:
            raise HTTPException(status_code=404, detail="Season not found")

        # Return cached connection if available
        if season in self.season_db:
            return self.season_db[season][credentials.get("db_name")]

        # Create new connection
        logger.info("Creating new season sync client connection")
        season_client = self.get_client_uri(
            credentials.get("username"),
            credentials.get("password"),
            credentials.get("url"),
        )

        # Cache the connection
        college_id = master_data.get("college_id")
        if college_id not in self.season_db:
            self.season_db[college_id] = {}

        self.season_db[college_id][season] = season_client
        self._season_client = season_client
        self._season_database = season_client[credentials.get("db_name")]

        return self._season_database

    def reset_connections(self) -> 'PyMongoBase':
        """Reset all database connections and return self for chaining."""
        self._master_database = None
        self._season_database = None
        self._season_client = None
        return self


# Global connection manager instance
pymongo_base = PyMongoBase()


class DatabaseConnectionManager:
    """
    Provides managed access to season-specific database connections.
    Handles connection caching and reuse.
    """

    def __init__(self):
        """Initialize with current season credentials."""
        self.master_data = MotorBaseSingleton.get_instance().master_data
        self.season = self.master_data.get("current_season")
        self.credentials = pymongo_base.get_season_credentials()

    def get_client(self) -> Database:
        """
        Get or create a season database client.

        Returns:
            Database instance for the current season
        """
        college_id = self.master_data.get("college_id", "")

        # Create new connection if none exists
        if not pymongo_base.season_db.get(college_id, {}).get(self.season):
            pymongo_base.get_season_connection()

        return pymongo_base.season_db[college_id][self.season][
            self.credentials.get("db_name")
        ]


class DatabaseConfigurationSync:
    """
    Contain database configuration
    """

    def __init__(self, database=None):
        """
        Initialize the master database and season database
        """
        self.database = database
        if self.database == "master":
            self.master_database = pymongo_base.create_client_with_master()
        else:
            self.season_database = DatabaseConnectionManager().get_client()
        self.initialize()

    def initialize(self):
        """
        Initialize the database configuration base on master and None
        """
        if self.database == "master":
            self.user_collection = self.master_database.users
            self.client_collection = self.master_database.client_configurations
            self.college_collection = self.master_database.colleges
            self.user_audit_collection = self.master_database.user_audit_log
            self.college_form_details = self.master_database.application_form_details
            self.extra_limit_ip_collection = self.master_database.extra_limit_ip_addresses
            self.role_collection = self.master_database.roles
            self.template_merge_fields_collection = (
                self.master_database.template_merge_fields
            )
            self.refresh_token_collection = self.master_database.refreshToken
            self.country_collection = self.master_database.countries
            self.state_collection = self.master_database.states
            self.city_collection = self.master_database.cities
            self.provider_collection = self.master_database.providers
            self.cache_invalidations = self.master_database.cache_invalidations
        else:
            self.course_collection = self.season_database.courses
            self.studentApplicationForms = self.season_database.studentApplicationForms
            self.comments_collection = self.season_database.query_comments
            self.studentsPrimaryDetails = self.season_database.studentsPrimaryDetails
            self.studentSecondaryDetails = self.season_database.studentSecondaryDetails
            self.payment_collection = self.season_database.payments
            self.studentTimeline = self.season_database.studentTimeline
            self.queryCategories = self.season_database.queryCategories
            self.queries = self.season_database.queries
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
            self.automation_activity_collection = (
                self.season_database.automation_activity
            )
            self.activity_download_request_collection = (
                self.season_database.activity_download_request
            )
            self.user_timeline_collection = self.season_database.userTimeline
            self.lead_upload_history = self.season_database.leadUploadHistory
            self.whatsapp_sms_activity = self.season_database.whatsapp_sms_activity
            self.otp_template_collection = self.season_database.otpTemplates
            self.component_charges_collection = self.season_database.componentCharges
            self.form_details_collection = self.season_database.formDetails
            self.health_science_courses_collection = (
                self.season_database.healthScienceCourses
            )
            self.event_collection = self.season_database.events
            self.field_mapping_collection = self.season_database.FieldMapping
            self.data_segment_mapping_collection = (
                self.season_database.data_segment_student_mapping
            )
            self.scholarship_collection = self.season_database.scholarships
            self.offer_letter_list_collection = self.season_database.offerLetterlist
