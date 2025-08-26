"""
Outbound call summary helper for communication dashboard call summary table.
"""
from app.database.configuration import DatabaseConfiguration
from app.core.utils import utility_obj
from bson.objectid import ObjectId
from app.helpers.telephony.inbound_call_summary_helper import InboundCallSummary


class OutboundCallSummary:
    """
    All related function for getting outbound calls list from the database.
    """

    async def call_data_helper(self, item: dict) -> dict:
        """Function for format the dictionary data which is getting from database to the response format

        Params:
            item (dict): Unit raw data of calls which is getting from the database.

        Returns:
            dict: Formatted unit data.
        """
        application = {}
        if application_id := item.get("application"):
            application = await DatabaseConfiguration().studentApplicationForms.find_one({"_id": application_id})
        return {
            "_id": str(item.get("_id")),
            "call_instance": utility_obj.get_local_time(item.get("created_at")) if item.get("created_at") else None,
            "dialed_number": item.get("call_to_number"),
            "call_status": "Answered" if item.get("status") == "Call Complete" else "Not Answered",
            "duration": item.get("duration", 0),
            "recording": item.get("mcube_file_path", None),
            "dialed_by": item.get("call_from_name"),
            "call_to_name": item.get("call_to_name"),
            "custom_application_id": application.get("custom_application_id"),
            "application_id": str(application_id) if application_id else None,
            "student_id": str(item.get("call_to")) if item.get("call_to") else None
        }

    async def outbound_calls(self, dialed_by: list[str], call_status: str, 
                             date_range: dict, search: str, sort: bool, 
                             sort_name: str, sort_type: str, page_num: int, 
                             page_size: int) -> list[dict]:
        """
        Function to get all calls data from the database.

        Params:
            dialed_by (list[str]): List of dialed college user unique id.
            call_status (str): It must be "Answered" or "Not Answered"
            date_range (dict): Date range which data has to be fetched.
            search (str): Search key
            sort (bool): Is sort apply on the data or not.
            sort_name (str): Field name which has to be sorted.
            sort_type (str): It denotes the sorting order will be asc or desc.

        Returns:
            list[dict]: Return list of call details.

        """
        pipeline = []

        match_stage = {
            "type": "Outbound"
        }

        if call_status and call_status.lower() == 'answered':
            match_stage.update({
                "status": "Call Complete"
            })

        if call_status and call_status.lower() == "not answered":
            match_stage.update({
                "status": {
                    "$ne": "Call Complete"
                }
            })

        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'),
                date_range.get('end_date'))
            match_stage.update({
                "created_at": {"$gte": start_date,
                               "$lte": end_date
                               }
            })

        if search:
            match_stage.update({
                "$or": [
                    {
                        "call_to_number": {
                            "$regex": search, 
                            "$options": "i"
                        }
                    },
                    {
                        "call_to_name": {
                            "$regex": search, 
                            "$options": "i"
                        }
                    }
                ]
            })

        if dialed_by:
            match_stage.update({
                "call_from": {
                    "$in": [ObjectId(user_id) for user_id in dialed_by]
                }
            })
        
        pipeline.append({"$match": match_stage})

        await InboundCallSummary().add_sort_in_pipeline(pipeline)

        if sort:
            if sort_name.lower() == "call status":
                sort_name = "status"

            elif sort_name.lower() == "duration":
                sort_name = "duration"
            
            elif sort_name.lower() == "dialed by":
                sort_name = "call_from_name"

            pipeline.append({"$sort": {sort_name: 1 if sort_type in [None, "asc"] else -1}})

        skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                              page_size)
        pipeline.append({
            "$facet": {
                "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                "totalCount": [{"$count": "count"}],
            }
        })

        calls_data = await (DatabaseConfiguration().call_activity_collection.aggregate(pipeline)).to_list(None)

        calls_data = calls_data[0] if calls_data else {}

        calls_dict = [
            await self.call_data_helper(item) for item in calls_data.get("paginated_results", [])
        ]
        
        totalCount = calls_data.get("totalCount", [{}])

        count = totalCount[0].get("count", 0) if totalCount else 0
        return calls_dict, count