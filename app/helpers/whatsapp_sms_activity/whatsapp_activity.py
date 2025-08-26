"""
This file contain class and functions related to whatsapp functionality
"""

import json
from datetime import datetime

import requests
from bson import ObjectId
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError
from requests.auth import HTTPBasicAuth

from app.background_task.send_mail_configuration import EmailActivity
from app.celery_tasks.celery_communication_log import CommunicationLogActivity
from app.core.celery_app import celery_app
from app.core.log_config import get_logger
from app.core.utils import settings
from app.database.database_sync import DatabaseConfigurationSync
from app.database.motor_base_singleton import MotorBaseSingleton
from app.dependencies.oauth import is_testing_env

logger = get_logger(__name__)


class WhatsappHelper:
    """
    Contain functions related to whatsapp activity
    """

    @staticmethod
    @celery_app.task(ignore_result=True)
    def store_whatsapp_activity(response, number, text, ip_address, data_segments):
        """
        Store the whatsapp activity data in the database.

        Params:
            response (Response | dict): Response which get when
             whatsapp message send.
            number ( int | str | None): Mobile number of a
            student. e.g., 1234567890
            text (str): Message which send through whatsApp.
            ip_address (str): IP address of user who performed the
            action of send whatsApp to student.

        Returns:
            None: Not returning anything.
        """
        if (
                student := DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                    {"basic_details.mobile_number": str(number)}
                )
        ) is not None:
            try:
                # TODO: Not able to add student timeline data
                #  using celery task when environment is
                #  demo. We'll remove the condition when
                #  celery work fine.
                if settings.environment in ["demo"]:
                    CommunicationLogActivity().add_whatsapp_communication_log(
                        student_id=str(student.get("_id")),
                        response=response,
                        data_type="whatsapp",
                        event_type="sent",
                        event_status="sent",
                        event_name=f"whatsapp message is: {text}",
                    )
                else:
                    if not is_testing_env():
                        CommunicationLogActivity().add_whatsapp_communication_log.delay(
                            student_id=str(student.get("_id")),
                            response=response,
                            data_type="whatsapp",
                            event_type="sent",
                            event_status="sent",
                            event_name=f"whatsapp message is: {text}",
                        )
            except KombuError as celery_error:
                logger.error(f"error whatsapp_communication_log {celery_error}")
            except Exception as error:
                logger.error(f"error whatsapp_communication_log {error}")

            message_list = {
                "user_name": student.get("user_name"),
                "user_id": ObjectId(student.get("_id")),
                "send_to": [number],
                "ip_address": ip_address,
                "created_at": datetime.utcnow(),
                "submit_date": response.get("MESSAGEACK").get("GUID").get("SUBMITDATE"),
                "whatsapp_content": text,
                "id": response.get("MESSAGEACK").get("GUID").get("ID"),
                "guid": response.get("MESSAGEACK").get("GUID").get("GUID"),
                "status": "sent",
            }

            # For Billing Dashboard
            selected_college_id = MotorBaseSingleton.get_instance().master_data.get("college_id")
            DatabaseConfigurationSync("master").college_collection.update_one(
                {"_id": ObjectId(selected_college_id)}, {"$inc": {"usages.whatsapp_sms_sent": 1}}
            )

            DatabaseConfigurationSync().whatsapp_sms_activity.insert_one(message_list)

    def whatsapp_template_helper(
            self, template_id: str | None = None, template_content: str | None = None
    ):
        """
        Check the template id and template content
            params:
                template_id (str): taking template id or none valve
                template_content (str): taking template content
            return:
             response: dict or none value
        """
        template = None
        if template_id is not None:
            template = {"template_id": template_id}
        if template_content is not None:
            if template is None:
                template = {"template_content": template_content}
            else:
                template.update({"template_content": template_content})
        return template

    def get_button_list(
            self, button_list: dict, data: dict, whatsapp_data: dict, action: list = None
    ):
        """
        Modify the data and whatsapp_data fields.

            Params:
                - button_list (dict): Title name of the button.
                - data (dict): A dictionary data which has to be
                 modified/updated.
                - whatsapp_data (dict): A dictionary data which has to be
                 modified/updated.

            Returns:
                tuple: A tuple which contains a modified/updated dictionary
                 and a dictionary which has to be modified/updated.
        """
        data.get("SMS", [{}])[0].update({"@MSGTYPE": "7"})
        whatsapp_data.get("interactive", {}).update(
            {
                "type": "list",
                "action": {
                    "button": button_list.get("button_title"),
                    "sections": [{"title": "Indian", "rows": action}],
                },
            }
        )
        return data, whatsapp_data

    def get_whatsapp_location(self, data, location):
        """
        modify the data and whatsapp_data fields

        params:
            data (dict): dictionary data which has to be modified and updated
            whatsapp_data (dict): dictionary data which has to be modified
             and updated
             location (dict): store location and location details

        return:
            response: dict or none value
        """
        data.get("SMS", [{}])[0].update({"@MSGTYPE": "6"})
        data.get("SMS", [{}])[0].update({"@ID": "998"})
        whatsapp_data = {
            "type": "location",
            "recipient_type": "individual",
            "location": {
                "longitude": location.get("longitude"),
                "latitude": location.get("latitude"),
                "name": location.get("name"),
                "address": location.get("address"),
            },
        }
        return data, whatsapp_data

    def media_helper(self, data, media, template, file):
        """
        modified data for the  media
        params:
            data (dict): dictionary or None
            media (dict): media have the information of the media

        return:
            response: dictionary or None
        """

        data.update({"DLR": {"@URL": ""}})
        data.get("SMS", [{}])[0].update(
            {
                "@MSGTYPE": "3",
                "@TYPE": media.get("type", ""),
                "@CAPTION": media.get("caption", ""),
                "@CONTENTTYPE": media.get("content_type", ""),
                "@MEDIADATA": media.get("url", ""),
                "@ID": "",
            }
        )
        if template:
            data.get("SMS", [{}])[0].update(
                {"@TEMPLATEINFO": template.get("template_id", ""), "@MSGTYPE": "3"}
            )
        if file:
            data.get("SMS", [{}])[0].update(
                {
                    "@MEDIADATA": file.name,
                    "@TYPE": media.get("type", ""),
                    "@MSGTYPE": "3",
                }
            )
        return data

    def token_genrate_and_enable(self):
        """
        Generate token for sending message
        """
        token_generation_response = requests.post(
            settings.generate_whatsapp_token, auth=HTTPBasicAuth(settings.whatsapp_username, settings.whatsapp_password)
        )
        if token_generation_response.status_code == 200:
            return token_generation_response
        raise HTTPException(status_code=401, detail="Whatsapp token generation failed.")

    def send_whatsapp_to_users(
            self,
            send_to: list,
            text,
            media=None,
            template=None,
            button=None,
            button_list=None,
            location=None,
            file=None,
            ip_address=None,
            data_segments=None,
            _id=None,
            college_id=None
    ):
        """
        Send message from whatsapp
        """
        whatsapp_details, response = {}, {}
        if _id:
            if len(_id) != 24:
                raise HTTPException(
                    status_code=422,
                    detail=f"whatsapp id must be a 12-byte input or a "
                           f"24-character hex string",
                )
            whatsapp_details = DatabaseConfigurationSync().template_collection.find_one(
                {"_id": ObjectId(_id)}
            )

        for number in send_to:
            email_activity_obj = EmailActivity()
            student = (DatabaseConfigurationSync().studentsPrimaryDetails.find_one(
                {"basic_details.mobile_number": number}))
            variable_values = ""
            if student and college_id:
                text, variable_values = email_activity_obj.detect_and_validate_variables(
                    text, ObjectId(college_id), student.get("user_name"),
                    whatsapp_functionality=True
                )
            data = {
                "@VER": "1.2",
                "USER": {"@CH_TYPE": "4", "@UNIXTIMESTAMP": ""},
                "SMS": [
                    {
                        "@UDH": "",
                        "@CODING": "",
                        "@TEXT": "",
                        "@TEMPLATEINFO": f"{whatsapp_details.get('template_id')}{variable_values}",
                        "@PROPERTY": "",
                        "@MSGTYPE": "1",
                        "@ID": "",
                        "ADDRESS": [
                            {
                                "@FROM": settings.whatsapp_sender,
                                "@TO": "91" + str(number),
                                "@SEQ": "1",
                                "@TAG": "some client side random data",
                            }
                        ]
                    }
                ]
            }

            if location:
                data, whatsapp_data = self.get_whatsapp_location(data, location)

            media_type = whatsapp_details.get("attachmentType")
            if media_type not in ["", None]:
                if media_type == "pdf":
                    media_type = "document"
                data.get("SMS", [{}])[0].update(
                    {
                        "@MSGTYPE": "3",
                        "@TYPE": media_type,
                        "@MEDIADATA": whatsapp_details.get("attachmentURL")
                    }
                )

            button_url = whatsapp_details.get("b_url")
            if button_url not in ["", None]:
                data.get("SMS", [{}])[0].update({"@B_URLINFO": button_url})

            if media is None:
                if whatsapp_details is None:
                    whatsapp_details = {}
                media = whatsapp_details.get("media")

            # if media is available
            if media is not None:
                if media.get("url") not in ["", None]:
                    data = self.media_helper(
                        data=data, media=media, template=template, file=file
                    )
            response = requests.post(settings.send_whatsapp_url, data=json.dumps(data), headers={
                "Authorization": f"Bearer {json.loads(self.token_genrate_and_enable().text).get('token')}",
                "Content-Type": "application/json",
            })
            try:
                if not is_testing_env():
                    WhatsappHelper().store_whatsapp_activity.delay(
                        response=response.json(),
                        number=number,
                        text=text,
                        ip_address=ip_address,
                        data_segments=data_segments,
                    )
            except KombuError as celery_error:
                logger.error(f"error storing whatsapp activity {celery_error}")
            except Exception as error:
                logger.error(f"error storing whatsapp activity {error}")
        return response
