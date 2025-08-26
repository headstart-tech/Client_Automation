"""
This file contain class and functions related to data segment
"""

import datetime
from itertools import chain

from bson import ObjectId
from fastapi import BackgroundTasks

from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.helpers.data_segment.configuration import DataSegmentHelper
from app.helpers.data_segment.data_segment_helper import \
    data_segment_automation


class DataSegmentPipeline:
    """
    Use for building a pipeline for data segment aggregation
    """

    async def build_pipeline(self, data_segment_ids: list = None):
        """
        Build pipeline for the data segment
        """
        pipeline = [
            {"$sort": {"created_on": -1}},
            {
                "$project": {
                    "_id": 1,
                    "module_name": 1,
                    "data_segment_name": 1,
                    "description": 1,
                    "filters": 1,
                    "raw_data_name": 1,
                    "period": 1,
                    "segment_type": 1,
                    "enabled": 1,
                    "is_published": 1,
                    "created_by_id": 1,
                    "created_by_name": 1,
                    "created_on": 1,
                    "advance_filters": 1,
                    "updated_by": 1,
                    "updated_by_name": 1,
                    "updated_on": 1,
                    "data_count": 1,
                    "count_at_origin": 1,
                    "status": {
                        "$cond": [{"$eq": ["$enabled", True]}, "Active", "Closed"]
                    },
                }
            },
            {
                "$lookup": {
                    "from": "rule",
                    "let": {"segment_id": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$in": [
                                        "$$segment_id",
                                        {"$ifNull": ["$data_segment_id", []]},
                                    ]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "automation_id": {"$toString": "$_id"},
                                "automation_name": "$rule_name",
                                "data_type": 1,
                            }
                        },
                    ],
                    "as": "automation_details",
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "let": {"counselor_id": {"$ifNull": ["$filters.counselor_id", []]}},
                    "pipeline": [
                        {"$match": {"$expr": {"$in": ["$_id", "$$counselor_id"]}}},
                        {
                            "$project": {
                                "_id": 0,
                                "first_name": 1,
                                "middle_name": 1,
                                "last_name": 1,
                            }
                        },
                    ],
                    "as": "counselor_name",
                }
            },
            {
                "$lookup": {
                    "from": "courses",
                    "let": {
                        "course_id": {
                            "$cond": [
                                {"$eq": ["$filters.course.course_id", ""]},
                                [],
                                {"$ifNull": ["$filters.course.course_id", []]},
                            ]
                        }
                    },
                    "pipeline": [
                        {"$match": {"$expr": {"$in": ["$_id", "$$course_id"]}}},
                        {"$project": {"_id": 0, "course_name": 1}},
                        {
                            "$group": {
                                "_id": "",
                                "course_name": {"$push": "$course_name"},
                            }
                        },
                    ],
                    "as": "course_name",
                }
            },
        ]
        if data_segment_ids:
            pipeline.insert(0, {"$match": {"_id": {"$in": data_segment_ids}}})
        return pipeline


class DataSegment(DataSegmentPipeline):
    """
    Contains functions related to data segment activities
    """

    async def retrieve_all_data_segment_names(self):
        """
        Retrieve all data segment names from the collection named dataSegment and return it
        """
        pipeline = await self.build_pipeline()
        result = DatabaseConfiguration().data_segment_collection.aggregate(pipeline)
        return [document.get("data_segment_name") async for document in result]

    async def valid_data_segment(self, data_segment_id, data_segment_name):
        """
        Check data segment exist or not based on id or name
        """
        if data_segment_id:
            await utility_obj.is_id_length_valid(
                _id=data_segment_id, name="Data segment id"
            )
            data_segment = (
                await DatabaseConfiguration().data_segment_collection.find_one(
                    {"_id": ObjectId(data_segment_id)}
                )
            )
        elif data_segment_name:
            data_segment = (
                await DatabaseConfiguration().data_segment_collection.find_one(
                    {"data_segment_name": data_segment_name.title()}
                )
            )
        else:
            return False
        return data_segment

    async def delete_segment_by_id_or_name(
        self,
        data_segment_id,
        data_segment_name,
        user,
        college,
        background_tasks: BackgroundTasks,
    ):
        """
        Delete data segment by id or name
        """
        data_segment = await self.valid_data_segment(data_segment_id, data_segment_name)
        if data_segment:
            await DatabaseConfiguration().data_segment_collection.delete_one(
                {"_id": ObjectId(str(data_segment.get("_id")))}
            )
            return True
        return False

    async def get_segment_details_by_id_or_name(
        self, data_segment_id, data_segment_name
    ):
        """
        Delete data segment by id or name
        """
        data_segment = await self.valid_data_segment(data_segment_id, data_segment_name)
        return data_segment

    async def get_data_Segment(
        self,
        college_id: str | None = None,
        page_num: int | None = None,
        page_size: int | None = None,
        status: str | None = None,
        data_segment_ids: list[ObjectId] | None = None,
        data_segments: bool = True,
        search_string=None,
        data_types=None,
        segment_type=None,
        counselor_id=None
    ):
        """
        Get all data segments data
        """
        total_data, data = 0, []
        pipeline = await self.build_pipeline(data_segment_ids=data_segment_ids)
        match_cond = []
        if search_string is not None:
            pipeline.insert(
                0,
                {
                    "$addFields": {
                        "result": {
                            "$regexMatch": {
                                "input": "$data_segment_name",
                                "regex": search_string,
                                "options": "i",
                            }
                        }
                    }
                },
            )
            pipeline.insert(1, {"$match": {"$expr": {"$ne": ["$result", False]}}})
        if counselor_id:
            match_cond.append({"shared_with.user_id": {"$in": counselor_id}})
        if status in ["Active", "Closed"]:
            match_cond.append({"enabled": True if status == "Active" else False})
        if data_types:
            match_cond.append({"module_name": {"$in": data_types}})
        if segment_type not in ["", None]:
            match_cond.append({"segment_type": segment_type})
        if status in ["Active", "Closed"]:
            match_cond.append({"enabled": True if status == "Active" else False})
        if match_cond:
            pipeline.insert(0, {"$match": {"$and": match_cond}})
        paginated_result = []
        if page_num and page_size:
            skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
            paginated_result = [{"$skip": skip}, {"$limit": limit}]
        pipeline.append(
            {
                "$facet": {
                    "paginated_results": paginated_result,
                    "totalCount": [{"$count": "count"}],
                }
            }
        )
        result = DatabaseConfiguration().data_segment_collection.aggregate(pipeline)
        async for documents in result:
            try:
                total_data = documents.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
            # Todo - We can improvement below statement if possible
            data = [
                await DataSegmentHelper().data_helper(
                    document, college_id, data_segments=data_segments
                )
                for document in documents.get("paginated_results", [])
            ]
        return total_data, data

    async def _get_data_segment_stats(
        self, data, communication_type, data_segment_stats
    ):
        data_segment_id = str(data.get("data_segment_id"))
        data_segment_stat = data_segment_stats.get(data_segment_id)

        if data_segment_stat is None:
            data_segment_stat = {
                "data_segment_id": data_segment_id,
                "data_segment_name": data.get("data_segment_name"),
            }
            data_segment_stats[data_segment_id] = data_segment_stat

        if communication_type == "email" and communication_type in data.get(
            "action_type"
        ):
            data_segment_stat.setdefault("email_sent", 0)
            data_segment_stat["email_sent"] += data.get("targeted_audience", 0)
            data_segment_stat.setdefault("email_opened", 0)
            data_segment_stat["email_opened"] += data.get("email_opened", 0)
            data_segment_stat.setdefault("email_clicked", 0)
            data_segment_stat["email_clicked"] += data.get("email_clicked", 0)
        elif communication_type in [
            "sms",
            "whatsapp",
        ] and communication_type in data.get("action_type"):
            data_segment_stat.setdefault("sent", 0)
            data_segment_stat["sent"] += data.get("targeted_audience", 0)
            data_segment_stat.setdefault("delivered", 0)
            data_segment_stat["delivered"] += data.get(
                f"{communication_type}_delivered", 0
            )

    async def _calculate_rates(self, data_segment_stats, communication_type):
        for data_segment_stat in data_segment_stats.values():
            if communication_type == "email":
                if data_segment_stat.get("email_sent", 0) > 0:
                    data_segment_stat["open_rate"] = (
                        data_segment_stat["email_opened"]
                        / data_segment_stat["email_sent"]
                    )
                    data_segment_stat["click_rate"] = (
                        data_segment_stat["email_clicked"]
                        / data_segment_stat["email_sent"]
                    )
            else:
                if data_segment_stat.get("sent", 0) > 0:
                    data_segment_stat["delivery_rate"] = (
                        data_segment_stat["delivered"] / data_segment_stat["sent"]
                    )

    async def get_top_performing_data_segment_details(
        self, communication_type, page_num, page_size
    ):
        """
        Get top performing data segments details
        """
        result = DatabaseConfiguration().automation_activity_collection.aggregate([])
        data_segment_stats = {}

        async for data in result:
            await self._get_data_segment_stats(
                data, communication_type, data_segment_stats
            )

        await self._calculate_rates(data_segment_stats, communication_type)

        final_data = list(data_segment_stats.values())

        if page_num and page_size:
            response = await utility_obj.pagination_in_api(
                page_num,
                page_size,
                final_data,
                len(final_data),
                route_name="/data_segments/communication_performance_dashboard/",
            )
            return {
                "data": response.get("data"),
                "total": len(final_data),
                "count": page_size,
                "pagination": response.get("pagination"),
                "message": "Get counselor wise call activity data.",
            }

        return {"data": final_data, "message": "Get counselor wise call activity data."}

    async def change_status_of_data_segments(
        self, data_segments_ids: list[ObjectId], status: str, user: dict
    ) -> dict:
        """
        Change status of data segments by ids.

        Params:
            - data_segments_ids list[ObjectId]: A list which contains unique
                ids/identifiers
                e.g., ["123456789012345678901231", "123456789012345678901232"]
            - status (str): A status which we will update for provided data segments
                ids. e.g., "Active"
            - user (dict): A dictionary which contains user data.

        Returns:

        """
        if status in ["Active", "Closed"]:
            status = True if status == "Active" else False
            await DatabaseConfiguration().data_segment_collection.update_many(
                {"_id": {"$in": data_segments_ids}},
                {
                    "$set": {
                        "enabled": status,
                        "updated_by_name": utility_obj.name_can(user),
                        "updated_by": ObjectId(user.get("_id")),
                        "updated_on": datetime.datetime.utcnow(),
                    }
                },
            )
            return {"message": "Data segments status updated successfully."}
        return {"detail": "Make sure provided status is correct."}

    async def get_all_data_segments_detail(
            self,
            data_segment_ids: list | None = None,
            college_id: str | None = None):
        """
        get the data segments detail based on data segment id

        param:
            data_segment_ids (list): Get the list of data segment objectId
            college_id (str): Get the college id of the data segment

        return:
            total count and list of dictionary contains data segment details
        """
        total_segment_data = []
        for _id in data_segment_ids:
            segment_details = await data_segment_automation(
            ).student_mapped_details(
                data_segment_id=str(_id),
                college_id=college_id,
                download=True
            )
            total_segment_data.extend(segment_details)
        unique_keys = list(
            set(chain.from_iterable(sub.keys() for sub in total_segment_data)))
        return unique_keys, total_segment_data
