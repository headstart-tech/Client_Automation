"""
This file contains class and functions which useful to perform operation (s) on counselor activity data.
"""
from app.database.configuration import DatabaseConfiguration
from app.core.utils import utility_obj
from bson import ObjectId
from datetime import datetime, timezone

class CallActivity:
    """
    Counsellor call activity related functions.
    """

    async def update_match_stage_by_date_range(self, match_stage: dict, date_range: dict, field_name: str = "datetime") -> dict:
        """
        Update the match_stage by date_range.

        Params:
            - match_stage (dict): A dictionary which want to update by date_range.
            - date_range (dict): A dictionary which contains start_date and end_date, which useful for update match_stage dictionary.
            - field_name (str): Name of field which useful for sort data by date_range.

        Returns:
        - dict: An updated dictionary of match_stage which useful in aggregation pipeline.
        """
        start_date, end_date = await utility_obj.date_change_format(
                        date_range.get('start_date'),
                        date_range.get('end_date'))
        match_stage.update({
            field_name: {
                "$gte": start_date,
                "$lte": end_date
            }
        })
        return match_stage
    

    async def update_match_stage_by_current_date(self, match_stage: dict) -> dict:
        """
        Update the match_stage by current date.

        Params:
            - match_stage (dict): A dictionary which want to update by current date.

        Returns:
        - dict: An updated dictionary of match_stage which useful in aggregation pipeline.
        """
        current_date = (datetime.now(timezone.utc)).replace(hour=0, minute=0, second=0, microsecond=0)
        match_stage.update({
            "datetime": {
                "$gte": current_date
            }
        })
        return match_stage

    async def get_common_pipeline_stages_info(self, match_stage: dict, field_name: str = "datetime", sort: int = 1) -> list:
        """
        Get the common pipeline stages information.

        Params:
            - match_stage (dict): A dictionary which basic match stage information.
            - field_name (str): Name of field which useful for sort data by date_range.

        Returns:
        - list: A list which contains common pipeline stages information.
        """
        return [{
                        '$match': match_stage
                    }, {
                        '$sort': {
                            field_name: sort
                        }
                    }]
    
    async def get_common_match_stage_info(self, user_id: ObjectId) -> list:
        """
        Get the common match stage information.

        Params:
        - user_id (ObjectId): An unique identifier/id of a user.

        Returns:
        - dict: A dict which contains common match stage information.
        """
        return {
            "$or": [
                {
                    "call_from": user_id
                },
                {
                    "call_to": user_id
                }
            ]
        }


    async def last_check_out_helper(self, counsellor: dict, response: dict, date_range: dict|None = None) -> None:
        """Find last check-out time of counsellor and update the response dict.

        Params:
            counsellor (dict): Current counsellor details
            response (dict): Response data model.
            date_range (dict): Must be the combination of start_date and end_date
        """

        match_stage = {
            "user_id": counsellor.get("_id"),
            'check_in_status': False
        }

        if date_range:
            match_stage = await self.update_match_stage_by_date_range(match_stage, date_range)

        else:
            match_stage = await self.update_match_stage_by_current_date(match_stage)

        pipeline = await self.get_common_pipeline_stages_info(match_stage, sort=-1)

        pipeline.extend([ 
            {
                '$limit': 1
            }
        ])
        check_out = await (DatabaseConfiguration().check_in_out_log.aggregate(pipeline)).to_list(None)
        
        if check_out:
            response.update({
                "last_check_out": utility_obj.get_local_time(check_out[0].get("datetime"))
            })
        else:
            response.update({
                "last_check_out": None
            })


    async def first_check_in_helper(self, counsellor: dict, response: dict, date_range: dict|None = None) -> None:
        """Find first check-in time and update the response dict.

        Params:
            counsellor (dict): Current counsellor details
            response (dict): Response data model.
            date_range (dict): Must be the combination of start_date and end_date
        """

        match_stage = {
            "user_id": counsellor.get("_id"),
            'check_in_status': True
        }

        if date_range:
            match_stage = await self.update_match_stage_by_date_range(match_stage, date_range)

        else:
            match_stage = await self.update_match_stage_by_current_date(match_stage)

        check_in = await (DatabaseConfiguration().check_in_out_log.aggregate([
            {
                "$match": match_stage
            },
            {
                '$limit': 1
            }
        ])).to_list(None)
        
        if check_in:
            response.update({
                "first_check_in": utility_obj.get_local_time(check_in[0].get("datetime"))
            })
        else:
            response.update({
                "first_check_in": None
            })


    async def last_call_time_helper(self, counsellor: dict, response: dict, date_range: dict|None = None) -> None:
        """Find last call time and update the response dict.

        Params:
            counsellor (dict): Current counsellor details
            response (dict): Response data model.
            date_range (dict): Must be the combination of start_date and end_date
        """

        and_condition_list = [
            await self.get_common_match_stage_info(counsellor.get("_id"))
        ]

        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'),
                date_range.get('end_date'))
            and_condition_list.insert(0, {
                "starttime": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            })

        call = await (DatabaseConfiguration().call_activity_collection.aggregate([
            {
                '$match': {
                    "$and": and_condition_list
                }
            }, {
                '$sort': {
                    'starttime': -1
                }
            }, {
                '$limit': 1
            }
        ])).to_list(None)

        if call:
            response.update({
                "last_call_time": utility_obj.get_local_time(call[0].get("starttime"))
            })
        else:
            response.update({
                "last_call_time": None
            })

    async def ideal_duration_helper(self, counsellor: dict, response: dict, date_range: dict|None = None) -> None:
        """Calculate total ideal duration of counsellor and update the response dict.

        Params:
            counsellor (dict): Current counsellor details
            response (dict): Response data model.
            date_range (dict): Must be the combination of start_date and end_date
        """

        and_condition_list = [
            await self.get_common_match_stage_info(counsellor.get("_id")),
            {
                'status': {
                    '$in': [
                        'Call Complete', 'ANSWER'
                    ]
                }
            }
        ]
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'),
                date_range.get('end_date'))
            and_condition_list.insert(0, {
                "starttime": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            })
        call = await (DatabaseConfiguration().call_activity_collection.aggregate([
            {
                '$match': {
                    "$and": and_condition_list
                }
            }, {
                '$sort': {
                    'starttime': -1
                }
            }, {
                '$limit': 1
            }, {
                '$addFields': {
                    'current_time': {
                        '$toDate': datetime.utcnow()
                    }, 
                    'last_call_time': '$endtime', 
                    'idle_duration': {
                        '$divide': [
                            {
                                '$subtract': [
                                    {
                                        '$toDate': datetime.utcnow()
                                    }, '$endtime'
                                ]
                            }, 3600000
                        ]
                    }
                }
            }
        ])).to_list(None)

        if call:
            response.update({
                "ideal_duration": int(call[0].get("idle_duration"))
            })
        else:
            response.update({
                "ideal_duration": 0
            })


    async def average_handling_time_helper(self, counsellor: dict, response: dict, date_range: dict|None = None) -> None:
        """Calculate Average handling time and update the response dict.

        Params:
            counsellor (dict): Current counsellor details
            response (dict): Response data model.
            date_range (dict): Must be the combination of start_date and end_date
        """
        and_condition_list = [
            await self.get_common_match_stage_info(counsellor.get("_id")),
            {
                'status': {
                    '$in': [
                        'Call Complete', 'ANSWER'
                    ]
                }
            }
        ]

        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'),
                date_range.get('end_date'))
            and_condition_list.insert(0, {
                "starttime": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            })

        calls = await (DatabaseConfiguration().call_activity_collection.aggregate([
            {
                '$match': {
                    "$and": and_condition_list
                }
            }, {
                '$group': {
                    '_id': None, 
                    'totalDuration': {
                        '$sum': '$duration'
                    }, 
                    'totalCount': {
                        '$sum': 1
                    }
                }
            }, {
                '$project': {
                    '_id': 0, 
                    'averageDuration': {
                        '$divide': [
                            '$totalDuration', '$totalCount'
                        ]
                    }
                }
            }
        ])).to_list(None)

        if calls:
            response.update({
                "aht": int(calls[0].get("averageDuration"))
            })
        else:
            response.update({
                "aht": 0
            })


    async def talk_time_helper(self, counsellor: dict, response: dict, date_range: dict|None = None) -> None:
        """Calculate total talk time and update the response dict.

        Params:
            counsellor (dict): Current counsellor details
            response (dict): Response data model.
            date_range (dict|None): Must be the combination of start_date and end_date
        """
        and_condition_list = [
            await self.get_common_match_stage_info(counsellor.get("_id")),
            {
                "$or": [
                    {
                        "status": "Call Complete"
                    },
                    {
                        "status": "ANSWER"
                    }
                ]
            }
        ]

        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
            and_condition_list.insert(0, {
                "starttime": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            })
            
        calls = await (DatabaseConfiguration().call_activity_collection.aggregate([
            {
                "$match": {
                    "$and": and_condition_list
                }
            }
        ])).to_list(None)

        total_duration = 0

        for call in calls:
            total_duration += call.get("duration")

        response.update({
            "talk_time": total_duration
        })


    async def check_in_out_hours_helper(self, counsellor: dict, response: dict, date_range: dict) -> None:
        """Calculate total check in and out hours and update the response dict.

        Params:
            counsellor (dict): Current counsellor details
            response (dict): Response data model.
            date_range (dict): Must be the combination of start_date and end_date
        """
        match_stage = {
            "user_id": counsellor.get("_id")
        }

        if date_range:
            match_stage = await self.update_match_stage_by_date_range(match_stage, date_range)

        pipeline = await self.get_common_pipeline_stages_info(match_stage)

        pipeline.extend([
            {
                '$group': {
                    '_id': None, 
                    'logs': {
                        '$push': {
                            'datetime': '$datetime', 
                            'check_in_status': '$check_in_status'
                        }
                    }
                }
            }, {
                '$project': {
                    'checkInPairs': {
                        '$map': {
                            'input': {
                                '$range': [
                                    0, {
                                        '$subtract': [
                                            {
                                                '$size': '$logs'
                                            }, 1
                                        ]
                                    }
                                ]
                            }, 
                            'as': 'index', 
                            'in': {
                                '$cond': [
                                    {
                                        '$and': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$arrayElemAt': [
                                                            '$logs.check_in_status', '$$index'
                                                        ]
                                                    }, True
                                                ]
                                            }, {
                                                '$eq': [
                                                    {
                                                        '$arrayElemAt': [
                                                            '$logs.check_in_status', {
                                                                '$add': [
                                                                    '$$index', 1
                                                                ]
                                                            }
                                                        ]
                                                    }, False
                                                ]
                                            }
                                        ]
                                    }, {
                                        'checkIn': {
                                            '$arrayElemAt': [
                                                '$logs.datetime', '$$index'
                                            ]
                                        }, 
                                        'checkOut': {
                                            '$arrayElemAt': [
                                                '$logs.datetime', {
                                                    '$add': [
                                                        '$$index', 1
                                                    ]
                                                }
                                            ]
                                        }
                                    }, None
                                ]
                            }
                        }
                    }, 
                    'checkOutPairs': {
                        '$map': {
                            'input': {
                                '$range': [
                                    0, {
                                        '$subtract': [
                                            {
                                                '$size': '$logs'
                                            }, 1
                                        ]
                                    }
                                ]
                            }, 
                            'as': 'index', 
                            'in': {
                                '$cond': [
                                    {
                                        '$and': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$arrayElemAt': [
                                                            '$logs.check_in_status', '$$index'
                                                        ]
                                                    }, False
                                                ]
                                            }, {
                                                '$eq': [
                                                    {
                                                        '$arrayElemAt': [
                                                            '$logs.check_in_status', {
                                                                '$add': [
                                                                    '$$index', 1
                                                                ]
                                                            }
                                                        ]
                                                    }, True
                                                ]
                                            }
                                        ]
                                    }, {
                                        'checkOut': {
                                            '$arrayElemAt': [
                                                '$logs.datetime', '$$index'
                                            ]
                                        }, 
                                        'checkIn': {
                                            '$arrayElemAt': [
                                                '$logs.datetime', {
                                                    '$add': [
                                                        '$$index', 1
                                                    ]
                                                }
                                            ]
                                        }
                                    }, None
                                ]
                            }
                        }
                    }
                }
            }, {
                '$project': {
                    'checkInPairs': {
                        '$filter': {
                            'input': '$checkInPairs', 
                            'as': 'pair', 
                            'cond': {
                                '$ne': [
                                    '$$pair', None
                                ]
                            }
                        }
                    }, 
                    'checkOutPairs': {
                        '$filter': {
                            'input': '$checkOutPairs', 
                            'as': 'pair', 
                            'cond': {
                                '$ne': [
                                    '$$pair', None
                                ]
                            }
                        }
                    }
                }
            }, {
                '$project': {
                    'totalCheckInTimeInSeconds': {
                        '$sum': {
                            '$map': {
                                'input': '$checkInPairs', 
                                'as': 'pair', 
                                'in': {
                                    '$divide': [
                                        {
                                            '$subtract': [
                                                '$$pair.checkOut', '$$pair.checkIn'
                                            ]
                                        }, 1000
                                    ]
                                }
                            }
                        }
                    }, 
                    'totalCheckOutTimeInSeconds': {
                        '$sum': {
                            '$map': {
                                'input': '$checkOutPairs', 
                                'as': 'pair', 
                                'in': {
                                    '$divide': [
                                        {
                                            '$subtract': [
                                                '$$pair.checkIn', '$$pair.checkOut'
                                            ]
                                        }, 1000
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        ])

        check_in_out = await (DatabaseConfiguration().check_in_out_log.aggregate(pipeline)).to_list(None)

        if check_in_out:
            response.update({
                "check_in_duration_sec": int(check_in_out[0].get("totalCheckInTimeInSeconds", 0)),
                "check_out_duration_sec": int(check_in_out[0].get("totalCheckOutTimeInSeconds", 0))
            })
        else:
            response.update({
                "check_in_duration_sec": 0,
                "check_out_duration_sec": 0
            })


    async def counsellor_status_helper(self, counsellor: dict, response: dict) -> None:
        """Counsellor status update in response

        Params:
            counsellor (dict): Current counsellor details
            response (dict): Response data model.
        """
        call = await DatabaseConfiguration().call_activity_collection.find_one({
            "$and": [
                {
                    "$or": [
                        {
                            "call_from": counsellor.get("_id")
                        },
                        {
                            "call_to": counsellor.get("_id")
                        }
                    ]
                },
                {
                    "$or": [
                        {
                            "status": "CONNECTING"
                        },
                        {
                            "status": "Originate"
                        }
                    ]
                }
            ]
        })

        user = await DatabaseConfiguration().user_collection.find_one({
            "_id": counsellor.get("_id"),
            "role.role_name": "college_counselor"
        })

        reason = user.get("reason") if user and user.get("check_in_status")==False else {"title": None, "icon": None}

        if call:
            status = "On Call"
        
        elif counsellor.get("check_in_status"):
            status = "Active"

        else:
            status = "Inactive"

        response.update({
            "counsellor_status": status,
            "reason": reason
        })


    async def counsellor_data_helper(self, quick_filter: str, activity_status: list[str], date_range: dict|None, sort: bool, sort_name: str|None, sort_type: str|None, college_id: list) -> list:
        """Counsellor call details helper for collecting information about counsellor activity.

        Params:
            quick_filter (str): Nmae of quick filter
            activity_status (list[str]): list of reasons of inactive counsellor for sorting
            date_range (dict | None): date range which data has to be sort.
            sort (bool): Apply sort or not?
            sort_name (str | None): Field name which has to be sort
            sort_type (str | None): It denotes asc or dsc.

        Returns:
            list: data response of all counsellors.
        """
        counsellors = await (DatabaseConfiguration().user_collection.aggregate([
            {
                "$match": {
                    "role.role_name": "college_counselor",
                    "is_activated": True,
                    "associated_colleges": {
                        "$in": college_id
                    }
                }
            }
        ])).to_list(None)

        data = []

        for counsellor in counsellors:

            counsellor_reason = counsellor.get("reason", {}).get("title")

            if activity_status and not counsellor.get("check_in_status") and counsellor_reason not in activity_status:
                if "Other" in activity_status:
                    all_reason_data = await (DatabaseConfiguration().check_out_reason.aggregate([{"$match": {"title": {"$ne": "Other"}}}])).to_list(None)
                    all_reason_list = []
                    for reason in all_reason_data:
                        all_reason_list.append(reason.get("title"))
                    
                    if counsellor_reason in all_reason_list:
                        continue
                    
                else:
                    continue

            response = {
                "id": str(counsellor.get("_id")),
                "caller_name": utility_obj.name_can(counsellor)
            }

            await self.counsellor_status_helper(counsellor, response)

            if quick_filter and response.get("counsellor_status") != quick_filter:
                continue

            await self.check_in_out_hours_helper(counsellor, response, date_range)

            await self.talk_time_helper(counsellor, response, date_range)

            await self.average_handling_time_helper(counsellor, response, date_range)

            await self.ideal_duration_helper(counsellor, response, date_range)

            await self.last_call_time_helper(counsellor, response, date_range)

            await self.first_check_in_helper(counsellor, response, date_range)

            await self.last_check_out_helper(counsellor, response, date_range)

            data.append(response)

        sorted_data = data
        if sort:
            sorted_data = sorted(data, key=lambda x: x.get(sort_name), reverse=True if sort_type == 'dsc' else False)

        return sorted_data