"""
no authentication required for this request object and will be ignored
"""

import certifi
from bson import ObjectId
from fastapi.exceptions import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.log_config import get_logger
from app.core.utils import settings
from app.database.database_sync import DatabaseConfigurationSync

logger = get_logger(__name__)


class DatabaseConnection:

    def __init__(self, _id=None):
        """
        Initialize the college id, master_client and season_client
        """
        self.id = _id
        self.master_client = None
        self.season_client = {}
        self.season = None

    def get_url(self, db_username, db_password, db_url):
        """return url of the database"""
        return f"mongodb+srv://{db_username}:{db_password}@{db_url}/?retryWrites=true&w=majority"

    def get_season_db(self, all_season, season=None):
        """
        check the season_id in given season from a list
         of all available seasons.
        """
        return next((data.get("database") for data in all_season if
                     data.get("season_id") == season), {})

    def get_credential_season(self, college_id=None):
        """
        Get the credential of the season base on season id

        Return:-
            A dictionary containing the credential of the season database
        """
        if college_id is not None:
            if self.id != college_id:
                self.id = college_id
        master_data = DatabaseConfigurationSync(
            'master').college_collection.find_one(
            {"_id": ObjectId(self.id)})
        self.season = master_data.get("current_season")
        credential = self.get_season_db(master_data.get("seasons", []),
                                        season=self.season)
        if len(credential) < 1:
            raise HTTPException(status_code=404,
                                detail=f"{self.season} not found in our system")
        return credential

    def helper_seasons(self, college_id):
        """
        Connection with season database and check the connection
         is already exist or not if not then create new connection and save in
          the season_client

        Return:-
            instance of season client
        """
        self.id = college_id
        credential = self.get_credential_season()
        if self.season_client.get(self.id, {}).get(self.season) is not None:
            return self.season_client.get(self.id, {}).get(
                self.season)[credential.get("db_name")]
        season_uri = self.get_url(credential.get("username"),
                                  credential.get("password"),
                                  credential.get("url"))
        logger.info("create season connection to course"
                    " fetch no auth credentials")
        try:
            season_client = AsyncIOMotorClient(season_uri, ssl=True,
                                               tlsCAFile=certifi.where())
        except Exception as error:
            logger.error(f"Error connecting to season MongoDB using"
                         f" motor async: {error}")
        if self.season_client.get(self.id) is not None:
            self.season_client.get(self.id, {}).update(
                {self.season: season_client})
        else:
            self.season_client.update({self.id: {self.season: season_client}})
        logger.info("Creating no_auth_connection client"
                    " database instance using async")
        return self.season_client.get(self.id, {}).get(
            self.season)[credential.get("db_name")]

    def connection_with_season(self, college_id):
        """connection with season database"""
        return self.helper_seasons(college_id=college_id)

    def client_md(self):
        """
        Get client object which useful when run test cases.
        """
        if self.master_client is None:
            logger.info("Create client md connection for test cases")
            master_uri = self.get_url(settings.db_username,
                                      settings.db_password, settings.db_url)
            try:
                self.master_client = AsyncIOMotorClient(
                    master_uri, ssl=True, tlsCAFile=certifi.where(),
                    maxPoolSize=settings.max_pool_size,
                    minPoolSize=settings.min_pool_size)
            except Exception as error:
                logger.error(f"Error connecting to master MongoDB using"
                             f" motor async for test db: {error}")
        return self.master_client


motor_base_no_auth = DatabaseConnection()


class create_connection:
    """
    Create a connection with season wise
    """

    def __init__(self, college_id):
        """
        Initialize the college id
        """
        self.college_id = college_id

    def get_client(self):
        """
        Get the instance of the season connection database
        """
        return motor_base_no_auth.connection_with_season(self.college_id)


class NoAuthDatabaseConfiguration:
    """
    Get the season database connection configuration
    Initialize the collections
    """

    def __init__(self, college_id):
        """
        Initialize the season database connection configuration and college id
        """
        self.college_id = college_id
        self.season = create_connection(college_id).get_client()
        self.initialize()

    def initialize(self):
        """
        Initialize the season database connection with collections
        """
        self.course_collection = self.season.courses
        self.health_science_courses_collection = self.season.healthScienceCourses
