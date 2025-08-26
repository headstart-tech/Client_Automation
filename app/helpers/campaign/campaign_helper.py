"""
This file contain class and functions related to campaign routes
"""
import datetime
from dataclasses import dataclass

from bson import ObjectId
from fastapi.encoders import jsonable_encoder

from app.core.log_config import get_logger
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import insert_data_in_cache

logger = get_logger(__name__)


@dataclass
class SourceStats:
    """
    Set default attributes for source
    """
    name: str
    source_name: str
    total_leads: float = 0
    paid_application: float = 0
    form_initiated: float = 0
    total_application: float = 0
    verified_leads: float = 0


class campaign_manager:
    """
    A class contains campaign routes functionality.
    """

    async def get_aggregate_header(self, lead_type: str | None = None,
                                   start_date=None, end_date=None,
                                   college_id: str | None = None):
        """
        get the aggregate header and fetch the data from the database

        params:
            lead_type (str): Get the lead type for filtering purposes,
            start_date (datetime): Get the start date for filtering by datetime,
            end_date (datetime): Get the end date for filtering by datetime,

        returns:
            response: A dictionary containing the counts of header data
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
                    "source": 1,
                    "is_verify": 1,
                }
            },
            {
                "$group": {
                    "_id": "",
                    "total_leads": {"$sum": {
                        "$cond": [{"$eq": ["$source.primary_source.lead_type",
                                           lead_type]}, 1, 0]}},
                    "verified_leads": {
                        "$sum": {"$cond": ["$is_verify", 1, 0]}},
                    "primary_leads": {"$sum": {
                        "$cond": [{"$eq": ["$source.primary_source.lead_type",
                                           lead_type]}, 1, 0]}},
                    "secondary_leads": {"$sum": {
                        "$cond": [
                            {"$eq": ["$source.secondary_source.lead_type",
                                     lead_type]}, 1, 0]}},
                    "tertiary_leads": {"$sum": {
                        "$cond": [{"$eq": ["$source.tertiary_source.lead_type",
                                           lead_type]}, 1, 0]}}
                }
            }
        ]
        application_pipeline = [
            {
                '$match': {
                    'current_stage': {
                        '$gte': 2
                    }
                }
            },
            {
                '$group': {
                    '_id': '',
                    'total_application': {
                        '$sum': 1
                    },
                    'paid_application': {
                        '$sum': {
                            "$cond": [
                                {
                                  "$and": [
                                    {"$eq": ["$payment_info.status", "captured"]}
                                  ]
                                },
                                1,
                                0
                            ],
                        }
                    }
                }
            }
        ]
        if start_date is not None and end_date is not None:
            pipeline[0].get("$match", {}).update(
                {"created_at": {"$gte": start_date, "$lte": end_date}})
            application_pipeline[0].get("$match", {}).update(
                {"enquiry_date": {"$gte": start_date, "$lte": end_date}}
            )
            (application_pipeline[1].get("$group", {}).get("paid_application", {})
             .get("$sum", {}).get("$cond", [])[0].get("$and", []).extend(
                [
                    {"$gte": ["$payment_info.created_at", start_date]},
                    {"$lte": ["$payment_info.created_at", end_date]}]
            ))
        primary_result = await DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            pipeline).to_list(None)
        application_result = await (DatabaseConfiguration().studentApplicationForms.aggregate(application_pipeline)
                                    .to_list(None))
        primary_result = primary_result[0] if primary_result else {}
        primary_result.update(application_result[0] if application_result else {})
        return primary_result

    async def get_campaign_percentage(self, previous_campaign_details,
                                      current_campaign_details):
        """
        get the percentage of the current campaign for the previous campaign

        params:
            previous_campaign_details (dict): Get the previous campaign details,
            current_campaign_details (dict): Get the current campaign details,

        returns:
            response: A dictionary containing the percentage of the campaign
        """
        paid = await utility_obj.get_percentage_difference_with_position(
            previous_campaign_details.get("paid_application", 0),
            current_campaign_details.get("paid_application", 0))
        verified = await utility_obj.get_percentage_difference_with_position(
            previous_campaign_details.get("verified_leads", 0),
            current_campaign_details.get("verified_leads", 0))
        leads = await utility_obj.get_percentage_difference_with_position(
            previous_campaign_details.get("total_leads", 0),
            current_campaign_details.get("total_leads", 0))
        return {"lead_percentage": leads.get("percentage", 0),
                "lead_position": leads.get("position", "equal"),
                "paid_percentage": paid.get("percentage", 0),
                "paid_position": paid.get("position", "equal"),
                "verified_percentage": verified.get("percentage", 0),
                "verified_position": verified.get("position", "equal")}

    async def get_campaign_helper(self, lead_type: str | None = None,
                                  date_range=None,
                                  change_indicator: str | None = None,
                                  college: dict | None = None,
                                  change_indicator_cache = None
                                  ):
        """
        Get the campaign manager details counts for a given lead types

        params:
            lead_type (str): The lead type for the district campaign count
            date_range (dict): The date range for the campaign count based
            change_indicator (str): The change indicator for
                    the campaign count and position indicator
            college (str): get the college details

        returns:
            response: A dictionary contains the campaign manager details.
        """
        start_date = None,
        end_date = None
        if date_range is not None:
            date_range = jsonable_encoder(date_range)
            if len(date_range) > 1:
                start_date, end_date = await utility_obj.date_change_format(
                    date_range.get("start_date"), date_range.get("end_date"))
        campaign_details = await self.get_aggregate_header(
            lead_type=lead_type, start_date=start_date, end_date=end_date,
            college_id=str(college.get("id")))
        if change_indicator_cache:
            cache_key, cache_data = change_indicator_cache
        else:
            cache_key, cache_data = None, None
        if cache_data:
            (campaign_indicator, previous_campaign_details,
             current_campaign_details) = (cache_data.get("campaign_indicator", {}),
                                          cache_data.get("previous_campaign_details", {}),
                                          cache_data.get("current_campaign_details", {}))
        else:
            (previous_start_date, previous_end_date,
             current_start_date) = await (utility_obj
            .get_start_date_and_end_date_by_change_indicator(
                change_indicator))
            previous_start_date, previous_end_date = await (utility_obj
            .date_change_format(
                str(previous_start_date),
                str(previous_end_date)))
            current_start_date, current_end_date = await (utility_obj
            .date_change_format(
                str(current_start_date),
                str(datetime.date.today())))
            previous_campaign_details = await self.get_aggregate_header(
                lead_type=lead_type, start_date=previous_start_date,
                end_date=previous_end_date,
                college_id=str(college.get("id")))
            current_campaign_details = await self.get_aggregate_header(
                lead_type=lead_type, start_date=current_start_date,
                end_date=current_end_date,
                college_id=str(college.get("id")))
            campaign_indicator = await self.get_campaign_percentage(
                previous_campaign_details=previous_campaign_details,
                current_campaign_details=current_campaign_details)
            await insert_data_in_cache(cache_key=cache_key, data={"previous_campaign_details": previous_campaign_details,
                                                                  "current_campaign_details": current_campaign_details,
                                                                  "campaign_indicator": campaign_indicator
                                                                  }, change_indicator=True)
        verified_percentage = utility_obj.get_percentage_result(
            campaign_details.get("verified_leads", 0),
            campaign_details.get("total_leads", 0)
        )
        paid_percentage = utility_obj.get_percentage_result(
            campaign_details.get("paid_application", 0),
            campaign_details.get("total_application", 0)
        )
        campaign_details["paid_application"] = paid_percentage
        prev_paid = utility_obj.get_percentage_result(
            previous_campaign_details.get("paid_application", 0),
            previous_campaign_details.get("total_application", 0))
        curr_paid = utility_obj.get_percentage_result(
            current_campaign_details.get("paid_application", 0),
            current_campaign_details.get("total_application", 0))
        paid_perc_indicator = await (utility_obj.get_percentage_difference_with_position(
            prev_paid, curr_paid))

        campaign_details.update(campaign_indicator)
        campaign_details["verified_lead_percentage"] = verified_percentage
        campaign_details["paid_application_percentage"] = paid_perc_indicator.get("percentage")
        campaign_details["paid_position"] = paid_perc_indicator.get("position")
        return campaign_details

    async def get_aggregate_utm_campaign_count(self,
                                               utm_type: str | None = None,
                                               source_name: list | None = None,
                                               college_id: str | None = None,
                                               field_name=None,
                                               start_date=None,
                                               end_date=None,
                                               skip=None, limit=None):
        """
        Get the campaign manager utm details.

        Params:
            source_name (list | None): Either None or a list which contains
                source names which useful for get data based on source names.
            utm_type (str | None): Either None or the utm type like campaign,
                keyword and median for get utm data.
            college_id (str | None): Either None or a unique id/identifier
                for get college utm data.
            start_date (datetime): Either None or start date for filter utm
                data by start date.
            end_date (datetime): Either None or end date for filter utm data
                by start date.
            field_name (str | None): Either None or a field name which useful
                for sort utm data based on field name.
            skip (int | None): Either None or an integer value which useful
                for skip the utm data.
            limit (int | None): Either None or an integer value which useful
                for limit the utm data.

        Returns:
            tuple: A tuple which returns total counts of utm data along
             with data count summary.
        """
        if field_name is None:
            field_name = "total_leads"
        pipeline = [
            {
                "$match": {
                    "college_id": ObjectId(college_id)
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
                                "payment_info": 1,
                                "current_stage": 1
                            }
                        },
                        {
                            "$group": {
                                "_id": "",
                                "total_application": {"$sum": 1},
                                "paid_application": {"$sum": {
                                    "$cond": [{"$eq": ["$payment_info.status",
                                                       "captured"]}, 1, 0]}},
                                "form_initiated": {"$sum": {
                                    "$cond": [
                                        {"$gte": ["$current_stage", 2]}, 1,
                                        0]}},
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
                    "_id": {"name": f"$source.primary_source.{utm_type}",
                            "source_name": "$source.primary_source.utm_source"},
                    "paid_application": {"$sum": {
                        "$ifNull": ["$student_application.paid_application",
                                    0]}},
                    "total_application": {"$sum": {
                        "$ifNull": ["$student_application.total_application",
                                    0]}},
                    "form_initiated": {"$sum": {
                        "$ifNull": ["$student_application.form_initiated",
                                    0]}},
                    "verified_leads": {
                        "$sum": {"$cond": ["$is_verify", 1, 0]}},
                    "total_leads": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "name": "$_id.name",
                    "source_name": "$_id.source_name",
                    "paid_application": "$paid_application",
                    "total_application": "$total_application",
                    "form_initiated": "$form_initiated",
                    "verified_leads": "$verified_leads",
                    "total_leads": "$total_leads"
                }
            },
            {
                "$sort": {
                    f"{field_name}": -1
                }
            },
            {
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            }
        ]
        if source_name is not None and source_name:
            pipeline[0].get("$match", {}).update(
                {"source.primary_source.utm_source": {"$in": source_name}})
        if start_date is not None and end_date is not None:
            pipeline[0].get("$match", {}).update(
                {"created_at": {"$gte": start_date, "$lte": end_date}})
        result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            pipeline)
        total_data, utm_campaign = 0, {}
        async for utm_data in result:
            try:
                total_data = utm_data.get('totalCount', [])[0].get("count", 0)
            except IndexError:
                total_data = 0
            for data in utm_data.get('paginated_results', []):
                sourceStats = SourceStats(name=data.get("name", ""),
                                          source_name=data.get(
                                              "source_name", ""))
                sourceStats.total_leads += data.get("total_leads", 0)
                sourceStats.paid_application += data.get(
                    "paid_application", 0)
                sourceStats.form_initiated += data.get("form_initiated", 0)
                sourceStats.total_application += data.get(
                    "total_application", 0)
                sourceStats.verified_leads += data.get("verified_leads", 0)
                utm_campaign[(data.get("name", ""),
                              data.get("source_name", ""))] = sourceStats
        return total_data, utm_campaign

    async def get_change_indicator_utm_details(
            self, previous_utm_details: dict,
            current_utm_details: dict) -> dict:
        """
        Get the utm details according to change indicator.

        Params:
            previous_utm_details (dict): A dictionary which contains previous
                    data count of utm details.
            current_utm_details (dict): A dictionary which contains current
                    data count of utm details.

        Returns:
            dict: A dictionary which contains position and percentage of
                utm details according to change indicator.
        """
        utm_details = leads = paid = application = form_initiated \
            = verified_lead = {}
        for key in previous_utm_details.keys() | current_utm_details.keys():
            if (key in current_utm_details) and (key in previous_utm_details):
                try:
                    leads = await (utility_obj
                    .get_percentage_difference_with_position(
                        previous_utm_details[key].total_leads,
                        current_utm_details[key].total_leads))
                    paid = await (utility_obj
                    .get_percentage_difference_with_position(
                        previous_utm_details[key].paid_application,
                        current_utm_details[key].paid_application))
                    application = await (utility_obj
                    .get_percentage_difference_with_position(
                        previous_utm_details[key].total_application,
                        current_utm_details[key].total_application))
                    form_initiated = await (utility_obj
                    .get_percentage_difference_with_position(
                        previous_utm_details[key].form_initiated,
                        current_utm_details[key].form_initiated))
                    verified_lead = await (utility_obj
                    .get_percentage_difference_with_position(
                        previous_utm_details[key].verified_leads,
                        current_utm_details[key].verified_leads))
                except KeyError as error:
                    logger.error(f"An error occurred {error}")
            elif key in previous_utm_details:
                try:
                    leads = await (utility_obj
                    .get_percentage_difference_with_position(
                        previous_utm_details[key].total_leads,
                        0))
                    paid = await (utility_obj
                    .get_percentage_difference_with_position(
                        previous_utm_details[key].paid_application,
                        0))
                    application = await (utility_obj
                    .get_percentage_difference_with_position(
                        previous_utm_details[key].total_application,
                        0))
                    form_initiated = await (utility_obj
                    .get_percentage_difference_with_position(
                        previous_utm_details[key].form_initiated,
                        0))
                    verified_lead = await (utility_obj
                    .get_percentage_difference_with_position(
                        previous_utm_details[key].verified_leads,
                        0))
                except KeyError as error:
                    logger.error(f"An error occurred {error}")
            elif key in current_utm_details:
                try:
                    leads = await (utility_obj
                    .get_percentage_difference_with_position(
                        0, current_utm_details[key].total_leads))
                    paid = await (utility_obj
                    .get_percentage_difference_with_position(
                        0, current_utm_details[key].paid_application))
                    application = await (utility_obj
                    .get_percentage_difference_with_position(
                        0, current_utm_details[key].total_application))
                    form_initiated = await (utility_obj
                    .get_percentage_difference_with_position(
                        0, current_utm_details[key].form_initiated))
                    verified_lead = await (utility_obj
                    .get_percentage_difference_with_position(
                        0, current_utm_details[key].verified_leads))
                except KeyError as error:
                    logger.error(f"An error occurred {error}")
            utm_details.update({key: {
                "lead_percentage": leads.get("percentage", 0),
                "lead_position": leads.get("position", "equal"),
                "paid_percentage": paid.get("percentage", 0),
                "paid_position": paid.get("position", "equal"),
                "verified_percentage": verified_lead.get(
                    "percentage", 0),
                "verified_position": verified_lead.get("position",
                                                       "equal"),
                "form_initiated_percentage": form_initiated.get("percentage",
                                                                0),
                "form_initiated_position": form_initiated.get("position",
                                                              "equal"),
                "application_position": application.get("position", "equal"),
                "application_percentage": application.get("percentage", 0)}})
        return utm_details

    async def get_utm_campaign_count(self, utm_type: str | None = None,
                                     source_name: list | None = None,
                                     change_indicator: str | None = None,
                                     college_id: str | None = None,
                                     date_range=None, page_num=None,
                                     page_size=None, field_name=None):
        """
        Get the utm campaign count for source wise and utm type

        params:
            source_name (str): Get the multiple source name in the list for
                filter the data by source name,
            utm_type (str): Get the utm type e.q. campaign, keyword and median
            change_indicator (str): Get the change indicator for the indicator
                position by default is "last_7_days"
            date_range (dict): Get the date range for the filter data by
                datetime.
            college_id (str): Get the college id for filter by college.

        return:
            response: A list containing the utm counts data of total_leads,
             paid_application, total_application, verified_leads etc.
        """
        start_date, end_date = None, None
        skip, limit = await utility_obj.return_skip_and_limit(
            page_num=page_num, page_size=page_size)
        if date_range is not None:
            date_range = jsonable_encoder(date_range)
            if len(date_range) > 1:
                start_date, end_date = await utility_obj.date_change_format(
                    date_range.get("start_date"),
                    date_range.get("end_date"))
        total_data, utm_details = await self.get_aggregate_utm_campaign_count(
            utm_type=utm_type, start_date=start_date, end_date=end_date,
            college_id=college_id, field_name=field_name,
            source_name=source_name, skip=skip, limit=limit)
        (previous_start_date, previous_end_date,
         current_start_date) = await (utility_obj
        .get_start_date_and_end_date_by_change_indicator(
            change_indicator))
        previous_start_date, previous_end_date = await (utility_obj
        .date_change_format(
            str(previous_start_date),
            str(previous_end_date)))
        current_start_date, current_end_date = await (utility_obj
        .date_change_format(
            str(current_start_date),
            str(datetime.date.today())))
        total, previous_utm_details = await self.get_aggregate_utm_campaign_count(
            utm_type=utm_type, start_date=previous_start_date,
            end_date=previous_end_date,
            college_id=college_id, field_name=field_name,
            source_name=source_name, skip=skip, limit=limit)
        total, current_utm_details = await self.get_aggregate_utm_campaign_count(
            utm_type=utm_type, start_date=current_start_date,
            end_date=current_end_date, source_name=source_name,
            college_id=college_id, field_name=field_name, skip=skip,
            limit=limit)
        utm_indicator = await self.get_change_indicator_utm_details(
            previous_utm_details=previous_utm_details,
            current_utm_details=current_utm_details
        )
        final_lst = []
        for key in utm_details.keys() | utm_indicator.keys():
            data = {}
            if (key in utm_details) and (key in utm_indicator):
                data = jsonable_encoder(utm_details[key])
                data.update(utm_indicator[key])
            elif key in utm_details:
                data = jsonable_encoder(utm_details[key])
                data.update({
                    "lead_percentage": 0,
                    "lead_position": "equal",
                    "paid_percentage": 0,
                    "paid_position": "equal",
                    "verified_percentage": 0,
                    "verified_position": "equal",
                    "form_initiated_percentage": 0,
                    "form_initiated_position": "equal",
                    "application_position": "equal",
                    "application_percentage": 0
                })
            if data:
                final_lst.append(data)
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, len(final_lst),
            route_name="/campaign/utm_details/"
        )

        (total_leads, total_applications,
         form_initiated, paid, verified) = 0, 0, 0, 0, 0
        for data in final_lst:
            total_applications += data.get("total_application", 0)
            total_leads += data.get("total_leads", 0)
            form_initiated += data.get("form_initiated", 0)
            paid += data.get("paid_application", 0)
            verified += data.get("verified_leads", 0)
        return {
            "total_count_data": {
                "total_leads": total_leads,
                "total_applications": total_applications,
                "form_initiated": form_initiated,
                "paid": paid,
                "verified": verified
            },
            "data": final_lst,
            "total": total_data,
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Campaign source wise data fetched successfully!",
        }
