"""
This file contain schemas related to create/update template
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EmailType(str, Enum):
    """
    Schema of email type
    """

    default = "default"
    promotional = "promotional"
    transactional = "transactional"


class EmailProvider(str, Enum):
    """
    Schema of email provider
    """

    default = "default"
    karix = "karix"
    amazon_ses = "amazon_ses"


class EmailCategory(str, Enum):
    """
    Schema of email category
    """

    default = "default"
    forget_password = "forget_password"
    welcome = "welcome"
    login = "login"
    payment = "payment"
    otp = "otp"
    advertisement = "advertisement"


class SMSCategory(str, Enum):
    """
    Schema of email category
    """

    default = "default"
    otp = "otp"


class UserDetails(BaseModel):
    """
    Schema for user details
    """
    type: Optional[str | None] = None
    name: Optional[str | None] = None
    id: Optional[str | None] = None


class InteractiveButtonTemplateOptionData(BaseModel):
    """
    Schema for Interactive button template option data
    """

    type: str = Field(
        None, description="It must be 'cta' or 'quick_reply'",
        example="cta quick_reply"
    )
    nature: str = Field(
        None, description="It must be 'static' or 'dynamic'",
        example="static dynamic"
    )
    url: str = Field(
        None, description="Button redirect URL."
    )


class TemplateSchema(BaseModel):
    """
    Schema for Template create/update
    """

    sender_email_id: str = Field(
        None,
        description="Sender email id should be mandatory for email templates",
        example="sender@headstart.biz"
    )
    reply_to_email: str = Field(
        None,
        description="Reply to email can be added in the email template creation",
        example="reply@headstart.biz"
    )
    template_type: str = Field(
        None,
        description="Template type should be any of the following: email, sms and whatsapp",
        example="email",
    )
    template_id: str = Field(
        None,
        description="Template id should be any of the following: whatsapp",
        example="45656452",
    )
    template_name: str = Field(
        None,
        description="Enter name of the template if sms template, give pre define sms_sender_name",
        example="string",
    )
    content: str = Field(
        None,
        description="Enter template content. Content of template can be of following type: HTML, string etc",
        example="string",
    )
    template_json: dict = Field(None, description="Enter template json",
                                example={})
    tags: list[str] = Field(
        None, description="Enter tags for template", example=["string"]
    )
    is_published: bool = Field(
        False,
        description="If you want to publish template then send value True",
        example=False,
    )
    email_type: EmailType = Field(
        None,
        description="Enter email type, it can be default, promotional and transactional",
    )
    email_provider: EmailProvider = Field(
        None,
        description="Enter email provider, it can be default, karix and amazon_ses",
    )
    email_category: str = Field(
        None,
        description="Enter email category, it can be default, forget_password, welcome, email, login, payment and otp",
    )
    dlt_content_id: str = Field(
        None, description="Enter dlt_content_id, pass only when template_type is sms"
    )
    subject: str = Field(
        None,
        description="Enter subject of email, pass only when template_type is email",
    )
    sms_type: str = Field(
        None,
        description="Enter sms type, there are 3 type 1. service implicit, service explicit, promotional",
    )
    sms_category: SMSCategory = Field(
        None,
        description="Enter sms category, it can be otp",
    )
    sender: str = Field(
        None,
        description="Enter sender name or number",
    )
    template_type_option: str = Field(
        None,
        description="Enter Template type option - 'interactive_button', 'media_attachments' or 'text_only'",
        example="interactive_button media_attachments text_only",
    )
    add_template_option_url: list[InteractiveButtonTemplateOptionData] = Field(
        None,
        description="Enter Template option url list for 'interactive_button'"
    )
    attachmentType: str = Field(
        None,
        description="Enter attachment type (video, image, pdf) in case of user select template type "
                    "option media_attachments.",
    )
    attachmentURL: str = Field(
        None,
        description="Enter attachment url in case of user select template type option media_attachments.",
    )
    select_profile_role: list[str | None] = Field(
        None, description="Enter list of profile role who can access template"
    )
    select_members: list[UserDetails] = Field(
        None, description="Enter list of users who can access the template"
    )
    b_url: str = Field(
        None, description="Button redirect URL."
    )
    attachment_document_link: list[str | None] = Field(
        None, description="Enter list of documents which should be added in the attachment of email"
    )


class OtpTemplateSchema(BaseModel):
    """
    Schema for create/update otp template
    """

    template_name: str = Field(
        None, description="Enter the given pre define sms sender name", example="APOLOC"
    )
    content: str = Field(
        None,
        description="Enter template content. Content of template can be of following type: HTML, string etc",
        example="string",
    )
    dlt_content_id: str = Field(
        None, description="Enter dlt_content_id, pass only when template_type is sms"
    )
    sender: str = Field(
        None,
        description="Enter sender name or number",
    )
    sms_type: str = Field(
        None,
        description="Enter sms type, there are 3 type 1. service implicit, service explicit, promotional",
    )


class ActivateTemplate(BaseModel):
    """
    Schema for activate template
    """

    template_id: str = Field(
        ..., description="Enter template id if you want to activate template"
    )


class button(BaseModel):
    """
    Name of the button
    """

    button_title: Optional[str] = None
    description: Optional[str] = None


class button_option(BaseModel):
    """
    Scheme for button showing selected option
    """

    button_list: Optional[bool] = None
    button_title: Optional[str] = None


class location_helper(BaseModel):
    """
    scheme for location helper of whatsapp
    """

    longitude: Optional[str] = None
    latitude: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None


class media_helper(BaseModel):
    """
    schema for media helper of whatsapp
    """

    content_type: Optional[str] = None
    caption: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None


class WhatsappTemplate(BaseModel):
    """
    Schema for whatsapp template
    """

    send_to: list[str]
    data_segments_ids: list[str] | None = None
    whatsapp_obj_id: Optional[str] = None
    template_id: Optional[str] = None
    template_content: Optional[str] = None
    whatsapp_button: list[button] = None
    list_button: Optional[button_option] = None
    location: Optional[location_helper] = None
    media: Optional[media_helper] = None


class AddMergeField(BaseModel):
    """
    Schema for add merge field.
    """

    field_name: str
    value: str
