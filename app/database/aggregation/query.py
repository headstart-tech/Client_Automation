"""
This file contains class and methods for get data regarding query.
"""
from app.core.utils import utility_obj
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from app.database.configuration import DatabaseConfiguration
from app.helpers.student_curd.student_query_configuration import QueryHelper


class AggregationQuery:
    """
    Contains functions related to query.
    """

    async def get_query_pipeline_base_match(self, query_filter: dict):
        """
        Get the base match stage which useful in the aggregation pipeline of
            get queries.

        Params:
            - query_filter (dict): A dictionary which useful for get queries
                based on filters.

        Returns:
            - dict: A dictionary which contains base match stage which useful
                for get queries based on filters.

        Raises:
           - ObjectIdInValid: An error which occurred when counselor id will
            be wrong.
        """
        date_range = query_filter.get("date_range", {})
        if not date_range:
            date_range = {}
        start_date, end_date = date_range.get("start_date"), \
            date_range.get("end_date")
        query_match = {}
        counselor_ids = query_filter.get("counselor_ids", []) if query_filter.get("counselor_ids") else []
        search = query_filter.get("search")
        program_names = query_filter.get("program_names")
        query_type = query_filter.get("query_type")
        if counselor_ids and "None" not in counselor_ids:
            counselor_ids = [ObjectId(counselor_id)
                             for counselor_id in counselor_ids
                             if await utility_obj.is_length_valid(
                    counselor_id, "Counselor id")]
            query_match.update(
                {"assigned_counselor_id": {"$in": counselor_ids}})
        elif "None" in counselor_ids:
            query_match.update({
                "assigned_counselor_id": None
            })
        if search not in ["", None]:
            query_match.update(
                {"$or": [{"student_name":
                              {"$regex": f".*{search}.*", "$options": "i"}},
                         {"student_email_id":
                              {"$regex": f"^{search}", "$options": "i"}}
                         ]})
        if program_names:
            program_names = jsonable_encoder(program_names)
            program_filter = [
                {"course_name": program.get("course_name"),
                 "specialization_name": program.get("spec_name")}
                for program in program_names]
            query_match.update({"$or": program_filter})
        if start_date and end_date:
            start_date, end_date = await utility_obj.date_change_format(
                start_date, end_date
            )
            query_match.update({"created_at":
                                    {"$gte": start_date, "$lte": end_date}})
        if query_type:
            query_match.update({"category_name": {"$in": query_type}})
        return query_match

    async def get_sort_info(self, query_filter: dict) -> None | dict:
        """
        Get the sorting information which useful in the aggregation pipeline
            for sort the queries.

        Params:
            - query_filter (dict): A dictionary which useful for get queries
                based on filters.

        Returns:
            - dict: A dictionary which contains sorting information which useful
                for sort the queries.
        """
        data_sort_info = {
            "student_name": query_filter.get("name_sort"),
            "student_email_id": query_filter.get("email_sort"),
            "created_at": query_filter.get("created_on_sort"),
            "updated_at": query_filter.get("update_on_sort")
        }
        sort_info = next(
            ({"key": key, "value": 1 if value else -1} for key, value in
             data_sort_info.items()
             if value is not None), None)
        return sort_info

    async def get_paginated_result(
            self, page_num: int | None, page_size: str | None,
            sort_info: None | dict) -> list:
        """
        Get the sorting information which useful in the aggregation pipeline
            for sort the queries.

        Params:
            - page_num (int | None): Either None or page number where you want
                to show data. e.g., 1
            - page_size (int | none): Either None or page size, useful for show
                data on page_num. e.g., 25.
                If we give page_num=1 and page_size=25 i.e., we want 25
                    records on page 1.
            - sort_info (None | dict): Either None or a dictionary which
                contains sorting information which useful for sort the queries.

        Returns:
            dict: A list which useful for get queries.
        """
        if page_num and page_size:
            skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                                  page_size)
            paginated_results = [{"$skip": skip}, {"$limit": limit}]
        else:
            paginated_results = []
        if sort_info:
            paginated_results.insert(0, {"$sort": {sort_info.get("key"): sort_info.get("value")}})
        else:
            paginated_results.insert(0, {"$sort": {"created_at": -1}})
        return paginated_results

    async def get_all_queries(
            self, query_filter: dict, page_num: int | None,
            page_size: str | None, counselor_id) -> tuple:
        """
        Get all queries with/without filter

        Params:
            - query_filter (dict): A dictionary which useful for get queries
                based on filters.
            - page_num (int | None): Either None or page number where you want
                to show data. e.g., 1
            - page_size (int | none): Either None or page size, useful for show
                data on page_num. e.g., 25.
                If we give page_num=1 and page_size=25 i.e., we want 25
                    records on page 1.

        Returns:
            - tuple: A tuple which contains queries along with total count.
        """
        season = query_filter.get("season")
        sort = query_filter.get("sort")
        sort_info = None
        if sort:
            sort_info = {
                "key": query_filter.get("sort"),
                "value": 1 if query_filter.get("sort_type") in ["asc", None] else -1
            }
        query_match = await self.get_query_pipeline_base_match(query_filter)
        if query_filter.get("counselor_ids") is None:
            if counselor_id:
                query_match.update(
                    {"assigned_counselor_id": {"$in": counselor_id}})
        pipeline = []
        if query_match:
            pipeline.append({"$match": query_match})
        paginated_results = await self.get_paginated_result(
            page_num, page_size, sort_info)
        pipeline.append(
            {
                "$facet": {
                    "paginated_results": paginated_results,
                    "totalCount": [{"$count": "count"}],
                }
            }
        )
        if season == "":
            season = None
        aggregation_result = DatabaseConfiguration(season=season).queries.aggregate(pipeline)
        queries, total_queries = [], 0
        async for documents in aggregation_result:
            try:
                total_queries = documents.get("totalCount")[0].get("count")
            except IndexError:
                total_queries = 0
            queries = [QueryHelper().query_helper(document)
                       for document in documents.get("paginated_results",
                                                     [])]
        return queries, total_queries
