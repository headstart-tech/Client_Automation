"""
This file contains class and functions related to payment.
"""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import BackgroundTasks, Request
from kombu.exceptions import KombuError

from app.background_task.send_mail_configuration import EmailActivity
from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.custom_error import DataNotFoundError
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.database.configuration import DatabaseConfiguration
from app.database.database_sync import DatabaseConfigurationSync
from app.dependencies.oauth import cache_invalidation, is_testing_env
from app.helpers.student_curd.student_application_configuration import (
    StudentApplicationHelper,
)
from app.s3_events.s3_events_configuration import upload_multiple_files

logger = get_logger(name=__name__)


class PaymentHelper:

    async def get_payment_mode_info(self, item: dict, request: Request) -> tuple:
        """
        Get payment mode, mode information and payment_id
        from payment details.

        Params:
            - item (dict): A dictionary which contains payment details.
            - request (Request): An object of `Request` which contains
                request data, useful for get ip address.

        Returns:
            - tuple: A tuple which contains payment mode, mode information
             and payment_id.
        """
        payment_id = item.get("id")
        payment_mode = item.get("method", "NA")
        payment_mode_info = {
            "card": item.get("card", {}),
            "bank": item.get("bank", "NA"),
            "wallet": item.get("wallet", "NA"),
            "card_id": item.get("card_id", "NA"),
            "upi": item.get("upi", {}),
            "acquirer_data": item.get("acquirer_data", {}),
            "payment_location": item.get("notes", {}).get("address", "NA"),
            "ip_address": utility_obj.get_ip_address(request),
        }
        return payment_mode, payment_mode_info, payment_id

    async def update_payment_data_and_send_mail(
        self,
        application_id: str,
        document_files: list,
        payment_id: str,
        user: dict,
        current_datetime: datetime,
        season: str | None,
        background_tasks: BackgroundTasks,
        reason_type: str,
        reason_name: str | None,
        note: str | None,
        college: dict,
        request: Request,
        payment_device: str,
        device_os: str,
        name: str | None,
        course_name: str | None,
        specialization_name: str | None,
        amount: str | None
    ) -> None:
        """
        Validate input data, add payment information in the payment collection,
         update payment information in the student application collection,
         send payment successful mail and update student timeline.

        Params:
            - application_id (str): An unique identifier of an application.
            - document_files (str | None): Either None or list which contains
                publicly accessible document (s) URLs.
            - payment_id (str): An unique identifier of payment.
            - user (dict): A dictionary which contains user information.
            - current_datetime (datetime): User requested datetime.
            - season (str | None): Either None or season id which useful
                payment documents in the given season.
            - background_tasks (BackgroundTasks): An object of
                `BackgroundTasks` which useful for perform background task (s).
            - reason_type (PaymentReason): Type of payment reason like
                Campus visit, Outreach event, Payment by vender,
                Join payment and Other.
            - reason_name (str): Reason name in-case of reason type
                `Other`.
            - note (str | None): Either None or string which represents
                note.
            - college (dict): A dictionary which contains college information.
            - request (Request): An object of `Request` which contains
                request data, useful for get ip address.
            - payment_device (str): Device name from which payment captured.
            - device_os (str): Device operating system name which payment
                captured.

        Returns: None
        """
        await utility_obj.is_length_valid(application_id, name="Application id")
        if (
            application := await DatabaseConfiguration().studentApplicationForms.find_one(
                {"_id": ObjectId(application_id)}
            )
        ) is None:
            raise DataNotFoundError(message="Application", _id=application_id)
        if document_files:
            season_year = utility_obj.get_year_based_on_season(season)
            aws_env = settings.aws_env
            base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
            base_bucket_url = getattr(settings, f"s3_{aws_env}_base_bucket_url")
            upload_files = await upload_multiple_files(
                files=document_files,
                bucket_name=base_bucket,
                base_url=base_bucket_url,
                path=f"{utility_obj.get_university_name_s3_folder()}/"
                f"{season_year}/{settings.s3_reports_bucket_name}/",
            )
            document_files = upload_files
        payment_extra_info = {
            "payment_device": payment_device,
            "device_os": device_os,
            "payment_method": "Offline",
            "payment_mode": "Cash",
            "payment_mode_info": await self.get_payment_mode_info({}, request),
            "name": name,
            "course_name": course_name,
            "specialization_name": specialization_name,
            "amount": amount
        }
        payment_doc = {
            "payment_id": payment_id,
            "order_id": "",
            "user_id": ObjectId(user.get("_id")),
            "details": {
                "purpose": "StudentApplication",
                "application_id": ObjectId(application_id),
            },
            "status": "captured",
            "attempt_time": current_datetime,
            "error": {
                "error_code": None,
                "description": None,
                "created_at": current_datetime,
            },
            "document_files": document_files,
            "reason_type": reason_type,
            "reason_name": reason_name,
            "note": note,
        }
        payment_doc.update(payment_extra_info)
        await DatabaseConfiguration().payment_collection.insert_one(payment_doc)
        if (
            course := await DatabaseConfiguration().course_collection.find_one(
                {"_id": application.get("course_id")}
            )
        ) is None:
            course = {}
        course_name = course.get("course_name")
        spec_name = application.get("spec_name1")
        toml_data, student = utility_obj.read_current_toml_file(), None
        if toml_data.get("testing", {}).get("test") is False:
            if (
                student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": application.get("student_id")}
                )
            ) is not None:
                basic_details = student.get("basic_details", {})

                today_year = str(current_datetime.year)
                invoice_number = f"{today_year}-INV1"
                if (
                    await DatabaseConfiguration().application_payment_invoice_collection.find_one(
                        {"invoice_number": invoice_number}
                    )
                    is not None
                ):
                    record = (
                        DatabaseConfigurationSync()
                        .application_payment_invoice_collection.find({})
                        .sort("created_at", -1)
                        .limit(5)
                    )
                    for rec in record:
                        if rec.get("invoice_number"):
                            old_invoice = rec.get("invoice_number")
                            break
                        else:
                            old_invoice = invoice_number
                    old_invoice = (
                        "0" if old_invoice[9:] in ["", None] else old_invoice[9:]
                    )
                    old_id = int(old_invoice) + 1
                    old_invoice = old_invoice + str(old_id)
                else:
                    old_invoice = invoice_number
                background_tasks.add_task(
                    EmailActivity().payment_successful,
                    data={
                        "invoice_number": old_invoice,
                        "payment_status": "success",
                        "created_at": current_datetime,
                        "order_id": "",
                        "payment_id": payment_id,
                        "student_name": utility_obj.name_can(basic_details),
                        "student_id": str(student.get("_id")),
                        "student_email_id": basic_details.get("email"),
                        "student_mobile_no": basic_details.get("mobile_number"),
                        "application_number": application.get("custom_application_id"),
                        "degree": f"{course_name} in " f"{spec_name}",
                        "college_name": college.get("name"),
                        "nationality": basic_details.get("nationality"),
                        "application_fees": course.get("fees"),
                        "student_first_name": basic_details.get("first_name", {}),
                    },
                    event_type="email",
                    event_status="sent",
                    event_name=f"Application ({course_name} "
                    f"in {spec_name}) "
                    f"payment successful ",
                    email_preferences=college.get("email_preferences", {}),
                    request=request,
                )
                try:
                    # TODO: Not able to add student timeline data
                    #  using celery task when environment is
                    #  demo. We'll remove the condition when
                    #  celery work fine.
                    if settings.environment in ["demo"]:
                        StudentActivity().student_timeline(
                            student_id=str(application.get("student_id")),
                            event_type="Payment",
                            event_status="Done",
                            event_name=(
                                f"{course_name} in {spec_name}"
                                if spec_name not in ["", None]
                                else f"{course_name} Program"
                            ),
                            college_id=str(application.get("college_id")),
                        )
                        logger.info("Finished dispatching to the Celery " "server task")
                    else:
                        if not is_testing_env():
                            StudentActivity().student_timeline.delay(
                                student_id=str(application.get("student_id")),
                                event_type="Payment",
                                event_status="Done",
                                event_name=(
                                    f"{course_name} in {spec_name}"
                                    if spec_name not in ["", None]
                                    else f"{course_name} Program"
                                ),
                                college_id=str(application.get("college_id")),
                            )
                except KombuError as celery_error:
                    logger.error(f"error storing time line data " f"{celery_error}")
                except Exception as error:
                    logger.error(f"error storing time line data " f"{error}")
        if application.get("payment_attempts") is None:
            application["payment_attempts"] = []
        application_payment_info = {
            "payment_id": payment_id,
            "order_id": "",
            "status": "captured",
            "attempt_time": current_datetime,
        }
        application_payment_info.update(payment_extra_info)
        application.get("payment_attempts", []).insert(0, application_payment_info)
        update_info = {
            "payment_attempts": application.get("payment_attempts"),
            "payment_info": {
                "payment_id": payment_id,
                "order_id": "",
                "status": "captured",
                "created_at": current_datetime,
                "document_files": document_files,
                "reason_type": reason_type,
                "reason_name": reason_name,
                "note": note,
            },
        }
        update_info.update(payment_extra_info)
        if (
            await DatabaseConfiguration().studentApplicationForms.update_one(
                {"_id": ObjectId(application_id)}, {"$set": update_info}
            )
            is not None
        ):
            await StudentApplicationHelper().update_stage(
                str(application.get("student_id")), course_name, 7.50,
                spec_name, college_id=str(application.get("college_id"))
            )
            current_datetime = datetime.now(timezone.utc)
            update_data = {"last_user_activity_date": current_datetime}
            if student and not student.get("first_lead_activity_date"):
                update_data["first_lead_activity_date"] = current_datetime
            await DatabaseConfiguration().studentsPrimaryDetails.update_one({
                "_id": ObjectId(application.get("student_id"))},
                {"$set": update_data})
        await utility_obj.update_notification_db(
            event="Payment captured", application_id=application_id
        )
        await cache_invalidation(
            api_updated="student_application/update_payment_status"
        )
