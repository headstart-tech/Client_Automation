"""
This file contain class and functions for update report status and finished datetime by request id
"""

import datetime
import requests
from app.core.log_config import get_logger
from app.core.teamcity_config import headers
from app.core.utils import settings, utility_obj
from app.database.configuration import DatabaseConfiguration
from app.s3_events.s3_events_configuration import get_download_url
from pathlib import Path, PurePath
import inspect
from zipfile import ZipFile
from botocore.exceptions import ClientError
import boto3

logger = get_logger(name=__name__)


class ReportStatusHelper:
    """
    Contain functions related to report status
    """

    async def update_status_report_by_request_id(
            self, request_id, request, college={}, action_type="system"
    ):
        """
        Update report status and finished datetime by request id
        """
        email_preferences = {
            key: str(val) for key, val in
            college.get("email_preferences", {}).items()
        }
        try:
            response = requests.request(
                "GET",
                f"{settings.teamcity_base_path}/app/rest/builds?locator={request_id}",
                headers=headers,
            )
            if response.status_code != 200:
                logger.error(response.text)
                return
            data = response.json()
            date = datetime.datetime.strptime(
                data.get("build", [])[0].get(
                    "finishOnAgentDate", datetime.datetime.utcnow()
                ),
                "%Y%m%dT%H%M%S%z",
            )
            status = "In progress"
            if (
                    data.get("build")[0].get("state") == "finished"
                    and data.get("build")[0].get("status") == "SUCCESS"
            ):
                status = "Done"
                await DatabaseConfiguration().activity_download_request_collection.update_one(
                    {
                        "request_type": f"Generate report with request id {request_id}"},
                    {
                        "$set": {
                            "is_status_completed": True,
                            "request_completed_at": data,
                        }
                    },
                )
            elif (
                    data.get("build")[0].get("state") == "finished"
                    and data.get("build")[0].get("status") == "FAILURE"
            ):
                status = "Failed"
            await DatabaseConfiguration().report_collection.update_one(
                {"request_id": request_id},
                {"$set": {"status": status, "request_finished_on": date}},
            )
            logger.info(f"Report status updated with request id {request_id}")
            report = await DatabaseConfiguration().report_collection.find_one(
                {"request_id": request_id}
            )
            ip_address = utility_obj.get_ip_address(request)
            if report:
                if report.get("status") == "Done" and (
                        report.get("report_send_to") not in [None, ""]
                        or (report.get("recipient_details"))
                        or (
                                report.get("generate_and_reschedule", {}).get(
                                    "recipient_details"
                                )
                        )
                ):
                    email, user_names = [], []
                    if report.get("report_send_to") not in [None, ""]:
                        user_name = report.get("report_send_to")
                        email = [user_name]
                        if (
                        user := await DatabaseConfiguration().user_collection.find_one(
                                {"user_name": user_name})) is None:
                            user = {}
                        user_names.append(
                            user.get("first", "").title() if user else "user")
                    for item in [
                        report.get("recipient_details"),
                        report.get("generate_and_reschedule", {}).get(
                            "recipient_details"
                        ),
                    ]:
                        if item:
                            for email_info in item:
                                if isinstance(email_info, dict):
                                    email_id = email_info.get(
                                        "recipient_email_id")
                                    cc_mail_ids = email_info.get(
                                        "recipient_cc_mail_id")
                                    recipient_name = email_info.get(
                                        "recipient_name")
                                    if not recipient_name:
                                        if (
                                                user := await DatabaseConfiguration().user_collection.find_one(
                                                    {
                                                        "user_name": email_id})) is None:
                                            user = {}
                                        recipient_name = user.get("first",
                                                                  "").title() if user else "user"
                                    if cc_mail_ids:
                                        cc_mail_ids = cc_mail_ids.split(",")
                                        email.extend(cc_mail_ids)
                                        for item in range(len(cc_mail_ids)):
                                            user_names.append(recipient_name)
                                    email.append(email_id)
                                    user_names.append(recipient_name)
                    season = utility_obj.get_year_based_on_season()
                    aws_env = settings.aws_env
                    base_bucket = getattr(settings,
                                          f"s3_{aws_env}_base_bucket")
                    report_format = report.get("format", "").lower()
                    if report_format == "excel":
                        report_format = "xlsx"

                    s3_res = boto3.resource(
                        "s3", aws_access_key_id=settings.aws_access_key_id,
                        aws_secret_access_key=settings.aws_secret_access_key,
                        region_name=settings.region_name)
                    s3 = settings.s3_client
                    path = Path(inspect.getfile(inspect.currentframe())).resolve()
                    pth = PurePath(path).parent
                    path_zip = PurePath(pth, Path("sample.zip"))

                    with ZipFile(str(path_zip), "w") as zipObj:
                        object_key = \
                            f'{utility_obj.get_university_name_s3_folder()}/' \
                            f'{season}/{settings.s3_reports_bucket_name}/' \
                            f'{settings.report_folder_name}/' \
                            f'{settings.teamcity_build_type}/{request_id}/' \
                            f'data.{report_format}'
                        object_name = PurePath(object_key).name
                        path = PurePath(pth, Path(object_name))
                        try:
                            s3_res.Bucket(
                                base_bucket).download_file(
                                object_key, str(path)
                            )
                        except Exception as error:
                            logger.error(f"Error downloading file %s: %s",
                                         object_name,
                                         error)
                        try:
                            zipObj.write(str(path), arcname=f"{request_id}/{object_name}")
                        except FileNotFoundError as error:
                            logger.error(
                                f"Error write the file inn zipObj {error}")
                        if Path(str(path)).is_file():
                            Path(str(path)).unlink()
                    unique_filename = utility_obj.create_unique_filename(extension=".zip")
                    path_to_unique_filename = f"{utility_obj.get_university_name_s3_folder()}/{settings.s3_download_bucket_name}/{unique_filename}"
                    try:
                        with open(str(path_zip), "rb") as f:
                            s3.upload_fileobj(
                                f, base_bucket, path_to_unique_filename
                            )
                    except ClientError as e:
                        logger.error(e)
                        return {'Error': e}
                    finally:
                        if Path(str(path_zip)).is_file():
                            Path(str(path_zip)).unlink()  # unlink (remove) the file
                    download_url = await get_download_url(
                        base_bucket, path_to_unique_filename, expire_time=86400
                    )
                    toml_data = utility_obj.read_current_toml_file()
                    if toml_data.get("testing", {}).get("test") is False:
                        if email:
                            logger.info(f"Usernames: {user_names}")
                            await utility_obj.publish_email_sending_on_queue({
                                "download_url": download_url,
                                "email": email,
                                "current_user": email[0],
                                "email_preferences": email_preferences,
                                "ip_address":ip_address,
                                "action_type": action_type,
                                "college_id": college.get("_id"),
                                "user_names": user_names,
                                "send_report_mail": True,
                                "environment": settings.environment
                            }, priority=3)
        except Exception as e:
            logger.error(f"Something went wrong. {str(e.args)}")
