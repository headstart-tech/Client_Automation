"""
This file contains classes which relates to send email using amazon ses
"""
import json
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from botocore.exceptions import ClientError
from fastapi.exceptions import HTTPException

from app.core.log_config import get_logger

logger = get_logger(name=__name__)


class SesDestination:
    """
    Contains data about an email destination.
    """

    def __init__(self, tos, ccs=None, bccs=None):
        """
        :param tos: The list of recipients on the 'To:' line.
        :param ccs: The list of recipients on the 'CC:' line.
        :param bccs: The list of recipients on the 'BCC:' line.
        """
        self.tos = tos
        self.ccs = ccs
        self.bccs = bccs

    def to_service_format(self):
        """
        :return: The destination data in the format expected by Amazon SES.
        """
        svc_format = {'ToAddresses': self.tos}
        if self.ccs is not None:
            svc_format['CcAddresses'] = self.ccs
        if self.bccs is not None:
            svc_format['BccAddresses'] = self.bccs
        return svc_format


class SesMailSender:
    """
    Encapsulates functions to send emails with Amazon SES.
    """

    def __init__(self, ses_client):
        """
        :param ses_client: A Boto3 Amazon SES client.
        """
        self.ses_client = ses_client

    def send_email(self, source, destination, subject, text, html,
                   reply_tos=None, configuration_set_name=None):
        """
        Sends an email.

        Note: If your account is in the Amazon SES  sandbox, the source and
        destination email accounts must both be verified.

        :param source: The source email account.
        :param destination: The destination email account.
        :param subject: The subject of the email.
        :param text: The plain text version of the body of the email.
        :param html: The HTML version of the body of the email.
        :param reply_tos: Email accounts that will receive a reply if the recipient
                          replies to the message.
        :return: The response of email send.
        """
        send_args = {
            'Source': source,
            'Destination': destination.to_service_format(),
            'Message': {
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': text}, 'Html': {'Data': html}}},
            "ConfigurationSetName": configuration_set_name}
        if reply_tos is not None:
            send_args['ReplyToAddresses'] = reply_tos
        try:
            response = self.ses_client.send_email(**send_args)
            return response
        except ClientError as e:
            logger.error(f"Couldn't send mail to {destination.tos} - {e}")

    def send_templated_email(
            self, source, destination, template_name, template_data, reply_tos=None):
        """
        Sends an email based on a template. A template contains replaceable tags
        each enclosed in two curly braces, such as {{name}}. The template data passed
        in this function contains key-value pairs that define the values to insert
        in place of the template tags.

        Note: If your account is in the Amazon SES  sandbox, the source and
        destination email accounts must both be verified.

        :param source: The source email account.
        :param destination: The destination email account.
        :param template_name: The name of a previously created template.
        :param template_data: JSON-formatted key-value pairs of replacement values
                              that are inserted in the template before it is sent.
        :return: The ID of the message, assigned by Amazon SES.
        """
        send_args = {
            'Source': source,
            'Destination': destination.to_service_format(),
            'Template': template_name,
            'TemplateData': json.dumps(template_data)
        }
        if reply_tos is not None:
            send_args['ReplyToAddresses'] = reply_tos
        try:
            response = self.ses_client.send_templated_email(**send_args)
            return response
        except ClientError as e:
            logger.error(f"Couldn't send mail to {destination.tos} - {e}")

    def send_email_with_attachments(
            self, source, destination, subject, html, cc_recipients=[],
            reply_tos=None, configuration_set_name=None,
            attachment_files=None):
        """
        Sends an email with attachments.

        Note: If your account is in the Amazon SES  sandbox, the source and
        destination email accounts must both be verified.

        :param source: The source email account.
        :param destination: The destination email account.
        :param subject: The subject of the email.
        :param html: The HTML version of the body of the email.
        :param cc_recipients: .
        :param configuration_set_name: Useful for get webhook notification.
        :param attachment_files: Attachment files.
        :param reply_tos: Email accounts that will receive a reply if the recipient
                          replies to the message.
        :return: The response of email send.
        """
        try:
            message = MIMEMultipart()
            message['Subject'] = subject
            message['From'] = source
            message['To'] = ', '.join(destination)  # Combine multiple
            # recipients into a comma-separated string
            if cc_recipients:
                message['Cc'] = ', '.join(cc_recipients)
            if reply_tos:
                message.add_header('Reply-To', reply_tos)

            # Add the body text
            message.attach(MIMEText(html, 'html'))

            # Add the attachments
            if attachment_files:
                for attachment_file in attachment_files:
                    with open(attachment_file, 'rb') as file:
                        attachment = MIMEApplication(file.read())
                        attachment.add_header(
                            'Content-Disposition', 'attachment',
                            filename=attachment_file)
                        message.attach(attachment)

            # Convert the message to a raw string
            raw_message = message.as_string()

            response = self.ses_client.send_raw_email(
                Source=source,
                Destinations=destination,
                RawMessage={'Data': raw_message},
                ConfigurationSetName=configuration_set_name
            )
            return response
        except ClientError as e:
            logger.error(f"Couldn't send mail to {destination} - {e}")
            raise HTTPException(status_code=500, detail=f"Error - {e}")
