"""
This file contains API routes/endpoints related to user
"""

import ast
import datetime
from typing import Union

from bson.objectid import ObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, Body
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from pydantic import EmailStr

from app.background_task.admin_user import DownloadRequestActivity
from app.background_task.send_mail_configuration import EmailActivity
from app.core.custom_error import ObjectIdInValid, CustomError, DataNotFoundError
from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, settings, requires_feature_permission
from app.database.aggregation.admin_user import AdminUser
from app.database.aggregation.roles_menu_and_permission import Role
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.cryptography import EncryptionDecryption
from app.dependencies.hashing import Hash
from app.dependencies.oauth import CurrentUser, cache_invalidation, Is_testing, get_current_user_object
from app.helpers.user_curd.role_configuration import RoleHelper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.student_user_schema import User, SortType
from app.models.user_schema import (
    UserCreation,
    UserPermission,
    UpdateUserInfo,
    getPanelist,
)
from app.s3_events.s3_events_configuration import upload_csv_and_get_public_url

logger = get_logger(__name__)
user_router = APIRouter()


@user_router.post(
    "/create_super_admin/", response_description="Create Superuser", deprecated=True
)
async def create_super_admin():
    """
    Create Super Admin\n
    * :*return* **Message - SuperAdmin created successfully.** if SuperAdmin
    created successfully:
    """
    super_admin = await UserHelper().create_superadmin()
    if super_admin:
        return utility_obj.response_model(
            super_admin, message="SuperAdmin created " "successfully."
        )


@user_router.post("/create_new_user/", response_description="Create a New User")
@requires_feature_permission("write")
async def create_new_user(
        testing: Is_testing,
        request: Request,
        new_user: UserCreation,
        current_user: CurrentUser,
        user_type: str = Query(
            description="Type of user which user you want to create 🚀 \n* "
                        "**client_manager** \n* **college_super_admin**"
                        "\n* **college_admin** \n* **college_head_counselor** "
                        "\n* **college_counselor** \n* "
                        "**college_publisher_console** \n* **panelist** "
                        "\n* **authorized_approver** \n* **moderator** "
                        "\n* **qa** \n* **head_qa**"
        ),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Create a New User\n

    Params:\n
        user_type (str): Type of new user.\n
        email (str): An email of a new user.\n
        full_name (str): A name of a new user.\n
        mobile_number (int): A mobile number of a new user.\n
        associated_colleges (list): A list which can contains college ids.\n
        designation (str): Designation of user. Mostly useful when creating
            panelist.\n
        school_name (str): A school name. Mostly useful when creating panelist.
        \n
        selected_programs (list): A list contains program names.

    Returns:
        dict: A dictionary contains info about new user.
    """
    college_id = college.get("id")
    if not testing:
        Reset_the_settings().check_college_mapped(college_id)
    total_user_count = await DatabaseConfiguration().user_collection.count_documents(
        {"associated_colleges": {"$in": [ObjectId(college_id)]}})
    total_user_limit = settings.users_limit

    if not testing and total_user_count >= total_user_limit:
        raise HTTPException(status_code=400,
                            detail=f"User creation failed: The maximum user limit of {total_user_limit} has been reached.")

    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    new_user = {
        key: value for key, value in new_user.model_dump().items() if value is not None
    }
    created_user = await UserHelper().create_user(
        new_user, current_user.get("user_name"), user_type.lower()
    )
    if created_user:
        if not testing:
            action_type = (
                "counselor"
                if user.get("role", {}).get("role_name") == "college_counselor"
                else "system"
            )
            await EmailActivity().send_username_password_to_user(
                user_name=created_user.get("user_name"),
                password=created_user.get("password"),
                first_name=created_user.get("first_name"),
                email_preferences=college.get("email_preferences", {}),
                request=request,
                event_type="email",
                event_status="sent",
                event_name="Verification",
                payload={
                    "content": "Create new user",
                    "email_list": [created_user.get("user_name")],
                },
                action_type=action_type,
                college_id=college_id
            )
        return utility_obj.response_model(
            created_user.get("details"), "User created successfully."
        )


@user_router.post("/reset_password/", response_description="Reset Password of User")
async def reset_password(
        testing: Is_testing,
        request: Request,
        email: EmailStr = Query(description="Enter email ID", example="john@example.com")
):
    """
    Reset Password of Admin User.\n

    Params:\n
        - email: An email id/address of admin user. e.g., test@gmail.com

    Returns:\n
        - dict: A dictionary which contains successful message "Mail sent successfully.".

    Raises:\n
        - CustomError: An error occurred with status code 404 when admin user not  found in the system/db.
        - HTTPException: An error occurred with status code 500 when something wrong in the backend code.
    """
    try:
        if not testing:
            user = await DatabaseConfiguration().user_collection.find_one(
                {"user_name": email}
            )
            if not user:
                raise CustomError("You have not registered with us, please register.")
            role_name = user.get("role", {}).get("role_name")
            # In case of super admin, we're using default apollo college id.
            college_id = "628dfd41ef796e8f757a5c13" if role_name == "super_admin" else str(
                user.get("associated_colleges")[0])
            college = await get_college_id(college_id)

            data = {"userid": str(user["_id"])}
            token = EncryptionDecryption().encrypt_message(str(data))
            token = token.decode("utf-8")
            reset_password_url = (
                f"https://{settings.base_admin_path}/user/dkper/user/{token}"
            )
            await EmailActivity().reset_password_user(
                email=email,
                reset_password_url=reset_password_url,
                event_type="email",
                event_status="sent",
                event_name="Reset password",
                payload={"content": "reset password", "email_list": [email]},
                current_user=email,
                request=request,
                email_preferences=college.get("email_preferences", {}),
                college_id=college.get("id")
            )
        return {"message": "Mail sent successfully."}
    except CustomError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        logger.error(f"An error got when admin user reset the password. Error - {error}")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@user_router.get("/dkper/user/{token}")
async def get_user_token(
        token: str,
        new_password: str = Query(
            description="Enter your new password", min_length=8, max_length=20
        ),
):
    """
    For reset user password
    """
    updated_password = True
    toml_data = utility_obj.read_current_toml_file()
    if toml_data.get("testing", {}).get("test") is False:
        try:
            dt = await EncryptionDecryption().decrypt_message(token)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid token")
        dt = ast.literal_eval(dt)
        if (
                data := await DatabaseConfiguration().user_collection.find_one(
                    {"_id": ObjectId(dt["userid"])}
                )
        ) is None:
            raise HTTPException(status_code=404, detail="username not found")
        password = Hash().get_password_hash(new_password)
        updated_password = await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(data["_id"])}, {"$set": {"password": password}}
        )
    if updated_password:
        return utility_obj.response_model(
            data=True, message="Your password has been updated successfully."
        )
    else:
        raise HTTPException(status_code=500, detail="Something went wrong.")


@user_router.delete(
    "/delete_all_users/", response_description="Delete User", deprecated=True
)
@requires_feature_permission("delete")
async def delete_all_user(
        current_user: CurrentUser,
        user_type: str = Query(
            description="Type of user which user list you want to delete "
                        "🚀 \n* **client_manager** \n* **college_super_admin**"
                        " \n* **college_admin** \n* **college_head_counselor"
                        "** \n* **college_counselor** \n* "
                        "**college_publisher_console**"
                        " \n* **panelist** \n* **authorized_approver** "
                        "\n* **moderator** \n* **qa** \n* **head_qa**"
        ),
):
    """
    Delete All Users Based on user_type
    :*param* **user_type** e.g. client_manager:
    :*return* **Delete all users based on user_type**:
    """
    await DatabaseConfiguration().user_collection.find_one({"user_name": current_user.get("user_name")})
    users = await UserHelper().delete_users(current_user, user_type.lower())
    if users:
        return utility_obj.response_model(
            users, message="All users removed " "successfully."
        )
    raise HTTPException(status_code=404, detail="User not found.")


@user_router.get("/list/", response_description="Get list of user")
@requires_feature_permission("read")
async def user_list(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
        user_type: str = Query(
            description="Type which user list you want 🚀 \n* "
                        "**client_manager** \n* **college_super_admin** \n* "
                        "**college_admin** \n* **college_head_counselor** "
                        "\n* **college_counselor** \n* "
                        "**college_publisher_console** \n* **panelist** "
                        "\n* **authorized_approver** \n* **moderator** "
                        "\n* **qa** \n* **head_qa**"
        ),
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
):
    """
    Get List of User\n
    * :*return **List of users based on user type** if more than one user
    present in database:
    """
    user_helper_obj = UserHelper()
    user = await user_helper_obj.is_valid_user(current_user)
    college_id = college.get("id")
    if (user.get("role", {}).get("role_name") != "super_admin" and
            college_id not in user.get("associated_colleges", [])):
        raise HTTPException(status_code=401,
                            detail=f"Not enough permissions to get another "
                                   f"college user data.")
    users = await user_helper_obj.retrieve_users(
        user, user_type.lower(), college_id,
        page_num, page_size, route_name="/user/list/"
    )
    if users:
        if page_size and page_num:
            return users
        return utility_obj.response_model(
            data=users, message="List of users fetched " "successfully."
        )
    raise HTTPException(status_code=404, detail="User not found.")


@user_router.put("/change_password/", summary="Change Password")
@requires_feature_permission("edit")
async def change_user_password(
        current_user: CurrentUser,
        current_password: str = Query(description="Enter your current " "password"),
        new_password: str = Query(
            description="Enter your new password", min_length=8, max_length=20
        ),
        confirm_password: str = Query(description="Confirm your new password"),
):
    """
    Change Password
    * :*param* **old_password*** e.g., test:
    * :*param* **new_password** e.g., test1:
    * :*param* **confirm_password** e.g., test1:
    * :*return* **Message - New Password updated successfully.**:
    """
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if Hash().verify_password(user["password"], current_password):
        if new_password != confirm_password:
            raise HTTPException(
                status_code=422,
                detail="New Password and Confirm Password doesn't match.",
            )
        if Hash().verify_password(user["password"], new_password):
            raise HTTPException(
                status_code=422,
                detail="Your new password should not match with last " "password.",
            )
        password = Hash().get_password_hash(new_password)
        updated_password = await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(user["_id"])}, {"$set": {"password": password}}
        )
        if updated_password:
            return utility_obj.response_model(
                data=True, message="Your password has been updated successfully."
            )
        else:
            raise HTTPException(status_code=500, detail="Something went wrong.")
    else:
        raise HTTPException(status_code=400, detail="Current password is incorrect.")


@user_router.get(
    "/get_menu_and_permission/",
    response_description="Get menu list and permissions based on user type",
)
@requires_feature_permission("read")
async def get_menu_and_permission(
        current_user: CurrentUser,
        user_type: str = Query(
            description="Type which user list you want 🚀 \n* **super_admin**"
                        " \n* **client_manager** \n* **college_super_admin**"
                        " \n* **college_admin** \n* **college_head_counselor**"
                        " \n* **college_counselor** "
                        "\n* **college_publisher_console**"
                        " \n* **panelist** \n* **authorized_approver** "
                        "\n* **moderator** \n* **qa** \n* **head_qa** \n* **student**"
        ),
):
    """
    Get Menu List and Permissions Based on User Type\n
    * :*param* **user_type*** e.g., college_publisher_console:\n
    * :*return **List of menu and permission**:
    """
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not user:
        raise HTTPException(status_code=422, detail="Not enough permissions")
    menus_and_permissions = await UserHelper().retrieve_menus_and_permissions(
        user, user_type.lower()
    )
    return {"data": menus_and_permissions, "message": "List of menu and permission."}


@user_router.put("/update_permissions/")
@requires_feature_permission("edit")
async def update_user_permissions(
        current_user: CurrentUser,
        user_permission: UserPermission,
        user_type: str = Query(
            description="Type of user which user you want to add permission 🚀"
                        " \n* **super_admin** \n* **client_manager** "
                        "\n* **college_super_admin** \n* **college_admin** "
                        "\n* **college_head_counselor** \n* "
                        "**college_counselor** \n*"
                        " **college_publisher_console**"
                        " \n* **panelist** \n* **authorized_approver** "
                        "\n* **moderator** \n* **qa** \n* **head_qa**"
        ),
):
    """
    Update the user permission based on user_type
    """
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not user:
        raise HTTPException(status_code=422, detail="Not enough permissions")
    if user["role"]["role_name"] != "super_admin":
        raise HTTPException(status_code=422, detail="Not enough permissions")
    permissions = {
        k: v for k, v in user_permission.model_dump().items() if v is not None
    }
    if len(permissions) < 1:
        raise HTTPException(
            status_code=422,
            detail="Need to pass atleast one field for update permission.",
        )
    updated_permission = await UserHelper().user_permissions(
        user, user_type.lower(), permissions
    )
    if updated_permission:
        role = await DatabaseConfiguration().role_collection.find_one(
            {"role_name": user_type.lower()}
        )
        return {
            "data": RoleHelper().permission_helper(role),
            "message": "Permission updated.",
        }


@user_router.get(
    "/get_all_menu_and_permission/",
    response_description="Get all users menu list and permissions",
)
@requires_feature_permission("read")
async def get_all_menu_and_permission(current_user: CurrentUser):
    """
    Get All Users Menu list and Permissions\n
    * :*param* **user_type*** e.g., college_publisher_console:\n
    * :*return **List of menu and permission of all users**:
    """
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not user:
        raise HTTPException(status_code=422, detail="Not enough permissions")
    if user["role"]["role_name"] != "super_admin":
        raise HTTPException(status_code=422, detail="Not enough permissions")
    all_menus_and_permissions = await Role().retrieve_all_menus_and_permissions()
    data = []
    async for doc in all_menus_and_permissions:
        data.append(RoleHelper().role_helper(doc))
    return {"data": data, "message": "List of all menus and permissions."}


@user_router.put("/enable_or_disable/", summary="Enable or disable user")
@requires_feature_permission("edit")
async def enable_or_disable_user(
        current_user: CurrentUser,
        user_id: str = Query(
            description="Enter user id which status you want update",
            example="62cd086378d740fd54795787",
        ),
        is_activated: bool = Query(
            description="For enable user, send value True. For disable user, "
                        "send value False"
        ),
):
    """
    Enable or disable user\n
    * :*param* **user_id** description="Enter user id which status you want
    update", example="62cd086378d740fd54795787":\n
    * :*param* **is_activated** description="For enable user, send value True.
     For disable user, send value False:\n
    * :*return* **Message - User status updated.**:
    """
    user = await UserHelper().is_valid_user(current_user)
    if (
            user.get("role", {}).get("role_name") != "college_super_admin"
            and user.get("role", {}).get("role_name") != "college_admin"
    ):
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    await utility_obj.is_id_length_valid(_id=user_id, name="User id")
    user = await DatabaseConfiguration().user_collection.find_one(
        {"_id": ObjectId(user_id)}
    )
    if not user:
        raise HTTPException(
            status_code=422, detail="User id not exist. Provide correct user id."
        )
    if user.get("is_activated") == is_activated:
        raise HTTPException(
            status_code=422, detail="Unable to update, no changes have been made."
        )
    await DatabaseConfiguration().user_collection.update_one(
        {"_id": ObjectId(user_id)}, {"$set": {"is_activated": is_activated}}
    )
    await cache_invalidation(api_updated="updated_user", user_id=user.get("email"))
    return {"message": "User status updated."}


@user_router.post("/get_details/", summary="Get all user of college details")
@requires_feature_permission("read")
async def all_user_details(
        background_tasks: BackgroundTasks,
        request: Request,
        current_user: CurrentUser,
        search_pattern: str | None = Query(None,
                                           description="Enter search pattern which useful for get "
                                                       "user details by search_pattern."),
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
        sort_type: SortType | None | str = None,
        column_name: str | None = Query(
            None,
            description="Column name which useful for sort data based "
                        "on sort type. Column name can be: "
                        "name, email, mobile_number, created_on, "
                        "last_accessed, is_activated and college.",
        ),
        download_data: bool = False,
        filters: list = Body(default=[]),
):
    """
    Get All College User Details\n
    * :*return* **Get all user details**:
    """
    # TODO: Improve in API response, calling multiple aggregation in this API
    current_datetime = datetime.datetime.utcnow()
    current_user = jsonable_encoder(current_user)
    user = await UserHelper().is_valid_user(current_user.get("user_name"))
    try:
        data, total = await AdminUser().all_details(
            user=current_user,
            page_num=page_num,
            page_size=page_size,
            sort_type=sort_type,
            column_name=column_name,
            search_pattern=search_pattern,
            filters=filters,
        )

        if download_data:
            background_tasks.add_task(
                DownloadRequestActivity().store_download_request_activity,
                request_type="Users data",
                requested_at=current_datetime,
                ip_address=utility_obj.get_ip_address(request),
                user=user,
                total_request_data=len(data),
                is_status_completed=True,
                request_completed_at=datetime.datetime.utcnow(),
            )

            if data:
                data_keys = list(data[0].keys())
                get_url = await upload_csv_and_get_public_url(
                    fieldnames=data_keys, data=data, name="applications_data"
                )

                return get_url

            raise HTTPException(status_code=404, detail="Users data not found.")

        if page_num is not None and page_size is not None:
            response = await utility_obj.pagination_in_aggregation(
                page_num=page_num,
                page_size=page_size,
                data_length=total,
                route_name="/user/get_details/",
            )

            return {
                "data": data,
                "total": total,
                "count": len(data),
                "pagination": response["pagination"],
                "message": "Get all user details.",
            }

        return utility_obj.response_model(data=data, message="data fetch successfully")
    except (ObjectIdInValid, DataNotFoundError) as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@user_router.post("/download_data/", summary="Download users data by IDs")
@requires_feature_permission("download")
async def download_users_data(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        request: Request,
        user_ids: list[str] = None,
):
    """
    Download Users Data by IDs\n
    * :*param* **user_ids** example=['6290c5f4e87e304387308499',
    '6290c65fe87e30438730849a']:\n
    * :*return* **Public URL of CSV file which contain users data**:
    """
    current_datetime = datetime.datetime.utcnow()
    login_user = await UserHelper().is_valid_user(current_user)
    if (
            login_user.get("role", {}).get("role_name") != "college_super_admin"
            and login_user.get("role", {}).get("role_name") != "college_admin"
    ):
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    users, user = [], {}
    if user_ids:
        for _id in user_ids:
            await utility_obj.is_id_length_valid(_id=_id, name="User id")
            user = await DatabaseConfiguration().user_collection.find_one(
                {"_id": ObjectId(_id)}
            )
            if not user:
                raise HTTPException(
                    status_code=422, detail=f"User id '{_id}' not exist."
                )
            college = await DatabaseConfiguration().college_collection.find_one(
                {"_id": ObjectId(str(user.get("associated_colleges", {})[0]))}
            )
            users.append(
                {
                    "user_id": str(user.get("_id")),
                    "user_name": utility_obj.name_can(user),
                    "user_email": user.get("email"),
                    "user_role": user.get("role", {}).get("role_name"),
                    "institute_allocated": college.get("name") if college else None,
                    "created_on": user.get("created_on"),
                    "last_active_on": user.get("last_accessed"),
                    "status": "Active" if user.get("is_activated") else "Inactive",
                }
            )
    else:
        users = (await AdminUser().all_details(login_user))[0]
    toml_data = utility_obj.read_current_toml_file()
    if toml_data.get("testing", {}).get("test") is True:
        return {"message": "Data downloaded"}
    background_tasks.add_task(
        DownloadRequestActivity().store_download_request_activity,
        request_type=f"Users data",
        requested_at=current_datetime,
        ip_address=utility_obj.get_ip_address(request),
        user=await UserHelper().check_user_has_permission(user_name=current_user),
        total_request_data=len(users),
        is_status_completed=True,
        request_completed_at=datetime.datetime.utcnow(),
    )
    if users:
        data_keys = list(users[0].keys())
        get_url = await upload_csv_and_get_public_url(
            fieldnames=data_keys, data=users, name="users_data"
        )
        return get_url
    raise HTTPException(status_code=404, detail="No found.")


@user_router.get("/current_user_details/", summary="Get current user details")
@requires_feature_permission("read")
async def current_user_details(current_user: CurrentUser):
    """
    Get current user details
    :return: Details of current user
    """
    user = await UserHelper().is_valid_user(current_user)
    associated_colleges_ids = (
        [str(i) for i in user.get("associated_colleges")]
        if user.get("associated_colleges")
        else None
    )
    associated_colleges_names = []
    if associated_colleges_ids:
        for _id in associated_colleges_ids:
            try:
                college = await DatabaseConfiguration().college_collection.find_one(
                    {"_id": ObjectId(_id)}
                )
                associated_colleges_names.append(college.get("name"))
            except AttributeError:
                continue
    data = {
        "user_id": user.get("_id"),
        "name": utility_obj.name_can(user),
        "email": user.get("email"),
        "mobile_number": user.get("mobile_number"),
        "associated_colleges": associated_colleges_names,
        "role_name": user.get("role").get("role_name"),
        "check_in_status": user.get("check_in_status"),
        "show_check_in": (
            True
            if user.get("role").get("role_name")
               in ["college_counselor", "moderator"]
            else False
        ),
        "message": "Get current user details",
    }
    if user.get("role", {}).get("role_name") == "client_admin":
        client_data = await DatabaseConfiguration().client_collection.find_one(
            {"_id": ObjectId(user.get("associated_client"))}
        )
        data.pop("associated_colleges")
        data["associated_client"] = user.get("associated_client")
        data["can_create_college"] = client_data.get("is_configured", False)
    return data


@user_router.get("/timeline/", summary="Get timeline of users based on filter")
@requires_feature_permission("read")
async def user_timeline(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
        own_timeline: bool = Query(
            False, description="Send True if want to see own " "timeline"
        ),
        college_super_admin_timeline: bool = Query(
            False,
            description="Send True if "
                        "want to get "
                        "all college "
                        "super admins "
                        "timeline.",
        ),
        head_counselors_timeline: bool = Query(
            False,
            description="Send True if want" " to get all head " "counselors " "timeline.",
        ),
        counselors_timeline: bool = Query(
            False, description="Send True if want to " "get all counselors " "timeline."
        ),
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
):
    """
    Get users timeline based on filter
    """
    user = await UserHelper().is_valid_user(current_user)
    users_timeline, total = await AdminUser().get_timeline(
        user,
        own_timeline,
        college_super_admin_timeline,
        head_counselors_timeline,
        counselors_timeline,
        page_num,
        page_size,
    )
    if page_num is not None and page_size is not None:
        response = await utility_obj.pagination_in_aggregation(
            page_num=page_num,
            page_size=page_size,
            data_length=total,
            route_name="/user/timeline/",
        )
        return {
            "data": users_timeline,
            "total": total,
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Get users timeline.",
        }
    return {"data": users_timeline, "message": "Get users timeline."}


@user_router.get("/session_info/", response_description="Get session info")
@requires_feature_permission("read")
async def get_session_info(
        current_user: CurrentUser,
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
        college: dict = Depends(get_college_id),
):
    """
    Get session info of users
    """
    return await AdminUser().session_info(
        college.get("id"), current_user, page_num, page_size, route_name=f"/oauth/session_info/"
    )


@user_router.put("/update/", response_description="Update user data")
@requires_feature_permission("edit")
async def update_user_data(
        data: UpdateUserInfo,
        current_user: CurrentUser,
        user_id: str = Query(description="Enter user id"),
        college: dict = Depends(get_college_id),
):
    """
    Update user data by id.

    Params:
        data (dict): User data which need to update.
        user_id (str): An unique id of user.
        college_id (str): An unique id of college.

    Returns:
          dict: A dictionary contains info about update user.
    """
    data = {key: value for key, value in data.model_dump().items() if value is not None}
    return await UserHelper().update_user_data(data, current_user, user_id)


@user_router.post("/delete_by_ids/", response_description="Delete users by ids")
@requires_feature_permission("delete")
async def update_user_data(
        user_ids: list[str],
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
):
    """
    Delete users data by ids.

    Params:
        user_ids (list[str]): A list which contains user_ids.
        college_id (str): An unique id of college.

    Returns:
          dict: A dictionary contains info about delete users.
    """
    return await UserHelper().delete_users_by_ids(current_user, user_ids)


@user_router.post("/download_panelist/", summary="Download panelist data by " "Ids")
@requires_feature_permission("download")
async def download_panelist(
        current_user: CurrentUser,
        background_tasks: BackgroundTasks,
        request: Request,
        panelists_ids: list[str] = None,
        college: dict = Depends(get_college_id)
):
    """
    Download panelists data by Ids.

    Params:\n
        panelists_ids (list[str]): A list contains panelists ids.\n
            For Example,
            ["64b2c11e9f4f0ce7ad232512", "64b2c11e9f4f0ce7ad232513"]
        college_id (str): An unique id of a college.
            For Example. 64b2c11e9f4f0ce7ad232511

    Returns:
        dict: A dictionary which contains download panelist info.
            Successful Response - {"file_url": "https://***.com/***",
                                "message": "File downloaded successfully."}
    """
    return await UserHelper().download_panelist_by_ids(
        current_user, panelists_ids, background_tasks, request, college.get("id")
    )


@user_router.get(
    "/panelist_manager_header_info/", summary="Get panelist manager header info"
)
@requires_feature_permission("read")
async def panelist_manager_header_info(
        current_user: CurrentUser, college: dict = Depends(get_college_id)
):
    """
    Get panelist manager header info.

    Params:\n
        college_id (str): An unique id of a college.
            For Example. 64b2c11e9f4f0ce7ad232511

    Returns:
        dict: A dictionary which contains panelist manager header info.
            Successful Response -
            {"message": "Get panelist manager header info."}
    """
    return await UserHelper().panelist_manager_header_info(current_user)


@user_router.get("/get_data_by_id/", response_description="Get user data by id")
@requires_feature_permission("read")
async def get_user_data_by_id(
        user_id: str, current_user: CurrentUser, college: dict = Depends(get_college_id)
):
    """
    Get user data by id.

    Params:\n
        user_id (str): An unique identifier/id of user_id.
            For example, 123456789012345678901234
        college_id (str): An unique id of college.
            For example, 123456789012345678901211
    Returns:
          dict: A dictionary contains info about user.
            Successful response contains user info with message -
            `Get user data.`
    """
    return await UserHelper().get_user_data_by_id(current_user, user_id)


@user_router.post(
    "/panelists/", response_description="Get panelist data " "with/without filter"
)
@requires_feature_permission("read")
async def get_panelists_data(
        current_user: CurrentUser,
        filters: getPanelist = None,
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
        college: dict = Depends(get_college_id)
):
    """
    Get List of Panelists\n
    * :*return **List of panelists data
    """
    user_helper_obj = UserHelper()
    filters = filters.model_dump() if filters else {}
    user = await user_helper_obj.is_valid_user(current_user)
    await user_helper_obj.check_permission(
        role_name=user.get("role", {}).get("role_name"), user_type="panelist"
    )
    users, total_users = await AdminUser().get_panelist_by_ids(
        college_id=college.get("id"), filters=filters, page_num=page_num, page_size=page_size,
        get_panelists=True
    )
    if users:
        if page_size and page_num:
            response = await utility_obj.pagination_in_aggregation(
                page_num, page_size, total_users, "/user/panelists/"
            )
            return {
                "data": users,
                "total": total_users,
                "count": page_size,
                "pagination": response["pagination"],
                "message": "List of panelists fetched successfully.",
            }
        return {"data": users, "message": "List of panelists fetched " "successfully."}
    return {"data": [], "message": "Panelists not found."}


@user_router.put("/enable_or_disable_users/", summary="Enable or disable users by ids")
@requires_feature_permission("edit")
async def enable_or_disable_users(
        current_user: CurrentUser,
        user_ids: list[str],
        is_activated: bool = Query(
            description="For enable users, send value True. For disable users,"
                        " send value False"
        ),
):
    """
    Enable or disable users by ids.

    Params:
        - is_activated (bool): A boolean value which will be useful for
        update status of user. Possible values - True or False
        True value will be useful for activate users.
        False value will be useful for deactivate users.

    Request body parameters:
        - user_ids (list[str]): A list which contains unique
            identifiers/ids of users which status you want update.
            e.g., ["62cd086378d740fd54795787", "62cd086378d740fd54795711"]

    Returns:
        dict: A dictionary which contains information about change statuses
        of users.
    """
    user = await UserHelper().is_valid_user(current_user)
    role_name = user.get("role", {}).get("role_name")
    if role_name not in ["college_super_admin", "college_admin"]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    try:
        user_ids = [
            ObjectId(user_id)
            for user_id in user_ids
            if await utility_obj.is_length_valid(user_id, "User id")
        ]
        await DatabaseConfiguration().user_collection.update_many(
            {"_id": {"$in": user_ids}}, {"$set": {"is_activated": is_activated}}
        )
        await cache_invalidation(api_updated="updated_user")
        return {"message": "Updated status of users."}
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        logger.error(f"Internal error occurred. Error - {str(error)}")
        raise HTTPException(
            status_code=500, detail="Internal error occurred. " f"Error - {str(error)}"
        )


@user_router.post(
    "/chart_info/", response_description="Get/download the user " "chart information."
)
@requires_feature_permission("download")
async def user_chart_info(
        current_user: CurrentUser,
        request: Request,
        background_tasks: BackgroundTasks,
        download_data: bool = False,
        college: dict = Depends(get_college_id),
):
    """
    Get/download the user chart information.

    Params:\n
        - college_id (str): An unique id/identifier of a college.
            e.g., 123456789012345678901234
        - download_data (bool). Useful for download user chart information.
            Default value: False.

    Returns:\n
        - dict: A dictionary which contains information about user chart
            information. e.g., {"userChart": {"labels": ["test"], "data": [1]},
                "dataChart": {"data": [44, 55, 41], "labels": [
                    "Limited", "Created", "Balance"]}}

    Raises:\n
        - 401 (Not enough permissions): AN error raised with status code 401
            when user don't have permission to get/download user chart
            information.
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        current_datetime = datetime.datetime.utcnow()
        data = await AdminUser().get_chart_info(college)
        if download_data:
            background_tasks.add_task(
                DownloadRequestActivity().store_download_request_activity,
                request_type="User Chart Info",
                requested_at=current_datetime,
                ip_address=utility_obj.get_ip_address(request),
                user=user,
                total_request_data=len(data),
                is_status_completed=True,
                request_completed_at=datetime.datetime.utcnow(),
            )
            final_data = data.get("userChart", {})
            data_chart_info = data.get("dataChart", {})
            for item in ["labels", "data"]:
                final_data.get(item, []).extend(data_chart_info.get(item, []))
            get_url = await upload_csv_and_get_public_url(
                fieldnames=["label", "percentage"], data=final_data, name="chart_info"
            )
            return get_url
        return {"data": data, "message": "Get the user chart information."}
    except Exception as error:
        logger.error(
            f"An error got when when user chart information. " f"Error - {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"An error got when user chart " f"information. Error - {error}",
        )


@user_router.get("/get_all_users/", summary="Get required feature roles")
@requires_feature_permission("read")
async def get_all_user(
        current_user: CurrentUser,
        page_num: int = Query(..., gt=0),
        page_size: int = Query(..., gt=0),
):
    """
    Get required feature roles.

    Params:
        - page_num (int): A number which will be useful for pagination.
            Default value: None
        - page_size (int): A number which will be useful for pagination.
            Default value: None
        - current_user (CurrentUser): A current user object.

    Returns:
        - dict: A dictionary which contains information about required
            feature roles.
            e.g., {"data": [{"role_name": "super_admin", "permissions": []},
                {"role_name": "client_manager", "permissions": []}],
                "message": "Get required feature roles."}
    """
    try:
        user = await UserHelper().is_valid_user(current_user)
        return await UserHelper().get_user_data(
            user=user, page_num=page_num, page_size=page_size)
    except CustomError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        logger.error(f"An error got when get required feature roles. Error - {error}")
        raise HTTPException(status_code=500, detail=f"Error - {error}")
