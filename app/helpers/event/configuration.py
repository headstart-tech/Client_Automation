"""
This file contain class and functions related to event API routes/endpoints
"""
import datetime

from bson import ObjectId

from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import cache_invalidation
from app.helpers.user_curd.user_configuration import UserHelper


class EventHelper:
    """
    Contain operations related to event
    """

    async def event_helper(self, event_data):
        """
        Get event data
        """
        if event_data.get("_id"):
            event_data.update({"_id": str(event_data.get('_id'))})
        if event_data.get("created_by_id"):
            event_data.update({"created_by_id": str(event_data.get('created_by_id'))})
        for name in ["updated_by_name", "learning", "updated_by",
                     "updated_on"]:
            if event_data.get(name) is None:
                event_data[name] = None
        if event_data.get("updated_by"):
            event_data.update({"updated_by": str(event_data.get('updated_by'))})
        if event_data.get("event_start_date"):
            if type(event_data.get("event_start_date")) != str:
                event_data["event_start_date"] = utility_obj.get_local_time(event_data.get("event_start_date"),
                                                                            only_date=True)
        for name in ["updated_on", "created_on"]:
            if event_data.get(name):
                if type(event_data.get(name)) != str:
                    event_data[name] = utility_obj.get_local_time(event_data.get(name))
        if event_data.get("event_end_date"):
            if type(event_data.get("event_end_date")) != str:
                event_data["event_end_date"] = utility_obj.get_local_time(event_data.get("event_end_date"), only_date=True)
        return {
            **event_data
        }

    async def get_event_types(self, college_id, current_user):
        """
        Get event types
        """
        await UserHelper().is_valid_user(current_user)
        results = DatabaseConfiguration().college_collection.aggregate([
            {
                "$match": {
                    "_id": ObjectId(college_id)
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "event_types": 1
                }
            }
        ])
        async for event_types in results:
            return event_types

    async def add_event_types_into_database(self, current_user, college, event_types):
        """
        Add event types in the database
        """
        event_types = list(set([item.title() for item in event_types]))
        college_data = await self.get_event_types(college.get('id'), current_user)
        if college_data.get('event_types'):
            for event_type in college_data.get('event_types', []):
                if event_type in event_types:
                    event_types.remove(event_type)
            college_data.get('event_types', []).extend(event_types)
            await DatabaseConfiguration().college_collection.update_one({"_id": ObjectId(college.get("id"))}, {
                "$set": {"event_types": college_data.get('event_types', [])}})
            await cache_invalidation(api_updated="updated_college", user_id=college.get("id"))
            return {"data": event_types, "message": "Updated event types."}
        else:
            await DatabaseConfiguration().college_collection.update_one({"_id": ObjectId(college.get("id"))},
                                                                        {"$set": {"event_types": event_types}})
            await cache_invalidation(api_updated="updated_college", user_id=college.get("id"))
            return {"data": event_types, "message": "Added event types."}

    async def add_event_data_into_database(self, current_user, college, payload, event_id):
        """
        Add event data in the database
        """
        user = await UserHelper().is_valid_user(current_user)
        event_data = {key: value for key, value in payload.dict().items() if value is not None}
        if event_data.get('event_name'):
            event_data['event_name'] = event_data.get('event_name', "").title()
        if event_data.get('event_start_date'):
            event_data['event_start_date'] = await utility_obj.date_change_utc(event_data.get('event_start_date'),
                                                                               date_format="%d/%m/%Y")
        if event_data.get('event_end_date'):
            event_data['event_end_date'] = await utility_obj.date_change_utc(event_data.get('event_end_date'),
                                                                             date_format="%d/%m/%Y")
        if event_data.get('event_type'):
            college_data = await self.get_event_types(college.get('id'), current_user)
            if event_data.get('event_type', "").title() not in college_data.get('event_types', []):
                return {"detail": "Enter a valid event type."}
            event_data['event_type'] = event_data.get('event_type', "").title()
        if event_id:
            await utility_obj.is_id_length_valid(_id=event_id, name="Event id")
            event = await DatabaseConfiguration().event_collection.find_one({"_id": ObjectId(event_id)})
            if not event:
                return {'detail': "Event not found. Make sure provided event id should be correct."}
            if event_data.get('event_name') == event.get('event_name'):
                pass
            elif await DatabaseConfiguration().event_collection.find_one(
                    {'event_name': event_data.get('event_name', "").title()}) is not None:
                return {'detail': "Event name already exist."}
            event_data.update({'updated_by': user.get('_id'),
                               'updated_by_name': utility_obj.name_can(user), 'updated_on': datetime.datetime.utcnow()})
            await DatabaseConfiguration().event_collection.update_one({'_id': event.get('_id')}, {'$set': event_data})
            return {"message": "Event data updated."}
        if event_data.get('event_name') in ["", None]:
            return {'detail': "Event name should be valid."}
        elif await DatabaseConfiguration().event_collection.find_one(
                {'event_name': str(event_data.get('event_name')).title()}) is not None:
            return {'detail': 'Event name already exists.'}
        elif event_data.get('event_start_date') in ["", None]:
            return {'detail': "Event start date should be valid."}
        elif event_data.get('event_end_date') in ["", None]:
            return {'detail': "Event end date should be valid."}
        event_data.update({'created_by_id': user.get('_id'), 'created_by_name': utility_obj.name_can(user),
                           'created_on': datetime.datetime.utcnow()})
        created_event_data = await DatabaseConfiguration().event_collection.insert_one(event_data)
        event_data['_id'] = created_event_data.inserted_id
        return {'data': await self.event_helper(event_data), 'message': "Event created."}

    async def valid_event(self, event_id, event_name):
        """
        Check event exist or not based on id or name
        """
        if event_id:
            await utility_obj.is_id_length_valid(_id=event_id, name="Event id")
            event = await DatabaseConfiguration().event_collection.find_one(
                {"_id": ObjectId(event_id)})
        elif event_name:
            event = await DatabaseConfiguration().event_collection.find_one(
                {"event_name": event_name.title()})
        else:
            return None
        return event

    async def delete_event_from_database(self, background_tasks, current_user, event_name, event_id):
        """
        Delete event by name or id
        """
        user = await UserHelper().is_valid_user(current_user)
        event = await self.valid_event(event_id, event_name)
        if event:
            await DatabaseConfiguration().event_collection.delete_one(
                {"_id": ObjectId(str(event.get('_id')))})
            return {"message": "Event deleted."}
        return {"detail": "Event not found. Make sure you provided event_id or event_name is correct."}

    async def get_event_data_by_name_or_id(self, background_tasks, current_user, event_name, event_id):
        """
        Delete event by name or id
        """
        await UserHelper().is_valid_user(current_user)
        event = await self.valid_event(event_id, event_name)
        if event:
            return {"data": await self.event_helper(event), "message": "Get event data."}
        return {"detail": "Event not found. Make sure you provided event_id or event_name is correct."}
