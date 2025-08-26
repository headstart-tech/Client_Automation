"""
This file contain common utility classes and methods that can be used
across application.
"""

import asyncio
import datetime
import hashlib
import hmac
import json
import os
import random
import re
import time
import uuid
from functools import lru_cache
from pathlib import Path, PurePath
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Optional, List

import aio_pika
import boto3
import meilisearch
import pandas as pd
import pika
import pytz
import razorpay
import redis
import toml
from aio_pika import DeliveryMode
from boto3.session import Session
from bson import ObjectId
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from fastapi import Request
from fastapi import status
from fastapi.exceptions import HTTPException
from jose import JWTError, jwt
from kombu.exceptions import KombuError
from pydantic import ConfigDict
from sqlalchemy import text, RowMapping
from sqlalchemy.orm import DeclarativeMeta

from app.core.custom_error import ObjectIdInValid, CustomError, DataNotFoundError
from app.core.log_config import get_logger
from app.core.settings.tag_metadata import tags_metadata
from app.database.master_db_connection import toml_data
from app.database.motor_base_singleton import MotorBaseSingleton

master_credential = MotorBaseSingleton.get_instance().master_data

logger = get_logger(__name__)


def get_new_instance_mastar_data():
    """get new instance of MotorBase class"""
    global master_credential
    master_credential = MotorBaseSingleton.get_instance().master_data
    return master_credential


def requires_feature_permission(permission_type: str):
    """
    Decorator to mark a route handler with a required feature-level permission.

    This decorator attaches the required permission type (e.g., "read", "write", "edit", "delete")
    to the route function as an attribute. The permission can later be accessed in a dependency
    (e.g., `get_current_user_object`) to enforce access control.

    Params:
        permission_type (str): The type of permission required to access the route.

    Returns:
        Callable: The decorated route function with the required permission attribute.
    """

    def decorator(func):
        setattr(func, "required_permission", permission_type)
        return func

    return decorator


class Settings:
    """
    Get credentials values from .env file
    """

    # Environment
    general_info = toml_data.get("general", {})
    environment: str = general_info.get("environment")
    origins: list = general_info.get("origins")

    # Auth module
    secret_key: str = toml_data.get("authentication", {}).get("secret_key_auth")
    algorithm_used: str = toml_data.get("authentication", {}).get("algorithm")

    # master Database credentials
    db_username: str = toml_data.get("master_db", {}).get("db_username")
    db_password: str = toml_data.get("master_db", {}).get("db_password")
    db_url: str = toml_data.get("master_db", {}).get("db_url")
    db_name: str = toml_data.get("master_db", {}).get("db_name")

    # PostgreSQL Database credentials
    pgsql_db_credentials = toml_data.get("pgsql_db", {})
    pgsql_username: str = pgsql_db_credentials.get("pgsql_username")
    pgsql_password: str = pgsql_db_credentials.get("pgsql_password")
    pgsql_host: str = pgsql_db_credentials.get("pgsql_host")
    pgsql_port: str = pgsql_db_credentials.get("pgsql_port")
    pgsql_name: str = pgsql_db_credentials.get("pgsql_name")

    # Super admin credentials
    superadmin_username: str = general_info.get("first_superuser")
    superadmin_password: str = general_info.get("first_superuser_password")

    # Google recaptcha credentials
    auth_secret_key: str = toml_data.get("Google_recaptcha", {}).get("captcha_site_key")
    captcha_secret_key: str = toml_data.get("Google_recaptcha", {}).get(
        "captcha_secret_key"
    )

    # Pooling DB
    max_pool_size: int = toml_data.get("pool_db", {}).get("max_pool_size", 100)
    min_pool_size: int = toml_data.get("pool_db", {}).get("min_pool_size", 0)

    # Credentials for create random password/name/OTP
    random_password: str = toml_data.get("random", {}).get("password_str")
    random_name: str = toml_data.get("random", {}).get("random_name")
    random_otp: str = toml_data.get("random", {}).get("random_otp")

    # Base path credentials
    base_path: str = toml_data.get("base_path", {}).get("base_path")
    user_base_path: str = toml_data.get("base_path", {}).get("user_base_path")
    base_path_api: str = toml_data.get("base_path", {}).get("base_path_api")
    base_admin_path: str = toml_data.get("base_path", {}).get("base_admin_path")
    base_dev_path: str = toml_data.get("base_path", {}).get("base_dev_path")

    # Rate limiting values
    rate_limit_type: str = toml_data.get("rate_limiting", {}).get("rate_limit_type")
    public_limit_count: str = toml_data.get("rate_limiting", {}).get(
        "public_limit_count"
    )
    private_limit_count: str = toml_data.get("rate_limiting", {}).get(
        "private_limit_count"
    )
    global_limit_count: str = toml_data.get("rate_limiting", {}).get(
        "global_limit_count"
    )
    advance_public_limit_count: str = toml_data.get("rate_limiting", {}).get(
        "advance_public_limit_count"
    )
    advance_private_limit_count: str = toml_data.get("rate_limiting", {}).get(
        "advance_private_limit_count"
    )
    advance_global_limit_count: str = toml_data.get("rate_limiting", {}).get(
        "advance_global_limit_count"
    )

    # University/College credentials
    client_name: str = master_credential.get("client_name", "")
    university_name: str = master_credential.get("university", {}).get(
        "university_name"
    )
    university_logo: str = master_credential.get("university", {}).get(
        "university_logo"
    )
    payment_successful_mail_message: str = master_credential.get("university", {}).get(
        "payment_successfully_mail_message"
    )
    university_contact_us_email: str = master_credential.get("university", {}).get(
        "university_contact_us_mail"
    )
    university_website_url: str = master_credential.get("university", {}).get(
        "university_website_url"
    )
    university_admission_website_url: str = master_credential.get("university", {}).get(
        "university_admission_website_url"
    )

    # Teamcity credentials
    teamcity_base_path: str = toml_data.get("teamcity_credential", {}).get(
        "teamcity_base_path"
    )
    teamcity_build_type: str = toml_data.get("teamcity_credential", {}).get(
        "teamcity_build_type"
    )
    teamcity_token: str = toml_data.get("teamcity_credential", {}).get("teamcity_token")

    # AWS environment
    # The "aws_user_audit_bucket" will be set according to the "aws_env" value.
    aws_env_data = toml_data.get("env", {})
    aws_env: str = aws_env_data.get("aws_env", "")
    aws_user_audit_bucket: str = aws_env_data.get("aws_user_audit_bucket", "")
    reports_bucket_name: str = aws_env_data.get("reports_bucket_name", "")
    reports_access_key_id: str = aws_env_data.get("reports_access_key_id", "")
    reports_secret_access_key: str = aws_env_data.get("reports_secret_access_key", "")
    reports_region_name: str = aws_env_data.get("reports_region_name", "")

    # whatsapp credentials
    send_whatsapp_url: str = master_credential.get("whatsapp_credential", {}).get(
        "send_whatsapp_url"
    )
    generate_whatsapp_token: str = master_credential.get("whatsapp_credential", {}).get(
        "generate_whatsapp_token"
    )
    whatsapp_username: str = master_credential.get("whatsapp_credential", {}).get(
        "whatsapp_username"
    )
    whatsapp_password: str = master_credential.get("whatsapp_credential", {}).get(
        "whatsapp_password"
    )
    whatsapp_sender: str = master_credential.get("whatsapp_credential", {}).get(
        "whatsapp_sender"
    )

    # RabbitMQ Database credentials
    rmq_username: str = master_credential.get("rabbit_mq_credential", {}).get("rmq_username")
    rmq_password: str = master_credential.get("rabbit_mq_credential", {}).get("rmq_password")
    rmq_url: str = master_credential.get("rabbit_mq_credential", {}).get("rmq_url")
    rmq_host: str = master_credential.get("rabbit_mq_credential", {}).get("rmq_host")
    rmq_port: str = master_credential.get("rabbit_mq_credential", {}).get("rmq_port")
    rmq_email_queue: str = toml_data.get("rabbit_mq", {}).get("rmq_email_queue")

    title: str = "GTCRM-API"
    description: str = """ GTCRM API Modules 🚀 """
    version: str = "1.8.0"
    contact: Dict[str, str] = {
        "name": "Shift Boolean",
        "url": "https://shiftboolean.com/",
        "email": "support@shiftboolean.com",
    }
    openapi_tags: Optional[List[Dict[str, Any]]] = tags_metadata
    docs_url: str = "/docs"
    redoc_url: str = "/redocs"
    openapi_url: str = "/openapi.json"
    disable_docs: bool = (
            toml_data.get("general", {}).get("environment") != "development"
    )

    # SMS credentials
    sms_username_trans: str = master_credential.get("sms", {}).get("username_trans")
    sms_username_pro: str = master_credential.get("sms", {}).get("username_pro")
    sms_password: str = master_credential.get("sms", {}).get("password")
    sms_authorization: str = master_credential.get("sms", {}).get("authorization")
    sms_send_to_prefix: str = master_credential.get("sms", {}).get("sms_send_to_prefix")

    # Report webhook credentials
    report_webhook_api_key: str = master_credential.get("report_webhook_api_key")

    # Email payload credentials
    payload_username: str = master_credential.get("email", {}).get("payload_username")
    payload_password: str = master_credential.get("email", {}).get("payload_password")
    payload_from: str = master_credential.get("email", {}).get("payload_from")
    contact_us_number: str = master_credential.get("email", {}).get(
        "contact_us_number")
    university_email_name: str = master_credential.get("email", {}).get(
        "university_email_name")
    verification_email_subject: str = master_credential.get("email", {}).get(
        "verification_email_subject")
    banner_image_url: str = master_credential.get(
        "email", {}
    ).get("banner_image")
    email_logo: str = master_credential.get(
        "email", {}
    ).get("email_logo")
    email_cc: str = master_credential.get(
        "email", {}
    ).get("email_cc")

    # Seasons
    seasons: list = master_credential.get("seasons", [])
    current_season: str = master_credential.get("current_season", {})

    # AWS credentials
    s3_username: str = master_credential.get("s3", {}).get("username")
    aws_access_key_id: str = master_credential.get("s3", {}).get("aws_access_key_id")
    aws_secret_access_key: str = master_credential.get("s3", {}).get(
        "aws_secret_access_key"
    )
    region_name: str = master_credential.get("s3", {}).get("region_name")
    s3_assets_bucket_name: str = master_credential.get("s3", {}).get(
        "assets_bucket_name"
    )
    s3_reports_bucket_name: str = master_credential.get("s3", {}).get(
        "reports_bucket_name"
    )
    s3_public_bucket_name: str = master_credential.get("s3", {}).get(
        "public_bucket_name"
    )
    s3_student_documents_bucket_name: str = master_credential.get("s3", {}).get(
        "student_documents_name"
    )
    s3_assets_base_url: str = master_credential.get("s3", {}).get("assets_base_url")
    s3_reports_base_url: str = master_credential.get("s3", {}).get("reports_base_url")
    s3_public_base_url: str = master_credential.get("s3", {}).get("public_base_url")
    s3_student_documents_base_url: str = master_credential.get("s3", {}).get(
        "student_documents_base_url"
    )
    report_folder_name: str = master_credential.get("s3", {}).get("report_folder_name")
    s3_base_folder_name: str = master_credential.get("s3_base_folder")
    s3_base_bucket_url: str = master_credential.get("s3", {}).get("base_bucket_url")
    s3_download_bucket_name: str = master_credential.get("s3", {}).get(
        "download_bucket_name"
    )
    s3_dev_base_bucket_url: str = master_credential.get("s3", {}).get(
        "dev_base_bucket_url"
    )
    s3_demo_base_bucket_url: str = master_credential.get("s3", {}).get(
        "demo_base_bucket_url"
    )
    s3_stage_base_bucket_url: str = master_credential.get("s3", {}).get(
        "stage_base_bucket_url"
    )
    s3_prod_base_bucket_url: str = master_credential.get("s3", {}).get(
        "prod_base_bucket_url"
    )
    s3_dev_base_bucket: str = master_credential.get("s3", {}).get("dev_base_bucket")
    s3_demo_base_bucket: str = master_credential.get("s3", {}).get("demo_base_bucket")
    s3_stage_base_bucket: str = master_credential.get("s3", {}).get("stage_base_bucket")
    s3_prod_base_bucket: str = master_credential.get("s3", {}).get("prod_base_bucket")
    season_folder_name: str = master_credential.get("s3", {}).get("season_folder_name")

    # CollPoll credential
    collpoll_aws_access_key_id: str = master_credential.get("collpoll", {}).get(
        "aws_access_key_id"
    )
    collpoll_aws_secret_access_key: str = master_credential.get("collpoll", {}).get(
        "aws_secret_access_key"
    )
    collpoll_region_name: str = master_credential.get("collpoll", {}).get("region_name")
    collpoll_s3_bucket_name: str = master_credential.get("collpoll", {}).get(
        "s3_bucket_name"
    )
    collpoll_url: str = master_credential.get("collpoll", {}).get("collpoll_url")
    collpoll_auth_security_key: str = master_credential.get("collpoll", {}).get(
        "collpoll_auth_security_key"
    )

    # meilisearch credentials
    meilisearch_url = master_credential.get("meilisearch", {}).get("meili_server_host")
    master_key = master_credential.get("meilisearch", {}).get("meili_server_master_key")

    # Razorpay credentials
    razorpay_api_key: str = master_credential.get("razorpay", {}).get(
        "razorpay_api_key"
    )
    razorpay_secret: str = master_credential.get("razorpay", {}).get("razorpay_secret")
    razorpay_webhook_secret: str = master_credential.get("razorpay", {}).get(
        "razorpay_webhook_secret"
    )

    # Redis cache
    redis_cache_host: str = master_credential.get("cache_redis", {}).get("host")
    redis_cache_port: str = master_credential.get("cache_redis", {}).get("port")
    redis_cache_password: str = master_credential.get("cache_redis", {}).get("password")

    tawk_secret_key: str = master_credential.get("tawk_secret", "")

    university_prefix_name: str = master_credential.get(
        "university_prefix_name", "")

    telephony_secret_key: str = master_credential.get("telephony_secret", "")

    publisher_bulk_lead_push_limit: dict = master_credential.get("publisher_bulk_lead_push_limit",
                                                                 {})

    users_limit: int = master_credential.get("users_limit", 0)

    # s3 auth credentials
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name,
    )

    # session auth s3 credentials
    session = Session(
        aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key
    )

    # redis credentials
    redis_server_url: str = toml_data.get("redis_server", {}).get("redis_server_url")

    # textract credentials
    textract_aws_access_key_id: str = master_credential.get("aws_textract", {}).get(
        "textract_aws_access_key_id"
    )
    textract_aws_secret_access_key: str = master_credential.get("aws_textract", {}).get(
        "textract_aws_secret_access_key"
    )
    textract_aws_region_name: str = master_credential.get("aws_textract", {}).get(
        "textract_aws_region_name"
    )

    @property
    def fastapi_kwargs(self) -> Dict[str, Any]:
        """This returns a dictionary of the most commonly used keyword
        arguments when initializing a FastAPI instance.

        If `self.disable_docs` is True, the various docs-related arguments
        are disabled, preventing spec from being published.
        """
        fastapi_kwargs: Dict[str, Any] = {
            "title": self.title,
            "description": self.description,
            "version": self.version,
            "contact": self.contact,
            "openapi_tags": self.openapi_tags,
            "docs_url": self.docs_url,
            "redoc_url": self.redoc_url,
            "openapi_url": self.openapi_url,
        }
        if self.disable_docs:
            fastapi_kwargs.update(
                {"docs_url": None, "openapi_url": None, "redoc_url": None}
            )
        return fastapi_kwargs

    model_config = ConfigDict(extra="ignore")


settings = Settings()


@lru_cache
def get_settings():
    # SMS credentials
    settings.sms_username_trans = master_credential.get("sms", {}).get("username_trans")
    settings.sms_username_pro = master_credential.get("sms", {}).get("username_pro")
    settings.sms_password = master_credential.get("sms", {}).get("password")
    settings.sms_authorization = master_credential.get("sms", {}).get("authorization")
    settings.sms_send_to_prefix = master_credential.get("sms", {}).get(
        "sms_send_to_prefix"
    )

    # Report webhook credentials
    settings.report_webhook_api_key = master_credential.get("report_webhook_api_key")

    # Email payload credentials
    settings.payload_username = master_credential.get("email", {}).get(
        "payload_username"
    )
    settings.payload_password = master_credential.get("email", {}).get(
        "payload_password"
    )
    settings.payload_from = master_credential.get("email", {}).get("payload_from")
    settings.university_email_name = master_credential.get(
        "email", {}).get("university_email_name")
    settings.contact_us_number = master_credential.get(
        "email", {}).get("contact_us_number")
    settings.verification_email_subject = master_credential.get(
        "email", {}).get("verification_email_subject")
    settings.banner_image_url = master_credential.get(
        "email", {}
    ).get("banner_image")
    settings.email_logo = master_credential.get(
        "email", {}
    ).get("email_logo")
    settings.email_cc = master_credential.get("email", {}).get("email_cc", [])

    # AWS credentials
    settings.s3_username = master_credential.get("s3", {}).get("username")
    settings.aws_access_key_id = master_credential.get("s3", {}).get(
        "aws_access_key_id"
    )
    settings.aws_secret_access_key = master_credential.get("s3", {}).get(
        "aws_secret_access_key"
    )
    settings.region_name = master_credential.get("s3", {}).get("region_name")
    settings.s3_assets_bucket_name = master_credential.get("s3", {}).get(
        "assets_bucket_name"
    )
    settings.s3_base_folder_name = master_credential.get("s3", {}).get(
        "base_folder"
    )
    settings.season_folder_name = master_credential.get("s3", {}).get(
        "season_folder_name"
    )
    settings.s3_reports_bucket_name = master_credential.get("s3", {}).get(
        "reports_bucket_name"
    )
    settings.s3_public_bucket_name = master_credential.get("s3", {}).get(
        "public_bucket_name"
    )
    settings.s3_student_documents_bucket_name = master_credential.get("s3", {}).get(
        "student_documents_name"
    )
    settings.s3_download_bucket_name = master_credential.get("s3", {}).get(
        "download_bucket_name"
    )
    settings.s3_assets_base_url = master_credential.get("s3", {}).get("assets_base_url")
    settings.s3_reports_base_url = master_credential.get("s3", {}).get(
        "reports_base_url"
    )
    settings.s3_public_base_url = master_credential.get("s3", {}).get("public_base_url")
    settings.s3_student_documents_base_url = master_credential.get("s3", {}).get(
        "student_documents_base_url"
    )
    settings.report_folder_name = master_credential.get("s3", {}).get(
        "report_folder_name"
    )
    settings.s3_dev_base_bucket_url = master_credential.get("s3", {}).get(
        "dev_base_bucket_url"
    )
    settings.s3_demo_base_bucket_url = master_credential.get("s3", {}).get(
        "demo_base_bucket_url"
    )
    settings.s3_stage_base_bucket_url = master_credential.get("s3", {}).get(
        "stage_base_bucket_url"
    )
    settings.s3_prod_base_bucket_url = master_credential.get("s3", {}).get(
        "prod_base_bucket_url"
    )
    settings.s3_dev_base_bucket = master_credential.get("s3", {}).get("dev_base_bucket")
    settings.s3_demo_base_bucket = master_credential.get("s3", {}).get(
        "demo_base_bucket"
    )
    settings.s3_stage_base_bucket = master_credential.get("s3", {}).get(
        "stage_base_bucket"
    )
    settings.s3_prod_base_bucket = master_credential.get("s3", {}).get(
        "prod_base_bucket"
    )

    # CollPoll credential
    settings.collpoll_aws_access_key_id = master_credential.get("collpoll", {}).get(
        "aws_access_key_id"
    )
    settings.collpoll_aws_secret_access_key = master_credential.get("collpoll", {}).get(
        "aws_secret_access_key"
    )
    settings.collpoll_region_name = master_credential.get("collpoll", {}).get(
        "region_name"
    )
    settings.collpoll_s3_bucket_name = master_credential.get("collpoll", {}).get(
        "s3_bucket_name"
    )
    settings.collpoll_url = master_credential.get("collpoll", {}).get("collpoll_url")
    settings.collpoll_auth_security_key = master_credential.get("collpoll", {}).get(
        "collpoll_auth_security_key"
    )

    # University/College credentials
    settings.university_name = master_credential.get("university", {}).get(
        "university_name"
    )
    settings.university_logo = master_credential.get("university", {}).get(
        "university_logo"
    )
    settings.payment_successful_mail_message = master_credential.get(
        "university", {}
    ).get("payment_successfully_mail_message")
    settings.university_contact_us_email = master_credential.get("university", {}).get(
        "university_contact_us_mail"
    )
    settings.university_website_url = master_credential.get("university", {}).get(
        "university_website_url"
    )
    settings.university_admission_website_url = master_credential.get(
        "university", {}
    ).get("university_admission_website_url")

    # meilisearch credentials
    settings.meilisearch_url = master_credential.get("meilisearch", {}).get(
        "meili_server_host"
    )
    settings.master_key = master_credential.get("meilisearch", {}).get(
        "meili_server_master_key"
    )

    # Razorpay credentials
    settings.razorpay_api_key = master_credential.get("razorpay", {}).get(
        "razorpay_api_key"
    )
    settings.razorpay_secret = master_credential.get("razorpay", {}).get(
        "razorpay_secret"
    )
    settings.razorpay_webhook_secret = master_credential.get("razorpay", {}).get(
        "razorpay_webhook_secret"
    )

    # whatsapp credentials
    settings.send_whatsapp_url = master_credential.get("whatsapp_credential", {}).get(
        "send_whatsapp_url"
    )
    settings.generate_whatsapp_token = master_credential.get(
        "whatsapp_credential", {}
    ).get("generate_whatsapp_token")
    settings.whatsapp_username = master_credential.get("whatsapp_credential", {}).get(
        "whatsapp_username"
    )
    settings.whatsapp_password = master_credential.get("whatsapp_credential", {}).get(
        "whatsapp_password"
    )
    settings.whatsapp_sender = master_credential.get("whatsapp_credential", {}).get(
        "whatsapp_sender"
    )

    # aws textract
    settings.textract_aws_access_key_id = master_credential.get("aws_textract", {}).get(
        "textract_aws_access_key_id"
    )
    settings.textract_aws_secret_access_key = master_credential.get(
        "aws_textract", {}
    ).get("textract_aws_secret_access_key")
    settings.textract_aws_region_name = master_credential.get("aws_textract", {}).get(
        "textract_aws_region_name"
    )

    settings.s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.region_name,
    )
    settings.session = Session(
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )

    # Seasons
    settings.client_name = master_credential.get("client_name", "")
    settings.seasons = master_credential.get("seasons", [])
    settings.current_season = master_credential.get("current_season", {})

    settings.university_prefix_name = master_credential.get(
        "university_prefix_name")

    # Redis cache
    settings.redis_cache_host = master_credential.get("cache_redis", {}).get("host")
    settings.redis_cache_port = master_credential.get("cache_redis", {}).get("port")
    settings.redis_cache_password = master_credential.get("cache_redis", {}).get(
        "password"
    )

    # Tawk Credintials
    settings.tawk_secret_key = master_credential.get("tawk_secret", "")

    # Telephony credintials
    settings.telephony_secret_key = master_credential.get("telephony_secret", "")

    # Publisher bulk lead push limit
    settings.publisher_bulk_lead_push_limit = master_credential.get(
        "publisher_bulk_lead_push_limit", {})

    # Users limit
    settings.users_limit = master_credential.get("users_limit", 0)


class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON Encoder class to handle encoding of non-serializable objects.

    This encoder extends the default JSONEncoder provided by the json module
    to handle encoding of specific non-serializable types such as ObjectId,
    datetime, and bytes.

    Methods:
        default(obj): Overrides the default method of JSONEncoder to handle
                      encoding of non-serializable objects.
    """

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return str(obj)
        if isinstance(obj, bytes):
            return json.loads(obj.decode("utf-8"))
        if isinstance(obj, RowMapping):
            return dict(obj)
        # Handle SQLAlchemy ORM models like Roles, Permissions and Groups
        if isinstance(obj.__class__, DeclarativeMeta):
            return {column.name: getattr(obj, column.name) for column in obj.__table__.columns}
        return super().default(obj)


class Utility:
    """
    Contain functions related to utility
    """

    TIMEZONE_NAME = "Asia/Kolkata"

    def validate_document_format(self, filename: str) -> bool:
        """
        Validate document format.

        Params:
            filename (str): Name of the file.

        Returns:
            bool: A bool value which represents document valid or not.
        """
        base_name, extension = os.path.splitext(filename)
        lowercase_extension = extension.lower()
        filename = base_name + lowercase_extension
        valid_extensions = (".png", ".jpg", ".jpeg", ".pdf")
        return filename.endswith(valid_extensions)

    def format_float_to_2_places(self, float_value):
        """
        Format floating point number to 2 decimal places
        """
        if float_value >= 9999:
            float_value = 9999.00
        return round(float_value, 2)

    def get_percentage_result(self, dividend, divisor):
        """
        Get percentage
        """
        if divisor == 0:
            return 0
        return self.format_float_to_2_places(dividend / divisor * 100)

    async def update_transaction_details_by_message_id(
            self, message_id: str, communication_data: dict,
            name: str, com_type: str = "email"
    ):
        """
        Update the message delivered response

        Param:
            message_id (str): Get the message id of the webhook message
            communication_data (dict): Get the communication data of the student
            name (str): Get the name of the message id
            com_type (str): Get the type of communication type

        Return:
               None
        """
        transaction_ids = communication_data.get(f"{com_type}_summary", {}).get("transaction_id",
                                                                                [])
        transaction_detail = next((
            data for data in transaction_ids if data.get(name) == message_id),
            {})
        transaction_detail[f"{com_type}_delivered"] = True

    async def get_average_data_compare(
            self, current_data, current_total, previous_data, previous_total
    ):
        """get compare with previous data and current data"""
        current_percentage = self.get_percentage_result(current_data, current_total)
        previous_percentage = self.get_percentage_result(previous_data, previous_total)
        if current_percentage < previous_percentage:
            average_position = "down"
        elif current_percentage > previous_percentage:
            average_position = "up"
            if previous_percentage <= 0.01:
                current_percentage = 100
        else:
            average_position = "equal"
        return current_percentage, average_position

    async def get_position_based_on_percentage_difference(self, percentage_difference):
        """
        Get position based on percentage difference
        """
        position = "equal"
        if percentage_difference > 0:
            position = "up"
        elif percentage_difference < 0:
            position = "down"
        return position

    async def get_percentage_difference_with_position(self, old_value, current_value):
        """
        Get percentage difference with position based on indicator
        """
        try:
            percentage_difference = ((current_value - old_value) / old_value) * 100
        except:
            percentage_difference = 0
        position = await self.get_position_based_on_percentage_difference(
            percentage_difference
        )
        if abs(int(percentage_difference)) > 9999:
            percentage_difference = 9999
        return {
            "percentage": abs(float(format(percentage_difference, ".2f"))),
            "position": position,
        }

    async def get_start_date_and_end_date_by_change_indicator(self, change_indicator):
        """
        Get start date and end date by change indicator
        """
        today = datetime.date.today()
        number = int(change_indicator.split("_")[1])
        start_date = today - datetime.timedelta(days=number * 2 - 1)
        middle_date = today - datetime.timedelta(days=number)
        previous_date = today - datetime.timedelta(days=number - 1)
        return start_date, middle_date, previous_date

    async def pagination_in_api(
            self, page_num, page_size, data, data_length, route_name
    ):
        """
        Get data based on page_num and page_size
        """
        start = (page_num - 1) * page_size
        end = start + page_size
        response = {
            "data": data[start:end],
            "total": data_length,
            "count": page_size,
            "pagination": {},
        }
        if end >= data_length:
            response["pagination"]["next"] = None
        else:
            response["pagination"][
                "next"
            ] = f"{route_name}?page_number={page_num + 1}&page_size={page_size}"

        if page_num > 1:
            response["pagination"]["previous"] = (
                f"{route_name}?page_number={page_num - 1}&" f"page_size={page_size}"
            )
        else:
            response["pagination"]["previous"] = None
        return response

    async def pagination_in_aggregation(
            self, page_num, page_size, data_length, route_name
    ):
        """
        Get pagination for aggregation query
        """
        start = (page_num - 1) * page_size
        end = start + page_size
        response = {"pagination": {}}
        if end >= data_length:
            response["pagination"]["next"] = None
        else:
            response["pagination"]["next"] = (
                f"{route_name}?page_number={page_num + 1}&" f"page_size={page_size}"
            )

        if page_num > 1:
            response["pagination"]["previous"] = (
                f"{route_name}?page_number={page_num - 1}&" f"page_size={page_size}"
            )
        else:
            response["pagination"]["previous"] = None
        return dict(response)

    async def payment_helper(self, details, college, request) -> dict:
        """
        Helper function for get payment details
        """
        # Do not import staments of this function above at top otherwise
        # we will get circular import error
        error_info = details.get("error", {})
        if error_info:
            created_at = utility_obj.get_local_time(error_info.get("created_at"))
            details["error"]["created_at"] = created_at
            details["created_at"] = created_at
        payment_details = details.get("details", {})
        application_id = payment_details.get("application_id")
        course_fee = "N/A"
        payment_method = details.get("payment_method", "As per Flow")
        payment_mode = details.get("payment_mode", "N/A")
        payment_id = details.get("payment_id", "N/A")
        if payment_mode in ["NA", None]:
            from app.helpers.college_configuration import CollegeHelper

            headers, x_razorpay_account, client_id, client_secret = (
                await CollegeHelper().razorpay_header_update_partner(college)
            )
            client = razorpay.Client(auth=(client_id, client_secret))
            try:
                details = client.payment.fetch(payment_id, headers=headers)
            except Exception:
                details = {}
            from app.helpers.payment_configuration import PaymentHelper

            payment_mode, payment_mode_info, payment_id = (
                await PaymentHelper().get_payment_mode_info(details, request)
            )
        voucher_promocode_status, voucher_promocode, invoice_document = "No", "N/A", "N/A"
        if payment_method in ["Voucher", "Promocode"]:
            voucher_promocode_status, voucher_promocode = "Yes", details.get(
                f"used_{payment_method.lower()}"
            )
        if application_id:
            # Do not move below statement at top otherwise we will get
            # circular import error
            from app.database.configuration import DatabaseConfiguration

            if (
                    application := await DatabaseConfiguration().studentApplicationForms.find_one(
                        {"_id": application_id}
                    )
            ) is not None:
                if (
                        course := await DatabaseConfiguration().course_collection.find_one(
                            {"_id": application.get("course_id")}
                        )
                ) is not None:
                    course_fee = course.get("fees")
                if payment_method == "Offline":
                    invoice_documents = application.get("document_files", [])
                    if invoice_documents:
                        invoice_document = invoice_documents[0].get("public_url")
                else:
                    if (
                            payment_invoice := await DatabaseConfiguration().application_payment_invoice_collection.find_one(
                                {"payment_id": payment_id}
                            )
                    ) is not None:
                        invoice_document = payment_invoice.get("invoice_url")
            application_id = str(application_id)
        return {
            "id": str(details.get("_id")),
            "order_id": details.get("order_id"),
            "payment_id": payment_id,
            "merchant": details.get("merchant"),
            "status": details.get("status"),
            "user_id": str(details.get("user_id")),
            "purpose": payment_details.get("purpose"),
            "application_id": application_id,
            "error": error_info,
            "created_at": details.get("created_at"),
            "transaction_details": {
                "transaction_id": "N/A",
                "gateway_id": "N/A",
                "reference_number": "N/A",
                "payment_device": details.get("payment_device", "N/A"),
                "device_os": details.get("device_os", "N/A"),
            },
            "payment_method": payment_method,
            "payment_mode": payment_method,
            "mode_of_payment_info": details.get("payment_mode_info", "N/A"),
            "amount_received": course_fee,
            "voucher_promocode_status": voucher_promocode_status,
            "voucher_promocode": voucher_promocode,
            "invoice_document": invoice_document,
        }

    def name_can(self, item) -> str:
        """
        Combine first_name, middle_name and last_name of user and return
        fullname of user.
        """
        if item is None:
            return ""
        return " ".join(
            [
                i
                for i in [
                item.get("first_name", ""),
                item.get("middle_name", ""),
                item.get("last_name", ""),
            ]
                if i != "" and i is not None
            ]
        )

    def get_local_time(
            self,
            items=None,
            season=None,
            only_hour=None,
            hour_meridiem=None,
            hour_minute=None,
            only_date=None,
            release_window=None,
    ):
        """
        Convert the utc datetime to local datetime format
        """
        if items is None:
            items = datetime.datetime.utcnow()
        item = items.strftime("%d-%m-%Y %H:%M:%S")
        # Create datetime object in local timezone
        dt_utc = datetime.datetime.strptime(item, "%d-%m-%Y %H:%M:%S")
        dt_utc = dt_utc.replace(tzinfo=pytz.utc)
        # Get local timezone
        local_zone = pytz.timezone(self.TIMEZONE_NAME)
        dt_local = dt_utc.astimezone(local_zone)
        if season and hour_minute:
            central = dt_local.strftime("%Y-%m-%d %I:%M %p")
        else:
            temp_dict = {
                season: "%Y-%m-%d",
                hour_minute: "%I:%M %p",
                hour_meridiem: "%I:00%p",
                only_hour: "%I",
                only_date: "%d %b %Y",
                release_window: "%d/%m/%Y %I:%M %p",
            }
            format_date = next(
                (value for key, value in temp_dict.items() if key),
                "%d %b %Y %I:%M:%S %p",
            )
            central = dt_local.strftime(format_date)
        return central

    def read_current_toml_file(self):
        """Read toml file with using the toml package"""
        path = Path(__file__).parent.parent.parent
        path = PurePath(path, Path("config.toml"))
        return toml.load(str(path))

    async def date_change_utc(self, follow_date, date_format="%d/%m/%Y %I:%M %p"):
        """
        Convert the local datetime into utc datetime format
        """
        try:
            if not isinstance(follow_date, str):
                raise TypeError("follow_date must be a string")
            dt_utc = datetime.datetime.strptime(follow_date, date_format)
            local_time = pytz.timezone(self.TIMEZONE_NAME)
            naive = datetime.datetime.strptime(
                dt_utc.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"
            )
            local_dt = local_time.localize(naive, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            return utc_dt
        except TypeError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e),
            )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format or value",
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong. Error-{e}",
            )

    def sync_date_change_utc(self, convertable_date: any, date_format: str = "%d/%m/%Y %I:%M %p"):
        """
        Convert the local datetime into utc datetime format

        Params:
            - convertable_date (any): The date which need to convert into utc format.
            - date_format (str): The format of convertable_date.

        Returns:
              - datetime: The UTC format of convertable_date.

        Raises:
              - TypeError: When convertable_date format is wrong.
              - ValueError: When pass invalid convertable_date format.
              - Exception: When something went wrong at the time of convert local time to utc format.
        """
        try:
            if not isinstance(convertable_date, str):
                raise TypeError("Date must in a string format.")
            dt_utc = datetime.datetime.strptime(convertable_date, date_format)
            local_time = pytz.timezone(self.TIMEZONE_NAME)
            naive = datetime.datetime.strptime(
                dt_utc.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"
            )
            local_dt = local_time.localize(naive, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            return utc_dt
        except TypeError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e),
            )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format or value",
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong. Error-{e}",
            )

    async def date_change_format(
            self, start_date, end_date, datetime_format="%Y-%m-%d %H:%M:%S.%f"
    ):
        """
        Convert the of start date and end date to utc datetime format
        """
        start = start_date + " " + "00:00:00.000"
        end = end_date + " " + "23:59:59.000"
        local_time = pytz.timezone(self.TIMEZONE_NAME)
        naive = datetime.datetime.strptime(start, datetime_format)
        naive1 = datetime.datetime.strptime(end, datetime_format)
        local_dt = local_time.localize(naive, is_dst=None)
        local_dt1 = local_time.localize(naive1, is_dst=None)
        start_date = local_dt.astimezone(pytz.utc)
        end_date = local_dt1.astimezone(pytz.utc)
        return start_date, end_date

    def single_date_format(self, start_date, datetime_format="%Y-%m-%d %H:%M:%S.%f"):
        """
        Convert the of start date to utc datetime format
        """
        start = start_date + " " + "00:00:00.000"
        local_time = pytz.timezone(self.TIMEZONE_NAME)
        naive = datetime.datetime.strptime(start, datetime_format)
        local_dt = local_time.localize(naive, is_dst=None)
        start_date = local_dt.astimezone(pytz.utc)
        return start_date

    def date_change_format_sync(
            self, start_date, end_date, datetime_format="%Y-%m-%d %H:%M:%S.%f"
    ):
        """
        Convert the of start date and end date to utc datetime format
        """
        start = start_date + " " + "00:00:00.000"
        end = end_date + " " + "23:59:59.000"
        local_time = pytz.timezone(self.TIMEZONE_NAME)
        naive = datetime.datetime.strptime(start, datetime_format)
        naive1 = datetime.datetime.strptime(end, datetime_format)
        local_dt = local_time.localize(naive, is_dst=None)
        local_dt1 = local_time.localize(naive1, is_dst=None)
        start_date = local_dt.astimezone(pytz.utc)
        end_date = local_dt1.astimezone(pytz.utc)
        return start_date, end_date

    def datetime_range(self, start_date, end_date):
        """
        Get all dates between two dates
        """
        span = end_date - start_date
        for date in range(span.days + 1):
            yield start_date + datetime.timedelta(days=date)

    async def date_change_format_unix_time(self, start_date, end_date):
        """
        Convert the format of start date and end date to unix
        """
        start_date = (
                time.mktime(datetime.datetime.strptime(start_date, "%Y-%m-%d").timetuple())
                * 1000
        )
        end_date = (
                time.mktime(
                    (
                            datetime.datetime.strptime(end_date, "%Y-%m-%d")
                            + datetime.timedelta(days=1)
                    ).timetuple()
                )
                * 1000
        )
        return start_date, end_date

    async def last_3_month(self):
        """
        Return the start date and end date with the difference of 3 months
        """
        today = datetime.date.today()
        date = datetime.date.today() - pd.offsets.DateOffset(months=3)
        date = str(date)
        date_sp = date.split(" ")
        data = {"start_date": date_sp[0], "end_date": str(today)}
        return data

    async def next_3_month(self):
        """
        Return the start date and end date with the difference of 3 months
        """
        today = datetime.date.today()
        date = datetime.date.today() + pd.offsets.DateOffset(months=3)
        date = str(date)
        date_sp = date.split(" ")
        data = {"start_date": str(today), "end_date": date_sp[0]}
        return data

    async def format_date_range(self, date_range):
        """
        Format date range
        """
        if date_range:
            date_range = {k: v for k, v in date_range.dict().items() if v is not None}
        else:
            date_range = {}
        return date_range

    async def format_filter_list(self, data):
        """Format the data set of base model into proper dictionary

        Args:
            data: BaseModel formated data

        Returns:
            dict: returns the proper dictionary.
        """
        if data:
            data_dict = {k: v for k, v in data.dict().items() if v is not None}
        else:
            data_dict = {}
        return data_dict

    async def last_30_days(self, days=30):
        """
        Return the start date and end date with the difference of 30 or
        custom days.
        """
        today = datetime.date.today()
        date = datetime.date.today() - datetime.timedelta(days=days)
        date = str(date)
        date_sp = date.split(" ")
        data = {"start_date": date_sp[0], "end_date": str(today)}
        return data

    async def yesterday(self, season=None):
        """
        Return the start date and end date with the difference of 1 day
        """
        today = datetime.date.today()
        if season:
            date = datetime.date.today() + datetime.timedelta(days=1)
        else:
            date = datetime.date.today() - datetime.timedelta(days=1)
        date = str(date)
        date_sp = date.split(" ")
        if season:
            data = {"start_date": str(today), "end_date": date_sp[0]}
        else:
            data = {"start_date": date_sp[0], "end_date": date_sp[0]}
        return data

    async def week(self):
        """
        Return the start date and end date with the difference of 7 day
        """
        today = datetime.date.today()
        date = datetime.date.today() - datetime.timedelta(days=6)
        date = str(date)
        date_sp = date.split(" ")
        return {"start_date": str(date_sp[0]), "end_date": str(today)}

    def rename_func(self):
        """
        Create random name and return it
        """
        name = settings.random_name
        random_name = "".join(random.sample(name, 15))
        return random_name

    def break_name(self, user):
        """
        Break user full_name into three parts: first_name, middle_name and
        last_name.
        """
        full_name = user.pop("full_name")
        name = full_name.split(" ")
        if len(name) >= 3:
            first_name = name.pop(0)
            last_name = name.pop(-1)
            middle_name = " ".join(name)
        elif len(name) == 2:
            first_name = name.pop(0)
            last_name = name.pop(-1)
            middle_name = ""
        else:
            first_name = name.pop(0)
            last_name = ""
            middle_name = ""
        user["first_name"] = first_name.title()
        user["middle_name"] = middle_name.title()
        user["last_name"] = last_name.title()
        return user

    def random_pass(self):
        """
        Create random password
        """
        password = settings.random_password
        length_pass = 8
        random_password = "".join(random.sample(password, length_pass))
        return random_password

    async def user_serialize(self, user):
        """make all object id to string"""
        user["_id"] = str(user.get("_id"))
        if user.get("associated_colleges"):
            user["associated_colleges"] = [
                str(_id) for _id in user.get("associated_colleges", [])
            ]
        if user.get("created_by"):
            user["created_by"] = str(user.get("created_by"))
        if user.get("role", {}):
            user["role"] = {
                "role_name": user.get("role", {}).get("role_name"),
                "role_id": str(user.get("role", {}).get("role_id")),
            }
        user["check_in_status"] = user.get("check_in_status", False)
        user["assign_group_permissions"] = user.get("assign_group_permissions", [])
        return user

    async def generate_random_otp(self):
        """
        Create random 6 digit OTP
        """
        random_password = "".join(random.sample(settings.random_otp, 6))
        return random_password

    def response_model(self, data, message):
        """
        Helper function for return successful response
        """
        return {"data": [data], "code": 200, "message": message}

    def is_valid_extension(slef, filename: str, extensions=(".json", ".csv")):
        """
        Check file extension is valid or not
        """
        valid_extensions = extensions
        return filename.endswith(valid_extensions)

    def local_time_for_compare(self, item, format="%d-%m-%Y %H:%M:%S"):
        """
        Convert the local datetime to utc datetime format
        """
        # Create datetime object in local timezone
        dt_utc = datetime.datetime.strptime(item, format)
        dt_utc = dt_utc.replace(tzinfo=pytz.UTC)
        # Get local timezone
        local_zone = pytz.timezone(self.TIMEZONE_NAME)
        dt_local = dt_utc.astimezone(local_zone)
        return dt_local

    async def is_id_length_valid(self, _id: str, name: str):
        """
            Check provided object id has valid length and hexadecimal number or not, if object id is
            not validate then raise error with message
            Params:
                _id (str): The input college_id to validate.
                name (str): Name of the ID that needs to be checked
            Returns:
                bool: Returns True if the input is a valid
        """
        if len(_id) != 24:
            raise HTTPException(
                status_code=422,
                detail=f"{name} must be a 12-byte input or a "
                       f"24-character hex string",
            )

        if not re.fullmatch(r'[0-9a-fA-F]{24}', _id):
            raise HTTPException(
                status_code=422,
                detail=f"{name} is not a valid hexadecimal string",
            )

        return True

    async def is_length_valid(self, _id: str, name: str):
        """
            Check provided object id has valid length and hexadecimal number or not, if object id is
            not validate then raise error with message
            Params:
                _id (str): The input college_id to validate.
                name (str): Name of the ID that needs to be checked
            Returns:
                bool: Returns True if the input is a valid
        """
        if len(_id) != 24:
            raise ObjectIdInValid(_id, name)
        if not re.fullmatch(r'[0-9a-fA-F]{24}', _id):
            raise HTTPException(
                status_code=422,
                detail=f"{name} is not a valid hexadecimal string",
            )
        return True

    def create_unique_filename(self, extension):
        """
        Get unique name of a file using uuid module
        """
        unique_filename = uuid.uuid4().hex
        unique_filename = f"{unique_filename}{extension}"
        return unique_filename

    async def get_valid_date_range(self, date_range: dict):
        """
        Minimum date range needed is 2. For lower value return last 3 months' range.
        """
        if len(date_range) < 2:
            date_range = await self.last_3_month()
        return date_range

    async def return_skip_and_limit(self, page_num, page_size):
        """
        Get skip and limit values for filter data with the help of
        page_number and page_size.
        """
        skip = (page_num - 1) * page_size
        limit = page_size
        return skip, limit

    def get_ip_address(self, request: Request):
        """
        Get ip address of current user.

        Params:
            request (Request): The object of class Request.

        Returns:
            str: An IP address of a current user.

        """
        # Don't move below import statement in the top, otherwise it will
        # give ImportError due to circular import
        origin_ip = "127.0.0.1"
        if request is None:
            logger.warning(
                "Returning default IP address when request data " "not found..."
            )
            return origin_ip
        x = "x-forwarded-for".encode("utf-8")
        try:
            for header in request.headers.raw:
                if header[0] == x:
                    origin_ip = re.split(", ", header[1].decode("utf-8"))[0]
        except AttributeError:
            logger.error("'NoneType' object has no attribute 'headers'")
        except Exception as e:
            logger.error(f"Failed to fetch user ip address. Error - {e}")
        logger.warning("Finished execution of function get_ip_address().")
        return origin_ip

    async def get_start_and_end_date(self, date_range):
        """
        Get start date and end date with the help of date range
        """
        date_range = await self.get_valid_date_range(date_range)
        start_date, end_date = await self.date_change_format(
            date_range.get("start_date"), date_range.get("end_date")
        )
        return start_date, end_date

    async def verify_signature(self, api_key, token, timestamp, signature):
        """
        Verify passed signature with expected signature, return true if
        signature verified else false.
        """
        hmac_digest = hmac.new(
            key=api_key,
            msg="{}{}".format(timestamp, token).encode("utf-8"),
            digestmod=hashlib.sha512,
        ).hexdigest()
        return hmac.compare_digest(signature, hmac_digest)

    async def temporary_path(self, file):
        """
        Create temporary file which contain of uploaded file data and use it
        for further computation.
        """
        contents = await file.read()
        file_copy = NamedTemporaryFile("wb", delete=False)
        file_copy.write(contents)  # copy the received file data into a new temp file.
        file_copy.seek(0)  # move to the beginning of the file
        return file_copy

    async def prepare_role_name(self, role_name: str):
        """
        Return role_name in a proper format
        """
        split_role_name = role_name.split("college_")[1]
        new_role_name_in_list_format = str(split_role_name).split("_")
        return " ".join([word.capitalize() for word in new_role_name_in_list_format])

    async def get_role_name_in_proper_format(self, role_name, remove_college=True):
        """
        Get role_name in proper format
        """
        if str(role_name).startswith("college_") and remove_college:
            new_role_name = await self.prepare_role_name(role_name)
        else:
            split_role_name = str(role_name).split("_")
            new_role_name = " ".join([word.capitalize() for word in split_role_name])
        return new_role_name

    async def get_meili_client(self):
        """
        Create connection with meilisearch server
        """
        url = settings.meilisearch_url
        key = settings.master_key
        client = meilisearch.Client(url, key)
        return client

    def normalize_score(self, marking_scheme, score):
        """
        Normalize score based on marking scheme

        Params:
            marking_scheme (str): A marking scheme used to normalize score.
            score: A score which need to normalize

        Returns:
            str: Normalize score in a percentage format.
        """
        try:
            if type(score) != float and marking_scheme in ["Grades", "CGPA"]:
                if marking_scheme == "Grades":
                    grade_dict = {
                        "A+": "95-100",
                        "A": "90-94",
                        "A-": "85-89",
                        "B+": "80-84",
                        "B": "75-79",
                        "B-": "70-74",
                        "C+": "65-69",
                        "C": "60-64",
                        "C-": "55-59",
                        "D+": "50-54",
                        "D": "45-49",
                        "F": "0-44",
                    }
                    score = grade_dict.get(score, "").split("-")
                    score = random.uniform(int(score[0]), int(score[1]))
                elif marking_scheme == "CGPA":
                    score = float(score) * 9.5
            elif score is None or type(score) == str or score > 100:
                score = random.uniform(0, 100)
        except Exception as e:
            logger.warning(f"Internal error occurred. Error - {e}")
            score = random.uniform(0, 100)
        return round(score, 2)

    def format_hour(self, hour):
        """
        Get hour in 12-hour format

        hour (int): A hour of time.
        """
        if hour in [0, 12]:
            return 12
        elif 1 <= hour <= 11:
            return hour
        else:
            return hour - 12

    def calculate_time_diff(self, prev_time, current_time, req_hrs=False):
        """
        returns time difference between given two times
        """
        delta = relativedelta(current_time, prev_time)
        years = delta.years
        months = delta.months
        days = delta.days
        time_diff = []
        if req_hrs:
            if years > 0:
                time_diff.append(f"{years}y")
            if months > 0:
                time_diff.append(f"{months}m")
            if days > 0:
                time_diff.append(f"{days}d")
            hours = delta.hours
            minutes = delta.minutes
            seconds = delta.seconds
            if hours > 0:
                time_diff.append(f"{hours}h")
            if minutes > 0:
                time_diff.append(f"{minutes}m")
            if seconds > 0:
                time_diff.append(f"{seconds}s")
            return "".join(time_diff)
        if years > 0:
            time_diff.append(f"{years} years")
            return " ".join(time_diff)
        if months > 0:
            time_diff.append(f"{months} mon")
            return " ".join(time_diff)
        if days > 0:
            if days == 1:
                time_diff.append(f"{days} day")
            else:
                time_diff.append(f"{days} days")
            return " ".join(time_diff)
        return "0 days"

    def get_year_based_on_season(self, curr_season=None):
        """
        To get the year depending on the season
        Params:
           season(str): season
        """
        if curr_season is None:
            curr_season = settings.current_season
        seasons = settings.seasons
        for season in seasons:
            if curr_season == season.get("season_id"):
                if (season_folder := season.get("season_folder_name")) is not None:
                    return season_folder
                return season.get("season_name").split("-")[0].replace(" ", "")

    def get_local_hour_utc_hour_dict(self):
        """
        This function returns comparison of utc hours and local hours dict
        Params: None Returns: dict (here keys are local time str values
        which includes(am/pm) also. values are int which are hours of utc
        time.)
        """
        return {
            "12 AM": 18,
            "1 AM": 19,
            "2 AM": 20,
            "3 AM": 21,
            "4 AM": 22,
            "5 AM": 23,
            "6 AM": 0,
            "7 AM": 1,
            "8 AM": 2,
            "9 AM": 3,
            "10 AM": 4,
            "11 AM": 5,
            "12 PM": 6,
            "1 PM": 7,
            "2 PM": 8,
            "3 PM": 9,
            "4 PM": 10,
            "5 PM": 11,
            "6 PM": 12,
            "7 PM": 13,
            "8 PM": 14,
            "9 PM": 15,
            "10 PM": 16,
            "11 PM": 17,
        }

    def get_university_name_s3_folder(self):
        """
        returns the university name removing all spaces and in lower case
        Params:
          None
        Returns:
            college name removing spaces and in lower case
        """
        university_name = settings.s3_base_folder_name
        if university_name is None:
            university_name = ""
        return "".join(university_name.split()).lower()

    async def is_quality_score_valid(self, score: float, name: str) -> bool:
        """
        Check provided quality score has a valid value or not, if value is
        not valid then raise error with message.

        Params:
            score (float): A value which has to be check.
            name (str): Name of the field.

        Returns:
            - bool: A boolean value True when score is valid.

        Raises:
            - CustomError: An error occurred when score value is not valid.
        """
        if not 0 <= score <= 5:
            raise CustomError(f"{name} must be in between 0 and 5")
        return True

    async def is_score_valid(self, score: float, name: str) -> bool:
        """
        Check provided score has a valid value or not, if value is not
        validate then raise error with message.

        Params:
            - score (float): A value which want to check.
            - name (str): Name of the field.

        Returns:
            - bool: A boolean value True when score is valid.

        Raises:
            - CustomError: An error occurred when score value is not valid.
        """
        if not 0 <= score <= 10:
            raise CustomError(f"{name} must be in between 0 and 10")
        return True

    async def is_email_valid(self, email: str) -> bool:
        """Validate email according to patterns

        Args:
            email (str): Email for validation.

        Returns:
            bool: True if email is valid ortherwise False.
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    async def is_phone_number_valid(self, phone: str) -> bool:
        """Validate phone number according to digit and length count.

        Args:
            phone (str): Phone number for validation

        Returns:
            bool: True if phone number is valid ortherwise False.
        """
        pattern = r"^\d{10}$"
        return re.match(pattern, phone) is not None

    async def store_login_activity_helper(self, username, ip_address):
        """
        Get the login activity helper for the current user

        params:
            - username (str): Get the current username
            -ip_address (str): get the current IP address

        return:
            - None
        """
        from app.celery_tasks.celery_login_activity import login_activity
        from app.dependencies.oauth import is_testing_env

        toml_data = self.read_current_toml_file()
        try:
            if toml_data.get("testing", {}).get("test") is False:
                # TODO: Not able to add student timeline data
                #  using celery task when environment is
                #  demo. We'll remove the condition when
                #  celery work fine.
                if settings.environment in ["demo"]:
                    login_activity().store_login_activity(
                        user_name=username, ip_address=ip_address
                    )
                else:
                    if not is_testing_env():
                        login_activity().store_login_activity.delay(
                            user_name=username, ip_address=ip_address
                        )
        except KombuError as celery_error:
            logger.error(f"Error in sending task to Celery: {celery_error}")
        except Exception as error:
            logger.error(f"General error: {error}")

    async def convert_date_to_utc(self, date: str):
        """
        Convert a date to UTC from any format

        param:
            date (str): Date will be string format

        return:
            UTC format date
        """
        if date in ["", None]:
            return None
        date = parse(date)
        local_time = pytz.timezone(self.TIMEZONE_NAME)
        local_dt = local_time.localize(date, is_dst=None)
        return local_dt.astimezone(pytz.utc)

    async def get_current_month_date_range(self):
        """
        Get current month date range.

        Params: None.

        Returns:
            dict: A dictionary which contains current month date_range
                (start_date and end_date).
        """
        end_date = datetime.datetime.utcnow()
        return {
            "start_date": f"{end_date.year}-{end_date.month}-01",
            "end_date": end_date.strftime("%Y-%m-%d"),
        }

    async def get_current_year_date_range(self):
        """
        Get current year date range.

        Params: None.

        Returns:
            dict: A dictionary which contains current year date_range
                (start_date and end_date).
        """
        end_date = datetime.datetime.utcnow()
        return {
            "start_date": f"{end_date.year}-01-01",
            "end_date": end_date.strftime("%Y-%m-%d"),
        }

    async def get_application_student_details(
            self, application_id: str | None, student_id: str | None
    ):
        """
        Get application and student details
        Params:
            - application_id (str|None): The unique id of student application
            - student_id (str|None): The unique id of student
        Returns:
            - application (dict): The details of application
            - student (dict): The details of student
        Raises:
            - Exception: An error occurred when something wrong happen in the code.
        """
        from app.database.configuration import DatabaseConfiguration

        try:
            if application_id:
                application_id = ObjectId(application_id)
                application = (
                    await DatabaseConfiguration().studentApplicationForms.find_one(
                        {"_id": application_id}
                    )
                )
                student_id = application.get("student_id")
            else:
                student_id = ObjectId(student_id)
                application = (
                    await DatabaseConfiguration().studentApplicationForms.find_one(
                        {"student_id": student_id}
                    )
                )
                application_id = application.get("_id")
            student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                {"_id": student_id}
            )
            return student, application, student_id, application_id
        except Exception as error:
            logger.error(
                f"An error occurred while fetching application and student data: {error}"
            )

    async def get_event_type(
            self,
            event: str,
            application_id,
            student_id,
            application: dict,
            student: dict,
            data: dict | None,
            counselor,
    ):
        """
        Get data based on event
        Params:
            - event (str): The information of event type
            - application_id (Objectid): The unique id of application
            - student_id (objectId): The unique id of student
            - application (dict): The details of application
            - student (dict): The details of student
            - counselor (dict): Unique id of counselor
        Returns:
            - data (dict): The data extracted from event
        Raises:
            - Exception: An error occurred when something wrong happen in the code.
        """
        from app.database.configuration import DatabaseConfiguration

        if event == "Follow up":
            followup = await DatabaseConfiguration().leadsFollowUp.find_one(
                {"application_id": ObjectId(application_id)}
            )
            followup_field = followup.get("followup", [{}]) if followup else [{}]
            followup_counselor = followup_field[0].get("assigned_counselor_id", "")
            if followup_counselor:
                counselor = followup_counselor
            date = followup_field[0].get("followup_date", datetime.datetime.utcnow())
            event_type, send_to, event_datetime, message, student_id, application_id = (
                "Followup Scheduled",
                counselor,
                datetime.datetime.utcnow(),
                f"Follow-up scheduled for <span class='notification-inner'>{self.name_can(student.get('basic_details', {}))}</span> with mobile number <span class='notification-inner'>{student.get('basic_details', {}).get('mobile_number')}</span> at <span class='notification-inner'>{utility_obj.get_local_time(date)}</span>.",
                student_id,
                application_id,
            )
        elif event == "Followup remainder":
            followup = await DatabaseConfiguration().leadsFollowUp.find_one(
                {"application_id": ObjectId(application_id)}
            )
            followup_field = followup.get("followup", [{}]) if followup else [{}]
            followup_counselor = followup_field[0].get("assigned_counselor_id", "")
            if followup_counselor:
                counselor = followup_counselor
            date = followup_field[0].get("followup_date", datetime.datetime.utcnow())
            event_type, send_to, event_datetime, message, student_id, application_id = (
                "Followup remainder",
                counselor,
                datetime.datetime.utcnow(),
                f"Your follow-up with <span class='notification-inner'>{self.name_can(student.get('basic_details', {}))}</span> (Mobile: <span class='notification-inner'>{student.get('basic_details', {}).get('mobile_number')}</span>) is scheduled in the next <span class='notification-inner'>10 minutes</span> at <span class='notification-inner'>{utility_obj.get_local_time(date)}</span>.",
                student_id,
                application_id,
            )

        elif event == "Payment started":
            event_type, send_to, event_datetime, message, student_id, application_id = (
                "Payment Started",
                counselor,
                datetime.datetime.utcnow(),
                f"<span class='notification-inner'>{self.name_can(student.get('basic_details', {}))}</span> with mobile number <span class='notification-inner'>{student.get('basic_details', {}).get('mobile_number')}</span> performed payment activity.",
                student_id,
                application_id,
            )
        elif event == "Payment captured":
            event_type, send_to, event_datetime, message, student_id, application_id = (
                "Payment Captured",
                counselor,
                datetime.datetime.utcnow(),
                f"Bingo!! Payment captured for <span class='notification-inner'>{self.name_can(student.get('basic_details', {}))}</span> with mobile number <span class='notification-inner'>{student.get('basic_details', {}).get('mobile_number')}</span>.",
                student_id,
                application_id,
            )
        elif event == "Application submitted":
            event_type, send_to, event_datetime, message, student_id, application_id = (
                "Application Submitted",
                counselor,
                datetime.datetime.utcnow(),
                f"Bravo!! Application has been successfully submitted for <span class='notification-inner'>{self.name_can(student.get('basic_details', {}))}</span> with mobile number <span class='notification-inner'>{student.get('basic_details', {}).get('mobile_number')}</span>.",
                student_id,
                application_id,
            )
        elif event == "Allocate counselor":
            last_update = data.get("allocate_to_counselor", {}).get("last_update")
            if not application:
                application["enquiry_date"] = last_update - pd.offsets.DateOffset(
                    months=1
                )
            time_difference = last_update - application.get("enquiry_date")
            if (time_difference.total_seconds() / 60) < 1:
                (
                    event_type,
                    send_to,
                    event_datetime,
                    message,
                    student_id,
                    application_id,
                ) = (
                    "Assigned Lead",
                    counselor,
                    last_update,
                    f"New Lead is assigned <span class='notification-inner'>{self.name_can(student.get('basic_details', {}))}</span> to you check here.",
                    student_id,
                    application_id,
                )
            else:
                (
                    event_type,
                    send_to,
                    event_datetime,
                    message,
                    student_id,
                    application_id,
                ) = (
                    "Manual Assignment of Lead",
                    data.get("allocate_to_counselor", {}).get("counselor_id"),
                    data.get("allocate_to_counselor", {}).get("last_update"),
                    f"<span class='notification-inner'>{data.get('assigned_lead_count')}</span> Leads are Assigned from <span class='notification-inner'>{data.get('user_name')} ({await utility_obj.get_role_name_in_proper_format(data.get('user_role', ''))})</span>.",
                    student_id,
                    application_id,
                )
        elif event == "Student query":
            event_type, send_to, event_datetime, message, student_id, application_id = (
                "Student Created Query",
                counselor,
                datetime.datetime.utcnow(),
                f"New Queries is raised by <span class='notification-inner'>{self.name_can(student.get('basic_details', {}))}</span>.",
                student_id,
                application_id,
            )
        elif event == "Duplicate Enquiry Form":
            event_type, send_to, event_datetime, message, student_id, application_id = (
                "Duplicate Enquiry Form",
                counselor,
                datetime.datetime.utcnow(),
                f"<span class='notification-inner'>{self.name_can(student.get('basic_details', {}))}</span> has tried to fill the enquiry form again.",
                student_id,
                application_id,
            )
        elif event == "Data Segment Assignment":
            event_type, send_to, event_datetime, message, student_id, application_id = (
                "Data Segment Assignment",
                data.get("user_id"),
                datetime.datetime.utcnow(),
                data.get("message"),
                student_id,
                application_id,
            )
        elif event == "New Application Form":
            event_type, send_to, event_datetime, message, student_id, application_id = (
                "New Application Form",
                counselor,
                datetime.datetime.utcnow(),
                data.get("message"),
                student_id,
                application_id,
            )
        else:
            return
        data = {
            "event_type": event_type,
            "send_to": send_to,
            "student_id": student_id,
            "application_id": application_id,
            "message": message,
            "mark_as_read": False,
            "event_datetime": event_datetime,
            "created_at": datetime.datetime.utcnow(),
        }
        return data

    async def update_notification_db(
            self,
            event,
            application_id: str | None = None,
            student_id: str | None = None,
            data: dict | None = None,
            base_counselor=None,
    ):
        """
        Update notification database with given notification details
        Params:
            - event (str): This is the event that has happened
            - student_id (str|None): The unique id of student
            - application_id (str|None): The unique id of student application
            - data (dict|None): The data required to fill columns accordingly
        Returns:
            None
        Raises:
            - Exception: An error occurred when something wrong happen in the code.
        """
        from app.database.configuration import DatabaseConfiguration

        try:
            counselor = None
            if student_id is not None or application_id is not None:
                student, application, student_id, application_id = (
                    await self.get_application_student_details(
                        application_id, student_id
                    )
                )
                if base_counselor:
                    counselor = base_counselor
                else:
                    counselor = application.get("allocate_to_counselor", {}).get(
                        "counselor_id"
                    )
            else:
                application = student = {}
            if isinstance(data, dict):
                data_segment_redirect_link = data.get("data_segment_redirect_link")
                data_segment_id = data.get("data_segment_id")
            data = await self.get_event_type(
                event, application_id, student_id, application, student, data, counselor
            )
            if data:
                if event == "Data Segment Assignment":
                    data["data_segment_redirect_link"] = data_segment_redirect_link
                    data["data_segment_id"] = data_segment_id
                inserted = (
                    await DatabaseConfiguration().notification_collection.insert_one(
                        data
                    )
                )
                data["_id"] = inserted.inserted_id
                await self.update_redis(data, str(data.get("send_to")))
        except Exception as error:
            logger.error(
                f"An error occurred while updating notifications database {error}"
            )

    async def bulk_update_to_redis(self, data: list):
        """
        This function is used to process bulk updates to users
        Params:
            - data (dict): all notifications data to be processed
        Returns:
            None
        Raises:
            - Exception: An error occurred when something wrong happen in the code.
        """
        try:
            for notification in data:
                notification.pop("id")
                await self.update_redis(notification, str(notification.get("send_to")))
        except Exception as error:
            logger.error(f"An error occurred while bulk update in redis: {error}")

    async def update_redis(self, data: dict, counselor_id: str):
        """
        This function will update notification details in redis
        Params:
            - data (dict): The data which is to be stored in redis
            - counselor_id (str): The unique id of counselor
        Returns:
            None
        Raises:
            - Exception: An error occurred when something wrong happen in the code.
        """
        from app.dependencies.oauth import get_redis_client, is_testing_env

        if not is_testing_env():
            r = get_redis_client()
            data.update(
                {
                    "send_to": str(data.get("send_to")),
                    "student_id": (
                        str(data.get("student_id")) if data.get("student_id") else ""
                    ),
                    "application_id": (
                        str(data.get("application_id"))
                        if data.get("application_id")
                        else ""
                    ),
                    "event_datetime": str(data.get("event_datetime")),
                    "created_at": (
                        str(data.get("created_at"))
                        if data.get("created_at")
                        else str(datetime.datetime.utcnow())
                    ),
                    "_id": str(data.get("_id")),
                }
            )
            update_resource_id = data.get("update_resource_id")
            data_segment_redirect_link = data.get("data_segment_redirect_link")
            data_segment_id = data.get("data_segment_id")
            for value, key_name in [
                (update_resource_id, "update_resource_id"),
                (data_segment_redirect_link, "data_segment_redirect_link"),
                (data_segment_id, "data_segment_id")
            ]:
                if value:
                    data.update({key_name: str(value)})
            key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/{counselor_id}_notifications"
            async with r.pipeline() as pipe:
                while True:
                    try:
                        await pipe.watch(key)
                        pipe.multi()
                        try:
                            data = json.dumps(data)
                        except Exception as e:
                            logger.error(f"Some internal error occurred: {e}")
                            break
                        if await pipe.rpush(key, data):
                            await pipe.expire(key, (300 + random.randint(0, 300)))
                        await pipe.execute()
                        break
                    except redis.WatchError as e:
                        logger.error(f"While storing data in cache got error: {e}")
                        continue
                    except redis.TimeoutError as e:
                        logger.error(f"Timeout while storing data in cache: {e}")
                        break
                    except Exception as e:
                        logger.error(f"Some internal error occurred: {e}")
                        break
            connection = await utility_obj.get_rabbitMQ_connection_channel()
            async with connection:
                channel = await connection.channel()
                message_body = "Data published"
                exchange = await channel.declare_exchange(key, aio_pika.ExchangeType.FANOUT,
                                                          durable=True)
                await exchange.publish(
                    aio_pika.Message(body=message_body.encode()),
                    routing_key=""
                )
                await channel.close()
            await connection.close()

    def get_count_aggregation(self, pipeline, skip=None, limit=None):
        """
        Add an aggregation functions which is taking count all documents

        params:
            pipeline (str): Get the aggregation pipeline
            skip (int): Get the skip count of the document
            limit (int): Get the limit of document

        return:
            A aggregation function which takes count all documents
        """
        pipeline_temp = [
            {"$facet": {"totalCount": [{"$count": "value"}], "pipelineResults": []}},
            {"$unwind": "$pipelineResults"},
            {"$unwind": "$totalCount"},
            {
                "$replaceRoot": {
                    "newRoot": {
                        "$mergeObjects": [
                            "$pipelineResults",
                            {"totalCount": "$totalCount.value"},
                        ]
                    }
                }
            },
        ]
        if skip is not None and limit is not None:
            pipeline_temp[0].get("$facet", {}).get("pipelineResults", []).extend(
                [{"$skip": skip}, {"$limit": limit}]
            )
        pipeline.extend(pipeline_temp)
        return pipeline

    async def get_user_instance(
            self,
            token,
    ):
        """
        Retrieves the current user based on the provided JWT token.

        Parameters:
        - token (HTTPAuthorizationCredentials): The JWT token extracted from the request header.

        Returns:
        - User: The user object associated with the provided JWT token.

        Raises:
        - HTTPException: If the credentials cannot be validated or if the user associated with the token does not exist.
        """
        from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache
        try:
            decoded_token = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm_used],
            )
        except JWTError:
            return None, None

        email = decoded_token.get("sub")
        scope = decoded_token.get("scopes")[0]
        expire_at = datetime.datetime.fromtimestamp(
            decoded_token.get("exp"), pytz.utc
        ).astimezone(pytz.timezone("Asia/Kolkata"))
        from app.database.configuration import DatabaseConfiguration

        if scope == "student":
            user = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                {"user_name": email}
            )
        else:
            user = await get_collection_from_cache(collection_name="users", field=email)
            if not user:
                user = await DatabaseConfiguration().user_collection.find_one({"user_name": email})
                if user:
                    await store_collection_in_cache(collection=user, collection_name="users",
                                                    expiration_time=10800,
                                                    field=email)
        if user:
            return ObjectId(user.get("_id")), expire_at
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

    async def delete_old_data_in_redis(self, key, minutes, redis_client):
        """
        Delete the old data in Redis
        Params:
            key (str): The unique key name in Redis in which old data should be removed
            minutes (int): No. of minutes previous data is to be removed.
            redis_client: Redis client to perform  redis operations
        Returns:
            None
        Exception:
            HTTPException: Raises when some unexpected error occurs

        """
        minutes_ago = int(time.time()) - (minutes * 60)
        lua_script = """
                    local key = KEYS[1]
                    local minutes_ago = tonumber(ARGV[1])
                    local elements = redis.call('LRANGE', key, 0, -1)
                    for i, element in ipairs(elements) do
                        local data = cjson.decode(element)
                        if data['timestamp'] <= minutes_ago then
                            redis.call('LREM', key, 0, element)
                        end
                    end
                """
        await redis_client.eval(lua_script, 1, key, minutes_ago)

    async def get_endpoint_used_count(self, redis_server, user_data, rate_limit_type, endpoint):
        """
        Retrieve the count of API calls made by the user for a specific endpoint.

        Args:
            redis_server (Redis): The Redis server connection.
            user_data (str): The user data identifier.
            rate_limit_type (str): The rate limit type, either "api_wise" or "global".
            endpoint (str): The API endpoint to check the usage count for.

        Returns:
            int: The count of API calls made by the user for the specified endpoint.
        """
        historical_data = await redis_server.lrange(str(user_data) + "_api_used", 0, -1)
        historical_dict = [json.loads(item) for item in historical_data]
        return len(historical_dict)

    async def store_api_hit(self, user_id, api_name, redis_server):
        """
        Store the API hit details for a user in Redis.

        Args:
            user_id (str): The user identifier.
            api_name (str): The name of the API that was called.
        """
        try:
            key = f"{user_id}_api_used{api_name}/{int(time.time())}"
            json_data = json.dumps({"api_name": api_name, "timestamp": int(time.time())})
            await redis_server.setex(key, 60 + random.randint(0, 30), json_data)
        except Exception as e:
            logger.error(f"Some connection error occurred while fetching data from Redis: {e}")

    def get_api_and_description(self, route):
        """
        Retrieve API description and type based on prefix and endpoint.

        Args:
            route (str): Endpoint name to search for.

        Returns:
            tuple: Description (str or None), API type (str or None).
        """

        def clean_prefix(prefix):
            """Regular expression pattern to match the suffixes"""
            pattern = r"(s|_beta|_manager)$"
            cleaned_prefix = re.sub(pattern, "", prefix)
            return cleaned_prefix

        description = None
        route_segments = route.replace("/", "", 1).split("/")
        queue_name = "user_audit_queue"
        for i in range(1, len(route_segments)):
            current_prefix = "/".join(route_segments[:i])
            route_details = tags_metadata[0].get("route_details", {}) if tags_metadata else []
            if current_prefix not in route_details:
                current_prefix = clean_prefix(current_prefix)
            if current_prefix == "role_permissions":
                queue_name = "role_permission_logs"
            remaining_route = route.replace(f"/{current_prefix}", "", 1)
            data = route_details.get(current_prefix, {})
            route_dt = data.get("routes", {}).get(remaining_route, "")
            if route_dt:
                return route_dt.get("description", None), queue_name
        return description, queue_name

    async def fetch_and_store(self):
        """
        Fetches data from Redis and stores it in MongoDB.

        Returns:
            dict: A dictionary containing a message indicating the success of the operation.

        Raises:
            HTTPException: If no data is found in Redis.
        """
        from app.dependencies.oauth import get_redis_client
        from app.database.configuration import DatabaseConfiguration

        redis_client = get_redis_client()
        batch_size = 500
        while True:
            data_from_redis = await redis_client.lrange("audit_trail_data", 0, batch_size - 1)
            await redis_client.ltrim("audit_trail_data", batch_size, -1)
            if data_from_redis:
                data = await self.process_data(data_from_redis)
                try:
                    DatabaseConfiguration().user_audit_collection.insert_many(data)
                except Exception as e:
                    logger.error(f"While storing data in MongoDB got error: {e}")
                    await self.store_back_to_redis(redis_client, data_from_redis)
                    raise CustomError(e)
            else:
                break
        return {
            "code": 200,
            "message": "Data stored successfully"
        }

    async def cache_roles_and_permissions(self):
        """
        Fetches all roles and their associated permissions from PostgreSQL and caches them in Redis.

        This function:
        - Queries the database to retrieve roles and their associated permissions.
        - Formats the data into a dictionary with role IDs as keys and role details as JSON.
        - Clears existing cached data in Redis before storing new role-permission mappings.

        Returns:
            dict: A response containing a status code and a message.

        Raises:
            Exception: If any error occurs during database query execution or Redis operations.
        """
        from app.dependencies.oauth import get_redis_client, is_testing_env
        from app.database.motor_base import pgsql_conn
        db = await pgsql_conn.get_db_session()
        try:
            sql_query = text("""
                SELECT 
                    r.id, r.name, r.description, r.scope, r.mongo_id,
                    JSONB_BUILD_OBJECT(
                        'college_permissions', COALESCE(
                            JSONB_AGG(DISTINCT p.name) FILTER (WHERE p.name IS NOT NULL AND p.scope = 'college'
                        ), '[]'::jsonb),
                        'global_permissions', COALESCE(
                            JSONB_AGG(DISTINCT p.name) FILTER (WHERE p.name IS NOT NULL AND p.scope = 'global'
                        ), '[]'::jsonb)
                    ) AS permissions
                FROM roles r
                LEFT JOIN role_permissions rp ON r.id = rp.role_id
                LEFT JOIN permissions p ON rp.permission_id = p.id
                GROUP BY r.id
            """)
            result_data = await db.execute(sql_query)
            result = result_data.fetchall()
            roles_data = {
                str(row.mongo_id): json.dumps({**row._mapping})
                for row in result
            }
            if not is_testing_env():
                redis_client = get_redis_client()
                # Delete existing data
                await redis_client.delete("roles_permissions")
                # Store new data in Redis
                await redis_client.hset("roles_permissions", mapping=roles_data)
            return {
                "code": 200,
                "message": "Roles and permissions cached successfully",
                "data": roles_data
            }
        except Exception as e:
            await db.rollback()  # Rollback on error
            raise Exception(f"Error caching roles and permissions: {e}")
        finally:
            await db.close()

    async def cache_groups_and_permissions(self, data=None):
        """
        Cache group and permission mappings in Redis.

        If `data` is provided, only that group's data is cached. Otherwise, all group-permission mappings
        are fetched from the database and cached. Caching is skipped entirely in a testing environment.

        Params:
            data (Optional[Groups]): An optional Groups SQLAlchemy model instance. If provided,
                                     only this group's information will be cached.

        Returns:
            dict: A response dict containing:
                - `code`: HTTP-like status code (200 on success)
                - `message`: A message indicating the result of the caching operation
                - `data`: A dictionary of group data with JSON-serialized values

        Raises:
            Exception: If an error occurs during the caching process or DB interaction.
        """
        from app.dependencies.oauth import get_redis_client, is_testing_env
        from app.database.motor_base import pgsql_conn
        from app.database.configuration import DatabaseConfiguration
        db = await pgsql_conn.get_db_session()
        try:
            if data:
                groups_data = {
                    str(data.id): json.dumps({
                        "id": data.id, "name": data.name, "description": data.description,
                        "created_by": data.created_by, "created_at": data.created_at.isoformat(),
                        "permissions": [], "users": []
                    })
                }
            else:
                sql_query = text("""
                    SELECT 
                        row_to_json(g) AS group_data,
                        JSONB_BUILD_OBJECT(
                            'college_permissions', COALESCE(
                                JSONB_AGG(DISTINCT p.name) FILTER (WHERE p.name IS NOT NULL AND p.scope = 'college'
                            ), '[]'::jsonb),
                            'global_permissions', COALESCE(
                                JSONB_AGG(DISTINCT p.name) FILTER (WHERE p.name IS NOT NULL AND p.scope = 'global'
                            ), '[]'::jsonb)
                        ) AS permissions
                    FROM groups g
                    LEFT JOIN group_permissions gp ON g.id = gp.group_id
                    LEFT JOIN permissions p ON gp.permission_id = p.id
                    GROUP BY g.id
                """)
                result_data = await db.execute(sql_query)
                result = result_data.fetchall()
                pipeline = [
                    {"$unwind": "$group_ids"},
                    {"$group": {"_id": "$group_ids",
                                "user_ids": {"$addToSet": {"$toString": "$_id"}}}}
                ]
                group_user_map = await DatabaseConfiguration().user_collection.aggregate(
                    pipeline).to_list(None)
                group_to_users = {item["_id"]: item["user_ids"] for item in group_user_map}
                groups_data = {
                    str(row.group_data.get("id")): json.dumps(
                        {**row.group_data, "permissions": row.permissions,
                         "users": group_to_users.get(row.group_data.get("id"), [])}
                    )
                    for row in result
                }
            if not is_testing_env():
                redis_client = get_redis_client()
                key = "groups_and_permissions"
                if not data:
                    # Delete existing data
                    await redis_client.delete(key)
                # Store new data in Redis
                await redis_client.hset(key, mapping=groups_data)
            return {
                "code": 200,
                "message": "Groups and their permissions cached successfully",
                "data": groups_data
            }
        except Exception as e:
            await db.rollback()  # Rollback on error
            raise Exception(f"Error caching groups and permissions: {e}")
        finally:
            await db.close()

    async def cache_permissions(self, collection: str) -> dict[str, Any]:
        """
        Cache permission data from the database into Redis.

        This method fetches all permissions from the database, serializes the data,
        and stores it in a Redis hash under the specified collection. It deletes any
        existing data in the Redis collection before storing the updated data.

        Params:
            collection (str): The Redis collection name to store the permission data.

        Returns:
            dict: A response containing:
                - code (int): Status code (200 for success).
                - message (str): Success message.
                - data (dict): Cached permission data where the key is the permission ID
                  and the value is the serialized permission object.

        Raises:
            Exception: If any error occurs during the caching process.
        """
        from app.dependencies.oauth import get_redis_client, is_testing_env
        from app.database.motor_base import pgsql_conn

        db = await pgsql_conn.get_db_session()
        query = "SELECT * FROM permissions ORDER BY name ASC"
        result = (await db.execute(text(query))).mappings().all()
        perm_data = dict(
            map(lambda p: (str(p.get("id")), json.dumps(
                {"id": p.get("id"), "name": p.get("name"), "description": p.get("description"),
                 "scope": p.get("scope")})), result)
        )
        if not is_testing_env():
            redis_client = get_redis_client()
            # Delete existing data
            await redis_client.delete(collection)
            # Store new data in Redis
            await redis_client.hset(collection, mapping=perm_data)
        return {
            "code": 200,
            "message": "Permissions cached successfully",
            "data": perm_data
        }

    async def process_data(self, data_from_redis: list) -> tuple:
        """
        Asynchronously processes data fetched from Redis by delegating the task
        to a thread pool executor.

        Params:
            data_from_redis (list): A list of data items retrieved from Redis.

        Returns:
            tuple: A tuple of processed data items.
        """
        loop = asyncio.get_event_loop()
        return await asyncio.gather(
            *[
                loop.run_in_executor(None, self.format_data, d)
                for d in data_from_redis
            ]
        )

    async def store_back_to_redis(self, redis_client, data: list) -> None:
        """
        Asynchronously stores data back to Redis using a pipeline.

        Params:
            redis_client: The Redis client instance.
            data (list): A list of data items to be pushed back into Redis.

        Returns:
            None
        """
        try:
            pipe = await redis_client.pipeline(transaction=False)
            await pipe.rpush("audit_trail_data", *data)
            await pipe.execute()
            logger.info("Data restored in redis successfully")
        except Exception as e:
            logger.error(f"Failed to store data back to Redis: {e}")

    def format_data(self, redis_data) -> dict:
        """
        Process each Redis data item: decode, parse JSON, and convert timestamp.

        Params:
            redis_data (bytes): Redis data item in bytes format.

        Returns:
            dict: Processed data dictionary with converted timestamp.
        """
        json_data = json.loads(redis_data.decode('utf-8'))
        json_data["timestamp"] = datetime.datetime.strptime(
            json_data["timestamp"],
            "%Y-%m-%d %H:%M:%S.%f%z"
        )
        return json_data

    async def store_user_audit_trail(self, data, redis_server, key):
        """
        Store user audit trail data in Redis.

        Args:
            data (dict): The data to be stored in the audit trail.
            redis_server (Redis): The Redis server connection.
            key (str): The collection name where data needs to be stored.
        """
        json_data = json.dumps(data, cls=CustomJSONEncoder)
        async with redis_server.pipeline() as pipe:
            while True:
                try:
                    await pipe.watch(key)
                    pipe.multi()
                    await pipe.rpush(key, json_data)
                    await pipe.execute()
                    break
                except redis.WatchError as e:
                    logger.error(f"While storing data in {key} got error: {e}")
                    continue
                except redis.TimeoutError as e:
                    logger.error(f"Timeout while storing data in {key}: {e}")
                    break
                except Exception as e:
                    logger.error(f"Some internal error occurred: {e}")
                    break

    def mask_custom_format_string(self, custom_id: str, mask_char: str = "*") -> str:
        """
        Function to mask the custom id.

        Params:
            custom_id (str): Application custom id 
            mask_char (str, optional): Masked character replaced with this. Defaults to "*".

        Raises:
            CustomError: Raise when no any / character found in the string
            HTTPException: Raise when the data of custom id is passed with some another data type.

        Returns:
            str: Masked custom id.
        """
        try:
            index = custom_id.index("/") + 2
            left = len(custom_id) - index
            return custom_id[:index] + mask_char * left

        except ValueError:
            raise CustomError(f"{custom_id} does not contains value.")

        except Exception as error:
            logger.error("An error occurred when mask the custom application id.")
            raise HTTPException(status_code=500, detail=f"Error - {error}")

    def mask_email(self, email: str, mask_char: str = "*", unmasked_prefix_length: int = 4) -> str:
        """
        Masking email address

        Params:
            email (str): Full email id for masking
            mask_char (str, optional): Masked character replaced with this. Defaults to "*".
            unmasked_prefix_length (int, optional): Unmask character count in the email. Defaults to 4.

        Raises:
            CustomError: If email data is not in there proper data type.
            HTTPException: Raise when the data of email is passed with some another data type.

        Returns:
            str: Masked email id
        """
        try:
            local, domain = email.split('@')
            if len(local) > unmasked_prefix_length:
                masked_local = local[:unmasked_prefix_length] + mask_char * (
                        len(local) - unmasked_prefix_length)
            else:
                masked_local = local  # In case the local part is shorter than the unmasked prefix length
            return masked_local + '@' + domain
        except ValueError:
            raise CustomError("Invalid email id.")

        except Exception as error:
            logger.error("An error occurred when mask the email id.")
            raise HTTPException(status_code=500, detail=f"Error - {error}")

    def get_application_stage(self, current_stage: float) -> str:
        """
        Return application stage value by getting current_stage

        Params:
            current_stage (float): It should be 1.25 to 10.0

        Return:
            str: It should be the value as per current stage
        """
        names = {
            1.25: "Form Initiated",
            2.5: "Basic and preference details",
            3.75: "Parent details",
            5.0: "Address details",
            6.25: "Education details",
            7.5: "Payment",
            8.75: "Upload document",
            10.0: "Declaration",
        }
        return names.get(current_stage, "Invalid stage")

    def mask_phone_number(self, phone_number: str, unmasked_length: int = 5,
                          mask_char: str = "*") -> str:
        """
        Function for making full phone no. to masked phone no.

        Params:
            phone_number (str): Full phone number for masking
            unmasked_length (int, optional): Unmask character count in the email. Defaults to 5.
            mask_char (str, optional): Masked character replaced with this. Defaults to "*".

        Returns:
            str: Masked phone no.
        """
        if len(phone_number) > unmasked_length:
            masked_phone = phone_number[:unmasked_length] + mask_char * (
                    len(phone_number) - unmasked_length)
        else:
            masked_phone = phone_number  # In case the phone number is shorter than the unmasked length
        return masked_phone

    async def update_ip_addresses_in_redis(self):
        """
        Restore IP addresses with extra API limits into Redis.

        This method retrieves all IP addresses with extra API limits from the database
        and stores them in Redis for efficient access. It deletes any existing data in the
        Redis key "extra_limit_ip_collection" before storing the updated list of IP addresses.

        Raises:
            HTTPException:
                - status_code=400: If there is an error while storing data in Redis.

        Returns:
            bool: True if the operation is successful, otherwise raises an exception.
        """
        from app.dependencies.oauth import get_redis_client
        from app.database.configuration import DatabaseConfiguration
        try:
            pipeline = [
                {
                    "$project": {
                        "ip_address": 1,
                        "_id": 0
                    }
                }
            ]
            all_data = await DatabaseConfiguration().extra_limit_ip_collection.aggregate(
                pipeline).to_list(None)
            all_data = all_data[0] if all_data else {}
            redis_client = get_redis_client()
            await redis_client.delete("extra_limit_ip_collection")
            await self.store_user_audit_trail(all_data.get("ip_address", []), redis_client,
                                              "extra_limit_ip_collection")
            return True
        except Exception as e:
            logger.error(f"While storing data in Redis, got error: {e}")
            raise HTTPException(status_code=400,
                                detail=f"While storing data in Redis got error: {e}")

    def search_for_document(self, collection: list, field: str, search_name: str,
                            single_document=True):
        """
        searches for a particular document in given list of dicts
        Params:
            collection: The given collection
            field (str): The field which is to be searched
            search_name (str): The search which is to be done
            single_document (bool): True if required to send a single document else list of documents
        Return:
            Document: The required document
        """
        if single_document:
            return next((item for item in collection
                         if item.get(field) and item[field].lower() == search_name.lower()), None)
        return [item for item in collection if
                item.get(field) and item[field].lower() == search_name.lower()]

    def search_for_document_two_fields(self, collection: list, field1: str, field1_search_name: str,
                                       field2: str,
                                       field2_search_name: str, single_document=True):
        """
        searches for a particular document in given list of dicts
        Params:
            collection: The given collection
            field1 (str): The field which is to be searched
            field1_search_name (str): The search which is to be done on field1
            field2 (str): The field which is to be searched
            field2_search_name (str): The search which is to be done on field2
            single_document (bool): True if required to send a single document else list of documents
        Return:
            Document: The required document if found else None
        """
        if single_document:
            return next((item for item in collection
                         if (item.get(field1) and item[field1].lower() == field1_search_name.lower()
                             and item.get(field2) and item[
                                 field2].lower() == field2_search_name.lower())),
                        None)
        return [
            item for item in collection
            if (item.get(field1) and item[field1].lower() == field1_search_name.lower()
                and item.get(field2) and item[field2].lower() == field2_search_name.lower())
        ]

    async def publish_to_rabbitmq(self, data: Any, queue_name: str | None = None) -> None:
        """
        Publishes messages to a RabbitMQ queue asynchronously.

        This function connects to a RabbitMQ server using the provided credentials and URL.
        It then declares a durable queue named "user_audit_queue" and publishes messages
        from the `user_audit_buffer` to this queue. After successfully publishing the messages,
        it clears the buffer. If an error occurs during connection, channel creation, or message
        publishing, it logs the error.

        Returns:
        None

        Raises:
        aio_pika.exceptions.AMQPConnectionError: If there is an issue with connecting to the RabbitMQ server.
        aio_pika.exceptions.AMQPChannelError: If there is an issue with creating the channel.
        aio_pika.exceptions.AMQPError: For other general AMQP errors.
        Exception: For any other unexpected errors.
        """
        url = (
            f"amqp://{settings.rmq_username}:{settings.rmq_password}@{settings.rmq_url}:{settings.rmq_port}/"
            f"{settings.rmq_host}")
        try:
            connection = await aio_pika.connect_robust(url, heartbeat=60, timeout=10)
            async with connection:
                channel = await connection.channel()
                queue = await channel.declare_queue(queue_name, durable=True)
                message = aio_pika.Message(body=json.dumps(data).encode('utf-8'))
                await channel.default_exchange.publish(
                    message, routing_key=queue.name
                )
        except aio_pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Connection error: {e}")
        except aio_pika.exceptions.AMQPChannelError as e:
            logger.error(f"Channel error: {e}")
        except aio_pika.exceptions.AMQPError as e:
            logger.error(f"AMQP error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")

    def get_student_pipeline(self, emails: list) -> list:
        """
            Returns student pipeline
            Params:
                emails (list): list of students email ids
            Returns:
                pipeline (list): The pipeline to get student details
        """
        pipeline = [
            {
                "$match": {
                    "user_name": {"$in": emails}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "student_id": {"$toString": "$_id"},
                    "student_name": {
                        "$trim": {
                            "input": {
                                "$concat": [
                                    {"$ifNull": ["$basic_details.first_name", ""]},
                                    " ",
                                    {"$ifNull": ["$basic_details.middle_name", ""]},
                                    " ",
                                    {"$ifNull": ["$basic_details.last_name", ""]}
                                ]
                            }
                        },
                    },
                    "student_email": "$user_name"
                }
            }
        ]
        return pipeline

    def get_raw_data_pipeline(self, emails: list) -> list:
        """
            Returns raw data students pipeline
            Params:
                emails (list): list of raw data students email ids
            Returns:
                pipeline (list): The pipeline to get raw data student details
        """
        pipeline = [
            {
                "$match": {
                    "mandatory_field.email": {"$in": emails}
                }
            },
            {
                "$lookup": {
                    "from": "offline_data",
                    "localField": "offline_data_id",
                    "foreignField": "_id",
                    "as": "offline_data"
                }
            },
            {
                "$unwind": {
                    "path": "$offline_data"
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "student_id": {"$toString": "$_id"},
                    "student_name": "$other_field.full_name",
                    "student_email": "$mandatory_field.email",
                    "offline_data_id": {"$toString": "$offline_data_id"},
                    "offline_data_name": "$offline_data.data_name"
                }
            }
        ]
        return pipeline

    def get_user_pipeline(self, current_user: str) -> list:
        """
        Returns users pipeline
        Params:
            current_user (str): The email id of current user
        Returns:
            pipeline (list): The pipeline to get user details
        """
        user_pipeline = [
            {
                "$match": {
                    "user_name": current_user
                },
            },
            {
                "$project": {
                    "_id": 0,
                    "email": "$user_name",
                    "role": "$role.role_name",
                    "user_id": {"$toString": "$_id"},
                    "name": {
                        "$trim": {
                            "input": {
                                "$concat": [
                                    {"$ifNull": ["$first_name", ""]},
                                    " ",
                                    {"$ifNull": ["$middle_name", ""]},
                                    " ",
                                    {"$ifNull": ["$last_name", ""]}
                                ]
                            }
                        }
                    }
                }
            }
        ]
        return user_pipeline

    async def get_rabbitMQ_connection_channel(self):
        """
        Returns rabbitMq connection
        """
        url = f"amqp://{settings.rmq_username}:{settings.rmq_password}@{settings.rmq_url}:{settings.rmq_port}/{settings.rmq_host}"
        try:
            connection = await aio_pika.connect_robust(url, heartbeat=60, timeout=50)
            return connection
        except aio_pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Connection error: {e}")
        except aio_pika.exceptions.AMQPChannelError as e:
            logger.error(f"Channel error: {e}")
        except aio_pika.exceptions.AMQPError as e:
            logger.error(f"AMQP error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")

    def custom_serializer(self, obj):
        """
        Function to convert values into json
        """
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return str(obj)

    async def publish_email_sending_on_queue(self, data, priority=1, cc: bool = False):
        """
            Publishes an email sending request to RabbitMQ synchronously.
           This method sends the provided email data to a RabbitMQ queue, ensuring the request
           is published with the specified priority level.
           Params:
               data (dict): A dictionary containing the email sending request details.
               priority (int, optional): The priority of the task in the queue. Defaults to 1.
               cc (bool, optional): True if need to send cc else False.
           Returns:
               None
        """
        from app.database.configuration import DatabaseConfiguration
        emails = data.get("email_ids")
        results = await DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            self.get_student_pipeline(emails)).to_list(None)
        if cc:
            data.update({"cc": settings.email_cc})
        results = await DatabaseConfiguration().studentsPrimaryDetails.aggregate(self.get_student_pipeline(emails)).to_list(None)

        result = {result['student_email']: result for result in results}
        raw_data = await DatabaseConfiguration().raw_data.aggregate(
            self.get_raw_data_pipeline(emails)).to_list(None)
        raw_data = {raw['student_email']: {**raw, "is_raw_data": True} for raw in raw_data}
        result.update(raw_data)
        data["student_details"] = result
        current_user = data.get("current_user")
        user = await DatabaseConfiguration().user_collection.aggregate(
            self.get_user_pipeline(current_user)).to_list(None)
        data["user_details"] = user[0] if user else None
        template_id = data.get("template_id", None)
        if template_id not in ["", None, "None"]:
            template_details = await DatabaseConfiguration().template_collection.find_one(
                {"_id": ObjectId(template_id)}
            )
            data["template_details"] = template_details
        if data.get("data_segments"):
            data_segment_ids = data.get("data_segments", {}).keys()
            data_segments_details = self.get_data_segment_details(data_segment_ids=data_segment_ids)
            data["data_segments_details"] = data_segments_details
        connection = await self.get_rabbitMQ_connection_channel()
        queue = f"{settings.aws_env}/{settings.rmq_email_queue}"
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(queue, durable=True,
                                                arguments={"x-max-priority": 20})
            message = aio_pika.Message(
                body=json.dumps(data, default=self.custom_serializer).encode('utf-8'),
                delivery_mode=DeliveryMode.PERSISTENT,
                priority=priority
            )
            await channel.default_exchange.publish(
                message,
                routing_key=queue.name,
            )
            logger.info(f"Added job on Email service Queue")

    def get_sync_rabbitMQ_connection_channel(self):
        """
        Returns rabbitMq connection
        """
        url = f"amqp://{settings.rmq_username}:{settings.rmq_password}@{settings.rmq_url}:{settings.rmq_port}/{settings.rmq_host}"
        connection = pika.BlockingConnection(
            pika.URLParameters(url)
        )
        channel = connection.channel()
        return channel

    def sync_publish_email_sending_on_queue(self, data, priority=1, cc: bool = False):
        """
        Publish the email sending request data on rabbitMQ in sync way
        Params:
            data (dict): Data that is to be published on RabbitMQ
            priority (int): The priority of the task
            cc (bool, optional): Is CC to be added in mail
        Returns:
            None
        """
        from app.database.database_sync import DatabaseConfigurationSync
        emails = data.get("email_ids")
        if cc:
            data.update({"cc": settings.email_cc})
        current_user = data.get("current_user")
        results = list(DatabaseConfigurationSync().studentsPrimaryDetails.aggregate(
            self.get_student_pipeline(emails)))
        results = {result['student_email']: result for result in results}
        raw_data = list(DatabaseConfigurationSync().raw_data.aggregate(
            self.get_raw_data_pipeline(emails)))
        raw_data = {raw['student_email']: {**raw, "is_raw_data": True} for raw in raw_data}
        results.update(raw_data)
        data["student_details"] = results
        user = list(DatabaseConfigurationSync("master").user_collection.aggregate(
            self.get_user_pipeline(current_user)))
        data["user_details"] = user[0] if user else None
        template_id = data.get("template_id", None)
        if template_id not in ["", None, "None"]:
            template_details = DatabaseConfigurationSync().template_collection.find_one(
                {"_id": ObjectId(template_id)}
            )
            data["template_details"] = template_details
        channel = self.get_sync_rabbitMQ_connection_channel()
        queue = f"{settings.aws_env}/{settings.rmq_email_queue}"
        channel.queue_declare(queue=queue, durable=True, arguments={'x-max-priority': 20})
        channel.basic_publish(
            exchange='',
            routing_key=queue,
            body=json.dumps(data, default=self.custom_serializer).encode('utf-8'),
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent,
                priority=priority
            ))
        logger.info(f"Added job on Email service Queue")

    def get_data_segment_details(self, data_segment_ids):
        """
            Fetch details for a list of data segment IDs.

            Args:
                data_segment_ids (list): A list of unique identifiers (IDs) representing the data segments
                                         whose details need to be retrieved.

            Returns:
                list: A list containing the details of each data segment ID. The structure may vary
                      based on the implementation but generally includes metadata or attributes related
                      to each segment ID. For example:
                      {
                          "segment_id_1": {"key1": "value1", "key2": "value2"},
                          "segment_id_2": {"key1": "value1", "key2": "value2"},
                          ...
                      }
        """
        from app.database.database_sync import DatabaseConfigurationSync
        data_segment_ids = [ObjectId(id) for id in data_segment_ids]
        pipeline = [
            {
                "$match": {
                    "_id": {"$in": data_segment_ids}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "data_segment_id": {"$toString": "$_id"},
                    "data_type": "$module_name",
                    "segment_type": 1,
                    "data_segment_name": 1
                }
            }
        ]
        data_segments_details = list(
            DatabaseConfigurationSync().data_segment_collection.aggregate(pipeline))
        data_segments_details = {data_segment['data_segment_id']: data_segment for data_segment in
                                 data_segments_details}
        return data_segments_details

    async def check_dashboard_type(self, dashboard_type: str):
        """
        Check the dashboard type and return the corresponding value.

        Args:
            dashboard_type (str): The dashboard type to check.

        Returns:
            str: The corresponding value for the given dashboard type.
        """
        if dashboard_type not in ["admin_dashboard", "student_dashboard"]:
            raise CustomError(f"Invalid dashboard type. Must be either"
                              f" 'admin_dashboard' or 'student_dashboard'.")

    def is_empty(self, val):
        return val in (None, {}, [], "")

    def clean_data(self, data):
        if isinstance(data, dict):
            return {k: v for k, v in ((k, self.clean_data(v)) for k, v in data.items()) if
                    not self.is_empty(v)}
        if isinstance(data, list):
            return [v for v in (self.clean_data(i) for i in data) if not self.is_empty(v)]
        return data

    async def update_checkout_details(self, user_data: dict, present_time: any) -> None:
        """
            Updates the checkout details for a user.
            Params:
                user_data (dict): A dictionary containing user-related data.
                present_time (any): The current time or timestamp.
            Returns:
                None
        """
        from app.database.configuration import DatabaseConfiguration
        check_in_details = user_data.get("check_in_details", [])
        for i in range(len(check_in_details) - 1, -1, -1):
            if check_in_details[i].get("check_in") and not check_in_details[i].get("check_out",
                                                                                   None):
                check_in_time = check_in_details[i].get("check_in")
                total_mins = int((present_time - check_in_time).total_seconds() // 60)
                DatabaseConfiguration().checkincheckout.update_one({
                    "user_id": ObjectId(user_data.get("user_id")),
                    "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                    f"check_in_details.{i}.check_out": {"$exists": False},
                }, {
                    "$set": {
                        f"check_in_details.{i}.check_out": present_time,
                        f"check_in_details.{i}.total_mins": total_mins,
                        "last_checkout": present_time,
                        "current_stage": "CheckOut"
                    }
                })

    async def update_login_details(self, user_id: ObjectId, user: dict, device: str,
                                   device_info: str, ip_address: str) -> None:
        """
            Updates the login details for a user.

            Params:
                user_id (ObjectId): The unique identifier of the user.
                user (dict): A dictionary containing user-related data.
                device (str): The type of device used for login.
                device_info (str): Additional information about the device.
                ip_address (str): The IP address of the user.

            Returns:
                None
        """
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        from app.database.configuration import DatabaseConfiguration
        user_data = await DatabaseConfiguration().checkincheckout.find_one({
            "user_id": ObjectId(user_id),
            "date": date
        })
        if user_data:
            update_data = {}
            if "login_details" in user_data and user_data.get("login_details"):
                last_entry = user_data.get("login_details", [])[-1]
                if "logout" not in last_entry:
                    last_entry["logout"] = datetime.datetime.utcnow()
                    last_entry["total_mins"] = (last_entry["logout"] - last_entry[
                        "login"]).total_seconds() // 60
                user_data.get("login_details", []).append({"login": datetime.datetime.utcnow()})
                update_data.update({
                    "login_details": user_data.get("login_details")
                })
            update_data.update({
                "current_stage": "LogIn",
                "last_logout": None,
                f"live_on_{device}": True
            })
            await DatabaseConfiguration().checkincheckout.update_one({"_id": user_data.get("_id")},
                                                                     {"$set": update_data}
                                                                     )
        else:
            await DatabaseConfiguration().checkincheckout.insert_one({
                "user_id": user_id,
                "date": date,
                "user_details": {
                    "name": utility_obj.name_can(user),
                    "user_id": user_id,
                    "role_id": user.get("role", {}).get("role_id"),
                    "role_name": user.get("role", {}).get("role_name"),
                    "user_name": user.get("user_name")
                },
                f"live_on_{device}": True,
                f"{device}_login_details": {
                    "timestamp": datetime.datetime.utcnow(),
                    "ip_address": ip_address,
                    "device_info": device_info
                },
                "current_stage": "LogIn",
                "first_login": datetime.datetime.utcnow(),
                "login_details": [{"login": datetime.datetime.utcnow()}]
            })

    async def cache_descendant_mongo_ids(self, role_id: str | None = None):
        """
        Cache the descendant role IDs for a given role or all roles.

        If a specific `role_id` is provided, this function retrieves all descendant role IDs
        from the database for that role and stores them in Redis under the 'role_descendants' hash.
        If no `role_id` is provided, it computes descendant mappings for all roles and updates Redis
        with the entire mapping in a single operation.

        Params:
            role_id (str | None): Optional Mongo ID of the role. If provided, only that role's
                                  descendant data is fetched and cached. If not, all role hierarchies
                                  are processed.

        Returns:
            dict: A mapping of role Mongo IDs to their descendant role Mongo ID lists.

        Raises:
            HTTPException: If the given `role_id` has no corresponding data in the database.
        """
        from app.dependencies.oauth import get_redis_client, is_testing_env
        from app.database.motor_base import pgsql_conn
        db = await pgsql_conn.get_db_session()
        redis_client = get_redis_client()
        redis_key = "role_descendants"
        if role_id:
            sql = text("""
                WITH RECURSIVE descendants AS (
                    SELECT id AS root_role_id, id AS descendant_id
                    FROM roles
                    WHERE mongo_id = :mongo_id
                    UNION ALL
                    SELECT d.root_role_id, r.id
                    FROM descendants d
                    JOIN roles r ON r.parent_id = d.descendant_id
                )
                SELECT 
                    root_roles.mongo_id AS root_mongo_id,
                    ARRAY_AGG(DISTINCT child_roles.mongo_id) AS descendant_mongo_ids
                FROM descendants d
                JOIN roles root_roles ON root_roles.id = d.root_role_id
                JOIN roles child_roles ON child_roles.id = d.descendant_id
                WHERE child_roles.mongo_id IS NOT NULL AND root_roles.mongo_id IS NOT NULL
                    AND child_roles.id != root_roles.id 
                GROUP BY root_roles.mongo_id
            """)
            result = await db.execute(sql, {"mongo_id": role_id})
            row = result.fetchone()
            if row:
                value = json.dumps({"descendant_ids": row.descendant_mongo_ids})
                if redis_client and not is_testing_env():
                    await redis_client.hset(redis_key, row.root_mongo_id, value)
                return json.loads(value)
            raise HTTPException(status_code=404, detail="No role found or no descendants.")
        else:
            sql = text("""
                WITH RECURSIVE descendants AS (
                    SELECT id AS root_role_id, id AS descendant_id
                    FROM roles
                    UNION ALL
                    SELECT d.root_role_id, r.id
                    FROM descendants d
                    JOIN roles r ON r.parent_id = d.descendant_id
                )
                SELECT 
                    root_roles.mongo_id AS root_mongo_id,
                    ARRAY_AGG(DISTINCT child_roles.mongo_id) AS descendant_mongo_ids
                FROM descendants d
                JOIN roles root_roles ON root_roles.id = d.root_role_id
                JOIN roles child_roles ON child_roles.id = d.descendant_id
                WHERE root_roles.mongo_id IS NOT NULL AND child_roles.mongo_id IS NOT NULL
                    AND child_roles.id != root_roles.id 
                GROUP BY root_roles.mongo_id
            """)
            result = await db.execute(sql)
            row_data = result.fetchall()
            redis_mapping, return_data = {}, {}
            for row in row_data:
                data = {"descendant_ids": row.descendant_mongo_ids}
                redis_mapping[row.root_mongo_id] = json.dumps(data)
                return_data[row.root_mongo_id] = data["descendant_ids"]
            if not is_testing_env():
                await redis_client.delete(redis_key)
                await redis_client.hset(redis_key, mapping=redis_mapping)
            return return_data

    def flatten_features(self, features):
        """
        Recursively collect all feature IDs in this features dict and nested features,
        return a dict with feature_id as key and empty dict {} as value.
        """
        flat = {}
        for feat_id, feat_data in features.items():
            if not isinstance(feat_data, dict):
                continue
            flat[feat_id] = {
                k: v for k, v in feat_data.items() if k != "features"
            }
            # Recursively include nested features
            nested = feat_data.get("features")
            if isinstance(nested, dict):
                flat.update(self.flatten_features(nested))
        return flat

    async def transform_data(self, data):
        """
        Given the whole 'data' dict, transform each top-level user key by
        flattening its features with recursion.
        """
        result = {}
        for obj_id, menus in data.items():
            result[obj_id] = self.flatten_features(menus)
        return result

    async def fetch_store_cache_features(self, collection_name: str, field: str = None,
                                         update_data: bool = False,
                                         role_id: str | None = None,
                                         college_id: str | None = None):
        """
        Retrieves role menu feature configurations from Redis cache or MongoDB,
        and stores them in Redis if not cached.

        This function first attempts to retrieve role-specific
        menu data from Redis using the provided `collection_name`
        and optional `field`. If not found in cache, it queries MongoDB's
        `role_collection` to fetch and structure
        the menu data for each role.

        The MongoDB aggregation:
        - Filters documents with non-empty `menus` fields.
        - Filters menu items that are objects and have a non-empty `feature_id`.
        - Transforms each document into a key-value mapping using its `_id` as the key.
        - Merges all documents into a single dictionary under the `data` field.
        - If `college_id` is provided, it queries the `college_roles` collection instead.

        The resulting dictionary is cached in Redis with a default TTL.

        Params:
            collection_name (str): The name used to construct the Redis cache key.
            field (str, optional): An optional key to extract a specific role's menu configuration.
            update_data (bool, optional): If True, forces an update of the cache even if data exists.
            college_id (str | None, optional): If provided, queries the `college_roles` collection instead

        Returns:
            dict: The role menu configuration data for the specified `field`, or an empty dict if not found.

        Raises:
            HTTPException: If any unexpected error occurs during MongoDB aggregation or Redis interaction.
        """
        from app.database.configuration import DatabaseConfiguration
        from app.dependencies.oauth import get_collection_from_cache
        try:
            match_stage = {"$match": {"menus": {"$exists": True, "$ne": {}}}}
            if field:
                data = None
                if not update_data:
                    data = await get_collection_from_cache(collection_name, field)
                if data:
                    return data
                match_stage["$match"]["_id"] = ObjectId(role_id)
            pipeline = [
                match_stage,
                {
                    "$addFields": {
                        "menus": {
                            "$arrayToObject": {
                                "$filter": {
                                    "input": {"$objectToArray": "$menus"},
                                    "as": "menuItem",
                                    "cond": {
                                        "$and": [
                                            {"$eq": [{"$type": "$$menuItem.v"}, "object"]},
                                            {
                                                "$gt": [
                                                    {
                                                        "$strLenCP": {
                                                            "$ifNull": [
                                                                "$$menuItem.v.feature_id",
                                                                "",
                                                            ]
                                                        }
                                                    },
                                                    0,
                                                ]
                                            },
                                        ]
                                    },
                                }
                            }
                        }
                    }
                },
                {"$match": {"menus": {"$ne": {}}}},
                {"$project": {"_id": 0, "k": {"$toString": "$_id"}, "v": "$menus"}},
                {"$replaceRoot": {"newRoot": {"$arrayToObject": [[{"k": "$k", "v": "$v"}]]}}},
                {"$group": {"_id": None, "data": {"$mergeObjects": "$$ROOT"}}},
                {"$project": {"_id": 0, "data": 1}}
            ]
            if college_id:
                role_menus = await DatabaseConfiguration().college_roles.aggregate(
                    pipeline).to_list(
                    length=None)
            else:
                role_menus = await DatabaseConfiguration().role_collection.aggregate(
                    pipeline).to_list(
                    length=None)
            role_menus = role_menus[0].get("data", {}) if role_menus else {}
            role_menus = await self.transform_data(role_menus)
            await self.store_data_in_redis(role_menus, collection_name=collection_name,
                                           update_data=update_data, college_id=college_id)
            if role_menus:
                return role_menus.get(role_id, {}) if field else role_menus
            return {}

        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis connection error while caching role menus: {e}")
        except redis.exceptions.TimeoutError as e:
            logger.error(f"Redis timeout error while caching role menus: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while caching role menus: {e}")
            raise HTTPException(status_code=400,
                                detail=f"Unexpected error while caching role menus: {e}")

    async def fetch_store_master_screen_features(self, collection_name: str, field: str = None):
        """
        Fetches master screen feature configurations from Redis cache or MongoDB, and stores them in Redis if not cached.

        This function attempts to retrieve screen features (field-level configurations) from Redis using the provided
        `collection_name` and optional `field`. If not found in cache, it performs an aggregation query on the
        `master_screens` collection in MongoDB to construct a key-value mapping of screen configuration features.

        The aggregation filters out entries without valid `feature_id`, constructs a unique key based on screen type,
        dashboard type, and either `college_id` or `client_id`, then transforms the data into a nested dictionary format.
        The results are cached in Redis with a default TTL.

        Params:
            collection_name (str): The base name of the collection to form the cache key.
            field (str, optional): An optional sub-key to extract a specific configuration from the full dataset.

        Returns:
            dict: The filtered and cached master screen features for the given field, or an empty dictionary if not found.

        Raises:
            HTTPException: If an unexpected error occurs during data fetching or caching.
        """
        from app.database.configuration import DatabaseConfiguration
        from app.dependencies.oauth import get_collection_from_cache
        try:
            pipeline = []
            if field:
                data = await get_collection_from_cache(collection_name, field)
                if data:
                    return data
                pipeline = [{"$match": {"college_id": ObjectId(field)}}]
            pipeline.extend([
                {
                    "$addFields": {
                        "filteredFeatures": {
                            "$arrayToObject": {
                                "$filter": {
                                    "input": {"$objectToArray": "$$ROOT"},
                                    "as": "item",
                                    "cond": {
                                        "$gt": [
                                            {"$strLenCP": {"$ifNull": ["$$item.v.feature_id", ""]}},
                                            0
                                        ]
                                    }
                                }
                            }
                        }
                    }
                },
                {
                    "$addFields": {
                        "key": {
                            "$cond": [
                                {"$ifNull": ["$college_id", False]},
                                {
                                    "$concat": [
                                        "$screen_type", "/",
                                        "$dashboard_type", "/",
                                        {"$toString": "$college_id"}
                                    ]
                                },
                                {
                                    "$cond": [
                                        {"$ifNull": ["$client_id", False]},
                                        {"$concat": [
                                            "$screen_type", "/",
                                            "$dashboard_type", "/",
                                            {"$toString": "$client_id"}
                                        ]},
                                        {"$concat": ["$screen_type", "/", "$dashboard_type"]}
                                    ]
                                }
                            ]
                        }
                    }
                },
                {
                    "$project": {
                        "key": 1,
                        "value": "$filteredFeatures"
                    }
                },
                {
                    "$replaceRoot": {
                        "newRoot": {
                            "$arrayToObject": [[{"k": "$key", "v": "$value"}]]
                        }
                    }
                },
                {"$group": {"_id": None, "data": {"$mergeObjects": "$$ROOT"}}},
                {"$project": {"_id": 0, "data": 1}}
            ])

            master_features = await DatabaseConfiguration().master_screens.aggregate(
                pipeline).to_list(length=None)
            master_features = master_features[0].get("data", {}) if master_features else {}
            master_features = await self.transform_data(master_features)
            await self.store_data_in_redis(master_features)
            if master_features:
                field_name = f"{collection_name}"
                if field:
                    field_name += f"/{field}"
                data_obj = master_features.get(field_name, {})
                return data_obj
            return {}

        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis connection error while caching role menus: {e}")
        except redis.exceptions.TimeoutError as e:
            logger.error(f"Redis timeout error while caching role menus: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while caching role menus: {e}")
            raise HTTPException(status_code=400,
                                detail=f"Unexpected error while caching role menus: {e}")

    async def store_data_in_redis(
            self,
            data: dict,
            collection_name: str = None,
            ttl: int = 3600,
            update_data: bool = False,
            college_id: str | None = None
    ):
        """
        Stores a dictionary of data in Redis with optional TTL and namespacing.

        For each key-value pair in the `data` dictionary, this function generates a Redis key
        using the environment and university name (via `settings.aws_env` and `utility_obj.get_university_name_s3_folder()`),
        optionally appending a collection name. If the key does not already exist in Redis, it sets the key
        with the JSON-serialized value and applies a time-to-live (TTL).

        Uses a Lua script to ensure atomicity: the key is only set if it does not already exist.

        Params:
            data (dict): The dictionary of key-value pairs to be stored in Redis.
            collection_name (str, optional): An optional collection name to be included in the Redis key.
            ttl (int, optional): Time-to-live for the Redis keys, in seconds. Defaults to 3600 seconds (1 hour).

        Returns:
            None
        """
        from app.dependencies.oauth import get_redis_client
        redis_client = get_redis_client()
        if not redis_client or not data:
            return

        lua_script = """
            if redis.call('exists', KEYS[1]) == 0 then
              redis.call('set', KEYS[1], ARGV[1])
              redis.call('expire', KEYS[1], tonumber(ARGV[2]))
              return 1
            else
              return 0
            end
        """

        async with redis_client.pipeline(transaction=True) as pipe:
            for key_suffix, value in data.items():
                if value:
                    if collection_name:
                        cache_key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/{collection_name}/{key_suffix}"
                        if college_id:
                            cache_key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/{collection_name}/{college_id}/{key_suffix}"
                    else:
                        cache_key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/{key_suffix}"
                    value_json = json.dumps(value)
                    if update_data:
                        pipe.set(cache_key, value_json)
                        pipe.expire(cache_key, ttl)
                    else:
                        pipe.eval(lua_script, 1, cache_key, value_json, str(ttl))
            await pipe.execute()

    async def merge_values(self, data: dict, data2: dict, bool_check: bool = False):
        """
        Merge two dictionaries, updating values in data from data2 where keys exist in data.

        Params:
            data (dict): The first dictionary (base dictionary that will be updated).
            data2 (dict): The second dictionary (source of updates).
            bool_check (bool): A boolean flag to check for boolean values.

        Returns:
            dict: A new dictionary with updated values from data2 where keys exist in data.
        """
        result = data.copy()
        for feature_id in result:  # Only iterate through keys that exist in data
            if feature_id not in data2:
                if bool_check is False:
                    feature_data = result[feature_id]
                    feature_data["visibility"] = False
                continue  # Skip if feature_id doesn't exist in data2

            feature_data = result[feature_id]
            feature_data2 = data2[feature_id]

            # Handle simple fields
            for key in feature_data:
                if key not in feature_data2:
                    continue  # Skip if key doesn't exist in data2

                if key == 'permissions':
                    merged_permissions = {}
                    for perm_key in feature_data.get('permissions', {}):
                        if perm_key in feature_data2.get('permissions', {}):
                            if feature_data2['permissions'][perm_key] is bool_check:
                                merged_permissions[perm_key] = bool_check
                            else:
                                merged_permissions[perm_key] = feature_data['permissions'][perm_key]
                        else:
                            merged_permissions[perm_key] = feature_data['permissions'][perm_key]
                    feature_data['permissions'] = merged_permissions
                elif key == 'features':
                    if 'features' in feature_data2:
                        merged_sub_features = await self.merge_values(
                            feature_data.get('features', {}),
                            feature_data2.get('features', {}),
                            bool_check=bool_check
                        )
                        feature_data['features'] = merged_sub_features
                else:
                    if isinstance(feature_data2[key], bool):
                        if feature_data2[key] is bool_check:
                            feature_data[key] = bool_check
                    else:
                        feature_data[key] = feature_data2[key]

        return result

    async def mapped_feature_permissions(
            self,
            data: dict,
            user: dict,
    ):
        """
        Map the role permissions for a user.

        Params:
            data (dict): A dictionary containing the role permissions.
            user (dict): A dictionary containing the user details.

        Returns:
            dict: A dictionary containing the mapped role permissions.
        """
        from app.database.motor_base_singleton import MotorBaseSingleton
        master_data = MotorBaseSingleton.get_instance().master_data
        is_college = False
        college_data = {}
        if user.get("associated_colleges", []):

            college_id_master = master_data.get("college_id")

            for college_id in user.get("associated_colleges", []):
                if str(college_id) == str(college_id_master):
                    is_college = True
                    break

            if not is_college:
                raise CustomError(message="College ID not found in associated colleges.")

            college_data = await self.fetch_store_master_screen_features(
                "college_screen/admin_dashboard", field=str(college_id_master))

            if not college_data:
                logger.warning(
                    f"College screen not available for college id {college_id_master}")

        if user.get("assign_group_permissions", []):
            for group in user.get("assign_group_permissions", []):
                group_menus = await self.fetch_store_cache_features("role_features",
                                                                    group.get("group_id"),
                                                                    role_id=group.get("group_id"))
                if not group_menus:
                    raise DataNotFoundError(message="Group")
                data = await self.merge_values(
                    data=data, data2=group_menus, bool_check=True)

        if is_college and college_data:
            data = await self.merge_values(data=data, data2=college_data, bool_check=False)

        return data

    async def get_user_feature_permissions(
            self,
            user: dict,
            dashboard_type: str = "admin_dashboard",
            college_id: str | None = None
    ):
        """
        Get the role permissions for a user.

        Params:
            user (dict): A dictionary containing the user details.

        Returns:
            dict: A dictionary containing the role permissions.
        """
        if dashboard_type == "admin_dashboard":
            role_id = str(user.get("role", {}).get("role_id"))
            field = role_id
            college_id = college_id
            if user.get("associated_colleges", []):
                college_id = str(user.get("associated_colleges")[0])
                field = f"{college_id}/{role_id}"
            roles_features = await self.fetch_store_cache_features(
                "role_features", field=field, college_id=college_id, role_id=role_id)
            roles_features = await self.mapped_feature_permissions(
                data=roles_features, user=user)
        else:
            college_id = str(user.get("college_id")) if user.get("college_id") else None
            roles_features = await self.fetch_store_master_screen_features(
                collection_name=f"college_screen/{dashboard_type}", field=college_id)

        if not roles_features:
            raise DataNotFoundError(message="Role permissions")

        data = json.dumps(roles_features, cls=CustomJSONEncoder)
        return json.loads(data)

    async def update_role_features(self, role_id):
        """
        Updates the cached role features and clears related user dashboard feature caches in Redis.

        This method performs the following steps:
        1. Updates and stores role-specific feature data in Redis using `fetch_store_cache_features`.
        2. Retrieves all users associated with the specified role from the database.
        3. Deletes Redis keys for allowed features for each user across both 'admin' and 'student' dashboards,
           ensuring updated feature permissions take effect.

        Params:
            role_id (str): The ID of the role whose features are being updated.

        Raises:
            HTTPException (400): If any error occurs while updating role features or deleting Redis keys.
        """
        from app.database.configuration import DatabaseConfiguration
        from app.dependencies.oauth import get_redis_client
        try:
            roles_features = await self.fetch_store_cache_features("role_features", role_id,
                                                                   update_data=True)
            user_roles = await DatabaseConfiguration().user_collection.find(
                {"role.role_id": ObjectId(role_id)}).to_list(length=None)
            redis_client = get_redis_client()
            if redis_client:
                key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/allowed_features"
                for user in user_roles:
                    user_name = user.get("user_name")
                    for dashboard in ["admin", "student"]:
                        redis_key = f"{key}/{dashboard}_dashboard/{user_name}"
                        await redis_client.delete(redis_key)
        except Exception as e:
            raise HTTPException(status_code=400,
                                detail="Something went wrong while updating user allowed features")


# create instance of class
utility_obj = Utility()
