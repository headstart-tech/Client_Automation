"""
This file contain class and functions related to college API routes/endpoints
"""

import asyncio
import datetime
import json
from typing import Dict, Any, Optional, Union

import pandas as pd
from bson.objectid import ObjectId
from fastapi import BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException

from app.core.custom_error import CustomError, DataNotFoundError
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, CustomJSONEncoder
from app.database.aggregation.college import College
from app.database.aggregation.course import Course
from app.database.configuration import DatabaseConfiguration
from app.database.database_sync import DatabaseConfigurationSync
from app.database.motor_base_singleton import MotorBaseSingleton
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.student_user_schema import User


class CollegeHelper:
    """
    Contain operations related to college
    """

    async def update_status(
            self, college_id, user, status, background_tasks: BackgroundTasks
    ):
        """
        Approve college form
        """
        from app.dependencies.oauth import cache_invalidation
        await utility_obj.is_id_length_valid(_id=college_id, name="College id")
        college = await DatabaseConfiguration().college_collection.find_one(
            {"_id": ObjectId(college_id)}
        )
        if not college:
            return {"detail": "College not found."}
        if status.lower() == "approved":
            if college.get("_id") not in user.get("associated_colleges", []):
                user.get("associated_colleges", []).insert(0,
                                                           college.get("_id"))
            await DatabaseConfiguration().user_collection.update_one(
                {"_id": user.get("_id")},
                {"$set": {
                    "associated_colleges": user.get("associated_colleges")}},
            )
        await DatabaseConfiguration().college_collection.update_one(
            {"_id": ObjectId(college_id)},
            {
                "$set": {
                    "client_manager_name": utility_obj.name_can(user),
                    "client_manager_id": user.get("_id"),
                    "client_manager_email_id": user.get("email"),
                    "status": status.title(),
                    f"status_changed_on": datetime.datetime.utcnow(),
                }
            },
        )
        await cache_invalidation(api_updated="updated_user", user_id=user.get('email') if user else None)
        await cache_invalidation(api_updated="updated_college", user_id=college_id)
        return {"message": "Status updated."}

    async def colleges_based_on_status(
            self,
            approved,
            declined,
            pending,
            own_colleges,
            page_num=None,
            page_size=None,
            route_name=None,
            user=None,
    ):
        """
        Get colleges forms based on status
        """
        colleges = await College().get_colleges_by_status(
            approved, declined, pending, own_colleges, user
        )
        if colleges:
            if page_num and page_size:
                response = await utility_obj.pagination_in_api(
                    page_num, page_size, colleges, len(colleges), route_name
                )

                return {
                    "data": json.loads(json.dumps(response["data"], cls=CustomJSONEncoder)),
                    "total": len(colleges),
                    "count": page_size,
                    "pagination": response["pagination"],
                    "message": "Colleges data found.",
                }
            return {"data": json.loads(json.dumps(colleges, cls=CustomJSONEncoder)),
                    "message": "Colleges data found."}
        return False

    async def update_details(
            self, college_id, data, user, background_tasks: BackgroundTasks, create_client
    ):
        """
        Update college details
        """
        from app.dependencies.oauth import cache_invalidation
        if user.get("role", {}).get("role_name") not in ["client_manager", "super_admin"]:
            return {"detail": "Not enough permissions"}
        data = {
            key: value for key, value in data.items() if
            value not in [None, {}, []]
        }
        await utility_obj.is_id_length_valid(_id=college_id, name="College id")
        college = await DatabaseConfiguration().college_collection.find_one(
            {"_id": ObjectId(college_id)}
        )
        if not college:
            return {
                "detail": "College not found. "
                          "Make sure provided college id should be correct."
            }
        if data.get("name") and college.get("name") != data.get("name"):
            if (
                    await DatabaseConfiguration().college_collection.find_one(
                        {"name": data.get("name")})
                    is not None
            ):
                raise HTTPException(400,
                                    detail="College data already exist.")

        last_modified_timeline = {
            "last_modified_at": datetime.datetime.utcnow(),
            "user_id": ObjectId(str(user.get("_id"))),
            "user_name": utility_obj.name_can(user),
        }
        if college.get("last_modified_timeline"):
            college.get("last_modified_timeline", []).insert(0,
                                                             last_modified_timeline)
            data["last_modified_timeline"] = college.get(
                "last_modified_timeline")
        else:
            data["last_modified_timeline"] = [last_modified_timeline]
        client_info = {}
        for item in [("name", "name"), ("current_season", "current_season"),
                     ("season_info", "seasons"), ("aws_s3_credentials", "s3"),
                     ("email_credentials", "email"), ("sms_credentials", "sms"),
                     ("whatsapp_credentials", "whatsapp_credential"),
                     ("meilisearch_credentials", "meilisearch"),
                     ("report_webhook_api_key", "report_webhook_api_key"),
                     ("university_info", "university"),
                     ("aws_textract_credentials", "aws_textract"),
                     ("redis_cache_credentials", "cache_redis"), ("tawk_secret", "tawk_secret"),
                     ("telephony_secret", "telephony_secret"), ("razorpay_credentials", "razorpay"),
                     ("client_manager_name", "client_manager_name")]:
            field_name = item[0]
            if data.get(field_name):
                client_info.update({item[1]: data.pop(field_name)})
        if create_client and client_info:
            await DatabaseConfiguration().client_collection.update_one(
                {"client_id": ObjectId(college_id)}, {"$set": client_info}
            )
        if data:
            await DatabaseConfiguration().college_collection.update_one(
                {"_id": ObjectId(college_id)}, {"$set": data}
            )
            await cache_invalidation(api_updated="updated_college", user_id=college_id)
        return {"message": "Updated college data."}

    async def get_course_details(self, course_name: str | None, college: dict,
                                 specialization_name: str | None) -> dict:
        """
        Get course details. If a course/specialization name is given then giving
        form details which is specific to course/specialization.

        Params:
            - course_name (str | None): Either None or name of a course.
                e.g., B.Sc.
            - college: A dictionary which contains college information.
            - specialization_name (str | None): Either None or name of
                course specialization. e.g., Physician Assistant.

        Returns:
            dict: A dictionary which contains information of form.
        """
        if course_name:
            form_details = await College().fetch_form_details(college.get('id'))
            data = {}
            if college.get("is_different_forms") is False:
                data = form_details
                data["system_preference"] = college.get(
                    "system_preference", {})
            else:
                for item in form_details.values():
                    if item.get("course_name") == course_name:
                        for key in ["course_name", "_id"]:
                            if key in item:
                                item.pop(key)
                        if specialization_name:
                            if item.get("spec_name") == specialization_name:
                                if "spec_name" in item:
                                    item.pop("spec_name")
                                data = item
                                data["system_preference"] = college.get(
                                    "system_preference", {})
                                break
                        else:
                            data = item
                            data["system_preference"] = college.get(
                                "system_preference", {})
                            break
            return {"data": json.loads(json.dumps(data, cls=CustomJSONEncoder)),
                    "message": "Get course details."}
        else:
            return {
                "data": json.loads(
                    json.dumps(college.get("course_details"), cls=CustomJSONEncoder)),
                "message": "Get all course details."
            }

    async def add_or_update_component_charges(self, component_charges):
        """
        Add or update component charges
        """
        component_charges = jsonable_encoder(component_charges)
        data = await DatabaseConfiguration().component_charges_collection.find_one(
            {})
        if data:
            await DatabaseConfiguration().component_charges_collection.update_one(
                {"_id": ObjectId(data.get("_id"))}, {"$set": component_charges}
            )
            data["_id"] = str(data.get("_id"))
            return {"data": data, "message": "Updated component charges."}
        await DatabaseConfiguration().component_charges_collection.insert_one(
            component_charges
        )
        data = await DatabaseConfiguration().component_charges_collection.find_one(
            {})
        data["_id"] = str(data.get("_id"))
        return {"data": data, "message": "Add component charges."}

    async def get_component_charges(self):
        """
        Add or update component charges
        """
        data = await DatabaseConfiguration().component_charges_collection.find_one(
            {})
        if data:
            data["_id"] = str(data.get("_id"))
        return {"data": data if data else "NA",
                "message": "Get component charges."}

    async def estimated_bill(self, current_user, page_num, page_size,
                             route_name):
        """
        Get estimated bill of college
        """
        user = await UserHelper().is_valid_user(current_user)
        if user.get("role", {}).get("role_name") != "client_manager":
            return {"detail": "Not enough permissions"}
        colleges = await College().get_colleges_estimation_bill_data()
        if colleges:
            if page_num and page_size:
                response = await utility_obj.pagination_in_api(
                    page_num, page_size, colleges, len(colleges), route_name
                )
                return {
                    "data": response["data"],
                    "total": len(colleges),
                    "count": page_size,
                    "pagination": response["pagination"],
                    "message": "Get estimated bill.",
                }
            return {"data": colleges, "message": "Get estimated bill."}
        return {"detail": "Colleges data not found."}

    def _flatten_features(self, feature_dict: Dict[str, Any]) -> list[Dict[str, Any]]:
        """
        Recursively flatten nested feature structures into a flat list of dicts
        containing 'feature_id', 'name', and 'amount'.
        """
        flat: list[Dict[str, Any]] = []
        for entry in feature_dict.values():
            if isinstance(entry, dict) and 'feature_id' in entry: # and 'amount' in entry
                flat.append({
                    'feature_id': entry['feature_id'],
                    'name': entry.get('name', ''),
                    'amount': entry.get('amount', 0)
                })
                nested = entry.get('features', {})
                if isinstance(nested, dict):
                    flat.extend(self._flatten_features(nested))
        return flat

    async def get_college_billing(
            self,
            from_date: str,
            to_date: Optional[str] = None,
            college_id: str = None,
    ) -> Dict[str, Any]:
        """
        Calculate billing activities for a single college within a date range.

        - from_date: 'YYYY-MM-DD'
        - to_date: 'YYYY-MM-DD' or None (defaults to now)

        Returns a dict with:
          - feature_breakdown (list of {feature_id, name, monthly_total, college_count=1})
          - feature_grand_total
          - sms_count, sms_cost
          - whatsapp_count, whatsapp_cost
          - email_count, email_cost
          - grand_total

        Raises:
          - CustomError: if from_date or to_date is invalid
        """
        from app.dependencies.oauth import is_testing_env
        # Parse start date
        try:
            start_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
        except ValueError:
            raise CustomError("from_date must be in 'YYYY-MM-DD' format.")

        # Determine end date
        if to_date:
            try:
                end_date = datetime.datetime.strptime(to_date, '%Y-%m-%d') + datetime.timedelta(
                    days=1) - datetime.timedelta(microseconds=1)
            except ValueError:
                raise CustomError("to_date must be in 'YYYY-MM-DD' format or None.")
        else:
            end_date = datetime.datetime.now()

        # Check if college id is there, if not Using Default College
        # As Per Frontend Request we are Doing this, It means What to Show if no College ID is Provided
        if not college_id:
            college_id = MotorBaseSingleton.get_instance().master_data.get("college_id")

        # Check if College exists or not
        if not (college := await self.college_details(str(college_id), with_helper=False)):
            raise DataNotFoundError(message="College")

        PRICELIST = {
            'sms': college.get("charges_per_release", {}).get("forSMS", 0),
            'whatsapp': college.get("charges_per_release", {}).get("forWhatsapp", 0),
            'email': college.get("charges_per_release", {}).get("forEmail", 0),
            'lead': college.get("charges_per_release", {}).get("forLead", 0)
        }

        # Convert to ObjectId
        oid = ObjectId(college_id)

        # 1) Fetch single screen config and flatten
        screen = await DatabaseConfiguration().master_screens.find_one({'college_id': oid}, {'_id': 0, 'college_id': 0, 'screen_type': 0, 'dashboard_type': 0, 'created_at': 0, 'updated_at': 0})
        if not is_testing_env():
            Reset_the_settings().get_user_database(college_id)
            if not screen:
                raise DataNotFoundError(message="College Screen")

        flattened = self._flatten_features(screen or {})

        # Aggregate feature totals
        feature_totals: Dict[str, float] = {}
        feature_names: Dict[str, str] = {}
        for feat in flattened:
            fid = feat['feature_id']
            amt = feat['amount']
            feature_totals[fid] = feature_totals.get(fid, 0) + amt
            feature_names[fid] = feat['name']

        feature_breakdown = [
            {
                'feature_id': fid,
                'name': feature_names[fid],
                'monthly_total': total_amt,
            }
            for fid, total_amt in feature_totals.items()
        ]
        feature_grand_total = sum(feature_totals.values())

        # 2) Single aggregation query for all transaction types
        pipeline = [
            {
                '$match': {
                    'created_at': {'$gte': start_date, '$lte': end_date}
                }
            },
            {'$project': {'_id': 0, 'type': 'sms'}},
            {
                '$unionWith': {
                    'coll': 'whatsapp_sms_activity',
                    'pipeline': [
                        {'$match': {
                            'created_at': {'$gte': start_date, '$lte': end_date}
                        }},
                        {'$project': {'_id': 0, 'type': 'whatsapp'}}
                    ]
                }
            },
            {
                '$unionWith': {
                    'coll': 'activity_email',
                    'pipeline': [
                        {'$match': {
                            'created_at': {'$gte': start_date, '$lte': end_date}
                        }},
                        {'$project': {'_id': 0, 'type': 'email'}}
                    ]
                }
            },
            {'$group': {'_id': '$type', 'count': {'$sum': 1}}}
        ]
        try:
            result = await DatabaseConfiguration().sms_activity.aggregate(pipeline).to_list(None)
        except Exception as e:
            raise CustomError(f"Unable to Connect with the Collections: {e}")
        counts = {doc['_id']: doc['count'] for doc in result}
        sms_count = counts.get('sms', 0)
        whatsapp_count = counts.get('whatsapp', 0)
        email_count = counts.get('email', 0)

        # Calculate costs
        sms_cost = sms_count * PRICELIST['sms']
        whatsapp_cost = whatsapp_count * PRICELIST['whatsapp']
        email_cost = email_count * PRICELIST['email']

        # Total
        grand_total = (
                feature_grand_total +
                sms_cost +
                whatsapp_cost +
                email_cost
        )

        response = {
            'college_id': college_id,
            'college_name': college.get("name"),
            'feature_breakdown': feature_breakdown,
            'feature_grand_total': feature_grand_total,
            'sms_count': sms_count,
            'sms_cost': sms_cost,
            'whatsapp_count': whatsapp_count,
            'whatsapp_cost': whatsapp_cost,
            'email_count': email_count,
            'email_cost': email_cost,
            'grand_total': grand_total
        }
        return json.loads(json.dumps(response, default=str))

    async def get_form_details(self):
        """
        Get form details
        """
        from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache
        form_details = await get_collection_from_cache(collection_name="form_details")
        if form_details:
            data = form_details[0]
        else:
            data = await DatabaseConfiguration().form_details_collection.find_one(
                {})
            await store_collection_in_cache(collection=[data], collection_name="form_details")
        if data:
            data["_id"] = str(data.get("_id"))
        return {"data": data if data else "NA", "message": "Get form details."}

    async def check_college_exist(self, college_id):
        """
        Check college exists or not
        """
        try:
            college = await DatabaseConfiguration().college_collection.find_one(
                {"_id": ObjectId(college_id)}
            )
        except:
            raise HTTPException(
                status_code=422,
                detail="College id must be a 12-byte input or a "
                       "24-character hex string.",
            )
        if not college:
            raise HTTPException(
                status_code=404,
                detail="College not found. " "Make sure college id should be correct.",
            )

    def college_helper(self, college) -> dict:
        """
        Get college details
        """
        key_categories = college.get("key_categories", [])
        if key_categories and isinstance(key_categories, list):
            for _id, data in enumerate(key_categories):
                if data and isinstance(data, dict):
                    key_categories[_id] = \
                        {"index": _id,
                         "category_name": data.get("category_name"),
                         "created_by": data.get("created_by"),
                         "created_by_id": str(data.get("created_by_id")),
                         "created_at": utility_obj.get_local_time(
                             data.get("created_at")) if isinstance(data.get("created_at"),
                                                                   datetime.datetime) else None}

        form_details = DatabaseConfigurationSync(database="master").college_form_details.find_one(
            {"college_id": ObjectId(college.get('_id'))}, {"form_details": 1}
        )
        form_details = form_details.get('form_details') if form_details else {}

        return {
            "id": str(college.get("_id")),
            "associated_client_id": str(college.get("associated_client_id")),
            "name": college.get("name"),
            "address": college.get("address"),
            "integrations": college.get("integrations"),
            "website_url": college.get("website_url"),
            "pocs": college.get("pocs"),
            "subscriptions": college.get("subscriptions"),
            "enforcements": college.get("enforcements"),
            "status_info": {
                key: str(value) for key, value in
                college.get("status_info", {}).items()
            },
            "college_manager_name": college.get("college_manager_name"),
            "extra_fields": college.get("extra_fields"),
            "course_details": college.get("course_details"),
            "is_different_forms": college.get("is_different_forms"),
            "form_details": form_details,
            "charges_details": college.get("charges_details"),
            "status": college.get("status"),
            "background_image": college.get("background_image"),
            "logo": college.get("logo"),
            "email_preferences": {
                key: str(value)
                for key, value in college.get("email_preferences", {}).items()
            } if college.get("email_preferences", {}) else {},
            "features": college.get("features", {}),
            "zoom_credentials": college.get("zoom_credentials", {}),
            "lead_tags": college.get("lead_tags", []),
            "key_categories": key_categories,
            "languages": college.get("languages", []),
            "landing_numbers": college.get("landing_numbers", []),
            "brochure_url": college.get("brochure_url"),
            "campus_tour_video_url": college.get("campus_tour_video_url"),
            "system_preference": college.get("system_preference"),
            "want_student_dashboard": college.get("want_student_dashboard"),
            "thank_you_page_url": college.get("thank_you_page_url"),
            "widget_url": college.get("website_widget_url"),
            "html_url": college.get("website_html_url"),
            "lead_stage_label": college.get("lead_stage_label"),
            "fee_rules": college.get("fee_rules"),
            "email_id_list": college.get("email_id_list", {}),
            "course_categories": college.get("course_categories", []),
            "stage_values": college.get("stage_values"),
            "file_format": college.get("file_format")
        }

    def college_serialize(self, item):
        """
        Get the id and name of college
        """
        return {"id": str(item.get("_id")), "name": item.get("name")}

    async def create_new_college(self, college_data, user,
                                 create_client: bool = True):
        """
        Create new client/college
        """
        if (role := await DatabaseConfiguration().role_collection.find_one(
                {"_id": ObjectId(user["role"]["role_id"])}
        )) is None:
            raise HTTPException(status_code=404,
                                detail="Role details not found")
        if not role.get("permission", {}).get("add_client"):
            raise HTTPException(status_code=401,
                                detail="Not enough permissions")
        else:
            data = await DatabaseConfiguration().component_charges_collection.find_one(
                {}
            )
            if not data:
                data = {}
            college_data["status_info"][
                "creation_date"] = datetime.datetime.utcnow()
            college_data["season_start_datetime"] = datetime.datetime.now()
            charges_per_release = sum(
                [data.get("sms", 0), data.get("email", 0), data.get("sms", 0)]
            )
            college_data["charges_details"] = {
                "lead": (
                    (
                            (
                                    college_data.get("enforcements", {}).get(
                                        "lead_limit", 0)
                                    // 200000
                            )
                            * 100
                    )
                    * charges_per_release
                    if college_data.get("enforcements", {}).get("lead_limit",
                                                                0)
                       > 200000
                    else data.get("lead", 0) * charges_per_release
                ),
                "counselor_account": (
                    (
                            college_data.get("enforcements", {}).get(
                                "counselor_limit", 0)
                            // 15
                    )
                    * 100
                    if college_data.get("enforcements", {}).get(
                        "counselor_limit", 0)
                       > 15
                    else data.get("counselor_account", 0)
                ),
                "client_manager_account": (
                    (
                            college_data.get("enforcements", {}).get(
                                "client_manager_limit", 0
                            )
                            // 4
                    )
                    * 100
                    if college_data.get("enforcements", {}).get(
                        "client_manager_limit", 0
                    )
                       > 4
                    else data.get("client_manager_account", 0)
                ),
                "publisher_account": (
                    (
                            college_data.get("enforcements", {}).get(
                                "publisher_account_limit", 0
                            )
                            // 8
                    )
                    * 100
                    if college_data.get("enforcements", {}).get(
                        "publisher_account_limit", 0
                    )
                       > 8
                    else data.get("publisher_account", 0)
                ),
                "raw_data_module": data.get("raw_data_module", 0),
                "lead_management_system": data.get("lead_management_system",
                                                   0),
                "app_management_system": data.get("app_management_system", 0),
                "per_sms_charge": data.get("sms", 0),
                "per_email_charge": data.get("email", 0),
                "per_whatsapp_charge": data.get("whatsapp", 0),
            }
            college_data.get("charges_details", {}).update(
                {
                    "total_bill": sum(
                        [
                            college_data.get("charges_details", {}).get("lead",
                                                                        0),
                            college_data.get("charges_details", {}).get(
                                "counselor_account", 0
                            ),
                            college_data.get("charges_details", {}).get(
                                "client_manager_account", 0
                            ),
                            college_data.get("charges_details", {}).get(
                                "publisher_account", 0
                            ),
                            data.get("raw_data_module", 0),
                            data.get("lead_management_system", 0),
                            data.get("app_management_system", 0),
                        ]
                    )
                }
            )
            college_data["season_end_datetime"] = college_data[
                                                      "season_start_datetime"
                                                  ] + pd.offsets.DateOffset(
                months=12)
            college_data["name"] = str(college_data["name"]).title()
            college_data["status"] = "Pending"
            client_info = {"client_name": college_data.pop("client_name")
            if college_data.get("client_name") else college_data["name"],
                           "current_season": college_data.pop("current_season")
                           if college_data.get(
                               "current_season") else "Season0",
                           "seasons": college_data.pop("season_info")
                           if college_data.get("season_info") else [],
                           "s3": college_data.pop("aws_s3_credentials")
                           if college_data.get("aws_s3_credentials") else {},
                           "email": college_data.pop("email_credentials")
                           if college_data.get("email_credentials") else {},
                           "sms": college_data.pop("sms_credentials")
                           if college_data.get("sms_credentials") else {},
                           "whatsapp_credential": college_data.pop(
                               "whatsapp_credentials")
                           if college_data.get("whatsapp_credentials") else {},
                           "meilisearch": college_data.pop(
                               "meilisearch_credentials")
                           if college_data.get(
                               "meilisearch_credentials") else {},
                           "report_webhook_api_key": college_data.pop(
                               "report_webhook_api_key")
                           if college_data.get(
                               "report_webhook_api_key") else "",
                           "university": college_data.pop("university_info")
                           if college_data.get("university_info") else {},
                           "aws_textract": college_data.pop(
                               "aws_textract_credentials")
                           if college_data.get(
                               "aws_textract_credentials") else {},
                           "cache_redis": college_data.pop(
                               "redis_cache_credentials")
                           if college_data.get(
                               "redis_cache_credentials") else {},
                           "tawk_secret": college_data.pop("tawk_secret")
                           if college_data.get("tawk_secret") else "",
                           "telephony_secret": college_data.pop(
                               "telephony_secret") if college_data.get(
                               "telephony_secret") else "",
                           "razorpay": college_data.pop("razorpay_credentials")
                           if college_data.get("razorpay_credentials") else {},
                           "client_manager_name": college_data.pop(
                               "client_manager_name")
                           if college_data.get("client_manager_name") else {}
                           }
            create_college = (
                await DatabaseConfiguration().college_collection.insert_one(
                    college_data
                )
            )
            new_college = await DatabaseConfiguration().college_collection.find_one(
                {"_id": create_college.inserted_id}
            )
            if create_client:
                client_info["client_id"] = create_college.inserted_id
                if await DatabaseConfiguration().client_collection.find_one(
                        {"client_name": client_info.get("client_name")}) is None:
                    await DatabaseConfiguration().client_collection.insert_one(
                        client_info)
                client_info.pop("client_id")
            return self.college_helper(new_college)

    async def college_list(
            self, page_num=None, page_size=None, route_name=None, user=None,
            using_for=None
    ):
        """
        Get list of colleges
        """
        colleges = await College().get_college_data(user, using_for=using_for)
        if colleges:
            if page_num and page_size:
                response = await utility_obj.pagination_in_api(
                    page_num, page_size, colleges, len(colleges), route_name
                )
                return {
                    "data": response["data"],
                    "total": len(colleges),
                    "count": page_size,
                    "pagination": response["pagination"],
                    "message": "Colleges data found.",
                }
            return {"data": colleges, "message": "Colleges data found."}
        return False

    async def college_details(self, _id=None, name=None, with_helper=True):
        """
        Get college details using id or name
        """
        if _id:
            await utility_obj.is_id_length_valid(_id=_id, name="College id")
            college = await DatabaseConfiguration().college_collection.find_one(
                {"_id": ObjectId(_id)}
            )
        elif name:
            college = await DatabaseConfiguration().college_collection.find_one(
                {"name": name.title()}
            )
        else:
            return False

        if not college:
            return False

        if with_helper:
            return self.college_helper(college)
        return college

    async def get_colleges_by_client_ids(self, client_ids: list, page: int = None, limit: int = None,
                                         route: str = None) -> list:
        """
        Get College List by list of Client Ids

        Params:
        - client_ids (list): A list containing the clients ids.
        """
        # Validate client_ids
        if not all(ObjectId.is_valid(client_id) for client_id in client_ids):
            raise CustomError(message="Invalid client ids")

        colleges = await DatabaseConfiguration().college_collection.aggregate([
            {
                "$match": {
                    "associated_client_id": {"$in": [ObjectId(client_id) for client_id in client_ids]}
                },
            },
            {
                "$project": {
                    "name": 1,
                    "college_email": 1,
                    "associated_client_id": 1,
                    "address": 1,
                    "mobile_number": 1
                }
            }
        ]).to_list(length=None)
        if page and limit:
            colleges = await utility_obj.pagination_in_api(
                data=colleges,
                data_length=len(colleges),
                page_num=page,
                page_size=limit,
                route_name=route,
            )
        return json.loads(json.dumps(colleges, default=str))

    async def add_csv_file_college_data_into_database(self, csv_data):
        """
        Add csv file college_data into database
        """
        from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache
        payload = json.loads(csv_data.to_json(orient="records"))
        data_list = []
        for i in payload:
            if not i.get("name"):
                raise HTTPException(
                    status_code=400,
                    detail="College name should be exist in csv."
                )
            pocs_name = []
            if i.get("pocs_name"):
                if i.get("pocs_name").find(","):
                    for item in i.get("pocs_name").strip().split(","):
                        pocs_name.append(item)
            pocs_email = []
            if i.get("pocs_email"):
                if i.get("pocs_email").find(","):
                    for item in i.get("pocs_email").strip().split(","):
                        pocs_email.append(item)
            pocs_mobile_number = []
            if i.get("pocs_mobile_number"):
                if str(i.get("pocs_mobile_number")).find(","):
                    for item in str(i.get("pocs_mobile_number")).strip().split(
                            ","):
                        if len(item) == 10:
                            pocs_mobile_number.append(int(item))
                        else:
                            raise HTTPException(
                                status_code=400,
                                detail="Mobile must be 10 digit in csv.",
                            )
            college_manager_name = []
            if i.get("college_manager_name"):
                if i.get("college_manager_name").find(","):
                    for item in i.get("college_manager_name").split(","):
                        college_manager_name.append(item)

            country_code = i.get("country_code")
            if country_code:
                countries = await get_collection_from_cache(collection_name="countries")
                if countries:
                    country = utility_obj.search_for_document(countries, field="name",
                                                              search_name=country_code.strip().title())
                else:
                    country = await DatabaseConfiguration().country_collection.find_one(
                        {"name": country_code.strip().title()}
                    )
                    countries = await DatabaseConfiguration().country_collection.aggregate(
                        []).to_list(None)
                    await store_collection_in_cache(collection=countries,
                                                    collection_name="countries")
                if country:
                    country_code = country.get("iso2")
                else:
                    raise HTTPException(
                        status_code=400, detail="Enter valid country name"
                    )
            state_code = i.get("state_code")
            if state_code:
                states = await get_collection_from_cache(collection_name="states")
                if states:
                    state = await utility_obj.search_for_document_two_field(states,
                                                                            field1="name",
                                                                            field1_search_name=state_code.strip().title(),
                                                                            field2="country_code",
                                                                            field2_search_name=country_code
                                                                            )
                else:
                    state = await DatabaseConfiguration().state_collection.find_one(
                        {"name": state_code.strip().title(),
                         "country_code": country_code}
                    )
                    collection = await DatabaseConfiguration().state_collection.aggregate(
                        []).to_list(None)
                    await store_collection_in_cache(collection, collection_name="states")

                if state:
                    state_code = state.get("state_code")
                else:
                    raise HTTPException(
                        status_code=400, detail="Enter valid state name"
                    )
            city = i.get("city")
            if city:
                found_city = await DatabaseConfiguration().city_collection.find_one(
                    {
                        "name": city.title().strip(),
                        "country_code": country_code,
                        "state_code": state_code,
                    }
                )
                if found_city:
                    city = found_city.get("name")
                else:
                    raise HTTPException(status_code=400,
                                        detail="Enter valid city name")
            if pocs_name == [] and pocs_email == [] and pocs_mobile_number == []:
                pocs = [
                    {"name": None, "pocs_email": None,
                     "pocs_mobile_number": None}
                    for i, j, k in
                    zip(pocs_name, pocs_email, pocs_mobile_number)
                ]
            elif pocs_name == [] and pocs_email == []:
                pocs = [
                    {"name": None, "pocs_email": None, "pocs_mobile_number": k}
                    for i, j, k in
                    zip(pocs_name, pocs_email, pocs_mobile_number)
                ]
            elif pocs_mobile_number == [] and pocs_email == []:
                pocs = [
                    {"name": i, "pocs_email": None, "pocs_mobile_number": k}
                    for i, j, k in
                    zip(pocs_name, pocs_email, pocs_mobile_number)
                ]
            elif pocs_mobile_number == [] and pocs_name == []:
                pocs = [
                    {"name": None, "pocs_email": j, "pocs_mobile_number": None}
                    for i, j, k in
                    zip(pocs_name, pocs_email, pocs_mobile_number)
                ]
            elif not pocs_name:
                pocs = [
                    {"name": None, "pocs_email": j, "pocs_mobile_number": k}
                    for i, j, k in
                    zip(pocs_name, pocs_email, pocs_mobile_number)
                ]
            elif not pocs_email:
                pocs = [
                    {"name": i, "pocs_email": None, "pocs_mobile_number": k}
                    for i, j, k in
                    zip(pocs_name, pocs_email, pocs_mobile_number)
                ]
            elif not pocs_mobile_number:
                pocs = [
                    {"name": i, "pocs_email": j, "pocs_mobile_number": None}
                    for i, j, k in
                    zip(pocs_name, pocs_email, pocs_mobile_number)
                ]
            else:
                pocs = [
                    {"name": i, "pocs_email": j, "pocs_mobile_number": None}
                    for i, j, k in
                    zip(pocs_name, pocs_email, pocs_mobile_number)
                ]
            data = {
                "name": i.get("name").strip().title(),
                "address": {
                    "address_line_1": i.get("address_line_1"),
                    "address_line_2": i.get("address_line_2"),
                    "country_code": country_code,
                    "state_code": state_code,
                    "city": city,
                },
                "website_url": i.get("website_url"),
                "pocs": pocs,
                "subscriptions": {
                    "raw_data_module": i.get("raw_data_module"),
                    "lead_management_system": i.get("lead_management_system"),
                    "app_management_system": i.get("app_management_system"),
                },
                "enforcements": {
                    "lead_limit": i.get("lead_limit"),
                    "counselor_limit": i.get("counselor_limit"),
                    "college_managerLimit": i.get("college_managerLimit"),
                    "publisher_account_limit": i.get(
                        "publisher_account_limit"),
                },
                "leads": {
                    "verification_type": i.get("verification_type"),
                    "lead_api_enabled": i.get("lead_api_enabled"),
                },
                "number_of_forms": i.get("number_of_forms"),
                "integrations": {
                    "with_erp": i.get("with_erp"),
                    "with_3rd_party_app": i.get("with_3rd_party_app"),
                    "with_3rd_party_telephony": i.get(
                        "with_3rd_party_telephony"),
                },
                "status_info": {
                    "is_activated": i.get("is_activated"),
                    "activation_date": i.get("activation_date"),
                    "deactivation_date": i.get("deactivation_date"),
                    "creation_date": i.get("creation_date"),
                },
                "college_manager_name": college_manager_name,
            }
            college = await DatabaseConfiguration().college_collection.find_one(
                {"name": i.get("name").strip().title()}
            )
            if not college:
                await DatabaseConfiguration().college_collection.insert_one(
                    data)
                data_list.append(self.college_helper(data))
        if data_list:
            return data_list
        raise HTTPException(
            status_code=422, detail="Colleges data already exist in database."
        )

    async def get_college_season_list(self, _id=None, name=None):
        """
        Get season list based on college name or id
        """
        if _id:
            await utility_obj.is_id_length_valid(_id=_id, name="College id")
            college = await DatabaseConfiguration().college_collection.find_one(
                {"_id": ObjectId(_id)}
            )
        elif name:
            college = await DatabaseConfiguration().college_collection.find_one(
                {"name": name.title()}
            )
        else:
            return False
        if college:
            all_season_data = college.get("seasons", [])
            seasons_data = [
                (
                    {
                        "season_id": data.get("season_id"),
                        "season_name": data.get("season_name"),
                        "start_date": data.get("start_date"),
                        "end_date": data.get("end_date"),
                        "current_season": True,
                    }
                    if college.get("current_season") == data.get(
                        "season_id")
                    else {
                        "season_id": data.get("season_id"),
                        "season_name": data.get("season_name"),
                        "start_date": data.get("start_date"),
                        "end_date": data.get("end_date"),
                    }
                )
                for data in all_season_data
            ]
            return seasons_data

    async def get_communication_info(self, college_id=None, college_name=None):
        """
        Get communication info of college
        """
        college = None
        if college_id:
            await utility_obj.is_id_length_valid(_id=college_id,
                                                 name="College id")
            college = await DatabaseConfiguration().college_collection.find_one(
                {"_id": ObjectId(college_id)}
            )
        elif college_name:
            college = await DatabaseConfiguration().college_collection.find_one(
                {"name": college_name.title()}
            )
        if college:
            return {
                "email_allocated": (
                    college.get("email_allocated")
                    if college.get("email_allocated")
                    else "NA"
                ),
                "email_consumed": (
                    college.get("email_consumed")
                    if college.get("email_consumed")
                    else "NA"
                ),
                "email_credit_left": (
                    college.get("email_allocated") - college.get(
                        "email_consumed")
                    if (
                            college.get("email_allocated") and college.get(
                        "email_consumed")
                    )
                    else "NA"
                ),
                "sms_allocated": (
                    college.get("sms_allocated")
                    if college.get("sms_allocated")
                    else "NA"
                ),
                "sms_consumed": (
                    college.get("sms_consumed") if college.get(
                        "sms_consumed") else "NA"
                ),
                "sms_credit_left": (
                    college.get("sms_allocated") - college.get("sms_consumed")
                    if (college.get("sms_allocated") and college.get(
                        "sms_consumed"))
                    else "NA"
                ),
                "whatsapp_allocated": (
                    college.get("whatsapp_allocated")
                    if college.get("whatsapp_allocated")
                    else "NA"
                ),
                "whatsapp_consumed": (
                    college.get("whatsapp_consumed")
                    if college.get("whatsapp_consumed")
                    else "NA"
                ),
                "whatsapp_credit_left": (
                    college.get("whatsapp_allocated") - college.get(
                        "whatsapp_consumed")
                    if (
                            college.get("whatsapp_allocated")
                            and college.get("whatsapp_consumed")
                    )
                    else "NA"
                ),
            }, college
        return False, college

    async def get_communication_performance_dashboard(
            self, current_user, release_type, change_indicator
    ):
        """
        Get communication info of college
        """
        await UserHelper().is_valid_user(current_user)
        result = DatabaseConfiguration().communication_log_collection.aggregate(
            [
                {
                    "$group": {
                        "_id": "",
                        "total_communication_sent": {
                            "$push": {
                                "mails": {
                                    "$ifNull": ["$email_summary.email_sent",
                                                0]},
                                "messages": {
                                    "$ifNull": ["$sms_summary.sms_sent", 0]},
                                "whatsapp": {
                                    "$ifNull": [
                                        "$whatsapp_summary.whatsapp_sent", 0]
                                },
                            }
                        },
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "mails": {"$sum": "$total_communication_sent.mails"},
                        "messages": {
                            "$sum": "$total_communication_sent.messages"},
                        "whatsapp": {
                            "$sum": "$total_communication_sent.whatsapp"},
                    }
                },
            ]
        )
        communication_count = {}
        async for document in result:
            communication_count = {
                "total": document.get("mails", 0)
                         + document.get("messages", 0)
                         + document.get("whatsapp", 0),
                "mails": document.get("mails", 0),
                "messages": document.get("messages", 0),
                "whatsapp": document.get("whatsapp", 0),
            }
        if release_type:
            data = {
                "email_details": {
                    "sent": communication_count.get("mails"),
                    "open_rate": 0,
                    "click_rate": 0,
                },
                "sms_details": {
                    "sent": communication_count.get("mails"),
                    "open_rate": 0,
                    "click_rate": 0,
                },
                "whatsapp_details": {
                    "sent": communication_count.get("mails"),
                    "open_rate": 0,
                    "click_rate": 0,
                },
            }
            if change_indicator:
                data.get("email_details").update(
                    {
                        "open_rate_percentage": 0,
                        "open_rate_position": "equal",
                        "click_rate_percentage": 0,
                        "click_rate_position": "equal",
                    }
                )
                data.get("sms_details").update(
                    {
                        "open_rate_percentage": 0,
                        "open_rate_position": "equal",
                        "click_rate_percentage": 0,
                        "click_rate_position": "equal",
                    }
                )
                data.get("whatsapp_details").update(
                    {
                        "open_rate_percentage": 0,
                        "open_rate_position": "equal",
                        "click_rate_percentage": 0,
                        "click_rate_position": "equal",
                    }
                )
        else:
            data = {
                "total_communication_details": {
                    "automated_releases": 0,
                    "manual_releases": 0,
                    "sent": communication_count.get("total"),
                    "automated_releases_percentage": 0,
                    "manual_releases_percentage": 0,
                },
                "email_details": {
                    "automated_releases": 0,
                    "manual_releases": 0,
                    "sent": communication_count.get("mails"),
                    "automated_releases_percentage": 0,
                    "manual_releases_percentage": 0,
                },
                "sms_details": {
                    "automated_releases": 0,
                    "manual_releases": 0,
                    "sent": communication_count.get("messages"),
                    "automated_releases_percentage": 0,
                    "manual_releases_percentage": 0,
                },
                "whatsapp_details": {
                    "automated_releases": 0,
                    "manual_releases": 0,
                    "sent": communication_count.get("whatsapp"),
                    "automated_releases_percentage": 0,
                    "manual_releases_percentage": 0,
                },
            }
        return {
            "data": data,
            "message": "Get communication performance dashboard data.",
        }

    async def get_utm_medium_data_by_source_names(self, current_user,
                                                  source_names):
        """
        Get utm medium data by source names
        """
        await UserHelper().is_valid_user(current_user)
        return {
            "data": await College().get_utm_medium_data_by_source_names(
                source_names),
            "message": "Get utm medium data.",
        }

    async def remove_empty_dicts(self, dictionary: dict) -> dict:
        cleaned_dict = {}
        for key, value in dictionary.items():
            if value is None or value == {}:
                continue
            elif isinstance(value, dict):
                cleaned_value = await self.remove_empty_dicts(value)
                if cleaned_value != {}:
                    cleaned_dict[key] = cleaned_value
            else:
                cleaned_dict[key] = value
        return cleaned_dict

    async def update_features_in_roles(
            self, features: dict, college_id: ObjectId,
            college_col: bool = False
    ):
        from app.dependencies.oauth import cache_invalidation
        for menu, data in features.items():
            for sub_menu, value in data.items():
                if isinstance(value, dict):
                    for sub_menu_option, sub_menu_opt_value in value.items():
                        if await DatabaseConfiguration().role_collection.find_one(
                                {
                                    f"menus.{menu}.{sub_menu}.features."
                                    f"{sub_menu_option}": {"$exists": False}
                                }
                        ):
                            await DatabaseConfiguration().role_collection.update_many(
                                {},
                                {
                                    "$set": {
                                        f"menus.{menu}.{sub_menu}.features."
                                        f"{sub_menu_option}": False
                                    }
                                },
                            )
                        elif sub_menu_opt_value is False:
                            await DatabaseConfiguration().role_collection.update_many(
                                {},
                                {
                                    "$set": {
                                        f"menus.{menu}.{sub_menu}.features."
                                        f"{sub_menu_option}": sub_menu_opt_value
                                    }
                                },
                            )
                        if college_col:
                            if await DatabaseConfiguration().college_collection.find_one(
                                    {
                                        f"features.{menu}.{sub_menu}."
                                        f"{sub_menu_option}": {
                                            "$exists": False}
                                    }
                            ):
                                await DatabaseConfiguration().college_collection.update_one(
                                    {"_id": college_id},
                                    {
                                        "$set": {
                                            f"features.{menu}.{sub_menu}."
                                            f"{sub_menu_option}": sub_menu_opt_value
                                        }
                                    },
                                )
                            else:
                                await DatabaseConfiguration().college_collection.update_one(
                                    {"_id": college_id},
                                    {
                                        "$set": {
                                            f"features.{menu}.{sub_menu}"
                                            f".{sub_menu_option}": sub_menu_opt_value
                                        }
                                    },
                                )
        await cache_invalidation(api_updated="updated_college", user_id=str(college_id))

    async def update_features_in_db(self, features, college) -> None:
        """
        Update features in the db

        params:
        features (dict) - features which want to add/update
        college (dict) - college data in a dict format
        """
        from app.dependencies.oauth import cache_invalidation
        college_id = ObjectId(college.get("id"))
        if await DatabaseConfiguration().college_collection.find_one(
                {"_id": college_id, "features": {"$exists": False}}
        ):
            await DatabaseConfiguration().college_collection.update_one(
                {"_id": college_id}, {"$set": {"features": features}}
            )
            await self.update_features_in_roles(features, college_id)
        else:
            await self.update_features_in_roles(features, college_id,
                                                college_col=True)
        await cache_invalidation(api_updated="updated_college", user_id=college.get("id"))

    async def add_or_update_features(self, current_user, features, college):
        """
        Add or update features
        """
        user = await UserHelper().is_valid_user(current_user)
        if user.get("role", {}).get("role_name") not in [
            "client_manager",
            "super_admin",
        ]:
            raise HTTPException(status_code=401,
                                detail=f"Not enough permissions")
        features = features.dict()
        features = await self.remove_empty_dicts(features)
        if len(features) < 1:
            return {"detail": "There is nothing to update."}
        await self.update_features_in_db(features, college)
        return {"message": "Features updated."}

    async def get_features(self, current_user, college):
        """
        Get features data
        """
        await UserHelper().is_valid_user(current_user)
        return {"features": college.get("features", {}),
                "message": "Features updated."}

    async def verify_college(self, error_message, college_id=None,
                             domain_url=None):
        """
        Verify college based on college_id / domain url
        """
        if college_id:
            await utility_obj.is_id_length_valid(_id=college_id,
                                                 name="College id")
            college = await DatabaseConfiguration().college_collection.find_one(
                {"_id": ObjectId(college_id)}
            )
        elif domain_url:
            college = await DatabaseConfiguration().college_collection.find_one(
                {"dashboard_domain": domain_url}
            )
        else:
            raise HTTPException(status_code=200,
                                detail=error_message.get("detail"))
        return college

    async def terms_and_declaration(self, college_name:str, data_type: Optional[str]=None) -> Union[dict, str, None]:
        """
        Returns the predefined terms and conditions or declaration content for a given college.

        Params:
            college_name (str): The name of the college to be included in the dynamic text.
            data_type (Optional[str]): If provided, should be either 'terms_and_conditions' or 'declaration'.
                                       - If 'terms_and_conditions', returns the list of terms and conditions.
                                       - If 'declaration', returns the declaration text.
                                       - If None, returns both terms and conditions and declaration as a dictionary.

        Returns:
            Union[dict, str, None]:
                - Dictionary containing both terms and declaration if `data_type` is None.
                - String for declaration if `data_type` is 'declaration'.
                - List of terms and conditions if `data_type` is 'terms_and_conditions'.
                - None if an invalid `data_type` is passed.
        """
        data = {
            "terms_and_conditions": [
                {
                    "title": "Instructions for Login ID & PASSWORD:",
                    "content": [
                        f"Candidate is advised not to share their login credentials with anyone. {college_name} "
                        "will not be responsible for the violation or misuse of a candidate's password.",
                        "Candidates should remember to log out at the end of their session so that the details "
                        "cannot be tampered.",
                    ],
                },
                {
                    "title": "The Application Fee can be paid via Debit/ Credit Card/ UPI/ Net Banking/ PAYTM:",
                    "content": [
                        "The candidate has to select the Debit Card/ Credit Card/ UPI/ Net Banking/ e-Wallets option "
                        "to pay the application fee and follow the online instructions to complete the payment of "
                        "the fee. If the confirmation page is not generated after payment of the fee, consider "
                        "the transaction cancelled, and the amount will be refunded within 7 working days. If "
                        "not, the candidate must approach the concerned bank for a refund. However, in such cases, "
                        "the candidate needs to make another transaction to complete the online application process "
                        "if the confirmation page is not generated."
                    ],
                },
                {
                    "title": "Application fees is non-refundable:",
                    "content": [
                        "Application Fees for the program is INR 1000 only, which has been waived for the "
                        "first-session students. The application form shall be considered complete only when "
                        "the payment is received by the institute and all the mandatory fields in the application "
                        f"form are submitted. {college_name} will not be held responsible for any delay in submitting "
                        "complete information or receiving the application fees. Once submitted, changes in the "
                        "application form will NOT be entertained."
                    ],
                },
                {
                    "title": "Eligibility & Selection Process:",
                    "content": [
                        "As per the eligibility mentioned on the official website, a candidate must be eligible "
                        f"to process the application. {college_name} will not be responsible if the candidate is "
                        "not eligible with respect to the applied program as per the information provided in "
                        "the application form."
                    ],
                }
            ],
            "declaration": "I Certify That The Information Submitted By Me In Support Of This Application Is True "
                           "To The Best Of My Knowledge And Belief. I Understand That In The Event Of Any Information "
                           "Being Found False Or Incorrect, My Admission Is Liable To Be Rejected / Cancelled At "
                           "Any Stage Of The Program. I Undertake To Abide By The Disciplinary Rules And "
                           "Regulations Of The Institute."
        }
        if data_type:
            return data.get(data_type, None)
        return data

    async def get_signup_form_extra_fields(self, college_id=None, domain_url=None):
        """
        Get signup form extra fields
        """
        error_message = {
            "detail": "College not found. "
                      "Make sure college_id or domain_url is correct."
        }
        college = await self.verify_college(error_message, college_id,
                                            domain_url)
        if college:
            college_id = college.get("_id")
            from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache
            form_data = await get_collection_from_cache(collection_name="form_data", field=college_id)
            if not form_data:
                form_data = await DatabaseConfiguration().college_form_details.find_one(
                    {"college_id": ObjectId(college_id)}
                )
                if form_data:
                    await store_collection_in_cache(collection=form_data,
                                                    collection_name="form_data", expiration_time=10800,
                                                    field=college_id)

            declaration = college.get("declaration")
            if not declaration:
                declaration = await self.terms_and_declaration(college_name=college.get("name").title(),
                                                               data_type="declaration")

            terms_and_conditions = college.get("terms_and_conditions")
            if not terms_and_conditions:
                terms_and_conditions = await self.terms_and_declaration(college_name=college.get("name").title(),
                                                                        data_type="terms_and_conditions")
            return {
                "data": {
                    "college_id": str(college.get("_id")),
                    "college_logo": college.get("logo"),
                    "background_image": college.get("background_image"),
                    "student_dashboard_design_layout": college.get(
                        "student_dashboard_design_layout"
                    ),
                    "admin_dashboard_design_layout": college.get(
                        "admin_dashboard_design_layout"
                    ),
                    "form": {"student_registration_form_fields": form_data.get("student_registration_form_fields")} if form_data else [],
                    "extra_fields": [
                        field
                        for field in form_data.get(
                            "student_registration_form_fields", []
                        )
                        if field.get("extra_field") is True
                    ],
                    "brochure_url": college.get("brochure_url"),
                    "campus_tour_video_url": college.get("campus_tour_video_url"),
                    "system_preference": college.get("system_preference", {}),
                    "multiple_application_mode": college.get("multiple_application_mode"),
                    "is_country_fixed": college.get("is_country_fixed", False),
                    "widget_mobile_verification": college.get("widget_mobile_verification", False),
                    "terms_and_conditions": terms_and_conditions,
                    "declaration": declaration
                },
                "message": "Get signup form extra fields.",
            }
        return error_message

    async def format_fields_data(self, data):
        """
        Format fields data
        """
        final_data = []
        for item in [
            "student_registration_form_fields",
            "basic_details_form_fields",
            "guardian_details_fields",
            "parent_details_form_fields.father_details_form_fields",
            "parent_details_form_fields.mother_details_form_fields",
            "address_details_fields.address_for_correspondence",
            "address_details_fields.permanent_address",
            "educational_details.graduation_details",
            "educational_details.tenth_details." "tenth_academic_details",
            "educational_details.tenth_details" ".tenth_subject_wise_details",
            "educational_details.twelve_details" ".twelve_academic_details",
            "educational_details.twelve_details" ".twelve_subject_wise_details",
        ]:
            if item in data:
                if item.find(".") != -1:
                    item = item.split(".")
                    if len(item) == 2:
                        temp_list = [
                            {
                                "field_name": dict_info.get("field_name"),
                                "key_name": dict_info.get("key_name"),
                                "field_type": dict_info.get("field_type"),
                            }
                            for dict_info in
                            data.get(item[0], {}).get(item[-1], [])
                        ]
                    else:
                        temp_list = [
                            {
                                "field_name": dict_info.get("field_name"),
                                "key_name": dict_info.get("key_name"),
                                "field_type": dict_info.get("field_type"),
                            }
                            for dict_info in data.get(item[0], {})
                            .get(item[1], [])
                            .get(item[-1], [])
                        ]
                else:
                    temp_list = [
                        {
                            "field_name": dict_info.get("field_name"),
                            "key_name": dict_info.get("key_name"),
                            "field_type": dict_info.get("field_type"),
                        }
                        for dict_info in data.get(item)
                    ]
                final_data.extend(temp_list)

        return final_data

    async def get_existing_fields(self):
        """
        Get existing fields with key_names
        """
        from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache
        field_mapping = await get_collection_from_cache(collection_name="field_mapping")
        if field_mapping:
            fields = field_mapping[0]
        else:
            fields = await DatabaseConfiguration().field_mapping_collection.find_one(
                {})
            await store_collection_in_cache(collection=[fields], collection_name="field_mapping")
        data = []
        if fields:
            data = await self.format_fields_data(fields)
        return {"data": data, "message": "Get existing fields details."}

    async def get_razorpay_info(self, college):
        """
        Fetches the college from the database and returns the Razorpay info.

        Params:
        college: A dictionary representing college information.

        Returns:
        tuple: A tuple containing the Razorpay account details.
        - x_razorpay_account (str): The Razorpay account ID.
        - client_id (str): The client ID for Razorpay.
        - client_secret (str): The client secret for Razorpay.
        - is_partner (bool): A flag indicating whether the college is a
            partner.
        """
        if (
                college_details := await DatabaseConfiguration().college_collection.find_one(
                    {"_id": ObjectId(college.get("id"))}
                )) is None:
            raise HTTPException(status_code=404,
                                detail="College details not found.")
        razorpay_credentials = college_details.get("razorpay", {})

        x_razorpay_account = razorpay_credentials.get("x_razorpay_account", "")
        client_id = razorpay_credentials.get("razorpay_api_key", "")
        client_secret = razorpay_credentials.get("razorpay_secret", "")
        is_partner = razorpay_credentials.get("partner", False)

        return x_razorpay_account, client_id, client_secret, is_partner

    async def razorpay_header_update_partner(self, college: dict) -> tuple:
        """
        If the college is partner then update the header with
           x-razorpay-account.

        Params:
           - college (dict): A dictionary representing college information.

         Returns:
           tuple: A tuple containing the updated headers and Razorpay account
               details.
           - headers (dict): A dictionary containing the HTTP headers.
           - x_razorpay_account (str): The Razorpay account ID.
           - client_id (str): The client ID for Razorpay.
           - client_secret (str): The client secret for Razorpay.
        """

        headers = {"Content-Type": "application/json"}
        x_razorpay_account, client_id, client_secret, is_partner = (
            await CollegeHelper().get_razorpay_info(college)
        )
        if is_partner:
            headers.update({"X-Razorpay-Account": x_razorpay_account})

        return headers, x_razorpay_account, client_id, client_secret

    async def get_extra_filter_fields(self, college_id=None, domain_url=None):
        """
        Get extra filter fields based on college id / domain url
        """
        error_message = {
            "detail": "College not found. "
                      "Make sure college_id or domain_url is correct."
        }
        college = await self.verify_college(error_message, college_id,
                                            domain_url)
        if college:
            form_details = await College().fetch_form_details(college.get('_id'))
            return {
                "data": [
                    field
                    for field in form_details.get(
                        "student_registration_form_fields", []
                    )
                    if field.get("extra_field") is True
                       and field.get("field_type") == "select"
                ],
                "message": "Get extra filter fields.",
            }
        return error_message

    async def get_school_names(self, current_user) -> dict:
        """
        Get school names.

        Params:
            current_user (str): An user_name of current user.
        Returns:
            dict: A dictionary which contains school names info.
        """
        school_names = await Course().get_courses_data_by_school_names()
        return {"message": "Get school names", "data": school_names}

    def get_current_season_year(self, college_id: str):
        """
        Get current season year.
        """
        current_season = None
        if (
                client_data := DatabaseConfigurationSync(
                    "master"
                ).college_collection.find_one(
                    {"_id": ObjectId(college_id)})
        ) is None:
            raise HTTPException(status_code=404, detail="college not found")
        all_season_data = client_data.get("seasons", [])
        try:
            for data in all_season_data:
                if client_data.get("current_season") == data.get("season_id"):
                    season_name: str = data.get("season_name", "")
                    season_split_val = season_name.split("-")
                    if len(season_split_val) >= 2:
                        season_split_val[-1] = season_split_val[-1][-2:]
                        current_season = "-".join(season_split_val)
        except Exception:
            pass
        return current_season

    async def delete_features(self, features: list[dict], college: dict) -> dict:
        """
        Delete features for a college by college id.

        Params:
            - college_id (str): An unique identifier of a college.
                e.g., 123456789012345678901234
            - features (list): A list which contains information about delete feature.
                e.g., [{"menu_name": {"sub_menu_name": []}}]

        Returns:
            - dict: A dictionary which contains information about delete feature.
        """
        feature_delete = False
        college_id = ObjectId(college.get("id"))
        if await DatabaseConfiguration().college_collection.find_one(
                {"_id": college_id, "features": {"$exists": False}}
        ):
            return {"detail": f"Feature not found."}
        for feature_info in features:
            for menu_name, sub_menu_info in feature_info.items():
                if await DatabaseConfiguration().college_collection.find_one(
                        {"_id": college_id, f"features.{menu_name}": {"$exists": False}}
                ):
                    return {"detail": f"Menu `{menu_name}` not found."}
                if isinstance(sub_menu_info, dict):
                    for sub_menu_name, delete_features in sub_menu_info.items():
                        if await DatabaseConfiguration().college_collection.find_one(
                                {"_id": college_id,
                                 f"features.{menu_name}.{sub_menu_name}": {"$exists": False}}
                        ):
                            return {
                                "detail": f"Sub menu `{sub_menu_name}` not found inside menu `{menu_name}`."}
                        if isinstance(delete_features, list):
                            deletes = []
                            for feature_name in delete_features:
                                deletes.extend([
                                    DatabaseConfiguration().college_collection.update_one(
                                        {"_id": college_id},
                                        {"$unset": {
                                            f"features.{menu_name}.{sub_menu_name}.{feature_name}": True}}),
                                    DatabaseConfiguration().role_collection.update_many(
                                        {}, {"$unset": {
                                            f"menus.{menu_name}.{sub_menu_name}.features.{feature_name}": True}})])
                            if deletes:
                                await asyncio.gather(*deletes)
                                feature_delete = True
                        else:
                            return {"detail": f"Deleted features should be in the list format."}
                else:
                    return {"detail": "Sub menu information should be in the dictionary format."}
        if feature_delete:
            from app.dependencies.oauth import cache_invalidation
            await cache_invalidation(api_updated="updated_college", user_id=college.get("id"))
            return {"message": "Feature deleted."}
        return {"detail": "Feature not deleted."}

    async def get_utm_campaign_data(self, payload: list) -> dict:
        """
        Get utm campaign data based on payload.

        Params:
            - payload (list): A list which contains dictionaries of source name and utm medium name.
                e.g., [{"source_name": "organic", "utm_medium": "test"}]

        Returns:
            - dict: A dictionary which contains information about campaign list along with message.
        """
        return {
            "data": await College().get_utm_campaign_data(payload),
            "message": "Get utm campaign data."
        }

    async def set_college_urls(self, college: dict, urls: dict) -> dict:
        # Todo: Check this Again when it is Finalised for Deployment which is to be Confirmed yet
        """
        This function is used to set college urls, As Discussed most probably this will be used
        by Teamcity for Giving URLs after Deployment

        Params:
            - college_id (str): An unique identifier of a college.
            - student_dashboard_url (str): URL of student dashboard.
            - admin_dashboard_url (str): URL of admin dashboard.

        Returns:
            - dict: A dictionary which contains information about urls.

        Raises:
            - CustomError: If college id is invalid
        """
        # Updating URLs
        await DatabaseConfiguration().college_collection.update_one(
            {"_id": ObjectId(college.get("id"))},
            {"$set": urls}
        )

        return {
            "message": "URLs Updated Successfully"
        }

    async def fetch_form_tabs_and_fields(self, college_id: str,
                                         student_id: str,
                                         course_id: str | None = None,
                                         step_id: str | None = None
                                         ) -> dict:
        """
        Fetch application form stages or specific stage details for a given college and course.

        This method performs the following:
        - Validates the length of the provided college ID.
        - Verifies that the given college ID and course ID combination exists.
        - If `step_id` is provided, fetches detailed information of that specific application form step.
        - If `step_id` is not provided, returns the list of all application form steps with their IDs and names.

        Params:
            college_id (str): The unique identifier of the college.
            student_id (str): The unique identifier of the student.
            course_id (str): The unique identifier of the course.
            step_id (str, optional): The ID of a specific application form step to fetch.

        Returns:
            dict: A dictionary containing a success message and the requested data.

        Raises:
            HTTPException:
                - 400: If the college ID or course ID is invalid.
                - 404: If no relevant form data is found for the provided input.
        """
        await utility_obj.is_id_length_valid(_id=college_id, name="College Id")
        college = await DatabaseConfiguration().college_collection.find_one(
            {"_id": ObjectId(college_id)})

        if not college:
            raise HTTPException(status_code=404, detail="College not found")

        fetch_type = college.get("fetch_form_data_through", "college_wise")
        match_stage = {
            "college_id": ObjectId(college_id),
            "dashboard_type": "college_student_dashboard"
        }

        if fetch_type == "course_wise":
            if not course_id:
                raise HTTPException(status_code=400,
                                    detail="Form retrieval failed. Expected course_id for course-wise form access.")
            await utility_obj.is_id_length_valid(_id=course_id, name="Course Id")
            if not await DatabaseConfiguration().course_collection.find_one(
                    {"_id": ObjectId(course_id), "college_id": ObjectId(college_id)}):
                raise HTTPException(status_code=404, detail="Course not found")
            match_stage["course_id"] = ObjectId(course_id)

        if step_id:
            pipeline = [
                {"$match": match_stage},
                {
                    "$project": {
                        "application_form": {
                            "$filter": {
                                "input": "$application_form",
                                "as": "step",
                                "cond": {"$eq": ["$$step.step_id", step_id]}
                            }
                        }
                    }
                },
                {"$unwind": "$application_form"},
                {"$replaceRoot": {"newRoot": "$application_form"}}
            ]
            result = await DatabaseConfiguration().college_form_details.aggregate(pipeline).to_list(
                length=1)
            if not result:
                raise HTTPException(
                    status_code=404,
                    detail=f"No form data found for Step {step_id} in the application form. Please verify the Step ID."
                )
            return {
                "message": "Stage data fetched successfully.",
                "data": result[0]
            }

        pipeline = [
            {"$match": match_stage},
            {
                "$project": {
                    "_id": 0,
                    "application_form": {
                        "$map": {
                            "input": "$application_form",
                            "as": "step",
                            "in": {
                                "step_id": {"$ifNull": ["$$step.step_id", ""]},
                                "step_name": "$$step.step_name"
                            }
                        }
                    }
                }
            }
        ]

        result = await DatabaseConfiguration().college_form_details.aggregate(pipeline).to_list(
            length=1)
        application = await DatabaseConfiguration().studentApplicationForms.find_one({
            "student_id": ObjectId(student_id),
            "course_id": ObjectId(course_id)
        })
        percent = 0
        if application:
            percent = (application.get("current_stage", 0)) * 10
        if not result:
            raise HTTPException(
                status_code=404,
                detail="No application stages found for the provided college. "
                       "Please verify the college ID and try again.")
        return {
            "message": "Application stages fetched successfully.",
            "form_data": result[0],
            "percent": percent
        }

    async def get_college_urls(self, college_id: str) -> dict:
        # Todo: Check this Again when it is Finalised for Deployment which is to be Confirmed yet
        """
        This function is used to get college urls.

        Params:
            - college_id (str): An unique identifier of a college.

        Returns:
            - student_dashboard_url (str): URL of student dashboard.
            - admin_dashboard_url (str): URL of admin dashboard.

        Raises:
            - CustomError: If college id is invalid
            - DataNotFoundError: If college not found
        """
        # validate college id
        if not ObjectId.is_valid(college_id):
            raise CustomError(message="Invalid College Id")

        # get college details
        college = await DatabaseConfiguration().college_collection.find_one(
            {
                "_id": ObjectId(college_id)
            }
        )

        # raise error if college not found
        if not college:
            raise DataNotFoundError(message="College")

        return {
            "student_dashboard_url": college.get("dashboard_domain"),
            "admin_dashboard_url": college.get("admin_dashboard_url")
        }

    async def fetch_additional_upload_fields(self, client_id: str | None = None, college_id: str | None = None,
                                             course_id: str | None = None) -> dict:
        """
        Fetch additional upload fields based on client, college, and optionally course.

        This method retrieves additional upload field requirements either at the client level
        or at the college/course level, depending on the parameters provided.

        Params:
            client_id (str, optional): The unique identifier for the client.
                                       If provided, fetches upload fields at the client level.
            college_id (str, optional): The unique identifier for the college.
                                        If provided, fetches upload fields at the college or course level.
            course_id (str, optional): The unique identifier for the course.
                                       Required if the college fetch type is course-wise.

        Returns:
            dict: A dictionary containing the list of additional upload fields.

        Raises:
            HTTPException:
                - 400: If required parameters are missing or invalid.
                - 404: If the client, college, or course is not found, or if no upload fields are configured.
                - 500: For any unexpected internal errors.
        """

        if client_id:
            await utility_obj.is_id_length_valid(_id=client_id, name="Client Id")
            pipeline = [
                {
                    "$match": {
                        "_id": ObjectId(client_id)
                    }

                },
                {
                    "$lookup": {
                        "from": "application_form_details",
                        "let": {"client_id": "$_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {"$eq": ["$client_id", "$$client_id"]},
                                    "dashboard_type": "client_student_dashboard"
                                }
                            },
                            {
                                "$project": {
                                    "additional_upload_fields": {"$ifNull": ["$additional_upload_fields", []]},
                                    "_id": 0
                                }
                            }
                        ],
                        "as": "additional_uploads"
                    }
                }
            ]
            client_data = await DatabaseConfiguration().client_collection.aggregate(pipeline).to_list(None)
            if not client_data:
                raise HTTPException(status_code=404, detail="Client not found")
            client_data = client_data[0]
            if not client_data.get("additional_uploads"):
                raise HTTPException(status_code=404, detail="No additional upload fields found for the client")
            return {
                "additional_uploads": client_data.get("additional_uploads", [])[0].get("additional_upload_fields", [])}

        elif college_id:
            await utility_obj.is_id_length_valid(_id=college_id, name="College Id")
            college = await DatabaseConfiguration().college_collection.find_one(
                {"_id": ObjectId(college_id)})

            if not college:
                raise HTTPException(status_code=404, detail="College not found")

            fetch_type = college.get("fetch_form_data_through", "college_wise")
            match_stage = {
                "college_id": ObjectId(college_id),
                "dashboard_type": "college_student_dashboard"
            }
            if fetch_type == "course_wise":
                if not course_id:
                    raise HTTPException(status_code=400,
                                        detail="Form retrieval failed. Expected course_id for course-wise form access.")
                await utility_obj.is_id_length_valid(_id=course_id, name="Course Id")
                if not await DatabaseConfiguration().college_course_collection.find_one(
                        {"_id": ObjectId(course_id), "college_id": ObjectId(college_id)}):
                    raise HTTPException(status_code=404, detail="Course not found")
                match_stage["course_id"] = ObjectId(course_id)
            additional_uploads = await DatabaseConfiguration().college_form_details.aggregate(
                [{"$match": match_stage}]).to_list(None)
            if not additional_uploads:
                raise HTTPException(status_code=404, detail="No additional upload fields found for the college")
            return {
                "additional_uploads": additional_uploads[0].get("additional_upload_fields", [])}

        else:
            raise HTTPException(status_code=400, detail="Either client id or college id must be provided")

    async def get_all_colleges(self, user: User, page_num: int = None, page_size: int = None):
        """

        """
        pipeline = [
            {
                "$lookup": {
                    "from": "client_configurations",
                    "localField": "associated_client_id",
                    "foreignField": "_id",
                    "as": "client"
                }
            },
            {
                "$unwind": {
                    "path": "$client",
                    "preserveNullAndEmptyArrays": True
                }
            }
        ]
        if user.get("user_type") == "account_manager":
            pipeline.append({"$match": {"client.assigned_account_managers": {"$in": [ObjectId(user.get("_id"))]}}})
        elif user.get("user_type") == "super_account_manager":
            account_managers = user.get("assigned_account_managers") or []
            account_managers = [ObjectId(account_manager.get("account_manager_id")) for account_manager in
                                account_managers]
            pipeline.append({"$match": {"client.assigned_account_managers": {"$in": account_managers}}})
        elif user.get("user_type") == "client_admin":
            pipeline.append({"$match": {"client._id": {"$in": [ObjectId(user.get("associated_client"))]}}})

        pipeline.extend([
            {
                "$lookup": {
                    "from": "onboarding_details",
                    "localField": "_id",
                    "foreignField": "college_id",
                    "as": "onboarding_details"
                }
            },
            {
                "$unwind": {
                    "path": "$onboarding_details",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$sort": {
                    "onboarding_details.created_at": -1
                }
            },
            {"$project": {
                "college_id": {"$toString": "$_id"},
                "name": {"$ifNull": ["$name", ""]},
                "college_email": {"$ifNull": ["$college_email", ""]},
                "mobile_number": {"$ifNull": ["$mobile_number", ""]},
                "client_id": {"$toString": "$associated_client_id"},
                "assigned_account_managers": "$client.assigned_account_managers",
                "address": 1,
                "created_at": 1,
                "updated_at": 1,
                "current_season": 1,
                "onboarding_status": {"$ifNull": ["$onboarding_details.status", ""]}
            }},
        ])
        if page_size and page_num:
            skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
            pipeline.append(
                {
                    "$facet": {
                        "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                        "totalCount": [{"$count": "count"}],
                    }
                }
            )
        result = await DatabaseConfiguration().college_collection.aggregate(pipeline).to_list(length=None)
        if page_size and page_num:
            result = result[0] if result else {}
            colleges = result.get("paginated_results", [])
            colleges = json.loads(json.dumps(colleges, default=str))
            return (
                colleges,
                (
                    result.get("totalCount", [{}])[0].get("count", 0)
                    if result.get("totalCount")
                    else 0
                ),
            )
        else:
            result = json.loads(json.dumps(result, default=str))
            return result, len(result)

    async def validate_user(self, user, client_id, college_id):
        """

        """
        pipeline = []
        match = {}
        if user.get("user_type") == "account_manager":
            match = {"assigned_account_managers": {"$in": [ObjectId(user.get("_id"))]}}
        elif user.get("user_type") == "super_account_manager":
            account_managers = user.get("assigned_account_managers") or []
            account_managers = [ObjectId(account_manager.get("account_manager_id")) for account_manager in
                                account_managers]
            match = {"assigned_account_managers": {"$in": account_managers}}
        if client_id:
            match.update({"client_id": ObjectId(client_id)})
        if college_id:
            college = await DatabaseConfiguration().college_collection.find_one({"_id": ObjectId(college_id)})
            associated_client = college.get("associated_client_id")
            match.update({"client_id": ObjectId(associated_client)})
        results = await DatabaseConfiguration().client_collection.aggregate([
            {"$match": match}
        ]).to_list(None)
        if results:
            return True
        return False

    async def get_onboarding_details(self, current_user, client_id, college_id):
        """

        """
        validated = self.validate_user(current_user, client_id, college_id)
        if not validated:
            raise CustomError(message="Not Authorized!")
        match = {}
        if client_id:
            match.update({
                "client_id": ObjectId(client_id)
            })
        if college_id:
            match.update({
                "college_id": ObjectId(college_id)
            })
        pipeline = [
            {
                "$match": match
            },
            {
                '$project': {
                    'college_id': {
                        '$toString': '$college_id'
                    },
                    'client_id': {
                        '$toString': '$client_id'
                    },
                    'status': 1,
                    'steps_array': {
                        '$map': {
                            'input': {
                                '$objectToArray': '$steps'
                            },
                            'as': 'step',
                            'in': {
                                'label': {
                                    '$concat': [
                                        {
                                            '$toUpper': {
                                                '$substrCP': [
                                                    {
                                                        '$arrayElemAt': [
                                                            {
                                                                '$split': [
                                                                    '$$step.k', '_'
                                                                ]
                                                            }, 0
                                                        ]
                                                    }, 0, 1
                                                ]
                                            }
                                        }, {
                                            '$substrCP': [
                                                {
                                                    '$arrayElemAt': [
                                                        {
                                                            '$split': [
                                                                '$$step.k', '_'
                                                            ]
                                                        }, 0
                                                    ]
                                                }, 1, {
                                                    '$strLenCP': {
                                                        '$arrayElemAt': [
                                                            {
                                                                '$split': [
                                                                    '$$step.k', '_'
                                                                ]
                                                            }, 0
                                                        ]
                                                    }
                                                }
                                            ]
                                        }, {
                                            '$cond': [
                                                {
                                                    '$gt': [
                                                        {
                                                            '$size': {
                                                                '$split': [
                                                                    '$$step.k', '_'
                                                                ]
                                                            }
                                                        }, 1
                                                    ]
                                                }, {
                                                    '$reduce': {
                                                        'input': {
                                                            '$slice': [
                                                                {
                                                                    '$split': [
                                                                        '$$step.k', '_'
                                                                    ]
                                                                }, 1, 10
                                                            ]
                                                        },
                                                        'initialValue': '',
                                                        'in': {
                                                            '$concat': [
                                                                '$$value', ' ', {
                                                                    '$concat': [
                                                                        {
                                                                            '$toUpper': {
                                                                                '$substrCP': [
                                                                                    '$$this', 0, 1
                                                                                ]
                                                                            }
                                                                        }, {
                                                                            '$substrCP': [
                                                                                '$$this', 1, {
                                                                                    '$subtract': [
                                                                                        {
                                                                                            '$strLenCP': '$$this'
                                                                                        }, 1
                                                                                    ]
                                                                                }
                                                                            ]
                                                                        }
                                                                    ]
                                                                }
                                                            ]
                                                        }
                                                    }
                                                }, ''
                                            ]
                                        }
                                    ]
                                },
                                'status': '$$step.v.status',
                                'request_of': '$$step.v.request_of',
                                'requested_by': '$$step.v.requested_by',
                                'requested_id': '$$step.v.requested_id',
                                'updated_at': '$$step.v.updated_at',
                                'reason_to_reject': '$$step.v.reason_to_reject'
                            }
                        }
                    }
                }
            }
            ]
        results = await DatabaseConfiguration().onboarding_details.aggregate(pipeline).to_list(None)
        results = results[0] if results else {}
        clients = json.loads(json.dumps(results, default=str))
        return clients
