import asyncio
import datetime
import json
from json import dumps

import aio_pika
import redis
from bson import ObjectId
from fastapi import HTTPException
from fastapi.websockets import WebSocket, WebSocketState
from starlette import status

from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.database.configuration import DatabaseConfiguration
from app.database.database_sync import DatabaseConfigurationSync
from app.dependencies.jwttoken import Authentication
from app.dependencies.oauth import get_redis_client, get_sync_redis_client

logger = get_logger(name=__name__)


class WebhookHelper:
    """
    Contain helper functions related to status Webhook
    """

    async def get_websocket_information(self, websocket: WebSocket):
        """
        Fetch information from websocket. Converts websocket information into usable pythin dict
        Params:
            - websocket (WebSocket): The details sent by frontend
        Returns:
            - data (dict): The details in websocket
        Raises:
            - Exception: An error occurred when something wrong happen in the code.
        """
        try:
            data = await websocket.receive_text()
            if data is not None:
                data = json.loads(data)
                return data
            return None
        except Exception as e:
            logger.error(
                f"Something went wrong while fetching information from websocket: {e}"
            )

    async def get_student_details(self, data: dict):
        """
        Get student details with the help of token sent in data

        Params:
            - data (dict): The data sent by frontend which has values student token, student status

        Return:
            - student_details (dict) : the details of student extracted from  token
        """
        try:
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
            access_token = data.get("access_token")
            await Authentication().verify_token(
                access_token, credentials_exception, websocket=True
            )
            token_details = await Authentication().get_token_details(
                access_token, credentials_exception
            )
            if (
                user := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"user_name": token_details.get("sub")}
                )
            ) is None:
                user = {}
            if not user:
                logger.error(f"Student not found")
                return None
            return user
        except Exception as e:
            logger.error(f"Something went wrong. {e}")

    async def update_database(self, student_id, student_status):
        """
        Updates the database with login and logout activity of student

        Params:
            - student_id (str): The unique id of student
            - student_status (str): The status of student. This may have values offline/online

        Returns:
            None

        Raises:
            - Exception: An error occurred when something wrong happen in the code.
        """
        if (
            student_login_activity := await DatabaseConfiguration().studentLoginActivity.find_one(
                {"student_id": ObjectId(student_id)}
            )
        ) is None:
            login_details = [{}]
            if student_status == "online":
                login_details[0].update({"login": datetime.datetime.utcnow()})
            if student_status == "offline":
                login_details[0].update({"logout": datetime.datetime.utcnow()})
            await DatabaseConfiguration().studentLoginActivity.insert_one(
                {"student_id": ObjectId(student_id), "login_details": login_details}
            )
        else:
            if student_status == "online":
                update_operation = {
                    "$push": {"login_details": {"login": datetime.datetime.utcnow()}}
                }
                await DatabaseConfiguration().studentLoginActivity.update_one(
                    {"student_id": ObjectId(student_id)}, update_operation
                )
            elif student_status == "offline":
                last_index = len(student_login_activity.get("login_details", [])) - 1
                student_login_activity["login_details"][last_index][
                    "logout"
                ] = datetime.datetime.utcnow()
                await DatabaseConfiguration().studentLoginActivity.replace_one(
                    {"student_id": ObjectId(student_id)}, student_login_activity
                )

    async def update_data_in_redis(self, data, student_status):
        """
        update the data in redis database

        Params:
            - data (dict): The details of student.
            - student_status (str): The student_status of the student. This may have values offline/online

        Returns:
            - None

        Raises:
            - Exception: An error occurred when something wrong happen in the code.
        """
        try:
            key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/students_online"
            r = get_sync_redis_client()
            with r.pipeline() as pipe:
                while True:
                    try:
                        pipe.watch(key)
                        pipe.multi()
                        if student_status == "online":
                            pipe.rpush(key, json.dumps(data))
                        elif student_status == "offline":
                            pipe.lrem(key, 1, json.dumps(data))
                        pipe.execute()
                        break
                    except redis.WatchError as e:
                        logger.error(f"While storing data in cache got error: {e}")
                        break
                    except redis.TimeoutError as e:
                        logger.error(f"Timeout while storing data in cache: {e}")
                        break
                    except Exception as e:
                        logger.error(f"Some internal error occurred: {e}")
                        break
        except Exception as error:
            logger.error(f"An error occurred while storing the data in redis: {error} ")

    async def student_status_update(self, student_status, student_info):
        """
        This function updates the student student_status in database and redis server

        Params:
            - student_student_status (str): The student_status of student. This may have values offline/online
            - student_info (dict): The details of student
        """
        try:
            user_name = student_info.get("user_name")
            pipeline = [
                {"$match": {"student_id": student_info.get("_id")}},
                {
                    "$lookup": {
                        "from": "courses",
                        "localField": "course_id",
                        "foreignField": "_id",
                        "as": "course",
                    }
                },
                {"$unwind": {"path": "$course"}},
                {
                    "$project": {
                        "_id": 0,
                        "application_id": {"$toString": "$_id"},
                        "application_name": {
                            "$concat": [
                                "$course.course_name",
                                {
                                    "$cond": [
                                        {"$eq": ["$spec_name1", None]},
                                        "",
                                        {
                                            "$cond": [
                                                {
                                                    "$in": [
                                                        "$course.course_name",
                                                        ["Master", "Bachelor"],
                                                    ]
                                                },
                                                {"$concat": [" of ", "$spec_name1"]},
                                                {"$concat": [" in ", "$spec_name1"]},
                                            ]
                                        },
                                    ]
                                },
                            ]
                        },
                    }
                },
            ]
            application = []
            application_doc = await (
                DatabaseConfiguration().studentApplicationForms.aggregate(pipeline)
            ).to_list(
                None
            )
            for app in application_doc:
                application.append(app)
            data = {
                "email": user_name,
                "name": utility_obj.name_can(student_info.get("basic_details", {})),
                "student_id": str(student_info.get("_id")),
                "applications": application,
            }
            await self.update_data_in_redis(data, student_status)
            connection = await utility_obj.get_rabbitMQ_connection_channel()
            async with connection:
                channel = await connection.channel()
                key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/students_online"
                message_body = "Data published"
                exchange = await channel.declare_exchange(key, aio_pika.ExchangeType.FANOUT,
                                                          durable=True)
                await exchange.publish(aio_pika.Message(body=message_body.encode()), routing_key="")
                await channel.close()
            await connection.close()
        except Exception as error:
            logger.error(
                f"An error occurred while processing the student student_status update: {error}"
            )

    async def get_students_online(self, user):
        """
        This returns all the students online
        Params:
            user : present user details
        Returns:
            list
        Raises:
            - Exception: An error occurred when something wrong happen in the code.
        """
        try:
            r = get_sync_redis_client()
            key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/students_online"
            students_online = r.lrange(key, 0, -1)
            role_name = user.get("role", {}).get("role_name")
            students_online = [
                json.loads(element.decode("utf-8")) for element in students_online
            ]
            students_online = list({d["email"]: d for d in students_online}.values())
            user_names = None
            if role_name == "college_counselor":
                counselor_id = [ObjectId(user.get("_id"))]
                user_names = (
                    DatabaseConfigurationSync().studentsPrimaryDetails.distinct(
                        "user_name",
                        {"allocate_to_counselor.counselor_id": {"$in": counselor_id}},
                    )
                )
            elif role_name == "college_head_counselor":
                counselor_detail = list(DatabaseConfigurationSync(
                    database="master"
                ).user_collection.find({"head_counselor_id": ObjectId(user.get("_id"))}))
                counselor_id = [
                    ObjectId(counselor.get("_id"))
                     for counselor in counselor_detail
                ]
                user_names = (
                    DatabaseConfigurationSync().studentsPrimaryDetails.distinct(
                        "user_name",
                        {"allocate_to_counselor.counselor_id": {"$in": counselor_id}},
                    )
                )

            if user_names:
                students_online = [
                    student
                    for student in students_online
                    if student["email"] in user_names
                ]
            else:
                if role_name == "college_counselor":
                    return {
                        "live_students_count": 0,
                        "live_student_list": [],
                    }
            students_online = {
                "live_students_count": len(students_online),
                "live_student_list": students_online,
            }
            return students_online
        except ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            return []
        except Exception as error:
            logger.error(f"An error occurred while fetching students online: {error}")
            return []

    async def get_notifications(self, user, websocket_con):
        """
        This returns all real time notifications
        Params:
            r : redis client to make redis operations
            user : details of user
        Returns:
            None
        Raises:
            - Exception: An error occurred when something wrong happen in the code.
        """
        try:
            r = get_sync_redis_client()
            key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/{str(user.get('_id'))}_notifications"
            notifications = r.lrange(key, 0, -1)
            r.expire(key, 10)
            for notification in notifications:
                notification = json.loads(notification)
                current_datetime = datetime.datetime.utcnow()
                event_datetime = datetime.datetime.strptime(
                    notification.get("event_datetime"), "%Y-%m-%d %H:%M:%S.%f"
                )
                hours = abs(
                    int(
                        (datetime.datetime.utcnow() - event_datetime).total_seconds()
                        // 3600
                    )
                )
                if utility_obj.local_time_for_compare(
                    current_datetime.strftime("%d-%m-%Y %H:%M:%S")
                ).strftime("%d-%m-%Y") == utility_obj.local_time_for_compare(
                    current_datetime.strftime("%d-%m-%Y %H:%M:%S")
                ).strftime(
                    "%d-%m-%Y"
                ):
                    event_datetime = f"{hours} hours ago"
                    category = "today"
                else:
                    yesterday = str(
                        datetime.date.today() - datetime.timedelta(days=1)
                    ).split(" ")
                    days = abs(
                        (
                            utility_obj.local_time_for_compare(
                                current_datetime.strftime("%d-%m-%Y %H:%M:%S")
                            )
                            - utility_obj.local_time_for_compare(
                                event_datetime.strftime("%d-%m-%Y %H:%M:%S")
                            )
                        ).days
                    )
                    if yesterday[0] == utility_obj.local_time_for_compare(
                        event_datetime.strftime("%d-%m-%Y %H:%M:%S")
                    ).strftime("%Y-%m-%d"):
                        if hours < 24:
                            event_datetime = f"{hours} hours ago"
                        else:
                            event_datetime = f"{days} day ago"
                        category = "yesterday"
                    else:
                        event_datetime = f"{days} days ago"
                        category = "older"
                temp_result = {
                    "notification_id": notification.get("_id"),
                    "event_type": notification.get("event_type"),
                    "student_id": notification.get("student_id"),
                    "application_id": notification.get("application_id"),
                    "message": notification.get("message"),
                    "mark_as_read": notification.get("mark_as_read"),
                    "event_datetime": event_datetime,
                    "category": category,
                }
                await websocket_con.send_text(dumps(temp_result))
        except ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
        except Exception as error:
            logger.error(f"An error occurred while fetching students online: {error}")

    async def live_applicants(self, websocket_con, user):
        """
        Sends live applicants count via websocket.

        Params:
            - websocket_con (Websocket): The websocket connection object to perform websocket operations.
            - user (dict): A dictionary which contains user data.

        Returns:
            - None but send live applicants count via websocket.

        Raises:
            - Exception: An error occurred when something wrong happen in the code.
        """
        try:
            result = await self.get_students_online(user=user)
            if websocket_con.client_state == WebSocketState.CONNECTED:
                await websocket_con.send_text(dumps(result))
        except Exception as error:
            logger.error(f"some exception while sending websocket.send_text: {error}")

    def run_async_function_in_thread(self, websocket_con, user):
        """
        create a loop to run async function in thread

        Params:
            - websocket_con (obj): The websocket connection object to perform websocket operations
            - user (dict): The user details dict

        Returns:
            None

        Raises:
            - Exception: An error occurred when something wrong happen in the code.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.live_applicants(websocket_con, user))
            else:
                loop.run_until_complete(self.live_applicants(websocket_con, user))
        except Exception as error:
            logger.error(
                f"An error occurred while creating loop to call async live applicants function: {error}"
            )

    async def live_notifications(self, websocket_con, user):
        """
        Sends live notifications via websocket
        Params:
            - websocket_con (obj): The websocket connection object to perform websocket operations
            - user (dict): The details of user
        Returns:
            - None
            - sends message to websocket
        Raises:
            - Exception: An error occurred when something wrong happen in the code.
        """
        await webhook_helper.get_notifications(
            user=user, websocket_con=websocket_con
        )

    def run_async_thread_for_notifications(self, websocket_con, user):
        """
        create a loop to run async function in thread for notifications

        Params:
            - websocket_con (obj): The websocket connection object to perform websocket operations
            - user (dict): The user details dict

        Returns:
            None

        Raises:
            - Exception: An error occurred when something wrong happen in the code.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.live_notifications(websocket_con, user))
            else:
                loop.run_until_complete(self.live_notifications(websocket_con, user))
        except Exception as error:
            logger.error(
                f"An error occurred while creating loop to call async notification function: {error}"
            )


webhook_helper = WebhookHelper()
