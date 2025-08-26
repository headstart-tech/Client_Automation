"""
This file contain class and functions for get templates data by performing aggregation on the collection templates and tag_list
"""

from bson import ObjectId

from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.helpers.communication_summary.dashboard_header_helper import (
    CommunicationHeader,
)
from app.helpers.template.template_configuration import TemplateActivity

return_attributes = {
    "$project": {
        "_id": 1,
        "template_name": 1,
        "template_type": 1,
        "template_id": 1,
        "content": 1,
        "template_json": 1,
        "added_tags": 1,
        "created_by": 1,
        "created_by_user_name": 1,
        "created_on": 1,
        "sender": 1,
        "sms_type": 1,
        "is_published": 1,
        "template_status": 1,
        "dlt_content_id": 1,
        "subject": 1,
        "email_category": 1,
        "email_type": 1,
        "email_provider": 1,
        "sms_category": 1,
        "active": 1,
        "last_modified_timeline": 1,
        "select_profile_role": 1,
        "select_members": 1,
        "attachmentType": 1,
        "attachmentURL": 1,
        "template_type_option": 1,
        "add_template_option_url": 1,
        "documents": 1,
        "sender_email_id": 1,
        "reply_to_email": 1,
        "attachment_document_link": 1
    }
}
sort_by_created_on = {"$sort": {"created_on": -1}}


class Template:
    """
    Contain functions related to template activities
    """

    async def get_all_otp_templates_data(self, page_num, page_size):
        """
        Return OTP templates data and total count of templates
        """
        skip, limit = await utility_obj.return_skip_and_limit(
            page_num=page_num, page_size=page_size
        )
        data, total_data = [], []
        pipeline = [
            {
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            }
        ]
        all_templates_data = DatabaseConfiguration().otp_template_collection.aggregate(
            pipeline
        )
        async for all_templates in all_templates_data:
            try:
                total_data = all_templates.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
            data = [
                await TemplateActivity().otp_template_helper(template_data)
                for template_data in all_templates.get("paginated_results", [])
            ]
        return data, total_data

    async def data_skip_and_limit(self, page_num, page_size):
        """
        Get data skip and limit values
        :param page_num: description="Page number where you want to show data", example=1
        :param page_size: description="Page size means how many data you want to show on page_num", example=25
        :return: Skip and limit value
        """
        if page_num and page_size:
            skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
        else:
            skip = 0
            limit = await DatabaseConfiguration().template_collection.count_documents(
                {}
            )
        return skip, limit

    async def all_templates_by_tags(
            self,
            tag_names,
            template_type,
            email_category,
            sms_category,
            is_published,
            own_templates,
            user,
            skip,
            limit,
    ):
        pipeline = [
            {
                "$match": {
                    "tag_name": {"$in": tag_names},
                    "template_type": {"$in": [template_type]}
                }
            },
            {
                "$unwind": {
                    "path": "$associated_templates",
                    "includeArrayIndex": "arrayIndex",
                },
            },
            {
                "$project": {"_id": 0, "associated_templates": 1},
            },
            {
                "$lookup": {
                    "from": "templates",
                    "let": {"id": "$associated_templates"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$_id", "$$id"]},
                                "template_type": template_type,
                                "is_published": is_published,
                                "template_status": "enabled",
                            }
                        },
                        return_attributes,
                    ],
                    "as": "template_details",
                }
            },
            {
                "$unwind": {
                    "path": "$template_details",
                    "includeArrayIndex": "arrayIndex",
                }
            },
            sort_by_created_on,
        ]
        """
        Get pipeline which useful for retrieve templates by tag names
        """
        for name in [email_category, sms_category]:
            if name:
                if name in ["default", None]:
                    name = None
                pipeline.append({"$match": {f"template_details.{name}": name}})
        if own_templates:
            pipeline.append(
                {
                    "$match": {
                        "template_details.created_by": ObjectId(
                            str(user.get("_id")))
                    }
                }
            )
        pipeline.append(
            {
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            }
        )
        return pipeline

    async def extend_templates_pipeline_based_on_condition(
            self,
            skip,
            limit,
            pipeline,
            whatsapp_templates,
            draft_whatsapp_templates,
            draft_email_templates,
            email_templates,
            email_category,
            sms_templates,
            sms_category,
            draft_sms_template,
            own_templates,
            user,
    ):
        """
        Extend pipeline of aggregation of get all templates based on conditions
        """
        pipeline.extend([return_attributes, sort_by_created_on])
        base_draft_template_filter: dict = {"is_published": False}
        template_type = None
        if draft_whatsapp_templates or whatsapp_templates:
            template_type = "whatsapp"
            base_whatsapp_filter = {"template_type": template_type}
            if draft_whatsapp_templates:
                base_whatsapp_filter.update(base_draft_template_filter)
            pipeline.append({"$match": base_whatsapp_filter})
        if (
                draft_email_templates
                or email_templates
                or (email_category and email_templates)
        ):
            template_type = "email"
            base_email_filter = {"template_type": template_type}
            if draft_email_templates:
                base_email_filter.update(base_draft_template_filter)
            if email_category:
                email_category = email_category.lower()
                if email_category == "default":
                    email_category = None
                base_email_filter.update({"email_category": email_category})
            pipeline.append({"$match": base_email_filter})
        if sms_templates or draft_sms_template or (sms_category and sms_templates):
            template_type = "sms"
            base_sms_filter = {"template_type": template_type}
            if draft_sms_template:
                base_sms_filter.update(base_draft_template_filter)
            if sms_category:
                sms_category = sms_category.lower()
                if sms_category == "default":
                    sms_category = None
                base_sms_filter.update({"sms_category": sms_category})
            pipeline.append({"$match": base_sms_filter})
        user_id = ObjectId(str(user.get("_id")))
        if user.get("role", {}).get("role_name") not in ["super_admin", "college_super_admin", "college_admin"]:
            pipeline.append(
                {"$match": {"$or": [{"created_by": user_id}, {"$and": [
                    {"select_members": {"$exists": True, "$nin": [[], None]}},
                    {"select_members": {"$exists": True, "$all": [{"$elemMatch": {
                     "id": {"$in": [user_id]}}}], }}
                ]}, {"$and": [
                    {"select_members": {"$exists": True, "$in": [[], None]}}
                ]}]}})
        if not own_templates:
            pipeline.append({"$match": {"is_published": True}})
        pipeline.append(
            {
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            }
        )
        return pipeline, template_type

    async def store_templates_data_in_list(
            self, template_data, data, templates_by_tags=False
    ):
        """
        Store templates data in a list
        :param template_data: description="Template data"
        :param data: description="for store data"
        :param templates_by_tags: description="For get templates data by tags "
        :return: Templates Data list
        """
        if templates_by_tags:
            template_data = template_data.get("template_details", {})
        data.append(TemplateActivity().template_helper(template_data))

    async def perform_aggregation_based_on_tag_names(
            self,
            tag_names,
            email_templates,
            sms_templates,
            whatsapp_templates,
            draft_email_templates,
            draft_sms_template,
            draft_whatsapp_templates,
            email_category,
            sms_category,
            is_published,
            own_templates,
            user,
            skip,
            limit,
    ):
        """
        Get templates data based on tag names
        """
        tag_names = list(set([tag_name.lower() for tag_name in tag_names]))
        template_dicts = {
            "email": email_templates,
            "sms": sms_templates,
            "whatsapp": whatsapp_templates,
        }
        template_type = next(
            (key for key, value in template_dicts.items() if value), None
        )
        if draft_email_templates or draft_sms_template or draft_whatsapp_templates:
            is_published = False

        pipeline = await self.all_templates_by_tags(
            tag_names=tag_names,
            template_type=template_type,
            email_category=email_category,
            sms_category=sms_category,
            is_published=is_published,
            own_templates=own_templates,
            user=user,
            skip=skip,
            limit=limit,
        )
        all_templates_data = DatabaseConfiguration().tag_list_collection.aggregate(
            pipeline
        )
        return all_templates_data, template_type

    async def get_all_templates_data(
            self,
            page_num,
            page_size,
            draft_whatsapp_templates=False,
            whatsapp_templates=False,
            draft_email_templates=False,
            email_templates=False,
            email_category=None,
            sms_templates=False,
            sms_category=None,
            draft_sms_template=False,
            own_templates=False,
            user=None,
            tag_names=None,
    ):
        """
        Get templates data and total count of templates
        """
        skip, limit = await self.data_skip_and_limit(
            page_num=page_num, page_size=page_size
        )
        pipeline, data, total_data, is_published, all_templates_data = (
            [],
            [],
            0,
            True,
            None,
        )
        if tag_names:
            all_templates_data, template_type = await self.perform_aggregation_based_on_tag_names(
                tag_names,
                email_templates,
                sms_templates,
                whatsapp_templates,
                draft_email_templates,
                draft_sms_template,
                draft_whatsapp_templates,
                email_category,
                sms_category,
                is_published,
                own_templates,
                user,
                skip,
                limit,
            )
        else:
            pipeline, template_type = await self.extend_templates_pipeline_based_on_condition(
                skip=skip,
                limit=limit,
                pipeline=pipeline,
                draft_whatsapp_templates=draft_whatsapp_templates,
                whatsapp_templates=whatsapp_templates,
                draft_email_templates=draft_email_templates,
                email_templates=email_templates,
                email_category=email_category,
                sms_templates=sms_templates,
                sms_category=sms_category,
                draft_sms_template=draft_sms_template,
                own_templates=own_templates,
                user=user,
            )

            all_templates_data = DatabaseConfiguration().template_collection.aggregate(
                pipeline
            )
        async for all_templates in all_templates_data:
            try:
                total_data = all_templates.get("totalCount", [])[0].get("count", 0)
            except IndexError:
                total_data = 0
            for template_data in all_templates.get("paginated_results"):
                if template_type:
                    communication = await CommunicationHeader().count_helper(
                        {}, template_type, template_type,
                        template_data.get("_id")
                    )
                    template_data.update(
                        {
                            "sent_count": communication.get("email_type", {}),
                            "total_count": communication.get("total_email", 0),
                        }
                    )
                status = True if tag_names else False
                await self.store_templates_data_in_list(
                    template_data=template_data, data=data, templates_by_tags=status
                )
        return data, total_data

    async def get_all_tag_names(self, template_type):
        """
        Get all tag names based on template type
        """
        result = DatabaseConfiguration().tag_list_collection.aggregate(
            [
                {
                    "$match": {
                        "template_type": {
                            "$in": [template_type, "template_type"]}
                    }
                },
                {"$project": {"_id": 0, "tag_name": 1}},
            ]
        )
        return [data.get("tag_name") async for data in result]
