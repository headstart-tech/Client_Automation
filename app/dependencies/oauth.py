"""
This file contain class and functions related to authentication
"""

import json
import random
import socket
import types
from datetime import datetime
from threading import Lock
from typing import Annotated, Any

import redis
import redis.asyncio as redis_async
from bson import ObjectId
from fastapi import Depends, HTTPException, Request
from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from starlette import status

from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, settings, CustomJSONEncoder
from app.database.configuration import DatabaseConfiguration
from app.database.database_sync import DatabaseConfigurationSync
from app.database.motor_base import pgsql_conn
from app.dependencies.hashing import Hash
from app.dependencies.jwttoken import Authentication
from app.helpers.student_curd.student_user_crud_configuration import (
    StudentUserCrudHelper,
)

logger = get_logger(name=__name__)

REDIS_MAX_CONNECTIONS = 3000

oauth2_student_scheme = OAuth2PasswordBearer(
    tokenUrl="/oauth/token",
    scopes={
        "student": "read/write student related data",
        "super_admin": "read/write super_admin related data",
        "admin": "read/write admin related data",
        "super_account_manager": "read/write super_account_manager related data",
        "account_manager": "read/write account_manager related data",
        "client_admin": "read/write college related data",
        "client_manager": "read/write client_manger related data",
        "college_super_admin": "read/write college admin related data",
        "college_admin": "read/write college manager related data",
        "college_head_counselor": "College head counsellor permission",
        "college_counselor": "This user will manage leads",
        "college_publisher_console": "Add students to the system",
        "moderator": "See interviewed students, "
                     "able to send offer letter to students",
        "panelist": "Take interview slot, perform interview procedure data.",
        "hod": "Scopes unclear",
        "authorized_approver": "Scopes unclear",
        "qa": "Review call and see statistics",
        "head_qa": "See review call statistics",
    },
)


class AuthenticateUser:
    """
    Contain functions related to authenticate user
    """

    async def create_refresh_token_and_store_data(
            self,
            authentication_obj,
            user_id,
            college,
            request,
            data,
            user_type,
            user_email,
            ip_address,
            name,
    ):
        """
        Create refresh token and store refresh token data in the DB.

        Params:
            authentication_obj: An object of class Authentication.
            user_id (str): The current user id.
            college (list): College information in a list format like
            [{"name": "Test", "_id": "1234"}].
            request (Request): The object of class Request.
            data (Request): A dictionary containing data which need to return.
            user_type (str): Type of current
            user_email (str): Email of current user.
            ip_address (str): IP address of user system.
            name (str): Name of current user.

        Returns:
            dict: A dictionary containing information which useful for
            authentication.

        """
        token_info = await authentication_obj.create_refresh_token(
            data={
                "sub": str(user_id),
                "type": "refresh",
                "college_info": college,
                "name": name,
                "user_id": str(user_id)
            }
        )
        await DatabaseConfiguration().refresh_token_collection.insert_one(
            {
                "user_id": user_id,
                "user_name": name,
                "user_type": user_type,
                "user_email": user_email,
                "refresh_token": token_info.get("refresh_token"),
                "expiry_time": token_info.pop("expiry_time"),
                "issued_at": token_info.pop("issued_at"),
                "revoked": False,
                "device_info": request.headers.get("user-agent"),
                "ip_address": ip_address,
            }
        )
        data.update({"refresh_token": token_info.pop("refresh_token")})
        return data

    async def get_application_details(self, student_id: str, college_id: str):
        """
        get application data for the payment

        params:
            student_id (str): Unique Identify number of the student

        returns:
            Response:In form of dictionary of application data
        """
        if (
                await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"accept_payment": True, "_id": ObjectId(student_id)}
                )
                is None
        ):
            return {}
        application = DatabaseConfiguration().studentApplicationForms.find(
            {"student_id": ObjectId(student_id), "college_id": ObjectId(college_id)}
        )
        application = [data async for data in application]
        application_details = sorted(application, key=lambda i: int(i["current_stage"]))
        if len(application_details) < 1:
            application_details = {}
        else:
            application_details = application_details[-1]
        if (
                course := await DatabaseConfiguration().course_collection.find_one(
                    {"_id": ObjectId(application_details.get("course_id"))}
                )
        ) is None:
            course = {}
        if (
                application_details.get("current_stage") > 2
                or application_details.get("payment_info", {}).get("status") == "captured"
        ):
            return {}
        return {
            "last_payment": {
                "application_id": str(application_details.get("_id")),
                "course_name": course.get("course_name", ""),
                "specialization_name": application_details.get("spec_name1"),
                "course_fees": course.get("fees"),
                "custom_application_id": application_details.get(
                    "custom_application_id"
                ),
                "accept_payment": (
                    True
                    if application_details.get("payment_info", {}).get("status")
                       == "captured"
                    else False
                ),
            }
        }

    async def authenticate_student(
            self,
            user_name: str,
            password: str,
            scopes: list,
            college_id: str,
            refresh_token=False,
            request=None,
    ):
        """
        Get the access token and token type of student user
        """
        await utility_obj.is_id_length_valid(_id=college_id, name="College id")
        college = await DatabaseConfiguration().college_collection.find_one(
            {"_id": ObjectId(college_id)}
        )
        if not college:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"College not found. Make sure " f"college id is valid.",
            )
        user = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"college_id": ObjectId(college_id), "user_name": user_name}
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No Student found with this {user_name} user_name",
            )
        if not Hash().verify_password(user.get("password"), password):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Wrong user_name or password",
            )
        college = await DatabaseConfiguration().college_collection.find_one(
            {"_id": ObjectId(college_id)}
        )
        authentication_obj = Authentication()
        college = [{"name": college.get("name"), "_id": college_id}]
        name = utility_obj.name_can(user.get("basic_details", {}))
        payload = {
            "sub": user.get("user_name"),
            "scopes": scopes,
            "college_info": college,
            "name": name,
        }
        access_token = await authentication_obj.create_access_token(data=payload)
        data = {"access_token": access_token, "token_type": "bearer"}
        ip_address = None
        if request:
            if await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": user.get("_id"), "system_info": {"$exists": False}}
            ):
                ip_address = utility_obj.get_ip_address(request)
                DatabaseConfiguration().studentsPrimaryDetails.update_one(
                    {"user_name": user_name},
                    {
                        "$set": {
                            "system_info": {
                                "device_info": request.headers.get("user-agent"),
                                "ip_address": ip_address,
                                "stored_at": datetime.utcnow(),
                            }
                        }
                    },
                )
        await StudentUserCrudHelper().update_verification_status(user)
        if refresh_token:
            data = await self.create_refresh_token_and_store_data(
                authentication_obj,
                user.get("_id"),
                college,
                request,
                data,
                scopes[0],
                user.get("user_name"),
                ip_address,
                name,
            )
        application = await self.get_application_details(
            student_id=str(user.get("_id")), college_id=str(college_id)
        )
        data.update(application)
        data.update({"_id": str(user.get("_id"))})
        return data

    # TODO : Roles is getting checked at later stage
    #  Improve current implementation solution where we can find both
    #  roles types and user_name in single query
    #  user Authentication Module - GTCRM-374
    async def authenticate_user(
            self,
            user_name: str,
            password: str,
            scopes: list,
            refresh_token=False,
            request=None,
            is_college_level_user=False
    ):
        """
        Verify the authentication of user by validation user_name, password
        and scope
        """
        user = await DatabaseConfiguration().user_collection.find_one(
            {"user_name": user_name}
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No user found with this {user_name} user_name",
            )
        if not user.get("is_activated"):
            raise HTTPException(422, detail="You are deactivated.")
        if not Hash().verify_password(user.get("password"), password):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Wrong user_name or password",
            )
        if user.get("role", {}).get("role_name") != scopes[0]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Wrong Scope Defined"
            )
        role_id = user.get("role", {}).get("role_id")
        if isinstance(role_id, ObjectId):
            role_id = str(role_id)
        group_ids = user.get("group_ids", [])
        authentication_obj = Authentication()
        name = utility_obj.name_can(user)
        payload = {"sub": user.get("user_name"), "scopes": scopes, "name": name,
                   "user_id": str(user.get("_id")), "role_id": role_id, "group_ids": group_ids}
        college = []
        for college_id in user.get("associated_colleges", []):
            if (
                    college_detail := await DatabaseConfiguration().college_collection.find_one(
                        {"_id": ObjectId(college_id)}
                    )
            ) is not None:
                college.append(
                    {"name": college_detail.get("name"), "_id": str(college_id)}
                )
        payload.update(
            {
                "college_info": college,
                "is_college_level_user": is_college_level_user
            }
        )
        access_token = await authentication_obj.create_access_token(data=payload)
        data = {"access_token": access_token, "token_type": "bearer"}
        ip_address = None
        if request:
            ip_address = utility_obj.get_ip_address(request)
        if refresh_token:
            data = await self.create_refresh_token_and_store_data(
                authentication_obj,
                user.get("_id"),
                college,
                request,
                data,
                scopes[0],
                user.get("user_name"),
                ip_address,
                name,
            )
        return data

    async def create_refresh_token_helper(self, student, request, college):
        """
        Create a refresh token helper
        """
        authentication_obj = Authentication()
        name = utility_obj.name_can(student.get("basic_details", {}))
        user_name = student.get("user_name")
        college_info = [{"name": college.get("name"), "_id": college.get("id")}]
        access_token = await authentication_obj.create_access_token(
            data={
                "sub": user_name,
                "scopes": ["student"],
                "name": name,
                "college_info": college_info,
            }
        )
        data = {"access_token": access_token, "token_type": "bearer"}
        ip_address = utility_obj.get_ip_address(request)
        return await self.create_refresh_token_and_store_data(
            authentication_obj,
            str(student.get("_id")),
            college_info,
            request,
            data,
            "student",
            user_name,
            ip_address,
            name=name,
        )


async def get_db():
    """ Dependency function to get the postgres database session """
    async with pgsql_conn.get_sqlalchemy_session() as session:
        yield session


# TODO : Get if user is active implementation
async def get_current_user(
        security_scopes: SecurityScopes, token: str = Depends(oauth2_student_scheme),
):
    """
    Get the user_name of logged-in user
    """
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = f"Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    token_data = await Authentication().verify_token(token, credentials_exception)
    if token_data.scopes[0] == "student":
        college_id = token_data.college_info[0].get("_id")
        toml_data = utility_obj.read_current_toml_file()
        if toml_data.get("testing", {}).get("test") is False:
            Reset_the_settings().check_college_mapped(college_id)
        if (
                user := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"user_name": token_data.user_name}
                )
        ) is None:
            raise HTTPException(status_code=404, detail="username not found")
        user_name = user["user_name"]
    else:
        user = await get_collection_from_cache(collection_name="users", field=token_data.user_name)
        if not user:
            user = await DatabaseConfiguration().user_collection.find_one(
                {"user_name": token_data.user_name})
            if user:
                await store_collection_in_cache(collection=user, collection_name="users",
                                                expiration_time=10800, field=token_data.user_name)
        if not user:
            raise HTTPException(status_code=404, detail="username not found")
        # Todo: we will deleted this hard coded after the introduce new logic
        toml_data = utility_obj.read_current_toml_file()
        if toml_data.get("testing", {}).get("test") is False:
            Reset_the_settings().check_college_mapped(
                college_id=user.get(
                    "associated_colleges", ["628dfd41ef796e8f757a5c13"]
                )[0]
            )
        user_name = user["user_name"]
    if user is None:
        raise credentials_exception

    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user_name


async def get_current_user_object(
    request: Request,
    security_scopes: SecurityScopes,
    feature_key: str,
    token: str = Depends(oauth2_student_scheme),
):
    """
    Retrieve the current user's data, including roles and permissions.

    This function verifies the authentication token, checks the user's role,
    and fetches user details from the database or cache. It ensures the user
    has the required permissions.

    Params:
        security_scopes : SecurityScopes
            An instance of SecurityScopes that defines the required scopes for access.

        token : str
            The OAuth2 access token for user authentication, provided via the Depends function.

    Returns:
        dict: A dictionary containing the authenticated user's details, including:
            - user_name (str): The username of the authenticated user.
            - role (str or None): The role name of the user if available.
            - groups (list): A list of groups the user belongs to.
            - permissions (list): A list of permissions associated with the user's role.

    Raises:
        HTTPException (401)
            If the token is invalid or permissions are insufficient.

        HTTPException (404)
            If the user is not found.
    """
    route: APIRoute = request.scope.get("route")
    endpoint = getattr(route, "endpoint", None)
    required_permission = getattr(endpoint, "required_permission", None)

    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = f"Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    token_data = await Authentication().verify_token(token, credentials_exception)
    global_permissions_set = set()
    college_permissions_set = set()
    dashboard_type = "admin_dashboard"
    is_student = False
    college_id = None
    role, role_id, group_names = None, None, None
    if token_data.scopes[0] == "student":
        is_student = True
        dashboard_type = "student_dashboard"
        college_ids = token_data.college_info[0].get("_id")
        toml_data = utility_obj.read_current_toml_file()
        if toml_data.get("testing", {}).get("test") is False:
            Reset_the_settings().check_college_mapped(college_ids)
        if (
            user := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                {"user_name": token_data.user_name}
            )
        ) is None:
            raise HTTPException(status_code=404, detail="username not found")
        user_name = user["user_name"]
    else:
        college_id = None
        college_ids = [college.get("_id") for college in token_data.college_info]
        if college_ids:
            college_id = college_ids[0]
            field = f"{college_id}/{token_data.role_id}"
        else:
            field = token_data.role_id
        role = await get_cache_roles_permissions(
            collection_name="roles_permissions", field=field
        )
        if not role and isinstance(token_data.role_id, str):
            roles = await utility_obj.cache_roles_and_permissions()
            roles = roles.get("data", {})
            role = json.loads(roles.get(str(token_data.role_id)))

        cache_populated = False
        group_names = []
        for group in token_data.groups:
            group_data = await get_cache_roles_permissions(
                collection_name="groups_and_permissions", field=group
            )
            if not group_data:
                if not cache_populated:
                    groups = await utility_obj.cache_groups_and_permissions()
                    groups = groups.get("data", {})
                    group_data = json.loads(groups.get(str(group), "{}"))
                    cache_populated = True
            if group_data:
                group_names.append(group_data.get("name"))
                group_perms = group_data.get("permissions", {})
                global_permissions_set.update(group_perms.get("global_permissions", []))
                college_permissions_set.update(
                    group_perms.get("college_permissions", [])
                )

        user = await get_collection_from_cache(
            collection_name="users", field=token_data.user_name
        )
        if not user:
            user = await DatabaseConfiguration().user_collection.find_one(
                {"user_name": token_data.user_name})
            if user:
                await store_collection_in_cache(
                    collection=user,
                    collection_name="users",
                    expiration_time=10800,
                    field=token_data.user_name,
                )
        if not user:
            raise HTTPException(status_code=404, detail="username not found")

        # Todo: we will deleted this hard coded after the introduce new logic
        toml_data = utility_obj.read_current_toml_file()
        if toml_data.get("testing", {}).get("test") is False:
            if user.get("associated_colleges"):
                if user.get("associated_colleges"):
                    Reset_the_settings().check_college_mapped(
                        college_id=user.get(
                            "associated_colleges", ["628dfd41ef796e8f757a5c13"]
                        )[0]
                    )
        user_name = user["user_name"]
    if user is None:
        raise credentials_exception
    allowed_features = await get_collection_from_cache(
        f"allowed_features/{dashboard_type}", user_name
    )
    if not allowed_features and not is_testing_env():
        allowed_features = await utility_obj.get_user_feature_permissions(
            user=user, dashboard_type=dashboard_type, college_id=college_id
        )
        if allowed_features:
            await store_collection_in_cache(
                collection=allowed_features,
                collection_name=f"allowed_features/{dashboard_type}",
                field=user_name,
            )
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )

    if feature_key and not is_testing_env():
        feature = allowed_features.get(feature_key)

        if not (feature and feature.get("visibility", False)):
            raise HTTPException(
                status_code=403,
                detail="Access denied. You are not permitted to perform this operation.",
            )

        if not is_student and required_permission and not feature.get("permissions", {}).get(required_permission):
            raise HTTPException(
                status_code=403,
                detail="Access denied. You are not permitted to perform this operation.",
            )

    if role:
        role_permissions = role.get("permissions", {})
        global_permissions_set.update(role_permissions.get("global_permissions", []))
        college_permissions_set.update(role_permissions.get("college_permissions", []))
    user_object = {
        "user_id": str(user.get("_id", "")),
        "user_name": user_name,
        "role_id": {
            "mongo_id": role.get("mongo_id") if role else None,
            "pgsql_id": role.get("id") if role else None,
        },
        "role": role.get("name") if role else None,
        "groups": group_names or token_data.groups,
        "permissions": {
            "global_permissions": list(global_permissions_set),
            "college_permissions": list(college_permissions_set),
        },
        "associated_colleges": college_ids,
        "allowed_features": allowed_features,
    }
    return user_object


def is_testing_env():
    toml_data = utility_obj.read_current_toml_file()
    if toml_data.get("testing", {}).get("test") is True:
        return True
    return False


class RedisClient:
    """
    This class created a Redis connection object giving connection pool and its limit. It makes sure that
    on different threads the same Redis connection is being used.
    """
    _instances = {}
    _lock = Lock()

    def __new__(cls, host: str, port: int, password: str, *args, **kwargs):
        """
        This function is used to maintain same redis connection usage every single time.
        """
        key = (host, port, password)
        if key not in cls._instances:
            with cls._lock:
                if key not in cls._instances:
                    cls._instances[key] = super(RedisClient, cls).__new__(cls)
                    cls._instances[key].initialize(host, port, password)
        return cls._instances[key]

    def initialize(self, host: str, port: int, password: str):
        """
        This function initializes the Redis connection pool giving limit
        Params:
            host (str): Redis host
            port (int): Redis port
            password (str): Redis password
        Return:
             None
        Raises:
            Connection error : This occurs when there is some connection problem
            RedisError :  This occurs when something goes wrong in connection
            Exception : This raises when there is some unknown error occured
        """
        try:
            self.connection_pool = redis_async.ConnectionPool(
                host=host,
                port=port,
                password=password,
                max_connections=REDIS_MAX_CONNECTIONS,
                socket_timeout=2,
                socket_connect_timeout=2,
                retry_on_timeout=True,
                socket_keepalive=True,
                retry_on_error=[redis.exceptions.TimeoutError, socket.timeout,
                                redis.exceptions.ConnectionError],
                health_check_interval=60
            )
            self.client = redis_async.Redis(connection_pool=self.connection_pool)
            logger.info("Connection with Redis is done!!!!!")
        except ConnectionError as e:
            logger.error(f"Some connection error occurred while connecting to Redis: {e}")
            raise HTTPException(status_code=400, detail="Connection failed to redis")
        except redis.RedisError as e:
            logger.error(f"Some Redis Error occurred while connection to Redis: {e}")
            raise HTTPException(status_code=400, detail="Connection failed to redis")
        except Exception as e:
            logger.error(f"Some unexpected exception raised when connecting to Redis: {e}")
            raise HTTPException(status_code=400, detail="Connection failed to redis")

    def get_client(self):
        """
        This function returns Redis client object
        Params:
            None
        Returns:
            Redis Client
        """
        return self.client


def get_redis_client():
    """
    This is used to connect with redis client.
    Params:
        None
    Returns:
        Redis Client: The redis client to carry redis operations
    Raises:
        None
    """
    if not is_testing_env():
        redis_client = RedisClient(
            host=settings.redis_cache_host,
            port=settings.redis_cache_port,
            password=settings.redis_cache_password
        ).get_client()
        return redis_client


def get_sync_redis_client():
    """
    This is used to connect with redis client.
    Params:
        None
    Returns:
        Redis Client: The redis client to carry redis operations
    Raises:
        None
    """
    if not is_testing_env():
        redis_client = redis.Redis(
            host=settings.redis_cache_host,
            port=settings.redis_cache_port,
            password=settings.redis_cache_password,
            health_check_interval=10,
            socket_keepalive=True
        )
        return redis_client


def convert_generators_to_lists(data):
    """
    this function search if there is any generator object in the given data
    and if there is it will convert it into list.
    this is done because while storing the data in cache the data should be converted to json
    and generator objects are not convertable into json
    Params:
      data (dict/list): the data in which generator has to be checked
    Returns:
        data (dict/list): without generator object
    """
    try:
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = convert_generators_to_lists(value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                data[i] = convert_generators_to_lists(item)
        elif isinstance(data, types.GeneratorType):
            data = list(data)
    except Exception as e:
        logger.error(f"some error occurred while changing the  generator to list: {e}")
        return None
    return data


def hours_until_end_of_day() -> int:
    """
    Calculates the number of hours left until the end of the day, rounded down to the nearest hour.
    Params:
        None
    Returns:
        int: The number of hours left until midnight.
    """
    now = datetime.now()
    end_of_day = datetime.combine(now.date(), datetime.max.time())
    seconds_left = (end_of_day - now).total_seconds()
    return int(seconds_left)


async def insert_data_in_cache(cache_key, data, expiration_time=1800, set=False,
                               change_indicator=False):
    """
    This is used to insert the data in cache. IIt inserts the given data at
    Particular given key
    The expiration time by default will be 1800sec (30 mins)
    Params:
        - cache_key (str) : the key that is required to store the data
        - data (json): the data that is to be stored at particular key
        - expiration_time (int): No of seconds the data will live in cache. By default, it is set to 300(sec)
        - set (bool): True if set method should be used, False if set method is not used
        - change_indicator (bool): True if need to store change indicator value else false
    Raises:
        - Exception: An error occurred when something wrong happen in the code.
        - watchError: An error occurred when some problem occur in redis pipeline.
    """
    if not is_testing_env():
        r = get_redis_client()
        if change_indicator:
            expiration_time = hours_until_end_of_day()
        expiration_time = expiration_time + random.randint(0, 300)
        async with r.pipeline() as pipe:
            while True:
                try:
                    await pipe.watch(cache_key)
                    pipe.multi()
                    try:
                        data = json.dumps(data)
                    except TypeError:
                        data = convert_generators_to_lists(data)
                        if data:
                            data = json.dumps(data)
                        else:
                            logger.error(
                                f"While storing data in cache got"
                                f" some error related to generator"
                                f" to list"
                            )
                            break
                    except Exception as e:
                        logger.error(f"Some internal error occurred: {e}")
                        break
                    if set:
                        if await pipe.set(cache_key, data):
                            await pipe.expire(cache_key, expiration_time)
                    else:
                        if await pipe.setnx(cache_key, data):
                            await pipe.expire(cache_key, expiration_time)
                    await pipe.execute()
                    break
                except redis.WatchError as e:
                    logger.error(f"While storing data in cache got error: {e}")
                    continue
                except redis.TimeoutError as e:
                    logger.error(f"Timeout while storing data in cache: {e}")
                    break
                except Exception as e:
                    logger.error(f"Some internal error occurred: {e}")
                    break


async def cache_dependency(
        request: Request, current_user: str = Depends(get_current_user)
):
    """
    Dependency for cache. This will create a unique key for every API depending on the
    route, path parameters, query parameters, payload.
    Params:
      request : the request of the API hit. This request have all the data that
                are required to create a key
    Exception raised:
      connection error : This occurs when there is some problem in connection with redis data base

    """
    if not is_testing_env():
        r = get_redis_client()
        try:
            key = f"{settings.aws_env}/{current_user}/{utility_obj.get_university_name_s3_folder()}{request.get('path')}"
            query = request.get("query_string")
            key += query.decode("utf-8")
            req = await request.body()
            if req:
                req = json.loads(req)
                if isinstance(req, dict):
                    for param, value in req.items():
                        if isinstance(value, dict):
                            for k, v in value.items():
                                key += f"_{k}_{v}"
                        else:
                            key += f"_{param}_{value}"
                elif isinstance(req, list):
                    for value in req:
                        key += value
                else:
                    key += req
        except Exception as e:
            logger.error(f"Some error while fetching the key for cache: {e}")
            return None, None
        try:
            cached_value = await r.get(key)
            if cached_value:
                return key, json.loads(cached_value)
            return key, None
        except ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            return key, None
        except Exception as e:
            logger.error(f"Error while getting cache data: {e}")
            return key, None
    else:
        return None, None


async def cache_dependency_public_access(
        request: Request
):
    """
    Dependency for cache for public access. This will create a unique key for every API depending on the
    route, path parameters, query parameters, payload.
    Params:
      request : the request of the API hit. This request have all the data that
                are required to create a key
    Exception raised:
      connection error : This occurs when there is some problem in connection with redis data base

    """
    if not is_testing_env():
        r = get_redis_client()
        try:
            key = f"{settings.aws_env}{request.get('path')}"
            query = request.get("query_string")
            key += query.decode("utf-8")
            req = await request.body()
            if req:
                req = json.loads(req)
                if isinstance(req, dict):
                    for param, value in req.items():
                        if isinstance(value, dict):
                            for k, v in value.items():
                                key += f"_{k}_{v}"
                        else:
                            key += f"_{param}_{value}"
                elif isinstance(req, list):
                    for value in req:
                        key += value
                else:
                    key += req
        except Exception as e:
            logger.error(f"Some error while fetching the key for cache: {e}")
            await r.close()
            return None, None
        try:
            cached_value = await r.get(key)
            if cached_value:
                return key, json.loads(cached_value)
            return key, None
        except ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            return key, None
        except Exception as e:
            logger.error(f"Error while getting cache data: {e}")
            return key, None
    else:
        return None, None


async def delete_keys_matching_pattern(patterns: list, user_id=None) -> None:
    """
    Delete all keys from cache which match the provided pattern.

    Params:
        - patterns (list): All the patterns that are to be deleted from Redis
        - user_id (str): unique college id if deleting data for college else email of the user
    Returns: None

    Raises:
        - Exception: An error occurred when something wrong happen in the code.
        - watchError: An error occurred when some problem occur in redis pipeline.
    """
    r = get_redis_client()
    try:
        keys_to_delete = []
        for pattern in patterns:
            key = f"{utility_obj.get_university_name_s3_folder()}/{pattern}"
            if user_id:
                key += f"/{user_id}"
            keys_to_delete.extend(await r.keys(f"*{key}*"))
        async with r.pipeline() as pipe:
            try:
                for key in keys_to_delete:
                    pipe.delete(key)
                await pipe.execute()
            except redis.exceptions.WatchError as error:
                logger.error(
                    f"An occurred when deleting cache keys by matching pattern. Error: {error}"
                )
    except Exception as error:
        logger.error(
            f"An occurred when deleting cache keys by matching pattern. Error: {error}"
        )


def sync_delete_keys_matching_pattern(pattern: str) -> None:
    """
    Delete all keys from cache which match the provided pattern in synchronized way

    Params:
        - pattern (str): The pattern which useful for delete cache keys.

    Returns: None

    Raises:
        - Exception: An error occurred when something wrong happen in the code.
        - watchError: An error occurred when some problem occur in redis pipeline.
    """
    try:
        r = get_sync_redis_client()
        keys_to_delete = r.keys(f"*{pattern}*")
        with r.pipeline() as pipe:
            try:
                pipe.multi()
                for key in keys_to_delete:
                    pipe.delete(key)
                pipe.execute()
            except redis.exceptions.WatchError as error:
                logger.error(
                    f"An occurred when deleting cache keys by matching pattern. Error: {error}"
                )
    except Exception as error:
        logger.error(
            f"An occurred when deleting cache keys by matching pattern. Error: {error}"
        )


async def cache_invalidation(api_updated: str, user_id=None) -> None:
    """
    This function is used for cache invalidation.
    It will grab all those keys which are required to invalidate in cache and delete them.

    Params:
        - api_updated (str): The name of API which is updated
        - user_id (str): Default None, email of the user
    Returns: None

    Raises:
        - Exception: An error occurred when something wrong happen in the code.
    """
    if not is_testing_env():
        try:
            data = await get_collection_from_cache(collection_name="cache_invalidations")
            if not data:
                data = (
                    await DatabaseConfiguration()
                    .cache_invalidations.aggregate([])
                    .to_list(None)
                )
                await store_collection_in_cache(data, collection_name="cache_invalidations")
            data = data[0] if data is not None else {}
            cache_invalidates = data.get(api_updated, [])
            await delete_keys_matching_pattern(cache_invalidates, user_id)
        except Exception as error:
            logger.error(f"some error occurred while cache invalidation: {error}")


def sync_cache_invalidation(api_updated: str, user_id: str = None) -> None:
    """
    This function is used for cache invalidation in synchronized way.
    It will grab all those keys which are required to invalidate in cache and delete them.

    Params:
        - api_updated (str): The name of API which is updated
        - user_id (str): Default None, email of the user
    Returns: None

    Raises:
        - Exception: An error occurred when something wrong happen in the code.
    """
    if not is_testing_env():
        try:
            data = list(
                DatabaseConfigurationSync(database="master").cache_invalidations.aggregate([])
            )
            data = data[0] if data is not None else {}
            cache_invalidates = data.get(api_updated, [])
            for key in cache_invalidates:
                key = f"{utility_obj.get_university_name_s3_folder()}/{key}"
                if user_id:
                    key = f"{utility_obj.get_university_name_s3_folder()}/{key}/{user_id}"
                sync_delete_keys_matching_pattern(key)
        except Exception as error:
            logger.error(f"some error occurred while cache invalidation: {error}")


async def change_indicator_cache(request: Request,
                                 current_user: str = Depends(get_current_user)) -> tuple:
    """
    Dependency for cache change indicator. This will create a unique key for every API depending on the
    route, path parameters, query parameters mentioning change indicator separately
    Params:
        request : the request of the API hit. This request have all the data that
                are required to create a key
        Current_user: The Current user who is running the API
    Returns:
        tuple : Key and the data if present.
    Exception raised:
      connection error : This occurs when there is some problem in connection with redis data base
    """
    if not is_testing_env():
        r = get_redis_client()
        path = request.get("path")
        path = path.replace("_", "_ci", 1)
        try:
            key = (
                    settings.aws_env
                    + "/"
                    + utility_obj.get_university_name_s3_folder()
                    + "/"
                    + current_user
                    + f"{path}"
            )
            query = request.get("query_string")
            key += query.decode("utf-8") + "/change_indicator"
            cached_value = await r.get(key)
            if cached_value:
                return key, json.loads(cached_value)
            return key, None
        except Exception as e:
            logger.error("Some error occurred in change indicator cache setting!")
            return None, None
    else:
        return None, None


async def get_cache_roles_permissions(collection_name: str, field: str = None, scope: list = None):
    """
    Retrieve a collection or a specific field from a Redis hash.

    Params:
        collection_name (str): The name of the Redis hash.
        field (Optional[str]): The specific field to retrieve from the hash.
        scope (Optional[list]): The scope to filter the roles by ('global' or 'college').

    Returns:
        Optional[Any]: The entire hash or a specific field if found, otherwise None.
    """
    if is_testing_env():
        return None
    redis_client = get_redis_client()
    if not redis_client:
        return None
    try:
        if field:
            cached_data = await redis_client.hget(collection_name, field)
            if cached_data:
                return json.loads(cached_data)
        else:
            cached_data = await redis_client.hgetall(collection_name)
            if cached_data:
                roles = [json.loads(value) for value in cached_data.values()]
                if scope is not None and scope:
                    roles = [role for role in roles if role.get("scope") in scope]
                sorted_roles = sorted(roles, key=lambda x: x["name"].lower())
                return sorted_roles
    except Exception as e:
        logger.error(f"Something went wrong while fetching roles and permissions from redis: {e}")
    finally:
        await redis_client.close()


async def get_collection_from_cache(collection_name: str, field: str = None):
    """
    Get collection list or a specific field details from cache
    Params:
        collection_name (str): The name of collection which is to be extracted
        field(str):The specific field to retrieve from the collection for more granular caching
    Returns:
        collection or a specific field from the collection if found, otherwise None.
    """
    if not is_testing_env():
        redis_client = get_redis_client()
        if redis_client:
            key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/{collection_name}"
            if field:
                key += f"/{field}"
            collection_name = await redis_client.get(key)
            await redis_client.close()
            if collection_name:
                collection = json.loads(collection_name)
                return collection
        return None
    return None


async def store_collection_in_cache(collection: Any, collection_name: str, expiration_time=605000,
                                    field: str = None):
    """
    Store the given collection in Redis
    If a `field` is provided, it appends to the key for more specific caching.
    Params:
        collection (list): The collection details
        collection_name (str): The name of collection
        field (str, optional): The specific field that adds to the key which is helpful while fetching the data
    Returns:
        None
    """
    if not is_testing_env():
        data = json.dumps(collection, cls=CustomJSONEncoder)
        redis_client = get_redis_client()
        expiration_time += random.randint(0, 300)
        if redis_client:
            key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/{collection_name}"
            if field:
                key += f"/{field}"
            async with redis_client.pipeline() as pipe:
                while True:
                    try:
                        await pipe.watch(key)
                        pipe.multi()
                        if await pipe.setnx(key, data):
                            await pipe.expire(key, expiration_time)
                        await pipe.execute()
                        break
                    except redis.WatchError as e:
                        logger.error(f"While storing collection {collection_name} got error: {e}")
                        continue
                    except redis.TimeoutError as e:
                        logger.error(
                            f"Timeout while storing collection {collection_name} in cache: {e}")
                        break
                    except Exception as e:
                        logger.error(
                            f"Some internal error occurred while storing collection {collection}: {e}")
                        break


# CurrentUser = Annotated[str, Depends(get_current_user)]
CurrentUser = Annotated[dict, Depends(get_current_user_object)]
Is_testing = Annotated[bool, Depends(is_testing_env)]
