"""
Missed call dashboard related functions
"""
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from datetime import date
from app.core.custom_error import CustomError

class MissedCallDashboard:
    """
    Missed call dashboard data related functions
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
        match_stage = {
            '$match': {
                'status': {
                    '$in': [
                        'Missed', 'BUSY', 'CANCEL', 'NOANSWER'
                    ]
                }
            }
        }
        pipeline.extend(
            [
                {
                    '$facet': {
                        'missed_calls': [
                            match_stage, {
                                '$group': {
                                    '_id': None, 
                                    'total_missed_calls': {
                                        '$sum': 1
                                    }
                                }
                            }
                        ], 
                        'converted_to_lead': [
                            match_stage, {
                                '$lookup': {
                                    'from': 'studentsPrimaryDetails', 
                                    'localField': 'call_from', 
                                    'foreignField': '_id', 
                                    'as': 'student_primary_details'
                                }
                            }, {
                                '$match': {
                                    'student_primary_details.lead_source.utm_source': 'missed call'
                                }
                            }, {
                                '$group': {
                                    '_id': None, 
                                    'total_converted_to_lead': {
                                        '$sum': 1
                                    }
                                }
                            }
                        ], 
                        'converted_to_application': [
                            match_stage, {
                                '$lookup': {
                                    'from': 'studentApplicationForms', 
                                    'localField': 'application', 
                                    'foreignField': '_id', 
                                    'as': 'student_application_forms'
                                }
                            }, {
                                '$match': {
                                    'student_primary_details.lead_source.utm_source': 'missed call', 
                                    'student_application_forms.payment_info.status': 'captured'
                                }
                            }, {
                                '$group': {
                                    '_id': None, 
                                    'total_converted_to_application': {
                                        '$sum': 1
                                    }
                                }
                            }
                        ], 
                        'responded_calls': [
                            {
                                '$match': {
                                    'type': 'Outbound', 
                                    '$expr': {
                                        '$eq': [
                                            '$call_from_number', '$call_to_number'
                                        ]
                                    }
                                }
                            }, {
                                '$count': 'total_responded_calls'
                            }
                        ], 
                        'interested_percentage': [
                            {
                                '$lookup': {
                                    'from': 'leadsFollowUp', 
                                    'localField': 'application', 
                                    'foreignField': 'application_id', 
                                    'as': 'lead_follow_up'
                                }
                            }, {
                                '$match': {
                                    'lead_follow_up.lead_stage': 'interested', 
                                    'student_primary_details.lead_source.utm_source': 'missed call'
                                }
                            }, {
                                '$count': 'total_interested'
                            }
                        ]
                    }
                }, {
                    '$addFields': {
                        'total_missed_calls': {
                            '$ifNull': [
                                {
                                    '$arrayElemAt': [
                                        '$missed_calls.total_missed_calls', 0
                                    ]
                                }, 0
                            ]
                        }, 
                        'total_converted_to_lead': {
                            '$ifNull': [
                                {
                                    '$arrayElemAt': [
                                        '$converted_to_lead.total_converted_to_lead', 0
                                    ]
                                }, 0
                            ]
                        }, 
                        'total_converted_to_application': {
                            '$ifNull': [
                                {
                                    '$arrayElemAt': [
                                        '$converted_to_application.total_converted_to_application', 0
                                    ]
                                }, 0
                            ]
                        }, 
                        'total_responded_calls': {
                            '$ifNull': [
                                {
                                    '$arrayElemAt': [
                                        '$responded_calls.total_responded_calls', 0
                                    ]
                                }, 0
                            ]
                        }, 
                        'total_interested': {
                            '$ifNull': [
                                {
                                    '$arrayElemAt': [
                                        '$interested_percentage.total_interested', 0
                                    ]
                                }, 0
                            ]
                        }
                    }
                }, {
                    '$project': {
                        'total_missed_calls': 1, 
                        'total_converted_to_lead': 1, 
                        'total_converted_to_application': 1, 
                        'total_responded_calls': 1, 
                        'total_interested': 1
                    }
                }
            ]
        )

        try:
            result = await (DatabaseConfiguration().call_activity_collection.aggregate(pipeline)).to_list(None)
        except Exception as error:
            raise CustomError("Something want wrong from database.")

        if result:
            result = result[0]

            converted_lead = await utility_obj.get_percentage_difference_with_position(result.pop("total_converted_to_lead"), result.get("total_missed_calls"))
            converted_application = await utility_obj.get_percentage_difference_with_position(result.pop("total_converted_to_application"), result.get("total_missed_calls"))
            interested_lead = await utility_obj.get_percentage_difference_with_position(result.pop("total_interested"), result.get("total_missed_calls"))
            result.update({"converted_to_lead_percentage": converted_lead.get("percentage", 0)})
            result.update({"converted_to_paid_application_percentage": converted_application.get("percentage", 0)})
            result.update({"interested_percentage": interested_lead.get("percentage", 0)})
            return result
        return {}


    async def header_data_helper(self, date_range: dict, change_indicator: str) -> dict:
        """
        Missed call dashboard header data filter function helper

        Params:
            date_range (_type_): Date range for filtering
            change_indicator (_type_): Change indicator filtering

        Returns:
            dict: Response data
        """
        header_data = await self.date_data_helper(date_range)

        start_date, middle_date, previous_date = await utility_obj. \
            get_start_date_and_end_date_by_change_indicator(change_indicator)

        previous_date_data = await self.date_data_helper(date_range={"start_date": str(start_date),
                    "end_date": str(middle_date)})
        current_date_data = await self.date_data_helper(date_range={"start_date": str(previous_date),
                    "end_date": str(date.today())})
        
        total_calls_change_indicator = await utility_obj.get_percentage_difference_with_position(previous_date_data.get("total_missed_calls", 0), current_date_data.get("total_missed_calls", 0))

        header_data.update({
            "total_calls_change_indicator": {
                "total_missed_calls_perc_indicator": total_calls_change_indicator.get("percentage", 0),
                "total_missed_calls_pos_indicator": total_calls_change_indicator.get("position", "equal")
            }
        })

        return header_data