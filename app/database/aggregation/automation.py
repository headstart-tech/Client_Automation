"""
This file contain class and functions related to automation
"""

import datetime

from bson import ObjectId
from fastapi.exceptions import HTTPException

from app.core.log_config import get_logger
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration

logger = get_logger(name=__name__)


class Automation:
    """
    Contain functions related to automation activities
    """

    async def unique_code_of_aggregation(
            self, pipeline, module_type, data_segment_name
    ):
        """
        Return pipeline based on condition
        """
        if module_type:
            pipeline.append(
                {
                    "$match": {
                        "module_name": {
                            "$in": [module.title() for module in module_type]
                        }
                    }
                }
            )
        if data_segment_name:
            pipeline.append(
                {"$match": {"data_segment_name": data_segment_name.title()}}
            )
        return pipeline

    async def validate_automation_id(self, automation_job_id):
        """
        Check automation id valid or not and return automation details if automation id is valid
        """
        if automation_job_id.startswith("Job#"):
            automation_job = (
                await DatabaseConfiguration().automation_activity_collection.find_one(
                    {"job_id": automation_job_id}
                )
            )
        else:
            await utility_obj.is_id_length_valid(
                _id=automation_job_id, name="Automation job id"
            )
            automation_job = (
                await DatabaseConfiguration().automation_activity_collection.find_one(
                    {"_id": ObjectId(automation_job_id)}
                )
            )
        return automation_job

    async def get_automation_job_details(self, document):
        """
        Helper for return automation job details
        """
        if document.get("template_details", {}).get("email"):
            document["template_details"]["email"]["template_id"] = str(
                document.get("template_details", {}).get("email", {}).get(
                    "template_id")
            )
        if document.get("template_details", {}).get("sms"):
            document["template_details"]["sms"]["template_id"] = str(
                document.get("template_details", {}).get("sms", {}).get(
                    "template_id")
            )
        if document.get("template_details", {}).get("whatsapp"):
            document["template_details"]["whatsapp"]["template_id"] = str(
                document.get("template_details", {})
                .get("whatsapp", {})
                .get("template_id")
            )
        return {
            "job_id": (
                str(document.get("_id"))
                if document.get("job_id") is None
                else document.get("job_id")
            ),
            "rule_id": str(document.get("rule_id")),
            "rule_name": document.get("rule_name"),
            "template_details": document.get("template_details"),
            "action_type": document.get("action_type"),
            "status": document.get("status"),
            "module_type": document.get("module_name"),
            "execution_time": utility_obj.get_local_time(
                document.get("execution_time")
            ),
            "data_segment_name": document.get("data_segment_name"),
            "data_segment_id": str(document.get("data_segment_id")),
            "targeted_audience": document.get("targeted_audience"),
        }

    async def get_automation_rule_details(
            self, skip, limit, automation_id, module_type: str,
            data_segment_name: str
    ):
        """
        Return automation rule details
        """
        try:
            pipeline = [{"$match": {"rule_id": ObjectId(automation_id)}}]
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail="Automation id is wrong. Please provide correct automation id.",
            )
        pipeline = await self.unique_code_of_aggregation(
            pipeline, module_type, data_segment_name
        )
        pipeline.append(
            {
                "$facet": {
                    "paginated_results": [
                        {"$sort": {"execution_time": -1}},
                        {"$skip": skip},
                        {"$limit": limit},
                    ],
                    "totalCount": [{"$count": "count"}],
                }
            }
        )
        result = DatabaseConfiguration().automation_activity_collection.aggregate(
            pipeline
        )
        rule_data, total_data = [], 0
        async for data in result:
            try:
                total_data = data.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
            rule_data = [
                await self.get_automation_job_details(document)
                for document in data.get("paginated_results")
            ]
        return rule_data, total_data

    async def get_automation_rule_jobs_details(
            self, job_ids, module_type: str, data_segment_name: str
    ):
        """
        Return automation rule jobs details by ids and based on filter
        """
        if job_ids:
            if job_ids[0].startswith("Job#"):
                match = {"job_id": {"$in": job_ids}}
            else:
                match = {"_id": {"$in": [ObjectId(x) for x in job_ids]}}
            try:
                pipeline = [{"$match": match},
                            {"$sort": {"execution_time": -1}}]
            except Exception as e:
                logger.error("Something went wrong. ", e)
                return False
        else:
            pipeline = [{"$sort": {"execution_time": -1}}]
        pipeline = await self.unique_code_of_aggregation(
            pipeline, module_type, data_segment_name
        )
        result = DatabaseConfiguration().automation_activity_collection.aggregate(
            pipeline
        )
        return [
            await self.get_automation_job_details(document) async for document
            in result
        ]

    async def communication_details_of_job(self, automation_job):
        """
        Return Communication details like email, sms and whatsapp
        """
        email_details, sms_details, whatsapp_details = None, None, None
        if "email" in automation_job.get("action_type"):
            email_details = {
                "sent": automation_job.get("targeted_audience"),
                "delivered": (
                    automation_job.get("email_status", {}).get("delivered")
                    if automation_job.get("email_status", {}).get("delivered")
                    else "NA"
                ),
                "opened": (
                    automation_job.get("email_status", {}).get("opened")
                    if automation_job.get("email_status", {}).get("opened")
                    else "NA"
                ),
                "clicked": (
                    automation_job.get("email_status", {}).get("clicked")
                    if automation_job.get("email_status", {}).get("clicked")
                    else "NA"
                ),
            }
        if "sms" in automation_job.get("action_type"):
            sms_details = {
                "sent": automation_job.get("targeted_audience"),
                "delivered": (
                    automation_job.get("sms_status", {}).get("delivered")
                    if automation_job.get("sms_status", {}).get("delivered")
                    else "NA"
                ),
            }
        if "whatsapp" in automation_job.get("action_type"):
            whatsapp_details = {
                "sent": automation_job.get("targeted_audience"),
                "invalid": (
                    automation_job.get("whatsapp_status", {}).get("invalid")
                    if automation_job.get("whatsapp_status", {}).get("invalid")
                    else "NA"
                ),
                "opened": (
                    automation_job.get("whatsapp_status", {}).get("opened")
                    if automation_job.get("whatsapp_status", {}).get("opened")
                    else "NA"
                ),
                "clicked": (
                    automation_job.get("whatsapp_status", {}).get("clicked")
                    if automation_job.get("whatsapp_status", {}).get("clicked")
                    else "NA"
                ),
            }
        return email_details, sms_details, whatsapp_details

    async def communication_status_of_job(self, automation_job):
        """
        Get communication status details of automation
        """
        email_details, sms_details, whatsapp_details = None, None, None
        if "email" in automation_job.get("action_type"):
            email_details = {
                "sent": automation_job.get("targeted_audience"),
                "unique_delivered": (
                    [
                        utility_obj.get_percentage_result(
                            automation_job.get("email_status", {}).get(
                                "delivered"),
                            automation_job.get("targeted_audience"),
                        ),
                        automation_job.get("email_status", {}).get(
                            "delivered"),
                    ]
                    if automation_job.get("email_status", {}).get("opened")
                    else ["NA", "NA"]
                ),
                "unique_open": (
                    [
                        utility_obj.get_percentage_result(
                            automation_job.get("email_status", {}).get(
                                "opened"),
                            automation_job.get("targeted_audience"),
                        ),
                        automation_job.get("email_status", {}).get("opened"),
                    ]
                    if automation_job.get("email_status", {}).get("opened")
                    else ["NA", "NA"]
                ),
                "unique_click": (
                    [
                        utility_obj.get_percentage_result(
                            automation_job.get("email_status", {}).get(
                                "clicked"),
                            automation_job.get("targeted_audience"),
                        ),
                        automation_job.get("email_status", {}).get("clicked"),
                    ]
                    if automation_job.get("email_status", {}).get("clicked")
                    else ["NA", "NA"]
                ),
            }
        if "sms" in automation_job.get("action_type"):
            sms_details = {
                "sent": automation_job.get("targeted_audience"),
                "unique_delivered": (
                    [
                        utility_obj.get_percentage_result(
                            automation_job.get("sms_status", {}).get(
                                "delivered"),
                            automation_job.get("targeted_audience"),
                        ),
                        automation_job.get("sms_status", {}).get("delivered"),
                    ]
                    if automation_job.get("sms_status", {}).get("opened")
                    else ["NA", "NA"]
                ),
            }
        if "whatsapp" in automation_job.get("action_type"):
            whatsapp_details = {
                "sent": automation_job.get("targeted_audience"),
                "invalid": (
                    [
                        utility_obj.get_percentage_result(
                            automation_job.get("whatsapp_status", {}).get(
                                "invalid"),
                            automation_job.get("targeted_audience"),
                        ),
                        automation_job.get("whatsapp_status", {}).get(
                            "invalid"),
                    ]
                    if automation_job.get("email_status", {}).get("opened")
                    else ["NA", "NA"]
                ),
                "unique_open": (
                    [
                        utility_obj.get_percentage_result(
                            automation_job.get("whatsapp_status", {}).get(
                                "opened"),
                            automation_job.get("targeted_audience"),
                        ),
                        automation_job.get("whatsapp_status", {}).get(
                            "opened"),
                    ]
                    if automation_job.get("whatsapp_status", {}).get("opened")
                    else ["NA", "NA"]
                ),
                "whatsapp_click": (
                    [
                        utility_obj.get_percentage_result(
                            automation_job.get("whatsapp_status", {}).get(
                                "clicked"),
                            automation_job.get("targeted_audience"),
                        ),
                        automation_job.get("whatsapp_status", {}).get(
                            "clicked"),
                    ]
                    if automation_job.get("whatsapp_status", {}).get("opened")
                    else ["NA", "NA"]
                ),
            }
        return email_details, sms_details, whatsapp_details

    async def job_details_by_id(
            self, skip, limit, automation_job, email_id, action_type=None
    ):
        """
        Get job details by id
        """
        pipeline = [
            {"$match": {"_id": automation_job.get("_id")}},
            {"$unwind": {"path": "$job_details"}},
        ]
        if email_id and action_type:
            email_filter = []
            for email, action in zip(email_id, action_type):
                email_filter.append(
                    {
                        "$and": [
                            {"job_details.action_type": action},
                            {"job_details.email_id": email},
                        ]
                    }
                )
            pipeline.append({"$match": {"$or": email_filter}})
        elif email_id:
            pipeline.append({"$match": {"job_details.email_id": email_id}})
        pipeline.append(
            {
                "$facet": {
                    "paginated_results": [
                        {"$sort": {"communication_date": -1}},
                        {"$skip": skip},
                        {"$limit": limit},
                    ],
                    "totalCount": [{"$count": "count"}],
                }
            }
        )
        result = DatabaseConfiguration().automation_activity_collection.aggregate(
            pipeline
        )
        job_data, total_data = [], 0
        async for data in result:
            try:
                total_data = data.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
            count = 1
            for document in data.get("paginated_results"):
                job_data.append(
                    {
                        "index_number": count,
                        "job_id": (
                            str(automation_job.get("_id"))
                            if automation_job.get("job_id") is None
                            else automation_job.get("job_id")
                        ),
                        "rule_id": str(automation_job.get("rule_id")),
                        "rule_name": automation_job.get("rule_name"),
                        "action_type": document.get("job_details", {}).get(
                            "action_type"
                        ),
                        "name": document.get("job_details", {}).get("name"),
                        "email_id": document.get("job_details", {}).get(
                            "email_id"),
                        "communication_date": utility_obj.get_local_time(
                            document.get("job_details", {}).get(
                                "communication_date",
                                datetime.datetime.utcnow()
                            )
                        ),
                        "status": document.get("job_details", {}).get(
                            "status"),
                    }
                )
                count += 1
        return job_data, total_data
