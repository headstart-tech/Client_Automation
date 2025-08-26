"""
This file contains class and functions related to get tawk chat data.
"""

from app.database.configuration import DatabaseConfiguration
from app.core.utils import utility_obj
from datetime import datetime


class GetTawkChatData:
    """
    Tawk Chat list table related class and functions which help to retrieve
        chat list.
    """

    async def chat_data_helper(self, data: dict) -> dict:
        """
        Get the user chat data in formatted way.

        Params:
            - data (dict): A dictionary which contains user chat data which
                want to format.

        Returns:
            - dict: A dictionary which contains chat user data in the
                formatted way.
        """
        res = {
            "_id": str(data.get("_id")),
            "chat_id": data.get("chat_id"),
            "name": data.get("name"),
            "city": data.get("city"),
            "country": data.get("country"),
            "email": data.get("email"),
            "chat_end_time": utility_obj.get_local_time(data.get("chat_end_time")),
            "converted_lead": data.get("converted_lead")
        }

        return res

    async def get_chat_data(self) -> list:
        """
        Retrieve the user chat data from database.

        Returns:
            - list: A list which contains all chat data of users.
        """
        chat_list = DatabaseConfiguration().tawk_chat.aggregate([])
        chat_data_dict = [
            await self.chat_data_helper(item)
            for item in await chat_list.to_list(None)]
        return chat_data_dict
