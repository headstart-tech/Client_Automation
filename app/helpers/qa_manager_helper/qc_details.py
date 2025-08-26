"""
This file contain class and functions related to QC Header data.
"""

from app.database.configuration import DatabaseConfiguration
from app.core.utils import utility_obj
from bson import ObjectId


class QCReviewDetails:
    """
    QC Header related class which contens all the function related to the header section.
    """

    async def retrieve_qc_details(self, date_range: dict, qa: str|None = None) -> dict:
        """
        Get the call summary count for header section of the QA manager.

        Params:
            - date_range (dict): A dictionary which contains start_date and end_date which useful for get call summary count based on date range. e.g., {"start_date": "2023-12-14", "end_date": "2023-12-31"}
            
        Returns:
            - dict: A dictionary which contains summary of call data.
        """
        query = {}
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'),
                date_range.get('end_date'))
            query.update(
                {"created_at": {"$gte": start_date, "$lte": end_date}})

        call_activity = DatabaseConfiguration().call_activity_collection

        parameters = {}
        parameters.update(query)
        total_calls = await call_activity.count_documents(parameters)

        parameters = {}
        parameters.update(query)
        parameters.update({"qced": {"$exists": False}})
        not_qced_calls = await call_activity.count_documents(parameters)

        if qa:
            query.update(
                {"qced.0.qced_qa": ObjectId(qa)}
            )

        parameters = {}
        parameters.update(query)
        parameters.update({"qced": {"$exists": True}})
        qced_calls = await call_activity.count_documents(parameters)

        parameters = {}
        parameters.update(query)
        parameters.update({"qced": {"$exists": True}})
        parameters.update({'qced.0.qc_status': 'Rejected'})
        rejected_calls = await call_activity.count_documents(parameters)

        parameters = {}
        parameters.update(query)
        parameters.update({"qced": {"$exists": True}})
        parameters.update({'qced.0.qc_status': 'Fatal Rejected'})
        fataled_calls = await call_activity.count_documents(parameters)

        parameters = {}
        parameters.update(query)
        parameters.update({"qced": {"$exists": True}})
        parameters.update({"qced.0.call_quality_score": {"$gt": 4.5}})
        call_qc_gt_90 = await call_activity.count_documents(parameters)

        try:
            qced_percent = (qced_calls/total_calls)*100
        except:
            qced_percent = 0

        try:
            rejected_percent = (rejected_calls/total_calls)*100
        except:
            rejected_percent = 0

        try:
            fataled_percent = (fataled_calls/total_calls)*100
        except:
            fataled_percent = 0

        data = {
            "total_calls": total_calls,
            "not_qced_calls": not_qced_calls,
            "qced_calls": {
                "count": qced_calls,
                "percent": utility_obj.format_float_to_2_places(qced_percent)
            },
            "rejected_calls": {
                "count": rejected_calls,
                "percent": utility_obj.format_float_to_2_places(rejected_percent)
            },
            "fataled_calls": {
                "count": fataled_calls,
                "percent": utility_obj.format_float_to_2_places(fataled_percent)
            },
            "call_qc_gt_90": call_qc_gt_90
        }

        return data


    async def retrieve_rejected_qc_details(self, date_range: dict, counsellor_id: str|None) -> dict:
        """
        Get the rejected call summary count for header section of the QA manager.

        Params:
            - date_range (dict): A dictionary which contains start_date and end_date which useful for get rejected call summary count based on date range. e.g., {"start_date": "2023-12-14", "end_date": "2023-12-31"}
            
        Returns:
            - dict: A dictionary which contains summary of rejected call data.
        """
        query = {}
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'),
                date_range.get('end_date'))
            query.update(
                {
                    "created_at": {
                        "$gte": start_date, 
                        "$lte": end_date
                    }
                }
            )
            
        if counsellor_id:
            query.update(
                {
                    "call_from": ObjectId(counsellor_id)
                }
            )

        call_activity = DatabaseConfiguration().call_activity_collection

        total_calls = await call_activity.count_documents(query)

        parameters = {}
        parameters.update(query)
        parameters.update({"qced": {"$exists": True}})
        qced_calls = await call_activity.count_documents(parameters)
        
        parameters = {}
        parameters.update(query)
        parameters.update({"qced": {"$exists": True}})
        parameters.update({'qced.0.qc_status': 'Rejected'})
        rejected_calls = await call_activity.count_documents(parameters)

        parameters = {}
        parameters.update(query)
        parameters.update({"qced": {"$exists": True}})
        parameters.update({'qced.0.qc_status': 'Fatal Rejected'})
        fataled_calls = await call_activity.count_documents(parameters)

        sup_parameters = []
        if query:
            sup_parameters.append({"$match": query})
            sup_parameters.append({"$group": {"_id": None, "total_duration": {"$sum": "$call_duration"}}})
        else:
            sup_parameters.append({"$group": {"_id": None, "total_duration": {"$sum": "$call_duration"}}})

        call_duration_list = await call_activity.aggregate(sup_parameters).to_list(None)
        if not call_duration_list:
            call_duration_list.append({"call_duration": 0})
        call_duration = call_duration_list[0]

        try:
            qced_percent = (qced_calls/total_calls)*100
        except:
            qced_percent = 0

        try:
            rejected_percent = (rejected_calls/total_calls)/100
        except:
            rejected_percent = 0

        try:
            fataled_percent = (fataled_calls/total_calls)/100
        except:
            fataled_percent = 0

        data = {
            "total_calls": total_calls,
            "qced_calls": {
                "count": qced_calls,
                "percent": utility_obj.format_float_to_2_places(qced_percent)
            },
            "rejected_calls": {
                "count": rejected_calls,
                "percent": utility_obj.format_float_to_2_places(rejected_percent)
            },
            "fataled_calls": {
                "count": fataled_calls,
                "percent": utility_obj.format_float_to_2_places(fataled_percent)
            },
            "qced_calls_duration": call_duration.get("total_duration")
        }

        return data
