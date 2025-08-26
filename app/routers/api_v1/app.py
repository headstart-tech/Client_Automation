"""
This file contains instantiation of application
"""
import csv
import json
import logging
import os
import tracemalloc
from json import dumps
from sys import platform
import datetime
import asyncio
import aio_pika
import boto3
import redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, Security
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocket, WebSocketDisconnect
from app.celery_tasks.celery_add_user_audit_logs import UserAuditTrail
from app.core.log_config import get_logger
from app.core.log_file_handler import logs as Log
from app.core.middleware import AuditAndHeaderMiddleware
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, settings
from app.database.configuration import app as database_connection
from app.database.motor_base import client, init_databases, pgsql_conn
from app.database.motor_base_singleton import MotorBaseSingleton
from app.dependencies.college import get_college_id
from app.dependencies.oauth import (
    get_current_user_object,
    get_redis_client,
    delete_keys_matching_pattern,
    get_sync_redis_client
)
from app.dependencies.security_auth import get_current_username
from app.helpers.notification.real_time_configuration import Notification
from app.helpers.telephony.call_popup_websocket import manager
from app.helpers.user_curd.role_configuration import RoleHelper
from app.helpers.webhook_helper.student_status_webhook_helper import \
    webhook_helper
from app.models.role_schema import Role
from app.routers.api_v1.routes.admin_dashboard_geographical_map_data_routes import (
    map_router as MapRouter,
)
from app.routers.api_v1.routes.admin_routes import admin as Admin
from app.routers.api_v1.routes.advance_filter_routes import \
    advance_filter_router
from app.routers.api_v1.routes.application_routes import application_wrapper
from app.routers.api_v1.routes.authentication_routes import oauth2
from app.routers.api_v1.routes.automation_routes import automation_router
from app.routers.api_v1.routes.call_activity_routes import (
    call_activities as CallActivityRouter,
)
from app.routers.api_v1.routes.campaign_routes import campaign_router
from app.routers.api_v1.routes.checkin_checkout_routes import checkinout_router
from app.routers.api_v1.routes.client_automation import client_router
from app.routers.api_v1.routes.client_student_dashboard_routes import client_router as client_student_router
from app.routers.api_v1.routes.colleges_routes import \
    college_router as CollegeRouter
from app.routers.api_v1.routes.communication_performance_routes import communication_performance
from app.routers.api_v1.routes.communication_summary_routes import \
    communication
from app.routers.api_v1.routes.counselor_router import \
    counselor as CounselorRouter
from app.routers.api_v1.routes.countries_states_cities_routes import (
    country_router as CountryRouter,
)
from app.routers.api_v1.routes.courses_routes import \
    course_router as CourseRouter
from app.routers.api_v1.routes.data_segment_router import data_segment_router
from app.routers.api_v1.routes.document_verification_routes import document_verification
from app.routers.api_v1.routes.email_routes import email_router
from app.routers.api_v1.routes.event_routes import event_router
from app.routers.api_v1.routes.exclusion_list_routes import router as exclusion_list
from app.routers.api_v1.routes.followup_notes_routes import (
    followup_notes_router as FollowupNotesRouter,
)
from app.routers.api_v1.routes.interview_list_router import interview_list
from app.routers.api_v1.routes.interview_module_routes import interview_module
from app.routers.api_v1.routes.lead_user_router import lead as leadRouter
from app.routers.api_v1.routes.manage_router import manage
from app.routers.api_v1.routes.master_routes import master_router
from app.routers.api_v1.routes.nested_automation_routes import \
    nested_automation_router
from app.routers.api_v1.routes.notification_routes import (
    notification as NotificationRouter,
)
from app.routers.api_v1.routes.payment_gateway_routes import (
    payment_router as PaymentRouter,
)
from app.routers.api_v1.routes.planner_routes import planner_module
from app.routers.api_v1.routes.promocode_vouchers_routes import \
    promocode_vouchers
from app.routers.api_v1.routes.publisher_dashboard_routes import (
    publisher_router as PublisherRouter,
)
from app.routers.api_v1.routes.qa_manager_routes import qa_manager_router
from app.routers.api_v1.routes.query_categories_routes import (
    query_category_router as QueryCategoriesRouter,
)
from app.routers.api_v1.routes.query_routes import \
    queries_router as QueryRouter
from app.routers.api_v1.routes.report_routes import \
    report_router as ReportRouter
from app.routers.api_v1.routes.resource_routes import resource_router
from app.routers.api_v1.routes.role_permissions import router as rbac_router
from app.routers.api_v1.routes.sms_activity_routes import \
    sms_router as SMSRouter
from app.routers.api_v1.routes.student_application_routes import (
    application_router as StudentApplicationRouter,
)
from app.routers.api_v1.routes.student_email_routers import (
    email_router as StudentEmailRouter,
)
from app.routers.api_v1.routes.student_profile_call_logs_routes import (
    call_log_router as CallLogRouter,
)
from app.routers.api_v1.routes.student_profile_communication_log_routes import (
    communication_router as CommunicationLogRouter,
)
from app.routers.api_v1.routes.student_query_routes import (
    query_router as StudentQueryRouter,
)
from app.routers.api_v1.routes.student_timeline_routes import (
    timeline_router as TimelineRouter,
)
from app.routers.api_v1.routes.student_user_curd_routes import (
    router as StudentUserCurdRouter,
)
from app.routers.api_v1.routes.students_routes import router as StudentRouter
from app.routers.api_v1.routes.super_admin import \
    super_router as SuperAdminRouter
from app.routers.api_v1.routes.tawk_routes import tawk_webhook_routers
from app.routers.api_v1.routes.telephony_routes import telephony
from app.routers.api_v1.routes.template_routes import \
    template_router as TemplateRouter
from app.routers.api_v1.routes.text_extraction_routes import ExtractionRouter
from app.routers.api_v1.routes.unsubcribe_automation_routes import unsubscribe
from app.routers.api_v1.routes.users_curd_routes import user_router as Users
from app.routers.api_v1.routes.whatsapp_routes import whatsapp_router
from app.routers.api_v1.routes.approval_route import approval_router
from app.routers.api_v1.routes.role_permissions import router as rbac_router
from app.routers.api_v1.routes.client_curd_routes import client_crud_router
from app.routers.api_v1.routes.account_manager import account_manager_router
from app.routers.api_v1.routes.scholarship_routes import scholarship_router
from app.routers.api_v1.routes.super_account_manager_routes import super_account_manager_router

logger = get_logger(
    name=__name__,
    filename="logs/GTCRM-Debug.log",
    when="midnight",
    interval=3,
    backup_count=3,
)

scheduler = AsyncIOScheduler()


async def store_user_audit_data():
    """
    Asynchronous function to store user audit data with error handling.

    This function executes asynchronously using the `await` keyword.
    It attempts to fetch and store user audit data using the `fetch_and_store`
    method of the `utility_obj`. If an exception occurs during execution, it
    captures the exception and assigns it to the `message` variable. Finally,
    it prints the `message`.
    """
    try:
        message = await utility_obj.fetch_and_store()
    except Exception as e:
        message = e
    logger.debug(message)

async def cache_roles_permissions ():
    """
    Calls `cache_roles_and_permissions` to fetch roles and permissions from PostgreSQL and store
    them in Redis. Logs the response or error.
    """
    try:
        response = await utility_obj.cache_roles_and_permissions()
        logger.debug(response.get("message", ""))
    except Exception as e:
        logger.error(f"Error while caching roles and permissions: {e}")



async def upload_and_remove_old_user_audits():
    """
    Remove user audit records older than seven days from the database.

    This asynchronous function calculates the date seven days ago from the current UTC time and deletes all records in
    the 'user_audit_details' that have a 'timestamp' earlier than that date. The function logs a message indicating
    whether the deletion was successful or if an error occurred.

    Returns:
        - None
    """
    from app.database.configuration import DatabaseConfiguration
    seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    file_path = (seven_days_ago - datetime.timedelta(days=1)).strftime("%Y-%m-%d")+".csv"
    try:
        base_bucket = settings.aws_user_audit_bucket
        path = f"{settings.reports_bucket_name}/audit_trail_data/{file_path}"
        pipe = [{"$match": {"timestamp": {"$lt": seven_days_ago}}}]
        data = await DatabaseConfiguration().user_audit_collection.aggregate(pipe).to_list(None)
        if data:
            with open(file_path, mode="w", newline="", encoding="utf-8") as file:
                csv_writer = csv.DictWriter(file, fieldnames=data[0].keys())
                csv_writer.writeheader()
                csv_writer.writerows(data)
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.reports_access_key_id,
                aws_secret_access_key=settings.reports_secret_access_key,
                region_name=settings.reports_region_name,
            )
            try:
                with open(file_path, "rb") as f:
                    s3_client.upload_fileobj(f, base_bucket, path)
            except Exception as e:
                logger.error(f"Some error occurred while uploading file to S3: {e}")
            else:
                await DatabaseConfiguration().user_audit_collection.delete_many(
                    {"timestamp": {"$lt": seven_days_ago}}
                )
            os.remove(file_path)
        message = "File uploaded successfully to S3 and deleted audit data i.e. older than 7 days."
    except Exception as error:
        message = f"An error got while uploading the old user audit details. Error - {error}"
    logger.debug(message)


async def read_and_publish_to_rabbitmq(file_name):
    """
    Reads JSON log entries from 'local_logs.log' and publishes them to RabbitMQ.

    Args:
        file_name (str): The name of the log file to process.

    This function:
    1. Reads the log file.
    2. Decodes each line as JSON and publishes it to RabbitMQ.
    3. Logs errors for JSON decoding issues and other exceptions.
    4. Clears the log file after processing.

    Logs an error if the file does not exist.
    """
    queue_mapping = {
        "local_logs.log": "user_audit_queue",
        "rbac_activity_logs.log": "role_permission_logs"
    }
    parent_dir = os.path.dirname(os.getcwd())
    file_path = os.path.join(parent_dir, file_name)
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        with open(file_path, 'w') as f:
            for line in lines:
                try:
                    log_entry = json.loads(line.strip())
                    queue_name = queue_mapping.get(file_name, "user_audit_queue")
                    await utility_obj.publish_to_rabbitmq(log_entry, queue_name)
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON from log file: {e}")
                except Exception as e:
                    logger.error(f"An unexpected error occurred: {e}")
        logger.info(f"Sent messages to RabbitMQ")
    except FileNotFoundError:
        logger.error(f"'{file_name}' doesn't exist!")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


async def Consume_from_rabbitmq(queue_name: str):
    """
    Trigger the Celery task to consume from RabbitMQ for a specific queue.

    Args:
        queue_name (str): The RabbitMQ queue name to consume from.
    """
    try:
        UserAuditTrail().add_user_audit_logs.delay(queue_name)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


async def restore_ip_addresses_into_redis():
    """
    Restore IP addresses into Redis from the database.

    This asynchronous function attempts to restore IP addresses into a Redis
    datastore by calling the `update_ip_addresses_in_redis` method of the
    `utility_obj`. If the operation is successful, it logs a success message.
    If an exception occurs during the process, it catches the exception and
    logs the error message.

    The function performs the following steps:
    1. Attempts to update IP addresses in Redis.
    2. If an exception occurs, it catches and logs the exception message.
    3. If the operation is successful, it logs a success message.
    """
    try:
        await utility_obj.update_ip_addresses_in_redis()
    except Exception as e:
        message = e
    else:
        message = "Ip-addresses restored successfully"
    logger.info(message)


def log_memory_usage():
    # Stop tracemalloc tracing and get a snapshot of the memory usage
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")

    # Group the stats by filename
    grouped_stats = {}
    for stat in top_stats:
        key = stat.traceback[0].filename
        if key not in grouped_stats:
            grouped_stats[key] = stat.size
        else:
            grouped_stats[key] += stat.size

    # Sort the stats by memory usage and write them to a file
    sorted_stats = sorted(grouped_stats.items(), key=lambda x: x[1], reverse=True)
    with open("memory_stats.txt", "w") as f:
        f.write("[ Top 10 memory consuming files ]\n")
        for stat in sorted_stats[:10]:
            f.write(f"{stat[0]}: {stat[1]} bytes\n")

    # Print the top 10 memory consuming files
    print("[ Top 10 memory consuming files ]")
    for stat in sorted_stats[:10]:
        print(f"{stat[0]}: {stat[1]} bytes")


def get_fastapi_app() -> FastAPI:
    fast_app_api = FastAPI(**settings.fastapi_kwargs)
    testing_env = utility_obj.read_current_toml_file().get("testing", {}).get("test")
    if testing_env is not True and settings.environment != "demo":
        fast_app_api.add_middleware(AuditAndHeaderMiddleware)

    fast_app_api.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_origin_regex="https://.*\.azurewebsites.net",
        allow_credentials=True,
        allow_methods=["POST", "GET", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    fast_app_api.include_router(Users, tags=["User"], prefix="/user")

    fast_app_api.include_router(
        Log,
        tags=["Log"],
        prefix="/logs",
    )

    fast_app_api.include_router(CourseRouter, tags=["Course"], prefix="/course")

    fast_app_api.include_router(CollegeRouter, tags=["College"], prefix="/college")

    fast_app_api.include_router(
        StudentRouter,
        tags=["Student"],
        prefix="/student",
        dependencies=[Security(get_current_user_object, scopes=["student"])],
    )

    fast_app_api.include_router(
        StudentUserCurdRouter,
        tags=["Student User CRUD"],
        prefix="/student_user_crud",
    )

    fast_app_api.include_router(
        StudentApplicationRouter,
        tags=["Student Application"],
        prefix="/student_application"
    )

    fast_app_api.include_router(
        StudentQueryRouter,
        tags=["Student Query"],
        prefix="/student_query",
        dependencies=[Security(get_current_user_object, scopes=["student"])],
    )

    fast_app_api.include_router(Admin, tags=["Admin"], prefix="/admin")

    fast_app_api.include_router(leadRouter, tags=["Admin Lead"], prefix="/lead")

    fast_app_api.include_router(CountryRouter, tags=["Country"], prefix="/countries")

    fast_app_api.include_router(
        application_wrapper, tags=["Application"], prefix="/application_wrapper"
    )

    # Student and User Authentication
    fast_app_api.include_router(router=oauth2, tags=["Authentication"], prefix="/oauth")

    fast_app_api.include_router(
        router=StudentEmailRouter, tags=["Student Email"], prefix="/student/email"
    )

    fast_app_api.include_router(
        router=PaymentRouter, tags=["Payment Gateway"], prefix="/payments"
    )

    fast_app_api.include_router(router=MapRouter, tags=["Map"], prefix="/map_data")

    fast_app_api.include_router(
        router=CounselorRouter, tags=["Counselor Admin"], prefix="/counselor"
    )

    fast_app_api.include_router(
        router=client_router, tags=["Client Automation"], prefix="/client_automation"
    )

    fast_app_api.include_router(
        router=TimelineRouter,
        tags=["Student Timeline"],
        prefix="/student_timeline",
    )

    fast_app_api.include_router(
        router=manage,
        tags=["Manage Lead"],
        prefix="/manage",
    )

    fast_app_api.include_router(
        router=CommunicationLogRouter,
        tags=["Student Communication Log"],
        prefix="/student_communication_log",
    )

    fast_app_api.include_router(
        router=CallLogRouter,
        tags=["Student Call Log"],
        prefix="/student_call_log",
    )

    fast_app_api.include_router(
        router=QueryCategoriesRouter,
        tags=["Query Categories"],
        prefix="/create_query_categories",
    )

    fast_app_api.include_router(router=QueryRouter, tags=["Query"], prefix="/query")

    fast_app_api.include_router(
        router=FollowupNotesRouter,
        tags=["Followup and Notes"],
        prefix="/followup_notes",
    )

    fast_app_api.include_router(
        SuperAdminRouter,
        tags=["Super Admin"],
        prefix="/super_admin",
        dependencies=[Security(get_current_user_object, scopes=["super_admin"])],
    )

    fast_app_api.include_router(
        PublisherRouter,
        tags=["Publisher"],
        prefix="/publisher",
        dependencies=[Security(get_current_user_object, scopes=["college_publisher_console"])],
    )

    fast_app_api.include_router(TemplateRouter, tags=["Template"], prefix="/templates")

    fast_app_api.include_router(
        database_connection, tags=["check Database Connection"], prefix="/check"
    )
    fast_app_api.include_router(
        ExtractionRouter,
        tags=["Student Document Text Extraction"],
        prefix="/student/documents",
    )

    fast_app_api.include_router(ReportRouter, tags=["Report"], prefix="/reports")

    fast_app_api.include_router(SMSRouter, tags=["SMS Router"], prefix="/sms")

    fast_app_api.include_router(
        NotificationRouter, tags=["Notification"], prefix="/notifications"
    )

    fast_app_api.include_router(
        CallActivityRouter, tags=["Call Activity"], prefix="/call_activities"
    )

    fast_app_api.include_router(
        automation_router, tags=["Automation"], prefix="/automation"
    )

    fast_app_api.include_router(
        nested_automation_router,
        tags=["Nested Automation"],
        prefix="/nested_automation",
    )

    fast_app_api.include_router(campaign_router, tags=["Campaign"], prefix="/campaign")

    fast_app_api.include_router(
        data_segment_router, tags=["Data Segment"], prefix="/data_segment"
    )

    fast_app_api.include_router(email_router, tags=["Email"], prefix="/email")

    fast_app_api.include_router(whatsapp_router, tags=["Whatsapp"], prefix="/whatsapp")

    fast_app_api.include_router(event_router, tags=["Event"], prefix="/event")

    fast_app_api.include_router(
        interview_module, tags=["Interview Module"], prefix="/interview"
    )

    fast_app_api.include_router(
        interview_list, tags=["Interview List"], prefix="/interview_list"
    )

    fast_app_api.include_router(
        planner_module, tags=["Planner Module"], prefix="/planner"
    )

    fast_app_api.include_router(
        master_router, tags=["Master Module"], prefix="/master"
    )

    fast_app_api.include_router(resource_router, tags=["Resource"], prefix="/resource")

    (
        fast_app_api.include_router(
            qa_manager_router, tags=["QA Manager"], prefix="/qa_manager"
        ),
    )

    fast_app_api.include_router(
        advance_filter_router, tags=["Advance Filter"], prefix="/advance_filter"
    )

    fast_app_api.include_router(
        unsubscribe, tags=["Unsubscribe"], prefix="/unsubscribe"
    )

    fast_app_api.include_router(
        tawk_webhook_routers, tags=["Tawk Chat Bot"], prefix="/tawk"
    )

    fast_app_api.include_router(
        telephony, tags=["Telephony Integration"], prefix="/telephony"
    )

    fast_app_api.include_router(
        communication, tags=["Communication Summary"], prefix="/communication"
    )

    fast_app_api.include_router(
        communication_performance, tags=["Communication Performance"], prefix="/communication_performance"
    )

    fast_app_api.include_router(
        exclusion_list, tags=["Exclusion List"], prefix="/exclusion_list"
    )

    fast_app_api.include_router(
        checkinout_router, tags=["CheckIn Check Out"], prefix="/checkin_checkout"
    )
    fast_app_api.include_router(
        client_student_router, tags=["Client Student Dashboard"], prefix="/client_student_dashboard"
    )

    fast_app_api.include_router(
        master_router, tags=["Master Stages"], prefix="/master_stages"
    )

    fast_app_api.include_router(
        promocode_vouchers, tags=["Promocode Vouchers"], prefix="/promocode_vouchers"
    )

    fast_app_api.include_router(
        document_verification, tags=["Document Verification"], prefix="/document_verification"
    )

    fast_app_api.include_router(
        approval_router, tags=["Approval"], prefix="/approval"
    )

    fast_app_api.include_router(rbac_router, tags=["Roles and Permissions"], prefix="/role_permissions")

    fast_app_api.include_router(
        client_crud_router, tags=["Client CRUD"], prefix="/client"
    )

    fast_app_api.include_router(
        account_manager_router, tags=["Account Manager"], prefix="/account_manager"
    )

    fast_app_api.include_router(
        super_account_manager_router, tags=["Super Account Manager"], prefix="/super_account_manager"
    )

    fast_app_api.include_router(scholarship_router, tags=["Scholarship"], prefix="/scholarship")

    return fast_app_api


app = get_fastapi_app()

scheduler.add_job(Consume_from_rabbitmq, 'interval', minutes=30, args=["user_audit_queue"])
scheduler.add_job(Consume_from_rabbitmq, 'interval', minutes=30, args=["role_permission_logs"])
scheduler.add_job(upload_and_remove_old_user_audits, 'interval', days=1)
scheduler.add_job(read_and_publish_to_rabbitmq, 'interval', hours=2, args=["local_logs.log"])
scheduler.add_job(read_and_publish_to_rabbitmq, 'interval', hours=2, args=["rbac_activity_logs.log"])
scheduler.add_job(store_user_audit_data, 'interval', hours=6)
scheduler.add_job(restore_ip_addresses_into_redis, 'interval', days=7)
scheduler.start()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """
    exception handler function for override inbuilt fastapi validation
    """
    error = exc.errors()[0]

    if error["type"] == "value_error":
        msg = error["msg"]
    else:
        # Default fallback formatting for field validation errors
        try:
            field_name = error["loc"][-1]
            if isinstance(field_name, int):
                msg = error.get("ctx", {}).get("error", "Some thing went Wrong!")
                msg = msg + " " + error.get("msg", "")
            else:
                msg = f"{str(field_name).title().replace('_', ' ')} must be required and valid."
        except Exception:
            msg = f"{error['loc'][0]} must be required and valid."

    return JSONResponse(
        status_code=400,
        content=jsonable_encoder({"detail": msg}),
    )


def init_log_setup():
    """
    Initialize logger to override uvicorn config
    """
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.setLevel(logger.level)  # Use the level from your logger
    uvicorn_logger.addHandler(logger)  # this will add all the handlers
    # from logger

    # Please don't delete this

    # Remove existing handlers from uvicorn_logger and add handlers from logger
    # uvicorn_logger.handlers = []
    # for handler in logger.handlers:
    #     uvicorn_logger.addHandler(handler)


# Call init_log_setup() after creating the logger
init_log_setup()


@app.on_event("startup")
async def startup():
    """
    create connection with database when app start
    """

    # Initialize Celery instance and check connection
    # app.state.celery = create_celery_app()
    #
    # try:
    #     conn = app.state.celery.connection()
    #     conn.ensure_connection(max_retries=5)
    #     logger.info("Connected to Redis successfully!")
    # except KombuError:
    #     logger.error("Failed to connect to Redis, please check" " your broker URL.")
    # except socket.gaierror:
    #     logger.error(
    #         "Unable to connect to Redis: Network is unreachable. "
    #         "Please check your network connection."
    #     )
    from app.dependencies.oauth import get_db
    tracemalloc.start()  # start memory profiling
    client.server_info()
    motor_base_singleton = MotorBaseSingleton.get_instance()
    motor_base_singleton.motor_base = await init_databases()
    message = "and 4 workers are running"
    if platform in ["linux", "linux2"]:
        message = "Skipping System Information for Faster boot time"
        # Uncomment below line for get system information
        # SystemInfo().system_information()
    elif platform == "win32":
        # Windows...
        message = "and workers disabled"
    async for _ in get_db():
        logger.info("PostgresSQL connection initialized on startup")
        break
    logger.info("Operating system = %s %s", platform, message)
    logger.info("Connected to Database.")
    # deleting the data in redis regarding students online
    await delete_keys_matching_pattern(["students_online"])
    # Commented below statement for check server performance
    # app.state.background_task = asyncio.create_task(Notification()
    #                                                 .send_notifications(None,
    #                                                                     None))


def close_clients(db_connection):
    if db_connection is not None:
        if isinstance(db_connection, dict):
            logger.info("Close all the season clients")
            for key, value in db_connection.items():
                if isinstance(value, dict):
                    for key2, value2 in value.items():
                        if "datetime" in key2.split("_"):
                            continue
                        value2.close()


@app.on_event("shutdown")
async def shutdown():
    """
    close connection with database when app shutdown
    """
    from app.database.motor_base import motor_base, client
    from app.database.database_sync import pymongo_base
    from app.database.master_db_connection import singleton_client
    from app.database.no_auth_connection_db import motor_base_no_auth
    singleton_client.close()
    if pymongo_base.client is not None:
        pymongo_base.client.close()
    db_connection = motor_base_no_auth.season_client
    close_clients(db_connection)
    db_connection = motor_base.season_db
    close_clients(db_connection)
    db_connection = pymongo_base.season_db
    close_clients(db_connection)
    if client is not None:
        client.close()
    client.close()
    redis_client = get_redis_client()
    if redis_client:
        await redis_client.close()
        logger.info("Connection with Redis is closed!")
    logger.info("connection to mongodb database has been closed.")
    await pgsql_conn.engine_generate.dispose()
    logger.info("PostgresSQL connection closed successfully")
    log_memory_usage()


@app.get("/")
async def read_root():
    """
    Returns the html content for Local Dev, and Development Server
    """
    if settings.environment == "development":
        html_content = """
        <html>
            <head>
                <title>GTCRM API</title>
            </head>
            <body>
                <h1>Authentication Ahead</h1>
                <p>Welcome to GTCRM API&nbsp;</p>
                <p>Please go through API Documentation here&nbsp;</p>
                <p><a href="http://127.0.0.1:8000/docs">Local Dev&nbsp;</a></p>
                <p><a href="https://dev.shiftboolean.com/docs">Development
                 Server&nbsp;</a></p>
                <p><a href="https://stage.shiftboolean.com/docs">Stage
                 Server&nbsp;</a></p>
            </body>
        </html>
        """
    else:
        html_content = """
            <html>
                <head>
                    <script src="https://unpkg.com/@lottiefiles/
                    lottie-player@latest/dist/lottie-player.js"></script>
                    <title>GTCRM API</title>
                    <style>
                        body, html {
                            height: 100%;
                            margin: 0;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            background: #FFFFFF;
                        }
                        lottie-player {
                            width: 100%;
                            height: 100%;
                        }
                    </style>
                </head>
                <body>
                    <lottie-player src="
                    https://lottie.host/5277f004-23b8-42db-98d0-
                    7844a178d066/c1wJ08XlhZ.json" loop autoplay direction="1"
                     mode="normal"></lottie-player>
                </body>
            </html>
            """
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/docs", include_in_schema=False)
async def get_swagger_documentation(_username: str = Depends(get_current_username)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


@app.get("/redoc", include_in_schema=False)
async def get_redoc_documentation(_username: str = Depends(get_current_username)):
    return get_redoc_html(openapi_url="/openapi.json", title="docs")


@app.get("/openapi.json", include_in_schema=False)
async def openapi(_username: str = Depends(get_current_username)):
    return get_openapi(title=app.title, version=app.version, routes=app.routes)


@app.post("/create_role/", tags=["Role"], deprecated=True)
async def create_role(role: Role):
    """
    Create Role\n
    * :*param* **role_name**: e.g. Test\n
    * :*return* **Message - New role created successfully.** if role
     successfully created in database:
    """
    role = jsonable_encoder(role)
    new_role = await RoleHelper().create_new_role(role)
    if new_role:
        return utility_obj.response_model(
            new_role, f"New role " f"created successfully."
        )


async def handle_message_telephony(message, websocket: WebSocket, key: str) -> None:
    """
    Process a RabbitMQ message and trigger the corresponding function to handle telephony events.

    Params:
        message (Message): The RabbitMQ message received from the queue.
        websocket (WebSocket): The WebSocket connection to send data back to the client.
        key (str): A unique identifier (usually the queue name) used to route the message to the correct function.

    Returns:
        None
    """
    async with message.process():
        manager.run_async_function_telephony(websocket, key)


async def consume_rabbitmq_messages_telephony(queue_name: str, websocket: WebSocket, channel):
    """
    Consumes RabbitMQ messages asynchronously from a specified queue and sends them to a WebSocket connection.

    Args:
        queue_name (str): The name of the RabbitMQ queue to consume messages from.
        websocket (WebSocket): The WebSocket connection where the messages will be sent.
        channel (RabbitMQ): The RabbitMQ channel

    Returns:
        None: This function is asynchronous and does not return any value.

    Raises:
        ConnectionError: If there is an issue with the RabbitMQ connection.
        WebSocketDisconnect: If the WebSocket connection is closed unexpectedly.
    """
    exchange = await channel.declare_exchange(queue_name, aio_pika.ExchangeType.FANOUT, durable=True)
    queue = await channel.declare_queue('', exclusive=True)
    await queue.bind(exchange)
    consumer_task = await queue.consume(lambda message: asyncio.create_task(handle_message_telephony(message, websocket,
                                                                                                     queue_name)))
    return queue, consumer_task


@app.websocket("/call_initiation_popup")
async def check_in_or_out(
    websocket: WebSocket,
    college: dict = Depends(get_college_id),
):
    """
    Create a websocket connection for call initiation popup

    Params:
        - websocket (WebSocket): Websocket connection instance.
        - college_id (str): An unique identifier of a college which useful for get college data.

    Returns:
        - dict: A dictionary which contains call initiate information.
    """
    try:
        logger.debug("Telephony websocket")
        Reset_the_settings().check_college_mapped(college.get("id"))
        Reset_the_settings().get_user_database(college.get("id"))
        user = await manager.connect(websocket, college)
        if user:
            key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/{user.get('_id')}_telephony"
            connection = await utility_obj.get_rabbitMQ_connection_channel()
            channel = await connection.channel()
            queue, consume_task = await consume_rabbitmq_messages_telephony(key, websocket, channel)
            try:
                while True:
                    try:
                        await websocket.receive_text()
                    except WebSocketDisconnect:
                        await queue.cancel(consume_task)
                        break
            finally:
                await queue.cancel(consume_task)
                await channel.close()
                await connection.close()
    except redis.exceptions.ConnectionError as error:
        logger.error(f"Some error occurred regarding redis connection. Error: {error}")
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as error:
        logger.error(f"Something went wrong in the websocket. Error - {error}")



@app.websocket("/ws/liveApplicant/{college_id}/")
async def update_student_status_websocket(websocket_info: WebSocket, college_id: str):
    """
    This websocket API will be called when the student enters/ exits the dashboard

    Params:
        - websocket : This has values sent by frontend. This will have values student token and status

    Returns:
        None

    Raises:
        - Exception: An error occurred when something wrong happen in the code.
    """
    try:
        logger.debug("Live Applicants Websocket")
        await websocket_info.accept()
        Reset_the_settings().check_college_mapped(college_id)
        Reset_the_settings().get_user_database(college_id)
        data = await webhook_helper.get_websocket_information(websocket_info)
        student_info = None
        if data:
            student_info = await webhook_helper.get_student_details(data)
            if student_info:
                await webhook_helper.student_status_update("online", student_info)
            else:
                logger.error(
                    "Student not found or error occurred during user retrieval."
                )
            counselor_details = student_info.get('allocate_to_counselor', {})

            await webhook_helper.get_counselor_status(websocket_info, counselor_details)
            redis_client = get_sync_redis_client()
            key = (f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/"
                   f"{str(counselor_details.get('counselor_id'))}/check_in_status")
            pubsub = redis_client.pubsub()
            pubsub.subscribe(
                **{
                    key: lambda message: webhook_helper.run_async_thread_for_counselor_status(
                        websocket_info, counselor_details, key
                    )
                }
            )
            thread = pubsub.run_in_thread(sleep_time=0.001, daemon=True)
        else:
            logger.error(f"No data is send via websocket")
        while True:
            try:
                await websocket_info.receive_text()
            except WebSocketDisconnect:
                if student_info:
                    await webhook_helper.student_status_update("offline", student_info)
                    thread.stop()
                else:
                    logger.error("Student info not found to mark it offline!")
                break
    except redis.exceptions.ConnectionError as error:
        logger.error(f"Some error occurred regarding redis connection. Error: {error}")
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"Something went wrong. {e}")


async def handle_message_students_live(message, websocket: WebSocket, user: dict) -> None:
    """
    Processes a single RabbitMQ message and sends the processed data to a WebSocket connection.

    Args:
        message (IncomingMessage): The RabbitMQ message received for processing.
        websocket (WebSocket): The WebSocket connection where the processed message will be sent.
        user (dict): The identifier of the user associated with the WebSocket connection.

    Returns:
        None: This function is asynchronous and does not return any value.

    Raises:
        WebSocketDisconnect: If the WebSocket connection is closed unexpectedly during message handling.
    """
    async with message.process():
        webhook_helper.run_async_function_in_thread(websocket, user)


async def consume_rabbitmq_messages_students_live(routing_key: str, websocket: WebSocket, user: dict, channel):
    """
    Consumes RabbitMQ messages asynchronously from the specified queue and processes each message
    for a live student session, sending the data to a WebSocket connection.

    Args:
        routing_key (str): The name of the RabbitMQ queue to consume messages from.
        websocket (WebSocket): The WebSocket connection where the messages will be sent.
        user (dict): The identifier of the user associated with the WebSocket connection.
        channel (RabbitMQ): The RabbitMQ channel

    Returns:
        None: This function is asynchronous and does not return any value.

    Raises:
        ConnectionError: If there is an issue with the RabbitMQ connection.
        WebSocketDisconnect: If the WebSocket connection is closed unexpectedly.
    """
    exchange = await channel.declare_exchange(routing_key, aio_pika.ExchangeType.FANOUT, durable=True)
    queue = await channel.declare_queue('', exclusive=True)
    await queue.bind(exchange)
    consumer_tag = await queue.consume(lambda message: asyncio.create_task(handle_message_students_live(message, websocket, user)))
    return (queue, consumer_tag)


@app.websocket("/ws/liveApplicants/{college_id}/")
async def get_student_status_websocket(websocket_con: WebSocket, college_id: str):
    """
    This websocket API will return the students online

    Params:
        - websocket : This has values sent by frontend. This will have values student token and status
        - college_id: The unique id of college

    Returns:
        - List : List of all students who are online

    Raises:
        - Exception: An error occurred when something wrong happen in the code.
    """
    try:
        logger.debug("Students online Websocket")
        await websocket_con.accept()
        Reset_the_settings().check_college_mapped(college_id)
        Reset_the_settings().get_user_database(college_id)
        key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/students_online"
        user = await Notification().get_user_details(websocket_con, college_id)
        if user:
            result = await webhook_helper.get_students_online(user=user)
            await websocket_con.send_text(dumps(result))
            connection = await utility_obj.get_rabbitMQ_connection_channel()
            channel = await connection.channel()
            queue, consume_task = await consume_rabbitmq_messages_students_live(key, websocket_con, user, channel)
            try:
                while True:
                    try:
                        await websocket_con.receive_text()
                    except WebSocketDisconnect:
                        await queue.cancel(consume_task)
                        break
            finally:
                await queue.cancel(consume_task)
                await channel.close()
                await connection.close()
        else:
            logger.info("User details not found")
    except redis.exceptions.ConnectionError as error:
        logger.error(f"Some error occurred regarding redis connection. Error: {error}")
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"Something went wrong. {e}")


async def handle_message_notifications(message, websocket: WebSocket, user: dict) -> None:
    """
    Processes a single RabbitMQ message related to notifications and sends the processed
    data to a WebSocket connection.

    Args:
        message: The RabbitMQ message received for processing.
        websocket (WebSocket): The WebSocket connection where the processed message will be sent.
        user (dict): The identifier of the user associated with the WebSocket connection.

    Returns:
        None: This function is asynchronous and does not return any value.

    Raises:
        WebSocketDisconnect: If the WebSocket connection is closed unexpectedly during message handling.
    """
    async with message.process():
        webhook_helper.run_async_thread_for_notifications(websocket, user)


async def consume_rabbitmq_messages_notifications(routing_key: str, websocket: WebSocket, user: dict, channel):
    """
    Consumes RabbitMQ messages asynchronously from a specified notifications queue
    and processes each message, sending the data to a WebSocket connection.

    Args:
        routing_key (str): The name of the RabbitMQ queue to consume notification messages from.
        websocket (WebSocket): The WebSocket connection where the messages will be sent.
        user (dict): The identifier of the user associated with the WebSocket connection.
        channel (RabbitMQ): The RabbitMQ channel

    Returns:
        None: This function is asynchronous and does not return any value.

    Raises:
        ConnectionError: If there is an issue with the RabbitMQ connection.
        WebSocketDisconnect: If the WebSocket connection is closed unexpectedly.
    """
    exchange = await channel.declare_exchange(routing_key, aio_pika.ExchangeType.FANOUT, durable=True)
    queue = await channel.declare_queue('', exclusive=True)
    await queue.bind(exchange)
    consume_task = await queue.consume(lambda message: asyncio.create_task(handle_message_notifications(message, websocket, user)))
    return queue, consume_task


@app.websocket("/ws/notification/{college_id}/")
async def get_notifications_websocket(websocket_con: WebSocket, college_id: str):
    """
    This websocket API will return real time notification

    Params:
        - websocket : This has values sent by frontend. This will have value token
        - college_id: The unique id of college

    Returns:
        - List : List of all students who are online

    Raises:
        - Exception: An error occurred when something wrong happen in the code.
    """
    try:
        logger.debug("Notification Websocket")
        await websocket_con.accept()
        Reset_the_settings().check_college_mapped(college_id)
        Reset_the_settings().get_user_database(college_id)
        r = get_redis_client()
        user = await Notification().get_user_details(websocket_con, college_id)
        if user:
            key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/{str(user.get('_id'))}_notifications"
            await r.delete(key)
            connection = await utility_obj.get_rabbitMQ_connection_channel()
            channel = await connection.channel()
            queue, consume_task = await consume_rabbitmq_messages_notifications(key, websocket_con, user, channel)
            try:
                while True:
                    try:
                        await websocket_con.receive_text()
                    except WebSocketDisconnect:
                        await queue.cancel(consume_task)
                        break
            finally:
                await queue.cancel(consume_task)
                await channel.close()
                await connection.close()
    except redis.exceptions.ConnectionError as error:
        logger.error(f"Some error occurred regarding redis connection. Error: {error}")
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"Something went wrong. {e}")
