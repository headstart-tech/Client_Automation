"""
Call quality data related functions
"""
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from datetime import date
from app.core.custom_error import CustomError
from bson import ObjectId

class CallQuality:
    """
    Call quality data related functions
    """
    
    async def date_data_helper(self, user: dict, date_range: dict) -> dict:
        """
        Fetch call details within a date range

        Params:
            user (dict): Counsellor data for retrieving their call details
            date_range (dict): Date range containing start date and end date.

        Returns:
            dict: Returns data count
        """

        pipeline = []
        match_case = {
            "$match": {
                "$or": [
                    {"call_from": user.get("_id")},
                    {"call_to": user.get("_id")}
                ],
                "duration": {
                    "$exists": True
                }
            }
        }
        
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'),
                date_range.get('end_date')
            )
            match_case["$match"].update({"created_at": {"$gte": start_date, "$lte": end_date}})

        pipeline.extend([
            match_case,
            {
                '$facet': {
                    'dailyData': [
                        {
                            '$group': {
                                '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$starttime'}},
                                'dailyCallCount': {'$sum': 1},
                                'totalDuration': {'$sum': '$duration'}
                            }
                        },
                        {
                            '$group': {
                                '_id': None,
                                'totalDays': {'$sum': 1},
                                'totalCalls': {'$sum': '$dailyCallCount'},
                                'totalDuration': {'$sum': '$totalDuration'}
                            }
                        },
                        {
                            '$project': {
                                '_id': 0,
                                'averageCallsPerDay': {'$divide': ['$totalCalls', '$totalDays']},
                                'averageDuration': {'$divide': ['$totalDuration', '$totalCalls']}
                            }
                        }
                    ],
                    'missedCalls': [
                        {
                            '$match': {
                                'type': {'$in': ['Inbound', 'CallBack']},
                                'status': {'$in': ['BUSY', 'CANCEL', 'NOANSWER', 'Missed']}
                            }
                        },
                        {'$count': 'missedCallCount'}
                    ],
                    'callQuality': [
                        {
                            '$match': {'qced': {'$exists': True}}
                        },
                        {
                            '$project': {'call_quality': {'$arrayElemAt': ['$qced.call_quality_score', 0]}}
                        },
                        {
                            '$group': {
                                '_id': None,
                                'average_call_quality': {'$avg': '$call_quality'}
                            }
                        }
                    ]
                }
            },
            {
                '$project': {
                    'averageCallsPerDay': {'$arrayElemAt': ['$dailyData.averageCallsPerDay', 0]},
                    'averageDuration': {'$arrayElemAt': ['$dailyData.averageDuration', 0]},
                    'missedCallCount': {'$arrayElemAt': ['$missedCalls.missedCallCount', 0]},
                    'callQuality': {'$arrayElemAt': ['$callQuality.average_call_quality', 0]}
                }
            }
        ])

        calls = await DatabaseConfiguration().call_activity_collection.aggregate(pipeline).to_list(None)
        calls = calls[0] if calls else {}

        return {
            "id": str(user.get("_id")),
            "counsellor_name": utility_obj.name_can(user),
            "avg_call_per_day": utility_obj.format_float_to_2_places(calls.get("averageCallsPerDay", 0)),
            "average_duration": utility_obj.format_float_to_2_places(calls.get("averageDuration", 0)),
            "missed_call_count": calls.get("missedCallCount", 0),
            "call_quality": utility_obj.format_float_to_2_places((calls.get("callQuality", 0) / 5) * 100)
        }

    async def call_quality_data_helper(self, date_range: dict, change_indicator: str, page_num: int, page_size: int, college: dict) -> dict:
        """
        Telephony dashboard header data filter function helper

        Params:
            date_range (dict): Date range for filtering
            change_indicator (str): Change indicator filtering
            page_num (int): Page number
            page_size (int): Number of data in one page

        Returns:
            dict: Response data
        """
        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
        
        users_pipeline = [
            {"$match": {"is_activated": True, "role.role_name": "college_counselor", "associated_colleges": {"$in": [ObjectId(college.get("id"))]}}},
            {"$facet": {
                "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                "totalCount": [{"$count": "count"}]
            }}
        ]

        users = await DatabaseConfiguration().user_collection.aggregate(users_pipeline).to_list(None)
        users = users[0] if users else {}
        users, count = users.get("paginated_results", []), users.get("totalCount", [])[0].get("count", 0) if users.get("totalCount") else 0

        response = []

        for user in users:
            data = await self.date_data_helper(user, date_range)

            if change_indicator is not None:
                start_date, middle_date, previous_date = await utility_obj.get_start_date_and_end_date_by_change_indicator(change_indicator)

                previous_date_data = await self.date_data_helper(user, date_range={"start_date": str(start_date), "end_date": str(middle_date)})
                current_date_data = await self.date_data_helper(user, date_range={"start_date": str(previous_date), "end_date": str(date.today())})

                average_call_change_indicator = await utility_obj.get_percentage_difference_with_position(previous_date_data.get("avg_call_per_day", 0), current_date_data.get("avg_call_per_day", 0))
                avg_duration_change_indicator = await utility_obj.get_percentage_difference_with_position(previous_date_data.get("average_duration", 0), current_date_data.get("average_duration", 0))
                missed_call_change_indicator = await utility_obj.get_percentage_difference_with_position(previous_date_data.get("missed_call_count", 0), current_date_data.get("missed_call_count", 0))

                data.update({
                    "average_call_per_day_change_indicator": {
                        "average_call_per_day_perc_indicator": average_call_change_indicator.get("percentage", 0),
                        "average_call_per_day_pos_indicator": average_call_change_indicator.get("position", "equal")
                    },
                    "avg_duration_change_indicator": {
                        "avg_duration_perc_indicator": avg_duration_change_indicator.get("percentage", 0),
                        "avg_duration_pos_indicator": avg_duration_change_indicator.get("position", "equal")
                    },
                    "missed_call_change_indicator": {
                        "missed_call_perc_indicator": missed_call_change_indicator.get("percentage", 0),
                        "missed_call_pos_indicator": missed_call_change_indicator.get("position", "equal")
                    }
                })

            response.append(data)

        return response, count

    async def call_quality_total_data_helper(self, date_range: dict) -> dict:
        """
        Call activity total summary data

        Params:
            date_range (dict): Date range

        Returns:
            dict: Total response data
        """
        pipeline = [
            {
                "$match": {
                    "duration": {"$exists": True}
                }
            }, {
                '$facet': {
                    'dailyData': [
                        {
                            '$group': {
                                '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$starttime'}},
                                'dailyCallCount': {'$sum': 1},
                                'totalDuration': {'$sum': '$duration'}
                            }
                        }, {
                            '$group': {
                                '_id': None,
                                'totalDays': {'$sum': 1},
                                'totalCalls': {'$sum': '$dailyCallCount'},
                                'totalDuration': {'$sum': '$totalDuration'}
                            }
                        }, {
                            '$project': {
                                '_id': 0,
                                'averageCallsPerDay': {'$divide': ['$totalCalls', '$totalDays']},
                                'averageDuration': {'$divide': ['$totalDuration', '$totalCalls']}
                            }
                        }
                    ],
                    'missedCalls': [
                        {
                            '$match': {
                                'status': {'$in': ['BUSY', 'CANCEL', 'NOANSWER', 'Missed']}
                            }
                        }, {
                            '$count': 'missedCallCount'
                        }
                    ],
                    'callQuality': [
                        {
                            '$match': {'qced': {'$exists': True}}
                        }, {
                            '$project': {'call_quality': {'$arrayElemAt': ['$qced.call_quality_score', 0]}}
                        }, {
                            '$group': {
                                '_id': None,
                                'average_call_quality': {'$avg': '$call_quality'}
                            }
                        }
                    ]
                }
            }, {
                '$project': {
                    'averageCallsPerDay': {'$arrayElemAt': ['$dailyData.averageCallsPerDay', 0]},
                    'averageDuration': {'$arrayElemAt': ['$dailyData.averageDuration', 0]},
                    'missedCallCount': {'$arrayElemAt': ['$missedCalls.missedCallCount', 0]},
                    'callQuality': {'$arrayElemAt': ['$callQuality.average_call_quality', 0]}
                }
            }
        ]

        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'),
                date_range.get('end_date')
            )
            pipeline[0]['$match'].update({
                "created_at": {"$gte": start_date, "$lte": end_date},
            })

        data = await DatabaseConfiguration().call_activity_collection.aggregate(pipeline).to_list(None)
        data = data[0] if data else {}

        return {
            "total_call_count": utility_obj.format_float_to_2_places(data.get("averageCallsPerDay", 0)),
            "total_call_duration": utility_obj.format_float_to_2_places(data.get("averageDuration", 0)),
            "missed_call_count": data.get("missedCallCount", 0),
            "call_quality": utility_obj.format_float_to_2_places((data.get("callQuality", 0) / 5) * 100)
        }
