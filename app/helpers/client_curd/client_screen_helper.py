"""
This File Contains Functions helping Configure Client Screen
"""
import json

from app.database.configuration import DatabaseConfiguration
from bson import ObjectId
from app.core.custom_error import CustomError, DataNotFoundError

class ClientScreenHelper():
    async def get_client_screen_by_id(self, client_id: str)->dict:
        """
        This method is used to get the client screen

        Params:
            client_id (str): Get the client id

        Returns:
            dict: Return the client screen

        Raises:
            CustomError: If the client id is invalid
            DataNotFoundError: If the client screen is not found
        """
        # Check if the client id is valid
        if not ObjectId.is_valid(client_id):
            raise CustomError(message="Invalid client id")

        # Get the client screen
        client_screen = await DatabaseConfiguration().master_screens.find_one(
            {
                "client_id": ObjectId(client_id),
                "screen_type": "client_screen"
            }
        )
        if not client_screen:
            raise DataNotFoundError(message="Client screen")

        client_screen = json.loads(json.dumps(client_screen, default=str))

        return client_screen

