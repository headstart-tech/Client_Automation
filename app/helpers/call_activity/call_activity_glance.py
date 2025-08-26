"""
this file contain class and functions of call activity glance
"""
import re

from app.core.utils import utility_obj, settings
from app.database.configuration import DatabaseConfiguration


class call_activity_glance:
    """
    Contain functions related to call activity glance
    """

    def __init__(self):
        pass

    async def get_total_call_duration(self):
        """
        Get all detail from call activity collection
        """
        outbound_call_detail = await self.call_aggregation_build("Outbound")
        inbound_call_detail = await self.call_aggregation_build("Inbound")
        return {"outbound_call_details": outbound_call_detail, "inbound_call_details": inbound_call_detail}

    async def call_aggregation_build(self, type_call):
        """
        Build aggregation of call duration
        """
        pipeline = [
            {
                "$match": {
                    "type": type_call.title()
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "type": 1,
                    "call_duration": 1
                }
            },
            {
                "$group": {
                    "_id": "",
                    "total_call_attempt": {"$sum": 1},
                    "total_missed_call": {
                        "$push": {"$cond": [{"$eq": ["$call_duration", 0]}, 1, 0]}
                    },
                    "total_talk_time": {
                        "$push": "$call_duration"
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total_call_attempt": "$total_call_attempt",
                    "total_missed_call": {"$sum": "$total_missed_call"},
                    "total_talk_time": {"$sum": "$total_talk_time"}
                }
            }
        ]
        results = DatabaseConfiguration().call_activity_collection.aggregate(pipeline)
        async for data in results:
            return data


class call_activity_report:
    """"
    Contain functions related to call activity report
    """

    def __init__(self, start_date, end_date, skip, limit):
        self.start_date = start_date
        self.end_date = end_date
        self.skip = skip
        self.limit = limit

    async def get_counselor_outbound_report(self, payload):
        """
        Get counselor wise outbound details
        """
        return await self.build_pipeline_aggregation("Outbound", payload)

    async def get_counselor_inbound_report(self, payload):
        """
        Get counselor wise inbound details
        """
        return await self.build_pipeline_aggregation("Inbound", payload)

    async def build_pipeline_aggregation(self, call_type, payload):
        """
        Build aggregation for call activity report
        """
        skip, limit = await utility_obj.return_skip_and_limit(page_num=self.skip, page_size=self.limit)
        pipeline = [
            {
                "$match": {
                    "type": call_type.title(),
                    "created_at": {"$gte": self.start_date, "$lte": self.end_date}
                }
            },
            {
                "$sort": {
                    "created_at": -1
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "call_to": 1,
                    "call_to_name": 1,
                    "call_from": 1,
                    "call_from_name": 1,
                    "call_started_at": 1,
                    "call_duration": 1
                }
            },
            {
                "$lookup": {
                    "from": "studentsPrimaryDetails",
                    "let": {"student_phone_number": "$call_to"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": ["$basic_details.mobile_number", "$$student_phone_number"]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 1,
                                "user_name": 1,
                                "is_verify": 1
                            }
                        }],
                    "as": "student_details"
                }
            },
            {
                "$unwind": {
                    "path": "$student_details"
                }
            },
            {
                "$lookup": {
                    "from": "studentSecondaryDetails",
                    "let": {"student_id": "$student_details._id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": ["$student_id", "$$student_id"]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "attachments": 1
                            }
                        }
                    ],
                    "as": "secondary_details"
                }
            },
            {
                "$unwind": {
                    "path": "$secondary_details",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            {
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            }
        ]
        if call_type.title() == "Inbound":
            pipeline[3].get("$lookup", {}).get("let", {}).update({"student_phone_number": "$call_from"})
        if payload.get("call_status") is not None:
            pipeline[0].get("$match", {}).update(
                {"call_duration": {"$gt": 0} if payload.get("call_status").lower() == "answered" else {"$eq": 0}})
        if payload.get("lead_status") is not None:
            pipeline[3].get("$lookup", {}).get("pipeline", [{}])[0].get("$match", {}).update(
                {"is_verify": True if payload.get("lead_status").lower() == "verified" else False})
        if payload.get("counselor_id"):
            if call_type == "Inbound":
                pipeline[0].get("$match", {}).update({"call_to": {"$in": payload.get("counselor_id")}})
            else:
                pipeline[0].get("$match", {}).update({"call_from": {"$in": payload.get("counselor_id")}})
        results = DatabaseConfiguration().call_activity_collection.aggregate(pipeline)
        return await self.extract_result(results, payload, call_type)

    async def extract_result(self, results, payload, call_type):
        """
        Extract the result
        """
        call_details = []
        season_year = utility_obj.get_year_based_on_season()
        aws_env = settings.aws_env
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        async for result in results:
            try:
                total = result.get("totalCount", [{}])[0].get("count")
            except Exception:
                total = 0
            for data in result.get("paginated_results", []):
                temp = {"id": str(data.get("_id")), "student_email": data.get("student_details", {}).get("user_name"),
                        "duration": data.get("call_duration"), "date_time": data.get("call_started_at"),
                        "lead_status": "verified" if data.get("student_details", {}).get(
                            "is_verify") is True else "unverified",
                        "call_status": "Answered" if data.get("call_duration") > 0 else "Missed",
                        "student_photo": ""}
                if call_type == "Outbound":
                    temp["student_name"] = data.get("call_to_name")
                    temp["student_mobile"] = data.get("call_to")
                    temp["counselor_name"] = data.get("call_from_name")
                else:
                    temp["student_name"] = data.get("call_from_name")
                    temp["counselor_name"] = data.get("call_to_name")
                    temp["student_mobile"] = str(data.get("call_from"))
                if data.get("secondary_details", {}).get("attachments", {}).get("recent_photo", {}).get(
                        "file_s3_url") is not None:
                    path = f"{utility_obj.get_university_name_s3_folder()}/{season_year}/{settings.s3_public_bucket_name}/{data.get('secondary_details', {}).get('attachments', {}).get('recent_photo', {}).get('file_s3_url').split('/')[8]}"
                    url = await self.create_presigned_post(self, base_bucket, path)
                    temp["student_image"] = url
                else:
                    temp["student_image"] = ""
                call_details.append(temp)
        if payload.get("search") is not None:
            call_details = await self.search_result(call_details, payload)
        response = await utility_obj.pagination_in_aggregation(self.skip, self.limit, total,
                                                               route_name="/call_activities/counselor_wise_outbound_report")
        return {
            "data": call_details,
            "total": total,
            "count": self.limit,
            "pagination": response["pagination"],
            "message": "data fetch successfully"
        }

    async def search_result(self, call_details, payload):
        """
        Search by name, email and number
        """
        denied_metrics = [re.compile(payload.get("search").lower()), re.compile(f"{payload.get('search').lower()}$")]
        if payload.get("search").isalpha() is True:
            return [student_data for student_data in call_details
                    if any(dm.search(str(student_data.get("student_name").lower())) for dm in denied_metrics)]
        elif payload.get("search").isnumeric() is True:
            return [student_data for student_data in call_details
                    if any(dm.search(str(student_data.get("student_mobile"))) for dm in denied_metrics)]
        else:
            return [student_data for student_data in call_details
                    if any(dm.search(str(student_data.get("student_email").lower())) for dm in denied_metrics)]

    async def create_presigned_post(self, bucket_name, object_name,
                                    fields=None, conditions=None, expiration=86400):
        """
        Generate a presigned URL S3 POST request to upload a file

        :param bucket_name: string
        :param object_name: str
        :param fields: Dictionary of prefilled form fields
        :param conditions: List of conditions to include in the policy
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Dictionary with the following keys:
            url: URL to post to
            fields: Dictionary of form fields and values to submit with the POST
        :return: None if error.
        """

        try:
            response = settings.s3_client.generate_presigned_post(bucket_name,
                                                                  object_name,
                                                                  Fields=fields,
                                                                  Conditions=conditions,
                                                                  ExpiresIn=expiration)
        except Exception as e:
            return None
        return response
