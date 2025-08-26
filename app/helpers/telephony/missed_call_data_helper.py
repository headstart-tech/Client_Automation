"""
Missed call data summary helper for communication dashboard missed call summary table.
"""
from app.database.configuration import DatabaseConfiguration
from app.core.utils import utility_obj
from bson.objectid import ObjectId



class MissedCallSummary:
    """
    All related function for getting missed calls list from the database.
    """

    async def call_data_helper(self, item: dict) -> dict:
        """Function for format the dictionary data which is getting from database to the response format

        Params:
            item (dict): Unit raw data of calls which is getting from the database.

        Returns:
            dict: Formatted unit data.
        """
        call_from_name = item.get("call_from_name")
        call_from_number = item.get("call_from_number")
        application_id = item.get("application")
        application = await DatabaseConfiguration().studentApplicationForms.find_one({"_id": ObjectId(application_id) if application_id else None})
        assigned_counsellor = item.get("assigned_counsellor_list", [])
        if assigned_counsellor:
            assigned_counsellor = assigned_counsellor[0]

        return {
            "student_name": call_from_name if call_from_name else "Candidate",
            "custom_application_id": application.get("custom_application_id") if application else None,
            "student_id": str(item.get("call_from")),
            "application_id": str(application_id) if application_id else None,
            "dialed_call_count": await DatabaseConfiguration().call_activity_collection.count_documents({"type": "Outbound", 'call_to_number': call_from_number}),
            "missed_call_count": item.get("missed_call_count", 0),
            "assigned_counsellor": assigned_counsellor,
            "missed_call_age": int(item.get("missed_call_age", 0)),
            "student_mobile_number": call_from_number,
            "landing_number": None,
            "date_time": utility_obj.get_local_time(item.get("max_created_at"))
        }

    async def missed_call_list(self, counsellors: list[str], landing_number: str, 
                             date_range: dict, search: str, sort: bool, 
                             sort_name: str, sort_type: str, page_num: int, 
                             page_size: int) -> tuple:
        """
        Function to get all missed calls data from the database.

        Params:
            counsellors (list[str] | None): Either None or list of college counsellors unique ids.
            landing_number (str | None): Either None or a number in string format.
            date_range (dict | None): Either None or date range which useful for filter data according to date range.
            search (str | None): EIther None or search pattern which useful for get data by search pattern.
            sort (bool | None): Either None or a boolean value which useful for apply sort either ascending or decending way.
            sort_name (str | None): Either None or field name which has to be sorted.
            sort_type (str | None): Either None or type of sorting order either asc or desc.

        Returns:
            tuple: A tuple which contains list of call details and total count of call details.

        """
        pipeline = []

        match_stage = {
            'type': {
                '$in': ['Inbound', 'CallBack']
            },
            "status": {
                "$in": ["BUSY", "CANCEL", "NOANSWER", "Missed"]
            }
        }

        if landing_number:
            match_stage.update({
                "landing_number": int(landing_number)
            })

        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'),
                date_range.get('end_date'))
            match_stage.update({
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            })

        if search:
            match_stage.update({
                "$expr": {
                    "$regexMatch": {
                        "input": { "$toString": "$call_from_number" },
                        "regex": search,
                        "options": "i"
                    }
                }
            })

        if counsellors:
            match_stage.update({
                "call_to": {
                    "$in": [ObjectId(user_id) for user_id in counsellors]
                }
            })
        
        pipeline.extend([{"$match": match_stage}, {
            '$group': {
                '_id': '$call_from_number', 
                "call_from_name": { "$first": "$call_from_name" },
                "call_from": {
                    "$first": "$call_from"
                },
                "application": {
                    "$first": "$application"
                },
                'missed_call_count': {
                    '$sum': 1
                }, 
                'assigned_counsellor_list': {
                    '$addToSet': '$call_to_name'
                }, 
                'max_created_at': {
                    '$max': '$created_at'
                }
            }
        }, {
            '$project': {
                '_id': 0, 
                'call_from_number': '$_id', 
                "call_from_name": 1,
                "call_from": 1,
                "application": 1,
                'missed_call_count': 1, 
                'assigned_counsellor_list': 1, 
                'missed_call_age': {
                    '$divide': [
                        {
                            '$subtract': [
                                {
                                    '$toDate': '$$NOW'
                                }, '$max_created_at'
                            ]
                        }, 86400000
                    ]
                },
                'max_created_at': 1
            }
        }])

        if sort:
            if sort_name.lower() == "missed_call_count":
                sort_name = "missed_call_count"

            elif sort_name.lower() == "dialed_call_count":
                sort_name = "dialed_call_count"
            
            elif sort_name.lower() == "missed_call_age":
                sort_name = "missed_call_age"

            pipeline.append({"$sort": {sort_name: 1 if sort_type in [None, "asc"] else -1}})

        skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                              page_size)
        pipeline.append({
            "$facet": {
                "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                "totalCount": [{"$count": "count"}],
            }
        })

        calls_data = await (DatabaseConfiguration().call_activity_collection.aggregate(pipeline)).to_list(None)

        calls_data = calls_data[0] if calls_data else {}

        calls_dict = [
            await self.call_data_helper(item) for item in calls_data.get("paginated_results", [])
        ]
        
        totalCount = calls_data.get("totalCount", [{}])

        count = totalCount[0].get("count", 0) if totalCount else 0
        return calls_dict, count