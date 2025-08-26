"""
This file contains class and functions for create zoom meet.
"""
from app.core.utils import utility_obj
from datetime import datetime
from zoomus import ZoomClient


class ZoomMeet:
    """
    Contains function which useful for create zoom meet.
    """

    async def create_zoom_meet(
            self, start_datetime: datetime, emails: list,
            zoom_credentials: dict, host_emails, duration):
        """
        Create a zoom meet.

        Params:
            start_datetime (datetime): Start datetime of meet in datetime format.
            emails (list): A list which contains invitees email ids.
            zoom_credentials (dict): A dictionary which contains zoom
                 credentials which required to create new access token.
             host_emails (str): Multiple host email ids separated by
                semi-colon (;). It can contains publisher email ids.
            duration (int): Duration of meet in minutes.

        Returns:
            dict: A dictionary which contains zoom details.
        """
        invitees = [
            {
                "email": invitee
            } for invitee in emails
        ]

        try:
            start_datetime = start_datetime.strftime("%Y-%m-%d %H:%M")
            meeting_details = {
                "agenda": "My Meeting",
                "default_password": False,
                "duration": duration,
                "password": await utility_obj.generate_random_otp(),
                "settings": {
                    "allow_multiple_devices": True,
                    # "alternative_hosts": host_emails,
                    # "alternative_hosts_email_notification": True,
                    "approval_type": 2,
                    "auto_recording": "cloud",
                    "calendar_type": 1,
                    "close_registration": True,
                    "encryption_type": "enhanced_encryption",
                    "focus_mode": True,
                    "host_video": True,
                    "join_before_host": False,
                    "meeting_authentication": False,
                    "meeting_invitees": invitees,
                    "email": emails,
                    "mute_upon_entry": False,
                    "participant_video": True,
                    "private_meeting": True,
                    "registrants_confirmation_email": True,
                    "registrants_email_notification": True,
                    "registration_type": 1,
                    "show_share_button": True,
                    "waiting_room": True,
                    "host_save_video_order": True,
                    "alternative_host_update_polls": True
                },
                "start_time": datetime.strptime(start_datetime, "%Y-%m-%d %H:%M"),
                "timezone": "Asia/Kolkata",
                "topic": "My Meeting",
                "type": 2,
                "user_id": "me"
            }
            client = ZoomClient(zoom_credentials.get('client_id'),
                                zoom_credentials.get('client_secret'),
                                api_account_id=zoom_credentials.get(
                                    'account_id'))
            response = client.meeting.create(**meeting_details)
            data = response.json()
            return {"meeting_link": data.get("join_url"),
                    "passcode": data.get("password"), "data": data}
        except Exception as e:
            raise e
