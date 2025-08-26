"""
This file contains API routes related to planner module
"""
import calendar

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks, \
    Request

from app.core.custom_error import ObjectIdInValid, DataNotFoundError
from app.core.log_config import get_logger
from app.core.utils import utility_obj, requires_feature_permission
from app.database.aggregation.planner import PlannerAggregation
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import CurrentUser
from app.helpers.interview_module.planner_configuration import planner_obj
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.interview_module_schema import SlotsPanels, MonthWiseSlots
from app.models.planner_module_schema import Panel, Slot, slotPanelFilters, \
    getSlotPanelFilter, getPanelNames

planner_module = APIRouter()
logger = get_logger(name=__name__)


@planner_module.post("/create_or_update_panel/",
                     summary="Create or update panel")
@requires_feature_permission("write")
async def create_or_update_panel(
        panel_data: Panel, current_user: CurrentUser,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        panel_id: str = Query(None, description="Enter panel id if updating "
                                                "an existing panel")):
    """
    Either create a new panel or update existing panel depending on whether
    the panel_id is provided.

    Params:\n
        panel_data (dict): A data which useful for create/update panel.\n
        college_id (str): An unique id for get college data.\n
        panel_id (str): An unique id for update panel data.

    Returns:
        dict: A dictionary which contains create/update panel data info.
    """
    panel_data = {key: value for key, value in panel_data.model_dump().items()
                  if value is not None}
    return await planner_obj.create_or_update_panel(current_user, panel_data,
                                                    panel_id)


@planner_module.post("/create_or_update_slot/",
                     summary="Create or update slot")
@requires_feature_permission("write")
async def create_or_update_slot(
        slot_data: Slot, current_user: CurrentUser,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        slot_id: str = Query(None, description="Enter slot id if updating an"
                                               " existing slot")):
    """
    Either create a new slot or update existing slot depending on whether the
     slot_id is provided.

    Params:\n
        slot_data (dict): A data which useful for create/update slot.\n
        college_id (str): An unique id for get college data.\n
        slot_id (str): An unique id for update slot data.

    Returns:
        dict: A dictionary which contains create/update slot data info.
    """
    slot_data = {key: value for key, value in slot_data.model_dump().items() if
                 value is not None}
    return await planner_obj.create_or_update_slot(current_user, slot_data,
                                                   slot_id)


@planner_module.get(
    "/slot/get_data_by_id/", response_description="Get slot details"
)
@requires_feature_permission("read")
async def get_slot_details(
        current_user: CurrentUser,
        slot_id: str,
        college_id: dict = Depends(get_college_id_short_version(short_version=True)), ):
    """
        get slot details

        Params:\n
            slot_id (str): An unique id (Slot id)
            college_id (str): An unique id for get college data.

        Returns:
            dict: A dictionary which contains slot data info
        """
    return await planner_obj.get_slot_details_by_id(current_user, slot_id)


@planner_module.get(
    "/panel/get_data_by_id/", response_description="Get panel details"
)
@requires_feature_permission("read")
async def get_panel_details(
        current_user: CurrentUser,
        panel_id: str,
        college_id: dict = Depends(get_college_id_short_version(short_version=True)), ):
    """
        get panel details

        Params:\n
            panel_id (str): An unique id (Panel id)
            college_id (str): An unique id for get college data.

        Returns:
            dict: A dictionary which contains panel data info
        """
    return await planner_obj.get_panel_details_by_id(current_user, panel_id)


@planner_module.post(
    "/calender_info/",
    response_description="Get date wise information of PI/GD"
)
@requires_feature_permission("read")
async def get_calender_info(
        current_user: CurrentUser,
        filters: dict,
        month: int = Query(
            description="Enter month in MM format ie, an integer value eg:12",
            ge=1, le=12),
        year: int = Query(
            description="Enter year in YYYY format ie, an integer value "
                        "eg:2023", ge=2000, lt=10000),
        college_id: dict = Depends(get_college_id_short_version(short_version=True)),):
    """
    Get day wise PI/GD information for given month and year
    Also consider the filter given and change the result value

    Params:\n
        month(int): Month required
        year(int): year required
        college_id (str): An unique id for get college data.

        filters (dict) : all the filters. These may include
              filter_slot, slot_status, moderator, program_name, slot_state

    Returns:
       result (list): contains multiple dictionaries with information of PI/GD
    """
    filter_slot = filters.get("filter_slot")
    slot_status = filters.get("slot_status")
    moderator = filters.get("moderator")
    program_name = filters.get("program_name")
    slot_state = filters.get("slot_state")
    try:
        is_valid = await UserHelper().is_valid_user(user_name=current_user)
        if not is_valid:
            return {"error": "Invalid user"}
        result = []
        num_days_in_month = calendar.monthrange(year, month)[1]
        for date in range(1, num_days_in_month + 1):
            details = await planner_obj.get_pi_gd_details_per_day(
                date, month, year, filter_slot, slot_status, moderator,
                program_name, slot_state)
            result.append(details)
        return result
    except Exception as e:
        logger.error(f"Error in get_calender_info: {e}")
        return {"error": f"An error occurred while fetching the calendar "
                         f"info {e} "}


@planner_module.post(
    "/day_wise_slot_panel_data/",
    response_description="Get day-wise slots and panels data"
)
@requires_feature_permission("read")
async def day_wise_slot_panel_data(
        current_user: CurrentUser,
        slot_panel_filters: slotPanelFilters = None,
        college_id: dict = Depends(get_college_id_short_version(short_version=True)),
        date: str = Query(
            None, description="Enter date in the format %Y-%m-%d"),
):
    """
    Get day wise slots and panels data along with next day.
    By default, current date and next date slots/panels data can get.
    Want particular date slots and panels data, then pass date in the format
    %Y-%m-%d.

    Params:
        - college_id (str): An unique id for get college data.
            For example, 123456789012345678901211
        - date (str): Optional field. Useful for get particular date slots
            and panels data.
             For example, 2023-12-31.

    Request body parameters:
        - slot_panel_filters (slotPanelFilters): An object of pydantic class
            `slotPanelFilters` which contains the following fields:
            - filter_slot (list[str] | None): Optional field.
                Default value: None. A list which can contains slot type.
                Possible types: GD, PI.
            - slot_status (list[str] | None): Optional field.
                Default value: None. A list which can contains status of slot
                Possible values: Available, Booked
            - moderator (list[str] | None): Optional field.
                Default value: None. A list which can contains unique
                identifier/id of moderator.
                e.g., ["123456789012345678901234", "123456789012345678901214"]
            - slot_state (str | None): Optional field. Default value: None.
                State of a slot. Possible values: Published, Not Published.
            - program_name (list): Optional field. Default value: None.
                A list which contains course_name and specialization_name.
                e.g., ["course_name": "B.Sc.",
                    "specialization_name": "Physical Assistant."]

    Returns:
       dict: A dictionary which contains info about day wise slots and panels
       data.
    """
    if slot_panel_filters:
        slot_panel_filters = slot_panel_filters.model_dump()
    else:
        slot_panel_filters = {}
    return {
        "data":
            await planner_obj.day_wise_slots_and_panels_data(
                current_user, date, slot_panel_filters),
        "message": "Get day-wise slots and panels data."}


@planner_module.post(
    "/take_a_slot/",
    response_description="Take a slot based on id."
)
@requires_feature_permission("write")
async def take_a_slot(
        request: Request,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
        slot_id: str = Query(
            description="Required field. An unique identifier/id of slot. "
                        "Useful for take a particular slot."),
        application_id: str = Query(
            None, description="Optional field. An unique identifier/id of "
                              "slot. Required when student try to "
                              "take a slot."),
        is_student: bool = Query(
            False, description="Optional field. Default value will be false. "
                               "Send True if student try to take slot"),
):
    """
    Panelist/Student can accept/take the slot.

    Params:\n
        college_id (str): Required field.
            An unique identifier of college for get college data.
            For example, 123456789012345678901211
        slot_id (str): Required field. An unique identifier/id of slot. "
                        "Useful for take a particular slot.
             For example, 123456789012345678901212.
         application_id (str): Optional field. An unique identifier/id of "
                              "slot. Required when student try to "
                              "take a slot.
             For example, 123456789012345678901214.
             Send application id when student try to take slot.
         is_student (bool): Optional field. By default, value will be false.
            Send True if student try to take slot.

    Returns:
       dict: A dictionary which contains accept/take slot info.
    """
    return await planner_obj.take_a_slot(
        current_user.get("user_name"), slot_id, is_student, application_id, college, request)


@planner_module.put("/publish_slots_or_panels/",
                    summary="Publish slots or panels")
@requires_feature_permission("write")
async def publish_slots_or_panels(
        request: Request,
        current_user: CurrentUser,
        payload: SlotsPanels = None,
        date: str | None = Query(
            None, description="Optional field. Date format: YYYY-MM-DD. "
                              "Useful for publish slots or panels of a "
                              "specified date.",
            example="1999-12-31"),
        college: dict = Depends(get_college_id)):
    """
    Publish slots or panels based on ids. Able to publish specified date slots
    and panels if date specified/provided.

    Params:
        _ college_id (str): An unique identifier/id of college for retrieve
            college data.
        - date (str | None): Optional field. Date format: YYYY-MM-DD.
            Useful for publish slots or panels of a specified date.

    Request body parameters:
        - payload (SlotsPanels): Optional. Default value: None.
            An object of pydantic class `SlotsPanels` which contains the
            following fields:

            - slots_panels_ids (list[str]): Optional field.
                A list which can contains slots or panels ids when want to
                publish.
                e.g., ["123456789012345678901212", "123456789012345678901213"]

    Returns:
          dict: A dictionary contains info about publish slots or panels.
    """
    if payload is None:
        payload = {}
    payload = dict(payload)
    return await planner_obj.publish_slots_or_panels(
        current_user, payload, date, request, college)


@planner_module.get("/profile_marking_details/",
                    summary="Student profile and marking details")
@requires_feature_permission("read")
async def profile_marking_details(
        current_user: CurrentUser,
        season:str =None,
        slot_id: str = Query(...,
                             description="Id of a application "
                                         "**6223040bea8c8768d96d3880**"
                             ),
        college: dict = Depends(get_college_id_short_version(short_version=True)),):
    """
    Details of student profile and details of marking scheme
    Params:\n
        slot_id (str) : the id of the slot
        college_id (dict): get college data as a dict format.
                hint, {"_id": 117654, etc...}\n
        current_user: Current user which is retrieve data call this API.
    Returns:
        result(dict) : student details and marking schema
    """
    await UserHelper().is_valid_user(user_name=current_user)
    await utility_obj.is_id_length_valid(slot_id, "Slot id")
    try:
        result = await planner_obj.display_profile_marking(slot_id,season=season)
    except DataNotFoundError as e:
        logger.error(f"{e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An internal error occurred: {e}")
    return result


@planner_module.post("/month_wise_slots_info/")
@requires_feature_permission("read")
async def month_wise_slots_info(
        current_user: CurrentUser,
        month_wise_slots_data: MonthWiseSlots,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get month wise slots info with/without filter according to program.

    Params:
        - college_id (dict): Required Field. An unique identifier/id of
            college. Useful for get college data.
            e.g., 123456789012345678901234

    Request body parameters:
        - month_wise_slots_data (MonthWiseSlots): An object of pydantic class
            `MonthWiseSlots` which contains the following fields:

            - application_id (str): Required field.
                A unique identifier/id of application.
                e.g., 123456789012345678901212
            - location (list[str] | None): Optional field. Default value: None.
                Location can be based on city.
                e.g., Pune.
            - month (int | None) - Optional field. Default value: None.
                Month format will be `MM` format as an integer value
                Possible values: Between 1 and 12.

    Returns:
        dict: A dictionary which contains month-wise slots data.
    """
    month_wise_slots_data = month_wise_slots_data.model_dump()
    try:
        return {
            "data":
                await planner_obj.month_wise_slots_info(
                    month_wise_slots_data),
            "message": "Get month-wise slots data."}
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500,
                            detail="Get error while fetching month-wise "
                                   f"slots data. Error - {error}")


@planner_module.post("/invite_student_to_meeting/")
@requires_feature_permission("write")
async def invite_student_to_meeting(
    request: Request,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id),
    slot_id: str = Query(
        description="Required field. An unique identifier/id of a slot."),
    application_id: str = Query(
        description="Required field. An unique identifier/id of "
                    "an application.")
):
    """
    Invite student for meeting through mail.

    Params:
        - college_id (dict): Required Field. A unique identifier/id of
            college. Useful for get college data.
            e.g., 123456789012345678901234
        - slot_id (dict): Required Field. A unique identifier/id of a slot.
            e.g., 123456789012345678901212
        - application_id (dict): Required Field. An unique identifier/id of
            application. Useful for get student data.
            e.g., 123456789012345678901222

    Returns:
        dict: A dictionary which contains invite student mail info.
    """
    user = await UserHelper().is_valid_user(current_user)
    slot_data = await planner_obj.get_slot_data(slot_id)
    try:
        action_type = "counselor" if user.get("role", {}).get("role_name") == "college_counselor" else "system"
        return await planner_obj.invite_student_to_meeting(
            slot_data, application_id, request, college, action_type=action_type)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        logger.error(f"Something went wrong while sending interview mail to "
                     f"student. Error - {str(error)}")
        raise HTTPException(
            status_code=500, detail="Something went wrong while sending "
                                    "interview mail to student. "
                                    f"Error - {str(error)}")


@planner_module.get("/student_profile/",
                    summary="Student profile")
@requires_feature_permission("read")
async def student_profile(
        current_user: CurrentUser,
        interview_list_id: str = Query(
            description="Id of a interview list **6223040bea8c8768d96d3880**"),
        application_id: str = Query(
            description="Id of a application **6223040bea8c8768d96d3880**"),
        season: str = None,
        college_id: dict = Depends(get_college_id_short_version(short_version=True)),):
    """
    Details of student
    Params:\n
        interview_list_id (str) : the id of the interview list
        application_id (str) : the id of the application
        college_id (dict): get college data as a dict format.
                hint, {"_id": 117654, etc...}\n
        current_user: Current user which is retrieve data call this API.
    Returns:
        result(dict) : student details
    """
    await UserHelper().is_valid_user(user_name=current_user)
    await utility_obj.is_id_length_valid(application_id, "Application id")
    await utility_obj.is_id_length_valid(interview_list_id, "InterviewList id")
    try:
        result = await planner_obj.display_student_profile(
            application_id, interview_list_id,season=season)
    except DataNotFoundError as e:
        logger.error(f"{e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An internal error occurred: {e}")
    return result


@planner_module.post("/unassign_applicants_from_slots/",
                     summary="Un-assign all applicants from given slots")
@requires_feature_permission("edit")
async def unassign_applicants_of_slots(
        request: Request,
        current_user: CurrentUser,
        slots_ids: list[str],
        college_id: dict = Depends(get_college_id)
):
    """
    Un-assign/Remove all applicants of given slots.

    Params:
        slots_ids (list(str)): Required field. A list which contains unique
            identifiers/ids of slots.
            e.g., ["123456789012345678901232", "123456789012345678901211"]
        college_id (str): Required field. A unique identifier/id of
            a college for get college data. e.g., 123456789012345678901222

    Returns:
        dict : {"message": "All applicants are unassigned from given slots."}

    Raises:
        401 (NoPermission) - Raise error with status code 401 when
            user don't have enough access to perform action.
        404 (DataNotFoundError) - Raise error with status code 404 when
            data not found.
        500 (Internal Server Error) - Raise error with status code 500 when
            internal error occurred.
    """
    user = await UserHelper().is_valid_user(current_user)
    try:
        result = await planner_obj.remove_all_applicants_from_slots(
            slots_ids, college_id, user, request)
        return result
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An internal error"
                                                    f" occurred: {error}")


@planner_module.get("/date_wise_panel_slot_hours/",
                    summary="Date wise panels slots and hours count ")
@requires_feature_permission("read")
async def panel_slot_hours(
        current_user: CurrentUser,
        is_slot: bool,
        date: str = Query(description="Enter date in the format %d/%m/%Y"),
        college_id: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    returns date wise panel slot hours details
    Params:\n
        is_slot(bool): If true send slot data else send panel data.
        college_id (dict): get college data as a dict format.
                hint, {"_id": 117654, etc...}\n
        current_user: Current user which is retrieve data call this API.
        date (str):  Useful for get particular date slots
            and panels data.
             For example, 31/12/2023.
    Returns:
        result(dict) : date wise details
    """
    await UserHelper().is_valid_user(user_name=current_user)
    try:
        result = await planner_obj.panels_slots_hours(date, is_slot)
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An internal error occurred: {e}")
    return result


@planner_module.post("/get_slot_or_panel_data/",
                     summary="Get slot or panel data based on id.")
@requires_feature_permission("read")
async def get_slot_or_panel_data_based_on_id(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        slot_or_panel_id: str = Query(description="Enter slot or panel id."),
        filter_slot_panel: getSlotPanelFilter = None,
        page_num: None | int = Query(
            None, description="Page number will be only useful for "
                              "show applicants data."),
        page_size: None | int = Query(
            None, description="Page size will be only useful for "
                              "show limited applicants data.")
):
    """
    Get slot or panel data by id.

    Params:
        - college_id (dict): Required Field. An unique identifier/id of
            college. Useful for get college data.
            e.g., 123456789012345678901234
        - slot_or_panel_id (dict): Required Field. An unique identifier/id of
            a slot or panel. e.g., 123456789012345678901212
        - page_num (int | None): Optional field. Default value - None.
            Page number will be only useful for show applicants data.
            e.g., 1
        - page_size (int | None): Page size means how many data you want to
                show on page_num. e.g., 25

    Request body parameters:
        - filter_slot_panel (getSlotPanelFilter): An object of pydantic class
            `getSlotPanelFilter` which contains the following fields:
            - search_by_applicant (str | None): Useful for search applicants
                by name (first_name / last_name).
            - search_by_panelist (str | None): Useful for search panelists
                by name (first_name / last_name).
            - sort_by_twelve_marks (bool | None): Useful for sort applicants
                by twelve score. Possible values: True or false. True

    Returns:
        dict: A dictionary which contains information about slot/panel along
            with available panelist and applicants.
    """
    await UserHelper().is_valid_user(user_name=current_user)
    if filter_slot_panel:
        filter_slot_panel = filter_slot_panel.model_dump()
    else:
        filter_slot_panel = {}
    try:
        return await planner_obj.get_slot_or_panel_data_based_on_id(
            slot_or_panel_id, filter_slot_panel, page_num, page_size)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as e:
        logger.error(f"{e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An internal error occurred: {e}")


@planner_module.post("/get_panel_names/",
                     summary="Get panel names with/without filters.")
@requires_feature_permission("read")
async def get_panel_names(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        filters: getPanelNames = None
):
    """
    Get panel names with/without filters.

    Params:
        - college_id (dict): Required Field. An unique identifier/id of
            college. Useful for get college data.
            e.g., 123456789012345678901234

    Request body parameters:
        - filters (getPanelNames): An object of pydantic class
            `getPanelNames` which contains the following fields:
            - interview_list_id (str | None): Either None or a string which
                contains unique identifier/id of interview_list which can be
                 useful for get panel names based on interview list.
            - start_time (str | None): Either None or a start time of a panel
                which come along with field `end_time` which can useful for
                get panel names based on time.
            - end_time (bool | None): Either None or a end time of a panel
                which come along with field `start_time` which can useful for
                get panel names based on time.
            - slot_type (str | None): Either None or a string which contains
                type of slot. Possible values: GD, PI.

    Returns:
        dict: A dictionary which contains information about panel names.
    """
    await UserHelper().is_valid_user(user_name=current_user)
    if filters:
        filters = filters.model_dump()
    else:
        filters = {}
    try:
        return {"data": await PlannerAggregation().get_panel_names(filters),
                "message": "Get panel names."}
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as e:
        logger.error(f"{e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An internal error occurred: {e}")
