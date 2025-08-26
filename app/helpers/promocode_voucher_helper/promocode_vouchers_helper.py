"""
This file contains functions regarding promocode and vouchers
"""

import datetime
import random
import uuid

from bson import ObjectId
from fastapi import HTTPException
from kombu.exceptions import KombuError

from app.background_task.send_mail_configuration import EmailActivity
from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.custom_error import DataNotFoundError
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import cache_invalidation, is_testing_env
from app.helpers.student_curd.student_application_configuration import (
    StudentApplicationHelper,
)

logger = get_logger(name=__name__)
VOUCHER_DISCOUNT = 100


class PromocodeVouchers:
    """
    Contains helper functions related to promocode and vouchers
    """

    async def create_promocode(self, payload: dict, user: dict):
        """
        create a promo code
        Params:
            - payload (dict): Payload contains all fields that are to be inserted in the database regarding promocode
                              It has fields like name, code, discount, units, duration, e.t.c.
            - user (dict): Details of current user
        Returns (dict): A dict that has message of successful creation of promocode
        Raises:
            - Exception: An error occurred when something wrong happen in the code.
        """
        try:
            code = payload.get("code")
            if (
                await DatabaseConfiguration().promocode_collection.find_one(
                    {"code": code}
                )
                is not None
            ):
                return {"detail": "Promo code already exists."}
            duration = payload.get("duration", {})
            duration["start_date"], duration["end_date"] = (
                await utility_obj.date_change_format(
                    duration.get("start_date"), duration.get("end_date")
                )
            )
            data_segment_ids = payload.get("data_segment_ids", [])
            if data_segment_ids:
                payload["data_segment_ids"] = [ObjectId(id) for id in data_segment_ids]
            payload.update(
                {
                    "created_at": datetime.datetime.utcnow(),
                    "created_by_id": ObjectId(user.get("_id")),
                    "created_by_name": utility_obj.name_can(user),
                    "applied_count": 0,
                }
            )
            await DatabaseConfiguration().promocode_collection.insert_one(payload)
            return {"message": "Successfully created promocode!"}
        except Exception as e:
            logger.error("An error occurred while creating promo code")
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while creating promo code. Error - {e}",
            )

    async def get_all_promocodes(
        self,
        page_num: int | None,
        page_size: int | None,
        date_range: dict | None = None,
        download: bool = False,
    ) -> tuple:
        """
        Get all promocodes data with pagination.

        Params:
            - page_num (int | None): Either None or Page number which is required for pagination. A integer number which
                represents page number where want to show data. e.g., 1
            - page_size (int | None): Either None or Page size which is required for pagination. A integer number which
                represents data count per page. e.g., 25
            - date_range (dict): A dictionary which contains start_date and end_date which useful for get data
                based on date_range.
            - download (bool): True if need to download else false.

        Returns:
           A tuple which contains following things: result (list): list of all promocodes.
            total (int): total no. of documents.

        Raises:
            - Exception: An unexpected error occurred from code.
        """
        pipeline = [
            {
                '$addFields': {
                    'multi': {
                        '$map': {
                            'input': '$applied_by',
                            'as': 'item',
                            'in': {
                                '$multiply': [
                                    '$$item.course_fee', {
                                        '$divide': [
                                            '$discount', 100
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }, {
                '$addFields': {
                    'total_multi': {
                        '$sum': '$multi'
                    }
                }
            }, {
                '$project': {
                    '_id': {
                        '$toString': '$_id'
                    },
                    'code': 1,
                    'name': 1,
                    'discount': 1,
                    'applied_count': {
                        '$ifNull': [
                            '$applied_count', 0
                        ]
                    },
                    'total_units': '$units',
                    'available': {
                        '$subtract': [
                            '$units', {
                                '$ifNull': [
                                    '$applied_count', 0
                                ]
                            }
                        ]
                    },
                    'start_date': '$duration.start_date',
                    'end_date': '$duration.end_date',
                    'status': {
                        '$ifNull': [
                            '$status', ''
                        ]
                    },
                    'estimated_cost': '$total_multi',
                    'data_segment_ids': 1,
                    'created_at': 1
                }
            }, {
                '$unwind': {
                    'path': '$data_segment_ids',
                    'preserveNullAndEmptyArrays': True
                }
            }, {
                '$lookup': {
                    'from': 'dataSegment',
                    'let': {
                        'segment_id': '$data_segment_ids'
                    },
                    'pipeline': [
                        {
                            '$match': {
                                '$expr': {
                                    '$eq': [
                                        '$_id', '$$segment_id'
                                    ]
                                }
                            }
                        }, {
                            '$project': {
                                '_id': 1,
                                'data_segment_name': 1,
                                'segment_type': 1,
                                'count_at_origin': 1
                            }
                        }
                    ],
                    'as': 'data_segments'
                }
            }, {
                '$unwind': {
                    'path': '$data_segments',
                    'preserveNullAndEmptyArrays': True
                }
            }, {
                '$group': {
                    '_id': '$_id',
                    'code': {
                        '$first': '$code'
                    },
                    'name': {
                        '$first': '$name'
                    },
                    'discount': {
                        '$first': '$discount'
                    },
                    'applied_count': {
                        '$first': '$applied_count'
                    },
                    'total_units': {
                        '$first': '$total_units'
                    },
                    'available': {
                        '$first': '$available'
                    },
                    'start_date': {
                        '$first': '$start_date'
                    },
                    'end_date': {
                        '$first': '$end_date'
                    },
                    'status': {
                        '$first': '$status'
                    },
                    'estimated_cost': {
                        '$first': '$estimated_cost'
                    },
                    'created_at': {
                        '$first': '$created_at'
                    },
                    'data_segment_ids': {
                        '$push': {
                            '$cond': {
                                'if': {
                                    '$ne': [
                                        {
                                            '$ifNull': [
                                                '$data_segments', None
                                            ]
                                        }, None
                                    ]
                                },
                                'then': {
                                    'data_segment_id': {
                                        '$toString': '$data_segments._id'
                                    },
                                    'data_segment_name': '$data_segments.data_segment_name',
                                    'segment_type': '$data_segments.segment_type',
                                    'count_of_entities': '$data_segments.count_at_origin'
                                },
                                'else': None
                            }
                        }
                    }
                }
            }, {
                '$sort': {
                    'created_at': -1
                }
            }
        ]
        if not download:
            paginated_results = []
            if page_num and page_size:
                skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
                paginated_results.extend([{"$skip": skip}, {"$limit": limit}])
            pipeline.append(
                {
                    "$facet": {
                        "paginated_results": paginated_results,
                        "totalCount": [{"$count": "count"}],
                    }
                }
            )
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
            pipeline.insert(
                0,
                {
                    "$match": {
                        "duration.start_date": {"$gte": start_date},
                        "duration.end_date": {"$lte": end_date},
                    }
                },
            )
        result = (
            await DatabaseConfiguration()
            .promocode_collection.aggregate(pipeline)
            .to_list(None)
        )
        total = 0
        if not download:
            total = result[0].get("totalCount", [])
            total = total[0].get("count") if total else 0
            result = result[0].get("paginated_results", [])
        for doc in result:
            status = doc.get("status", "")
            start_date = doc.get("start_date")
            end_date = doc.get("end_date")
            now = datetime.datetime.utcnow()
            if doc.get("data_segment_ids", [])[0] is None:
                doc["data_segment_ids"] = []
            if not status or status == "Active":
                doc["status"] = (
                    "Active"
                    if (start_date < now < end_date)
                    else (
                        "Upcoming"
                        if (now < start_date)
                        else "Expired" if (now > end_date) else "Inactive"
                    )
                )
            doc.update(
                {
                    "start_date": utility_obj.get_local_time(start_date),
                    "end_date": utility_obj.get_local_time(end_date),
                    "estimated_cost": round(doc.get("estimated_cost", 0), 2),
                }
            )
        return result, total

    async def check_and_update_duration(
        self, duration: dict | None, update_info: dict, data: dict
    ) -> dict:
        """
        Check the conditions and update duration if valid else raise error
        Params:
            - duration (dict): It has start_date, end_date in it.
            - update_info (dict): The dict in which the data is to be updated.
            - data (dict): The current data in database.
        Returns:
            - dict : Updated dict to update database info
        """
        start_date = duration.get("start_date", None)
        end_date = duration.get("end_date", None)
        if start_date:
            start_date, start_date_ = await utility_obj.date_change_format(
                start_date, start_date
            )
            start_date = start_date.replace(tzinfo=None)
            if (
                f"{start_date}"[:10]
                != f"{data.get('duration', {}).get('start_date')}"[:10]
            ):
                if (
                    data.get("duration", {}).get("start_date")
                    < datetime.datetime.utcnow()
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="Start date cannot be changed as it is already "
                        "started!",
                    )
                if end_date is None:
                    if start_date > data.get("duration", {}).get("end_date"):
                        raise HTTPException(
                            status_code=400,
                            detail="Start date cannot be after end date",
                        )
                if start_date < datetime.datetime.utcnow():
                    raise HTTPException(
                        status_code=400,
                        detail="Start date cannot be earlier than today!",
                    )
            update_info.update({"duration.start_date": start_date})
        if end_date:
            end_date, end_date = await utility_obj.date_change_format(
                end_date, end_date
            )
            end_date = end_date.replace(tzinfo=None)
            if end_date < datetime.datetime.utcnow():
                raise HTTPException(
                    status_code=400, detail="End date cannot be earlier than today!"
                )
            if start_date is None:
                if end_date < data.get("duration", {}).get("start_date"):
                    raise HTTPException(
                        status_code=400, detail="End date cannot be before start date"
                    )
            update_info.update({"duration.end_date": end_date})
        return update_info

    async def update_upcoming_promocode(
        self,
        data: dict,
        units: int | None,
        name: str | None,
        code: str | None,
        discount: int | None,
    ) -> dict:
        """
        update upcoming promocode with given values
        Params:
            - data (dict): The Current data in the database regarding promocode.
            - units (int): The units to be changed for promocode.
            - name (str): The name of promocode that is to be changed.
            - code (str): The code of promocode that is to be changed.
            - discount (int): The discount to be changed for promocode.
        Returns:
            - update_info (dict): The updated dict
        """
        update_info = {}
        now = datetime.datetime.utcnow()
        if now < data.get("duration", {}).get("start_date"):
            if units:
                update_info.update({"units": units})
            if name:
                update_info.update({"name": name})
            if code:
                if (
                    await DatabaseConfiguration().promocode_collection.find_one(
                        {"code": code}
                    )
                    is not None
                ):
                    raise HTTPException(
                        detail="Promo code already exists.", status_code=400
                    )
                update_info.update({"code": code})
            if discount:
                update_info.update({"discount": discount})
        else:
            if units:
                applied = data.get("applied_count", 0)
                if applied > units:
                    raise HTTPException(
                        status_code=400,
                        detail="Units cannot be less than applied count",
                    )
                update_info.update({"units": units})
        return update_info

    async def update_edit_promocode(self, _id: str, payload: dict | None):
        """
        Update or edit promocode.
        Params:
            - id (str): Unique id of promocode that is to be updated.
            - payload (dict): This can have fields like status, status_value, duration,
                - status (bool): True if user wants to change the status false if user wants to change duration.
                - status_value (str): This can have two values Inactive/Active.
                - duration (dict): Has start_date and/or end_date as per conditions.
                - units (int): Given if need to change units field.
                - data_segments (list): List of datasegment ids that are to be added.
                - name (str): Given if required to change the name of promocode.
                - code (str): Given if required to chnage the code of promocode.
                - discount (int): Given if required to change the discount field.
        Returns: None
        Raises:
            - DataNotFoundError: This error is raised when data is not found in database regarding given id.
            - ConditionMismatch error: There are multiple cases where the update process cannot be changed. In those cases error is raised
        """
        try:
            await utility_obj.is_id_length_valid(_id=_id, name="Promocode id")
            _id = ObjectId(_id)
            if (
                data := await DatabaseConfiguration().promocode_collection.find_one(
                    {"_id": _id}
                )
            ) is None:
                raise DataNotFoundError(_id, "Promocode")
            units, name, code, discount, duration, data_segments = (
                payload.get("units", None),
                payload.get("name", None),
                payload.get("code", None),
                payload.get("discount", None),
                payload.get("duration", None),
                payload.get("data_segments", None),
            )
            if payload.get("status", False):
                await DatabaseConfiguration().promocode_collection.update_one(
                    {"_id": _id}, {"$set": {"status": payload.get("status_value")}}
                )
            else:
                update_info = await self.update_upcoming_promocode(
                    data, units, name, code, discount
                )
                if duration:
                    update_info = await self.check_and_update_duration(
                        duration, update_info, data
                    )
                if data_segments:
                    data_segments = [ObjectId(id) for id in data_segments]
                    update_info.update({"data_segment_ids": data_segments})
                if update_info:
                    await DatabaseConfiguration().promocode_collection.update_one(
                        {"_id": _id}, {"$set": update_info}
                    )
        except DataNotFoundError as e:
            logger.error(f"{e.message}")
            raise HTTPException(status_code=404, detail=e.message)

    async def get_applied_students(
        self,
        promocode_id: str,
        page_num: int,
        page_size: int,
        program_name: list | None,
        search: str | None,
    ) -> tuple:
        """
        Returns all students information who applied the given promocode id
        params:
            - promocode_id (str): Unique id of promocode.
            - page_num (int): Page num required.
            - page_size (int): Page size required.
            - program_name (list): List of dicts that has course, specialization details.
            - search (str): The search string if required.
        Returns:
            tuple - result (list of applied students)
                  - total (total count of result)
        Raises:
            - DATANOTFOUNDError - This is raised when the promoocode id is not found in database
        """
        try:
            await utility_obj.is_id_length_valid(_id=promocode_id, name="Promocode id")
            promocode_id = ObjectId(promocode_id)
            if (
                await DatabaseConfiguration().promocode_collection.find_one(
                    {"_id": promocode_id}
                )
            ) is None:
                raise DataNotFoundError(promocode_id, "Promocode")
            skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
            pipeline = [
                {"$unwind": {"path": "$applied_by"}},
                {"$match": {"_id": promocode_id}},
                {
                    "$lookup": {
                        "from": "studentsPrimaryDetails",
                        "let": {"student_id": "$applied_by.student_id"},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$_id", "$$student_id"]}}},
                            {
                                "$project": {
                                    "_id": 1,
                                    "user_name": 1,
                                    "basic_details": 1,
                                }
                            },
                        ],
                        "as": "student_details",
                    }
                },
                {
                    "$unwind": {
                        "path": "$student_details",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "application_id": {"$toString": "$applied_by.application_id"},
                        "student_id": {"$toString": "$applied_by.student_id"},
                        "custom_application_id": "$applied_by.custom_application_id",
                        "course_name": "$applied_by.course_name",
                        "spec_name": "$applied_by.spec_name",
                        "student_name": {
                            "$trim": {
                                "input": {
                                    "$concat": [
                                        "$student_details.basic_details.first_name",
                                        " ",
                                        "$student_details.basic_details.middle_name",
                                        " ",
                                        "$student_details.basic_details.last_name",
                                    ]
                                }
                            }
                        },
                    }
                },
                {
                    "$facet": {
                        "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                        "totalCount": [{"$count": "count"}],
                    }
                },
            ]
            if program_name:
                program_filter = [
                    {
                        "applied_by.course_id": ObjectId(program.get("course_id")),
                        "applied_by.spec_name": program.get("course_specialization"),
                    }
                    for program in program_name
                ]
                pipeline[1].get("$match").update({"$or": program_filter})
            if search:
                name_pattern = f".*{search}.*"
                pipeline.insert(
                    4,
                    {
                        "$match": {
                            "$or": [
                                {
                                    "student_details.basic_details.first_name": {
                                        "$regex": name_pattern,
                                        "$options": "i",
                                    }
                                },
                                {
                                    "student_details.basic_details.last_name": {
                                        "$regex": name_pattern,
                                        "$options": "i",
                                    }
                                },
                                {
                                    "student_details.basic_details.middle_name": {
                                        "$regex": name_pattern,
                                        "$options": "i",
                                    }
                                },
                                {
                                    "student_details.user_name": {
                                        "$regex": name_pattern,
                                        "$options": "i",
                                    }
                                },
                            ]
                        }
                    },
                )
            result = (
                await DatabaseConfiguration()
                .promocode_collection.aggregate(pipeline)
                .to_list(None)
            )
            total = result[0].get("totalCount", [])
            total = total[0].get("count") if total else 0
            result = result[0].get("paginated_results", [])
            return result, total
        except DataNotFoundError as e:
            logger.error(f"{e.message}")
            raise HTTPException(status_code=404, detail=e.message)

    async def generate_voucher_codes(self):
        """
        Generate multiple voucher codes
        Params:
            None
        Return:
            - str (unique voucher code)
        """
        generated_uuid = uuid.uuid4()
        hex_string = str(generated_uuid).replace("-", "")
        random_number = random.randint(1, 20)
        hex_string = hex_string[random_number : random_number + 10]
        return hex_string

    async def create_voucher(self, payload: dict, user: dict):
        """
        Create voucher
        Params:
            - payload (dict): Payload contains all fields that are to be inserted in the database regarding voucher
                              It has fields like name, quantity, cost_of_voucher, assign_to, duration, e.t.c.
            - user (dict): Details of current user
        Returns (dict): A dict that has message of successful creation of promocode
        Raises:
            - Exception: An error occurred when something wrong happen in the code.
        """
        duration = payload.get("duration", {})
        duration["start_date"], duration["end_date"] = (
            await utility_obj.date_change_format(
                duration.get("start_date"), duration.get("end_date")
            )
        )
        assign_to = ObjectId(payload.get("assign_to"))
        assignee = await DatabaseConfiguration().user_collection.find_one(
            {"_id": assign_to}
        )
        payload["assign_to"] = {
            "assign_to_id": assignee.get("_id"),
            "assign_to_name": utility_obj.name_can(assignee),
        }
        payload.update(
            {
                "created_at": datetime.datetime.utcnow(),
                "created_by_id": ObjectId(user.get("_id")),
                "created_by_name": utility_obj.name_can(user),
                "applied_count": 0,
            }
        )
        for program in payload.get("program_name"):
            course_id = program.get("course_id")
            course = await DatabaseConfiguration().course_collection.find_one(
                {"_id": ObjectId(course_id)}
            )
            program.update(
                {
                    "course_id": ObjectId(course_id),
                    "course_name": course.get("course_name"),
                }
            )
        payload["vouchers"] = []
        for _ in range(payload.get("quantity")):
            code = await self.generate_voucher_codes()
            payload["vouchers"].append({"code": code, "used": False})
        await DatabaseConfiguration().voucher_collection.insert_one(payload)

    async def get_all_vouchers(
        self,
        page_num: int,
        page_size: int,
        date_range: dict | None,
        program_name: list | None,
        publisher: ObjectId | None,
        download: bool,
    ):
        """
        Get all vouchers
        Params:
            - page_num (int): required page_num
            - page_size (int): required page_size
            - date_range (DateRange): Date Range filter, It has values start date and end date
            - program_name (list): List of dicts. It has fields course_id, course_specialization
            - publisher (ObjectId): publisher id to filter accordingly
            - download (bool): True if want to download the results else false
        Returns:
            - tuple : result - list of all vouchers
                      total  - total count of vouchers
        """
        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
        pipeline = [
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "name": 1,
                    "assign_to": "$assign_to.assign_to_name",
                    "assign_id": {"$toString": "$assign_to.assign_to_id"},
                    "cost_per_voucher": "$cost_per_voucher",
                    "start_date": "$duration.start_date",
                    "end_date": "$duration.end_date",
                    "program_name": {
                        "$map": {
                            "input": "$program_name",
                            "in": {
                                "course_id": {"$toString": "$$this.course_id"},
                                "course_name": "$$this.course_name",
                                "spec_name": "$$this.spec_name",
                            },
                        }
                    },
                    "used": "$applied_count",
                    "created": "$quantity",
                    "assigned_date": "$created_at",
                    "status": 1,
                }
            },
            {"$sort": {"assigned_date": -1}},
        ]
        if not download:
            pipeline.append(
                {
                    "$facet": {
                        "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                        "totalCount": [{"$count": "count"}],
                    }
                }
            )
        match_stage = {}
        if publisher:
            match_stage.update({"assign_to.assign_to_id": publisher})
        if program_name:
            program_filter = [
                {
                    "course_id": ObjectId(program.get("course_id")),
                    "spec_name": program.get("course_specialization"),
                }
                for program in program_name
            ]
            match_stage.update(
                {"program_name": {"$elemMatch": {"$or": program_filter}}}
            )
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
            match_stage.update(
                {
                    "duration.start_date": {"$gte": start_date},
                    "duration.end_date": {"$lte": end_date},
                }
            )
        if match_stage:
            pipeline.insert(0, {"$match": match_stage})
        result = (
            await DatabaseConfiguration()
            .voucher_collection.aggregate(pipeline)
            .to_list(None)
        )
        total = 0
        if not download:
            total = result[0].get("totalCount", [])
            total = total[0].get("count") if total else 0
            result = result[0].get("paginated_results", [])
        for doc in result:
            start_date = doc.get("start_date")
            end_date = doc.get("end_date")
            now = datetime.datetime.utcnow()
            status = doc.get("status", "")
            doc.update(
                {
                    "start_date": utility_obj.get_local_time(start_date),
                    "end_date": utility_obj.get_local_time(end_date),
                    "assigned_date": utility_obj.get_local_time(
                        doc.get("assigned_date")
                    ),
                }
            )
            if not status or status == "Active":
                doc["status"] = (
                    "Active"
                    if (start_date < now < end_date)
                    else (
                        "Upcoming"
                        if (now < start_date)
                        else "Expired" if (now > end_date) else "Inactive"
                    )
                )
        return result, total

    async def update_upcoming_voucher(
        self,
        data: dict | None,
        name: str | None,
        quantity: int | None,
        cost_per_voucher: int | None,
        duration: dict | None,
        program_name: list | None,
        assign_to: str | None,
    ):
        """
        update upcoming vouchers
        Params:
            - data (dict): The present details of given voucher.
            - name (str): The name to be changed.
            - quantity (str): The quantity to be changed.
            - cost_per_voucher (int): The cost per voucher to be changed.
            - duration (dict): It has start date and end date to be changed.
            - program_name (list): List of dict that has course_id, spec_name in it
            - assign_to (str): The unique id of publisher assigned to
        Returns:
            - update_info (dict): The updated dict
        """
        update_info = {}
        if program_name:
            for program in program_name:
                course_id = program.get("course_id")
                course = await DatabaseConfiguration().course_collection.find_one(
                    {"_id": ObjectId(course_id)}
                )
                program.update(
                    {
                        "course_id": ObjectId(course_id),
                        "course_name": course.get("course_name"),
                    }
                )
            update_info.update({"program_name": program_name})
        if name:
            update_info.update({"name": name})
        if quantity:
            present_quantity = data.get("quantity")
            if present_quantity >= quantity:
                update_info.update(
                    {"quantity": quantity, "vouchers": data.get("vouchers")[:quantity]}
                )
            else:
                extra = quantity - present_quantity
                vouchers = data.get("vouchers")
                for _ in range(extra):
                    code = await self.generate_voucher_codes()
                    vouchers.append({"code": code, "used": False})
                update_info.update({"quantity": quantity, "vouchers": vouchers})
        if cost_per_voucher:
            update_info.update({"cost_per_voucher": cost_per_voucher})
        if duration:
            duration["start_date"], duration["end_date"] = (
                await utility_obj.date_change_format(
                    duration.get("start_date"), duration.get("end_date")
                )
            )
            if duration["start_date"].replace(tzinfo=None) < datetime.datetime.utcnow():
                raise HTTPException(
                    status_code=400, detail="Start date cannot be earlier than today!"
                )
            update_info.update({"duration": duration})
        if assign_to:
            assign_to = ObjectId(assign_to)
            assignee = await DatabaseConfiguration().user_collection.find_one(
                {"_id": assign_to}
            )
            update_info.update(
                {
                    "assign_to": {
                        "assign_to_id": assignee.get("_id"),
                        "assign_to_name": utility_obj.name_can(assignee),
                    }
                }
            )
        return update_info

    async def update_voucher(self, voucher_id: str, payload: dict):
        """
        Update the voucher
        Params:
            - voucher_id (str): The unique id of voucher
            - payload (dict): The details to be updated regarding voucher
        Return:
            None
        """
        try:
            await utility_obj.is_id_length_valid(_id=voucher_id, name="Voucher id")
            voucher_id = ObjectId(voucher_id)
            if (
                data := await DatabaseConfiguration().voucher_collection.find_one(
                    {"_id": voucher_id}
                )
            ) is None:
                raise DataNotFoundError(voucher_id, "Voucher")
            name, quantity, cost_per_voucher, duration, program_name, assign_to = (
                payload.get("name", None),
                payload.get("quantity", None),
                payload.get("cost_per_voucher", None),
                payload.get("duration", None),
                payload.get("program_name", None),
                payload.get("assign_to"),
            )
            if payload.get("status", False):
                await DatabaseConfiguration().voucher_collection.update_one(
                    {"_id": voucher_id},
                    {"$set": {"status": payload.get("status_value")}},
                )
            else:
                now = datetime.datetime.utcnow()
                update_info = {}
                if now < data.get("duration", {}).get("start_date"):
                    update_info = await self.update_upcoming_voucher(
                        data,
                        name,
                        quantity,
                        cost_per_voucher,
                        duration,
                        program_name,
                        assign_to,
                    )
                else:
                    if duration:
                        update_info = await self.check_and_update_duration(
                            duration, update_info, data
                        )
                if update_info:
                    await DatabaseConfiguration().voucher_collection.update_one(
                        {"_id": voucher_id}, {"$set": update_info}
                    )
        except DataNotFoundError as e:
            logger.error(f"{e.message}")
            raise HTTPException(status_code=404, detail=e.message)

    async def get_voucher_details(
        self,
        voucher_id: str,
        page_num: int,
        page_size: int,
        sort: bool | None,
        sort_name: str | None,
        sort_type: str | None,
    ):
        """
        Get all details of given voucher
        Params:
            - voucher_id (str): The unique id of voucher
            - page_num (int): The page number for pagination purpose
            - page_size (int): The page size for pagination purpose
            - sort (bool): True if need to sort else False
            - sort_name (str): This can have two values name/status
            - sort_type (str): This can have two values asc/dsc
        Returns:
            - Tuple : result - List of voucher details
                      total  - total no. of voucher codes
        """
        try:
            await utility_obj.is_id_length_valid(_id=voucher_id, name="Voucher id")
            voucher_id = ObjectId(voucher_id)
            if (
                await DatabaseConfiguration().voucher_collection.find_one(
                    {"_id": voucher_id}
                )
            ) is None:
                raise DataNotFoundError(voucher_id, "Voucher")
            skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
            pipeline = [
                {"$match": {"_id": voucher_id}},
                {"$unwind": {"path": "$vouchers"}},
                {
                    "$lookup": {
                        "from": "studentsPrimaryDetails",
                        "let": {"student_id": "$vouchers.used_by.student_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": ["$_id", "$$student_id"],
                                    },
                                },
                            },
                            {
                                "$project": {
                                    "_id": 1,
                                    "user_name": 1,
                                    "basic_details": 1,
                                },
                            },
                        ],
                        "as": "student_details",
                    }
                },
                {
                    "$unwind": {
                        "path": "$student_details",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "code": "$vouchers.code",
                        "status": {
                            "$cond": {
                                "if": {
                                    "$eq": ["$vouchers.used", True],
                                },
                                "then": "used",
                                "else": "unused",
                            },
                        },
                        "student_id": {
                            "$ifNull": [
                                {
                                    "$toString": "$vouchers.used_by.student_id",
                                },
                                "NA",
                            ],
                        },
                        "application_id": {
                            "$ifNull": [
                                {
                                    "$toString": "$vouchers.used_by.application_id",
                                },
                                "NA",
                            ],
                        },
                        "custom_application_id": {
                            "$ifNull": [
                                "$vouchers.used_by.custom_application_id",
                                "NA",
                            ],
                        },
                        "student_name": {
                            "$ifNull": [
                                {
                                    "$trim": {
                                        "input": {
                                            "$concat": [
                                                "$student_details.basic_details.first_name",
                                                " ",
                                                "$student_details.basic_details.middle_name",
                                                " ",
                                                "$student_details.basic_details.last_name",
                                            ],
                                        },
                                    },
                                },
                                "NA",
                            ],
                        },
                    }
                },
                {
                    "$facet": {
                        "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                        "totalCount": [{"$count": "count"}],
                    }
                },
            ]
            if sort:
                pipeline.insert(
                    5, {"$sort": {sort_name: 1 if sort_type in [None, "asc"] else -1}}
                )
            result = (
                await DatabaseConfiguration()
                .voucher_collection.aggregate(pipeline)
                .to_list(None)
            )
            total = result[0].get("totalCount", [])
            total = total[0].get("count") if total else 0
            result = result[0].get("paginated_results", [])
            return result, total
        except DataNotFoundError as e:
            logger.error(f"{e.message}")
            raise HTTPException(status_code=404, detail=e.message)

    async def quick_view_result(self, start_date, end_date):
        """
        Get quick view results
        Params:
            - start_date : Start date in date range filter
            - end_date: End date in date range filter
        Returns:
            - dict : Concatenation of both promocode and voucher details.

        """
        promocode_pipeline = [
            {
                '$addFields': {
                    'multi': {
                        '$map': {
                            'input': '$applied_by',
                            'as': 'item',
                            'in': {
                                '$multiply': [
                                    '$$item.course_fee', {
                                        '$divide': [
                                            '$discount', 100
                                        ]
                                    }
                                ]
                            }
                        }
                    },
                    'unused': {
                        '$subtract': [
                            '$units', '$applied_count'
                        ]
                    }
                }
            }, {
                '$addFields': {
                    'total_multi': {
                        '$sum': '$multi'
                    }
                }
            }, {
                '$group': {
                    '_id': None,
                    'unused_promocode': {
                        '$sum': {
                            '$subtract': [
                                '$units', '$applied_count'
                            ]
                        }
                    },
                    'total_promocode_applied': {
                        '$sum': '$applied_count'
                    },
                    'estimated_promocode_cost': {
                        '$sum': '$total_multi'
                    }
                }
            }
        ]
        voucher_pipeline = [
            {
                "$facet": {
                    "grouped_results": [
                        {
                            "$group": {
                                "_id": None,
                                "total_voucher_applied": {
                                    "$sum": {"$ifNull": ["$applied_count", 0]}
                                },
                                "unused_vouchers": {
                                    "$sum": {
                                        "$subtract": [
                                            {"$ifNull": ["$quantity", 0]},
                                            {"$ifNull": ["$applied_count", 0]},
                                        ]
                                    }
                                },
                                "estimated_voucher_cost": {
                                    "$sum": {
                                        "$multiply": [
                                            {"$ifNull": ["$applied_count", 0]},
                                            {"$ifNull": ["$cost_per_voucher", 0]},
                                        ]
                                    }
                                },
                            }
                        }
                    ]
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total_voucher_applied": {
                        "$ifNull": [
                            {
                                "$arrayElemAt": [
                                    "$grouped_results.total_voucher_applied",
                                    0,
                                ]
                            },
                            0,
                        ]
                    },
                    "unused_vouchers": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$grouped_results.unused_vouchers", 0]},
                            0,
                        ]
                    },
                    "estimated_voucher_cost": {
                        "$ifNull": [
                            {
                                "$arrayElemAt": [
                                    "$grouped_results.estimated_voucher_cost",
                                    0,
                                ]
                            },
                            0,
                        ]
                    },
                }
            },
        ]
        if start_date and end_date:
            match = {
                "$match": {
                    "duration.start_date": {"$gte": start_date},
                    "duration.end_date": {"$lte": end_date},
                }
            }
            promocode_pipeline.insert(0, match)
            voucher_pipeline.insert(0, match)
        promocode = (
            await DatabaseConfiguration()
            .promocode_collection.aggregate(promocode_pipeline)
            .to_list(None)
        )
        result = promocode[0] if promocode else {}
        voucher = (
            await DatabaseConfiguration()
            .voucher_collection.aggregate(voucher_pipeline)
            .to_list(None)
        )
        result.update(voucher[0] if voucher else {})
        result.update(
            {
                "total_applied": result.get("total_promocode_applied", 0)
                + result.get("total_voucher_applied", 0)
            }
        )
        return result

    async def get_quick_view(
        self, date_range: dict | None, change_indicator: str | None
    ):
        """
        Get quick view details
        Params:
            - date_range (dict): The date range filter if required. This has start_date and end_date in it
            - change_indicator (str): The change indicator value
            - unused (str): This can have two values promocode/voucher
        Returns:
            - dict : All details along with change indicator values

        """
        start_date, end_date = None, None
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
        result = await self.quick_view_result(start_date, end_date)
        if change_indicator:
            start_date, middle_date, previous_date = (
                await utility_obj.get_start_date_and_end_date_by_change_indicator(
                    change_indicator
                )
            )
            previous_start_date, previous_end_date = (
                await utility_obj.date_change_format(str(start_date), str(middle_date))
            )
            prev_result = await self.quick_view_result(
                previous_start_date, previous_end_date
            )
            current_start_date, current_end_date = await utility_obj.date_change_format(
                str(previous_date), str(datetime.date.today())
            )
            curr_result = await self.quick_view_result(
                current_start_date, current_end_date
            )
            total_applied = await utility_obj.get_percentage_difference_with_position(
                prev_result.get("total_applied", 0), curr_result.get("total_applied", 0)
            )
            promocode_cost = await utility_obj.get_percentage_difference_with_position(
                prev_result.get("estimated_promocode_cost", 0),
                curr_result.get("estimated_promocode_cost", 0),
            )
            voucher_cost = await utility_obj.get_percentage_difference_with_position(
                prev_result.get("estimated_voucher_cost", 0),
                curr_result.get("estimated_voucher_cost", 0),
            )
            result.update(
                {
                    "total_applied_perc": total_applied.get("percentage"),
                    "total_applied_position": total_applied.get("position"),
                    "estimated_promocode_cost_perc": promocode_cost.get("percentage"),
                    "estimated_promocode_cost_position": promocode_cost.get("position"),
                    "estimated_voucher_cost_perc": voucher_cost.get("percentage"),
                    "estimated_voucher_cost_position": voucher_cost.get("position"),
                }
            )
        return result

    async def verify_promocode_voucher(
        self, code: str, course_fee: int, application_id: str, preference_fee: int = None
    ) -> dict:
        """
        Verify promocode and voucher.

        Params:
            - code (str): The code which is to be cross-checked
            - course_fee (int): The course fee of particular course
            - application_id (str): The unique id of application
            - preference_fee (int): The 1st preference fee on which promocode should be applied

        Returns:
            - dict (details of given code. It has status, discount, code, amount)
        """
        application_id = ObjectId(application_id)
        now = datetime.datetime.utcnow()
        pipeline = [
            {
                "$match": {
                    "code": code,
                    "status": {"$ne": "Inactive"},
                    "$expr": {"$lt": ["$applied_count", "$units"]},
                }
            }
        ]
        code_doc = (
            await DatabaseConfiguration()
            .promocode_collection.aggregate(pipeline)
            .to_list(None)
        )
        code_doc = code_doc[0] if code_doc else {}
        if code_doc:
            duration = code_doc.get("duration")
            if duration.get("start_date") <= now <= duration.get("end_date"):
                data_segments = code_doc.get("data_segment_ids", [])
                discount = code_doc.get("discount")
                if preference_fee:
                    amount = preference_fee - (preference_fee * (discount/100))
                    amount += (course_fee - preference_fee)
                else:
                    amount = course_fee - (course_fee * (discount / 100))
                if data_segments:
                    for segment_id in data_segments:
                        if (
                            await DatabaseConfiguration().data_segment_mapping_collection.find_one(
                                {
                                    "data_segment_id": ObjectId(segment_id),
                                    "application_id": application_id,
                                }
                            )
                        ) is not None:
                            return {
                                "type": "promocode",
                                "discount": discount,
                                "status": "Applied Successfully",
                                "amount": amount,
                                "code": code,
                                "application_id": str(application_id),
                            }
                    return {"status": "Not Applicable"}
                else:
                    return {
                        "type": "promocode",
                        "discount": discount,
                        "status": "Applied Successfully",
                        "amount": amount,
                        "code": code,
                        "application_id": str(application_id),
                    }
            else:
                return {"status": "Invalid"}
        else:
            pipeline = [
                {"$unwind": {"path": "$vouchers"}},
                {
                    "$match": {
                        "vouchers.code": code,
                        "vouchers.used": False,
                        "status": {"$ne": "Inactive"},
                    }
                },
            ]
            code_doc = (
                await DatabaseConfiguration()
                .voucher_collection.aggregate(pipeline)
                .to_list(None)
            )
            code_doc = code_doc[0] if code_doc else {}
            if code_doc:
                duration = code_doc.get("duration")
                if duration.get("start_date") <= now <= duration.get("end_date"):
                    program_name = code_doc.get("program_name")
                    program_filter = []
                    for program in program_name:
                        program_filter.append(
                            {
                                "course_id": program.get("course_id"),
                                "spec_name1": program.get("spec_name"),
                            }
                        )
                    pipeline = [{"$match": {"_id": application_id}}]
                    if program_filter:
                        pipeline[0].get("$match", {}).update({"$or": program_filter})
                    application = await (
                        DatabaseConfiguration().studentApplicationForms.aggregate(
                            pipeline
                        )
                    ).to_list(
                        None
                    )
                    application = application[0] if application else {}
                    if application:
                        return {
                            "type": "voucher",
                            "discount": VOUCHER_DISCOUNT,
                            "status": "Applied Successfully",
                            "amount": 0,
                            "code": code,
                            "application_id": str(application_id),
                        }
                    else:
                        return {"status": "Not Applicable"}

                else:
                    return {"status": "Invalid"}
        return {"status": "Invalid"}

    async def update_promocode_usage(self, promocode, application_id, course, course_fee):
        """
        Update promocode usage
        Params:
            - promocode (str): The unique code that is being used
            - application_id (str): The unique id of application
            - course (dict): The details of course
            - course_fee (int): The course fee on which promocode is applied.
        Returns: None
        Raises:\n
        - Exception: An error occurred with status code 500 when something happen wrong backend code while updating promocode usage.
        """
        if (
            application := await DatabaseConfiguration().studentApplicationForms.find_one(
                {"_id": ObjectId(application_id)}
            )
        ) is not None:
            await DatabaseConfiguration().promocode_collection.update_one(
                {"code": promocode},
                {
                    "$push": {
                        "applied_by": {
                            "student_id": application.get("student_id"),
                            "application_id": ObjectId(application_id),
                            "custom_application_id": application.get(
                                "custom_application_id"
                            ),
                            "course_id": application.get("course_id"),
                            "spec_name": application.get("spec_name1"),
                            "course_name": course.get("course_name"),
                            "course_fee": course_fee
                        }
                    },
                    "$inc": {"applied_count": 1},
                },
            )

    async def payment_through_code(
        self,
        application_id: str,
        code: str,
        student: dict,
        college: dict,
        testing: bool,
        code_type: str,
        payment_device: str | None,
        device_os: str | None,
        course_fee: int | None
    ):
        """
        Payment through code.
        Params:
            - application_id (str): The unique id of application
            - voucher_code (str): The code which is to be applied
            - student (dict): The details of student
            - college (dict): The details of college
            - code_type (str): This can have two values (promocode/voucher)

        Returns:
            - dict : Message that code is added
        Raises:
            - Exception: An error occurred with status code 500 when something happen wrong backend code while applying voucher code.
        """
        await utility_obj.is_id_length_valid(_id=application_id, name="Application id")
        if code_type.lower() == "promocode":
            promocode_validation = await self.verify_promocode_voucher(
                code, 0, application_id
            )
            status = promocode_validation.get("status")
            if status in ["Invalid", "Not Applicable"]:
                raise HTTPException(status_code=404, detail=f"Promocode is {status}")
        payment_info = {
            "status": "captured",
            "created_at": datetime.datetime.utcnow(),
            "payment_device": payment_device,
            "device_os": device_os,
        }
        promocode_update = {
            "payment_method": "Promocode",
            "used_promocode": code,
            "paid_amount": 0,
        }
        voucher_update = {"payment_method": "Voucher", "used_voucher": code}
        try:
            if (
                application := await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"_id": ObjectId(application_id)}
                )
            ) is None:
                raise DataNotFoundError(message="Application")
            payment_collection_doc = {
                "payment_id": "None",
                "order_id": "None",
                "user_id": application.get("student_id"),
                "details": {
                    "purpose": "StudentApplication",
                    "application_id": ObjectId(application_id),
                },
                "status": "captured",
                "attempt_time": datetime.datetime.utcnow(),
                "captured_at": datetime.datetime.utcnow(),
            }
            course = await DatabaseConfiguration().course_collection.find_one(
                {"_id": application.get("course_id")}
            )
            if code_type == "voucher":
                filter_criteria = {
                    "vouchers": {"$elemMatch": {"code": code, "used": False}}
                }
                if (
                    await DatabaseConfiguration().voucher_collection.find_one(
                        filter_criteria
                    )
                ) is None:
                    raise DataNotFoundError(message="Voucher")
                await DatabaseConfiguration().voucher_collection.update_one(
                    filter_criteria,
                    {
                        "$set": {
                            "vouchers.$.used": True,
                            "vouchers.$.used_by": {
                                "student_id": application.get("student_id"),
                                "application_id": application.get("_id"),
                                "custom_application_id": application.get(
                                    "custom_application_id"
                                ),
                            },
                        },
                        "$inc": {"applied_count": 1},
                    },
                )
                payment_info.update(voucher_update)
                payment_collection_doc.update(voucher_update)
            else:
                await self.update_promocode_usage(
                    code, application_id, course, course_fee)
                payment_info.update(promocode_update)
                payment_collection_doc.update(promocode_update)
            await DatabaseConfiguration().studentApplicationForms.update_one(
                {"_id": ObjectId(application_id)},
                {"$set": {"payment_info": payment_info, "payment_initiated": True}},
            )
            await DatabaseConfiguration().payment_collection.insert_one(
                payment_collection_doc
            )
            await StudentApplicationHelper().update_stage(
                application.get("student_id"), course.get("course_name"),
                7.50, application.get("spec_name1"), college_id=str(application.get("college_id"))
            )
            await utility_obj.update_notification_db(
                event="Payment captured", application_id=application_id
            )
            await cache_invalidation(
                api_updated="student_application/update_payment_status"
            )
            if not testing:
                basic_details = student.get("basic_details", {})
                await EmailActivity().payment_successful(
                    data={
                        "payment_status": "success",
                        "created_at": datetime.datetime.utcnow(),
                        "order_id": "None",
                        "payment_id": "None",
                        "student_name": utility_obj.name_can(basic_details),
                        "student_id": str(student.get("_id")),
                        "student_email_id": basic_details.get("email"),
                        "student_mobile_no": basic_details.get("mobile_number"),
                        "application_number": application.get("custom_application_id"),
                        "degree": f"{course.get('course_name')} in "
                        f"{application.get('spec_name1')}",
                        "college_name": college.get("name"),
                        "nationality": basic_details.get("nationality"),
                        "application_fees": (
                            course.get("fees") if code_type != "promocode" else "Rs.0/-"
                        ),
                        "student_first_name": basic_details.get("first_name", {}),
                    },
                    event_type="email",
                    event_status="sent",
                    event_name=f"Application "
                    f"({course.get('course_name')} in "
                    f"{application.get('spec_name1')}) "
                    f"payment successful",
                    email_preferences=college.get("email_preferences", {}),
                    college=college,
                )
            try:
                # TODO: Not able to add student timeline data
                #  using celery task when environment is
                #  demo. We'll remove the condition when
                #  celery work fine.
                if settings.environment in ["demo"]:
                    StudentActivity().student_timeline(
                        student_id=str(application.get("student_id")),
                        event_type="Payment",
                        event_status="Done",
                        event_name=(
                            f"{course.get('course_name')} in {application.get('spec_name1')}"
                            if (
                                application.get("spec_name1") != ""
                                and application.get("spec_name1")
                            )
                            else f"{course.get('course_name')} Program"
                        ),
                        college_id=str(application.get("college_id")),
                    )
                else:
                    if not is_testing_env():
                        StudentActivity().student_timeline.delay(
                            student_id=str(application.get("student_id")),
                            event_type="Payment",
                            event_status="Done",
                            event_name=(
                                f"{course.get('course_name')} in {application.get('spec_name1')}"
                                if (
                                    application.get("spec_name1") != ""
                                    and application.get("spec_name1")
                                )
                                else f"{course.get('course_name')} Program"
                            ),
                            college_id=str(application.get("college_id")),
                        )
            except KombuError as celery_error:
                logger.error(f"error storing time line data " f"{celery_error}")
            except Exception as error:
                logger.error(f"error storing time line data " f"{error}")
        except DataNotFoundError as e:
            logger.error(f"{e.message}")
            raise HTTPException(status_code=404, detail=e.message)
        except Exception as error:
            logger.error(
                f"Some error occurred while applying the voucher code: {error}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Some error occurred while applying the voucher code: {error}",
            )


promocode_vouchers_obj = PromocodeVouchers()
