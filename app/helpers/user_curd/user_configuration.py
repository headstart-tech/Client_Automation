"""
This file contain class and methods which helpful for user routes
"""
import json
from datetime import datetime

from bson.objectid import ObjectId
from fastapi import BackgroundTasks, Request
from fastapi.exceptions import HTTPException

from app.background_task.admin_user import DownloadRequestActivity
from app.core.custom_error import DataNotFoundError
from app.core.utils import utility_obj, CustomJSONEncoder
from app.core.custom_error import DataNotFoundError
from app.core.utils import utility_obj
from app.database.configuration import settings, DatabaseConfiguration
from app.dependencies.hashing import Hash
from app.helpers.user_curd.role_configuration import RoleHelper
from app.models.student_user_schema import User


class UserHelper:
    """
    Contain functions related to user
    """

    def user_helper(self, user: dict):
        """
        Get user details
        """
        data = {
            "id": str(user.get("_id")),
            "email": user.get("email"),
            "first_name": user.get("first_name"),
            "middle_name": user.get("middle_name"),
            "last_name": user.get("last_name"),
            "mobile_number": user.get("mobile_number"),
            "associated_colleges": [str(i) for i in
                                    user.get("associated_colleges")]
            if user.get("associated_colleges")
            else None,
            "role_name": user.get("role").get("role_name"),
            "role_id": str(user.get("role").get("role_id")),
            "last_accessed": user.get("last_accessed"),
            "created_on": user.get("created_on"),
            "created_by": str(user.get("created_by")),
            "is_activated": user.get("is_activated"),
            "associated_source_value": user.get("associated_source_value"),
            "user_type": user.get("user_type"),
            "designation": user.get("designation"),
            "school_name": user.get("school_name"),
            "selected_programs": [program for program in
                                  user.get("selected_programs")]
            if user.get("selected_programs") else None
        }
        if data.get("role_name") == "panelist":
            interview_taken = user.get("interview_taken")
            selected_students = user.get("selected_students")
            if not interview_taken:
                interview_taken = 0
            if not selected_students:
                selected_students = 0
            data.update({"interview_taken": interview_taken,
                         "selected_students": selected_students,
                         "rejected_students": user.get("rejected_students", 0),
                         "selection_ratio":
                             utility_obj.get_percentage_result(
                                 selected_students, interview_taken)})
        return data

    async def is_valid_user(self, user_name, season=None):
        """
        Check user is valid or not
        """
        from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache
        if isinstance(user_name, dict):
            user_name = user_name.get("user_name")
        user = await get_collection_from_cache(collection_name="users", field=user_name)
        if not user:
            user = await DatabaseConfiguration(
                season=season).user_collection.find_one({"user_name": user_name})
            if user:
                await store_collection_in_cache(collection=user, collection_name="users",
                                                expiration_time=180,
                                                field=user_name)
        if not user:
            raise HTTPException(status_code=401, detail=f"Not enough permissions")
        user = await utility_obj.user_serialize(user)
        return user

    async def check_user_has_permission(
            self, user_name, check_roles: list | None = None,
            condition: bool = True) -> dict:
        """
        Check user has permission or not
        """
        if check_roles is None:
            check_roles = ["super_admin", "client_manager",
                           "college_publisher_console"]
        user = await self.is_valid_user(user_name, season=None)
        role_name = user.get("role", {}).get("role_name")
        if not condition:
            if role_name not in check_roles:
                raise HTTPException(status_code=401,
                                    detail=f"Not enough permissions")
        else:
            if role_name in check_roles:
                raise HTTPException(status_code=401,
                                    detail=f"Not enough permissions")
        return user

    async def check_permission(self, role_name, user_type):
        """
        Check user has permission to access particular route or not
        """
        temp_dict = {
            "student": ["super_admin"],
            "super_admin": ["super_admin"],
            "client_manager": ["super_admin"],
            "college_super_admin": ["super_admin", "client_manager"],
            "college_admin": ["college_super_admin"],
            "college_head_counselor": ["college_super_admin", "college_admin"],
            "college_counselor": ["college_head_counselor",
                                  "college_super_admin", "college_admin",
                                  "college_counselor"],
            "college_publisher_console": ["college_head_counselor",
                                          "college_super_admin",
                                          "college_admin"],
            "panelist": ["college_head_counselor", "college_super_admin",
                         "college_admin"],
            "authorized_approver": ["college_head_counselor",
                                    "college_super_admin", "college_admin"],
            "moderator": ["college_head_counselor", "college_super_admin",
                          "college_admin", "moderator"],
            "head_qa": ["college_super_admin", "college_admin"],
            "qa": ["college_super_admin", "college_admin", "head_qa"]
        }
        if user_type in temp_dict:
            if role_name not in temp_dict.get(user_type):
                raise HTTPException(status_code=401,
                                    detail=f"Not enough permissions")
        else:
            raise HTTPException(
                status_code=422, detail=f"Please provide correct user_type."
            )

    async def check_create_or_delete_user_permission(
            self, check_role, user_type, operation="delete"
    ):
        """
        Check permissions of user to create or delete the other user
        """
        user_permissions = ["client_manager", "college_super_admin",
                            "college_admin", "college_head_counselor",
                            "college_counselor", "panelist",
                            "authorized_approver", "moderator",
                            "college_publisher_console", "qa", "head_qa"]

        if user_type not in user_permissions:
            raise HTTPException(
                status_code=422,
                detail="Please provide correct user_type. User type "
                       "should be any of the following: client_manager, "
                       "college_super_admin, college_admin, "
                       "college_head_counselor, college_counselor, "
                       "college_publisher_console, panelist, "
                       "authorized_approver, moderator, qa and head_qa",
            )

        permission = f"{operation}_{user_type}"
        if not check_role.get("permission", {}).get(permission):
            raise HTTPException(status_code=401,
                                detail="Not enough permissions")

    async def delete_users(self, current_user, user_type):
        """
        Delete all student from database
        """
        user = await UserHelper().is_valid_user(current_user)
        check_role = await DatabaseConfiguration().role_collection.find_one(
            {"role_name": user["role"]["role_name"]}
        )
        await self.check_create_or_delete_user_permission(check_role,
                                                          user_type)
        user_found = await DatabaseConfiguration().user_collection.find_one(
            {"role.role_name": user_type})
        if user_found:
            await DatabaseConfiguration().user_collection.delete_many(
                {"role.role_name": user_type})
            return True

    async def retrieve_users(
            self, user, user_type, college_id, page_num=None, page_size=None,
            route_name=None
    ):
        """
        Retrieve list of user
        """
        role_name = user.get("role", {}).get("role_name")
        await self.check_permission(role_name=role_name, user_type=user_type)
        if role_name == user_type:
            all_user = [self.user_helper(user)]
        else:
            all_user = [
                self.user_helper(item)
                for item in await DatabaseConfiguration().user_collection. \
                    aggregate([{"$match": {"role.role_name": user_type, "associated_colleges":
                    {"$in": [ObjectId(college_id)]}}}]).to_list(None)
            ]
        response = {}
        if page_num and page_size:
            user_length = len(all_user)
            response = await utility_obj.pagination_in_api(
                page_num, page_size, all_user, user_length, route_name
            )
        if all_user:
            if page_num and page_size:
                return {
                    "data": [response["data"]],
                    "total": response["total"],
                    "count": page_size,
                    "pagination": response["pagination"],
                    "message": "List of users fetched successfully.",
                }
            return all_user
        return False

    async def create_superadmin(self):
        """
        Create super_admin
        """
        from app.dependencies.oauth import cache_invalidation
        super_admin = dict()
        user_name = settings.superadmin_username
        password = settings.superadmin_password
        get_role = await DatabaseConfiguration().role_collection.find_one(
            {"role_name": "super_admin"})
        role = {"role_name": "super_admin",
                "role_id": ObjectId(get_role.get("_id"))}
        check = await DatabaseConfiguration().user_collection.find_one(
            {"user_name": user_name})
        if check:
            raise HTTPException(status_code=422,
                                detail=f"SuperAdmin already exist.")
        password2 = Hash().get_password_hash(password)
        super_admin["user_name"] = user_name
        super_admin["password"] = password2
        super_admin["email"] = "shiftboolean.com"
        super_admin["role"] = role
        super_admin["last_accessed"] = datetime.utcnow()
        super_admin["created_on"] = datetime.utcnow()
        await DatabaseConfiguration().user_collection.insert_one(super_admin)
        await cache_invalidation(api_updated="updated_user")
        super_admin.clear()
        return {"message": "SuperAdmin created successfully."}

    async def create_client_admin(self, client_details):
        """
        Create client_admin

        Params:
            client_details (dict): A dictionary which contains client details.

        Returns:
            client_user_details (dict): A dictionary which contains client user details.
        """
        from app.dependencies.oauth import cache_invalidation

        # Getting required Information from Client Data
        client_admin = dict()
        client_name = client_details.get("client_name")
        user_name = client_details.get("client_email")
        phone_number = client_details.get("client_phone")
        client_id = client_details.get("_id")
        password = utility_obj.random_pass()

        # Checking if client_name, client_id and client_email is present
        if not client_name or not client_id or not user_name:
            raise HTTPException(status_code=422,
                                detail="Client Name, Client Id and Client Email "
                                       "is required.")

        role = await DatabaseConfiguration().role_collection.find_one(
            {"role_name": "client_admin"}, {"role_name": 1, "pgsql_id": 1}
        )
        if not role:
            raise DataNotFoundError(message="Role")
        role["role_id"] = role.pop("_id")

        # Check if user already exist
        check = await DatabaseConfiguration().user_collection.find_one(
            {"user_name": user_name})
        if check:
            raise HTTPException(status_code=422,
                                detail=f"Client Admin already exist with this Email.")
        # Creating Dictionary for Client Admin
        password2 = Hash().get_password_hash(password)
        client_admin["first_name"] = client_name
        # Making them Empty String Client name can be a Company Name, though in Future we can add First Name, Last Name
        client_admin["middle_name"] = ""
        client_admin["last_name"] = ""
        client_admin["user_name"] = user_name
        client_admin["mobile_number"] = phone_number
        client_admin["password"] = password2
        client_admin["email"] = user_name
        client_admin["associated_client"] = client_id
        client_admin["role"] = role
        client_admin["last_accessed"] = datetime.utcnow()
        client_admin["created_on"] = datetime.utcnow()
        client_admin["created_by"] = ObjectId(client_details.get("created_by"))
        client_admin["user_type"] = "client_admin"
        client_admin["is_activated"] = True

        # Inserting the client_admin into DB
        client_creation = await DatabaseConfiguration().user_collection.insert_one(client_admin)

        # Invalidating Cache
        await cache_invalidation(api_updated="updated_user")

        client_admin['password'] = password
        client_admin["_id"] = client_creation.inserted_id
        return client_admin

    async def create_user(self, details: dict, user_name: any, user_type: str) \
            -> dict:
        """
        Create a new user except super admin.

        Params:
            details (dict): A dictionary which contains create new user info.
            user_name (str): An user_name of user.
            user_type: Type of new user.

        Returns:
              dict: A dictionary which contains newly created user info.
        """
        from app.dependencies.oauth import cache_invalidation
        user = await DatabaseConfiguration().user_collection.find_one(
            {"user_name": user_name})
        if not user:
            raise HTTPException(status_code=404, detail=f"User not exist!")
        email = details.get("email", "").lower()
        if await DatabaseConfiguration().user_collection.find_one(
                {"user_name": email}) is not None:
            raise HTTPException(status_code=422,
                                detail=f"user_name already exists!")
        role_name = user.get("role", {}).get("role_name")
        check_role = await DatabaseConfiguration().role_collection.find_one(
            {"role_name": role_name}
        )
        associated_colleges = details.get("associated_colleges", [])
        if associated_colleges is None:
            associated_colleges = []
        try:
            details["associated_colleges"] = [ObjectId(i) for i in
                                              associated_colleges]
        except:
            raise HTTPException(
                status_code=422, detail="Enter valid associated college id."
            )
        if user_type != "client_manager":
            if role_name != "super_admin":
                try:
                    if details["associated_colleges"][0] not in user.get(
                            "associated_colleges"):
                        raise HTTPException(
                            status_code=422,
                            detail="Associated id should be correct. You "
                                   "can't create user for other college.",
                        )
                except IndexError:
                    details["associated_colleges"] = []
        await self.check_create_or_delete_user_permission(
            check_role, user_type, operation="add")
        if user_type != "college_publisher_console" and details.get(
                "associated_source_value"
        ):
            raise HTTPException(
                status_code=422,
                detail="Only publisher can have associated source value. Remove field 'associated_source_value' and "
                       "register again.",
            )
        if user_type == "college_publisher_console" and (
                details.get("associated_source_value") in ["", None]):
            raise HTTPException(status_code=422,
                                detail="Publisher must be associated with source.")

        if user_type == "college_publisher_console":
            details.update({
                "bulk_lead_push_limit": {
                    "daily_limit": details.pop("daily_limit",
                                               settings.publisher_bulk_lead_push_limit.get(
                                                   "daily_limit")),
                    "bulk_limit": details.pop("bulk_limit",
                                              settings.publisher_bulk_lead_push_limit.get(
                                                  "bulk_limit"))
                }
            })

        create_role = await DatabaseConfiguration().role_collection.find_one(
            {"role_name": user_type})
        toml_data = utility_obj.read_current_toml_file()
        if toml_data.get('testing', {}).get('test') is True or settings.environment == "demo":
            # for testing , set hardcoded pwd during registration
            random_password = "getmein"
        else:
            # generate random password
            random_password = utility_obj.random_pass()
        current_datetime = datetime.utcnow()
        details = utility_obj.break_name(details)
        designation = details.get("designation")
        if designation:
            details["designation"] = designation.title()
        details.update(
            {"password": Hash().get_password_hash(random_password), "role": {
                "role_name": user_type,
                "role_id": ObjectId(create_role.get("_id")),
            }, "is_activated": True, "created_by": ObjectId(user.get("_id")),
             "last_accessed": current_datetime,
             "created_on": current_datetime, "user_name": email,
             "user_type": user_type, "email": email})
        details.update(
            {
                "associated_source_value": details.get(
                    "associated_source_value").title()
                if (
                        details.get("associated_source_value")
                        and details.get("associated_source_value") != ""
                )
                else None
            }
        )
        if details.get("_id"):
            details.pop("_id")
        await DatabaseConfiguration().user_collection.insert_one(details)
        await cache_invalidation(api_updated="updated_user")
        return {
            "details": self.user_helper(details),
            "user_name": email,
            "password": random_password,
            "first_name": details.get("first_name").title(),
        }

    async def retrieve_menus_and_permissions(self, user, user_type):
        """
        Retrieve menus and permissions
        """
        role_name = user.get("role", {}).get("role_name")
        await self.check_permission(role_name=role_name, user_type=user_type)
        menus_and_permissions = await DatabaseConfiguration().role_collection.find_one(
            {"role_name": user_type}
        )
        return RoleHelper().role_serialize(menus_and_permissions)

    async def user_permissions(self, user, user_type, permissions):
        """
        Retrieve menus and permissions"""
        role_name = user.get("role", {}).get("role_name")
        await self.check_permission(role_name=role_name, user_type=user_type)
        role = await DatabaseConfiguration().role_collection.find_one(
            {"role_name": user_type})
        temp_permission = role.get("permission", {})
        temp_permission.update(permissions)
        update_permission = await DatabaseConfiguration().role_collection.update_one(
            {"_id": ObjectId(str(role["_id"]))},
            {"$set": {"permission": temp_permission}}
        )
        if update_permission:
            return True
        raise HTTPException(status_code=422, detail="Permission not updated.")

    async def update_user_data(self, data: dict, user_name: str,
                               user_id: id) -> dict:
        """
        Update user data by id.

        Params:
            data (dict): User data which need to update.
            user_name (str): An user_name of an user.
            user_id (str): An unique id of user.

        Returns:
              dict: A dictionary contains info about update user.
        """
        # Don't move import statement at top otherwise get ImportError because
        # of circular import
        from app.helpers.template.template_configuration import \
            TemplateActivity
        from app.dependencies.oauth import cache_invalidation
        current_user = await self.is_valid_user(user_name)
        await utility_obj.is_id_length_valid(_id=user_id, name="User id")
        user = await DatabaseConfiguration().user_collection.find_one(
            {"_id": ObjectId(user_id)})
        if not user:
            return {
                'detail': "User not found. Make sure provided user id should "
                          "be correct."}
        await self.check_permission(
            role_name=current_user.get("role", {}).get("role_name"),
            user_type=user.get("role", {}).get("role_name"))
        last_modified_timeline = await TemplateActivity().get_last_timeline(
            user)
        if user.get("last_modified_timeline") is None:
            user["last_modified_timeline"] = []
        user.get("last_modified_timeline", []).insert(0,
                                                      last_modified_timeline[
                                                          0])
        data.update(
            {"last_modified_timeline": user.get("last_modified_timeline")})
        if user.get("role", {}).get("role_name") == "college_publisher_console":
            data.update({
                "bulk_lead_push_limit": {
                    "daily_limit": data.pop("daily_limit",
                                            settings.publisher_bulk_lead_push_limit.get(
                                                "daily_limit")),
                    "bulk_limit": data.pop("bulk_limit",
                                           settings.publisher_bulk_lead_push_limit.get(
                                               "bulk_limit"))
                }
            })

        await DatabaseConfiguration().user_collection.update_one(
            {'_id': user.get('_id')},
            {'$set': data})
        await cache_invalidation(api_updated="updated_user", user_id=user.get("email"))
        return {"message": "User data updated."}

    async def delete_users_by_ids(self, user_name, user_ids) -> dict:
        """
        Delete users by ids.

        Params:
            user_name (str): An user_name of an user.
            user_ids (list): A list contains user_ids.

        Returns:
              dict: A dictionary contains info about delete users.
        """
        current_user = await self.is_valid_user(user_name)
        user_ids = [ObjectId(user_id) for user_id in user_ids]
        if current_user.get("role", {}).get("role_name") not in ["super_admin",
                                                                 "college_super_admin",
                                                                 "college_admin"]:
            raise HTTPException(status_code=401,
                                detail="Not enough permissions")
        await DatabaseConfiguration().user_collection.delete_many(
            {"_id": {"$in": user_ids},
             "role.role_name": {"$ne": "super_admin"}}),
        return {"message": "Deleted users by ids."}

    async def download_panelist_by_ids(self, current_user: User,
                                       panelists_ids: list,
                                       background_tasks: BackgroundTasks,
                                       request: Request, college_id) -> dict:
        """
        Download panelist by ids.

        Params:
            current_user (User): An user_name of the user.
                For Example, test@example.com
            panelists_ids (list): A list contains panelists_ids.
                For Example,
            ["64b2c11e9f4f0ce7ad232512", "64b2c11e9f4f0ce7ad232513"]

        Returns:
              dict: A dictionary contains info about download users.
              Successful Response - {"file_url": "https://***.com/***",
                                "message": "File downloaded successfully."}
        """
        # Don't move import statement at top otherwise get ImportError because
        # of circular import
        from app.database.aggregation.admin_user import AdminUser
        from app.s3_events.s3_events_configuration import \
            upload_csv_and_get_public_url
        current_datetime = datetime.utcnow()
        user_helper = UserHelper()
        await user_helper.is_valid_user(current_user)
        users, total_users = await AdminUser().get_panelist_by_ids(
            college_id, panelists_ids)
        toml_data = utility_obj.read_current_toml_file()
        if toml_data.get('testing', {}).get('test') is False:
            background_tasks.add_task(
                DownloadRequestActivity().store_download_request_activity,
                request_type=f"Users data",
                requested_at=current_datetime,
                ip_address=utility_obj.get_ip_address(request),
                user=await user_helper.check_user_has_permission(
                    user_name=current_user),
                total_request_data=len(users), is_status_completed=True,
                request_completed_at=datetime.utcnow())
        if users:
            data_keys = list(users[0].keys())
            temp_public_download_url = await upload_csv_and_get_public_url(
                fieldnames=data_keys, data=users, name="users_data"
            )
            return temp_public_download_url
        raise HTTPException(status_code=404, detail="Panelist not found.")

    async def panelist_manager_header_info(self, current_user: str) -> dict:
        """
        Get panelist manager header info.

        Params:
            current_user (str): An user_name of the user.
                For Example, test@example.com

        Returns:
              dict: A dictionary which contains panelist manager header info.
            Successful Response -
            {"message": "Get panelist manager header info."}
        """
        await self.is_valid_user(current_user)
        return {"message": "Get panelist manager header info.",
                "data": {
                    "active_panelist":
                        await DatabaseConfiguration().user_collection.count_documents(
                            {"role.role_name": "panelist", "is_activated": True
                             }), "available_slots":
                        await DatabaseConfiguration().slot_collection.count_documents(
                            {"status": "published"}),
                    "interview_done":
                        await DatabaseConfiguration().studentApplicationForms.
                        count_documents(
                            {"interviewStatus.status": "Interviewed"}),
                    "total_panelists":
                        await DatabaseConfiguration().user_collection.count_documents(
                            {"role.role_name": "panelist"})
                }}

    async def get_user_data_by_id(self, user_name: str | None, user_id: str,
                                  check_authentication: bool = True) -> dict:
        """
        Get user data by id.

        Params:
            user_name (str): An user_name of user.
            user_id (str): An unique identifier/id of user_id.
                For example, 123456789012345678901234

        Returns:
              dict: A dictionary contains info about user.
            Successful response contains user info with message -
            `Get user data.`
        """
        if check_authentication:
            await self.is_valid_user(user_name)
        await utility_obj.is_id_length_valid(user_id, "User id")
        if (user := await DatabaseConfiguration().user_collection.find_one(
                {"_id": ObjectId(user_id)})) is None:
            raise HTTPException(status_code=404,
                                detail="User not found.")
        return {"message": "Get user data.", "data": self.user_helper(user)}

    async def get_user_data(
            self, user: dict, page_num: int, page_size: int):
        """
        Get user data.

        Params:
            user (dict): A dictionary contains user data.
                For example, {"user_name": "", "user_id": "123456789012345678901234"}
            page_num (int): A page number.
            page_size (int): A page size.

        Returns:
            dict: A dictionary contains info about user.
            Successful response contains user info with message -
            `Get user data.`
        """
        filter_data = {}
        if user.get("associated_colleges"):
            filter_data["associated_colleges"] = {
                "$in": [ObjectId(i) for i in user.get("associated_colleges")]
            }
        skip, limit = await utility_obj.return_skip_and_limit(
            page_num=page_num, page_size=page_size)
        data = await DatabaseConfiguration().user_collection.aggregate([
            {
                "$match": filter_data
            },
            {
                "$facet": {
                    "metadata": [
                        {"$count": "total"}
                    ],
                    "users": [
                        {
                            "$skip": skip
                        },
                        {
                            "$limit": limit
                        },
                        {
                            "$project": {
                                "_id": {"$toString": "$_id"},
                                "user_name": 1,
                                "name": {
                                    "$trim": {
                                        "input": {
                                            "$concat": [
                                                {"$ifNull": ["$first_name", ""]},
                                                " ",
                                                {"$ifNull": ["$middle_name", ""]},
                                                " ",
                                                {"$ifNull": ["$last_name", ""]}
                                            ]
                                        },
                                        "chars": " "
                                    }
                                },
                                "permissions": {"$ifNull": ["$assign_group_permissions", []]}
                            }
                        }
                    ]
                }
            },
            {
                "$project": {
                    "total": {"$arrayElemAt": ["$metadata.total", 0]},
                    "user_list": "$users"
                }
            }
        ]).to_list(None)
        if not data:
            raise DataNotFoundError("User")

        data = data[0]
        data = json.dumps(data, cls=CustomJSONEncoder)
        data = json.loads(data)

        response = await utility_obj.pagination_in_aggregation(
            skip, limit, data.get("total"), route_name="/users/get_all_users/"
        )

        return {
            "data": data.get("user_list", []),
            "total": data.get("total", 0),
            "count": len(data.get("user_list", [])),
            "pagination": response["pagination"],
            "message": "data fetch successfully",
        }
