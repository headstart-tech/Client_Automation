"""
This file contain class and functions related to user notifications
"""
import datetime
from dateutil.relativedelta import relativedelta
from bson import ObjectId
from app.database.configuration import DatabaseConfiguration

current_datetime = datetime.datetime.utcnow()


class Notification:
    """
    Contain functions related to notification activities
    """

    async def get_event_datetime_and_category(self, data: dict) -> tuple:
        """
        Get event datetime and category
        Params:
            data (dict): The data from which event datetime is fetched
        Returns:
            - Tuple: A tuple which contains following elements:
              - event_datetime (str): Event date time in string format.
              - category (str): Category in which event date falls in.
        """
        current_time_str = datetime.datetime.utcnow().strftime(
            "%d %b %Y %I:%M:%S %p")
        current_time = datetime.datetime.strptime(current_time_str,
                                                  "%d %b %Y %I:%M:%S %p")
        event_time_str = data.get("event_datetime").strftime(
            "%d %b %Y %I:%M:%S %p")
        event_time = datetime.datetime.strptime(event_time_str,
                                                "%d %b %Y %I:%M:%S %p")
        delta = relativedelta(current_time, event_time)
        months = delta.months
        days = delta.days
        hours = delta.hours
        if days == 0:
            if hours == 1:
                event_datetime = f"{hours} hour ago"
            else:
                event_datetime = f"{hours} hours ago"
            category = "today"
        elif months == 0:
            if days == 1:
                event_datetime = f"{days} day ago"
                category = "yesterday"
            else:
                event_datetime = event_time_str
                category = "older"
        else:
            event_datetime = event_time_str
            category = "older"
        return event_datetime, category

    async def format_notification_message_as_required(self, message: str) -> (
            str):
        """
        Format notification message as required

        Params:
            message (str): The message which is to be formatted

        Returns:
            message (str): The formatted message
        """
        CHAR_LENGTH = 95
        if message and len(message) > CHAR_LENGTH:
            temp_message = message.replace("<span class='notification-inner'>", "")
            temp_message = temp_message.replace("</span>", "")
            if len(temp_message) <= CHAR_LENGTH:
                pass
            else:
                result, char_count, prev_end_index = "", 0, 0
                while True:
                    start_index = message.find(
                        "<span class='notification-inner'>",
                        prev_end_index)

                    end_index = message.find("</span>", start_index)
                    if start_index != -1 and end_index != -1:
                        temp_str = message[prev_end_index + 1 if prev_end_index != 0 else prev_end_index: start_index]
                        if len(temp_str) != 0:
                            if char_count + len(temp_str) <= CHAR_LENGTH:
                                result += temp_str
                                char_count += len(temp_str)
                                prev_end_index = len(result) - 1
                                if char_count == CHAR_LENGTH:
                                    break
                                continue
                            else:
                                remaining_chars = CHAR_LENGTH - char_count
                                result += message[
                                          prev_end_index + 1:prev_end_index +
                                                             remaining_chars + 1]
                                break
                        inner_text_length = end_index - (
                                start_index +
                                len("<span class='notification-inner'>"))
                        if char_count + inner_text_length <= CHAR_LENGTH:
                            if char_count == 0:
                                char_count += (start_index + inner_text_length)
                                result += message[prev_end_index:
                                                  end_index + len("</span>")]
                            else:
                                char_count += inner_text_length
                                result += message[
                                          prev_end_index + 1:
                                          end_index + len("</span>")]
                            if char_count == CHAR_LENGTH:
                                break
                        else:
                            remaining_chars = CHAR_LENGTH - char_count
                            result += message[
                                      prev_end_index + 1:prev_end_index +
                                                         len("<span class='notification-inner'>") + remaining_chars + 1]
                            break

                        prev_end_index = len(result) - 1
                    else:
                        remaining_chars = CHAR_LENGTH - char_count
                        result += message[
                                  prev_end_index + 1:prev_end_index +
                                                     remaining_chars + 1]
                        break

                message = f"{result}..."
        return message

    async def prepare_user_notifications(self, response: dict, data: list, user: dict) -> list:
        """
        Get user notifications in proper format into list
        Params:
            response (dict): The result from pipeline
            data (list): The result data
            user (dict): User details
        Returns:
            data (list): The updated list
        """
        for doc in response.get("paginated_results"):
            event_datetime, category = await self.get_event_datetime_and_category(doc)
            title = doc.get("title")
            message = doc.get("message")
            update_resource_id = doc.get("update_resource_id")
            message = message.replace("{name}", user.get("first_name"))
            message = await self.format_notification_message_as_required(message)
            data.append(
                {
                    "notification_id": str(doc.get("_id")),
                    "event_type": doc.get("event_type"),
                    "student_id": str(doc.get("student_id")),
                    "application_id": str(doc.get("application_id")),
                    "message": message,
                    "mark_as_read": doc.get("mark_as_read"),
                    "event_datetime": event_datetime,
                    "category": category,
                    "title": title,
                    "update_resource_id": str(update_resource_id),
                    "hide": doc.get("hide", False),
                    "data_segment_redirect_link": doc.get("data_segment_redirect_link")
                }
            )
        return data

    async def user_notifications(self, user, skip, limit, unread_notification):
        """
        Return user notifications
        """
        pipeline = [
            {"$match": {"send_to": ObjectId(user.get("_id")), "hide":
                {"$in": [False, None]}}},
            {"$sort": {"created_at": -1}},
            {
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            },
        ]
        if unread_notification:
            pipeline[0].get("$match").update({"mark_as_read": False})
        result = DatabaseConfiguration().notification_collection.aggregate(
            pipeline)
        data, total_data = [], 0
        async for response in result:
            try:
                total_data = response.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
            data = await self.prepare_user_notifications(response, data, user)
        return total_data, data
