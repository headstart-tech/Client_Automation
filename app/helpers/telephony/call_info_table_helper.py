"""
Call Info data related functions
"""
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from datetime import date
from app.core.custom_error import CustomError
from bson import ObjectId

class CallInfo:
    """
    Call info data related functions
    """ 

    async def call_info_data_helper(self, user: dict, date_range: dict, call_type: str) -> dict:
        """
        General helper function for outbound/inbound call details of a particular counselor

        Params:
            user (dict): Data of counselor to retrieve call details
            date_range (dict): Date range for data filter
            call_type (str): Type of call ('Outbound' or 'Inbound')

        Returns:
            dict: Details of calls
        """

        match_field = "call_from" if call_type == "Outbound" else "call_to"

        match_case = {
            "$match": {
                match_field: user.get("_id"),
                "type": call_type
            }
        }

        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'),
                date_range.get('end_date')
            )
            match_case["$match"].update({"created_at": {"$gte": start_date, "$lte": end_date}})

        calls = await DatabaseConfiguration().call_activity_collection.aggregate([
            match_case,
            {
                '$group': {
                    '_id': None,
                    'attemptedCallsCount' if call_type == "Outbound" else "receivedCallsCount": {
                        '$sum': {
                            '$cond': [
                                {
                                    '$eq': [
                                        '$status', 'Customer Busy' if call_type == "Outbound" else 'ANSWER'
                                    ]
                                }, 1, 0
                            ]
                        }
                    },
                    'connectedCallsCount' if call_type == "Outbound" else "missedCallsCount": {
                        '$sum': {
                            '$cond': [
                                {
                                    '$eq': [
                                        '$status', 'Call Complete'
                                    ]
                                } if call_type == "Outbound" else {
                                    '$in': [
                                        '$status', ['NOANSWER', 'BUSY', 'CANCEL', "Missed"]
                                    ]
                                }, 1, 0
                            ]
                        }
                    },
                    'totalDuration': {
                        '$sum': '$duration'
                    },
                    'averageDuration': {
                        '$avg': '$duration'
                    }
                }
            }, {
                '$project': {
                    '_id': 0,
                    'attemptedCallsCount' if call_type == "Outbound" else "receivedCallsCount": 1,
                    'connectedCallsCount' if call_type == "Outbound" else "missedCallsCount": 1,
                    'totalDuration': 1,
                    'averageDuration': 1
                }
            }
        ]).to_list(None)
        calls = calls[0] if calls else {}

        return {
            "id": str(user.get("_id")),
            "counsellor_name": utility_obj.name_can(user),
            "attempted_call" if call_type == "Outbound" else "received_call": calls.get("attemptedCallsCount" if call_type == "Outbound" else "receivedCallsCount", 0),
            "connected_call" if call_type == "Outbound" else "missed_call": calls.get("connectedCallsCount" if call_type == "Outbound" else "missedCallsCount", 0),
            "duration": calls.get("totalDuration", 0),
            "average_duration": utility_obj.format_float_to_2_places(calls.get("averageDuration") if calls.get("averageDuration") else 0)
        }


    async def call_info_helper(self, counsellors: list[str], data_type: str, date_range: dict, page_num: int, 
                                        page_size: int, sort: bool, sort_name: str, sort_type: str, college: dict) -> dict:
        """
        Fetch call header data from the database using an aggregation pipeline.

        Params:
            counsellors (list[str]): List of counselor IDs.
            data_type (str): Type of call ('Outbound' or 'Inbound')
            date_range (dict): Date range for filtering data.
            page_num (int): Current requested page no.
            page_size (int): No. of data in one page.
            sort (bool): Apply sorting on data (true, false)
            sort_name (str): Name of the column which have to sort
            sort_type (str): Type of sort ("asc", "dsc")
            college (dict): Details of current college.

        Returns:
            dict: Response dictionary.
        """
        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
        if counsellors:
            counsellors = [ObjectId(counsellor) for counsellor in counsellors]
        else:
            counsellors = []

        users_pipeline = []
        if counsellors:
            users_pipeline.append({
                "$match": {
                    "_id": {
                        "$in": counsellors
                    }
                }
            })

        else:
            users_pipeline.append({
                "$match": {
                    "is_activated": True, 
                    "role.role_name": "college_counselor", 
                    "associated_colleges": {"$in": [ObjectId(college.get("id"))]}
                }
            })

        users_pipeline.append({
            "$facet": {
                "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                "totalCount": [{"$count": "count"}]
            }
        })
        users = await DatabaseConfiguration().user_collection.aggregate(users_pipeline).to_list(None)
        users = users[0] if users else {}
        users, count = users.get("paginated_results", []), users.get("totalCount", [])[0].get("count", 0) if users.get("totalCount") else 0

        data = []
        if data_type == "Outbound":
            for user in users:
                data.append(await self.call_info_data_helper(user, date_range, data_type))
        else:
            for user in users:
                data.append(await self.call_info_data_helper(user, date_range, data_type))

        sorted_data = data
        if sort:
            sorted_data = sorted(data, key=lambda x: x.get(sort_name), reverse=True if sort_type == 'dsc' else False)

        return sorted_data, count