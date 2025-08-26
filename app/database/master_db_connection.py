"""
connection with master database
"""
import time
from pathlib import Path, PurePath
from time import sleep

import certifi
import tomli as tomllib
from bson import ObjectId
from fastapi.exceptions import HTTPException
from pymongo import MongoClient
from pymongo.errors import NetworkTimeout, ConnectionFailure

from app.core.log_config import get_logger

logger = get_logger(__file__)

data = {
    "client_id": ObjectId(),
    "client_name": "dummy collection",
    "addrss": {
        "address line 2": "Lorem",
        "address line 1": "Lorem",
        "City": "Lorem",
        "State": "Lorem",
        "country": "Lorem"
    },
    "websiteUrl": "./resource.txt#frag01",
    "POCs": {},
    "subscriptions": {
        "rawDataModule": True,
        "Lead Management System": True,
        "Application Management System": True
    },
    "enforcements": {
        "leadLimit": -53,
        "counselorLimit": -63,
        "clientManagerLimit": 45,
        "publisherAccountLimit": 68
    },
    "leads": {
        "verificationType": "'OTP'",
        "leadAPIEnabled": True
    },
    "numberOfForms": 67,
    "integrations": {
        "withERP": False,
        "with3rdPartyApp": True,
        "with3rdPartyTelephony": True
    },
    "statusInfo": {
        "isActivated": True,
        "activationDate": {
            "$date": "2016-04-08T15:06:21.595Z"
        },
        "deActivationDate": {
            "$date": "2016-04-08T15:06:21.595Z"
        },
        "creationDate": {
            "$date": "2016-04-08T15:06:21.595Z"
        }
    },
    "chargesPerRelease": {
        "forSMS": -93,
        "forEmail": 10
    },
    "clientManagerName": {
        "client1": "Lorem"
    },
    "lead_stage_label": {
        "Not Interested": [
            "Already Enrolled Somewhere Else",
            "Fee Too High",
            "Desired Course Not Available",
            "Accommodation Issues",
            "Migration Issues",
            "Transportation Issues",
            "Did Not Disclose",
            "Financial Aid Not Available"
        ],
        "Interested": [
            "Need a campus visit physically",
            "Need virtual campus tour",
            "Need Faculty Interaction",
            "Need more Information"
        ],
        "checking": [
            "sound check"
        ]
    },
    "current_season": "season0",
    "seasons": [
        {
            "season_id": "season1",
            "season_name": "2023-2024",
            "start_date": "2023-01-01",
            "end_date": "2023-12-30",
            "database": {
                "username": "*************",
                "password": "**************",
                "url": "****************",
                "db_name": "*********"
            }
        },
        {
            "season_id": "season0",
            "season_name": "2022-2023",
            "start_date": "2022-01-01",
            "end_date": "2023-12-30",
            "database": {
                "username": "devseason1",
                "password": "TQvir95SBVQoV1hp",
                "url": "season1.qye7wal.mongodb.net",
                "db_name": "dummy"
            }
        }
    ],
    "s3": {
        "username": "************",
        "aws_access_key_id": "**************",
        "aws_secret_access_key": "*****************",
        "region_name": "ap-south-1",
        "assets_bucket_name": "**************",
        "reports_bucket_name": "*************",
        "public_bucket_name": "*********************",
        "student_documents_name": "*************************",
        "assets_base_url": "*************************************",
        "reports_base_url": "************************************",
        "public_base_url": "**********************",
        "student_documents_base_url": "*************************",
        "report_folder_name": "***********"
    },
    "email": {
        "payload_username": "*******",
        "payload_password": "*******",
        "payload_from": "************"
    },
    "collpoll": {
        "aws_access_key_id": "*****************",
        "aws_secret_access_key": "************",
        "region_name": "ap-south-1",
        "s3_bucket_name": "*************",
        "collpoll_url": "***********************************",
        "collpoll_auth_security_key": "****************"
    },
    "sms": {
        "username_trans": "************",
        "username_pro": "**********",
        "password": "*****",
        "authorization": "*****************",
        "sms_send_to_prefix": "91"
    },
    "razorpay": {
        "razorpay_api_key": "**********",
        "razorpay_secret": "***************",
        "razorpay_webhook_secret": "*************",
        "partner": False
    },
    "meilisearch": {
        "meili_server_host": "http://4.240.89.193:7700/",
        "meili_server_master_key": "X69XAC3RPvIIbw85rkUhamMutEf-va0N-3yCoMWcBeQ"
    },
    "report_webhook_api_key": "*****"
}

college_data_temp = {
    "name": "dummy collection",
    "current_season": "season0",
    "seasons": [
        {
            "season_id": "season1",
            "season_name": "2023-2024",
            "start_date": "2023-01-01",
            "end_date": "2023-12-30",
            "database": {
                "username": "*************",
                "password": "**************",
                "url": "****************",
                "db_name": "*********"
            }
        },
        {
            "season_id": "season0",
            "season_name": "2022-2023",
            "start_date": "2022-01-01",
            "end_date": "2023-12-30",
            "database": {
                "username": "devseason1",
                "password": "TQvir95SBVQoV1hp",
                "url": "season1.qye7wal.mongodb.net",
                "db_name": "dummy"
            }
        }
    ],
}


class GetPathInfo:
    """A class to get TOML file data."""

    @classmethod
    def from_toml(cls):
        """
        Read the TOML file and return its contents as a dictionary.

        Returns:
            dict: The contents of the TOML file.

        Raises:
            HTTPException: If the TOML file has a wrong format.
            HTTPException: If the TOML file is not found.
        """
        toml_dict = {}
        try:
            with open(str(cls.get_toml_file_path()), "rb") as toml:
                toml_dict = tomllib.load(toml)
        except tomllib.TOMLDecodeError:
            raise HTTPException(status_code=403, detail="TOML file has wrong"
                                                        " format!")
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=f"File not found! {e}")
        return toml_dict

    @classmethod
    def get_toml_file_path(cls):
        """
        Get the full path of the TOML file.

        Returns:
            PurePath: The full path of the TOML file.
        """
        path = Path(__file__).parent.parent.parent
        toml_file_path = PurePath(path, Path("config.toml"))
        return toml_file_path


toml_data = GetPathInfo().from_toml()


class CreateConnection:
    """
    Create a connection with master database client
    """

    def __init__(self):
        self.db_username = toml_data.get("master_db", {}).get("db_username")
        self.db_password = toml_data.get("master_db", {}).get("db_password")
        self.db_url = toml_data.get("master_db", {}).get("db_url")
        self.max_pool_size = toml_data.get("pool_db", {}).get("max_pool_size",
                                                              100)
        self.min_pool_size = toml_data.get("pool_db", {}).get("min_pool_size",
                                                              0)
        self.client = None

    def create_mongo_client(self, uri, max_retries=3, retry_delay=2):
        """
        Create a MongoDB client with retry logic.

        :param uri: MongoDB's connection URI.
        :param max_retries: Maximum number of retry attempts.
        :param retry_delay: Delay between retries in seconds.
        :return: MongoDB client instance.
        """
        retries = 0

        while retries < max_retries:
            try:
                _client = MongoClient(
                    uri, ssl=True, tlsCAFile=certifi.where(),
                    maxPoolSize=self.max_pool_size,
                    minPoolSize=self.min_pool_size,
                    serverSelectionTimeoutMS=20000
                )
                return _client
            except (NetworkTimeout, ConnectionFailure) as e:
                logger.warning(f"Sync Connection attempt {retries + 1} failed: {e}")
                retries += 1
                time.sleep(retry_delay)
            except Exception as error:
                logger.error(f"Failed to connect to MongoDB {error}")
                raise HTTPException(status_code=502,
                                    detail=f"Failed to connect"
                                           f" to MongoDB {error}")

        # Raise an exception if all retries fail
        raise HTTPException(status_code=502,
                            detail="Failed to connect to MongoDB "
                                   "after multiple attempts")

    def create_client_database(self):
        """create client database instance"""
        mongodb_connection = f"mongodb+srv://{self.db_username}:{self.db_password}@{self.db_url}/?retryWrites=true&w" \
                             f"=majority"
        logger.info("Creating master client database instance for singleton")
        self.client = self.create_mongo_client(uri=mongodb_connection)
        return self.client

    @property
    def get_master_db(self):
        if self.client is None:
            self.client = self.create_client_database()
        try:
            yield self.client
        finally:
            sleep(1)


singleton_client = next(CreateConnection().get_master_db)


class Master_db:
    """connection with master db using pymondo"""

    def __init__(self, college_id=None, db_name=None):
        """instance of master db connection"""
        self.college_id = college_id
        self.custom_db_name = db_name
        self.db_name = toml_data.get("master_db", {}).get("db_name")
        self.master_data = self.get_data_from_master_db()

    def get_data_from_master_db(self):
        """Connect with master database using pymongo."""
        client = singleton_client
        database = client.get_database(self.custom_db_name or self.db_name)
        college_collection = database.colleges
        client_collection = database.client_configurations

        if self.college_id is None:
            self.get_college_id(college_collection, client_collection)

        master_data = college_collection.find_one(
            {"_id": ObjectId(self.college_id)})
        client_data = client_collection.find_one({"college_ids": {
            "$in": [ObjectId(self.college_id)]}})
        if master_data is None:
            raise HTTPException(status_code=404, detail="College not found")
        if client_data is None:
            client_data = {}
        seasons = client_data.get("seasons", [])
        current_season = client_data.get("current_season")
        check_data = False
        if not master_data.get("seasons", []):
            master_data["seasons"] = seasons
            check_data = True
        if not master_data.get("current_season"):
            master_data["current_season"] = current_season
            check_data = True
        if check_data:
            college_collection.update_one({"_id": ObjectId(self.college_id)},
                                          {"$set": {
                                              "seasons": seasons,
                                              "current_season": current_season}})
        master_data.update(client_data)
        master_data["college_id"] = str(self.college_id)
        return master_data

    def get_college_id(self, college_collection, client_collection):
        """
        check the college id
        if not found create custom college
        """
        if (college_data := college_collection.find_one({"name": "dummy collection"})
        ) is None:
            if (college_collection.insert_one(college_data_temp)) is None:
                raise HTTPException(status_code=422,
                                    detail="college data is not inserted")
            college_data = college_collection.find_one(
                {"name": "dummy collection"})
        if (dummy_data := client_collection.find_one(
                {"client_name": "dummy collection"})) is None:
            data["college_ids"] = [college_data.get("_id")]
            if (data_insert := client_collection.insert_one(data)) is None:
                raise HTTPException(status_code=422,
                                    detail="data is not inserted")
        client_collection.update_one({"client_name": "dummy collection"},
                                     {"$set": {"college_ids": [
                                         college_data.get("_id")]}})
        self.college_id = college_data.get("_id")
