"""
This file contain class and functions related to client automation
"""

import copy
import json
from datetime import datetime, timezone
from typing import Dict, Any

from bson import ObjectId
from fastapi import HTTPException
from starlette.responses import JSONResponse

from app.background_task.send_mail_configuration import EmailActivity
from app.core.common_utils import Utils_helper
from app.core.custom_error import CustomError, DataNotFoundError
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import Utility, utility_obj, CustomJSONEncoder
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import cache_invalidation, get_cache_roles_permissions
from app.helpers.approval.approval_helper import ApprovalCRUDHelper, ApprovedRequestHandler
from app.helpers.client_automation.master_helper import Master_Service
from app.helpers.client_curd.client_curd_helper import ClientCurdHelper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.client_automation_schema import FormStatus


class college_details:

    async def add_college_by_admin(
        self, payload: dict | None = None, user: dict = None
    ):
        """
        Create the college by the admin

        Param:
            payload (dict): Get the details of the college

        Return:
            Return success message
        """
        if await DatabaseConfiguration().college_collection.find_one(
                {"$or": [{"name": payload.get("name")}, {"email": payload.get("email")}]}
        ):
            raise CustomError(message="College already exists")
        address = payload.get("address", {})
        if address:
            country_code = state_code = city_name = None
            local_field = False
            if address.get("country_code"):
                local_field = True
                country_code = address.get("country_code")
            if address.get("state_code"):
                local_field = True
                state_code = address.get("state_code")
            if address.get("city_name"):
                local_field = True
                city_name = address.get("city_name")
            if local_field:
                address_details = await Utils_helper().Check_address(
                    country_code=country_code,
                    state_code=state_code,
                    city_name=city_name,
                )
                if address_details is None:
                    raise CustomError(message="Wrong address")
                address.update(
                    {
                        "country_code": address_details.get("country_code"),
                        "country_name": address_details.get("country_name"),
                        "state_name": address_details.get("state_name"),
                        "city_name": address_details.get("name"),
                        "state_code": address_details.get("state_code"),
                    }
                )
        # If the User is Client Admin then He will be Allocated this College
        if user.get("user_type") == "client_admin":
            payload["associated_client"] = user.get("associated_client")

        # Checking if the client exists
        client = await ClientCurdHelper().get_client_by_id(payload.get("associated_client"))
        # Check if the Client Configuration is Done
        if not client.get("is_configured"):
            raise CustomError(message="Client is not configured")

        data = {
            "name": payload.get("name"),
            "college_email": payload.get("email"),
            "mobile_number": payload.get("phone_number"),
            "associated_client_id": ObjectId(payload.get("associated_client")),
            "school_names": [],
            "address": address,
        }

        inserted_college = await DatabaseConfiguration().college_collection.insert_one(
            data
        )
        await DatabaseConfiguration().client_collection.update_one(
            {"_id": ObjectId(payload.get("associated_client"))},
            {"$push": {"college_ids": inserted_college.inserted_id}},
        )

        super_admin = await DatabaseConfiguration().user_collection.find_one(
            {"role.role_name": "super_admin"}
        )

        await EmailActivity().send_onboarding_notification_email(
            entity_type="college",
            entity_data=data,
            recipient_email=super_admin.get("email"),
            email_preferences={},
            request=None,
            event_type="email",
            event_status="sent",
            event_name="Verification",
        )

        await DatabaseConfiguration().onboarding_details.insert_one({
            "college_id": inserted_college.inserted_id,
            "type": "college",
            "status": "In Progress",
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow(),
            "steps": {
                "create_college": {
                    "updated_at": datetime.utcnow(),
                    "status": "Done",
                    "requested_by": {
                        "_id": user.get("_id"),
                        "name": utility_obj.name_can(user)
                    },
                    "request_of": "create_college"
                }
            }
        })
        return {
            "message": "College create successfully.",
            "college_id": str(inserted_college.inserted_id),
        }

    def _flatten_features(self, feature_dict: Dict[str, Any]) -> list[Dict[str, Any]]:
        """
        Recursively flatten nested feature structures into a flat list of dicts
        containing 'feature_id', 'name', and 'amount' (defaulting amount to 0 if missing).
        """
        flat: list[Dict[str, Any]] = []
        for entry in feature_dict.values():
            if isinstance(entry, dict):
                # If entry has feature_id, capture amount or default to 0
                if 'feature_id' in entry:
                    flat.append({
                        'feature_id': entry['feature_id'],
                        'name': entry.get('name', ''),
                        'amount': entry.get('amount', 0)
                    })
                # Always recurse into nested 'features' if present
                nested = entry.get('features')
                if isinstance(nested, dict):
                    flat.extend(self._flatten_features(nested))
        return flat

    async def get_billing_details(self, college_ids: list = []):
        """
        Get Details of Multiple or All Colleges

        Param:
            college_ids (list): Get the details of the college

        Return:
            Return success message
        """
        college_ids = [ObjectId(cid) for cid in college_ids]

        feature_totals: Dict[str, float] = {}
        feature_names: Dict[str, str] = {}
        feature_colleges: Dict[str, set] = {}

        screens_pipeline = []
        if college_ids:
            screens_pipeline.append(
                {"$match": {"college_id": {"$in": college_ids}}}
            )
        screens_pipeline.append(
            {"$match": {"college_id": {"$exists": True}, "dashboard_type": "admin_dashboard"}}
        )

        screens = await DatabaseConfiguration().master_screens.aggregate(
            screens_pipeline
        ).to_list(None)

        for screen in screens:
            college_oid = screen.get('college_id')
            flattened = self._flatten_features(screen)
            seen_in_this_college = set()
            for feat in flattened:
                fid = feat['feature_id']
                feature_totals[fid] = feature_totals.get(fid, 0) + feat['amount']
                feature_names[fid] = feat['name']
                if fid not in feature_colleges:
                    feature_colleges[fid] = set()
                if college_oid not in seen_in_this_college:
                    feature_colleges[fid].add(college_oid)
                    seen_in_this_college.add(college_oid)

        feature_breakdown = []
        for fid, total_amt in feature_totals.items():
            feature_breakdown.append({
                'feature_id': fid,
                'name': feature_names.get(fid, ''),
                'total_amount': total_amt,
                'college_count': len(feature_colleges[fid])
            })

        feature_grand_total = sum(feature_totals.values())

        usage_pipeline = []
        if college_ids:
            usage_pipeline.append(
                {"$match": {"_id": {"$in": college_ids}}}
            )
        usage_pipeline.extend([
            {"$group": {
                "_id": None,
                "lead_count": {
                    "$sum": {"$ifNull": ["$usages.lead_registered", 0]}
                },
                "lead_cost": {
                    "$sum": {
                        "$multiply": [
                            {"$ifNull": ["$usages.lead_registered", 0]},
                            {"$ifNull": ["$charges_per_release.forLead", 0]}
                        ]
                    }
                },
                "lead_limit": {
                    "$sum": {"$ifNull": ["$enforcements.lead_limit", 0]}
                },

                "sms_count": {
                    "$sum": {"$ifNull": ["$usages.sms_sent", 0]}
                },
                "sms_cost": {
                    "$sum": {
                        "$multiply": [
                            {"$ifNull": ["$usages.sms_sent", 0]},
                            {"$ifNull": ["$charges_per_release.forSMS", 0]}
                        ]
                    }
                },

                "whatsapp_count": {
                    "$sum": {"$ifNull": ["$usages.whatsapp_sms_sent", 0]}
                },
                "whatsapp_cost": {
                    "$sum": {
                        "$multiply": [
                            {"$ifNull": ["$usages.whatsapp_sms_sent", 0]},
                            {"$ifNull": ["$charges_per_release.forWhatsapp", 0]}
                        ]
                    }
                },

                "email_count": {
                    "$sum": {"$ifNull": ["$usages.email_sent", 0]}
                },
                "email_cost": {
                    "$sum": {
                        "$multiply": [
                            {"$ifNull": ["$usages.email_sent", 0]},
                            {"$ifNull": ["$charges_per_release.forEmail", 0]}
                        ]
                    }
                },
            }},

            {"$project": {
                "_id": 0,
                "lead_count": 1,
                "lead_cost": 1,
                "lead_limit": 1,
                "sms_count": 1,
                "sms_cost": 1,
                "whatsapp_count": 1,
                "whatsapp_cost": 1,
                "email_count": 1,
                "email_cost": 1,
                "grand_total": {
                    "$add": [
                        "$lead_cost",
                        "$sms_cost",
                        "$whatsapp_cost",
                        "$email_cost"
                    ]
                }
            }}
        ])

        result = await DatabaseConfiguration().college_collection.aggregate(usage_pipeline).to_list(length=1)

        summary = result[0] if result else {
            "lead_count": 0, "lead_cost": 0, "lead_limit": 0,
            "sms_count": 0, "sms_cost": 0,
            "whatsapp_count": 0, "whatsapp_cost": 0,
            "email_count": 0, "email_cost": 0,
            "grand_total": 0
        }

        # summary['feature_breakdown'] = feature_breakdown Enable it if Need
        summary['feature_grand_total'] = feature_grand_total

        return summary

    async def save_signup_form_details(self, college_id: str, data: dict, current_user):
        """
        This function validates the current user, checks if the provided `college_id` is valid,
        and then updates the college collection with the student registration form fields.
        Params:
            college_id (str): The unique identifier of the college where the signup form fields should be saved.
            data (SignupFormRequest): The signup form data containing student registration fields.
            current_user: The authenticated user making the request.
        Returns:
            dict: A success message if the form fields are saved successfully.
                  If an error occurs, a dictionary containing an "error" key with a relevant message.
        Raises:
            Exception: If the `college_id` is not in a valid format, an error message is returned.
                       If the college does not exist, an error message is returned.
                       If the update operation fails, an error message is returned.
        """
        await UserHelper().is_valid_user(current_user)
        fields_dict = data.get("student_registration_form_fields", [])
        update_result = await DatabaseConfiguration().college_collection.update_one(
            {"_id": ObjectId(college_id)},
            {"$set": {"student_registration_form_fields": fields_dict}},
        )
        if update_result.modified_count == 0:
            raise CustomError(message="Failed to update signup form fields")
        return {"message": "Signup form fields saved successfully"}

    async def update_activation_status(
            self, data: dict, college_id: str, current_user
    ) -> dict[str, str]:
        """
         Update the activation status of a college.
        Params:
             data (Dict[str, Any]): Dictionary containing the 'is_activated' flag.
             college_id (str): The ID of the college to update.
             current_user (Any): The authenticated user performing the update.
         Returns:
             Dict[str, str]: A dictionary containing a success message.
         Raises:
             CustomError: If required fields are missing.
             DataNotFoundError: If the college with the given ID does not exist.
        """
        await UserHelper().is_valid_user(current_user)

        if not college_id or not data:
            raise CustomError(message="college_id and status_info are required")

        is_activated = data.get("is_activated")

        if is_activated is None:
            raise CustomError(message="is_activated field is required")
        college_exists = await DatabaseConfiguration().college_collection.find_one(
            {"_id": ObjectId(college_id)}
        )
        if not college_exists:
            raise DataNotFoundError(message="College")
        status_info = {"is_activated": is_activated, "creation_date": datetime.utcnow()}

        if is_activated:
            status_info["activation_date"] = datetime.utcnow()
        else:
            status_info["deactivation_date"] = datetime.utcnow()

        await DatabaseConfiguration().college_collection.update_one(
            {"_id": ObjectId(college_id)}, {"$set": {"status_info": status_info}}
        )
        return {"message": "College Activation status updated successfully"}

    async def add_college_course(
        self, payload: dict, college: dict, user: dict = {}, approval_id: str = None
    ) -> dict:
        """
        Add the course details of the college

        Param:
            payload (dict): Course Details

        Return:
            Return success message
        """
        # Storing Original Payload
        original_payload = payload.copy()

        # If college object have "id" instead of "_id"
        if college.get("id"):
            college["_id"] = ObjectId(college.get("id"))

        college = await DatabaseConfiguration().college_collection.find_one(
            {"_id": ObjectId(college.get("_id"))}
        )

        if college.get("is_configured"):
            # Trying to Check Whether We are Even Able to Connect with Season Database
            try:
                Reset_the_settings().get_user_database(college.get("_id"))
            except Exception as e:
                raise CustomError(message="Unable to Establish Connection with Season Db: " + str(e))

            # Get College Course Details
            college_courses = (
                await DatabaseConfiguration()
                .course_collection.aggregate(
                    [
                        {"$match": {"college_id": ObjectId(college.get("_id"))}},
                        {"$project": {"_id": 0}},
                    ]
                )
                .to_list(length=None)
            )
        else:
            college_courses = []

        college_course_details = {
            "course_details": college_courses
        }

        # Get College School Names & Preference Detail
        college_course_details.update(
            await DatabaseConfiguration().college_collection.find_one(
                {"_id": ObjectId(college.get("_id"))}, {"_id": 0, "school_names": 1}
            )
        )

        # This Values will be updated in the database
        values = {}

        # Checking if the Course List are provided
        if payload.get("course_lists"):
            for course in payload.get("course_lists", []):
                # Checking if Course already exists
                if course.get("course_name") in [
                    course.get("course_name")
                    for course in college_course_details.get("course_details", [])
                ]:
                    raise CustomError(message="Course already exists")

                # Adding College ID & Client ID
                course["college_id"] = ObjectId(college.get("_id"))
                course["client_id"] = ObjectId(college.get("associated_client_id"))
                course["fees"] = f"Rs.{int(course.get('fees'))}.0/-" if type(course.get('fees')) in [int, float] else course.get('fees')
                course["duration"] = f"{int(course.get('duration'))} Years" if type(course.get('duration')) == int else course.get('duration')
                course["is_ug"] = True if course.get("course_type") == "UG" else False
                course["is_pg"] = True if course.get("course_type") == "PG" else False
                course["is_phd"] = True if course.get("course_type") == "PHD" else False

            # Adding Previous + New Course Details
            values["course_details"] = payload.get("course_lists")

        # Adding School which are different from existing ones
        if payload.get("school_names"):
            existing_schools = set(
                college_course_details.get("school_names", [])
            )  # Convert existing schools to a set for faster lookup
            new_schools = set(
                payload.get("school_names", [])
            )  # Convert new schools to a set for faster lookup

            # Adding Previous + New School Names
            values["school_names"] = list(existing_schools.union(new_schools))

        # Checking if Preference Details are provided
        if payload.get("preference_details"):
            preference_based = payload.get("preference_details").get(
                "do_you_want_preference_based_system"
            )
            if preference_based:  # If True, all fields must be non-None
                required_fields = [
                    "will_student_able_to_create_multiple_application",
                    "maximum_fee_limit",
                    "how_many_preference_do_you_want",
                    "fees_of_trigger",
                ]
                for field in required_fields:
                    if payload.get("preference_details").get(field) is None:
                        raise CustomError(
                            f"'{field}' is mandatory when 'do_you_want_preference_based_system'"
                            f" is True"
                        )

                # Converting fees_of_trigger from dict to list
                if (
                    type(payload.get("preference_details").get("fees_of_trigger"))
                    == dict
                ):
                    payload["preference_details"]["fees_of_trigger"] = list(
                        payload.get("preference_details")
                        .get("fees_of_trigger")
                        .values()
                    )
            values["system_preference"] = {
                "preference": payload.get("preference_details", {}).get(
                    "do_you_want_preference_based_system", False
                ),
                "preference_count": payload.get("preference_details", {}).get(
                    "how_many_preference_do_you_want", 0
                ),
            }
            values["fee_rules"] = {
                "fee_cap": payload.get("preference_details", {}).get(
                    "maximum_fee_limit", 0
                ),
                "additional_fees": [],
                "base_fees": {},
            }

            # Adding Base Fees
            for course in values.get("course_details", []):
                values["fee_rules"]["base_fees"][course.get("course_name")] = {}
                for spec in course.get("course_specialization", []):
                    values["fee_rules"]["base_fees"][course.get("course_name")][spec.get("spec_name")] = int(spec.get("spec_fees")) \
                        if spec.get("spec_fees") \
                        else float(course.get("fees").replace("Rs.", "").replace("/-", ""))

            for index, fee in enumerate(
                payload.get("preference_details", {}).get("fees_of_trigger", [])
            ):
                data = {"type": "fixed", "trigger_count": index + 1, "amount": fee}
                values["fee_rules"]["additional_fees"].append(data)

        values["fetch_form_data_through"] = payload.get(
            "fetch_form_data_through", "college_wise"
        )
        # If the User is not Admin or Super Admin, then Approval Request wil be Created
        if user and user.get("role", {}).get("role_name") not in [
            "admin",
            "super_admin",
        ]:
            approval_request = await ApprovalCRUDHelper().create_approval_request(
                user,
                {
                    "college_id": ObjectId(college.get("_id")),
                    "approval_type": "college_course_details",
                    "payload": original_payload,
                },
                approval_id=approval_id,
            )
            await ApprovedRequestHandler().update_onboarding_details(
                college_id=college.get("_id"), client_id=None, step_name="course_details", status="In Progress",
                user=user, approval_request=approval_request,
                request_of="college_course_details"
            )
            return approval_request
        else:
            if not college.get("is_configured"):
                raise CustomError(message="College not configured")

        # Adding Course Details
        if values.get("course_details"):
            await DatabaseConfiguration().course_collection.insert_many(
                values.get("course_details")
            )
            values.pop("course_details")

        # Adding School & Preference Detail in College
        await DatabaseConfiguration().college_collection.update_one(
            {"_id": ObjectId(college.get("_id"))}, {"$set": values}
        )

        await cache_invalidation(api_updated="updated_college", user_id=str(college.get("_id")))

        await ApprovedRequestHandler().update_onboarding_details(
            college_id=college.get("_id"), client_id=None, step_name="course_details", status="Approved",
            user=user,
            request_of="college_course_details"
        )
        return {"message": "Course details added successfully."}

    # Functions were Already Present, In Some Functionality Needed this can be Used
    # async def add_extra_college_details(self, payload: dict, college: dict, user: dict = {}, approval=False) -> dict:
    #     """
    #     Add the extra details of the college
    #
    #     Param:
    #         payload (dict): Extra Details
    #         college (dict): College Details
    #         user (dict): User Details
    #
    #     Return:
    #         Return success message
    #     """
    #     # If college object have "id" instead of "_id"
    #     if college.get("id"):
    #         college["_id"] = ObjectId(college.get("id"))
    #
    #     if not approval and payload.get('lead_tags'):
    #         #retrieving previous lead tags if any
    #         previous_lead_tags = college.get("lead_tags", [])
    #         # Adding Previous + New Lead Tags
    #         payload['lead_tags'] = previous_lead_tags + payload.get('lead_tags', [])
    #
    #     if not approval and payload.get('lead_stages'):
    #         #retrieving previous lead stages if any
    #         previous_lead_stages = college.get("lead_stages", [])
    #         # Adding Previous + New Lead Stages
    #         payload['lead_stages'] = previous_lead_stages + payload.get('lead_stages', [])
    #
    #     # If the User is not Admin or Super Admin, then Approval Request wil be Created
    #     if user and user.get("role", {}).get("role_name") not in ["admin", "super_admin"]:
    #         return await ApprovalCRUDHelper().create_approval_request(
    #             user, {
    #                 "college_id": ObjectId(college.get("_id")),
    #                 "approval_type": "college_additional_details",
    #                 "payload": payload
    #             }
    #         )
    #
    #     # Adding Extra Details
    #     await DatabaseConfiguration().college_collection.update_one(
    #         {"_id": ObjectId(college.get("_id"))},
    #         {"$set": payload}
    #     )
    #
    #     return {"message": "Extra details added successfully."}
    #

    async def fetch_college_by_role(
            self, current_user: dict, page_num: int, page_size: int
    ) -> JSONResponse:
        """
        Fetches colleges based on the role of the currently authenticated user.
        - If the user is a `super_account_manager`, it fetches colleges associated with all clients
          under their assigned account managers.
        - If the user is an `account_manager`, it fetches colleges associated with their assigned clients.
        - If the user is a `client_admin`, it fetches colleges associated with their linked client.
        - If the user is a `super_admin` or `admin`, all colleges are fetched (no filtering by client).
        - Any other role is unauthorized.
        Pagination is applied to the result using the provided `page_num` and `page_size`.
        Params:
            current_user (dict): The currently authenticated user's information, including role and username.
            page_num (int): The page number for pagination (1-indexed).
            page_size (int): The number of records per page.
        Returns:
            JSONResponse: A paginated list of colleges along with metadata like total count and pagination details.
        Raises:
            HTTPException:
                - 404 if the user is not found in the database.
                - 401 if the user is not authorized to perform this action.
        """
        role = current_user.get("role", "")
        user_name = current_user.get("user_name")
        client_ids = []
        if role == "super_account_manager":
            pipeline = [
                {
                    "$match": {
                        "user_name": user_name,
                        "role.role_name": "super_account_manager",
                    }
                },
                {
                    "$project": {
                        "account_manager_ids": {
                            "$map": {
                                "input": {
                                    "$ifNull": ["$assigned_account_managers", []]
                                },
                                "as": "am",
                                "in": "$$am.account_manager_id",
                            }
                        }
                    }
                },
                {
                    "$lookup": {
                        "from": "users",
                        "let": {"am_ids": "$account_manager_ids"},
                        "pipeline": [
                            {"$match": {"$expr": {"$in": ["$_id", "$$am_ids"]}}},
                            {"$project": {"assigned_clients": 1}},
                            {"$unwind": "$assigned_clients"},
                            {
                                "$group": {
                                    "_id": None,
                                    "client_ids": {
                                        "$addToSet": "$assigned_clients.client_id"
                                    },
                                }
                            },
                        ],
                        "as": "clients_info",
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "client_ids": {
                            "$ifNull": [
                                {"$arrayElemAt": ["$clients_info.client_ids", 0]},
                                [],
                            ]
                        },
                    }
                },
            ]
            result = (
                await DatabaseConfiguration()
                .user_collection.aggregate(pipeline)
                .to_list(1)
            )
            if not result:
                raise HTTPException(status_code=404, detail="User not found")
            client_ids = result[0].get("client_ids", [])
        elif role == "account_manager":
            pipeline = [
                {
                    "$match": {
                        "user_name": user_name,
                        "role.role_name": "account_manager",
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "client_ids": {
                            "$map": {
                                "input": "$assigned_clients",
                                "as": "client",
                                "in": "$$client.client_id",
                            }
                        },
                    }
                },
            ]
            result = (
                await DatabaseConfiguration()
                .user_collection.aggregate(pipeline)
                .to_list(1)
            )
            if not result:
                raise HTTPException(status_code=404, detail="User not found")
            client_ids = result[0].get("client_ids", [])
        elif role == "client_admin":
            user = await DatabaseConfiguration().user_collection.find_one(
                {"user_name": current_user.get("user_name")}
            )
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            client_ids = [user.get("associated_client")]
        elif role not in ["super_admin", "admin"]:
            raise HTTPException(
                status_code=401, detail="You are not authorized to perform this action"
            )

        match_stage = (
            {"$match": {"client_id": {"$in": client_ids}}} if client_ids else {}
        )
        pipeline = [match_stage] if match_stage else []
        colleges = (
            await DatabaseConfiguration()
            .college_collection.aggregate(pipeline)
            .to_list(length=None)
        )
        if page_num and page_size:
            route_name = f"/client_automation/get_colleges"
            total_data = len(colleges)
            response = await utility_obj.pagination_in_api(
                page_num, page_size, colleges, total_data, route_name
            )
            college_data = {
                "data": response["data"],
                "total": total_data,
                "count": len(response["data"]),
                "pagination": response["pagination"],
                "message": "Colleges Fetched Successfully",
            }
            college_data = json.dumps(college_data, cls=CustomJSONEncoder)
            return JSONResponse(status_code=200, content=json.loads(college_data))

    async def fetch_all_colleges_data(
            self, current_user, page_num: int, page_size: int
    ):
        """
        Retrieves application form fields along with college details, with pagination.

        Params:
            - current_user (User): Authenticated user.
            - page_num (int): Page number for pagination.
            - page_size (int): Number of records per page.

        Returns:
            - A tuple containing:
                1. List of application form fields with full document structure.
                2. Total count of matching records.
        """
        await UserHelper().is_valid_user(current_user)
        utility_obj = Utility()
        pipeline = [
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "college_basic_details": 1,
                    "form_details.signup_form": 1,
                    "form_details.dynamic_tab_wise_forms": 1,
                    "feature_subscription_lists": 1,
                    "additional_details": 1,
                }
            }
        ]
        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
        pipeline.append(
            {
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            }
        )

        result = (
            await DatabaseConfiguration()
            .college_collection.aggregate(pipeline)
            .to_list(None)
        )
        result = result[0] if result else {}

        return (
            result.get("paginated_results", []),
            (
                result.get("totalCount", [{}])[0].get("count", 0)
                if result.get("totalCount")
                else 0
            ),
        )

    async def update_college_status(
            self, college_ids: list[str], new_status: FormStatus, current_user
    ) -> int:
        """
        Update the status of multiple colleges.
        Params:
            college_ids (list[str]): List of college IDs as strings.
            new_status (FormStatus): The new status to set (Approved, Declined, Pending).
            current_user (User): The currently authenticated user object.
        Returns:
            int: Number of colleges updated.
        Raises:
            HTTPException: If there is an error during the update process.
        """
        # TODO: Authentication & Authorization will be changed based on RBAC
        await UserHelper().is_valid_user(current_user)
        if not college_ids:
            raise CustomError("College IDs list cannot be empty.")
        valid_ids = [ObjectId(cid) for cid in college_ids]

        update_result = await DatabaseConfiguration().college_collection.update_many(
            {"_id": {"$in": valid_ids}}, {"$set": {"status": new_status.value}}
        )

        return update_result.modified_count


class Client_screens:

    async def add_client_helper(
            self, payload: list, master_details: dict, reformatted_data: dict
    ):
        """
        Add the client helper details

        Param:
            payload (list): Get the details of the client
            master_details (dict): Get the master details
            reformatted_data (dict): Get the reformatted data

        Return:
            None
        """
        for data in payload:
            feature_id = data.get("feature_id")
            if feature_id:
                if feature_id not in list(master_details.keys()):
                    raise DataNotFoundError(message=f"Feature id '{feature_id}'")
                temp_data = master_details.get(feature_id, {})
                temp = data.get("features", [])
                temp_master = {}
                if temp:
                    if temp_data.get("features"):
                        temp_master = temp_data.pop("features", {})
                reformatted_data[feature_id] = temp_data
                if temp:
                    reformatted_data[feature_id]["features"] = {}
                    await self.add_client_helper(
                        payload=temp,
                        master_details=temp_master,
                        reformatted_data=reformatted_data[feature_id]["features"],
                    )
            else:
                await Master_Service().update_data(
                    reformatted_data=reformatted_data, payload=[data]
                )

    async def add_client_screen(
            self,
            payload: list,
            screen_type: str,
            client_id: str | None = None,
            college_id: str | None = None,
            user: dict = None,
            dashboard_type: str | None = None,
            approval_id: str | None = None,
    ):
        """
        Add the client screen details

        Param:
            payload (dict): Get the screen details
            client_id (str): Get the client id
            college_id (str): Get the college id
            screen_type (str): Get the screen type
            dashboard_type (str): Get the dashboard type

        Return:
            Return success message
        """
        message = "Client screen created successfully."
        if not payload:
            raise CustomError(message="Screen details must be required")
        if (
                master_details := await DatabaseConfiguration().master_screens.find_one(
                    {"screen_type": "master_screen", "dashboard_type": dashboard_type}
                )
        ) is None:
            raise DataNotFoundError(message="Master screen")
        filter_data = {"screen_type": screen_type, "dashboard_type": dashboard_type}
        if college_id:
            if not ObjectId.is_valid(college_id):
                raise CustomError(message="College id is not valid")
            filter_data.update({"college_id": ObjectId(college_id)})
            message = "College screen created successfully."
        elif client_id:
            filter_data.update({"client_id": ObjectId(client_id)})
            message = "Client screen created successfully."
        current_exist = True
        if (
                reformatted_data := await DatabaseConfiguration().master_screens.find_one(
                    filter_data
                )
        ) is None:
            reformatted_data = {}
            current_exist = False
        await self.add_client_helper(
            payload=payload,
            master_details=master_details,
            reformatted_data=reformatted_data,
        )
        reformatted_data.update(filter_data)
        if user and user.get("role", {}).get("role_name") not in [
            "admin",
            "super_admin",
        ]:
            approval_request = await ApprovalCRUDHelper().create_approval_request(
                user,
                {
                    "args": {
                        "dashboard_type": dashboard_type,
                        "screen_type": screen_type,
                    },
                    "payload": payload,
                    "approval_type": (
                        "college_subscription_details"
                        if college_id
                        else "client_subscription_details"
                    ),
                    **(
                        {"client_id": ObjectId(client_id)}
                        if client_id is not None
                        else {}
                    ),
                    **(
                        {"college_id": ObjectId(college_id)}
                        if college_id is not None
                        else {}
                    ),
                },
                approval_id=approval_id,
            )
            await ApprovedRequestHandler().update_onboarding_details(
                college_id=college_id, client_id=client_id, step_name="subscription_module", status="In Progress",
                user=user, approval_request=approval_request,
                request_of="college_subscription_details" if college_id else "client_subscription_details"
            )
            return approval_request
        if current_exist:
            reformatted_data["updated_at"] = datetime.now(timezone.utc)
            await DatabaseConfiguration().master_screens.update_one(
                filter_data, {"$set": reformatted_data}
            )
            message = message.replace("created", "updated")
        else:
            reformatted_data.update(
                {
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            await DatabaseConfiguration().master_screens.insert_one(reformatted_data)
        await ApprovedRequestHandler().update_onboarding_details(
            college_id=college_id, client_id=client_id, step_name="subscription_module", status="Approved",
            user=user, last_step=True,
            request_of="college_subscription_details" if college_id else "client_subscription_details"
        )
        return {"message": message}

    async def update_client_dashboard(
            self, payload: list, reformatted_data: dict, master_details: dict
    ):
        """
        Update the dashboard controller data by the super admin

        Param:
            payload (list): Get the details of the dashboard
            reformatted_data (dict): Get the reformatted data
            master_details (dict): Get the master details

        Return:
            Return success message
        """
        for data in payload:
            feature_id = data.get("feature_id")
            if feature_id:
                temp_data = data.get("features", [])
                if feature_id not in list(master_details.keys()):
                    raise DataNotFoundError(message=f"Feature id '{feature_id}'")
                if temp_data:
                    data.pop("features", [])
                if not reformatted_data.get(feature_id):
                    reformatted_data[feature_id] = {}
                reformatted_data[feature_id].update(data)
                if temp_data:
                    if not reformatted_data[feature_id].get("features"):
                        reformatted_data[feature_id]["features"] = {}
                    await self.update_client_dashboard(
                        payload=temp_data,
                        reformatted_data=reformatted_data[feature_id]["features"],
                        master_details=master_details[feature_id].get("features", []),
                    )
            else:
                await Master_Service().update_data(
                    reformatted_data=reformatted_data, payload=[data]
                )

    def merge_feature_objects(self, obj1, obj2):
        """
        Recursively merge two feature objects (with nested 'features' lists).

        Param:
            obj1 (dict): First feature object.
            obj2 (dict): Second feature object.
        Return:
            dict: Merged feature object.
        """
        merged = copy.deepcopy(obj1)

        if "features" in obj1 and "features" in obj2:
            merged_features = {f["feature_id"]: f for f in obj1["features"]}
            for feature in obj2["features"]:
                fid = feature["feature_id"]
                if fid in merged_features:
                    merged_features[fid] = self.merge_feature_objects(
                        merged_features[fid], feature
                    )
                else:
                    merged_features[fid] = feature
            merged["features"] = list(merged_features.values())

        return merged

    def merge_json_objects(self, first, second):
        """
        Merges two JSON objects dynamically based on their structure.

        Param:
            first (dict): First JSON object.
            second (dict): Second JSON object.
        Return:
            dict: Merged JSON object.
        """
        merged = copy.deepcopy(first)

        for key, value in second.items():
            if key not in merged:
                merged[key] = value
            else:
                # If it's a feature object with 'feature_id'
                if isinstance(value, dict) and "feature_id" in value:
                    if merged[key].get("feature_id") != value["feature_id"]:
                        # Different features at same key: preserve both
                        merged[key + "_from_second"] = value
                    else:
                        # Same feature_id, maybe merge nested features
                        if "features" in merged[key] and isinstance(
                                merged[key]["features"], list
                        ):
                            merged[key] = self.merge_feature_objects(merged[key], value)
                else:
                    # For non-feature fields like _id, timestamps, etc., just keep original
                    pass

        return merged

    async def merge_multiple_jsons(self, json_list):
        """
        Merge a list of JSON dictionaries using merge_json_objects function.

        Param:
            json_list (list): List of JSON dictionaries to merge.
        Return:
            dict: Merged JSON object.
        """
        from functools import reduce

        return reduce(self.merge_json_objects, json_list)

    async def update_client_screen(
            self,
            payload: list,
            screen_type: str,
            client_id: str | None = None,
            college_id: str | None = None,
            dashboard_type: str | None = None,
            invalidation_route: str | None = None
    ):
        """
        Update the client screen details

        Param:
            payload (dict): Get the screen details
            client_id (str): Get the client id
            college_id (str): Get the college id
            screen_type (str): Get the screen type
            dashboard_type (str): Get the dashboard type

        Return:
            Return success message
        """
        filter_data = {"screen_type": screen_type}
        message = "Client screen has been updated successfully."
        error_message = "Client screen"
        if (
                master_details := await DatabaseConfiguration().master_screens.find_one(
                    {"screen_type": "master_screen", "dashboard_type": dashboard_type}
                )
        ) is None:
            raise DataNotFoundError(message="Master screen")
        total_json = [master_details]
        if college_id:
            if client_data := await DatabaseConfiguration().client_collection.find_one(
                    {"college_ids": {"$in": [ObjectId(college_id)]}}
            ):
                if client_screen := await DatabaseConfiguration().master_screens.find_one(
                        {
                            "screen_type": "client_screen",
                            "dashboard_type": dashboard_type,
                            "client_id": ObjectId(client_data.get("client_id")),
                        }
                ):
                    total_json.append(client_screen)
            if college_screen := await DatabaseConfiguration().master_screens.find_one(
                    {
                        "college_id": ObjectId(college_id),
                        "screen_type": "college_screen",
                        "dashboard_type": dashboard_type,
                    }
            ):
                total_json.append(college_screen)
            filter_data.update({"college_id": ObjectId(college_id)})
            error_message = "College screen"
            message = "College screen has been updated successfully."
        elif client_id:
            if client_screen := await DatabaseConfiguration().master_screens.find_one(
                    {
                        "screen_type": "client_screen",
                        "client_id": ObjectId(client_id),
                        "dashboard_type": dashboard_type,
                    }
            ):
                total_json.append(client_screen)
            filter_data.update(
                {"client_id": ObjectId(client_id), "dashboard_type": dashboard_type}
            )
        master_details = await self.merge_multiple_jsons(total_json)
        if (
                reformatted_data := await DatabaseConfiguration().master_screens.find_one(
                    filter_data
                )
        ) is None:
            raise DataNotFoundError(message=error_message)
        await self.update_client_dashboard(
            payload=payload,
            reformatted_data=reformatted_data,
            master_details=master_details,
        )
        reformatted_data["updated_at"] = datetime.now(timezone.utc)
        await DatabaseConfiguration().master_screens.update_one(
            filter_data, {"$set": reformatted_data}
        )
        await cache_invalidation(api_updated=invalidation_route)
        return {"message": message}

    async def collect_required_role_ids(self, screen_data):
        """
        Recursively collects all unique role IDs from the given screen data.

        This method traverses the nested structure of the provided screen data and collects
        all values associated with the "required_role_ids" key, assuming they are lists.

        Params:
            screen_data (Any): A nested dictionary or list structure containing role ID data.

        Returns:
            List[Any]: A list of unique role IDs extracted from the screen data.
        """
        unique_role_ids = set()

        def traverse(node):
            """Recursively traverses nested dicts/lists to collect values"""
            if isinstance(node, dict):
                for key, value in node.items():
                    if key == "required_role_ids" and isinstance(value, list):
                        unique_role_ids.update(value)
                    else:
                        traverse(value)
            elif isinstance(node, list):
                for item in node:
                    traverse(item)

        traverse(screen_data)
        return list(unique_role_ids)

    async def collect_required_role_names(self, screen_data: dict) -> list:
        """
        Collects and returns a list of role objects with their IDs and names based on the provided screen data.

        This method first retrieves a set of unique role IDs from the given screen data. For each role ID, it attempts
        to fetch the role's data (including the name) from a cached store. If the role data is not found in the cache,
        it refreshes the cache and tries again. If the role still cannot be found, a DataNotFoundError is raised.

        Params:
            screen_data (dict): Input data used to determine the required role IDs.

        Returns:
            List[dict]: A list of dictionaries, each containing the 'id' and 'name' of a role.

        Raises:
            DataNotFoundError: If role data for a required role ID cannot be found after cache refresh.
        """
        unique_role_ids = await self.collect_required_role_ids(screen_data)
        role_obj = []
        for role_id in unique_role_ids:
            role_data = await get_cache_roles_permissions(
                collection_name="roles_permissions", field=str(role_id)
            )
            if not role_data:
                cached_data = await utility_obj.cache_roles_and_permissions()
                all_roles = cached_data.get("data", {})
                role_data = json.loads(all_roles.get(str(role_id), "{}"))
            if not role_data:
                raise DataNotFoundError(message=f"Role with id '{role_id}'")
            role_obj.append({"id": role_id, "name": role_data.get("name")})
        return role_obj

    async def update_specific_feature_field(
            self,
            payload: dict,
            client_id: str | None = None,
            dashboard_type: str | None = None,
            screen_type: str | None = None,
            college_id: str | None = None
    ):
        """
        Update specific feature field in the client screen.

        Params:
            payload (dict): The payload containing the feature details to be updated.
            client_id (str | None): The client ID for which the screen is being updated.
            dashboard_type (str | None): The type of dashboard.
            screen_type (str | None): The type of screen.
            college_id (str | None): The college ID for which the screen is being updated.

        Returns:
            dict: A message indicating the success of the operation.

        Raises:
            CustomError: If the payload is empty or if the screen type is not provided.
        """
        filter_data = {"screen_type": screen_type}
        message = "Client screen has been updated successfully."
        error_message = "Client screen"

        if college_id:
            filter_data.update({"college_id": ObjectId(college_id)})
            error_message = "College screen"
            message = "College screen has been updated successfully."

        elif client_id:
            filter_data.update(
                {"client_id": ObjectId(client_id), "dashboard_type": dashboard_type}
            )

        if (
                reformatted_data := await DatabaseConfiguration().master_screens.find_one(
                    filter_data
                )
        ) is None:
            raise DataNotFoundError(message=error_message)

        response = await Master_Service().recursive_check(
            data=reformatted_data, target_id=payload.get("feature_id"),
            update_data=payload)

        if response:
            reformatted_data["updated_at"] = datetime.now(timezone.utc)
            await DatabaseConfiguration().master_screens.update_one(
                filter_data, {"$set": reformatted_data}
            )
            await cache_invalidation(api_updated="master_screen_update")
            return {"message": message}
        raise CustomError(f"Feature id '{payload.get('feature_id')}' not found in the screen data.")
