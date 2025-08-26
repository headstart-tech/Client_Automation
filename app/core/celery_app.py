"""
This file is useful for celery setup in the application.
"""
import importlib
import socket
import sys

from celery import Celery
from kombu.exceptions import KombuError

from app.core.utils import settings, logger


def create_celery_app():
    """
    Create and configure a Celery instance with enhanced connection settings,
    including heartbeats.

    Returns:
        celery.Celery: A Celery instance.
    """
    # Define the socket keepalive options based on the platform
    socket_keepalive_options = {
        socket.TCP_KEEPCNT: 5,  # Number of keepalive probes to send before
        # considering the connection dead
        socket.TCP_KEEPINTVL: 10  # The interval between keepalive probes
    }
    # Add platform-specific keepalive settings
    if sys.platform == "darwin":
        # macOS (Darwin) uses TCP_KEEPALIVE for the idle interval option
        socket_keepalive_options[socket.TCP_KEEPALIVE] = 60
    elif sys.platform == "linux":
        # Linux uses TCP_KEEPIDLE for the idle interval option
        socket_keepalive_options[socket.TCP_KEEPIDLE] = 60

    # Define the Celery instance with adjusted connection pool settings and
    # heartbeat
    celery_app = Celery(
        "tasks",
        broker=settings.redis_server_url,
        backend=settings.redis_server_url,
        broker_connection_retry=True,
        broker_connection_retry_on_startup=True,
        worker_cancel_long_running_tasks_on_connection_loss=True,
        broker_pool_limit=5,  # Adjust based on your expected workload
        broker_connection_max_retries=5,
        broker_connection_timeout=30,  # Seconds
        broker_heartbeat=10,  # Heartbeat sent every 10 seconds
        broker_heartbeat_checkrate=2.0,
    )

    # Set Redis-specific connection options
    celery_app.conf.redis_socket_timeout = 3
    celery_app.conf.redis_socket_connect_timeout = 3
    celery_app.conf.redis_retry_on_timeout = True
    celery_app.conf.broker_transport_options = celery_app.conf.result_backend_transport_options = {
        "socket_timeout": 3,
        "socket_connect_timeout": 3,
        #  TODO: this code will be uncommented once testing is done!
        # "socket_keepalive": True,
        # "socket_keepalive_options": socket_keepalive_options
    }

    # Test the connection to the broker
    try:
        logger.info("Attempting to establish a connection to Redis...")
        conn = celery_app.connection()
        conn.ensure_connection(max_retries=5, interval_start=0,
                               interval_step=0.2, interval_max=2)
        logger.info("Connected to Redis successfully!")
    except (KombuError, socket.gaierror) as e:
        logger.error(f"Failed to establish connection to Redis: {e}")
        # Close the connection and retry
        conn.release()
        logger.info("Retrying connection to Redis...")
        try:
            conn.ensure_connection(max_retries=5, interval_start=0,
                                   interval_step=0.2, interval_max=2)
            logger.info("Connected to Redis successfully on retry!")
        except (KombuError, socket.gaierror) as retry_e:
            logger.error(f"Retry failed to establish connection to Redis: {retry_e}")
    return celery_app


# Initialize the Celery instance
celery_app = create_celery_app()

# List of modules to import that contain Celery tasks
task_modules = [
    "app.routers.api_v1.routes.student_email_routers",
    "app.routers.api_v1.routes",
    "app.celery_tasks.celery_student_timeline",
    "app.celery_tasks.celery_add_user_audit_logs",
    "app.celery_tasks.celery_add_user_timeline",
    "app.celery_tasks.celery_communication_log",
    "app.celery_tasks.celery_email_activity",
    "app.celery_tasks.celery_generate_pdf",
    "app.celery_tasks.celery_login_activity",
    "app.celery_tasks.celery_manage",
    "app.celery_tasks.celery_publisher_upload_leads",
    "app.celery_tasks.celery_send_mail",
    "app.celery_tasks.celery_student_timeline",
    "app.background_task.send_mail_configuration",
    "app.helpers.counselor_deshboard.counselor_allocation",
    "app.helpers.whatsapp_sms_activity.whatsapp_activity",
    "app.background_task.doc_text_extraction"
    # Add more modules here as needed
]
for task_module in task_modules:
    importlib.import_module(task_module)