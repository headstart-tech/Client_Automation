"""
Counsellor call log data summary helper.
"""
from app.database.configuration import DatabaseConfiguration
from app.core.utils import utility_obj
from bson.objectid import ObjectId
from datetime import date
from app.core.log_config import get_logger
from app.core.custom_error import CustomError

logger = get_logger(name=__name__)

class CounsellorCallLog:
    """
    All related function for getting missed calls list from the database.
    """

    async def call_header_helper(self, item: dict) -> dict:
        """Function for format the dictionary data which is getting from database to the response format

        Params:
            item (dict): Unit raw data of calls which is getting from the database.

        Returns:
            dict: Formatted unit data.
        """
        return {
            "total_calls": item.get("totalCalls")[0].get("count") if item.get("totalCalls") else 0,
            "inbound_calls": item.get("inboundCalls")[0].get("count") if item.get("inboundCalls") else 0,
            "outbound_calls": item.get("outboundCalls")[0].get("count") if item.get("outboundCalls") else 0,
            "connected_calls": item.get("connectedCalls")[0].get("count") if item.get("connectedCalls") else 0,
            "call_gt_90": item.get("callsGT90")[0].get("count") if item.get("callsGT90") else 0,
            "missed_calls": item.get("missedCalls")[0].get("count") if item.get("missedCalls") else 0,
            "callback_calls": item.get("callBackCalls")[0].get("count") if item.get("callBackCalls") else 0,
        }
    

    async def call_data_pipeline_helper(self, counsellors: list[str], date_range: dict) -> dict:
        """
        Fetch call header data from the database using an aggregation pipeline.

        Params:
            counsellors (list[str]): List of counselor IDs.
            date_range (dict): Date range for filtering data.

        Returns:
            dict: Response dictionary.
        """
        try:
            counsellors_list = [ObjectId(user_id) for user_id in counsellors]
            match_stage = {'$or': [{'call_to': {"$in": counsellors_list}}, {'call_from': {'$in': counsellors_list}}]}
            
            if date_range:
                start_date, end_date = await utility_obj.date_change_format(
                    date_range.get('start_date'),
                    date_range.get('end_date')
                )
                match_stage.update({"created_at": {"$gte": start_date, "$lte": end_date}})
            
            pipeline = [
                {"$match": match_stage},
                {
                    '$facet': {
                        "totalCalls": [{"$count": "count"}],
                        "inboundCalls": [{"$match": {"type": {"$in": ['Inbound', 'CallBack']}}}, {"$count": "count"}],
                        "outboundCalls": [{"$match": {"type": "Outbound"}}, {"$count": "count"}],
                        "connectedCalls": [{"$match": {"status": {"$in": ["ANSWER", 'Call Complete']}}}, {"$count": "count"}],
                        "callsGT90": [{"$match": {"duration": {"$gt": 90}}}, {"$count": "count"}],
                        "missedCalls": [{"$match": {'type': {'$in': ['Inbound', 'CallBack']}, 'status': {"$in": ["BUSY", "CANCEL", "NOANSWER", "Missed"]}}}, {"$count": "count"}],
                        "callBackCalls": [{"$match": {'type': 'CallBack'}}, {"$count": "count"}]
                    }
                },
                {
                    '$project': {
                        "totalCalls": 1,
                        "inboundCalls": 1,
                        "outboundCalls": 1,
                        "connectedCalls": 1,
                        "callsGT90": 1,
                        "missedCalls": 1,
                        "callBackCalls": 1
                    }
                }
            ]
            
            calls_data = await DatabaseConfiguration().call_activity_collection.aggregate(pipeline).to_list(None)
            if not calls_data:
                return {}
            
            return await self.call_header_helper(calls_data[0])
        except Exception as e:
            logger.info(f"An error occure in getting the data. Error - {e}")
            raise CustomError("An error occure in getting the data.")


    async def log_header_helper(self, counsellors: list[str], date_range: dict, change_indicator) -> dict:
        """
        Fetch and process all call data for the counselor call log header.
        
        Params:
            counsellors (list[str]): List of counselor IDs.
            date_range (dict): Date range for filtering data.
            change_indicator (str): Change indicator parameter.

        Returns:
            dict: A dictionary containing total count of call details and change indicators.
        """

        data = await self.call_data_pipeline_helper(counsellors, date_range)

        if change_indicator is not None:
            start_date, middle_date, previous_date = await utility_obj. \
                get_start_date_and_end_date_by_change_indicator(change_indicator)

            previous_date_data = await self.call_data_pipeline_helper(counsellors, date_range={"start_date": str(start_date),
                        "end_date": str(middle_date)})
            current_date_data = await self.call_data_pipeline_helper(counsellors, date_range={"start_date": str(previous_date),
                        "end_date": str(date.today())})
            
            total_calls_change_indicator = await utility_obj.get_percentage_difference_with_position(previous_date_data.get("total_calls", 0), current_date_data.get("total_calls", 0))
            calls_gt_90_change_indicator = await utility_obj.get_percentage_difference_with_position(previous_date_data.get("call_gt_90", 0), current_date_data.get("call_gt_90", 0))

            data.update({
                "total_calls_change_indicator": {
                    "total_calls_perc_indicator": total_calls_change_indicator.get("percentage", 0),
                    "total_calls_pos_indicator": total_calls_change_indicator.get("position", "equal")
                },
                "call_gt_90_change_indicator": {
                    "calls_gt_90_perc_indicator": calls_gt_90_change_indicator.get("percentage", 0),
                    "calls_gt_90_pos_indicator": calls_gt_90_change_indicator.get("position", "equal")
                }
            })
        
        return data