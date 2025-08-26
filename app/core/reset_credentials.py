"""
Initialize the current credentials which we are fetch from the database
"""

from bson import ObjectId as BsonObjectId
from fastapi.exceptions import HTTPException

from app.core.log_config import get_logger
from app.core.utils import get_settings, get_new_instance_mastar_data
from app.database.motor_base_singleton import MotorBaseSingleton

logger = get_logger(__name__)


class Reset_the_settings:
    """rest the fields of the settings dictionary"""

    def validate(self, v):
        if not BsonObjectId.is_valid(v):
            raise ValueError("Invalid college ObjectId")

    def get_user_database(self, college_id, form_data=None, db_name=None):
        """initialize the current user database"""
        master_credential = MotorBaseSingleton.get_instance().master_data
        if college_id is None or college_id == "":
            if form_data.client_id is None:
                raise HTTPException(
                    status_code=422, detail="Please enter the college id"
                )
            college_id = form_data.client_id
        self.validate(college_id)
        if str(college_id) == str(master_credential.get("collage_id")):
            return
        MotorBaseSingleton.clear_instance()
        MotorBaseSingleton(college_id=college_id, db_name=db_name)
        logger.info("College id changed in singleton file to %s", college_id)
        from app.database.motor_base import (motor_base, SeasonConnectionManager)
        from app.database.database_sync import PyMongoBase
        motor_base.reset_connections()
        SeasonConnectionManager.reset_all_connections()
        PyMongoBase().reset_connections()
        get_new_instance_mastar_data()
        get_settings.cache_clear()
        get_settings()
        return college_id

    def check_college_mapped(self, college_id):
        """
        Check the college credential mapping with current settings

        params:
            college_id (str): College id to check for mapping in utils settings

        return:
            response: nothing
        """
        master_data = MotorBaseSingleton.get_instance().master_data
        if str(master_data.get("client_id")) != str(college_id):
            self.get_user_database(college_id=str(college_id))
