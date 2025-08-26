"""
Communication summary counsellor wise followup data helper.
"""
import datetime
from app.database.configuration import DatabaseConfiguration
from app.core.utils import utility_obj
from bson.objectid import ObjectId
from app.helpers.counselor_deshboard.counselor import CounselorDashboardHelper


class CounsellorWiseFollowup:
    """
    All related functions of counsellor wise followup count.
    """

    async def get_followup_report(self, counselor_ids: list[ObjectId], start_date: datetime.datetime | None, end_date: datetime.datetime | None) -> dict:
        """"
        Get follow-up related summary information based on counselor ids.

        Params:
            counselor_ids (list[ObjectId]): A list which contains counselor
                ids. e.g., [ObjectId("123456789012345678901234")]
            start_date (datetime | None): Either none or start date which
                useful for filter data.
            end_date (datetime | None): Either none or end date which
                useful for filter data.

        Returns:
            dict: A dictionary which contains followup details summary
                information.
        """
        result = await DatabaseConfiguration().leadsFollowUp.aggregate([{
            "$match": {
                "followup.assigned_counselor_id": {
                    "$in": counselor_ids
                },
                "followup.followup_date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
        }, {
            "$unwind": "$followup"
        }, {
            "$group": {
                "_id": {
                    "counselor_id": "$followup.assigned_counselor_id",
                    "status": "$followup.status"
                },
                "total": {"$sum": 1}
            }
        }, {
            "$group": {
                "_id": "$_id.counselor_id",
                "followups": {
                    "$push": {
                        "status": "$_id.status",
                        "total": "$total"
                    }
                }
            }
        }]).to_list(None)
    
        # Initialize the followup information dictionary
        followup_info = {
            "first_followup": {"total": 0, "pending": 0},
            "second_followup": {"total": 0, "pending": 0},
            "third_followup": {"total": 0, "pending": 0}
        }

        # Process the result to populate the followup_info dictionary
        for doc in result:
            followups = doc['followups']
            
            total_followups = sum(f['total'] for f in followups)
            pending_followups = sum(f['total'] for f in followups if f['status'] != 'Completed')
            
            # Distribute the counts into first, second, and third followup
            if total_followups > 0:
                followup_info['first_followup']['total'] += 1
                if pending_followups > 0:
                    followup_info['first_followup']['pending'] += 1
            
            if total_followups > 1:
                followup_info['second_followup']['total'] += 1
                if pending_followups > 1:
                    followup_info['second_followup']['pending'] += 1
            
            if total_followups > 2:
                followup_info['third_followup']['total'] += 1
                if pending_followups > 2:
                    followup_info['third_followup']['pending'] += 1
        
        return followup_info


    async def counsellor_wise_followup(self, counsellor_ids: list[ObjectId], head_counsellor_id: ObjectId, date: str) -> dict:
        """
        Helper function to get followups details according to the counsellors.

        Params:
            counsellor_ids (list[ObjectId]): List of counsellor id's for filteration
            head_counsellor_id (ObjectId): Head counsellor id for getting all related counsellors data.
            date (str): Date for datewise filteration

        Returns:
            dict: Return response for all counsellors followup details, head counsellor wise and counsellor wise.
        """
        if date:
            date_start, date_end = await utility_obj.date_change_format(date, date)

        else:
            current_date = str(datetime.date.today())
            date_start, date_end = await utility_obj.date_change_format(
                current_date, current_date)

        head_counsellors = await DatabaseConfiguration().user_collection.aggregate([{
            "$match": {
                "role.role_name": "college_head_counselor",
                "is_activated": True
            }
        }]).to_list(None)

        head_counsellors_list = []

        for head_counsellor in head_counsellors:

            counsellors = await DatabaseConfiguration().user_collection.aggregate([{
                "$match": {
                    "head_counselor_id": head_counsellor.get("_id"),
                    "role.role_name": "college_counselor"
                }
            }]).to_list(None)

            id_of_counsellors = [ObjectId(data.get("_id")) for data in counsellors]

            followup_data = await CounselorDashboardHelper().get_followup_info_by_counselor_ids(id_of_counsellors, date_start, date_end, None)

            head_counsellors_list.append({
                "head_counselor_id": str(head_counsellor.get("_id")),
                "name": utility_obj.name_can(head_counsellor),
                "total_followup": followup_data.get("total_followups", 0),
                "pending_followup": followup_data.get("upcoming_followups", 0)+followup_data.get("overdue_followups", 0)
            })


        if head_counsellor_id:
            counsellors = await DatabaseConfiguration().user_collection.aggregate([{
                "$match": {
                    "head_counselor_id": head_counsellor_id,
                    "role.role_name": "college_counselor"
                }
            }]).to_list(None)

            counsellors_list = []

            for counsellor in counsellors:
                counsellor_followup_data = await CounselorDashboardHelper().get_followup_info_by_counselor_ids([counsellor.get("_id")], date_start, date_end, None)
                counsellors_list.append({
                    "counselor_id": str(counsellor.get("_id")),
                    "name": utility_obj.name_can(counsellor),
                    "total_followup": counsellor_followup_data.get("total_followups", 0),
                    "pending_followup": counsellor_followup_data.get("upcoming_followups", 0)+counsellor_followup_data.get("overdue_followups", 0)
                })

        total_counsellors = await DatabaseConfiguration().user_collection.aggregate([{
            "$match": {
                "role.role_name": "college_counselor",
                "is_activated": True
            }
        }]).to_list(None)

        if not counsellors_list or counsellor_ids:
            counsellors_list = []
            if counsellor_ids:
                counsellors = await DatabaseConfiguration().user_collection.aggregate([{
                    "$match": {
                        "_id": {
                            "$in": counsellor_ids,
                        },
                        "is_activated": True
                    }
                }]).to_list(None)
            else:
                counsellors = total_counsellors

            for counsellor in counsellors:
                counsellor_followup_data = await CounselorDashboardHelper().get_followup_info_by_counselor_ids([counsellor.get("_id")], date_start, date_end, None)
                counsellors_list.append({
                    "counselor_id": str(counsellor.get("_id")),
                    "name": utility_obj.name_can(counsellor),
                    "total_followup": counsellor_followup_data.get("total_followups", 0),
                    "pending_followup": counsellor_followup_data.get("upcoming_followups", 0)+counsellor_followup_data.get("overdue_followups", 0)
                })

        counsellor_ids = [ObjectId(data.get("_id")) for data in total_counsellors]

        total_followup_data = await CounselorDashboardHelper().get_followup_info_by_counselor_ids(counsellor_ids, date_start, date_end, None)

        followups = await self.get_followup_report(counsellor_ids, date_start, date_end)

        return {
            "total_followups": total_followup_data.get("total_followups", 0),
            "completed_followups": total_followup_data.get("completed_followups", 0),
            "overdue_followups": total_followup_data.get("overdue_followups", 0),
            "first_followup": followups.get("first_followup"),
            "second_followup": followups.get("second_followup"),
            "third_followup": followups.get("third_followup"),
            "followup_under_head_counsellors": head_counsellors_list,
            "coursellors_followups": counsellors_list
        }