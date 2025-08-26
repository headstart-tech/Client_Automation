"""
This file contains class and functions related to student payment activity
"""

import asyncio
from datetime import datetime

from bson import ObjectId
from fastapi import Request
from kombu.exceptions import KombuError

from app.background_task.send_mail_configuration import EmailActivity
from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.log_config import get_logger
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import cache_invalidation, is_testing_env
from app.helpers.promocode_voucher_helper.promocode_vouchers_helper import (
    promocode_vouchers_obj,
)

logger = get_logger(name=__name__)


class StudentPaymentActivity:
    """
    Contains functions related to student payment activity.
    """

    async def validate_and_get_payment_status_info(self, data: dict) -> tuple | None:
        """
        Validate webhook data and get payment information.

        Params:
            - data (dict): Webhook data which want to validate and get payment
                information.

        Returns:
            - tuple: A tuple which contains information like payment_id,
                order_id and status which got from webhook.
        """
        payment_id, status, order_id = None, None, None
        if "event" not in data:
            logger.error("Invalid data: 'event' key not found.")
            return
        if data.get("event") == "refund.processed":
            received_data = data.get("payload", {}).get("refund", {}).get("entity", {})
            payment_id = received_data.get("payment_id")
            order_id = received_data.get("order_id")
            status = "refunded"
        elif data.get("event") == "payment.captured":
            received_data = data.get("payload", {}).get("payment", {}).get("entity", {})
            payment_id = received_data.get("id")
            order_id = received_data.get("order_id")
            status = "captured"
        return payment_id, order_id, status

    async def update_and_get_data_by_existing_payment_id(
        self,
        find_payment_details: dict,
        status: str,
        current_datetime: datetime,
        payment_id: str,
        order_id: str,
        promocode: str,
        paid_amount: int | None
    ) -> tuple:
        """
        Update the data in the DB based on payment id.

        Params:
            - find_payment_details (dict): A dictionary which contains payment
                info.
            - status (str): Status of the payment which got from webhook.
            - current_datetime (datetime): Event datetime.
            - payment_id (str): Payment id which get in the webhook event data.
            - order_id (str): Order id of payment.
            - promocode (str): The promocode applied
            - paid_amount (int): The amount paid by lead after applying promocode

        Returns:
            - tuple: A tuple which a dictionary which contains payment
                information which want to update, application payment
                status, application_id and application.
        """

        # Update status and timestamp in payment collection
        update_info = {"status": status, f"{status}_at": current_datetime}
        if promocode != "":
            update_info.update(
                {
                    "payment_method": "Promocode",
                    "used_promocode": promocode,
                    "paid_amount": paid_amount,
                }
            )
        await DatabaseConfiguration().payment_collection.update_one(
            {"payment_id": find_payment_details.get("payment_id")},
            {"$set": update_info},
        )

        application_id = find_payment_details.get("details", {}).get("application_id")

        # Find corresponding student application
        application = await DatabaseConfiguration().studentApplicationForms.find_one(
            {"_id": application_id}
        )

        if not application:
            application = {}
            logger.info(
                f"Application data not found based on " f"payment id `{payment_id}`."
            )
        payment_attempts = application.get("payment_attempts", [])
        # Iterate through all payment attempts and update respective
        # payment attempt based on payment_id
        for _id, item in enumerate(payment_attempts):
            if item.get("payment_id") == payment_id:
                payment_attempts[_id]["status"] = status
                payment_attempts[_id]["attempt_time"] = current_datetime

        payment_info = application.get("payment_info", {})
        application_payment_status = payment_info.get("status")
        if application_payment_status != status:
            payment_info.update(
                {
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "status": status,
                    "created_at": current_datetime,
                }
            )
            if promocode != "" and application_payment_status == "captured":
                payment_info.update(
                    {
                        "payment_method": "Promocode",
                        "used_promocode": promocode,
                        "paid_amount": paid_amount,
                    }
                )
        return payment_info, application_payment_status, application_id, application

    async def add_and_get_data_by_payment_id(
        self,
        status: str,
        current_datetime: datetime,
        payment_id: str,
        order_id: str,
        promocode: str,
        paid_amount: int | None
    ) -> tuple:
        """
        Update the data in the DB based on payment id.

        Params:
            - status (str): Status of the payment which got from webhook.
            - current_datetime (datetime): Event datetime.
            - payment_id (str): Payment id which get in the webhook event data.
            - order_id (str): Order id of payment.

        Returns:
            - tuple: A tuple which a dictionary which contains payment
                information which want to update, application payment
                status, application_id and application.
        """
        # Find order details from DB using order_id
        order_details = await DatabaseConfiguration().payment_collection.find_one(
            {"order_id": order_id}
        )
        if not order_details:
            logger.info(f"Order data not found based on " f"order id `{order_id}`.")
            order_details = {}
        application_id = order_details.get("details", {}).get("application_id")
        # Store payment details when payment id not found
        application = await DatabaseConfiguration().studentApplicationForms.find_one(
            {"_id": application_id}
        )
        if application is None:
            logger.info(
                f"Application data not found based on " f"payment id `{payment_id}`."
            )
            application = {}
        payment_info = application.get("payment_info", {})
        payment_doc = {
            "payment_id": payment_id,
            "order_id": order_id,
            "merchant": "RazorPay",
            "user_id": order_details.get("user_id"),
            "details": {
                "purpose": "StudentApplication",
                "application_id": application_id,
            },
            "status": status,
            "attempt_time": current_datetime,
            f"{status}_at": current_datetime,
            "error": {
                "error_code": None,
                "description": None,
                "created_at": current_datetime,
            },
            "used_promocode": promocode,
            "payment_device": payment_info.get("payment_device"),
            "device_os": payment_info.get("device_os"),
        }
        if promocode:
            payment_doc.update(
                {
                    "payment_method": "Promocode",
                    "used_promocode": promocode,
                    "paid_amount": paid_amount,
                }
            )
        await DatabaseConfiguration().payment_collection.insert_one(payment_doc)
        if application.get("payment_attempts") is None:
            application["payment_attempts"] = []
        application.get("payment_attempts", []).insert(
            0,
            {
                "payment_id": payment_id,
                "order_id": order_id,
                "status": status,
                "attempt_time": current_datetime,
            },
        )
        application_payment_status = payment_info.get("status")
        if application_payment_status != status:
            payment_info.update(
                {
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "status": status,
                    "created_at": current_datetime,
                    "payment_device": payment_info.get("payment_device"),
                    "device_os": payment_info.get("device_os"),
                }
            )
            if promocode != "" and application_payment_status == "captured":
                payment_info.update(
                    {
                        "payment_method": "Promocode",
                        "used_promocode": promocode,
                        "paid_amount": paid_amount,
                    }
                )
        return payment_info, application_payment_status, application_id, application

    async def update_data_and_send_mail(
        self,
        application_id: ObjectId,
        application: dict,
        college: dict,
        current_datetime: datetime,
        payment_info: dict,
        application_payment_status: str,
        request: Request,
        status: str,
        promocode: str,
        paid_amount: int | None,
        college_id=None,
        course_fee: int | None = None
    ) -> None:
        """
        Update payment data in the student application collection and send
        payment successful mail.

        Params:
            - application_id (ObjectId): An unique application id.
            - application (dict): A dictionary which contains application data.
            - college (dict): A dictionary which contains college data.
            - current_datetime (datetime): Event datetime.
            - payment_info (dict): A dictionary which contains payment
                information which want to update.
            - application_payment_status (str): Application payment status.
            - request (Request): Request information.
            - status (str): Payment status which got from webhook.

        Returns: None
        """
        # Update status and attempts in application collection
        if (
            await DatabaseConfiguration().studentApplicationForms.update_one(
                {"_id": application_id},
                {
                    "$set": {
                        "payment_info": payment_info,
                        "payment_attempts": application.get("payment_attempts"),
                    }
                },
            )
        ) is not None:
            if application_payment_status != "captured" and status == "captured":
                if (
                    student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                        {"_id": application.get("student_id")}
                    )
                ) is not None:
                    course = await DatabaseConfiguration().course_collection.find_one(
                        {"_id": application.get("course_id")}
                    )
                    if not course:
                        course = {}
                        logger.info(
                            f"Course data not found based on application "
                            f"id `{application.get('_id')}` when sending "
                            f"payment captured mail in the payment "
                            f"webhook function."
                        )
                    course_name = course.get("course_name")
                    spec_name = application.get("spec_name1")

                    today_year = str(current_datetime.year)
                    invoice_number = f"{today_year}-INV01"
                    if (
                        await DatabaseConfiguration().application_payment_invoice_collection.find_one(
                            {"invoice_number": invoice_number}
                        )
                        is not None
                    ):
                        record = (
                            DatabaseConfiguration()
                            .application_payment_invoice_collection.find()
                            .sort({"created_at": -1})
                            .limit(5)
                        )
                        async for rec in record:
                            if rec.get("invoice_number"):
                                invoice_number = rec.get("invoice_number")
                                break
                        temp_old_invoice = invoice_number[9:]
                        try:
                            old_id = int(temp_old_invoice) + 1
                        except:
                            old_id = 1
                        invoice_number = invoice_number[:9] + str(old_id)

                    # Send payment successful mail to student if status is
                    # captured
                    basic_details = student.get("basic_details", {})
                    await EmailActivity().payment_successful(
                        data={
                            "invoice_number": invoice_number,
                            "payment_status": "success",
                            "created_at": current_datetime,
                            "order_id": payment_info.get("order_id"),
                            "payment_id": payment_info.get("payment_id"),
                            "student_name": utility_obj.name_can(basic_details),
                            "student_id": str(student.get("_id")),
                            "student_email_id": basic_details.get("email"),
                            "student_mobile_no": basic_details.get("mobile_number"),
                            "application_number": application.get(
                                "custom_application_id"
                            ),
                            "degree": f"{course_name} in " f"{spec_name}",
                            "college_name": college.get("name"),
                            "nationality": basic_details.get("nationality"),
                            "application_fees": (
                                course.get("fees") if promocode in ["",None] else paid_amount
                            ),
                            "student_first_name": basic_details.get("first_name", {}),
                        },
                        event_type="email",
                        event_status="sent",
                        event_name=f"Application ({course_name} "
                        f"in {spec_name}) "
                        f"payment successful ",
                        email_preferences=college.get("email_preferences", {}),
                        request=request,
                        college=college
                    )
                    if promocode != "":
                        await promocode_vouchers_obj.update_promocode_usage(
                            promocode, application_id, course, course_fee
                        )
                    await utility_obj.update_notification_db(
                        event="Payment captured", application_id=application_id
                    )
                    if 7.50 > application.get("current_stage"):
                        # Update current stage of application if payment
                        # is captured
                        await DatabaseConfiguration().studentApplicationForms.update_one(
                            {"_id": application_id}, {"$set": {"current_stage": 7.50}}
                        )
                        # Add student timeline if payment is captured
                        try:
                            if not is_testing_env():
                                StudentActivity().student_timeline.delay(
                                    student_id=str(application.get("student_id")),
                                    event_type="Payment",
                                    event_status="Done",
                                    application_id=str(application_id),
                                    event_name=(
                                        f"{course_name} in " f"{spec_name}"
                                        if (spec_name != "" and spec_name)
                                        else f"{course_name} Program"
                                    ),
                                    college_id=college_id,
                                )
                        except KombuError as celery_error:
                            logger.error(
                                f"error storing time line data " f"{celery_error}"
                            )
                        except Exception as error:
                            logger.error(f"error storing time line data {error}")
                else:
                    logger.info(
                        f"Student data not found based on application id "
                        f"`{application.get('_id')}` when sending payment "
                        f"captured mail in the payment webhook function."
                    )

    async def update_payment_status(
        self, data: dict, request: Request, college: dict
    ) -> None:
        """
        Update the payment status with the help of webhook. If payment is
        captured then sending mail to student and adding student timeline.

        Params:
            - data (dict): Data which get from webhook and use it for perform
                operation.
            - request (Request): A object of class Request which useful for get
                ip address and other details.
            - college (dict): A dictionary which contains college data.

        Returns:
            None: Returning none when some condition fails.
        """
        try:
            # We're using asyncio.sleep instead of time.sleep to not block
            # the thread
            await asyncio.sleep(2)

            # Extracting payment_id and status based on the event type in data
            payment_id, order_id, status = (
                await self.validate_and_get_payment_status_info(data)
            )

            # Check if payment_id exists, if not log an error
            if not payment_id:
                logger.error("No payment_id found.")
                return

            # Finding payment details in the database
            find_payment_details = (
                await DatabaseConfiguration().payment_collection.find_one(
                    {"payment_id": payment_id}
                )
            )

            current_datetime = datetime.utcnow()
            promocode = data.get("description", {}).get("code", "")
            course_fee = data.get("description", {}).get("course_fee")
            paid_amount = data.get("amount", None)

            # If payment details found, then proceed
            if find_payment_details:
                logger.info("Payment details found based on payment_id.")
                (
                    payment_info,
                    application_payment_status,
                    application_id,
                    application,
                ) = await self.update_and_get_data_by_existing_payment_id(
                    find_payment_details,
                    status,
                    current_datetime,
                    payment_id,
                    order_id,
                    promocode,
                    paid_amount,
                )
            else:
                logger.info(
                    "Payment id not exists in a system. Storing "
                    "payment details in a system ..."
                )
                (
                    payment_info,
                    application_payment_status,
                    application_id,
                    application,
                ) = await self.add_and_get_data_by_payment_id(
                    status,
                    current_datetime,
                    payment_id,
                    order_id,
                    promocode,
                    paid_amount,
                )

            await self.update_data_and_send_mail(
                application_id,
                application,
                college,
                current_datetime,
                payment_info,
                application_payment_status,
                request,
                status,
                promocode,
                paid_amount,
                college_id=college.get("id"),
                course_fee=course_fee
            )
            await cache_invalidation(
                api_updated="student_application/update_payment_status"
            )
        except Exception as error:
            logger.error(f"Something went wrong. Error - {error}. "
                         f"Error line#: {error.__traceback__.tb_lineno}")
