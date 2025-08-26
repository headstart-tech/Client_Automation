"""
This file contain class and functions related to college which useful for background tasks
"""
from bson import ObjectId

from app.core.custom_error import DataNotFoundError
from app.database.configuration import DatabaseConfiguration


class College:
    """
    Contain functions related to college activities
    """

    async def fetch_form_details(self, college_id):
        """
            Fetches the form details for a given college ID.
            Params:
                college_id (str): The ID of the college as a string.
            Returns:
                dict: A dictionary containing the form details if found, otherwise an empty dictionary.
        """
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
        return form_data.get("form_details", {}) if form_data else {}

    async def get_college_data(self, user, using_for=None):
        """
        Get colleges data
        """
        pipeline = [
            {
                "$lookup": {
                    "from": "client_configurations",
                    "let": {"client_ids": {"$ifNull": ["$assigned_clients.client_id", []]}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$in": ["$_id", "$$client_ids"]
                                }
                            }
                        }
                    ],
                    "as": "client_details"
                }
            },
            {"$unwind": "$client_details"},

            {
                "$lookup": {
                    "from": "colleges",
                    "localField": "client_details.college_ids",
                    "foreignField": "_id",
                    "as": "college_details"
                }
            },
            {"$unwind": "$college_details"},
            {
                "$group": {
                    "_id": "$college_details._id",
                    "college": {"$first": "$college_details"}
                }
            },
            {
                "$replaceRoot": {"newRoot": "$college"}
            }
        ]
        if user.get('role', {}).get('role_name') in ["super_admin", "admin"]:
            result = DatabaseConfiguration().college_collection.aggregate([])
        elif user.get('role', {}).get('role_name') == "super_account_manager":
            pipeline.insert(0, {"$match": {
                "associated_super_account_manager": ObjectId(user.get("_id"))}})
            result = DatabaseConfiguration().user_collection.aggregate(pipeline)
        elif user.get('role', {}).get('role_name') == "account_manager":
            pipeline.insert(0, {"$match": {
                "_id": ObjectId(user.get("_id"))}})
            result = DatabaseConfiguration().user_collection.aggregate(pipeline)
        elif user.get('role', {}).get('role_name') in ["client_manager", "client_admin"]:
            pipeline = [
                {
                    "$match": {
                        "client_id": ObjectId(user.get("_id")),
                    }
                },
                {
                    "$lookup": {
                        "from": "colleges",
                        "localField": "college_ids",
                        "foreignField": "_id",
                        "as": "college_details"
                    }
                },
                {"$unwind": "$college_details"},
                {
                    "$group": {
                        "_id": "$college_details._id",
                        "college": {"$first": "$college_details"}
                    }
                },
                {
                    "$replaceRoot": {"newRoot": "$college"}
                }
            ]
            result = DatabaseConfiguration().client_collection.aggregate(pipeline)
        else:
            if user.get("associated_colleges") is None:
                raise DataNotFoundError("College")
            user["associated_colleges"] = [ObjectId(_id) for _id in
                                           user.get("associated_colleges", [])]
            pipeline = [
                {
                    "$match": {
                        "_id": {"$in": user.get("associated_colleges", [])}
                    }
                }
            ]
            result = DatabaseConfiguration().college_collection.aggregate(pipeline)
        if using_for:
            return [{
                "id": str(document.get("_id")),
                "name": document.get("name"),
                "system_preference": document.get("system_preference")}
                async for document in result]
        else:
            return [{
                "id": str(document.get("_id")),
                "name": document.get("name"),
                "address": document.get("address"),
                "website_url": document.get("website_url"),
                "pocs": document.get("pocs"),
                "subscriptions": document.get("subscriptions"),
                "enforcements": document.get("enforcements"),
                "status_info": document.get("status_info"),
                "charges_per_release": document.get("charges_per_release"),
                "college_manager_name": document.get("college_manager_name"),
                "extra_fields": document.get("extra_fields"),
                "course_details": document.get("course_details"),
                "is_different_forms": document.get("is_different_forms"),
                "form_details": await self.fetch_form_details(document.get("_id")),
                "charges_details": document.get("charges_details"),
                "status": document.get("status"),
                "background_image": document.get("background_image"),
                "logo": document.get("logo"),
                "system_preference": document.get("system_preference")
            } async for document in result]

    async def get_colleges_by_status(self, approved, declined, pending,
                                     own_colleges, user):
        """
        Get colleges data by status
        """
        status = []
        if approved:
            status.append("Approved")
        if declined:
            status.append("Declined")
        if pending:
            status.append("Pending")
        pipeline = [{"$match": {"status": {"$in": status}}},
                    {"$sort": {"status_info.creation_date": -1}}]
        if own_colleges:
            pipeline[0].get("$match").update(
                {"client_manager_id": user.get('_id')})
        pipeline.extend([{
            "$lookup": {
                "from": "client_configurations",
                "localField": "_id",
                "foreignField": "client_id",
                "as": "client_configurations_info",
            }
        },
            {
                '$lookup': {
                    'from': 'application_form_details',
                    'localField': '_id',
                    'foreignField': 'college_id',
                    'as': 'application_form_details'
                }
            },
            {
                "$addFields": {
                    "client_configurations_info": {
                        "$arrayElemAt": [
                            "$client_configurations_info", 0
                        ]
                    },
                    'application_form_details': {
                        '$arrayElemAt': [
                            '$application_form_details', 0
                        ]
                    }
                }
            },
            {"$project": {
                "_id": 0,
                "id": {"$toString": "$_id"},
                "name": "$name",
                "address": "$address",
                "website_url": "$website_url",
                "pocs": "$pocs",
                "subscriptions": "$subscriptions",
                "enforcements": "$enforcements",
                "status_info": "$status_info",
                "charges_per_release": "$charges_per_release",
                "college_manager_name": "$college_manager_name",
                "extra_fields": "$extra_fields",
                "course_details": "$course_details",
                "is_different_forms": "$is_different_forms",
                'form_details': '$application_form_details.form_details',
                "charges_details": "$charges_details",
                "status": "$status",
                "background_image": "$background_image",
                "logo": "$logo",
                "school_names": "$school_names",
                "lead_stage_label": "$lead_stage_label",
                "lead_tags": "$lead_tags",
                "tawk_secret": "$client_configurations_info.tawk_secret",
                "telephony_secret": "$client_configurations_info.telephony_secret",
                "report_webhook_api_key": "$client_configurations_info.report_webhook_api_key",
                "meilisearch_credentials": "$client_configurations_info.meilisearch",
                "university_info": "$client_configurations_info.university",
                "razorpay_credentials": "$client_configurations_info.razorpay",
                "aws_s3_credentials": "$client_configurations_info.s3",
                "redis_cache_credentials": "$client_configurations_info.cache_redis",
                "aws_textract_credentials": "$client_configurations_info.aws_textract",
                "email_credentials": "$client_configurations_info.email",
                "sms_credentials": "$client_configurations_info.sms",
                "whatsapp_credentials": "$client_configurations_info.whatsapp_credential",
                "current_crm_usage": "$current_crm_usage",
                "name_of_current_crm": "$name_of_current_crm",
                "old_data_migration": "$old_data_migration",
                "brochure_url": "$brochure_url",
                "campus_tour_video_url": "$campus_tour_video_url",
                "website_html_url": "$website_html_url",
                "google_tag_manager_id": "$google_tag_manager_id",
                "project_title": "$project_title",
                "project_meta_description": "$project_meta_description",
                "thank_you_page_url": "$thank_you_page_url",
                "favicon_url": "$favicon_url",
                "fee_rules": "$fee_rules",
                "multiple_application_mode": "$multiple_application_mode",
                "system_preference": "$system_preference",
                "dashboard_domain": "$dashboard_domain"
            }}
        ])
        result = await DatabaseConfiguration().college_collection.aggregate(
            pipeline).to_list(None)
        return result if result else []

    async def get_colleges_estimation_bill_data(self):
        """
        Get colleges estimation bill data
        """
        result = DatabaseConfiguration().college_collection.aggregate(
            [{'$match': {"charges_details": {"$exists": True}}}])
        return [{
            "id": str(document.get("_id")),
            "name": document.get("name"),
            "charges_details": document.get('charges_details')
        } async for document in result]

    async def get_utm_medium_data_by_source_names(self, source_names):
        """
        Get utm medium data by source names
        """
        result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            [{'$match': {"source.primary_source.utm_source": {
                "$in": [str(x).lower() for x in source_names]}}},
                {
                    "$group": {
                        "_id": {
                            "source_name": "$source.primary_source.utm_source",
                            "medium_name": "$source.primary_source.utm_medium"
                        }
                    }
                }
            ])
        return [{
            "label": document.get("_id", {}).get("medium_name"),
            "value": {"source": document.get("_id", {}).get("source_name"),
                      "utm_medium": document.get("_id", {}).get(
                          "medium_name")},
            "role": document.get("_id", {}).get("source_name")
        } async for document in result
            if document.get("_id", {}).get("medium_name") not in ["", None]]

    async def get_utm_campaign_data(self, payload: list) -> list:
        """
        Get utm campaign data based on payload.

        Params:
            - payload (list): A list which contains dictionaries of source name and utm medium name.
                e.g., [{"source_name": "organic", "utm_medium": "test"}]

        Returns:
            - list: A list which contains information about campaigns.
        """
        result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            [{'$match': {"$or": [
                {
                    "source.primary_source.utm_source": dict(temp_data).get(
                        "source_name"
                    ),
                    "source.primary_source.utm_medium": dict(temp_data).get(
                        "utm_medium"
                    ),
                }
                for temp_data in payload
            ], "source.primary_source.utm_campaign": {"$nin": ["", None]}}},
                {
                    "$group": {
                        "_id": {
                            "source_name": "$source.primary_source.utm_source",
                            "medium_name": "$source.primary_source.utm_medium",
                            "campaign_name": "$source.primary_source.utm_campaign"
                        }
                    }
                }
            ])
        return [{
            "label": document.get("_id", {}).get("campaign_name"),
            "value": {"source": document.get("_id", {}).get("source_name"),
                      "utm_medium": document.get("_id", {}).get(
                          "medium_name"),
                      "utm_campaign": document.get("_id", {}).get(
                          "campaign_name")
                      },
            "role": document.get("_id", {}).get("source_name")
        } async for document in result]
