"""
This file contain class and functions related to data segment
"""

import datetime

from bson import ObjectId

from app.core.custom_error import DataNotFoundError, CustomError
from app.core.utils import utility_obj, settings
from app.database.configuration import DatabaseConfiguration
from app.dependencies.jwttoken import Authentication
from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache
from app.helpers.automation.automation_configuration import AutomationHelper


class DataSegmentHelper:
    """
    Contain functions related to data segment
    """

    async def data_segment_helper(self, data, college_id, data_segments=False):
        """
        Get data segment details
        """
        total_data, data_list = await AutomationHelper().get_data_from_db(
            data, college_id, data_segments=data_segments, call_segments=True
        )
        if len(data.get("filters", {}).get("state_code", [])) > 0:
            state_names = []
            states = await get_collection_from_cache(collection_name="states")
            for state_code in data.get("filters", {}).get("state_code", []):
                if states:
                    state = utility_obj.search_for_document_two_fields(states,
                                                                       field1="state_code",
                                                                       field1_search_name=str(state_code).upper(),
                                                                       field2="country_code",
                                                                       field2_search_name="IN"
                                                                       )
                else:
                    state = await DatabaseConfiguration().state_collection.find_one(
                        {"state_code": state_code.upper(), "country_code": "IN"}
                    )
                state_names.append(state.get("name"))
            if not states:
                collection = await DatabaseConfiguration().state_collection.aggregate([]).to_list(None)
                await store_collection_in_cache(collection, collection_name="states")
            data["filters"]["state_names"] = state_names
        if len(data.get("filters", {}).get("counselor_id", [])) > 0:
            counselor_names, counselor_ids = [], []
            for counselor_id in data.get("filters", {}).get("counselor_id",
                                                            []):
                counselor = await DatabaseConfiguration().user_collection.find_one(
                    {"_id": ObjectId(counselor_id)}
                )
                counselor_names.append(utility_obj.name_can(counselor))
                counselor_ids.append(str(counselor_id))
            data["filters"]["counselor_names"] = counselor_names
            data["filters"]["counselor_id"] = counselor_ids
        if len(data.get("filters", {}).get("course", {})) > 0:
            temp_list = []
            if type(data.get("filters", {}).get("course")) == str:
                data["filters"]["course"] = []
            elif type(data.get("filters", {}).get("course")) == dict:
                if (
                        len(data.get("filters", {}).get("course", {}).get(
                            "course_id", {}))
                        > 0
                ):
                    course_id = (
                        data.get("filters", {}).get("course", {}).get(
                            "course_id", [])
                    )
                    specialization = (
                        data.get("filters", {})
                        .get("course", {})
                        .get("course_specialization", [])
                    )
                    for temp in zip(course_id, specialization):
                        temp_dict = {}
                        try:
                            temp_dict.update({"course_id": str(temp[0])})
                        except Exception:
                            temp_dict.update({"course_id": None})
                        try:
                            temp_dict.update(
                                {"course_specialization": str(temp[1])})
                        except Exception:
                            temp_dict.update({"course_specialization": None})
                        temp_list.append(temp_dict)
            data["filters"]["course"] = temp_list
        return {
            "data_segment_id": str(data.get("_id")),
            "data_segment_name": data.get("data_segment_name"),
            "data_segment_description": data.get("data_segment_description"),
            "module_name": data.get("module_name"),
            "segment_type": data.get("segment_type"),
            "filters": data.get("filters"),
            "advance_filters": data.get("advance_filters"),
            "raw_data_name": data.get("raw_data_name"),
            "period": data.get("period"),
            "enabled": data.get("enabled"),
            "is_published": data.get("is_published"),
            "created_by_id": str(data.get("created_by_id")),
            "created_by_name": data.get("created_by_name"),
            "created_on": utility_obj.get_local_time(data.get("created_on")),
            "updated_by": str(data.get("updated_by_id")),
            "updated_by_name": data.get("updated_by_name"),
            "updated_on": utility_obj.get_local_time(data.get("updated_on")),
            "count_of_entities": total_data,
            "entities_data": data_list,
        }

    async def get_state_names(self, state_codes: list[str]) -> list:
        """
        Get state names based on state codes

        Params:
            state_codes (list[str]): A list which contains state codes. e.g., ["AP", "UP"]

        Returns:
            list: A list which contains state names.
                e.g., ["Andra Pradesh", "Uttar Pradesh"]
        """
        aggregation_pipeline = [
            {"$match": {"state_code": {"$in": state_codes},
                        "country_code": "IN"}},
            {"$project": {"_id": 0, "name": 1}},
            {"$group": {"_id": "", "state_name": {"$push": "$name"}}},
        ]
        result = DatabaseConfiguration().state_collection.aggregate(
            aggregation_pipeline
        )
        async for document in result:
            return document.get("state_name")
        return []

    async def get_data_segment_communication_info(
            self, data_segment_id: ObjectId | None = None,
            status_dict: dict | None = None
    ) -> dict:
        """
        Get the particular/all data segment communication count information
            like total communication count, total email sent, total sms sent,
                total whatsapp sent etc.

        Params:
            - data_segment_id (ObjectId | None): None or A unique
                id/identifier of data segment.
                e.g., ObjectId("123456789012345678901234")
            - status (dict | None): Status of data segments. Useful for get data segments
                quick view information based on data segment status.
                Possible values: ["Active", "Closed"]

        Returns:
            dict: A dictionary which contains data segment (s) communication
                information. e.g., {"total": 0, "email": 0, "sms": 0,
                    "whatsapp": 0}
        """
        aggregation_pipeline = [
            {
                "$project": {
                    "_id": 0,
                    "email": {
                        "$cond": [{"$ifNull": [
                            "$communication_count.email", False]},
                            "$communication_count.email", 0]
                    },
                    "sms": {
                        "$cond": [
                            {"$ifNull": [
                                "$communication_count.sms", False]},
                            "$communication_count.sms", 0]
                    },
                    "whatsapp": {
                        "$cond": [
                            {"$ifNull": [
                                "$communication_count.whatsapp", False]},
                            "$communication_count.whatsapp", 0]
                    }
                }
            },
            {
                "$group": {
                    "_id": "",
                    "total": {
                        "$sum": {"$add": ["$email", "$sms", "$whatsapp"]}},
                    "email": {"$sum": "$email"},
                    "sms": {"$sum": "$sms"},
                    "whatsapp": {"$sum": "$whatsapp"},
                }
            },
            {"$project": {"_id": 0, "total": 1, "email": 1, "sms": 1,
                          "whatsapp": 1}},
        ]
        match_list = []
        if status_dict:
            match_list.append(status_dict)
        if data_segment_id:
            match_list.append({"_id": ObjectId(data_segment_id)})
        if match_list:
            aggregation_pipeline.insert(0, {"$match": {"$and": match_list}})
        result = DatabaseConfiguration().data_segment_collection.aggregate(
            aggregation_pipeline
        )
        async for document in result:
            return document
        return {"total": 0, "email": 0, "sms": 0, "whatsapp": 0}

    async def data_helper(self, data, college_id, data_segments):
        """
        Return data segment details
        """
        authentication_obj = Authentication()
        if data.get("segment_type", "").lower() == "dynamic":
            total_data, data_list = await AutomationHelper().get_data_from_db(
                data,
                college_id,
                data_segments=data_segments,
                call_segments=True,
                skip=0,
                limit=5,
            )
        else:
            total_data, data_list = 0, []
        if data.get("filters", {}).get("state_code"):
            data["filters"]["state_names"] = await self.get_state_names(
                data.get("filters", {}).get("state_code", [])
            )
        if len(data.get("filters", {}).get("counselor_id", [])) > 0:
            counselor_names, counselor_ids = [], []
            for counselor_id in data.get("filters", {}).get("counselor_id",
                                                            []):
                counselor = await DatabaseConfiguration().user_collection.find_one(
                    {"_id": ObjectId(counselor_id)}
                )
                counselor_names.append(utility_obj.name_can(counselor))
                counselor_ids.append(str(counselor_id))
            data["filters"]["counselor_names"] = counselor_names
            data["filters"]["counselor_id"] = counselor_ids
        if len(data.get("filters", {}).get("course", {})) > 1:
            if type(data.get("filters", {}).get("course")) == str:
                data["filters"]["course"] = {}
            course_id = data.get("filters", {}).get("course", {}).get(
                "course_id")
            data["filters"]["course"]["course_id"] = (
                [str(_id) for _id in course_id] if course_id else []
            )
            course_data = []
            if not data.get("course_name", [{}]):
                data["course_name"] = [{}]
            course_names = data.get("course_name", [{}])[0].get("course_name",
                                                                [])
            course_specs = (
                data.get("filters", {})
                .get("course", {})
                .get("course_specialization", [])
            )
            for course_name, course_spec in zip(course_names, course_specs):
                course_data.append(
                    f"{course_name} in {course_spec}"
                    if course_spec not in ["", None]
                    else f"{course_name} Program"
                )
            data["filters"]["course"]["course_name"] = course_data
        token = await authentication_obj.create_access_token(
            data={"sub": str(data.get("_id"))}
        )
        temp_dict = {
            "share_link": f"{settings.user_base_path}data-segment-details/{token}",
            "data_segment_name": data.get("data_segment_name"),
            "created_on": utility_obj.get_local_time(data.get("created_on")),
            "created_by_name": data.get("created_by_name"),
            "module_name": data.get("module_name"),
            "segment_type": data.get("segment_type"),
            "count_of_entities": data.get("count_at_origin", 0),
            "current_data_count": (
                total_data
                if data.get("segment_type", "").lower() == "dynamic"
                else data.get("data_count", 0)
            ),
            "communication_info": await self.get_data_segment_communication_info(
                data.get("_id")
            ),
            "linked_automation_count": len(data.get("automation_details", [])),
            "linked_automation_info": data.get("automation_details", []),
            "status": data.get("status"),
        }
        if data_segments:
            temp_dict.update(
                {
                    "data_segment_id": str(data.get("_id")),
                    "data_segment_description": data.get(
                        "data_segment_description"),
                    "filters": data.get("filters"),
                    "advance_filters": data.get("advance_filters"),
                    "raw_data_name": data.get("raw_data_name"),
                    "period": data.get("period"),
                    "enabled": data.get("enabled"),
                    "is_published": data.get("is_published"),
                    "created_by_id": str(data.get("created_by_id")),
                    "updated_by": str(data.get("updated_by_id")),
                    "updated_by_name": data.get("updated_by_name"),
                    "updated_on": utility_obj.get_local_time(
                        data.get("updated_on")),
                }
            )
        return temp_dict

    async def get_quick_view_info(
            self, status: str | None = None, counselor_id: list | None = None
    ) -> dict:
        """
        Get quick view information of data segments.

        Params:
            status (str): Status of data segments. Useful for get data segments
                quick view information based on data segment status.
                Possible values: ["Active", "Closed"]
            counselor_id (list): List of counselor ids to filter

        Returns:
            dict: A dictionary which contains data segments quick view info.
        """
        match_filter = {}
        lead_filter = {"module_name": "Lead"}
        application_filter = {"module_name": "Application"}
        raw_filter = {"module_name": "Raw Data"}
        payment_filter = {"module_name": "Payment"}
        active_filter = {"enabled": True}
        closed_filter = {"enabled": False}
        status_filter = {}
        if status not in ["", None]:
            if status in ["Active", "Closed"]:
                status_filter: dict = {
                    "enabled": True if status == "Active" else False}
                lead_filter.update(status_filter)
                application_filter.update(status_filter)
                raw_filter.update(status_filter)
                payment_filter.update(status_filter)
        if counselor_id:
            counselor_filter = {"shared_with.user_id": {"$in": counselor_id}}
            match_filter.update(counselor_filter)
            lead_filter.update(counselor_filter)
            application_filter.update(counselor_filter)
            raw_filter.update(counselor_filter)
            payment_filter.update(counselor_filter)
            status_filter.update(counselor_filter)
            active_filter.update(counselor_filter)
            closed_filter.update(counselor_filter)

        return {
            "total_data_segments": await DatabaseConfiguration().data_segment_collection.count_documents(
                match_filter
            ),
            "active_data_segments": await DatabaseConfiguration().data_segment_collection.count_documents(
                active_filter
            ),
            "closed_data_segments": await DatabaseConfiguration().data_segment_collection.count_documents(
                closed_filter
            ),
            "lead_data_segments": await DatabaseConfiguration().data_segment_collection.count_documents(
                lead_filter
            ),
            "application_data_segments": await DatabaseConfiguration().data_segment_collection.count_documents(
                application_filter
            ),
            "raw_data_segments": await DatabaseConfiguration().data_segment_collection.count_documents(
                raw_filter
            ),
            "payment_data_segments": await DatabaseConfiguration().data_segment_collection.count_documents(
                payment_filter
            ),
            "communication_info": await self.get_data_segment_communication_info(
                status_dict=status_filter
            ),
        }

    async def get_count_of_entities(
            self, data_segment_info: dict, college_id: str
    ) -> dict:
        """
        Get count of data segment entities.

        Params:
            - data_segment_info (str): A dictionary which contains data
                segment info.
            - college_id (str): A unique id/identifier of college.
                e.g., "123456789012345678901234"

        Returns:
            dict: A dictionary which contains information about count of data
                segment entities.
        """
        total_data, data_list = await AutomationHelper().get_data_from_db(
            data_segment_info,
            college_id,
            emails=True,
            call_segments=True,
            skip=0,
            limit=10,
        )
        return {"entities_count": total_data}

    async def add_custom_data(self, _id, data_segment_id, segment_details):
        """
        Add custom data to student mapping student data

        params:
            _id (str): Get the custom added student id
            data_segment_id (str): Get the custom added data segment id
            segment_details (dict): Get the segment details
        return:
            Student added successfully
        """
        await utility_obj.is_length_valid(_id, "Student")
        if (
                student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(_id)}
                )
        ) is None:
            raise DataNotFoundError(_id, "Student")
        if (
                await DatabaseConfiguration().data_segment_mapping_collection.find_one(
                    {
                        "student_id": ObjectId(_id),
                        "data_segment_id": ObjectId(data_segment_id),
                    }
                )
                is not None
        ):
            raise CustomError("Student already found in data segment")
        application = DatabaseConfiguration().studentApplicationForms.find(
            {"student_id": ObjectId(_id)}
        )
        await DatabaseConfiguration().data_segment_mapping_collection.insert_one(
            {
                "data_segment_id": ObjectId(data_segment_id),
                "application_id": [
                    ObjectId(app.get("_id")) async for app in application
                ],
                "student_id": ObjectId(student.get("_id")),
                "data_segment_name": segment_details.get("data_segment_name"),
                "mobile_number": student.get("basic_details", {}).get(
                    "mobile_number"),
                "student_name": utility_obj.name_can(
                    student.get("basic_details", {})),
                "email_id": student.get("basic_details", {}).get("email",''),
                "added_on": datetime.datetime.utcnow(),
                "custom_added": True,
                "updated_on": datetime.datetime.utcnow(),
            }
        )

    async def custom_student_assign(
            self, application_id: list | None, data_segment_id: str | None
    ):
        """
        Add student in the data segment.

        Params:
            application_id: An unique id/identifier of an application
                    which useful for add student in the data segment.
                e.g., 123456789012345678901234
            data_segment_id: An unique id/identifier of a data segment.
                e.g., 123456789012345678901231
            data_type (str): Data type will be lead/application
        Returns:
            dict: A dictionary which contains information about
                    add student in the data segment.

        Raises:
            ObjectIdInValid: An error occurred when
                            data_segment_id/application_id not valid.
            DataNotFoundError: An error occurred when
                                data_segment/application not found using id.
            CustomError: An error occurred when student already exists
                            in the data segment.
        """
        await utility_obj.is_length_valid(data_segment_id, "Data Segment")
        if (
                segment_details := await DatabaseConfiguration().data_segment_collection.find_one(
                    {"_id": ObjectId(data_segment_id)}
                )
        ) is None:
            raise DataNotFoundError(data_segment_id, "Data Segment")
        for _id in application_id:
            if segment_details.get("module_name", "").lower() == "application":
                await utility_obj.is_length_valid(_id, "Application")
                if (
                        application := await DatabaseConfiguration().studentApplicationForms.find_one(
                            {"_id": ObjectId(_id)}
                        )
                ) is None:
                    raise DataNotFoundError(_id, "Application")
                if (
                        await DatabaseConfiguration().data_segment_mapping_collection.find_one(
                            {
                                "application_id": ObjectId(_id),
                                "data_segment_id": ObjectId(data_segment_id),
                            }
                        )
                        is not None
                ):
                    raise CustomError("Student already found in data segment")
                if (
                        student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                            {"_id": ObjectId(application.get("student_id"))}
                        )
                ) is None:
                    raise CustomError(
                        f"Student not found by given" f" application id: {_id}."
                    )
                await (
                    DatabaseConfiguration().data_segment_mapping_collection.insert_one(
                        {
                            "data_segment_id": ObjectId(data_segment_id),
                            "application_id": ObjectId(_id),
                            "student_id": ObjectId(
                                application.get("student_id")),
                            "data_segment_name": segment_details.get(
                                "data_segment_name"
                            ),
                            "added_on": datetime.datetime.utcnow(),
                            "student_name": utility_obj.name_can(
                                student.get("basic_details", {})
                            ),
                            "email_id": student.get("basic_details", {}).get("email",''),
                            "mobile_number": student.get("basic_details",
                                                         {}).get(
                                "mobile_number"
                            ),
                            "custom_added": True,
                            "updated_on": datetime.datetime.utcnow(),
                        }
                    )
                )
            elif segment_details.get("module_name", "").lower() == "lead":
                await self.add_custom_data(
                    _id=_id,
                    data_segment_id=data_segment_id,
                    segment_details=segment_details,
                )
        count = (
            await (
                DatabaseConfiguration().data_segment_mapping_collection.count_documents(
                    {"data_segment_id": ObjectId(data_segment_id)}
                )
            )
        )
        await DatabaseConfiguration().data_segment_collection.update_one(
            {"_id": ObjectId(data_segment_id)}, {"$set": {"data_count": count}}
        )
        return {"message": "student added successfully in data segment."}

    async def user_shared_helper(
            self,
            field_name: str,
            value: str | ObjectId | None,
            data_segment_id: str | None,
            data_segment_details,
            permission,
    ):
        """
        Check the data segment user for the update the data segment permission

        params:
            field_name (str): Get the field name should be used for name
                email and user id,
            value (str): Get the value of email and user id
            data_segment_id (str): Get the data segment id should be used for
                filter the data segment and update.
            data_segment_details (str): Get the data segment details
            permission (str): Get the data segment permissions for user
                    e.q. (viewer/contributor)

        returns:
            response: User permission has been updated successfully
        """
        if not any(
                str(data.get(field_name)) == value
                for data in data_segment_details.get("shared_with", [])
        ):
            raise DataNotFoundError(value, field_name)
        temp_lst = []
        for data in data_segment_details.get("shared_with", []):
            if str(data.get(field_name)) == str(value):
                data["permission"] = permission
            temp_lst.append(data)
        await DatabaseConfiguration().data_segment_collection.update_one(
            {"_id": ObjectId(data_segment_id)},
            {"$set": {"shared_with": temp_lst}}
        )
        return {"data": "User permission has been updated successfully"}

    async def get_update_user_shared_permission(
            self,
            email_id: str | None,
            user_id: str | None,
            data_segment_id: str,
            permission: str | None,
    ):
        """
        Get the update the permission for the user with shared data segment

        params:
            email_id (str): get the email_id for the change the permission,
            permission (str): change the permission to the user with
                shared data segment.
            data_segment_id (str): get the id (identifier) for
                the fetch the data segment details
            permission (str): Get the permission for
                the user shared link permission
        returns:
            response: User permission has been updated successfully
        """
        await utility_obj.is_length_valid(data_segment_id, "Data Segment Id")
        if (
                data_segment_details := await DatabaseConfiguration().data_segment_collection.find_one(
                    {"_id": ObjectId(data_segment_id)}
                )
        ) is None:
            raise DataNotFoundError(data_segment_id, "Data Segment Id")
        if email_id:
            return await self.user_shared_helper(
                "email", email_id, data_segment_id, data_segment_details,
                permission
            )
        elif user_id:
            await utility_obj.is_length_valid(user_id, "user Id")
            return await self.user_shared_helper(
                "user_id",
                ObjectId(user_id),
                data_segment_id,
                data_segment_details,
                permission,
            )
        else:
            return {"data": "please provide email address or user_id"}

    async def get_data_segment_shared_user(
            self,
            data_segment_id: str | None,
    ):
        """
        get the user details who have data segment shared link

        params:
            - data_segment_id (str): get the data segment id of the
                data segment

        return:
            - A list containing the list of shared user
        """
        await utility_obj.is_length_valid(data_segment_id, "data_segment_id")
        if (
                data_segment := await DatabaseConfiguration().data_segment_collection.find_one(
                    {"_id": ObjectId(data_segment_id)}
                )
        ) is None:
            raise DataNotFoundError(data_segment_id, "data_segment")
        return [
            {
                "user_id": str(data.get("user_id")),
                "permission": data.get("permission"),
                "email": data.get("email"),
                "role": data.get("role"),
                "name": data.get("name"),
            }
            for data in data_segment.get("shared_with", [])
        ]

    async def remove_data_segment_permission_access(
            self, data_segment_id: str, user_id: str
    ) -> dict:
        """
        Remove data segment permission access

        params:
            - data_segment_id (str): Unique id of data segment
            - user_id (str): Unique id of user id

        return:
            - Dict: Message that data segment permission is removed

        Raises:
            - DataNotFound Exception: This occurs when data is not found
            - ObjectIdInvalid Exception: This occurs when the object id is invalid
            - Exception: An unexpected error occurred in code
        """
        await utility_obj.is_length_valid(data_segment_id, "data_segment_id")
        await utility_obj.is_length_valid(user_id, "user_id")
        if (
                await DatabaseConfiguration().data_segment_collection.find_one(
                    {"_id": ObjectId(data_segment_id)}
                )
        ) is None:
            raise DataNotFoundError(data_segment_id, "data_segment")
        if (
                await DatabaseConfiguration().user_collection.find_one(
                    {"_id": ObjectId(user_id)}
                )
        ) is None:
            raise DataNotFoundError(user_id, "user_id")
        await DatabaseConfiguration().data_segment_collection.update_one(
            {"_id": ObjectId(data_segment_id)},
            {"$pull": {"shared_with": {"user_id": ObjectId(user_id)}}},
        )
        await DatabaseConfiguration().notification_collection.find_one_and_update(
            {
                "send_to": ObjectId(user_id),
                "data_segment_id": ObjectId(data_segment_id)
            },
            {"$set": {"hide": True}},
            sort=[('created_at', -1)]
            )
        return {"message": "Removed Permission access successfully!"}
