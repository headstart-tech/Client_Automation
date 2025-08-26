"""
This file contain classes and functions for returns the list of counselor
"""
import re
from bson import ObjectId
from fastapi import BackgroundTasks
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import cache_invalidation
from app.helpers.counselor_deshboard.counselor import CounselorDashboardHelper
from app.database.aggregation.admin_user import AdminUser


class Counselor:
    """
    Contain functions related to counselor activities
    """

    async def get_college_counselors(self, skip, limit, college_id,
                                     source=None, state=None,
                                     search_string=None):
        """
        Get the list of counselors
        """
        if source or state:
            pipeline = [{"$match": {
                "college_id": {"$in": college_id}}}]
            if state:
                pipeline[0].get("$match").update(
                    {
                        "address_details.communication_address.state.state_code": {
                            "$in": [x.upper() for x in state]}}
                )
            if source:
                if "Organic" in source:
                    value_index = list(source).index("Organic")
                    source[value_index] = None
                sources = []
                for x in source:
                    if x is not None:
                        sources.append(x.lower())
                    else:
                        sources.append(None)
                pipeline[0].get("$match").update(
                    {"source.primary_source": {"$in": sources}})
            pipeline.extend([{
                "$group": {
                    "_id": "$allocate_to_counselor.counselor_id"
                }
            }, {
                "$lookup": {
                    "from": "users",
                    "let": {"user_id": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$_id", "$$user_id"]}
                            }
                        }
                    ],
                    "as": "users",
                }
            },
                {"$unwind": {"path": "$users"}}])
        else:
            pipeline = [
                {"$match": {"role.role_name": "college_counselor",
                            "associated_colleges": {"$in": college_id}}}
            ]
        pipeline.append({
            "$facet": {
                "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                "totalCount": [{"$count": "count"}],
            }
        })
        if state or source:
            result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
                pipeline)
        else:
            result = DatabaseConfiguration().user_collection.aggregate(
                pipeline)
        data, total_data = [], 0
        async for documents in result:
            try:
                total_data = documents.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
            if state or source:
                data = [
                    CounselorDashboardHelper().college_counselors_serialize(
                        document.get('users', {})) for document
                    in
                    documents.get("paginated_results")]
            else:
                data = [
                    CounselorDashboardHelper().college_counselors_serialize(
                        document) for document in
                    documents.get("paginated_results")]
        if search_string is not None:
            denied_metrics = [re.compile(search_string, flags=re.IGNORECASE),
                              re.compile(f"{search_string}$")]
            data = [counselor_data for counselor_data in data
                    if any(dm.search(
                    str(counselor_data.get('counselor_name', "")))
                           for dm in denied_metrics)]
            total_data = len(data)
        return data, total_data

    async def get_college_head_counselors(self, college_id):
        """
        Get the list of counselors
        """
        counselors = DatabaseConfiguration().user_collection.aggregate(
            [
                {"$match": {"role.role_name": "college_head_counselor",
                            "associated_colleges": {"$in": [college_id]}}}
            ]
        )
        data = [{
            "id": str(document.get("_id")),
            "counselor_name": utility_obj.name_can(document),
            "email": document.get("user_name")
        } async for document in counselors]
        return data

    async def map_head_counselor_to_counselor(self, head_counselor_id,
                                              head_counselor_email_id,
                                              counselor_id, user,
                                              college,
                                              background_tasks: BackgroundTasks):
        """
        Map head_counselor to counselor
        """
        if head_counselor_id == "None":
            head_counselor = None
        elif head_counselor_id:
            await utility_obj.is_id_length_valid(_id=head_counselor_id,
                                                 name="Head counselor id")
            head_counselor = await DatabaseConfiguration().user_collection.find_one(
                {"_id": ObjectId(head_counselor_id),
                 "role.role_name": "college_head_counselor"})
        elif head_counselor_email_id:
            head_counselor = await DatabaseConfiguration().user_collection.find_one(
                {"email": head_counselor_email_id,
                 "role.role_name": "college_head_counselor"})
        else:
            return {
                "detail": "Need to provide head_counselor_id or head_counselor_email"}
        await utility_obj.is_id_length_valid(_id=counselor_id,
                                             name="Counselor id")
        if (
                counselor := await DatabaseConfiguration().user_collection.find_one(
                    {"_id": ObjectId(counselor_id)})) is None:
            return {
                "detail": "Counselor not found. Make sure counselor_id must be valid."}
        await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(counselor_id)}, {
                "$set": {"head_counselor_name": utility_obj.name_can(
                    head_counselor) if head_counselor else None,
                    "head_counselor_id": head_counselor.get("_id") if head_counselor else None,
                    "head_counselor_email_id": head_counselor.get(
                        "email") if head_counselor else None}})
        await cache_invalidation(api_updated="updated_user", user_id=counselor.get('email'))
        return {"message": "Map head_counselor to counselor."}


class CounselorCallHistory:
    """
    Contain functions related to counselor call history activities
    """

    async def call_activity_helper(self, call_activity_data):
        """
        Helper function for return call activity data in a proper format
        """
        return {'type': call_activity_data.get('type'),
                'call_to': str(call_activity_data.get('call_to')),
                'call_to_name': call_activity_data.get('call_to_name'),
                'call_from': str(call_activity_data.get('call_from')),
                'call_from_name': call_activity_data.get('call_from_name'),
                'call_started_at': call_activity_data.get('call_started_at'),
                'call_duration': call_activity_data.get('call_duration'),
                'created_at': utility_obj.get_local_time(
                    call_activity_data.get('created_at'))}

    async def get_counselor_call_history(self, counselor_id, page_num=None,
                                         page_size=None, search_input=None):
        """
        Get counselor call history (both inbound and outbound) from the collection call activity
        """
        pipeline = [
            {
                '$match': {
                    "$or": [
                        {"call_to": ObjectId(counselor_id)},
                        {"call_from": ObjectId(counselor_id)}
                    ]
                }
            },
            {"$sort": {"created_at": -1}},
            {
                "$facet": {
                    "paginated_results": [],
                    "totalCount": [{"$count": "count"}],
                }
            }
        ]
        if search_input:
            pipeline.insert(0, {
                '$match': {
                    "$or": [
                        {"call_to": {"$regex": f"^{search_input}"}},
                        {"call_from": {"$regex": f"^{search_input}"}}
                    ]
                }
            })
        if page_num is not None and page_size is not None:
            skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                                  page_size)
            pipeline[-1].get("$facet", {}).get("paginated_results", []).extend(
                [{"$skip": skip}, {"$limit": limit}])
        result = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)
        temp_data, total_data = [], 0
        async for doc in result:
            try:
                total_data = doc.get("totalCount")[0].get("count", 0)
            except IndexError:
                total_data = 0
            temp_data = [await self.call_activity_helper(call_activity_data)
                         for call_activity_data in
                         doc.get("paginated_results", [])]
        return temp_data, total_data

    async def call_activity_data_by_type(self, call_type, counselor_ids,
                                         field_name, temp_dict, date_range):
        """
        Get counselor wise call activity data by call type.
        """
        pipeline = [
            {
                '$match': {
                    "type": call_type,
                    field_name: {"$in": counselor_ids}
                }
            },
            {
                "$group": {
                    "_id": f"${field_name}",
                    "counselor_name": {"$first": f"${field_name}_name"},
                    "total_call_attempted": {"$sum": 1},
                    "total_missed_call": {
                        "$push": {
                            "$cond": [{"$eq": ["$call_duration", 0]}, 1, 0]}
                    },
                    "total_connected_calls": {"$sum": {
                        "$cond": [{"$gt": [{
                            "$ifNull": ["$call_duration", 0]}, 0]}, 1, 0]}},
                    "total_call_duration": {
                        "$push": "$call_duration"
                    }
                }
            },
            {
                "$project": {
                    "_id": "$_id",
                    "counselor_name": "$counselor_name",
                    "total_call_attempted": "$total_call_attempted",
                    "total_missed_call": {"$sum": "$total_missed_call"},
                    "total_call_duration": {"$sum": "$total_call_duration"},
                    "total_connected_calls": "$total_connected_calls"
                }
            }
        ]
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
            pipeline.insert(0, {"$project": {
                "call_started_at": {"$dateFromString": {
                    "dateString": "$call_started_at",
                    "timezone": "Asia/Kolkata"
                }},
                "call_from_name": 1,
                "call_from": 1,
                "call_to_name": 1,
                "call_to": 1,
                "call_duration": 1,
                "type": 1
            }})
            pipeline[1].get("$match", {}).update(
                {"call_started_at": {"$gte": start_date,
                                "$lte": end_date}})
        results = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)
        async for data in results:
            if str(data.get("_id")) in temp_dict:
                temp_dict.get(str(data.get("_id"))).update({
                    "inbound_call": {
                        "total_call_received": data.get('total_call_attempted',
                                                        0),
                        "total_missed_Call": data.get('total_missed_call', 0),
                        "total_call_duration": utility_obj.format_float_to_2_places(
                            data.get('total_call_duration', 0) / 60),
                        "total_connected_calls": data.get(
                            "total_connected_calls",
                            0)}})
            else:
                temp_dict[str(data.get('_id'))] = {
                    "counselor_id": str(data.get('_id')),
                    "counselor_name": data.get('counselor_name'),
                    "outbound_call": {"total_call_attempted": 0,
                                      "total_call_duration": 0,
                                      "total_connected_calls": 0} if call_type == "Inbound" else {
                        "total_call_attempted": data.get(
                            'total_call_attempted', 0),
                        "total_call_duration": utility_obj.format_float_to_2_places(
                            data.get('total_call_duration', 0) / 60),
                        "total_connected_calls": data.get(
                            "total_connected_calls", 0)
                    },
                    "inbound_call": {"total_call_received": data.get(
                        'total_call_attempted'),
                        "total_missed_Call": data.get(
                            'total_missed_call', 0),
                        "total_connected_calls": data.get(
                            "total_connected_calls", 0),
                        "total_call_duration": utility_obj.format_float_to_2_places(
                            data.get('total_call_duration',
                                     0) / 60)} if call_type == "Inbound" else {
                        "total_call_received": 0, "total_missed_Call": 0,
                        "total_call_duration": 0, "total_connected_calls": 0}
                }
        return temp_dict

    async def counselor_wise_call_activity_data(
            self, user: dict, date_range: dict, page_num: int, page_size: int,
            college: dict) -> dict:
        """
        Get counselor wise call activity data count.

        Params:
            - user (dict): A dictionary which contains user data.
            - date_range (dict): A dictionary which contains start date and
                end date which useful for filter data according to date range.
                e.g., {"start_date": "2023-10-27", "end_date": "2023-10-27"}
            - page_num (int): A integer number which represents page number
                where want to show data. e.g., 1
            - page_size (int): A integer number which represents data count per
                page. e.g., 25
            - college (dict): A dictionary which contains college data.

        Returns:
            - dict: A dictionary which contains counselor-wise call activity
                data count.
        """
        if user.get("role", {}).get("role_name") == "college_counselor":
            counselor_ids = [ObjectId(user.get('_id'))]
        else:
            if user.get("role", {}).get(
                    "role_name") == "college_head_counselor":
                counselor_ids = await AdminUser().get_users_ids_by_role_name(
                    "college_counselor", college.get("id"), user.get("_id"))
            else:
                counselor_ids = await AdminUser().get_users_ids_by_role_name(
                    "college_counselor", college.get("id"))
        outbound_call_details = await self.call_activity_data_by_type(
            "Outbound", counselor_ids, "call_from", {}, date_range)
        inbound_call_details = await self.call_activity_data_by_type(
            "Inbound", counselor_ids, "call_to", outbound_call_details,
            date_range)
        final_data = [value for value in inbound_call_details.values()]
        response = await utility_obj.pagination_in_api(
            page_num, page_size, final_data, len(final_data),
            route_name="/call_activities/counselor_wise_data/")
        return {"data": response.get('data'),
                "total": len(final_data),
                "count": page_size,
                "pagination": response.get("pagination"),
                "message": "Get counselor wise call activity data."
                }


class CounselorLead:
    """
    Contain functions related to counselor lead activities
    """

    async def format_counselor_leads(self, lead_data):
        """
        Helper function for return counselor lead data in a proper format
        """
        return {'student_name': utility_obj.name_can(
            lead_data.get('basic_details', {})),
            'student_id': str(lead_data.get('_id')),
            'student_mobile_no': lead_data.get('basic_details', {}).get(
                'mobile_number')}

    async def get_counselor_leads_details(self, counselor_id, page_num,
                                          page_size, search_input):
        """
        Get counselor leads details like name and mobile number
        """
        pipeline = [
            {
                '$match': {
                    'allocate_to_counselor.counselor_id': counselor_id
                }
            },
            {
                '$project': {
                    '_id': 1,
                    'basic_details': 1
                }
            },
            {
                "$facet": {
                    "paginated_results": [],
                    "totalCount": [{"$count": "count"}],
                }
            }
        ]
        if search_input:
            pipeline[0].get("$match", {}).update({
                "basic_details.mobile_number": {
                    "$regex": f"^{search_input}"}})
        if page_num is not None and page_size is not None:
            skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                                  page_size)
            pipeline[-1].get("$facet", {}).get("paginated_results", []).extend(
                [{"$skip": skip}, {"$limit": limit}])
        result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            pipeline)
        temp_data, total_data = [], 0
        async for doc in result:
            try:
                total_data = doc.get("totalCount")[0].get("count", 0)
            except IndexError:
                total_data = 0
            temp_data = [await self.format_counselor_leads(lead_data) for
                         lead_data in doc.get("paginated_results", [])]
        return temp_data, total_data
