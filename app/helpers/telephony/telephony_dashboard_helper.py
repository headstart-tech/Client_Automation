"""
Telephony dashboard related functions
"""
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from datetime import date
from app.core.custom_error import CustomError

class TelephonyDashboard:
    """
    Telephony dashboard data related functions
    """
    async def date_data_helper(self, date_range: dict) -> dict:
        """
        Calls details fetch with date range

        Params:
            date_range (dict): Date range contains start date and end date.

        Returns:
            dict: Returns data count
        """
        pipeline = []
        if date_range and date_range.get("start_date") and date_range.get("end_date"):
            start_date, end_date = await utility_obj.date_change_format(date_range.get("start_date"),
                                                                        date_range.get("end_date"))
            pipeline.append({
                "$match": {
                    "created_at": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                }
            })
        pipeline.append({
            '$group': {
                '_id': None, 
                'total_calls': {
                    '$sum': 1
                }, 
                'outbound_calls': {
                    '$sum': {
                        '$cond': {
                            'if': {
                                '$eq': [
                                    '$type', 'Outbound'
                                ]
                            }, 
                            'then': 1, 
                            'else': 0
                        }
                    }
                }, 
                'inbound_calls': {
                    '$sum': {
                        '$cond': {
                            'if': {
                                '$in': ['$type', ['Inbound', 'CallBack']]
                            }, 
                            'then': 1, 
                            'else': 0
                        }
                    }
                }, 
                'total_duration': {
                    '$sum': '$duration'
                }, 
                'outbound_duration': {
                    '$sum': {
                        '$cond': {
                            'if': {
                                '$eq': [
                                    '$type', 'Outbound'
                                ]
                            }, 
                            'then': '$duration', 
                            'else': 0
                        }
                    }
                }, 
                'inbound_duration': {
                    '$sum': {
                        '$cond': {
                            'if': {
                                '$in': ['$type', ['Inbound', 'CallBack']]
                            }, 
                            'then': '$duration', 
                            'else': 0
                        }
                    }
                }, 
                'outbound_calls_gt_90_sec': {
                    '$sum': {
                        '$cond': {
                            'if': {
                                '$and': [
                                    {
                                        '$eq': [
                                            '$type', 'Outbound'
                                        ]
                                    }, {
                                        '$gt': [
                                            '$duration', 90
                                        ]
                                    }
                                ]
                            }, 
                            'then': 1, 
                            'else': 0
                        }
                    }
                }, 
                'inbound_calls_gt_90_sec': {
                    '$sum': {
                        '$cond': {
                            'if': {
                                '$and': [
                                    {
                                        '$in': ['$type', ['Inbound', 'CallBack']]
                                    }, {
                                        '$gt': [
                                            '$duration', 90
                                        ]
                                    }
                                ]
                            }, 
                            'then': 1, 
                            'else': 0
                        }
                    }
                }, 
                'total_calls_gt_90_sec': {
                    '$sum': {
                        '$cond': {
                            'if': {
                                '$gt': [
                                    '$duration', 90
                                ]
                            }, 
                            'then': 1, 
                            'else': 0
                        }
                    }
                }, 
                'total_missed_calls': {
                    '$sum': {
                        '$cond': {
                            'if': {
                                '$in': [
                                    '$status', [
                                        'NOANSWER', 'BUSY', 'CANCEL', 'Missed'
                                    ]
                                ]
                            }, 
                            'then': 1, 
                            'else': 0
                        }
                    }
                }
            }
        })

        try:
            result = await (DatabaseConfiguration().call_activity_collection.aggregate(pipeline)).to_list(None)
        except Exception as error:
            raise CustomError("Something want wrong from database.")

        if result:
            return result[0]
        return {}


    async def header_data_helper(self, date_range: dict, change_indicator: str) -> dict:
        """
        Telephony dashboard header data filter function helper

        Params:
            date_range (_type_): Date range for filtering
            change_indicator (_type_): Change indicator filtering

        Returns:
            dict: Response data
        """
        header_data = await self.date_data_helper(date_range)

        active_counsellor_count = await DatabaseConfiguration().user_collection.count_documents({
            "check_in_status": True
        })

        data = {
            "total_calls": header_data.get("total_calls", 0),
            "outbound_calls": header_data.get("outbound_calls", 0),
            "inbound_calls": header_data.get("inbound_calls", 0),
            "total_duration": header_data.get("total_duration", 0),
            "outbound_duration": header_data.get("outbound_duration", 0),
            "inbound_duration": header_data.get("inbound_duration", 0),
            "outbound_calls_gt_90_sec": header_data.get("outbound_calls_gt_90_sec", 0),
            "inbound_calls_gt_90_sec": header_data.get("inbound_calls_gt_90_sec", 0),
            "total_calls_gt_90_sec": header_data.get("total_calls_gt_90_sec", 0),
            "total_missed_calls": header_data.get("total_missed_calls", 0),
            "active_counsellor_count": active_counsellor_count
        }

        if change_indicator is not None:
            start_date, middle_date, previous_date = await utility_obj. \
                get_start_date_and_end_date_by_change_indicator(change_indicator)

            previous_date_data = await self.date_data_helper(date_range={"start_date": str(start_date),
                        "end_date": str(middle_date)})
            current_date_data = await self.date_data_helper(date_range={"start_date": str(previous_date),
                        "end_date": str(date.today())})
            
            total_calls_change_indicator = await utility_obj.get_percentage_difference_with_position(previous_date_data.get("total_calls", 0), current_date_data.get("total_calls", 0))

            data.update({
                "total_calls_change_indicator": {
                    "total_calls_perc_indicator": total_calls_change_indicator.get("percentage", 0),
                    "total_calls_pos_indicator": total_calls_change_indicator.get("position", "equal")
                }
            })

        return data