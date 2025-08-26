"""
This file contains class and functions which useful for get QA Reviews data.
"""

from app.database.configuration import DatabaseConfiguration
from app.core.utils import utility_obj


class QAReview:
    """
    Counsellor review related functions in QA Manager module.
    """

    async def qa_data_count_helper(self, params: dict, date_range: dict|None=None) -> int:
        """Count the number of data from the database according to the given condition and date range.

        Args:
            params (dict): condition query for the condition in dictionary format for mongodb.
            date_range (dict | None, optional): start date and end date. Defaults to None.

        Returns:
            int: returns the number of data in the database.
        """
        query = {}
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'),
                date_range.get('end_date'))
            query.update(
                {"created_at": {"$gte": start_date, "$lte": end_date}})
            
        query.update(params)

        return await DatabaseConfiguration().call_activity_collection.count_documents(query)


    async def qa_helper(self, data: dict, date_range: dict|None=None) -> dict:
        """
        Get the QA count information which useful in QA module.

        Params:
            data (dict): A dictionary which contains QA information.

        Returns:
            dict: A dictionary which contains QA count information which useful in QA module.
        """

        params = {
            "qced.0.qced_qa": data.get("_id")
        }
        total_qced_calls = await self.qa_data_count_helper(params, date_range)

        params = {
            "$and" : [
                {
                    "qced": {
                        "$exists": True
                    }
                },
                {
                    "qced.0.qced_qa": data.get("_id")
                },
                {
                    "qced.0.qc_status": "Accepted"
                } 
            ]
        }
        total_qc_pass = await self.qa_data_count_helper(params, date_range)

        params = {
            "$and" : [
                {
                    "qced": {
                        "$exists": True
                    }
                },
                {
                    "qced.0.qced_qa": data.get("_id")
                },
                {
                    "qced.0.qc_status": "Rejected"
                } 
            ]
        }
        total_qc_failed = await self.qa_data_count_helper(params, date_range)

        params = {
            "$and" : [
                {
                    "qced": {
                        "$exists": True
                    }
                },
                {
                    "qced.0.qced_qa": data.get("_id")
                },
                {
                    "qced.0.qc_status": "Fatal Rejected"
                } 
            ]
        }
        total_qc_fataled = await self.qa_data_count_helper(params, date_range)

        data_set = {
            "qa_id": str(data.get("_id")),
            "qa_name": utility_obj.name_can(data),
            "total_qced_calls": total_qced_calls,
            "total_qc_pass": total_qc_pass,
            "total_qc_failed": total_qc_failed,
            "total_qc_fataled": total_qc_fataled
        }

        return data_set


    async def retrieve_qa(
            self, page_num: int|None=None, page_size: int|None =None, date_range: dict|None=None, route_name: str|None=None
    ) -> dict:
        """
        This function is for retrive data of QA's with there reviews count.

        Params:
            page_num (int | None, optional): Current page no for retrive data. Defaults to None.
            page_size (int | None, optional): No. of data in one page. Defaults to None.
            route_name (str | None, optional): revert path of the data. Defaults to None.

        Returns:
            dict: All merged review count of each counsellor in a dictionary.
        """
        
        qas = DatabaseConfiguration().user_collection.aggregate([{"$match": {"$or": [{"role.role_name": "qa"}, {"role.role_name": "head_qa"}, {"role.role_name": "college_super_admin"}]}}])

        all_qa = [
            await self.qa_helper(item, date_range) for item in await qas.to_list(None)
        ]
        if page_num and page_size:
            user_length = len(all_qa)
            response = await utility_obj.pagination_in_api(
                page_num, page_size, all_qa, user_length, route_name
            )
        if all_qa:
            if page_num and page_size:
                return {
                    "data": [response["data"]],
                    "total": response["total"],
                    "count": page_size,
                    "pagination": response["pagination"],
                    "message": "List of counsellors fetched successfully.",
                }
            return all_qa
        return {}
    