"""
This file contains class and functions related to student communication
timeline.
"""
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from fastapi.encoders import jsonable_encoder

from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.helpers.student_curd.student_user_crud_configuration import \
    StudentUserCrudHelper
from app.models.email_schema import EmailWebhook

logger = get_logger(name=__name__)


class CommunicationLog:
    """
    Contain functions related to communication log activities
    """

    async def get_communication_timeline(
            self, student_id, event_type: str | None,
            start_date: datetime | None = None,
            end_date: datetime | None = None):
        """
        This function returns the list of communication timeline
        """
        pipeline = [
            {"$match": {"student_id": student_id}},
            {"$unwind": {"path": "$timeline"}}
        ]
        match_stages = []
        if event_type:
            match_stages.append({"timeline.event_type": event_type})
        if start_date and end_date:
            match_stages.append({"timeline.timestamp":
                                     {"$gte": start_date, "$lte": end_date}})
        if match_stages:
            pipeline.append({"$match": {"$and": match_stages}})
        pipeline.append({"$sort": {"timeline.timestamp": -1}})
        result = DatabaseConfiguration().communication_log_collection. \
            aggregate(pipeline)
        event_timeline, gap_bet_timeline, prev_date = [], 0, None
        async for item in result:
            timeline = item.get('timeline', {})
            temp_date = timeline.get('timestamp')
            if prev_date is not None:
                days_gap = abs(temp_date - prev_date)
                gap_bet_timeline = days_gap.days
                event_timeline[-1].update({
                    "gap_bet_timeline": gap_bet_timeline})
            prev_date = timeline.get('timestamp')
            event_name = timeline.get('event_name')
            event_type = timeline.get('event_type')
            event_status = timeline.get('event_status')
            action_type = timeline.get('action_type')
            event_timeline.append({
                "action_type": action_type if action_type else "system",
                "message": f"{event_name} {event_type} {event_status}.",
                "timestamp": utility_obj.get_local_time(temp_date),
                'event_status': event_status,
                "event_type": event_type,
                "event_name": event_name
            })
        return event_timeline

    async def update_transaction_details_by_message_id_in_the_communication_log_collection(
            self, message_id, data,
            name, automation=False):
        """
        Update email status by message_id
        """
        try:
            if automation:
                result = (DatabaseConfiguration()
                .automation_communicationLog_details.aggregate(
                    [
                        {'$match': {
                            f"email_summary.transaction_id.{name}": message_id}},
                        {'$group': {
                            '_id': "$_id"
                        }}
                    ]
                ))
            else:
                result = (DatabaseConfiguration()
                .communication_log_collection.aggregate(
                    [
                        {'$match': {
                            f"email_summary.transaction_id.{name}": message_id}},
                        {'$group': {
                            '_id': "$_id"
                        }}
                    ]
                ))
            async for item in result:
                if automation:
                    communication_data = await (DatabaseConfiguration()
                    .automation_communicationLog_details.find_one(
                        {'_id': item.get('_id')}))
                else:
                    communication_data = await (DatabaseConfiguration()
                    .communication_log_collection.find_one(
                        {'_id': item.get('_id')}))
                if communication_data:
                    for _id, element in enumerate(
                            communication_data.get("email_summary", {}).get(
                                "transaction_id")):
                        if element.get(name) == message_id:
                            if len(data) == 0:
                                logger.info(
                                    f"Nothing to update for message id:"
                                    f" {message_id} in the collection named "
                                    f"communicationLog")
                                break
                            element.update(data)
                            if data.get("email_open"):
                                communication_data[
                                    "last_5_email_opened"] = element.get(
                                    "last_opened", False)
                                if communication_data.get("email_summary", {}).get(
                                        "open_rate") is None:
                                    communication_data["email_summary"]["open_rate"] = 0
                                communication_data["email_summary"][
                                    "open_rate"] = \
                                    communication_data["email_summary"][
                                        "open_rate"] + 1
                                element.pop("last_opened")
                            elif data.get("email_click"):
                                if communication_data.get("email_summary", {}).get(
                                        "click_rate") is None:
                                    communication_data["email_summary"]["click_rate"] = 0
                                communication_data["email_summary"][
                                    "click_rate"] = \
                                    communication_data["email_summary"][
                                        "click_rate"] + 1
                                student = await (DatabaseConfiguration()
                                .studentsPrimaryDetails.find_one(
                                    {'_id': communication_data.get(
                                        'student_id')}))
                                if student:
                                    await StudentUserCrudHelper(). \
                                        update_verification_status(student)
                            elif data.get("email_delivered"):
                                if communication_data.get("email_summary", {}).get(
                                        "email_delivered") is None:
                                    communication_data["email_summary"]["email_delivered"] = 0
                                communication_data["email_summary"][
                                    "email_delivered"] = \
                                    communication_data["email_summary"][
                                        "email_delivered"] + 1
                                await utility_obj.update_transaction_details_by_message_id(
                                    message_id=message_id, communication_data=communication_data,
                                    name=name, com_type="email")
                            elif data.get("email_bounce"):
                                communication_data[
                                    "email_bounce"] = element.get(
                                    "email_bounce", False)
                            communication_data["email_summary"][
                                "transaction_id"][_id] = element
                            if automation:
                                await (DatabaseConfiguration()
                                .automation_communicationLog_details.update_one(
                                    {"_id": item.get('_id')},
                                    {
                                        '$set': communication_data}))
                            else:
                                await (DatabaseConfiguration()
                                .communication_log_collection.update_one(
                                    {"_id": item.get('_id')},
                                    {
                                        '$set': communication_data}))
        except Exception as e:
            logger.error(f"Something went wrong: {e}")

    async def update_transaction_details_by_message_id_in_the_activity_email_collection(
            self, message_id: str, data: dict, name: str, event_type: str) -> None:
        """
        Update email status by message_id in the activity email collection.

        Params:
            - message_id (str): Unique identifier of email transaction.
            - data (dict): A dictionary which contains information of email event.
            - name (str): Name of the field in the activity email collection which holds the message_id.
            - event_type (str): Type of email event.

        Returns: None

        Raises:
             - Exception: If any error occurs during the operation of the update the email status.
        """
        try:
            result = DatabaseConfiguration().activity_email.aggregate(
                [
                    {'$match': {"transaction_details": {"$exists": True},
                                f"transaction_details.{name}": message_id}
                     },
                    {'$group': {
                        '_id': "$_id"
                    }}
                ]
            )
            async for item in result:
                activity_email_data = await DatabaseConfiguration().activity_email.find_one(
                    {'_id': item.get('_id')})
                if activity_email_data:
                    for _id, element in enumerate(
                            activity_email_data.get("transaction_details")):
                        if element.get(name) == message_id:
                            if len(data) == 0:
                                logger.info(
                                    f"Nothing to update for message id: {message_id} in the collection named "
                                    f"activity_email")
                                break
                            email_list = activity_email_data.get("email_list", [])
                            if (activity_email_data.get(
                                    "is_scholarship_letter_sent") and isinstance(email_list, list)
                                    and len(email_list) == 1):
                                application_id = email_list[0].get("application_id")
                                if (
                                        application_information := await DatabaseConfiguration().studentApplicationForms.find_one(
                                        {'_id': application_id})) is not None:
                                    all_scholarship_info = application_information.get(
                                        "offered_scholarship_info",
                                        {}).get("all_scholarship_info",
                                                [])
                                    for iteration_id, scholarship_info in enumerate(
                                            all_scholarship_info):
                                        if scholarship_info.get("message_id") == message_id:
                                            event_name = "delivered" if event_type in ["delivered",
                                                                                       "delivery"] \
                                                else f"{event_type}ed"
                                            scholarship_info.update(
                                                {
                                                    f"scholarship_letter_{event_name}_on": datetime.now(
                                                        timezone.utc),
                                                    "scholarship_letter_current_status": event_name.title()})
                                            await DatabaseConfiguration().studentApplicationForms.update_one(
                                                {"_id": application_id},
                                                {'$set': {
                                                    f'offered_scholarship_info.all_scholarship_info.{iteration_id}':
                                                        scholarship_info}})
                                            break

                            element.update(data)
                            await DatabaseConfiguration().activity_email.update_one(
                                {"_id": item.get('_id')},
                                {'$set': {
                                    f'transaction_details.{_id}': element}})

        except Exception as e:
            logger.error(f"Something went wrong: {e}")

    async def update_last_opened(self, message_id, name):
        """
        This function will calculate the last opened email count and returns it
        Params:
           message_id (str): The unique message id of transaction
            name (str): The way message_id is texted with respect to different senders
        Returns:
            LastOpened (bool): The bool  value if last opened True
        """
        result = DatabaseConfiguration().communication_log_collection.aggregate(
            [
                {'$match': {
                    f"email_summary.transaction_id.{name}": message_id}},
                {'$group': {
                    '_id': "$_id"
                }}
            ]
        )
        async for item in result:
            communication_data = await DatabaseConfiguration().communication_log_collection.find_one(
                {'_id': item.get('_id')})
            if communication_data:
                transactions = communication_data.get("email_summary", {}).get(
                    "transaction_id", [])
                last_opened = 0
                len_transaction = len(transactions)
                end = 5 if len_transaction >= 5 else len_transaction
                if len_transaction not in [0, 1]:
                    for i in range(0, end):
                        if transactions[i].get("email_open", False):
                            last_opened += 1
                            break
                    if last_opened >= 1:
                        return True
                    return False
            return True

    async def process_email_webhook(self, message_id: str, event_type: str,
                                    event_time: Optional[str] = None,
                                    amazon_ses=False):
        data = {}
        if message_id:
            name = "messageId"
            if amazon_ses:
                name = "MessageId"
        try:
            if event_type in ["delivered", "delivery"]:
                last_opened = await self.update_last_opened(message_id, name)
                data.update(
                    {"last_opened": last_opened, "email_delivered": True,
                     'email_delivered_time': event_time})
            elif event_type == "open":
                last_opened = await self.update_last_opened(message_id, name)
                data.update({"last_opened": last_opened, "email_open": True,
                             'email_open_time': event_time})
            elif event_type == "click":
                data.update(
                    {"email_click": True, 'email_click_time': event_time})
            elif event_type == "spam":
                data.update(
                    {"email_spam": True, "email_spam_time": event_time})
            elif event_type == "bounce":
                data.update(
                    {"email_bounce": True, "email_bounce_time": event_time})
            if message_id:
                await self.update_transaction_details_by_message_id_in_the_communication_log_collection(
                    str(message_id), data, name)
                await self.update_transaction_details_by_message_id_in_the_communication_log_collection(
                    str(message_id), data, name, automation=True)
                await self.update_transaction_details_by_message_id_in_the_activity_email_collection(
                    str(message_id), data, name, event_type)
        except Exception as e:
            logger.error(f"Something went wrong: {e}")

    async def get_event_based_on_event_type_or_action_type(self, payload):
        """
        Get event from webhook payload
        """
        action_type_map = {
            'Delivered': 'delivered',
        }

        event_type_map = {
            'Open': 'open',
            'Click': 'click',
            'Spam': 'spam',
            'Bounce': 'bounce'
        }

        action_type = payload.get('action_type')
        event_type = payload.get('event_type')
        if action_type:
            event = action_type_map.get(action_type)
        elif event_type:
            event = event_type_map.get(event_type)
        else:
            raise ValueError("Unable to determine event type from the payload")
        return event

    async def capture_email_status_karix(self, request: Request,
                                         payload: EmailWebhook):
        """
        Capture email status by karix
        """
        payload = jsonable_encoder(payload)

        event = await self.get_event_based_on_event_type_or_action_type(
            payload)
        message_id = payload.get('message_id')
        event_time = payload.get('event_time')
        await self.process_email_webhook(message_id, event, event_time)

    async def capture_email_status_amazon_ses(self, request: Request):
        """
        Capture email status by amazon ses
        """
        try:
            event_data = await request.body()
            event_json = json.loads(event_data)
            event_type = str(event_json.get("eventType", "")).lower()
            mail_info = event_json.get("mail", {})
            message_id = mail_info.get("messageId")
            source = mail_info.get("source")

            logger.debug("___________________________________")
            logger.debug(event_json)
            logger.debug("____________________________________")
            logger.debug(f"Event type: {event_type}, message_id: {message_id},"
                         f" source: {source}")
            if not event_type or not message_id or not source:
                logger.error("Missing essential event data.")
                return
            if (college_info := await DatabaseConfiguration().college_collection.find_one(
                    {"email.source": source})) is not None:
                Reset_the_settings().check_college_mapped(
                    str(college_info.get("_id")))
                event_time = event_json.get(f"{event_type}", {}).get("timestamp",
                                                                     "")
                await self.process_email_webhook(message_id, event_type,
                                                 event_time, amazon_ses=True)
            else:
                logger.info(f"Client not found by source: {source}.")
        except json.JSONDecodeError as json_error:
            logger.error(f"JSON decode error: {json_error}")
        except Exception as e:
            logger.error(f"Something went wrong: {e}")

    async def get_timeline_based_on_event(
            self, student_id, event_type, start_date: datetime | None = None,
            end_date: datetime | None = None):
        """
        Get the email timeline.

        Params:
            student_id (ObjectId): A unique identifier/id of a student.
                e.g., 62bfd13a5ce8a398ad101bd7

        Returns:
            list: A list which contains email timeline.
        """
        pipeline = [
            {"$match": {"student_id": student_id}},
            {"$unwind": {"path": f"${event_type}_summary.transaction_id"}}
        ]
        facet_stage = {
            f"{event_type}_sent": [{"$count": "count"}],
            f"{event_type}_delivered": [
                {"$match": {
                    f"{event_type}_summary.transaction_id.{event_type}_delivered": True
                }},
                {"$count": "count"}],
        }
        if event_type == "email":
            facet_stage.update({"email_open": [
                {"$project": {"email_open_time": {"$dateFromString": {
                    "dateString": f"${event_type}_summary.transaction_id.email_open_time"
                }}}},
                {"$match": {
                    f"{event_type}_summary.transaction_id.email_open": True}},
                {"$count": "count"}], "email_click": [
                {"$project": {"email_click_time": {"$dateFromString": {
                    "dateString": f"${event_type}_summary.transaction_id.email_click_time"
                }}}},
                {"$match": {
                    f"{event_type}_summary.transaction_id.email_click": True}},
                {"$count": "count"}]})
        response = {}
        if start_date and end_date:
            facet_stage.get(f"{event_type}_sent", []).insert(
                0, {"$match": {
                    f"{event_type}_summary.transaction_id.created_at": {
                        "$gte": start_date,
                        "$lte": end_date}}})
            facet_stage.get(f"{event_type}_delivered", [])[0].get(
                "$match").update({
                f"{event_type}_summary.transaction_id.{event_type}_delivered_time":
                    {"$gte": start_date,
                     "$lte": end_date}})
            if event_type in ["email", "sms"]:
                facet_stage.get(f"{event_type}_delivered", []).insert(
                    0, {"$project": {
                        f"{event_type}_delivered_time": {"$dateFromString": {
                            "dateString": f"${event_type}_summary.transaction_id.{event_type}_delivered_time"
                        }}}})
            if event_type == "email":
                facet_stage.get("email_open", [])[1].get("$match", {}).update(
                    {f"{event_type}_summary.transaction_id.email_open_time":
                         {"$gte": start_date,
                          "$lte": end_date}}
                )
                facet_stage.get("email_click", [])[1].get("$match", {}).update(
                    {f"{event_type}_summary.transaction_id.email_click_time":
                         {"$gte": start_date,
                          "$lte": end_date}}
                )
        pipeline.append({"$facet": facet_stage})
        result = DatabaseConfiguration().communication_log_collection. \
            aggregate(pipeline)
        async for document in result:
            try:
                response["sent"] = document.get(f"{event_type}_sent", [{}])[
                    0].get("count", 0)
            except IndexError:
                response["sent"] = 0
            try:
                response["delivered"] = \
                    document.get(f"{event_type}_delivered", [{}])[0].get(
                        "count", 0)
            except IndexError:
                response[f"delivered"] = 0

            response.update({
                "sent": response.get("sent", 0),
                "delivered": response.get("delivered")})
            if event_type == "whatsapp":
                response.update({"auto_reply": 0,
                                 "click_rate": 0})
            if event_type == "email":
                try:
                    response["open_rate"] = \
                        document.get(f"email_open", [{}])[0].get("count", 0)
                except IndexError:
                    response["open_rate"] = 0
                try:
                    response["click_rate"] = \
                        document.get(f"email_click", [{}])[0].get(
                            "count", 0)
                except IndexError:
                    response["click_rate"] = 0
                email_open_rate = utility_obj.get_percentage_result(
                    response.get('email_open', 0), response.get(
                        'email_sent', 0))
                email_click_rate = utility_obj.get_percentage_result(
                    response.get('click_rate', 0),
                    response.get('sent', 0))
                email_delivered_rate = utility_obj.get_percentage_result(
                    response.get('delivered', 0),
                    response.get('sent', 0))
                response.update({
                    "open_rate": email_open_rate,
                    "click_rate": email_click_rate,
                    "complaint_rate": 0,
                    "bounce_rate": 0,
                    "unsubscribe_rate": 0,
                    "delivered_rate": email_delivered_rate
                })
        return {"data": response, "message": f"Get the {event_type} logs."}
