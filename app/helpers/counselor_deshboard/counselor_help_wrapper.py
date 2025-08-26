"""
This file contains the function of counselor routers
"""

import datetime
from scipy import stats
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from bson import ObjectId


class counselor_wrapper:
    """
    A class containing information about the counselor routers.
    """

    async def performance_report_helper(
            self, counselor_id: list | None = None, start_date=None,
            end_date=None, college_id=None):
        """
        Get the information about counselor performance.

        Params:
            - counselor_id (list): Either None or unique identifier of
                counselor (s) which useful for get performance report.
            - start_date (datetime | None): Either None or start_datetime which
                useful for filter call data.
            - end_date (datetime | None): Either None or end_datetime which
                useful for filter call data.
            - college_id (str | None): Either None or unique identifier of a
                college.

        Returns:
            - dict: A dictionary which contains information about
                the counselor performance.
        """
        app_base_match = {
            "college_id": ObjectId(college_id),
            "current_stage": {"$gte": 2},
            "allocate_to_counselor.counselor_id": {
                "$in": counselor_id}
        }
        payment_match = app_base_match.copy()
        payment_match.update({"payment_info.status": "captured"})
        lead_match = {"college_id": ObjectId(college_id), "is_verify": True,
                      "allocate_to_counselor.counselor_id":
                          {"$in": counselor_id}}
        if start_date and end_date:
            app_base_match.update(
                {"enquiry_date": {"$gte": start_date, "$lte": end_date}})
            lead_match.update(
                {"created_at": {"$gte": start_date, "$lte": end_date}})
            payment_match.update({"payment_info.created_at": {
                                "$gte": start_date, "$lte": end_date}})
        form_initiated = await DatabaseConfiguration().\
            studentApplicationForms.count_documents(app_base_match)
        app_base_match.update({"declaration": True})
        application_submitted = await DatabaseConfiguration(). \
            studentApplicationForms.count_documents(app_base_match)
        app_base_match.pop("declaration")
        paid_application = await DatabaseConfiguration(). \
            studentApplicationForms.count_documents(payment_match)
        payment_match.update({"payment_initiated": True,
                              "payment_info.status": {"$ne": "captured"}})
        payment_initiated = await DatabaseConfiguration(). \
            studentApplicationForms.count_documents(payment_match)
        verified_leads = await DatabaseConfiguration(). \
            studentsPrimaryDetails.count_documents(lead_match)
        return {"application_submitted": application_submitted,
                "paid_application": paid_application,
                "payment_initiated": payment_initiated,
                "form_initiated": form_initiated,
                "verified_leads": verified_leads}

    async def get_call_performance(
            self, counselor_id: list | None = None, start_date=None,
            end_date=None):
        """
        Get the call activity performance based on counselor id.

        Params:
            - counselor_id (list): List of counselor IDs to get
                the call activity performance
            - start_date (datetime | None): Either None or start_datetime which
                useful for filter call data.
            - end_date (datetime | None): Either None or end_datetime which
                useful for filter call data.

        Returns:
            - dict: A dictionary call activity details
        """
        pipeline = [
                {
                    "$match": {
                        "$or": [
                            {
                                "call_to": {"$in": counselor_id}},
                            {
                                "call_from": {"$in": counselor_id}}]
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "call_duration": 1,
                        "call_started_at": {"$dateFromString": {
                            "dateString": "$call_started_at",
                            "timezone": "Asia/Kolkata"
                        }}
                    }
                },
                {
                    "$group": {
                        "_id": "",
                        "days_included": {"$addToSet": {
                            "$dateToString": {"format": "%Y-%m-%d",
                                              "date": "$call_started_at"}}},
                        "total_call": {"$sum": 1},
                        "call_duration": {"$push": "$call_duration"}
                    }
                }
            ]
        if start_date and end_date:
            pipeline.insert(2, {"$match":
                {"call_started_at": {"$gte": start_date, "$lte": end_date}}})
        result = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)
        call_info = {}
        async for data in result:
            if data is None:
                return {}
            days_included = len(data.get("days_included")) \
                if data.get("days_included") else 0
            call_info["avr_call_day"] = utility_obj.format_float_to_2_places(
                data.get("total_call", 0) / days_included) \
                if days_included != 0 else 0
            IQR = stats.iqr(data.get("call_duration"),
                            interpolation='midpoint')
            call_info["avr_call_duration"] = IQR
            return call_info
        return call_info

    async def pending_followup(self, counselor_id: list | None = None):
        """
        Get the pending followup based on counselor id

        params:
            counselor_id (list): List of counselor IDs to get
            the pending followup

        returns:
         response: A dictionary pending followup details
        """
        today = str(datetime.date.today())
        current_date, end_date = await utility_obj.date_change_format(
            today, today)
        result = DatabaseConfiguration().leadsFollowUp.aggregate(
            [
                {
                    "$unwind": {
                        "path": "$followup"
                    }
                },
                {
                    "$match": {
                        "followup.followup_date": {"$gte": current_date}
                    }
                },
                {
                    "$group": {
                        "_id": "",
                        "total_pending_followup": {"$sum": 1}
                    }
                }
            ]
        )
        async for data in result:
            if data is None:
                return {}
            return data
        return {}

    async def calculate_call_quality(
            self, counselor_id: list[ObjectId],
            start_date: datetime.datetime | None,
            end_date: datetime.datetime | None) -> float:
        """
        Calculate call quality based on counselor_id.

        Params:
            - counselor_id (list): List of counselor IDs to get
                the call activity performance
            - start_date (datetime | None): Either None or start_datetime which
                useful for filter call data.
            - end_date (datetime | None): Either None or end_datetime which
                useful for filter call data.

        Returns:
            - float: Count of call quality.
        """
        pipeline = [{
            "$match": {
                "call_from": {"$in": counselor_id},
                "qced": {
                    "$exists": True
                }
            }
        },
            {
                '$project': {
                    'call_quality': {
                        '$arrayElemAt': [
                            '$qced.call_quality_score', 0
                        ]
                    }
                }
            },
            {
                '$group': {
                    '_id': None,
                    'average_call_quality': {
                        '$avg': '$call_quality'
                    }
                }
            }
        ]
        if start_date and end_date:
            pipeline.insert(0, {
                    "$project": {
                        "_id": 0,
                        "call_from": 1,
                        "qced": 1,
                        "call_started_at": {"$dateFromString": {
                            "dateString": "$call_started_at",
                            "timezone": "Asia/Kolkata"
                        }}
                    }
                })
            pipeline[1].get("$match", {}).update(
                {"call_started_at": {"$gte": start_date, "$lte": end_date}})
        average_quality_list = await DatabaseConfiguration().\
            call_activity_collection.aggregate(pipeline).to_list(None)

        if not average_quality_list:
            average_quality_list.append({"average_call_quality": 0})
        return utility_obj.format_float_to_2_places(
            average_quality_list[0].get("average_call_quality"))

    async def counselor_performance_helper(
            self, counselor_id: list | None = None, date_range=None,
            college_id=None) -> dict:
        """
        Get the information about counselor performance

        params:
            - counselor_id (list): Either None or list of counselor ids.
            - date_range (dict): Date range (start and end date) which useful
                for get the student based on date range

        Returns:
            response: A dictionary containing information about
                the counselor performance
        """
        date_range = await utility_obj.format_date_range(date_range)
        start_date, end_date = date_range.get("start_date"), \
            date_range.get("end_date")
        if start_date and end_date:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date"))
        student_data = await self.performance_report_helper(
            counselor_id=counselor_id, start_date=start_date,
            end_date=end_date, college_id=college_id)
        call_info = await self.get_call_performance(
            counselor_id=counselor_id, start_date=start_date,
            end_date=end_date)
        student_data.update({"avr_call_day": str(call_info.get("avr_call_day", 0)),
                             "avr_call_duration": str(call_info.get(
                                 "avr_call_duration", 0))})
        student_data["call_quality_score"] = str(
            await self.calculate_call_quality(
            counselor_id=counselor_id, start_date=start_date,
            end_date=end_date))
        today = str(datetime.date.today())
        current_date, end_date = await utility_obj.date_change_format(
            today, today)
        follow_up = {
            "followup": {
                "$all": [
                    {
                        "$elemMatch": {
                            "assigned_counselor_id": {"$in": counselor_id},
                            "followup_date": {
                                "$gte": end_date
                            }
                        }
                    }]}
        }
        upcoming_followup_count = await DatabaseConfiguration().\
            leadsFollowUp.count_documents(follow_up)
        student_data.update({"total_pending_followup": upcoming_followup_count})
        return student_data
