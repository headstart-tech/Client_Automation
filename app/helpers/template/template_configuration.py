"""
This file contain class and functions related to template data
"""

from datetime import datetime

from bson import ObjectId
from fastapi.exceptions import HTTPException

from app.core.custom_error import CustomError, DataNotFoundError
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache
from app.helpers.user_curd.user_configuration import UserHelper
from pathlib import PurePath


class TemplateActivity:
    """
    Perform template related activities
    """

    def template_helper(self, data, otp_template=False):
        """
        Get details of template
        """
        if data.get("select_members"):
            for member in data.get("select_members", []):
                if member is None:
                    break
                member.update({"id": str(member.get("id"))})
        temp = {
            "template_id": str(data.get("_id")),
            "whatsapp_template_id": data.get("template_id"),
            "sender_email_id": data.get("sender_email_id"),
            "documents": data.get("documents", []),
            "reply_to_email": data.get("reply_to_email"),
            "template_name": data.get("template_name"),
            "template_json": data.get("template_json"),
            "content": data.get("content"),
            "last_modified_timeline": (
                [
                    {
                        "last_modified_at": utility_obj.get_local_time(
                            template_doc.get("last_modified_at")
                        ),
                        "user_id": str(template_doc.get("user_id")),
                        "user_name": template_doc.get("user_name"),
                    }
                    for template_doc in data.get("last_modified_timeline")
                ]
                if data.get("last_modified_timeline")
                else None
            ),
            "created_by": str(data.get("created_by")),
            "created_by_user_name": data.get("created_by_user_name"),
            "created_on": utility_obj.get_local_time(data.get("created_on")),
            "sent_count": {
                "total_count": data.get("total_count", 0),
                "automated_count": data.get("sent_count", {}).get("automated", 0),
                "manual_count": data.get("sent_count", {}).get("manual", 0),
            },
            "selected_members": data.get("select_members", []),
            "select_profile_role": data.get("select_profile_role", []),
            "attachment_type": data.get("attachmentType", ""),
            "attachment_url": data.get("attachmentURL", ""),
            "template_type_option": data.get("template_type_option", ""),
            "add_template_option_url": data.get("add_template_option_url", []),
            "attachment_document_link": data.get("attachment_document_link", [])
        }
        if otp_template is False:
            temp.update(
                {
                    "template_type": data.get("template_type"),
                    "added_tags": (
                        (
                            {
                                "tag_id": str(item.get("tag_id")),
                                "tag_name": item.get("tag_name"),
                            }
                            for item in data.get("added_tags", [])
                        )
                        if data.get("added_tags", [])
                        else None
                    ),
                    "is_published": data.get("is_published"),
                    "template_status": data.get("template_status"),
                    "dlt_content_id": data.get("dlt_content_id"),
                    "subject": (
                        data.get("subject") if data.get(
                            "subject") else None
                    ),
                    "email_type": (
                        data.get("email_type").title()
                        if data.get("email_type")
                        else "Default"
                    ),
                    "email_provider": (
                        data.get("email_provider").title()
                        if data.get("email_provider")
                        else "Default"
                    ),
                    "email_category": (
                        data.get("email_category", "")
                        if data.get("email_category")
                        else "Default"
                    ),
                    "sms_category": (
                        data.get("sms_category", "")
                        if data.get("sms_category")
                        else "Default"
                    ),
                    "sms_type": (
                        data.get("sms_type").title() if data.get(
                            "sms_type") else None
                    ),
                    "sender": data.get("sender"),
                    "active": data.get("active", False),
                    "media": data.get("media"),
                }
            )
        return temp

    async def otp_template_helper(self, data):
        """
        Get details of template
        """
        temp = self.template_helper(data, otp_template=True)
        temp.update({"display_name": data.get("display_name")})
        return temp

    async def valid_template(self, template_id, template_name):
        templates = await get_collection_from_cache(collection_name="templates")
        if template_id:
            await utility_obj.is_id_length_valid(_id=template_id,
                                                 name="Template id")
            if templates:
                template = utility_obj.search_for_document(templates, field="_id", search_name=str(template_id))
            else:
                template = await DatabaseConfiguration().otp_template_collection.find_one(
                    {"_id": ObjectId(template_id)}
                )
                collection = await DatabaseConfiguration().otp_template_collection.aggregate([]).to_list(None)
                await store_collection_in_cache(collection, collection_name="templates")
        elif template_name:
            if templates:
                template = utility_obj.search_for_document(templates, field="template_name", search_name=template_name.lower())
            else:
                template = await DatabaseConfiguration().otp_template_collection.find_one(
                    {"template_name": template_name.lower()}
                )
                collection = await DatabaseConfiguration().otp_template_collection.aggregate([]).to_list(None)
                await store_collection_in_cache(collection, collection_name="templates")
        else:
            return False
        return template

    async def get_template_details_by_id_or_name(self, template_id,
                                                 template_name):
        """
        Delete data segment by id or name
        """
        otp_template = await self.valid_template(template_id, template_name)
        return otp_template

    async def validate_template_type(self, template_type: str) -> None:
        """
        Check Template Type is Valid or not
        :param template_type: Type of template like SMS, Email and Whatsapp
        :raises HTTPException: If template_type is not into validated list
        """
        if template_type not in ["email", "sms", "whatsapp"]:
            raise HTTPException(
                status_code=422,
                detail="Template type should be any of the following: email, sms and whatsapp",
            )

    async def check_and_add_tag(self, template_details):
        """ """
        tag_list = []
        if template_details.get("tags"):
            tags = set(map(str.lower, template_details.get("tags")))
            for tag in tags:
                if (
                        tag_data := await DatabaseConfiguration().tag_list_collection.find_one(
                            {"tag_name": tag.lower()}
                        )
                ) is not None:
                    tag_id = tag_data.get("_id")
                else:
                    tag_data = (
                        await DatabaseConfiguration().tag_list_collection.insert_one(
                            {"tag_name": tag.lower()}
                        )
                    )
                    tag_id = tag_data.inserted_id
                tag_list.append({"tag_id": tag_id, "tag_name": tag.lower()})
            template_details.pop("tags")
            template_details["added_tags"] = tag_list if tag_list else None
        return template_details, tag_list

    async def get_last_timeline(self, user):
        """
        Get last modified timeline of user
        """
        last_modified_timeline = [
            {
                "last_modified_at": datetime.utcnow(),
                "user_id": ObjectId(str(user.get("_id"))),
                "user_name": utility_obj.name_can(user),
            }
        ]
        return last_modified_timeline

    async def common_code_of_add_or_update_template_data(
            self, current_user, template_schema
    ):
        """
        Common code of add or update template data
        """
        user = await UserHelper().check_user_has_permission(
            current_user, ["super_admin", "college_super_admin"],
            condition=False
        )
        template_details = {}
        if template_schema:
            template_details = {
                key: value
                for key, value in template_schema.dict().items()
                if value is not None
            }
        template_type = template_details.get("template_type", "").lower()
        if template_details.get("template_type") not in ["", None]:
            await self.validate_template_type(template_type=template_type)
            template_details["template_type"] = template_type

        if not template_details.get("sender_email_id") and template_type == "email":
            raise HTTPException(
                status_code=422, detail="Sender email id of email template not provided."
            )
        for key in [
            "template_type_option",
            "add_template_option_url",
            "attachmentURL",
            "attachmentType",
        ]:
            if (
                    template_details.get(key) not in ["", None]
                    and template_type != "whatsapp"
            ):
                template_details.pop(key)

        for key in ["dlt_content_id", "sms_type", "sender", "sms_category"]:
            if template_details.get(key) not in ["",
                                                 None] and template_type != "sms":
                template_details.pop(key)
        if template_type == "whatsapp":
            template_details["template_id"] = template_details.get(
                "template_id")
            attachment_type = template_details.get("attachmentType")
            ATTACHMENT_TYPES = {"image": (".png", ".jpg", ".jpeg"), "pdf": (".pdf",), "video": (".mp4",)}
            if attachment_type not in ["", None] and attachment_type not in ATTACHMENT_TYPES:
                raise HTTPException(
                    status_code=400, detail="Invalid attachment type. "
                                            f"Supported attachment types are: {', '.join(ATTACHMENT_TYPES.keys())}"
                )
            attachment_url = template_details.get("attachmentURL")
            if attachment_url not in ["", None] and attachment_type not in ["", None]:
                file_name = PurePath(attachment_url).name
                allowed_extensions = ATTACHMENT_TYPES[attachment_type]
                if not utility_obj.is_valid_extension(file_name, extensions=allowed_extensions):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid attachment URL for media type `{attachment_type}`. "
                               f"Supported attachment URL types are: {', '.join(allowed_extensions)}"
                    )
        for key in ["subject", "email_type", "email_provider",
                    "email_category", "sender_email_id", "reply_to_email", "attachment_document_link"]:
            if template_details.get(key) and template_type != "email":
                template_details.pop(key)

        for name in ["email", "sms"]:
            if template_details.get(f"{name}_category") == "default":
                template_details.pop(f"{name}_category")
        if template_details.get("template_name") not in ["", None]:
            template_details["template_name"] = template_details.pop(
                "template_name", ""
            ).lower()
        template_details, tag_list = await self.check_and_add_tag(
            template_details)
        return template_details, tag_list, user

    async def update_template_data(
            self, template_id: str, template_details: dict,
            last_modified_timeline: list
    ) -> dict:
        """
        Update template data
        """
        await utility_obj.is_id_length_valid(_id=template_id,
                                             name="Template id")
        tag_data = await DatabaseConfiguration().template_collection.find_one(
            {"_id": ObjectId(template_id)}
        )
        if not tag_data:
            raise HTTPException(
                status_code=404,
                detail="Template not found. Make sure provided template id should be correct.",
            )
        if template_details.get("select_members"):
            for member in template_details.get("select_members"):
                member.update({"id": ObjectId(member.get("id"))})

        template_details["last_modified_timeline"] = (
                tag_data.get("last_modified_timeline",
                             []) + last_modified_timeline
        )
        await DatabaseConfiguration().template_collection.update_one(
            {"_id": ObjectId(template_id)}, {"$set": template_details}
        )
        return {"message": "Template data updated."}

    async def update_template_id_in_tag_list_collection(
            self, tag_list, data, add_template_data
    ):
        """
        update template id in tag list collection
        """
        template_type = data.get("template_type")
        for tag in tag_list:
            tag_data = await DatabaseConfiguration().tag_list_collection.find_one(
                {"_id": tag.get("tag_id")}
            )
            if tag_data.get("associated_templates"):
                temp_template_type = tag_data.get("template_type")
                if template_type not in temp_template_type:
                    data_to_set = {
                        "associated_templates": tag_data.get(
                            "associated_templates")
                                                + [
                                                    add_template_data.inserted_id],
                        "template_type": temp_template_type + [template_type],
                    }
                else:
                    data_to_set = {
                        "associated_templates": tag_data.get(
                            "associated_templates")
                                                + [
                                                    add_template_data.inserted_id]
                    }
            else:
                data_to_set = {
                    "associated_templates": [add_template_data.inserted_id],
                    "template_type": [template_type],
                }
            await DatabaseConfiguration().tag_list_collection.update_one(
                {"_id": tag.get("tag_id")}, {"$set": data_to_set}
            )

    async def add_template_data(
            self,
            template_details: dict,
            user: dict,
            last_modified_timeline: list,
            tag_list: list,
    ) -> dict:
        """
        Add template data in the database
        """
        template_type = template_details.get("template_type", "").lower()
        if template_details.get("template_type") in ["", None]:
            raise HTTPException(status_code=422,
                                detail="Template type not provided.")
        elif template_details.get("template_name") in ["", None]:
            raise HTTPException(status_code=422,
                                detail="Template name not provided.")
        elif template_details.get("content") in ["", None]:
            raise HTTPException(
                status_code=422, detail="Template content not provided."
            )
        elif (
                template_details.get("dlt_content_id") in ["", None]
                and template_type == "sms"
        ):
            raise HTTPException(status_code=422,
                                detail="DLT content id not provided.")
        elif template_details.get("subject") in ["",
                                                 None] and template_type == "email":
            raise HTTPException(
                status_code=422, detail="Subject of email not provided."
            )
        elif template_type == "whatsapp" and template_details.get(
                "template_type_option"
        ) not in ["interactive_button", "media_attachments", "text_only"]:
            raise HTTPException(
                status_code=422, detail="Invalid template type option data"
            )
        elif (
            template_type == "whatsapp"
            and template_details.get("template_type_option") == "media_attachments"
            and template_details.get("attachmentType")
            not in [None, "", "video", "image", "pdf"]
        ):
            raise HTTPException(status_code=422,
                                detail="Invalid attachment type")
        elif (
            template_type == "whatsapp"
            and template_details.get("template_type_option") == "interactive_button"
        ):
            for interactive_button_data in template_details.get(
                    "add_template_option_url"
            ):
                if interactive_button_data.get("type") not in [
                    None,
                    "",
                    "cta",
                    "quick_reply",
                ] or interactive_button_data.get("nature") not in [
                    None,
                    "",
                    "static",
                    "dynamic",
                ]:
                    raise HTTPException(
                        status_code=422, detail="Invalid type or nature"
                    )

        if template_details.get("select_members"):
            for member in template_details.get("select_members"):
                member.update({"id": ObjectId(member.get("id"))})

        data = {
            "template_name": template_details.pop("template_name"),
            "template_type": template_details.pop("template_type"),
            "template_json": template_details.get("template_json"),
            "content": template_details.pop("content"),
            "template_id": template_details.get("template_id"),
            "added_tags": template_details.get("added_tags"),
            "last_modified_timeline": last_modified_timeline,
            "created_by": ObjectId(str(user.get("_id"))),
            "created_by_user_name": utility_obj.name_can(user),
            "created_on": datetime.utcnow(),
            "is_published": template_details.pop("is_published"),
            "template_status": "enabled",
            "select_profile_role": template_details.get("select_profile_role"),
            "select_members": template_details.get("select_members"),
        }
        if data.get("template_type", "").lower() == "sms":
            data.update({
                "dlt_content_id": template_details.get("dlt_content_id"),
                "sms_type": template_details.get("sms_type"),
                "sender": template_details.get("sender")
            })
        if data.get("template_type", "").lower() == "email":
            data.update({
                "subject": template_details.get("subject"),
                "email_type": template_details.get("email_type"),
                "email_provider": template_details.get("email_provider"),
                "sender_email_id": template_details.get("sender_email_id"),
                "reply_to_email": template_details.get("reply_to_email"),
                "attachment_document_link": template_details.get("attachment_document_link")
            })
        if data.get("template_type", "").lower() == "whatsapp":
            data.update({
                "template_type_option": template_details.get("template_type_option"),
                "add_template_option_url": template_details.get("add_template_option_url"),
                "attachmentType": template_details.get("attachmentType"),
                "attachmentURL": template_details.get("attachmentURL")
            })
        for name in ["email", "sms"]:
            if template_details.get(f"{name}_category") not in ["", None]:
                data[f"{name}_category"] = template_details.get(
                    f"{name}_category")
        add_template_data = (
            await DatabaseConfiguration().template_collection.insert_one(data)
        )
        await self.update_template_id_in_tag_list_collection(
            tag_list, data, add_template_data
        )
        data.update({"_id": add_template_data.inserted_id})
        return {
            "data": TemplateActivity().template_helper(data),
            "message": "Template created.",
        }

    async def add_or_update_template_data(
            self, current_user: dict, template_schema: dict, template_id: str
    ):
        """
        Add or update template data based on request
        """
        template_details, tag_list, user = (
            await self.common_code_of_add_or_update_template_data(
                current_user, template_schema
            )
        )
        last_modified_timeline = await self.get_last_timeline(user)
        if template_id:
            return await self.update_template_data(
                template_id, template_details, last_modified_timeline
            )
        else:
            return await self.add_template_data(
                template_details, user, last_modified_timeline, tag_list
            )

    async def validate_input_params(self, activate_template_data: any) -> any:
        """
        Validate input paramters and return template data
        """
        template_data = {}
        if activate_template_data:
            template_data = {
                key: value
                for key, value in activate_template_data.dict().items()
                if value is not None
            }
        template_id = template_data.get("template_id", "")
        await utility_obj.is_id_length_valid(_id=template_id,
                                             name="Template id")
        template = await DatabaseConfiguration().template_collection.find_one(
            {"_id": ObjectId(template_id)}
        )
        if not template:
            raise HTTPException(status_code=200, detail="Template not found.")
        template_type = template.get("template_type")
        template_category = template.get(f"{template_type}_category")
        if template_category is None:
            raise HTTPException(
                status_code=200,
                detail=f"Enter a valid {template_type} category."
            )
        return template, template_category

    async def activate_template_by_category(self, template, category):
        active_template = await DatabaseConfiguration().template_collection.find_one(
            {f"{template.get('template_type')}_category": category,
             "active": True}
        )
        if active_template is not None:
            await DatabaseConfiguration().template_collection.update_one(
                {"_id": active_template.get("_id")},
                {"$unset": {"active": True}}
            )
        await DatabaseConfiguration().template_collection.update_one(
            {"_id": ObjectId(template.get("_id"))}, {"$set": {"active": True}}
        )

    async def activate_template(self, activate_template_data: any) -> dict:
        """
        Activate template by using template id
        """
        # Validate input parameters
        template, category = await self.validate_input_params(
            activate_template_data)

        # Check if the template is already activated
        if template.get("active", False):
            return {"detail": "Template is already activated."}

        # Activate the template
        await self.activate_template_by_category(template, category)

        return {"message": "Template activated."}

    async def get_template_merge_fields(
            self, college_id: ObjectId, page_num: str | None,
            page_size: str | None
    ) -> dict:
        """
        Get template merge fields.

        Params:
            - college_id (ObjectId): A unique id/identifier of a college.
            - page_num (int | None): Either None or page number where you want
                to show data. e.g., 1
            - page_size (int | none): Either None or page size, useful for show
                data on page_num. e.g., 25.
                If we give page_num=1 and page_size=25 i.e., we want 25
                    records on page 1.


        Returns:
            dict: A dictionary which contains template merge tags.
        """
        merge_fields = (
            await DatabaseConfiguration().template_merge_fields_collection.find_one(
                {"college_id": college_id}
            )
        )
        existing_fields = merge_fields.get("merge_fields", [])
        if existing_fields is None:
            existing_fields = []
        existing_fields = [
            {"name": field.get("field_name"),
             "value": f"{{{field.get('field_name')}}}"}
            for field in existing_fields
            if isinstance(field, dict)
        ]
        total = len(existing_fields)
        pagination = {}
        if page_num and page_size:
            response = await utility_obj.pagination_in_api(
                page_num,
                page_size,
                existing_fields,
                len(existing_fields),
                "/templates/get_template_merge_fields/",
            )
            existing_fields = response["data"]
            pagination = response["pagination"]
        return {
            "merge_fields": existing_fields,
            "total": total,
            "message": "Get the template merge fields.",
            "count": page_size if page_size else total,
            "pagination": pagination,
        }

    async def add_template_merge_field(
            self, college_id: ObjectId, add_merge_field: dict
    ) -> dict:
        """
        Add template merge field.

        Params:
            - college_id (ObjectId): A unique id/identifier of a college.
                e.g., 123456789012345678901234
            - add_merge_field (dict): A dictionary which contains merge field
                data like field_name and value.
                e.g., {"field_name": "name", "value: "test"}

        Returns:
            dict: A dictionary which contains template merge tags.
        """
        merge_fields = (
            await DatabaseConfiguration().template_merge_fields_collection.find_one(
                {"college_id": college_id}
            )
        )
        if not merge_fields:
            await DatabaseConfiguration().template_merge_fields_collection.insert_one(
                {"college_id": college_id, "merge_fields": [add_merge_field]}
            )
        else:
            existing_fields = merge_fields.get("merge_fields", [])
            if existing_fields is None:
                existing_fields = []
            field_name = add_merge_field.get("field_name", "").title()
            key_name = field_name.replace(" ", "_").lower()
            existing_field_keys, existing_field_names = [], []
            for item in existing_fields:
                existing_field_keys.append(item.get("key_name"))
                existing_field_names.append(item.get("field_name"))
            if field_name in existing_field_names:
                raise CustomError(
                    message="Field name already exist. "
                            "Please use another field name."
                )
            existing_fields.insert(
                0,
                {
                    "field_name": field_name,
                    "value": add_merge_field.get("value", ""),
                    "key_name": key_name,
                },
            )
            await DatabaseConfiguration().template_merge_fields_collection.update_one(
                {"college_id": college_id},
                {"$set": {"merge_fields": existing_fields}}
            )
        return {"message": "Template merge field added successfully."}

    async def get_template(self, template_id: str | None,
                           template_type: str | None,
                           message_id: str | None,
                           student_id: str | None):
        """
        Get the template details for a given template ID.
        Parameters:
            template_id (str): The ID of the template to retrieve details for.
            template_type (str): The type of template to retrieve details
            message_id (str): The ID of the message to get the status
            student_id (str): ID of the student
        Returns:
            dict: A dictionary containing the details of the template.
                The dictionary may contain keys such as:
                    - 'name' (str): The name of the template.
                    - 'description' (str): A description of the template.
                    - Additional details specific to the template.
        """
        await utility_obj.is_length_valid(template_id, "Template ID")
        if (template := await DatabaseConfiguration().template_collection.find_one(
                    {"_id": ObjectId(template_id),
                     "template_type": template_type}
                )
        ) is None:
            raise DataNotFoundError(_id=template_id, message="Template")
        data = self.template_helper(template)
        if message_id and student_id:
            pipeline = [
                {
                    '$match': {
                        'student_id': ObjectId(student_id) if ObjectId.is_valid(student_id) else str(student_id)
                    }
                }, {
                    '$unwind': '$email_summary.transaction_id'
                }, {
                    '$match': {
                        'email_summary.transaction_id.MessageId': message_id
                    }
                }, {
                    '$addFields': {
                        'status': {
                            '$switch': {
                                'branches': [
                                    {
                                        'case': {
                                            '$eq': [
                                                '$email_summary.transaction_id.email_click', True
                                            ]
                                        },
                                        'then': 'Clicked'
                                    }, {
                                        'case': {
                                            '$eq': [
                                                '$email_summary.transaction_id.email_open', True
                                            ]
                                        },
                                        'then': 'Opened'
                                    }, {
                                        'case': {
                                            '$eq': [
                                                '$email_summary.transaction_id.email_delivered', True
                                            ]
                                        },
                                        'then': 'Delivered'
                                    }, {
                                        'case': {
                                            '$eq': [
                                                '$email_summary.transaction_id.email_bounce', True
                                            ]
                                        },
                                        'then': 'Bounced'
                                    }, {
                                        'case': {
                                            '$eq': [
                                                '$email_summary.transaction_id.email_sent', True
                                            ]
                                        },
                                        'then': 'Sent'
                                    }
                                ],
                                'default': 'Sent'
                            }
                        }
                    }
                }, {
                    '$project': {
                        '_id': 0,
                        'status': 1
                    }
                }
            ]
            result =  await DatabaseConfiguration().communication_log_collection.aggregate(pipeline).to_list(None)
            if result:
                data.update(result[0])
            else:
                data.update({"status": "Sent"})
        else:
            data.update({"status": "Sent"})
        return data


    async def add_or_get_category(self, user: dict,
                                  category_name: str | None) -> list:
        """Add or get categories helper function

        Args:
            user (dict): Current user details
            category_name (str|None): Category name if any have to add in the database.

        Returns:
            list: List of template category.
        """
        if (
                category_name
                and not await DatabaseConfiguration().template_category.find_one(
            {"category_name": category_name}
        )
        ):
            await DatabaseConfiguration().template_category.insert_one(
                {
                    "category_name": category_name,
                    "created_at": datetime.utcnow(),
                    "created_by": ObjectId(user.get("_id")),
                }
            )

        return (
            await DatabaseConfiguration()
            .template_category.aggregate(
                [
                    {
                        "$project": {
                            "_id": 0,
                            "id": {"$toString": "$_id"},
                            "category_name": 1,
                        }
                    }
                ]
            )
            .to_list(None)
        )

    async def get_user_list_for_template_manager(self, role_list: list[str],
                                                 college_id: str) -> list:
        """Get list of users data which belongs to the provided role list.

        Params:
            role_list (list[str]): List of role name.
            college_id (str): The unique identifier of college which useful for
             get particular college users only.

        Returns:
            list: List of username (s) data and its role.
        """

        return await (DatabaseConfiguration().user_collection.aggregate([
                {
                    "$match": {
                        "role.role_name": {"$in": role_list},
                        "is_activated": True,
                        "associated_colleges": {"$in": [ObjectId(college_id)]}
                    }
                },
                {
                    "$project": {
                        "label": {
                            "$trim": {
                                "input": {
                                    "$concat": [
                                        "$first_name",
                                        " ",
                                        {
                                            "$cond": {
                                                "if": {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                "$middle_name",
                                                                None,
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$middle_name",
                                                                "",
                                                            ]
                                                        },
                                                    ]
                                                },
                                                "then": "",
                                                "else": {
                                                    "$concat": [
                                                        "$middle_name",
                                                        " "]
                                                },
                                            }
                                        },
                                        "$last_name",
                                    ]
                                }
                            }
                        },
                        "role": {
                            "$map": {
                                "input": {
                                    "$split": ["$role.role_name", "_"]},
                                "as": "word",
                                "in": {
                                    "$concat": [
                                        {
                                            "$toUpper": {
                                                "$substrCP": ["$$word", 0,
                                                                1]
                                            }
                                        },
                                        {
                                            "$substrCP": [
                                                "$$word",
                                                1,
                                                {"$strLenCP": "$$word"},
                                            ]
                                        },
                                    ]
                                },
                            }
                        },
                    }
                },
                {
                    "$project": {
                        "id": {"$toString": "$_id"},
                        "label": 1,
                        "role": {
                            "$reduce": {
                                "input": "$role",
                                "initialValue": "",
                                "in": {
                                    "$concat": [
                                        "$$value",
                                        {
                                            "$cond": {
                                                "if": {"$eq": ["$$value",
                                                                ""]},
                                                "then": "",
                                                "else": " ",
                                            }
                                        },
                                        "$$this",
                                    ]
                                },
                            }
                        },
                    }
                }, {
                '$project': {
                    '_id': 0, 
                    'label': '$label', 
                    'value': {
                        'role': '$role', 
                        'name': '$label', 
                        'id': '$id'
                    }, 
                    'role': '$role'
                }
            }
        ]).to_list(None))



    async def get_user_roles_helper(self) -> list:
        """Get all users role details fetch function helper

        Returns:
            list: List of roles name of all users
        """
        roles = (
            await DatabaseConfiguration()
            .role_collection.aggregate(
                [
                    {
                        "$project": {
                            "_id": 1,
                            "value": "$role_name",
                            "label": {
                                "$map": {
                                    "input": {"$split": ["$role_name", "_"]},
                                    "as": "word",
                                    "in": {
                                        "$concat": [
                                            {
                                                "$toUpper": {
                                                    "$substrCP": ["$$word", 0,
                                                                  1]
                                                }
                                            },
                                            {
                                                "$substrCP": [
                                                    "$$word",
                                                    1,
                                                    {"$strLenCP": "$$word"},
                                                ]
                                            },
                                        ]
                                    },
                                }
                            },
                        }
                    },
                    {
                        "$project": {
                            "_id": {"$toString": "$_id"},
                            "value": 1,
                            "label": {
                                "$reduce": {
                                    "input": "$label",
                                    "initialValue": "",
                                    "in": {
                                        "$concat": [
                                            "$$value",
                                            {
                                                "$cond": {
                                                    "if": {"$eq": ["$$value",
                                                                   ""]},
                                                    "then": "",
                                                    "else": " ",
                                                }
                                            },
                                            "$$this",
                                        ]
                                    },
                                }
                            },
                        }
                    },
                ]
            )
            .to_list(None)
        )

        return roles
