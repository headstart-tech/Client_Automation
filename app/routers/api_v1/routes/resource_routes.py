"""
This file contains API routes related to resource
"""
from typing import Union

from fastapi import APIRouter, Depends, Query, Body
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException

from app.core.custom_error import CustomError, ObjectIdInValid, \
    DataNotFoundError
from app.core.log_config import get_logger
from app.core.utils import utility_obj, requires_feature_permission
from app.database.aggregation.resource import Resource
from app.dependencies.college import get_college_id
from app.dependencies.oauth import CurrentUser, cache_dependency, \
    insert_data_in_cache, cache_invalidation
from app.helpers.resource.category_config import KeyCategory
from app.helpers.resource.script_config import ScriptQuery
from app.helpers.resource.updates_config import Updates
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.resource_schema import CreateKeyCategory, SendUpdateToProfile, \
    CreateQuestion, QuestionFilter, ScriptField

resource_router = APIRouter()
logger = get_logger(name=__name__)


@resource_router.post("/create_key_category/",
                      summary="Create a key category.")
@requires_feature_permission("write")
async def create_key_category(
        category_info: CreateKeyCategory,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
        index_number: int | None = Query(
            None, description="Required in case of update key category name. "
                              "A unique number of key category. "
                              "e.g., 0"),
):
    """
    Create a key category.

    Params:
        - college_id (str): A unique id/identifier of a college.
            e.g., 123456789012345678901234
        - index_number (int | None): Required in case of update key category name.
            A unique number of key category. e.g., 0

    Request body params:
        - key_category_name (CreateKeyCategory): An object of pydantic class
                `CreateKeyCategory` which contains following field:
                - category_name (str): Required field. Name of a category.
                    e.g., "test_category"

    Returns:
        dict: A dictionary which contains information about create key
        category.
    """
    user = await UserHelper().is_valid_user(current_user)
    category_info = jsonable_encoder(category_info)
    try:
        data = await KeyCategory().create_key_category(college, category_info,
                                                       user, index_number)
        await cache_invalidation("resource/create_key_category")
        return data
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        logger.error("An error got when creating key category in the "
                     "resource category section.")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@resource_router.post("/send_update_to_profile/", summary="Send update to the "
                                                          "selected profiles")
@requires_feature_permission("write")
async def send_update_to_profile(
        send_update_info: SendUpdateToProfile,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)
):
    """
    Send update to the selected profiles.

    Params:
        - college_id (str): A unique id/identifier of a college.
            e.g., 123456789012345678901234

    Request body params:
        - send_update_info (SendUpdateToProfile): An object of pydantic class
                `SendUpdateToProfile` which contains following field:
                - selected_profiles (list[str]): Required field. A list which
                    contains role names of users who will receive update.
                    e.g., ["super_admin", "college_admin"]
                    Possible values are super_admin, client_manager,
                    college_super_admin, college_admin, college_head_counselor,
                     college_counselor, college_publisher_console, panelist,
                     authorized_approver and moderator.
                - title (str): A title of the update. e.g., Test update
                - update_content (Str): Content which want to update/send to
                    the selected profiles. e.g., Test content

    Returns:
        dict: A dictionary which contains information about send update to
            the selected profiles.
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        data = await Updates().send_update_to_profiles(
            college.get('id'), jsonable_encoder(send_update_info), user)
        return data
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        logger.error("An error got when send update to the selected profiles "
                     "in the resource updates section.")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@resource_router.get("/get_user_updates/", summary="Get the user updates")
@requires_feature_permission("read")
async def get_user_updates(
        current_user: CurrentUser,
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
        college: dict = Depends(get_college_id),
        update_id: str = None
):
    """
    Get the user updates.

    Params:\n
        - college_id (str): A unique id/identifier of a college.
            e.g., 123456789012345678901234
        - page_num (int | None): Either None or page number where you want
                to data. e.g., 1
        - page_size (int | none): Either None or page size, useful for show
                data on page_num. e.g., 25.
                If we give page_num=1 and page_size=25 i.e., we want 25
                    records on page 1.

    Returns:\n
        dict: A dictionary which contains information about user updates.
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        user_updates, total_updates = await Resource().get_user_updates(
            page_num, page_size, user.get("role", {}).get("role_name"),
            update_id)
        response = {}
        if page_num and page_size:
            response = await utility_obj.pagination_in_aggregation(
                page_num, page_size, total_updates,
                "/resource/get_user_updates/")
        return {"data": user_updates, "total": total_updates,
                "pagination": response.get("pagination"),
                "message": "Get the user updates."}
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        logger.error("An error got when send update to the selected profiles "
                     "in the resource updates section.")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@resource_router.get("/get_key_categories/", summary="Get key categories")
@requires_feature_permission("read")
async def get_key_categories(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        college: dict = Depends(get_college_id),
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
):
    """
    Get key categories.

    Params:
        - college_id (str): A unique id/identifier of a college.
            e.g., 123456789012345678901234
        - page_num (int | None): Either None or page number where you want
                to data. e.g., 1
        - page_size (int | none): Either None or page size, useful for show
                data on page_num. e.g., 25.
                If we give page_num=1 and page_size=25 i.e., we want 25
                    records on page 1.

    Returns:
        dict: A dictionary which contains information about get key
        categories.
    """
    cache_key, data = cache_data
    if data:
        return data
    exist_key_categories = college.get("key_categories", [])
    if not exist_key_categories:
        exist_key_categories = []
    exist_key_categories = [
        {"index": category_info.get("index"), "category_name": category_info.get("category_name"),
         "total": await Resource().get_questions(
             page_num, page_size, {"tags":
                                       [category_info.get("category_name",
                                                          "")]},
             total_only=True
         )}
        for category_info in exist_key_categories]
    response, total = {}, len(exist_key_categories)
    if page_num and page_size:
        response = await utility_obj.pagination_in_api(
            page_num, page_size, exist_key_categories,
            total, "/resource/get_key_categories/")
        exist_key_categories = response['data']
    data = {"data": exist_key_categories,
            "message": "Get the key categories.", "total":
                total, "pagination":
                response.get("pagination")}
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@resource_router.post("/create_or_update_a_question/",
                      summary="Create or update a question.")
@requires_feature_permission("write")
async def create_or_update_a_question(
        current_user: CurrentUser,
        question_info: CreateQuestion,
        question_id: str | None = Query(
            None, description="Required in case of update question info. "
                              "A unique id/identifier of question. "
                              "e.g., 123456789012345678901241"),
        college: dict = Depends(get_college_id)
):
    """
    Create or update a question.

    Params:
        - college_id (str): Required field.
            A unique id/identifier of a college. e.g., 123456789012345678901234
        - question_id (str): Required in case of update question info.
            A unique id/identifier of a question.
            e.g., 123456789012345678901241

    Request body params:
        - question_info (CreateQuestion): An object of pydantic class
                `CreateQuestion` which contains following field:
                - question (str): Required field in case of create question.
                    Question which want to add.
                    e.g., "Eligibility criteria of course B.Sc.?"
                - answer (str): Required field in case of create question.
                    Answer of the question.
                    e.g., "Candidate must completed 10th."
                - tags (list[str] | None): Optional field. Tags which want to
                    add to the question. e.g., ["Eligibility", "Course"]

    Returns:
        dict: A dictionary which contains information about create or update
            a question.
    """
    user = await UserHelper().is_valid_user(current_user)
    question_info = jsonable_encoder(question_info)
    try:
        data = await KeyCategory().create_or_update_a_question(
            question_info, user, question_id)
        await cache_invalidation(
            api_updated="resource/create_or_update_a_question")
        return data
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        logger.error(f"An error got when create a question. Error - {error}")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@resource_router.post("/get_questions/", summary="Get the questions "
                                                 "with/without filters.")
@requires_feature_permission("read")
async def get_questions(
        current_user: CurrentUser,
        question_filter: QuestionFilter | None = Body(None),
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
        cache_data=Depends(cache_dependency),
        college: dict = Depends(get_college_id)
):
    """
    Get the questions with/without filters.

    Params:\n
        - college_id (str): A unique id/identifier of a college.
            e.g., 123456789012345678901234
        - page_num (int | None): Either None or page number where you want
                to data. e.g., 1
        - page_size (int | none): Either None or page size, useful for show
                data on page_num. e.g., 25.
                If we give page_num=1 and page_size=25 i.e., we want 25
                    records on page 1.

    Request body params:
        - question_filter (QuestionFilter | None): None or An object of
            pydantic class `QuestionFilter` which contains following field:
                - search_pattern (str | None):
                    None or a pattern which useful for get questions based on
                        pattern match. e.g., "tes"
                - tags (list[str] | None): None or tags which useful for get
                    questions based on tags. e.g., ["Eligibility", "Course"]

    Returns:\n
        dict: A dictionary which contains information about get questions.
    """
    try:
        cache_key, data = cache_data
        if data:
            return data
        if not question_filter:
            question_filter = {}
        question_filter = jsonable_encoder(question_filter)
        user_updates, total_updates = await Resource().get_questions(
            page_num, page_size, question_filter)
        response = {}
        if page_num and page_size:
            response = await utility_obj.pagination_in_aggregation(
                page_num, page_size, total_updates,
                "/resource/get_questions/")
        data = {"data": user_updates, "total": total_updates,
                "pagination": response.get("pagination"),
                "message": "Get the questions."}
        if cache_key:
            await insert_data_in_cache(cache_key, data)
        return data
    except Exception as error:
        logger.error("An error got when get the questions "
                     "in the resource section.")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@resource_router.post("/delete_questions/",
                      summary="Delete questions.")
@requires_feature_permission("delete")
async def delete_questions(
        questions_ids: list[str],
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)
):
    """
    Delete questions based on ids.

    Params:\n
        - college_id (str): A unique id/identifier of a college.
            e.g., 123456789012345678901234

    Request body params:\n
        - questions_ids (list[str]): A list which contains questions unique
            ids/identifiers.

    Returns:\n
        dict: A dictionary which contains information about delete questions.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        data = await KeyCategory().delete_questions(questions_ids)
        await cache_invalidation(api_updated="resource/delete_questions")
        return data
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        logger.error("An error got when delete the questions "
                     "in the resource section.")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@resource_router.delete("/delete_key_category/",
                        summary="Delete a key category by index number.")
@requires_feature_permission("delete")
async def delete_key_category(
        current_user: CurrentUser,
        index_number: int = Query(
            description="Required in case of update key category name. "
                        "A unique number of key category. e.g., 0"),
        college: dict = Depends(get_college_id)
):
    """
    Delete a key category by index number.

    Params:\n
        - college_id (str): A unique id/identifier of a college.
            e.g., 123456789012345678901234
        - index_number (int): Required field. A unique index number of key
            category. e.g., 0

    Returns:\n
        dict: A dictionary which contains information about delete key
            category.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        data = await KeyCategory().delete_key_category(index_number, college)
        await cache_invalidation(api_updated="resource/delete_key_category")
        return data
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        logger.error("An error got when delete the key category "
                     "in the resource section.")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@resource_router.put("/create_or_update_a_script/",
                     summary="Create or update any script")
@requires_feature_permission("write")
async def create_or_update_a_script(
        current_user: CurrentUser,
        script_data: ScriptField,
        script_id: str | None = Query(
            None, description="Required in case of update scripts. "
                              "A unique id/identifier of scripts. "
                              "e.g., 123456789012345678901241"),
        college: dict = Depends(get_college_id)
):
    """
    Create or Update for Scripts

    Args:
        script_data (ScriptField): Script data dictionary which has to be update or insert.
        script_id (str | None, optional): Script ID is only for the update purpous of script. If you have to insert any new script then you doesn't need to pass script_id. Defaults to Query( None, description="Required in case of update scripts. " "A unique id/identifier of scripts. " "e.g., 123456789012345678901241").
        current_user (User, optional): User details of Requested user. Defaults to Depends(get_current_user).
        college (dict, optional): For validation of the correct college request. Defaults to Depends(get_college_id).

    Returns:
        dict: Returns the response message in json format.
    """

    user = await UserHelper().is_valid_user(current_user)

    script_data = jsonable_encoder(script_data)
    try:
        return await ScriptQuery().create_or_update_script(
            script_data, user, script_id)

    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)

    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)

    except Exception as error:
        logger.error(f"An error got when create a script. Error - {error}")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@resource_router.post("/scripts/", summary="get all scripts with pagination")
@requires_feature_permission("read")
async def get_all_scripts(
        current_user: CurrentUser,
        all: bool = True,
        page_num: int = 1,
        page_size: int = 10,
        search: str | None = None,
        program_name: list | None = Body(None),
        tags: list | None = Body(None),
        application_stage: str | None = Body(None),
        lead_stage: str | None = Body(None),
        source: list | None = Body(None),
        sort: bool | None = None,
        sort_type: str | None = Query(None,
                               description="Sort_type can be 'asc' or 'dsc'"),
        sort_field: str | None = None,
        cache_data=Depends(cache_dependency),
        college: dict = Depends(get_college_id),
):
    """
    Get the Scripts with/without filters.

    Params:
        - all (bool): If want to return all scripts then
            True else return draft scripts.
        - page_num (int): The page number in pagination.
        - page_size(int): Size of the page in pagination.
        - search (str | None): Either None or search the required script.
        - course (str): The course filter if required.
        - sort (bool | None): Either None or True If want to sort the data.
        - sort_field (str | None): Either None or the field which is to be sorted.
        - college_id (str): An unique college identifier for get college data.

    Request body params:
        - program_name (list | None): Either None or A list which contains
            programs information which useful for filter data by program name (s).
        - tags (list | None): Either None or A list which contains
            tags information which useful for filter data by tags.
        - application_stage (str | None): Either None or A string value
            which useful for get data by application stage.
        - lead_stage (str | None): Either None or A string value
            which useful for get data by lead stage.
        - source (list | None): Either None or A list which contains
            source (s) information which useful for filter data by source (s).

    Returns:
        - dict: A dictionary which contains get scripts with/without filters.

    Raises:
        - Exception: An error occurred with status code 500 when
            something wrong happen in the code.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        cache_key, data = cache_data
        if data:
            return data
        data = await ScriptQuery().get_all_scripts(
            all, program_name, sort, sort_type, sort_field, tags,
            application_stage, lead_stage, source)
        if search:
            data = [data_dict for data_dict in data if
                    search in data_dict['script_name']]
        response = await utility_obj.pagination_in_api(page_num, page_size,
                                                       data, len(data),
                                                       route_name="/resource/scripts/")
        data = {
            "data": response["data"],
            "total": len(data),
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Get the scripts.",
        }
        if cache_key:
            await insert_data_in_cache(cache_key, data)
        return data
    except Exception as error:
        logger.error(f"An error got when get the scripts. Error - {error}")
        raise HTTPException(status_code=500, detail=f"Error - {error}")


@resource_router.delete("/delete_a_script/", summary="delete a script")
@requires_feature_permission("delete")
async def delete_scripts(
        script_id: str,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
):
    """
    Delete a script from database

    Params:
        script_id (str): the unique id of script
        current_user (User, optional): User details of Requested user. Defaults to Depends(get_current_user).
        college (dict, optional): For validation of the correct college request. Defaults to Depends(get_college_id).

    Returns:
        - dict: A dictionary which contains information about delete a script.

    Raises:
        - ObjectIdInValid: An error occurred with status code 422 when script id is wrong.
        - DataNotFoundError: An error occurred with status code 404 when script not found.
        - Exception: An error occurred with status code 500 when s something wrong happen in the backend code.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        await utility_obj.is_length_valid(script_id, name="Script id")
        result = await ScriptQuery().delete_script(script_id)
        await cache_invalidation(api_updated="resource/delete_a_script")
        return {"message": result}
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as e:
        logger.error(f"{e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as error:
        logger.error(f"An error got when create a script. Error - {error}")
        raise HTTPException(status_code=500, detail=f"Error - {error}")
