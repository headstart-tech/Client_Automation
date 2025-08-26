"""
This file contains class and functions related to calls list.
"""

from app.database.configuration import DatabaseConfiguration
from app.core.utils import utility_obj
from bson import ObjectId

class CallsListReview:
    """
    Call list table related class and functions which help to retrive call list for review by QA.
    """

    async def call_review_helper(self, call: dict) -> dict:
        """
        Get the call activity/review data.

        Params:
            call_review_data (dict): A dictionary which contains call review data.

        Returns:
            dict: A dictionary which contains call review data in the formated way.
        """

        qced = {}
        if call.get("qced"):
            qced.update(call.get("qced")[0])

        data = {
            "_id": str(call.get("_id")),
            "call_date_time": utility_obj.get_local_time(call.get("created_at")),
            "call_type": call.get("type"),
            "call_duration": call.get("duration"),
            "recording": call.get("mcube_file_path"),
            "qc_status": "Not QCed" if qced.get("qc_status")==None else qced.get("qc_status"),
            "qa_score": qced.get("call_quality_score"),
            "qa_name": qced.get("qced_qa_name"),
            "qc_date": qced.get("date_time"),
            "counsellor_name": call.get("call_from_name"),
            "lead_name": call.get("call_to_name"),
            "call_starting": qced.get("call_starting"),
            "call_closing": qced.get("call_closing"),
            "call_engagement": qced.get("engagement"),
            "call_issue_handling": qced.get("issue_handling"),
            "call_product_knowledge": qced.get("product_knowledge"),
            "call_remarks": qced.get("remarks"),
            "counsellor_id": str(call.get("call_from")),
            "qa_id": str(qced.get("qced_qa")),
        }
        if call.get("type") == "Inbound":
            data.update({
                "counsellor_name": call.get("call_to_name"), 
                "counsellor_id": str(call.get("call_to")), 
                "lead_name": call.get("call_from_name")
            })

        return data


    async def retrieve_call_list(self, qc_date_range: dict, call_date_range: dict, qa: dict|None = None, counsellors: dict|None = None, call_type: str|None = None, qc_status: dict|None = None) -> dict:
        """
        Function of retriving data from database for all calls list.

        Params:
            qc_date_range (dict): start_date and end_date dictionary
            call_date_range (dict): start_date and end_date dictionary
            qa (str | None, optional): QA for filtering the calls. Defaults to None.
            counsellor (str | None, optional): Counsellor unique id for filteration of calls as per counsellor. Defaults to None.
            call_type (str | None, optional): It must be "Outbound" or "Inbound". Defaults to None.
            qc_status (str | None, optional): It must be 'Accepted', 'Rejected', 'Fatal Rejected' or 'Not QCed'. Defaults to None.

        Returns:
            dict: data of all calls for qa manager review section.
        """

        query = {"duration": {"$ne": 0}}

        if qc_date_range:
            qc_start_date, qc_end_date = await utility_obj.date_change_format(
                qc_date_range.get("start_date"),
                qc_date_range.get("end_date")
            )
            query.update(
                {
                    "qced.0.date_time": {
                        "$gte": qc_start_date, 
                        "$lte": qc_end_date
                    }
                }
            )

        if call_date_range:
            call_start_date, call_end_date = await utility_obj.date_change_format(
                call_date_range.get("start_date"),
                call_date_range.get("end_date")
            )
            query.update(
                {
                    "created_at": {
                        "$gte": call_start_date,
                        "$lte": call_end_date
                    }
                }
            )

        if qc_status.get("qc_status"):
            qc_status_params = []
            for qc in qc_status.get("qc_status"):
                if qc == "Not QCed":
                    qc_status_params.append(
                        {
                            "qced": {
                                "$exists": False
                            }
                        }
                    )

                else:
                    qc_status_params.append({"qced.0.qc_status": qc})
            query.update(
                {
                    "$or": qc_status_params
                }
            )
        
        if call_type:
            query.update(
                {
                    "type": call_type
                }
            )
        
        if counsellors.get("counsellor"):
            counsellor_params = []
            for counsellor in counsellors.get("counsellor"):
                counsellor_params.append({"call_from": ObjectId(counsellor)})
            query.update(
                {
                    "$or": counsellor_params
                }
            )

        if qa.get("qa"):
            qa_params = []
            for q in qa.get("qa"):
                qa_params.append({"qced.0.qced_qa": ObjectId(q)})
            query.update(
                {
                    "$or": qa_params
                }
            )

        calls_list = DatabaseConfiguration().call_activity_collection.aggregate([{"$match": query}, {"$sort": {"created_at": -1}}])

        call_dict = [
            await self.call_review_helper(item) for item in await calls_list.to_list(None)
        ]

        return call_dict
