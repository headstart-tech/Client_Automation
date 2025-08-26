"""
This file contain class and functions for returns the list of counselor
"""
import asyncio
import json
from datetime import datetime

from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException

from app.core.custom_error import DataNotFoundError
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.database.aggregation.college import College
from app.database.configuration import DatabaseConfiguration
from app.helpers.roles.role_permission_helper import RolePermissionHelper
from app.helpers.user_curd.user_configuration import UserHelper

logger = get_logger(name=__name__)


class AdminUser:
    """
    Contain functions related to admin user activities
    """

    async def get_timeline(self, user, own_timeline,
                           college_super_admin_timeline,
                           head_counselors_timeline,
                           counselors_timeline, page_num, page_size):
        """
        Return users timeline based on filter
        """
        pipeline = []
        if own_timeline:
            pipeline.append({'$match': {'user_id': user.get('_id')}})
        elif college_super_admin_timeline:
            if user.get('role', {}).get('role_name') not in ["super_admin",
                                                             "client_manager"]:
                raise HTTPException(status_code=401,
                                    detail="Not enough permissions")
            pipeline.append({'$match': {'user_type': "college_super_admin"}})
        elif head_counselors_timeline:
            if user.get('role', {}).get('role_name') not in \
                    ["college_super_admin", "college_admin"]:
                raise HTTPException(status_code=401,
                                    detail="Not enough permissions")
            pipeline.append(
                {'$match': {'user_type': "college_head_counselor"}})
        elif counselors_timeline:
            if user.get('role', {}).get('role_name') not in [
                "college_super_admin", "college_admin",
                "college_head_counselor"]:
                raise HTTPException(status_code=401,
                                    detail="Not enough permissions")
            pipeline.append({'$match': {'user_type': "college_counselor"}})
        pipeline.extend([{"$unwind": {"path": "$timelines"}},
                         {"$sort": {"timelines.timestamp": -1}}])
        if page_num and page_size:
            skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                                  page_size)
            paginated_results = [{"$skip": skip}, {"$limit": limit}]
        else:
            paginated_results = []
        pipeline.append(
            {
                "$facet": {
                    "paginated_results": paginated_results,
                    "totalCount": [{"$count": "count"}],
                }
            }
        )
        result = DatabaseConfiguration().user_timeline_collection.aggregate(
            pipeline)
        data, total_data = [], 0
        async for documents in result:
            try:
                total_data = documents.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
            for document in documents.get("paginated_results"):
                data.append({'_id': str(document.get('_id')),
                             'user_id': str(document.get('user_id')),
                             'user_type': document.get('user_type'),
                             'timestamp': utility_obj.get_local_time(
                                 document.get('timelines', {}).get(
                                     'timestamp')),
                             'message': f"{document.get('timelines', {}).get('event_status')} {document.get('timelines', {}).get('event_type')}"})
        return data, total_data

    async def packing_data(
            self, user: dict,
            page_num: int | None = None,
            page_size: int | None = None,
            sort_type: str | None = None,
            column_name: str | None = None,
            search_pattern: str | None = None,
            filters: list | None = None,
    ):
        """
        Perform aggregation and packing data into users list
        """

        pipeline = [
            {"$sort": {"created_on": -1}},
            {
                "$lookup": {
                    "from": "colleges",
                    "localField": "associated_colleges",
                    "foreignField": "_id",
                    "as": "college_details"
                }
            },
            {
                "$unwind": {
                    "path": "$college_details",
                    "preserveNullAndEmptyArrays": True
                }
            }
        ]
        if user.get("role", "") == "super_admin":
            pipeline.insert(0, {
                "$match": {
                    "role.role_name": {
                        "$nin": ["super_admin"]
                    }
                }
            })
        elif user.get("role", "") == "admin":
            pipeline.insert(0, {
                "$match": {
                    "role.role_name": {
                        "$nin": ["super_admin", "admin"]
                    }
                }
            })
        else:
            college_ids = [ObjectId(college_id) for college_id in
                           user.get("associated_colleges", [])]

            if not college_ids:
                user_temp = user.copy()
                user_temp["role"] = {}
                user_temp["_id"] = user.get("user_id")
                user_temp["role"]["role_name"] = user.get("role", "")
                college_details = await College().get_college_data(
                    user=user_temp, using_for="authentication")
                college_ids = [ObjectId(document.get("id")) for document in college_details]

            roles_details = await RolePermissionHelper().fetch_pgsql_entity(
                current_user=user, data_type="roles")

            college_role_ids, global_role_ids = [], []
            roles_details = jsonable_encoder(roles_details)
            roles_details = json.loads(roles_details.get("body", {}))

            for data in roles_details.get("data", []):
                if data.get("scope") == "college":
                    college_role_ids.append(ObjectId(data.get("mongo_id")))
                elif data.get("scope") == "global":
                    global_role_ids.append(ObjectId(data.get("mongo_id")))

            temp_pipeline = [
                {
                    "$lookup": {
                        "from": "client_configurations",
                        "localField": "_id",
                        "foreignField": "assigned_account_managers",
                        "as": "client_details"
                    }
                },
                {
                    "$unwind": {
                        "path": "$client_details",
                        "preserveNullAndEmptyArrays": True
                    }
                },
                {
                    "$project": {
                        "client_id": "$client_details.client_id",
                        "account_manager_id": "$_id"
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "client_ids": {"$push": "$client_id"},
                        "manager_ids": {"$push": "$account_manager_id"}
                    }
                },
                {
                    "$project": {
                        "all_ids": {
                            "$setUnion": ["$client_ids", "$manager_ids"]
                        }
                    }
                }
            ]
            check_super_account = False
            if user.get("role", "") == "super_account_manager":
                check_super_account = True
                temp_pipeline.insert(
                    0, {"$match": {
                        "associated_super_account_manager": ObjectId(user.get("user_id"))}})

            user_ids = []
            if user.get("role", "") == "account_manager":
                check_super_account = True
                temp_pipeline.insert(
                    0, {"$match": {
                        "_id": ObjectId(user.get("user_id"))}})

            if check_super_account:
                temp_result = await DatabaseConfiguration().user_collection.aggregate(
                    temp_pipeline).to_list(length=None)
                if temp_result:
                    temp_result = temp_result[0]
                    user_ids = temp_result.get("all_ids", [])

            pipeline.insert(0, {
                '$match': {
                    '$or': [
                        {
                            '$expr': {
                                '$and': [
                                    {'$ne': [
                                        {'$filter': {
                                            'input': '$associated_colleges',
                                            'as': 'college',
                                            'cond': {'$in': ['$$college', college_ids]}
                                        }},
                                        []
                                    ]},
                                    {'$in': ['$role.role_id', college_role_ids]}
                                ]
                            }
                        },
                        {
                            '$and': [
                                {'role.role_id': {'$in': global_role_ids}},
                                {'_id': {'$in': user_ids}}
                            ]
                        }
                    ]
                }
            })

        if filters:
            base_filter = {"user_type": {"$in": filters}}
            pipeline[0].get("$match", {}).update(base_filter)

        if search_pattern not in ["", None]:
            match_pattern = {"$regex": f".*{search_pattern}.*", "$options": "i"}
            pipeline.append({
                "$match": {
                    "$or": [
                        {
                            "name": match_pattern
                        },
                        {
                            "email": match_pattern
                        },
                        {
                            "mobile_number": match_pattern
                        },
                        {
                            '$expr': {
                                '$regexMatch': {
                                    'input': {'$toString': '$mobile_number'},
                                    'regex': f'.*{search_pattern}.*',
                                    'options': 'i'
                                }
                            }
                        }
                    ]
                }
            })
        facet = {
            "$facet": {
                "metadata": [
                    {"$count": "total"}
                ],
                "data": [
                    {
                        "$project": {
                            "_id": 1,
                            "name": {
                                "$trim": {
                                    "input": {
                                        "$concat": [
                                            "$first_name",
                                            " ",
                                            "$middle_name",
                                            " ",
                                            "$last_name"
                                        ]
                                    }
                                }
                            },
                            "email": 1,
                            "mobile_number": 1,
                            "role": {
                                "$cond": {
                                    "if": {"$regexMatch": {"input": "$role.role_name",
                                                           "regex": "^college_"}},
                                    "then": {
                                        "$reduce": {
                                            "input": {"$split": [{"$arrayElemAt": [
                                                {"$split": ["$role.role_name",
                                                            "college_"]}, 1]}, "_"]},
                                            "initialValue": "",
                                            "in": {
                                                "$trim": {
                                                    "input": {
                                                        "$concat": ["$$value", " ",
                                                                    "$$this"]}
                                                }
                                            }}},
                                    "else": {
                                        "$reduce": {
                                            "input": {
                                                "$split": ["$role.role_name", "_"]},
                                            "initialValue": "",
                                            "in": {
                                                "$trim": {
                                                    "input": {
                                                        "$concat": ["$$value", " ",
                                                                    "$$this"]}
                                                }}}
                                    }
                                }
                            },
                            "created_on": 1,
                            "last_accessed": 1,
                            "is_activated": 1,
                            "associated_source_value": 1,
                            "college_name": "$college_details.name",
                            "bulk_lead_push_limit": "$college_details.bulk_lead_push_limit"
                        }
                    }
                ]
            }
        }

        if page_num and page_size:
            skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                                  page_size)
            facet.get("$facet", {}).get("data", []).insert(0, {"$skip": skip})
            facet.get("$facet", {}).get("data", []).insert(1, {"$limit": limit})

        pipeline.append(facet)

        if sort_type and column_name:
            sort_order = 1 if sort_type == "asc" else -1
            pipeline.append({"$sort": {f"data.{column_name}": sort_order}})
        pipeline.append({
            "$project": {
                "_id": 0,
                "total": {
                    "$arrayElemAt": [
                        "$metadata.total", 0]
                },
                "data": {
                    "$map": {
                        "input": "$data",
                        "as": "item",
                        "in": {
                            "user_id": {"$toString": "$$item._id"},
                            "user_name": "$$item.name",
                            "user_email": "$$item.email",
                            "mobile_number": "$$item.mobile_number",
                            "user_role": "$$item.role",
                            "created_on": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d %H:%M:%S",
                                    "date": "$$item.created_on",
                                    "timezone": "+05:30"
                                }
                            },
                            "last_active_on": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d %H:%M:%S",
                                    "date": "$$item.last_accessed",
                                    "timezone": "+05:30"
                                }
                            },
                            "is_activated": "$$item.is_activated",
                            "associated_source_value":
                                {"$ifNull": ["$$item.associated_source_value", {"$literal": "--"}]},
                            "institute_allocated": {"$ifNull": ["$$item.college_name",
                                                                {"$literal": "--"}]},
                            "status": {"$cond": ["$$item.is_activated", "Active", "Inactive"]},
                            "source": {
                                "$ifNull": ["$$item.associated_source_value", {"$literal": "--"}]},
                            "bulk_limit": {"$ifNull": ["$$item.bulk_lead_push_limit.bulk_limit",
                                                       {"$literal": 0}]},
                            "daily_limit": {"$ifNull": ["$$item.bulk_lead_push_limit.daily_limit",
                                                        {"$literal": 0}]},
                        }
                    }
                }
            }
        })

        result = await DatabaseConfiguration().user_collection.aggregate(
            pipeline).to_list(length=None)

        if not result:
            return [], 0

        data = result[0]

        return data.get("data", []), data.get("total", 0)

    async def all_details(
            self, user, page_num=None, page_size=None,
            sort_type: str | None = None, column_name: str | None = None,
            search_pattern: str | None = None, filters: list | None = None):
        """
        Get all_users details.
        Condition for get all users details - If college_super_admin or college_admin login into system then we're checking
        its associated colleges ids and based on each associated college id, we're taking all users of each associated colleges.
        """
        total_record, total = await self.packing_data(
            user=user, page_num=page_num,
            page_size=page_size,
            sort_type=sort_type, column_name=column_name,
            search_pattern=search_pattern, filters=filters
        )
        return total_record, total

    async def combine_session_info(self, session_document):
        """
        Get session information of users in a particular format.

        Params:
            session_document: A dictionary containing the session information.

        Returns:
            dict: A dictionary containing the session information.
        """
        role_name = await utility_obj.get_role_name_in_proper_format(
            session_document.get("user_type"))
        return {
            "_id": session_document.get("refresh_token"),
            "user_id": str(session_document.get("user_id")),
            "user_type": role_name,
            "user_email": session_document.get("user_email"),
            "device_info": session_document.get("device_info"),
            "ip_address": session_document.get("ip_address"),
            "issued_at": session_document.get("issued_at"),
            "expiry_time": session_document.get("expiry_time"),
            "is_revoked": session_document.get("revoked")
        }

    async def get_session_info_from_DB(self, user_ids, page_num, page_size):
        """
        Get session info of users from DB.

        Params:
            page_num (int): The page number for pagination.
            page_size (int): The number of sessions per page.

        Returns:
            list: A list containing the session information of users
            int: Count of all session information documents

        """
        pipeline = [
            {"$match": {"user_type": {"$ne": "student"}, "user_id": {"$in": user_ids}}},
            {
                "$facet": {
                    "paginated_results": [{"$sort": {"issued_at": -1}}],
                    "totalCount": [{"$count": "count"}]
                }
            }]
        if page_num and page_size:
            skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                                  page_size)
            pipeline[1].get("$facet", {}).get("paginated_results", []).extend(
                [{"$skip": skip}, {"$limit": limit}])
        result = DatabaseConfiguration().refresh_token_collection.aggregate(
            pipeline)
        data, total_data = [], 0
        async for documents in result:
            try:
                total_data = documents.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
            gather_data = [self.combine_session_info(session_document) for
                           session_document in
                           documents.get("paginated_results", [])]
            data = await asyncio.gather(*gather_data)
        return data, total_data

    async def session_info(self, college_id, current_user, page_num, page_size,
                           route_name=None):
        """
        Get session information of users.

        Params:
            current_user: The current user object.
            page_num (int): The page number for pagination.
            page_size (int): The number of sessions per page.
            route_name (str): The name of the route.

        Returns:
            dict: A dictionary containing the session information.

        Raises:
            SomeException: An exception that may occur during the execution.
        """
        await UserHelper().is_valid_user(current_user)
        try:
            aggregation_pipeline = [{
                "$match": {"associated_colleges": {"$in": [ObjectId(college_id)]}}
            },
                {
                    "$group": {
                        "_id": None,
                        "users_ids": {"$push": "$_id"}
                    }
                }
            ]
            aggregation_result = await DatabaseConfiguration().user_collection. \
                aggregate(aggregation_pipeline).to_list(None)
            user_ids = aggregation_result[0].get("users_ids", []) if aggregation_result else []
            session_data, count_of_data = await self.get_session_info_from_DB(
                user_ids, page_num, page_size)
            if session_data:
                response = {}
                if page_num and page_size:
                    response = await utility_obj.pagination_in_aggregation(
                        page_num, page_size, count_of_data,
                        route_name)
                return {
                    "data": session_data,
                    "total": count_of_data,
                    "count": page_size,
                    "pagination": response.get("pagination"),
                    "message": "Get session info of users."
                }
            return {"detail": "Session info data not found."}
        except Exception as e:
            logger.error(f"Failed to get session info of users. Error - {e}")

    async def update_base_match_based_on_time(
            self, start_time: datetime, end_time: datetime,
            available_panelist: bool = False, program: list | None = None) \
            -> list:
        """
        Update match stage based on start time and end time.

        Params:
            start_time (datetime): A start datetime.
            end_date (datetime): An end datetime.
            available_panelist (bool): Useful when getting available
                panelist data based on slot/panel id.

        Returns:
            list: A list which contains panelist ids.
        """
        if not available_panelist:
            start_time = await utility_obj.date_change_utc(start_time)
            end_time = await utility_obj.date_change_utc(end_time)
        pipeline = [
            {
                "$match": {
                    "time": {"$gte": start_time, "$lt": end_time}
                }
            },
            {
                "$addFields": {
                    "panelists": {
                        "$ifNull": ["$panelists", []]
                    }
                }
            },
            {
                "$group": {
                    "_id": "",
                    "all_panelists": {
                        "$push": "$panelists"
                    }
                }
            }]
        panelists, elements = [], []
        result = DatabaseConfiguration().slot_collection.aggregate(pipeline)
        async for documents in result:
            panelists = [sublist for sublist in
                         documents.get('all_panelists', []) if sublist != []]
            elements = [elem for sublist in panelists for elem in sublist]
        if program:
            all_panelist = await self.get_panelists_program_wise(program)
        else:
            all_panelist = DatabaseConfiguration().user_collection.aggregate(
                [{"$match": {"role.role_name": "panelist"}}])
        async for user in all_panelist:
            _id = user.get('_id')
            if _id not in elements:
                elements.append(_id)
        panelists_count = len(panelists)
        if panelists_count != 1:
            panelists = [item for item in elements if
                         elements.count(item) != panelists_count]
        else:
            panelists = [item for item in elements if item != elements]
        return panelists

    async def get_panelists_program_wise(self, program: list):
        """
        Get panelist based on program.

        Params:
            program: A list which contains program details like course names
            and specialization names.

        Returns:
            panelists: A list of panelists which belongs to the given
            program.
        """
        all_panelist = await DatabaseConfiguration().user_collection.aggregate(
            [{"$match": {"selected_programs": {"$in": program}}}]).to_list(
            length=None)
        panelists = [panelist_doc.get('_id') for panelist_doc in
                     all_panelist]
        return panelists

    async def get_panelist_by_ids(
            self, college_id: str, panelist_ids: list | None = None,
            filters: dict | None = None, page_num: None | int = None,
            page_size: None | int = None, get_panelists: bool = False) \
            -> tuple:
        """
        Get panelist data by ids or filters.

        Params:
            - college_id (str): An unique id/identifier of a college.
                e.g., 123456789012345678901234
            panelist_ids (list): A list contains panelist ids.
                For Example, ["64b2c11e9f4f0ce7ad232512",
                            "64b2c11e9f4f0ce7ad232513"]
            filters (dict): A dictionary which contains filterable data.
            page_num (int | None): Page number where you want to
                users data. For example, 1
            page_size (int | None): Page size means how many data you want to
                show on page_num. For example, 25
            get_panelists (bool): Useful for get panelists data based on
                program.

        Returns:
            tuple: A tuple which contains panelist data along with count.
                For example:
                ([{"name" "test", "school": "sot", "designation": "test",
                "selected_programs": ["test"], "email": "test@gmail.com"},
                ...], 2)
        """
        base_match = {"role.role_name": "panelist",
                      "associated_colleges": {"$in": [ObjectId(college_id)]}}
        if panelist_ids:
            _ids = []
            for _id in panelist_ids:
                await utility_obj.is_id_length_valid(_id, name="Panelist id "
                                                               f"`{_id}`")
                _ids.append(ObjectId(_id))
            base_match.update(
                {"_id": {"$in": _ids}})
        if filters:
            program = filters.get('program')
            active = filters.get('is_activated')
            interview_list_id = filters.get('interview_list_id')
            start_time = filters.get('start_time')
            end_time = filters.get('end_time')
            search_input = filters.get("search_input")
            if search_input:
                name_pattern = f".*{search_input}.*"
                new_pattern = {"$regex": name_pattern, "$options": "i"}
                base_match.update({"$or": [
                    {"first_name": new_pattern},
                    {"last_name": name_pattern}, {"email": new_pattern}]})
            if interview_list_id:
                base_match.update({"is_activated": True})
                await utility_obj.is_length_valid(_id=interview_list_id,
                                                  name="Interview list id")
                if (interview_list := await DatabaseConfiguration().
                        interview_list_collection.find_one(
                    {"_id": ObjectId(interview_list_id)})) is None:
                    raise DataNotFoundError(message="Interview list")
                program = [
                    {"course_name": interview_list.get('course_name'),
                     "specialization_name":
                         interview_list.get('specialization_name')}]
            if program:
                panelists = await self.get_panelists_program_wise(program)
                if len(panelists) > 0 or get_panelists:
                    base_match.update({"selected_programs": {"$in": program}})
            if active is not None:
                base_match.update({"is_activated": active})
            if start_time and end_time:
                panelists = await self.update_base_match_based_on_time(
                    start_time, end_time, program)
                base_match.update({"_id": {"$in": panelists}})
        pipeline = [
            {"$match": base_match},
            {"$sort": {"created_on": -1}},
            {"$project": {
                "_id": {"$toString": "$_id"},
                "name": {"$concat": ["$first_name",
                                     " ", "$middle_name",
                                     " ", "$last_name"]},
                "school": "$school_name",
                "designation": "$designation",
                "selected_programs": "$selected_programs",
                "email": "$email",
            }}
        ]
        paginated_results = []
        if page_num and page_size:
            skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                                  page_size)
            paginated_results = [{"$skip": skip}, {"$limit": limit}]
        pipeline.append(
            {
                "$facet": {
                    "paginated_results": paginated_results,
                    "totalCount": [{"$count": "count"}],
                }
            }
        )
        result = DatabaseConfiguration().user_collection.aggregate(pipeline)
        users, total_users = [], 0
        async for documents in result:
            try:
                total_users = documents.get("totalCount")[0].get("count")
            except IndexError:
                total_users = 0
            users = [document for document in
                     documents.get("paginated_results")]
        return users, total_users

    async def available_panelist_by_filters(self, filters: dict | None) \
            -> list:
        """
        Get panelist data by filters.

        Params:
            filters (dict | None): A dictionary which contains filterable
                fields with their values.

        Returns:
            list: A list which contains panelist data.
        """
        base_match = {"role.role_name": "panelist"}
        if filters:
            panelist_ids = filters.get('panelist_ids')
            if panelist_ids:
                base_match.update(
                    {"_id": {"$in": panelist_ids}})
            filter_slot_panel = filters.get('filter_slot_panel')
            if filter_slot_panel:
                name_query = filter_slot_panel.get("search_by_panelist")
                if name_query:
                    name_pattern = f".*{name_query}.*"
                    base_match.update({"$or": [
                        {"first_name": {"$regex": name_pattern,
                                        "$options": "i"}},
                        {"last_name": {"$regex": name_pattern,
                                       "$options": "i"}}]})
        pipeline = [
            {"$match": base_match},
            {"$sort": {"created_on": -1}},
            {"$project": {
                "_id": {"$toString": "$_id"},
                "name": {"$concat": ["$first_name",
                                     " ", "$middle_name",
                                     " ", "$last_name"]},
                "school": "$school_name",
                "school_short": {
                    "$reduce": {
                        "input": {"$split": ["$school_name", " "]},
                        "initialValue": "",
                        "in": {"$concat": ["$$value",
                                           {"$substr": ["$$this", 0, 1]}]}
                    }},
                "designation": "$designation",
                "selected_programs": "$selected_programs",
            }}
        ]
        result = DatabaseConfiguration().user_collection.aggregate(pipeline)
        return [document async for document in result]

    async def get_notification_info_of_users(
            self, college_id: str, role_names: list[str], content: str,
            current_datetime: datetime, update_id: ObjectId, title: str) -> list:
        """
        Get notification information of users.

        Params:
            - college_id (str): A unique id/identifier of a college.
                e.g., 123456789012345678901234
            - role_names (list[str]): A list which contains role names.
                e.g., ["super_admin", "college_admin"]
            - content (str): Message of send update.
            - current_datetime (datetime): Datetime of event.
            - update_id (ObjectId): An unique identifier/id of an update.

        Returns:
            list: A list which contains notification information of users.
        """
        match_condition = {"$or": [{"associated_colleges":
                                        {"$in": [ObjectId(college_id)]},
                                    "role.role_name": {"$in": role_names}}]}
        if "super_admin" in role_names:
            match_condition.get("$or", []).append(
                {"role.role_name": "super_admin"})
        pipeline = [{"$match": match_condition},
                    {"$project": {"_id": 0, "event_type": "Important Update",
                                  "send_to": "$_id", "message": content,
                                  "mark_as_read": {"$literal": False},
                                  "event_datetime": current_datetime}}]
        result = DatabaseConfiguration().user_collection.aggregate(pipeline)
        return [{**document, 'created_at': datetime.utcnow(),
                 "update_resource_id": update_id, "title": title}
                async for document in result]

    async def get_chart_info(self, college_info: dict) -> dict:
        """
        Get user chart information.

        Params:
            - college_info (dict): A dictionary which contains college information.

        Returns:
            - dict: A dictionary which contains user chart information.
                e.g., {"userChart": {"labels": ["test"], "data": [1]},
                "dataChart": {"data": [44, 55, 41], "labels": [
                    "Limited", "Created", "Balance"]}}
        """
        college_id = ObjectId(college_info.get("id"))

        aggregation_pipeline = [{
            '$match': {
                'role.role_name': {'$ne': 'super_admin'},
                "associated_colleges": {"$in": [college_id]}
            }
        }, {
            '$group': {
                '_id': {'role': '$role.role_name', 'active': '$is_activated'},
                'count': {'$sum': 1}
            }
        }, {
            '$group': {
                '_id': '$_id.role',
                'total_count': {'$sum': '$count'},
                'active_count': {'$sum': {'$cond': [{'$eq': ['$_id.active', True]}, '$count', 0]}},
                'inactive_count': {
                    '$sum': {'$cond': [{'$eq': ['$_id.active', False]}, '$count', 0]}}
            }
        }, {
            '$sort': {'_id': 1}
        }, {
            '$group': {
                '_id': None,
                'total': {'$sum': '$total_count'},
                'roles': {
                    '$push': {
                        'role': {
                            '$reduce': {
                                'input': {'$split': ['$_id', '_']},
                                'initialValue': '',
                                'in': {'$trim': {'input': {'$concat': ['$$value', ' ', '$$this']}}}
                            }
                        },
                        'total_count': '$total_count',
                        'active_count': '$active_count',
                        'inactive_count': '$inactive_count',
                        'active_percentage': {
                            '$round': [{'$multiply': [
                                {'$divide': ['$active_count', '$total_count']}, 100]}, 2]
                        },
                        'inactive_percentage': {
                            '$round': [{'$multiply': [
                                {'$divide': ['$inactive_count', '$total_count']}, 100]}, 2]
                        }
                    }
                }
            }
        }, {
            '$project': {
                '_id': 0,
                'labels': '$roles.role',
                'data': {
                    '$map': {
                        'input': '$roles',
                        'as': 'role_data',
                        'in': {
                            'total_count': '$$role_data.total_count',
                            'active_count': '$$role_data.active_count',
                            'inactive_count': '$$role_data.inactive_count',
                            'active_percentage': '$$role_data.active_percentage',
                            'inactive_percentage': '$$role_data.inactive_percentage',
                            'overall_percentage': {
                                '$round': [{'$multiply': [
                                    {'$divide': ['$$role_data.total_count', '$total']}, 100]}, 2]
                            }
                        }
                    }
                }
            }
        }]

        aggregation_result = await DatabaseConfiguration().user_collection.aggregate(
            aggregation_pipeline).to_list(None)
        chart_info = aggregation_result[0] if aggregation_result else {}

        if (users_limit := settings.users_limit) is None:
            raise HTTPException(status_code=404, detail="Users limit not found.")

        aggregation_pipeline = [{
            '$match': {
                'role.role_name': {'$ne': 'super_admin'},
                "associated_colleges": {"$in": [college_id]}
            }
        }, {
            '$group': {
                '_id': '$is_activated',
                'count': {'$sum': 1}
            }
        }, {
            '$group': {
                '_id': None,
                'active_count': {'$sum': {'$cond': [{'$eq': ['$_id', True]}, '$count', 0]}},
                'inactive_count': {'$sum': {'$cond': [{'$eq': ['$_id', False]}, '$count', 0]}}
            }
        }, {
            '$project': {
                '_id': 0,
                'active_count': 1,
                'inactive_count': 1
            }
        }]

        aggregation_result = await DatabaseConfiguration().user_collection.aggregate(
            aggregation_pipeline).to_list(None)
        user_info = aggregation_result[0] if aggregation_result else {}

        active_count = user_info.get("active_count", 0)
        inactive_count = user_info.get("inactive_count", 0)
        balance = max(0, users_limit - (active_count + inactive_count))

        return {
            "userChart": {
                "labels": [item.title() for item in chart_info.get("labels", [])],
                "data": chart_info.get("data", [])
            },
            "dataChart": {
                "labels": ["Active", "Inactive", "Balance"],
                "data": [active_count, inactive_count, balance]
            }
        }

    async def get_users_ids_by_role_name(
            self, role_name: str, college_id: str,
            head_counselor_id: str | None = None) -> list:
        """
        Get users ids by role_name.

        Params:
            - role_name (str): A string which represent role name.
                Useful for get all users based on role name.
            - college_id (str): An unique identifier of college for get
                college users. For example, 123456789012345678901234
            - head_counselor_id (str | None): Either None or head counselor
                id which useful for get users based on head counselor id.

        Returns:
            - list: A list which contains users ids.
        """
        base_match = {"associated_colleges":
                          {"$in": [ObjectId(college_id)]},
                      "role.role_name": role_name}
        if head_counselor_id:
            base_match.update(
                {"head_counselor_id": ObjectId(head_counselor_id)})
        aggregation_pipeline = [{
            "$match": base_match
        },
            {
                "$group": {
                    "_id": None,
                    "users_ids": {"$push": "$_id"}
                }
            }
        ]
        aggregation_result = await DatabaseConfiguration().user_collection. \
            aggregate(aggregation_pipeline).to_list(None)
        try:
            return aggregation_result[0].get("users_ids", [])
        except IndexError:
            return []
