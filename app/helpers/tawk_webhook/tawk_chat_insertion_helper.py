"""
This file contains class and functions related to add tawk chat into DB
through webhook.
"""

from app.database.configuration import DatabaseConfiguration
from app.core.utils import settings
from app.core.custom_error import CustomError
from fastapi.exceptions import HTTPException
from datetime import datetime
import hmac
import hashlib
import json


class TawkChatWebhook:

    def verify_signature(self, body, signature: str) -> bool:
        """
        Verify signature along with data and signature.
        key.

        Params:
            - body (dict): A request body which get from webhook.
            - signature (str): Hash secret key.

        Raises:
            - CustomError: 404 - Verification failed.

        Returns:
            - bool: A boolean value True if signture verified else false.
        """
        
        if (tawk_secret_key := settings.tawk_secret_key) is None:
            raise HTTPException(status_code=404, detail="Tawk secret key not "
                                                        "found.")

        digest = hmac.new(tawk_secret_key.encode('utf-8'),
                          body.encode("utf-8"), hashlib.sha1).hexdigest()

        return signature == digest

    async def chat_data_insertion(self, data, signature: str) -> dict:
        """
        Chat data insertion helper function.

        Params:
            - data (dict): Payload data in the form of dictionary
            - signature (str): Header signature secret key which is sending by
                the tawk requester.

        Raises:
            - CustomError: 404 - Verification failed

        Returns:
            - dict: Success message if verified and successfully saved.
        """
        if not self.verify_signature(body=data.decode("utf-8"),
                                     signature=signature):
            raise CustomError("Verification failed")
        
        temp_data = json.loads(data.decode('utf-8'))

        visitor_info = temp_data.get("visitor", {})

        data_to_insert = {
            "chat_id": temp_data.get("chatId", ""),
            "name": visitor_info.get("name", ""),
            "city": visitor_info.get("city", ""),
            "country": visitor_info.get("country", ""),
            "email": visitor_info.get("email", ""),
            "chat_end_time": datetime.strptime(temp_data.get("time"),
                                               "%Y-%m-%dT%H:%M:%S.%fZ"),
            "created_at": datetime.utcnow(),
            "converted_lead": False
        }

        await DatabaseConfiguration().tawk_chat.insert_one(data_to_insert)
        return {"message": "Chat saved successfully!!"}
