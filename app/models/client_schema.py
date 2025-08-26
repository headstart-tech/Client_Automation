"""
This File Contains Schema Related to Client CURD Operation

"""
from typing import List, Optional

from pandas.io.clipboard import clipboard_set
from pydantic import BaseModel, EmailStr, HttpUrl, Field, field_validator, model_validator, ValidationError
from datetime import datetime
from bson import ObjectId
from app.models.client_automation_schema import address_details


class POC(BaseModel):
    """
    Schema for Point of Contact
    """
    name: Optional[str]
    email: Optional[EmailStr]
    mobile_number: Optional[str] = Field(pattern=r"^[1-9]\d*$", min_length=10, max_length=10, default=None)

class StatusInfo(BaseModel):
    """
    Schema for Status Information
    """
    isActivated: Optional[bool] = True
    activationDate: Optional[datetime] = Field(default_factory=datetime.now)
    deActivationDate: Optional[datetime] = None

class S3Config(BaseModel):
    """
    Schema for S3 Configuration
    """
    username: Optional[str]
    aws_access_key_id: Optional[str]
    aws_secret_access_key: Optional[str]
    region_name: Optional[str]
    assets_bucket_name: Optional[str]
    reports_bucket_name: Optional[str]
    public_bucket_name: Optional[str]
    student_documents_name: Optional[str]
    report_folder_name: Optional[str]
    download_bucket_name: Optional[str]
    demo_base_bucket_url: Optional[str]
    dev_base_bucket_url: Optional[str]
    prod_base_bucket_url: Optional[str]
    stage_base_bucket_url: Optional[str]
    demo_base_bucket: Optional[str]
    dev_base_bucket: Optional[str]
    prod_base_bucket: Optional[str]
    stage_base_bucket: Optional[str]
    base_folder: Optional[str]

    @model_validator(mode='before')
    @classmethod
    def validate_urls(cls, value):
        """
        Validate the URL
        """
        if value.get("demo_base_bucket_url"):
            HttpUrl(value.get("demo_base_bucket_url"))
        if value.get("dev_base_bucket_url"):
            HttpUrl(value.get("dev_base_bucket_url"))
        if value.get("prod_base_bucket_url"):
            HttpUrl(value.get("prod_base_bucket_url"))
        if value.get("stage_base_bucket_url"):
            HttpUrl(value.get("stage_base_bucket_url"))
        return value

class CollpollConfig(BaseModel):
    """
    Schema for Collpoll Configuration
    """
    aws_access_key_id: Optional[str]
    aws_secret_access_key: Optional[str]
    region_name: Optional[str]
    s3_bucket_name: Optional[str]
    collpoll_url: Optional[str]
    collpoll_auth_security_key: Optional[str]

    @field_validator("collpoll_url", mode='before')
    @classmethod
    def validate_url(cls, v):
        """
        Validate the URL
        """
        if v:
            HttpUrl(v)
        return v

class SMSConfig(BaseModel):
    """
    Schema for SMS Configuration
    """
    username_trans: Optional[str]
    username_pro: Optional[str]
    password: Optional[str]
    authorization: Optional[str]
    sms_send_to_prefix: Optional[str]

class MeiliSearchConfig(BaseModel):
    """
    Schema for MeiliSearch Configuration
    """
    meili_server_host: Optional[str]
    meili_server_master_key: Optional[str]

    @field_validator("meili_server_host", mode='before')
    @classmethod
    def validate_url(cls, v):
        """
        Validate the URL
        """
        if v:
            HttpUrl(v)
        return v

class TextractConfig(BaseModel):
    """
    Schema for Textract Configuration
    """
    textract_aws_access_key_id: Optional[str]
    textract_aws_secret_access_key: Optional[str]
    textract_aws_region_name: Optional[str]

class WhatsAppCredential(BaseModel):
    """
    Schema for WhatsApp Configuration
    """
    send_whatsapp_url: Optional[str]
    generate_whatsapp_token: Optional[str]
    whatsapp_username: Optional[str]
    whatsapp_password: Optional[str]
    whatsapp_sender: Optional[str] = Field(pattern=r"^[1-9]\d*$", min_length=12, max_length=12)

    @model_validator(mode='before')
    @classmethod
    def validate_urls(cls, value):
        """
        Validate the URL
        """
        if value.get("send_whatsapp_url"):
            HttpUrl(value.get("send_whatsapp_url"))
        if value.get("generate_whatsapp_token"):
            HttpUrl(value.get("generate_whatsapp_token"))
        return value

class CacheRedisConfig(BaseModel):
    """
    Schema for Cache Redis Configuration
    """
    host: Optional[str]
    port: Optional[int]
    password: Optional[str]

class RazorpayConfig(BaseModel):
    """
    Schema for Razorpay Configuration
    """
    razorpay_api_key: Optional[str]
    razorpay_secret: Optional[str]
    razorpay_webhook_secret: Optional[str]
    partner: Optional[bool]
    x_razorpay_account: Optional[str]

class RabbitMQCredential(BaseModel):
    """
    Schema for RabbitMQ Configuration
    """
    rmq_host: Optional[str]
    rmq_password: Optional[str]
    rmq_url: Optional[str]
    rmq_username: Optional[str]
    rmq_port: Optional[str]

class ZoomCredentials(BaseModel):
    """
    Schema for Zoom Configuration
    """
    client_id: Optional[str]
    client_secret: Optional[str]
    account_id: Optional[str]

class ClientModel(BaseModel):
    """
    Schema for Client Information
    """
    client_name: Optional[str] = Field(min_length=3, max_length=50)
    client_email: Optional[EmailStr]
    client_phone: Optional[str] = Field(pattern=r"^[1-9]\d*$", min_length=10, max_length=10)
    assigned_account_managers: Optional[List[str]] = []
    address: Optional[address_details] = Field(default={})
    websiteUrl: Optional[str] = Field(default=None)
    POCs: Optional[List[POC]] = Field(default=[])

    @field_validator("assigned_account_managers", mode='before')
    def validate_account_managers(cls, v):
        """
        Validate account managers
        """
        if v:
            for account_manager in v:
                if not ObjectId.is_valid(account_manager):
                    raise ValueError("Invalid account manager id")
        return v

    @field_validator("websiteUrl", mode='before')
    def validate_url(cls, v):
        """
        Validate the URL
        """
        if v:
            HttpUrl(v)
        return v



class ClientUpdateModel(BaseModel):
    """
    Schema for Client Update Information
    """
    client_name: Optional[str] = Field(min_length=3, max_length=50, default=None)
    client_email: Optional[EmailStr] = Field(default=None)
    client_phone: Optional[str] = Field(pattern=r"^[1-9]\d*$", min_length=10, max_length=10, default=None)
    address: Optional[address_details] = Field(default=None)
    websiteUrl: Optional[str] = Field(default=None)
    POCs: Optional[List[POC]] = Field(default=None)

    @field_validator("websiteUrl", mode='before')
    def validate_url(cls, v):
        """
        Validate the URL
        """
        if v:
            HttpUrl(v)
        return v


class ClientConfigurationModel(BaseModel):
    s3: Optional[S3Config] = Field(default={})
    collpoll: Optional[CollpollConfig] = Field(default={})
    sms: Optional[SMSConfig] = Field(default={})
    meilisearch: Optional[MeiliSearchConfig] = Field(default={})
    aws_textract: Optional[TextractConfig] = Field(default={})
    whatsapp_credential: Optional[WhatsAppCredential] = Field(default={})
    rabbit_mq_credential: Optional[RabbitMQCredential] = Field(default={})
    zoom_credentials: Optional[ZoomCredentials] = Field(default={})

    class Config:
        """
        Configuration for Schema
        """
        populate_by_name = True
        arbitrary_types_allowed = True

class SystemFields(BaseModel):
    """
    Schema for System Fields which are Generated by System & Added to Client Information
    """
    student_dashboard_form: Optional[str] = None
    student_dashboard_screen: Optional[str] = None
    admin_dashboard_screen: Optional[str] =None
    college_ids: Optional[list] = []
    created_by: str
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)

    class Config:
        """
        Configuration for Schema
        """
        arbitrary_types_allowed = True

class ClientDetailsResponse(BaseModel):
    id: Optional[str] = Field(alias="_id")
    client_name: Optional[str] = None
    client_email: Optional[EmailStr] = None
    client_phone: Optional[str] = None
    assigned_account_managers: Optional[List] = []
    address: Optional[dict] = None
    websiteUrl: Optional[str] = None
    POCs: Optional[List] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    statusInfo: Optional[StatusInfo] = None
    college_ids: Optional[List[str]] = []
    student_dashboard: Optional[dict] = None
    client_screen: Optional[dict] = None
    can_create_college: Optional[bool] = None

    class Config:
        extra = "ignore"