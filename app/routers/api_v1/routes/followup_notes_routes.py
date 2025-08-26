"""
This file contains API routes/endpoints related to followup_notes
"""
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from fastapi import APIRouter, Depends, Path, Query, Body
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError
from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.custom_error import ObjectIdInValid
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import (
    CurrentUser,
    cache_dependency,
    insert_data_in_cache,
    cache_invalidation, is_testing_env,
)
from app.helpers.counselor_deshboard.counselor import CounselorDashboardHelper
from app.helpers.followup_queries.followup_lead_stage import \
    add_lead_stage_label
from app.helpers.followup_queries.followup_notes_configuration import (
    FollowupNotesHelper,
    lead_stage_label,
    pending_followup,
)
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.applications import DateRange
from app.models.followup_notes_schema import FollowupNotes, list_application
from app.models.student_user_schema import User

logger = get_logger(__name__)

followup_notes_router = APIRouter()


async def send_data(current_user, application_id):
    """
    Return the detail of user and details of student
    """
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not user:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    try:
        application = await DatabaseConfiguration().studentApplicationForms.find_one(
            {"_id": ObjectId(application_id)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail="Application id must be a 12-byte input or a "
            "24-character hex string.",
        )
    if not application:
        raise HTTPException(
            status_code=404,
            detail=f"Application not found. Enter correct application id.",
        )
    return user, application


@followup_notes_router.put(
    "/update_followup_status/{application_id}/", summary="Update followup status"
)
@requires_feature_permission("edit")
async def update_followup_status(
    current_user: CurrentUser,
    status: bool = Query(
        ...,
        description="Status can be any of following:\n* true\n* false",
        example="completed",
    ),
    application_id: str = Path(
        ..., description="Enter application ID", example="62ac13e38ad84805ecae3d7c"
    ),
    index_number: int = Query(..., description="give integer value"),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    testing: bool = Query(
        False,
        description="Using this parameter for testing purpose only",
    ),
):
    """
    Update Followup Status
    * :*param* **application_id** e.g., 62ac13e38ad84805ecae3d7c:\n
    * :*param* **index number** e.g., 0,1,2,3,4,5\n
    * :*return* **Message - Followup status updated.**:
    """
    user, application = await send_data(current_user, application_id)
    if user.get("role", {}).get("role_name") in [
        "super_admin",
        "college_publisher_console",
    ]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    if (
        followup_record := await DatabaseConfiguration().leadsFollowUp.find_one(
            {"application_id": ObjectId(application_id)}
        )
    ) is not None:
        if testing:
            return utility_obj.response_model(data=True, message="followup has updated")
        if len(followup_record.get("followup", [])) <= index_number:
            raise HTTPException(status_code=404, detail="index number not found")
        if status is True:
            status = "Completed"
        elif status is False:
            status = "Incomplete"
        else:
            raise HTTPException(
                status_code=422, detail="please select the boolean value"
            )
        name = utility_obj.name_can(user)
        followup_record.get("followup")[index_number].update(
            {
                "updated_by": name,
                "updated_date": datetime.now(timezone.utc),
                "status": status,
            }
        )
        followup_record_index = followup_record.get("followup")[index_number]
        await DatabaseConfiguration().leadsFollowUp.update_one(
            {"_id": ObjectId(followup_record.get("_id"))}, {"$set": followup_record}
        )
        current_datetime = datetime.now(timezone.utc)
        update_data = {"last_user_activity_date": current_datetime}
        student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"_id": application.get("student_id")}
        )
        if student and not student.get("first_lead_activity_date"):
            update_data["first_lead_activity_date"] = current_datetime
        await DatabaseConfiguration().studentsPrimaryDetails.update_one({
            "_id": ObjectId(application.get("student_id"))}, {"$set": update_data})
        timeline_update = {
            "user_id": followup_record_index.get("user_id"),
            "timestamp": datetime.now(timezone.utc),
            "event_type": "Application",
            "event_status": f"Lead stage {followup_record.get('followup')[index_number - 1]['status']} is changed to {status}",
            "message": f"{name} has marked the follow up scheduled for {utility_obj.get_local_time(followup_record_index.get('timestamp'))} {status}",
            "application_id": application_id,
        }
        await DatabaseConfiguration().studentTimeline.update_one(
            {"student_id": application.get("student_id")},
            {"$push": {"timelines": timeline_update}},
        )
        return utility_obj.response_model(data=True, message="followup has updated")
    else:
        raise HTTPException(status_code=404, detail="application not found")


# TODO: Below API method code need to be modify and refector
@followup_notes_router.put(
    "/{application_id}/", summary="Add or get follow-up and notes"
)
@requires_feature_permission("write")
async def get_followup_notes_data(
    current_user: CurrentUser,
    followup_notes: FollowupNotes,
    application_id: str = Path(..., description="Enter application id"),
    resolved: bool = False,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Add or Get Follow-up and Notes
    * :*param* **note** e.g., no answer What's app sent:
    * :*param* **assigned_counselor_id** e.g., 62aadb13040d039d95027faa:
    * :*param* **followup_date** e.g., no answer What's app sent:
    * :*param* **followup_note** e.g., no answer What's app sent:
    * :*param* **lead_stage** e.g., no answer What's app sent:
    * :*param* **label** e.g., already take admission anywhere:
    * :*param* **application_sub stage** e.g., Unpaid:
    * :*param* **application_id** e.g., 62aa2cd25c11b18093568925:
    :return:
    """
    user, application = await send_data(current_user, application_id)
    if user.get("role", {}).get("role_name") in [
        "super_admin",
        "client_manager",
        "college_publisher_console",
    ]:
        raise HTTPException(status_code=401, detail=f"Not enough permissions")
    json_followup_notes_data = {
        key: value
        for key, value in followup_notes.model_dump().items()
        if value is not None
    }
    try:
        find_data = await DatabaseConfiguration().leadsFollowUp.find_one(
            {"application_id": ObjectId(application_id)}
        )

        if resolved:
            for data in find_data.get("followup", []):
                data['status'] = "Completed"
                
    except Exception as e:
        raise HTTPException(status_code=404, detail="lead not found")
    if len(json_followup_notes_data) < 1:
        if not find_data:
            raise HTTPException(
                status_code=404, detail="Application followup and notes not found."
            )
        return utility_obj.response_model(
            data=FollowupNotesHelper().followup_notes_helper(find_data),
            message="Get follow-up and notes.",
        )
    if json_followup_notes_data.get("note"):
        notes_list = []
        note = {
            "note": json_followup_notes_data.pop("note"),
            "timestamp": datetime.now(timezone.utc),
            "user_id": ObjectId(user.get("_id")),
            "added_by": utility_obj.name_can(user),
        }
        notes_list.append(note)
        json_followup_notes_data["notes"] = notes_list
        json_followup_notes_data["total_notes"] = len(notes_list)
    if json_followup_notes_data.get("followup", {}).get(
        "assigned_counselor_id"
    ) not in [None, ""]:
        await CounselorDashboardHelper().allocate_counselor(
            application_id,
            current_user.get("user_name"),
            str(
                json_followup_notes_data.get("followup", {}).get(
                    "assigned_counselor_id"
                )
            ),
        )
        assigned_counselor_id = ObjectId(
            json_followup_notes_data.get("followup", {}).get("assigned_counselor_id")
        )
        json_followup_notes_data["lead_stage"] = "Follow-up"
    else:
        if json_followup_notes_data.get("followup") is not None:
            json_followup_notes_data["followup"]["assigned_counselor_id"] = str(
                application.get("allocate_to_counselor", {}).get("counselor_id")
            )
            assigned_counselor_id = ObjectId(
                str(application.get("allocate_to_counselor", {}).get("counselor_id"))
            )
    date_utc = None
    if json_followup_notes_data.get("followup", {}).get("followup_date") in [None, ""]:
        if json_followup_notes_data.get("followup") is not None:
            json_followup_notes_data.pop("followup")
    if json_followup_notes_data.get("followup", {}).get("followup_date") not in [None,""]:
        followup_list = []
        if (
            json_followup_notes_data.get("followup", {}).get("assigned_counselor_id")
            and json_followup_notes_data.get("followup", {}).get(
                "assigned_counselor_id"
            )
            != ""
        ):
            json_followup_notes_data["followup"]["assigned_counselor_id"] = ObjectId(
                str(
                    json_followup_notes_data.get("followup", {}).get(
                        "assigned_counselor_id"
                    )
                )
            )
            try:
                counselor = await DatabaseConfiguration().user_collection.find_one(
                    {
                        "_id": ObjectId(
                            json_followup_notes_data["followup"][
                                "assigned_counselor_id"
                            ]
                        )
                    }
                )
            except:
                raise HTTPException(
                    status_code=422,
                    detail="Assigned counselor id must be a 12-byte input"
                    " or a 24-character hex string.",
                )
            if counselor:
                json_followup_notes_data["followup"]["assigned_counselor_name"] = (
                    utility_obj.name_can(counselor)
                )
            else:
                raise HTTPException(
                    status_code=422, detail="Enter correct assigned counselor id"
                )
        else:
            json_followup_notes_data["followup"]["assigned_counselor_name"] = (
                application.get("allocate_to_counselor", {}).get("counselor_name")
            )
            json_followup_notes_data["followup"]["assigned_counselor_id"] = ObjectId(
                str(application.get("allocate_to_counselor", {}).get("counselor_id"))
            )

        followup = json_followup_notes_data.pop("followup")
        date_utc = await utility_obj.date_change_utc(followup.get("followup_date"))
        followup.update(
            {
                "followup_date": date_utc,
                "timestamp": datetime.now(timezone.utc),
                "user_id": ObjectId(user.get("_id")),
                "added_by": utility_obj.name_can(user),
                "status": "Incomplete",
            }
        )
        followup_list.append(followup)
        json_followup_notes_data["followup"] = followup_list

    lead_stage = json_followup_notes_data.get("lead_stage")
    if not find_data:
        if isinstance(json_followup_notes_data.get("followup"), list):
            if json_followup_notes_data.get("followup", [])[0].get(
                "followup_date"
            ) not in [None, ""]:
                counselor_timeline = [
                    {
                        "assigned_counselor_id": assigned_counselor_id,
                        "assigned_counselor_name": followup.get(
                            "assigned_counselor_name"
                        ),
                        "timestamp": datetime.now(timezone.utc),
                        "user_id": user.get("_id"),
                        "added_by": utility_obj.name_can(user),
                    }
                ]
                json_followup_notes_data.update(
                    {
                        "application_id": ObjectId(application_id),
                        "counselor_timeline": counselor_timeline,
                        "student_id": ObjectId(application.get("student_id")),
                        "application_status": (
                            "completed"
                            if application.get("declaration")
                            else "Incomplete"
                        ),
                    }
                )
        else:
            json_followup_notes_data.update(
                {
                    "application_id": ObjectId(application_id),
                    "student_id": ObjectId(application["student_id"]),
                    "application_status": (
                        "Completed" if application["declaration"] else "Incomplete"
                    ),
                }
            )
        if lead_stage:
            json_followup_notes_data["lead_stage_history"] = [lead_stage]
            json_followup_notes_data["lead_stage_change_count"] = 2
            await DatabaseConfiguration().studentsPrimaryDetails.update_one(
                {"_id": ObjectId(application.get("student_id"))},
                {"$set": {"lead_stage_change_at": datetime.now(timezone.utc)}}
            )
            await DatabaseConfiguration().studentApplicationForms.update_one(
                {"_id": ObjectId(application.get("_id"))},
                {"$set": {"lead_stage_change_at": datetime.now(timezone.utc)}}
            )
        if inserted_data := await DatabaseConfiguration().leadsFollowUp.insert_one(
            json_followup_notes_data
        ):
            get_data = await DatabaseConfiguration().leadsFollowUp.find_one(
                {"_id": inserted_data.inserted_id}
            )
            if isinstance(json_followup_notes_data.get("followup"), list):
                if json_followup_notes_data.get("followup", [])[0].get(
                    "followup_date"
                ) not in [None, ""]:
                    await utility_obj.update_notification_db(
                        event="Follow up", application_id=application_id
                    )

            return utility_obj.response_model(
                data=FollowupNotesHelper().followup_notes_helper(get_data),
                message="Follow-up and notes data added.",
            )
    if (
        json_followup_notes_data.get("notes") is not None
        and json_followup_notes_data.get("notes") != ""
    ):
        if find_data.get("notes"):
            find_data.get("notes").insert(0, note)
            json_followup_notes_data["notes"] = find_data.get("notes")
            json_followup_notes_data["total_notes"] = len(find_data.get("notes"))
        else:
            json_followup_notes_data["notes"] = notes_list
    if (
        json_followup_notes_data.get("followup") is not None
        and json_followup_notes_data.get("followup") != ""
    ):
        temp = {
            "assigned_counselor_id": assigned_counselor_id,
            "assigned_counselor_name": followup.get("assigned_counselor_name"),
            "timestamp": datetime.now(timezone.utc),
            "user_id": user.get("_id"),
            "added_by": utility_obj.name_can(user),
        }
        if find_data.get("followup"):
            find_data.get("followup").insert(0, followup)
            json_followup_notes_data["followup"] = find_data.get("followup")
        else:
            json_followup_notes_data["followup"] = followup_list
        await CounselorDashboardHelper().counselor_timeline_history(
            find_data, temp, application_id
        )
    if lead_stage:
        previous_lead_stage = find_data.get("lead_stage")
        lead_stage_count = find_data.get("lead_stage_change_count", 1)
        json_followup_notes_data["lead_stage_change_count"] = lead_stage_count + 1
        json_followup_notes_data["previous_lead_stage"] = previous_lead_stage
        json_followup_notes_data["previous_lead_stage_label"] = find_data.get(
            "lead_stage_label"
        )
        if find_data.get("lead_stage_history") is None:
            find_data["lead_stage_history"] = []
        find_data["lead_stage_history"].insert(0, lead_stage)
        json_followup_notes_data["lead_stage_history"] = find_data["lead_stage_history"]
        try:
            # TODO: Not able to add student timeline data
            #  using celery task when environment is
            #  demo. We'll remove the condition when
            #  celery work fine.
            if settings.environment in ["demo"]:
                StudentActivity().student_timeline(
                    student_id=str(application.get("student_id")),
                    event_type="User",
                    event_status="Change lead stage",
                    message=f"{utility_obj.name_can(user)}"
                    f" has changed the lead stage from"
                    f" {previous_lead_stage} to {lead_stage}",
                )
            else:
                if not is_testing_env():
                    StudentActivity().student_timeline.delay(
                        student_id=str(application.get("student_id")),
                        event_type="User",
                        event_status="Change lead stage",
                        message=f"{utility_obj.name_can(user)}"
                        f" has changed the lead stage from"
                        f" {previous_lead_stage} to {lead_stage}",
                    )
        except KombuError as celery_error:
            logger.error(
                f"error storing change the lead stage"
                f" timeline data "
                f"{celery_error}"
            )
        except Exception as error:
            logger.error(
                f"error storing change the lead stage" f" timeline data " f"{error}"
            )
    if await DatabaseConfiguration().leadsFollowUp.update_one(
        {"application_id": ObjectId(find_data["application_id"])},
        {"$set": json_followup_notes_data},
    ):
        update_info = {"last_user_activity_date": datetime.now(timezone.utc)}
        if lead_stage:
            update_info.update({"lead_stage_change_at": datetime.now(timezone.utc)})
            await DatabaseConfiguration().studentApplicationForms.update_one(
                {"_id": ObjectId(application.get("_id"))},
                {"$set": {"lead_stage_change_at": datetime.now(timezone.utc)}}
            )
        await DatabaseConfiguration().studentsPrimaryDetails.update_one({
            "_id": ObjectId(application.get("student_id"))},
            {"$set": update_info})
        if date_utc:
            from app.routers.api_v1.app import scheduler
            scheduler.add_job(
                utility_obj.update_notification_db,
                trigger='date',
                run_date=date_utc - timedelta(minutes=10),
                kwargs={"event": "Followup remainder", "application_id": application_id}
            )
        await cache_invalidation(api_updated="followup_notes/multiple_lead_stage")
        return utility_obj.response_model(
            data=FollowupNotesHelper().followup_notes_helper(find_data),
            message="Follow-up and notes data updated.",
        )
    raise HTTPException(status_code=422, detail="Failed to insert data.")


# ToDo - Need to add test cases regarding below API route
@followup_notes_router.put("/multiple_lead_stage")
@requires_feature_permission("write")
async def multiple_lead(
    current_user: CurrentUser,
    lead_stage_info: list_application,
    lead_stage: str,
    label: str = None,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Add/Update lead stage information for multiple applications.
    If application_id found in leadsFollowUp will update the lead stage,
    if not it will add new document in leadsFollowUp

    Params:\n
        - lead_stage (str): Name of a lead stage which want to update for
            multiple applications.
        - label (str | None): Optional field.
            Name of a lead stage label which comes along with lead_stage.
        - college_id (str): A unique id/identifier of a college.
                e.g., 123456789012345678901234

    Request body params:\n
       - lead_stage_info (list_application): An object of pydantic class
                `list_application` which contains following field:
                - application_id (List): A list which contains unique
                    applications ids which useful for update/add lead
                    stage information. e,g., ["123456789012345678901245",
                                            "123456789012345678901246"]
                - followup_date (str | None): Required in case of
                    lead_stage=Follow-up. Accepted format: DD/MM/YYYY HH/MM
                    pm/am.
                - followup_note (str | None): Either None or a note of
                    followup.
                - assigned_counselor_id( str | None): Either None or a unique
                    id/identifier of a counselor.
                    e.g., "123456789012345678901248"

    Returns:\n
        - dict - A dictionary which contains information about add multiple
            lead stage to applications.

    Raises:
         - ObjectIdInValid: An error with status code 422 which occurred
            when application id will be wrong.
        - Exception: An error with status code 500 which occurred when
            something went wrong in the background code.
    """
    lead_stage_info = jsonable_encoder(lead_stage_info)
    if (
        user := await DatabaseConfiguration().user_collection.find_one(
            {"user_name": current_user.get("user_name")}
        )
    ) is None:
        raise HTTPException(status_code=404, detail="user not found")
    if user.get("role", {}).get("role_name") == "college_publisher_console":
        raise HTTPException(status_code=403, detail="Not authenticated")
    for application_id in lead_stage_info.get("application_id"):
        try:
            if (
                await utility_obj.is_length_valid(application_id, "Application id")
                and (
                    application := await DatabaseConfiguration().studentApplicationForms.find_one(
                        {"_id": ObjectId(application_id)}
                    )
                )
                is not None
            ):

                data = {
                    "lead_stage": lead_stage,
                    "application_id": ObjectId(application_id),
                }
                data.update({"lead_stage_label": label})
                if lead_stage == "Follow-up":
                    await FollowupNotesHelper().update_followup_info(
                        lead_stage_info.get("assigned_counselor_id"),
                        application,
                        str(current_user.get("user_name")),
                        lead_stage_info.get("followup_date"),
                        user,
                        lead_stage_info.get("followup_note"),
                    )
                lead_followup_info = (
                    await DatabaseConfiguration().leadsFollowUp.find_one(
                        {
                            "application_id": ObjectId(application_id),
                            "student_id": application.get("student_id"),
                        }
                    )
                )
                if lead_followup_info:
                    previous_lead_stage = lead_followup_info.get("lead_stage")
                    lead_stage_count = lead_followup_info.get("lead_stage_change_count", 1)
                    data["lead_stage_change_count"] = lead_stage_count + 1
                    data["previous_lead_stage"] = previous_lead_stage
                    data["previous_lead_stage_label"] = lead_followup_info.get(
                        "lead_stage_label"
                    )
                    if lead_followup_info.get("lead_stage_history") is None:
                        lead_followup_info["lead_stage_history"] = []
                    lead_followup_info["lead_stage_history"].insert(0, lead_stage)
                    data["lead_stage_history"] = lead_followup_info[
                        "lead_stage_history"
                    ]
                    await lead_stage_label().add_lead_stage_timeline(
                        application=application, current_lead_stage=lead_stage,
                        previous_lead_stage=previous_lead_stage,
                        user=user
                    )
                else:
                    await lead_stage_label().add_lead_stage_timeline(
                        application=application, current_lead_stage=lead_stage,
                        user=user
                    )
                await DatabaseConfiguration().leadsFollowUp.update_one(
                    {
                        "application_id": ObjectId(application_id),
                        "student_id": application.get("student_id"),
                    },
                    {"$set": data},
                    upsert=True,
                )
                current_datetime = datetime.now(timezone.utc)
                update_data = {"last_user_activity_date": current_datetime}
                student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": application.get("student_id")}
                )
                if student and not student.get("first_lead_activity_date"):
                    update_data["first_lead_activity_date"] = current_datetime
                await DatabaseConfiguration().studentsPrimaryDetails.update_one({
                    "_id": ObjectId(application.get("student_id"))}, {"$set": update_data})
        except ObjectIdInValid as error:
            raise HTTPException(status_code=422, detail=error.message)
        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail=f"An error got when add lead stage to "
                f"multiple applications. Error - "
                f"{error}.",
            )
    await cache_invalidation(api_updated="followup_notes/multiple_lead_stage")
    return utility_obj.response_model(data=True, message="data updated successfully")


@followup_notes_router.put("/add_lead_stage_label")
@requires_feature_permission("write")
async def add_lead_label(
    current_user: CurrentUser,
    lead_stage: str,
    label: str = Query(max_length=50),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """add lead stage label on client database"""
    await UserHelper().is_valid_user(current_user)
    data = await add_lead_stage_label().add_lead_stage_label_data(
        lead_stage, label, college.get("id")
    )
    await cache_invalidation(api_updated="followup_notes/add_lead_stage_label")
    return utility_obj.response_model(
        data=data.get("lead_stage_label", {}), message="data update successfully"
    )


@followup_notes_router.put("/head_counselor_details")
@requires_feature_permission("read")
async def get_head_counselor_details(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    season: str = Body(
        None, description="Enter season value if want to get data season-wise"
    ),
    date_range: DateRange = Body(None),
    page_num: int = Query(gt=0),
    page_size: int = Query(gt=0),
):
    """
    get all head counselor details
    """
    if date_range is None:
        date_range = await utility_obj.next_3_month()
    date_range = jsonable_encoder(date_range)
    start_date, end_date = await utility_obj.date_change_format(
        date_range.get("start_date"), date_range.get("end_date")
    )
    if season == "":
        season = None
    await UserHelper().is_valid_user(current_user)
    return await pending_followup(
        current_user.get("user_name"), start_date, end_date, page_num, page_size
    ).head_counselor_detail(season=season)


@followup_notes_router.put("/get_pending_followup")
@requires_feature_permission("read")
async def get_all_pending_followup(
    current_user: CurrentUser,
    head_counselor_id: str = None,
    date_range: DateRange = Body(None),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
    page_num: int = Query(gt=0),
    page_size: int = Query(gt=0),
):
    """get all pending lead"""
    await UserHelper().is_valid_user(current_user)
    if date_range is None:
        date_range = await utility_obj.next_3_month()
    date_range = jsonable_encoder(date_range)
    start_date, end_date = await utility_obj.date_change_format(
        date_range.get("start_date"), date_range.get("end_date")
    )
    data = await pending_followup(
        current_user.get("user_name"), start_date, end_date, page_num, page_size
    ).get_pending_followup_lead(head_counselor_id)
    return data


@followup_notes_router.get("/get_lead_stage_label")
@requires_feature_permission("read")
async def get_lead_label(
    current_user: CurrentUser,
    cache_data=Depends(cache_dependency),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """get lead stage label from client database"""
    await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    lead_stage = await lead_stage_label().get_lead_stage_with_label(college.get("id"))
    data = utility_obj.response_model(
        data=lead_stage, message="data fetch successfully"
    )
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data
