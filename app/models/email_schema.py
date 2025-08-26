"""
This file contain schemas related to email
"""
from pydantic import BaseModel


class EmailWebhook(BaseModel):
    """
     Schema for email webhook
     """
    message_id: str
    action_type: str = None
    event_type: str = None
    to_email: str = None
    from_email: str = None
    email_send_date: str = None
    email_send_time: str = None
    event_date: str = None
    event_time: str = None
    event_status: str = None
    event_desc: str = None
    message_tag1: str = None
    message_tag2: str = None
    message_tag3: str = None
    event_code: str = None
    ip: str = None
