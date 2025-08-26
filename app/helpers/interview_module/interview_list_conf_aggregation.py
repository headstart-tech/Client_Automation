"""
This file contains the aggregation of interview_list_configuration file
"""
from pymongo.errors import PyMongoError

from app.core.utils import logger, utility_obj
from app.database.configuration import DatabaseConfiguration


class Interview_aggregation:
    """
    A class representing the aggregation of interview configuration file
    """

    def __init__(self):
        self.gd = "GD"
        self.pi = "PI"
        self.done = "Done"
        self.selected = "Selected"
        self.rejected = "Rejected"
        self.shortlisted = "Shortlisted"

    async def get_grid_interview_list(self, ids=None, skip=None, limit=None):
        """
        Aggregate grid view interview list

        Params:\n
            ids (list): A list which contains interview_list ids in a
            string format.\n

        Returns:
            message: type(list): A list formatted data
        """
        pipeline = [
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": {"application_id": {
                        "$ifNull": ["$eligible_applications", []]}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$in": ["$_id", "$$application_id"]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 1,
                                "meetingDetails": 1,
                                "interviewStatus": 1,
                            }
                        }
                    ],
                    "as": "application_details"
                }
            },
            {
                "$unwind": {
                    "path": "$application_details",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$group": {
                    "_id": {"interview_id": "$_id", "list_name": "$list_name",
                            "course_name": "$course_name",
                            "specialization_name": "$specialization_name",
                            "status": "$status"},
                    "total_count": {"$sum": 1},
                    "gd_count": {"$sum": {"$cond": [{"$eq": [
                        "$application_details.meetingDetails.slot_type",
                        self.gd]}, 1, 0]}},
                    "pi_count": {"$sum": {"$cond": [{"$eq": [
                        "$application_details.meetingDetails.slot_type",
                        self.pi]}, 1, 0]}}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "interview_id": {"$toString": "$_id.interview_id"},
                    "list_name": "$_id.list_name",
                    "course_name": {"$concat": ["$_id.course_name", " ",
                                                "$_id.specialization_name"]},
                    "status": "$_id.status",
                    "total_count": "$total_count",
                    "gd_count": "$gd_count",
                    "pi_count": "$pi_count"
                }
            }
        ]
        if ids is None:
            pipeline.insert(0, {
                "$project": {
                    "_id": 1,
                    "list_name": 1,
                    "status": 1,
                    "course_name": 1,
                    "specialization_name": 1,
                    "application_ids": 1
                }
            })
            pipeline.append({
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            })
            return pipeline
        else:
            pipeline.insert(0, {
                "$match": {
                    "_id": {"$in": ids}
                }
            })
        try:
            return [data async for data in
                    DatabaseConfiguration().interview_list_collection.aggregate(
                        pipeline)]
        except PyMongoError as error:
            logger.error(f"An error occurred while trying "
                         f"to execute the query: {error}")

    async def get_detail_interview_list(self, ids=None, skip=None, limit=None):
        """
            Aggregate detail view interview list

            Params:\n
                ids (list): A list which contains interview_list ids in a
                string format.\n

            Returns:
                message: type(list): A list formatted data
        """
        pipeline = [
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": {"application_id": {
                        "$ifNull": ["$eligible_applications", []]}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$in": ["$_id", "$$application_id"]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 1,
                                "meetingDetails": 1,
                                "interviewStatus": 1,
                                "approval_status": 1,
                            }
                        }
                    ],
                    "as": "application_details"
                }
            },
            {
                "$unwind": {
                    "path": "$application_details",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$group": {
                    "_id": {"interview_id": "$_id", "list_name": "$list_name",
                            "course_name": "$course_name",
                            "specialization_name": "$specialization_name",
                            "status": "$status",
                            "moderator_name": "$moderator_name"},
                    "total_count": {"$sum": 1},
                    "selected": {"$sum": {"$cond": [{"$eq": [
                        "$application_details.approval_status",
                        self.selected]}, 1,
                        0]}},
                    "offered": {"$sum": {"$cond": [{"$ifNull": [
                        "$application_details.offer_letter", False]},
                        1,
                        0]}},
                    "rejected": {"$sum": {"$cond": [{"$eq": [
                        "$application_details.approval_status",
                        self.rejected]},
                        1,
                        0]}},
                    "seat_booked": {"$sum": {"$cond": [{"$eq": [
                        "$application_details.payment_info.status",
                        "captured"]}, 1,
                        0]}},
                    "shortlisted": {"$sum": {"$cond": [{"$eq": [
                        "$application_details.interviewStatus.status",
                        self.shortlisted]},
                        1, 0]}},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "interview_id": {"$toString": "$_id.interview_id"},
                    "list_name": "$_id.list_name",
                    "course_name": {"$concat": ["$_id.course_name", " ",
                                                "$_id.specialization_name"]},
                    "moderator_name": "$_id.moderator_name",
                    "status": "$_id.status",
                    "total_count": "$total_count",
                    "selected": "$selected",
                    "offered": "$offered",
                    "rejected": "$rejected",
                    "seat_booked": "$seat_booked",
                    "shortlisted": "$shortlisted"
                }
            }
        ]
        if ids is not None:
            pipeline.insert(0, {
                "$match": {
                    "_id": {"$in": ids}
                }
            })
        else:
            pipeline.append({
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            })
            return pipeline
        try:
            return [data async for data in
                    DatabaseConfiguration().interview_list_collection.aggregate(
                        pipeline)]
        except PyMongoError as error:
            logger.error(f"An error occurred while trying "
                         f"to execute the query: {error}")

    async def get_gd_pi_details(self, page_num: str | None = None,
                                page_size: str | None = None,
                                interview_status: str | None = None,
                                slot_type: str | None = None):
        """
            Get the gd pi grid and details view

            params:
                page_num (int): The number of the page to retrieve
                page_size (int): The size of the page to retrieve
                interview_status (str): interview status will be Archived,
                                        Active and Closed
                slot_type (str): Slot type to retrieve from the database

            return:
                response object: return a list to the user
        """
        pipeline = [
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": {"application_id": {
                        "$ifNull": ["$eligible_applications", []]}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$in": ["$_id", "$$application_id"]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 1,
                                "meetingDetails": 1,
                                "interviewStatus": 1,
                                "approval_status": 1,
                                "gd_status": 1,
                                "pi_status": 1
                            }
                        }
                    ],
                    "as": "application_details"
                }
            },
            {
                "$unwind": {
                    "path": "$application_details",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$group": {
                    "_id": {"interview_id": "$_id", "list_name": "$list_name",
                            "course_name": "$course_name",
                            "specialization_name": "$specialization_name",
                            "status": "$status",
                            "moderator_name": "$moderator_name",
                            "created_at": "$created_at",
                            "slot_type": [{"$cond": [{"$ifNull": [
                                "$selection_procedure"
                                ".gd_parameters_weightage", False]}, self.gd,
                                None]},
                                {"$cond": [{"$ifNull": [
                                    "$selection_procedure"
                                    ".pi_parameters_weightage", False]},
                                    self.pi, None]}]
                            },
                    "total_count": {"$sum": 1},
                    "selected": {"$sum": {"$cond": [{"$eq": [
                        "$application_details.approval_status",
                        self.selected]}, 1,
                        0]}},
                    "offered": {"$sum": {"$cond": [{"$ifNull": [
                        "$application_details.offer_letter", False]},
                        1,
                        0]}},
                    "rejected": {"$sum": {"$cond": [{"$eq": [
                        "$application_details.approval_status",
                        self.rejected]},
                        1,
                        0]}},
                    "seat_booked": {"$sum": {"$cond": [{"$eq": [
                        "$application_details.payment_info.status",
                        "captured"]}, 1,
                        0]}},
                    "shortlisted": {"$sum": {"$cond": [{"$eq": [
                        "$application_details.interviewStatus.status",
                        self.shortlisted]},
                        1, 0]}},
                    "gd_count": {"$sum": {
                        "$cond": {
                            "if": {
                                "$eq": [
                                    "$application_details.gd_status"
                                    ".interview_result",
                                    self.selected]},
                            "then": 1,
                            "else": 0}}},
                    "pi_count": {"$sum": {
                        "$cond": {
                            "if": {
                                "$eq": [
                                    "$application_details.pi_status"
                                    ".interview_result",
                                    self.selected]},
                            "then": 1,
                            "else": 0}}},
                    "gd_available": {
                        "$sum": {"$cond": [
                            {"$eq": ["$application_details.gd_status.status",
                                     "Done"]}, 1, 0]}
                    },
                    "pi_available": {
                        "$sum": {"$cond": [
                            {"$eq": ["$application_details.pi_status.status",
                                     "Done"]}, 1, 0]}
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "interview_id": {"$toString": "$_id.interview_id"},
                    "list_name": "$_id.list_name",
                    "course": "$_id.course_name",
                    "specialization_name": "$_id.specialization_name",
                    "course_name": {"$concat": ["$_id.course_name", " ",
                                                "$_id.specialization_name"]},
                    "moderator_name": "$_id.moderator_name",
                    "status": "$_id.status",
                    "total_count": "$total_count",
                    "selected": "$selected",
                    "offered": "$offered",
                    "rejected": "$rejected",
                    "seat_booked": "$seat_booked",
                    "shortlisted": "$shortlisted",
                    "slot_type": "$_id.slot_type",
                    "created_at": {
                        "$dateToString": {"format": "%d-%m-%Y %H:%M:%S",
                                          "date": "$_id.created_at",
                                          "timezone": "Asia/Kolkata"}
                    },
                    "sorting_date": {
                        "$dateToString": {"format": "%Y-%m-%d %H:%M:%S",
                                          "date": "$_id.created_at",
                                          "timezone": "Asia/Kolkata"}
                    },
                    "gd_count": {
                        "$cond":
                            {"if": {"$in": [self.gd, "$_id.slot_type"]},
                             "then": "$gd_count",
                             "else": {
                                 "$cond": {"if": {
                                     "$in": [self.pi, "$_id.slot_type"]
                                 },
                                     "then": "$gd",
                                     "else": "$gd_count"
                                 }}}},
                    "pi_count": {
                        "$cond":
                            {"if": {"$in": [self.pi, "$_id.slot_type"]},
                             "then": "$pi_count",
                             "else": {
                                 "$cond": {"if": {
                                     "$in": [self.gd, "$_id.slot_type"]
                                 },
                                     "then": "$pi",
                                     "else": "$pi_count"
                                 }}}},
                    "gd_available": {"$cond": {"if": {"$gt": [
                        {"$subtract": ["$total_count", "$gd_available"]}, 0]},
                        "then": True,
                        "else": False}},
                    "pi_available": {"$cond": {"if": {"$gt": [
                        {"$subtract": ["$total_count", "$pi_available"]}, 0]},
                        "then": True,
                        "else": False}}
                }
            },
            {
                "$addFields": {
                    "slot_type": {
                        "$filter": {
                            "input": "$slot_type",
                            "as": "d",
                            "cond": {
                                "$ne": ["$$d", None]
                            }
                        }
                    }
                }
            },
            {
                "$sort": {
                    "sorting_date": -1
                }
            }
        ]
        if interview_status is None:
            pipeline.insert(0, {"$match": {
                "status": {"$ne": "Archived"}
            }})
        else:
            pipeline.insert(0, {"$match": {
                "status": interview_status.title()
            }})
        if slot_type is not None:
            pipeline.insert(0, {"$match": {"status": "Active"}})
            if slot_type.upper() == "PI":
                pipeline.append({
                    "$match": {
                        f"{slot_type.lower()}_available": {"$eq": True},
                        "$or": [{"slot_type": {"$in": [slot_type.upper()]}},
                                {"$and": [{"$expr": {
                                    "$eq": [{"$size": "$slot_type"}, 0]
                                }},
                                    {"gd_count": {"$gt": 0}}]}]
                    }
                })
            else:
                pipeline.append({
                    "$match": {
                        f"{slot_type.lower()}_available": {"$eq": True},
                        "$or": [{"slot_type": {"$in": [slot_type.upper()]}},
                                {"$expr": {
                                    "$eq": [{"$size": "$slot_type"}, 0]}}]
                    }
                })
        if page_num is not None and page_size is not None:
            skip, limit = await utility_obj.return_skip_and_limit(
                page_num=page_num, page_size=page_size)
            pipeline.append({
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            })
            result = DatabaseConfiguration().interview_list_collection \
                .aggregate(pipeline)
            total, interview_list = 0, []
            async for data in result:
                try:
                    total = data.get("totalCount", [{}])[0].get("count")
                except IndexError:
                    total = 0
                except Exception:
                    total = 0
                interview_list = data.get("paginated_results")
            response = await utility_obj.pagination_in_aggregation(
                page_num,
                page_size,
                total,
                "/interview_list/get_interview_header")
            return {"message": "Get Interview list data.",
                    "data": interview_list, "total": total,
                    "count": len(interview_list),
                    "pagination": response.get("pagination")}
        result = DatabaseConfiguration().interview_list_collection \
            .aggregate(pipeline)
        return [data async for data in result]
