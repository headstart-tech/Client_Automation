"""
This file contain class and functions of publisher_dashboard_router
"""
import datetime

from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.database.aggregation.get_all_applications import Application


class Publisher:
    """
    Contain functions related to publisher activities
    """

    async def leads_publisher_aggregation(self, source_name, start_date=None,
                                          end_date=None):
        """
        Count leads by source of publisher
        """
        pipeline = [
            {
                "$facet": {
                    "total_leads": [
                        {
                            "$match": {
                                "$or": []
                            }},
                        {"$count": "total"}],
                    "primary_source": [
                        {
                            "$match": {
                                "source.primary_source.utm_source": source_name
                            }
                        },
                        {"$count": "primary_source"}
                    ],
                    "secondary_source": [
                        {
                            "$match": {
                                "source.secondary_source."
                                "utm_source": source_name
                            }
                        },
                        {"$count": "secondary_source"}
                    ],
                    "tertiary_source": [
                        {
                            "$match": {
                                "source.tertiary_source."
                                "utm_source": source_name
                            }
                        },
                        {"$count": "tertiary_source"}
                    ]
                }
            },
            {"$project": {
                "total_leads": {"$arrayElemAt": ["$total_leads.total", 0]},
                "tertiary_source": {"$arrayElemAt": ["$tertiary_source."
                                                     "tertiary_source", 0]},
                "secondary_source": {"$arrayElemAt": ["$secondary_source."
                                                      "secondary_source", 0]},
                "primary_source": {"$arrayElemAt": ["$primary_source."
                                                    "primary_source", 0]}
            }}
        ]
        if start_date is not None and end_date is not None:
            pipeline[0].get("$facet", {}).get("total_leads", [])[0].get(
                "$match", {}).get("$or", []).extend([
                {"source.primary_source.utm_source": source_name,
                 "source.primary_source.utm_enq_date": {"$gte": start_date,
                                                        "$lte": end_date}},
                {"source.secondary_source.utm_source": source_name,
                 "source.secondary_source.utm_enq_date": {"$gte": start_date,
                                                          "$lte": end_date}},
                {"source.tertiary_source.utm_source": source_name,
                 "source.tertiary_source.utm_enq_date": {"$gte": start_date,
                                                         "$lte": end_date}}])
            pipeline[0].get("$facet", {}).get("primary_source")[0].get(
                "$match", {}).update(
                {"source.primary_source.utm_enq_date": {"$gte": start_date,
                                                        "$lte": end_date}})
            pipeline[0].get("$facet", {}).get("secondary_source")[0].get(
                "$match", {}).update(
                {"source.secondary_source.utm_enq_date": {"$gte": start_date,
                                                          "$lte": end_date}})
            pipeline[0].get("$facet", {}).get("tertiary_source")[0].get(
                "$match", {}).update(
                {"source.tertiary_source.utm_enq_date": {"$gte": start_date,
                                                         "$lte": end_date}})
        else:
            pipeline[0].get("$facet", {}).get("total_leads", {})[0].get(
                "$match", {}).get("$or").extend([
                {"source.primary_source.utm_source": source_name},
                {"source.secondary_source.utm_source": source_name},
                {"source.tertiary_source.utm_source": source_name}])
        result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            pipeline)
        async for total_count in result:
            if total_count is None:
                total_count = {}
            return total_count

    async def aggregation_application_based_on_source(self, source_name,
                                                      start_date=None,
                                                      end_date=None):
        pipeline = [
            {
                "$match": {"source.primary_source.utm_source": source_name}
            },
            {
                "$project": {
                    "_id": 1,
                    "source": 1
                }
            },
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": {
                        "student_id": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": ["$student_id", "$$student_id"]
                                }}
                        },
                        {
                            "$project": {
                                "_id": 1,
                                "declaration": 1,
                                "payment_info": 1,
                                "current_stage": 1,
                                "student_id": 1
                            }
                        },
                        {
                            "$group": {
                                "_id": "",
                                "submit_application": {
                                    "$sum": {"$cond": ["$declaration", 1, 0]}
                                },
                                "paid_application": {
                                    "$sum": {
                                        "$cond": [
                                            {
                                                "$eq": [
                                                    "$payment_info.status",
                                                    "captured",
                                                ]
                                            },
                                            1,
                                            0,
                                        ]
                                    }
                                },
                                "total_application": {
                                    "$sum": {
                                        "$cond": [
                                            {
                                                "$gte": ["$current_stage", 2]
                                            },
                                            1,
                                            0,
                                        ]
                                    }
                                }
                            }
                        }
                    ],
                    "as": "student_application"
                }
            },
            {
                "$unwind": {
                    "path": "$student_application"
                }
            },
            {
                "$group": {
                    "_id": "$source.primary_source.utm_source",
                    "total_application": {
                        "$sum": "$student_application.total_application"},
                    "paid_application": {
                        "$sum": "$student_application.paid_application"},
                    "submit_application": {
                        "$sum": "$student_application.submit_application"}
                }
            },
            {
                "$project": {
                    "source_name": "$_id",
                    "total_application": "$total_application",
                    "paid_application": "$paid_application",
                    "submit_application": "$submit_application"
                }
            }
        ]
        """
        Count paid application, submit application and  total_application
        """
        if start_date is not None and end_date is not None:
            pipeline[0].get("$match", {}).update(
                {"primary_source.utm_enq_date": {"$gte": start_date,
                                                 "$lte": end_date}})

        result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            pipeline)
        async for total_count in result:
            if total_count is None:
                total_count = {}
            return total_count
        

    async def lead_application_details_of_publisher(self, source_name: str, date_range: dict|None = None) -> dict:
        """Lead application details with pipeline and database calling

        Params:
            source_name (str): Name of the source of requested user
            date_range (dict | None, optional): Date range data (start_date and end_date). Defaults to None.

        Returns:
            dict: data set return with count values
        """
        pipeline = []
        if date_range and date_range.get("start_date") and date_range.get("end_date"):
            start_date, end_date = await utility_obj.date_change_format(date_range.get("start_date"),
                                                                        date_range.get("end_date"))
            pipeline.append({
                "$match": {
                    "enquiry_date": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                }
            })
        pipeline.extend([
            {
                '$lookup': {
                    'from': 'studentsPrimaryDetails', 
                    'localField': 'student_id', 
                    'foreignField': '_id', 
                    'as': 'student'
                }
            }, {
                '$unwind': '$student'
            }, {
                '$match': {
                    '$or': [
                        {
                            'student.source.primary_source.utm_source': source_name
                        }, {
                            'student.source.secondary_source.utm_source': source_name
                        }, {
                            'student.source.tertiary_source.utm_source': source_name
                        }
                    ]
                }
            }, {
                '$group': {
                    '_id': None, 
                    'total_application': {
                        '$sum': 1
                    }, 
                    'form_initiated_count': {
                        '$sum': {
                            '$cond': {
                                'if': {
                                    '$and': [
                                        {'$gte': ['$current_stage', 2]},
                                        {'$eq': ['$student.source.primary_source.utm_source', source_name]}
                                    ]
                                }, 
                                'then': 1, 
                                'else': 0
                            }
                        }
                    }, 
                    'primary_application_count': {
                        '$sum': {
                            '$cond': {
                                'if': {
                                    '$eq': [
                                        '$student.source.primary_source.utm_source', source_name
                                    ]
                                }, 
                                'then': 1, 
                                'else': 0
                            }
                        }
                    }, 
                    'secondary_application_count': {
                        '$sum': {
                            '$cond': {
                                'if': {
                                    '$eq': [
                                        '$student.source.secondary_source.utm_source', source_name
                                    ]
                                }, 
                                'then': 1, 
                                'else': 0
                            }
                        }
                    }, 
                    'tertiary_application_count': {
                        '$sum': {
                            '$cond': {
                                'if': {
                                    '$eq': [
                                        '$student.source.tertiary_source.utm_source', source_name
                                    ]
                                }, 
                                'then': 1, 
                                'else': 0
                            }
                        }
                    }, 
                    'total_paid_application': {
                        '$sum': {
                            '$cond': {
                                'if': {
                                    '$and': [
                                        {'$eq': ['$payment_info.status', 'captured']},
                                        {'$eq': ['$student.source.primary_source.utm_source', source_name]}
                                    ]
                                }, 
                                'then': 1, 
                                'else': 0
                            }
                        }
                    }, 
                    'total_submitted_application': {
                        '$sum': {
                            '$cond': {
                                'if': {
                                    '$and': [
                                        {'$eq': ['$declaration', True]},
                                        {'$eq': ['$student.source.primary_source.utm_source', source_name]}
                                    ]
                                }, 
                                'then': 1, 
                                'else': 0
                            }
                        }
                    }
                }
            }, {
                '$project': {
                    '_id': 0, 
                    'total_application': 1, 
                    'form_initiated_count': 1, 
                    'primary_application_count': 1, 
                    'secondary_application_count': 1, 
                    'tertiary_application_count': 1,
                    'total_paid_application': 1, 
                    'total_submitted_application': 1
                }
            }
        ])

        response = await (DatabaseConfiguration().studentApplicationForms.aggregate(pipeline)).to_list(None)

        if response:
            return response[0]
        return {}


    async def leads_count_based_on_publisher(self, source_name:str, change_indicator, date_range:dict|None=None) -> dict:
        """Lead application related data as per publisher

        Params:
            source_name (str): Name of the source of the requested publisher
            change_indicator (_type_): Change indicator data
            date_range (dict | None, optional): Date range for filteration. Defaults to None.

        Returns:
            dict: Response data with change indicator
        """

        header_data = await self.lead_application_details_of_publisher(source_name, date_range)

        data = {
            'total_application': header_data.get("total_application", 0), 
            'form_initiated_count': header_data.get("form_initiated_count", 0), 
            'primary_application_count': header_data.get("primary_application_count", 0), 
            'secondary_application_count': header_data.get("secondary_application_count", 0),
            'tertiary_application_count': header_data.get("tertiary_application_count"),
            'total_paid_application': header_data.get("total_paid_application", 0), 
            'total_submitted_application': header_data.get("total_submitted_application", 0)
        }

        if change_indicator is not None:
            start_date, middle_date, previous_date = await utility_obj. \
                get_start_date_and_end_date_by_change_indicator(change_indicator)
            
            previous_date_data = await self.lead_application_details_of_publisher(date_range={"start_date": str(start_date),
                        "end_date": str(middle_date)}, source_name=source_name)
            current_date_data = await self.lead_application_details_of_publisher(date_range={"start_date": str(previous_date),
                        "end_date": str(datetime.date.today())}, source_name=source_name)
            
            total_application_change_indicator = await utility_obj.get_percentage_difference_with_position(previous_date_data.get("total_application", 0), current_date_data.get("total_application", 0))
            form_initiated_count_change_indicator = await utility_obj.get_percentage_difference_with_position(previous_date_data.get("form_initiated_count", 0), current_date_data.get("form_initiated_count", 0))
            primary_application_count_change_indicator = await utility_obj.get_percentage_difference_with_position(previous_date_data.get("primary_application_count", 0), current_date_data.get("primary_application_count", 0))
            secondary_application_count_change_indicator = await utility_obj.get_percentage_difference_with_position(previous_date_data.get("secondary_application_count", 0), current_date_data.get("secondary_application_count", 0))
            tertiary_application_count_change_indicator = await utility_obj.get_percentage_difference_with_position(previous_date_data.get("tertiary_application_count", 0), current_date_data.get("tertiary_application_count", 0))
            total_paid_application_change_indicator = await utility_obj.get_percentage_difference_with_position(previous_date_data.get("total_paid_application", 0), current_date_data.get("total_paid_application", 0))
            total_submitted_application_change_indicator = await utility_obj.get_percentage_difference_with_position(previous_date_data.get("total_submitted_application", 0), current_date_data.get("total_submitted_application", 0))

            data.update({
                "total_application_change_indicator": {
                    "total_application_perc_indicator": total_application_change_indicator.get("percentage", 0),
                    "total_application_pos_indicator": total_application_change_indicator.get("position", "equal")
                },
                "form_initiated_count_change_indicator": {
                    "form_initiated_count_perc_indicator": form_initiated_count_change_indicator.get("percentage", 0),
                    "form_initiated_count_pos_indicator": form_initiated_count_change_indicator.get("position", "equal")
                },
                "primary_application_count_change_indicator":{
                    "primary_application_count_perc_indicator": primary_application_count_change_indicator.get("percentage", 0),
                    "primary_application_count_pos_indicator": primary_application_count_change_indicator.get("position", "equal")
                },
                "secondary_application_count_change_indicator": {
                    "secondary_application_count_perc_indicator": secondary_application_count_change_indicator.get("percentage", 0),
                    "secondary_application_count_pos_indicator": secondary_application_count_change_indicator.get("position", "equal")
                },
                "tertiary_application_count_change_indicator": {
                    "tertiary_application_count_perc_indicator": tertiary_application_count_change_indicator.get("percentage", 0),
                    "tertiary_application_count_pos_indicator": tertiary_application_count_change_indicator.get("position", "equal")
                },
                "total_paid_application_change_indicator": {
                    "total_paid_application_perc_indicator": total_paid_application_change_indicator.get("percentage", 0),
                    "total_paid_application_pos_indicator": total_paid_application_change_indicator.get("position", "equal")
                },
                "total_submitted_application_change_indicator": {
                    "total_submitted_application_perc_indicator": total_submitted_application_change_indicator.get("percentage", 0),
                    "total_submitted_application_pos_indicator": total_submitted_application_change_indicator.get("position", "equal")
                }
            })

        return data


    async def leads_count_based_on_publisher_source(self, user):
        """
        Get total count of leads based on publisher sources,
         primary_source, tertiary_ source and secondary_source
        """
        source_name = user.get("associated_source_value", "").lower()
        count_data = await self.leads_publisher_aggregation(
            source_name=source_name)
        count_data.update(
            {"primary_percentage": utility_obj.get_percentage_result(
                count_data.get("primary_source",
                               0),
                count_data.get("total_leads", 0)),
                "secondary_percentage": utility_obj.get_percentage_result(
                    count_data.get("secondary_source", 0),
                    count_data.get("total_leads", 0)),
                "tertiary_percentage": utility_obj.get_percentage_result(
                    count_data.get("tertiary_source", 0),
                    count_data.get("total_leads", 0))
            })
        return count_data

    async def get_uploaded_leads_count(self, publisher_id):
        """
        Get count of uploaded leads by publisher.

        Params:
            publisher_id (str): Publisher id whose uploaded leads count want to get.

        Returns:
            int: Count of uploaded leads by publisher.
        """
        start_date, end_date = await utility_obj.date_change_format(
            start_date=str(datetime.date.today()),
            end_date=str(datetime.date.today()),
        )
        result = DatabaseConfiguration().lead_upload_history.aggregate(
            pipeline=[
                {
                    '$match': {
                        "imported_by": publisher_id,
                        "uploaded_on": {"$gte": start_date, "$lte": end_date},
                    }
                },
                {
                    "$group": {"_id": "", "total_lead_upload": {"$sum": {
                        "$ifNull": ["$successful_lead_count", 0]
                    }}}
                }
            ]
        )
        async for data in result:
            return data.get("total_lead_upload", 0)
        return 0
