"""
This file contain functions related to followup notes
"""
from bson import ObjectId

from app.database.configuration import DatabaseConfiguration


class FollowupNotes:
    """
    Contain functions related to followup notes activities
    """

    async def total_followup_count_of_counselor(self, start_date, end_date, counselor_id):
        """
        Get total followup count of counselor
        """
        result = DatabaseConfiguration().leadsFollowUp.aggregate(
            [
                {"$project": {"_id": 0, "followup": 1}},
                {
                    "$unwind": {
                        "path": "$followup",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
                {
                    "$match": {
                        "followup.followup_date": {"$gte": start_date, "$lte": end_date},
                        "followup.assigned_counselor_id": ObjectId(counselor_id),
                    }
                },
                {"$facet": {"totalCount": [{"$count": "count"}]}},
            ]
        )
        total_data = 0
        async for data in result:
            try:
                total_data = data.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
        return total_data

    async def total_notes_count_of_counselor(self, start_date, end_date, counselor_id):
        """
        Get total notes count of counselor
        """
        result = DatabaseConfiguration().leadsFollowUp.aggregate(
            [
                {"$project": {"_id": 0, "notes": 1}},
                {
                    "$unwind": {
                        "path": "$notes",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
                {
                    "$match": {
                        "notes.timestamp": {"$gte": start_date, "$lte": end_date},
                        "notes.user_id": ObjectId(counselor_id),
                    }
                },
                {"$facet": {"totalCount": [{"$count": "count"}]}},
            ]
        )
        total_data = 0
        async for data in result:
            try:
                total_data = data.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
        return total_data

    async def total_untouched_stage_count(self, start_date, end_date, counselor_id):
        """
        Get total untouched stage count
        """
        result = DatabaseConfiguration().leadsFollowUp.aggregate(
            [
                {"$project": {"_id": 0, "lead_stage": 1, "counselor_timeline": 1}},
                {
                    "$unwind": {
                        "path": "$counselor_timeline",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
                {
                    "$match": {
                        "counselor_timeline.assigned_counselor_id": ObjectId(counselor_id),
                        "counselor_timeline.timestamp": {
                            "$gte": start_date,
                            "$lte": end_date,
                        },
                        "$expr": {"$eq": ["$counselor_timeline.lead_stage", "$lead_stage"]},
                    }
                },
                {"$facet": {"totalCount": [{"$count": "count"}]}},
            ]
        )
        total_data = 0
        async for data in result:
            try:
                total_data = data.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
        return total_data

    async def total_engaged_lead_count(
            self, start_date,
            end_date,
            counselor_id,
            leads_engagement_percentage=False,
            not_engaged_leads=False,
    ):
        """
        Get total engaged lead by counselor
        """
        result = DatabaseConfiguration().leadsFollowUp.aggregate(
            [
                {"$project": {"_id": 0, "application_id": 1, "counselor_timeline": 1}},
                {
                    "$unwind": {
                        "path": "$counselor_timeline",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
                {
                    "$match": {
                        "counselor_timeline.timestamp": {
                            "$gte": start_date,
                            "$lte": end_date,
                        }
                    }
                },
            ]
        )
        all_counselor_leads, total_not_engaged_leads, total_engaged_leads = [], [], 0
        count = 0
        async for data in result:
            count += 1
            if (
                    str(data.get("counselor_timeline", {}).get("assigned_counselor_id", ""))
                    == counselor_id
            ):
                total_engaged_leads += 1
                if str(data.get("application_id")) not in all_counselor_leads:
                    all_counselor_leads.append(str(data.get("application_id")))
            else:
                if str(data.get("application_id")) not in all_counselor_leads:
                    total_not_engaged_leads.append(str(data.get("application_id")))
        if leads_engagement_percentage:
            return total_engaged_leads, len(all_counselor_leads)
        if not_engaged_leads:
            return len(total_not_engaged_leads)
        return len(all_counselor_leads)
