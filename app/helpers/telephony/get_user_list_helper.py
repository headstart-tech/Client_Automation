"""
Gat user list for filteration in communication module helper
"""
from app.database.configuration import DatabaseConfiguration
from app.core.utils import utility_obj
from bson.objectid import ObjectId


class UserListHelper:
    """
    All related function for getting users from the database.
    """

    async def user_list_helper(self, user: dict) -> dict:
        """Function for format the dictionary data which is getting from database to the response format

        Params:
            user (dict): Unit raw data of user which is getting from the database.

        Returns:
            dict: Formatted unit data.
        """
        return {
            "id": str(user.get("_id")),
            "name": utility_obj.name_can(user)
        }
    

    async def getting_user_list(self, users: list, customer_call: bool) -> list[dict]:
        """Getting user list which has to be shown to the requested user.

        Params:
            users (dict): List of all possible users which can be shown.
            customer_call (bool): If it is true - it means that it should be the Inbound call otherwise Outbound

        Returns:
            list[dict]: User list which should be shown to the user
        """
        pipeline = []

        if users:
            pipeline.insert(0, {
                "$match": {
                    "_id": {
                        "$in": [ObjectId(user_id) for user_id in users]
                    }
                }
            })

        filter_users = await (DatabaseConfiguration().user_collection.aggregate(pipeline)).to_list(None)
        calls_user = await (DatabaseConfiguration().call_activity_collection.aggregate([{
                '$group': {
                    '_id': "$call_to" if customer_call else "$call_from"
                }
            },
            {
                '$project': {
                    'call_to' if customer_call else 'call_from'
                        : "$_id",
                    '_id': 0
                }
            }]
        )).to_list(None)

        calls = [str(call.get("call_to")) if customer_call else str(call.get("call_from")) for call in calls_user]

        user_list = []
        for user in filter_users:
            if str(user.get("_id")) in calls:
                user_list.append(user)

        return user_list
    

    async def get_allowed_users_list(self, user: dict) -> list:
        """Filteration of users which details has to be shown to the requested user.

        Params:
            user (dict): Current requested user.

        Returns:
            list: List of users which can be displayed to the requested user
        """

        if user.get("role", {}).get("role_name") in ['college_admin', 'college_super_admin', 'super_admin']:
            return []

        elif user.get("role", {}).get("role_name") == 'college_head_counselor':
            users = [str(counsellor.get("_id")) for counsellor in 
                                        await (DatabaseConfiguration().user_collection.aggregate([{
                                                "$match": {
                                                    "head_counselor_id": ObjectId(user.get("_id"))
                                                }
                                        }])).to_list(None)]
            users.append(str(user.get("_id")))
            return users
            

        else:
            return [user.get("_id")]
        

    async def get_user_list(self, user: dict, is_answered_by: bool = True) -> list[dict]:
        """Function to get all the data of answered by user from the database

        Params:
            users (dict | None, optional): List of users can be shown. Defaults to None.

        Returns:
            list[dict]: Return list of data object in list format.
        """
    
        users = await self.get_allowed_users_list(user)

        filter_users = await self.getting_user_list(users, is_answered_by)

        return [
            await self.user_list_helper(user) for user in filter_users
        ]
