"""
This file contains function of verify email and mobile number by itp.
"""
import json
import re
from datetime import datetime, timedelta

from bson import ObjectId
from fastapi import HTTPException

from app.background_task.send_mail_configuration import EmailActivity
from app.background_task.send_sms import SmsActivity
from app.core.background_task_logging import background_task_wrapper
from app.core.utils import utility_obj, settings
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache, get_redis_client


class VerifyEmail_Mobile:

    async def validate_email(self, email):
        """
            Check if email is valid
        params:
            email (str): get an email in string format
        returns:
            response: true/false
        """
        if re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return True
        return False

    async def validate_email_or_mobile(self, email_or_mobile: str):
        """
            Check and validate email or mobile number

        params:
            email_or_mobile (str): Get email or mobile number

        returns:
            email variable with true and false
        """
        email = await self.validate_email(email_or_mobile)
        if email_or_mobile.isnumeric():
            if len(str(email_or_mobile)) != 10:
                raise HTTPException(status_code=422, detail="Invalid mobile" " number")
        if email and email_or_mobile.isnumeric():
            raise HTTPException(status_code=422, detail="email or mobile is invalid")
        return email

    @background_task_wrapper
    async def remove_old_data(self, now):
        """
        Remove the old data from the database
        """
        old_time = now - timedelta(minutes=60)
        await DatabaseConfiguration().student_verification_collection.delete_many(
            {"created_at": {"$lte": old_time}}
        )

    async def validate_email_mobile(
        self,
        background_task,
        college_id: str,
        email_or_mobile: str,
        otp: str | None = None,
        ip_address: str | None = None,
        action_type="system",
        mobile_prefix=None
    ):
        if (
            college := await DatabaseConfiguration().college_collection.find_one(
                {"_id": ObjectId(college_id)}
            )
        ) is None:
            raise HTTPException(status_code=404, detail="college not found")
        otp_time = college.get("mobile_otp_time", 3) * 60
        email = await self.validate_email_or_mobile(email_or_mobile)
        now = datetime.now()
        if email:
            var = "email"
        else:
            var = "mobile_number"
        redis_key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/{email_or_mobile}/otp"
        redis_client = get_redis_client()
        otp_sent = await redis_client.get(redis_key)
        if otp is not None:
            if otp_sent:
                otp_sent = json.loads(otp_sent)
                check_otp = otp_sent.get("otp")
                if check_otp == str(otp):
                    await redis_client.delete(redis_key)
                    return {"status": "success", "message": "OTP verified successfully"}
                else:
                    raise HTTPException(status_code=401, detail="OTP is not valid")
            else:
                raise HTTPException(status_code=401, detail="OTP is not valid")
        data = {
            f"{var}": email_or_mobile,
            "otp": await utility_obj.generate_random_otp(),
            "created_at": (datetime.now()).isoformat(),
        }
        if otp_sent is not None:
            otp_sent = json.loads(otp_sent)
            time_val = otp_sent.get("created_at")
            time_val = datetime.fromisoformat(time_val)
            remaining_time = now - time_val
            remaining_time = divmod(remaining_time.total_seconds(), 60)
            remaining_time = int(remaining_time[0] * 60) + int(remaining_time[1])
            remaining_time = otp_time - remaining_time
            if remaining_time <= 0:
                data1 = json.dumps(data)
                if await redis_client.set(redis_key, data1):
                    await redis_client.expire(redis_key, otp_time)
            else:
                return {
                    "status": "success",
                    "message": f"OTP already sent on your {var}",
                    "remaining_time": remaining_time,
                }
        else:
            data1 = json.dumps(data)
            if await redis_client.set(redis_key, data1):
                await redis_client.expire(redis_key, otp_time)
        if email:
            background_task.add_task(
                EmailActivity().send_otp_through_email,
                first_name="Student",
                email_otp=data.get("otp"),
                email=email_or_mobile,
                event_type="email",
                event_status="sent",
                event_name="Login with OTP",
                payload={
                    "content": "Login with OTP",
                    "email_list": [email_or_mobile],
                },
                current_user=email_or_mobile,
                ip_address=ip_address,
                email_preferences=college.get("email_preferences", {}),
                action_type=action_type,
                college_id=str(college.get("_id"))
            )
        else:
            templates = await get_collection_from_cache(collection_name="templates")
            if templates:
                otp_template = utility_obj.search_for_document(templates, field="template_name", search_name="otp")
            else:
                otp_template = (
                    await DatabaseConfiguration().otp_template_collection.find_one(
                        {"template_name": "otp"}
                    )
                )
                collection = await DatabaseConfiguration().otp_template_collection.aggregate([]).to_list(None)
                await store_collection_in_cache(collection, collection_name="templates")
            background_task.add_task(
                SmsActivity().send_sms_to_users,
                send_to=[email_or_mobile],
                dlt_content_id=otp_template.get("dlt_content_id", ""),
                sms_content=otp_template.get("content", "").format(
                    name="Student", otp=data.get("otp")
                ),
                sms_type=otp_template.get("sms_type", ""),
                sender=otp_template.get("sender", ""),
                ip_address=ip_address,
                student={},
                action_type=action_type,
                mobile_prefix=mobile_prefix
            )
        return {
            "status": "success",
            "message": "OTP sent successfully",
            "remaining_time": otp_time,
        }
