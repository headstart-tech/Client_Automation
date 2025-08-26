import asyncio
import datetime
import time
from contextlib import asynccontextmanager
from pathlib import Path, PurePath
from typing import Optional, Generator

import certifi
import toml
from fastapi.exceptions import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import NetworkTimeout, ConnectionFailure
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.background_task_logging import background_task_wrapper
from app.core.log_config import get_logger
from app.core.utils import settings
from app.database.motor_base_singleton import MotorBaseSingleton

path = Path(__file__).parent.parent.parent
path = PurePath(path, Path("config.toml"))
toml_data = toml.load(str(path))

logger = get_logger(__name__)

# Constants
COLLECTION_NAMES = [
    "courses", "studentsPrimaryDetails", "loginActivity", "master_screens",
    "studentSecondaryDetails", "studentApplicationForms", "studentTimeline",
    "lead_details", "leadsFollowUp", "payments", "counselor_management",
    "tag_list", "queries", "queryCategories", "boardDetails", "templates",
    "activity_email", "application_payment_invoices", "reports", "raw_data",
    "meeting", "exam_schedules", "template_gallery", "promocode", "questions",
    "activity_download_request", "checkInOutLog", "offline_data",
    "notifications", "sms_template", "sms_activity", "automation", "campaign",
    "campaign_rule", "rule", "automation_activity", "otpTemplates",
    "componentCharges", "call_activity", "healthScienceCourses", "events",
    "interviewSelectionProcedure", "interviewLists", "panels", "slots",
    "vouchers", "userUpdates", "scripts", "users", "colleges", "refreshToken",
    "dataSegment", "advanceFilterFields", "template_merge_fields",
    "scholarships", "application_form_details", "client_stages", "stages", "reportFields",
    "custom_fields", "client_sub_stages", "college_course_details",
    "approvals", "approval_requested_data"
]

MASTER_COLLECTIONS = [
    "users", "refreshToken", "colleges", "application_form_details",
    "master_screens", "advanceFilterFields", "template_merge_fields",
    "client_stages", "stages", "reportFields", "custom_fields", "client_sub_stages",
    "college_course_details", "approvals", "approval_requested_data"
]


class MotorBase:
    """
        Manages MongoDB connections with connection pooling and retry logic.

        Attributes:
            master_db: Master database instance
            client: MongoDB client instance
            test_db: Name of test database if in testing mode
            season: Current season identifier
            season_db: Dictionary of season-specific database connections
            collection_name: List of all collection names
            master_collection: List of master collection names
    """

    def __init__(self, season: Optional[str] = None, test_db: Optional[str] = None):
        """
        Initialize MongoDB connection manager.

        Args:
            season: Season identifier (optional)
            test_db: Test database name (optional)
        """
        self.master_db = MotorBaseSingleton.get_instance().master_data
        self.client = None
        self.test_db = test_db
        self.season = season
        self._master_database = None
        self._season_database = None
        self.season_db = {}
        self._season_client = None

        # Set event loop based on testing mode
        self.loop = (asyncio.get_running_loop() if toml_data["testing"]["test"]
                     else asyncio.get_event_loop())

        if toml_data["testing"]["test"]:
            self.test_db = "test"

        self.collection_name = COLLECTION_NAMES
        self.master_collection = MASTER_COLLECTIONS

    def create_mongo_client(self, uri: str, max_retries: int = 3,
                            retry_delay: int = 2) -> AsyncIOMotorClient:
        """
        Create MongoDB client with retry logic.

        Args:
            uri: MongoDB connection URI
            max_retries: Maximum connection attempts
            retry_delay: Delay between retries in seconds

        Returns:
            AsyncIOMotorClient instance

        Raises:
            HTTPException: If connection fails after retries
        """
        for retry in range(max_retries):
            try:
                return AsyncIOMotorClient(
                    uri,
                    ssl=True,
                    tlsCAFile=certifi.where(),
                    maxPoolSize=settings.max_pool_size,
                    minPoolSize=settings.min_pool_size,
                    serverSelectionTimeoutMS=20000
                )
            except (NetworkTimeout, ConnectionFailure) as e:
                logger.warning(f"Connection attempt {retry + 1} failed: {e}")
                if retry < max_retries - 1:
                    time.sleep(retry_delay)
            except Exception as error:
                logger.error(f"Failed to connect to MongoDB: {error}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to connect to MongoDB: {error}"
                )

        raise HTTPException(
            status_code=502,
            detail="Failed to connect to MongoDB after multiple attempts"
        )

    def _get_connection_url(self, username: str, password: str, host: str) -> str:
        """
        Construct MongoDB connection URL.

        Args:
            username: Database username
            password: Database password
            host: Database host URL

        Returns:
            Formatted MongoDB connection string
        """
        return f"mongodb+srv://{username}:{password}@{host}/?retryWrites=true&w=majority"

    def get_season_db(self, all_seasons: list, season: Optional[str] = None) -> dict:
        """
        Get season database credentials from all available seasons.

        Args:
            all_seasons: List of all available seasons
            season: Season identifier to look for

        Returns:
            Dictionary of season database credentials
        """
        return next(
            (data.get("database", {})
             for data in all_seasons
             if data.get("season_id") == season), {}
        )

    def get_season_credentials(self, season: Optional[str] = None) -> dict:
        """
        Get credentials for a specific season.

        Args:
            season: Season identifier (uses current season if None)

        Returns:
            Dictionary of season credentials

        Raises:
            HTTPException: If season is not found
        """
        if self.master_db is None:
            self.master_db = MotorBaseSingleton.get_instance().master_data

        self.season = season or self.master_db.get("current_season")
        credentials = self.get_season_db(
            self.master_db.get("seasons", []),
            season=self.season
        )

        if not credentials:
            raise HTTPException(
                status_code=404,
                detail=f"{self.season} not found in our system"
            )

        return credentials

    def connect_season_db(self, season_name: Optional[str] = None) -> AsyncIOMotorDatabase:
        """
        Connect to a season-specific database.

        Args:
            season_name: Season identifier

        Returns:
            AsyncIOMotorDatabase instance for the season
        """
        credentials = self.get_season_credentials(season_name)
        season_uri = self._get_connection_url(
            credentials.get("username"),
            credentials.get("password"),
            credentials.get("url")
        )

        season_client = self.create_mongo_client(uri=season_uri)
        logger.info("Creating season client database instance")

        season_name = season_name or self.master_db.get("current_season")
        self._season_client = season_client

        db_name = self.test_db or credentials.get("db_name")
        self._season_database = season_client[db_name]

        # Cache the connection
        college_id = self.master_db.get("college_id")
        if college_id not in self.season_db:
            self.season_db[college_id] = {}

        self.season_db[college_id][season_name] = season_client
        return self._season_database

    def connect_master_db(self) -> AsyncIOMotorClient:
        """Connect to the master database and return the client."""
        if self.client is None:
            uri = self._get_connection_url(
                settings.db_username,
                settings.db_password,
                settings.db_url
            )
            self.client = self.create_mongo_client(uri=uri)
            logger.info("Creating master client instance")

        db_name = self.test_db or settings.db_name
        self._master_database = self.client[db_name]
        return self.client

    def connect(self) -> None:
        """Establish connections to both master and season databases."""
        self.connect_master_db()
        self.connect_season_db()

    def reset_connections(self) -> None:
        """Reset all database connections."""
        self.master_db = None
        self._master_database = None
        self._season_database = None
        self._season_client = None

    def clear_season_cache(self) -> None:
        """Clear all cached season database connections."""
        self.season_db = {}

    @property
    def master_database(self) -> Generator[AsyncIOMotorDatabase, None, None]:
        """
        Get master database instance with connection management.

        Yields:
            AsyncIOMotorDatabase instance

        Note:
            Automatically handles connection cleanup
        """
        if self._master_database is None:
            self.connect_master_db()

        try:
            yield self._master_database
        finally:
            time.sleep(1)  # Allow time for operations to complete

    @property
    def season_database(self, reset: bool = False) -> Generator[AsyncIOMotorDatabase, None, None]:
        """
        Get season database instance with connection management.

        Args:
            reset: Whether to force a new connection

        Yields:
            AsyncIOMotorDatabase instance

        Note:
            Automatically handles connection cleanup
        """
        if reset:
            self._season_database = None

        if self._season_database is None:
            self._season_database = self.connect_season_db()

        try:
            yield self._season_database
        finally:
            time.sleep(1)  # Allow time for operations to complete


async def init_databases():
    """
    Initialization of the database connection class on startup
    """
    motor_base = MotorBase()
    return motor_base


# Initialize database connection based on environment
motor_base = MotorBase(
    test_db="test" if toml_data["testing"]["test"] else None
)
master_database = next(motor_base.master_database)
season_database = next(motor_base.season_database)
client = motor_base.client


class ConnectionCleanup:
    """
    Manages cleanup of unused database connections.

    Automatically removes connections that haven't been used for 2 days.
    """

    def __init__(self, connection_manager: motor_base):
        """
        Initialize with a connection manager instance.

        Args:
            connection_manager: MongoDBConnectionManager instance
        """
        self.connection_manager = connection_manager

    @background_task_wrapper
    async def cleanup_unused_connections(self) -> None:
        """
        Remove unused database connections older than 2 days.

        Runs as a background task to periodically clean up connections.
        """
        season_db = self.connection_manager.season_db
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=2)

        for college_id, connections in season_db.items():
            for key in list(connections.keys()):
                if "_datetime" in key:
                    last_used = connections.get(key)
                    if isinstance(last_used, datetime.datetime) and last_used < cutoff_date:
                        connection_key = key.replace("_datetime", "")
                        connection = connections.get(connection_key)

                        if connection:
                            try:
                                await connection.close()
                                connections.pop(connection_key, None)
                                connections.pop(key, None)
                                logger.info(f"Closed unused connection: {connection_key}")
                            except Exception as e:
                                logger.warning(f"Error closing connection {connection_key}: {e}")


class SeasonConnectionManager:
    """
    Manages season-specific database connections with caching.
    """
    _instances = set()  # Track all instances of this class

    def __init__(self, season: Optional[str] = None):
        """
        Initialize with optional season identifier.

        Args:
            season: Season identifier (uses current season if None)
        """
        self._initialize_connection(season)
        self.__class__._instances.add(self)  # Register this instance

    def __del__(self):
        """Clean up when instance is destroyed"""
        self.__class__._instances.discard(self)

    def _initialize_connection(self, season: Optional[str] = None) -> None:
        """Helper method to initialize or reinitialize connection"""
        self.master_data = motor_base.master_db
        if self.master_data is None:
            self.master_data = MotorBaseSingleton.get_instance().master_data
        self.season = season or self.master_data.get("current_season")
        self.credentials = motor_base.get_season_credentials(self.season)

    @classmethod
    def reset_all_connections(cls) -> None:
        """
        Class method to reset ALL connections across ALL instances.
        Also clears the motor_base cache.
        """
        # Then reset all instances
        for instance in cls._instances:
            instance.reset_connection()
            instance._initialize_connection(instance.season)  # Reinitialize with same season

    def reset_connection(self) -> None:
        """
        Reset this instance's database connections.
        """
        self.master_data = None
        self.season = None
        self.credentials = None

    def get_db_client(self) -> AsyncIOMotorDatabase:
        """
        Get or create a database client for the season.

        Returns:
            AsyncIOMotorDatabase instance
        """
        college_id = self.master_data.get("college_id", "")
        season_connections = motor_base.season_db.get(college_id, {})

        if self.season not in season_connections:
            motor_base.connect_season_db(season_name=self.season)
            season_connections = motor_base.season_db[college_id]

        # Update last used timestamp
        season_connections[f"{self.season}_datetime"] = datetime.datetime.now()

        try:
            return season_connections[self.season][self.credentials.get("db_name")]
        except (AttributeError, KeyError):
            logger.warning("Failed to get database - resetting connection")
            motor_base.clear_season_cache()
            motor_base.connect_season_db(season_name=self.season)
            return motor_base.season_db[college_id][self.season]


class PostgresConnection:
    def __init__(self):
        """
        Initialize PostgreSQL connection parameters.
        """
        self.database_url = (
            f"postgresql+asyncpg://{settings.pgsql_username}:{settings.pgsql_password}@{settings.pgsql_host}:"
            f"{settings.pgsql_port}/{settings.pgsql_name}")

        if settings.environment in ["demo"] or toml_data["testing"]["test"]:
            parts = self.database_url.split("/")
            parts[-1] = "test"
            self.database_url = "/".join(parts)

        self.engine_generate = create_async_engine(
            self.database_url, pool_size=10, max_overflow=5,
            pool_timeout=30, pool_recycle=3600, pool_pre_ping=True,
            echo=True)

        self.async_session = async_sessionmaker(
            self.engine_generate, class_=AsyncSession, expire_on_commit=False)

    @asynccontextmanager
    async def get_sqlalchemy_session(self):
        """
        Provides an asynchronous session for FastAPI dependency injection.
        """
        async with self.async_session() as session:
            try:
                logger.info("Establishing PostgreSQL connection")
                yield session
                await session.commit()
                logger.info("PostgreSQL connection created successfully")
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    async def get_db_session(self) -> AsyncSession:
        """
        Returns an asynchronous session for manual use in normal functions.
        The caller is responsible for closing the session.
        """
        try:
            return self.async_session()
        except Exception as e:
            logger.error(f"Failed to create PostgresSQL session: {e}")
            raise


pgsql_conn = PostgresConnection()
