"""
This file contains classes and functions related to campaign manager
"""
import datetime
from collections import Counter

from attr import dataclass
from bson import ObjectId
from fastapi.encoders import jsonable_encoder

from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import insert_data_in_cache


@dataclass
class SourceStats:
    """
    Set default attributes for source
    """
    source_name: str
    leads: int = 0
    verified_leads: int = 0
    total_applications = 0
    paid_applications: int = 0
    unpaid_applications: int = 0


@dataclass
class SourceDetails:
    """
    Set default attributes for source
    """
    name: str
    leads: int = 0
    primary_leads: int = 0
    secondary_leads: int = 0
    tertiary_leads: int = 0


class campaign:
    """
    Contain functions related to campaign
    """

    async def total_campaign_count(self, start_date=None, end_date=None):
        """get total count campaign
        total primary source, total secondary source, total tertiary source"""
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "primary_source": "$source.primary_source",
                        "primary_count": {"$sum": {
                            "$cond": ["$source.primary_source", 1, 0]}},
                        "secondary_source": "$source.secondary_source",
                        "secondary_count": {"$sum": {
                            "$cond": ["$source.secondary_source", 1, 0]}},
                        "tertiary_source": "$source.tertiary_source",
                        "tertiary_count": {"$sum": {
                            "$cond": ["$source.tertiary_source", 1, 0]}}
                    }
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "total_count": {"$add": ["$_id.primary_count",
                                             "$_id.secondary_count",
                                             "$_id.tertiary_count"]},
                }
            },
            {
                "$group": {
                    "_id": "",
                    "total_source": {"$sum": "$total_count"},
                    "primary": {"$sum": "$_id.primary_count"},
                    "secondary": {"$sum": "$_id.secondary_count"},
                    "tertiary": {"$sum": "$_id.tertiary_count"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "all_source": "$total_source",
                    "primary_source": "$primary",
                    "secondary_source": "$secondary",
                    "tertiary_source": "$tertiary"
                }
            }
        ]
        if start_date and end_date:
            pipeline.insert(0,
                            {"$match": {
                                "source.primary_source.utm_enq_date": {
                                    "$gte": start_date, "$lte": end_date}}})
        results = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            pipeline)
        async for data in results:
            return data

    async def source_wise_table(self, name="utm_source", start_date=None,
                                end_date=None):
        pipeline = [
            {
                "$group": {

                    "_id": None,
                    "primary_sources": {
                       "$push": f"$source.primary_source.{name}"
                    },
                    "secondary_sources": {
                      "$push": f"$source.secondary_source.{name}"
                    },
                    "tertiary_sources": {
                      "$push": f"$source.tertiary_source.{name}"
                    }
                }
            },
            {
                "$project": {
                  "_id": 0,
                  "primary_source": "$primary_sources",
                  "secondary_source": "$secondary_sources",
                  "tertiary_source": "$tertiary_sources"
                }
            }
        ]
        if start_date and end_date:
            pipeline.insert(0,
                            {"$match": {
                                "source.primary_source.utm_enq_date": {
                                    "$gte": start_date, "$lte": end_date}}})
        results = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            pipeline)
        async for data in results:
            return {"primary_source": dict(Counter(data.get(
                "primary_source"))),
                "secondary_source": dict(Counter(data.get(
                    "secondary_source"))),
                "tertiary_source": dict(Counter(data.get(
                    "tertiary_source")))}

    async def get_percentage(self, obtain, total, percentage):
        """calculate percentage"""
        try:
            data = (obtain / total) * percentage
        except ZeroDivisionError:
            data = 0
        return round(data, 1)

    async def campaign_percentage(self, campaign_count):
        """
        function get total percentage
        """
        data = {}
        if campaign_count:
            for obtain in campaign_count:
                percentage = await self.get_percentage(
                    campaign_count.get(obtain),
                    campaign_count.get("all_source"), 100)
                data.update({obtain: percentage})
            campaign_count.update({"percentage": data})
        return campaign_count

    async def source_wise_per(self, campaign_count, source_wise_count):
        """
        get percentage of source wise
        """
        if source_wise_count:
            for per in source_wise_count:
                for data in source_wise_count.get(per):
                    source_wise_count.get(per).update(
                        {data: await self.get_percentage(
                            source_wise_count.get(per).get(data),
                            campaign_count.get(
                                per),
                            campaign_count.get("percentage").get(
                                per))})
        return source_wise_count

    async def all_source_details(self, start_date=None, end_date=None):
        """
        Get all source details
        """
        pipeline = [
            {
                "$project": {
                    "_id": 1,
                    "is_verify": 1,
                    "source": 1
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
                                    "$eq": ["$$student_id", "$student_id"]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 1,
                                "payment_info": 1
                            }
                        }
                    ],
                    "as": "results",
                }
            },
            {"$unwind": {"path": "$results", "includeArrayIndex": "arrayIndex",
                         "preserveNullAndEmptyArrays": True}},
            {
                "$group": {
                    "_id": "$source.primary_source.utm_source",
                    "total_application": {"$sum": 1},
                    "unpaid_count": {"$sum": {"$cond": [
                        {"$ne": ["$results.payment_info.status", "captured"]},
                        1, 0]}},
                    "student_count": {"$addToSet": "$_id"},
                    "verified_lead": {"$sum": {"$cond": ["is_verify", 1, 0]}},
                    "paid_count": {"$sum": {"$cond": [
                        {"$eq": ["$results.payment_info.status", "captured"]},
                        1, 0]}}
                }
            },
            {
                "$project": {
                    "_id": "$_id",
                    "total_application": "$total_application",
                    "unpaid_count": "$unpaid_count",
                    "student_count": {"$size": "$student_count"},
                    "verified_lead": "$verified_lead",
                    "paid_count": "$paid_count"
                }
            }
        ]
        if start_date and end_date:
            pipeline.insert(0, {"$match": {
                "source.primary_source.utm_enq_date": {"$gte": start_date,
                                                       "$lte": end_date}}})
            pipeline[2].get("$lookup", {}).get("pipeline", []).insert(0, {
                "$match": {
                    "payment_info.created_at": {"$gte": start_date,
                                                "$lte": end_date}
                }})
        result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            pipeline)
        return [{"source_name": data.get("_id"),
                 "leads": data.get("student_count", 0),
                 "verified_leads": data.get("verified_lead", 0),
                 "paid_applications": data.get("paid_count", 0),
                 "unpaid_applications": data.get("unpaid_count", 0),
                 "total_applications": data.get("total_application", 0)} async
                for data in result]

    async def verified_unverified_leads_count(self, source_name,
                                              start_date=None, end_date=None):
        """
        Return count of verified and unverified leads based on source name
        """
        pipeline = [
            {
                "$match": {"source.primary_source.utm_source": source_name}
            },
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "localField": "_id",
                    "foreignField": "student_id",
                    "as": "student_application"}
            },
            {
                "$unwind": {"path": "$student_application"}
            },
            {
                "$facet": {
                    "verified_leads": [
                        {
                            "$match": {
                                "is_verify": True}},
                        {"$count": "total"}],
                    "unverified_leads": [
                        {
                            "$match": {
                                "is_verify": False}},
                        {"$count": "total"}],
                    "submitted_applications": [
                        {
                            "$match": {
                                "student_application.declaration": True
                            }
                        },
                        {"$count": "total"}
                    ],
                    "form_initiated": [
                        {
                            "$match": {
                                "student_application.current_stage": {"$gte": 2}
                            }
                        },
                        {"$count": "total"}
                    ],

                }
            },
            {"$project": {
                "verified_leads": {
                    "$arrayElemAt": ["$verified_leads.total", 0]},
                "unverified_leads": {
                    "$arrayElemAt": ["$unverified_leads.total", 0]},
                "submitted_applications": {
                    "$arrayElemAt": ["$submitted_applications.total", 0]},
                "form_initiated": {
                    "$arrayElemAt": ["$form_initiated.total", 0]}
            }}
        ]
        if start_date and end_date:
            pipeline[0].get("$match", {}).update({
                "source.primary_source.utm_enq_date": {"$gte": start_date,
                                                       "$lte": end_date}})
            pipeline[3].get("$facet", {}).get("verified_leads")[0].get(
                "$match", {}).update(
                {"is_verify": True,
                 f"created_at": {"$gte": start_date,
                                 "$lte": end_date}})
            pipeline[3].get("$facet", {}).get("unverified_leads")[0].get(
                "$match", {}).update(
                {"is_verify": False,
                 f"created_at": {"$gte": start_date,
                                 "$lte": end_date}})
            pipeline[3].get("$facet", {}).get("submitted_applications")[0].get(
                "$match", {}).update(
                {"student_application.declaration": True,
                 f"last_updated_time": {"$gte": start_date, "$lte": end_date}})
            pipeline[3].get("$facet", {}).get("form_initiated")[0].get(
                "$match", {}).update(
                {"student_application.current_stage": {"$gte": 2},
                 f"last_updated_time": {"$gte": start_date, "$lte": end_date}})
        result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            pipeline)
        return [{"verified_leads": document.get(
            "verified_leads") if document.get("verified_leads") else 0,
                 "unverified_leads": document.get(
                     "unverified_leads") if document.get(
                     "unverified_leads") else 0,
                 "submitted_applications": document.get(
                     "submitted_applications") if document.get(
                     "submitted_applications") else 0,
                 "leads": (document.get('verified_leads') if document.get(
                     'verified_leads') else 0) + (
                              document.get('unverified_leads') if document.get(
                                  'unverified_leads') else 0),
                 "form_initiated": document.get(
                     "form_initiated") if document.get(
                     'form_initiated') else 0,
                 "admission": "N/A"} async for
                document in
                result]

    async def count_leads(self, details):
        source_dict = dict()
        if details:
            for key, value in details.items():
                for data in value.keys():
                    if source_dict.get(data) is None:
                        sourceStats = SourceDetails(name=data)
                    else:
                        sourceStats = source_dict.get(data)
                    if key == "primary_source":
                        sourceStats.primary_leads += details[key][data]
                    elif key == "secondary_source":
                        sourceStats.secondary_leads += details[key][data]
                    elif key == "tertiary_source":
                        sourceStats.tertiary_leads += details[key][data]
                    sourceStats.leads += details[key][data]
                    source_dict[data] = sourceStats
        return [source_dict[source_key] for source_key in source_dict]

    async def campaign_manager_helper(self, college_id, date_range):
        """
        get all utm_source from primary and secondary and tertiary
        """
        start_date, end_date = None, None
        if date_range is None:
            total_leads = await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
                {'college_id': ObjectId(college_id)})
            total_verified_leads = await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
                {'college_id': ObjectId(college_id), "is_verify": True})
            total_applications = await DatabaseConfiguration().studentApplicationForms.count_documents(
                {'college_id': ObjectId(college_id)})
            total_paid_applications = await DatabaseConfiguration().studentApplicationForms.count_documents(
                {'college_id': ObjectId(college_id),
                 "payment_info.status": "captured"})
            total_unpaid_applications = await DatabaseConfiguration().studentApplicationForms.count_documents(
                {'college_id': ObjectId(college_id),
                 "payment_info.status": {"$ne": "captured"}})
        else:
            date_range = await utility_obj.format_date_range(date_range)
            start_date, end_date = await utility_obj.get_start_and_end_date(
                date_range=date_range)
            total_leads = await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
                {'college_id': ObjectId(college_id),
                 "created_at": {"$gte": start_date,
                                "$lte": end_date}})
            total_verified_leads = await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
                {'college_id': ObjectId(college_id), "is_verify": True,
                 "created_at": {"$gte": start_date,
                                "$lte": end_date}})
            total_applications = await DatabaseConfiguration().studentApplicationForms.count_documents(
                {'college_id': ObjectId(college_id),
                 "enquiry_date": {"$gte": start_date,
                                  "$lte": end_date}})
            total_paid_applications = await DatabaseConfiguration().studentApplicationForms.count_documents(
                {'college_id': ObjectId(college_id),
                 "payment_info.status": "captured",
                 "payment_info.created_at": {"$gte": start_date,
                                             "$lte": end_date}})
            total_unpaid_applications = total_applications - total_paid_applications
        campaign_count = await self.total_campaign_count(start_date, end_date)
        source_wise_details = await self.source_wise_table("utm_source",
                                                           start_date,
                                                           end_date)
        total_percentage = await self.campaign_percentage(campaign_count)
        source_wise_percentage = await self.source_wise_per(campaign_count,
                                                            source_wise_details)
        all_source_details: list = await self.all_source_details(start_date,
                                                                 end_date)
        if all_source_details:
            count_of_leads = sum(
                [item.get("leads") for item in all_source_details])
            count_of_verified_leads = sum(
                [item.get("verified_leads") for item in all_source_details])
            count_of_paid_applications = sum(
                [item.get("paid_applications") for item in all_source_details])
            count_of_unpaid_applications = sum(
                [item.get("unpaid_applications") for item in
                 all_source_details])
            count_of_total_applications = sum(
                [item.get("total_applications") for item in
                 all_source_details])
            if (total_leads - count_of_leads) > 0:
                all_source_details.append({"source_name": "organic",
                                           "leads": total_leads - count_of_leads,
                                           "verified_leads": total_verified_leads - count_of_verified_leads,
                                           "paid_applications": abs(
                                               total_paid_applications - count_of_paid_applications),
                                           "unpaid_applications": abs(
                                               total_unpaid_applications - count_of_unpaid_applications),
                                           "total_applications": total_applications - count_of_total_applications})
        if total_percentage is None:
            total_percentage = {}
        total_percentage.update(
            {"all_source_details": all_source_details,
             "source_wise_percentage": source_wise_percentage})
        return total_percentage

    async def source_wise_details(self, source_name, name="utm_source",
                                  start_date=None, end_date=None):
        pipeline = [
            {
                "$facet": {
                    "total_leads": [
                        {
                            "$match": {
                                "$or": [
                                    {f"source.primary_source"
                                     f".{name}": source_name},
                                    {f"source.secondary_source"
                                     f".{name}": source_name},
                                    {f"source.tertiary_source"
                                     f".{name}": source_name}]
                            }},
                        {"$count": "total"}],
                    "primary_source": [
                        {
                            "$match": {
                                f"source.primary_source.{name}": source_name
                            }
                        },
                        {"$count": "primary_source"}
                    ],
                    "secondary_source": [
                        {
                            "$match": {
                                f"source.secondary_source.{name}": source_name
                            }
                        },
                        {"$count": "secondary_source"}
                    ],
                    "tertiary_source": [
                        {
                            "$match": {
                                f"source.tertiary_source.{name}": source_name
                            }
                        },
                        {"$count": "tertiary_source"}
                    ]
                }
            },
            {"$project": {
                "total_leads": {"$arrayElemAt": ["$total_leads.total", 0]},
                "tertiary_source": {
                    "$arrayElemAt": ["$tertiary_source.tertiary_source", 0]},
                "secondary_source": {
                    "$arrayElemAt": ["$secondary_source.secondary_source", 0]},
                "primary_source": {
                    "$arrayElemAt": ["$primary_source.primary_source", 0]}
            }}
        ]
        if start_date and end_date:
            pipeline[0].get("$facet", {}).get("total_leads", [])[0].get(
                "$match", {}).get("$or", []).extend([
                {"source.primary_source.utm_enq_date": {"$gte": start_date,
                                                        "$lte": end_date}},
                {"source.secondary_source.utm_enq_date": {"$gte": start_date,
                                                          "$lte": end_date}},
                {"source.tertiary_source.utm_enq_date": {"$gte": start_date,
                                                         "$lte": end_date}}])
            pipeline[0].get("$facet", {}).get("primary_source")[0].get(
                "$match", {}).update(
                {f"source.primary_source.{name}": source_name,
                 "source.primary_source.utm_enq_date": {"$gte": start_date,
                                                        "$lte": end_date}})
            pipeline[0].get("$facet", {}).get("secondary_source")[0].get(
                "$match", {}).update(
                {f"source.secondary_source.{name}": source_name,
                 "source.secondary_source.utm_enq_date": {"$gte": start_date,
                                                          "$lte": end_date}})
            pipeline[0].get("$facet", {}).get("tertiary_source")[0].get(
                "$match", {}).update(
                {f"source.tertiary_source.{name}": source_name,
                 "source.tertiary_source.utm_enq_date": {"$gte": start_date,
                                                         "$lte": end_date}})
        result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            pipeline)
        return [{"all_source": document.get("total_leads") if document.get(
            "total_leads") else 0,
                 "primary_source": document.get(
                     "primary_source") if document.get(
                     "primary_source") else 0,
                 "secondary_source": document.get(
                     "secondary_source") if document.get(
                     "secondary_source") else 0,
                 "tertiary_source": document.get(
                     "tertiary_source") if document.get(
                     "tertiary_source") else 0} async for
                document in result][0]

    async def organic_lead_details(self, start_date=None, end_date=None,
                                   college_id=None):
        """
        get all lead organic lead detail
        """
        pipeline = [
            {
                "$match": {
                    "college_id": ObjectId(college_id),
                    "source.primary_source.utm_source": "organic"
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "is_verify": 1,
                    "source": 1
                }
            },
            {
                "$group": {
                    "_id": "",
                    "total_leads": {"$sum": 1},
                    "verify_leads": {"$sum": {"$cond": ["$is_verify", 1, 0]}},
                    "unverified_leads": {
                        "$sum": {"$cond": ["$is_verify", 0, 1]}},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "leads": "$total_leads",
                    "unverified_leads": "$unverified_leads",
                    "verify_leads": "$verify_leads"
                }
            }
        ]
        if start_date is not None and end_date is not None:
            pipeline[0].get("$match", {}).update({"created_at": {
                "$gte": start_date, "$lte": end_date}})
        result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            pipeline)
        async for data in result:
            return data

    async def organic_source_application_details(self, start_date=None,
                                                 end_date=None,
                                                 college_id=None):
        """
        Get application of details of source named organic
        """
        pipeline = [
            {
                "$match": {
                    "college_id": ObjectId(college_id)
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "student_id": 1,
                    "payment_info": 1
                }
            },
            {
                "$lookup": {
                    "from": "studentsPrimaryDetails",
                    "let": {"student_id": "$student_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": ["$$student_id", "$student_id"]
                                },
                                "source.primary_source.utm_source": "organic"
                            }
                        },
                        {
                            "$project": {
                                "_id": 1
                            }
                        }
                    ],
                    "as": "student_primary"
                }
            },
            {
                "$unwind": {
                    "path": "$student_primary"
                }
            },
            {
                "$group": {
                    "_id": "",
                    "total_applications": {"$sum": 1},
                    "application_data": {
                        "$push": {
                            "paid_applications": {
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
                            },
                            "unpaid_applications": {
                                "$cond": [
                                    {
                                        "$ne": [
                                            "$payment_info.status",
                                            "captured",
                                        ]
                                    },
                                    1,
                                    0,
                                ]
                            }
                        }
                    }
                }},
            {
                "$project": {
                    "_id": 0,
                    "total_applications": "$total_applications",
                    "paid_applications": {
                        "$sum": "$application_data.paid_applications"},
                    "unpaid_applications": {
                        "$sum": "$application_data.unpaid_applications"}
                }
            }
        ]
        if start_date is not None and end_date is not None:
            pipeline[0].get("$match", {}).update(
                {
                    "enquiry_date": {"$gte": start_date, "$lte": end_date}
                }
            )
        result = DatabaseConfiguration().studentApplicationForms.aggregate(
            pipeline)
        async for data in result:
            return data

    async def get_source_wise_details(self, source_name: str, date_range=None):
        """
        get all utm_source from primary and secondary and tertiary
        """
        start_date, end_date = None, None
        if date_range:
            date_range = await utility_obj.format_date_range(date_range)
            start_date, end_date = await utility_obj.get_start_and_end_date(
                date_range=date_range)
        if source_name:
            data = await self.source_wise_details(source_name.lower(),
                                                  start_date, end_date)
        else:
            data = await self.total_campaign_count(start_date, end_date)
        return data

    async def get_source_performance_details(self, college_id, start_date,
                                             end_date):
        """
        Get all details of leads based on source
        Params:
          college_id (str): unique id of college
          startdate( str): the state date in date range
          end_date (str): the end date in date range
        """
        (data, primary_leads, secondary_leads, tertiary_leads, verified_leads,
         unverified_leads, total_count_leads, submitted_applications,
         form_initiated) = [], 0, 0, 0, 0, 0, 0, 0, 0
        primary_pipeline = [
            {
                "$match": {
                    "college_id": ObjectId(college_id)
                }
            },
            {
                "$facet": {
                    "total_leads": [
                        {"$count": "count"}
                    ],
                    "total_verified_leads": [
                        {"$match": {"is_verify": True}},
                        {"$count": "count"}
                    ],
                    "total_unverified_leads": [
                        {"$match": {"is_verify": False}},
                        {"$count": "count"}
                    ]
                }
            },
            {
                "$project": {
                    "total_leads": {
                        "$arrayElemAt": ["$total_leads.count", 0]
                    },
                    "total_verified_leads": {
                        "$arrayElemAt": ["$total_verified_leads.count", 0]
                    },
                    "total_unverified_leads": {
                        "$arrayElemAt": ["$total_unverified_leads.count", 0]
                    }
                }
            }
        ]
        application_pipeline = [
            {
                "$match": {
                    "college_id": ObjectId(college_id)
                }
            },
            {
                "$facet": {
                    "total_submitted_applications": [
                        {"$match": {"declaration": True}},
                        {"$count": "count"}
                    ],
                    "total_form_initiated_leads": [
                        {"$match": {"current_stage": {"$gte": 2}}},
                        {"$count": "count"}
                    ]
                }
            },
            {
                "$project": {
                    "total_submitted_applications": {
                        "$arrayElemAt": ["$total_submitted_applications.count", 0]
                    },
                    "total_form_initiated_leads": {
                        "$arrayElemAt": ["$total_form_initiated_leads.count", 0]
                    }
                }
            }
        ]
        # total_leads = await DatabaseConfiguration(
        # ).studentsPrimaryDetails.count_documents(
        #     {'college_id': ObjectId(college_id)})
        # total_verified_leads = await DatabaseConfiguration(
        # ).studentsPrimaryDetails.count_documents(
        #     {'college_id': ObjectId(college_id), "is_verify": True})
        # total_unverified_leads = await DatabaseConfiguration(
        # ).studentsPrimaryDetails.count_documents(
        #     {'college_id': ObjectId(college_id), "is_verify": False})
        # total_submitted_applications = await DatabaseConfiguration(
        # ).studentApplicationForms.count_documents(
        #     {'college_id': ObjectId(college_id), "declaration": True})
        # total_form_initiated_leads = await DatabaseConfiguration(
        # ).studentApplicationForms.count_documents(
        #     {'college_id': ObjectId(college_id), "current_stage": {"$gte": 2}}
        # )
        if start_date and end_date:
            primary_pipeline[0].get("$match").update({"created_at": {"$gte": start_date,"$lte": end_date}})
            application_pipeline[0].get("$match").update({"last_updated_time": {"$gte": start_date,"$lte": end_date}})

            primary_details = await DatabaseConfiguration().studentsPrimaryDetails.aggregate(primary_pipeline).to_list(
                None)
            primary_details = primary_details[0] if primary_details else {}
            total_leads = primary_details.get("total_leads", 0)
            total_verified_leads = primary_details.get("total_verified_leads", 0)
            total_unverified_leads = primary_details.get("total_unverified_leads", 0)
            application_details = await DatabaseConfiguration().studentApplicationForms.aggregate(
                application_pipeline).to_list(None)
            application_details = application_details[0] if application_details else {}
            total_submitted_applications = application_details.get("total_submitted_applications", 0)
            total_form_initiated_leads = application_details.get("total_form_initiated_leads", 0)
        else:
            primary_details = await DatabaseConfiguration().studentsPrimaryDetails.aggregate(primary_pipeline).to_list(
                None)
            primary_details = primary_details[0] if primary_details else {}
            total_leads = primary_details.get("total_leads", 0)
            total_verified_leads = primary_details.get("total_verified_leads", 0)
            total_unverified_leads = primary_details.get("total_unverified_leads", 0)
            application_details = await DatabaseConfiguration().studentApplicationForms.aggregate(
                application_pipeline).to_list(None)
            application_details = application_details[0] if application_details else {}
            total_submitted_applications = application_details.get("total_submitted_applications", 0)
            total_form_initiated_leads = application_details.get("total_form_initiated_leads", 0)
        count_utm_source_details = await self.source_wise_table(
            name="utm_source", start_date=start_date,
            end_date=end_date)
        utm_source_details = await self.count_leads(count_utm_source_details)
        for source_name in utm_source_details:
            source_data = jsonable_encoder(source_name)
            lead_status = await self.verified_unverified_leads_count(
                source_data.get("name"), start_date, end_date)
            source_data.update(lead_status[0])
            data.append(source_data)
            primary_leads += source_data.get("primary_leads")
            secondary_leads += source_data.get("secondary_leads")
            tertiary_leads += source_data.get("tertiary_leads")
            unverified_leads += source_data.get("unverified_leads")
            verified_leads += source_data.get("verified_leads")
            total_count_leads += source_data.get("leads")
            submitted_applications += source_data.get("submitted_applications")
            form_initiated += source_data.get("form_initiated")
        total_count_data = {
            "name": "total",
            "leads": total_count_leads + (total_leads - total_count_leads),
            "primary_leads": primary_leads,
            "secondary_leads": secondary_leads,
            "tertiary_leads": tertiary_leads,
            "verified_leads": verified_leads + (
                    total_verified_leads - verified_leads),
            "unverified_leads": unverified_leads + (
                    total_unverified_leads - unverified_leads),
            "submitted_applications": submitted_applications + (
                    total_submitted_applications - submitted_applications),
            "form_initiated": form_initiated + (
                    total_form_initiated_leads - form_initiated),
            "admission": "N/A"
        }
        if (total_leads - total_count_leads) > 0 or (
                total_submitted_applications - submitted_applications) > 0:
            data.append(
                {'name': 'organic', 'leads': total_leads - total_count_leads,
                 'primary_leads': 0,
                 'secondary_leads': 0, 'tertiary_leads': 0,
                 'verified_leads': total_verified_leads - verified_leads,
                 'unverified_leads': total_unverified_leads - unverified_leads,
                 'form_initiated': total_form_initiated_leads - form_initiated,
                 'admission': "N/A",
                 'submitted_applications': total_submitted_applications - submitted_applications})
        return data, total_count_data

    async def get_source_performance_details_change_indicator(self, college_id,
                                                              data,
                                                              change_indicator, cache_change_indicator=None):
        """
        Returns the change indicator values of source performance details function
        Params:
          college_id (str): unique id of college
          data (list): the result in which fields have to be appended
          change_indicator(str): the change indicator value
        """
        start_date, middle_date, previous_date = await utility_obj.get_start_date_and_end_date_by_change_indicator(
            change_indicator)
        previous_start_date, previous_end_date = await utility_obj.date_change_format(
            str(start_date), str(middle_date))
        current_start_date, current_end_date = await utility_obj.date_change_format(
            str(previous_date), str(datetime.date.today()))
        if cache_change_indicator:
            cache_key, cache_data = cache_change_indicator
            if cache_data:
                previous_data, current_data = cache_data.get("previous_data"), cache_data.get("current_data")
            else:
                previous_data, total_count_data = await (self.get_source_performance_details(
                    college_id, previous_start_date, previous_end_date))
                current_data, total_count_data = await (self.get_source_performance_details(
                    college_id, current_start_date, current_end_date))
                cache_data = {
                    "previous_data": previous_data,
                    "current_data": current_data
                }
                insert_data_in_cache(cache_key, cache_data, change_indicator=True)
        for source in data:
            if source.get("name") != "total":
                prev = list(i for i in previous_data if
                            i.get("name") == source.get("name"))
                curr = list(i for i in current_data if
                            i.get("name") == source.get("name"))
                prev = prev[0] if prev else {}
                curr = curr[0] if curr else {}
                temp = {}
                for field, value in source.items():
                    if field != "name":
                        prev_value = prev.get(field)
                        curr_value = curr.get(field)
                        diff = await utility_obj. \
                            get_percentage_difference_with_position(prev_value,
                                                                    curr_value)
                        temp.update({
                            f"{field}_perc": diff.get("percentage"),
                            f"{field}_pos": diff.get("position")})
                source.update(temp)
        return data
