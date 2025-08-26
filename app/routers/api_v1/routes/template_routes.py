"""
This file contains functions related to template
"""

from datetime import datetime
from io import BytesIO
from pathlib import PurePath

from PIL import Image
from bson import ObjectId
from fastapi import APIRouter, Body, Depends, Query, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.param_functions import File

from app.core.custom_error import CustomError, DataNotFoundError, \
    ObjectIdInValid
from app.core.log_config import get_logger
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, settings, requires_feature_permission
from app.database.aggregation.get_all_templates import Template
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id
from app.dependencies.oauth import (
    CurrentUser,
    cache_dependency,
    insert_data_in_cache,
    cache_invalidation, get_collection_from_cache, store_collection_in_cache,
    is_testing_env,
    Is_testing,
)
from app.helpers.template.media_gallery_helper import TemplateGallery
from app.helpers.template.template_configuration import TemplateActivity
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.student_user_schema import User, DateRange
from app.models.template_schema import (
    TemplateSchema,
    OtpTemplateSchema,
    ActivateTemplate,
    SMSCategory,
    AddMergeField,
)
from app.s3_events.s3_events_configuration import upload_multiple_files

template_router = APIRouter()
logger = get_logger(name=__name__)


@template_router.put("/add_or_update/", summary="Add or update templates")
@requires_feature_permission("write")
async def add_or_update_template(
        current_user: CurrentUser,
        template_schema: TemplateSchema = Body(None),
        template_id: str = Query(
            None,
            description="Enter template id if you want to update template data"
        ),
        college: dict = Depends(get_college_id),
):
    """
    Add or Update template\n
    * :*param* **template_id** description="Enter template id if you want to update template data", example="62f13a09375bf909a28ea9d8":\n
    * :*param* **template_name** description="Enter name of the template", example="string":\n
    * :*param* **content** description="Content of template, it can be of following type: HTML, string etc", example="string":\n
    * :*param* **template_json** description="Enter template json", example={'message': 'string'}:\n
    * :*param* **tags** description="Enter tags for template", example=['string']:\n
    * :*return* **Email template data with message**:
    """
    data = await TemplateActivity().add_or_update_template_data(
        current_user, template_schema, template_id
    )
    await cache_invalidation("templates/add_or_update")
    return data


@template_router.post("/particular_role_user_list")
@requires_feature_permission("read")
async def particular_role_user_list(
        role_list: list[str],
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
) -> dict:
    """User list according to particular role list for template creation module

    Params:
        role_list (list[str]): List of role which we have to fetch users.
        current_user (User, optional): Current requested users. Defaults to Depends(get_current_user).
        college_id (dict, optional): College unique id. Defaults to Depends(get_college_id).

    Raises:
        HTTPException: When invalid input send by the user
        CustomError: It raise in case of any unused data send by the user.
        Exception: In case of unexpected data send by the user
        ObjectIdInValid: Invalid unique id

    Returns:
        dict: Data set of user details
    """
    try:
        if (
                user := await DatabaseConfiguration().user_collection.find_one(
                    {"user_name": current_user.get("user_name")}
                )
        ) is None or user.get("role", {}).get("role_name", "") not in [
            "college_admin",
            "college_super_admin",
            "super_admin",
        ]:
            raise HTTPException(status_code=401, detail="permission denied")

        for role in role_list:
            if not await DatabaseConfiguration().role_collection.find_one(
                    {"role_name": role}
            ):
                raise CustomError(f"Invalid role name - {role}")

        return {
            "data": await TemplateActivity().get_user_list_for_template_manager(
                role_list, college.get("id")
            ),
            "message": "User list fetched successfully.",
        }

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the users data. Error: {error}.",
        )


@template_router.post("/", summary="Get all templates")
@requires_feature_permission("read")
async def templates(
        current_user: CurrentUser,
        draft_whatsapp_templates: bool = Query(
            False,
            description="If you want to get all draft whatsapp templates then send value True",
        ),
        whatsapp_templates: bool = Query(
            False,
            description="If you want to get all whatsapp templates then send value True",
        ),
        draft_email_templates: bool = Query(
            False,
            description="If you want to get all draft email templates then send value True",
        ),
        email_templates: bool = Query(
            False,
            description="If you want to get all email templates then send value True",
        ),
        email_category: str = Query(
            None,
            description="If you want to get all email templates based on category then send value of category",
        ),
        sms_category: SMSCategory = Query(
            None,
            description="If you want to get all sms templates based on category then send value of category",
        ),
        sms_templates: bool = Query(
            False,
            description="If you want to get all email templates then send value True",
        ),
        draft_sms_template: bool = Query(
            False,
            description="If you want to get all draft sms templates then send value True",
        ),
        own_templates: bool = Query(False,
                                    description="Get all templates of current user"),
        tag_names: list[str] = None,
        page_num: int = Query(
            gt=0,
            description="Enter page number where you want to show email templates data",
            example=1,
        ),
        page_size: int = Query(
            gt=0,
            description="Enter page size means how many data you want to show on page_num",
            example=25,
        ),
        cache_data=Depends(cache_dependency),
        college: dict = Depends(get_college_id),
):
    """
    Get All Templates\n
    * :*param* **draft_email_templates** description="If you want to get all draft email templates then send value True":\n
    * :*param* **email_templates** description="If you want to get all email templates then send value True":\n
    * :*param* **sms_templates** description="If you want to get all sms templates then send value True":\n
    * :*param* **own_templates** description="If you want to get all templates of current user then send value True":\n
    * :*param* **tag_names** description="Get all templates by tag_names", example=["string", "string1"]:\n
    * :*param* **page_num** description="Enter page number where you want to show email templates data", example=1:\n
    * :*param* **page_size** description="Enter page size means how many data you want to show on page_num", example=25:\n
    * :*return* **Email templates with message**:
    """
    user = await UserHelper().check_user_has_permission(current_user)
    cache_key, data = cache_data
    if data:
        return data
    if not is_testing_env():
        Reset_the_settings().check_college_mapped(college.get("id"))
    all_templates_data, total_templates_count = await Template().get_all_templates_data(
        page_num=page_num,
        page_size=page_size,
        whatsapp_templates=whatsapp_templates,
        email_templates=email_templates,
        email_category=email_category,
        sms_templates=sms_templates,
        sms_category=sms_category,
        draft_sms_template=draft_sms_template,
        draft_email_templates=draft_email_templates,
        draft_whatsapp_templates=draft_whatsapp_templates,
        user=user,
        own_templates=own_templates,
        tag_names=tag_names,
    )
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total_templates_count, route_name="/templates/"
    )
    data = {
        "data": all_templates_data,
        "total": total_templates_count,
        "count": page_size,
        "pagination": response["pagination"],
        "message": "Get all templates.",
    }
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@template_router.put("/update_status/",
                     summary="Enable or disable status of template")
@requires_feature_permission("edit")
async def update_status(
        current_user: CurrentUser,
        template_id: str = Query(
            ...,
            description="Enter template id if you want to update template data"
        ),
        template_status: str = Query(
            ...,
            description="For enable template, send value enabled. For disable template, send value disabled",
        ),
        college: dict = Depends(get_college_id),
):
    """
    * :*param* **template_id** description="Enter template id if you want to update template data", example="62f13a09375bf909a28ea9d8":\n
    * :*param* **template_status** description="For enable template, send value enabled. For disable template, send value disabled":\n
    * :*return* **Message - Template status updated.**:
    """
    status = ["enabled", "disabled"]
    await UserHelper().check_user_has_permission(current_user)
    await utility_obj.is_id_length_valid(_id=template_id, name="Template id")
    template = await DatabaseConfiguration().template_collection.find_one(
        {"_id": ObjectId(template_id)}
    )
    if not template:
        raise HTTPException(
            status_code=404,
            detail="Template not found. Make sure provided template id should be correct.",
        )
    if template_status.lower() not in status:
        raise HTTPException(
            status_code=404,
            detail="Template status should be any of the following: enabled and disabled.",
        )
    if template.get("template_status") == template_status.lower():
        return {
            "message": "No update needed, existing and new status are same"}
    await DatabaseConfiguration().template_collection.update_one(
        {"_id": ObjectId(str(template.get("_id")))},
        {"$set": {"template_status": template_status.lower()}},
    )
    await cache_invalidation("templates/update_status/")
    return {"message": "Template status updated."}


@template_router.get("/roles", summary="Get all roles of users")
@requires_feature_permission("read")
async def get_all_user_roles(
        current_user: CurrentUser,
) -> dict:
    """API for getting all users role details list for template creation

    Params:
        current_user (User, optional): Current requested user details. Defaults to Depends(get_current_user).
        college_id (dict, optional): College unique id. Defaults to Depends(get_college_id).

    Raises:
        HTTPException: When invalid input send by the user
        CustomError: It raise in case of any unused data send by the user.
        Exception: In case of unexpected data send by the user
        ObjectIdInValid: Invalid unique id

    Returns:
        dict: Response of list of all roles of users.
    """
    try:
        if (
                user := await DatabaseConfiguration().user_collection.find_one(
                    {"user_name": current_user.get("user_name")}
                )
        ) is None or user.get("role", {}).get("role_name", "") not in [
            "college_admin",
            "college_super_admin",
            "super_admin",
        ]:
            raise HTTPException(status_code=401, detail="permission denied")

        return {
            "data": await TemplateActivity().get_user_roles_helper(),
            "message": "User roles list fetched successfully.",
        }

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when get the users role data. Error: {error}.",
        )


@template_router.get("/tags/", summary="Get all tag names based of type")
@requires_feature_permission("read")
async def all_tag_names(
        current_user: CurrentUser,
        template_type: str = Query(
            ...,
            description="Enter template type. Template type should be any of the following: email, sms and whatsapp",
        ),
        cache_data=Depends(cache_dependency),
        college: dict = Depends(get_college_id),
):
    """
    Get All Tag Names based on Template Type
    * :param template_type:
    * :return Message - Get all tag names:
    """
    await UserHelper().check_user_has_permission(current_user)
    cache_key, data = cache_data
    if data:
        return data
    await TemplateActivity().validate_template_type(
        template_type=template_type)
    tag_names = await Template().get_all_tag_names(
        template_type=template_type.lower())
    data = {"data": tag_names, "message": "Get all tag names."}
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@template_router.delete("/delete/", summary="Delete template by id")
@requires_feature_permission("delete")
async def delete_template(
        current_user: CurrentUser,
        template_id: str = Query(
            ..., description="Enter id of a template which you want to delete"
        ),
        college: dict = Depends(get_college_id),
):
    """
     Delete template by id
    * :*param* **template_id** description="Enter id of a template which you want to delete", example="62f13a09375bf909a28ea9d8":\n
    * :return Message - Template deleted:
    """
    await UserHelper().check_user_has_permission(current_user)
    await utility_obj.is_id_length_valid(_id=template_id, name="Template id")
    template = await DatabaseConfiguration().template_collection.find_one(
        {"_id": ObjectId(template_id)}
    )
    if not template:
        raise HTTPException(
            status_code=404,
            detail="Template not found. Make sure provided template id should be correct.",
        )
    if template.get("active", False):
        return {
            "detail": "Template is activated. For delete template, need to deactivate it."
        }
    await DatabaseConfiguration().template_collection.delete_one(
        {"_id": ObjectId(template_id)}
    )
    await cache_invalidation("templates/delete/")
    return {"message": "Template deleted."}


@template_router.put("/otp/add_or_update/",
                     summary="Create or update otp template")
@requires_feature_permission("write")
async def create_or_update_otp_template(
        current_user: CurrentUser,
        otp_template_schema: OtpTemplateSchema = Body(None),
        template_id: str = Query(
            None,
            description="Enter otp template id if you want to " "update template data"
        ),
        college: dict = Depends(get_college_id),
):
    """
    Create or update otp template
    """
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") != "college_super_admin":
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    template_details = {}
    if otp_template_schema:
        template_details = {
            key: value
            for key, value in otp_template_schema.dict().items()
            if value is not None
        }
    if template_details.get("template_name") not in ["", None]:
        if (
                await DatabaseConfiguration().otp_template_collection.find_one(
                    {"template_name": str(
                        template_details.get("template_name")).lower()}
                )
                is not None
        ):
            return {"detail": "Template name already exist."}
        template_details["display_name"] = template_details.get(
            "template_name", "")
        template_details["template_name"] = template_details.pop(
            "template_name", ""
        ).lower()
    last_modified_timeline = [
        {
            "last_modified_at": datetime.utcnow(),
            "user_id": ObjectId(str(user.get("_id"))),
            "user_name": utility_obj.name_can(user),
        }
    ]
    if template_id:
        await utility_obj.is_id_length_valid(_id=template_id,
                                             name="Template id")
        tag_data = await DatabaseConfiguration().otp_template_collection.find_one(
            {"_id": ObjectId(template_id)}
        )
        if not tag_data:
            raise HTTPException(
                status_code=404,
                detail="Template not found. Make sure provided template id should be correct.",
            )
        template_details["last_modified_timeline"] = (
                tag_data.get("last_modified_timeline") + last_modified_timeline
        )
        await DatabaseConfiguration().otp_template_collection.update_one(
            {"_id": ObjectId(template_id)}, {"$set": template_details}
        )
        await cache_invalidation("templates/otp/add_or_update/")
        return {"message": "Template data updated."}
    else:
        if template_details.get("template_name") in ["", None]:
            raise HTTPException(status_code=422,
                                detail="Template name not provided.")
        elif template_details.get("content") in ["", None]:
            raise HTTPException(
                status_code=422, detail="Template content not provided."
            )
        data = {
            "display_name": template_details.get("display_name"),
            "template_name": template_details.pop("template_name"),
            "content": template_details.pop("content"),
            "last_modified_timeline": last_modified_timeline,
            "sms_type": template_details.get("sms_type"),
            "sender": template_details.get("sender"),
            "dlt_content_id": template_details.get("dlt_content_id"),
            "created_by": ObjectId(str(user.get("_id"))),
            "created_by_user_name": utility_obj.name_can(user),
            "created_on": datetime.utcnow(),
        }
        add_template_data = (
            await DatabaseConfiguration().otp_template_collection.insert_one(
                data)
        )
        data.update({"_id": add_template_data.inserted_id})
        await cache_invalidation("templates/otp/add_or_update/")
        return {
            "data": await TemplateActivity().otp_template_helper(data),
            "message": "Template created.",
        }


@template_router.post("/otp/", summary="Get all OTP templates")
@requires_feature_permission("read")
async def templates(
        current_user: CurrentUser,
        page_num: int = Query(
            gt=0,
            description="Enter page number where you want to show email templates " "data",
            example=1,
        ),
        page_size: int = Query(
            gt=0,
            description="Enter page size means how many data you want to show on page_num",
            example=25,
        ),
        cache_data=Depends(cache_dependency),
        college: dict = Depends(get_college_id),
):
    """
    Get All OTP Templates
    """
    user = await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    (
        all_templates_data,
        total_templates_count,
    ) = await Template().get_all_otp_templates_data(
        page_num=page_num, page_size=page_size
    )
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total_templates_count,
        route_name="/templates/otp/"
    )
    data = {
        "data": all_templates_data,
        "total": total_templates_count,
        "count": page_size,
        "pagination": response["pagination"],
        "message": "Get all otp templates.",
    }
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@template_router.delete("/otp/delete/", summary="Delete OTP template by id")
@requires_feature_permission("delete")
async def delete_template(
        current_user: CurrentUser,
        template_id: str = Query(
            ...,
            description="Enter id of an OTP template which you want to delete"
        ),
        college: dict = Depends(get_college_id),
):
    """
    Delete OTP template by id
    """
    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") != "college_super_admin":
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    await utility_obj.is_id_length_valid(_id=template_id, name="Template id")
    templates = await get_collection_from_cache(collection_name="templates")
    if templates:
        template = utility_obj.search_for_document(templates, field="_id", search_name=str(template_id))
    else:
        template = await DatabaseConfiguration().otp_template_collection.find_one(
            {"_id": ObjectId(template_id)}
        )
        collection = await DatabaseConfiguration().otp_template_collection.aggregate([]).to_list(None)
        await store_collection_in_cache(collection, collection_name="templates")
    if not template:
        raise HTTPException(
            status_code=404,
            detail="Template not found. Make sure provided template id should be correct.",
        )
    await DatabaseConfiguration().otp_template_collection.delete_one(
        {"_id": ObjectId(template_id)}
    )
    await cache_invalidation("templates/otp/delete/")
    return {"message": "Template deleted."}


@template_router.get("/otp/get_by_name_or_id/")
@requires_feature_permission("read")
async def get_otp_template_details_by_name_or_id(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        college: dict = Depends(get_college_id),
        template_id: str = Query(None, description="Enter otp template id"),
        template_name: str = Query(None,
                                   description="Enter otp template name"),
):
    """
    Get data segment details by id or name
    """
    user = await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    otp_template = await TemplateActivity().get_template_details_by_id_or_name(
        template_id, template_name
    )
    if otp_template:
        data = {
            "data": await TemplateActivity().otp_template_helper(otp_template),
            "message": "Get otp template details.",
        }
        if cache_key:
            await insert_data_in_cache(cache_key, data)
        return data
    return {
        "detail": "Template not found. Make sure you provided "
                  "template_id or template_name is correct."
    }


@template_router.put("/set_active/")
@requires_feature_permission("edit")
async def activate_template(
        activate_template_data: ActivateTemplate,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
):
    """
    Activate email template based on template id
    """
    await UserHelper().is_valid_user(current_user)
    data = await TemplateActivity().activate_template(activate_template_data)
    await cache_invalidation("templates/set_active/")
    return data


@template_router.get("/get_template_merge_fields/")
@requires_feature_permission("read")
async def get_template_merge_fields(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
        page_num: None | int = None,
        page_size: None | int = None,
):
    """
    Get template merge fields.

    Params:
        - college_id (str): An unique identifier/id of college for
            get college data. e.g., 123456789012345678901234
        - page_num (int | None): Either None or page number where you want
                to show data. e.g., 1
        - page_size (int | none): Either None or page size, useful for show
                data on page_num. e.g., 25.
                If we give page_num=1 and page_size=25 i.e., we want 25
                    records on page 1.

    Returns:
        dict: A dictionary which template merge fields along with message and
            other info.
    """
    await UserHelper().is_valid_user(current_user)
    return await TemplateActivity().get_template_merge_fields(
        ObjectId(college.get("id")), page_num, page_size
    )


@template_router.post("/add_template_merge_field/")
@requires_feature_permission("write")
async def add_template_merge_field(
        add_merge_field: AddMergeField,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
):
    """
    Add template merge field.

    Params:
        - college_id (str): An unique identifier/id of college for
            get college data. e.g., 123456789012345678901234

    Request body params:
        - add_merge_field (AddMergeField): An object of pydantic class
                `AddMergeField` which contains following fields:
            - field_name (str): Required field. Name of a field.
                    e.g., "field_name"
            - value (str): Required field. Value of the field.
                    e.g., "value"

    Returns:
        dict: A dictionary which template merge fields along with message and
            other info.
    """
    add_merge_field = add_merge_field.model_dump()
    await UserHelper().is_valid_user(current_user)
    try:
        data = await TemplateActivity().add_template_merge_field(
            ObjectId(college.get("id")), add_merge_field
        )
        await cache_invalidation("templates/add_template_merge_field/")
        return data
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as e:
        logger.exception(
            f"An error occurred when add specializations of course: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when add template "
                   f"merge field. Error: {str(e)}",
        )


@template_router.get("/get_template_details")
@requires_feature_permission("read")
async def get_template_detail(
        template_id: str,
        template_type: str,
        current_user: CurrentUser,
        student_id: str = None,
        message_id: str = None,
        college: dict = Depends(get_college_id),
):
    """
    Get the template data by template id.

    Params:
        - template_id (str): Unique identifier/id of a template
        which useful for get template data.
         - template_type (str): Type of template. e.g., whatsapp, email, sms.
         - college_id (s): trUnique identifier/id of a college which useful
          for get college data.

    Returns:
        dict: A dictionary which contains template data.

    Exception:
       - 401: An error occurred with status code 401 when user don't
       have access to use API.
       - DataNotFoundError: An error occurred with status code 404 when
       template not found.
        - ObjectIdInValid: An error occurred with status code 422 when
        template_id will be invalid.
        Exception: An error occurred with status code 500 when something
        wrong happen in the backend code.
    """
    if template_type.lower() not in ["email", "sms", "whatsapp"]:
        raise HTTPException(
            status_code=422, detail="template type is not a valid template"
        )
    await UserHelper().is_valid_user(user_name=current_user)
    try:
        return await TemplateActivity().get_template(
            template_id=template_id,
            template_type=template_type,
            message_id=message_id,
            student_id=student_id
        )
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@template_router.post("/add_or_get_template_category")
@requires_feature_permission("write")
async def add_or_get_template_category(
        current_user: CurrentUser,
        category_name: str | None = None,
        college: dict = Depends(get_college_id),
) -> dict:
    """Create or Get list of template category

    Params:
        category_name (str | None, optional): Name of category which have to add in the list of category otherwise leave it blank. Defaults to None.
        current_user (User, optional): Current user details. Defaults to Depends(get_current_user).
        college (dict, optional): College unique id. Defaults to Depends(get_college_id).

    Returns:
        dict: List of template categories.
    """
    try:
        user = await UserHelper().is_valid_user(user_name=current_user)
        data = await TemplateActivity().add_or_get_category(user, category_name)
        return {"data": data,
                "message": "Get or Add template category successfully."}

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when add or get the template category data. Error: {error}.",
        )


@template_router.post("/gallery_upload")
@requires_feature_permission("write")
async def gallery_upload(
        current_user: CurrentUser,
        file: UploadFile = File(...),
        college: dict = Depends(get_college_id),
) -> dict:
    """\nAPI for upload files like image, video and pdf and generate access link.

    Params:\n
        file (UploadFile): File must be a video, image or File ('.zip', '.doc', '.docx', '.xlx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf') which is under 100 mb. Defaults to None.
        current_user (User): User must be college_admin, college_super_admin or super_admin. Defaults to Depends(get_current_user).
        college_id (dict): Unique college id. Defaults to Depends(get_college_id).

    Raise:\n
        CustomError: When file format will invalid.
        CustomError: When file size will be greater than 100mb.

    Returns:\n
        dict: Response message about file upload
    """
    try:
        # User authorization validation
        user = await UserHelper().is_valid_user(current_user)

        filename = file.filename
        extension = PurePath(file.filename).suffix.lower()

        # File type validation
        if extension not in ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.avi', '.wmv', '.flv', '.zip', '.doc',
                             '.docx', '.xlx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf']:
            raise CustomError("file format is not supported")

            # Determine file type
        file_type = (
            "Image" if extension in ['.jpg', '.jpeg', '.png', '.gif'] else
            "Video" if extension in ['.mp4', '.mov', '.avi', '.wmv', '.flv'] else
            "File"
        )

        # Generate a unique filename
        file.filename = utility_obj.create_unique_filename(extension=extension)

        # Extract and validate file size
        file_size = len(await file.read()) / 1048576  # Convert bytes to MB
        if file_size >= 100:
            raise CustomError("File size must be under 100 MB.")
        await file.seek(0)  # Reset file pointer

        # Extract image dimensions if applicable
        dimensions = None
        if extension in ['.jpg', '.jpeg', '.png', '.gif']:
            image = Image.open(BytesIO(await file.read()))
            dimensions = image.size
            await file.seek(0)  # Reset file pointer

        # File url and name.
        season_year = utility_obj.get_year_based_on_season()
        aws_env = settings.aws_env
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        base_bucket_url = getattr(settings, f"s3_{aws_env}_base_bucket_url")
        path = (
            f"{utility_obj.get_university_name_s3_folder()}/{season_year}/"
            f"{settings.s3_assets_bucket_name}/template-gallery/"
        )

        # Upload file on s3.
        upload_files = await upload_multiple_files(
            files=[file],
            bucket_name=base_bucket,
            base_url=base_bucket_url,
            path=path
        )

        if upload_files:
            # File details saved in db
            await DatabaseConfiguration().template_gallery.insert_one({
                "uploaded_by": user.get("user_name"),
                "uploaded_on": datetime.utcnow(),
                "file_name": filename,
                "file_extension": extension,
                "file_type": file_type,
                "file_size": file_size,
                "media_url": upload_files[0].get("public_url"),
                "dimensions": dimensions,
                "is_deleted": False
            })

            await cache_invalidation(api_updated="templates/gallery_upload")

            return {"message": "File uploaded successfully!!"}

        else:
            raise CustomError("File upload failed")

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when upload file for template gallery. Error: {error}.",
        )


@template_router.post("/get_media_gallery")
@requires_feature_permission("read")
async def get_media_gallery(
        current_user: CurrentUser,
        testing: Is_testing,
        media_type: list[str] = Body(None),
        uploaded_by: list[str] = Body(None),
        date_range: DateRange = Body(None),
        search: str = Body(None),
        page_num: int = Query(1, gt=0),
        page_size: int = Query(25, gt=0),
        cache_data=Depends(cache_dependency),
        college: dict = Depends(get_college_id),
) -> dict:
    """\nAPI for getting all media data for template gallery.

    Params:\n
        media_type (list[str], optional): It must be 'Video', 'Image' or 'File' for filtering data. Defaults to Body(None).
        uploaded_by (list[str], optional): It should be the user_name of the user whos uploaded gallery has to be filter. Defaults to Body(None).
        date_range (DateRange, optional): Date range filter which holds start_date and end_date. Defaults to Body(None).
        search (str, optional): Search string for filtering according to the search query of file name. Defaults to Body(None).
        page_num (int, optional): Current page no.. Defaults to 1.
        page_size (int, optional): No of data in one page. Defaults to 25
        college_id (dict, optional): College unique id. Defaults to Depends(get_college_id).

    Raises:\n
        CustomError: Permission denied which unauthorize user try to access. Allowed users - "college_admin", "college_super_admin" and "super_admin"
        CustomError: When media type will be invalid.

    Returns:\n
        dict: List of media files with details.
    """

    date_range = await utility_obj.format_date_range(date_range)
    cache_key, data = cache_data

    if data:
        return data

    try:
        if not testing:
            Reset_the_settings().check_college_mapped(college.get("id"))

        if (
                user := await DatabaseConfiguration().user_collection.find_one(
                    {"user_name": current_user.get("user_name")}
                )
        ) is None or user.get("role", {}).get("role_name", "") not in [
            "college_admin",
            "college_super_admin",
            "super_admin"
        ]:
            raise CustomError("permission denied")

        if media_type and set(media_type) - {'Video', 'Image', 'File'}:
            raise CustomError("Invalid media type.")

        data, count = await TemplateGallery().template_gallery_data_helper(
            media_type=media_type, uploaded_by=uploaded_by, date_range=date_range, search=search, page_num=page_num,
            page_size=page_size
        )

        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, count, "/templates/get_media_gallery"
        )

        data = {
            "data": data,
            'total': count,
            "count": page_size,
            "pagination": {
                "next": response.get("pagination", {}).get("next"),
                "previous": response.get("pagination", {}).get("previous"),
            },
            "message": "Template gallery data retrieve successfully!!"
        }

        if cache_key:
            await insert_data_in_cache(cache_key, data)
        return data


    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when getting files of template gallery. Error: {error}.",
        )


@template_router.post("/delete_gallery_data")
@requires_feature_permission("delete")
async def delete_gallery_data(
        testing: Is_testing,
        data_ids: list[str],
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)
) -> dict:
    """\nAPI for deleting the gallery data by passing the gallery data id (it should be single or multiple)

    Request Body Params:\n
        data_ids (list[str]): It is a list of media id which has to be deleted.

    Params:\n
        college_id (dict, optional): College unique id.

    Raises:\n
        ObjectIdInValid: An error occurred with status code 422 when user pass the wrong or invalid media id.
        CustomError: An error occurred with status code 400 when user not enough permission or user pass the invalid media id
        Exception: An error occurred with status code 500 when something wrong happen in the backend code other than .

    Returns:\n
        dict: Response message about media.
    """
    try:
        if not testing:
            Reset_the_settings().check_college_mapped(college.get("id"))
        if (
                user := await DatabaseConfiguration().user_collection.find_one(
                    {"user_name": current_user.get("user_name")}
                )
        ) is None or user.get("role", {}).get("role_name", "") not in [
            "college_admin",
            "college_super_admin",
            "super_admin"
        ]:
            raise CustomError("permission denied")

        for data_id in data_ids:
            if len(data_id) != 24 or \
                    not await (DatabaseConfiguration().template_gallery.aggregate([
                        {"$match": {"_id": ObjectId(data_id), "is_deleted": False}}])).to_list(None):
                raise CustomError("Gallery data id is invalid.")

        return await TemplateGallery().template_gallery_delete_helper(data_ids)


    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when deleting files of template gallery. Error: {error}.",
        )


@template_router.post("/download_media")
@requires_feature_permission("download")
async def download_media(
        current_user: CurrentUser,
        testing: Is_testing,
        media_ids: list[str] = Body(None),
        college: dict = Depends(get_college_id),
) -> dict:
    """\nAPI for getting links of selected media download

    Params:\n
        media_ids (list[str], optional): List of media unique id which has to be download. Defaults to Body(None).
        college_id (dict, optional): College unique id. Defaults to Depends(get_college_id).

    Raises:
        CustomError: Must be valid all media id otherwise raise this error.

    Returns:
        dict: List of media links in media_links.
    """
    try:
        if not testing:
            Reset_the_settings().check_college_mapped(college.get("id"))
        if (
                user := await DatabaseConfiguration().user_collection.find_one(
                    {"user_name": current_user.get("user_name")}
                )
        ) is None or user.get("role", {}).get("role_name", "") not in [
            "college_admin",
            "college_super_admin",
            "super_admin"
        ]:
            raise CustomError("permission denied")

        template_media_ids = []
        if media_ids:
            for media_id in media_ids:
                if len(media_id) == 24:
                    if not await DatabaseConfiguration().template_gallery.find_one(
                            {"_id": ObjectId(media_id), "is_deleted": False}):
                        raise CustomError("Invalid media selected.")
                    if ObjectId(media_id) not in template_media_ids:
                        template_media_ids.append(ObjectId(media_id))
                else:
                    raise CustomError("Invalid media id")
        else:
            raise CustomError("Select a valid media file")

        response = await TemplateGallery().template_gallery_download_helper(template_media_ids)
        response.update({"message": "Template gallery download link retrieve successfully!!"})
        return response


    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when getting download links of template gallery. Error: {error}.",
        )


@template_router.get("/get_spec_media_details")
@requires_feature_permission("read")
async def get_spec_media_details(
        testing: Is_testing,
        media_id: str,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
) -> dict:
    """\nAPI for getting specific media all details by passing there unique id in parameter.\n

    Params:\n
        media_id (str): Media unique id
        college_id (dict, optional): College unique id.

    Raises:\n
        - ObjectIdInValid: An error occurred with status code 422 when user pass the wrong or invalid media id.
        - CustomError: An error occurred with status code 400 when user not enough permission or user pass the invalid media id
        - Exception: An error occurred with status code 500 when something wrong happen in the backend code other than .

    Returns:\n
        dict: Returns all media details in the json format.
    """
    try:
        if not testing:
            Reset_the_settings().check_college_mapped(college.get("id"))
        if (
                user := await DatabaseConfiguration().user_collection.find_one(
                    {"user_name": current_user.get("user_name")}
                )
        ) is None or user.get("role", {}).get("role_name", "") not in [
            "college_admin",
            "college_super_admin",
            "super_admin"
        ]:
            raise CustomError("permission denied")

        if len(media_id) != 24 or \
                not await (DatabaseConfiguration().template_gallery.aggregate([
                    {"$match": {"_id": ObjectId(media_id), "is_deleted": False}}])).to_list(None):
            raise CustomError("Gallery media id is invalid.")

        return {
            "data": await TemplateGallery().template_gallery_spec_media_helper(media_id),
            "message": "Media data fetched successfully."
        }

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when getting the specific media details of template gallery. Error: {error}.",
        )


@template_router.get("/get_media_uploaded_user_list")
@requires_feature_permission("read")
async def get_media_uploaded_user_list(
        testing: Is_testing,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)
) -> dict:
    """\nAPI for getting List of users who have uploaded photo/video/file\n

    Params:\n
        college_id: Unique college id for validation.

    Raises:\n
        CustomError: If user has no permission for getting result.
        Exception: It raise In case of database error.


    Returns:\n
        dict: Data response with list of users and details.
    """
    try:
        if not testing:
            Reset_the_settings().check_college_mapped(college.get("id"))
        if (
                user := await DatabaseConfiguration().user_collection.find_one(
                    {"user_name": current_user.get("user_name")}
                )
        ) is None or user.get("role", {}).get("role_name", "") not in [
            "college_admin",
            "college_super_admin",
            "super_admin"
        ]:
            raise CustomError("permission denied")

        return {
            "data": await TemplateGallery().media_uploaded_user_helper(),
            "message": "Users data fetched successfully."
        }

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(error)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred when getting the user details of template gallery. Error: {error}.",
        )


@template_router.get("/email_id_list")
@requires_feature_permission("read")
async def get_all_email_id(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        college: dict = Depends(get_college_id),
) -> dict:
    """\nGetting email id list of organization from the database.\n

    Params:\n
        - college_id (str): An unique identifier/id of college which useful for get college data/information.

    Returns:\n
        - dict: A dictionary which contains list of email id list.
    """
    cache_key, data = cache_data
    if data:
        return data

    user = await UserHelper().is_valid_user(current_user)
    if user.get("role", {}).get("role_name") in [
        "college_admin",
        "college_super_admin",
        "super_admin",
    ]:
        data = college.get("email_id_list", {})

    else:
        raise HTTPException(status_code=400, detail="User not authorized.")

    data = {"data": data, "message": "Get the email id list."}

    if cache_key:
        await insert_data_in_cache(cache_key, data)

    return data


@template_router.post("/template_ids_for_filter", summary="Get all template ids for filter")
@requires_feature_permission("read")
async def get_template_ids_for_filter(
        template_type: str,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
):
    """
        Retrieve template IDs based on the given template type.

        Params:
            template_type (str): The type of template to filter.
            current_user (User): The currently authenticated user (injected dependency).
            college (dict): The college details, including its ID (injected dependency).

        Returns:
            List[dict]: A list of email template IDs matching the given filter criteria.
    """
    await UserHelper().is_valid_user(current_user)
    templates = await DatabaseConfiguration().template_collection.aggregate([
        {
            "$match": {
                "template_type": template_type.lower(),
                "is_published": True
            }
        },
        {
            "$project": {
                "_id": 0,
                "template_id": {"$toString": "$_id"},
                "template_name": 1
            }
        }
    ]).to_list(None)
    return templates
