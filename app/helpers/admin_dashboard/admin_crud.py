from app.models.admin import SystemFieldsModel
from app.database.configuration import DatabaseConfiguration
from app.core.custom_error import CustomError, DataNotFoundError
from app.dependencies.oauth import is_testing_env, Hash
from app.core.utils import utility_obj
from bson import ObjectId
import json
from app.helpers.client_curd.client_curd_helper import ClientCurdHelper
from app.background_task.send_mail_configuration import EmailActivity

class AdminCRUD:


    async def create_admin_user(self, admin_data: dict, user: dict) -> dict:
        """
        This method is used to create admin user, This API can be Used by Super Admin only

        Params:
            - admin_data (dict): A dictionary containing the admin user details.
            - user (dict): A dictionary containing the user details.

        Returns:
            - message (str): A string containing the success message.
            - admin_id (str): Object id of admin
        """
        from app.dependencies.oauth import cache_invalidation
        # Checking if the Environment is in Testing
        testing = is_testing_env()
        # Checking Email & Mobile Uniqueness
        if await DatabaseConfiguration().user_collection.find_one(
            {"$or": [{"email": admin_data.get("email")}, {"mobile_number": admin_data.get("mobile_number")}]}
        ):
            raise CustomError(message="Email or Mobile Number already exists")

        role = await DatabaseConfiguration().role_collection.find_one(
            {"role_name": "admin"}, {"role_name": 1, "pgsql_id": 1}
        )
        if not role:
            raise DataNotFoundError(message="Role")
        role["role_id"] = role.pop("_id")

        # Creating Random Password
        password = utility_obj.random_pass()

        # Creating System Fields
        system_fields = SystemFieldsModel(
            **{
                "created_by": user.get("_id"),
                "user_name": admin_data.get("email"),
                "password": Hash().get_password_hash(password),
                "role": role,
            }
        )

        # Combining all details and System Fields
        admin_data.update(system_fields.model_dump())

        # Converting to Object Ids
        admin_data = await ClientCurdHelper().to_object_id(keys=["created_by"], data=admin_data)

        # Creating Account Manager
        account_manager = await DatabaseConfiguration().user_collection.insert_one(admin_data)

        # Sending Email
        if not testing:
            await EmailActivity().send_username_password_to_user(
                user_name=admin_data.get("user_name"),
                password=password,
                first_name=admin_data.get("first_name"),
                email_preferences={},
                request=None,
                event_type="email",
                event_status="sent",
                event_name="Verification",
                payload={
                    "content": "Create new user",
                    "email_list": [admin_data.get("email")],
                }
            )

        await cache_invalidation(api_updated="updated_user")

        # Returning Account Manager Id
        return {
            "message": "Admin Created Successfully",
            "admin_id": str(account_manager.inserted_id)
        }


    async def get_admin_by_id(self, admin_id: str, user: dict = None) -> dict:
        """
        This method is used to get admin by id, This API can be Used by Super Admin and Self User profile (Admin)

        Params:
            - admin_id (str): A string containing the admin id.
            - user (dict): A dictionary containing the user details.

        Returns:
            - admin (dict): A dictionary containing the admin details.

        Raises:
            - DataNotFoundError: If admin not found
            - CustomError: If admin id is invalid
        """

        # Checking if the admin id is valid
        if not ObjectId.is_valid(admin_id):
            raise CustomError(message="Invalid admin id")

        # If User is Itself the Same Admin
        if user and user.get("user_type") == "admin":
            if user.get("_id") == admin_id:
                user.pop("password")
                return json.loads(json.dumps(user, default=str))
            else:
                # If the Accessing User is Admin and its accessing other admin
                raise CustomError(message="You don't have permission to access this admin")

        # Getting admin by id
        admin = await DatabaseConfiguration().user_collection.find_one(
            {
                "_id": ObjectId(admin_id)
            },
            {
                "password": 0
            }
        )

        # Checking if admin not found
        if not admin:
            raise DataNotFoundError(message="Admin")

        # Returning admin
        return json.loads(json.dumps(admin, default=str))


    async def get_all_admins(self, route: str, page: int = None, limit: int = None) -> dict:
        """
        This function is used to get all super account manager details,
        this Should be Used by only Super Admin & Admin

        Params:
            - route (str): A string containing the route.
            - page (Optional[int]): A integer containing the page number.
            - limit (Optional[int]): A integer containing the limit.

        Returns:
            - message (str): A string containing the success message.
            - super_account_managers (list): A list containing the super account manager details.

        Raises:
            - DataNotFoundError: If super account manager not found
        """

        # Getting all admin details
        admin_list = await DatabaseConfiguration().user_collection.aggregate(
            [
                {
                    "$match": {
                        "user_type": "admin"
                    }
                },
                {
                    "$project": {
                        "password": 0
                    }
                }
            ]
        ).to_list(length=None)

        # Checking if super account manager not found
        if not admin_list:
            raise DataNotFoundError("Admins")

        # Converting to String
        admin_list = json.loads(json.dumps(admin_list, default=str))

        # Pagination
        if page and limit:
            admin_list = await utility_obj.pagination_in_api(
                page_num = page,
                page_size = limit,
                data = admin_list,
                data_length = len(admin_list),
                route_name = route
            )
            admin_list.update({"message": "Admin Data List Found"})
            return admin_list

        return {
            "message": "Admin Data List Found",
            "admins": admin_list
        }


    async def update_admin(self, admin_id: str, admin_data: dict, user: dict) -> dict:
        """
        This method is used to update admin by id, This API can be Used by Super Admin and Self User profile (Admin)

        Params:
            - admin_id (str): A string containing the admin id.
            - admin_data (dict): A dictionary containing the admin details.
            - user (dict): A dictionary containing the user details.

        Returns:
            - message (str): A string containing the success message.

        Raises:
            - DataNotFoundError: If admin not found
            - CustomError: If admin id is invalid
        """
        from app.dependencies.oauth import cache_invalidation
        # Checking Admin Things
        await self.get_admin_by_id(admin_id=admin_id, user=user)

        # Updating User Name
        if admin_data.get("email"):
            # Checking if Email or Username is already exists
            if await DatabaseConfiguration().user_collection.find_one(
                    {
                        "$or": [{"email": admin_data.get("email")}, {"user_name": admin_data.get("email")}],
                        "_id": {"$ne": ObjectId(admin_id)}
                    }, {}
            ):
                raise CustomError(message="Email already exists")
            admin_data.update({"user_name": admin_data.get("email")})

        # Checking if Mobile Number is already exists
        if admin_data.get("mobile_number"):
            if await DatabaseConfiguration().user_collection.find_one(
                {
                    "mobile_number": {"$in": [admin_data.get("mobile_number"), int(admin_data.get("mobile_number"))]},
                    "_id": {"$ne": ObjectId(admin_id)}
                }, {}
            ):
                raise CustomError(message="Mobile Number already exists")

        # Updating Admin
        await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(admin_id), "user_type": "admin"},
            {"$set": admin_data}
        )

        await cache_invalidation(api_updated="updated_user")

        return {
            "message": "Admin Updated Successfully"
        }


    async def activate_admin(self, admin_id: str, user: dict) -> dict:
        """
        This method is used to activate admin by id, This API can be Used by Super Admin only

        Params:
            - admin_id (str): A string containing the admin id.
            - user (dict): A dictionary containing the user details.

        Returns:
            - message (str): A string containing the success message.

        Raises:
            - DataNotFoundError: If admin not found
            - CustomError: If admin id is invalid
        """
        from app.dependencies.oauth import cache_invalidation
        # Checking Admin Things
        admin = await self.get_admin_by_id(admin_id=admin_id, user=user)

        # Checking if the admin is already activated
        if admin.get("is_activated"):
            raise CustomError("Admin Already Activated")

        # Activating Admin
        await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(admin_id), "user_type": "admin"},
            {"$set": {"is_activated": True}}
        )

        # Invalidating Cache
        await cache_invalidation(api_updated="updated_user")

        return {
            "message": "Admin Activated Successfully"
            }


    async def deactivate_admin(self, admin_id: str, user: dict) -> dict:
        """
        This method is used to deactivate admin by id, This API can be Used by Super Admin only

        Params:
            - admin_id (str): A string containing the admin id.
            - user (dict): A dictionary containing the user details.

        Returns:
            - message (str): A string containing the success message.

        Raises:
            - DataNotFoundError: If admin not found
            - CustomError: If admin id is invalid
        """
        from app.dependencies.oauth import cache_invalidation
        # Checking Admin Things
        admin = await self.get_admin_by_id(admin_id=admin_id, user=user)

        # Checking if the admin is already deactivated
        if not admin.get("is_activated"):
            raise CustomError("Admin Already Deactivated")

        # Deactivating Admin
        await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(admin_id), "user_type": "admin"},
            {"$set": {"is_activated": False}}
        )

        # Invalidating Cache
        await cache_invalidation(api_updated="updated_user")

        return {
            "message": "Admin Deactivated Successfully"
            }