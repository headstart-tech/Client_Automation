"""
This file contains API routes/endpoints related to nested automation
"""

from bson import ObjectId
from fastapi import APIRouter, Depends, Body, Query
from fastapi.exceptions import HTTPException

from app.core.custom_error import ObjectIdInValid, DataNotFoundError
from app.core.utils import utility_obj, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id
from app.dependencies.oauth import CurrentUser
from app.helpers.automation.automation_helper import nested_automation_helper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.applications import DateRange

nested_automation_router = APIRouter()


@nested_automation_router.post("/automation_link_to_data_segment")
@requires_feature_permission("read")
async def get_automation_assign_to_data_segment(
        current_user: CurrentUser,
        automation_id: str,
        data_segment_ids: list[str] = Body(),
        college: dict = Depends(get_college_id)
):
    """
    Data segment assign to the automation

    params:
        - automation_id (str): Get the automation id,
        - data_segment_id (list): Get the multiple data_segment_id of
            the data segment
        - current_user (str): Get the current user from the token automatically
        - college (dict): Get the college details based on college id

    return:
        - Data segment assign to the automation successfully.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await nested_automation_helper().data_segment_assign(
            automation_id=automation_id, data_segment_ids=data_segment_ids)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@nested_automation_router.get("/automation_top_bar_data")
@requires_feature_permission("read")
async def get_automation_top_bar_details(
        current_user: CurrentUser,
        status_type: str = None,
        data_type: str = None,
        college: dict = Depends(get_college_id)
):
    """
    Get automation top bar details

    params:
        - current_user (str): Get the current user from the token automatically
        - status_type (str): The filter for status type. This might have values saved, active, stopped
        - data_type (str): The filter for data_type. This might have values Lead,Raw Data, Application
        - college (dict): Get the college details based on college id

    return:
        - Automation top bar details
    """
    await UserHelper().is_valid_user(current_user)
    try:
        data = {"data": await nested_automation_helper().get_top_bar_details(
            status_type, data_type),
                "message": "Automation Top bar details."}
        return data
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@nested_automation_router.post("/automation_list")
@requires_feature_permission("read")
async def get_automation_list(
        current_user: CurrentUser,
        search: str = None,
        template: bool = None,
        data_type: list | None = Body(None),
        date_range: DateRange | None = Body(None),
        communication: list = Body(None),
        page_num: int = 1,
        page_size: int = 5,
        college: dict = Depends(get_college_id)
):
    """
    Get automation list

    params:
        - current_user (str): Get the current user from the token automatically
        - search (str): The search str to search automations
        - date_range (date range): the date range filter
        - communication (list): Communication filter This may have values email/sms/whatsapp
        - college (dict): Get the college details based on college id

    return:
        - dict - automation list
    """
    await UserHelper().is_valid_user(current_user)
    try:
        data, total = await nested_automation_helper().get_automation_list(
            search, date_range, communication, template,
            data_type, page_num, page_size)
        if data:
            await nested_automation_helper().get_last_execution_time(data=data)
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, total,
            route_name="/nested_automation/automation_list/"
        )
        data = {
            "data": data,
            "total": total,
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Automation List Details.",
        }
        return data
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@nested_automation_router.post("/delete_automation")
@requires_feature_permission("delete")
async def get_automation_list(
        current_user: CurrentUser,
        automation_ids: list = Body(),
        college: dict = Depends(get_college_id)
):
    """
    Deletion of automation

    params:
        - current_user (str): Get the current user from the token automatically
        - automation_ids (list): The list of unique ids of automation
        - college (dict): Get the college details based on college id

    return:
        - dict - message that automation is stopped
    """
    await UserHelper().is_valid_user(current_user)
    try:
        await nested_automation_helper().delete_automation(automation_ids),
        return {
            "message": "Automations which are not active are deleted successfully!"}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@nested_automation_router.post("/change_automation_status")
@requires_feature_permission("edit")
async def get_automation_list(
        current_user: CurrentUser,
        automation_ids: list = Body(),
        status: str = Body(),
        college: dict = Depends(get_college_id)
):
    """
    Stop the automations

    params:
        - current_user (str): Get the current user from the token automatically
        - automation_id (list): list of unique automation ids
        - college (dict): Get the college details based on college id

    return:
        - dict - message that automation stopped
    """
    await UserHelper().is_valid_user(current_user)
    try:
        automation_ids = [ObjectId(id) for id in automation_ids]
        filter_criteria = {'_id': {'$in': automation_ids}}
        update_operation = {'$set': {'status': status}}
        await DatabaseConfiguration().rule_collection.update_many(
            filter_criteria, update_operation)
        return {"message": "Automations status is changed successfully!"}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


@nested_automation_router.post("/get_active_data_segments")
@requires_feature_permission("read")
async def get_active_data_segments(
        current_user: CurrentUser,
        data_type: list[str] = Body([]),
        search: str = None,
        college: dict = Depends(get_college_id)
):
    """
    get active data segment based on given filters

    params:
        - current_user (str): Get the current user from the token automatically
        - data_type (str): A filter to get data segments this can have values (Lead, Application, Raw Data),
        - search (str): Used when some data is needed to search
        - college (dict): Get the college details based on college id

    raises:
        -  HTTPException: An error occurred with status code 404 when automation not found by automation_id.
        - ObjectIdInValid: An error occurred when automation_id is wrong.

    return:
        - dict - list of active data segments
    """
    await UserHelper().is_valid_user(current_user)
    try:
        data = await nested_automation_helper().get_active_data_segments(
            data_type, search)
        return {"data": data,
                "message": "Get Data Segments!"}
    except Exception as error:
        raise HTTPException(status_code=500,
                            detail=f"An error occurred when get active data segments. Error - {error}")


@nested_automation_router.post("/copy_automation")
@requires_feature_permission("write")
async def copy_automation(
        current_user: CurrentUser,
        automation_id: str,
        name: str | None = Body(None),
        data_segments: list = Body([]),
        college: dict = Depends(get_college_id)
):
    """
    copy automation

    params:
        - current_user (str): Get the current user from the token automatically
        - automation_id (str): The unique id of automation which should be copied
        - name (str | None): The name of automation if required else copied automation name "_copy" is considered
        -  data_segments (list | None): The unique id of data segments that should be linked to the automation that is copied
                                        else there will be no automations assigned
        - college (dict): Get the college details based on college id

    raises:
        -  HTTPException: An error occurred with status code 404 when automation not found by automation_id.
        - ObjectIdInValid: An error occurred when automation_id is wrong.

    return:
        - dict - message that automation copied
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        await nested_automation_helper().copy_automation(automation_id, name,
                                                         data_segments, user)
        return {"message": "Copied Automation Successfully!"}
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500,
                            detail=f"An error occur when copying automation.Error -  {error}")


@nested_automation_router.post("/communication_data/",
                               summary="Get automation communication data")
@requires_feature_permission("read")
async def get_automation_communication_data(
        current_user: CurrentUser,
        automation_id: str = Query(...,
                                   description="Enter automation id."),
        email: bool = Query(False,
                            description="A boolean value True which useful for"
                                        " get email communication data"),
        sms: bool = Query(False,
                          description="A boolean value True which useful for"
                                      " get sms communication data"),
        whatsapp: bool = Query(False,
                               description="A boolean value True which useful "
                                           "for get sms communication data"),
        college: dict = Depends(get_college_id),
):
    """
    Get automation communication data.

    Params:\n
        - college_id (str): An unique identifier of a college which useful for
            get college details
        - automation_id (str | None): Either None or An unique identifier of
            automation which useful for get automation communication data.
        - email (bool): Default value: False. A boolean value True which useful
            for get email communication data.
        - sms (bool): Default value: False. A boolean value True which useful
            for get sms communication data.
        - whatsapp (bool): Default value: False. A boolean value True which
            useful for get whatsapp communication data.
    
    Returns:\n
        - dict: A dictionary which contains automation communication data.
    
    Raises:\n
        - 401: An error occurred with status code 401 when unauthorized user
            try to get automation top bar details.
        - ObjectIdInValid: An error which occurred when automation id will
            be wrong.
        - DataNotFoundError: An error occurred when automation not found by id.
        - Exception: An error occurred with status code 500 when something
            wrong happen in the backend code.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return {"data": await nested_automation_helper().get_automation_communication_data(
            automation_id, email, sms, whatsapp),
                "message": "Get the automation communication data."}
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"An error occurred when get the "
                                    f"automation top bar details. "
                                    f"Error - {error}")


@nested_automation_router.post("/top_bar_details/",
                               summary="Get automation top bar data.")
@requires_feature_permission("read")
async def get_automation_top_bar_details(
        current_user: CurrentUser,
        automation_id: str = Query(description="Enter automation id."),
        date_range: DateRange | None = Body(None),
        college: dict = Depends(get_college_id)
):
    """
    Get automation top bar details.
    
    Params:\n
        - college_id (str): An unique identifier of a college which useful for
            get college details
        - automation_id (str): An unique identifier of automation which useful
            for get automation.
    
    Request body params:\n
        - date_range (DateRange | None): Either None or get the date range
            for get data based on date_range.
    
    Returns:\n
        - dict: A dictionary which contains automation top bar details.
    
    Raises:\n
        - 401: An error occurred with status code 401 when unauthorized user
            try to get automation top bar details.
        - ObjectIdInValid: An error which occurred when automation id will
            be wrong.
        - DataNotFoundError: An error occurred when automation not found by id.
        - Exception: An error occurred with status code 500 when something
            wrong happen in the backend code.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return {"data": await nested_automation_helper().get_automation_top_bar_details(
            automation_id=automation_id, date_range=date_range),
                "message": "Get the automation top bar details."}
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"An error occurred when get the "
                                    f"automation top bar details. "
                                    f"Error - {error}")


@nested_automation_router.get("/get_data_by_id/",
                              summary="Get the automation data by id")
@requires_feature_permission("read")
async def get_automation_data_by_id(
        current_user: CurrentUser,
        automation_id: str = Query(description="Enter automation id."),
        college: dict = Depends(get_college_id)
):
    """
    Get automation data by id.

    Params:\n
        - college_id (str): An unique identifier of a college which useful for
            get college details.
        - automation_id (str): An unique identifier of automation which useful
            for get automation data.

    Returns:\n
        - dict: A dictionary which contains automation data.

    Raises:\n
        - 401: An error occurred with status code 401 when unauthorized user
            try to get automation data by id.
        - Exception: An error occurred with status code 500 when something
            wrong happen in the backend code.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return {"data": await nested_automation_helper().
        get_automation_data_by_id(automation_id, college.get("id")),
                "message": "Get the automation data by id."}
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"An error occurred when get the "
                                    f"automation data by id. Error - {error}")
