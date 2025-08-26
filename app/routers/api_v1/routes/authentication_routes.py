"""
This file contains functions related to authentication
"""

from fastapi import APIRouter, Depends, status, Request, Query
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from kombu.exceptions import KombuError

from app.celery_tasks.celery_student_timeline import StudentActivity
# from app.core.celery_app import create_celery_app
from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, settings
from app.database.configuration import DatabaseConfiguration
# from app.dependencies.celery_worker_status import require_redis_connection
from app.dependencies.jwttoken import Authentication
from app.dependencies.oauth import AuthenticateUser, is_testing_env

oauth2 = APIRouter()
logger = get_logger(__name__)
# app = create_celery_app()


# TODO : Remove Existing Function Auth Module
@oauth2.post("/token", response_description="Login")
# @require_redis_connection
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    college_id: str = Query(
        None, description="Enter college id, need of it when" " student try to login"
    ),
):
    """
    Global Login entry point to authorize users/students by validating
     credentials along with their scope of access \n
    * :*param* **form_data**:\n
    * :*return* **Success login message '{"access_token": "success",
    "token_type": "bearer"}'**:
    """

    if len(form_data.scopes) != 1:
        raise HTTPException(status_code=422, detail="Scope not found")

    scope = form_data.scopes[0]

    if scope == "student":
        if college_id is None:
            college_id = form_data.client_id
        toml_data = utility_obj.read_current_toml_file()

        if toml_data.get("testing", {}).get("test") is False:
            Reset_the_settings().get_user_database(college_id, form_data)
        user = await AuthenticateUser().authenticate_student(
            form_data.username,
            form_data.password,
            form_data.scopes,
            college_id,
            request=request,
        )
    else:
        users = await DatabaseConfiguration().user_collection.find_one(
            {"user_name": form_data.username}
        )

        if users is None:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        toml_data = utility_obj.read_current_toml_file()

        if toml_data.get("testing", {}).get("test") is False:
            Reset_the_settings().get_user_database(
                str(users.get("associated_colleges", ["628dfd41ef796e8f757a5c13"])[0]),
                form_data,
            )
        user = await AuthenticateUser().authenticate_user(
            user_name=form_data.username,
            password=form_data.password,
            scopes=form_data.scopes,
        )

    if not user:
        raise HTTPException(status_code=422, detail="Data not valid")

    ip_address = utility_obj.get_ip_address(request)

    await utility_obj.store_login_activity_helper(
        username=form_data.username, ip_address=ip_address
    )
    if scope == "student":
        try:
            toml_data = utility_obj.read_current_toml_file()
            if toml_data.get("testing", {}).get("test") is False:
                # TODO: Not able to add student timeline data
                #  using celery task when environment is
                #  demo. We'll remove the condition when
                #  celery work fine.
                if settings.environment in ["demo"]:
                    StudentActivity().student_timeline(
                        student_id=str(user.get("_id")),
                        event_type="Login",
                        event_status=f"{utility_obj.name_can(user.get('basic_details', {}))}"
                        f" logged in through Password method into"
                        f" the Dashboard",
                        college_id=college_id,
                    )
                else:
                    if not is_testing_env():
                        StudentActivity().student_timeline.delay(
                            student_id=str(user.get("_id")),
                            event_type="Login",
                            event_status=f"{utility_obj.name_can(user.get('basic_details', {}))}"
                            f" logged in through Password method into"
                            f" the Dashboard",
                            college_id=college_id,
                        )
        except KombuError as celery_error:
            logger.error(f"error storing login by password data " f"{celery_error}")
        except Exception as error:
            logger.error(f"error storing otp data {error}")
    return user


@oauth2.post("/tokeninfo")
async def get_token_info_api(token: str = None):
    """
    Returns Token Payload to get token info
    :param token:
    :return: ** Token Payload**:
    """
    credentials_exception = HTTPException(
        detail="Token is not valid", status_code=status.HTTP_401_UNAUTHORIZED
    )
    if not token:
        raise credentials_exception
    return await Authentication().get_token_details(token, credentials_exception)


@oauth2.post("/refresh_token/generate/", response_description="Generate refresh token")
# @require_redis_connection
async def generate_refresh_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    college_id: str = Query(
        None, description="Enter college id, need of it when student try to login"
    ),
):
    """
    Generate refresh token
    """
    if len(form_data.scopes) != 1:
        form_data.scopes = ["other"]

    if college_id is None:
        college_id = form_data.client_id

    scope = form_data.scopes[0]
    toml_data = utility_obj.read_current_toml_file()

    if scope == "student":
        if toml_data.get("testing", {}).get("test") is False:
            Reset_the_settings().get_user_database(college_id, form_data)
        user = await AuthenticateUser().authenticate_student(
            form_data.username,
            form_data.password,
            form_data.scopes,
            college_id,
            refresh_token=True,
            request=request,
        )
    else:
        users = await DatabaseConfiguration().user_collection.find_one(
            {"user_name": form_data.username}
        )

        if users is None:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        user = await AuthenticateUser().authenticate_user(
            form_data.username,
            form_data.password,
            form_data.scopes,
            refresh_token=True,
            request=request,
        )

        if toml_data.get("testing", {}).get("test") is False:
            Reset_the_settings().get_user_database(
                str(users.get("associated_colleges")[0]), form_data
            )

    if not user:
        raise HTTPException(status_code=422, detail="Data not valid")
    ip_address = utility_obj.get_ip_address(request)

    await utility_obj.store_login_activity_helper(
        username=form_data.username, ip_address=ip_address
    )

    return user


@oauth2.post("/refresh_token/verify/", response_description="Verify refresh token")
async def verify_refresh_token(token: str = None):
    """
    Generate refresh token
    """
    credentials_exception = HTTPException(detail="Token is not valid", status_code=422)
    if not token:
        raise credentials_exception
    return await Authentication().verify_refresh_token(token, credentials_exception)


@oauth2.post("/refresh_token/revoke/", response_description="Revoke refresh token")
async def revoke_refresh_token(token: str = None):
    """
    Revoke refresh token
    """
    credentials_exception = HTTPException(detail="Token is not valid", status_code=422)
    if not token:
        raise credentials_exception
    return await Authentication().revoke_refresh_token(token, credentials_exception)
