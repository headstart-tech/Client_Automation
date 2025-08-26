"""This file contain all the crud operation Helper of super account manager"""

import json

from bson import ObjectId
from app.core.background_task_logging import background_task_wrapper
from app.core.custom_error import CustomError, NotEnoughPermission, DataNotFoundError
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.hashing import Hash
from app.dependencies.oauth import is_testing_env, cache_invalidation
from app.background_task.send_mail_configuration import EmailActivity
from app.helpers.client_curd.client_curd_helper import ClientCurdHelper
from app.models.super_account_manager import SystemFieldsModel


class SAMCrudHelper:
    async def create_super_account_manager(self, sam_details: dict, user: dict) -> dict:
        """
        This function is used to create super account manager and can be Used by only Admin & Super Admin

        Params:
            - sam_details (dict): A dictionary containing the super account manager details.
            - user (dict): A dictionary containing the user details.

        Returns:
            - message (str): A string containing the success message.
            - super_account_manager_id (str): A string containing the super account manager id.

        Raises:
            - CustomError: If email or phone already exists
        """
        from app.dependencies.oauth import cache_invalidation

        # Checking if it is testing
        testing = is_testing_env()

        # Checking Email and Phone Uniqueness
        if (
            not (
                await DatabaseConfiguration().user_collection.find_one(
                    {
                        "$or": [
                            {"email": sam_details.get("email")},
                            {"mobile_number": sam_details.get("mobile_number")},
                        ]
                    }
                )
            )
            is None
        ):
            raise CustomError("Email or Mobile Number already exists")

        role = await DatabaseConfiguration().role_collection.find_one(
            {"role_name": "super_account_manager"}, {"role_name": 1, "pgsql_id": 1}
        )
        if not role:
            raise DataNotFoundError(message="Role")
        role["role_id"] = role.pop("_id")

        # Creating Random Password
        password = utility_obj.random_pass()

        # Create System Fields
        system_fields = SystemFieldsModel(
            created_by=user.get("_id"),
            user_name=sam_details.get("email"),
            password=Hash().get_password_hash(password),
            role=role,
            user_type="super_account_manager",
        )

        # Combining all the Details
        sam_details.update(system_fields.model_dump())

        # Converting to object id
        sam_details = await ClientCurdHelper().to_object_id(["created_by"], sam_details)

        # Sending Email
        if not testing:
            await EmailActivity().send_username_password_to_user(
                user_name=sam_details.get("user_name"),
                password=password,
                first_name=sam_details.get("first_name"),
                email_preferences={},
                request=None,
                event_type="email",
                event_status="sent",
                event_name="Verification",
                payload={
                    "content": "Create new user",
                    "email_list": [sam_details.get("email")],
                },
            )

        await cache_invalidation(api_updated="updated_user")

        # Inserting Super Account Manager
        super_account_manager_id = (
            await DatabaseConfiguration().user_collection.insert_one(sam_details)
        )
        return {
            "message": "Super Account Manager Created Successfully",
            "super_account_manager_id": str(super_account_manager_id.inserted_id),
        }

    async def get_sam_by_id(
        self, super_account_manager_id: str, user: dict = {}
    ) -> dict:
        """
        This function is used to get super account manager by id,
        This Should be Used by only Super Account Manager, Admin & Super Admin

        Params:
            - super_account_manager_id (str): A string containing the super account manager id.
            - user (dict): A dictionary containing the user details.

        Returns:
            - super_account_manager_details (dict): A dictionary containing the super account manager details.

        Raises:
            - DataNotFoundError: If super account manager not found
            - CustomError: If super account manager id is invalid
            - NotEnoughPermission: If the Accessing User is Super Account Manager and its accessing other
              super account manager
        """
        # Checking the super_account_manager_id is Valid or not
        if not ObjectId.is_valid(super_account_manager_id):
            raise CustomError("Invalid Super Account Manager Id")

        # If User is Itself the Same Super Account Manager
        if user.get("user_type") == "super_account_manager":
            if user.get("_id") == super_account_manager_id:
                user.pop("password")
                return json.loads(json.dumps(user, default=str))
            else:
                # If the Accessing User is Super Account Manager and its accessing other super account manager
                raise NotEnoughPermission

        # Getting super account manager details
        super_account_manager_details = (
            await DatabaseConfiguration().user_collection.find_one(
                {
                    "_id": ObjectId(super_account_manager_id),
                    "user_type": "super_account_manager",
                },
                {"password": 0},
            )
        )

        if super_account_manager_details is None:
            raise DataNotFoundError("Super Account Manager")

        super_account_manager_details = json.loads(
            json.dumps(super_account_manager_details, default=str)
        )

        return super_account_manager_details

    async def get_all_sam(
        self, route: str, page: int = None, limit: int = None
    ) -> dict:
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

        # Getting all super account manager details
        sam_list = (
            await DatabaseConfiguration()
            .user_collection.aggregate(
                [
                    {"$match": {"user_type": "super_account_manager"}},
                    {"$project": {"password": 0}},
                ]
            )
            .to_list(length=None)
        )

        # Checking if super account manager not found
        if not sam_list:
            raise DataNotFoundError("Super Account Managers")

        # Converting to String
        sam_list = json.loads(json.dumps(sam_list, default=str))

        # Pagination
        if page and limit:
            sam_list = await utility_obj.pagination_in_api(
                page_num=page,
                page_size=limit,
                data=sam_list,
                data_length=len(sam_list),
                route_name=route,
            )
            sam_list.update({"message": "Super Account Manager Data List Found"})
            return sam_list

        return {
            "message": "Super Account Manager Data List Found",
            "super_account_managers": sam_list,
        }

    async def update_sam(
        self, super_account_manager_id: str, sam_details: dict, user: dict
    ) -> dict:
        """
        This function is used to update super account manager details,
        this Should be Used by only Super Admin, Admin & Super Account Manager

        Params:
            - super_account_manager_id (str): A string containing the super account manager id.
            - sam_details (dict): A dictionary containing the super account manager details.
            - user (dict): A dictionary containing the user details.

        Returns:
            - message (str): A string containing the success message.

        Raises:
            - DataNotFoundError: If super account manager not found
            - NotEnoughPermission: If the Accessing User is Super Account Manager and its accessing other
              super account manager
            - CustomError: If the Super Account Manager Id is invalid
        """
        from app.dependencies.oauth import cache_invalidation

        # Checking the Super Account Manager Things
        await self.get_sam_by_id(
            super_account_manager_id=super_account_manager_id, user=user
        )

        # Updating user_name
        if sam_details.get("email"):
            # Check if email or username already exists
            if await DatabaseConfiguration().user_collection.find_one(
                {
                    "$or": [
                        {"email": sam_details.get("email")},
                        {"user_name": sam_details.get("email")},
                    ],
                    "_id": {"$ne": ObjectId(super_account_manager_id)},
                }
            ):
                raise CustomError("Email already exists")
            sam_details.update({"user_name": sam_details.get("email")})

        # Check If Mobile Number already exists
        if sam_details.get("mobile_number"):
            if await DatabaseConfiguration().user_collection.find_one(
                {
                    "mobile_number": {
                        "$in": [
                            sam_details.get("mobile_number"),
                            int(sam_details.get("mobile_number")),
                        ]
                    },
                    "_id": {"$ne": ObjectId(super_account_manager_id)},
                }
            ):
                raise CustomError("Mobile Number already exists")

        # Updating Super Account Manager
        await DatabaseConfiguration().user_collection.update_one(
            {
                "_id": ObjectId(super_account_manager_id),
                "user_type": "super_account_manager",
            },
            {"$set": sam_details},
        )

        # Invalidating Cache
        await cache_invalidation(api_updated="updated_user")

        return {"message": "Super Account Manager Updated Successfully"}

    async def activate_sam(self, super_account_manager_id: str) -> dict:
        """
        This function is used to activate super account manager,
        this Should be Used by only Super Admin & Admin

        Params:
            - super_account_manager_id (str): A string containing the super account manager id.

        Returns:
            - message (str): A string containing the success message.

        Raises:
            - DataNotFoundError: If super account manager not found
            - CustomError: If the Super Account Manager Id is invalid
            - CustomError: If the Super Account Manager is already activated
        """

        # Checking the Super Account Manager Things
        sam = await self.get_sam_by_id(
            super_account_manager_id=super_account_manager_id
        )

        # Checking if its Already Activated
        if sam.get("is_activated"):
            raise CustomError("Super Account Manager Already Activated")

        # Activating Super Account Manager
        await DatabaseConfiguration().user_collection.update_one(
            {
                "_id": ObjectId(super_account_manager_id),
                "user_type": "super_account_manager",
            },
            {"$set": {"is_activated": True}},
        )

        # Invalidating Cache
        await cache_invalidation(api_updated="updated_user")

        return {"message": "Super Account Manager Activated Successfully"}

    async def deactivate_sam(self, super_account_manager_id: str) -> dict:
        """
        This function is used to deactivate super account manager,
        this Should be Used by only Super Admin & Admin

        Params:
            - super_account_manager_id (str): A string containing the super account manager id.

        Returns:
            - message (str): A string containing the success message.

        Raises:
            - DataNotFoundError: If super account manager not found
            - CustomError: If the Super Account Manager Id is invalid
            - CustomError: If the Super Account Manager is already deactivated
        """
        # Checking the Super Account Manager Things
        sam = await self.get_sam_by_id(
            super_account_manager_id=super_account_manager_id
        )

        # Checking if its Already Deactivated
        if not sam.get("is_activated"):
            raise CustomError("Super Account Manager Already Deactivated")

        # Checking if Super Account Manager have allocated Account Managers
        if sam.get("assigned_account_managers"):
            raise CustomError("Super Account Manager have Allocated Account Managers")

        # Deactivating Super Account Manager
        await DatabaseConfiguration().user_collection.update_one(
            {
                "_id": ObjectId(super_account_manager_id),
                "user_type": "super_account_manager",
            },
            {"$set": {"is_activated": False}},
        )

        return {"message": "Super Account Manager Deactivated Successfully"}

    @background_task_wrapper
    async def assigning_am_to_sam(
        self,
        super_account_manager_id: ObjectId,
        sam_details: dict,
        account_manager_ids: list[ObjectId],
        account_manager_details: list[dict],
    ) -> None:
        """
        This Function is a Background Task for Db Changes of AM & SAM

        Params:
            - super_account_manager_id (str): A string containing the super account manager id (ObjectId).
            - sam_details (dict): A dictionary containing the super account manager details.
            - account_manager_ids (list): A list containing the unique account manager ids.
            - account_manager_details (list): A list containing the account manager details.

        Returns:
            - None
        """
        # Removing Account Manager from Super Account Managers
        await DatabaseConfiguration().user_collection.update_many(
            {
                "user_type": "super_account_manager",
                "assigned_account_managers.account_manager_id": {
                    "$in": account_manager_ids
                },
            },
            {
                "$pull": {
                    "assigned_account_managers": {
                        "account_manager_id": {"$in": account_manager_ids}
                    }
                }
            },
        )

        # Adding Super Account Manager to Account Managers
        await DatabaseConfiguration().user_collection.update_many(
            {"_id": {"$in": account_manager_ids}, "user_type": "account_manager"},
            {
                "$set": {
                    "associated_super_account_manager": ObjectId(
                        super_account_manager_id
                    ),
                    "associated_super_account_manager_name": utility_obj.name_can(
                        sam_details
                    ),
                }
            },
        )

        # Adding Account Managers to Super Account Manager
        await DatabaseConfiguration().user_collection.update_one(
            {
                "_id": ObjectId(super_account_manager_id),
                "user_type": "super_account_manager",
            },
            {
                "$push": {
                    "assigned_account_managers": {"$each": account_manager_details}
                }
            },
        )

    async def assign_account_managers_to_super_account_manager(
        self, super_account_manager_id: str, account_manager_ids: list
    ) -> dict:
        """
        This function is used to assign account managers to super account manager,
        this Should be Used by only Super Admin & Admin

        Params:
            - super_account_manager_id (str): A string containing the super account manager id.
            - account_manager_ids (list): A list containing the account manager ids.

        Returns:
            - message (str): A string containing the success message.

        Raises:
            - DataNotFoundError: If super account manager not found
            - CustomError: If the Super Account Manager Id is invalid
        """
        # Checking the Super Account Manager Things
        sam_details = await self.get_sam_by_id(
            super_account_manager_id=super_account_manager_id
        )

        # Getting Previous Account Managers
        previous_account_manager = set()
        for account_managers in sam_details.get("assigned_account_managers"):
            previous_account_manager.add(account_managers.get("account_manager_id"))

        new_account_managers = set(account_manager_ids)

        # Getting Unique Account Managers
        unique_account_managers = new_account_managers.difference(
            previous_account_manager
        )

        # Converting to ObjectIds
        unique_account_managers = [
            ObjectId(account_manager_id)
            for account_manager_id in unique_account_managers
        ]

        # Getting Details of Account Manager
        account_manager_full_details = (
            await DatabaseConfiguration()
            .user_collection.aggregate(
                [
                    {
                        "$match": {
                            "_id": {"$in": unique_account_managers},
                            "user_type": "account_manager",
                        }
                    }
                ]
            )
            .to_list(None)
        )

        # Checking if all account manager are found (Comment it for Now, We can enable this anytime)
        # if len(account_manager_full_details) != len(unique_account_managers):
        #     raise DataNotFoundError("Some Account Manager")

        account_manager_details = []

        # Formatting Account Manager Details for Storing in Super Account Manager as assigned_account_managers
        for account_manager in account_manager_full_details:
            account_manager_details.append(
                {
                    "account_manager_id": account_manager.get("_id"),
                    "account_manager_name": utility_obj.name_can(account_manager),
                }
            )

        # Db Queries for Background Task
        if unique_account_managers:
            await self.assigning_am_to_sam(
                super_account_manager_id=super_account_manager_id,
                sam_details=sam_details,
                account_manager_ids=unique_account_managers,
                account_manager_details=account_manager_details,
            )

        return {
            "message": f"{len(unique_account_managers)} Account Managers Assigned Successfully"
        }
