"""
Check out reason data helper
"""
from app.database.configuration import DatabaseConfiguration


class CheckOutReasonList:
    """
    All related function for getting checkout reason from the database.
    """

    async def reason_list_helper(self, item: dict) -> dict:
        """Function for format the dictionary data which is getting from database to the response format

        Params:
            item (dict): Unit raw data of reason which is getting from the database.

        Returns:
            dict: Formatted unit data.
        """
        data = {
            "title": item.get("title"),
            "icon": item.get("icon")
        }

        return data

    async def get_reason_helper(self) -> list[dict]:
        """Function to get all the data of check out reason from the database.

        Returns:
            dict: Return list of data object in list format.
        """

        reason_data = DatabaseConfiguration().check_out_reason.aggregate([
            {
                "$match": {
                    "status": True
                }
            }
        ])

        reason_dict = [
            await self.reason_list_helper(item) for item in await reason_data.to_list(None)
        ]

        return reason_dict