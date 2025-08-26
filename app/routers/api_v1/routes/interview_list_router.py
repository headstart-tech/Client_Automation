"""
this file contains routers of interview list
"""
from typing import Union, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from meilisearch.errors import MeilisearchCommunicationError, \
    MeilisearchApiError

from app.core.custom_error import DataNotFoundError, UserLimitExceeded
from app.core.utils import utility_obj, logger, settings, requires_feature_permission
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import CurrentUser
from app.helpers.interview_module.get_interview_list_details import \
    Interview_list_details
from app.helpers.interview_module.interview_list_conf_aggregation import \
    Interview_aggregation
from app.helpers.interview_module.planner_configuration import Planner
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.interview_module_schema import search_interview_filter, \
    slot_time_update_schema

interview_list = APIRouter()


@interview_list.post(
    "/get_interview_list/",
    summary="Get interview list details",
    response_description="Get all interview details",
)
@requires_feature_permission("read")
async def get_all_interview_details(
        current_user: CurrentUser,
        search_input: Union[str, None] = Query(None,
                                               description="Enter "
                                                           "search pattern"),
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
        payload: search_interview_filter = None,
        interview_id: str = None,
        selected_status: str = None,
        sorted_order: str = None,
        sorted_type: str = None,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        client=Depends(utility_obj.get_meili_client),
):
    """
        Get all the interview details from the meili search

        params:
        - page_num (int): Required Field. Useful for show approval pending
                        applicants data on a particular page.
                        e.g., 1
        - page_size (int): Required field. Useful for show limited data on "
                          "particular page. e.g., 25
        - client (url): Depends on meili search url being authenticated
        - search_input: Search key and name email etc. from meili search
                        server.
        - current_user (str): Depends on current user being authenticated
        - interview_id (str): when we search student inside the application
                            used this interview id.
        - selected_status (str): when we search in the selected student
                                give the interview_status is "Selected"
        - interview_status (str): Get value from user Done, Slot Not Booked
        - gd_status (str): Get value from user Done, Slot Not Booked
        - secondary_score: (str) = Get value from user in integer
        - ug_score: Optional[str] = Get value from user in integer
        - interview_score: Optional[str] = Get value from user in integer
        - sorted_order (str) = Get value from user in ug_score,
                            interview_score and 12th_score
        - sorted_type (str) = Get value from user in sorted_type is asc and
                            desc, default value is desc.

    Returns:
        list: A list contains relevant application data.
    """
    await UserHelper().is_valid_user(current_user)
    if payload is None:
        payload = {}
    payload = jsonable_encoder(payload)
    filters = []
    if interview_id not in ["", None]:
        await utility_obj.is_id_length_valid(interview_id, "Interview_id")
        filters.append([f"interview_id = {interview_id}"])
    if selected_status not in ["", None]:
        filters.append([f"selection_status = {selected_status.title()}"])
    if payload.get("interview_status") not in ["", None]:
        filters.append(
            [f"interview_status = {payload.get('interview_status').title()}"])
    if payload.get("gd_status") not in ["", None]:
        filters.append([f"gd_status = {payload.get('gd_status')}"])
    if payload.get("ug_score") not in ["", None]:
        filters.append([f"ug_score >= {int(payload.get('ug_score'))}"])
    if payload.get("secondary_score") not in ["", None]:
        filters.append(
            [f"12th_score >= {int(payload.get('secondary_score'))}"])
    if payload.get("interview_score") not in ["", None]:
        filters.append(
            [f"interview_score >= {int(payload.get('interview_score'))}"])
    temp_dict = {
        'filter': filters,
        'showMatchesPosition': True,
        'attributesToHighlight': ['*'],
        'highlightPreTag': "<span class='search-query-highlight'>",
        'highlightPostTag': '</span>',
        'hitsPerPage': page_size,
        'page': page_num}
    if sorted_order is not None:
        if sorted_type is None:
            sorted_type = "desc"
        temp_dict.update({'sort': [f'{sorted_order}:{sorted_type}']})
    name = (f"{settings.client_name.lower().replace(' ', '_')}"
            f"_{settings.current_season.lower()}")
    try:
        interview_list_record = client.index(f'{name}_interview_list').search(
            search_input, temp_dict)

        return {"data": interview_list_record.get('hits'),
                'total': interview_list_record.get("totalHits"),
                "count": interview_list_record.get('hitsPerPage'),
                "page_num": interview_list_record.get('page'),
                "message": "Fetched interview records successfully"}
    except MeilisearchCommunicationError as error:
        logger.error(f"Error - {str(error.args)}")
        raise HTTPException(status_code=404,
                            detail="Meilisearch server is not running.")
    except MeilisearchApiError as error:
        logger.error(f"Error - {str(error.args)}")
        raise HTTPException(status_code=404, detail=str(error.args))
    except Exception as e:
        logger.error(f"Error - {str(e.args)}")
        raise HTTPException(status_code=404, detail=str(e.args))


@interview_list.post(
    "/get_interview_header/",
    summary="Get interview list header",
    response_description="Get all interview header",
)
@requires_feature_permission("read")
async def get_all_interview_header(
        current_user: CurrentUser,
        search_input: str = Query(None, description="Enter search pattern"),
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
        interview_status: Union[str, None] = Query(None,
                                                   description="Enter the "
                                                               "status of "
                                                               "interview"),
        slot_type: Union[str, None] = Query(None),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        client=Depends(utility_obj.get_meili_client),
):
    """
        Get all the interview list header details from the meili search server.

        params:
        - page_num (int): Required Field. Useful for show approval pending
                        applicants data on a particular page.
                        e.g., 1
        - page_size (int): Required field. Useful for show limited data on "
                          "particular page. e.g., 25
        - client (url): Depends on meili search url being authenticated
        - search_input: Search key and name email etc. from meili search
                        server.
        - interview_status (str): interview status will be Archived, Closed,
                                    Active
        - slot_type (str): slot type will be GD, PI, None
        - current_user (str): Depends on current user being authenticated

    Returns:
        list: A list contains relevant application data.
    """
    filter = []
    if interview_status is None:
        filter.append([f"status!=Archived"])
    else:
        filter.append([f"status = {interview_status.title()}"])
    await UserHelper().is_valid_user(current_user)
    try:
        if search_input is None:
            return await Interview_aggregation().get_gd_pi_details(
                page_num=page_num,
                page_size=page_size,
                interview_status=interview_status,
                slot_type=slot_type
            )
        name = (f"{settings.client_name.lower().replace(' ', '_')}"
                f"_{settings.current_season.lower()}")
        interview_list_record = client.index(
            f'{name}_interview_header').search(
            search_input, {
                'filter': filter,
                'showMatchesPosition': True,
                'attributesToHighlight': ['*'],
                'highlightPreTag': "<span class='search-query-highlight'>",
                'highlightPostTag': '</span>',
                'hitsPerPage': page_size,
                'page': page_num})

        return {"data": interview_list_record.get('hits'),
                'total': interview_list_record.get("totalHits"),
                "count": interview_list_record.get('hitsPerPage'),
                "page_num": interview_list_record.get('page'),
                "message": "Fetched interview header record successfully"}
    except MeilisearchCommunicationError as error:
        logger.error(f"Error - {str(error.args)}")
        raise HTTPException(status_code=404,
                            detail="Meilisearch server is not running.")
    except MeilisearchApiError as error:
        logger.error(f"Error - {str(error.args)}")
        raise HTTPException(status_code=404, detail=str(error.args))
    except Exception as e:
        logger.error(f"Error - {str(e.args)}")
        raise HTTPException(status_code=404, detail=str(e.args))


@interview_list.get("/unassigned_application")
@requires_feature_permission("read")
async def unassigned_students(
        request: Request,
        current_user: CurrentUser,
        application_id: str = Query(
            None, description="Optional field. A unique identifier/id of "
                              "an application."),
        panelist_id: str = Query(
            None, description="Optional field. A unique identifier/id of "
                              "an panelist."),
        slot_id: str = Query(description="Required field. A unique "
                                         "identifier/id of a slot."),
        college: dict = Depends(get_college_id)
):
    """
    Unassigned/Remove applicant/panelist from a slot.

    Params:
        application_id (str): Optional field. A unique identifier/id of
            applicant for get application data.
            e.g., 123456789012345678901234
        panelist_id (str): Optional field. A unique identifier/id of
            panelist for get panelist data.
            e.g., 123456789012345678901231
        slot_id (str): Required field. A unique identifier/id of
            a slot for get slot data. e.g., 123456789012345678901232
        college_id (str): Required field. A unique identifier/id of
            a college for get college data. e.g., 123456789012345678901230

    Returns:
        dict: A dictionary which contains unassigned applicants'/panelist info.

    Raises:
        422 (Invalid data): Raise error with status code 422 at
            invalid condition.
        404 (DataNotFoundError) - Raises error with status code 404 when
            data not found.
        500 (Internal Server Error) - Raises error with status code 500 when
            internal error occurred.
    """
    user = await UserHelper().is_valid_user(current_user)
    if application_id:
        _id, name = application_id, "Application id"
    elif panelist_id:
        _id, name = panelist_id, "Panelist id"
    else:
        raise HTTPException(status_code=422,
                            detail="Either application or panelist id "
                                   "required.")
    await utility_obj.is_id_length_valid(_id, name)
    await utility_obj.is_id_length_valid(slot_id, "Slot id")
    try:
        return await Interview_list_details().unassigned_applicant_from_slot(
            application_id, panelist_id, slot_id, college, user, request)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An internal error"
                                                    f" occurred: {error}")


@interview_list.post("/reschedule_interview")
@requires_feature_permission("edit")
async def reschedule_interview_application(
        current_user: CurrentUser,
        origin_slot_id: str,
        reschedule_slot_id: str,
        application_id: str
):
    """
        Get all the interview list header details from the meili search server.

        params:
        - current_user (str): Depends on current user being authenticated
        - slot_id (str): unique identifier for slot collection
        - reschedule_slot_id (str): unique identifier for slot collection
        - application_id (str): unique identifier for application

    Returns:
        Response: Interview has been rescheduled.
    """
    await UserHelper().is_valid_user(current_user)
    await utility_obj.is_id_length_valid(origin_slot_id, "Slot id")
    await utility_obj.is_id_length_valid(reschedule_slot_id,
                                         "reschedule_slot_id")
    await utility_obj.is_id_length_valid(application_id, "Application id")
    try:
        return await Interview_list_details().get_rescheduled_interview_list(
            origin_slot_id=origin_slot_id,
            reschedule_slot_id=reschedule_slot_id,
            application_id=application_id)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except UserLimitExceeded as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Internal server "
                                                    f"Error - {str(error)}")


@interview_list.put("/assign_application/panelist")
@requires_feature_permission("edit")
async def get_assign_application_panelist(
        request: Request,
        current_user: CurrentUser,
        slot_id: str,
        application_id: Optional[str] = None,
        panelist_id: Optional[str] = None,
        college: dict = Depends(get_college_id)
):
    """
    Assign applicant/panelist to the slot. After assign slot user will get
        interview details through mail.

    Params:
        - slot_id (str): Either None or a unique identifier of slot.
            e.g., 123456789012345678901234
        - application_id (str | None): Optional field. Either None or a unique
            identifier of application. e.g., 123456789012345678901222
        - panelist_id (str | None): Optional field. Either None or a unique
            identifier of panelist. e.g., 123456789012345678901233
        - college_id (str): Required field. A unique identifier of panelist.
            e.g., 123456789012345678901211

    Returns:
        dict: A dictionary which contains information about slot assigned to
            user.
    """
    user = await UserHelper().is_valid_user(current_user)
    await utility_obj.is_id_length_valid(slot_id, "Slot_id")
    slot_data = await Planner().get_slot_data(slot_id)
    if application_id:
        await utility_obj.is_id_length_valid(application_id, "Application_id")
    elif panelist_id:
        await utility_obj.is_id_length_valid(panelist_id, "Panelist id")
    else:
        raise HTTPException(
            status_code=422, detail="Application or panelist is must be "
                                    "required.")
    try:
        action_type = "counselor" if user.get("role", {}).get("role_name") == "college_counselor" else "system"
        return await Interview_list_details().get_assign_application(
            slot_data=slot_data, current_user=current_user, college=college,
            request=request, application_id=application_id, panelist_id=panelist_id,
            action_type=action_type)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Internal server "
                                                    f"Error - {str(error)}")


@interview_list.put("/slot_time_management")
@requires_feature_permission("edit")
async def slot_time_manage(
        current_user: CurrentUser,
        payload: slot_time_update_schema,
):
    """
        Modify the slot time management.

        params:
        - current_user (str): Depends on current user being authenticated
        - slot_id (str): unique identifier of the slot id
        - panel_id (str): unique identifier of the application id
        - slot_duration (int): Get slot duration in minutes.
        - gap_between_slot (int): Get the slot gap in minutes

    Returns:
        Response: panel has been updated.
    """
    if payload is None:
        payload = {}
    payload = jsonable_encoder(payload)
    await UserHelper().is_valid_user(current_user)
    await utility_obj.is_id_length_valid(payload.get("panel_id"), "Panel id")
    for slot in payload.get("updated_slot", []):
        await utility_obj.is_id_length_valid(slot.get("slot_id"), "Slot id")
    try:
        return await Interview_list_details().panel_time_management(
            payload)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Internal server "
                                                    f"Error - {str(error)}")
