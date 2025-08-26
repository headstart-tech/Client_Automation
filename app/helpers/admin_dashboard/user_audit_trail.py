from app.core.log_config import get_logger
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration

logger = get_logger(__name__)


class AuditTrail:
    """
    Contain helper functions related to user audit trail
    """
    async def get_audit_trail_aggregate(
            self,
            user=None,
            start_date=None,
            end_date=None,
            skip=0,
            limit=10,
    ):
        """
        Aggregate audit trail data from the MongoDB collection with optional filtering, pagination, and date range.

        This method constructs and executes an aggregation pipeline on the `user_audit_collection` to fetch
        audit trail data. The data can be filtered by user ID, date range, and paginated using skip and limit
        parameters. The results are returned along with the total count of matching documents.

        Args:
            user (str, optional): The ID of the user to filter the audit data by. Defaults to None.
            start_date (datetime, optional): The start date for filtering the audit data. Defaults to None.
            end_date (datetime, optional): The end date for filtering the audit data. Defaults to None.
            skip (int, optional): The number of documents to skip for pagination. Defaults to None.
            limit (int, optional): The maximum number of documents to return for pagination. Defaults to None.

        Returns:
            tuple: A tuple containing:
                - result_data (list): The list of paginated results matching the filter criteria.
                - result_count (int): The total count of documents matching the filter criteria.
        """
        pipeline = [
            {
                "$project": {
                    "_id": 0,
                    "user_id": "$requested_user",
                    "ip_address": "$ip_address",
                    "api_hit": "$action",
                    "description": "$description",
                    "timestamp": "$timestamp",
                    "status_code": "$details.code",
                    "message":"$details.message"
                },
            },
            {
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            }
        ]
        match = {}
        date_range = {}
        if start_date or end_date:
            if start_date:
                date_range["$gte"] = start_date
            if end_date:
                date_range["$lte"] = end_date
            match.update({"timestamp": date_range})

        if user:
            match.update({"requested_user": user})

        if match:
            pipeline.insert(0,{"$match": match})

        try:
            result = (
                await DatabaseConfiguration()
                .user_audit_collection.aggregate(pipeline)
                .to_list(None)
            )
            result_data = result[0].get("paginated_results")
            result_count = result[0].get("totalCount")[0].get("count")
            logger.info("Aggregation query executed successfully")
            logger.debug(f"Result data: {result_data}, Result count: {result_count}")

            for data in result_data:
                data["timestamp"] = utility_obj.get_local_time(data.get("timestamp"))
            return result_data, result_count
        except Exception as e:
            logger.error(f"An error occurred while executing the aggregation query: {e}")
            raise
