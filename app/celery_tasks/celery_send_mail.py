"""
this file contains all function of send mail using celery.
"""

import inspect
from datetime import date
from pathlib import Path, PurePath

import boto3
from bs4 import BeautifulSoup as bs
from bson import ObjectId
from fastapi import Request

from app.celery_tasks.celery_communication_log import CommunicationLogActivity
from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.celery_app import celery_app
from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import settings
from app.core.utils import utility_obj
from app.database.database_sync import DatabaseConfigurationSync
from app.dependencies.cryptography import EncryptionDecryption

logger = get_logger(name=__name__)


class send_mail_config:
    """A configuration for sending mail using amazon and karix"""

    @staticmethod
    # @celery_app.task
    async def counselor_send_bulk_email(
            payload,
            template,
            subject,
            event_type=None,
            event_status=None,
            template_id=None,
            event_name=None,
            email_activity_payload=None,
            current_user=None,
            ip_address=None,
            email_type=None,
            email_preferences=None,
            action_type="system",
            college_id=None,
            data_segments=None,
    ):
        """
        Send bulk mail
        """
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)
        from app.background_task.send_mail_configuration import EmailActivity
        from app.dependencies.oauth import is_testing_env
        if not is_testing_env():
            priority = False
            if event_type != "promotional":
                priority = True
            template_data, attachments = {}, []
            if template_id:
                template_data = DatabaseConfigurationSync().template_collection.find_one({"_id": ObjectId(template_id)})
                documents = template_data.get("attachment_document_link", [])
                if isinstance(template_data, dict) and documents:
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
            await utility_obj.publish_email_sending_on_queue({
                "email_preferences": email_preferences,
                "email_type": email_type,
                "email_ids": payload.get("email_id", []),
                "subject": subject,
                "template": template,
                "event_type": event_type,
                "event_status": event_status,
                "event_name": event_name,
                "current_user": current_user,
                "ip_address": ip_address,
                "payload": email_activity_payload,
                "attachments": attachments,
                "action_type": action_type,
                "college_id": college_id,
                "data_segments": data_segments,
                "template_id": template_id,
                "add_timeline": True,
                "priority": priority
            }, priority=15 if priority else 1)


    @staticmethod
    @celery_app.task
    def send_report_mail(
            download_url,
            email,
            current_user,
            email_preferences=None,
            ip_address=None,
            action_type="system",
            college_id=None,
            user_names=None
    ):
        """
        Send report to user through mail
        """
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)
        # Do not move position of below statement at top otherwise we'll get
        # circular ImportError
        from app.background_task.send_mail_configuration import EmailActivity
        headers, path = EmailActivity().get_data(
            file_path="templates/send_report.html")

        for email_id, name in zip(email, user_names):
            with open(path, "r", encoding="utf-8") as f:
                soup = bs(f, "html.parser")
                result = soup.find(id="button-container")
                result.clear()
                result.append(
                    bs(
                        f"<a href='{download_url}' id='login-button'>Download Report</a>",
                        "html.parser",
                    )
                )
                result = soup.find(id="dear")
                result.string.replace_with(f"Dear {name if name else 'user'},")
                result = soup.find(id="welcome")
                result.string.replace_with(settings.university_name)
                result = soup.find(id="log")
                result.string.replace_with(settings.university_name)
            html_file = EmailActivity().get_updated_html(path, soup)
            utility_obj.sync_publish_email_sending_on_queue({
                "email_preferences": email_preferences,
                "email_type": "default",
                "email_ids": [email_id],
                "subject": "Request of download report",
                "template": html_file,
                "event_type": "email",
                "event_status": "sent",
                "event_name": "Request of download report",
                "current_user": current_user,
                "ip_address": ip_address,
                "payload": {"content": "Request of download report", "email_list": email},
                "attachments": None,
                "action_type": action_type,
                "college_id": college_id,
                "data_segments": None,
                "template_id": None,
                "add_timeline": True,
                "priority": True
            }, priority=15)

    @staticmethod
    @celery_app.task(ignore_result=True)
    def send_mail(
            data: dict,
            event_type=None,
            event_status=None,
            event_name=None,
            payload=None,
            current_user=None,
            ip_address=None,
            email_preferences=None,
            college_id=None,
            add_timeline=True
    ):
        """
        Send verification mail to student
        """
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)
        data1 = {
            "userid": data.get("id"),
            "password": data.get("password"),
            "college_id": college_id,
        }
        token = EncryptionDecryption().encrypt_message(str(data1))
        token = token.decode("utf-8")
        urls = f"https://{settings.base_path}/student/email/dkper/redirect/{token}"
        template = DatabaseConfigurationSync().template_collection.find_one(
            {"email_category": "login", "active": True,
             "template_status": "enabled"}
        )
        current_year = date.today().year
        subject = settings.verification_email_subject
        # Do not move position of below statement at top otherwise we'll get
        # circular ImportError
        from app.background_task.send_mail_configuration import EmailActivity
        if template:
            html_file = template.get("content")
            subject = template.get("subject")
            replacements = {
                "{Institute Name}": settings.university_email_name,
                "{name}": data.get("first_name"),
                "{email id}": data.get("user_name"),
                "{mobile number}": data.get("mobile_number"),
                "{admission year}": f"{current_year}",
                "{password}": data.get("password"),
                "{Institute website URL}": settings.university_website_url,
                "{Institute contact email id}": settings.university_contact_us_email,
                "{Institute admission email id}": settings.university_admission_website_url,
                "{contact number}": settings.contact_us_number,
                "{verify_link}": urls,
            }
            html_file = EmailActivity().update_string_html_content(
                replacements, html_file
            )
        else:
            headers, path = EmailActivity().get_data(
                file_path="templates/verification.html"
            )
            with open(path, "r", encoding="utf-8") as f:
                soup = bs(f, "html.parser")
                result = soup.find(id="button-container")
                result.clear()
                result.append(
                    bs(
                        f"<a href='{urls}' id='login-button'>Verify and Start Your Application</a>",
                        "html.parser",
                    )
                )
                result = soup.find(id="contact-us-email")
                result.clear()
                result.append(
                    bs(
                        f"<a href='{settings.university_contact_us_email}'>{settings.university_contact_us_email}</a>",
                        "html.parser",
                    )
                )
                result = soup.find(id="first-website-url")
                result.clear()
                result.append(
                    bs(
                        f"<a href='{settings.university_website_url}'>{settings.university_website_url}</a>",
                        "html.parser",
                    )
                )
                result = soup.find(id="website-url")
                result.clear()
                result.append(
                    bs(
                        f"<a href='{settings.university_website_url}'>{settings.university_website_url}</a>",
                        "html.parser",
                    )
                )
                result = soup.find(id="admission-website-url")
                result.clear()
                result.append(
                    bs(
                        f"<a href='{settings.university_admission_website_url}'>"
                        f"{settings.university_admission_website_url}</a>",
                        "html.parser",
                    )
                )
                result = soup.find(id="logo")
                result.string.replace_with(
                    f"Welcome to" f" {settings.university_email_name}")
                result = soup.find(id="A")
                result.string.replace_with(f"Email - {data.get('user_name')}")
                result = soup.find(id="B")
                result.string.replace_with(
                    f"Password - {data.get('password')}")
                result = soup.find(id="name")
                result.string.replace_with(f"Dear {data.get('first_name')},")
                result = soup.find(id="desc")
                result.string.replace_with(
                    f"Thank you for registering for {settings.university_email_name},"
                    f" where we empower individuals and communities with the"
                    f" knowledge and skills to bring positive social changes,"
                    f" exercise universal freedom, and contribute to tackling"
                    f" the most pressing issues of global importance with"
                    f" email ID {data['user_name']} and mobile "
                    f"number:{data['mobile_number']}. "
                )
                result = soup.find(id="log")
                result.string.replace_with(
                    f"{settings.university_email_name}" f" - Admission Team"
                )
                result = soup.find(id="contact_us_number")
                result.string.replace_with(f"| {settings.contact_us_number} |")
            html_file = EmailActivity().get_updated_html(path, soup)
        utility_obj.sync_publish_email_sending_on_queue({
            "email_preferences": email_preferences,
            "email_type": "transactional",
            "email_ids": [data.get("user_name")],
            "subject": subject,
            "template": html_file,
            "event_type": event_type,
            "event_status": event_status,
            "event_name": event_name,
            "current_user": current_user,
            "ip_address": ip_address,
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


    @staticmethod
    @celery_app.task
    def send_comment_notification_mail(
            feedback, email, name, email_preferences=None, ip_address=None,
            college_id=None
    ):
        """
        Send student documents information like verification status, comment/remark and reupload link if document verification failed etc through email.

        Params:
          feedback (dict): A dictionary which contains all documents information.
          email(list): list of emails of a student which useful for send all document information. e.g., xxxxx@xxxx.com
          name(str): Name of the student.
          email_preferences (dict | None): Either none or email preferences details.
          ip_address (None | str): An IP address of user.

        Returns:
            None: Not returning anything.
        """
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)
        # Do not move position of below statement at top otherwise we'll get
        # circular ImportError
        from app.background_task.send_mail_configuration import EmailActivity
        headers, path = EmailActivity().get_data(
            file_path="templates/send_notification.html"
        )
        message = f"Dear {name}"
        with open(path, "r", encoding="utf-8") as f:
            soup = bs(f, "html.parser")
            salutation = soup.find(id="dear")
            univeristy_name = settings.university_name
            result = soup.find(id="welcome")
            result.string.replace_with(univeristy_name)
            result = soup.find(id="log")
            result.string.replace_with(univeristy_name)
            salutation.string.replace_with(message)
            for row in soup.find("tbody").find_all("tr"):
                row.extract()
            for doc in feedback:
                new_row = soup.new_tag("tr")
                status = feedback[doc].get("status", "")
                for segment in [doc.title(), status,
                                feedback[doc].get("comments", "")]:
                    cell = soup.new_tag("td")
                    cell.string = segment
                    new_row.append(cell)
                content_container = soup.new_tag("td")
                content_div = soup.new_tag("div", id="button-container")
                if status == "Rejected":
                    content_a = soup.new_tag(
                        "a",
                        href=f"https://{settings.base_path}/?reupload=true"
                    )
                    content_a.string = "Reupload"
                else:
                    content_a = soup.new_tag("p")
                    content_a.string = "--"
                content_div.append(content_a)
                content_container.append(content_div)
                new_row.append(content_container)
                soup.find("tbody").append(new_row)
        html_file = EmailActivity().get_updated_html(path, soup)
        utility_obj.sync_publish_email_sending_on_queue({
            "email_preferences": email_preferences,
            "email_type": "transactional",
            "email_ids": email,
            "subject": "Notification of comments and status of documents uploaded",
            "template": html_file,
            "event_type": "email",
            "event_status": "sent",
            "event_name": "Notification of comments and status",
            "current_user": email[0],
            "ip_address": ip_address,
            "payload": {
                "content": "Notification of comments and status of documents",
                "email_list": email,
            },
            "attachments": None,
            "action_type": "system",
            "college_id": college_id,
            "data_segments": None,
            "template_id": None,
            "add_timeline": True,
            "priority": True,
            "environment": settings.environment
        }, priority=10)

    @staticmethod
    @celery_app.task
    def update_student_timeline_after_send_sms(
            numbers: list, response: dict, college: dict, user: dict,
            dlt_content_id: str, current_user: str, sms_content: str, data_segments
    ):
        """
        Send student documents information like verification status, comment/remark and reupload link if document verification failed etc through email.

        Params:
          - numbers (list): Mobile numbers of students.
          - response(dict): Response which get after send sms.
          - college (dict): Information of college.
          - user (dict): Information of user.
          - dlt_content_id (str): Dlt content id which is required field to
            send sms.
          - current_user (str): Username of current user.
          - sms_content (str):
          - data_segments (dict): The data segment details

        Returns:
            None: Not returning anything.
        """
        try:
            from app.background_task.send_mail_configuration import \
                EmailActivity
            if (
                    template := DatabaseConfigurationSync(
                    ).template_collection.find_one(
                        {"dlt_content_id": dlt_content_id}
                    )
            ) is None:
                template = {}
            for number, response_data in zip(
                    numbers, response.get("submitResponses")):
                student = (DatabaseConfigurationSync(
                ).studentsPrimaryDetails.find_one(
                    {"basic_details.mobile_number": number}))
                if student:
                    sms_content = EmailActivity().detect_and_validate_variables(
                        sms_content, ObjectId(college.get("id")),
                        student.get("user_name")
                    )
                    action_type = (
                        "counselor"
                        if user.get("role", {}).get("role_name") ==
                           "college_counselor" else "system")
                    CommunicationLogActivity().add_communication_log(
                        student_id=str(student.get("_id")),
                        response=response_data,
                        data_type="sms",
                        event_type="sms",
                        event_status="sent",
                        event_name=f"mobile number {number}",
                        action_type=action_type,
                        current_user=current_user,
                        template_id=str(template.get("_id")),
                        college_id=college.get("id"),
                        user_id=str(user.get("_id")),
                        data_segments=data_segments
                    )
                    name = utility_obj.name_can(
                        student.get("basic_details", {}))
                    if user.get("role", {}).get("role_name"):
                        name = utility_obj.name_can(user)
                    StudentActivity().student_timeline(
                        student_id=str(student.get("_id")),
                        event_type="sms",
                        event_status="sent sms",
                        user_id=str(user.get("_id")),
                        template_type="sms",
                        template_id=str(template.get("_id")),
                        template_name=template.get("template_name"),
                        message=f"{name} send a SMS",
                        college_id=str(student.get("college_id")),
                        data_segments=data_segments
                    )
        except Exception as error:
            logger.error(f"An error occurred when send sms to students. "
                         f"Error - {error}. "
                         f"Error line#: {error.__traceback__.tb_lineno}.")

    async def send_payment_receipt_to_user(
            self,
            file: any,
            college: dict,
            user: dict,
            request: Request,
            user_email: str,
            student_name: str,
            action_type="system",
            season=None,
    ):
        """
        Send payment receipt to user through mail.

        First, download payment receipt from s3 bucket then sending it
        as an attachment in the mail.

        Params:
            - file (any): Payment receipt file which want to send over mail.
            - college (dict): A dictionary which contains college data.
            - user (dict): A dictionary which contains user data.
            - request (Request): An object of `Request` which contains
                request data, useful for get ip address.
            - user_email (str): Email address of user which useful for
                send payment receipt.
            - student_name (str): Name of a student.
            - action_type: (str): Type of action. Defaul value: "system"
            - season (str | None): Either None or an unique identifier of a
                season.

        Returns:
            None: Not return anything.
        """
        path = Path(inspect.getfile(inspect.currentframe())).resolve()
        path = PurePath(path).parent
        file_name = PurePath(file).name
        path = str(PurePath(path, Path(file_name)))
        try:
            s3_res = boto3.resource(
                "s3",
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.region_name,
            )
            season = utility_obj.get_year_based_on_season(season)
            aws_env = settings.aws_env
            base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
            object_key = (
                f"{utility_obj.get_university_name_s3_folder()}/"
                f"{season}/"
                f"{settings.s3_reports_bucket_name}/{file_name}"
            )
            s3_res.Bucket(base_bucket).download_file(object_key, path)
            attachments = {
                "object_key": object_key,
                "file_name": file
            }
            arguments = {
                "email_preferences": college.get("email_preferences", {}),
                "email_type": "transactional",
                "email_ids": [user_email],
                "subject": "Application Payment Receipt",
                "template": f"Dear {student_name}, <br><br>Please find the "
                            f"application payment receipt in the attachment. "
                            f"<br><br>Thank "
                            "you & Regards,<br>"
                            f"{college.get('name')}, "
                            f"{college.get('address', {}).get('city')}<br><br>",
                "event_type": "email",
                "event_status": "send",
                "event_name": "Document",
                "current_user": user.get("user_name"),
                "ip_address": utility_obj.get_ip_address(request),
                "payload": {
                    "content": "Send Application Payment Receipt to User",
                    "email_list": [user_email],
                },
                "attachments": [attachments],
                "action_type": action_type,
                "college_id": college.get("id"),
                "priority": True,
                "data_segments": None,
                "template_id": None,
                "add_timeline": True,
                "environment": settings.environment
            }
            await utility_obj.publish_email_sending_on_queue(data=arguments, priority=10)
        except Exception as e:
            logger.error(f"Error - {e}")
        finally:
            if Path(path).is_file():
                Path(path).unlink()  # unlink (remove) the file
