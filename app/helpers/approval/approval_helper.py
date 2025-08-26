"""This File Contains Helper Functions for Approval CURD Operations"""

# Todo: Recheck Again when all Users are created even Higher Hierarchies & All Other Components are Ready which needs approval
import json
from datetime import datetime
from typing import Union

from bson import ObjectId

from app.core.custom_error import DataNotFoundError, CustomError
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import is_testing_env
from app.helpers.client_curd.client_curd_helper import ClientCurdHelper
from app.helpers.college_configuration import CollegeHelper
from app.models.approval_schema import SystemFields


class ApprovalCRUDHelper:

    async def get_approval_request(self, approval_id: str, user: dict = None) -> dict:
        """
        Get the approval request

        Param:
            approval_id (str): Get the approval id

        Return:
            dict: Return the approval request having information about approval request

        Raises:
            CustomError: If the approval Id is not valid
            DataNotFoundError: If the approval request is not found
        """
        # Is Object Id Valid
        if not ObjectId.is_valid(approval_id):
            raise CustomError("Invalid Approval Request Id")

        if user and not user.get("role", {}).get("role_name") == "super_admin":
            search_in = [
                {"submitted_by": ObjectId(user.get("_id"))},
                {"current_approvers": {"$in": [ObjectId(user.get("_id"))]}},
            ]
            if user.get("associated_client") or user.get("associated_colleges"):
                org_info = await self.get_user_organization(user)
                org_type = org_info.get("org_type")
                org_id = org_info.get("org_id")
                search_in.append({org_type: ObjectId(org_id)})

            # Get the approval request
            approval_request = (
                await DatabaseConfiguration().approvals_collection.find_one(
                    {"_id": ObjectId(approval_id), "$or": search_in}
                )
            )

            if not approval_request:
                raise DataNotFoundError("Approval Request")

            return approval_request

        approval_request = await DatabaseConfiguration().approvals_collection.find_one(
            {"_id": ObjectId(approval_id)}
        )

        if not approval_request:
            raise DataNotFoundError("Approval Request")

        return approval_request

    async def check_repeated_approval(
        self, org_type: str, org_id: str, approval_type: str, approval_data: dict = None
    ) -> None:
        """
        Check if the approval request is already present

        Param:
            org_type (str): Get the type of the approval workflow
            org_id (ObjectId): Get the id of the client or college
            approval_type (str): Get the type of the approval request

        Return:
            None

        Raises:
            CustomError: If the approval request is already present
            CustomError: If the Organisation Id is not valid
        """
        # Check Object Id Valid
        if not ObjectId.is_valid(org_id):
            raise CustomError("Invalid Organisation Id")

        if (
            pending_approvals := await DatabaseConfiguration()
            .approvals_collection.find(
                {
                    org_type: ObjectId(org_id),
                    "approval_type": approval_type,
                    "status": {"$in": ["pending", "partially_approved"]},
                }
            )
            .to_list(length=None)
        ):
            # Checking Requested Approval Data Present, if present then check if college or client is same in for approval requested data
            if approval_data:
                if approval_data.get("client_id"):
                    all_approval_requested_data = (
                        await DatabaseConfiguration()
                        .approval_request_data_collection.find(
                            {
                                "_id": {
                                    "$in": [
                                        ObjectId(x.get("approval_request_data_id"))
                                        for x in pending_approvals
                                    ]
                                },
                                "client_id": ObjectId(approval_data.get("client_id")),
                            }
                        )
                        .to_list(length=None)
                    )
                elif approval_data.get("college_id"):
                    all_approval_requested_data = (
                        await DatabaseConfiguration()
                        .approval_request_data_collection.find(
                            {
                                "_id": {
                                    "$in": [
                                        ObjectId(x.get("approval_request_data_id"))
                                        for x in pending_approvals
                                    ]
                                },
                                "college_id": ObjectId(approval_data.get("college_id")),
                            }
                        )
                        .to_list(length=None)
                    )
                else:
                    all_approval_requested_data = None
                if not all_approval_requested_data:
                    return
            raise CustomError("Approval Request Already Present")

    async def get_approval_workflow(
        self, org_type: str, org_id: str, approval_type: str
    ) -> dict:
        """
        Get the approval workflow

        Param:
            org_type (str): Get the type of the approval workflow
            org_id (ObjectId): Get the id of the client or college
            approval_type (str): Get the type of the approval request

        Raises:
            CustomError: If the Organisation Id is not valid
            DataNotFoundError: If the approval workflow is not found

        Return:
            dict: Return the approval workflow details
        """

        # Check Object Id Valid
        if not ObjectId.is_valid(org_id):
            raise CustomError("Invalid Organisation Id")

        if org_type in ["client_id", "college_id"]:
            if org_type == "client_id":
                client_id = ObjectId(org_id)
            else:
                college = await DatabaseConfiguration().college_collection.find_one(
                    {"_id": ObjectId(org_id)}
                )
                client_id = college.get("associated_client_id")
            pipeline = [
                # 1) Match the specific client configuration
                {"$match": {"_id": client_id}},
                # 2) Lookup all Admin user `_id`s into a temp field "admins"
                {
                    "$lookup": {
                        "from": "users",
                        "pipeline": [
                            {"$match": {"role.role_name": "admin"}},
                            {"$project": {"_id": 1}},
                        ],
                        "as": "admins",
                    }
                },
                # 3) Project the structure
                {
                    "$project": {
                        "_id": 0,
                        "levels": [
                            {
                                "level": 1,
                                # assigned_account_managers is already [ObjectId, …]
                                "approvers": "$assigned_account_managers",
                                "requiredApprovals": 1,
                            },
                            {
                                "level": 2,
                                # get the `_id` field out of each admin document
                                "approvers": {
                                    "$map": {
                                        "input": "$admins",
                                        "as": "adm",
                                        "in": "$$adm._id",
                                    }
                                },
                                "requiredApprovals": 1,
                            },
                        ],
                    }
                },
            ]
        else:
            pipeline = [
                # 1) Lookup all Admin user `_id`s
                {
                    "$lookup": {
                        "from": "users",
                        "pipeline": [
                            {"$match": {"role.role_name": "admin"}},
                            {"$project": {"_id": 1}},
                        ],
                        "as": "admins",
                    }
                },
                # 2) Project the structure with a single level
                {
                    "$project": {
                        "_id": 0,
                        "levels": [
                            {
                                "level": 1,
                                "approvers": {
                                    "$map": {
                                        "input": "$admins",
                                        "as": "adm",
                                        "in": "$$adm._id",
                                    }
                                },
                                "requiredApprovals": 1,
                            }
                        ],
                    }
                },
            ]
        result = (
            await DatabaseConfiguration()
            .client_collection.aggregate(pipeline)
            .to_list(length=1)
        )
        if result:
            return result[0]

        # Get the approval workflow
        if not (
            approval_workflow := await DatabaseConfiguration().approval_workflow_collection.find_one(
                {org_type: ObjectId(org_id), "approval_type": approval_type}
            )
        ):
            raise DataNotFoundError("Approval Workflow")

        return approval_workflow

    async def get_user_organization(
        self, user: dict = {}, requested_data: dict = None
    ) -> dict:
        """
        Get the user organization

        Param:
            user_id (str): Get the user id

        Raises:
            CustomError: If the user is not associated with any client or college
            CustomError: If the user is not associated with any college
            CustomError: If the user is not associated with any client

        Return:
            dict: Return the user organization
                - org_type (str): Get the type of the approval workflow
                - org_id (ObjectId): Get the id of the client or college
                - org_name (str): Get the name of the client or college
                - org_info (dict): Get the details of the client or college
        """
        if is_testing_env():
            college = await DatabaseConfiguration().college_collection.find_one()
            user["associated_colleges"] = [college.get("_id")]
        if user.get("associated_colleges"):
            org_type = "college_id"
            if requested_data and requested_data.get("college_id"):
                org_id = requested_data.get("college_id")
            else:
                if len(user.get("associated_colleges")) < 1:
                    raise CustomError("User not associated with any college")
                org_id = user.get("associated_colleges")[0]
            org_info = await DatabaseConfiguration().college_collection.find_one(
                {"_id": ObjectId(org_id)}
            )
            if not org_info:
                raise CustomError("User not associated with any college")
            org_name = org_info.get("name")
        elif user.get("associated_client"):
            org_type = "client_id"
            org_id = user.get("associated_client")
            org_info = await DatabaseConfiguration().client_collection.find_one(
                {"_id": ObjectId(org_id)}
            )
            if not org_info:
                raise CustomError("User not associated with any client")
            org_name = org_info.get("client_name")
        else:
            # If the Requested Data Already have that for which Client or College is going to be Updated
            if requested_data and (
                requested_data.get("client_id") or requested_data.get("college_id")
            ):
                if requested_data.get("client_id"):
                    org_type = "client_id"
                    org_id = requested_data.get("client_id")
                    org_info = await DatabaseConfiguration().client_collection.find_one(
                        {"_id": ObjectId(org_id)}
                    )
                    if not org_info:
                        raise DataNotFoundError("Client Id")
                    org_name = org_info.get("client_name")
                else:
                    org_type = "college_id"
                    org_id = requested_data.get("college_id")
                    org_info = (
                        await DatabaseConfiguration().college_collection.find_one(
                            {"_id": ObjectId(org_id)}
                        )
                    )
                    if not org_info:
                        raise DataNotFoundError("College Id")
                    org_name = org_info.get("name")

        return {
            "org_type": org_type,
            "org_id": org_id,
            "org_name": org_name,
            "org_info": org_info,
        }

    async def delete_approval_request(self, approval_id: str) -> dict:
        """
        Delete the approval request

        Param:
            approval_id (str): Get the approval id

        Return:
            dict: Return the success message
        """
        approval_request = await self.get_approval_request(approval_id)
        await DatabaseConfiguration().approvals_collection.delete_one({"_id": ObjectId(approval_id)})
        await DatabaseConfiguration().approval_request_data_collection.delete_one({"_id": ObjectId(approval_request.get("approval_request_data_id"))})
        return {"message": "Approval Request Deleted", "deleted_approval_request": approval_request}

    async def create_approval_request(
        self, user: dict, request_data: Union[dict, list], approval_id = None
    ) -> dict:
        """
        Create the approval request

        Param:
            user (dict): Get the user details
            request_data (dict): Get the details which is need to be Approved
            approval_id (str): Approval Id in Case its need to be Updated

        Raises:
            CustomError: If the Organisation Id is not valid
            CustomError: If the approval workflow is not found
            CustomError: If the approval request is already present
            CustomError: If the user is not associated with any client or college
            CustomError: If the user is not associated with any college
            CustomError: If the user is not associated with any client

        Return:
            dict: Return success message
        """

        # Check Approval Type
        approval_types = await self.get_approval_metadata()
        if request_data.get("approval_type") not in approval_types.get(
            "approval_types"
        ):
            raise CustomError(
                f"Invalid Approval Type {request_data.get('approval_type')}"
            )

        # Todo: Check this Logic Again when all the Users are done even Higher Hierarchy
        org_info = {}
        if (
            user.get("associated_colleges")
            or user.get("associated_client")
            or request_data.get("client_id")
            or request_data.get("college_id")
        ):
            org_info = await self.get_user_organization(requested_data=request_data)

        org_type = org_info.get("org_type")
        org_id = org_info.get("org_id")
        org_name = org_info.get("org_name")

        if is_testing_env():
            approval_workflow = {
                "levels": [
                    {
                        "level": 1,
                        "approvers": [ObjectId(user.get("_id"))],
                        "requiredApprovals": 1,
                    },
                    {
                        "level": 2,
                        "approvers": [ObjectId(user.get("_id"))],
                        "requiredApprovals": 1,
                    },
                ],
                "approval_type": "college_course_details",
                org_type: org_id,
            }
            await self.check_repeated_approval(
                org_type, org_id, request_data.get("approval_type"), request_data
            )
        else:

            # Check if the approval request is already present (Currently disabling it, Because Application Forms needs Multiple Requests)
            # await self.check_repeated_approval(org_type, org_id, request_data.get("approval_type"),
            #                                   request_data)

            # Get the approval workflow
            approval_workflow = await self.get_approval_workflow(
                org_type, org_id, request_data.get("approval_type")
            )

        if approval_workflow is None:
            # This Error should never happen as approval workflow will be generated by system
            raise DataNotFoundError("Approval Workflow")

        # Check if the approval workflow level is empty list
        if len(approval_workflow.get("levels")) < 1:
            # This Error should never happen as approval workflow will be generated by system & level will never be empty
            raise CustomError("Approval Workflow Invalid")

        # Create the Internal Fields
        system_data = {
            "submitted_by": ObjectId(user.get("_id")),
            "submitted_by_name": utility_obj.name_can(user),
            "submitted_by_email": user.get("email"),
            "submitted_by_mobile": str(user.get("mobile_number")),
            "submitted_by_org_name": org_name,
            org_type: ObjectId(org_id),
            "current_approvers": approval_workflow.get("levels")[0].get("approvers"),
            "current_level": approval_workflow.get("levels")[0].get("level"),
            "previous_timeline": [],
        }

        if approval_id:
            deleted_approval_request = await self.delete_approval_request(approval_id)
            system_data["_id"] = ObjectId(approval_id)
            prev_status = {
                "status": deleted_approval_request.get("deleted_approval_request").get("status"),
                "remarks": deleted_approval_request.get("deleted_approval_request").get("remarks"),
                "approvals": deleted_approval_request.get("deleted_approval_request").get("approvals"),
                "updated_at": deleted_approval_request.get("deleted_approval_request").get("updated_at"),
            }
            system_data["previous_timeline"].append(prev_status)

        # Passing through Pydantic Model for Validation & Create Some more Fields
        system_fields = SystemFields(**system_data)

        # Storing Requested Data
        requested_data_inserted_response = (
            await DatabaseConfiguration().approval_request_data_collection.insert_one(
                request_data
            )
        )
        request_data.pop("payload", None)
        request_data.pop("client_id", None)
        request_data.pop("college_id", None)

        # Storing Object Id of Requested Data
        request_data["approval_request_data_id"] = (
            requested_data_inserted_response.inserted_id
        )

        # Merge System Fields with Requested Data
        request_data.update(system_fields.model_dump(exclude_none=True, by_alias=True))

        # Inserting the Crated Approval
        approval_inserted_response = (
            await DatabaseConfiguration().approvals_collection.insert_one(request_data)
        )

        return {
            "approval_id": str(approval_inserted_response.inserted_id),
            "message": "Approval Request Created Successfully.",
        }

    async def get_all_approval_requests(
        self,
        user: dict,
        filters: dict,
        page: int = None,
        limit: int = None,
        route: str = None,
    ) -> list:
        """
        Get All Approval Requests by Merging get_approval_requests and get_request_need_approval

        Param:
            user (dict): Get the user details

        Return:
            list: Return the approval requests
        """
        approval_metadata = await self.get_approval_metadata()
        # Validate approval_type
        invalid_types = [
            t
            for t in filters.get("approval_type", [])
            if t not in approval_metadata.get("approval_types", [])
        ]
        if invalid_types:
            raise CustomError(f"Invalid Approval Type(s): {invalid_types}")

        # Validate approval_status
        invalid_statuses = [
            s
            for s in filters.get("approval_status", [])
            if s not in approval_metadata.get("approval_status", [])
        ]
        if invalid_statuses:
            raise CustomError(f"Invalid Approval Status(es): {invalid_statuses}")

        # Validating client_ids & Converting to ObjectId
        if filters.get("client_ids"):
            filters["client_ids"] = [
                ObjectId(client_id) for client_id in filters.get("client_ids") if ObjectId.is_valid(client_id)
            ]

        # Validating college_ids & Converting to ObjectId
        if filters.get("college_ids"):
            filters["college_ids"] = [
                ObjectId(college_id) for college_id in filters.get("college_ids") if ObjectId.is_valid(college_id)
            ]

        # Get the approval requests
        approval_requests = await self.get_approval_requests(
            user, filters.get("approval_type"), filters.get("approval_status"), filters.get("client_ids"), filters.get("college_ids")
        )

        # Frontend needs to know if the user can approve or reject
        for approval_request in approval_requests:
            approval_request["can_approve_or_reject"] = False

        # Get the approval requests need approval
        approval_request_need_approval = await self.get_request_need_approval(
            user, filters.get("approval_type"), filters.get("approval_status"), filters.get("client_ids"), filters.get("college_ids")
        )

        # Frontend needs to know if the user can approve or reject
        for approval_request in approval_request_need_approval:
            approval_request["can_approve_or_reject"] = True

        # Sorting by the `created_at`
        all_approval_requests = approval_requests + approval_request_need_approval
        all_approval_requests.sort(key=lambda x: x["created_at"], reverse=True)

        if page and limit:
            all_approval_requests = await utility_obj.pagination_in_api(
                data=all_approval_requests,
                data_length=len(all_approval_requests),
                page_num=page,
                page_size=limit,
                route_name=route,
            )
            return json.loads(json.dumps(all_approval_requests, default=str))

        # Merge the approval requests and approval requests need approval
        return all_approval_requests


    async def return_sorted_order(self, approval_data:list):
        """
            Extracts and flattens the 'documents' from a list of approval data objects,
            removing specified keys from each document.
            Params:
                approval_data (List[Dict[str, Any]]): A list of approval data items,
                    each containing a 'documents' field which is a list of document dictionaries.
            Returns:
                List[Dict[str, Any]]: A flattened list of cleaned document dictionaries
                    with unwanted keys removed.
        """
        result=[]
        for data in approval_data:
            doc = data.get("documents",[])
            for i in doc:
                keys_to_remove = ["result", "group_key","group_type","approval_sort_order"]
                for key in keys_to_remove:
                    i.pop(key, None)
                result.append(i)
        return result


    async def get_approval_requests(
        self, user: dict, filter_approval_type: list = [], filter_status: list = [], filter_client_ids: str = [], filter_college_ids: str = []
    ) -> list:
        """
        Get the approval requests

        Param:
            user (dict): Get the user details
            filter_approval_type (list): Filter the approval requests by approval type
            filter_status (list): Filter the approval requests by status

        Raises:
            CustomError: If the user is not associated with any client or college
            CustomError: If the user is not associated with any college
            CustomError: If the user is not associated with any client

        Return:
            list: Return the approval requests
        """

        # Get the User Organization
        search_in = [{"submitted_by": ObjectId(user.get("_id"))}]

        if user.get("associated_client") or user.get("associated_colleges"):
            org_info = await self.get_user_organization(user)
            org_type = org_info.get("org_type")
            org_id = org_info.get("org_id")
            search_in.append({org_type: ObjectId(org_id)})

        pipeline = [{"$match": {"$or": search_in}}]
        if filter_approval_type:
            pipeline.append(
                {"$match": {"approval_type": {"$in": filter_approval_type}}}
            )

        if filter_status:
            pipeline.append({"$match": {"status": {"$in": filter_status}}})

        union_filter = []
        if filter_client_ids:
            union_filter.append({"client_id": {"$in": filter_client_ids}})

        if filter_college_ids:
            union_filter.append({"college_id": { "$in": filter_college_ids}})

        if union_filter:
            pipeline.append({"$match": {"$or": union_filter}})

        pipeline.extend([
                {
                    '$lookup': {
                        'from': 'approval_requested_data',
                        'localField': 'approval_request_data_id',
                        'foreignField': '_id',
                        'as': 'result'
                    }
                }, {
                    '$unwind': '$result'
                }, {
                    '$addFields': {
                        'group_key': {
                            '$cond': [
                                {
                                    '$ifNull': [
                                        '$result.college_id', False
                                    ]
                                }, '$result.college_id', '$result.client_id'
                            ]
                        },
                        'group_type': {
                            '$cond': [
                                {
                                    '$ifNull': [
                                        '$result.college_id', False
                                    ]
                                }, 'college', 'client'
                            ]
                        }
                    }
                }, {
                    '$addFields': {
                        'approval_sort_order': {
                            '$cond': [
                                {
                                    '$eq': [
                                        '$group_type', 'college'
                                    ]
                                }, {
                                    '$indexOfArray': [
                                        [
                                            'college_course_details',
                                            'college_student_registration_form',
                                            'college_student_application_form',
                                            'college_additional_details',
                                            'college_color_theme',
                                            'college_subscription_details'
                                        ], '$approval_type'
                                    ]
                                }, {
                                    '$indexOfArray': [
                                        [
                                            'client_student_registration_form',
                                            'client_student_application_form',
                                            'client_subscription_details'
                                        ], '$approval_type'
                                    ]
                                }
                            ]
                        }
                    }
                }, {
                    '$sort': {
                        'approval_sort_order': 1
                    }
                }, {
                    '$group': {
                        '_id': {
                            'type': '$group_type',
                            'id': '$group_key'
                        },
                        'documents': {
                            '$push': '$$ROOT'
                        }
                    }
                }, {
                    '$project': {
                        'documents': 1,
                        '_id': {
                            'type': '$_id.type',
                            'id': '$_id.group_id',
                            'created_at': {
                                '$arrayElemAt': [
                                    '$documents.created_at', 0
                                ]
                            }
                        }
                    }
                }, {
                    '$sort': {
                        '_id.created_at': -1
                    }
                }
            ]
        )
        approval_requests = await DatabaseConfiguration().approvals_collection.aggregate(pipeline).to_list(None)
        approval_requests = await self.return_sorted_order(approval_requests)
        return json.loads(json.dumps(approval_requests, default=str))


    async def get_request_need_approval(
        self, user: dict, filter_approval_type: list = [], filter_status: list = [], filter_client_ids: str = [], filter_college_ids: str = []
    ) -> list:
        """
        Get the approvals need Approval

        Param:
            user (dict): Get the user details

        Return:
            list: Return the approvals need Approval
        """
        pipeline = [
            {
                "$match": {
                    "status": {"$in": ["pending", "partially_approved"]},
                    "current_approvers": {"$in": [ObjectId(user.get("_id"))]},
                }
            },
        ]

        if user.get("role", {}).get("role_name") == "super_admin":
            pipeline = []

        if filter_approval_type:
            pipeline.append(
                {"$match": {"approval_type": {"$in": filter_approval_type}}}
            )

        if filter_status:
            pipeline.append({"$match": {"status": {"$in": filter_status}}})

        union_filter = []
        if filter_client_ids:
            union_filter.append({"client_id": {"$in": filter_client_ids}})

        if filter_college_ids:
            union_filter.append({"college_id": { "$in": filter_college_ids}})

        if union_filter:
            pipeline.append({"$match": {"$or": union_filter}})

        pipeline.append({"$sort": {"created_at": -1}})

        # Get the approvals need to be approved
        approvals_need_to_be_approved = (
            await DatabaseConfiguration()
            .approvals_collection.aggregate(pipeline)
            .to_list(None)
        )

        return json.loads(json.dumps(approvals_need_to_be_approved, default=str))

    async def get_approval_requested_data(self, user: dict, approval_id: str) -> dict:
        """
        Get the approval requested data

        Param:
            user (dict): Get the user details
            approval_id (str): Get the approval id

        Return:
            - dict / list: Return the approval requested data
        """
        if not ObjectId.is_valid(approval_id):
            raise CustomError(message="Invalid approval id")
        # BELOW WE ARE FOLLOWING STRICT VALIDATIONS CHECK BASED ON USER AND DEPENDENT ON THAT APPROVALS WILL BE SHOWN
        # IF WE WANT TO SHOW ALL APPROVALS THEN REMOVE BELOW VALIDATIONS
        # Colleges & Clients User have Access to
        users_colleges = await CollegeHelper().college_list(user=user)
        users_clients = await ClientCurdHelper().get_all_clients(user=user)

        # Extracting Ids
        college_ids =  [ObjectId(college.get("id")) for college in users_colleges.get("data") if type(college) == dict and college.get("id")]
        client_ids = [ObjectId(client.get("_id")) for client in users_clients.get("data") if type(client) == dict and client.get("_id")]

        # Get the approval request
        approval_request = await DatabaseConfiguration().approvals_collection.find_one(
            {
                "_id": ObjectId(approval_id),
                "$or": [
                    {"client_id": {"$in": client_ids}},
                    {"college_id": {"$in": college_ids}},
                    {"submitted_by": ObjectId(user.get("_id"))},
                    {"current_approvers": {"$in": [ObjectId(user.get("_id"))]}},
                ],
            }
        )

        if not approval_request:
            raise DataNotFoundError("Approval Request")

        # Retrieve the approval request data
        approval_request_data = (
            await DatabaseConfiguration().approval_request_data_collection.find_one(
                {"_id": ObjectId(approval_request.get("approval_request_data_id"))}
            )
        )

        # This Error should never happen
        if not approval_request_data:
            raise DataNotFoundError("Approval Request Data")

        approval_request_data["approval_request"] = approval_request

        return json.loads(json.dumps(approval_request_data, default=str))

    async def approve_reject_approval(
        self, user: dict, approval_id: str, action: str, messages: dict
    ) -> dict:
        """
        Approve or Reject the approval request

        Param:
            user (dict): Get the user details
            approval_id (str): Get the approval id
            action (Literal["approve", "reject"]): Get the action
            messages (dict): Inside it there's a Remark key

        Raises:
            CustomError: If the user is not associated with any client or college
            CustomError: If the user is not associated with any college
            CustomError: If the user is not associated with any client
            CustomError: If the approval request is already approved or rejected
            CustomError: If the user is not an approver

        Return:
            Return success message
        """
        # Get the approval request
        approval_request = await self.get_approval_request(approval_id, user)

        # Check if the approval request is already approved or rejected
        if not approval_request.get("status") in ["pending", "partially_approved"]:
            raise CustomError("Approval Request Already Approved or Rejected")

        if is_testing_env():
            approval_workflow = {
                "levels": [
                    {
                        "level": 1,
                        "approvers": [ObjectId(user.get("_id"))],
                        "requiredApprovals": 1,
                    },
                    {
                        "level": 2,
                        "approvers": [ObjectId(user.get("_id"))],
                        "requiredApprovals": 1,
                    },
                ],
                "approval_type": "college_onboarding",
                "college_id": id,
            }
        else:
            # Get the approval workflow
            approval_workflow = await self.get_approval_workflow(
                "college_id" if approval_request.get("college_id") else "client_id",
                approval_request.get("college_id") or approval_request.get("client_id"),
                approval_request.get("approval_type"),
            )

        # Get the approver level
        approver_level = approval_request.get("current_level")

        # Check if the action is reject
        if action == "reject":
            # Update the status, remarks and updated_at
            await DatabaseConfiguration().approvals_collection.update_one(
                {"_id": ObjectId(approval_id)},
                {
                    "$set": {
                        "status": "rejected",
                        "remarks": messages.get("remarks"),
                        "updated_at": datetime.now(),
                    }
                },
            )
            college_id, client_id = approval_request.get("college_id"), approval_request.get("client_id")
            filter = {"college_id": college_id, "type": "college"} if college_id else \
                {"client_id": client_id, "type": "client"}
            onboarding_details = await DatabaseConfiguration().onboarding_details.find_one(filter)
            steps = onboarding_details.get("steps", {})
            matched_key = next(
                (key for key, step in steps.items()
                 if str(step.get("requested_id")) == str(approval_id)),
                None
            )
            if matched_key:
                await DatabaseConfiguration().onboarding_details.update_one(
                    filter,
                    {
                        "$set": {
                            f"steps.{matched_key}.status": "Rejected",
                            f"steps.{matched_key}.updated_at": datetime.utcnow(),
                            f"steps.{matched_key}.reason_to_reject": messages.get("remarks", ""),
                            "status": "In Progress",
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            return {"message": "Approval Request Rejected Successfully."}

        done_approvals = approval_request.get("approvals")
        done_approvals.append(
            {
                "approverId": ObjectId(user.get("_id")),
                "level": approver_level,
                "status": "approved",
                "comments": messages.get("remarks"),
                "approvedAt": datetime.now(),
            }
        )

        # Get the approver details
        if len(approval_workflow.get("levels")) > approver_level:
            new_approver_details = approval_workflow.get("levels")[approver_level].get(
                "approvers"
            )

            # Update the current approvers and current level
            await DatabaseConfiguration().approvals_collection.update_one(
                {"_id": ObjectId(approval_id)},
                {
                    "$set": {
                        "status": "partially_approved",
                        "current_approvers": new_approver_details,
                        "current_level": approver_level + 1,
                        "approvals": done_approvals,
                    }
                },
            )
            return {"message": "Approved Successfully & Moved to Next Level"}
        else:
            # Initiating Data Migration
            await ApprovedRequestHandler().master_approved_request_handler(approval_id)

            # Update the status, remarks and updated_at
            await DatabaseConfiguration().approvals_collection.update_one(
                {"_id": ObjectId(approval_id)},
                {
                    "$set": {
                        "status": "approved",
                        "remarks": messages.get("remarks"),
                        "updated_at": datetime.now(),
                        "approvals": done_approvals,
                    }
                },
            )

            return {"message": "Approval Request Approved Successfully."}

    async def delete_request_sent(self, user: dict, approval_request_id: str) -> dict:
        """
        Delete the Approval Request which was Sent but in Pending State

        Param:
            user (dict): Get the user details
            approval_request_id (str): Get the approval request id

        Raises:
            CustomError: If the approval request is not found
            CustomError: If the approval request is already approved or rejected
            CustomError: Approval Request Not Belongs to the Organisation
            CustomError: User not associated with any client or college
            CustomError: User not associated with any college
            CustomError: User not associated with any client

        Return:
            dict: Return success message
                - message (str): Get the success message
        """
        # Get the approval request
        approval_request = await self.get_approval_request(approval_request_id, user)

        # Check if the approval request is already approved or rejected
        if approval_request.get("status") != "pending":
            raise CustomError(
                "Approval Request Already Approved, Rejected or Partially Approved"
            )

        # Delete the approval request
        await DatabaseConfiguration().approvals_collection.delete_one(
            {"_id": ObjectId(approval_request_id)}
        )
        await DatabaseConfiguration().approval_request_data_collection.delete_one(
            {
                "approval_request_id": ObjectId(
                    approval_request.get("approval_request_data_id")
                )
            }
        )

        return {"message": "Approval Request Deleted Successfully."}

    async def update_request(
        self, user: dict, approval_request_id: str, request_data: Union[dict, list]
    ) -> dict:
        """
        Update the Approval Request which was Sent but in Pending State

        Param:
            user (dict): Get the user details
            approval_request_id (str): Get the approval request id

        Raises:
            CustomError: If the approval request is not found
            CustomError: If the approval request is already approved or rejected
            CustomError: Approval Request Not Belongs to the Organisation
            CustomError: User not associated with any client or college
            CustomError: User not associated with any college
            CustomError: User not associated with any client

        Return:
            dict: Return success message
                - message (str): Get the success message
        """
        # Get the approval request
        approval_request = await self.get_approval_request(approval_request_id, user)

        # Check if the approval request is already approved or rejected
        if approval_request.get("status") != "pending":
            raise CustomError("Approval Request Already Approved or Rejected")

        # Update the approval request data
        await DatabaseConfiguration().approval_request_data_collection.update_one(
            {"_id": ObjectId(approval_request.get("approval_request_data_id"))},
            {"$set": {"payload": request_data}},
        )

        return {"message": "Approval Request Updated Successfully."}

    async def get_approval_metadata(self):
        """
        Show Approval Types and Approval Status defined in the System
        """
        # Get the Metadata
        metadata = (
            await DatabaseConfiguration().approval_request_data_collection.find_one(
                {"type": "approval_metadata"}, {"_id": 0}
            )
        )

        # If the metadata is not found, then Create Default Metadata
        if not metadata:
            metadata = {
                "type": "approval_metadata",
                "approval_status": [
                    "pending",
                    "partially_approved",
                    "approved",
                    "rejected",
                ],
                "approval_types": [
                    "college_course_details",
                    "college_student_registration_form",
                    "client_student_registration_form",
                    "college_student_application_form",
                    "client_student_application_form",
                    "college_additional_details",
                    "college_subscription_details",
                    "client_subscription_details",
                    "college_color_theme",
                ],
            }
            await DatabaseConfiguration().approval_request_data_collection.insert_one(
                metadata
            )

        return metadata


class ApprovedRequestHandler:
    async def master_approved_request_handler(self, approval_id: str) -> None:
        """
        It Handles the Data Which has been Approved

        Param:
            approval_id (str): Get the approval id
        """
        approval_request = await ApprovalCRUDHelper().get_approval_request(approval_id)
        approval_request_data = (
            await DatabaseConfiguration().approval_request_data_collection.find_one(
                {"_id": approval_request.get("approval_request_data_id")}
            )
        )

        # Before Approving Finally Check Whether the College or the Client has Been Configured and Are we Able to Create Connections
        if approval_request_data.get("college_id"):
            if not (college := await DatabaseConfiguration().college_collection.find_one(
                {"_id": approval_request_data.get("college_id")}
            )):
                raise DataNotFoundError("College")
            if not college.get("is_configured"):
                raise CustomError("Request Cannot be Approved Until the College has Been Configured by Super Admin")

            # Trying to Create Connection
            try:
                Reset_the_settings().get_user_database(college.get("_id"))
            except Exception as e:
                raise CustomError(message="Unable to Establish Connection with Season Db: " + str(e))
        elif approval_request_data.get("client_id"):
            if not (client := await DatabaseConfiguration().client_collection.find_one(
                {"_id": approval_request_data.get("client_id")}
            )):
                raise DataNotFoundError("Client")
            if not client.get("is_configured"):
                raise CustomError("Request Cannot be Approved Until the Client has Been Configured by Super Admin")

        # Checking Approval Request Type
        approval_type = approval_request_data.get("approval_type")
        if approval_type == "college_course_details":
            await self.save_course_details(approval_request_data)
        elif approval_type == "college_additional_details":
            await self.save_college_additional_details(approval_request_data)
        elif approval_type in [
            "college_subscription_details",
            "client_subscription_details",
        ]:
            await self.save_college_subscription_details(approval_request_data)
        elif approval_type in [
            "college_student_registration_form",
            "client_student_registration_form",
        ]:
            await self.save_registration_form(approval_request_data)
        elif approval_type in [
            "client_student_application_form",
            "college_student_application_form",
        ]:
            await self.save_application_form(approval_request_data)
        elif approval_type == "college_color_theme":
            await self.save_color_theme(approval_request_data)

    async def save_course_details(self, request_data: dict) -> None:
        """
        Save the college onboarding course details

        Param:
            request_data (dict): Get the details which is need to be Approved
        """
        from app.helpers.client_automation.client_automation_helper import (
            college_details,
        )

        college = await DatabaseConfiguration().college_collection.find_one(
            {"_id": ObjectId(request_data.get("college_id"))}
        )
        await college_details().add_college_course(
            payload=request_data.get("payload"),
            college=college,
            user=request_data.get("user"),
        )

    async def save_college_additional_details(self, request_data: dict) -> None:
        """
        Save the college onboarding extra details

        Param:
            request_data (dict): Get the details which is need to be Approved
        """
        from app.helpers.college_wrapper.college_helper import CollegeRout

        await CollegeRout().store_general_additional_details(
            request_data.get("payload"), request_data.get("college_id")
        )

    async def save_college_subscription_details(self, request_data: dict) -> None:
        """
        Save the college onboarding subscription details

        Param:
            request_data (dict): Get the details which is need to be Approved
        """
        from app.helpers.client_automation.client_automation_helper import (
            Client_screens,
        )

        await Client_screens().add_client_screen(
            payload=request_data.get("payload"),
            screen_type=request_data.get("args").get("screen_type"),
            college_id=request_data.get("college_id"),
            client_id=request_data.get("client_id"),
            dashboard_type=request_data.get("args").get("dashboard_type"),
        )

    async def save_registration_form(self, request_data: dict) -> None:
        """
        Save the college onboarding registration form details

        Param:
            request_data (dict): Get the details which is need to be Approved
        """
        from app.helpers.client_automation.master_helper import Master_Service

        await Master_Service().update_registration_data(
            college_id=request_data.get("college_id"),
            client_id=request_data.get("client_id"),
            registration_form=request_data.get("payload"),
        )

    async def save_application_form(self, request_data: dict) -> None:
        """
        Save the college onboarding application form details

        Param:
            request_data (dict): Get the details which is need to be Approved
        """
        from app.helpers.client_automation.master_helper import Master_Service

        if request_data.get("college_id"):
            from app.core.reset_credentials import Reset_the_settings
            # Checking Whether Course Details Exists for this College
            Reset_the_settings().check_college_mapped(request_data.get("college_id"))
            if not (await DatabaseConfiguration().course_collection.find_one(
                    {"college_id": ObjectId(request_data.get("college_id"))}
            )):
                raise CustomError(
                    message="Course details not found for this college, First Approve or Add Course Details"
                )

        await Master_Service().update_client_or_college_form_data(
            college_id=request_data.get("college_id"),
            client_id=request_data.get("client_id"),
            application_form=request_data.get("payload"),
            request="update",
            user=request_data.get("user"),
        )

    async def save_color_theme(self, request_data: dict) -> None:
        """
        Save the colleges onboarding color theme details

        Param:
            request_data (dict): Get the details which is need to be Approved
        """
        college_id = request_data.get("college_id")
        payload = request_data.get("payload")
        await DatabaseConfiguration().college_collection.update_one(
            {"_id": college_id}, {"$set": {"color_theme": payload}}
        )
        await ApprovedRequestHandler().update_onboarding_details(
            college_id=college_id, client_id=None, step_name="color_theme", status="Approved",
            user={},
            request_of="college_color_theme"
        )

    async def update_onboarding_details(self, college_id: str | None, client_id: str | None, step_name: str, status: str,
                                        user: dict, request_of: str, approval_request: dict = {},
                                        last_step: bool = False) -> None:
        """
            Updates the onboarding step details for a given college or client.

            This method updates the status of a specific onboarding step, adds metadata such as the approver,
            and optionally handles finalization if it's the last step.
            Params:
                college_id (str | None): The ID of the college, if applicable.
                client_id (str | None): The ID of the client, if applicable.
                step_name (str): The name of the onboarding step to update (e.g., 'color_theme').
                status (str): The new status of the step (e.g., 'Approved', 'Rejected').
                user (dict): The user performing the action, including their ID and name.
                request_of (str): Describes what the approval is for (e.g., 'college_color_theme').
                approval_request (dict, optional): Additional approval data, including request ID and rejection reason.
                last_step (bool, optional): Whether this is the final step in the onboarding process.

            Returns:
                None
        """
        if college_id or client_id:
            filter_query = {}
            if client_id and not college_id:
                filter_query = {"client_id": ObjectId(client_id),
                                "type": "client"
                                }
            elif college_id:
                filter_query = {"college_id": ObjectId(college_id),
                                "type": "college"
                                }
            is_client = client_id and not college_id
            if (actual_document := await DatabaseConfiguration().onboarding_details.find_one(filter_query)) is None:
                basic = {
                    "client_id": ObjectId(client_id),
                    "type": "client"} if is_client else {
                    "college_id": ObjectId(college_id),
                    "type": "college"}
                step_key = "create_client" if is_client else "create_college"
                data = {
                    **basic,
                    "status": "In Progress",
                    "created_at": datetime.utcnow(),
                    "last_updated": datetime.utcnow(),
                    "steps": {
                        step_key: {
                            "updated_at": datetime.utcnow(),
                            "status": "Done",
                            "requested_by": {
                                "_id": user.get("_id"),
                                "name": utility_obj.name_can(user)
                            },
                            "request_of": "create_client"
                        }
                    }
                }
                await DatabaseConfiguration().onboarding_details.insert_one(data)
                actual_document = data
            if status == "In Progress":
                update_data = {
                    "$set": {
                        f"steps.{step_name}": {
                            "updated_at": datetime.utcnow(),
                            "status": "Pending",
                            "requested_by": {
                                "_id": user.get("_id"),
                                "name": utility_obj.name_can(user)
                            },
                            "requested_id": ObjectId(approval_request.get("approval_id")),
                            "request_of": request_of
                        },
                        "updated_at": datetime.utcnow(),
                        "status": "Pending"
                    }
                }
            else:
                update_data = {
                    "$set": {
                        f"steps.{step_name}.status":  status,
                        f"steps.{step_name}.updated_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            await DatabaseConfiguration().onboarding_details.update_one(filter_query, update_data)
            if status == "Approved" or (last_step or actual_document.get("last_step_approved") is True):
                approved = False
                if last_step or actual_document.get("last_step_approved") or is_client:
                    approved = all(
                            step.get("status") in ["Approved", "Done"]
                            for key, step in actual_document.get("steps", {}).items()
                            if key != step_name
                        )
                update_data = {"status": "Approved" if approved else "Partially Approved"}
                if not approved and last_step:
                    update_data["last_step_approved"] = True
                await DatabaseConfiguration().onboarding_details.update_one(
                    filter_query, {"$set": update_data}
                )
