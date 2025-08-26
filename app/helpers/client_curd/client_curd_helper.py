"""
This Files Contains Helper Functions for Client CURD Operations
"""
import json
from datetime import datetime

from bson.objectid import ObjectId
from fastapi.responses import JSONResponse

from app.background_task.send_mail_configuration import EmailActivity
from app.core.background_task_logging import background_task_wrapper
from app.core.common_utils import Utils_helper
from app.core.custom_error import CustomError, DataNotFoundError
from app.core.log_config import get_logger
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import is_testing_env
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.client_schema import SystemFields, StatusInfo

logger = get_logger(__name__)

class ClientCurdHelper:

    async def to_object_id(self, keys, data):
        """
        Convert the Keys to ObjectId

        Param:
            keys (list): List of keys
            data (dict): Data to be converted

        Return:
            data (dict): Converted Data
        """
        for key in keys:
            if type(data[key]) == list:
                data[key] = [ObjectId(i) for i in data[key]]
            else:
                data[key] = ObjectId(data[key])

        return data

    async def get_client_by_id(self, client_id, extra_query={}, user=None, need_full = False):
        """
        Get the Client Information

        Param:
            client_id (str): Client Id
            extra_query (dict): Extra Query

        Return:
            data (dict): Client Information
        """
        # Checking Object Id
        if not ObjectId.is_valid(client_id):
            raise CustomError(message="Invalid client id")

        filter = {}

        # Checking if the User is Account Manager
        if user and user.get("user_type") == "account_manager":
            filter['assigned_account_managers'] = {'$in': [ObjectId(user.get("_id"))]}

        filter['_id'] = ObjectId(client_id)

        # Checking the Client
        if not (
                client := await DatabaseConfiguration().client_collection.find_one(
                    filter,
                    extra_query
                )
        ):
            raise DataNotFoundError("Client or Configuration")

        client["can_create_college"] = False
        if client.get("is_configured", False):
            client["can_create_college"] = True

        if need_full:
            # Getting the Student Dashboard
            student_dashboard = await DatabaseConfiguration().college_form_details.find_one(
                {"client_id": ObjectId(client_id)}
            )

            # Getting the Client Screen
            client_screen = await DatabaseConfiguration().master_screens.find_one(
                {"client_id": ObjectId(client_id)}
            )

            # Adding Student Dashboard and Client Screen
            client['student_dashboard'] = student_dashboard
            client['client_screen'] = client_screen
        return client

    @background_task_wrapper
    async def create_client_user_and_send_email(self, client_information: dict, testing: bool = False) -> None:
        """
        Create Client User and Send Email

        Param:
            client_information (dict): Information of the Client
        """
        # Creating Client Admin User
        client_user_details = await UserHelper().create_client_admin(client_information)
        await DatabaseConfiguration().client_collection.update_one(
            {"_id": client_information.get("_id")},
            {"$set": {"client_id": client_user_details.get("_id")}}
        )
        if not testing:
            await EmailActivity().send_username_password_to_user(
                user_name=client_user_details.get("user_name"),
                password=client_user_details.get("password"),
                first_name=client_information.get("client_name"),
                email_preferences={},
                request=None,
                event_type="email",
                event_status="sent",
                event_name="Verification",
                payload={
                    "content": "Create new user",
                    "email_list": [client_information.get("client_email")],
                }
            )
            super_admin = await DatabaseConfiguration().user_collection.find_one(
                {"role.role_name": "super_admin"}
            )
            await EmailActivity().send_onboarding_notification_email(
                entity_type="client",
                entity_data=client_information,
                recipient_email=super_admin.get("email"),
                email_preferences={},
                request=None,
                event_type="email",
                event_status="sent",
                event_name="Verification",
            )

    @background_task_wrapper
    async def allocate_client_to_account_managers(self, client: dict, account_manager_ids: list)-> None:
        """
        Allocate Client to Account Manager

        Param:
            client_id (str): Client Id
            account_manager_ids (list): List of Account Manager Ids

        Return:
            None
        """
        account_manager_ids = [ObjectId(account_manager_id) for account_manager_id in account_manager_ids]
        await DatabaseConfiguration().user_collection.update_many(
            {'_id': {'$in': account_manager_ids}, 'user_type': 'account_manager'},
            {'$push':
                {'assigned_clients':
                    {
                        "client_id": ObjectId(client.get("_id")),
                        "client_name": client.get("client_name")
                    }
                }
            }
        )

    async def create_client(self, client_information: dict, user: dict) -> dict:
        """
        Create the Client

        Param:
            client_information (dict): Information of the Client
            created_by (str): Created By (Object Id of User)

        Return:
            Return the Client Id and Document Id
        """

        # Checking if the Environment is in Testing
        testing = is_testing_env()

        # Checking Email Uniqueness
        if not (
                await DatabaseConfiguration().client_collection.find_one(
                    {'client_email': client_information.get('client_email')}
                )
        ) is None:
            raise CustomError("Email Already Exists")

        # Checking Email Uniqueness in Client User
        if not (
                await DatabaseConfiguration().user_collection.find_one(
                    {'user_name': client_information.get('client_email')}
                )
        ) is None:
            raise CustomError("Email Already Exists")
        # Checking Fields

        # If User is Account Manager
        if user.get("user_type") == "account_manager":
            client_information['assigned_account_managers'] = [user.get("_id")]

        if not client_information.get('assigned_account_managers'):
            raise CustomError("Please Give Account Managers")

        # Checking Account Managers
        assigned_account_managers_object_ids = await self.to_object_id(keys=['assigned_account_managers'], data={'assigned_account_managers': client_information.get('assigned_account_managers')})
        account_managers = await DatabaseConfiguration().user_collection.aggregate(
            [
                {
                    '$match': {
                        '_id': {'$in': assigned_account_managers_object_ids.get('assigned_account_managers')},
                        'user_type': 'account_manager'
                    }
                }
            ]
        ).to_list(length=None)

        if len(account_managers) != len(client_information.get('assigned_account_managers')):
            raise DataNotFoundError("Account Manager")

        # Address Validation
        address = await Utils_helper().Check_address(
            country_code=client_information.get('address').get('country_code'),
            state_code=client_information.get('address').get('state_code'),
            city_name=client_information.get('address').get('city_name')
        )

        if address is None:
            raise CustomError("Invalid Address")

        client_information['address'].update({
            'address_line_1': client_information.get('address').get('address_line_1'),
            'address_line_2': client_information.get('address').get('address_line_2'),
            'city_name': address.get('name'),
            'state_name': address.get('state_name'),
            'state_code': address.get('state_code'),
            'country_name': address.get('country_name'),
            'country_code': address.get('country_code')
        })

        # Addition of Additional Fields
        additional_data = SystemFields(**{'created_by': user.get('_id')}).model_dump()
        additional_data.update({"statusInfo": StatusInfo(**{}).model_dump()})
        client_information.update(additional_data)

        # Converting String to ObjectIds
        client_information = await self.to_object_id(
            ['assigned_account_managers', 'created_by'],
            client_information
        )

        # Insert Data in the Database
        inserted_response = await DatabaseConfiguration().client_collection.insert_one(client_information)
        client_information['_id'] = ObjectId(inserted_response.inserted_id)
        await DatabaseConfiguration().onboarding_details.insert_one({
            "client_id": client_information.get("_id"),
            "type": "client",
            "status": "In Progress",
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow(),
            "steps": {
                "create_client": {
                    "updated_at": datetime.utcnow(),
                    "status": "Done",
                    "requested_by": {
                        "_id": user.get("_id"),
                        "name": utility_obj.name_can(user)
                    },
                    "request_of": "create_client"
                }
            }
        })
        # Allocating Client to Account Managers
        await self.allocate_client_to_account_managers(
            client=client_information,
            account_manager_ids=client_information.get('assigned_account_managers')
        )

        # Creating Client User and Sending Email with Credentials
        await self.create_client_user_and_send_email(client_information, testing)

        return {
            "mesage": "Client Created Successfully",
            "client_id": str(inserted_response.inserted_id),
        }

    async def add_client_configuration(self, client_id, client_configuration, user):
        """
        Add the Client Configuration

        Param:
            client_id (str): Client Id
            client_configuration (dict): Client Configuration
            user (dict): Details of requested user

        Return:
            data (dict): Client Configuration
        """
        # Checking the Client
        await self.get_client_by_id(client_id)

        client_configuration["updated_at"] = datetime.now()
        client_configuration["is_configured"] = True

        # Adding Client Configuration in the Client Object
        await DatabaseConfiguration().client_collection.update_one(
            {'_id': ObjectId(client_id)},
            {'$set': client_configuration}
        )
        await DatabaseConfiguration().onboarding_details.update_one(
            {"client_id": ObjectId(client_id), "type": "client"},
            {
                "$set":
                {
                    "steps.client_configurations": {
                        "updated_at": datetime.utcnow(),
                        "status": "Done",
                        "requested_by": {
                            "_id": user.get("_id"),
                            "name": utility_obj.name_can(user)
                        },
                        "request_of": "client_configurations"
                    },
                    "status": "Approved"
                }
            }
        )

        return {
            "message": "Client Configuration Added Successfully"
        }

    async def get_client_configuration(self, client_id):
        """
        Get the Client Configuration

        Param:
            client_id (str): Client Id

        Return:
            data (dict): Client Configuration
        """
        # Checking the Client
        client = await self.get_client_by_id(client_id=client_id, extra_query={
            "s3": 1,
            "collpoll": 1,
            "sms": 1,
            "meilisearch": 1,
            "aws_textract": 1,
            "whatsapp_credential": 1,
            "rabbit_mq_credential": 1,
            "zoom_credentials": 1
        })

        client = json.loads(json.dumps(client, default=str))
        return client

    async def get_client(self, client_id, user):
        """
        Get the Client Information

        Param:
            client_id (str): Client Id

        Return:
            data (dict): Client Information
        """
        # Checking the Client
        client = await self.get_client_by_id(client_id, user=user, need_full=True)
        client = json.loads(json.dumps(client, default=str))
        return client

    async def client_list(self, user):
        """
        Get the Client List, depending upon the user

        Param:
            user (dict): User Object

        Return:
            data (list): List of Clients
        """
        pipeline = []

        # Checking if the User is Account Manager
        if user.get("user_type") == "account_manager":
            pipeline.append({"$match": {"assigned_account_managers": {"$in": [ObjectId(user.get("_id"))]}}})
        elif user.get("user_type") == "super_account_manager":
            account_managers = user.get("assigned_account_managers") or []
            account_managers = [ObjectId(account_manager.get("account_manager_id")) for account_manager in account_managers]
            pipeline.append({"$match": {"assigned_account_managers": {"$in": account_managers}}})

        pipeline.extend([
            {
                "$sort": {
                    "created_at": -1
                }
            },
            {
                "$lookup": {
                    "from": "onboarding_details",
                    "localField": "_id",
                    "foreignField": "client_id",
                    "as": "onboarding_details"
                }
            },
            {
                "$unwind": {
                    "path": "$onboarding_details",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {"$project": {
                "client_name": 1,
                "client_email": 1,
                "client_phone": 1,
                "client_id": 1,
                "assigned_account_managers": 1,
                "address": 1,
                "websiteUrl": 1,
                "POCs": 1,
                "created_at": 1,
                "updated_at": 1,
                "created_by": 1,
                "statusInfo": 1,
                "college_ids": 1,
                "onboarding_status": {"$ifNull": ["$onboarding_details.status", ""]}
            }},
        ])

        # Getting All the Clients
        clients = await DatabaseConfiguration().client_collection.aggregate(pipeline).to_list(length=None)
        clients = json.loads(json.dumps(clients, default=str))
        return clients

    async def get_all_clients(self, user, route=None, page=None, limit=None):
        """
        Get All the Clients

        Param:
            page (int): Page Number
            limit (int): Limit

        Return:
            data (list): List of Clients
        """

        # Getting All the Clients
        clients = await self.client_list(user)

        if clients:
            # Pagination
            if page and limit:
                clients = await utility_obj.pagination_in_api(
                    page_num=page,
                    page_size=limit,
                    data=clients,
                    data_length=len(clients),
                    route_name=route
                )
                clients.update({"message": "Client Data List Found"})
                return clients

            #Returning the Clients
            return {
                "data": clients,
                "message": "Client Data List Found"
            }
        # Returning the Error
        return JSONResponse(
            status_code=404,
            content={
                "data": clients,
                "message": "No Client Data Found"
            }
        )

    async def update_client(self, client_id, client_information):
        """
        Update the Client

        Param:
            client_id (str): Client Id
            client_information (dict): Client Information
            updated_by (str): Updated By (Object Id of User)

        Return:
            dict: {"message": "Client Updated Successfully"}
        """

        # Checking Object Id
        await utility_obj.is_id_length_valid(_id=client_id, name="Client Id")

        # Checking the Client
        client = await self.get_client_by_id(client_id)

        # If Client EMail is Included and Not Same as the Existing Email
        if client_information.get('client_email') and not client_information.get('client_email') == client.get('client_email'):
                # Checking Email Uniqueness
                if not (
                        await DatabaseConfiguration().client_collection.find_one(
                            {'client_email': client_information.get('client_email'), '_id': {'$ne': ObjectId(client_id)}}
                        )
                ) is None:
                    raise CustomError("Email Already Exists")

                # Checking Email Uniqueness in Client User
                if not (
                        await DatabaseConfiguration().user_collection.find_one(
                            {'user_name': client_information.get('client_email'), 'associated_client': {'$ne': ObjectId(client_id)}}
                        )
                ) is None:
                    raise CustomError("Email Already Exists")

        # Checking Fields if the Fields Exists
        # TODO IMPLEMENTATION OF REDIS FOR CHECKING THE FIELDS

        # Checking if the Fields Exists
        object_id_fields = ['assigned_account_managers', 'student_dashboard_form', 'student_dashboard_screen', 'admin_dashboard_screen', 'created_by']
        if (
                fields := list(set(client_information.keys()) & set(object_id_fields))
        ):
            # Converting String to ObjectIds
            client_information = await self.to_object_id(fields, client_information)

        if client_information.get('address'):
            # Checking if the Country, State and City is Same
            if not (
                client_information.get('address').get('country_code') == client.get('address').get('country_code') and
                client_information.get('address').get('state_code') == client.get('address').get('state_code') and
                client_information.get('address').get('city_name') == client.get('address').get('city_name')
            ):
                # Address Validation
                address = await Utils_helper().Check_address(
                    country_code=client_information.get('address').get('country_code'),
                    state_code=client_information.get('address').get('state_code'),
                    city_name=client_information.get('address').get('city_name')
                )

                if address is None:
                    raise CustomError("Invalid Address")

                client_information['address'].update({
                    'address_line_1': client_information.get('address').get('address_line_1'),
                    'address_line_2': client_information.get('address').get('address_line_2'),
                    'city_name': address.get('name'),
                    'state_name': address.get('state_name'),
                    'state_code': address.get('state_code'),
                    'country_name': address.get('country_name'),
                    'country_code': address.get('country_code')
                })
            else:
                client_information['address'] = client.get('address')
                client_information['address'].update({
                    'address_line_1': client_information.get('address').get('address_line_1'),
                    'address_line_2': client_information.get('address').get('address_line_2'),
                })

        # Adding POCs if they exists in request Body
        if client_information.get("POCs"):
            previous_poc = client.get("POCs")
            new_poc = client_information.get("POCs")
            client_information["POCs"] = previous_poc + new_poc

        # Addition of Additional Fields
        client_information.update({
            'updated_at': datetime.now()
        })

        # Updating the Client
        await DatabaseConfiguration().client_collection.update_one(
            {'_id': ObjectId(client_id)},
            {'$set': client_information}
        )

        return {
            "message": "Client Updated Successfully"
        }

    async def delete_client(self, client_id):
        """
        Delete the Client. This Permission will be only given to the Admin

        Param:
            client_id (str): Client Id

        Return:
            data (dict): Deleted Client Information
        """
        # Checking the Client
        client = await self.get_client_by_id(client_id)

        # Deleting the Client
        await DatabaseConfiguration().client_collection.delete_one(
            {'_id': ObjectId(client_id)}
        )

        # Deleting Associated Users
        await DatabaseConfiguration().user_collection.delete_many(
            {'associated_client': ObjectId(client_id)}
        )

        # TODO Delete Associated Colleges & their Users if Needed
        # TODO Deletes Associated Stages, Sub Stages if Needed

        client.pop('client_configuration', None)
        return json.loads(json.dumps(client, default=str))