"""
this file contain class and functions of utm campaign routers
"""
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration


class utm_campaign:
    """
    Get data utm_medium, utm_keyword, utm_campaign based on source
    """

    def __init__(self, source_name, utm_wise, start_date, end_date, page_num,
                 page_size):
        """
        Initialize the variables
        """
        self.source_name = str(source_name).lower()
        self.utm_wise = utm_wise
        self.start_date = start_date
        self.end_date = end_date
        self.skip = page_num
        self.limit = page_size

    async def get_percentage_calculator(self, total, obtain):
        """
        Calculate percentage
        """
        try:
            result = (obtain / total) * 100
        except ZeroDivisionError:
            result = 0
        return round(result, 2)

    async def merge_utm_source(self, primary_details, secondary_details,
                               tertiary_details):
        """
        Merge all source
        """
        dct_temp = {
            data.get("_id"): {"total_leads": data.get("total_leads", 0),
                              "primary_leads": data.get("total_leads", 0),
                              "verified_leads": data.get("verified_leads", 0),
                              "paid_leads": data.get("paid_leads", 0)} for data
            in primary_details}
        for sec in secondary_details:
            if sec.get("_id") in dct_temp:
                dct_temp.get(sec.get("_id")).update({
                    "total_leads": dct_temp.get(sec.get("_id")).get(
                        "total_leads", 0),
                    "secondary_leads": sec.get("total_leads", 0),
                    "verified_leads": dct_temp.get(sec.get("_id")).get(
                        "verified_leads", 0),
                    "paid_leads": dct_temp.get(sec.get("_id")).get(
                        "paid_leads", 0)})
        for sec in tertiary_details:
            if sec.get("_id") in dct_temp:
                dct_temp.get(sec.get("_id")).update({
                    "total_leads": dct_temp.get(sec.get("_id")).get(
                        "total_leads", 0),
                    "tertiary_leads": sec.get("total_leads", 0),
                    "verified_leads": dct_temp.get(sec.get("_id")).get(
                        "verified_leads", 0),
                    "paid_leads": dct_temp.get(sec.get("_id")).get(
                        "paid_leads", 0)})
        final_lst = []
        for key, value in dct_temp.items():
            percentage_verify = await self.get_percentage_calculator(
                value.get("total_leads", 0),
                value.get("verified_leads", 0))
            percentage_paid = await self.get_percentage_calculator(
                value.get("total_leads", 0),
                value.get("paid_leads", 0))
            final_lst.append(
                {"utm": key, "total_leads": value.get("total_leads", 0),
                 "primary_leads": value.get("primary_leads", 0),
                 "secondary_leads": value.get("secondary_leads", 0),
                 "tertiary_leads": value.get("tertiary_leads", 0),
                 "verified_percentage": percentage_verify,
                 "paid_percentage": percentage_paid})
        final_lst = sorted(final_lst, key=lambda x: x.get("total_leads"),
                           reverse=True)
        response = await utility_obj.pagination_in_api(
            self.skip, self.limit, final_lst, len(final_lst),
            route_name="/campaign/get_utm_campaign/"
        )
        return {"data": response.get('data'),
                "total": len(final_lst),
                "count": self.limit,
                "pagination": response.get("pagination"),
                "message": "fetch data successfully.",
                }

    async def get_source_details(self):
        """
        Get source details by utm details
        """
        return await self.get_data_by_utm_source("primary")

    async def get_source_wise_data(self):
        """
        Get source wise data
        """
        primary_details = await self.get_data_by_source_name("primary")
        secondary_details = await self.get_data_by_source_name("secondary")
        tertiary_details = await self.get_data_by_source_name("tertiary")
        return await self.merge_utm_source(primary_details, secondary_details,
                                           tertiary_details)

    async def get_data_by_utm_source(self, source_wise):
        """
        Build pipeline for campaign based on utm_source data
        """
        pipeline = [
            {
                "$match": {
                    "source.primary_source."
                    "utm_source": self.source_name}
            },
            {
                "$project": {
                    "_id": 1,
                    f"source": 1,
                    "is_verify": 1
                }
            },
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": {"student_id": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": ["$student_id", "$$student_id"]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "payment_info": 1
                            }
                        }
                    ],
                    "as": "student_application"
                }
            },
            {
                "$unwind": {
                    "path": "$student_application",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$group": {
                    "_id": f"$source.{source_wise}_source.{self.utm_wise}",
                    "total_leads": {"$addToSet": "$_id"},
                    "verified_leads": {"$sum": {
                        "$cond": ["$is_verify", 1, 0]}},
                    "paid_leads": {
                        "$sum": {"$cond": [{
                            "$eq": ["$student_application."
                                    "payment_info.status",
                                    "captured"]}, 1, 0]}},
                    "unpaid_leads": {
                        "$sum": {"$cond": [{
                            "$ne": ["$student_application."
                                    "payment_info.status",
                                    "captured"]}, 1, 0]}}
                }
            },
            {
                "$project": {
                    "_id": "$_id",
                    "total_leads": {"$size": "$total_leads"},
                    "verified_leads": "$verified_leads",
                    "paid_leads": "$paid_leads",
                    "unpaid_leads": "$unpaid_leads"
                }
            }
        ]
        if self.start_date and self.end_date:
            pipeline[0].get("$match", {}).update({
                "source.primary_source.utm_enq_date": {"$gte": self.start_date,
                                                       "$lte": self.end_date}})
            skip, limit = await utility_obj.return_skip_and_limit(
                page_num=self.skip, page_size=self.limit)
            pipeline.extend([{
                "$skip": skip
            },
                {
                    "$limit": limit
                }])
        results = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            pipeline)
        return [{"source_name": data.get("_id"),
                 "leads": data.get("total_leads", 0),
                 "verified_leads": data.get("verified_leads", 0),
                 "paid_applications": data.get("paid_leads", 0),
                 "unpaid_applications": data.get("unpaid_leads", 0),
                 "total_applications": data.get("paid_leads", 0) + data.get(
                     "unpaid_leads", 0)} async for data in
                results]

    async def get_data_by_source_name(self, source_wise):
        """
        Build pipeline for campaign based on utm_source data
        """
        pipeline = [
            {
                "$match": {"source.primary_source"
                           ".utm_source": self.source_name}
            },
            {
                "$project": {
                    "_id": 1,
                    f"source": 1,
                    "is_verify": 1
                }
            },
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": {"student_id": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": ["$student_id", "$$student_id"]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "payment_info": 1
                            }
                        }
                    ],
                    "as": "student_application"
                }
            },
            {
                "$unwind": {
                    "path": "$student_application",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$group": {
                    "_id": f"$source.{source_wise}_source.{self.utm_wise}",
                    "total_leads": {"$addToSet": "$_id"},
                    "verified_leads": {"$sum": {
                        "$cond": ["$is_verify", 1, 0]}},
                    "paid_leads": {
                        "$sum": {"$cond": [{"$eq": [
                            "$student_application.payment_info.status",
                            "captured"]}, 1, 0]}}
                }
            },
            {
                "$project": {
                    "_id": "$_id",
                    "total_leads": {"$size": "$total_leads"},
                    "verified_leads": "$verified_leads",
                    "paid_leads": "paid_leads"
                }
            }
        ]
        if source_wise == "primary":
            if self.start_date and self.end_date:
                pipeline[0].get("$match", {}).update(
                    {"source.primary_source.utm_source": self.source_name,
                     "source.primary_source.utm_enq_date": {
                         "$gte": self.start_date,
                         "$lte": self.end_date}})
        if source_wise == "secondary":
            pipeline[0].get("$match", {}).update(
                {"$and": [
                    {"source.secondary_source.utm_source": self.source_name},
                    {"source.primary_source.utm_source": {
                        "$ne": self.source_name}},
                    {"source.tertiary_source.utm_source": {
                        "$ne": self.source_name}}]})
            if self.start_date and self.end_date:
                pipeline[0].get("$match", {}).update(
                    {"source.secondary_source.utm_enq_date": {
                        "$gte": self.start_date,
                        "$lte": self.end_date}})
        elif source_wise == "tertiary":
            pipeline[0].get("$match", {}).update(
                {"$and": [
                    {"source.tertiary_source.utm_source": self.source_name},
                    {"source.primary_source.utm_source": {
                        "$ne": self.source_name}},
                    {"source.secondary_source.utm_source": {
                        "$ne": self.source_name}}]})
            if self.start_date and self.end_date:
                pipeline[0].get("$match", {}).update(
                    {"source.tertiary_source.utm_enq_date": {
                        "$gte": self.start_date,
                        "$lte": self.end_date}})
        results = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            pipeline)
        return [data async for data in results]

    async def get_all_source_details(self):
        """
        Get all source name
        """
        primary = await self.build_source_pipeline("primary")
        secondary = await self.build_source_pipeline("secondary")
        tertiary = await self.build_source_pipeline("tertiary")
        return await self.merge_utm_source(primary, secondary, tertiary)

    async def build_source_pipeline(self, source_wise):
        """
        Get all source name with details
        """
        pipeline = [
            {
                "$match": {
                    f"source.{source_wise}_source.utm_enq_date": {
                        "$gte": self.start_date, "$lte": self.end_date}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "source": 1,
                    "is_verify": 1
                }
            },
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": {"student_id": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": ["$student_id", "$$student_id"]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "payment_info": 1
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
                    "_id": f"$source.{source_wise}_source.{self.utm_wise}",
                    "total_leads": {"$addToSet": "$_id"},
                    "verified_leads": {"$sum": {
                        "$cond": ["$student_primary.is_verify", 1, 0]}},
                    "paid_leads": {
                        "$sum": {"$cond": [{"$eq": [
                            "$student_application.payment_info.status",
                            "captured"]}, 1, 0]}}
                }
            },
            {
                "$project": {
                    "_id": "$_id",
                    "total_leads": {"$size": "$total_leads"},
                    "verified_leads": "$verified_leads",
                    "paid_leads": "$paid_leads"
                }
            }
        ]
        results = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            pipeline)
        return [data async for data in results]
