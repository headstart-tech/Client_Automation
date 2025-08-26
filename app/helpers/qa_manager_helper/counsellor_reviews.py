"""
This file contain class and functions related to Counsellor Reviews
"""

from app.database.configuration import DatabaseConfiguration
from app.core.utils import utility_obj


class CounsellorReview:
    """
    Counsellor review related functions in QA Manager module.
    """

    async def date_filter_query_helper(self, date_range: dict|None=None) -> dict:
        """Function for creating query dictionary for filtering the data in limited time line according to created_at field in database.

        Args:
            date_range (dict | None, optional): Start date and end date in the form of dictionary. Defaults to None.

        Returns:
            dict: Returns the dictionary blank if no any date range is provided but created_at conditional dictionary for filtering the data in the given date range.
        """
        query = {}
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'),
                date_range.get('end_date'))
            query.update(
                {"created_at": {"$gte": start_date, "$lte": end_date}})
            
        return query

    async def qa_helper(self, params: dict, date_range: dict|None=None) -> int:
        """Count the number of data from the database according to the given condition.

        Params:
            params (dict): condition query for the condition in dictionary format for mongodb.
            date_range (dict | None, optional): start date and end date. Defaults to None.

        Returns:
            int: returns the number of data in the database.
        """
        query = await self.date_filter_query_helper(date_range)
        
        query.update(params)

        return await DatabaseConfiguration().call_activity_collection.count_documents(query)

    async def counsellor_helper(self, data: dict, date_range: dict|None=None) -> dict:
        """
        Get the counselor count information which useful in QA module.

        Params:
            data (dict): A dictionary which contains counselor information.

        Returns:
            dict: A dictionary which contains counselor count information which useful in QA module.
        """

        params = {
            "call_from": data.get("_id")
        }
        total_calls = await self.qa_helper(params, date_range)

        params = {
            "$and" : [
                {
                    "call_from": data.get("_id")
                }, 
                {
                    "qced": {
                        "$exists": True
                    }
                }
            ]
        }
        total_qced_calls = await self.qa_helper(params, date_range)

        params = {
            "$and" : [
                {
                    "call_from": data.get("_id")
                }, 
                {
                    "qced": {
                        "$exists": True
                    }
                }, 
                {
                    "qced.0.qc_status": "Accepted"
                }
            ]
        }
        qc_passed = await self.qa_helper(params, date_range)

        params = {
            "$and" : [
                {
                    "call_from": data.get("_id")
                }, 
                {
                    "qced": {
                        "$exists": True
                    }
                }, 
                {
                    "qced.0.qc_status": "Rejected"
                }
            ]
        }
        qc_failed = await self.qa_helper(params, date_range)

        params = {
            "$and" : [
                {
                    "call_from": data.get("_id")
                }, 
                {
                    "qced": {
                        "$exists": True
                    }
                }, 
                {
                    "qced.0.qc_status": "Fatal Rejected"
                }
            ]
        }
        qc_fataled = await self.qa_helper(params, date_range)


        matching = {
            "call_from": data.get("_id"), 
            "qced": {
                "$exists": True
            }
        }
        matching.update(await self.date_filter_query_helper(date_range))
        param1 = {
            "$match": matching
        }
        
        param2 = {
            '$project': {
                'call_quality': {
                    '$arrayElemAt': [
                        '$qced.call_quality_score', 0
                    ]
                }
            }
        }
        param3 = {
            '$group': {
                '_id': None, 
                'average_call_quality': {
                    '$avg': '$call_quality'
                }
            }
        }
        average_quality_list = await DatabaseConfiguration().call_activity_collection.aggregate([param1, param2, param3]).to_list(None)

        if not average_quality_list:
            average_quality_list.append({"average_call_quality": 0})


        data_set = {
            "counsellor_id": str(data.get("_id")),
            "counsellor_name": utility_obj.name_can(data),
            "total_calls": total_calls,
            "total_qced_calls": total_qced_calls,
            "qc_passed": qc_passed,
            "qc_failed": qc_failed,
            "qc_fataled": qc_fataled,
            'call_quality': utility_obj.format_float_to_2_places(average_quality_list[0].get("average_call_quality"))
        }

        return data_set


    async def retrieve_counsellors(
            self, college_id: str, page_num: int|None=None, page_size: int|None =None, date_range: dict|None=None, route_name: str|None=None
    ) -> dict:
        """
        This function is for retrive data of counsellors with there reviews.

        Params:
            - college_id (str): An unique id/identifier of a college.
                e.g., 123456789012345678901234
            page_num (int | None, optional): Current page no for retrive data. Defaults to None.
            page_size (int | None, optional): No. of data in one page. Defaults to None.
            route_name (str | None, optional): revert path of the data. Defaults to None.

        Returns:
            dict: All merged review count of each counsellor in a dictionary.
        """

        counsellors = DatabaseConfiguration().user_collection.find({"associated_colleges": {"$in": [college_id]},
                                                                    "role.role_name": "college_counselor"})

        all_counsellor = [
            await self.counsellor_helper(item, date_range) for item in await counsellors.to_list(None)
        ]
        if page_num and page_size:
            user_length = len(all_counsellor)
            response = await utility_obj.pagination_in_api(
                page_num, page_size, all_counsellor, user_length, route_name
            )
        if all_counsellor:
            if page_num and page_size:
                return {
                    "data": [response["data"]],
                    "total": response["total"],
                    "count": page_size,
                    "pagination": response["pagination"],
                    "message": "List of counsellors fetched successfully.",
                }
            return all_counsellor
        return {}
    