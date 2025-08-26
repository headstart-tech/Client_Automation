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

logger = get_logger(__name__)


@dataclass
class SourceStats:
    """
    Set default attributes for source
    """
    source_name: str
    primary_source: float = 0
    secondary_source: float = 0
    tertiary_source: float = 0
    verified: float = 0
    total_application: float = 0
    form_initiated: float = 0


class campaign_source_overlap:
    """
    A class representing a source overlap.
    """

    async def extract_data(self,
                           pipeline: list | None = None):
        """
        Get the source overlap data based on given pipeline from the database.

         Params:
            - pipeline (list): An aggregation pipeline for get source
                 overlap data.

        Returns:
            - tuple: A tuple which contains source overlap data.
        """
        result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            pipeline)
        source_dict = {}
        async for utm_data in result:
            if source_dict.get(utm_data.get("_id", "")) is None:
                source_helper = SourceStats(source_name=utm_data.get("_id",
                                                                     ""))
            else:
                source_helper = source_dict.get(utm_data.get("_id", ""))
            source_helper.primary_source += utm_data.get("primary_source",
                                                         0)
            source_helper.secondary_source += utm_data.get(
                "secondary_source", 0)
            source_helper.tertiary_source += utm_data.get(
                "tertiary_source", 0)
            source_helper.verified += utm_data.get("verified", 0)
            source_helper.total_application += utm_data.get(
                "total_application", 0)
            source_helper.form_initiated += utm_data.get(
                "form_initiated", 0)
            source_dict[utm_data.get("_id", "")] = source_helper
        return source_dict

    async def get_aggregate_utm(self, college_id: str | None = None,
                                utm_source="primary_source", start_date=None,
                                end_date=None, source_name=None):
        """
        Get the source overlap for a given college

        Params:
        - college_id (str): A unique id/identifier of a college which useful
                for get particular college source overlap data.
        - utm_source (str): Name of the utm source which can be primary_source,
            secondary_source and tertiary_source, useful for get source
                    overlap data according to utm source.
        - start_date (datetime | None): Either None or a start date for get
                source overlap data based on start_date.
        - end_date (datetime | None): Either None or end_date for get source
                overlap data based on end_date.
        - source_name (str): Get the name of the source

    Returns:
        - tuple: A tuple which contains source overlap data along with total count.
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
                    "is_verify": 1
                }
            }
        ]
        if utm_source == "primary_source":
            pipeline.extend([{
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
                                "form_initiated": {"$sum": {
                                    "$cond": [{"$gte": ["$current_stage", 2]},
                                              1, 0]}},
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
                        "_id": f"$source.{utm_source}.utm_source",
                        f"{utm_source}": {"$sum": 1},
                        "form_initiated": {"$sum": {
                            "$ifNull": ["$student_application.form_initiated",
                                        0]}},
                        "total_application": {"$sum": {
                            "$ifNull": [
                                "$student_application.total_application", 0]}},
                        "verified": {"$sum": {"$cond": ["$is_verify", 1, 0]}}
                    }
                }
            ])
        else:
            pipeline.append({
                "$group": {
                    "_id": f"$source.{utm_source}.utm_source",
                    f"{utm_source}": {"$sum": 1},
                }
            })
        if start_date is not None and end_date is not None:
            pipeline[0].get("$match", {}).update({
                "created_at": {"$gte": start_date, "$lte": end_date}
            })
        if source_name is not None and source_name:
            pipeline[0].get("$match", {}).update({
                f"source.{utm_source}.utm_source": {
                    "$in": [source.lower() for source in source_name]}
            })
        return await self.extract_data(pipeline=pipeline)

    async def get_call_aggregations(self, college_id: str | None = None,
                                    start_date=None, end_date=None,
                                    source_name=None):
        """
        Get the call aggregations function
        Params:
            - college_id (str): A unique id/identifier of a college which useful
                for get particular college source overlap data.
            - start_date (datetime | None): Either None or a start date for
                get source overlap data based on start_date.
            - end_date (datetime | None): Either None or an end_date for get
                source overlap data based on end_date.
            - source_name (str): Get the name of the source

    Returns:
        - tuple: A tuple which contains a dictionary of all the details of
                primary, secondary and tertiary.
        """
        secondary_count = await self.get_aggregate_utm(
            college_id=college_id, start_date=start_date, end_date=end_date,
            utm_source="secondary_source", source_name=source_name)
        tertiary_count = await self.get_aggregate_utm(
            college_id=college_id, start_date=start_date, end_date=end_date,
            utm_source="tertiary_source", source_name=source_name)
        primary_count = await self.get_aggregate_utm(
            college_id=college_id, start_date=start_date, end_date=end_date,
            utm_source="primary_source", source_name=source_name)
        for key in primary_count.keys() | secondary_count.keys() | tertiary_count.keys():
            if (key in primary_count) and (key in secondary_count) and (
                    key in tertiary_count):
                try:
                    primary_count[key].secondary_source += secondary_count[
                        key].secondary_source
                    primary_count[key].tertiary_source += tertiary_count[
                        key].tertiary_source
                except KeyError as error:
                    logger.error(f"An occur error: {error}")
            elif (key in secondary_count) and (key in tertiary_count):
                try:
                    primary_count[key] = secondary_count[key]
                    primary_count[key].tertiary_source += tertiary_count[
                        key].tertiary_source
                except KeyError as error:
                    logger.error(f"An occur error with both: {error}")
            elif (key in secondary_count) and (key in primary_count):
                try:
                    primary_count[key].secondary_source += secondary_count[
                        key].secondary_source
                except KeyError as error:
                    logger.error(f"An occur error with secondary & "
                                 f"primary: {error}")
            elif (key in tertiary_count) and (key in primary_count):
                try:
                    primary_count[key].tertiary_source += tertiary_count[
                        key].tertiary_source
                except KeyError as error:
                    logger.error(f"An occur error with"
                                 f" tertiary & primary: {error}")
            elif key in secondary_count:
                try:
                    primary_count[key] = secondary_count[key]
                except KeyError as error:
                    logger.error(f"An occur error with secondary: {error}")
            elif key in tertiary_count:
                try:
                    primary_count[key] = tertiary_count[key]
                except KeyError as error:
                    logger.error(f"An occur error with tertiary: {error}")
        return primary_count

    async def get_change_indicator_helper(self, college_id: str | None = None,
                                          change_indicator="last_7_days",
                                          source_name=None):
        """
        Get the percentage and position for the given source overlap

        params:
            - college_id (str): Get the college id for the filter the data.
            - change_indicator (dict): Get the date range keyword e.q.
                last_7_days, last_30_days and last_15_days
            - source_name (str): Get the name of the source

        return:
            response: A dictionary contains the following
                percentage and position
        """
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
        previous_campaign_details = await self.get_call_aggregations(
            college_id=college_id, start_date=previous_start_date,
            end_date=previous_end_date, source_name=source_name)
        current_campaign_details = await self.get_call_aggregations(
            college_id=college_id, start_date=current_start_date,
            end_date=current_end_date, source_name=source_name)
        temp_dict = application = verified = primary_source \
            = secondary_source = tertiary_source = form_initiated = {}
        for key in previous_campaign_details.keys() | current_campaign_details.keys():
            if (key in current_campaign_details) and (
                    key in current_campaign_details):
                try:
                    application = await (utility_obj
                    .get_percentage_difference_with_position(
                        previous_campaign_details[key].total_application,
                        current_campaign_details[key].total_application))
                    verified = await (utility_obj
                    .get_percentage_difference_with_position(
                        previous_campaign_details[key].verified,
                        current_campaign_details[key].verified))
                    primary_source = await (utility_obj
                    .get_percentage_difference_with_position(
                        previous_campaign_details[key].primary_source,
                        current_campaign_details[key].primary_source))
                    secondary_source = await (utility_obj
                    .get_percentage_difference_with_position(
                        previous_campaign_details[key].secondary_source,
                        current_campaign_details[key].secondary_source))
                    tertiary_source = await (utility_obj
                    .get_percentage_difference_with_position(
                        previous_campaign_details[key].tertiary_source,
                        current_campaign_details[key].tertiary_source))
                    form_initiated = await (utility_obj
                    .get_percentage_difference_with_position(
                        previous_campaign_details[key].form_initiated,
                        current_campaign_details[key].form_initiated))
                except KeyError as error:
                    logger.error(f"An error occurred {error}")
            elif key in current_campaign_details:
                application = await (utility_obj
                .get_percentage_difference_with_position(
                    0,
                    current_campaign_details[key].total_application))
                verified = await (utility_obj
                .get_percentage_difference_with_position(
                    0,
                    current_campaign_details[key].verified))
                primary_source = await (utility_obj
                .get_percentage_difference_with_position(
                    0,
                    current_campaign_details[key].primary_source))
                secondary_source = await (utility_obj
                .get_percentage_difference_with_position(
                    0,
                    current_campaign_details[key].secondary_source))
                tertiary_source = await (utility_obj
                .get_percentage_difference_with_position(
                    0,
                    current_campaign_details[key].tertiary_source))
                form_initiated = await (utility_obj
                .get_percentage_difference_with_position(
                    0,
                    current_campaign_details[key].form_initiated))
            elif key in previous_campaign_details:
                application = await (utility_obj
                .get_percentage_difference_with_position(
                    previous_campaign_details[key].total_application,
                    0))
                verified = await (utility_obj
                .get_percentage_difference_with_position(
                    previous_campaign_details[key].verified,
                    0))
                primary_source = await (utility_obj
                .get_percentage_difference_with_position(
                    previous_campaign_details[key].primary_source,
                    0))
                secondary_source = await (utility_obj
                .get_percentage_difference_with_position(
                    previous_campaign_details[key].secondary_source,
                    0))
                tertiary_source = await (utility_obj
                .get_percentage_difference_with_position(
                    previous_campaign_details[key].tertiary_source,
                    0))
                form_initiated = await (utility_obj
                .get_percentage_difference_with_position(
                    previous_campaign_details[key].form_initiated,
                    0))
            temp_dict.update({key: {
                "primary_percentage": primary_source.get("percentage", 0),
                "primary_position": primary_source.get("position", "equal"),
                "application_percentage": application.get("percentage", 0),
                "application_position": application.get("position", "equal"),
                "verified_percentage": verified.get("percentage", 0),
                "verified_position": verified.get("position", "equal"),
                "secondary_percentage": secondary_source.get("percentage", 0),
                "secondary_position": secondary_source.get("position",
                                                           "equal"),
                "tertiary_percentage": tertiary_source.get("percentage", 0),
                "tertiary_position": tertiary_source.get("position", "equal"),
                "form_initiated_percentage": form_initiated.get("percentage",
                                                                0),
                "form_initiated_position": form_initiated.get("position",
                                                              "equal"),
            }})
        return temp_dict

    async def get_source_overlap(self, college_id: str | None = None,
                                 date_range=None, page_num: int | None = None,
                                 page_size: int | None = None,
                                 source_name=None,
                                 change_indicator="last_7_days"):
        """
        Get the source overlap details from given college id.

        Params:
            - college_id (str): A unique id/identifier of a college which
                useful for get particular college source overlap data.
            - date_range (dict): get the date range of the datetime
            - page_num (int | None): Either None or page number where want
                to show data.
            - page_size (int | None): Either None or get the number
                of the page size.
            - change_indicator (str | None): Either None or get the
                data count according change indicator. e.q
                    last_7_days, last_15_days and last_30_days.
            - source_name (str): Get the name of the source

        Returns:
            - dict: A dict which containing the source overlap details
                    along with count and message.
        """

        start_date = None,
        end_date = None
        if date_range is not None:
            date_range = jsonable_encoder(date_range)
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date"))
        source_data = await self.get_call_aggregations(
            college_id=college_id, start_date=start_date, end_date=end_date,
            source_name=source_name)
        change_indicator = await self.get_change_indicator_helper(
            college_id=college_id, change_indicator=change_indicator,
            source_name=source_name)
        final_lst = []
        for key in source_data.keys() | change_indicator.keys():
            data = {}
            if (key in source_data) and (key in change_indicator):
                data = jsonable_encoder(source_data[key])
                data.update(change_indicator[key])
            elif key in source_data:
                data = jsonable_encoder(source_data[key])
                data.update({
                    "primary_percentage": 0,
                    "primary_position": "equal",
                    "application_percentage": 0,
                    "application_position": "equal",
                    "verified_percentage": 0,
                    "verified_position": "equal",
                    "secondary_percentage": 0,
                    "secondary_position": "equal",
                    "tertiary_percentage": 0,
                    "tertiary_position": "equal",
                    "form_initiated_percentage": 0,
                    "form_initiated_position": "equal"
                })
            if key is None:
                continue
            if len(data) > 0:
                final_lst.append(data)
        skip, limit = await utility_obj.return_skip_and_limit(
            page_num=page_num, page_size=page_size)
        if len(final_lst) > 0:
            final_lst = sorted(final_lst,
                               key=lambda s: s.get('primary_source', 0),
                               reverse=True)
        total = len(final_lst)
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, total,
            route_name="/campaign/source_wise_overlap/"
        )
        limit = skip + limit
        primary_source = 0
        secondary_source = 0
        tertiary_source = 0
        verified = 0
        total_application = 0
        form_initiated = 0
        for data in final_lst:
            primary_source += data.get("primary_source", 0)
            secondary_source += data.get("secondary_source", 0)
            tertiary_source += data.get("tertiary_source", 0)
            verified += data.get("verified", 0)
            total_application += data.get("total_application", 0)
            form_initiated += data.get("form_initiated", 0)
        total_count_data = {
            "primary_source": primary_source,
            "secondary_source": secondary_source,
            "tertiary_source": tertiary_source,
            "verified": verified,
            "total_application": total_application,
            "form_initiated": form_initiated
        }
        final_lst = final_lst[skip: limit]
        return {
            "total_count_data": total_count_data,
            "data": final_lst,
            "total": total,
            "count": page_size,
            "pagination": response["pagination"],
            "message": "campaign overlap data fetched successfully!",
        }
