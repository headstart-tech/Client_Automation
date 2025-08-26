"""
This file contains functions of the colleges routes
"""
from datetime import datetime

from bson import ObjectId

from app.core.custom_error import CustomError
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import cache_invalidation
from app.helpers.approval.approval_helper import ApprovalCRUDHelper, ApprovedRequestHandler


class CollegeRout:

    async def store_general_additional_details(
        self,
        payload: dict,
        college_id: str,
        approval_id: str | None = None,
        user: dict = None,
    ):
        """
        Store additional details of the college route

        Param:
            payload: Get the general details of the colleges from the user
            college_id: Get the college id of the current college

        Return:
            A success massage
        """
        old_payload = payload.copy()
        if not payload:
            raise CustomError(message="General addition details required")
        college_details = await DatabaseConfiguration().college_collection.find_one(
            {"_id": ObjectId(college_id)}
        )
        lead_temp = {}
        data = {}
        if payload.get("lead_stages", []):
            lead_stage = payload.pop("lead_stages")
            for lead in lead_stage:
                if lead.get("stage_name"):
                    lead_temp.update(
                        {lead.get("stage_name"): lead.get("sub_lead_stage", [])}
                    )
            data.update({"lead_stages": lead_temp})
        if payload.get("lead_tags"):
            lead_tag = payload.pop("lead_tags", [])
            data.update({"lead_tags": lead_tag})
        general_details = college_details.get("general_additional_details", {})
        if not general_details:
            general_details = {}
        general_details.update(payload)
        data.update(
            {
                "general_additional_details": general_details,
                "university.university_admission_website_url": payload.get(
                    "student_dashboard_landing_page_link"
                ),
                "university.university_logo": payload.get("logo_transparent"),
            }
        )
        # If the User is not Admin or Super Admin, then Approval Request wil be Created
        if user and user.get("role", {}).get("role_name") not in ["admin", "super_admin"]:
            approval_request = await ApprovalCRUDHelper().create_approval_request(
                user, {
                    "college_id": ObjectId(college_id),
                    "approval_type": "college_additional_details",
                    "payload": old_payload,
                },
                approval_id=approval_id,
            )
            await ApprovedRequestHandler().update_onboarding_details(
                college_id=college_id, client_id=None, step_name="additional_details", status="In Progress",
                user=user, approval_request=approval_request,
                request_of="college_additional_details"
            )
            return approval_request
        await DatabaseConfiguration().college_collection.update_one(
            {"_id": ObjectId(college_id)},
            {"$set": data}
        )
        await ApprovedRequestHandler().update_onboarding_details(
            college_id=college_id, client_id=None, step_name="additional_details", status="Approved",
            user=user,
            request_of="college_additional_details"
        )
        await cache_invalidation(api_updated="updated_college", user_id=college_id)
        return {"message": "General addition details successfully saved."}

    async def add_college_configuration(self, payload: dict, college_id: str, user: dict) -> dict:
        """
        Add the college configuration details
        This Should be used by only Super Admin

        Param:
            payload: Get the college configuration details from the user
            college_id: Get the college id of the current college
            user: Details of user

        Return:
            A success message
        """
        college = await DatabaseConfiguration().college_collection.find_one(
            {"_id": ObjectId(college_id)}
        )
        if college.get("is_configured"):
            payload["university"]["university_admission_website_url"] = college.get(
                "university", {}).get("university_admission_website_url")
            payload["university"]["university_logo"] = college.get("university", {}).get(
                "university_logo")
        payload["is_configured"] = True
        await DatabaseConfiguration().college_collection.update_one(
            {"_id": ObjectId(college_id)}, {"$set": payload}
        )
        await DatabaseConfiguration().onboarding_details.update_one(
            {"college_id": ObjectId(college_id), "type": "college"},
            {
                "$set":
                    {
                        "steps.college_configurations": {
                            "updated_at": datetime.utcnow(),
                            "status": "Done",
                            "requested_by": {
                                "_id": user.get("_id"),
                                "name": utility_obj.name_can(user)
                            },
                            "request_of": "college_configurations"
                        },
                        "status": "In Progress"
                    }
            }
        )
        await cache_invalidation(api_updated="updated_college", user_id=college_id)
        return {"message": "College configuration added successfully"}

    async def get_college_configuration(self, college_id: str) -> dict:
        """
        Get the college configuration details

        Param:
            college_id: Get the college id of the current college

        Return:
            A dictionary contains the college configuration details

        Raises:
            CustomError: If the college is not configured
        """
        db_obj = await DatabaseConfiguration().college_collection.find_one(
            {"_id": ObjectId(college_id)},
            {
                "_id": 0,
                "is_configured": 1,
                "email": 1,
                "current_season": 1,
                "seasons": 1,
                "university_prefix_name": 1,
                "university": 1,
                "cache_redis": 1,
                "gateways": 1,
                "juno_erp": 1,
                "payment_configurations": 1,
                "payment_gateway": 1,
                "enforcements": 1,
                "charges_per_release": 1,
                "users_limit": 1,
                "publisher_bulk_lead_push_limit": 1,
                "eazypay": 1,
                "razorpay": 1,
                "report_webhook_api_key": 1,
                "telephony_secret": 1,
                "telephony_cred": 1,
                "email_display_name": 1,
                "s3_base_folder": 1,
            }
        )
        if not db_obj.get("is_configured"):
            raise CustomError(message="College is not configured")

        # Transforming into Some Different Schema which is Required by Frontend
        email = db_obj.get("email", {}) or {}
        university = db_obj.get("university", {}) or {}
        seasons_data = db_obj.get("seasons", []) or []
        gateways = db_obj.get("gateways", {}) or {}
        juno = db_obj.get("juno_erp", {}) or {}

        return {
            "email_credentials": {
                "payload_username": email.get("payload_username", ""),
                "payload_password": email.get("payload_password", ""),
                "payload_from": email.get("payload_from", ""),
                "source": email.get("source", "")
            },
            "email_configurations": {
                "verification_email_subject": email.get("verification_email_subject", ""),
                "contact_us_number": email.get("contact_us_number", ""),
                "university_email_name": email.get("university_email_name", ""),
                "banner_image": email.get("banner_image", ""),
                "email_logo": email.get("email_logo", "")
            },
            "seasons": [
                {
                    "season_name": s.get("season_name", ""),
                    "start_date": s.get("start_date", ""),
                    "end_date": s.get("end_date", ""),
                    "database": s.get("database", {})
                }
                for s in seasons_data
            ],
            "university_details": {
                "university_contact_us_mail": university.get("university_contact_us_mail", ""),
                "university_website_url": university.get("university_website_url", ""),
                "university_prefix_name": db_obj.get("university_prefix_name", "")
            },
            "payment_gateways": gateways,
            "juno_erp": {
                "first_url": juno.get("first_url", {}),
                "second_url": juno.get("second_url", {}),
                "prog_ref": juno.get("prog_ref", 0)
            },
            "payment_configurations": db_obj.get("payment_configurations", []) or [],
            "preferred_payment_gateway": db_obj.get("payment_gateway", ""),
            "payment_successfully_mail_message": university.get("payment_successfully_mail_message", ""),
            "cache_redis": db_obj.get("cache_redis", {}) or {},
            "enforcements": db_obj.get("enforcements", {}) or {},
            "charges_per_release": db_obj.get("charges_per_release", {}) or {},
            "users_limit": db_obj.get("users_limit", 0),
            "publisher_bulk_lead_push_limit": db_obj.get("publisher_bulk_lead_push_limit", {}) or {},
            "report_webhook_api_key": db_obj.get("report_webhook_api_key", ""),
            "telephony_secret": db_obj.get("telephony_secret", ""),
            "telephony_cred": db_obj.get("telephony_cred", {}) or {},
            "email_display_name": db_obj.get("email_display_name", ""),
            "s3_base_folder": db_obj.get("s3_base_folder", "")
        }

    async def store_season_details(self, payload: dict, college_id: str):
        """
        Get the season details and storing the college collection details.

        Param:
            payload: Get all the
            college_id: Get the current college object id

        Return:
            A dictionary contains the success message
        """
        if not payload:
            raise CustomError(message="Payload are required")
        college_details = await DatabaseConfiguration().college_collection.find_one(
            {"_id": ObjectId(college_id)}
        )
        seasons = college_details.get("seasons", [])
        if not seasons:
            seasons = []
        season_id = payload.get("season_id")
        for data in seasons:
            if season_id == data.get("season_id"):
                raise CustomError(message="season_id is already exists")
        seasons.append(payload)
        data = {"seasons": seasons}
        if payload.get("is_current_season"):
            data.update({"current_season": season_id})
        await DatabaseConfiguration().college_collection.update_one(
            {"_id": ObjectId(college_id)}, {"$set": data}
        )
        return {"message": "Season has been stored successfully."}
