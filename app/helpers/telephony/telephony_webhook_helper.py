"""
Call details by telephone webhook helper
"""
from datetime import datetime

from bson.objectid import ObjectId
from fastapi.exceptions import HTTPException

from app.core.log_config import get_logger
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.helpers.telephony.call_popup_websocket import manager
from app.dependencies.oauth import cache_invalidation

logger = get_logger(name=__name__)

class TelephonyWebhook:
    """
    All related functions of telephony webhook
    """
    async def application_details_helper(self, application: dict) -> dict:
        """
        Application details serializer
        
        Params:
            - application (dict): A dictionary which contains application data.

        Returns:
            - dict: A dictionary which contains formatted/serialized application data.
        """
        return {
            "application_id": str(application.get("_id")),
            "custom_application_id": application.get("application_id"),
            "course": application.get("course_name"),
            "specialization": application.get("spec_name")
        }
    

    async def websocket_data(self, call_from: str|None) -> list:
        """Searilize websocket data which has to be send to the frontend

        Params:
            call_from (str): Call initiator unique user id

        Returns:
            list: list of calls popup data
        """
        calls = []
        if call_from:
            calls = DatabaseConfiguration().call_activity_collection.aggregate([
                {
                    '$match': {
                        "$or": [
                            {
                                "call_from": ObjectId(call_from)
                            },
                            {
                                "call_to": ObjectId(call_from)
                            }
                        ],
                        'show_popup': True
                    }
                }
            ])

        call_activity = []

        async for call in calls:
            pipeline = []
            if call.get("type") == "Outbound":
                pipeline.append({
                    '$match': {
                        '_id': call.get("call_to")
                    }
                })
            else:
                pipeline.append({
                    "$match": {
                        "_id": call.get("call_from")
                    }
                })

            pipeline.extend([
                {
                    '$lookup': {
                        'from': 'studentApplicationForms', 
                        'localField': '_id', 
                        'foreignField': 'student_id', 
                        'as': 'applications'
                    }
                }, {
                    '$unwind': '$applications'
                }, {
                    '$lookup': {
                        'from': 'courses', 
                        'localField': 'applications.course_id', 
                        'foreignField': '_id', 
                        'as': 'courses'
                    }
                }, {
                    '$unwind': '$courses'
                }, {
                    '$group': {
                        '_id': '$applications._id', 
                        'application_id': {
                            '$first': '$applications.custom_application_id'
                        }, 
                        'course_name': {
                            '$first': '$courses.course_name'
                        }, 
                        'spec_name': {
                            '$first': '$applications.spec_name1'
                        }
                    }
                }
            ])
            applications = DatabaseConfiguration().studentsPrimaryDetails.aggregate(pipeline)
            if call.get("type") == "Outbound":
                data = {
                    "call_id": str(call.get("_id")),
                    "student_id": str(call.get("call_to")) if call.get("call_to") else None,
                    "student_phone": call.get("call_to_number"),
                    "student_name": call.get("call_to_name") if call.get("call_to_name", "") else "Unknown",
                    "call_type": call.get("type"),
                    "is_student_exist": True if call.get("call_to") else False,
                    "is_call_end": False if call.get("status") == "Originate" else True,
                    "call_initiate_time": utility_obj.get_local_time(call.get("starttime")),
                    "call_end_time": utility_obj.get_local_time(call.get("endtime")),
                    "duration": call.get("duration") if call.get("duration") else 0,
                    "application_list": [await self.application_details_helper(application) for application in await applications.to_list(None)]
                }
            else:
                data = {
                    "call_id": str(call.get("_id")),
                    "student_id": str(call.get("call_from")) if call.get("call_from") else None,
                    "student_phone": call.get("call_from_number"),
                    "student_name": call.get("call_from_name") if call.get("call_from_name", "") else "Unknown",
                    "call_type": call.get("type"),
                    "is_student_exist": True if call.get("call_from") else False,
                    "is_call_end": False if call.get("status") == "CONNECTING" else True,
                    "call_initiate_time": utility_obj.get_local_time(call.get("starttime")),
                    "call_end_time": utility_obj.get_local_time(call.get("endtime")),
                    "duration": call.get("duration") if call.get("duration") else 0,
                    "application_list": [await self.application_details_helper(application) for application in await applications.to_list(None)]
                }
            call_activity.append(data)

        return call_activity


    async def update_outbound_call_data(self, data: dict) -> dict:
        """Update telephony outbound call webhook data into database

        Params:
            data (dict): webhook data

        Returns:
            dict: return response message
        """

        call_data = await DatabaseConfiguration().call_activity_collection.find_one({
            "call_id": data.get("callid")
        })

        starttime = await utility_obj.date_change_utc(data.get("starttime"), date_format="%Y-%m-%d %H:%M:%S")
        endtime = None 
        if data.get("endtime") != "0000-00-00 00:00:00":
            endtime = await utility_obj.date_change_utc(data.get("endtime"), date_format="%Y-%m-%d %H:%M:%S")

        if not call_data:
            caller = await DatabaseConfiguration().user_collection.find_one({"mobile_number": int(data.get("executive"))})
            await DatabaseConfiguration().call_activity_collection.insert_one({
                "call_id": data.get("callid"),
                "starttime": starttime,
                "status": data.get("status"),
                "call_from_number": int(data.get("executive")),
                "call_from": caller.get("_id"),
                "call_from_name": utility_obj.name_can(caller),
                "call_to_number": int(data.get("customer")),
                "endtime": endtime,
                "ref_id": data.get("refid"),
                "pulse": data.get("pulse"),
                "type": data.get("callType"),
                "show_popup": True,
                "created_at": datetime.utcnow()
            })

        else:
            await DatabaseConfiguration().call_activity_collection.update_one(
                {"_id": call_data.get("_id")},
                {
                    "$set": {
                        "starttime": starttime,
                        "status": data.get("status"),
                        "endtime": endtime,
                        "ref_id": data.get("refid"),
                        "pulse": data.get("pulse"),
                        "type": data.get("callType"),
                        "duration": int(data.get("answeredtime")),
                        "show_popup": True if data.get("status") in ["Originate", "Call Complete"] else False,
                        "mcube_file_path": data.get("filename")
                    }
                }
            )
        
        call_data = await DatabaseConfiguration().call_activity_collection.find_one({
            "call_id": data.get("callid")
        })

        call_from = str(call_data.get("call_from"))

        call_activity = await self.websocket_data(call_from)

        await manager.publish_data_on_redis(f"{call_from}_telephony", call_activity)

        return {"message": "Data saved successfully!!"}


    async def update_inbound_callback_call_data(self, data: dict) -> dict:
        """Update telephony inbound/CallBack call webhook data into database

        Params:
            data (dict): Webhook data

        Returns:
            dict: return response message
        """
        call_id = data.get("callid")
        starttime = await utility_obj.date_change_utc(
            data.get("starttime"), date_format="%Y-%m-%d %H:%M:%S")
        endtime = None
        if data.get("dialstatus") != "CONNECTING":
            endtime = await utility_obj.date_change_utc(
                data.get("endtime"), date_format="%Y-%m-%d %H:%M:%S")
            
        caller = await DatabaseConfiguration().studentsPrimaryDetails.find_one({
            "basic_details.mobile_number": data.get("callfrom")
        })
        receiver = await DatabaseConfiguration().user_collection.find_one({
            "mobile_number": int(data.get("callto")) if data.get("callto") else 0
        })

        call_data = await DatabaseConfiguration().call_activity_collection.find_one({
            "call_id": call_id
        })

        missed_status = ['NOANSWER', 'BUSY', 'CANCEL', "Missed"]

        if not call_data:
            await DatabaseConfiguration().call_activity_collection.insert_one({
                "call_id": call_id,
                "starttime": starttime,
                "status": data.get("dialstatus"),
                "call_from_number": int(data.get("callfrom")),
                "call_from": caller.get("_id") if caller else None,
                "call_from_name": utility_obj.name_can(caller.get("basic_details")) if caller else None,
                "call_to": receiver.get("_id") if receiver else None,
                "call_to_name": utility_obj.name_can(receiver) if receiver else None,
                "call_to_number": int(data.get("callto")) if data.get("callto") else None,
                "endtime": endtime,
                "ref_id": data.get("refid"),
                "pulse": data.get("pulse"),
                "type": "CallBack" if data.get("calltype") == "CallBack" else "Inbound",
                "show_popup": False if data.get("dialstatus") in missed_status else True,
                "created_at": datetime.utcnow()
            })

        else:
            existing_call = await DatabaseConfiguration().call_activity_collection.find_one({
                "call_from_number": int(data.get("callfrom")),
                "status": {
                    "$in": missed_status
                },
                "call_id": {
                    "$ne": call_id
                }
            })

            data = {
                "status": data.get("dialstatus"),
                "call_from": caller.get("_id") if caller else None,
                "call_from_name": utility_obj.name_can(caller.get("basic_details")) if caller else None,
                "endtime": endtime,
                "ref_id": data.get("refid"),
                "duration": int(data.get("duration")),
                "pulse": data.get("pulse"),
                "show_popup": False if data.get("dialstatus") in missed_status else True,
                "mcube_file_path": data.get("filename"),
            }

            if existing_call:
                data.update({
                    "call_to": existing_call.get("call_to"),
                    "call_to_name": existing_call.get("call_to_name"),
                    "call_to_number": existing_call.get("call_to_number")
                })

            await DatabaseConfiguration().call_activity_collection.update_one(
                {"_id": call_data.get("_id")},
                {
                    "$set": data
                }
            )

        call_data = await DatabaseConfiguration().call_activity_collection.find_one({
            "call_id": call_id
        })

        await DatabaseConfiguration().studentsPrimaryDetails.update_one({
                "basic_details.mobile_number": str(call_data.get("call_from_number"))
            },
            {
                "$addToSet": {
                    "tags": "Missed Call"
                }
            }
        )
        
        call_to = str(call_data.get("call_to")) if call_data.get("call_to") else None

        call_activity = await self.websocket_data(call_to)
        await manager.publish_data_on_redis(f"{call_to}_telephony", call_activity)

        return {"message": "Data saved successfully!!"}


    async def update_websocket_data(self, data: dict) -> dict:
        """Update telephone call data through webhook into database

        Params:
            data (dict): Data which has to be stored

        Returns:
            dict: Return response message
        """

        await cache_invalidation(api_updated="telephony/webhook")

        if data.get("callType") == "Outbound":
            response = await self.update_outbound_call_data(data)


        elif data.get("callType") == "Inbound" or data.get("calltype") == "CallBack":
            response = await self.update_inbound_callback_call_data(data)

        else:
            logger.error("CallType invalid by telephony!!")
            raise HTTPException(status_code=404, detail="Telephony webhook data invalid")
        
        return response
