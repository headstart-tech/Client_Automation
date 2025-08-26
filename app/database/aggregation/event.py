"""
This file contain class and functions related to event
"""
import asyncio
import datetime

from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.helpers.event.configuration import EventHelper


class Event:
    """
    Contain functions related to event activities
    """

    async def gather_event_data(
            self, event_doc: dict, events_data: dict, start_datetime: datetime,
                                end_datetime: datetime) -> dict:
        """
        Gather event data for parallel processing
        """
        event_start_date = event_doc.get("event_start_date") + \
                           datetime.timedelta(hours=5, minutes=30)
        event_end_date = event_doc.get("event_end_date") + \
                         datetime.timedelta(hours=5, minutes=30)
        for current_date in list(utility_obj.datetime_range(
                start_date=start_datetime, end_date=end_datetime)):
            local_date = utility_obj.get_local_time(current_date, season=True)
            if event_start_date <= current_date <= event_end_date:
                if local_date in events_data.keys():
                    events_data[local_date].append(
                        await EventHelper().event_helper(event_doc))
                else:
                    events_data[local_date] = \
                        [await EventHelper().event_helper(event_doc)]
        return events_data

    async def get_events_by_date_range(self, start_date, end_date):
        """
        Get events data within a specified date range
        """

        events_data = {}
        start_date = start_date - datetime.timedelta(days=1)

        temp_start_date = utility_obj.get_local_time(
            start_date, season=True).split("-")
        temp_end_date = utility_obj.get_local_time(
            end_date, season=True).split("-")

        start_datetime = datetime.datetime(
            int(temp_start_date[0]), int(temp_start_date[1]),
            int(temp_start_date[2]), 0, 0, 0)
        end_datetime = datetime.datetime(
            int(temp_end_date[0]), int(temp_end_date[1]),
            int(temp_end_date[2]), 23, 59, 59)

        gather_data = [self.gather_event_data(
            event_doc, events_data, start_datetime, end_datetime)
            async for event_doc in DatabaseConfiguration().event_collection.
            aggregate([
                {"$match": {"event_start_date": {"$gte": start_date}}}
            ])]
        await asyncio.gather(*gather_data)
        return events_data

    async def get_events_data(
            self, page_num: int, page_size: int, event_filter: dict,
            season=None) -> any:
        """
        Get events data
        """
        date_range = {key: value for key, value in
                      event_filter.get("date_range", {}).items()
                      if value is not None}
        event_type = event_filter.get("event_type", [])
        event_name = event_filter.get("event_name", [])
        search_input = event_filter.get("search_input", "")
        pipeline = [{
            "$facet": {
                "paginated_results": [{"$sort": {"event_start_date": -1}}],
                "totalCount": [{"$count": "count"}],
            }
        }]
        if page_num and page_size:
            skip, limit = await utility_obj.return_skip_and_limit(
                page_num, page_size)
            pipeline[0].get("$facet", {}).get("paginated_results", []).extend(
                [{"$skip": skip}, {"$limit": limit}])

        # Match stages
        match_stages = []

        if len(date_range) >= 2:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
            start_date = start_date - datetime.timedelta(days=1)
            match_stages.append({"event_start_date": {"$gte": start_date},
                                 "event_end_date": {"$lte": end_date}})
        if search_input not in ["", None]:
            match_stages.append(
                {"event_name":
                     {"$regex": f"^{search_input}", "$options": "i"}})
        if event_name:
            event_name = [{"event_name":
                     {"$regex": f"^{item}", "$options": "i"}}
                          for item in event_name]
            match_stages.append({"$or": event_name})
        if event_type:
            match_stages.append({"event_type": {"$in": event_type}})

        # Combine match stages into a single $match stage
        if match_stages:
            pipeline.insert(0, {"$match": {"$and": match_stages}})

        result = DatabaseConfiguration(season=season).event_collection.\
            aggregate(pipeline)
        total_data, data = 0, []
        async for documents in result:
            try:
                total_data = documents.get("totalCount")[0].get("count", 0)
            except IndexError:
                total_data = 0
            gather_data = [EventHelper().event_helper(document) for document in
                           documents.get("paginated_results", [])]
            data = await asyncio.gather(*gather_data)
        return total_data, data
