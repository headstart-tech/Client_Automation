"""
This file contain class and functions related to send email
"""
import copy as cp
import inspect
import json
import os
import pathlib
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePath

import boto3
import requests
from bs4 import BeautifulSoup as bs
from bson import ObjectId
from fastapi import Request
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from requests.structures import CaseInsensitiveDict

from app.background_task.amazon_ses.configuration import SesMailSender, \
    SesDestination
from app.celery_tasks.celery_email_activity import email_activity
from app.core.background_task_logging import background_task_wrapper
from app.core.celery_app import celery_app
from app.core.custom_error import CustomError
from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, settings
from app.core.zoom_api_config import ZoomMeet
from app.database.configuration import DatabaseConfiguration
from app.database.database_sync import DatabaseConfigurationSync
from app.dependencies.jwttoken import Authentication
from app.dependencies.oauth import is_testing_env
from app.helpers.data_segment.data_segment_helper import \
    data_segment_automation
from app.helpers.report.pdf_configuration import PDFHelper
from app.helpers.unsubscribe_cache_helper import UnsubscribeHelper

logger = get_logger(name=__name__)


class EmailActivity:
    """
    Contain functions related to email activity
    """

    def get_updated_html(self, path, soup):
        """
        Get updated html file content
        """
        with open(path, "w", encoding='utf-8') as f:
            f.write(soup.prettify())
        with open(path, "r", encoding="utf-8") as f:
            html_file = f.read()
        return html_file

    def get_data(self, file_path):
        """
        Return header, template file path and send mail url
        """
        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/json"
        path = Path(inspect.getfile(inspect.currentframe())).resolve()
        path = PurePath(path).parent.parent.parent
        path = PurePath(path, Path(rf"app/{file_path}"))
        return headers, path

    def store_email_activity(
            self,
            payload: dict,
            current_user: str,
            ip_address: str,
            response: any,
            email_type: str | None = None,
            provider: str | None = None,
            college_id: str | None = None,
            offered_applicants_info: list | None = None,
            scholarship_information: dict | None = None,
            offer_letter_information: dict | None = None,
            offer_letter_applicants: list | None = None
    ):
        """
        Store email activity data in DB.

        Params:
            - payload (dict): A dictionary which contains email information like email_list, content and template_id.
            - current_user (str): Email id of currently looged in user.
            - ip_address (str): IP address of current user.
            - response (any): Response which get after email send.
            - email_type (str | None): Default value: None. Either None or Type of email.
            - provider (str | None): Default value: None. Either None or Email service provider which useful for send
                mail.
            - college_id (str | None): Default value: None. Either None or unique identifier of college.
            - offer_letter_information (dict | None): Default value: None.
                A dictionary which contains offer letter information.
            - offer_letter_applicants (list | None): Default value: None. Either None or offer letter application ids.
            - offered_applicants_info (list | None): Default value: None. Either None or offered scholarship information.
            - scholarship_information (dict | None): Default value: None. Either None or scholarship information.

        Returns: None
        """
        if payload:
            toml_data = utility_obj.read_current_toml_file()
            if toml_data.get("testing", {}).get("test") is False:
                email_activity().storing_email_activity(
                    payload=payload,
                    current_user=current_user,
                    ip_address=ip_address,
                    transaction_details=[response],
                    email_type=email_type,
                    provider=provider,
                    college_id=college_id,
                    offer_letter_information=offer_letter_information,
                    offer_letter_applicants=offer_letter_applicants,
                    offered_applicants_info=offered_applicants_info,
                    scholarship_information=scholarship_information
                )

    async def update_list_by_data_segments_ids(
            self,
            data_segments_ids: list,
            update_list: list | None,
            data_segments: dict,
            college_id: str,
            emails: bool = False,
            numbers: bool = False,
            get_emails: bool = False
    ) -> tuple:
        """
        Update list by data segments ids.

        Params:
            data_segments_ids (list): A list which contains unique
                ids/identifiers of data segments.
            update_list (dict): A dictionary which need to update.
            data_segments (dict): A dictionary which useful for update
                data segments info.
            college_id (str): A unique id/identifier of college.
            emails (bool): A boolean value which useful for get student email
                ids.
            numbers (bool): A boolean value which useful for get student mobile
                numbers.

        Returns:
            tuple: A tuple which contains updated list and data segments info.

        Raises:
           ObjectIdInValid: An error which occurred when data segment id will
            be wrong.
        """
        data_segments_ids = list(
            set(
                [
                    ObjectId(_id)
                    for _id in data_segments_ids
                    if await utility_obj.is_length_valid(_id, "Data segment id")
                ]
            )
        )
        if data_segments_ids and update_list:
            data_segments = {data_segments_ids[0]: update_list}
        elif data_segments_ids:
            temp_list = []
            for _id in data_segments_ids:
                if (
                        await DatabaseConfiguration().data_segment_collection.find_one(
                            {"_id": _id}
                        )
                ) is not None:
                    temp_data = await data_segment_automation().student_mapped_details(
                        data_segment_id=str(_id),
                        college_id=college_id,
                        emails=emails,
                        numbers=numbers,
                        download=True
                    )
                    if temp_data:
                        temp_list.extend(temp_data)
                        data_segments.update({str(_id): temp_data})
            if get_emails:
                update_list = temp_list
            else:
                update_list = list({d.get("email_id"): d for d in temp_list}.values())
        return update_list, data_segments

    def store_student_communication_data(
            self,
            recipient: str,
            response: dict,
            event_type: str,
            event_status: str,
            event_name: str | None = None,
            email_type: str | None = None,
            provider: str | None = None,
            action_type: str | None = "system",
            data_segments: dict | None = None,
            current_user: str | None = None,
            template_id: str | None = None,
            college_id: str | None = None,
            add_timeline: bool | None = True,
            scholarship_information: dict | None = None,
            offer_letter_information: dict | None = None
    ):
        """
        Store student communication log data in DB.

        Params:
            -  recipient(str): Email id of user.
            - response(dict): The response we got after sending mail.
            - event_type(str): The type of event. It can have values like "email", "payment" e.t.c
            - event_status(str):The status of the communication event
            - event_name(str, optional):The name of the communication event ,Default is None.
            - email_type(str, optional):The type of email sent,Default is None.
            - provider(str, optional):The email service provider used to send the communication, Default is None.
            - action_type(str, optional):The type of action that triggered the communication
                Default is "system".
            - data_segments(dict, optional):Additional data segments or context related to the communication.
            - current_user(str, optional):The user or system that initiated the communication.Default is None.
            - template_id(str, optional):The ID of the template used for the communication, Default is None.
            - college_id(str, optional):The ID of the college associated with the communication. Default is None.
            - add_timeline(bool, optional):Whether to add communication event to the student's timeline.
                Default is True.
            - scholarship_information (dict | None): Default value: None. Either None or scholarship information.
            - offer_letter_information (dict | None): Default value: None.
                A dictionary which contains offer letter information.

        Returns: None
        """
        from app.celery_tasks.celery_communication_log import CommunicationLogActivity

        student = DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
            {"user_name": recipient}
        )
        if student:
            toml_data = utility_obj.read_current_toml_file()
            if toml_data.get("testing", {}).get("test") is False:
                CommunicationLogActivity().add_communication_log(
                    response=response,
                    student_id=str(student.get("_id")),
                    data_type="email",
                    event_type=event_type,
                    event_status=event_status,
                    event_name=event_name,
                    email_type=email_type,
                    provider=provider,
                    action_type=action_type,
                    current_user=current_user,
                    template_id=template_id,
                    college_id=college_id,
                    add_timeline=add_timeline,
                    scholarship_information=scholarship_information,
                    offer_letter_information=offer_letter_information
                )

    async def send_mail_helper(
            self,
            credentials,
            soup,
            path,
            subject,
            recipient,
            headers,
            files=None,
            event_type=None,
            event_status=None,
            event_name=None,
            payload=None,
            current_user=None,
            request=None,
            college_id=None,
    ):
        """
        Send mail to user
        """
        url = credentials.get("url", "")
        html_file = self.get_updated_html(path, soup)
        data = json.dumps(
            {
                "version": "1.0",
                "userName": credentials.get("username", ""),
                "password": credentials.get("password", ""),
                "includeFooter": "yes",
                "message": {
                    "custRef": "testrefid",
                    "subject": subject,
                    "fromEmail": credentials.get("from_email", ""),
                    "fromName": settings.university_name,
                    "replyTo": credentials.get("from_email", ""),
                    "recipient": recipient,
                    "html": html_file,
                },
            }
        )
        resp = requests.post(url, headers=headers, data=data, files=files)
        if resp.status_code != 200:
            logger.error(
                f"Sent Email to {recipient} failed with " f"{resp.status_code}"
            )
        ip_address = utility_obj.get_ip_address(request)
        self.store_email_activity(
            payload, current_user, ip_address, [resp.json()], college_id=college_id
        )
        self.store_student_communication_data(
            recipient=recipient,
            response=resp.json(),
            event_type=event_type,
            event_status=event_status,
            event_name=event_name,
            college_id=college_id,
        )
        return True

    def send_multiple_mail_to_users(
            self,
            credentials,
            subject,
            recipients,
            html_file,
            event_type=None,
            event_status=None,
            event_name=None,
            payload=None,
            current_user=None,
            ip_address=None,
            email_type=None,
            provider=None,
            action_type="system",
            template_id=None
    ):
        """
        Send mail to multiple recipients/user
        """
        template = {}
        if template_id:
            template = DatabaseConfigurationSync().template_collection.find_one({"_id": ObjectId(template_id)})
        url = credentials.get("url", "")
        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/json"
        data = json.dumps(
            {
                "version": "1.0",
                "userName": credentials.get("username", ""),
                "password": credentials.get("password", ""),
                "includeFooter": "yes",
                "message": {
                    "custRef": "testrefid",
                    "subject": subject,
                    "fromEmail": template.get("sender_email_id", "") if template and template.get("sender_email_id")
                    else credentials.get("from_email", ""),
                    "fromName": settings.university_name,
                    "replyTo": template.get("reply_to_email", "") if template and template.get("reply_to_email")
                    else credentials.get("from_email", ""),
                    "html": html_file,
                    "recipients": recipients,
                },
            }
        )
        resp = requests.post(url, headers=headers, data=data)
        if resp.status_code != 200:
            logger.error(
                f"Sent Email to {recipients} failed with " f"{resp.status_code}"
            )
        self.store_email_activity(
            payload, current_user, ip_address, [resp.json()], email_type, provider
        )
        for email in recipients:
            self.store_student_communication_data(
                email,
                resp.json(),
                event_type,
                event_status,
                event_name,
                email_type,
                provider,
                action_type,
            )
        return True

    def update_string_html_content(self, replacements, html_content):
        """
        Update string html content

        Params:
        replacements (dict): A dictionary containing the replacement data
        html_content (str): A html content in a string format

        Returns:
            html_content (str) - Modified html content in a string format
        """
        for placeholder, value in replacements.items():
            if value is not None and isinstance(value, str):
                html_content = html_content.replace(placeholder, value)
        return html_content

    async def send_interview_invitation_through_mail(
            self,
            request: Request,
            time: datetime,
            minutes: int,
            meeting_id: int | str,
            passcode: str,
            meeting_link: str,
            college: dict,
            email_ids: list,
            current_user: str,
            action_type="system",
            college_id=None,
    ):
        """
        Send
        request (Request): Useful for get ip_address of client.
        time (datetime): The start datetime of interview.
        minutes (int): Duration of interview.
        meeting_id (int | str): Meeting id of zoom.
        passcode (str): Passcode of interview.
        meeting_link: The meeting link of zoom.
        college (dict): A dictionary which contains college data.
        email_ids (list[str]): Email ids of users.
        current_user (str): An user_name of current user.
        invitees (list): A list which contains email ids of invitees.
        """
        ip_address = utility_obj.get_ip_address(request)
        MESSAGE = (
            "Dear User, your interview is "
            "scheduled. <br><br>"
            "<b>Interview details are given "
            "below:</b><br>Interview time: "
            f"{utility_obj.get_local_time(time)}"
            f"<br>Duration: {minutes} minutes<br>"
            f"Meeting Id: {meeting_id}<br>"
            f"Passcode: {passcode}<br><br>"
            f"You can use the following link to"
            f" join interview: "
            f"{meeting_link}<br><br>"
            f"Thank you & Regards,<br>"
            f"{college.get('name')}, "
            f"{college.get('address', {}).get('city')}"
        )
        final_emails = []
        for email_id in email_ids:
            extra_emails = await self.add_default_set_mails(email_id)
            final_emails.extend(extra_emails)
        email_ids = final_emails
        if not is_testing_env():
            await utility_obj.publish_email_sending_on_queue(data={
                "email_preferences": college.get("email_preferences", {}),
                "email_type": "transactional",
                "email_ids": email_ids,
                "subject": "Interview Schedule Info",
                "template": MESSAGE,
                "event_type": "email",
                "event_status": "send",
                "event_name": "Zoom meeting link",
                "current_user": current_user,
                "ip_address": ip_address,
                "payload": {"content": "Interview Schedule Info",
                            "email_list": email_ids},
                "attachments": None,
                "action_type": action_type,
                "college_id": college.get("id"),
                "priority": True,
                "data_segments": None,
                "template_id": None,
                "add_timeline": True,
                "environment": settings.environment,
            }, priority=15)

    async def create_zoom_meet_and_send_mail(
            self,
            is_student,
            application_ids,
            slot_data,
            college,
            user,
            request,
            current_user,
            action_type="system",
            college_id=None,
    ):
        """
        Create a zoom meet and send zoom details through mail.
        """
        try:
            meeting_id, passcode, invitees, meeting_link = 0, 0, [], ""
            user_name = user.get("user_name")
            time = slot_data.get("time")
            minutes = (slot_data.get("end_time") - time).total_seconds() // 60
            if (
                    meeting_details := await DatabaseConfiguration().meeting_collection.find_one(
                        {"slot_id": slot_data.get("_id")}
                    )
            ) is None:
                meeting_details = {}
            if not meeting_details:
                if is_student:
                    if slot_data.get("interview_mode") == "Online":
                        invitees, alternative_hosts = [], ""
                        for panelist_id in slot_data.get("take_slot", {}).get(
                                "panelist_ids", []
                        ):
                            host = (
                                await DatabaseConfiguration().user_collection.find_one(
                                    {"_id": panelist_id}
                                )
                            )
                            if host:
                                email = host.get("user_name")
                                invitees.append(email)
                                alternative_hosts += f"{email};"
                        invitees = [user_name] + invitees
                        zoom_meet_info = await ZoomMeet().create_zoom_meet(
                            slot_data.get("time"),
                            invitees,
                            college.get("zoom_credentials"),
                            alternative_hosts,
                            minutes,
                        )
                        if zoom_meet_info:
                            meeting_link = zoom_meet_info.get("meeting_link")
                            meeting_id = zoom_meet_info.get("data", {}).get("id")
                            passcode = zoom_meet_info.get("passcode")
                            await DatabaseConfiguration().meeting_collection.insert_one(
                                {
                                    "meeting_type": slot_data.get("slot_type"),
                                    "user_limit": slot_data.get("user_limit"),
                                    "panel_id": slot_data.get("panel_id"),
                                    "slot_id": slot_data.get("_id"),
                                    "panelists": slot_data.get("take_slot", {}).get(
                                        "panelist_ids"
                                    ),
                                    "start_time": time,
                                    "duration": minutes,
                                    "interview_list_id": slot_data.get(
                                        "interview_list_id"
                                    ),
                                    "applicants": slot_data.get("take_slot", {}).get(
                                        "application_ids"
                                    ),
                                    "available_slot": slot_data.get("available_slot"),
                                    "booked_user": slot_data.get("booked_user"),
                                    "interview_mode": "Online",
                                    "zoom_link": meeting_link,
                                    "meet_start_url": zoom_meet_info.get(
                                        "data", {}
                                    ).get("start_url"),
                                    "meeting_id": meeting_id,
                                    "passcode": passcode,
                                    "status": "Scheduled",
                                }
                            )
            else:
                meeting_link = meeting_details.get("zoom_link")
                meeting_id = meeting_details.get("meeting_id")
                passcode = meeting_details.get("passcode")
                invitees = [user.get("user_name")]
                await DatabaseConfiguration().meeting_collection.update_one(
                    {"slot_id": slot_data.get("_id")},
                    {
                        "$set": {
                            "panelists": slot_data.get("take_slot", {}).get(
                                "panelist_ids"
                            ),
                            "applicants": slot_data.get("take_slot", {}).get(
                                "application_ids"
                            ),
                            "available_slot": slot_data.get("available_slot"),
                            "booked_user": slot_data.get("booked_user"),
                        }
                    },
                )
            await self.send_interview_invitation_through_mail(
                request,
                time,
                minutes,
                meeting_id,
                passcode,
                meeting_link,
                college,
                invitees,
                current_user,
                action_type=action_type,
                college_id=college_id,
            )
            if is_student:
                for application_id in application_ids:
                    if (
                            application := await DatabaseConfiguration().studentApplicationForms.find_one(
                                {"_id": ObjectId(application_id)}
                            )
                    ) is None:
                        application = {}
                    slot_type = slot_data.get("slot_type")
                    slot_type_in_lower_case = slot_type.lower()
                    allocated_interview_lists = application.get("interview_list_id")
                    interview_list_id = slot_data.get("interview_list_id")
                    removed_lists = []
                    if allocated_interview_lists:
                        for interview_list in allocated_interview_lists:
                            if interview_list_id != interview_list:
                                allocated_interview_lists.remove(interview_list)
                                removed_lists.append(interview_list)
                    application_id = ObjectId(application_id)
                    await DatabaseConfiguration().studentApplicationForms.update_one(
                        {"_id": application_id},
                        {
                            "$set": {
                                "meetingDetails": {
                                    "slot_id": slot_data.get("_id"),
                                    "slot_type": slot_type,
                                    "booked_date": datetime.utcnow(),
                                    "slot_status": "Scheduled",
                                    "status": "Scheduled",
                                    "scheduled_date": time,
                                    "duration": minutes,
                                    "zoom_link": meeting_link,
                                    "meeting_id": meeting_id,
                                    "passcode": passcode,
                                },
                                "interview_list_id": allocated_interview_lists,
                                f"{slot_type_in_lower_case}_status.status": "Scheduled",
                                f"{slot_type_in_lower_case}_status."
                                f"scheduled_date": time,
                                "interviewStatus.status": "Scheduled",
                            }
                        },
                    )
                    await DatabaseConfiguration().interview_list_collection.update_many(
                        {
                            "_id": {"$in": removed_lists},
                            "application_ids": {"$eq": application_id},
                        },
                        {
                            "$pull": {
                                "application_ids": application_id,
                                "eligible_applications": application_id,
                            }
                        },
                    )
        except Exception as e:
            logger.error(f"Something went wrong. Error - {e}")

    async def send_username_password_to_user(
            self,
            user_name: str,
            password: str,
            first_name: str,
            email_preferences,
            request,
            event_type=None,
            event_status=None,
            event_name=None,
            payload=None,
            action_type="system",
            college_id=None,
    ):
        """
        Send login credentials to admin user through mail
        """
        headers, path = self.get_data(
            file_path="templates/send_username_password_to_user.html"
        )
        with open(path, "r", encoding="utf-8") as f:
            soup = bs(f, "html.parser")
            result = soup.find(id="A")
            result.string.replace_with(f"Email - {user_name}")
            result = soup.find(id="B")
            result.string.replace_with(f"Password - {password}")
            result = soup.find(id="welcome")
            result.string.replace_with(settings.university_name)
            result = soup.find(id="dear")
            result.string.replace_with(f"Dear - {first_name},")
            result = soup.find(id="log")
            result.string.replace_with(settings.university_name)
        html_file = self.get_updated_html(path, soup)
        email_ids = await self.add_default_set_mails(user_name)
        if not is_testing_env():
            await utility_obj.publish_email_sending_on_queue(data={
                "email_preferences": email_preferences,
                "email_type": "transactional",
                "email_ids": email_ids,
                "subject": "Login Credentials of User",
                "template": html_file,
                "event_type": event_type,
                "event_status": event_status,
                "event_name": event_name,
                "current_user": user_name,
                "ip_address": utility_obj.get_ip_address(request),
                "payload": payload,
                "attachments": None,
                "action_type": action_type,
                "college_id": college_id,
                "priority": True,
                "data_segments": None,
                "template_id": None,
                "add_timeline": True,
                "environment": settings.environment
            }, priority=20)

    async def send_onboarding_notification_email(
            self,
            entity_type: str,
            entity_data: dict,
            recipient_email: str,
            email_preferences,
            request,
            event_type=None,
            event_status=None,
            event_name=None,
            payload=None,
            action_type="system",
            college_id=None,
    ):
        """
        Unified function to send onboarding notification emails for both clients and colleges

        Args:
            entity_type (str): Type of entity - "client" or "college"
            entity_data (dict): Entity information dictionary with all details
            recipient_email (str): Email address of the recipient (usually admin)
            email_preferences (dict): Email preferences dictionary
            request (Any): request
            event_type (str): Event type
            event_status (str): Event status
            event_name (str): Event name
            payload (dict): Payload dictionary
            action_type (str): Action type
            college_id (str): College ID

        Returns:

        """
        headers, path = self.get_data(
            file_path="templates/unified_onboarding_template.html"
        )

        # Common fields mapping between college and client data structures
        field_mappings = {
            "client": {
                "name_field": "client_name",
                "email_field": "client_email",
                "phone_field": "client_phone",
                "type_display": "Client"
            },
            "college": {
                "name_field": "name",
                "email_field": "college_email",
                "phone_field": "mobile_number",
                "type_display": "College"
            }
        }

        mapping = field_mappings.get(entity_type.lower())
        if not mapping:
            raise CustomError("Invalid entity type")

        entity_name = entity_data.get(mapping["name_field"], "")
        entity_email = entity_data.get(mapping["email_field"], "")
        entity_phone = entity_data.get(mapping["phone_field"], "")

        address = entity_data.get("address", {})
        address_line_1 = address.get("address_line_1", "")
        address_line_2 = address.get("address_line_2", "")

        city = address.get("city_name", "")
        state = address.get("state_name", "")
        country = address.get("country_name", "")

        # Format city/state line
        city_state = f"{city}, {state}" if city and state else (city or state or "")

        original_content = ""
        with open(path, "r", encoding="utf-8") as f:
            soup = bs(f, "html.parser")
            original_content = cp.deepcopy(soup)

            # Update common identifiers
            result = soup.find(id="welcome")
            result.string.replace_with(settings.university_name)

            result = soup.find(id="dear")
            result.string.replace_with(f"Dear Admin,")

            result = soup.find(id="log")
            result.string.replace_with(settings.university_name)

            intro_text = soup.find(id="intro-text")
            intro_text.string.replace_with(
                f"We are pleased to inform you that a new {mapping['type_display'].lower()} has been successfully added to our system."
            )

            entity_header = soup.find(id="entity-header")
            entity_header.string.replace_with(f"{mapping['type_display']} Information:")

            soup.find(id="entity-name").string.replace_with(entity_name)
            soup.find(id="entity-email").string.replace_with(entity_email)
            soup.find(id="entity-phone").string.replace_with(entity_phone)

            entity_type_span = soup.find(id="entity-type")
            entity_type_span.string.replace_with(mapping["type_display"])

            if address_line_1:
                soup.find(id="address-line1").string.replace_with(address_line_1)
            else:
                soup.find(id="address-line1").decompose()

            if address_line_2:
                soup.find(id="address-line2").string.replace_with(address_line_2)
            else:
                soup.find(id="address-line2").decompose()

            soup.find(id="address-city-state").string.replace_with(city_state)
            soup.find(id="address-country").string.replace_with(country)

            if entity_type.lower() == "client":
                website_url = entity_data.get("websiteUrl", "")
                if website_url:
                    website_container = soup.find(id="website-container")
                    website_container["style"] = ""  # remove display:none
                    website_link = soup.find(id="entity-website")
                    website_link["href"] = website_url
                    website_link.string.replace_with(website_url)

                pocs = entity_data.get("POCs", [])
                if pocs:
                    for elem in soup.select(".poc-table"):
                        if 'class' in elem.attrs:
                            elem['class'].remove('poc-table')

                    poc_tbody = soup.find(id="poc-tbody")

                    for poc in pocs:
                        poc_row = soup.new_tag("tr")

                        name_td = soup.new_tag("td")
                        name_td.string = poc.get("name", "")
                        poc_row.append(name_td)

                        email_td = soup.new_tag("td")
                        email_td.string = poc.get("email", "")
                        poc_row.append(email_td)

                        phone_td = soup.new_tag("td")
                        phone_td.string = poc.get("mobile_number", "")
                        poc_row.append(phone_td)

                        poc_tbody.append(poc_row)

        html_file = self.get_updated_html(path, soup)

        if not is_testing_env():
            await utility_obj.publish_email_sending_on_queue(data={
                "email_preferences": email_preferences,
                "email_type": "transactional",
                "email_ids": [recipient_email],
                "subject": f"New {mapping['type_display']} Onboarded: {entity_name}",
                "template": html_file,
                "event_type": event_type,
                "event_status": event_status,
                "event_name": event_name,
                "current_user": recipient_email,
                "ip_address": utility_obj.get_ip_address(request),
                "payload": payload,
                "attachments": None,
                "action_type": action_type,
                "college_id": college_id,
                "priority": True,
                "data_segments": None,
                "template_id": None,
                "add_timeline": True,
                "environment": settings.environment
            }, priority=20)
        self.get_updated_html(path, original_content)


    async def add_lines_in_payment_invoice_pdf(self, pdf):
        """
        Add horizontal lines in the application PDF for separate section
        """
        pdf.line(240, 160, 240, 485)
        y1_points = [
            130,
            160,
            185,
            210,
            235,
            260,
            285,
            310,
            335,
            360,
            385,
            410,
            435,
            460,
            485,
            510,
        ]
        y2_points = [
            130,
            160,
            185,
            210,
            235,
            260,
            285,
            310,
            335,
            360,
            385,
            410,
            435,
            460,
            485,
            510,
        ]
        for y1_point, y2_point in zip(y1_points, y2_points):
            PDFHelper().add_line_in_pdf(
                pdf=pdf, x1_point=55, y1_point=y1_point, x2_point=490, y2_point=y2_point
            )

    async def generate_payment_invoice(self, data, file_name):
        """
        Generate payment invoice, store payment invoice in the AWS S3 Bucket
        then return public URL of payment invoice
        """
        pdf = canvas.Canvas("info.pdf", bottomup=0)

        pdf.setFillColorRGB(0, 0, 0)

        pdf.translate(40, 80)
        pdf.scale(1, -1)
        pdf.drawImage(settings.university_logo, 0, 0, width=100, height=70)

        pdf.scale(1, -1)
        pdf.translate(-40, -80)

        if data.get("college_name").lower() == "the apollo university":
            pdf.setFillColor(HexColor("#326872"))
            pdf.setFont("Helvetica-Bold", 13)
            pdf.drawCentredString(200, 50, data.get("college_name"))
            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawCentredString(200, 65, "Chittoor")
            pdf.setFont("Helvetica-Oblique", 8)
            pdf.drawCentredString(200, 75, "An initiative of Apollo Hospitals " "Group")

        pdf.setFillColorRGB(0, 0, 0)
        # pdf.setFont("Courier", 22)
        # pdf.drawCentredString(230, 150, "Online Payment Portal")

        pdf.setFont("Courier", 22)
        pdf.drawCentredString(280, 92, "Online Fee Payment")

        pdf.setLineWidth(0.1)
        pdf.roundRect(55, 100, 435, 460, 0)

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawCentredString(265, 120, "Application Fee Details")
        pdf.setFont("Helvetica-Bold", 8)

        # pdf.drawCentredString(370, 145, "Payment Confirmation")
        # pdf.drawCentredString(75, 155, "page")
        # pdf.drawCentredString(135, 155, "success")

        pdf.setFont("Helvetica", 10.5)
        pdf.drawString(65, 175, "Invoice Number :")
        pdf.setFont("Helvetica", 11.5)
        pdf.drawString(250, 175, data.get("invoice_number", ""))

        pdf.setFont("Helvetica", 10.5)
        pdf.drawString(65, 200, "Payment Status :")
        pdf.setFont("Helvetica-Bold", 10.5)
        pdf.drawString(250, 200, "success")

        pdf.setFont("Helvetica", 10.5)
        pdf.drawString(65, 225, "Payment Date :")
        pdf.drawString(
            250,
            225,
            f"{utility_obj.get_local_time(data.get('created_at'))}",
        )

        pdf.drawString(65, 250, "Order ID :")
        pdf.drawString(250, 250, data.get("order_id"))

        pdf.drawString(65, 275, "Payment ID :")
        pdf.drawString(250, 275, data.get("payment_id"))

        pdf.drawString(65, 300, "Student Name :")
        pdf.drawString(250, 300, data.get("student_name"))

        pdf.drawString(65, 325, "Student Email ID :")
        pdf.drawString(250, 325, data.get("student_email_id"))

        pdf.drawString(65, 350, "Mobile No :")
        pdf.drawString(250, 350, data.get("student_mobile_no"))

        pdf.drawString(65, 375, "Application No :")
        pdf.drawString(250, 375, data.get("application_number"))

        pdf.drawString(65, 400, "Degree :")
        pdf.drawString(250, 400, data.get("degree"))

        pdf.drawString(65, 425, "College Name :")
        pdf.drawString(250, 425, data.get("college_name"))

        pdf.drawString(65, 450, "Nationality :")
        nationality = data.get("nationality")
        if nationality:
            pdf.drawString(250, 450, data.get("nationality"))

        pdf.drawString(65, 475, "Application Fees :")
        pdf.drawString(250, 475, data.get("application_fees"))

        pdf.setFont("Helvetica-Bold", 10.5)
        pdf.drawString(65, 500, "Note : Application Fees are non-refundable.")

        pdf.setFont("Helvetica", 10.5)
        pdf.drawString(
            65,
            525,
            "You have successfully applied for examination and made the "
            "payment. Take a print",
        )
        pdf.drawString(
            65,
            540,
            "of out of receipt and keep it for your reference. "
            "Submit receipt copy to college.",
        )
        pdf.drawString(
            65,
            555,
            "Please visit the university website from time to time for "
            "announcements.",
        )

        await self.add_lines_in_payment_invoice_pdf(pdf=pdf)
        PDFHelper().save_pdf(pdf=pdf)
        s3 = settings.s3_client
        aws_env = settings.aws_env
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        base_bucket_url = getattr(settings, f"s3_{aws_env}_base_bucket_url")
        season_year = utility_obj.get_year_based_on_season()
        path = (
            f"{utility_obj.get_university_name_s3_folder()}/"
            f"{season_year}/{settings.s3_reports_bucket_name}/{file_name}"
        )
        with open("info.pdf", "rb") as f:
            s3.upload_fileobj(f, base_bucket, path)
        rem_file = pathlib.Path("info.pdf")
        rem_file.unlink()
        s3.put_object_acl(ACL="public-read", Bucket=base_bucket, Key="%s" % path)
        return f"{base_bucket_url}{path}"

    @background_task_wrapper
    async def application_submit(
            self,
            student: dict,
            application: dict,
            course: dict,
            college: dict,
            request: Request,
            event_type: str,
            event_status: str,
            event_name: str,
            email_preferences: str,
            college_id=None,
    ):
        """
        Send application submitted mail to student

        Params:
            student (dict): A dictionary containing student data.
            application (dict): A dictionary containing application data.
            course (dict): A dictionary containing course data.
            college (dict): A dictionary containing college data.
            request (Request): An object of class `Request` which useful for
            get/store user info.
            event_type (str): Type of event.
            event_status (str): Status of event.
            event_name (str): Name of event.
            email_preferences (str): Email preference name.
        """
        path = Path(inspect.getfile(inspect.currentframe())).resolve()
        path = PurePath(path).parent.parent.parent
        if course.get("is_pg", False):
            check_std_name = "graduation"
        else:
            check_std_name = "inter_school"
        secondary_details = (
            await DatabaseConfiguration().studentSecondaryDetails.find_one(
                {"student_id": student.get("_id")}
            )
        )
        if secondary_details is None:
            secondary_details = {}
        if (
                secondary_details.get("education_details", {})
                        .get(f"{check_std_name}_details", {})
                        .get("is_pursuing", False)
        ):
            file_path = "templates/application_submitted_after_details.html"
        else:
            file_path = "templates/application_submitted.html"
        path = PurePath(path, Path(rf"app/{file_path}"))
        with open(f"{path}", "r") as file:
            html_file = file.read()
        application_name = (
            f"{course.get('course_name')} in {application.get('spec_name1')}"
            if (application.get("spec_name1") != "" and application.get("spec_name1"))
            else f"{course.get('course_name')} Program"
        )
        standard = {"graduation": "UG", "inter_school": "12th"}
        student_basic_details = student.get("basic_details", {})
        replacements = {
            "{Institute Name}": college.get("name"),
            "{name}": student_basic_details.get("first_name", "").title(),
            "{education standard}": standard.get(check_std_name),
            "{application name}": application_name,
            "{application id}": str(application.get("custom_application_id")),
            "{contact email}": college.get("pocs", [{}])[0].get("email"),
            "{contact no}": college.get("pocs", [{}])[0].get("mobile_number"),
            "{Address}": college.get("address", {}).get("city"),
            "{website url}": college.get("website_url"),
            "{contact toll free no}": settings.contact_us_number,
            "{banner image}": settings.banner_image_url,
            "{email logo}": settings.email_logo
        }
        html_file = self.update_string_html_content(replacements, html_file)
        email = student.get("user_name")
        email_ids = await self.add_default_set_mails(email)
        if not is_testing_env():
            await utility_obj.publish_email_sending_on_queue(data={
                "email_preferences": email_preferences,
                "email_type": "transactional",
                "email_ids": email_ids,
                "subject": "Application Submitted",
                "template": html_file,
                "event_type": event_type,
                "event_status": event_status,
                "event_name": event_name,
                "current_user": email,
                "ip_address": utility_obj.get_ip_address(request),
                "payload": {"content": "Application Submitted", "email_list": email_ids},
                "attachments": None,
                "action_type": "user",
                "college_id": college_id,
                "data_segments": None,
                "template_id": None,
                "add_timeline": True,
                "priority": True,
                "environment": settings.environment,
            }, priority=10)

    @background_task_wrapper
    async def payment_successful(
            self,
            data: dict,
            event_type=None,
            event_status=None,
            event_name=None,
            email_preferences=None,
            request=None,
            college=None,
    ):
        """
        Send application payment successful mail to student
        """
        college_id = None
        if college:
            college_id = college.get("id")
        if data.get("invoice_number"):
            data["invoice_number"] = str(uuid.uuid4())
        unique_filename = utility_obj.create_unique_filename(extension=".pdf")
        student_first_name = data.pop("student_first_name")
        invoice_url = await self.generate_payment_invoice(
            data=data, file_name=unique_filename
        )
        data["invoice_url"] = invoice_url
        await DatabaseConfiguration().application_payment_invoice_collection.insert_one(
            data
        )
        await DatabaseConfiguration().payment_collection.update_one(
            {"payment_id": data.get("payment_id")},
            {"$set": {"reciept_url": invoice_url}}
        )
        template = await DatabaseConfiguration().template_collection.find_one(
            {"email_category": "payment", "active": True, "template_status": "enabled"}
        )
        subject = "Application Payment Successfully Done"
        if template:
            html_file = template.get("content")
            subject = template.get("subject")
            replacements = {
                "{Institute Name}": college.get("name"),
                "{name}": student_first_name.title(),
                "{fees}": data.get("application_fees"),
                "{application name}": data.get("degree"),
                "{application id}": data.get("custom_application_id"),
                "{payment id}": data.get("payment_id"),
                "{contact email}": college.get("pocs", [{}])[0].get("email"),
                "{contact no}": college.get("pocs", [{}])[0].get("mobile_number"),
                "{Address}": college.get("address", {}).get("city"),
                "{website url}": college.get("website_url"),
                "{contact toll free no}": college.get("pocs", [{}])[0].get(
                    "toll_free_number"
                ),
            }
            html_file = self.update_string_html_content(replacements, html_file)
        else:
            headers, path = self.get_data(
                file_path="templates/send_payment_successful_mail.html"
            )
            with open(path, "r", encoding="utf-8") as f:
                soup = bs(f, "html.parser")
                result = soup.find(id="logo")
                result.string.replace_with(settings.university_name)
                result = soup.find(id="name")
                result.string.replace_with(f"Dear " f"{student_first_name.title()},")
                result = soup.find(id="desc")
                result.clear()
                result.append(
                    bs(
                        f"{settings.payment_successful_mail_message}" f"{invoice_url}",
                        "html.parser",
                    )
                )
                result = soup.find(id="log")
                result.string.replace_with(settings.university_name)
            html_file = self.get_updated_html(path, soup)
        email = data.get("student_email_id")
        email_ids = await self.add_default_set_mails(email)
        if not is_testing_env():
            await utility_obj.publish_email_sending_on_queue(data={
                "email_preferences": email_preferences,
                "email_type": "transactional",
                "email_ids": email_ids,
                "subject": subject,
                "template": html_file,
                "event_type": event_type,
                "event_status": event_status,
                "event_name": event_name,
                "current_user": email,
                "ip_address": utility_obj.get_ip_address(request),
                "payload": {"content": "Send payment successful mail", "email_list": email_ids},
                "attachments": None,
                "action_type": "user",
                "college_id": college_id,
                "data_segments": None,
                "template_id": None,
                "add_timeline": True,
                "priority": True,
                "environment": settings.environment
            }, priority=10)

    def get_nested_value(self, dict_data: dict, nested_key: str):
        """
        Get the value of a field with/without iterate to the nested dictionary.

        Params:
            dict_data (dict): A dictionary which useful for update value of
                a field
            nested_key (str): A key which can contains nested field names
                separated by `.`

        Returns:
            Returns: Value of a field.
        """
        if "." in nested_key:
            keys = nested_key.split(".")
            value = dict_data
            for key in keys:
                value = value.get(key, {})
            if value == {}:
                value = ""
        else:
            value = dict_data.get(nested_key, "")
        return value

    def update_dictionary_key_by_value(self, update_dict: dict, db_data: dict) -> dict:
        """
        Update dictionary key value.
        """
        for update_key, update_value in update_dict.items():
            value = update_value.get("value")
            if value in ["", None]:
                value = self.get_nested_value(
                    db_data, update_value.get("collection_field_name")
                )
            update_dict[update_key] = value
        return update_dict

    def detect_and_validate_variables(
            self, template_content: str, college_id: ObjectId, student_email: str,
            whatsapp_functionality: bool = False
    ) -> str | tuple:
        """
        Detect variables from template message.

        Params:
            - template_content: Content of template.
            - college_id (ObjectId): An unique identifier of a college.
            - student_email: An email id of student.
            - whatsapp_functionality (bool): A boolean value which represents tasks performing for whatsapp or not.

       Returns:
            - str | tuple: Either A string value which represents updated template content (in case of sms or email)
                or tuple which contains template content and variable values (in case of whatsapp).
        """
        variable_values = ""

        # Regular expression to find variables like {username}
        variable_pattern = re.compile(r"{(.*?)}")

        # Find all the variables in the template content
        if whatsapp_functionality:
            detected_variables = variable_pattern.findall(template_content)
        else:
            detected_variables = set(variable_pattern.findall(template_content))
        if detected_variables:
            merge_fields = DatabaseConfigurationSync(
                database="master"
            ).template_merge_fields_collection.find_one({"college_id": college_id})
            if merge_fields:
                existing_fields_info = merge_fields.get("merge_fields", [])
                if existing_fields_info:
                    existing_fields = [
                        item.get("field_name") for item in existing_fields_info
                    ]
                    # Check if all detected variables exist in the mapping
                    # collection
                    (primary_fields, secondary_fields, student_secondary, counselor,
                     application_fields, student_application) = {}, {}, {}, {}, {}, {}
                    if (student_primary := DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                            {"user_name": student_email})) is None:
                        student_primary = {}
                    if (student_secondary := DatabaseConfigurationSync().studentSecondaryDetails.find_one(
                            {"student_id": student_primary.get("_id")})) is None:
                        student_secondary = {}
                    if (counselor := DatabaseConfigurationSync(
                            database="master").user_collection.find_one(
                        {"_id": student_primary.get("allocate_to_counselor", {}).get("counselor_id")}
                    )) is None:
                        counselor = {}
                    if (student_application := DatabaseConfigurationSync().studentApplicationForms.find_one(
                            {"student_id": student_primary.get("_id")})) is None:
                        student_application = {}
                    for field_name in detected_variables:
                        if field_name in existing_fields:
                            if field_name in ["Counselor Name", "Counselor Mobile Number"]:
                                if field_name == "Counselor Name":
                                    variable_values += f"~{utility_obj.name_can(counselor) if counselor else 'NA'}"
                                    primary_fields.get("{Counselor Name}", {}).update({
                                        "value": utility_obj.name_can(counselor) if counselor else "NA"})
                                if field_name == "Counselor Mobile Number":
                                    primary_fields.get("{Counselor Mobile Number}", {}).update({
                                        "value": str(counselor.get("mobile_number", "NA")) if counselor else "NA"})
                                    variable_values += f"~{str(counselor.get('mobile_number', 'NA')) if counselor else 'NA'}"
                                continue
                            field_index = existing_fields.index(field_name)
                            field_info = existing_fields_info[field_index]
                            collection_field_name = field_info.get("collection_field_name")
                            if field_info.get("collection_name") == "studentsPrimaryDetails":
                                field_value = field_info.get("value")
                                primary_fields.update(
                                    {
                                        f"{{{field_name}}}": {
                                            "collection_field_name": collection_field_name,
                                            "value": field_value,
                                        }
                                    }
                                )
                                if whatsapp_functionality:
                                    if field_value in ["", None]:
                                        field_value = self.get_nested_value(
                                            student_primary, collection_field_name
                                        )
                                    variable_values += f"~{field_value}"
                            elif field_info.get("collection_name") == "studentSecondaryDetails":
                                field_value = field_info.get("value")
                                secondary_fields.update(
                                    {
                                        f"{{{field_name}}}": {
                                            "collection_field_name": collection_field_name,
                                            "value": field_value,
                                        }
                                    }
                                )
                                if whatsapp_functionality:
                                    if field_value in ["", None]:
                                        field_value = self.get_nested_value(
                                            student_secondary, collection_field_name
                                        )
                                    variable_values += f"~{field_value}"
                            else:
                                field_value = field_info.get("value")
                                application_fields.update(
                                    {
                                        f"{{{field_name}}}": {
                                            "collection_field_name": collection_field_name,
                                            "value": field_value,
                                        }
                                    }
                                )
                    if not whatsapp_functionality and (len(primary_fields) >= 1 or len(secondary_fields) >= 1 or
                                                       len(application_fields) >= 1):
                        if student_primary:
                            if len(secondary_fields) >= 1:
                                if student_secondary:
                                    secondary_fields = (
                                        self.update_dictionary_key_by_value(
                                            secondary_fields, student_secondary
                                        )
                                    )
                            if len(primary_fields) >= 1:
                                primary_fields = self.update_dictionary_key_by_value(
                                    primary_fields, student_primary
                                )
                            if len(application_fields) >= 1:
                                application_fields = self.update_dictionary_key_by_value(
                                    application_fields, student_application
                                )
                        primary_fields.update(**secondary_fields, **application_fields)
                        template_content = self.update_string_html_content(
                            primary_fields, template_content
                        )
        if whatsapp_functionality:
            return template_content, variable_values
        return template_content

    async def send_message(
            self,
            to,
            subject,
            message,
            payload=None,
            current_user=None,
            ip_address=None,
            event_type=None,
            event_status=None,
            event_name=None,
            email_preferences=None,
            email_type=None,
            college_id=None,
            template_id=None,
            template=None
    ):
        """
        Send mail to user
        """
        email_activity_obj = EmailActivity()
        message = email_activity_obj.detect_and_validate_variables(
            message, ObjectId(college_id), to[0]
        )
        headers, path = email_activity_obj.get_data(
            file_path="templates/send_message.html"
        )
        with open(path, "w", encoding="ISO-8859–1"):
            soup = bs(message, "html.parser")
        html_file = email_activity_obj.get_updated_html(path, soup)
        if not is_testing_env():
            priority = False
            prior = 20
            if email_type != "promotional":
                priority = True
                prior = 1
            attachments = []
            documents = template.get("attachment_document_link", [])
            if template and documents:
                season = utility_obj.get_year_based_on_season()
                for document in documents:
                    file_name = PurePath(document).name
                    object_key = (
                        f"{utility_obj.get_university_name_s3_folder()}/"
                        f"{season}/"
                        f"{settings.s3_assets_bucket_name}/"
                        f"template-gallery/{file_name}"
                    )
                    attachments.append({
                        "file_name": file_name,
                        "object_key": object_key
                    })
            await utility_obj.publish_email_sending_on_queue(data={
                "email_preferences": email_preferences,
                "email_type": email_type,
                "email_ids": to,
                "subject": subject,
                "template": html_file,
                "event_type": event_type,
                "event_status": event_status,
                "event_name": event_name,
                "current_user": current_user,
                "ip_address": ip_address,
                "payload": payload,
                "attachments": attachments,
                "action_type": "system",
                "college_id": college_id,
                "data_segments": None,
                "template_id": str(template_id),
                "add_timeline": True,
                "priority": priority,
                "environment": settings.environment,
                "template_gallery": True
            }, priority=prior)

    async def reset_password_user(
            self,
            email,
            reset_password_url,
            event_type=None,
            event_status=None,
            event_name=None,
            payload=None,
            current_user=None,
            request=None,
            email_preferences=None,
            college_id=None
    ):
        """
        Send reset password mail to user
        """
        template = await DatabaseConfiguration().template_collection.find_one(
            {
                "email_category": "forget_password",
                "active": True,
                "template_status": "enabled",
            }
        )
        subject = "Reset Password"
        if template:
            html_file = template.get("content")
            subject = template.get("subject")
            replacements = {"{reset_password_link}": reset_password_url}
            html_file = self.update_string_html_content(replacements, html_file)
        else:
            headers, path = self.get_data(file_path="templates/reset_password.html")
            with open(path, "r", encoding="utf-8") as f:
                soup = bs(f, "html.parser")
                for a in soup.findAll("a"):
                    a["href"] = reset_password_url
            html_file = self.get_updated_html(path, soup)
        email_ids = await self.add_default_set_mails(email)
        payload["email_list"] = email_ids
        if not is_testing_env():
            await utility_obj.publish_email_sending_on_queue(data={
                "email_preferences": email_preferences,
                "email_type": "transactional",
                "email_ids": email_ids,
                "subject": subject,
                "template": html_file,
                "event_type": event_type,
                "event_status": event_status,
                "event_name": event_name,
                "current_user": current_user,
                "ip_address": utility_obj.get_ip_address(request) if request else request,
                "payload": payload,
                "attachments": None,
                "action_type": "system",
                "college_id": college_id,
                "data_segments": None,
                "template_id": None,
                "add_timeline": True,
                "priority": True,
                "environment": settings.environment
            }, priority=20)

    def send_upload_leads_details(
            self,
            email,
            first_name,
            data,
            email_preferences,
            ip_address,
            action_type="system",
            college_id=None
    ):
        """
        Send statistics of request to user through mail
        """
        headers, path = self.get_data(
            file_path="templates/send_upload_leads_details.html"
        )
        with open(path, "r", encoding="utf-8") as f:
            soup = bs(f, "html.parser")
            result = soup.find(id="logo")
            result.string.replace_with(settings.university_name)
            result = soup.find(id="name")
            result.string.replace_with(f"Dear {first_name.title()},")
            result = soup.find(id="log")
            result.string.replace_with(settings.university_name)
            result = soup.find(id="desc")
            result.clear()
            result.append(
                bs(
                    f"Your request of upload leads successfully completed. "
                    f"The details of request is given below:<br><br><b>{data}"
                    f"</b>",
                    "html.parser",
                )
            )
            logger.info("Statistics of request send to user through mail.")
        html_file = self.get_updated_html(path, soup)
        if not is_testing_env():
            utility_obj.sync_publish_email_sending_on_queue({
                "email_preferences": email_preferences,
                "email_type": "transactional",
                "email_ids": [email],
                "subject": "Request of Upload Leads",
                "template": html_file,
                "event_type": "email",
                "event_status": "sent",
                "event_name": "Statistics of request of upload leads",
                "current_user": email,
                "ip_address": ip_address,
                "payload": {"content": "Statistics of request of upload leads",
                            "email_list": [email]},
                "attachments": None,
                "action_type": action_type,
                "college_id": college_id,
                "data_segments": None,
                "template_id": None,
                "add_timeline": True,
                "priority": True,
                "environment": settings.environment
            })

    def get_provider_details(self, email_preferences: dict, email_type: str) -> dict:
        """
        Get provider details which will useful for send email
        """
        provider_id = email_preferences.get(f"{email_type}_provider")
        if not provider_id:
            logger.info("Provider details not found.")
            return {}
        provider = DatabaseConfigurationSync(
            database="master"
        ).provider_collection.find_one({"_id": ObjectId(str(provider_id))})
        if not provider:
            return {}
        if provider.get("status") != "Active":
            logger.info("Provider is deactivate.")
            return {}
        return provider

    def send_email_using_amazon_ses(
            self,
            credentials: dict,
            email_ids: list,
            subject: str,
            text: any,
            html: any,
            event_type: str,
            event_status: str,
            event_name: str,
            current_user: any,
            ip_address: any,
            email_type: str,
            provider: str,
            attachments: any = None,
            action_type: str = "system",
            college_id: str | None = None,
            data_segments: dict | None = None,
            template_id: str | None = None,
            add_timeline: bool | None = True,
            offer_letter_information: dict | None = None,
            scholarship_information=None
    ) -> None:
        """
        Send email using amazon ses and get return then store response in DB.

        Params:
            - credentials (dict): A dictionary which contains email send credentials.
            - email_ids (list): List of email ids of receivers.
            - subject (str): Subject of email.
            - text (str): Content of email.
            - html (str): Content of email.
            - event_type (str): Type of event.
            - event_status (str): Status of event.
            - event_name (str): Name of event.
            - current_user (str): User who is sending email.
            - ip_address (str): IP address of user.
            - email_type (str): Type of email. Possible values are promotional, transactional and default.
            - provider (str): Name of provider who is sending mail.
            - attachments (any): Default value: None. Attachments to send with email.
            - action_type (str | None): Default value: system. Action type of email. Possible value are system and manual.
            - college_id (str | None): Default value: None. Unique identifier of college.
            - data_segments (dict | None): Default value: None. A dictionary which contains data segments information.
            - template_id (str | None): Default value: None. Unique identifier of template.
            - add_timeline (bool | None): Default value: None. Whether to add timeline or not.
            - offer_letter_information (dict | None): Default value: None.
                A dictionary which contains offer letter information.

        Returns: None
        """
        client = boto3.client(
            "ses",
            region_name=credentials.get("region", ""),
            aws_access_key_id=credentials.get("access_key_id", ""),
            aws_secret_access_key=credentials.get("secret_access_key", ""),
        )

        template = {}
        if template_id:
            template = DatabaseConfigurationSync().template_collection.find_one({"_id": ObjectId(template_id)})

        ses_email = SesMailSender(client)
        source = template.get("sender_email_id", "") if template and template.get(
            "sender_email_id") else credentials.get("source", "")
        offer_letter_applicants, add_update_offer_letter_info = [], False
        if offer_letter_information:
            offer_letter_applicants = offer_letter_information.pop("application_ids", [])
            add_update_offer_letter_info = offer_letter_information.pop("add_update_offer_letter_info", False)

        offered_applicants_info = []
        if scholarship_information:
            offered_applicants_info = scholarship_information.pop("offered_applicants_info", [])

        for _id, email_id in enumerate(email_ids):
            updated_html = self.add_footer_for_unsubscribe(html, email_id) if email_type == "promotional" else html
            updated_html = self.detect_and_validate_variables(
                updated_html, ObjectId(college_id), email_id
            ) if college_id else updated_html
            if attachments:
                response = ses_email.send_email_with_attachments(
                    source,
                    [email_id],
                    subject,
                    updated_html,
                    [],  # TODO: CC make dynamic in case of attachment for different requests
                    reply_tos=template.get("reply_to_email", "") if template and template.get(
                        "reply_to_email") else source,
                    configuration_set_name=credentials.get(
                        "configuration_set_name", ""
                    ),
                    attachment_files=attachments,
                )
            else:
                temp_email = [email_id]
                destination = SesDestination(temp_email)
                response = ses_email.send_email(
                    source,
                    destination,
                    subject,
                    text,
                    updated_html,
                    [template.get("reply_to_email", "") if template and template.get("reply_to_email") else source],
                    credentials.get("configuration_set_name", ""),
                )

            self.store_email_activity(
                {"email_list": [email_id], "content": text, "template_id": ""},
                current_user,
                ip_address,
                response,
                email_type=email_type,
                provider=provider,
                college_id=college_id,
                offer_letter_information=offer_letter_information,
                offer_letter_applicants=offer_letter_applicants,
                offered_applicants_info=offered_applicants_info,
                scholarship_information=scholarship_information
            )

            self.store_student_communication_data(
                email_id,
                response,
                event_type,
                event_status,
                event_name,
                email_type=email_type,
                provider=provider,
                action_type=action_type,
                data_segments=data_segments,
                current_user=current_user,
                template_id=template_id,
                add_timeline=add_timeline,
                offer_letter_information=offer_letter_information,
                scholarship_information=scholarship_information
            )
            db_config = DatabaseConfigurationSync()
            if offer_letter_applicants:
                application_id = offer_letter_applicants[_id]
                application_data = DatabaseConfigurationSync().studentApplicationForms.find_one(
                    {"_id": ObjectId(application_id)})
                if application_data:
                    offer_letter_list_id = offer_letter_information.get("offer_letter_list_id")
                    obj_offer_letter_list_id = ObjectId(offer_letter_list_id)
                    db_config.offer_letter_list_collection.update_one(
                        {"_id": obj_offer_letter_list_id},
                        {"$inc": {"communication_info.total_communication": 1, "communication_info.email_sent": 1}})
                    if add_update_offer_letter_info:
                        current_datetime = datetime.now(timezone.utc)
                        offer_letter_information.update(
                            {"offer_letter_list_id": obj_offer_letter_list_id,
                             "template_id": ObjectId(offer_letter_information.get("template_id")),
                             "provided_at": current_datetime,
                             "provided_by_id": ObjectId(offer_letter_information.get("provided_by_id")),
                             "message_id": response.get("MessageId"),
                             "offer_letter_sent_on": current_datetime})
                        exist_offer_letter_sent_info = application_data.get("offer_letter_sent_info", {})

                        if exist_offer_letter_sent_info and isinstance(exist_offer_letter_sent_info, list):
                            exist_offer_letter_sent_info.insert(0, offer_letter_information)
                        else:
                            exist_offer_letter_sent_info = [offer_letter_information]
                        db_config.studentApplicationForms.update_one(
                            {"_id": ObjectId(application_id)},
                            {"$set": {"is_offer_letter_sent": True,
                                      f"offer_letter_list_info.{offer_letter_list_id}.status": "Sent",
                                      "offer_letter_sent_count": application_data.get("offer_letter_sent_count", 0) + 1,
                                      "offer_letter_sent_info": exist_offer_letter_sent_info}})
                        db_config.offer_letter_list_collection.update_one(
                            {"_id": ObjectId(offer_letter_list_id)}, {"$inc": {"offer_letter_sent": 1}})

            if offered_applicants_info:
                application_information = offered_applicants_info[_id]
                if application_information and isinstance(application_information, dict):
                    application_id = application_information.pop("application_id", None)
                    obj_application_id = ObjectId(application_id)
                    application_data = db_config.studentApplicationForms.find_one(
                        {"_id": obj_application_id})
                    if application_data:
                        scholarship_id = ObjectId(scholarship_information.get("scholarship_id"))
                        scholarship_name = scholarship_information.get("scholarship_name")
                        current_datetime = datetime.now(timezone.utc)
                        scholarship_information.update(
                            {**application_information,
                             "scholarship_id": scholarship_id,
                             "template_id": ObjectId(scholarship_information.get("template_id")),
                             "provided_by_id": ObjectId(scholarship_information.get("provided_by_id")),
                             "message_id": response.get("MessageId") if isinstance(response, dict) else response,
                             "provided_at": current_datetime,
                             "scholarship_letter_sent_on": current_datetime})
                        exist_offered_scholarship_info = application_data.get("offered_scholarship_info", {})
                        if exist_offered_scholarship_info and isinstance(exist_offered_scholarship_info, dict):
                            update_data = exist_offered_scholarship_info.copy()
                            all_scholarship_info = exist_offered_scholarship_info.get("all_scholarship_info", [])
                            all_scholarship_info.insert(1, scholarship_information)
                            update_data.update({"all_scholarship_info": all_scholarship_info})
                        else:
                            update_data = {"all_scholarship_info": [scholarship_information]}
                        if scholarship_name == "Custom scholarship":
                            update_data.update({"custom_scholarship_applied": True,
                                                "custom_scholarship_info": scholarship_information})
                        db_config.studentApplicationForms.update_one(
                            {"_id": obj_application_id},
                            {"$set": {"offered_scholarship_info": update_data,
                                      "is_scholarship_letter_sent": True,
                                      "scholarship_letter_sent_count":
                                          application_data.get("scholarship_letter_sent_count", 0) + 1}})
                        if ((scholarship := db_config.scholarship_collection.find_one({"_id": scholarship_id}))
                                is not None):
                            for idx, program in enumerate(scholarship.get("programs", [])):
                                if (program.get("course_id") == application_data.get("course_id") and
                                        program.get("specialization_name") == application_data.get("spec_name1")):
                                    program_offered_applicants = program.get("offered_applicants", [])
                                    if obj_application_id not in program_offered_applicants:
                                        program_offered_applicants.append(obj_application_id)
                                        db_config.scholarship_collection.update_one(
                                            {"_id": scholarship_id},
                                            {"$set": {f"programs.{idx}.offered_applicants": program_offered_applicants,
                                                      f"programs.{idx}.offered_applicants_count": len(
                                                          program_offered_applicants)}
                                             })
                                    break

    @staticmethod
    @celery_app.task(ignore_result=True)
    def send_email_based_on_client_preference_provider(
            email_preferences: dict, email_type: str, email_ids: list, subject: str, template: str, event_type: str,
            event_status: str, event_name: str, current_user: str, ip_address: str, payload: dict,
            attachments: any = None, action_type: str | None = "system", college_id: str | None = None,
            data_segments: dict | None = None, template_id: str | None = None, add_timeline: bool | None = True,
            scholarship_information: dict | None = None, offer_letter_information: dict | None = None
    ):
        """
        Send email based on client preference provider.

        Params:
            - email_preferences (dict): A dictionary which contains email preferences information.
            - email_type (str): Type of email. Possible values are promotional, transactional and default.
            - email_ids (list): List of email ids of receivers.
            - subject (str): Subject of email.
            - template (str): Content of email.
            - event_type (str): Type of event.
            - event_status (str): Status of event.
            - event_name (str): Name of event.
            - current_user (str): User who is sending email.
            - ip_address (str): IP address of user.
            - payload (dict): Additional data to send with email.
            - attachments (any): Default value: None. Attachments to send with email.
            - action_type (str | None): Default value: system. Action type of email. Possible value are system and manual.
            - college_id (str | None): Default value: None. Unique identifier of college.
            - data_segments (dict | None): Default value: None. A dictionary which contains data segments information.
            - template_id (str | None): Default value: None. Unique identifier of template.
            - add_timeline (bool | None): Default value: None. Whether to add timeline or not.
            - scholarship_information (dict | None): Default value: None.
                A dictionary which contains scholarship information.
            - offer_letter_information (dict | None): Default value: None.
                A dictionary which contains offer letter information.

        Returns: None
        """
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)
        email_ids = UnsubscribeHelper().remove_email_unsubscribe_students(
            email_type, email_ids
        )
        provider = EmailActivity().get_provider_details(email_preferences, email_type)
        credentials = provider.get("credentials", {})
        provider_name = "_".join(
            [name.lower() for name in provider.get("provider_name", "").split(" ")]
        )
        if provider_name == "amazon_ses":
            EmailActivity().send_email_using_amazon_ses(
                credentials,
                email_ids,
                subject,
                template,
                template,
                event_type,
                event_status,
                event_name,
                current_user,
                ip_address,
                email_type,
                "Amazon SES",
                attachments,
                action_type,
                college_id=college_id,
                data_segments=data_segments,
                template_id=template_id,
                add_timeline=add_timeline,
                offer_letter_information=offer_letter_information,
                scholarship_information=scholarship_information
            )
        elif provider_name == "karix":
            EmailActivity().send_multiple_mail_to_users(
                credentials=credentials,
                subject=subject,
                recipients=email_ids,
                html_file=template,
                payload=payload,
                current_user=current_user,
                ip_address=ip_address,
                event_type=event_type,
                event_status=event_status,
                event_name=event_name,
                email_type=email_type,
                provider="Karix",
                action_type=action_type,
                template_id=template_id,
            )

    @background_task_wrapper
    async def send_otp_through_email(
            self,
            first_name: str,
            email_otp: str,
            email,
            event_type=None,
            event_status=None,
            ip_address=None,
            email_preferences=None,
            event_name=None,
            payload=None,
            current_user=None,
            action_type="system",
            college_id=None
    ):
        """
        Send OTP to user through email
        """
        template = await DatabaseConfiguration().template_collection.find_one(
            {"email_category": "otp", "active": True, "template_status": "enabled"}
        )
        subject = "Login with OTP"
        if template:
            html_file = template.get("content")
            subject = template.get("subject")
            replacements = {
                "{Institute Name}": settings.university_name,
                "{name}": first_name,
                "{OTP code}": email_otp,
            }
            html_file = self.update_string_html_content(replacements, html_file)
        else:
            headers, path = self.get_data(
                file_path="templates/send_otp_through_email.html"
            )
            with open(path, "r", encoding="utf-8") as f:
                soup = bs(f, "html.parser")
                result = soup.find(id="welcome")
                result.string.replace_with(settings.university_name)
                result = soup.find(id="dear")
                result.string.replace_with(f"Dear - {first_name},")
                result = soup.find(id="message")
                result.string.replace_with(
                    f"Your Login request with OTP is received. You login OTP"
                    f" is as follows: {email_otp}"
                )
                result = soup.find(id="university")
                result.string.replace_with(settings.university_name)
            html_file = self.get_updated_html(path, soup)
        email_ids = await self.add_default_set_mails(email)
        email_preferences = {key: str(value) for key, value in email_preferences.items()}
        if not is_testing_env():
            await utility_obj.publish_email_sending_on_queue(data={
                "email_preferences": email_preferences,
                "email_type": "transactional",
                "email_ids": email_ids,
                "subject": subject,
                "template": html_file,
                "event_type": event_type,
                "event_status": event_status,
                "event_name": "OTP",
                "current_user": email,
                "ip_address": ip_address,
                "payload": {"content": "OTP",
                            "email_list": email_ids},
                "attachments": None,
                "action_type": action_type,
                "college_id": college_id,
                "priority": True,
                "data_segments": None,
                "template_id": None,
                "add_timeline": False,
                "environment": settings.environment
            }, priority=20)

    async def send_document_to_respective_board(
            self,
            file: any,
            college: dict,
            current_user: str,
            request: Request,
            board_email: str,
            field_name,
            student_id,
            action_type="system",
            season=None,
            college_id=None,
    ):
        """
        Send document to respective board through mail for verification
        purpose.

        First, downloading document from s3 bucket then sending document
        as an attachment in the mail.

        Params:
            file (any): Document file which want to send for verification.
            college (dict): A dictionary which contains college data.
            current_user (str): An user_name of current user.
            board_email (str): Email address of a board which useful for
                send document for verification.

        Returns:
            None: Not return anything.
        """
        s3_res = boto3.resource(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.region_name,
        )
        file_name = PurePath(file).name
        try:
            season = utility_obj.get_year_based_on_season(season)
            aws_env = settings.aws_env
            base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
            object_key = (
                f"{utility_obj.get_university_name_s3_folder()}/"
                f"{season}/"
                f"{settings.s3_student_documents_bucket_name}/"
                f"{student_id}/{field_name}/{file_name}"
            )
            s3_res.Bucket(base_bucket).download_file(object_key, file_name)
            attachments = {
                "object_key": object_key,
                "file_name": file_name
            }
            if not is_testing_env():
                await utility_obj.publish_email_sending_on_queue(data={
                    "email_preferences": college.get("email_preferences", {}),
                    "email_type": "transactional",
                    "email_ids": [board_email],
                    "subject": "Verification of Document",
                    "template": "Hello sir/ma'am, <br><br>Please verify the "
                                "attached document of student, you can find "
                                "document in the attachment. <br><br>Thank "
                                "you & Regards,<br>"
                                f"{college.get('name')}, "
                                f"{college.get('address', {}).get('city')}<br><br>"
                                f"Note: This is a test email. Please do not reply.",
                    "event_type": "email",
                    "event_status": "send",
                    "event_name": "Document",
                    "current_user": current_user,
                    "ip_address": utility_obj.get_ip_address(request),
                    "payload": {
                        "content": "Send document to Respective Board for " "Verification",
                        "email_list": [board_email],
                    },
                    "attachments": [attachments],
                    "action_type": action_type,
                    "college_id": college_id,
                    "priority": True,
                    "data_segments": None,
                    "template_id": None,
                    "add_timeline": True,
                    "environment": settings.environment
                })
        except Exception as e:
            logger.error(f"Error - {e}")
        finally:
            if os.path.isfile(file_name):
                os.remove(file_name)

    def add_footer_for_unsubscribe(self, template, email_id):
        """
        add footer in emails for unsubcribe link
        Params:
         templete (html): the template to add the footer
         token : the token of student
        Returns:
            template with added footer
        """
        authentication_obj = Authentication()
        token = authentication_obj.create_access_token_sync(
            data={"sub": email_id, "scopes": ["student"]}
        )
        soup = bs(template, "html.parser")
        if not soup.body:
            new_soup = bs("<body></body>", "html.parser")
            new_soup.body.extend(soup.contents)
            soup = new_soup
        footer = soup.new_tag("footer")
        paragraph = soup.new_tag("p")
        anchor = soup.new_tag(
            "a",
            href=f"https://{settings.base_path}/"
                 f"unsubscribe/{token}?"
                 f"unsubscribe_status=true",
        )
        anchor.string = "unsubscribe"
        paragraph.append("If you no longer wish to receive these emails, please ")
        paragraph.append(anchor)
        paragraph.append(".")
        footer.append(paragraph)
        soup.body.append(footer)
        return soup.prettify()

    async def add_default_set_mails(self, email_id):
        """
        this will add default set emails into the email sending list
        Params:
          email_id (str):  the email id which should be searched for
        Returns:
            email_ids( list): list of email ids
        """
        result = [email_id]
        if (
                student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"user_name": email_id}
                )
        ) is None:
            return result
        basic_details = student.get("basic_details", {})
        check = {
            "secondary_email_set_as_default": "alternate_email",
            "tertiary_email_set_as_default": "tertiary_email",
        }
        for default, value in check.items():
            if basic_details.get(default):
                value = basic_details.get(value)
                if value not in [None, ""]:
                    result.append(value)
        return result
