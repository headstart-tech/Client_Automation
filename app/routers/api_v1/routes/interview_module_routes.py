"""
This file contains API routes related to interview module
"""
import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks, \
    Request
from fastapi.encoders import jsonable_encoder

from app.core.custom_error import ObjectIdInValid, DataNotFoundError, \
    CustomError
from app.core.utils import utility_obj, logger, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id
from app.dependencies.oauth import CurrentUser
from app.helpers.interview_module.get_interview_list_details import \
    Interview_list_details
from app.helpers.interview_module.hod_helper_configuration import \
    hod_helper
from app.helpers.interview_module.interview_list_configuration import \
    interview_list_obj
from app.helpers.interview_module.selection_procedure_configuration import \
    selection_procedure_obj
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.interview_module_schema import SelectionProcedure, \
    InterviewList, GetInterviewListApplications, Interview_view_list, \
    InterviewStatus, SlotsPanels, FeedBackSchema, \
    InterviewListSelectedApplications

interview_module = APIRouter()


@interview_module.post("/create_or_update_selection_procedure/",
                       summary="Create selection procedure for course")
@requires_feature_permission("write")
async def create_or_update_selection_procedure(
        selection_procedure_data: SelectionProcedure,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
        procedure_id: str = Query(None, description="Enter procedure id if "
                                                    "want to create/update "
                                                    "selection procedure"
                                                    " data")):
    """
    Create or update selection procedure for course.
    Selection procedure will be based on specialization when there is
     specialization (s) available for course.

    Params:\n
        selection_procedure_data (dict): A data which useful for
         create/update selection procedure of course.\n
        college_id (str): An unique id for get college data.\n
        procedure_id (str): An unique id for update selection procedure
         of course.

    Returns:
        dict: A dictionary which contains create/update selection procedure
         data info.
    """
    selection_procedure_data = selection_procedure_data.model_dump()
    return await selection_procedure_obj.create_or_update_selection_procedure(
        current_user, selection_procedure_data,
        procedure_id)


@interview_module.delete("/delete_selection_procedure/",
                         summary="Delete selection procedure of course")
@requires_feature_permission("delete")
async def delete_selection_procedure(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
        procedure_id: str = Query(description="Enter procedure id if "
                                              "want to delete selection "
                                              "procedure data")):
    """
    Delete selection procedure of course.

    Params:\n
        college_id (str): An unique id for get college data.\n
        procedure_id (str): An unique id for update selection
         procedure of course.

    Returns:
        dict: A dictionary which contains delete selection procedure info.
    """
    return await selection_procedure_obj.delete_selection_procedure(
        current_user, procedure_id)


@interview_module.get("/get_selection_procedure/",
                      summary="Get selection procedure of course")
@requires_feature_permission("read")
async def get_selection_procedure(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
        procedure_id: str = Query(description="Enter procedure id if "
                                              "want to get selection "
                                              "procedure data")):
    """
    Get selection procedure of course.

    Params:\n
        college_id (str): An unique id for get college data.\n
        procedure_id (str): An unique id for update selection
        procedure of course.

    Returns:
        dict: A dictionary which contains get selection procedure info.
    """
    return await selection_procedure_obj.get_selection_procedure(current_user,
                                                                 procedure_id)


@interview_module.get("/selection_procedures/",
                      summary="Get selection procedures data")
@requires_feature_permission("read")
async def get_selection_procedures(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0)
):
    """
    Get selection procedures data based on page number and page size.

    Params:\n
        college_id (str): An unique id for get college data.\n
        page_num (int): Enter page number where want to show selection
         procedures data.\n
        page_size (int): Enter page size means how many data want to show
        on page_num.

    Returns:
        dict: A dictionary which contains selection procedures data.
    """
    return await selection_procedure_obj.get_selection_procedures(current_user,
                                                                  page_num,
                                                                  page_size)


@interview_module.post("/create_or_update_interview_list/",
                       summary="Create interview list")
@requires_feature_permission("write")
async def create_or_update_selection_procedure(
        interview_list_data: InterviewList,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
        interview_list_id: str = Query(None,
                                       description="Enter interview list "
                                                   "id if want to update "
                                                   "interview list data")):
    """
    Create or update interview list for program
        (course_name + specialization_name).
    Interview list will be based on specialization when there is
     specialization (s) available for course.

    Params:\n
        college_id (str): An unique id for get college data.\n
            e.g., 123456789012345678901233
        interview_list_id (str): An unique interview list id.
            e.g., 123456789012345678901232

    Request body parameters:
        interview_list_data (InterviewList): An object of
            pydantic class `InterviewList` which contains following fields:
            course_name (str): Required field. Name of a course.
                For example, B.Sc.
            specialization_name (str | None): Optional field.
                Default value: None. Name of a course.
                specialization. For example, Physician Assistant.
            list_name (str | None): Optional field. Default value: None.
                Name of a list. e.g., test.
            description (str | None): Optional field. Default value: None.
                Description of a list. e.g., test description.
            moderator_id (str | None): Optional field. Default value: None.
                A unique identifier/id of a moderator.
                e.g., 123456789012345678901231
            status (str | None): Optional field. Default value: None.
                Status of a list. e.g., Active
            pick_top (int | None): Optional field. Default value: None.
                Useful for get top applications data based on course and
                specialization name.
            filters (dict | None): Optional Field. Default value: None.
                A dictionary which contains filterable fields and their values.
                For example, {"remove_application_ids": [],
                "state_code": ["AP", "TN"], "city_name": [],
                "application_stage_name": "", "twelve_board": [],
                "pg_marks": [], "pg_university": [], "source_name": [],
                "exam_name": [], "twelve_marks": [], "ug_marks": [],
                "experience": [], "exam_score": [], "category": [],
                "nationality": [], "pg_marks_sort": None, "ug_marks_sort": None
                , "exam_score_sort": None, "exam_name_sort": None}.
            preference (list | None): Either None or a list which contains
                information about preference.

    Returns:
        dict: A dictionary which contains create/update interview list
         data info.
    """
    interview_list_data = {k: v for k, v in
                           interview_list_data.model_dump().items()
                           if v is not None}
    return await interview_list_obj.create_or_update_interview_list(
        current_user, interview_list_data,
        interview_list_id)


@interview_module.post("/add_students_into_list/",
                       summary="Add students into interview list")
@requires_feature_permission("write")
async def add_students_into_interview_list(
        current_user: CurrentUser, application_ids: list[str],
                                           interview_list_id: str = Query(
                                               description="Enter interview"
                                                           " list id"),
                                           college: dict = Depends(
                                               get_college_id)
                                           ):
    """
    Add students into interview list.

    Params:\n
        application_ids (list): A list which contains application ids
         in a string format.\n
        college_id (str): An unique id for get college data.\n
        interview_list_id (str): An unique interview list id.

    Returns:
        dict: A dictionary which contains add students related info.
    """
    return await interview_list_obj.add_students_into_interview_list(
        current_user, application_ids,
        interview_list_id)


@interview_module.post("/delete_students_from_list/",
                       summary="Delete students from interview list")
@requires_feature_permission("delete")
async def delete_students_from_interview_list(
        current_user: CurrentUser, application_ids: list[str],
                                              interview_list_id: str = Query(
                                                  description="Enter interview"
                                                              " list id"),
                                              college: dict = Depends(
                                                  get_college_id)
                                              ):
    """
    Delete students from interview list.

    Params:\n
        application_ids (list): A list which contains application ids in
         a string format.\n
        college_id (str): An unique id for get college data.\n
        interview_list_id (str): An unique interview list id.

    Returns:
        dict: A dictionary which contains delete students related info.
    """
    return await interview_list_obj.delete_students_from_interview_list(
        current_user, application_ids,
        interview_list_id)


@interview_module.put("_list/change_status_by_ids/",
                      summary="Change status of interview list by ids")
@requires_feature_permission("edit")
async def change_interview_list_by_ids(
        interview_list_ids: list[str],
        status: str,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)):
    """
    Change status of interview lists by ids.

    Params:\n
        interview_list_ids (list[str]): A list which contains
            interview list ids in a string format.
            For example, ["64b4d5036605c8470f4bb123",
                        "64b4d5036605c8470f4bb124"]\n
        college_id (str): An unique id for get college data.
            For example, 64b4d5036605c8470f4bb121\n
        status: A status want to update for interview lists.
            For example, Closed.

    Returns:
        dict: A dictionary which contains change status of interview list ids.
        Successful Response: {"message": "Interview lists status updated."}
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await interview_list_obj.update_status_of_interview_lists(
            current_user, interview_list_ids, status)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as e:
        logger.exception(
            f"An internal error occurred. Error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"An internal error occurred. Error: "
                                    f"{str(e)}")


# Todo: delete method not using because test client is not support json
#  keyword.
@interview_module.put("/delete_list/", summary="Delete Interview list")
@requires_feature_permission("delete")
async def delete_interview_list(current_user: CurrentUser,
                                interview_list_ids: list[str],
                                college: dict = Depends(get_college_id)):
    """
        Delete interview lists by interview_list_ids.

        Params:\n
            interview_list_ids (list[str]): A list which contains
                interview list ids in a string format.
                For example, ["64b4d5036605c8470f4bb123",
                            "64b4d5036605c8470f4bb124"]\n
            college_id (dict): get college data as a dict format.
                hint, {"_id": 117654, etc...}\n
            CurrentUser (str): The current user_name which is used to retrieve

        Returns:
            Successful Response: {"message": "Interview lists has been
             deleted."}
            Failure Response: {"message": "Interview lists not deleted."}
        """
    await UserHelper().is_valid_user(current_user)
    try:
        return await interview_list_obj.delete_interview_list(
            interview_list_ids)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An internal error"
                                                    f" occurred: {error}")


@interview_module.post("/download_interview_list/",
                       summary="Delete Interview list")
@requires_feature_permission("download")
async def download_interview_list(current_user: CurrentUser,
                                  interview_list_ids: list[str],
                                  interview_list_type: str = None,
                                  college: dict = Depends(get_college_id)):
    """
        download interview lists by interview_list_ids.

        Params:\n
            interview_list_ids (list[str]): A list which contains
                interview list ids in a string format.
                For example, ["64b4d5036605c8470f4bb123",
                            "64b4d5036605c8470f4bb124"]\n
            interview_list_type (str): The type of list to download grid
                    or detail
            college_id (dict): get college data as a dict format.
                hint, {"_id": 117654, etc...}\n
            CurrentUser (str): The current user_name which
            is used to retrieve

        Returns:
            Successful Response: {"message": "Interview lists download."}
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await interview_list_obj.download_interview_list(
            interview_list_ids,
            type=interview_list_type)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An internal error"
                                                    f" occurred: {error}")


@interview_module.post("/view_interview_detail/",
                       summary="View interview details by id")
@requires_feature_permission("read")
async def view_interview_list_by_id(
        current_user: CurrentUser,
        interview_list_id: str,
        payload: Interview_view_list = None,
        college: dict = Depends(get_college_id),
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0)):
    """
    View interview details by id.

    Params:\n
        interview_list_id str: A variable which contains
            interview id in a string format.
            For example, "64b4d5036605c8470f4bb123"\n
        college_id (dict): get college data as a dict format.
                hint, {"_id": 117654, etc...}\n
        current_user: Current user which is retrieve data call this API.

    Returns:
        Successful Response: {"message": "get interview list ."}
    """
    if payload is None:
        payload = {}
    else:
        payload = jsonable_encoder(payload)
    await UserHelper().is_valid_user(current_user)
    await utility_obj.is_id_length_valid(_id=interview_list_id,
                                         name="Interview list id")
    try:
        return await Interview_list_details().get_view_interview_list_detail(
            interview_list_id, payload=payload, page_num=page_num,
            page_size=page_size)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An internal error"
                                                    f" occurred: {error}")


@interview_module.get("/interview_list_header/",
                      summary="View interview list header")
@requires_feature_permission("read")
async def particular_interview_list_header(
        interview_list_id: str,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)):
    """
        Get interview list header by id.

        Params:\n
            interview_list_id str: A variable which contains
                interview id in a string format.
                For example, "64b4d5036605c8470f4bb123"\n
            college_id (dict): get college data as a dict format.
                    hint, {"_id": 117654, etc...}\n
            current_user: Current user which is retrieve data call this API.

        Returns:
            Successful Response: {"message": "get interview list header."}
    """
    await UserHelper().is_valid_user(current_user)
    await utility_obj.is_id_length_valid(_id=interview_list_id,
                                         name="Interview list id")
    try:
        return await Interview_list_details().get_interview_list_header_detail(
            interview_list_id)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An internal error"
                                                    f" occurred: {error}")


@interview_module.post("/download_view_interview_detail/",
                       summary="Download view interview details by id")
@requires_feature_permission("download")
async def download_view_interview_list_by_id(
        application_list_id: list[str],
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)):
    """
    Download view interview details by id.

    Params:\n
        application_list_id list(str): A variable which contains
            application id list in a string format.
            For example, "64b4d5036605c8470f4bb123"\n
        college_id (dict): get college data as a dict format.
                hint, {"_id": 117654, etc...}\n
        current_user: Current user which is retrieve data call this API.

    Returns:
        Successful Response: {"message": "view interview list downloaded."}
    """
    await UserHelper().is_valid_user(current_user)
    _id = [ObjectId(ids) for ids in application_list_id if
           await utility_obj.is_id_length_valid(ids, "Application id")]
    try:
        return await Interview_list_details(
        ).download_view_interview_list_detail(_id)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An internal error"
                                                    f" occurred: {error}")


@interview_module.get("/gd_pi_interview_list/")
@requires_feature_permission("read")
async def get_gd_pi_interview_list(
        current_user: CurrentUser,
        scope: str = None,
        college: dict = Depends(get_college_id),
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0)):
    """
        Get GD PI Interview list details.

        Params:\n
            college_id (dict): get college data as a dict format.
                    hint, {"_id": 117654, etc...}\n
            current_user: Current user which is retrieve data call this API.
            scope (str): if scope value is 'grid' showing grid type information
                        of gd pi interview details
            page_num (int ()): required the page number. ex-> 1,2,3
            page_size (int): required field limit of interview list.

        Returns:
            Successful Response: {"message": "get GD PI interview list ."}
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await interview_list_obj.get_gd_pi_interview_detail(
            scope=scope, page_num=page_num, page_size=page_size)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An internal error"
                                                    f" occurred: {error}")


@interview_module.post("_list/applications_data_based_on_program/")
@requires_feature_permission("read")
async def get_interview_list_applications_data_based_on_program(
        current_user: CurrentUser,
        payload: GetInterviewListApplications,
        college: dict = Depends(get_college_id),
        page_num: int = Query(
            gt=0,
            description="Required Field. Useful for show applications data "
                        "of program on a particular page. For example, 1"),
        page_size: int = Query(
            gt=0,
            description="Required field. Useful for show limited data on "
                        "particular page. For example, 25"
        )
):
    """
    Get interview list applicants data based on program with/without filters.
    For example, Program `B.Sc.` applicants data with/without data.

    Params:\n
        college_id (dict): Required Field. a unique identifier/id of college.
         Useful for get college data. For example, 123456789012345678901234
        page_num (int): Required Field. Useful for show applications data "
                        "of program on a particular page. For example, 1
        page_size (int): Required field. Useful for show limited data on "
                        "particular page. For example, 25

        Request body parameters:
        Payload (GetInterviewListApplications): An object of pydantic class
            `GetInterviewListApplications` which contains following fields:
            course_name (str): Required field. Name of a course.
                For example, B.Sc.
            specialization_name (str | None): Optional field.
                Default value: None. Name of a course
                specialization. For example, Physician Assistant.
            pick_top (int): Optional field. Default value: None.
                Useful for get top applications data based on course and
                specialization name.
            filters (dict): Optional Field. A dictionary which contains
                filterable fields and their values.
                For example, {"remove_application_ids": [],
                "state_code": ["AP", "TN"], "city_name": [],
                "application_stage_name": "", "twelve_board": [],
                "pg_marks": [], "pg_university": [], "source_name": [],
                "exam_name": [], "twelve_marks": [], "ug_marks": [],
                "experience": [], "exam_score": [], "category": [],
                "nationality": [], "pg_marks_sort": None, "ug_marks_sort": None
                , "exam_score_sort": None, "exam_name_sort": None}.
            preference (list | None): Either None or a list which contains
                information about preference.

    Returns:
        dict: A dictionary which contains interview list applicants data.
    """
    payload = payload.model_dump()
    return await interview_list_obj. \
        get_interview_list_applications_data_based_on_program(
        current_user, page_num, page_size, payload)


@interview_module.get("/get_hod_header/")
@requires_feature_permission("read")
async def get_hod_header_data(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)):
    """
    Get summary of interview applicants.

    Params:
        - college_id (dict): Required Field. a unique identifier/id of
            college. Useful for get college data.
            e.g., 123456789012345678901234

    Returns:
        dict: A dictionary which contains summary of interview applicants.
            e.g., {"interview_done": 0, "selected_candidate": 0,
                "pending_for_review": 0, "rejected_candidate": 0}

    Raises:
        401: Raise error with status code 401 when unauthorized user try to
            get summary of interview applicants.
        500: Raise error with status code 500 when internal error occurred.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await hod_helper().get_hod_header_data()
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An internal error"
                                                    f" occurred: {error}")


@interview_module.get("/marking_details/",
                      summary="Get marking details based on program name")
@requires_feature_permission("read")
async def marking_details(
        current_user: CurrentUser,
        course_name: str,
        specialization_name: str,
        type: str = Query(None),
        college: dict = Depends(get_college_id)):
    """
    Marking details of given programme
    Params:\n
        course_name (str) : Name of the course
        specialization_name (str) : specialization in given course
        type (str): this can be pi/gd
        college_id (dict): get college data as a dict format.
                hint, {"_id": 117654, etc...}\n
        current_user: Current user which is retrieve data call this API.

    Returns:
        result (dict) : that contains marking scheme(details)
    """
    await UserHelper().is_valid_user(current_user)
    filter_query = {
        "$expr": {
            "$and": [

                {"$eq": ["$course_name", course_name]},
                {"$eq": ["$specialization_name", specialization_name]}
            ]
        }
    }
    doc = await DatabaseConfiguration().selection_procedure_collection.find_one(
        filter_query)
    if not doc:
        raise HTTPException(status_code=412, detail="Program name not found.")
    gd_weightage = doc.get("gd_parameters_weightage")
    pi_weightage = doc.get("pi_parameters_weightage")
    if not gd_weightage and pi_weightage:
        result = {"etiquette": 10, "communication_skills": 10, "attitude": 10,
                  "behavior": 10,
                  "domain_knowledge": 10}
    else:
        result = {}
        if type is None:
            result["gd"] = gd_weightage
            result["pi"] = pi_weightage
        else:
            result[type.lower()] = doc.get(f"{type.lower()}"
                                           f"_parameters_weightage")
    return result


@interview_module.post("/store_feedback/",
                       summary="Marks obtained by the given student")
@requires_feature_permission("write")
async def store_feedback(
        current_user: CurrentUser,
        feedback_data: FeedBackSchema,
        application_id: str = Query(
            description="Id of a application **6223040bea8c8768d96d3880**"),
        slot_id: str = Query(
            description="Id of a application **6223040bea8c8768d96d3880**"),
        college: dict = Depends(get_college_id)):
    """
    Marks obtained by the given student
    Params:\n
        application_id (str) : the id of the application
        college_id (dict): get college data as a dict format.
                hint, {"_id": 117654, etc...}\n
        current_user: Current user which is retrieve data call this API.
    Returns:
        message that feedback data is stored
    """
    user = await UserHelper().is_valid_user(user_name=current_user)
    await utility_obj.is_id_length_valid(application_id, "Application id")
    await utility_obj.is_id_length_valid(slot_id, "Slot id")
    try:
        if (
        application := await DatabaseConfiguration().studentApplicationForms.find_one(
                {"_id": ObjectId(application_id)})) is None:
            raise DataNotFoundError(application_id, "Application")
        feedback_data = dict(feedback_data)
        if (slot := await DatabaseConfiguration().slot_collection.find_one(
                {"_id": ObjectId(slot_id)})) is None:
            raise DataNotFoundError(slot_id, "Slot")
        slot_type = slot.get("slot_type")
        interview_list_id = slot.get("interview_list_id")

        feedback_data.update({"date": datetime.datetime.utcnow(),
                              "interviewer_id": ObjectId(user.get("_id")),
                              "interviewer_name": utility_obj.name_can(user),
                              "slot_type": slot_type,
                              "slot_id": ObjectId(slot_id),
                              "interview_list_id": ObjectId(interview_list_id)
                              })
        scores = feedback_data.get("scores")
        store_score = {f"{score['name'].lower().replace(' ', '_')}":
                           score["point"] for score in scores}
        feedback_data["scores"] = store_score
        meeting_details = application.get("meetingDetails", {})
        await DatabaseConfiguration().studentApplicationForms.update_one(
            {"_id": ObjectId(application_id)}, {
                "$push": {"feedback": feedback_data}})
        meeting_details.update({"slot_status": "Done", "status": "Done"})
        interview_status = {"status": "Done",
                            "interview_result": feedback_data.get(
                                "status", "").title(), "interview_score":
                                feedback_data.get("overall_rating")}
        await DatabaseConfiguration().studentApplicationForms.update_one(
            {"_id": ObjectId(application_id)}, {
                "$set": {"meetingDetails": meeting_details,
                         f"{slot_type.lower()}_status": interview_status,
                         "interviewStatus.status": "Done"}}
        )
        if user.get("role", {}).get("role_name") == "panelist":
            status = feedback_data.get("status", "").lower()
            if status in ["selected", "rejected"]:
                await DatabaseConfiguration().user_collection.update_one(
                    {"_id": ObjectId(user.get('_id'))}, {
                        "$set": {"interview_taken":
                                     user.get("interview_taken", 0) + 1,
                                 f"{status}_students":
                                     user.get(f"{status}_students", 0) + 1}}
                )
    except DataNotFoundError as e:
        logger.error(f"{e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"An internal error occurred: {e}")
    return {"message": "feedback data added."}


@interview_module.put("_list/change_interview_status_of_candidates/")
@requires_feature_permission("edit")
async def change_interview_status_of_candidates(
        request: Request,
        interview_status_data: InterviewStatus,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
        is_approval_status: bool = False):
    """
    Change the status of interview candidates, useful for further/next process.

    Params:
        - college_id (str): An unique identifier/id of college. Useful for
            get college data. For example, 64b4d5036605c8470f4bb121
        - is_approval_status (bool): A boolean value will be True when user
            want change approval status of candidate.

    Request body parameters:
        interview_status_data (InterviewStatus): An object of pydantic class
            `InterviewStatus` which contains the following fields:

            - interview_list_id (str): Required field. A unique identifier/id
                of an interview list id in a string format.
                e.g., "64b4d5036605c8470f4bb111"
            - application_ids (list[str]): A list which contains application
                ids in a string format.
                e.g., ["64b4d5036605c8470f4bb123", "64b4d5036605c8470f4bb124"]
            - status (str): An interview status, useful for update interview
                status of candidates.
                Possible values are: Shortlisted, Interviewed, Selected,
                    Rejected, Offer Letter Sent, Hold and Seat Blocked.

    Returns:
        dict: A dictionary which contains information about change status
            of candidates.
    """
    try:
        interview_status_data = interview_status_data.model_dump()
        return await interview_list_obj.change_interview_status_of_candidates(
            current_user, interview_status_data, is_approval_status, request, college)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as e:
        logger.error(f"{e.message}")
        raise HTTPException(status_code=404, detail=e.message)


@interview_module.get("/gd_pi_header_list/")
@requires_feature_permission("read")
async def get_gd_pi_header(
        current_user: CurrentUser,
        archive: bool = False,
        college: dict = Depends(get_college_id)):
    """
        View gd pi header list.

        Params:\n
            college_id (dict): get college data as a dict format.
                    hint, {"_id": 117654, etc...}\n
            current_user: Current user which is retrieve data call this API.
            archive (bool): Optional field. Default value: None.
             Useful value for get Archived interview lists when value is True.

        Returns:
            Successful Response: {"message": "get gd_pi header list"}
            {
                  "total_interview_list": int,
                  "active_interview_list": int,
                  "close_interview_list": int,
                  "total_candidate_count": int,
                  "selected_candidate_count": int,
                  "rejected_candidate_count": int,
                  "hold_candidate_count": int,
                  "slot_available": int,
                  "percentage_available_slot": int
            }
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await hod_helper().get_gd_pi_header_data(archive=archive)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An internal error"
                                                    f" occurred: {error}")


@interview_module.put("/delete_slots_or_panels/",
                      response_description="Delete slots or panels")
@requires_feature_permission("delete")
async def delete_slots_or_panels(
        delete_info: SlotsPanels,
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)
):
    """
    Delete slots or panels by ids (not able to delete both slots/panels at
        the same time).

    Params:\n
        college_id (str): An unique identifier/id of college for retrieve
            college data.

    Request body parameters:
        delete_info (SlotsPanels): An object of pydantic class
        `SlotsPanels` which contains the following fields:

        - slots_panels_ids (list[str]): Required field. A list which contains
            either slots or panels ids.
            e.g., ["64b4d5036605c8470f4bb123", "64b4d5036605c8470f4bb124"]

    Returns:
          dict: A dictionary contains info about delete slots and panels.
    """
    delete_info = delete_info.model_dump()
    await UserHelper().is_valid_user(current_user)
    try:
        return await interview_list_obj.delete_slots_or_panels(delete_info)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        logger.error(f"Internal server error. Error - {str(error)}")
        raise HTTPException(status_code=500, detail="Internal server error. "
                                                    f"Error - {str(error)}")


@interview_module.post("_list/selected_student_applications_data/")
@requires_feature_permission("read")
async def selected_student_applications_data(
        current_user: CurrentUser,
        payload: InterviewListSelectedApplications,
        college: dict = Depends(get_college_id),
        page_num: int = Query(
            gt=0,
            description="Required Field. Useful for show selected applicants "
                        "data based on interview list id. For example, 1"),
        page_size: int = Query(
            gt=0,
            description="Required field. Useful for show limited data on "
                        "particular page. For example, 25"
        )
):
    """
    Get interview list selected applicants data based on interview list id.

    Params:
        - college_id (dict): Required Field. a unique identifier/id of
            college. Useful for get college data.
            For example, 123456789012345678901234
        - page_num (int): Required Field. Useful for show selected
                        applications data of program on a particular page.
                        For example, 1
        - page_size (int): Required field. Useful for show limited data on "
                          "particular page. For example, 25

    Request body parameters:
        Payload (InterviewListSelectedApplications): An object of pydantic
            class `InterviewListSelectedApplications` which contains
            following fields:
            interview_list_id (str): Required field. Interview list id will be
                useful for get selected applicants of interview list.
                For example, 123456789012345678901212
            twelve_score (list | None): Optional field.
                Default value: None. Useful for get selected applicants data
                 based on twelve score.
            ug_score (list | None): Optional field. Default value: None.
                Useful for get selected applicants data
                 based on ug score.
            interview_score (list | None): Optional field. Default value: None.
                Useful for get selected applicants data
                 based on interview score.
            twelve_score_sort (bool | None): Optional field.
                Default value: None.
                Useful for sort selected applicants data based on twelve score.
            ug_score_sort (bool | None): Optional field. Default value: None.
                Useful for sort selected applicants data based on ug score.
            interview_score_sort (bool | None): Optional field.
                Default value: None.
                Useful for sort selected applicants data based on interview
                score.

    Returns:
        dict: A dictionary which contains interview list selected applicants'
        data.
    """
    await UserHelper().is_valid_user(current_user)
    payload = payload.model_dump()
    try:
        return await interview_list_obj. \
            interview_list_selected_applicants_data(
            current_user, page_num, page_size, payload)
    except Exception as error:
        logger.error(f"Internal server error. Error - {str(error)}")
        raise HTTPException(status_code=500, detail=f"Internal server error. "
                                                    f"Error - {str(error)}")


@interview_module.post("_list/approval_pending_applicants_data/")
@requires_feature_permission("read")
async def approval_pending_applications_data(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
        page_num: int = Query(
            gt=0,
            description="Required Field. Useful for show approval pending "
                        "applicants data. e.g., 1"),
        page_size: int = Query(
            gt=0,
            description="Required field. Useful for show limited data on "
                        "particular page. e.g., 25"
        )
):
    """
    Get approval pending applicants' data with pagination.

    Params:
        - college_id (dict): Required Field. An unique identifier/id of
            college. Useful for get college data.
            For example, 123456789012345678901234
        - page_num (int): Required Field. Useful for show approval pending
                        applicants data on a particular page.
                        For example, 1
        - page_size (int): Required field. Useful for show limited data on "
                          "particular page. For example, 25

    Returns:
        dict: A dictionary which contains approval pending applicants'
            data.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await interview_list_obj.approval_pending_applicants_data(
            current_user, page_num, page_size)
    except Exception as error:
        logger.error(f"Something went wrong while fetching approval pending"
                     f" applicants data. Error - {str(error)}")
        raise HTTPException(
            status_code=500, detail="Something went wrong while approval "
                                    f"pending applicants data. "
                                    f"Error - {str(error)}")


@interview_module.put("_list/send_applicants_for_approval/")
@requires_feature_permission("write")
async def send_applicants_for_approval(
        current_user: CurrentUser,
        payload: InterviewListSelectedApplications,
        application_ids: list[str] = None,
        college: dict = Depends(get_college_id)
):
    """
    Send applicants for approval.
    When applicants selected for interview, user can send applicants for final
    review/approval.

    Params:
        - college_id (str): An unique identifier/id of college. Useful for
            get college data. For example, 64b4d5036605c8470f4bb121
        # - interview_list_id (str): Required Field. A unique identifier/id of
        #     interview list. e.g., 64b4d5036605c8470f4bb120"

    Request body parameters:
        - application_ids (list[str]): A list which contains application
            ids in a string format.
            e.g., ["64b4d5036605c8470f4bb123", "64b4d5036605c8470f4bb124"]
        - payload (InterviewListSelectedApplications): An object of pydantic
            class `InterviewListSelectedApplications` which contains
            following fields:
            interview_list_id (str): Required field. Interview list id will be
                useful for get selected applicants of interview list.
                For example, 123456789012345678901212
            twelve_score (list | None): Optional field.
                Default value: None. Useful for get selected applicants data
                 based on twelve score.
            ug_score (list | None): Optional field. Default value: None.
                Useful for get selected applicants data
                 based on ug score.
            interview_score (list | None): Optional field. Default value: None.
                Useful for get selected applicants data
                 based on interview score.
            twelve_score_sort (bool | None): Optional field.
                Default value: None.
                Useful for sort selected applicants data based on twelve score.
            ug_score_sort (bool | None): Optional field. Default value: None.
                Useful for sort selected applicants data based on ug score.
            interview_score_sort (bool | None): Optional field.
                Default value: None.
                Useful for sort selected applicants data based on interview
                score.


    Returns:
        dict: A dictionary which contains information about
            send approval applicants.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        payload = payload.model_dump()
        return await interview_list_obj.send_applicants_for_approval(
            application_ids, payload)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except DataNotFoundError as e:
        logger.error(f"{e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as error:
        logger.error(f"Internal server error. Error - {str(error)}")
        raise HTTPException(status_code=500, detail="Internal server error. "
                                                    f"Error - {str(error)}")


@interview_module.post("_list/reviewed_applicants_data/")
@requires_feature_permission("read")
async def reviewed_applicants_data(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id),
        page_num: int = Query(
            gt=0,
            description="Required Field. Useful for show reviewed applicants "
                        "data. e.g., 1"),
        page_size: int = Query(
            gt=0,
            description="Required field. Useful for show limited data on "
                        "particular page. e.g., 25"
        )
):
    """
    Get reviewed applicants' data with pagination.

    Params:
        - college_id (dict): Required Field. a unique identifier/id of
            college. Useful for get college data.
            e.g., 123456789012345678901234
        - page_num (int): Required Field. Useful for show approval pending
                        applicants data on a particular page.
                        e.g., 1
        - page_size (int): Required field. Useful for show limited data on "
                          "particular page. e.g., 25

    Returns:
        dict: A dictionary which contains reviewed applicants' data.
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await interview_list_obj.reviewed_applicants_data(
            current_user, page_num, page_size)
    except Exception as error:
        logger.error(f"Something went wrong while fetching reviewed applicants"
                     f"data. Error - {str(error)}")
        raise HTTPException(
            status_code=500, detail="Something went wrong while fetching "
                                    f"reviewed applicants data. "
                                    f"Error - {str(error)}")


@interview_module.post("/delete_selection_procedures/",
                       summary="Delete selection procedures by ids")
@requires_feature_permission("delete")
async def delete_selection_procedures(
        selection_procedure_ids: list[str],
        current_user: CurrentUser,
        college: dict = Depends(get_college_id)
):
    """
    Delete selection procedures by ids.

    Params:
        selection_procedure_ids (list[str]): A list which contains unique
            identifiers/ids of selection procedure.
        college_id (str): An unique identifier/id of a college.

    Returns:
          dict: A dictionary contains info about delete selection procedures.
    """
    await selection_procedure_obj.is_valid_user_and_role(current_user)
    try:
        return await selection_procedure_obj.delete_selection_procedures_by_ids(
            selection_procedure_ids)
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        logger.error(f"Internal error occurred. Error - {str(error)}")
        raise HTTPException(status_code=500, detail="Internal error occurred. "
                                                    f"Error - {str(error)}")
