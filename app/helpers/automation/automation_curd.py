"""
this file contains the functions of nested automation routes
"""
import datetime

from bson import ObjectId
from dateutil.parser import parse
from fastapi.exceptions import HTTPException

from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration


class Automation_operator:
    """
    A class representing the function of a nested automation operator
    """

    async def get_node(self, actions, _id, node_id):
        """
        check the _id from a list of all available node list.
        param:
            actions (list): Get the all available list of nodes from
             the frontend
            _id (str): Get the value in _id for compare
            node_id (str): Get the field name in node_id for compare with
              the _id
        return:
            One node details which is in dictionary or empty dictionary
        """
        return next((data for data in actions
                     if data.get(node_id) == _id), {})

    async def delayNode_wrapper(self, temp_action: list | None,
                                target_node: dict | None,
                                source_node: dict | None):
        """
        Insert target node into the temp_action list for future calls

        param:
            tamp_action (list): Get the temp_action for insert target node
            target_node (dict): Get the target node for the generated node

        return:
            None
        """
        for data in temp_action:
            if data.get("id") == source_node.get("id"):
                data["target_id"] = target_node.get("id")

    async def releaseNode_wrapper(self, temp_dict: dict | None):
        """
        Convert into utc datetime format

        param:
            temp_dict (dict): Get the start_date and end_date from
             the temp_dict

        return:
            Converted start_date and end_date in dictionary or None
        """
        if temp_dict is None:
            return None
        return {
            "start_date": await utility_obj.convert_date_to_utc(
                temp_dict.get("start_time", "")),
            "end_date": await utility_obj.convert_date_to_utc(
                temp_dict.get("end_time", ""))
        }

    async def insert_data_segment(self, temp_action: list | None,
                                  source_id: str | None,
                                  target_id: str | None):
        """
        Insert the source id into target_id

        param:
            temp_action (list): Get the temp_action list which updated list
            _id (str): Get the source id for the list
            source_id (str): Get the source id from the source node
            target_id (str): Get the target id from the target node

        return:
            None
        """
        for data in temp_action:
            if data.get("target_id") == source_id:
                condition = data.get("conditions", [])
                condition.append({"next_id": target_id})
                data["conditions"] = condition

    async def communicationNode_wrapper(self, source: dict | None,
                                        target: dict | None,
                                        temp_action: list | None):
        """
        Get the communication node return with some fields

        param:
            source (dict): Get the source node details
            target (dict): Get the target node details
            temp_action (dict): Get the all node details in list

        return:
            A new dictionary which has new communication details node
        """

        delay_data = source.get("delay_data", {})
        communication_data = target.get("communication_data", {})
        temp_dict = {
            "id": target.get("id"),
            "node_name": "communication_node",
            "node_type": delay_data.get("delay_type"),
            "type": communication_data.get("communication_type", "").lower(),
            "content": communication_data.get("template_content"),
            "email_type": communication_data.get("email_type"),
            "sms_type": communication_data.get("sms_type"),
            "template_id": communication_data.get("template_id"),
            "email_provider": communication_data.get("email_provider"),
            "execution_time": communication_data.get("execution_time"),
            "script": {
                "trigger_by": delay_data.get("trigger_by"),
                "interval_value": delay_data.get("interval_value"),
                "release_interview": await self.releaseNode_wrapper(
                    delay_data.get("releaseWindow")),
                "date": delay_data.get("date"),
                "days": delay_data.get("days")
            }
        }
        await self.insert_data_segment(temp_action, source.get("id"),
                                       target.get("id"))
        return temp_dict

    async def exitNode_wrapper(self, source: dict | None,
                               target: dict | None,
                               temp_action: list | None):
        """
        Get the exit node return a dictionary

        param:
            source (dict): Get the source node details
            target (dict): Get the target node details
            temp_action (dict): Get the all node details in list

        return:
            A new dictionary which has new if elseNode details node
        """
        delay_data = source.get("delay_data", {})
        filter_data = []
        for data in target.get("exit_condition_data", []):
            for condition in data.get("filterOptions", []):
                filter_data.append({
                    "field_name": condition.get("fieldName"),
                    "operator": condition.get("operator"),
                    "value": condition.get("value"),
                    "collection_field_name": condition.get(
                        "collection_field_name"),
                    "collection_name": condition.get("collection_name")
                })
        temp_dict = {
            "id": target.get("id"),
            "node_type": delay_data.get("delay_type"),
            "node_name": "exit_node",
            "script": {
                "advance_filters": target.get("exit_condition_data", []),
                "condition_exec": filter_data,
                "trigger_by": delay_data.get("trigger_by"),
                "interval_value": delay_data.get("interval_value"),
                "release_interview": await self.releaseNode_wrapper(
                    delay_data.get("releaseWindow")),
                "date": delay_data.get("date"),
                "days": delay_data.get("days")
            }
        }
        await self.insert_data_segment(temp_action, source.get("id"),
                                       target.get("id"))
        return temp_dict

    async def tagNode_wrapper(self, source: dict | None,
                              target: dict | None,
                              temp_action: list | None):
        """
        Get the tag node return with some fields

        param:
            source (dict): Get the source node details
            target (dict): Get the target node details
            temp_action (dict): Get the all node details in list

        return:
            A new dictionary which has new if tagNode details node
        """
        delay_data = source.get("delay_data", {})
        tag_data = target.get("tag_data", "")
        tag_condition_data = target.get("tag_condition_data", {})
        temp_dict = {
            "id": target.get("id"),
            "node_type": delay_data.get("delay_type"),
            "node_name": "tag_node",
            "tag_data": tag_data,
            "script": {
                "condition_exec": [{"field_name": data.get("fieldName"),
                                    "operator": data.get("operator"),
                                    "value": data.get("value")} for data
                                   in tag_condition_data.get("filterOptions",
                                                             [])],
                "advance_filters": tag_condition_data,
                "trigger_by": delay_data.get("trigger_by"),
                "interval_value": delay_data.get("interval_value"),
                "release_interview": await self.releaseNode_wrapper(
                    delay_data.get("releaseWindow")),
                "date": delay_data.get("date"),
                "days": delay_data.get("days")
            }
        }
        await self.insert_data_segment(temp_action, source.get("id"),
                                       target.get("id"))
        return temp_dict

    async def leadStageNode_wrapper(self, source: dict | None,
                                    target: dict | None,
                                    temp_action: list | None):
        """
        Get the lead_stage node return with some fields

        param:
            source (dict): Get the source node details
            target (dict): Get the target node details
            temp_action (dict): Get the all node details in list

        return:
            A new dictionary which has new lead_stage_data details node
        """
        delay_data = source.get("delay_data", {})
        lead_stage_condition = target.get("lead_stage_condition", {})
        temp_dict = {
            "id": target.get("id"),
            "node_name": "lead_stage",
            "node_type": delay_data.get("delay_type"),
            "lead_stage_details": target.get("lead_stage_data"),
            "script": {
                "condition_exec": [{"field_name": data.get("fieldName"),
                                    "operator": data.get("operator"),
                                    "value": data.get("value")} for data
                                   in lead_stage_condition.get("filterOptions",
                                                               [])],
                "advance_filters": lead_stage_condition,
                "trigger_by": delay_data.get("trigger_by"),
                "interval_value": delay_data.get("interval_value"),
                "release_interview": await self.releaseNode_wrapper(
                    delay_data.get("releaseWindow")),
                "date": delay_data.get("date"),
                "days": delay_data.get("days")
            }
        }
        await self.insert_data_segment(temp_action, source.get("id"),
                                       target.get("id"))
        return temp_dict

    async def allocationNode_wrapper(self, source: dict | None,
                                     target: dict | None,
                                     temp_action: list | None):
        """
        Get the allocation node return with some fields

        param:
            source (dict): Get the source node details
            target (dict): Get the target node details
            temp_action (dict): Get the all node details in list

        return:
            A new dictionary which has new allocation_data details node
        """
        delay_data = source.get("delay_data", {})
        allocation_condition = target.get("allocation_condition", {})
        temp_dict = {
            "id": target.get("id"),
            "node_name": "allocation_counselor",
            "node_type": delay_data.get("delay_type"),
            "allocation_counsellor_data": [
                ObjectId(counselor_id)
                for counselor_id in
                target.get("allocation_counsellor_data", [])],
            "script": {
                "condition_exec": [{"field_name": data.get("fieldName"),
                                    "operator": data.get("operator"),
                                    "value": data.get("value")} for data
                                   in allocation_condition.get("filterOptions",
                                                               [])],
                "advance_filters": allocation_condition,
                "trigger_by": delay_data.get("trigger_by"),
                "interval_value": delay_data.get("interval_value"),
                "release_interview": await self.releaseNode_wrapper(
                    delay_data.get("releaseWindow")),
                "date": delay_data.get("date"),
                "days": delay_data.get("days")
            }
        }
        await self.insert_data_segment(temp_action, source.get("id"),
                                       target.get("id"))
        return temp_dict

    async def ifElseNode_wrapper(self, source: dict | None,
                                 target: dict | None,
                                 temp_action: list | None):
        """
        Get the ifElseNode node return with some fields

        param:
            source (dict): Get the source node details
            target (dict): Get the target node details
            temp_action (dict): Get the all node details in list

        return:
            A new dictionary which has new if elseNode details node
        """
        delay_data = source.get("delay_data", {})
        temp_dict = {
            "id": target.get("id"),
            "target_id": target.get("id"),
            "node_name": "if_else",
            "node_type": delay_data.get("delay_type"),
            "script": {
                "trigger_by": delay_data.get("trigger_by"),
                "interval_value": delay_data.get("interval_value"),
                "release_interview": await self.releaseNode_wrapper(
                    delay_data.get("releaseWindow")),
                "date": delay_data.get("date"),
                "days": delay_data.get("days")
            }
        }
        await self.insert_data_segment(temp_action, source.get("id"),
                                       target.get("id"))
        return temp_dict

    async def ifElseNode_communicationNode_wrapper(self, source: dict | None,
                                                   target: dict | None,
                                                   temp_action: list | None):
        """
        Get the communication node return with some fields

        param:
            source (dict): Get the source node details
            target (dict): Get the target node details
            actions (dict): Get the all node details in list

        return:
            A new dictionary which has new communication details node
        """
        communication_data = target.get("communication_data", {})
        communication_condition = target.get("if_else_condition", {})
        temp_dict = {
            "id": target.get("id"),
            "target_id": target.get("id"),
            "node_name": "communication_node",
            "type": communication_data.get("communication_type", "").lower(),
            "content": communication_data.get("template_content"),
            "email_type": communication_data.get("email_type"),
            "sms_type": communication_data.get("sms_type"),
            "template_id": communication_data.get("template_id"),
            "email_provider": communication_data.get("email_provider"),
            "dlt_template_id": communication_data.get("dlt_template_id"),
            "sender_id": communication_data.get("sender_id"),
            "execution_time": communication_data.get("execution_time"),
            "script": {
                "condition_exec": [{"field_name": data.get("fieldName"),
                                    "operator": data.get("operator"),
                                    "value": data.get("value")} for data
                                   in
                                   communication_condition.get("filterOptions",
                                                               [])],
                "advance_filters": communication_condition
            }
        }
        await self.insert_data_segment(temp_action, source.get("id"),
                                       target.get("id"))
        return temp_dict

    async def ifElseNode_tagNode_wrapper(self, source: dict | None,
                                         target: dict | None,
                                         temp_action: list | None):
        """
        Get the tagNode node return with some fields

        param:
            source (dict): Get the source node details
            target (dict): Get the target node details
            temp_action (dict): Get the all node details in list

        return:
            A new dictionary which has new if ifElseNode tagNode details node
        """
        tag_condition_data = target.get("if_else_condition", {})
        tag_data = target.get("tag_data", "")
        temp_dict = {
            "id": target.get("id"),
            "target_id": target.get("id"),
            "node_name": "tag_node",
            "tag_data": tag_data,
            "script": {
                "condition_exec": [{"field_name": data.get("fieldName"),
                                    "operator": data.get("operator"),
                                    "value": data.get("value")} for data
                                   in tag_condition_data.get("filterOptions",
                                                             [])],
                "advance_filters": tag_condition_data
            }
        }
        await self.insert_data_segment(temp_action, source.get("id"),
                                       target.get("id"))
        return temp_dict

    async def ifElseNode_leadStageNode_wrapper(self, source: dict | None,
                                               target: dict | None,
                                               temp_action: list | None):
        """
        Get the lead stage node return with some fields

        param:
            source (dict): Get the source node details
            target (dict): Get the target node details
            temp_action (dict): Get the all node details in list

        return:
            A new dictionary which has new lead_stage_data details node
        """
        lead_stage_condition = target.get("if_else_condition", {})
        temp_dict = {
            "id": target.get("id"),
            "target_id": target.get("id"),
            "node_name": "lead_stage",
            "lead_stage_details": target.get("lead_stage_data"),
            "script": {
                "condition_exec": [{"field_name": data.get("fieldName"),
                                    "operator": data.get("operator"),
                                    "value": data.get("value")} for data
                                   in lead_stage_condition.get("filterOptions",
                                                               [])],
                "advance_filters": lead_stage_condition
            }
        }
        await self.insert_data_segment(temp_action, source.get("id"),
                                       target.get("id"))
        return temp_dict

    async def ifElseNode_exitNode_wrapper(self, source: dict | None,
                                          target: dict | None,
                                          temp_action: list | None):
        """
        Get the exit node return with some fields

        param:
            source (dict): Get the source node details
            target (dict): Get the target node details
            temp_action (dict): Get the all node details in list

        return:
            A new dictionary which has new if exit node details node
        """
        exit_condition_data = target.get("if_else_condition", {})
        temp_dict = {
            "id": target.get("id"),
            "target_id": target.get("id"),
            "node_name": "exit_node",
            "script": {
                "condition_exec": [{"field_name": data.get("fieldName"),
                                    "operator": data.get("operator"),
                                    "value": data.get("value")} for data
                                   in exit_condition_data.get("filterOptions",
                                                              [])],
                "advance_filters": target.get("exit_condition_data", {})
            }
        }
        await self.insert_data_segment(temp_action, source.get("id"),
                                       target.get("id"))
        return temp_dict

    async def ifElseNode_allocationNode_wrapper(self, source: dict | None,
                                                target: dict | None,
                                                temp_action: list | None):
        """
        Get the allocation node return with some fields

        param:
            source (dict): Get the source node details
            target (dict): Get the target node details
            temp_action (dict): Get the all node details in list

        return:
            A new dictionary which has new if allocation details node
        """
        allocation_condition_data = target.get("if_else_condition", {})
        temp_dict = {
            "id": target.get("id"),
            "target_id": target.get("id"),
            "node_name": "allocation_counselor",
            "allocation_counsellor_data": [
                ObjectId(counselor_id)
                for counselor_id in
                target.get("allocation_counsellor_data", [])],
            "script": {
                "condition_exec": [{"field_name": data.get("fieldName"),
                                    "operator": data.get("operator"),
                                    "value": data.get("value")} for data
                                   in allocation_condition_data.get(
                        "filterOptions",
                        [])],
                "advance_filters": allocation_condition_data
            }
        }
        await self.insert_data_segment(temp_action, source.get("id"),
                                       target.get("id"))
        return temp_dict

    async def extract_automation_action(self, payload):
        """
        Extracts the function of a nested automation action node
         from the payload

        param:
            payload (dict): Get the action payload

        return:
            A list of dictionary containing the action payload
        """
        temp_action = []
        payload_actions = payload.get("automation_node_edge_details", {})
        edges = payload_actions.get("edges", [])
        actions = payload_actions.get("nodes", [])
        for edge in edges:
            new_node = {}
            source = edge.get("source")
            target = edge.get("target")
            source_node = await self.get_node(actions, source, "id")
            target_node = await self.get_node(actions, target, "id")
            if source_node.get("type") == "dataSegmentNode":
                continue
            elif target_node.get("type") == "delayNode":
                await self.delayNode_wrapper(
                    temp_action=temp_action, target_node=target_node,
                    source_node=source_node)
                continue
            elif source_node.get("type") == "delayNode":
                new_node = await (
                    getattr(self, f"{target_node.get('type')}"
                                  f"_wrapper")(source=source_node,
                                               target=target_node,
                                               temp_action=temp_action))
            elif source_node.get("type") == "ifElseNode":
                new_node = await (
                    getattr(self, f"ifElseNode_{target_node.get('type')}"
                                  f"_wrapper")(source=source_node,
                                               target=target_node,
                                               temp_action=temp_action))
            if len(new_node) > 0:
                temp_action.append(new_node)
        return temp_action

    async def action_type_wrapper(self, temp_action):
        """
        Get the email, sms and whatsapp action type

        param:
            temp_action (list): Get the email, sms and whatsapp
             from the temp action
        return:
            list of actions
        """
        data = [temp.get("type").lower() for temp in temp_action
                if
                temp.get("type", "").lower() in ["sms", "email", "whatsapp"]]
        return list(set(data))

    async def get_start_time_datetime(self, release_window, date):
        """
        Get the start time and date from the release window and date

        param:
            release_window (dict): Get the release window
            date (str): Get the date from the date

        return:
            start datetime value
        """
        temp_date = parse(release_window)
        temp = f"{str(date)} {str(temp_date.time())}"
        return await utility_obj.convert_date_to_utc(temp)

    async def create_automation(self, user: dict | None,
                                payload: dict | None):
        """
        Create a new automation instance based on the given user and payload

        param:
            user (dict): The user details in user dictionary
            payload (dict): The payload to be created as the automation

        return:
            Create a new automation instance
        """
        temp_payload = payload.get("automation_details", {})
        data = {
            "rule_name": temp_payload.get("automation_name").title(),
            "data_type": temp_payload.get("data_type"),
            "release_window": {
                "start_date": await utility_obj.convert_date_to_utc(
                    temp_payload.get("releaseWindow", {}).get("start_time",
                                                              "")),
                "end_date": await utility_obj.convert_date_to_utc(
                    temp_payload.get("releaseWindow", {}).get("end_time", "")
                )},
            "start_date_time": await self.get_start_time_datetime(
                date=temp_payload.get("date", {}).get("start_date"),
                release_window=temp_payload.get("releaseWindow",
                                                {}).get("start_time", "")
            ),
            "date": temp_payload.get("date"),
            "days": temp_payload.get("days"),
            "data_segment_id": [ObjectId(counselor.get("data_segment_id"))
                                for counselor in temp_payload.get(
                    "data_segment", []) if counselor.get("data_segment_id")],
            "data_count": temp_payload.get("data_count"),
            "actions": await self.extract_automation_action(payload),
            "status": payload.get("automation_status"),
            "template": payload.get("template", False),
            "filters": temp_payload.get("filters", {}),
            "updated_by_name": utility_obj.name_can(user),
            "created_by_id": ObjectId(user.get("_id")),
            "created_on": datetime.datetime.utcnow(),
            "front_end_data": payload.get("automation_node_edge_details", {})
        }
        data["action_type"] = await self.action_type_wrapper(
            data.get("actions", []))
        if (
                automation_details := await DatabaseConfiguration().rule_collection.find_one(
                    {"rule_name": data.get("rule_name")})) is not None:
            if automation_details.get("status") == "active":
                raise HTTPException(status_code=422,
                                    detail="Unable to update the"
                                           " running automation")
            else:
                await DatabaseConfiguration().rule_collection.update_one(
                    {"rule_name": data.get("rule_name")}, {"$set": data})
        else:
            await DatabaseConfiguration().rule_collection.insert_one(data)
        return {"message": "Automation create successfully"}
