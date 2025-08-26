"""
This file contains class and functions regarding advance filter.
"""
from app.core.log_config import get_logger
from app.database.configuration import DatabaseConfiguration
from bson import ObjectId

logger = get_logger(name=__name__)


class AdvanceFilter:
    """
    Contains functions related to advance filter.
    """

    async def get_dependencies_information(
            self, college_id: str, dependency_fields: list, data: list) -> list:
        """
        Get dependency field (s) information.

        Params:
            - college_id (str): An unique identifier of a college.
            - dependency_fields (list): A list which contains dependency
                field values.

        Returns:
            - list: A list which contains dependency information.
        """
        pipeline = [
            {"$match": {"college_id": ObjectId(college_id)}},
            {
                '$project': {
                    "_id": 0,
                    'categories_info': {
                        '$filter': {
                            'input': {
                                '$map': {
                                    'input': {
                                        '$objectToArray': '$$ROOT'
                                    },
                                    'as': 'field',
                                    'in': {
                                        'fields': '$$field.v',
                                        'category_name': '$$field.k'
                                    }
                                }
                            },
                            'as': 'field',
                            'cond': {
                                '$not': {
                                    '$in': ["$$field",
                                            ['_id', 'college_id']]
                                }
                            }
                        }
                    }
                }
            },
            {"$unwind": {
                "path": "$categories_info"}},
            {"$unwind": {
                "path": "$categories_info.fields"}},
            {"$match": {
                "categories_info.fields.field_name": {"$in": dependency_fields}
            }},
            {"$group": {"_id": "", "categories_info": {
                "$addToSet": "$categories_info.fields"}}}
        ]

        aggregation_result = DatabaseConfiguration(). \
            advance_filter_field_collection.aggregate(pipeline)
        async for document in aggregation_result:
            return [{**doc, "show": False}
                    for doc in document.get("categories_info", [])
                    if doc.get("field_name") not in data]
        return []

    async def get_categories_or_fields(
            self, college_id: str, search_pattern: str | None,
            category_name: str | None = None) -> tuple:
        """
        Get advance filter categories/fields with/without search pattern.

        Params:
            college_id (str): An unique id/identifier of a college.
            search_pattern (str | None): Either None or string which useful
                for get categories based on search_pattern.

        Returns:
            tuple: A tuple which contains advance filter categories/fields
                along with total count.
        """
        category_cond = '$$field.k'
        filter_cond = {
            '$not': {
                '$in': ["$$field",
                        ['_id', 'college_id']]
            }
        }
        if search_pattern or category_name:
            category_cond = {
                'fields': '$$field.v',
                'category_name': '$$field.k'
            }
            if category_name:
                filter_cond = {"$and":
                    [{
                        '$not': {
                            '$in': ["$$field.category_name",
                                    ['_id', 'college_id']]
                        }
                    }, {
                        '$in': ["$$field.category_name",
                                [category_name]]
                    }]}

        aggregation_pipeline = [
            {"$match": {"college_id": ObjectId(college_id)}},
            {
                '$project': {
                    "_id": 0,
                    'categories_info': {
                        '$filter': {
                            'input': {
                                '$map': {
                                    'input': {
                                        '$objectToArray': '$$ROOT'
                                    },
                                    'as': 'field',
                                    'in': category_cond
                                }
                            },
                            'as': 'field',
                            'cond': filter_cond
                        }
                    }
                }
            }
        ]

        if search_pattern or category_name:
            field_names = "$categories_info.category_name"
            if category_name:
                field_names = "$categories_info.fields"
            aggregation_pipeline.extend([
                {"$unwind": {
                    "path": "$categories_info"}},
                {"$unwind": {
                    "path": "$categories_info.fields"}}
            ])
            if search_pattern not in ["", None]:
                aggregation_pipeline.append({"$match": {
                    "categories_info.fields.field_name":
                        {"$regex": f".*{search_pattern}.*", "$options": "i"}
                }})
            aggregation_pipeline.append(
                {"$group": {"_id": "", "categories_info": {
                    "$addToSet": field_names}}})

        aggregation_pipeline.append(
            {
                "$facet": {
                    "paginated_results": [],
                    "totalCount": [{"$unwind": {
                        "path": "$categories_info"}}, {"$count": "count"}],
                }
            }
        )

        aggregation_result = DatabaseConfiguration(). \
            advance_filter_field_collection.aggregate(aggregation_pipeline)
        data, total_data = [], 0
        async for document in aggregation_result:
            try:
                total_data = document.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
            try:
                data = document.get("paginated_results", [{}])[0].get(
                    'categories_info', [])
            except IndexError:
                data = []
        dependant_fields, existing_fields = [], []
        if search_pattern and data:
            for field_info in data:
                if isinstance(field_info, dict):
                    existing_fields.append(field_info.get("field_name"))
                    dependent_fields = field_info.get("dependent_fields")
                    if dependent_fields:
                        dependant_fields.extend(dependent_fields)
        if dependant_fields:
            temp_data = await self.get_dependencies_information(
                college_id, dependant_fields, existing_fields)
            if temp_data:
                data.extend(temp_data)
        return data, total_data
