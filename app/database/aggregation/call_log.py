"""
This file contain class and functions related to call logs
"""
from datetime import datetime

from bson import ObjectId

from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration


class CallLog:
    """
    Contain functions related to call log activities
    """

    async def get_call_logs(self, mobile_number):
        """
        Get call logs like inbound call count, outbound call count, total call
         duration and call timelines
        """
        result = DatabaseConfiguration().call_activity_collection.aggregate([
            {
                '$facet': {
                    'total_inbound_call': [
                        {
                            '$match': {
                                'type': "Outbound",
                                'call_to': mobile_number
                            }
                        },
                        {"$count": "count"}],
                    'total_outbound_call': [
                        {
                            '$match': {
                                'type': "Inbound",
                                'call_from': mobile_number
                            }
                        },
                        {"$count": "count"}],
                }
            }
        ])
        total_outbound_call, total_inbound_call = 0, 0
        async for document in result:
            try:
                total_inbound_call = document.get('total_inbound_call')[0].get(
                    'count')
                total_outbound_call = document.get('total_outbound_call')[
                    0].get('count')
            except IndexError:
                pass
        return total_inbound_call, total_outbound_call

    async def get_call_durations_and_timelines(
            self, mobile_number: int | str, start_date: datetime | None = None,
            end_date: datetime | None = None) -> tuple:
        """
        Get total call duration and timeline of call
        """
        pipeline = [
            {
                '$match': {
                    "$or": [
                        {"call_to": mobile_number},
                        {"call_from": mobile_number},
                        {"call_to_number": int(mobile_number)},
                        {"call_from_number": int(mobile_number)}
                    ]
                }
            },
            {"$project": {
                "call_started_at": {
                    '$cond': {
                        'if': {
                            '$ne': [
                                '$call_started_at', None
                            ]
                        }, 
                        'then': {
                            '$dateFromString': {
                                'dateString': '$call_started_at', 
                                'timezone': 'Asia/Kolkata'
                            }
                        }, 
                        'else': {
                            '$dateFromString': {
                                'dateString': '$starttime', 
                                'timezone': 'UTC'
                            }
                        }
                    }
                },
                "call_from_name": 1,
                "call_from": 1,
                "call_to_name": 1,
                "call_to": 1,
                "duration": 1,
                "type": 1
            }},
            {"$sort": {"call_started_at": -1}},
        ]

        if start_date and end_date:
            pipeline.insert(
                2, {"$match": {"call_started_at":
                                   {"$gte": start_date, "$lte": end_date}}})
        
        result = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)

        total_outbound_call, total_inbound_call, outbound_call_duration, \
            inbound_call_duration, timelines, gap_bet_timeline, prev_date = \
            0, 0, 0, 0, [], 0, None
        async for data in result:
            call_started_at = data.get('call_started_at')
            call_duration = data.get('duration', 0)
            call_from_name = data.get('call_from_name')
            call_to_name = data.get('call_to_name')
            call_type = data.get('type')
            formatted_time = utility_obj.get_local_time(call_started_at)
            if prev_date is not None:
                days_gap = abs(call_started_at - prev_date)
                gap_bet_timeline = days_gap.days
                timelines[-1].update({
                    "gap_bet_timeline": gap_bet_timeline})
            if call_type == "Outbound":
                outbound_call_duration += int(call_duration)
                total_outbound_call += 1
                message = f"{call_from_name} (Counsellor) called " \
                          f"{call_to_name} and had a conversation for " \
                          f"{call_duration} Seconds at {formatted_time}"
                user_type = "counselor"
            else:
                total_inbound_call += 1
                inbound_call_duration += int(call_duration)
                message = f"{call_from_name} called {call_to_name} " \
                          f"(Counsellor) and had a conversation for " \
                          f"{call_duration} Seconds at {formatted_time}"
                user_type = "user"
            prev_date = data.get('call_started_at')
            timelines.append({"message": message, "call_type": call_type,
                              "call_duration": call_duration,
                              "call_from_name": call_from_name,
                              "call_to_name": call_to_name,
                              "timestamp": formatted_time,
                              "action_type": user_type})
        return total_outbound_call, total_inbound_call, inbound_call_duration, \
            outbound_call_duration, timelines

    async def get_call_duration(self, mobile_number: str | int) -> tuple:
        """
        Get call duration based on mobile number.

        Params:
            mobile_number (str | int): Mobile number of student.

        Returns:
            tuple: A tuple which contains total inbound and outbound call
                duration.
        """
        group_stage = {
            '$group': {
                '_id': '', 
                'total_talk_time': {
                    '$sum': {
                        '$add': [
                            {
                                '$ifNull': [
                                    '$duration', 0
                                ]
                            }, {
                                '$ifNull': [
                                    '$call_duration', 0
                                ]
                            }
                        ]
                    }
                }
            }
        }
        project_stage = {
            '$project': {
                '_id': 0, 
                'total_talk_time': {
                    '$sum': '$total_talk_time'
                }
            }
        }
        result = DatabaseConfiguration().call_activity_collection.aggregate([
            {
                '$facet': {
                    'total_outbound_call': [
                        {
                            '$match': {
                                'type': 'Outbound', 
                                '$or': [
                                    {'call_to': mobile_number,},
                                    {'call_to_number': int(mobile_number)}
                                ]
                            }
                        }, group_stage, project_stage
                    ], 
                    'total_inbound_call': [
                        {
                            '$match': {
                                'type': 'Inbound', 
                                '$or': [
                                    {'call_from': mobile_number,},
                                    {'call_from_number': int(mobile_number)}
                                ]
                            }
                        }, group_stage, project_stage
                    ]
                }
            }
        ])
        
        total_outbound_duration, total_inbound_duration = 0, 0
        async for document in result:
            total_inbound_duration = document.get('total_inbound_call')[
                0].get('total_talk_time', 0) if document.get('total_inbound_call') else 0
            total_outbound_duration = document.get('total_outbound_call')[
                0].get('total_talk_time', 0) if document.get('total_outbound_call') else 0
            
        return total_inbound_duration, total_outbound_duration

    async def connected_and_missed_call_count(
            self, counselor_ids: list[ObjectId], start_date: datetime | None,
            end_date: datetime | None) -> tuple:
        """
        Get connected call and missed call count summary based on counselor
        ids.

        Params:
            counselor_ids (list[ObjectId]): A list which contains counselor
                ids. e.g., [ObjectId("123456789012345678901234")]
            start_date (datetime | None): Either none or start date which
                useful for filter data.
            end_date (datetime | None): Either none or end date which
                useful for filter data.

        Returns:
            tuple: A tuple which contains connected call count and missed call
                count.
        """
        pipeline = [
            {
                '$match': {
                    "$or": [
                        {"call_to": {"$in": counselor_ids}},
                        {"call_from": {"$in": counselor_ids}}
                    ]
                }
            },
            {
                '$facet': {
                    'total_missed_call': [
                        {
                            '$match': {
                                "call_duration": 0
                            }
                        },
                        {"$count": "count"}],
                    'total_connected_call': [
                        {
                            '$match': {
                                "call_duration": {"$gt": 0.1}
                            }
                        },
                        {"$count": "count"}],
                }
            }
        ]
        if start_date and end_date:
            pipeline.insert(1, {"$project": {
                "call_started_at": {"$dateFromString": {
                    "dateString": "$call_started_at",
                    "timezone": "Asia/Kolkata"
                }}, "call_duration": 1
            }})
            pipeline.insert(
                2, {"$match": {"call_started_at":
                                   {"$gte": start_date, "$lte": end_date}}})
        result = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)
        total_missed_call, total_connected_call = 0, 0
        async for document in result:
            try:
                total_connected_call = document.get('total_connected_call')[
                    0].get(
                    'count')
                total_missed_call = document.get('total_missed_call')[
                    0].get('count')
            except IndexError:
                pass
        return total_connected_call, total_missed_call
