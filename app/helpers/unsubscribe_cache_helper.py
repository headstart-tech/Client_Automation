"""
This file contains functions regard to unsubscribe students cache storage
"""
import json

from app.database.configuration import DatabaseConfiguration


class UnsubscribeHelper:
    """
    Contain helper functions related to unsubscribe cache storage
    """

    async def check_unsubscribe(self):
        """
        This function checks and returns all those students who unsubscribed to get mails
        Params:
            None
        Returns:
            list: A list which contains students email ids who not unsubscribe emails.
        """
        pipeline = [
            {
                "$match": {"unsubscribe": True}
            },
            {
                "$group": {
                    "_id": None,
                    "result": {"$push": "$_id"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "result": 1
                }
            }
        ]

        result = await DatabaseConfiguration().studentsPrimaryDetails.aggregate(pipeline).to_list(None)
        result = result[0]["result"] if result else []
        return result

    async def check_last_opened_hard_bounce(self, student_ids):
        """
        This function grabs list of all those students whose mails are bounced
        Params:
            student_ids (list): The list of unique ids of student
        Returns:
            list: A list which contains students ids who not opened last 5 emails or email bounce.
        """
        pipeline = [
            {
              "$match": {
                  "student_id": {"$nin": student_ids},
                  "$or": [
                              {"last_5_email_opened": {"$exists": True, "$eq": False}},
                              {"email_bounce": {"$exists": True, "$eq": True}}
                          ]
                      }

            },
            {
                "$group": {
                    "_id": None,
                    "result": {"$push": "$student_id"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "result": 1
                }
            }
        ]
        result = await DatabaseConfiguration().communication_log_collection.aggregate(pipeline).to_list(None)
        result = result[0]["result"] if result else []
        await DatabaseConfiguration().studentsPrimaryDetails.update_many(
            {"_id": {"$in": result}},
            {"$set": {"unsubscribe": True}}
        )
        return result

    async def get_email_ids(self, student_ids):
        """
        This function returns  all email ids of given student_ids
        Params:
          student_ids (list): The list of unique ids of students
        Returns:
            list of email_ids of given student_ids
        """
        pipeline = [
            {
                "$match": {
                    "_id": {"$in": student_ids}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "user_names": {"$push": "$user_name"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "user_names": 1
                }
            }
        ]
        result = await DatabaseConfiguration().studentsPrimaryDetails.aggregate(pipeline).to_list(None)
        user_names = result[0].get("user_names", []) if result else []
        return user_names

    def remove_email_unsubscribe_students(self, email_type: str, email_ids: list) \
            -> list:
        """
        This functions removes all those mail_ids who unsubscribed or hardbounced
        Params:
          email_type (str): The email_type of email sent eg: default, promotional
          email_ids (list): the list of email ids
        """
        from app.dependencies.oauth import get_sync_redis_client, logger
        if email_type == "promotional":
            r = get_sync_redis_client()
            unsubscribe_emails = r.get("unsubscribed_student_list")
            if unsubscribe_emails:
                unsubscribe_emails = json.loads(unsubscribe_emails)
                unsubscribe_emails = set(unsubscribe_emails)
                email_ids = [x for x in email_ids if x not in unsubscribe_emails]
        if not email_ids:
            return []
        return email_ids
