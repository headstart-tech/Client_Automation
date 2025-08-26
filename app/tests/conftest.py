"""
This file contains methods/fixture which are useful for run test cases,
 this will automatically execute when any test case start to execute
"""

import asyncio
import random
import time
import uuid
from datetime import timedelta, datetime
from pathlib import Path, PurePath
from typing import AsyncIterable, Iterator

import httpx
import pytest
import toml
from bson import ObjectId
from fastapi import FastAPI
from kombu.exceptions import KombuError
from sqlalchemy import text

from app.core.log_config import get_logger
from app.core.utils import settings
from app.database.upload_test_db_data import Upload_file
from app.dependencies.hashing import Hash
from app.dependencies.jwttoken import Authentication

path = Path(__file__).parent.parent.parent
path = PurePath(path, Path("config.toml"))
toml_data = toml.load(str(path))

# Modify field
toml_data["testing"]["test"] = True  # Generic item from example you posted

# To use the dump function, you need to open the file in 'write' mode
# It did not work if I just specify file location like in load
with open(str(path), "w") as f:
    toml.dump(toml_data, f)

REDIS_HASH_NAME = "testing_tokens"
TOKEN_EXPIRY_SECONDS = 3600

logger = get_logger(name=__name__)

"""
logging info message color change
https://docs.pytest.org/en/7.1.x/how-to/logging.html for more logging reference
 plz visit this
"""


# Do not change the position of event loop
@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    """
    Reference: https://github.com/pytest-dev/pytest-asyncio/issues/38
    #issuecomment-264418154

    Create an instance of the default event loop for each test case.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
async def fastapi_app():
    """
    Return an object of class FastAPI
    """
    from app.routers.api_v1.app import app

    return app


@pytest.fixture
async def http_client_test(fastapi_app: FastAPI) -> AsyncIterable[httpx.AsyncClient]:
    """Return client object for testing"""
    async with httpx.AsyncClient(
            app=fastapi_app,
            base_url="http://test",
    ) as client:
        yield client


@pytest.fixture(scope="session")
async def connection_with_test_db():
    """connection with test season db"""
    from app.database.no_auth_connection_db import DatabaseConnection
    from app.core.reset_credentials import Reset_the_settings

    client_md = DatabaseConnection().client_md()
    master_database = client_md["test"]
    col = master_database["client_configurations"]

    time.sleep(2)
    logger.warning("---------------Connection with test DB started------------------")
    db_col_data = await col.find_one({"client_name": "Test"})
    if db_col_data is None:
        raise ValueError("Client not found")
    logger.info(f"--------Test DB connection established----------{str(db_col_data.get('_id'))}")
    logger.info(f"Client Id with test DB {str(db_col_data.get('client_id'))}")
    college_collection = master_database["colleges"]
    college_data = await college_collection.insert_one(
        {"seasons": db_col_data.get("seasons", []),
         "current_season": db_col_data.get("current_season")})
    college_id = college_data.inserted_id
    await col.update_one({"client_name": "Test"},
                         {"$set": {"college_ids": [ObjectId(college_id)]}})
    Reset_the_settings().get_user_database(
        college_id=str(college_id), form_data=None, db_name="test"
    )


@pytest.fixture(scope="session")
async def setup_module(connection_with_test_db):
    """
    Setup Module for Test cases
    Checks advisory_flag is ture then only test cases will run
    Set advisory_flag: true if executing test cases , Once completed it will
     set advisory:False
    Setup test database, upload data into test DB collections before
     test cases run and delete collections
    after test cases run successfully"""
    from app.database.motor_base import master_database, MotorBase
    from app.database.configuration import DatabaseConfiguration
    from app.core.reset_credentials import Reset_the_settings
    season_database = DatabaseConfiguration().season_database
    advisory_flag = master_database.advisory_check
    client_collection = master_database.client_configurations
    flag = True
    while flag:
        if (check_flag := await advisory_flag.find_one({"flag": False})) is not None:
            flag = False
            await advisory_flag.update_one(
                {"_id": check_flag.get("_id")}, {"$set": {"flag": True}}
            )
        else:
            logger.info(
                "---------------Testcase already running,"
                " Please wait 2 minutes------------------"
            )
            time.sleep(120)
    Upload_file().upload_data(master_database, season_database)

    logger.info("------------------Setup Module Started------------------\n")
    collection = MotorBase().collection_name
    client_details = await client_collection.find_one({"client_name": "Test"})
    if not client_details:
        raise ValueError("Client not found")
    Reset_the_settings().get_user_database(
        college_id=str(client_details.get("college_ids", [""])[0]), form_data=None, db_name="test"
    )
    time.sleep(30)
    """ because when test case finished from another side await function 
    taking time for deleted collection"""
    yield
    logger.info("--------------Teardown Started---------")
    from app.database.motor_base import master_database as master
    from app.database.configuration import DatabaseConfiguration

    season = DatabaseConfiguration().season_database
    for i in collection:
        if i in MotorBase().master_collection:
            await master.drop_collection(i)
        else:
            await season.drop_collection(i)
    toml_data["testing"]["test"] = False
    with open(str(path), "w") as f:
        toml.dump(toml_data, f)
    await advisory_flag.update_one(
        {"_id": check_flag.get("_id")}, {"$set": {"flag": False}}
    )
    time.sleep(10)


@pytest.fixture
def test_student_data(test_course_validation, test_college_validation):
    """Return dummy data for create new student"""
    return {
        "email": "test@example.com",
        "password": "getmein",
        "full_name": "thara bhai joginder",
        "mobile_number": "1111111111",
        "course": test_course_validation.get("course_name"),
        "main_specialization": test_course_validation.get("course_specialization")[
            1
        ].get("spec_name"),
        "country_code": "IN",
        "state_code": "UP",
        "city": "Gorakhpur",
        "college_id": str(test_college_validation.get("_id")),
        "utm_source": "test",
        "utm_campaign": "test",
        "utm_keyword": "test",
        "utm_medium": "test",
        "referal_url": "",
    }


@pytest.fixture
async def test_source_data(test_student_validation, test_user_publisher_validation):
    """Return dummy data for create new source students data"""
    from app.database.configuration import DatabaseConfiguration

    data = {
        "primary_source": {
            "utm_source": "google",
            "utm_campaign": "google dummy",
            "utm_keyword": "dummy insert",
            "utm_medium": "reports",
            "referal_url": "www.shiftboolean.com",
            "utm_enq_date": {"$date": "2023-03-13T12:22:11.605Z"},
            "lead_type": "api",
            "publisher_id": test_user_publisher_validation.get("_id"),
        },
        "secondary_source": {
            "utm_source": "instagram",
            "utm_campaign": "secondary",
            "utm_keyword": "reports_secondray",
            "utm_medium": "www.shiftboolean.in",
            "referal_url": "www.shiftboolean.in",
            "utm_enq_date": {"$date": "2023-03-13T12:22:11.605Z"},
            "lead_type": "api",
            "publisher_id": test_student_validation.get("_id"),
        },
        "tertiary_source": {
            "utm_source": "instagram",
            "utm_campaign": "tertiary_source",
            "utm_keyword": "tertiary_source",
            "utm_medium": "tertiary_source",
            "referal_url": "tertiary_source",
            "utm_enq_date": {"$date": "2023-03-13T12:22:11.605Z"},
            "lead_type": "api",
            "publisher_id": test_user_publisher_validation.get("_id"),
        },
    }
    await DatabaseConfiguration().studentsPrimaryDetails.update_one(
        {"_id": test_student_validation.get("_id")}, {"$set": {"source": data}}
    )
    return data


@pytest.fixture
async def test_student_validation(test_student_data):
    """Return student data, it will create student in test DB collection
    if student not exist. Using test student data for create student."""
    from app.database.configuration import DatabaseConfiguration
    from app.helpers.student_curd.student_user_crud_configuration import (
        StudentUserCrudHelper,
    )

    student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": test_student_data["email"]}
    )
    if not student:
        await StudentUserCrudHelper().student_register(test_student_data)
    student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": test_student_data["email"]}
    )
    return student


@pytest.fixture
async def access_token(test_student_validation):
    """
    Get the access token of student which we can be used for authenticate
    student
    """
    from app.database.motor_base_singleton import MotorBaseSingleton

    master_data = MotorBaseSingleton.get_instance().master_data
    token = await Authentication().create_access_token(
        data={
            "sub": test_student_validation["user_name"],
            "scopes": ["student"],
            "college_info": [{"_id": str(master_data.get("college_id"))}],
        },
        expires_delta=timedelta(hours=1),
    )
    return token


@pytest.fixture
def test_student_basic_details(test_course_validation, test_student_validation):
    """Return dummy basic details of student for add student basic details"""
    return {
        "main_specialization": test_course_validation.get("course_specialization")[
            0
        ].get("spec_name"),
        "secondary_specialization": "",
        "first_name": test_student_validation.get("basic_details", {}).get(
            "first_name"
        ),
        "last_name": test_student_validation.get("basic_details", {}).get("last_name"),
        "middle_name": test_student_validation.get("basic_details", {}).get(
            "middle_name"
        ),
        "email": test_student_validation.get("basic_details", {}).get("email"),
        "mobile_number": test_student_validation.get("basic_details", {}).get(
            "mobile_number"
        ),
        "date_of_birth": "1996-02-01",
        "admission_year": "2022",
        "gender": "male",
        "nationality": "indian",
        "category": "BC",
        "para_ability": {"is_disable": "True", "name_of_disability": "string"},
    }


@pytest.fixture
def test_student_parent_details():
    """Return dummy student parent and guardian details for add student parent
    and guardian details"""
    return {
        "father_details": {
            "salutation": "string",
            "name": "string",
            "email": "user@example.com",
            "mobile_number": "string",
        },
        "mother_details": {
            "salutation": "string",
            "name": "string",
            "email": "user@example.com",
            "mobile_number": "string",
        },
        "guardian_details": {
            "salutation": "string",
            "name": "string",
            "email": "user@example.com",
            "mobile_number": "string",
            "occupation": "string",
            "designation": "string",
            "relationship_with_student": "string",
        },
        "family_annual_income": "string",
    }


@pytest.fixture
def test_student_address_details():
    """Return dummy student address details for add student address details"""
    return {
        "country_code": "IN",
        "state_code": "MH",
        "district": "Pune",
        "city": "Pune",
        "address_line1": "string",
        "address_line2": "string",
        "pincode": "417688",
        "is_permanent_address_same": True,
    }


@pytest.fixture
def test_student_education_details():
    """Return dummy student education details for add student education
    details"""
    return {
        "tenth_school_details": {
            "school_name": "string",
            "board": "string",
            "year_of_passing": "2017",
            "marking_scheme": "cgpa",
            "obtained_cgpa": "6.7",
            "tenth_registration_number": "765442",
            "tenth_subject_wise_details": {
                "english": "60",
                "maths": "60",
                "science": "70",
                "social_science": "80",
                "language": "60",
                "other_subject": "60",
            },
        },
        "inter_school_details": {
            "school_name": "string",
            "board": "string",
            "year_of_passing": "2019",
            "marking_scheme": "cgpa",
            "obtained_cgpa": "6.0",
            "stream": "science",
            "inter_registration_number": "54321",
            "appeared_for_jee": True,
            "inter_subject_wise_details": [
                {
                    "subject_name": "string",
                    "max_marks": "100",
                    "obtained_marks": "string",
                    "percentage": "string",
                    "month_of_year_passing": "2019",
                }
            ],
        },
    }


@pytest.fixture
async def create_query_categories(http_client_test):
    """
    Create query categories in the collection
    """
    from app.database.configuration import DatabaseConfiguration

    query_category = await DatabaseConfiguration().queryCategories.find_one({})
    if not query_category:
        await http_client_test.post("/create_query_categories/")


@pytest.fixture
async def query_details(
        test_student_validation,
        http_client_test,
        access_token,
        create_query_categories,
        test_course_validation,
):
    """
    Return query details
    """
    from app.database.configuration import DatabaseConfiguration
    feature_key = user_feature_data()
    query = await DatabaseConfiguration().queries.find_one(
        {"student_id": test_student_validation["_id"]}
    )
    if not query:
        await http_client_test.post(
            "/student_query/create/?title=test&category_name=General%20Query&"
            f"course_name={test_course_validation.get('course_name')}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    query = await DatabaseConfiguration().queries.find_one(
        {"student_id": test_student_validation["_id"]}
    )
    return query


@pytest.fixture
async def application_details(
        test_student_validation,
        test_counselor_validation,
        test_course_validation,
        test_user_validation,
):
    """
    Return application details
    """
    from app.database.configuration import DatabaseConfiguration
    from bson import ObjectId
    from app.core.utils import utility_obj

    application = await DatabaseConfiguration().studentApplicationForms.find_one(
        {"student_id": ObjectId(str(test_student_validation["_id"]))}
    )
    if application is None:
        await DatabaseConfiguration().studentApplicationForms.insert_one(
            {
                "spec_name1":
                    test_course_validation.get("course_specialization")[1][
                        "spec_name"
                    ],
                "spec_name2": "",
                "spec_name3": "",
                "student_id": ObjectId(str(test_student_validation["_id"])),
                "course_id": ObjectId(str(test_course_validation.get("_id"))),
                "college_id": ObjectId(
                    str(test_student_validation.get("college_id"))),
                "current_stage": 2,
                "dv_status": "To be verified",
                "declaration": False,
                "payment_initiated": True,
                "payment_info": {"payment_id": "", "order_id": "",
                                 "status": "captured"},
                "enquiry_date": datetime.utcnow(),
                "last_updated_time": datetime.utcnow(),
                "school_name": "School of Technology",
                "is_created_by_publisher": False,
                "is_created_by_user": False,
                "custom_application_id": None,
                "allocate_to_counselor": {
                    "counselor_id": ObjectId(
                        str(test_counselor_validation.get("_id"))),
                    "counselor_name": utility_obj.name_can(
                        test_counselor_validation),
                    "last_update": datetime.utcnow(),
                },
                "meetingDetails": {
                    "status": "Booked",
                    "zoom_link": "",
                    "slot_type": "",
                },
                "feedback": [
                    {
                        "interviewer_id": test_user_validation.get("_id"),
                        "scores": {"communication_skills": 9},
                        "status": "Accepted",
                        "comments": "good",
                    }
                ],
            }
        )
        application = await DatabaseConfiguration().studentApplicationForms.find_one(
            {"student_id": ObjectId(str(test_student_validation["_id"]))}
        )
    return application


@pytest.fixture
async def student_timeline(application_details):
    """
    Add student timeline, need of this fixture because background task taking
    time to create student timeline
    """
    from app.celery_tasks.celery_student_timeline import StudentActivity

    try:
        StudentActivity().student_timeline(
            str(application_details.get("student_id")),
            "Application",
            "Started",
            str(application_details.get("_id")),
            "BSc (Physician Assistant)",
        )
    except KombuError as celery_error:
        logger.error(f"error storing time line data {celery_error}")
    except Exception as error:
        logger.error(f"error storing time line data {error}")


@pytest.fixture
def test_user_data(test_college_validation):
    """Return dummy user details for create new user"""
    return {
        "email": "user25@example.com",
        "full_name": "string string string",
        "mobile_number": 7576756757,
        "associated_colleges": [str(test_college_validation.get("_id"))],
        "associated_client": str(test_college_validation.get("_id")),
    }


@pytest.fixture
def test_user_publisher_data(test_user_validation):
    """Return dummy user details for create new user"""
    return {
        "email": "user103@example.com",
        "full_name": "viru bhai",
        "mobile_number": 7576757757,
        "associated_colleges": [
            str(test_user_validation.get("associated_colleges")[0])
        ],
        "associated_source_value": "google",
    }


@pytest.fixture
async def test_user_validation(test_user_data):
    """Return user data, it will create user of type college_super_admin in
    test DB collection
    if user not exist. Using test user data for create student."""
    from app.database.configuration import DatabaseConfiguration
    from app.helpers.user_curd.user_configuration import UserHelper

    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": test_user_data["email"]}
    )
    if not user:
        await UserHelper().create_user(
            test_user_data, settings.superadmin_username, "college_super_admin"
        )
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": test_user_data["email"]}
    )
    return user


@pytest.fixture
async def test_user_publisher_validation(
        test_user_publisher_data, test_counselor_validation
):
    """Return user data, it will create user of type college_super_admin in
    test DB collection
    if user not exist. Using test user data for create student."""
    from app.database.configuration import DatabaseConfiguration
    from app.helpers.user_curd.user_configuration import UserHelper

    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": test_user_publisher_data["email"]}
    )
    if not user:
        await UserHelper().create_user(
            test_user_publisher_data,
            test_counselor_validation.get("user_name"),
            "college_publisher_console",
        )
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": test_user_publisher_data["email"]}
    )
    return user


@pytest.fixture
async def notification_details(test_user_validation):
    """
    Get notification details
    """
    from app.database.configuration import DatabaseConfiguration

    notification = await DatabaseConfiguration().notification_collection.find_one(
        {"send_to": test_user_validation.get("_id")}
    )
    if not notification:
        notification_details = (
            await DatabaseConfiguration().notification_collection.insert_one(
                {
                    "event_type": "Manual Assignment of Lead",
                    "send_to": ObjectId("63765877c9f6fb7624a72099"),
                    "student_id": ObjectId("64219a79a248477711149d68"),
                    "application_id": ObjectId("64219ad0a248477711149e3c"),
                    "message": "Lead is assigned <span class='notification-inner'>"
                               "Test User884</span> to you check here.",
                    "mark_as_read": False,
                    "event_datetime": {"$date": "2023-03-27T14:35:54.409Z"},
                    "created_at": {"$date": "2023-03-27T14:36:24.451Z"},
                }
            )
        )
        notification = await DatabaseConfiguration().notification_collection.find_one(
            {"_id": ObjectId(notification_details.inserted_id)}
        )
    return notification


async def create_user(role_name: str, role_id: int) -> dict:
    """
    Create a new user with a random email and password, and assigns a role if provided.

    Params:
        role_name (str): The name of the user's role (e.g., "Admin", "User").
        role_id (int): The ID of the user's role.

    Returns:
        dict: A dictionary representing the newly created user.

    Raises:
        Exception: If there is an issue inserting the user into the database.
    """
    from app.database.configuration import DatabaseConfiguration
    random_digits = random.randint(1000, 9999)
    random_contact = random.randint(7000000000, 9999000000)
    email = f"{role_name or 'user'}_{random_digits}@yopmail.com"
    password = Hash().get_password_hash("getmein")

    new_user = {
        "_id": ObjectId(),
        "email": email,
        "mobile_number": random_contact,
        "first_name": role_name or "User",
        "middle_name": "",
        "last_name": "",
        "password": password,
        "role": {
            "role_name": role_name,
            "role_id": role_id
        } if role_name and role_id else None,
        "is_activated": True,
        "last_accessed": datetime.utcnow(),
        "created_on": datetime.utcnow(),
        "user_name": email,
        "user_type": role_name or "user",
        "check_in_status": False,
        "status_active": False,
        "groups": []
    }

    await DatabaseConfiguration().user_collection.insert_one(new_user)
    return new_user


async def get_role_permissions(db, role_name: str):
    """
    Fetch the role and its permissions from PostgreSQL by role name.

    Params:
        db (AsyncSession): The SQLAlchemy async database session.
        role_name (str): The name of the role to retrieve permissions for.

    Returns:
        sqlalchemy.engine.Row or None: A Row object containing the following fields:
            - role_id (int): The unique identifier of the role.
            - role_name (str): The name of the role.
            - permissions (list[str]): A list of permission names associated with the role.

        Returns `None` if no matching role is found.
    """
    query = """
        SELECT r.id AS role_id, r.name AS role_name, array_agg(p.name) AS permissions
        FROM public.roles r
        JOIN public.role_permissions rp ON r.id = rp.role_id
        JOIN public.permissions p ON rp.permission_id = p.id
        WHERE r.name = :role_name
        GROUP BY r.id, r.name
    """
    result = (await db.execute(text(query), {"role_name": role_name})).fetchone()
    return result


async def get_user_by_role(role_name: str | None = None, role_id: int | None = None) -> dict:
    """
    Retrieve a user from MongoDB with the given role_name and role_id.
    If no matching user is found, a new user is created with the provided role details.

    Params:
        role_name (str, optional): The name of the role to search for. Defaults to None.
        role_id (int, optional): The unique identifier of the role. Defaults to None.

    Returns:
        dict: A dictionary representing the user data.
    """
    from app.database.configuration import DatabaseConfiguration
    query = {"role": None} if not role_name or not role_id else {
        "role.role_name": role_name, "role.role_id": role_id
    }

    user = await DatabaseConfiguration().user_collection.find_one(query)

    if not user:
        user = await create_user(role_name, role_id)
    return user


async def generate_token(user: dict) -> str:
    """
    Generate an access token and store it in a Redis hash with expiration.

    This function creates a JWT access token containing user-specific data such as
    username, role, group IDs, and user ID. The token is set to expire after a
    predefined duration.

    Params:
        user (dict): A dictionary representing the user.

    Returns:
        str: The generated JWT access token.
    """
    # Create access token
    token = await Authentication().create_access_token(
        data={
            "sub": user["user_name"],
            "role_id": user["role"].get("role_id") if user["role"] else None,
            "group_ids": [],
            "user_id": str(user["_id"]),
            "scopes": [user["role"].get("role_name")] if user["role"] else ["user"]
        },
        expires_delta=timedelta(seconds=TOKEN_EXPIRY_SECONDS),
    )

    return token


async def access_token_for_postgres_role(role_name: str) -> str:
    """
    Fetch or generate an access token for a given PostgresSQL role.

    Params:
        role_name (str): The name of the role to fetch permissions for.

    Returns:
        str: The generated access token.

    Notes:
        - Retrieves role permissions from PostgresSQL.
        - Finds or creates a user with the given role in MongoDB.
        - Generates a JWT access token for the user.
    """
    from app.dependencies.oauth import get_db

    async for db in get_db():
        role_data = await get_role_permissions(db, role_name) if role_name else None
        if role_data:
            role_id, role_name, _ = role_data
        else:
            role_id, role_name = None, None

        user = await get_user_by_role(role_name, role_id)
        return await generate_token(user)


@pytest.fixture
async def super_admin_token():
    """
    Fetch or generate the super_admin token and return it.
    """
    return await access_token_for_postgres_role("super_admin")


@pytest.fixture
async def user_token():
    """
    Fetch or generate the normal user_admin token who doesn't have any role
    or permissions assigned and return it.
    """
    return await access_token_for_postgres_role("user")


@pytest.fixture
async def fetch_latest_role_perm(request):
    """
    Fixture to fetch the latest record from a specified model.

    Params:
        request (FixtureRequest): Provides access to the model passed via param.

    Returns:
        object: The most recent record from the provided SQLAlchemy model.

    Notes:
        - The model is passed using @pytest.mark.parametrize with the "indirect=True" option.
        - Retrieves the latest record based on the model's "id" field in descending order.
    """
    from app.dependencies.oauth import get_db
    model = request.param
    async for db in get_db():
        result = await db.execute(
            text(f"SELECT * FROM {model.__tablename__} ORDER BY id DESC LIMIT 1")
        )
        return result.fetchone()


@pytest.fixture
async def test_super_admin_validation():
    """
    Return the access token of student which we can be used for
    authenticate student
    """
    from app.database.configuration import DatabaseConfiguration
    from app.helpers.user_curd.user_configuration import UserHelper

    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": settings.superadmin_username}
    )
    if not user:
        await UserHelper().create_superadmin()
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": settings.superadmin_username}
    )
    return user


@pytest.fixture
async def super_admin_access_token(test_super_admin_validation):
    """
    Get the access token of super_admin user which we can be used for
    authenticate super_admin
    """
    token = await Authentication().create_access_token(
        data={
            "sub": test_super_admin_validation.get("user_name"),
            "scopes": [test_super_admin_validation.get("role", {}).get("role_name")],
        },
        expires_delta=timedelta(hours=1),
    )
    return token

  
async def fetch_unassigned_permission(entity_type: str, entity_id: int):
    """
    Fetch an unassigned permission for a given role or group.

    This asynchronous function retrieves a single permission that is not currently
    assigned to the specified role or group.

    Parameters:
    - entity_type (str): The type of entity ('role' or 'group').
    - entity_id (int): The unique identifier of the role or group.

    Returns:
    - Row or None: A database row representing an unassigned permission if available, or None
      if all permissions are assigned.

    Raises:
    - SQLAlchemyError: If there is an error executing the database query.

    Notes:
    - This function uses a synchronous database connection via `get_db()`.
    - It returns only one unassigned permission due to the `LIMIT 1` clause.
    """

    from app.dependencies.oauth import get_db
    if entity_type not in {"role", "group"}:
        logger.error(f"Invalid entity type: {entity_type}")
        return None

    table_name = f"{entity_type}_permissions"
    column_name = f"{entity_type}_id"
    assigned_query = text(f"""
            SELECT permission_id FROM {table_name}
            WHERE {column_name} = :entity_id
            LIMIT 1;
        """)

    delete_query = text(f"""
            DELETE FROM {table_name}
            WHERE {column_name} = :entity_id
            AND permission_id = :permission_id;
        """)
    query = text(f"""
        SELECT * 
        FROM permissions p
        WHERE p.id NOT IN (
            SELECT rp.permission_id
            FROM {table_name} rp
            WHERE rp.{column_name} = :entity_id
        )
        LIMIT 1;
    """)
    async for db in get_db():
        try:
            assigned_result = await db.execute(assigned_query, {"entity_id": entity_id})
            assigned_row = assigned_result.fetchone()
            if assigned_row:
                permission_id = assigned_row[0]
                await db.execute(delete_query, {"entity_id": entity_id, "permission_id": permission_id})
                await db.commit()
                return permission_id
            result = await db.execute(query, {"entity_id": entity_id})
            row = result.fetchone()
            return row[0] if row else None

        except Exception as e:
            logger.error(f"Something went wrong while fetching unassigned role permissions: {e}")
            return None


async def fetch_assigned_permission_ids(entity_type: str, entity_id: int):
    """
    Fetch assigned permission IDs for a given role.

    This asynchronous function retrieves the list of permission IDs associated with a specified role.

    Parameters:
    - entity_type (str): The type of entity ('role' or 'group').
    - entity_id (int): The unique identifier of the role or group.

    Returns:
    - Row(int) or None: A list of permission IDs if permissions are found, or None if no
    permissions are assigned.

    Raises:
    - SQLAlchemyError: If there is an error executing the database query.

    Notes:
    - This function uses a synchronous database connection via `get_db()`.
    - Ensure the provided `role_id` is valid and exists in the `role_permissions` table.
    """
    from app.dependencies.oauth import get_db
    table_name = f"{entity_type}_permissions"
    column_name = f"{entity_type}_id"
    async for db in get_db():
        try:
            result = await db.execute(
                text(f"""
                        SELECT rp.permission_id
                        FROM {table_name} rp
                        WHERE rp.{column_name} = :entity_id;
                    """),
                {"entity_id": entity_id}
            )
            permission_ids = [row[0] for row in result.fetchall()]  # Extract IDs from result
            return permission_ids
        except Exception as e:
            logger.error(f"Something went wrong while fetching assigned permission ids:: {e}")
            return []

async def fetch_unassigned_group_users(entity_type: str, entity_id: int):
    """
    Fetches the first user who does not have the specified group ID in their 'group_ids' field.

    Params:
        entity_type (str): The type of entity to validate, must be 'group'. If any other value is provided, an
        error will be logged.
        entity_id (int): The ID of the group to search for in the 'group_ids' field.

    Returns:
        str: The user ID of the first user found who does not belong to the specified group, or None if the
        entity type is invalid.
    """
    from app.database.configuration import DatabaseConfiguration
    if entity_type != "group":
        logger.error(f"Invalid entity type: {entity_type}")
        return None

    user = await DatabaseConfiguration().user_collection.find_one({"group_ids": {"$ne": entity_id}})
    return str(user.get("_id"))

async def fetch_assigned_group_users(entity_id: int):
    """
    Fetches the first user who has the specified group ID in their 'group_ids' field.
    If no such user is found, a new user is created and assigned to the specified group.

    Args:
        entity_id (int): The ID of the group to search for in the 'group_ids' field.

    Returns:
        str: The user ID of the first user found who belongs to the specified group, or the ID of the newly
        created user if none is found.
    """
    from app.database.configuration import DatabaseConfiguration
    user = await DatabaseConfiguration().user_collection.find_one({"group_ids": {"$in": [entity_id]}})
    if user:
        return str(user.get("_id"))
    user = await DatabaseConfiguration().user_collection.insert_one(
        {
            "name": "Testing",
            "email": "testing@yopmail.com",
            "group_ids": [entity_id]
        }
    )
    return str(user.inserted_id)

@pytest.fixture
async def college_super_admin_access_token(test_user_validation):
    """
    Get the access token of college_super_admin user which we can be used for
     authenticate college_super_admin
    """
    token = await Authentication().create_access_token(
        data={
            "sub": test_user_validation["user_name"],
            "scopes": [test_user_validation["role"]["role_name"]],
        },
        expires_delta=timedelta(hours=1),
    )
    return token


@pytest.fixture
async def publisher_access_token(test_user_publisher_validation):
    """
    Get the access token of college_super_admin user which we can be used for
    authenticate college_super_admin
    """
    token = await Authentication().create_access_token(
        data={
            "sub": test_user_publisher_validation["user_name"],
            "scopes": ["college_publisher_console"],
        },
        expires_delta=timedelta(hours=1),
    )
    return token


@pytest.fixture
def test_counselor_data(test_user_validation):
    """Return dummy course details for create new course"""
    return {
        "email": "user255@example.com",
        "full_name": "string string string",
        "mobile_number": 7576756757,
        "associated_colleges": [
            str(test_user_validation.get("associated_colleges")[0])
        ],
    }


@pytest.fixture
async def test_counselor_validation(test_counselor_data, test_user_validation):
    """Return counselor data, it will create counselor in test DB collection
    if counselor not exist. Using test counselor data for create counselor."""
    from app.database.configuration import DatabaseConfiguration
    from app.helpers.user_curd.user_configuration import UserHelper

    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": test_counselor_data.get("email")}
    )
    if not user:
        await UserHelper().create_user(
            test_counselor_data,
            test_user_validation.get("user_name"),
            "college_counselor",
        )
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": test_counselor_data.get("email")}
    )
    return user


@pytest.fixture
async def college_counselor_access_token(test_counselor_validation):
    """
    Get the access token of college_counselor user which we can be used for
     authenticate college_counselor
    """
    token = await Authentication().create_access_token(
        data={
            "sub": test_counselor_validation["user_name"],
            "scopes": [test_counselor_validation["role"]["role_name"]],
        },
        expires_delta=timedelta(hours=1),
    )
    return token


@pytest.fixture
async def test_new_admin_data():
    """ Return dummy admin details for create new admin"""
    return {
        "first_name": "Sandeep",
        "middle_name": "",
        "last_name": "Mehta",
        "email": "sandeep@example.com",
        "mobile_number": "7896543210"
    }

@pytest.fixture
async def test_sam_data():
    return {
        "email": "raj.kumar@domain.in",
        "first_name": "Raj",
        "middle_name": "Singh",
        "last_name": "Kumar",
        "mobile_number": "6976546210"
    }

def user_feature_data(return_data=False):
    feature_id = uuid.uuid4().hex[:8]
    if return_data:
        return {
            feature_id: {
                "feature_id": feature_id,
                "name": "Testing",
                "description": "testing description",
                "visibility": True,
                "need_api": False,
                "permissions": {
                    "read": True,
                    "write": True,
                    "delete": True,
                    "edit": True
                },
                "expandable": True
            }
        }
    else:
        return feature_id


@pytest.fixture
async def test_get_super_account_manager(college_super_admin_access_token):
    from app.database.configuration import DatabaseConfiguration
    if (super_account_manager := await DatabaseConfiguration().user_collection.find_one(
            {'user_type': 'super_account_manager'})):
        return super_account_manager
    else:
        from bson.objectid import ObjectId
        from datetime import datetime
        data = {
            "_id": ObjectId("67da51e38de294bf7040af95"),
            "email": "raj.kumar@domain.in",
            "first_name": "Raj",
            "middle_name": "Singh",
            "last_name": "Kumar",
            "mobile_number": "9876546210",
            "created_by": ObjectId("6290c40ee87e304387308492"),
            "user_name": "raj.kumar@domain.in",
            "password": "$2b$12$E0xZLd6PEBO1f4du5XmTz.J3J7nSz0BSjbFCt1Xkqni9k2pCeXzaC",
            "role": {
                "role_name": "super_account_manager",
                "role_id": 101
            },
            "user_type": "super_account_manager",
            "assigned_clients": [],
            "last_accessed": None,
            "created_on": datetime.now(),
            "is_activated": True
        }
        await DatabaseConfiguration().user_collection.insert_one(data)
        return data


@pytest.fixture
async def test_new_account_manager():
    """ Return dummy account manager details for create new account manager"""
    return {
        "first_name": "Sanjeev",
        "middle_name": "",
        "last_name": "Yadav",
        "email": "sanjeev@example.com",
        "mobile_number": "8754016652",
        "associated_super_account_manager": "67da51e38de294bf7040af95"
    }


@pytest.fixture
async def test_update_account_manager():
    """ Return dummy account manager details for create new account manager"""
    return {
        "email": "lKZdM@example.com",
    }


@pytest.fixture
async def test_get_account_manager():
    from app.database.configuration import DatabaseConfiguration
    if (account_manager := await DatabaseConfiguration().user_collection.find_one(
            {'user_type': 'account_manager'})):
        return account_manager
    else:
        from bson.objectid import ObjectId
        acc_mng = await DatabaseConfiguration().role_collection.find_one({"role_name": "account_manager"})
        data = {
            "_id": ObjectId("67e3fbafdbd1bab57a6a6f14"),
            "first_name": "Sanjeev",
            "middle_name": "",
            "last_name": "Yadav",
            "email": "sanjeev@example.com",
            "mobile_number": "8754016652",
            "associated_super_account_manager": ObjectId("67da51e38de294bf7040af95"),
            "created_by": ObjectId("6290c40ee87e304387308492"),
            "user_name": "sanjeev@example.com",
            "password": "$2b$12$sgM8tpADviy71XIZA4y5AO9qzPZDNBQp7Bi0b9VBQhAXgtko1FLba",
            "role": {
                "role_name": "account_manager",
                "role_id": acc_mng.get("_id")
            },
            "user_type": "account_manager",
            "assigned_clients": [],
            "last_accessed": None,
            "created_on": "2025-03-26T18:35:51.293Z",
            "is_activated": True
        }
        await DatabaseConfiguration().user_collection.insert_one(data)
        return data


@pytest.fixture
async def test_get_client(test_client_data, http_client_test, college_super_admin_access_token,
                          test_get_account_manager, test_client_configuration_data):
    from app.database.configuration import DatabaseConfiguration
    feature_key = user_feature_data()
    if (client := await DatabaseConfiguration().client_collection.find_one(
            {'client_email': 'randomuser245@yopmail.com'})):
        return client
    test_client_data["assigned_account_managers"] = [
        str(test_get_account_manager.get("_id"))
    ]
    response = await http_client_test.post(
        f"client/create/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_client_data
    )
    data = await DatabaseConfiguration().client_collection.find_one(
        {'client_email': 'randomuser245@yopmail.com'})
    return data


@pytest.fixture
def college_urls():
    return {
        "student_dashboard_url": "https://student.example.com/",
        "admin_dashboard_url": "https://admin.example.com/"
    }


@pytest.fixture
def test_client_data():
    """Return dummy client details for create new client"""
    return {
        "client_name": "Delta University",
        "client_email": "randomuser245@yopmail.com",
        "client_phone": "9876543210",
        "assigned_account_managers": [
            "6643a5874b12e3fc9c7f12ab",
            "6643a5874b12e3fc9c7f12bc",
            "6643a5874b12e3fc9c7f12cd"
        ],
        "address": {
            "address_line_2": "Tech Park, Sector 21",
            "address_line_1": "Building 5, Level 3",
            "city_name": "Pune",
            "state_code": "MH",
            "country_code": "IN"
        },
        "websiteUrl": "https://dev3.university.edu/",
        "POCs": [
            {
                "name": "John Doe",
                "email": "johndoe123@university.edu",
                "mobile_number": "9876543210"
            },
            {
                "name": "Jane Smith",
                "email": "janesmith@university.edu",
                "mobile_number": "9123456789"
            },
            {
                "name": "Robert Johnson",
                "email": "robert.johnson@university.edu",
                "mobile_number": "9012345678"
            }
        ]
    }


@pytest.fixture
async def test_fetch_master_screen_data(test_college_data, test_super_admin_validation):
    """Creates and inserts test master screen data for a client and college."""
    from app.database.configuration import DatabaseConfiguration
    from app.helpers.college_configuration import CollegeHelper
    client = await DatabaseConfiguration().client_collection.find_one()
    college = await DatabaseConfiguration().college_collection.find_one()
    if not college:
        await CollegeHelper().create_new_college(
            test_college_data, test_super_admin_validation
        )
        college = await DatabaseConfiguration().college_collection.find_one(
            {"name": str(test_college_data["name"]).title()}
        )
    client_id, college_id = client.get("_id"), college.get("_id")
    data = {
        "_id": ObjectId(),
        "d7b803a4": {
            "name": "Data segment Manager",
            "description": "Data segment manager show",
            "icon": "string",
            "amount": 10,
            "visibility": True,
            "need_api": True,
            "permissions": {},
            "feature_id": "d7b803a4",
            "required_role_ids": []
        },
        "screen_type": "client_screen",
        "client_id": client_id,
    }
    await DatabaseConfiguration().master_screens.insert_one(data)
    data.update({"college_id": college_id, "screen_type": "college_screen", "_id": ObjectId()})
    await DatabaseConfiguration().master_screens.insert_one(data)
    return str(client_id), str(college_id)


@pytest.fixture
def test_client_update_data():
    """Return dummy client details for update client"""
    return {
        "client_email": "randomemail@random.com",
        "address": {
            "address_line_2": "T-51",
            "address_line_1": "Sector 8",
            "city_name": "Noida",
            "state_code": "UP",
            "country_code": "IN"
        },
        "POCs": [
            {
                "name": "John Doe",
                "email": "johndoe123@university.edu",
                "mobile_number": "9876543210"
            }
        ]
    }


@pytest.fixture
def test_client_configuration_data():
    """Return dummy client configuration details for create new client"""
    return {
        "s3": {
            "username": "s3randomuser",
            "aws_access_key_id": "AKIAXYZ12345EXAMPLE",
            "aws_secret_access_key": "3KJN98dfJSKlmNO2j49I38d8sA3jKMDN+OpZ3LKD",
            "region_name": "us-east-1",
            "assets_bucket_name": "devassetsxyz",
            "reports_bucket_name": "devreportsxyz",
            "public_bucket_name": "devpublicxyz",
            "student_documents_name": "devstudentdocsxyz",
            "report_folder_name": "Reports_xyz",
            "download_bucket_name": "downloads_xyz",
            "demo_base_bucket_url": "https://demosxyz.s3.us-east-1.amazonaws.com/",
            "dev_base_bucket_url": "https://devxyz.s3.us-east-1.amazonaws.com/",
            "prod_base_bucket_url": "https://prodxxyz.s3.us-east-1.amazonaws.com/",
            "stage_base_bucket_url": "https://stagesxyz.s3.us-east-1.amazonaws.com/",
            "demo_base_bucket": "demosxyz",
            "dev_base_bucket": "devxyz",
            "prod_base_bucket": "prodxxyz",
            "stage_base_bucket": "stagesxyz",
            "base_folder": "deltauniversity"
        },
        "collpoll": {
            "aws_access_key_id": "AKIAUBXYZ87654EXAMPLE",
            "aws_secret_access_key": "XyKJn98dfJSMs29sk38NdslkWokdmM0PpY/39Ld",
            "region_name": "us-west-1",
            "s3_bucket_name": "growthtrack.collpoll.xyz",
            "collpoll_url": "https://deltauniversity.digitalcampus.com/api/students",
            "collpoll_auth_security_key": "Basic abcdef1234567890abcdef1234567890"
        },
        "sms": {
            "username_trans": "growthtracktrans.test",
            "username_pro": "growthtracktrans.xyz",
            "password": "p@ssw0rd123",
            "authorization": "dGVzdHVzZXI6cGFzc3dvcmQ=",
            "sms_send_to_prefix": "91"
        },
        "meilisearch": {
            "meili_server_host": "http://103.45.67.89:7700/",
            "meili_server_master_key": "X98ABC3RPvXYZ123rkUhamMutEfva4N-3yCoXYZ"
        },
        "report_webhook_api_key": "XYZ9876",
        "aws_textract": {
            "textract_aws_access_key_id": "AKIAXYZ8765EXAMPLE",
            "textract_aws_secret_access_key": "gHj7/N3daXWx123456Ga80N9LDBo06Jt7XYZ",
            "textract_aws_region_name": "us-east-2"
        },
        "whatsapp_credential": {
            "send_whatsapp_url": "https://api.messaging.com/psms/service",
            "generate_whatsapp_token": "https://api.messaging.com/psms/api/token",
            "whatsapp_username": "deltaunivbot",
            "whatsapp_password": "&abcXYZ12345!",
            "whatsapp_sender": "919876543210"
        },
        "cache_redis": {
            "host": "103.200.50.25",
            "port": 6379,
            "password": "randomP@ssw0rd!"
        },
        "tawk_secret": "1234abcd5678efghijklmnop7890qrstuvwx",
        "telephony_secret": "xyz987654321",
        "razorpay": {
            "razorpay_api_key": "rzp_test_partner_ABC123XYZ456",
            "razorpay_secret": "sdf98sd7f9sdf7s8df9",
            "razorpay_webhook_secret": "Xy!@#456$%^78",
            "partner": True,
            "x_razorpay_account": "acc_XYZ9876ABC5432"
        },
        "rabbit_mq_credential": {
            "rmq_host": "rabbit_host",
            "rmq_password": "RaNd0mP@ssw0rd!",
            "rmq_url": "rabbit.example.com",
            "rmq_username": "rabbituser",
            "rmq_port": "5672"
        },
        "zoom_credentials": {
            "client_id": "z8AbcD5Te6EfXyzMNrPq",
            "client_secret": "7YzXbQESjTyQk987VKL",
            "account_id": "AbcXyz9KhtQRpZav7w"
        }
    }

@pytest.fixture
def test_college_configuration_data():
    return {
          "email_credentials": {
            "payload_username": "apollobot",
            "payload_password": "StrongPass!458",
            "payload_from": "no-reply@apollouni.edu",
            "source": "noreply@headstartmail.com"
          },
          "email_configurations": {
            "verification_email_subject": "Confirm Your Email Address",
            "contact_us_number": "1800-111-2222",
            "university_email_name": "ApolloConnect",
            "banner_image": "https://cdn.apollouni.edu/mailers/banners/banner3.png",
            "email_logo": "https://cdn.apollouni.edu/assets/logo-mail.png"
          },
              "seasons": [
                {
                  "season_name": "2023-2026",
                  "start_date": "2025-01-01",
                  "end_date": "2026-12-30",
                  "database": {
                    "username": "aristo",
                    "password": "L1G1qC8axe5SpaYG",
                    "url": "clientauto.mxs2q.mongodb.net",
                    "db_name": "test"
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
                    "db_name": "season_2022"
                  }
                }
              ],
          "university_details": {
            "university_contact_us_mail": "connect@apollouni.edu",
            "university_website_url": "https://www.apollouni.edu",
            "university_prefix_name": "AU"
          },
          "payment_gateways": {
            "easy_buzz": {
              "base_url": "https://sandbox.easebuzz.in",
              "environment": "sandbox",
              "merchant_key": "KEY12345EZ",
              "merchant_salt": "SALT#EZ9988",
              "retrieve_url": "https://dashboard.sandbox.easebuzz.in"
            },
            "eazypay": {
              "encryption_key": "9900112233445566",
              "merchant_id": "A12345"
            },
            "hdfc": {
              "base_url": "https://uatgateway.hdfcbank.com/session",
              "customer_id": "APOLLO01",
              "environment": "uat",
              "key": "QWERTYUIOP1234567890==:TestEnv2025",
              "merchant_id": "HDFC1001",
              "retrieve_url": "https://uatgateway.hdfcbank.com/orders/"
            },
            "payu": {
              "merchant_key": "keyPAYU123",
              "merchant_salt": "SaltStringForPAYU123",
              "retrieve_url": "https://test.payu.in/merchant/postservice.php?form=3"
            },
            "razorpay": {
              "partner": True,
              "razorpay_api_key": "rzp_test_9876543210Abc",
              "razorpay_secret": "SecretRZP98765",
              "razorpay_webhook_secret": "whk#123secure",
              "x_razorpay_account": "acc_ABC123Xyz987"
            }
          },
          "juno_erp": {
            "first_url": {
              "authorization": "a1b2c3d4-e5f6-7890-gh12-ijklmnop4567",
              "juno_url": "https://erp.apollouni.edu/validateApplicant.json"
            },
            "prog_ref": 101,
            "second_url": {
              "authorization": "z9y8x7w6-v5u4-3210-tsrq-ponmlkji9876",
              "juno_url": "https://erp2.apollouni.edu/saveApplicantData.json"
            }
          },
          "payment_configurations": [
            {
              "allow_payment": True,
              "application_wise": False,
              "apply_promo_voucher": True,
              "apply_scholarship": True,
              "payment_gateway": [
                "razorpay",
                "payu"
              ],
              "payment_key": "registration",
              "payment_mode": {
                "offline": False,
                "online": True
              },
              "payment_name": "Registration Fee",
              "show_status": True
            }
          ],
          "preferred_payment_gateway": "RazorPay",
          "payment_successfully_mail_message": "Thank you for completing your application and payment. <br><br>Your next step is to upload all pending academic documents to proceed further. <br><br>Feel free to contact your admission counselor or visit https://www.apollouni.edu/support for queries. <br><br>You can view and download your receipt here: <br>",
          "cache_redis": {
            "host": "10.45.23.101",
            "port": 6380,
            "password": "SecUr3#Redis2025"
          },
          "enforcements": {
            "lead_limit": 80,
            "counselor_limit": 100,
            "client_manager_limit": 60,
            "publisher_account_limit": 30
          },
          "charges_per_release": {
            "forSMS": 1,
            "forEmail": 5,
            "forWhatsapp": 2,
            "forLead": 0.25
          },
          "users_limit": 500,
          "publisher_bulk_lead_push_limit": {
            "bulk_limit": 150,
            "daily_limit": 200
          },
          "report_webhook_api_key": "APIKEY2025XYZ",
          "telephony_secret": "telephonySecret@123456789",
          "telephony_cred": {
            "mcube": {
              "key": "apikey-mcube-2025",
              "outbound_url": "http://api.mcube.in/v1/callout"
            },
            "mcube2": {
              "tawk_secret": "s3cret4567tawkkey98273627387asdk",
              "key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
              "outbound_url": "https://api2.mcube.in/v2/outbound"
            }
          },
          "email_display_name": "Apollo Outreach",
          "s3_base_folder": "apollouni-2025"
        }


@pytest.fixture
def test_college_data():
    """Return dummy college details for create new college"""
    return {
        "name": "test",
        "logo": "test",
        "background_image": "test",
        "address": {
            "address_line_1": "string",
            "address_line_2": "string",
            "country_code": "string",
            "state": "string",
            "city": "string",
        },
        "website_url": "string",
        "pocs": [{"name": "string", "email": "user@example.com", "mobile_number": 0}],
        "subscriptions": {
            "raw_data_module": False,
            "lead_management_system": False,
            "app_management_system": False,
        },
        "integrations": {
            "razorpay": {
                "client_id": settings.razorpay_api_key,
                "partner": False,
                "client_secret": settings.razorpay_secret,
                "x_razorpay_account": "string",
            }
        },
        "enforcements": {
            "lead_limit": 200000,
            "counselor_limit": 15,
            "client_manager_limit": 4,
            "publisher_account_limit": 8,
        },
        "status_info": {
            "activation_date": "2023-02-15T10:21:48.904233",
            "deactivation_date": "2023-02-15T10:21:48.904233",
        },
        "college_manager_name": ["string"],
        "extra_fields": {},
        "course_details": [
            {
                "course_id": str(ObjectId()),
                "courseName": "BSc",
                "courseSpecializations": ["specializations1", "specializations2"],
            }
        ],
        "is_different_forms": False,
        "form_details": {
            "basicDetails": {
                "firstName": {
                    "fieldType": "input",
                    "mandatory": True,
                    "canRemove": False,
                },
                "mobileNumber": {
                    "fieldType": "input",
                    "mandatory": True,
                    "canRemove": False,
                },
                "alterNateMobileNumber": {
                    "fieldType": "input",
                    "mandatory": True,
                    "canRemove": True,
                },
                "gender": {
                    "fieldType": "select",
                    "items": ["item1", "item2"],
                    "mandatory": True,
                    "canRemove": True,
                },
            },
        },
    }


@pytest.fixture
async def test_college_validation(test_college_data, test_super_admin_validation):
    """Return college data, it will create college in test DB collection if
    college not exist.
    Using test college data for create college."""
    from app.database.configuration import DatabaseConfiguration
    from app.helpers.college_configuration import CollegeHelper
    from app.core.reset_credentials import Reset_the_settings
    college = await DatabaseConfiguration().college_collection.find_one(
        {"name": str(test_college_data["name"]).title()}
    )
    if not college:
        await CollegeHelper().create_new_college(
            test_college_data, test_super_admin_validation
        )
    college = await DatabaseConfiguration().college_collection.find_one(
        {"name": str(test_college_data["name"]).title()}
    )
    await DatabaseConfiguration().client_collection.update_one(
        {"client_name": str(test_college_data["name"]).title()},
        {"$set": {"college_ids": [ObjectId(college.get("_id"))]}}
    )
    Reset_the_settings().get_user_database(
        college_id=str(college.get("_id")), form_data=None, db_name="test"
    )
    return college


@pytest.fixture
def test_course_data():
    """Return dummy course details for create new course"""
    return {
        "course_name": "Test",
        "course_description": "string",
        "duration": 1,
        "fees": 60000,
        "is_activated": True,
        "banner_image_url": "string",
        "course_specialization": [
            {"spec_name": "string", "is_activated": True,
             "spec_fee_info": {"registration_fee": 100000}},
            {"spec_name": "test", "is_activated": True,
             "spec_fee_info": {"registration_fee": 100000}},
        ],
        "school_name": "Test",
    }


@pytest.fixture
async def new_approval_request_data():
    """
    Return dummy data for create new approval request
    """
    from app.database.configuration import DatabaseConfiguration
    college_id = await DatabaseConfiguration().college_collection.find_one()
    return {
        "approval_type": "college_course_details",
        "college_id": str(college_id.get("_id")),
        "payload": {
           "school_names": ["CSE", "ECE"],
           "course_lists": [
              {
                 "course_name": "BSc Computer Science",
                 "school_name": "CSE",
                 "course_type": "UG",
                 "course_activation_date": "2023-05-03",
                 "course_deactivation_date": "2025-05-03",
                 "do_you_want_different_form_for_each_specialization": True,
                 "course_banner_url": "https://example.com/course_banner.jpg",
                 "course_fees": 5000.50,
                 "specialization_names": [
                    {"spec_name": "Artificial Intelligence", "is_activated": True},
                    {"spec_name": "Cyber Security", "is_activated": True}
                 ],
                 "course_description": "A comprehensive program covering computer science fundamentals."
              }
           ],
           "preference_details": {
              "do_you_want_preference_based_system": True,
              "will_student_able_to_create_multiple_application": True,
              "maximum_fee_limit": 20000,
              "how_many_preference_do_you_want": 2,
              "fees_of_trigger": {"trigger_1": 100, "trigger_2": 100}
           }
        }
    }


@pytest.fixture
def client_automation_test_course_data():
    return {
        "school_names": [
            "CSE",
            "ECE"
        ],
        "course_lists": [
            {
                "course_name": "BSc Computer Science",
                "school_name": "CSE",
                "course_type": "UG",
                "course_activation_date": "2025-05-03",
                "course_deactivation_date": "2025-03-28",
                "do_you_want_different_form_for_each_specialization": True,
                "course_banner_url": "https://example.com/course_banner.jpg",
                "course_fees": 5000.50,
                "specialization_names": [
                    {
                        "spec_name": "Artificial Intelligence",
                        "is_activated": True,
                        "spec_custom_id": "BSAI"
                    },
                    {
                        "spec_name": "Cyber Security",
                        "is_activated": True,
                        "spec_custom_id": "BSCY"
                    }
                ],
                "course_description": "A comprehensive program covering computer science fundamentals."
            }
        ],
        "preference_details": {
            "do_you_want_preference_based_system": True,
            "will_student_able_to_create_multiple_application": True,
            "maximum_fee_limit": 20000,
            "how_many_preference_do_you_want": 2,
            "fees_of_trigger": {
                "trigger_1": 100,
                "trigger_2": 100
            }
        }
    }

@pytest.fixture
async def test_client_automation_college_additional_data():
    return {
  "logo_transparent": "https://example.com/",
  "fab_icon": "https://example.com/",
  "student_dashboard_landing_page_link": "https://example.com/",
  "google_tag_manager_id": "string",
  "student_dashboard_meta_description": "string",
  "admin_dashboard_meta_description": "string",
  "facebook_pixel_setup_code": "string",
  "student_dashboard_project_title": "string",
  "admin_dashboard_project_title": "string",
  "lead_stages": [
    {
      "stage_name": "string",
      "sub_lead_stage": [
        "string"
      ]
    }
  ],
  "lead_tags": [
    "string"
  ],
  "student_dashboard_domain": "https://example.com/",
  "campus_tour_video_url": "https://example.com/",
  "brochure_url": "https://example.com/",
  "payment_method": "icici_bank",
  "declaration_text": "string",
  "terms_and_condition_text": "string"
}

@pytest.fixture
async def test_client_automation_college_id(test_get_client, http_client_test, college_super_admin_access_token, test_client_configuration_data):
    feature_key = user_feature_data()
    from app.database.configuration import DatabaseConfiguration
    college = await DatabaseConfiguration().college_collection.find_one(
        {"name": "test1733", "email": "user@gmail.com"})
    if college is None:
        DatabaseConfiguration().college_collection.delete_many({"name": "test1733"})
        college_data = {
            "name": "test1733",
            "email": "user@gmail.com",
            "phone_number": "8889995556",
            "associated_client": str(test_get_client.get("_id")),
            "address": {
                "address_line_1": "",
                "address_line_2": "",
                "country_code": "IN",
                "state_code": "MH",
                "city_name": "Pune",
            },
        }
        response = await http_client_test.post(f"/client/{str(test_get_client.get('_id'))}/configuration/add"
                                               f"?feature_key={feature_key}",
                                               headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                               json=test_client_configuration_data
                                               )
        response = await http_client_test.post(
            f"/client_automation/add_college?feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            json=college_data,
        )
        return response.json().get("college_id")

    return college.get("_id")


@pytest.fixture
async def test_course_validation(test_course_data, test_college_validation):
    """Return course data. Create course in test DB collection if
    course not exist.
    Using test course data for create course."""
    from app.database.configuration import DatabaseConfiguration
    from app.helpers.course_configuration import CourseHelper

    course = await DatabaseConfiguration().course_collection.find_one(
        {
            "college_id": test_college_validation.get("_id"),
            "course_name": test_course_data.get("course_name"),
        }
    )
    if not course:
        await CourseHelper().create_new_course(
            test_course_data, str(test_college_validation.get("_id"))
        )
    course = await DatabaseConfiguration().course_collection.find_one(
        {
            "college_id": test_college_validation.get("_id"),
            "course_name": test_course_data.get("course_name"),
        }
    )
    return course


@pytest.fixture
def test_generate_report_data():
    """Return dummy report details for generate report"""
    return {
        "report_name": "test",
        "report_type": "Applications",
        "format": "csv",
    }


@pytest.fixture
def test_payment_details(test_user_validation, application_details):
    """
    Return payment details
    """
    import datetime

    return {
        "payment_id": "pay_KBioqqepq6qsWG",
        "order_id": "order_KBioPy4e6BClSp",
        "user_id": test_user_validation.get("_id"),
        "details": {
            "purpose": "studentApplication",
            "application_id": application_details.get("_id"),
        },
        "status": "failed",
        "error": {
            "error_code": None,
            "description": None,
            "merchant": "RazorPay",
            "created_at": datetime.datetime.utcnow(),
        },
    }


@pytest.fixture
async def payment_details(test_payment_details):
    """
    Return payment details
    """
    from app.database.configuration import DatabaseConfiguration

    payment = await DatabaseConfiguration().payment_collection.find_one(
        {"payment_id": test_payment_details.get("payment_id")}
    )
    if not payment:
        await DatabaseConfiguration().payment_collection.insert_one(
            test_payment_details
        )
    payment = await DatabaseConfiguration().payment_collection.find_one(
        {"payment_id": test_payment_details.get("payment_id")}
    )
    return payment


@pytest.fixture
async def followup_details(application_details, test_user_validation):
    """
    save and return followup_detail
    """
    from app.database.configuration import DatabaseConfiguration
    from app.core.utils import utility_obj

    if (
            lead := await DatabaseConfiguration().leadsFollowUp.find_one(
                {"application_id": ObjectId(str(application_details.get("_id")))}
            )
    ) is None:
        await DatabaseConfiguration().leadsFollowUp.insert_one(
            {
                "application_id": ObjectId(application_details.get("_id")),
                "student_id": ObjectId(application_details.get("student_id")),
                "lead_stage": "Fresh Lead",
                "followup": [
                    {
                        "assigned_counselor_id": ObjectId(
                            application_details.get("allocate_to_counselor", {}).get(
                                "assigned_counselor_id"
                            )
                        ),
                        "assigned_counselor_name": ObjectId(
                            application_details.get("allocate_to_counselor", {}).get(
                                "assigned_counselor_name"
                            )
                        ),
                        "status": "Incomplete",
                        "timestamp": datetime.utcnow(),
                        "followup_date": datetime.utcnow(),
                        "followup_note": "Take followup on time",
                        "added_by": utility_obj.name_can(test_user_validation),
                        "user_id": ObjectId(test_user_validation.get("_id")),
                    }
                ],
            }
        )
        lead = await DatabaseConfiguration().leadsFollowUp.find_one(
            {"application_id": ObjectId(str(application_details.get("_id")))}
        )
    return lead


@pytest.fixture
def test_template_data():
    """
    Dummy data for create template in the templates collection
    """
    return {
        "sender_email_id": "sender@headstart.biz",
        "reply_to_email": "reply@headstart.biz",
        "template_type": "email",
        "content": "sample",
        "template_json": {},
        "template_name": "email",
        "tags": [
            "test1",
            "test"
        ],
        "is_published": False,
        "subject": "events",
        "email_type": "default",
        "email_provider": "default",
        "email_category": "default",
        "dlt_content_id": "12334",
        "select_profile_role": [
            "college_admin"
        ],
        "select_members": [
            {
                "role": "college_admin",
                "name": "Fahim",
                "id": "62aadbd4040d039d95027fab"
            }
        ],
        "attachment_document_link": [
            "string"
        ]
    }


@pytest.fixture
def test_whatsapp_template_data():
    """
    Dummy data for create template in the templates collection
    """
    return {
        "template_type": "whatsapp",
        "template_name": "test name",
        "content": "testing",
        "tags": [
            "asdf",
            "test"
        ],
        "is_published": False,
        "template_id": "34567",
        "template_type_option": "interactive_button",
        "add_template_option_url": [
            {
                "type": "cta",
                "nature": "static",
                "url": "http://localhost:3006/create-view-template"
            },
            {
                "type": "quick_reply",
                "nature": "dynamic",
                "url": "http://localhost:3006/create-view-template"
            }
        ],
        "select_profile_role": [
            "college_counselor"
        ],
        "select_members": [
            {
                "role": "college_counselor",
                "name": "Tesing",
                "id": "62fddeceeff0ff29b1b6a8f3"
            }
        ],
        "attachmentType": "",
        "attachmentURL": ""
    }


@pytest.fixture
async def test_template_validation(test_template_data, test_user_validation):
    """
    Return template data, if template data not found then it will create it
    """
    from app.database.configuration import DatabaseConfiguration
    from datetime import datetime
    from app.core.utils import utility_obj

    template = await DatabaseConfiguration().template_collection.find_one({})
    if not template:
        test_template_data["last_modified_timeline"] = [
            {
                "last_modified_at": datetime.utcnow(),
                "user_id": ObjectId(str(test_user_validation.get("_id"))),
                "user_name": utility_obj.name_can(test_user_validation),
            }
        ]
        await DatabaseConfiguration().template_collection.insert_one(test_template_data)
    template = await DatabaseConfiguration().template_collection.find_one({})
    return template


@pytest.fixture
def call_activity_data(test_student_validation):
    """
    Dummy call activity data
    """
    return {
        "type": ["inbound"],
        "mobile_numbers": [
            test_student_validation.get("basic_details", {}).get("mobile_number")
        ],
        "call_started_datetimes": [datetime.utcnow().strftime("%d %b %Y %I:%M:%S %p")],
        "call_durations": [98],
    }


@pytest.fixture
async def test_call_history(test_counselor_validation, call_activity_data):
    """
    Get counselor call history, if call history not present then it will
    create it
    """
    from app.database.configuration import DatabaseConfiguration
    from app.core.utils import utility_obj
    from datetime import datetime

    await DatabaseConfiguration().call_activity_collection.delete_many({})
    await DatabaseConfiguration().call_activity_collection.insert_one(
        {
            "type": call_activity_data.get("type", [])[0].title(),
            "call_to": test_counselor_validation["_id"],
            "call_to_name": utility_obj.name_can(test_counselor_validation),
            "call_from": call_activity_data.get("mobile_numbers", [])[0],
            "call_from_name": "test",
            "call_started_at": call_activity_data.get("call_started_datetimes", [])[0],
            "call_duration": call_activity_data.get("call_durations", [])[0],
            "created_at": datetime.utcnow(),
        }
    )
    call_history = await DatabaseConfiguration().call_activity_collection.find_one(
        {
            "$or": [
                {"call_to": test_counselor_validation["_id"]},
                {"call_from": test_counselor_validation["_id"]},
            ]
        }
    )
    return call_history


@pytest.fixture
def test_successful_lead():
    """
    Returns dummy data for successful leads
    """
    return {
        "mandatory_field": {"email": "david@gmail.com", "mobile_number": 7485112652},
        "offline_data_id": ObjectId("63469aba9fea74b450e3753c"),
        "created_at": datetime.utcnow(),
        "duplicate_data": 1,
        "other_field": {
            "first_name": "David",
            "last_name": "Joseph",
            "class": 12,
            "section": "B",
        },
    }


@pytest.fixture
async def successful_lead(test_successful_lead):
    """
    Return successful lead data from the collection raw_data, if not exists
    then it will create it
    """
    from app.database.configuration import DatabaseConfiguration

    if (
            document := await DatabaseConfiguration().raw_data.find_one(
                {"offline_data_id": test_successful_lead["offline_data_id"]}
            )
    ) is None:
        await DatabaseConfiguration().raw_data.insert_one(test_successful_lead)
        document = await DatabaseConfiguration().raw_data.find_one(
            {"offline_data_id": ObjectId(test_successful_lead.get("offline_data_id"))}
        )
    return document


@pytest.fixture
def test_counselor(test_counselor_validation):
    """
    Returns dummy data for college_counselor
    """
    return {
        "counselor_id": test_counselor_validation.get("_id"),
        "counselor_name": "viru chaudhary",
        "no_allocation_date": ["2022-08-24", datetime.utcnow().strftime("%Y-%m-%d")],
        "last_update": datetime.utcnow(),
    }


@pytest.fixture
async def absent_counselor(test_counselor):
    from app.database.configuration import DatabaseConfiguration

    if (
            document := await DatabaseConfiguration().counselor_management.find_one(
                {"counselor_id": test_counselor.get("counselor_id")}
            )
    ) is None:
        await DatabaseConfiguration().counselor_management.insert_one(test_counselor)
        document = await DatabaseConfiguration().counselor_management.find_one(
            {"counselor_id": ObjectId(test_counselor.get("counselor_id"))}
        )
    return document


@pytest.fixture
async def student_name(test_student_validation):
    """
    Returns student details to get student details by id and name
    """
    from app.core.utils import utility_obj

    name = utility_obj.name_can(test_student_validation["basic_details"])
    return name


@pytest.fixture
async def start_end_date():
    """
    Returns start and end date
    """
    from app.core.utils import utility_obj

    data = await utility_obj.last_3_month()
    return data


@pytest.fixture
def test_offline_data(test_user_validation):
    """
    Dummy offline data for create document in the collection named offline_data
    """
    from app.core.utils import utility_obj

    return {
        "imported_by": test_user_validation.get("_id"),
        "import_status": "completed",
        "data_name": "test",
        "uploaded_on": datetime.utcnow(),
        "uploaded_by": utility_obj.name_can(test_user_validation),
        "lead_processed": 0,
        "duplicate_leads": 0,
        "failed_lead": 0,
        "duplicate_lead_data": [],
        "failed_lead_data": None,
        "successful_lead_count": 500,
    }


@pytest.fixture
async def test_offline_data_validation(test_offline_data):
    """
    Return offline data if exists, if not exists then create it
    """
    from app.database.configuration import DatabaseConfiguration

    document = await DatabaseConfiguration().offline_data.find_one(
        {"data_name": str(test_offline_data.get("data_name")).lower()}
    )
    if not document:
        await DatabaseConfiguration().offline_data.insert_one(test_offline_data)
    document = await DatabaseConfiguration().offline_data.find_one(
        {"data_name": str(test_offline_data.get("data_name")).lower()}
    )
    return document


@pytest.fixture
async def test_automation_validation(test_template_validation):
    """
    Return dummy automation data for create rule
    """
    from app.database.configuration import DatabaseConfiguration

    data = {
        "module_name": "test",
        "rule_name": "test",
        "automation_description": "string",
        "script": {
            "action": "string",
            "condition_exec": {"state": ["TN"]},
            "when_exec": {"schedule_value": 2, "schedule_type": "hours"},
            "selected_template_id": str(test_template_validation.get("_id")),
            "email_subject": "string",
            "action_type": "string",
        },
        "enabled": True,
        "is_published": True,
    }
    if (
            await DatabaseConfiguration().rule_collection.find_one({"rule_name": "test"})
            is None
    ):
        await DatabaseConfiguration().rule_collection.insert_one(data)
    return await DatabaseConfiguration().rule_collection.find_one({"rule_name": "test"})


@pytest.fixture
def test_automation_data(test_template_validation):
    """
    Return dummy automation data for create automation
    """
    return {
        "automation_details": {
            "automation_name": "test",
            "automation_description": "tester",
            "releaseWindow": {
                "start_time": "2024-01-10 10:10:10 PM",
                "end_time": "2024-10-10 10:10:10 PM",
            },
            "date": {"start_date": "2024-01-10", "end_date": "2024-11-11"},
            "days": ["Monday", "Tuesday"],
            "data_segment": [
                {
                    "data_segment_id": "6419544432534e90f95eb402",
                    "data_segment_name": "jawan",
                }
            ],
            "data_count": 155,
        },
        "automation_node_edge_details": {
            "nodes": [
                {
                    "id": "20",
                    "type": "dataSegmentNode",
                    "position": {},
                    "height": "",
                    "width": "",
                },
                {
                    "id": "5",
                    "type": "delayNode",
                    "position": {},
                    "height": "",
                    "width": "",
                    "delay_data": {
                        "trigger_by": "day",
                        "interval_value": 1,
                        "delay_type": "nurturing",
                        "releaseWindow": {
                            "start_time": "03/12/2024 08:00 AM",
                            "end_time": "03/12/2024 06:00 PM",
                        },
                        "date": {"start_date": "2024-01-10", "end_date": "2024-10-10"},
                        "days": [
                            "SUNDAY",
                            "MONDAY",
                            "TUESDAY",
                            "WEDNESDAY",
                            "THURSDAY",
                        ],
                    },
                },
                {
                    "id": "50",
                    "type": "delayNode",
                    "position": {},
                    "height": "",
                    "width": "",
                    "delay_data": {
                        "trigger_by": "week",
                        "interval_value": 1,
                        "delay_type": "nurturing",
                        "releaseWindow": {
                            "start_time": "03/12/2024 08:00 AM",
                            "end_time": "03/12/2024 06:00 PM",
                        },
                        "date": {"start_date": "2024-01-10", "end_date": "2024-10-10"},
                        "days": [
                            "SUNDAY",
                            "MONDAY",
                            "TUESDAY",
                            "WEDNESDAY",
                            "THURSDAY",
                        ],
                    },
                },
                {
                    "id": "25",
                    "type": "communicationNode",
                    "position": {},
                    "height": "",
                    "width": "",
                    "communication_data": {
                        "communication_type": "Email",
                        "template_id": "",
                        "email_provider": "",
                        "email_type": "",
                        "execution_time": "03/12/2024 08:00 AM",
                        "template_content": "",
                    },
                },
                {
                    "id": "101",
                    "type": "tagNode",
                    "position": {},
                    "height": "",
                    "width": "",
                    "tag_data": "DND",
                },
                {
                    "id": "102",
                    "type": "leadStageNode",
                    "position": {},
                    "height": "",
                    "width": "",
                    "lead_stage_data": {"lead_stage": "", "lead_stage_label": ""},
                },
                {
                    "id": "108",
                    "type": "allocationNode",
                    "position": {},
                    "height": "",
                    "width": "",
                    "allocation_counsellor_data": ["6419544432534e90f95eb402"],
                },
            ],
            "edges": [
                {
                    "type": "smoothstep",
                    "markerEnd": {"type": "arrowclosed"},
                    "pathOptions": {"offset": 5},
                    "id": "20->5",
                    "source": "20",
                    "target": "5",
                    "style": {"opacity": 1},
                },
                {
                    "type": "smoothstep",
                    "markerEnd": {"type": "arrowclosed"},
                    "pathOptions": {"offset": 5},
                    "id": "5->25",
                    "source": "5",
                    "target": "25",
                    "style": {"opacity": 1},
                },
                {
                    "type": "smoothstep",
                    "markerEnd": {"type": "arrowclosed"},
                    "pathOptions": {"offset": 5},
                    "id": "25->50",
                    "source": "25",
                    "target": "50",
                    "style": {"opacity": 1},
                },
                {
                    "type": "smoothstep",
                    "markerEnd": {"type": "arrowclosed"},
                    "pathOptions": {"offset": 5},
                    "id": "50->101",
                    "source": "50",
                    "target": "101",
                    "style": {"opacity": 1},
                },
                {
                    "type": "smoothstep",
                    "markerEnd": {"type": "arrowclosed"},
                    "pathOptions": {"offset": 5},
                    "id": "5->102",
                    "source": "5",
                    "target": "102",
                    "style": {"opacity": 1},
                },
                {
                    "type": "smoothstep",
                    "markerEnd": {"type": "arrowclosed"},
                    "pathOptions": {"offset": 5},
                    "id": "50->108",
                    "source": "50",
                    "target": "108",
                    "style": {"opacity": 1},
                },
            ],
        },
        "automation_status": "active",
        "template": False,
    }


@pytest.fixture
def test_campaign_data():
    """
    Return dummy campaign data for create campaign
    """
    return {
        "campaign_type": "string",
        "campaign_name": "string",
        "campaign_description": "string",
        "enabled": True,
        "is_published": True,
    }


@pytest.fixture
async def test_campaign_rule_beta_data(
        test_template_validation,
        http_client_test,
        college_super_admin_access_token,
        test_campaign_data,
):
    """
    Return dummy campaign rule data for create campaign rule in the collection
     named campaign_rule
    """
    from app.database.configuration import DatabaseConfiguration
    feature_key = user_feature_data()
    await DatabaseConfiguration().campaign_collection.delete_many({})
    await http_client_test.post(
        f"/campaign_beta/create/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_campaign_data,
    )
    return {
        "rule_name": "string",
        "script": {
            "condition_exec": {},
            "when_exec": {"schedule_value": 1, "schedule_type": "string"},
            "selected_template_id": str(test_template_validation.get("_id")),
            "email_subject": "string",
            "action_type": test_template_validation.get("template_type"),
        },
        "campaign_name": test_campaign_data.get("campaign_name"),
        "enabled": True,
        "is_published": True,
    }


@pytest.fixture
def test_create_data_segment():
    """
    Return dummy data segment data for create data segment
    """
    return {
        "module_name": "lead",
        "data_segment_name": "string",
        "segment_type": "static",
        "description": "string",
        "filters": {"state_code": ["MH"]},
        "period": "once",
        "enabled": True,
        "is_published": True,
    }


@pytest.fixture
async def test_create_data_segment_helper(test_user_validation):
    """
    Add data segment details in the DB collection if not exist and return
        data segment data.


    """
    data = {
        "module_name": "Lead",
        "data_segment_name": "test",
        "segment_type": "Dynamic",
        "description": "",
        "filters": {
            "state_code": [],
            "source_name": [],
            "lead_name": [],
            "lead_type_name": "",
            "counselor_id": [],
            "application_stage_name": "",
            "is_verify": "",
            "payment_status": ["Successful"],
            "course": {},
            "twelve_board": [],
            "twelve_marks": [],
            "form_filling_stage": [],
        },
        "raw_data_name": "",
        "period": "Real Time Data",
        "enabled": True,
        "is_published": True,
        "updated_by": test_user_validation.get("_id"),
        "updated_by_name": "apollo college super",
        "updated_on": datetime.utcnow(),
        "created_by_id": test_user_validation.get("_id"),
        "created_by_name": "apollo college super",
        "created_on": datetime.utcnow(),
        "shared_with": [{
            "user_id": ObjectId(test_user_validation.get("_id")),
            "email": "sample@gmail.com",
            "role": "sample",
            "name": "sample"
        }]
    }
    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().data_segment_collection.delete_many(
        {"data_segment_name": {"$ne": "test"}}
    )
    if (
            await DatabaseConfiguration().data_segment_collection.find_one(
                {"data_segment_name": "test"}
            )
            is None
    ):
        await DatabaseConfiguration().data_segment_collection.insert_one(data)
    return await DatabaseConfiguration().data_segment_collection.find_one(
        {"data_segment_name": "test"}
    )


@pytest.fixture
async def test_campaign_rule_data(
        test_college_validation,
        test_template_validation,
        http_client_test,
        college_super_admin_access_token,
        test_create_data_segment,
):
    """
    Return dummy campaign rule data for create campaign rule in the collection
     named campaign_rule
    """
    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().data_segment_collection.delete_many({})
    feature_key = user_feature_data()
    await http_client_test.post(
        f"/data_segment/create/?college_id=" f"{test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_create_data_segment,
    )
    return {
        "rule_name": "string",
        "rule_description": "string",
        "script": {
            "condition_exec": {},
            "when_exec": {"schedule_value": 1, "schedule_type": "once"},
            "selected_template_id": [str(test_template_validation.get("_id"))],
            "email_subject": "string",
            "action_type": [test_template_validation.get("template_type")],
        },
        "data_segment_name": str(test_create_data_segment.get("data_segment_name")),
        "enabled": True,
        "is_published": True,
    }


@pytest.fixture
async def test_automation_rule_details(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        test_campaign_rule_data,
        test_create_data_segment,
):
    """
    Return dummy automation rule details
    """
    from app.database.configuration import DatabaseConfiguration
    feature_key = user_feature_data()
    await DatabaseConfiguration().data_segment_collection.delete_many({})
    await DatabaseConfiguration().rule_collection.delete_many({})
    college_id = test_college_validation.get("_id")
    await http_client_test.post(
        f"/data_segment/create/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_create_data_segment,
    )
    await http_client_test.post(
        f"/campaign/create_rule/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_campaign_rule_data,
    )
    data_segment = await DatabaseConfiguration().data_segment_collection.find_one(
        {
            "data_segment_name": str(
                test_create_data_segment.get("data_segment_name")
            ).title()
        }
    )
    rule = await DatabaseConfiguration().rule_collection.find_one(
        {"rule_name": str(test_campaign_rule_data.get("rule_name")).title()}
    )
    return {
        "action_type": "email",
        "status": "success",
        "execution_time": datetime.utcnow(),
        "data_segment_name": str(rule.get("data_segment_name")).title(),
        "targeted_audience": 2,
        "rule_id": str(rule.get("_id")),
        "module_name": str(data_segment.get("module_name")).title(),
        "job_details": [
            {
                "email_id": "test@gmail.com",
                "name": "test",
                "communication_date": datetime.utcnow(),
                "status": "failed",
            }
        ],
    }


@pytest.fixture
async def test_automation_rule_details_validation(test_automation_rule_details):
    """
    Get dummy automation rule details
    """
    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().automation_activity_collection.delete_many({})
    test_automation_rule_details["rule_id"] = ObjectId(
        test_automation_rule_details.get("rule_id")
    )
    automation_activity = (
        await DatabaseConfiguration().automation_activity_collection.insert_one(
            test_automation_rule_details
        )
    )
    return str(automation_activity.inserted_id)


@pytest.fixture
async def test_add_timeline(test_user_validation):
    """
    Add timeline of user
    """
    from app.celery_tasks.celery_add_user_timeline import UserActivity

    UserActivity().add_user_timeline(
        test_user_validation, event_type="Test", event_status="Completed"
    )


@pytest.fixture
async def test_otp_template_validation(test_template_data, test_user_validation):
    """
    Return otp template data, if template data not found then it will create it
    """
    from app.database.configuration import DatabaseConfiguration
    from datetime import datetime
    from app.core.utils import utility_obj

    template = await DatabaseConfiguration().otp_template_collection.find_one({})
    if not template:
        test_template_data["last_modified_timeline"] = [
            {
                "last_modified_at": datetime.utcnow(),
                "user_id": ObjectId(str(test_user_validation.get("_id"))),
                "user_name": utility_obj.name_can(test_user_validation),
            }
        ]
        await DatabaseConfiguration().otp_template_collection.insert_one(
            test_template_data
        )
    template = await DatabaseConfiguration().otp_template_collection.find_one({})
    return template


@pytest.fixture
async def test_client_manager_validation(test_super_admin_validation, test_user_data):
    """
    Return client manager data, it will create user of type client_manager in
    test DB collection if user not exist.
    Using test user data for create student."""
    from app.database.configuration import DatabaseConfiguration
    from app.helpers.user_curd.user_configuration import UserHelper

    test_user_data["email"] = "user255@gmail.com"
    test_user_data["mobile_number"] = 8575767899
    test_user_data["full_name"] = "client manager"
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": test_user_data["email"]}
    )
    if not user:
        await UserHelper().create_user(
            test_user_data, settings.superadmin_username, "client_manager"
        )
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": test_user_data["email"]}
    )
    return user


@pytest.fixture
async def client_manager_access_token(test_client_manager_validation):
    """
    Get the access token of super_admin user which we can be used for
    authenticate super_admin
    """
    token = await Authentication().create_access_token(
        data={
            "sub": test_client_manager_validation.get("user_name"),
            "scopes": [test_client_manager_validation.get("role", {}).get("role_name")],
        },
        expires_delta=timedelta(hours=1),
    )
    return token


@pytest.fixture
def test_component_charges():
    """
    Return component charges
    """
    return {
        "raw_data_module": 1000,
        "lead_management_system": 1000,
        "app_management_system": 1000,
        "lead": 2000,
        "counselor_account": 150,
        "client_manager_account": 50,
        "publisher_account": 100,
        "email": 1,
        "sms": 1,
        "whatsapp": 2,
    }


@pytest.fixture
async def test_component_charges_validation(test_component_charges):
    """
    Return component charges details
    """
    from app.helpers.college_configuration import CollegeHelper

    return await CollegeHelper().get_component_charges()


@pytest.fixture
async def test_form_details_validation(test_component_charges):
    """
    Return form details
    """
    from app.helpers.college_configuration import CollegeHelper

    return await CollegeHelper().get_form_details()


@pytest.fixture
async def test_health_science_course_validation(test_college_validation):
    """Return health science course data, it will create health science course
     in test DB collection of course not exist.
    Using test course data for create course."""
    from app.database.configuration import DatabaseConfiguration

    course = await DatabaseConfiguration().health_science_courses_collection.find_one(
        {"college_id": test_college_validation.get("_id")}
    )
    if not course:
        await DatabaseConfiguration().health_science_courses_collection.insert_one(
            {
                "course_name": "test",
                "course_description": "test",
                "duration": "3 Years",
                "fees": "Rs.1000.0/-",
                "is_activated": True,
                "banner_image_url": None,
                "course_specialization": [
                    {
                        "spec_name": "Anesthesiology & Operation Theatre Technology",
                        "is_activated": True,
                    }
                ],
                "college_id": test_college_validation.get("_id"),
                "is_pg": False,
            }
        )
    course = await DatabaseConfiguration().health_science_courses_collection.find_one(
        {
            "college_id": test_college_validation.get("_id"),
        }
    )
    return course


@pytest.fixture
def test_event_data():
    """
    Get event data
    """
    return {
        "event_name": "test",
        "event_start_date": datetime.utcnow().strftime("%d/%m/%Y"),
        "event_end_date": datetime.utcnow().strftime("%d/%m/%Y"),
        "event_type": "test",
        "event_description": "string",
        "learning": "string",
    }


@pytest.fixture
def test_action_payload_data(test_offline_data_validation):
    """
    Get payload for perform action on raw data leads
    """
    return {
        "offline_ids": [str(test_offline_data_validation.get("_id"))],
        "template": "test",
        "subject": "test",
        "sms_content": "test",
        "dlt_content_id": "1007092019441212345",
        "sms_type": "Service Explicit",
        "sender_name": "AIMSAR",
        "whatsapp_text": "string",
    }


@pytest.fixture
async def test_create_student_by_publisher(
        test_student_data, test_user_publisher_validation
):
    """
    Create student by publisher, it will create student in test DB collection
    if student not exist. Using test student data for create student.
    """
    from app.database.configuration import DatabaseConfiguration
    from app.helpers.student_curd.student_user_crud_configuration import (
        StudentUserCrudHelper,
    )

    test_student_data["email"] = "testpublisher@gmail.com"
    test_student_data["mobile_number"] = "3333333333"
    student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": test_student_data["email"]}
    )
    if not student:
        await StudentUserCrudHelper().student_register(
            test_student_data,
            publisher_id=str(test_user_publisher_validation.get("_id")),
            lead_type="api",
        )
    student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": test_student_data["email"]}
    )
    return student


@pytest.fixture
async def test_tag_list_validation(test_template_validation):
    """
    Get tag list data, if tag list data not found then it will create it
    """
    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().tag_list_collection.delete_many({})
    await DatabaseConfiguration().tag_list_collection.insert_one(
        {
            "tag_name": "test",
            "associated_templates": [test_template_validation.get("_id")],
            "template_type": ["email"],
        }
    )
    tag_data = await DatabaseConfiguration().tag_list_collection.find_one({})
    return tag_data


@pytest.fixture
async def test_jwt_token_with_wrong_username():
    """
    create token for wrong user_name who is not exists in our collection
    """
    from app.dependencies.jwttoken import Authentication

    data = {"sub": "vvvvvv@gmail.com", "scopes": ["student"]}
    return await Authentication().create_access_token(data)


@pytest.fixture
async def test_jwt_token(test_student_validation):
    """
    create token for user_name who is exists in our collection
    """
    from app.dependencies.jwttoken import Authentication

    data = {"sub": test_student_validation.get("user_name"), "scopes": ["student"]}
    return await Authentication().create_access_token(data)


@pytest.fixture
async def test_template_validation_2(test_template_data, test_user_validation):
    """
    Return template data, if template data not found then it will create it
    """
    from app.database.configuration import DatabaseConfiguration
    from datetime import datetime
    from app.core.utils import utility_obj

    test_template_data["last_modified_timeline"] = [
        {
            "last_modified_at": datetime.utcnow(),
            "user_id": ObjectId(str(test_user_validation.get("_id"))),
            "user_name": utility_obj.name_can(test_user_validation),
        }
    ]
    template = await DatabaseConfiguration().template_collection.insert_one(
        test_template_data
    )
    new_template = await DatabaseConfiguration().template_collection.find_one(
        {"_id": template.inserted_id}
    )
    return new_template


@pytest.fixture
async def test_sms_template_validation(test_template_data, test_user_validation):
    """
    Return template data, if template data not found then it will create it
    """
    from app.database.configuration import DatabaseConfiguration
    from datetime import datetime
    from app.core.utils import utility_obj

    test_template_data.update(
        {
            "last_modified_timeline": [
                {
                    "last_modified_at": datetime.utcnow(),
                    "user_id": ObjectId(str(test_user_validation.get("_id"))),
                    "user_name": utility_obj.name_can(test_user_validation),
                }
            ],
            "template_type": "sms",
            "sms_category": "otp",
        }
    )
    template = await DatabaseConfiguration().template_collection.insert_one(
        test_template_data
    )
    new_template = await DatabaseConfiguration().template_collection.find_one(
        {"_id": template.inserted_id}
    )
    return new_template


@pytest.fixture
async def test_field_mapping_validation(test_component_charges):
    """
    Return form details
    """
    from app.helpers.college_configuration import CollegeHelper

    return await CollegeHelper().get_existing_fields()


@pytest.fixture
async def student_refresh_token(test_student_validation):
    """
    Get the refresh token of student which we can be used for authenticate
    student
    """
    token = await Authentication().create_refresh_token(
        data={
            "sub": str(test_student_validation["_id"]),
            "type": "refresh",
            "college_info": [
                {"name": "test", "_id": str(test_student_validation.get("college_id"))}
            ],
        }
    )
    return token


@pytest.fixture
def test_interview_list_data(
        test_user_validation, application_details, test_course_validation
):
    """
    Get dummy interview list data for perform operation.
    """
    return {
        "school_name": "test",
        "list_name": "test",
        "course_name": test_course_validation.get("course_name"),
        "specialization_name": test_course_validation.get("course_specialization")[
            0
        ].get("spec_name"),
        "moderator_id": str(test_user_validation.get("_id")),
        "eligible_applications": [str(application_details.get("_id"))],
        "application_ids": [str(application_details.get("_id"))],
    }


@pytest.fixture
async def test_interview_list_validation(
        test_user_validation, test_interview_list_data
):
    """
    Delete existing interview lists. After that create interview list and
    return interview list data.
    """
    from app.database.configuration import DatabaseConfiguration
    from app.helpers.interview_module.interview_list_configuration import InterviewList

    await DatabaseConfiguration().interview_list_collection.delete_many({})
    await InterviewList().create_or_update_interview_list(
        test_user_validation, test_interview_list_data, None
    )
    return await DatabaseConfiguration().interview_list_collection.find_one({})


@pytest.fixture
def test_panelist_data(test_user_validation, test_course_validation):
    """
    Get dummy panelist data
    """
    return {
        "full_name": "string string string",
        "mobile_number": 7576756757,
        "associated_colleges": [
            str(test_user_validation.get("associated_colleges")[0])
        ],
        "email": "testpanelist@example.com",
        "designation": "Test",
        "school_name": "test",
        "selected_programs": [
            {
                "course_name": test_course_validation.get("course_name"),
                "specialization_name": str(
                    test_course_validation.get("course_specialization")[0]
                ),
            }
        ],
    }


@pytest.fixture
async def test_panelist_validation(test_user_validation, test_panelist_data):
    """Return user data, it will create user of type panelist in test DB
    collection if user not exist. Using test user data for create panelist."""
    from app.database.configuration import DatabaseConfiguration
    from app.helpers.user_curd.user_configuration import UserHelper

    user = await DatabaseConfiguration().user_collection.find_one(
        {"role.role_name": "panelist"}
    )
    if not user:
        await UserHelper().create_user(
            test_panelist_data, test_user_validation.get("user_name"), "panelist"
        )
        user = await DatabaseConfiguration().user_collection.find_one(
            {"role.role_name": "panelist"}
        )
    return user


@pytest.fixture
def test_panel_data(test_interview_list_validation, test_panelist_validation):
    """
    Get dummy panel data for perform operation.
    """
    current_date = datetime.utcnow()
    end_date = current_date + timedelta(hours=3)
    start_time = current_date.strftime("%d/%m/%Y %I:%M %p")
    end_time = end_date.strftime("%d/%m/%Y %I:%M %p")
    return {
        "name": "string",
        "description": "string",
        "slot_type": "GD",
        "panel_type": "Online",
        "user_limit": 10,
        "panel_duration": "180",
        "gap_between_slots": "30",
        "interview_list_id": str(test_interview_list_validation.get("_id")),
        "panelists": [str(test_panelist_validation.get("_id"))],
        "slot_count": "2",
        "slot_duration": "60",
        "status": "Draft",
        "time": start_time,
        "end_time": end_time,
    }


@pytest.fixture
async def test_panel_validation(test_user_data, test_user_validation, test_panel_data):
    """
    Create panel if not exists.
    """
    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().panel_collection.delete_many({})
    from app.helpers.interview_module.planner_configuration import Planner

    await Planner().create_or_update_panel(
        test_user_validation, test_panel_data, None
    )
    return await DatabaseConfiguration().panel_collection.find_one({})


@pytest.fixture
def test_slot_data(
        test_interview_list_validation, test_panelist_validation, test_panel_validation
):
    """
    Get dummy slot data for perform operation.
    """
    current_date = datetime.utcnow()
    end_date = current_date + timedelta(hours=1)
    start_time = current_date.strftime("%d/%m/%Y %I:%M %p")
    end_time = end_date.strftime("%d/%m/%Y %I:%M %p")
    return {
        "name": "string",
        "description": "string",
        "slot_type": "GD",
        "interview_mode": "Online",
        "interview_list_id": str(test_interview_list_validation.get("_id")),
        "panelists": [str(test_panelist_validation.get("_id"))],
        "user_limit": 10,
        "status": "Draft",
        "time": start_time,
        "end_time": end_time,
    }


@pytest.fixture
async def test_create_interview_list(application_details):
    """Insert data in interview module"""
    from app.database.configuration import DatabaseConfiguration

    data = {
        "school_name": "School of Technology",
        "course_name": "B.Sc.",
        "specialization_name": "Physician Assistant",
        "list_name": "test",
        "description": "test",
        "moderator_id": ObjectId("64a51777154d1564eb0453a8"),
        "moderator_name": "String",
        "created_by": ObjectId("6290c40ee87e304387308492"),
        "created_by_name": "apollo college super",
        "created_at": {"$date": "2023-07-12T07:28:40.767Z"},
        "last_modified_timeline": [
            {
                "last_modified_at": {"$date": "2023-07-12T14:10:56.044Z"},
                "user_id": {"$oid": "6290c40ee87e304387308492"},
                "user_name": "apollo college super",
            },
            {
                "last_modified_at": {"$date": "2023-07-12T12:43:04.899Z"},
                "user_id": ObjectId("6290c40ee87e304387308492"),
                "user_name": "apollo college super",
            },
            {
                "last_modified_at": {"$date": "2023-07-12T09:44:31.164Z"},
                "user_id": ObjectId("6290c40ee87e304387308492"),
                "user_name": "apollo college super",
            },
            {
                "last_modified_at": {"$date": "2023-07-12T07:28:40.767Z"},
                "user_id": {"$oid": "6290c40ee87e304387308492"},
                "user_name": "apollo college super",
            },
        ],
        "status": "Active",
        "application_ids": [ObjectId(application_details.get("_id"))],
    }
    doc_count = await DatabaseConfiguration().interview_list_collection.count_documents(
        {}
    )
    if doc_count <= 1:
        await DatabaseConfiguration().interview_list_collection.insert_one(data)
    return [
        data
        for data in await DatabaseConfiguration().interview_list_collection.find({})
    ]


@pytest.fixture
async def test_extracted_details(test_student_validation):
    """
    get dummy extracted data
    """
    from app.database.configuration import DatabaseConfiguration

    student = test_student_validation.get("_id")
    new_document = {
        "student_id": ObjectId(student),
        "document_analysis": {
            "high_school_analysis": {
                "data": {
                    "name": "test",
                    "board": "null",
                    "year_of_passing": "null",
                    "marking_scheme": "null",
                    "obtained_cgpa": "null",
                    "registration_number": "null",
                    "date_of_birth": "31/02/2023",
                    "caste": "null",
                    "board_accuracy": "99",
                    "year_of_passing_accuracy": "99",
                    "marking_scheme_accuracy": "99",
                    "obtained_cgpa_accuracy": "99",
                    "registration_number_accuracy": "99",
                    "date_of_birth_accuracy": "99",
                }
            },
            "senior_school_analysis": {
                "data": {
                    "name": "test",
                    "board": "null",
                    "year_of_passing": "null",
                    "marking_scheme": "null",
                    "obtained_cgpa": "null",
                    "registration_number": "null",
                    "date_of_birth": "31/2/2000",
                    "caste": "null",
                    "board_accuracy": "99",
                    "year_of_passing_accuracy": "99",
                    "marking_scheme_accuracy": "99",
                    "obtained_cgpa_accuracy": "99",
                    "registration_number_accuracy": "99",
                    "date_of_birth_accuracy": "99",
                },
            },
            "graduation_analysis": {
                "data": {
                    "name": "test",
                    "board": "null",
                    "year_of_passing": "null",
                    "marking_scheme": "null",
                    "obtained_cgpa": "null",
                    "registration_number": "null",
                    "date_of_birth": "31/02/2031",
                    "caste": "null",
                    "board_accuracy": "99",
                    "year_of_passing_accuracy": "99",
                    "marking_scheme_accuracy": "99",
                    "obtained_cgpa_accuracy": "99",
                    "registration_number_accuracy": "99",
                    "date_of_birth_accuracy": "99",
                },
            },
        },
    }
    await DatabaseConfiguration().studentSecondaryDetails.insert_one(new_document)


@pytest.fixture
async def test_slot_details(test_user_data, test_user_validation, test_slot_data):
    """
    Create panel if not exists.
    """
    from app.database.configuration import DatabaseConfiguration
    from app.helpers.interview_module.planner_configuration import Planner

    await Planner().create_or_update_slot(
        test_user_validation, test_slot_data, None
    )
    return await DatabaseConfiguration().slot_collection.find_one({})


@pytest.fixture
def test_month_year():
    """
    Return sample month and year
    """
    return {
        "day": 20,
        "month": 7,
        "year": 2023,
        "date": "20/07/2023",
        "date_YMD": "2023-07-12",
    }


@pytest.fixture
async def panelist_access_token(test_panelist_validation):
    """
    Get the access token of panelist for access authorized APIs.
    """
    token = await Authentication().create_access_token(
        data={"sub": test_panelist_validation["user_name"], "scopes": ["panelist"]},
        expires_delta=timedelta(hours=1),
    )
    return token


@pytest.fixture
async def test_marking_details_by_programname(test_course_validation):
    """inserts sample gi pd parameters in interviewselectionprocess database"""
    from app.database.configuration import DatabaseConfiguration

    sample = {
        "course_name": test_course_validation.get("course_name"),
        "specialization_name": test_course_validation.get("course_specialization")[1][
            "spec_name"
        ],
        "gi_parameters_weightage": {},
        "pi_parameters_weightage": {},
    }
    await DatabaseConfiguration().selection_procedure_collection.insert_one(sample)
    return sample


@pytest.fixture
async def test_selection_procedure_validation(
        http_client_test,
        test_user_validation,
        test_college_validation,
        test_course_validation,
        college_super_admin_access_token,
):
    from app.database.configuration import DatabaseConfiguration
    feature_key = user_feature_data()
    await DatabaseConfiguration().selection_procedure_collection.delete_many({})
    await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "course_name": test_course_validation.get("course_name"),
            "specialization_name": test_course_validation.get("course_specialization")[
                0
            ].get("spec_name"),
            "offer_letter": {
                "template": "test",
                "authorized_approver": str(test_user_validation.get("_id")),
            },
        },
    )


@pytest.fixture
async def test_student_profile_details(
        test_student_validation, test_student_education_details
):
    """inserts sample details of student in different databases"""
    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().studentSecondaryDetails.insert_one(
        {
            "student_id": test_student_validation.get("_id"),
            "education_details": test_student_education_details,
        }
    )


@pytest.fixture
async def test_take_slot(
        test_slot_details, application_details, test_panelist_validation
):
    """inserts sample take slot information in slots database"""
    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().slot_collection.update_one(
        {"_id": test_slot_details.get("_id")},
        {
            "$set": {
                "take_slot": {
                    "application": True,
                    "panelist": True,
                    "panelist_ids": [test_panelist_validation.get("_id")],
                    "application_ids": [application_details.get("_id")],
                }
            }
        },
    )


@pytest.fixture
async def test_meeting_validation(
        test_user_validation,
        test_slot_details,
        test_panelist_validation,
        application_details,
):
    """inserts sample take slot information in slots database"""
    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().meeting_collection.delete_many({})
    current_date = datetime.utcnow()
    end_time = current_date + timedelta(hours=1)
    await DatabaseConfiguration().meeting_collection.insert_one(
        {
            "meeting_type": test_slot_details.get("slot_type"),
            "user_limit": test_slot_details.get("user_limit"),
            "panel_id": test_slot_details.get("panel_id"),
            "slot_id": test_slot_details.get("_id"),
            "interview_mode": "Online",
            "panelists": [test_panelist_validation.get("_id")],
            "interview_list_id": test_slot_details.get("interview_list_id"),
            "status": "Scheduled",
            "duration": 60,
            "applicants": [application_details.get("_id")],
            "start_time": current_date,
            "end_time": end_time,
            "available_slot": "Open",
            "booked_user": 2,
            "zoom_link": "zoom.com",
            "meeting_id": 12345678901,
            "passcode": "123456",
        }
    )
    return await DatabaseConfiguration().meeting_collection.find_one({})


@pytest.fixture
async def test_template_merge_fields(test_college_validation):
    """
    Add template merge fields if not exist otherwise return merge fields.

    Params:
        test_college_validation (dict): A fixture which add college data
            if not exist and return college data.

    Returns:
        dict: A dictionary which contains template merge fields.
    """
    from app.database.configuration import DatabaseConfiguration

    merge_fields = (
        await DatabaseConfiguration().template_merge_fields_collection.find_one(
            {"college_id": test_college_validation.get("_id")}
        )
    )
    if not merge_fields:
        await DatabaseConfiguration().template_merge_fields_collection.insert_one(
            {
                "college_id": test_college_validation.get("_id"),
                "merge_fields": [{"field_name": "test", "value": ""}],
            }
        )
        merge_fields = (
            await DatabaseConfiguration().template_merge_fields_collection.find_one(
                {"college_id": test_college_validation.get("_id")}
            )
        )
    return merge_fields


@pytest.fixture
async def test_key_category_validation(
        http_client_test, test_college_validation, college_super_admin_access_token
):
    """
    Add key category.

    Params:
        - http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        - test_college_validation (dict): A fixture which add college data
            if not exist and return college data.
        - college_super_admin_access_token (dict): A fixture which useful for get
            college super admin access token.

    Returns:
        None: not return anything
    """
    feature_key = user_feature_data()
    await http_client_test.post(
        f"/resource/create_key_category/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
        json={"category_name": "test"},
    )


@pytest.fixture
async def test_question_validation(
        http_client_test, test_college_validation, college_super_admin_access_token
):
    """
    Add a question.

    Params:
        - http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        - test_college_validation (dict): A fixture which add college data
            if not exist and return college data.
        - college_super_admin_access_token (dict): A fixture which useful for
            get college super admin access token.

    Returns:
        None: not return anything
    """
    from app.database.configuration import DatabaseConfiguration
    feature_key = user_feature_data()
    await DatabaseConfiguration().questions.delete_many({})
    await http_client_test.post(
        f"/resource/create_or_update_a_question/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
        json={"question": "test", "answer": "test", "tags": ["Test"]},
    )


@pytest.fixture
async def test_script_data():
    """inserts sample script and return it"""
    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().scripts_details.insert_one(
        {
            "script_name": "Testing",
            "program_name": ["test"],
            "source_name": [],
            "lead_stage": ["Interested", "Not Interested"],
            "tags": ["tech"],
            "application_stage": None,
            "script_text": "Random Testing, also known as monkey testing, "
                           "is a form of functional black box testing that "
                           "is performed when there is not enough time to "
                           "write and execute the tests.",
            "save_or_draft": True,
        }
    )
    return await DatabaseConfiguration().scripts_details.find_one({})


@pytest.fixture
async def test_report_template_data():
    """Inserts sample report template and return it"""
    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().report_collection.insert_one(
        {
            "report_name": "testing",
            "report_details": "testing",
            "report_type": "All Application data",
            "date_range": {"start_date": "2023-03-30", "end_date": "2023-03-30"},
            "statement": "2023-03-30 to 2023-03-30",
            "format": "CSV",
        }
    )
    return await DatabaseConfiguration().report_collection.find_one({})


@pytest.fixture
async def test_report_validation(
        http_client_test,
        test_college_validation,
        test_generate_report_data,
        college_super_admin_access_token,
):
    """
    Delete all existing reports and create a new report.
    """
    from app.database.configuration import DatabaseConfiguration
    feature_key = user_feature_data()
    await DatabaseConfiguration().report_collection.delete_many({})
    await http_client_test.post(
        f"/reports/generate_request_data/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
        json={"request_data": test_generate_report_data},
    )


@pytest.fixture
async def test_schedule_report_validation(
        http_client_test,
        test_college_validation,
        test_generate_report_data,
        college_super_admin_access_token,
):
    """
    Delete all existing reschedule reports and create a new reschedule report.
    """
    from app.database.configuration import DatabaseConfiguration
    feature_key = user_feature_data()
    await DatabaseConfiguration().report_collection.delete_many(
        {"reschedule_report": True}
    )
    test_generate_report_data.update(
        {"reschedule_report": True, "schedule_value": 1, "schedule_type": "Day"}
    )
    await http_client_test.post(
        f"/reports/generate_request_data/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
        json={"request_data": test_generate_report_data},
    )


@pytest.fixture
async def test_auto_schedule_report_validation(
        http_client_test,
        test_college_validation,
        test_generate_report_data,
        college_super_admin_access_token,
):
    """
    Delete all existing auto schedule reports and create a new auto schedule
    report.
    """
    from app.database.configuration import DatabaseConfiguration
    feature_key = user_feature_data()
    await DatabaseConfiguration().report_collection.delete_many(
        {"is_auto_schedule": True}
    )
    today_date = datetime.utcnow()
    format_date = today_date.strftime("%Y-%m-%d")
    test_generate_report_data.update(
        {
            "report_name": "auto_reschedule",
            "reschedule_report": False,
            "save_template": False,
            "is_auto_schedule": True,
            "generate_and_reschedule": {
                "trigger_by": "Weekly",
                "interval": 2,
                "date_range": {"start_date": format_date, "end_date": format_date},
            },
        }
    )
    await http_client_test.post(
        f"/reports/generate_request_data/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer " f"{college_super_admin_access_token}"},
        json={"request_data": test_generate_report_data},
    )


@pytest.fixture
async def test_promocode(http_client_test, test_college_validation):
    """
    Fixture to add promocode details and return the same
    """
    from app.database.configuration import DatabaseConfiguration

    now = datetime.utcnow()
    payload = {
        "name": "test",
        "discount": 50,
        "code": "test_promocode",
        "units": 0,
        "duration": {
            "start_date": now + timedelta(days=1),
            "end_date": now + timedelta(days=5),
        },
    }
    await DatabaseConfiguration().promocode_collection.insert_one(payload)
    return await DatabaseConfiguration().promocode_collection.find_one({})


@pytest.fixture
async def test_voucher(test_course_validation, test_counselor_validation):
    """
    Fixture to add voucher details and return the same
    """
    from app.database.configuration import DatabaseConfiguration

    now = datetime.utcnow()
    payload = {
        "name": "string",
        "quantity": 1,
        "cost_per_voucher": 100,
        "applied_count": 0,
        "duration": {
            "start_date": now + timedelta(days=1),
            "end_date": now + timedelta(days=4),
        },
        "program_name": [
            {
                "course_id": test_course_validation.get("_id"),
                "course_name": "test",
                "spec_name": "sample",
            }
        ],
        "assign_to": test_counselor_validation.get("_id"),
        "vouchers": [{"code": "sam12300", "used": False}],
    }
    if (data := await DatabaseConfiguration().voucher_collection.find_one({})) is None:
        await DatabaseConfiguration().voucher_collection.insert_one(payload)
        data = await DatabaseConfiguration().voucher_collection.find_one({})
    return data


@pytest.fixture
async def test_master_sub_stages():
    """Insert test stage data into the database and return the inserted document."""
    from app.database.configuration import DatabaseConfiguration
    data = {
        "_id": (result := await DatabaseConfiguration().sub_stages.insert_one({
            "sub_stage_name": "Address for Correspondence",
            "fields": [
                {
                    "name": "address_line_1",
                    "label": "Address Line 1",
                    "type": "text",
                    "is_required": True,
                    "description": "Primary address line.",
                    "locked": False,
                    "is_custom": False,
                    "depends_on": None,
                    "error": "",
                    "value": "",
                },
                {
                    "name": "country",
                    "label": "Country",
                    "type": "text",
                    "is_required": True,
                    "description": "Country of the address.",
                    "locked": True,
                    "is_custom": False,
                    "depends_on": None,
                    "error": "",
                    "value": "",
                },
                {
                    "name": "state",
                    "label": "State",
                    "type": "text",
                    "is_required": True,
                    "description": "State of the address.",
                    "locked": True,
                    "is_custom": False,
                    "depends_on": "country",
                    "error": "",
                    "value": "",
                    "reset": True,
                },
                {
                    "name": "city",
                    "label": "City",
                    "type": "text",
                    "is_required": True,
                    "description": "City of the address.",
                    "locked": True,
                    "is_custom": False,
                    "depends_on": "state",
                    "error": "",
                    "value": "",
                    "reset": True,
                },
            ],
        })).inserted_id
    }
    return data


@pytest.fixture
async def test_master_stages():
    """Insert test stage data into the database and return the inserted document."""
    from app.database.configuration import DatabaseConfiguration
    data = {
        "_id": (result := await DatabaseConfiguration().stages.insert_one({
            "stage_name": "Basic Details",
            "stage_order": 1,
            "sub_stages": [
                {
                    "sub_stage_id": "67c8302d94870eb19c7a5432",
                    "sub_stage_order": 1
                },
                {
                    "sub_stage_id": "67d29460ce936fe03506ee96",
                    "sub_stage_order": 3
                }
            ]
        })).inserted_id
    }
    return data


@pytest.fixture
async def test_signup_form():
    """
    Fixture returning a sample request body for the signup form.
    """
    return {
        "student_registration_form_fields": [
            {
                "key_name": "full_name",
                "field_name": "Full Name",
                "field_type": "text",
                "is_mandatory": True,
                "description": "Full name of Student",
                "locked": True,
                "is_custom": False,
                "depends_on": None,
                "value": "John Doe",
                "error": "",
                "editable": False,
                "can_remove": False,
                "options": []
            }
        ]
    }


async def add_course_data(_id, college_id):
    """
    Asynchronously constructs and returns a default course document for a given college.

    Params:
        college (dict): A dictionary representing the college, expected to contain an "_id" and
                        a "course_details" list with at least one course_id.

    Returns:
        dict: A dictionary representing the course data, including course name, type, fees,
              specialization names, activation status, and associated college ID.
    """
    return {
        "_id": _id,
        "course_name": "BSc Computer Science Engineering",
        "school_name": "CSE",
        "course_type": "UG",
        "is_activated": True,
        "course_fees": 5000.5,
        "specialization_names": [
            {"spec_name": "Artificial Intelligence", "is_activated": True},
            {"spec_name": "Cyber Security", "is_activated": True}
        ],
        "college_id": college_id
    }


@pytest.fixture
async def test_application_form(test_college_data, test_super_admin_validation):
    """
    Pytest fixture that retrieves or creates a test student application form configuration for a given test college.

    This fixture:
    - Attempts to find an existing form document in the `college_form_details` collection where `college_id` and
      `course_id` are present, and the `dashboard_type` is "student_dashboard".
    - If no such form exists, it looks up the test college in the `college_collection`. If the college is not found,
      it creates a new one using the helper method `create_new_college`.
    - Constructs a new default application form with three steps: "Program / Preference Details", "Basic Details"
      (including "First Name" and "Last Name" fields), and "Declaration".
    - Inserts the newly created form into the `college_form_details` collection.

    Returns:
        dict: The existing or newly created application form document.
    """
    from app.database.configuration import DatabaseConfiguration
    from app.helpers.college_configuration import CollegeHelper
    result = await DatabaseConfiguration().college_form_details.find_one({
        "college_id": {"$exists": True, "$ne": None},
        "course_id": {"$exists": True, "$ne": None},
        "dashboard_type": "college_student_dashboard"
    })

    if result:
        return result

    college = await DatabaseConfiguration().college_collection.find_one(
        {"name": str(test_college_data["name"]).title()}
    )
    if college:
        college_id = college.get("_id")
        course_id = college.get("course_details", [{}])[0].get("course_id")
        if not await DatabaseConfiguration().college_course_collection.find_one(
                {"_id": course_id}
        ):
            course_entry = await add_course_data(course_id, college_id)
            await DatabaseConfiguration().college_course_collection.insert_one(course_entry)
    else:
        college = await CollegeHelper().create_new_college(
            test_college_data, test_super_admin_validation
        )
        course_id = college.get("course_details")[0].get("course_id")
        college_id = ObjectId(college.get("id"))
        course_entry = await add_course_data(course_id, college_id)
        await DatabaseConfiguration().college_course_collection.insert_one(course_entry)
    result = {
        "_id": ObjectId(),
        "application_form": [
            {
                "step_id": "a3f9d2b7",
                "step_name": "Program / Preference Details",
                "is_locked": True,
                "no_sections": False,
                "not_draggable": True,
                "step_details": "Program / Preference Details fields will show according to the configuration"
            },
            {
                "step_id": "7c8e41f2",
                "step_name": "Basic Details",
                "sections": [
                    {
                        "section_title": "Personal Details",
                        "section_subtitle": "All Personal Details of Students",
                        "fields": [
                            {
                                "field_name": "First Name",
                                "field_type": "text",
                                "is_mandatory": True,
                                "editable": False,
                                "can_remove": False,
                                "value": "",
                                "error": "",
                                "key_name": "first_name",
                                "is_locked": True,
                                "is_readonly": True
                            },
                            {
                                "field_name": "Last Name",
                                "field_type": "text",
                                "is_mandatory": True,
                                "editable": False,
                                "can_remove": False,
                                "value": "",
                                "error": "",
                                "key_name": "last_name",
                                "is_locked": True,
                                "is_readonly": True
                            },
                        ]
                    },
                ]
            },
            {
                "step_id": "b937da1e",
                "step_name": "Declaration",
                "is_locked": True,
                "step_details": "Declaration content will show here",
                "no_sections": True,
                "not_draggable": True
            }
        ],
        "dashboard_type": "college_student_dashboard",
        "college_id": college_id,
        "course_id": course_id
    }
    await DatabaseConfiguration().college_form_details.insert_one(result)
    return result


@pytest.fixture
async def test_unique_key_name(test_college_validation):
    from app.database.configuration import DatabaseConfiguration
    """Insert test stage data into the database and return the inserted document."""
    test_college_id = test_college_validation.get("_id")
    data = {
        "_id": (result := await DatabaseConfiguration().stages.insert_one({
            "client_id": test_college_id,
            "college_id": test_college_id,
            "application_form": [
                {
                    "step_name": "Basic Details",
                    "sections": [
                        {
                            "section_title": "Personal Details",
                            "section_subtitle": "(Put details as per the 10th Standard Marksheet)",
                            "fields": [
                                {
                                    "field_name": "First Name",
                                    "field_type": "text",
                                    "is_mandatory": True,
                                    "editable": False,
                                    "can_remove": False,
                                    "value": "",
                                    "error": "",
                                    "key_name": "first_name",
                                    "is_locked": True,
                                    "is_readonly": True
                                },
                                {
                                    "field_name": "Middle Name",
                                    "field_type": "text",
                                    "is_mandatory": False,
                                    "editable": False,
                                    "can_remove": False,
                                    "value": "",
                                    "error": "",
                                    "key_name": "middle_name",
                                    "is_locked": True,
                                    "is_readonly": True
                                }
                            ]
                        }
                    ]
                }
            ]
        })).inserted_id
    }
    return data


@pytest.fixture()
def invalid_token():
    """Return invalid token required for testing apis."""
    return """eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Iko2bHdmOTJsT1FUY2RzUEtKc1hKRSJ9.eyJpc3MiOiJodHRwczovL2Rldi1pO
    Dd4bTU0dGJoc3YwNmVqLnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJhdXRoMHw2NWM1ZjhiNzlmZjlkY2UwMGNkN2YzY2IiLCJhdWQiOlsiaHR0cHM6Ly9kZ
    XYtaTg3eG01NHRiaHN2MDZlai51cy5hdXRoMC5jb20vYXBpL3YyLyIsImh0dHBzOi8vZGV2LWk4N3htNTR0YmhzdjA2ZWoudXMuYXV0aDAuY29tL3VzZ
    XJpbmZvIl0sImlhdCI6MTcxMDM0NjM5NSwiZXhwIjoxNzEwNDMyNzk1LCJhenAiOiI2Z0JneEVuNzk4OXBiajFSVXh6SVljRWZvUkhWUDVYVSIsInNjb
    3BlIjoicHJvZmlsZSBvcGVuaWQgZW1haWwgcmVhZDpjdXJyZW50X3VzZXIgdXBkYXRlOmN1cnJlbnRfdXNlcl9tZXRhZGF0YSBkZWxldGU6Y3VycmVud
    F91c2VyX21ldGFkYXRhIGNyZWF0ZTpjdXJyZW50X3VzZXJfbWV0YWRhdGEgY3JlYXRlOmN1cnJlbnRfdXNlcl9kZXZpY2VfY3JlZGVudGlhbHMgZGVsZ
    XRlOmN1cnJlbnRfdXNlcl9kZXZpY2VfY3JlZGVudGlhbHMgdXBkYXRlOmN1cnJlbnRfdXNlcl9pZGVudGl0aWVzIG9mZmxpbmVfYWNjZXNzIiwiZ3R5I
    joicGFzc3dvcmQifQ.nFUs3STXi4oadXpbJiHJHAo-A8tDhE6l7zNURjuuuz9TcArz-tIHl4hNNpc-2XfFogMlYLsiKpQDyvOgDfUGBlw18HNlwM_5_0
    umgNMdP0GxFGaQ4IzHAn6TEp4oAEQJDLlqgi4ixe_wwVPu3OkN6SWEjakG8A05oS7uwt8CFMDiN99s9RF3sjzgNaKL7ka2VUEFWZdckEOAARiwaLZEYQ
    nomMYLEPudRS5tUu6DBFOSugDZL_gBEQOMQPZgxKLHhSJa58T53Jxg7450DRkNQGKMnu-tEudZTYJxxeJLKdYWGf7DdibVFP0Dt6CLvkdIKKZCirXS39
    vuELK1z5KH2"""


@pytest.fixture
def master_data():
    """
    master screen data
    """
    return {
        "screen_details": [
            {
                "name": "string",
                "description": "string",
                "icon": "string",
                "amount": 0,
                "visibility": True,
                "need_api": True,
                "permissions": {
                    "read": True,
                    "write": True,
                    "delete": True
                },
                "features": [
                    {}
                ],
                "additionalProp1": {}
            }
        ]
    }


@pytest.fixture
async def test_client_stages(test_college_validation):
    """Insert test stage data into the database and return the inserted document."""
    data = {
        "stage_name": "Basic Details",
        "stage_order": 1,
        "client_id": test_college_validation.get("_id"),
        "college_id": test_college_validation.get("_id"),
        "sub_stages": [
            {
                "sub_stage_id": "67c8302d94870eb19c7a5432",
                "sub_stage_order": 1
            },
            {
                "sub_stage_id": "67d29460ce936fe03506ee96",
                "sub_stage_order": 3
            }
        ]
    }
    from app.database.configuration import DatabaseConfiguration
    result = await DatabaseConfiguration().client_stages.insert_one(data)
    data["_id"] = result.inserted_id
    return data


@pytest.fixture
async def test_client_sub_stages(test_college_validation):
    """Insert test sub stage data into the database and return the inserted document."""
    data = {
        "sub_stage_name": "Address for Correspondence",
        "client_id": test_college_validation.get("_id"),
        "college_id": test_college_validation.get("_id"),
        "fields": [
            {
                "name": "sample",
                "label": "Sample",
                "type": "text",
                "is_required": True,
                "description": "Sample",
                "is_custom": False,
                "error": "",
                "value": "",
                "reset": True,
            },
        ],
    }
    from app.database.configuration import DatabaseConfiguration
    result = await DatabaseConfiguration().client_sub_stages.insert_one(data)
    data["_id"] = result.inserted_id
    return data


@pytest.fixture
async def test_client_second_sub_stages(test_college_validation):
    """Insert test sub stage data into the database and return the inserted document."""
    data = {
        "sub_stage_name": "Sample Details",
        "client_id": test_college_validation.get("_id"),
        "college_id": test_college_validation.get("_id"),
        "fields": [
            {
                "name": "country",
                "label": "Country",
                "type": "text",
                "is_required": True,
                "description": "Country of the address.",
                "locked": True,
                "is_custom": False,
                "depends_on": None,
                "error": "",
                "value": "",
            },
            {
                "name": "state",
                "label": "State",
                "type": "text",
                "is_required": True,
                "description": "State of the address.",
                "locked": True,
                "is_custom": False,
                "depends_on": "country",
                "error": "",
                "value": "",
                "reset": True,
            }
        ],
    }
    from app.database.configuration import DatabaseConfiguration
    result = await DatabaseConfiguration().client_sub_stages.insert_one(data)
    data["_id"] = result.inserted_id
    return data


@pytest.fixture
async def client_screen_data():
    """
    Client screen data
    """
    return {
        "screen_details": [
            {
                "feature_id": "string",
                "name": "string",
                "description": "string",
                "icon": "string",
                "amount": 0,
                "visibility": True,
                "need_api": True,
                "permissions": {
                    "read": True,
                    "write": True,
                    "delete": True
                },
                "features": [
                    {}
                ],
                "additionalProp1": {}
            }
        ]
    }


@pytest.fixture
def test_create_scholarship_data(test_course_validation):
    """
    Return dummy scholarship data for create scholarship.
    """
    return {
        "name": "test scholarship",
        "programs": [
            {
                "course_name": test_course_validation.get("course_name"),
                "course_id": str(test_course_validation.get("_id")),
                "specialization_name": test_course_validation.get("course_specialization")[1].get(
                    "spec_name")
            }
        ],
        "count": 10,
        "waiver_type": "Percentage",
        "waiver_value": 10,
        "status": "Closed"
    }


@pytest.fixture
async def test_scholarship_validation(test_create_scholarship_data, application_details):
    """
    Get dummy scholarship details. If scholarship not exist in DB then create scholarship in the DB.
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().scholarship_collection.delete_many({})
    scholarship_info = await DatabaseConfiguration().scholarship_collection.find_one({
        "name": test_create_scholarship_data.get("name")
    })
    if not scholarship_info:
        created_scholarship = await DatabaseConfiguration().scholarship_collection.insert_one(
            test_create_scholarship_data)
        scholarship_id = created_scholarship.inserted_id
        scholarship_info = await DatabaseConfiguration().scholarship_collection.find_one({
            "_id": scholarship_id})
        application_id = application_details.get("_id")
        await DatabaseConfiguration().scholarship_collection.update_one(
            {"_id": scholarship_id},
            {"$set": {"offered_applicants": [application_id], "offered_applicants_count": 1,
                      "availed_applicants": [application_id], "availed_applicants_count": 1}})
        scholarship_name, waiver_type = scholarship_info.get("name"), scholarship_info.get(
            "waiver_type")
        waiver_value, template_id = scholarship_info.get("waiver_value"), scholarship_info.get(
            "template_id")
        template_name = scholarship_info.get("template_name")
        await DatabaseConfiguration().studentApplicationForms.update_one(
            {"_id": application_id}, {"$set": {"offered_scholarship_info": {
                "default_scholarship_id": scholarship_id,
                "default_scholarship_name": scholarship_info.get("name"),
                "default_scholarship_waiver_type": waiver_type,
                "default_scholarship_waiver_value": waiver_value,
                "description": "",
                "program_fee": 10000,
                "default_scholarship_fees_after_waiver": 9000,
                "default_scholarship_amount": 1000,
                "all_scholarship_info": [
                    {
                        "scholarship_id": scholarship_id,
                        "scholarship_name": scholarship_name,
                        "template_id": template_id,
                        "template_name": template_name,
                        "scholarship_waiver_type": waiver_type,
                        "scholarship_waiver_value": waiver_value,
                        "description": "",
                        "scholarship_letter_current_status": "Sent",
                        "fees_after_waiver": 9000,
                        "scholarship_amount": 1000
                    }
                ]
            }}})
    return scholarship_info


@pytest.fixture
async def test_stages(test_college_validation):
    """Insert test stage data into the database and return the inserted document."""
    data = {
        "application_form": [
            {
                "step_name": "Basic Details",
                "sections": [
                    {
                        "section_title": "Personal Details",
                        "section_subtitle": "(Put details as per the 10th Standard Marksheet)",
                        "fields": [
                            {
                                "field_name": "First Name",
                                "field_type": "text",
                                "is_mandatory": True,
                                "editable": False,
                                "can_remove": False,
                                "value": "",
                                "error": "",
                                "key_name": "first_name",
                                "is_locked": True,
                                "is_readonly": True
                            },
                            {
                                "field_name": "Middle Name",
                                "field_type": "text",
                                "is_mandatory": False,
                                "editable": False,
                                "can_remove": True,
                                "value": "",
                                "error": "",
                                "key_name": "middle_name",
                                "is_locked": False,
                                "is_readonly": True
                            }
                        ]
                    },
                    {
                        "section_title": "Parent/Guardians/Spouse Details",
                        "fields": [
                            {
                                "field_name": "Relationship With Student",
                                "field_type": "select",
                                "is_mandatory": True,
                                "editable": False,
                                "can_remove": False,
                                "value": "",
                                "error": "",
                                "key_name": "relationship_with_student",
                                "options": [
                                    "Father",
                                    "Mother",
                                    "Guardian",
                                    "Spouse",
                                    "Other"
                                ]
                            },
                            {
                                "field_name": "Mobile Number",
                                "field_type": "number",
                                "is_mandatory": True,
                                "editable": False,
                                "can_remove": True,
                                "value": "",
                                "error": "",
                                "key_name": "mobile_number",
                                "is_locked": False,
                                "is_readonly": True
                            }
                        ]
                    }
                ]
            }
        ],
        "client_id": test_college_validation.get("_id"),
        "college_id": test_college_validation.get("_id")
    }
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().stages.delete_many({})
    result = await DatabaseConfiguration().stages.insert_one(data)
    data["_id"] = result.inserted_id
    return data

@pytest.fixture
async def test_remove_field(test_college_validation):
    """Insert test stage data into the database and return the inserted document."""
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().stages.delete_many({})
    data = {
        "application_form": [
            {
                "step_name": "Education Details",
                "sections": [
                    {
                        "section_title": "Additional Details",
                        "fields": [
                            {
                                "field_name": "Your Name As Per Aadhar",
                                "field_type": "text",
                                "is_mandatory": False,
                                "editable": True,
                                "can_remove": True,
                                "value": "",
                                "error": "",
                                "key_name": "your_name_as_per_aadhar"
                            },
                            {
                                "field_name": "Aadhar Number",
                                "field_type": "number",
                                "is_mandatory": True,
                                "editable": True,
                                "can_remove": True,
                                "value": "",
                                "error": "",
                                "key_name": "aadhar_number"
                            },
                        ]
                    }
                ]
            },
        ],
        "client_id": test_college_validation.get("_id"),
        "college_id": test_college_validation.get("_id")}
    from app.database.configuration import DatabaseConfiguration
    result = await DatabaseConfiguration().stages.insert_one(data)
    data["_id"] = result.inserted_id
    return data


@pytest.fixture
async def test_remove_custom_field(test_client_validation, test_college_validation):
    """Insert test custom fields data into the database and return the inserted document."""
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().custom_fields.delete_many({})
    data = {
        "field_name": "Provisional Certificate",
        "field_type": "file",
        "key_name": "provisional_certificate",
        "is_mandatory": False,
        "options": ["string"],
        "selectVerification": "string",
        "isReadonly": False,
        "editable": True,
        "can_remove": True,
        "is_custom": True,
        "defaultValue": "string",
        "addOptionsFrom": "string",
        "apiFunction": "string",
        "with_field_upload_file": False,
        "separate_upload_API": True,
        "validations": [
            {
                "type": "",
                "value": "",
                "error_message": ""
            }
        ],
        "accepted_file_type": ["string"],
        "client_id": test_client_validation.get("_id"),
        "college_id": test_college_validation.get("_id"),
        "dashboard_type": "college_student_dashboard" if test_college_validation.get("_id") else "client_student_dashboard"
    }
    result = await DatabaseConfiguration().custom_fields.insert_one(data)
    data["_id"] = str(result.inserted_id)
    return data


@pytest.fixture
async def test_client_validation(test_college_validation):
    """
    This fixture sets the client_id in the client_collection using the _id of test_college_validation.
    It returns the updated client document.
    """
    college_id = test_college_validation.get("_id")
    college_name = test_college_validation.get("name")

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().client_collection.update_one(
        {"client_name": str(college_name).title()},
        {"$set": {"client_id": ObjectId(college_id)}}
    )
    updated_client = await DatabaseConfiguration().client_collection.find_one(
        {"client_id": ObjectId(college_id)}
    )
    return updated_client