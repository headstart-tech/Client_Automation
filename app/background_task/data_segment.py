"""
This file contains class and functions related to data segment.
"""
from bson import ObjectId

from app.core.background_task_logging import background_task_wrapper
from app.core.log_config import get_logger
from app.database.configuration import DatabaseConfiguration
from app.helpers.automation.automation_helper import AutomationHelper

logger = get_logger(name=__name__)


class DataSegmentActivity:
    """
    A class which contains data segment functionality related methods.
    """

    @background_task_wrapper
    async def store_student_mapped_data(self, data_segment_id: str,
                                        college_id: str) -> None:
        """
        Store data related student mapped with data segment in the DB.

        Params:
            - data_segment_id (str): An unique identifier of data segment.
                e.g., 123456789012345678901243
            - college_id (str): An unique identifier of college.
                e.g., 123456789012345678901234

        Returns: None

        Raises:
            - Exception: An error occurred when something wrong happen in the
              backend code.
        """
        try:
            if (data_segment_info := await DatabaseConfiguration().
                    data_segment_collection.find_one(
                {'_id': ObjectId(data_segment_id)})) is None:
                data_segment_info = {}
            data_list = await AutomationHelper().get_data_from_db(
                data_segment_info, college_id, data_segments=True, emails=True,
                numbers=True, data_segment_id=data_segment_id)
            if data_list:
                DatabaseConfiguration().data_segment_mapping_collection. \
                    insert_many(data_list)
        except Exception as error:
            logger.error(f"An error occurred when store student mapped data "
                         f"for data segment id `{data_segment_id}`. "
                         f"Error - {error}")
