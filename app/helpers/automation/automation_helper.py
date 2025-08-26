"""
This file contains the class and functions of nested automation routes.
"""

import datetime

from bson import ObjectId
from fastapi.encoders import jsonable_encoder

from app.core.custom_error import DataNotFoundError
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.helpers.automation.automation_configuration import AutomationHelper


class nested_automation_helper:
    """
    A class that provides the functionality to manage nested automation routes.
    """

    async def check_days(self, automation, next_execution):
        """
        Check the days of automation

        Param:
            automation (dict): The list of automation data
            next_execution (datetime): Get the next trigger datetime

        Return:
            Datetime
        """
        current_date = datetime.datetime.utcnow().date()
        if str(next_execution.date()) < str(current_date):
            next_execution = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        while next_execution.strftime("%A").upper() not in automation.get("days", []):
            next_execution += datetime.timedelta(days=1)
        return utility_obj.get_local_time(next_execution)

    async def get_last_execution_time(self, data: list):
        """
        Get the last execution time

        Param:
            data (list): The list of automation data

        Return:
            None
        """
        for automation in data:
            next_execution = None
            if automation.get("last_execution"):
                if str(automation.get("last_execution").date()) <= str(automation.get(
                        "date", {}).get("end_date")):
                    next_execution = automation.get("last_execution") + datetime.timedelta(hours=1)
                    next_execution = next_execution.strftime("%Y-%m-%d %H:%M:%S")
                    next_execution = datetime.datetime.strptime(
                        next_execution, "%Y-%m-%d %H:%M:%S")
                else:
                    automation["next_execution"] = next_execution
            else:
                next_execution = automation.get("start_date_time")
            if next_execution:
                automation["next_execution"] = await self.check_days(
                    automation=automation,
                    next_execution=next_execution)

    async def validate_and_get_data(self, automation_id: str) -> dict:
        """
        Validate automation id and return automation data if automation data
        exists then raise exception.

        Params:
            - automation_id (str): An unique identifier of automation which
                useful for get automation data.

        Returns:
            - dict: A dictionary which contains automation data.

        Raises:
            - ObjectIdInValid: An error which occurred when automation id will
            be wrong.
            - DataNotFoundError: An error occurred when automation not found
                by id.
        """
        await utility_obj.is_length_valid(automation_id, "Automation id")
        if (
                automation_details := await DatabaseConfiguration().rule_collection.find_one(
                    {"_id": ObjectId(automation_id)}
                )
        ) is None:
            raise DataNotFoundError(automation_id, "Automation")
        return automation_details

    async def data_segment_assign(
            self, data_segment_ids: list | None, automation_id: str | None
    ) -> dict:
        """
        Assign the multiple data segment id to the automation.

        Params:
            - data_segment_ids (list): Get the multiple data segment ids.
            - automation_id (str): Get the automation id of the automation.

        Returns:
            - dict: A dictionary which contains message about successfully
                assign data segment (s) to automation.
        """
        automation_details = await self.validate_and_get_data(automation_id)
        for _id in data_segment_ids:
            await utility_obj.is_length_valid(_id, "Data Segment id")
            if (
                    segment_details := await DatabaseConfiguration().data_segment_collection.find_one(
                        {"_id": ObjectId(_id)}
                    )
            ) is None:
                raise DataNotFoundError(_id, "Data segment")
            linked_automations = segment_details.get("linked_automations", [])
            linked_automations.append(ObjectId(automation_id))
            linked_automations = list(set(linked_automations))
            await DatabaseConfiguration().data_segment_collection.update_one(
                {"_id": ObjectId(_id)},
                {"$set": {"linked_automations": linked_automations}},
            )
        data_segment_id = automation_details.get("data_segment_id", [])
        for _id in data_segment_ids:
            data_segment_id.append(ObjectId(_id))
        data_segment_id = list(set(data_segment_id))
        await DatabaseConfiguration().rule_collection.update_one(
            {"_id": ObjectId(automation_id)},
            {"$set": {"data_segment_id": data_segment_id}},
        )
        return {"message": "Data segment assign to the" " automation successfully"}

    async def top_bar_helper(self, pipeline: list, com_type: str,
                             data_type: str | None = None, template_wise: bool = False) -> list:
        """
        Get the top bar details of automation.
        Param:
            status_type (str): The status_type filter. This may have
                values saved, active, stopped
            data_type (str): The data_type filter.
                This may have values Lead, Raw Data, Application
            com_type (str): The communication type. This may have values

        Return:
            dict: A dictionary which contains information about
                top bar details of automation.
        """
        temp = [
            {
                "$lookup": {
                    "from": "communicationLog",
                    "let": {"automation_id": "$_id"},
                    "pipeline": [
                        {"$unwind": f"${com_type}_summary.transaction_id"},
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": ["$$automation_id",
                                            {"$ifNull": [
                                                f"${com_type}_summary.transaction_id.automation_id",
                                                ""]}]
                                }
                            }
                        }
                    ],
                    "as": "communication_log"
                }
            },
            {
                "$unwind": "$communication_log"
            }
        ]

        if data_type:
            temp.append({"$match": {
                f"communication_log.{com_type}_summary.transaction_id.module_name": data_type.title()}})
        temp_data = {
            "$group": {
                "_id": None,
                f"{com_type}_sent": {"$sum": 1},
                f"{com_type}_delivered": {
                    "$sum": {
                        "$cond": [
                            {"$ifNull": [
                                f"$communication_log.{com_type}_summary.transaction_id.{com_type}_delivered",
                                False]},
                            1,
                            0
                        ]
                    }
                }
            }
        }
        if template_wise:
            if com_type == "email":
                temp_data.get("$group", {}).update(
                    {
                        "_id": {"template_id": {
                            "$toString": f"$communication_log.{com_type}_summary.transaction_id.template_id"},
                            "template_name": f"$communication_log.{com_type}_summary.transaction_id.template_name"},
                        f"{com_type}_opened": {
                            "$sum": {
                                "$cond": [
                                    {"$ifNull": [
                                        f"$communication_log.{com_type}_summary.transaction_id.{com_type}_opened",
                                        False]},
                                    1,
                                    0
                                ]
                            }
                        },
                        f"{com_type}_clicked": {
                            "$sum": {
                                "$cond": [
                                    {"$ifNull": [
                                        f"$communication_log.{com_type}_summary.transaction_id.{com_type}_clicked",
                                        False]},
                                    1,
                                    0
                                ]
                            }
                        }
                    }
                )
            if com_type == "sms":
                temp_data.get("$group", {}).update(
                    {
                        "_id": {"template_id": {
                            "$toString": f"$communication_log.{com_type}_summary.transaction_id.template_id"},
                            "template_name": f"$communication_log.{com_type}_summary.transaction_id.template_name",
                            "sms_type": f"$communication_log.{com_type}_summary.transaction_id.sms_type",
                            "sms_sender": f"$communication_log.{com_type}_summary.transaction_id.sms_sender",
                            "sms_content": f"$communication_log.{com_type}_summary.transaction_id.sms_content",
                            "dlt_content_id": f"$communication_log.{com_type}_summary.transaction_id.dlt_content_id"
                        },
                        f"{com_type}_sent": {"$sum": 1}
                    }
                )
            if com_type == "whatsapp":
                temp_data.get("$group", {}).update(
                    {
                        "_id": {"template_id": {
                            "$toString": f"$communication_log.{com_type}_summary.transaction_id.template_id"},
                            "template_name": f"$communication_log.{com_type}_summary.transaction_id.template_name",
                            "whatsapp_content": f"$communication_log.{com_type}_summary.transaction_id.whatsapp_content"},
                        f"{com_type}_clicked": {
                            "$sum": {
                                "$cond": [
                                    {"$ifNull": [
                                        f"$communication_log.{com_type}_summary.transaction_id.{com_type}_clicked",
                                        False]},
                                    1,
                                    0
                                ]
                            }
                        }
                    }
                )
        temp.append(temp_data)
        pipeline.extend(temp)
        return await DatabaseConfiguration().rule_collection.aggregate(pipeline).to_list(None)

    async def get_top_bar_details(
            self, status_type: str | None, data_type: str | None
    ) -> dict:
        """
        Get automation top bar details.

        Params:
            - status_type (str): The status_type filter. This may have
                values saved, active, stopped
            - data_type (str): The data_type filter.
                This may have values Lead, Raw Data, Application

        Returns:
            - dict: A dictionary which contains information about
                top bar details of automation.
        """
        total_communication = 0
        temp_data = {
            "total_automation": 0,
            "total_communication": 0,
            "email_communication": 0,
            "active_automation": 0,
            "saved-automation": 0,
            "stopped_automation": 0,
            "sms_communication": 0,
            "whatsapp_communication": 0,
            "email_delivered": 0,
            "sms_delivered": 0,
            "whatsapp_delivered": 0,
            "email_delivery_rate": 0,
            "sms_delivery_rate": 0,
            "whatsapp_delivery_rate": 0,
        }
        for com_type in ["email", "sms", "whatsapp"]:
            pipeline = []
            if status_type:
                pipeline.append({"$match": {"status": status_type.lower()}})
            data = await self.top_bar_helper(pipeline=pipeline, data_type=data_type,
                                             com_type=com_type)
            if data:
                temp_dt = data[0]
                total_sent = temp_dt.get(f"{com_type}_sent", 0)
                delivery_count = temp_dt.get(f"{com_type}_delivered", 0)
                total_communication += total_sent
                temp_data[f"{com_type}_communication"] = total_sent
                temp_data[f"{com_type}_delivered"] = delivery_count
                temp_data[f"{com_type}_delivery_rate"] = utility_obj.get_percentage_result(
                    dividend=delivery_count, divisor=total_sent)
        temp_data["total_communication"] = total_communication
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_automation": {"$sum": 1},
                    "active_automation": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status", "active"]}, 1, 0]
                        }
                    },
                    "saved_automation": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status", "saved"]}, 1, 0]
                        }
                    },
                    "stopped_automation": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status", "stopped"]}, 1, 0]
                        }
                    }
                }
            }
        ]
        if status_type:
            pipeline.insert(0, {"$match": {"status": status_type.lower()}})
        results = await DatabaseConfiguration(
        ).rule_collection.aggregate(pipeline).to_list(None)
        if results:
            filter_data = results[0]
            filter_data.pop("_id")
            temp_data.update(filter_data)
        return temp_data

    async def get_automation_list(
            self,
            search: str | None,
            date_range,
            communication: list | None,
            template: bool | None,
            data_type: list | None,
            page_num,
            page_size,
    ) -> tuple:
        """
        Get the list of automation details.

        Params:
            - search (str | None): Either None or a string which useful
                for get automations based on search pattern.
            - date_range (DateRange | None): Either None or date range which
                useful get data based on date range.
            - communication (list | None): Either None or type of
                communication like email/sms/whatsapp which useful for get
                automation by communication.
            - template (bool | None): If you want to return only template data
                then true else false
            - data_type (list | None): Filter for data_type
                This can have values (lead,application, raw_data)
            - page_num (int | None): Either None or page number where
                want to show data.
            - page_size (int | None): Either None or get the number of the
                page size.

        Returns:
         - tuple: A tuple which contains automation details with pagination
            along with count.
        """
        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
        pipeline = [
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "rule_name": 1,
                    "action_type": 1,
                    "date": 1,
                    "start_date_time": 1,
                    "days": 1,
                    "last_execution": 1,
                    "status": 1,
                    "next_execute": 1
                }
            }
        ]
        match = {}
        if data_type:
            stage = [
                {
                    "$lookup": {
                        "from": "dataSegment",
                        "let": {"data_segment": {"$ifNull": ["$data_segment_id", []]}},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$and": [{"$in": ["$_id", "$$data_segment"]}]
                                    }
                                }
                            }
                        ],
                        "as": "data_segment",
                    }
                },
                {
                    "$unwind": {
                        "path": "$data_segment",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
                {"$match": {"data_segment.module_name": {"$in": data_type}}},
            ]
            pipeline.extend(stage)
        if template:
            match.update({"template": True})
        if search:
            match.update({"rule_name": {"$regex": f".*{search}.*", "$options": "i"}})
        if date_range:
            date_range = await utility_obj.format_date_range(date_range)
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
            match.update({"created_on": {"$gte": start_date, "$lte": end_date}})
        if communication:
            communication = [com.lower() for com in communication]
            for com in communication:
                if com not in ["email", "sms", "whatsapp"]:
                    raise ValueError("Invalid communication type")
            match.update({"action_type": {"$in": communication}})
            project = {}
            temp_sum = []
            if "email" in communication:
                project.update({"email_sent": 1})
                temp_sum.append("$email_sent")
            if "sms" in communication:
                project.update({"sms_sent": 1})
                temp_sum.append("$sms_sent")
            if "whatsapp" == communication:
                project.update({"whatsapp_sent": 1})
                temp_sum.append("$whatsapp_sent")
            project.update({"communication": {"$sum": temp_sum}})
            pipeline[0].get("$project", {}).update(project)
        else:
            pipeline[0].get("$project", {}).update(
                {"email_sent": 1,
                 "sms_sent": 1,
                 "whatsapp_sent": 1,
                 "communication": {
                     "$sum": ["$email_sent", "$whatsapp_sent", "$sms_sent"]
                 }}
            )
        if match:
            pipeline.insert(0, {"$match": match})
        pipeline.append(
            {
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            }
        )
        automations = (
            await DatabaseConfiguration()
            .rule_collection.aggregate(pipeline)
            .to_list(None)
        )
        if automations:
            if not automations[0].get("totalCount", []):
                automations[0]["totalCount"] = [{"count": 0}]
            return automations[0].get("paginated_results", []), automations[0].get(
                "totalCount", []
            )[0].get("count", 0)
        else:
            return [], 0

    async def delete_automation(self, automation_ids):
        """
        Delete the automations

        Params:
         - automation_ids (list): list of automation unique ids

        Returns: None
        """
        automation_ids = [ObjectId(_id) for _id in automation_ids]
        pipeline = [
            {
                "$match": {
                    "$and": [
                        {"_id": {"$in": automation_ids}},
                        {"status": {"$ne": "active"}},
                    ]
                }
            },
            {"$project": {"_id": 1, "data_segment_id": 1}},
        ]
        automations = (
            await DatabaseConfiguration()
            .rule_collection.aggregate(pipeline)
            .to_list(None)
        )
        for automation in automations:
            automation_id = automation.get("_id")
            data_segment_ids = automation.get("data_segment_id", [])
            for data_segment_id in data_segment_ids:
                if (
                        data_segment := await DatabaseConfiguration().data_segment_collection.find_one(
                            {"_id": data_segment_id}
                        )
                ) is None:
                    continue
                linked_automations = data_segment.get("linked_automations", [])
                status = data_segment.get("status")
                if automation_id in linked_automations:
                    linked_automations.remove(automation_id)
                if not linked_automations:
                    status = "paused"
                await DatabaseConfiguration().data_segment_collection.update_one(
                    {"_id": data_segment.get("_id")},
                    {
                        "$set": {
                            "linked_automations": linked_automations,
                            "status": status,
                        }
                    },
                )
            await DatabaseConfiguration().rule_collection.delete_one(
                {"_id": automation_id}
            )

    async def get_active_data_segments(
            self, data_type: list | None, search: str | None
    ) -> dict:
        """
        Function to get active data segments based on filters.

        Params:
            - data_type (list | None): This acts as filter.
                This may have values (Lead, Application, Raw Data)
            - search (str |None): The search string to be searched in
                data segment

        Returns:
            - data (list): The list of active data segments depending on the
                given filters
        """
        match = {"status": "active"}
        if data_type:
            match.update({"module_name": {"$in": data_type}})
        if search:
            match.update(
                {"data_segment_name": {"$regex": f".*{search}.*", "$options": "i"}}
            )
        pipeline = [
            {"$match": match},
            {
                "$lookup": {
                    "from": "data_segment_student_mapping",
                    "localField": "_id",
                    "foreignField": "data_segment_id",
                    "as": "students_count",
                }
            },
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "data_segment_name": 1,
                    "period_type": 1,
                    "lead_count": {
                        "$cond": [
                            {"$eq": ["$period_type", "dynamic"]},
                            {"$size": {"$ifNull": ["$students_count", []]}},
                            "$lead_count",
                        ]
                    },
                }
            },
        ]
        data_segments = (
            await DatabaseConfiguration()
            .data_segment_collection.aggregate(pipeline)
            .to_list(None)
        )
        return data_segments

    async def copy_automation(
            self, automation_id: str, name: str | None, data_segments: list, user
    ):
        """
        Make a copy of given automation.

        Params:
            - automation_id (str): A unique id of automation that has to be
                copied.
            - name (str|none): The name of automation. If none then consider
                automation_name_copy
            - data_segment (list): The list of unique data segment ids that
                should be linked to copied automation

        raises:
            -  HTTPException: An error occurred with status code 404 when
                    automation not found by automation_id.
            - ObjectIdInValid: An error occurred when automation_id is wrong.

        Returns: None
        """
        await utility_obj.is_length_valid(_id=automation_id, name="Automation id")
        if (
                automation_data := await DatabaseConfiguration().rule_collection.find_one(
                    {"_id": ObjectId(automation_id)}
                )
        ) is None:
            raise DataNotFoundError(message="Automation")
        if not name:
            name = f"{automation_data.get('rule_name', '')}_copy"
        name = name.title()
        if (
                await DatabaseConfiguration().rule_collection.find_one({"rule_name": name})
                is not None
        ):
            return {
                "detail": "Automation rule name already exists. "
                          "Please provide different automation rule name."
            }
        await DatabaseConfiguration().rule_collection.insert_one(
            {
                "rule_name": name,
                "rule_description": automation_data.get("rule_description", ""),
                "action": automation_data.get("action", []),
                "action_type": automation_data.get("action_type", []),
                "status": automation_data.get("status", None),
                "template": automation_data.get("template", False),
                "enabled": automation_data.get("enabled", False),
                "is_published": automation_data.get("is_published", False),
                "data_segment_id": [ObjectId(data_id) for data_id in data_segments],
                "updated_on": datetime.datetime.utcnow(),
                "updated_by": ObjectId(user.get("_id")),
                "updated_by_name": utility_obj.name_can(user),
                "created_by_id": ObjectId(user.get("_id")),
                "next_execute": automation_data.get("next_execute"),
                "created_by_name": utility_obj.name_can(user),
                "created_on": datetime.datetime.utcnow(),
            }
        )

    async def get_automation_top_bar_details(
            self, automation_id: str, date_range: dict | None = None
    ) -> dict:
        """
        Get automation top bar details

        Params:
            - automation_id (str): An unique identifier of automation which
                useful for get automation.
            - date_range (DateRange | None): Either None or get the date range
                for get data based on date_range.

        Returns:
            - dict: A dictionary which contains automation top bar details.
        """
        await utility_obj.is_length_valid(automation_id, "Automation id")
        automation_data = await self.validate_and_get_data(automation_id)
        created_on = automation_data.get("created_on")
        start_date = end_date = None
        if date_range:
            date_range = jsonable_encoder(date_range)
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
        communication = {}
        for com_type in ["email", "sms", "whatsapp"]:
            pipeline = [
                {
                    "$match": {
                        "_id": ObjectId(automation_id)
                    }
                }
            ]
            if date_range:
                pipeline.append({"$match": {"created_on": {"$gte": start_date, "$lte": end_date}}})
            data = await self.top_bar_helper(pipeline=pipeline, com_type=com_type)
            if data:
                temp_dt = data[0]
                total_sent = temp_dt.get(f"{com_type}_sent", 0)
                delivery_count = temp_dt.get(f"{com_type}_delivered", 0)
                communication[f"{com_type}_communication"] = {
                    "sent": total_sent,
                    "delivered": delivery_count
                }

        temp_data = {
            "automation_name": automation_data.get("rule_name"),
            "data_type": automation_data.get("data_type"),
            "status": automation_data.get("status"),
            "count_at_origin": automation_data.get("data_count", 0),
            "date": utility_obj.get_local_time(created_on, only_date=True),
            "time": utility_obj.get_local_time(created_on, hour_minute=True),
            "current_data_count": automation_data.get("current_data_count", 0),
            "email_communication": {"sent": 0, "delivered": 0},
            "sms_communication": {"sent": 0, "delivered": 0},
            "whatsapp_communication": {"sent": 0, "delivered": 0},
        }
        temp_data.update(communication)
        return temp_data

    async def get_automation_communication_data(
            self, automation_id: str, email: bool, sms: bool, whatsapp: bool
    ) -> list:
        """
        Get automation (s) communication data.

        Params:
            - automation_id (str): An unique identifier of automation which
                useful for get automation.
            - email (bool): Default value: False. A boolean value True which useful
                for get email communication data.
            - sms (bool): Default value: False. A boolean value True which useful
                for get sms communication data.
            - whatsapp (bool): Default value: False. A boolean value True which
                useful for get whatsapp communication data.

        Returns:
            - dict: A dictionary which contains automation communication data.
        """
        await self.validate_and_get_data(automation_id)
        pipeline = [
            {
                "$match": {
                    "_id": ObjectId(automation_id)
                }
            }
        ]
        final_data = []
        if email:
            data = await self.top_bar_helper(pipeline=pipeline, com_type="email",
                                             template_wise=True)
            if data:
                for dt in data:
                    total_sent = dt.get("email_sent", 0)
                    total_delivered = dt.get("email_delivered", 0)
                    total_opened = dt.get("email_opened", 0)
                    total_clicked = dt.get("email_clicked", 0)
                    delivery_rate = utility_obj.get_percentage_result(
                        dividend=total_delivered, divisor=total_sent)
                    opened_rate = utility_obj.get_percentage_result(
                        dividend=total_opened, divisor=total_sent)
                    clicked_rate = utility_obj.get_percentage_result(
                        dividend=total_clicked, divisor=total_sent)
                    wrapper = dt.get("_id", {})
                    if not wrapper:
                        wrapper = {}

                    final_data.append(
                        {
                            "id": wrapper.get("template_id"),
                            "template_name": wrapper.get("template_name"),
                            "sent": dt.get("email_sent", 0),
                            "delivered": {"count": total_delivered,
                                          "rate": f"{delivery_rate}%"},
                            "opened": {"count": total_opened, "rate": f"{opened_rate}%"},
                            "clicked": {"count": total_clicked, "rate": f"{clicked_rate}%"},
                            "complaint_rate": "0%",
                            "bounce_rate": "0%",
                            "unsubscribe_rate": "0%",
                        }
                    )
        elif sms:
            data = await self.top_bar_helper(pipeline=pipeline, com_type="sms", template_wise=True)
            if data:
                for dt in data:
                    wrapper = dt.get("_id", {})
                    if not wrapper:
                        continue
                    final_data.append(
                        {
                            "id": wrapper.get("template_id"),
                            "template_name": wrapper.get("template_name"),
                            "sent": dt.get("sms_sent", 0),
                            "delivered": dt.get("sms_delivered", 0),
                            "dlt_id": wrapper.get("dlt_content_id"),
                            "sender_id": wrapper.get("sms_sender"),
                            "sms_type": wrapper.get("sms_type"),
                            "content": wrapper.get("sms_content"),
                        }
                    )
        elif whatsapp:
            data = await self.top_bar_helper(pipeline=pipeline, com_type="whatsapp",
                                             template_wise=True)
            if data:
                for dt in data:
                    wrapper = dt.get("_id", {})
                    if not wrapper:
                        continue
                    total_sent = dt.get("whatsapp_sent", 0)
                    total_clicked = dt.get("whatsapp_clicked", 0)
                    clicked_rate = utility_obj.get_percentage_result(
                        dividend=total_clicked, divisor=total_sent)
                    final_data.append(
                        {
                            "id": wrapper.get("template_id"),
                            "template_name": wrapper.get("template_name"),
                            "sent": total_sent,
                            "delivered": dt.get("whatsapp_delivered", 0),
                            "content": wrapper.get("whatsapp_content"),
                            "tag": wrapper.get("whatsapp_tag", "--"),
                            "click_rate": f"{clicked_rate}%",
                        }
                    )
        return final_data

    async def get_automation_data_by_id(
            self, automation_id: str, college_id: str
    ) -> dict:
        """
        Get automation (s) communication data.

        Params:
            - automation_id (str): An unique identifier of automation which
                useful for get automation.
            - college_id (str): An unique identifier of a college.

        Returns:
            - dict: A dictionary which contains automation communication data.
        """
        automation_data = await self.validate_and_get_data(automation_id)
        release_window = automation_data.get("release_window", {})
        data_segment = {}
        data_segments = [
            {
                "data_segment_name": data_segment.get("data_segment_name"),
                "module_name": data_segment.get("module_name"),
                "segment_type": data_segment.get("segment_type"),
                "count_of_entities": (
                    (
                        await AutomationHelper().get_data_from_db(
                            data_segment,
                            college_id,
                            data_segments=False,
                            skip=0,
                            limit=10,
                            call_segments=True,
                        )
                    )[0]
                    if data_segment.get("segment_type") != "Static"
                    else data_segment.get("count_at_origin", 0)
                ),
                "data_segment_id": str(segment_id),
                "filters": data_segment.get("filters"),
                "advance_filters": data_segment.get("advance_filters"),
                "raw_data_name": data_segment.get("raw_data_name"),
                "period": data_segment.get("period"),
                "count_at_origin": data_segment.get("count_at_origin", 0),
                "data_count": data_segment.get("data_count", 0),
            }
            for segment_id in automation_data.get("data_segment_id", [])
            if await utility_obj.is_length_valid(str(segment_id), "Data segment id")
               and (
                   data_segment := await DatabaseConfiguration().data_segment_collection.find_one(
                       {"_id": segment_id}
                   )
               )
               is not None
        ]

        return {
            "automation_details": {
                "automation_name": automation_data.get("rule_name"),
                "data_type": automation_data.get("data_type"),
                "releaseWindow": {
                    "start_time": utility_obj.get_local_time(
                        release_window.get("start_date"), release_window=True
                    ),
                    "end_time": utility_obj.get_local_time(
                        release_window.get("end_date"), release_window=True
                    ),
                },
                "date": automation_data.get("date"),
                "days": automation_data.get("days"),
                "data_segment": data_segments,
                "data_count": automation_data.get("data_count"),
                "filters": automation_data.get("filters"),
            },
            "automation_node_edge_details": automation_data.get("front_end_data"),
            "automation_status": automation_data.get("status"),
            "template": automation_data.get("template"),
        }
