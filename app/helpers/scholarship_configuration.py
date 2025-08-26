"""
This file contains class and functions related to scholarship.
"""

from app.core import get_logger
from app.database.configuration import DatabaseConfiguration
from fastapi import Request
from app.core.custom_error import CustomError, DataNotFoundError
from bson import ObjectId
from app.core.utils import utility_obj, settings
from datetime import datetime, timezone
from app.background_task.scholarship import ScholarshipActivity
from app.background_task.send_mail_configuration import EmailActivity
from app.celery_tasks.scholarship import ScholarshipCeleryTasks
from app.s3_events.s3_events_configuration import get_attachment_information

logger = get_logger(name=__name__)


class Scholarship:
    """
    This class contains functions related to scholarship.
    """

    async def get_scholarship_details(
            self, application_id: ObjectId, course_id: ObjectId | None, spec_name: str | None, program_fee: int,
            college_id: str, program_info: dict, default_scholarship_id: ObjectId | None = None) -> tuple:
        """
        Retrieve scholarship details for a specific application based on program, course and college.

        Params:
            - application_id (ObjectId): The unique identifier of the application.
            - course_id (ObjectId | None): Either None or The ID of the course the student has applied for.
            - spec_name (str | None): Either None or The specialization name associated with the course.
            - program_fee (int): The base fee of the program, used to calculate waiver values.
            - college_id (str): The identifier of the college.
            - program_info (dict): Program-related information for get eligible scholarships.

        Returns:
            - tuple: A tuple which contains eligible scholarship details, default scholarship name and
                default_scholarship_amount.
        """
        program_based_scholarships = await DatabaseConfiguration().scholarship_collection.aggregate([
            {"$match": {"programs.course_id": course_id, "programs.specialization_name": spec_name}}
        ]).to_list(None)
        scholarship_details, default_scholarship_name, default_scholarship_amount, temp_scholarship_percentage = (
            [], "", 0, 0)
        for scholarship_info in program_based_scholarships:
            filters = scholarship_info.get("filters", {})
            advance_filters = scholarship_info.get("advance_filters", [])
            if not filters:
                filters = {}
            any_filter_applied = any(filters.values())
            waiver_value = scholarship_info.get("waiver_value")
            position, waiver_type = 1, scholarship_info.get("waiver_type")
            if waiver_type == "Amount":
                percentage_value = round((waiver_value / program_fee) * 100, 2) if program_fee else 0
                fees_after_waiver = round(program_fee - waiver_value, 2)
            else:
                percentage_value = waiver_value
                fees_after_waiver = round(program_fee * (1 - (waiver_value / 100)), 2)
            scholarship_name, scholarship_id = scholarship_info.get("name"), scholarship_info.get("_id")
            if default_scholarship_id and default_scholarship_id == scholarship_id:
                position, default_scholarship_name, temp_scholarship_percentage = 0, scholarship_name, percentage_value
                default_scholarship_amount = program_fee - fees_after_waiver
            elif not default_scholarship_id and percentage_value > temp_scholarship_percentage:
                position, default_scholarship_name, temp_scholarship_percentage = 0, scholarship_name, percentage_value
                default_scholarship_amount = program_fee - fees_after_waiver
            temp_scholarship_info = {
                "scholarship_id": str(scholarship_info.get("_id")),
                "scholarship_name": scholarship_name,
                "program_fee": program_fee,
                "scholarship_waiver_type": waiver_type,
                "scholarship_waiver_value": waiver_value,
                "fee_after_waiver": fees_after_waiver,
                "percentage": percentage_value}
            if not any_filter_applied and not advance_filters:
                scholarship_details.insert(position, temp_scholarship_info)
            else:
                application_ids = await ScholarshipActivity().get_eligible_applicants_info(
                    programs_info=program_info,
                    normal_filters=scholarship_info.get("filters", {}),
                    advance_filters=scholarship_info.get("advance_filters", []),
                    college_id=college_id
                )
                if application_id in application_ids:
                    scholarship_details.insert(position, temp_scholarship_info)
        return scholarship_details, default_scholarship_name, default_scholarship_amount

    async def get_program_registration_fee(self, application_information: dict) -> int:
        """
        Get the program registration/enrollment fee.

        Params:
            - application_information: A dictionary which contains program fee.

        Returns:
            - int: An integer value which return program registration/enrollment fee.
        """
        if (course_information := await DatabaseConfiguration().course_collection.find_one(
                {"_id": ObjectId(application_information.get("course_id"))})) is None:
            course_information = {}
        spec_details = next(
            (
                data.get("spec_fee_info", {})
                for data in course_information.get("course_specialization", [])
                if data.get("spec_name") == application_information.get("spec_name1")
            ),
            {},
        )
        return int(spec_details.get("registration_fee", 0))

    async def get_send_scholarship_letter_info(self, scholarship_info: dict, scholarship_waiver_type: str,
                                               scholarship_waiver_value: float,
                                               college_id: str, custom_scholarship: bool | None = False) -> tuple:
        """
        Get send scholarship letter information.

        Params:
            - scholarship_info (dict): A dictionary which contains scholarship information.
            - scholarship_waiver_type (str): A string value which refers scholarship waiver type.
            - scholarship_waiver_value (float): A float value which refers scholarship waiver value.
            - college_id (str): A string value which refers college unique identifier.
            - custom_scholarship (bool): A boolean which useful for understand provided custom scholarship
                details or not.

        Returns:
            - tuple: A tuple which contains offered applicants, offered applicants info, email ids and program_fees.

        Raises:
            - CustomError: Raise when default and custom scholarship amount exceed program fee.
        """
        email_ids, offered_applicants, offered_applicants_info, program_fees_list = [], [], [], []
        for application_id in scholarship_info.get("application_ids", []):
            await utility_obj.is_length_valid(application_id, "Application Id")
            obj_application_id = ObjectId(application_id)
            if (application_information := await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"_id": obj_application_id})) is None:
                raise DataNotFoundError(application_id, "Application")
            program_fee = await self.get_program_registration_fee(application_information)
            program_fees_list.append(program_fee)
            if scholarship_waiver_type == "Percentage":
                fees_after_waiver = round(program_fee * (1 - (scholarship_waiver_value / 100)), 2)
            else:
                fees_after_waiver = round(program_fee - scholarship_waiver_value, 2)
            scholarship_amount = round(program_fee - fees_after_waiver, 2)
            if custom_scholarship:
                default_scholarship_amount = application_information.get("offered_scholarship_info", {}).get(
                    "default_scholarship_amount")
                if not default_scholarship_amount:
                    course_id = application_information.get("course_id")
                    spec_name = application_information.get("spec_name1")
                    scholarship_details, default_scholarship_name, default_scholarship_amount = \
                        await self.get_scholarship_details(
                            obj_application_id, application_information.get("course_id"),
                            spec_name, program_fee, college_id,
                            {"course_id": [course_id], "course_specialization": [spec_name]})
                if (scholarship_amount + default_scholarship_amount) > program_fee:
                    raise CustomError("Default and custom scholarship amount exceeding program fee amount.")
            if obj_application_id not in offered_applicants:
                offered_applicants.append(obj_application_id)
                offered_applicants_info.append({
                    "application_id": application_id,
                    "fees_after_waiver": fees_after_waiver,
                    "scholarship_amount": scholarship_amount,
                    "program_fee": program_fee
                })
                if (student_information := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                        {"_id": ObjectId(application_information.get("student_id"))})) is not None:
                    email_ids.append(student_information.get("user_name"))
        return offered_applicants, offered_applicants_info, email_ids, program_fees_list

    async def send_scholarship_letter_through_mail(
            self, scholarship_information: dict, template_information: dict, email_preferences: dict, email_ids: list,
            user: dict, request: Request, college_id: str, template_id: str) -> None:
        """
        Send a scholarship letter through mail.

        Params:
            - scholarship_information (dict): A dictionary which contains scholarship information.
            - template_information (dict): A dictionary which contains template information.
            - email_preferences (dict): A dictionary which contains email preferences information.
            - email_ids (list): A list which contains email ids of recipients.
            - user (dict): A dictionary which contains user information.
            - request (Request): A FastAPI request object.
            - college_id (str): Unique identifier/id of a college.
            - template_id (str): Unique identifier/id of a template.

        Returns: None
        """
        template_content = template_information.get("content")
        attachments = await get_attachment_information(template_information)
        if settings.environment in ["demo"]:
            EmailActivity().send_email_based_on_client_preference_provider(
                email_preferences=email_preferences,
                email_type="default",
                email_ids=email_ids,
                subject=template_information.get("subject"),
                template=template_content,
                event_type="email",
                event_status="sent",
                event_name="Scholarship Letter",
                current_user=user.get("email"),
                ip_address=utility_obj.get_ip_address(request),
                payload={
                    "content": template_content,
                    "email_list": email_ids,
                },
                college_id=college_id,
                scholarship_information=scholarship_information,
                template_id=template_id,
                attachments=attachments
            )
        else:
            EmailActivity().send_email_based_on_client_preference_provider.delay(
                email_preferences=email_preferences,
                email_type="default",
                email_ids=email_ids,
                subject=template_information.get("subject"),
                template=template_content,
                event_type="email",
                event_status="sent",
                event_name="Scholarship Letter",
                current_user=user.get("email"),
                ip_address=utility_obj.get_ip_address(request),
                payload={
                    "content": template_content,
                    "email_list": email_ids,
                },
                college_id=college_id,
                scholarship_information=scholarship_information,
                template_id=template_id,
                attachments=attachments
            )

    async def get_validate_programs_information(self, programs_info: list, convert_course_id: bool = True) -> tuple:
        """
        Get the programs information in validate/required format.

        Params:
            - programs_info (list): List of programs information.
            - convert_course_id (bool, optional): Convert course_id to ObjectId. Defaults to True.

        Returns:
            - tuple: A tuple which contains validated and required programs information.
        """
        course_ids, course_specializations_list, course_names, registration_fees = [], [], [], []
        if programs_info:
            for _id, program_info in enumerate(programs_info):
                course_id = program_info.get("course_id")
                if (course_info := await DatabaseConfiguration().course_collection.find_one(
                        {"_id": ObjectId(course_id)})) is None:
                    raise DataNotFoundError(course_id, "Course")
                course_name = program_info.get("course_name")
                if course_name != course_info.get("course_name"):
                    raise CustomError(f"Invalid course name.")
                spec_name = program_info.get("specialization_name")
                course_specializations = course_info.get("course_specialization", [])
                if course_specializations:
                    temp_course_specializations = [i["spec_name"] for i in course_specializations]
                    if spec_name not in temp_course_specializations:
                        raise CustomError(f"Invalid specialization for course {course_name}.")
                course_ids.append(course_id)
                if convert_course_id:
                    programs_info[_id]["course_id"] = ObjectId(course_id)
                course_specializations_list.append(spec_name)
                course_names.append(course_name)
                spec_details = next(
                    (
                        data.get("spec_fee_info", {})
                        for data in course_specializations
                        if data.get("spec_name") == spec_name
                    ),
                    {},
                )
                registration_fees.append(int(spec_details.get("registration_fee", 0)))
        return course_ids, course_specializations_list, course_names, registration_fees

    async def validate_scholarship_name(self, scholarship_name: str) -> None:
        """
        Validate scholarship name.

        Params:
            - scholarship_information (dict): A dictionary containing the scholarship information.

        Returns: None

        Raises:
            - CustomError: An error occurred when scholarship name already exist in DB.
        """
        if await DatabaseConfiguration().scholarship_collection.find_one({"name": scholarship_name}):
            raise CustomError("Scholarship name already exists.")

    async def validate_scholarship_by_id(self, scholarship_id: str) -> dict:
        """
        Validate scholarship by id.

        Params:
            - scholarship_id (str): A string value which represents unique identifier of scholarship.

        Returns: None

        Raises:
            - DataNotFoundError: An error occurred when scholarship not found in DB by id.
        """
        if (scholarship_info := await DatabaseConfiguration().scholarship_collection.find_one(
                {"_id": ObjectId(scholarship_id)})) is None:
            raise DataNotFoundError(scholarship_id, "Scholarship")
        return scholarship_info

    async def validate_scholarship_input_info(self, scholarship_information: dict,
                                              is_scholarship_exists: bool = False) -> dict:
        """
        Validate scholarship input data.

        Params:
            - scholarship_information (dict): A dictionary containing the scholarship information.
            - is_scholarship_exists (bool): A boolean value which indicates that scholarship exist in the DB or not,
                useful for skip validations. Defaults to False.

        Returns:
            - dict: A dictionary which contains information about the programs.

        Raises:
            - CustomError: An error occurred when validation of input failed.
            - DataNotFoundError: An error occurred when course not found by course_id.
        """
        template_name, scholarship_name = None, None
        if not is_scholarship_exists:
            temp_scholarship_name = scholarship_information.get("name")
            await self.validate_scholarship_name(temp_scholarship_name)
            if await DatabaseConfiguration().scholarship_collection.find_one(
                    {"name": temp_scholarship_name}):
                raise CustomError("Scholarship name already exists.")
            scholarship_id = scholarship_information.get("copy_scholarship_id")
            if scholarship_id:
                scholarship_info = await self.validate_scholarship_by_id(scholarship_id)
                scholarship_information["copy_scholarship_id"] = ObjectId(scholarship_id)
                scholarship_name = scholarship_info.get("name")
            template_id = scholarship_information.get("template_id")
            if template_id:
                if (template_info := await DatabaseConfiguration().template_collection.find_one(
                        {"_id": ObjectId(template_id)})) is None:
                    raise DataNotFoundError(template_id, "Template")
                scholarship_information["template_id"] = ObjectId(template_id)
                template_name = template_info.get("template_name")
        programs_info = scholarship_information.get("programs")
        course_ids, course_specializations_list, course_names, registration_fees = \
            await self.get_validate_programs_information(programs_info)
        if not is_scholarship_exists:
            waiver_value = scholarship_information.get("waiver_value")
            if scholarship_information.get("waiver_type") == "Percentage":
                if waiver_value > 100:
                    raise CustomError("Scholarship percentage should be less than or equal to 100.")
            else:
                maximum_waiver_value = min(registration_fees)
                if waiver_value > maximum_waiver_value:
                    raise CustomError(f"Scholarship amount should be less than or equal to {maximum_waiver_value}.")
        return {"course_id": course_ids, "course_specialization": course_specializations_list,
                "course_name": course_names, "registration_fee": registration_fees, "template_name": template_name,
                "scholarship_name": scholarship_name}

    async def create_scholarship(self, request: Request, scholarship_information: dict, user: dict,
                                 college_id: str) -> dict:
        """
        Create a new scholarship.

        Params:
            - request (Request): FastAPI request object for get ip address.
            - scholarship_information (dict): A dictionary containing the scholarship information.
            - user (dict): A dictionary containing user information.
            - college_id (str): An unique identifier/id of college.

        Returns:
            - dict: A dictionary which contains the information about the scholarship create.

        Raises:
            - CustomError: An error occurred when validation of input failed.
            - DataNotFoundError: An error occurred when course not found by course_id.
        """
        filter_programs_info = await self.validate_scholarship_input_info(scholarship_information)
        created_on = datetime.now(timezone.utc)
        scholarship_information.update({
            "ip_address": utility_obj.get_ip_address(request),
            "created_at": created_on,
            "created_by_id": ObjectId(user.get("_id")),
            "created_by_name": utility_obj.name_can(user)
        })
        created_scholarship_id = await DatabaseConfiguration().scholarship_collection.insert_one(
            scholarship_information)
        scholarship_id = str(created_scholarship_id.inserted_id)
        if settings.environment not in ["demo"]:
            await ScholarshipCeleryTasks().update_eligible_applicants_logic(
                programs_info=filter_programs_info,
                normal_filters=scholarship_information.get("filters", {}),
                advance_filters=scholarship_information.get("advance_filters"),
                college_id=college_id,
                scholarship_id=scholarship_id,
                user=user
            )
        else:
            ScholarshipCeleryTasks().update_eligible_applicants_info_in_db.delay(
                programs_info=filter_programs_info,
                normal_filters=scholarship_information.get("filters", {}),
                advance_filters=scholarship_information.get("advance_filters"),
                college_id=college_id,
                scholarship_id=scholarship_id,
                user=user
            )
        return {"created_scholarship_id": scholarship_id, "message": "Scholarship created successfully."}

    async def get_programs_fee_info(self, programs_info: dict, scholarship_waiver_type: str,
                                    scholarship_waiver_value: float) -> list:
        """
        Get programs fee information based on scholarship.

        Params:
            - programs_info (dict): A dictionary which contains program (s) information.
            - scholarship_waiver_type (str): Type of scholarship waiver.
            - scholarship_waiver_value (float): Value of scholarship waiver.

        Returns:
            - list: A list which contains programs fee information based on scholarship
        """
        courses_info = programs_info.get("course_id", [])
        specializations_info = programs_info.get("course_specialization", [])
        programs_fee_info = []
        if courses_info and specializations_info:
            programs_fee_info = [{
                "program_name": f"{course_name} {'of' if course_name in ['Master', 'Bachelor'] else 'in'} {spec_name}",
                "course_name": course_name,
                "specialization_name": spec_name,
                "first_year_fee": course_registration_fee,
                "fee_after_waiver": round(course_registration_fee * (1 - (scholarship_waiver_value / 100)),
                                          2) if scholarship_waiver_type == "Percentage" else round(
                    course_registration_fee - scholarship_waiver_value, 2)
            } for course_id, spec_name, course_name, course_registration_fee in zip(
                courses_info, specializations_info, programs_info.get("course_name", []),
                programs_info.get("registration_fee", []))]
        return programs_fee_info

    async def get_programs_fee_and_eligible_count_info(self, scholarship_information: dict, college_id: str) -> dict:
        """
        Get programs fee and eligible count information based on scholarship information.

        Params:
            - scholarship_information (dict): A dictionary which contains the scholarship information.
            - college_id (str): An unique identifier/id of college.

        Returns:
            - dict: A dictionary which contains information about programs fee and eligible count.

        Raises:
            - CustomError: An error occurred when validation of input failed.
            - DataNotFoundError: An error occurred when course/template not found by course_id/template_id.
            - Exception: An error occurred when something wrong happened in the code.
        """
        filter_programs_info = await self.validate_scholarship_input_info(scholarship_information)
        return {"eligible_applicants_count": await ScholarshipActivity().get_eligible_applicants_info(
            programs_info=filter_programs_info,
            normal_filters=scholarship_information.get("filters", {}),
            advance_filters=scholarship_information.get("advance_filters"),
            college_id=college_id,
            get_count_only=True
        ), "programs_fee_info": await self.get_programs_fee_info(
            filter_programs_info, scholarship_information.get("waiver_type"),
            scholarship_information.get("waiver_value")),
                "template_name": filter_programs_info.get("template_name"),
                "scholarship_name": filter_programs_info.get("scholarship_name")}

    async def update_scholarship_status(self, scholarship_id: str, status: str) -> dict:
        """
        Validate scholarship name.

        Params:
            - scholarship_id (str): A string value which represents unique identifier of scholarship.
            - status (str): A string value which represents status of scholarship.

        Returns:
            - dict: A dictionary which contains information about update scholarship status.
        """
        await utility_obj.is_length_valid(scholarship_id, "Scholarship id")
        await Scholarship().validate_scholarship_by_id(scholarship_id)
        if (
                await DatabaseConfiguration().scholarship_collection.update_one(
                    {"_id": ObjectId(scholarship_id)}, {"$set": {"status": status,
                                                                 "status_updated_at": datetime.now(timezone.utc)}}
                )
                is not None
        ):
            return {"message": f"Scholarship status updated successfully to {status.title()}."}
        return {"message": "Scholarship status not updated."}

    async def give_custom_scholarship(self, testing: bool, request: Request, custom_scholarship_info: dict, user: dict,
                                      college_id: str,
                                      email_preferences: dict) -> dict:
        """
        Give custom scholarship to applicants.

        Params:
            - testing (bool): A boolean value to check if it's testing or not.
            - request (Request): FastAPI request object for get ip address.
            - custom_scholarship_info: A dictionary which contains information about the custom scholarship.
            - user (dict): A dictionary which contains information about the user.
            - college_id (str): Unique identifier of the college.
            - email_preferences (dict): A dictionary which contains email preferences information.


        Returns:
            - dict: A dictionary which contains information about give custom scholarship.
        """
        template_id = custom_scholarship_info.get("template_id")
        template_information = await DatabaseConfiguration().template_collection.find_one(
            {"_id": ObjectId(template_id)})
        if not template_information:
            raise DataNotFoundError(template_id, "Template")
        scholarship_waiver_type = custom_scholarship_info.get("waiver_type")
        scholarship_waiver_value = custom_scholarship_info.get("waiver_value")
        if scholarship_waiver_type == "Percentage":
            if scholarship_waiver_value > 100:
                raise CustomError("Scholarship percentage should be less than or equal to 100.")
        offered_applicants, offered_applicants_info, email_ids, program_fees_list = \
            await self.get_send_scholarship_letter_info(custom_scholarship_info, scholarship_waiver_type,
                                                        scholarship_waiver_value, college_id, custom_scholarship=True)
        if scholarship_waiver_type == "Amount":
            maximum_waiver_value = min(program_fees_list)
            if scholarship_waiver_value > maximum_waiver_value:
                raise CustomError(f"Scholarship amount should be less than or equal to {maximum_waiver_value}.")
        custom_scholarship = await DatabaseConfiguration().scholarship_collection.find_one(
            {"name": "Custom scholarship"})
        if custom_scholarship:
            existing_offered_applicants = custom_scholarship.get("offered_applicants", [])
            offered_applicants = [_id for _id in offered_applicants if _id not in existing_offered_applicants]
            if offered_applicants:
                offered_applicants.extend(existing_offered_applicants)
                delist_applicants = custom_scholarship.get("delist_applicants", [])
                [delist_applicants.remove(_id) for _id in offered_applicants if _id in delist_applicants]
                await DatabaseConfiguration().scholarship_collection.update_one(
                    {"name": "Custom scholarship"},
                    {"$set": {"offered_applicants_count": len(offered_applicants),
                              "offered_applicants": offered_applicants,
                              "delist_applicants_count": len(delist_applicants),
                              "delist_applicants": delist_applicants}})
            custom_scholarship_id = custom_scholarship.get("_id")
        else:
            inserted_custom_scholarship = await DatabaseConfiguration().scholarship_collection.insert_one(
                {"name": "Custom scholarship", "offered_applicants_count": len(offered_applicants),
                 "offered_applicants": offered_applicants,
                 "status": "Active"})
            custom_scholarship_id = inserted_custom_scholarship.inserted_id
        if email_ids and not testing:
            await self.send_scholarship_letter_through_mail(
                {"scholarship_id": str(custom_scholarship_id),
                 "scholarship_name": "Custom scholarship",
                 "template_id": str(template_id),
                 "template_name": template_information.get("template_name"),
                 "scholarship_waiver_type": scholarship_waiver_type,
                 "scholarship_waiver_value": scholarship_waiver_value,
                 "description": custom_scholarship_info.get("description"),
                 "offered_applicants_info": offered_applicants_info,
                 "scholarship_letter_current_status": "Sent",
                 "provided_by_id": user.get("_id"),
                 "provided_by_name": utility_obj.name_can(user)
                 }, template_information, email_preferences, email_ids, user, request, college_id,
                template_id)
        return {"message": "Custom scholarship given to applicants."}

    async def send_scholarship_letter_to_applicants(self, testing: bool, request: Request, send_letter_info: dict,
                                                    user: dict,
                                                    college_id: str, email_preferences: dict) -> dict:
        """
        Send scholarship letter to applicants.

        Params:
            - testing (bool): A boolean value to check if it's testing or not.
            - request (Request): FastAPI request object for get ip address.
            - send_letter_info: A dictionary which contains information about send scholarship letter.
            - user (dict): A dictionary which contains information about the user.
            - college_id (str): Unique identifier of the college.
            - email_preferences (dict): A dictionary which contains email preferences information.


        Returns:
            - dict: A dictionary which contains information about give custom scholarship.
        """
        scholarship_id = send_letter_info.get("scholarship_id")
        await utility_obj.is_length_valid(scholarship_id, "Scholarship id")
        scholarship_info = await self.validate_scholarship_by_id(scholarship_id)
        template_id = send_letter_info.get("template_id")
        template_information = await DatabaseConfiguration().template_collection.find_one(
            {"_id": ObjectId(template_id)})
        if not template_information:
            raise DataNotFoundError(template_id, "Template")
        scholarship_waiver_type = scholarship_info.get("waiver_type")
        scholarship_waiver_value = scholarship_info.get("waiver_value")
        offered_applicants, offered_applicants_info, email_ids, program_fees_list = \
            await self.get_send_scholarship_letter_info(send_letter_info, scholarship_waiver_type,
                                                        scholarship_waiver_value, college_id)
        existing_offered_applicants = scholarship_info.get("offered_applicants", [])
        offered_applicants = [_id for _id in offered_applicants if _id not in existing_offered_applicants]
        offered_applicants.extend(existing_offered_applicants)
        if offered_applicants:
            delist_applicants = scholarship_info.get("delist_applicants", [])
            [delist_applicants.remove(_id) for _id in offered_applicants if _id in delist_applicants]
            await DatabaseConfiguration().scholarship_collection.update_one(
                {"_id": ObjectId(scholarship_id)},
                {"$set": {"offered_applicants_count": len(offered_applicants), "offered_applicants": offered_applicants,
                          "delist_applicants_count": len(delist_applicants), "delist_applicants": delist_applicants}})
        if email_ids and not testing:
            await self.send_scholarship_letter_through_mail(
                {"scholarship_id": scholarship_id,
                 "scholarship_name": scholarship_info.get("name"),
                 "template_id": template_id,
                 "template_name": template_information.get("template_name"),
                 "scholarship_waiver_type": scholarship_waiver_type,
                 "scholarship_waiver_value": scholarship_waiver_value,
                 "description": "",
                 "offered_applicants_info": offered_applicants_info,
                 "scholarship_letter_current_status": "Sent",
                 "provided_by_id": user.get("_id"),
                 "provided_by_name": utility_obj.name_can(user)
                 }, template_information, email_preferences, email_ids, user, request, college_id,
                template_id)
        return {"message": "Scholarship letter sent to applicants."}

    async def delist_applicants_from_scholarship(self, scholarship_id: str, application_ids: list[str]) -> dict:
        """
        De-list applicants from scholarship list.

        Params:
            - scholarship_id (str): A string value which represents unique identifier of scholarship.
            - application_ids (list[str]): A list of strings which represents unique identifiers of applicants.

        Returns:
            - dict: A dictionary which contains information about give custom scholarship.
        """
        await utility_obj.is_length_valid(scholarship_id, "Scholarship id")
        scholarship_info = await self.validate_scholarship_by_id(scholarship_id)

        offered_applicants = scholarship_info.get("offered_applicants", [])
        delist_applicants = scholarship_info.get("delist_applicants", [])
        application_ids = set(application_ids)
        scholarship_id = ObjectId(scholarship_id)

        db_config = DatabaseConfiguration()
        app_form_collection = db_config.studentApplicationForms

        for app_id_str in application_ids:
            await utility_obj.is_length_valid(app_id_str, "Application id")
            application_id = ObjectId(app_id_str)
            application_info = await app_form_collection.find_one({"_id": application_id})
            if not application_info:
                continue
            if application_id in offered_applicants:
                offered_applicants.remove(application_id)
                if application_id not in delist_applicants:
                    delist_applicants.append(application_id)

                await app_form_collection.update_one(
                    {
                        "_id": application_id,
                        "offered_scholarship_info.all_scholarship_info.scholarship_id": scholarship_id
                    },
                    {
                        "$set": {"offered_scholarship_info.all_scholarship_info.$[elem].hide": True}
                    },
                    array_filters=[
                        {"elem.scholarship_id": scholarship_id}
                    ]
                )
                offered_scholarship_info = application_info.get("offered_scholarship_info", {})
                add_unset_query, unset_query, update_info, final_update_query = False, {}, {}, {}

                if offered_scholarship_info.get("default_scholarship_id") == scholarship_id:
                    add_unset_query = True
                    unset_query = {"offered_scholarship_info.default_scholarship_id": True,
                                   "offered_scholarship_info.default_scholarship_name": True,
                                   "offered_scholarship_info.default_scholarship_waiver_type": True,
                                   "offered_scholarship_info.default_scholarship_waiver_value": True,
                                   "offered_scholarship_info.default_scholarship_fees_after_waiver": True,
                                   "offered_scholarship_info.default_scholarship_amount": True}

                elif (offered_scholarship_info.get("custom_scholarship_info", {}).get("scholarship_id") ==
                      scholarship_id):
                    update_info.update({"custom_scholarship_applied": False, "custom_scholarship_info": {}})

                if update_info:
                    final_update_query.update({"$set": update_info})
                if add_unset_query:
                    final_update_query.update({"$unset": unset_query})
                if final_update_query:
                    await app_form_collection.update_one(
                        {
                            "_id": application_id,
                            "$or": [
                                {"offered_scholarship_info.all_scholarship_info.scholarship_id": scholarship_id},
                                {"offered_scholarship_info.custom_scholarship_info.scholarship_id": scholarship_id}
                            ]
                        },
                        final_update_query
                    )
            for idx, program in enumerate(scholarship_info.get("programs", [])):
                if (program.get("course_id") == application_info.get("course_id") and
                        program.get("specialization_name") == application_info.get("spec_name1")):
                    program_offered_applicants = program.get("offered_applicants", [])
                    if application_id in program_offered_applicants:
                        program_offered_applicants.remove(application_id)
                        db_config.scholarship_collection.update_one(
                            {"_id": scholarship_id},
                            {"$set": {f"programs.{idx}.offered_applicants": program_offered_applicants,
                                      f"programs.{idx}.offered_applicants_count": len(
                                          program_offered_applicants)}
                             })
                    break

        await db_config.scholarship_collection.update_one(
            {"_id": scholarship_id},
            {
                "$set": {
                    "offered_applicants": offered_applicants,
                    "offered_applicants_count": len(offered_applicants),
                    "delist_applicants": delist_applicants,
                    "delist_applicants_count": len(delist_applicants)
                }
            }
        )
        return {"message": "De-list applicants from scholarship list."}

    async def change_default_scholarship(self, change_default_scholarship_info: dict, user: dict) -> dict:
        """
        Change default scholarship of applicant.

        Params:
            - change_default_scholarship_info (dict): A dictionary which contains information about change default
                scholarship.
            - user (dict): A dictionary which contains information about the user.

        Returns:
            - dict: A dictionary which contains information about change default scholarship.
        """
        application_id = change_default_scholarship_info.get("application_id")
        obj_application_id = ObjectId(application_id)
        if (
                application_information := await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"_id": obj_application_id}
                )
        ) is None:
            raise DataNotFoundError(message="Application", _id=application_id)
        scholarship_id = change_default_scholarship_info.get("default_scholarship_id")
        exist_offered_scholarship_info = application_information.get("offered_scholarship_info", {})
        all_scholarship_info = exist_offered_scholarship_info.get("all_scholarship_info", [])
        program_fee = await self.get_program_registration_fee(application_information)
        default_scholarship_amount = exist_offered_scholarship_info.get("default_scholarship_amount", 0)
        update_data, temp_data = {}, exist_offered_scholarship_info.copy()
        if scholarship_id:
            await utility_obj.is_length_valid(scholarship_id, "Scholarship id")
            scholarship_info = await self.validate_scholarship_by_id(scholarship_id)
            if exist_offered_scholarship_info.get("default_scholarship_id") != ObjectId(scholarship_id):
                waiver_type = scholarship_info.get("waiver_type")
                waiver_value = scholarship_info.get("waiver_value")
                if waiver_type == "Amount":
                    fees_after_waiver = round(program_fee - waiver_value, 2)
                else:
                    fees_after_waiver = round(program_fee * (1 - (waiver_value / 100)), 2)
                default_scholarship_amount = round(program_fee - fees_after_waiver, 2)
                update_data.update({"offered_scholarship_info": {
                    "custom_scholarship_applied": temp_data.get("custom_scholarship_applied", False),
                    "custom_scholarship_info": temp_data.get("custom_scholarship_info", {}),
                    "default_scholarship_id": ObjectId(scholarship_id),
                    "default_scholarship_name": scholarship_info.get("name"),
                    "default_scholarship_waiver_type": waiver_type,
                    "default_scholarship_waiver_value": waiver_value,
                    "program_fee": program_fee,
                    "default_scholarship_fees_after_waiver": fees_after_waiver if fees_after_waiver else 0,
                    "default_scholarship_amount": default_scholarship_amount,
                    "all_scholarship_info": all_scholarship_info,
                    "changed_by": ObjectId(user.get("_id")),
                    "changed_by_name": utility_obj.name_can(user),
                    "changed_at": datetime.now(timezone.utc)
                }})
        temp_offered_scholarship_info = update_data.get("offered_scholarship_info")
        update_data["offered_scholarship_info"] = temp_offered_scholarship_info \
            if temp_offered_scholarship_info else exist_offered_scholarship_info
        if change_default_scholarship_info.get("set_custom_scholarship"):
            scholarship_waiver_type = change_default_scholarship_info.get("waiver_type")
            scholarship_waiver_value = change_default_scholarship_info.get("waiver_value")
            if not (scholarship_waiver_type and scholarship_waiver_value):
                return {"detail": "Scholarship waiver type and value are mandatory when set custom scholarship "
                                  "as default scholarship."}
            if scholarship_waiver_type == "Percentage":
                if scholarship_waiver_value > 100:
                    return {"detail": "Custom scholarship percentage should be less than or equal to 100."}
                scholarship_amount = round(program_fee * (scholarship_waiver_value / 100), 2)
            else:
                scholarship_amount = round(scholarship_waiver_value, 2)
            if (scholarship_amount + default_scholarship_amount) > program_fee:
                return {"detail": "Default and custom scholarship amount exceeding program fee amount."}
            custom_scholarship = await DatabaseConfiguration().scholarship_collection.find_one(
                {"name": "Custom scholarship"})
            if not custom_scholarship:
                await DatabaseConfiguration().scholarship_collection.insert_one(
                    {"name": "Custom scholarship", "status": "Active"})
                custom_scholarship = await DatabaseConfiguration().scholarship_collection.find_one(
                    {"name": "Custom scholarship"})
            update_data.get("offered_scholarship_info", {}).update(
                {"custom_scholarship_applied": True,
                 "custom_scholarship_info": {
                     "scholarship_id": custom_scholarship.get("_id"),
                     "scholarship_name": custom_scholarship.get("name"),
                     "scholarship_waiver_type": scholarship_waiver_type,
                     "scholarship_waiver_value": scholarship_waiver_value,
                     "description": change_default_scholarship_info.get("description"),
                     "fees_after_waiver": round(program_fee - scholarship_amount, 2),
                     "scholarship_amount": scholarship_amount
                 }})
            existing_offered_applicants = custom_scholarship.get("offered_applicants", [])
            if obj_application_id not in existing_offered_applicants:
                existing_offered_applicants.insert(0, obj_application_id)
                await DatabaseConfiguration().scholarship_collection.update_one(
                    {"name": "Custom scholarship"},
                    {"$set": {"offered_applicants_count": len(existing_offered_applicants),
                              "offered_applicants": existing_offered_applicants}})
        else:
            update_data.get("offered_scholarship_info", {}).update({"custom_scholarship_applied": False,
                                                                    "custom_scholarship_info": {}})
            await DatabaseConfiguration().scholarship_collection.update_one(
                {"name": "Custom scholarship", "offered_applicants": {"$in": [obj_application_id]}},
                {"$inc": {"offered_applicants_count": -1}, "$pull": {"offered_applicants": obj_application_id}}
            )
        if update_data:
            await DatabaseConfiguration().studentApplicationForms.update_one(
                {"_id": ObjectId(application_id)}, {"$set": update_data})
        return {"message": "Default scholarship changed."}

    async def get_scholarship_overview_details(
            self, application_id: str, default_scholarship_id: str, waiver_type: str | None,
            waiver_value: float | None, college_id: str) -> dict:
        """
        Get the scholarship overview details.

        Params:
            - application_id (str): Unique identifier of an application. e.g., 123456789012345678901231
            - default_scholarship_id (str): Unique identifier of a scholarship. e.g., 123456789012345678901232
            - waiver_type (str | None): Either None or type of waiver, required in case of custom scholarship.
            - waiver_value (float | None): Either None or value of waiver, required in case of custom scholarship.
            - college_id (str): Unique identifier of a college. e.g., 123456789012345678901234

        Returns:
            - dict: A dictionary which contains information about change default scholarship.
        """
        await utility_obj.is_length_valid(application_id, "Application id")
        obj_application_id = ObjectId(application_id)
        if (
                application_information := await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"_id": obj_application_id}
                )
        ) is None:
            raise DataNotFoundError(message="Application", _id=application_id)
        await utility_obj.is_length_valid(default_scholarship_id, "Default scholarship id")
        obj_scholarship_id = ObjectId(default_scholarship_id)
        if (
                scholarship_information := await DatabaseConfiguration().scholarship_collection.find_one(
                    {"_id": obj_scholarship_id}
                )
        ) is None:
            raise DataNotFoundError(message="Default scholarship", _id=default_scholarship_id)
        program_fee = await self.get_program_registration_fee(application_information)
        application_ids = await ScholarshipActivity().get_eligible_applicants_info(
            programs_info={"course_id": [application_information.get("course_id")],
                           "course_specialization": [application_information.get("spec_name1")]},
            normal_filters=scholarship_information.get("filters", {}),
            advance_filters=scholarship_information.get("advance_filters", []),
            college_id=college_id
        )
        if obj_application_id not in application_ids:
            raise CustomError("Make sure default scholarship is associated with applicant.")
        scholarship_waiver_value = scholarship_information.get("waiver_value")
        if scholarship_information.get("waiver_type") == "Percentage":
            default_scholarship_amount = round(program_fee * (scholarship_waiver_value / 100), 2)
        else:
            default_scholarship_amount = round(scholarship_waiver_value, 2)
        default_scholarship_name = scholarship_information.get("name", "")
        custom_scholarship_fee, custom_scholarship_name = 0, ""
        if waiver_type and waiver_value:
            if waiver_type == "Percentage":
                custom_scholarship_fee = round(program_fee * (waiver_value / 100), 2)
                if waiver_value > 100:
                    raise CustomError("Custom scholarship percentage should be less than or equal to 100.")
            else:
                if waiver_value > program_fee:
                    raise CustomError(f"Custom Scholarship amount should be less than or equal to {program_fee}.")
                custom_scholarship_fee = round(waiver_value, 2)
            if (custom_scholarship_fee + default_scholarship_amount) > program_fee:
                return {"detail": "Default and custom scholarship amount exceeding program fee amount."}
            custom_scholarship_name = "Custom scholarship"
        return {"message": "Get the scholarship overview details.",
                "data": {
                    "program_fee": program_fee,
                    "default_scholarship_name": default_scholarship_name,
                    "default_scholarship_amount": default_scholarship_amount,
                    "custom_scholarship_name": custom_scholarship_name,
                    "custom_scholarship_amount": custom_scholarship_fee,
                    "fees_after_waiver": program_fee - default_scholarship_amount - custom_scholarship_fee
                }}
