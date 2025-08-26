"""This File contains the helper functions for Account Manager"""

import json

from bson.objectid import ObjectId

from app.background_task.send_mail_configuration import EmailActivity
from app.core.background_task_logging import background_task_wrapper
from app.core.custom_error import NotEnoughPermission, DataNotFoundError, CustomError
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.hashing import Hash
from app.dependencies.oauth import is_testing_env
from app.helpers.client_curd.client_curd_helper import ClientCurdHelper
from app.helpers.super_account_manager.sam_crud_operation import SAMCrudHelper
from app.models.account_manager import SystemFields


class AccountManagerCRUDHelper:
    async def get_clients_by_ids(self, client_ids: list, user: dict = None) -> dict:
        """
        This function is used to get clients by ids

        Params:
            - client_ids (list): A list containing the clients ids.
            - user (dict): A dictionary containing the user details.

        Returns:
            - data (list): A list containing the clients.

        Raises:
            - DataNotFoundError: If clients not found

        """
        pipeline = []

        # Checking If the client_ids are Valid or not
        if not all(ObjectId.is_valid(client_id) for client_id in client_ids):
            raise CustomError(message="Invalid client ids")

        # Checking if the User is Account Manager
        if user and user.get("user_type") == "account_manager":
            pipeline.append(
                {
                    "$match": {
                        "assigned_account_managers": {
                            "$in": [ObjectId(user.get("_id"))]
                        }
                    }
                }
            )

        pipeline.append(
            {
                "$match": {
                    "_id": {"$in": [ObjectId(client_id) for client_id in client_ids]}
                }
            }
        )
        pipeline.append({"$project": {"client_configuration": 0}})

        data = (
            await DatabaseConfiguration()
            .client_collection.aggregate(pipeline)
            .to_list(length=None)
        )
        if not data:
            raise DataNotFoundError(message="Clients")

        return data

    @background_task_wrapper
    async def allocate_am_to_sam_and_send_email(
        self, details: dict, testing: bool
    ) -> None:
        """
        This function is used to allocate account manager to super account manager and Send EMail in Background

        Params:
            - details (dict): A dictionary containing the account manager details.
            - testing (bool): A boolean value indicating whether the environment is in testing or not.

        Returns:
            - None
        """
        if not testing:
            await EmailActivity().send_username_password_to_user(
                user_name=details.get("user_name"),
                password=details.get("password"),
                first_name=details.get("name"),
                email_preferences={},
                request=None,
                event_type="email",
                event_status="sent",
                event_name="Verification",
                payload={
                    "content": "Create new user",
                    "email_list": [details.get("email")],
                },
            )

        await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(details.get("associated_super_account_manager"))},
            {
                "$push": {
                    "assigned_account_managers": {
                        "account_manager_id": ObjectId(details.get("_id")),
                        "account_manager_name": utility_obj.name_can(details),
                    }
                }
            },
        )

    async def create_account_manager_helper(self, details: dict, user: dict) -> dict:
        """
        This function is used to create account manager

        Params:
            - details (dict): A dictionary containing the account manager details.
            - user (dict): A dictionary containing the user details.

        Returns:
            - message (str): A string containing the success message.
            - account_manager_id (str): Object id of account manager

        Raises:
            - CustomError: If email or mobile number already exists
        """
        from app.dependencies.oauth import cache_invalidation

        # Checking if the Environment is in Testing
        testing = is_testing_env()

        # Check whether Email and Mobile Number already exist or not
        if await DatabaseConfiguration().user_collection.find_one(
            {
                "$or": [
                    {"email": details.get("email")},
                    {"mobile_number": details.get("mobile_number")},
                ]
            }
        ):
            raise CustomError(message="Email or Mobile Number already exists")

        # If the Account Manager is itself the Super Account Manager
        if user.get("role", {}).get("role_name", "") == "super_account_manager":
            details["associated_super_account_manager"] = user.get("_id")

        if not details.get("associated_super_account_manager"):
            raise CustomError(message="Associated Super Account Manager is Required")

        # Checking if the Super Account Manager exists or not
        if not (
            sam_details := await SAMCrudHelper().get_sam_by_id(
                details.get("associated_super_account_manager"), user
            )
        ):
            raise DataNotFoundError(message="Super Account Manager")

        role = await DatabaseConfiguration().role_collection.find_one(
            {"role_name": "account_manager"}, {"role_name": 1, "pgsql_id": 1}
        )
        if not role:
            raise DataNotFoundError(message="Role")
        role["role_id"] = role.pop("_id")

        # Creating Random Password
        password = utility_obj.random_pass()

        # Creating System Fields
        system_fields = SystemFields(
            **{
                "associated_super_account_manager_name": utility_obj.name_can(
                    sam_details
                ),
                "created_by": user.get("_id"),
                "user_name": details.get("email"),
                "password": Hash().get_password_hash(password),
                "role": role,
            }
        )

        # Combining all details and System Fields
        details.update(system_fields.model_dump())

        # Converting to Object Ids
        details = await ClientCurdHelper().to_object_id(
            keys=["created_by", "associated_super_account_manager"], data=details
        )

        # Creating Account Manager
        account_manager = await DatabaseConfiguration().user_collection.insert_one(
            details
        )

        # Allocating Account Manager to Super Account Manager & Sending mail
        await self.allocate_am_to_sam_and_send_email(details, testing)

        await cache_invalidation(api_updated="updated_user")

        # Returning Account Manager Id
        return {
            "message": "Account Manager Created Successfully",
            "account_manager_id": str(account_manager.inserted_id),
        }

    async def get_account_manager_by_id(
        self, account_manager_id: str, user: dict
    ) -> dict:
        """
        This function is used to get account manager details by id

        Params:
            - account_manager_id (str): A string containing the account manager id.
            - user (dict): A dictionary containing the user details.

        Raises:
            - DataNotFoundError: If account manager not found
            - NotEnoughPermission: If the Accessing User is Super Account Manager, and it is not allocated to it

        Returns:
            - account_manager (dict): A dictionary containing the account manager details.
        """
        # Checking the account_manager_id is Valid or not
        if not ObjectId.is_valid(account_manager_id):
            raise CustomError(message="Invalid account manager id")

        # If User is Itself the Same Account Manager
        if user.get("user_type") == "account_manager":
            if user.get("_id") == account_manager_id:
                user.pop("password")
                return json.loads(json.dumps(user, default=str))
            else:
                raise NotEnoughPermission

        # Getting account manager details
        account_manager = await DatabaseConfiguration().user_collection.find_one(
            {"_id": ObjectId(account_manager_id), "user_type": "account_manager"},
            {"password": 0},
        )

        # Checking if account manager exists or not
        if not account_manager:
            raise DataNotFoundError(message="Account Manager")

        # If the Accessing User is Super Account Manager then it will be Checked whether
        # the account manager belongs to it or not
        if user.get("user_type") == "super_account_manager":
            if account_manager.get("associated_super_account_manager") != ObjectId(
                user.get("_id")
            ):
                raise NotEnoughPermission

        account_manager = json.loads(json.dumps(account_manager, default=str))
        return account_manager

    async def get_all_account_manager(
        self, user: dict, route: str, page: int = None, limit: int = None
    ) -> dict:
        """
        This function is used to get all account manager details

        Params:
            - user (dict): A dictionary containing the user details.
            - route (str): A string containing the route.
            - page (Optional[int]): A integer containing the page number.
            - limit (Optional[int]): A integer containing the limit.

        Raises:
            - NotEnoughPermission: If the Accessing User is Super Account Manager, it is not allocated to it
            - DataNotFoundError: If account manager not found

        Returns:
            - data (dict): A list of dictionary containing the account manager details.
        """

        # If the Accessing User is Super Account Manager then only their account manager will be returned
        if user.get("user_type") == "super_account_manager":
            account_managers = (
                await DatabaseConfiguration()
                .user_collection.aggregate(
                    [
                        {
                            "$match": {
                                "user_type": "account_manager",
                                "associated_super_account_manager": ObjectId(
                                    user.get("_id")
                                ),
                            }
                        },
                        {"$project": {"password": 0}},
                    ]
                )
                .to_list(length=None)
            )
        else:
            # If the Accessing User is not Super Account Manager then all account manager will be returned
            account_managers = (
                await DatabaseConfiguration()
                .user_collection.aggregate(
                    [
                        {"$match": {"user_type": "account_manager"}},
                        {"$project": {"password": 0}},
                    ]
                )
                .to_list(length=None)
            )

        # Checking if account managers are there or not
        if not account_managers:
            raise DataNotFoundError(message="Account Managers")

        # Pagination
        if page and limit:
            account_managers = await utility_obj.pagination_in_api(
                data=account_managers,
                data_length=len(account_managers),
                page_num=page,
                page_size=limit,
                route_name=route,
            )
            return json.loads(json.dumps(account_managers, default=str))

        value = {"message": "Account Manager Data List Found", "data": account_managers}
        return json.loads(json.dumps(value, default=str))

    async def update_account_manager(
        self, account_manager_id: str, details: dict, user: dict
    ) -> dict:
        """
        This function is used to update account manager details

        Params:
            - account_manager_id (str): A string containing the account manager id.
            - details (dict): A dictionary containing the account manager details.
            - user (dict): A dictionary containing the user details.

        Raises:
            - DataNotFoundError: If account manager not found
            - NotEnoughPermission: If the Accessing User is Super Account Manager, it is not allocated to it

        Returns:
            - message (str): A string containing the success message.
        """
        from app.dependencies.oauth import cache_invalidation

        # Checking if account manager things
        await self.get_account_manager_by_id(
            account_manager_id=account_manager_id, user=user
        )

        # Updating user_name
        if details.get("email"):
            details.update({"user_name": details.get("email")})

        # Updating account manager details
        await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(account_manager_id), "user_type": "account_manager"},
            {"$set": details},
        )

        await cache_invalidation(api_updated="updated_user")

        return {"message": "Account Manager Updated Successfully"}

    @background_task_wrapper
    async def change_sam_db_queries(
        self,
        super_account_manager_id: ObjectId,
        sam_detail: dict,
        account_manager_id: ObjectId,
        am_detail: dict,
        previous_am: ObjectId,
    ) -> None:
        # Updating account manager details
        await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(account_manager_id), "user_type": "account_manager"},
            {
                "$set": {
                    "associated_super_account_manager": ObjectId(
                        super_account_manager_id
                    ),
                    "super_account_manager_name": utility_obj.name_can(sam_detail),
                }
            },
        )

        # Updating new Super Account Manager
        await DatabaseConfiguration().user_collection.update_one(
            {
                "_id": ObjectId(super_account_manager_id),
                "user_type": "super_account_manager",
            },
            {
                "$push": {
                    "assigned_account_managers": {
                        "account_manager_id": ObjectId(account_manager_id),
                        "account_manager_name": utility_obj.name_can(am_detail),
                    }
                }
            },
        )

        # Updating Previous Account Manager
        await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(previous_am), "user_type": "super_account_manager"},
            {
                "$pull": {
                    "assigned_account_managers": {
                        "account_manager_id": ObjectId(account_manager_id)
                    }
                }
            },
        )

    async def change_super_account_manager(
        self, account_manager_id: str, super_account_manager_id: str, user: dict
    ) -> dict:
        """
        This Function is used to Update the Super Account Manager for Account Manager
        Params:
            - account_manager_id (str): A string containing the account manager id.
            - details (dict): A dictionary containing the account manager details.
            - user (dict): A dictionary containing the user details.

        Raises:
            - DataNotFoundError: If account manager not found
            - NotEnoughPermission: If the Accessing User is not Super Account Manager
            - CustomError: If Super Account Manager is same

        Returns:
            - message (str): A string containing the success message.
        """
        # Checking if account manager things
        am_detail = await self.get_account_manager_by_id(
            account_manager_id=account_manager_id, user=user
        )

        previous_am = am_detail.get("associated_super_account_manager")

        if previous_am == super_account_manager_id:
            raise CustomError("Cannot Assign Same Super Account Manager")

        # Checking if Super Account Manager things
        sam_detail = await SAMCrudHelper().get_sam_by_id(
            super_account_manager_id=super_account_manager_id
        )

        await self.change_sam_db_queries(
            super_account_manager_id=super_account_manager_id,
            sam_detail=sam_detail,
            account_manager_id=account_manager_id,
            am_detail=am_detail,
            previous_am=previous_am,
        )

        return {"message": "Super Account Manager Updated Successfully"}

    @background_task_wrapper
    async def add_clients_bg_task(
        self, account_manager_id: str, unique_clients: list, updated_clients: list
    ) -> None:
        """
        This function is a Background Task which is Used to Add Clients

        Params:
            - account_manager_id (str): A string containing the account manager id.
            - unique_clients (list): A list containing the unique clients.
            - updated_clients (list): A list containing the updated clients.

        Returns:
            - None
        """
        # Converting to ObjectId
        unique_clients = [ObjectId(client) for client in unique_clients]
        updated_clients = [ObjectId(client) for client in updated_clients]
        account_manager_id = ObjectId(account_manager_id)
        updated_clients_info = (
            await DatabaseConfiguration()
            .client_collection.aggregate(
                [
                    {"$match": {"_id": {"$in": updated_clients}}},
                    {"$project": {"client_id": "$_id", "client_name": 1, "_id": 0}},
                ]
            )
            .to_list(length=None)
        )

        # Adding clients to account manager
        await DatabaseConfiguration().user_collection.update_one(
            {"_id": account_manager_id, "user_type": "account_manager"},
            {"$set": {"assigned_clients": updated_clients_info}},
        )

        # Adding account manager to clients
        await DatabaseConfiguration().client_collection.update_many(
            {"_id": {"$in": unique_clients}},
            {"$addToSet": {"assigned_account_managers": account_manager_id}},
        )

    async def add_clients(
        self, account_manager_id: str, clients_ids: list[str], user: dict
    ) -> dict:
        """
        This function is used to add clients, This API can be Used by Super Admin, Admin & Super Account Manager

        Params:
            - account_manager_id (str): A string containing the account manager id.
            - clients_ids (list[str]): A list containing the clients ids.
            - user (dict): A dictionary containing the user details.

        Raises:
            - DataNotFoundError: If account manager not found
            - NotEnoughPermission: If the Accessing User is Super Account Manager, it is not allocated to it

        Returns:
            - message (str): A string containing the success message.
        """
        # Checking if account manager things
        account_manager = await self.get_account_manager_by_id(
            account_manager_id=account_manager_id, user=user
        )

        # Checking the Client Ids List
        if len(await self.get_clients_by_ids(client_ids=clients_ids)) != len(
            clients_ids
        ):
            raise DataNotFoundError(message="Clients")

        # Converting string to ObjectId
        account_manager_id = ObjectId(account_manager_id)
        client_object_ids = [ObjectId(client_id) for client_id in clients_ids]

        # Update account manager document
        previous_clients = set(
            client["client_id"]
            for client in account_manager.get("assigned_clients", [])
        )
        new_clients = set(client_object_ids)
        unique_clients = list(new_clients.difference(previous_clients))
        updated_clients = list(previous_clients.union(new_clients))

        await self.add_clients_bg_task(
            account_manager_id=account_manager_id,
            unique_clients=unique_clients,
            updated_clients=updated_clients,
        )

        return {"message": "Clients Added Successfully"}

    async def remove_clients(
        self, account_manager_id: str, clients_id: str, user: dict
    ) -> dict:
        """
        This function is used to remove clients, This API can be Used by Super Admin, Admin & Super Account Manager

        Params:
            - account_manager_id (str): A string containing the account manager id.
            - clients_ids (list[str]): A list containing the clients ids.
            - user (dict): A dictionary containing the user details.

        Raises:
            - DataNotFoundError: If account manager not found
            - NotEnoughPermission: If the Accessing User is Super Account Manager, it is not allocated to it

        Returns:
            - message (str): A string containing the success message.
        """

        # Checking if account manager things
        account_manager = await self.get_account_manager_by_id(
            account_manager_id=account_manager_id, user=user
        )

        # Checking if the Client even Allocated to this Account Manager
        assigned_client_ids = {
            client["client_id"]
            for client in account_manager.get("assigned_clients", [])
        }
        if clients_id not in assigned_client_ids:
            raise DataNotFoundError(message="Client")

        # Remove Account Manager from Client
        response = await DatabaseConfiguration().client_collection.update_one(
            {
                "_id": ObjectId(clients_id),
                "assigned_account_managers.1": {"$exists": True},
            },
            {
                "$pull": {
                    "assigned_account_managers": ObjectId(account_manager.get("_id"))
                }
            },
        )

        # The Above Queries Means First It will Find the Client and Client should have more than one account manager
        # Then It will Remove the account manager, if the id doesn't exist then it will throw an error
        # Then If the Client has only one account manager then it will throw an error again
        if response.modified_count == 0:
            raise CustomError(
                message="Client is not Found or "
                "There's only one account manager allocated to this client"
            )

        # Remove Client from Account Manager
        await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(account_manager_id), "user_type": "account_manager"},
            {"$pull": {"assigned_clients": {"_id": ObjectId(clients_id)}}},
        )

        return {"message": "Clients Removed Successfully"}

    async def activate_account_manager(
        self, account_manager_id: str, user: dict
    ) -> dict:
        """
        This Function is used to Activate the Account Manager
        Params:
            - account_manager_id (str): A string containing the account manager id.
            - user (dict): A dictionary containing the user details.

        Raises:
            - DataNotFoundError: If account manager not found
            - NotEnoughPermission: If the Accessing User is Super Account Manager, it is not allocated to it
            - CustomError: If account manager is already active

        Returns:
            - message (str): A string containing the success message.
        """
        # Checking if account manager things
        account_manager = await self.get_account_manager_by_id(
            account_manager_id=account_manager_id, user=user
        )

        # Checking if account manager is already active
        if account_manager.get("is_activated"):
            raise CustomError(message="Account Manager is already Active")

        # Updating account manager details
        await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(account_manager_id), "user_type": "account_manager"},
            {"$set": {"is_activated": True}},
        )

        return {"message": "Account Manager Activated Successfully"}

    async def deactivate_account_manager(
        self, account_manager_id: str, user: dict
    ) -> dict:
        """
        This Function is used to Deactivate the Account Manager
        Params:
            - account_manager_id (str): A string containing the account manager id.
            - user (dict): A dictionary containing the user details.

        Raises:
            - DataNotFoundError: If account manager not found
            - NotEnoughPermission: If the Accessing User is Super Account Manager, it is not allocated to it
            - CustomError: If account manager have allocated clients
            - CustomError: If account manager is already INACTIVE

        Returns:
            - message (str): A string containing the success message.
        """
        # Checking if account manager things
        account_manager = await self.get_account_manager_by_id(
            account_manager_id=account_manager_id, user=user
        )

        # Checking if Account Manager have allocated clients
        if account_manager.get("assigned_clients"):
            raise CustomError(message="Account Manager have Allocated Clients")

        # Checking if account manager is already INACTIVE
        if not account_manager.get("is_activated"):
            raise CustomError(message="Account Manager is already Deactivated")

        # Updating account manager details
        await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(account_manager_id), "user_type": "account_manager"},
            {"$set": {"is_activated": False}},
        )

        return {"message": "Account Manager Deactivated Successfully"}
