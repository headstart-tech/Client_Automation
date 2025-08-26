"""
This file contains API routes related to student
"""
import datetime
import functools
from typing import List, Union

from bson.objectid import ObjectId
from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi import BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError
from pydantic import constr

from app.background_task.doc_text_extraction import DocExtraction
from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.custom_error import DataNotFoundError, CustomError
from app.core.utils import utility_obj, logger, settings, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.hashing import Hash
from app.dependencies.oauth import CurrentUser, is_testing_env
from app.helpers.college_configuration import CollegeHelper
from app.helpers.student_curd.student_application_configuration import (
    StudentApplicationHelper,
)
from app.helpers.student_curd.student_configuration import StudentHelper
from app.helpers.student_curd.student_user_crud_configuration import (
    StudentUserCrudHelper,
)
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.serialize import StudentCourse
from app.models.student_user_crud_schema import (
    AddressDetails,
    CandidateBasicPreference,
    EducationDetails,
    updateParentsDetails,
    FormStageName,
)
from app.models.student_user_schema import upload_docs
from app.s3_events.s3_events_configuration import upload_files, validate_file

router = APIRouter()


@router.get(
    "/get_students_primary_details/", response_description="Get Students primary data"
)
@requires_feature_permission("read")
async def get_student_primary_details(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get primary data of current Student\n
    * :*return* **List of students information with message
    'Students data fetched successfully'**:
    """
    student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": current_user.get("user_name")}
    )
    student = StudentCourse().student_primary(
        student, college.get("id"), college.get("system_preference"))
    if student:
        return student
    raise HTTPException(status_code=422, detail="user not found")


@router.get("/fetch_additional_upload_fields")
@requires_feature_permission("read")
async def fetch_additional_uploads(
        current_user: CurrentUser,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        course_id: str = Query(None, description="Enter form course id."),
):
    """
    Fetch additional upload fields for a specific college and course.

    This endpoint retrieves the additional fields that a student is required
    to upload during the form submission process based on the selected college and course.

    Params:
        current_user (CurrentUser): The currently logged-in user.
        college_id (str, optional): The unique ID of the college.
        course_id (str, optional): The unique ID of the course.

    Returns:
        JSON response containing the additional upload fields required.

    Raises:
        HTTPException: If the user is not valid, or an internal server error occurs.
    """
    try:
        # Checking if Student is valid or not
        if not (student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
            {"user_name": current_user.get("user_name")}
        )):
            raise DataNotFoundError("Student")
        if student.get("college_id") != ObjectId(college.get("id")):
            raise CustomError("You are not associated with this college")
        return await CollegeHelper().fetch_additional_upload_fields(college_id=college.get("id"),
                                                                    course_id=course_id)
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except HTTPException as error:
        raise error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occur {error}")


# function for get all student data
@router.get("/get_students_details/", response_description="Get Students data")
@requires_feature_permission("read")
async def get_students_full_detail(
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get All Student Data\n
    * :*return* **List of students information with message
     'Students data fetched successfully'**:
    """
    students = await StudentHelper().retrieve_students(current_user.get("user_name"))
    if students:
        return utility_obj.response_model(
            students, f"Students data fetched" f" successfully."
        )
    raise HTTPException(status_code=404, detail={"error'": "Country not found."})


EntryCode = constr(pattern=r"^\w{24}$")


# function for add or update basic details
@router.put(
    "/basic_details/{course_name}/", response_description="Add or update basic details"
)
@requires_feature_permission("write")
async def add_or_update_basic_details(
    course_name: str,
    basic_details: CandidateBasicPreference,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Add or Update Basic Details\n
    * :*param* **basic_details**:\n
    * :*param* **country iso2 e.g. IN **:\n
    * :*param* **state code e.g. UP **:\n
    * :*param* **city name e.g. city fullname**:\n
    * :*return* **Add or update basic details**:
    """
    basic_details = {
        k: v for k, v in basic_details.model_dump().items() if v is not None
    }
    if len(basic_details) < 1:
        raise HTTPException(status_code=422, detail="Need to pass at least one field.")
    user = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": current_user.get("user_name")}
    )
    response = await StudentHelper().update_basic_details(
        _id=str(user.get("_id")),
        basic_detail=basic_details,
        course_name=course_name,
        college_id=str(college.get("id")),
        student=True,
    )
    if response:
        try:
            # TODO: Not able to add student timeline data
            #  using celery task when environment is
            #  demo. We'll remove the condition when
            #  celery work fine.
            if settings.environment in ["demo"]:
                StudentActivity().add_student_timeline(
                    student_id=str(user.get("_id")),
                    event_type="Application",
                    event_status="Update Basic details",
                    message="has updated its 'Basic and Preferences'"
                    " details for programme:",
                    college_id=college.get("id"),
                )
            else:
                if not is_testing_env():
                    StudentActivity().add_student_timeline.delay(
                        student_id=str(user.get("_id")),
                        event_type="Application",
                        event_status="Update Basic details",
                        message="has updated its 'Basic and Preferences'"
                        " details for programme:",
                        college_id=college.get("id"),
                    )
        except KombuError as celery_error:
            logger.error(f"error storing timeline data {celery_error}")
        except Exception as error:
            logger.error(f"error storing timeline data {error}")
        return utility_obj.response_model(
            response, message=f"Basic details added or updated successfully"
        )
    raise HTTPException(status_code=404, detail="No found.")


# function for add or update parent details
@router.put(
    "/parent_details/{course_name}/",
    response_description="Add or update parent details",
)
@requires_feature_permission("write")
async def add_or_update_parent_details(
    course_name: str,
    parent_details: updateParentsDetails,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Add or Update Parent Details\n
    * :*param* **parent_details**:\n
    * :*param* **student_id**:\n
    * :*return* **Add or update parent details**:
    """
    parent_details = {
        k: v for k, v in parent_details.model_dump().items() if v is not None
    }
    key_value = "parents_details"
    user = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": current_user.get("user_name")}
    )
    response = await StudentHelper().insert_some(
        str(user["_id"]), parent_details, key_value, course_name, college_id=str(user.get("college_id"))
    )
    if response:
        try:
            toml_data = utility_obj.read_current_toml_file()
            if toml_data.get("testing", {}).get("test") is False:
                # TODO: Not able to add student timeline data
                #  using celery task when environment is
                #  demo. We'll remove the condition when
                #  celery work fine.
                if settings.environment in ["demo"]:
                    StudentActivity().add_student_timeline(
                        student_id=str(user.get("_id")),
                        event_type="Application",
                        event_status="Update parents details",
                        message="has updated its 'Parents' details for programme:",
                        college_id=college.get("id"),
                    )
                else:
                    if not is_testing_env():
                        StudentActivity().add_student_timeline.delay(
                            student_id=str(user.get("_id")),
                            event_type="Application",
                            event_status="Update parents details",
                            message="has updated its 'Parents' details for programme:",
                            college_id=college.get("id"),
                        )
        except KombuError as celery_error:
            logger.error(f"error parent details timeline {celery_error}")
        except Exception as error:
            logger.error(f"error storing parent details timeline data {error}")
        return utility_obj.response_model(
            response, message=f"Parent details added or updated successfully"
        )
    raise HTTPException(status_code=404, detail="No found.")


@router.put(
    "/address_details/{course_name}/",
    response_description="Add or update address details",
)
@requires_feature_permission("write")
async def add_or_update_address_details(
    course_name: str,
    address_details: AddressDetails,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Add or Update Address Details\n
    * :*param* **student_id**:\n
    * :*param* **address_details**:\n
    * :*return* **Add or update address details**:
    """
    address_details = {
        k: v for k, v in address_details.model_dump().items() if v is not None
    }
    key_value = "address_details"
    user = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": current_user.get("user_name")}
    )
    response = await StudentUserCrudHelper().address_insert(
        str(user["_id"]), address_details, key_value, course_name, college_id=college.get("id")
    )
    if response:
        try:
            toml_data = utility_obj.read_current_toml_file()
            if toml_data.get("testing", {}).get("test") is False:
                # TODO: Not able to add student timeline data
                #  using celery task when environment is
                #  demo. We'll remove the condition when
                #  celery work fine.
                if settings.environment in ["demo"]:
                    StudentActivity().add_student_timeline(
                        student_id=str(user.get("_id")),
                        event_type="Application",
                        event_status="Update address details",
                        message="has updated its 'Address' details for programme:",
                        college_id=college.get("id"),
                    )
                else:
                    if not is_testing_env():
                        StudentActivity().add_student_timeline.delay(
                            student_id=str(user.get("_id")),
                            event_type="Application",
                            event_status="Update address details",
                            message="has updated its 'Address' details for programme:",
                            college_id=college.get("id"),
                        )
        except KombuError as celery_error:
            logger.error(
                f"error storing address details" f" timeline data {celery_error}"
            )
        except Exception as error:
            logger.error(f"error storing address details" f" timeline data {error}")
        return utility_obj.response_model(
            response, message=f"Address details added or updated successfully."
        )
    raise HTTPException(status_code=404, detail="No found.")


@router.put(
    "/education_details/{course_name}/",
    response_description="Add or update education details",
)
@requires_feature_permission("write")
async def add_or_update_education_details(
    course_name: str,
    education_details: EducationDetails,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Add or Update Education Details\n
    * :*param* **student_id**:\n
    * :*param* **education_details**:\n
    * :*return* **Add or update education details**:
    """
    education_details = {
        k: v for k, v in education_details.model_dump().items() if v is not None
    }
    await StudentHelper().format_education_details(education_details)
    key_value = "education_details"
    user = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": current_user.get("user_name")}
    )
    course = await DatabaseConfiguration().course_collection.find_one(
        {"college_id": ObjectId(user.get("college_id")), "course_name": course_name}
    )
    education_detail = jsonable_encoder(education_details)
    if course is not None:
        if course.get("is_pg"):
            if education_detail.get("graduation_details") is None:
                raise HTTPException(
                    status_code=422,
                    detail="Graduation details required for this course."
                    " Please enter graduation details.",
                )
        response = await StudentHelper().insert_some(
            str(user["_id"]), education_detail, key_value, course_name, college_id=str(user.get("college_id"))
        )
        if response:
            try:
                toml_data = utility_obj.read_current_toml_file()
                if toml_data.get("testing", {}).get("test") is False:
                    # TODO: Not able to add student timeline data
                    #  using celery task when environment is
                    #  demo. We'll remove the condition when
                    #  celery work fine.
                    if settings.environment in ["demo"]:
                        StudentActivity().add_student_timeline(
                            student_id=str(user.get("_id")),
                            event_type="Application",
                            event_status="Updated education details",
                            message="has updated its 'Education'"
                            " details for programme:",
                            college_id=college.get("id"),
                        )
                    else:
                        if not is_testing_env():
                            StudentActivity().add_student_timeline.delay(
                                student_id=str(user.get("_id")),
                                event_type="Application",
                                event_status="Updated education details",
                                message="has updated its 'Education'"
                                " details for programme:",
                                college_id=college.get("id"),
                            )
            except KombuError as celery_error:
                logger.error(
                    f"error storing education details" f" timeline data {celery_error}"
                )
            except Exception as error:
                logger.error(
                    f"error storing education details" f" timeline data {error}"
                )
            return utility_obj.response_model(
                response, message=f"Education details added or" f" updated successfully"
            )
        raise HTTPException(status_code=404, detail="No found.")
    raise HTTPException(status_code=404, detail="Course not found")


@router.post("/document_details/{application_id}/")
@requires_feature_permission("edit")
async def upload_student_documents(
    background_tasks: BackgroundTasks,
    *,
    application_id: str,
    data: upload_docs = Depends(functools.partial(upload_docs)),
    current_user: CurrentUser,
    files: List[UploadFile] = File(..., description="Multiple files " "as UploadFile"),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Upload Student Documentations\n
    Supported File Format : ".png", ".jpg", ".jpeg", ".pdf"
    * :*param* **Upload documents by sequence 1. matrix, 2. secondary,
    3. graduation if available**:\n
    * :*param* **Upload documents**:\n
    * :*return* **all file is uploaded**:
    """
    user = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": current_user.get("user_name")}
    )
    name = utility_obj.name_can(user.get("basic_details"))
    await utility_obj.is_id_length_valid(application_id, "Application id")
    check_payment_status, course_name = await StudentHelper().check_payment(
        application_id)
    if not check_payment_status:
        raise HTTPException(status_code=402, detail="Application fee not paid.")

    await validate_file(attachments=files, college_id=college.get('id'))
    document = await DatabaseConfiguration().studentSecondaryDetails.find_one(
        {"student_id": ObjectId(user.get("_id"))}
    )
    re_upload = None
    if document:
        re_upload = document.get("attachments")
    data = jsonable_encoder(data)
    upload_file = await upload_files(files, str(user["_id"]), course_name, data, college_id=str(college.get("id")))
    if upload_file:
        try:
            toml_data = utility_obj.read_current_toml_file()
            if toml_data.get("testing", {}).get("test") is False:
                # TODO: Not able to add student timeline data in the
                #  DB when performing celery task so added condition
                #  which add student timeline when environment is
                #  not development. We'll remove the condition when
                #  celery work fine.
                message = f"{name} has uploaded its document details"
                if re_upload:
                    await DatabaseConfiguration().studentSecondaryDetails.update_one(
                        {"student_id": ObjectId(user.get("_id"))},
                        {"$set": {"documents_reuploaded": True}}
                    )
                    await DatabaseConfiguration().studentsPrimaryDetails.update_one(
                        {"_id": ObjectId(user.get("_id"))},
                        {"$set": {"dv_status": "Re-verification Pending"}}
                    )
                    await DatabaseConfiguration().studentApplicationForms.update_one(
                        {"student_id": ObjectId(user.get("_id"))},
                        {"$set": {"dv_status": "Re-verification Pending"}}
                    )

                    document_type = "/".join(
                        [key for key, value in data.items() if value is True]
                    )
                    message = f"{name} has re-uploaded " f"a document for {document_type}"
                # TODO: Not able to add student timeline data
                #  using celery task when environment is
                #  demo. We'll remove the condition when
                #  celery work fine.
                if settings.environment in ["demo"]:
                    StudentActivity().student_timeline(
                        student_id=str(user.get("_id")),
                        event_type="Application",
                        event_status="updated document details",
                        message=message,
                        college_id=college.get("id"),
                    )
                else:
                    if not is_testing_env():
                        StudentActivity().student_timeline.delay(
                            student_id=str(user.get("_id")),
                            event_type="Application",
                            event_status="updated document details",
                            message=message,
                            college_id=college.get("id"),
                        )
        except KombuError as celery_error:
            logger.error(f"error storing document timeline data {celery_error}")
        except Exception as error:
            logger.error(f"error storing document timeline data {error}")
        if settings.environment != "demo":
            DocExtraction().text_extraction.delay(student_id=str(user.get("_id")))
        return utility_obj.response_model(True, message="All files are uploaded.")
    raise HTTPException(status_code=422, detail="Failed to upload files.")


@router.get("/get_document/")
@requires_feature_permission("read")
async def get_student_documents(
    current_user: CurrentUser,
    season: str = None,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    get Student Documentations\n
    * :*param* **files**:
    * :*return* **get all documents of current student*:
    """
    student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": current_user.get("user_name")}
    )
    file = await DatabaseConfiguration().studentSecondaryDetails.find_one(
        {"student_id": ObjectId(str(student["_id"]))}
    )
    if file:
        if file.get("attachments"):
            return utility_obj.response_model(
                StudentApplicationHelper().file_helper(
                    file, student.get("_id"), season
                ),
                message="File fetched successfully.",
            )
        raise HTTPException(status_code=404, detail="Document not found.")
    raise HTTPException(status_code=404, detail="Document not found.")


@router.put("/change_password/", summary="Change Password")
@requires_feature_permission("edit")
async def change_password(
    current_user: CurrentUser,
    current_password: str = Query(description="Enter your current password"),
    new_password: str = Query(
        description="Enter your new password", min_length=8, max_length=20
    ),
    confirm_password: str = Query(..., description="Confirm your new password"),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Change Password
    * :*param* **old_password*** e.g., test:
    * :*param* **new_password** e.g., test1:
    * :*param* **confirm_password** e.g., test1:
    * :*return* **Message - New Password updated successfully.**:
    """
    student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if Hash().verify_password(student.get("password"), current_password):
        if new_password != confirm_password:
            raise HTTPException(
                status_code=422,
                detail="New Password and Confirm Password doesn't match.",
            )
        if Hash().verify_password(student.get("password"), new_password):
            raise HTTPException(
                status_code=422,
                detail="Your new password should not match with" " last password.",
            )
        password = Hash().get_password_hash(new_password)
        updated_password = (
            await DatabaseConfiguration().studentsPrimaryDetails.update_one(
                {"_id": ObjectId(student.get("_id"))}, {"$set": {"password": password,
                                                                 "last_password_updated_at": datetime.datetime.utcnow()
                                                                 }}
            )
        )
        if updated_password:
            return utility_obj.response_model(
                data=True, message="Your password has been updated successfully."
            )
        else:
            raise HTTPException(status_code=500, detail="Something went wrong.")
    else:
        raise HTTPException(status_code=400, detail="Current password is incorrect.")


async def subject_of_seconadary(stream):
    """
    Return the secondary subjects
    """
    if "physics" in stream.lower():
        return ["Physics", "Chemistry", "Mathematics", "English"]
    elif "commerce" in stream.lower():
        return ["Commerce", "Economics", "Mathematics", "English"]
    elif "arts" in stream.lower():
        return ["English"]
    raise HTTPException(status_code=404, detail="stream is not available")


@router.get("/inter_school_subject_detail/{stream}")
@requires_feature_permission("read")
async def inter_school_subject(stream: str):
    """
    Return the secondary subjects
    """
    data = await subject_of_seconadary(stream)
    return utility_obj.response_model(data=data, message="data fetch successfully.")


@router.get("/board_detail/")
@requires_feature_permission("read")
async def board_details(
    page_num: Union[int, None] = Query(None, gt=0),
    page_size: Union[int, None] = Query(None, gt=0),
):
    """
    Returns board details
    """
    if page_num and page_size:
        board = await StudentHelper().tenth_inter_board_name(
            page_num, page_size, route_name="/student/board_detail/"
        )
    else:
        board = await StudentHelper().tenth_inter_board_name()
    if board:
        if page_num and page_size:
            return board
        return utility_obj.response_model(
            data=board, message="data fetch successfully."
        )


@router.put("/_beta/basic_details/", response_description="Add or update basic details")
@requires_feature_permission("write")
async def add_or_update_basic_details(
    payload: dict,
    current_user: CurrentUser,
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Add or Update Basic Details\n
    * :*param* **basic_details**:\n
    * :*param* **country iso2 eg. IN **:\n
    * :*param* **state code eg. UP **:\n
    * :*param* **city name eg. city fullname**:\n
    * :*return* **Add or update basic details**:
    """
    basic_details = {k: v for k, v in payload.items() if v is not None}
    if len(basic_details) < 1:
        raise HTTPException(status_code=422, detail="Need to pass atleast one field.")
    user = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if not user:
        raise HTTPException(
            status_code=404, detail="No Student found with this email id"
        )
    await DatabaseConfiguration().studentsPrimaryDetails.update_one(
        {"user_name": user.get("user_name")}, {"$set": basic_details}, upsert=True
    )
    result = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": user.get("user_name")}
    )
    response = StudentCourse().student_primary(result)
    return utility_obj.response_model(
        response, message=f"Basic details added or updated successfully"
    )


@router.put(
    "/add_or_update_details/{course_name}/",
    response_description="Add or update details",
)
@requires_feature_permission("write")
async def add_or_update_parent_details(
    current_user: CurrentUser,
    stage_category: FormStageName,
    course_name: str,
    data: dict,
    name: str = Query(
        None, description="Enter stage name if " "selected stage category is others"
    ),
    college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Add or Update Parent Details
    """
    data = {k: v for k, v in data.items() if v is not None}
    user = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"user_name": current_user.get("user_name")}
    )
    if stage_category.lower() == "others":
        if not name:
            return {"detail": "Need to provide name of stage name."}
        stage_category = name.lower().replace(" ", "_")
    if stage_category.lower() == "education_details":
        course = await DatabaseConfiguration().course_collection.find_one(
            {"college_id": ObjectId(user.get("college_id")), "course_name": course_name}
        )
        if course is not None:
            if course.get("is_pg"):
                if data.get("graduation_details") is None:
                    raise HTTPException(
                        status_code=422,
                        detail="Graduation details required "
                        "for this course. Please enter"
                        " graduation details.",
                    )
    if stage_category == "basic_details":
        response = await StudentHelper().update_basic_details(
            str(user.get("_id")), basic_detail=data, course_name=course_name,
            college_id=str(college.get("id")),
            system_preference=college.get("system_preference")
        )
    elif stage_category == "address_details":
        response = await StudentUserCrudHelper().address_insert(
            str(user["_id"]), data, stage_category, course_name, dynamic=True, college_id=str(user.get("college_id"))
        )
    else:
        response = await StudentHelper().insert_some(
            str(user["_id"]), data, stage_category, course_name, dynamic=True, college_id=str(user.get("college_id"))
        )
    await DatabaseConfiguration().studentsPrimaryDetails.update_one({
        "_id": ObjectId(user.get("_id"))},
        {
            "$set": {"last_accessed": datetime.datetime.utcnow()}
        }
    )
    if response:
        course = await DatabaseConfiguration().course_collection.find_one(
            {"college_id": ObjectId(user.get("college_id")), "course_name": course_name}
        )
        application = await DatabaseConfiguration().studentApplicationForms.find_one(
            {
                "course_id": ObjectId(course.get("_id")),
                "student_id": ObjectId(user.get("_id")),
            }
        )
        if application is None:
            application = {}
        try:
            toml_data = utility_obj.read_current_toml_file()
            if toml_data.get("testing", {}).get("test") is False:
                # TODO: Not able to add student timeline data
                #  using celery task when environment is
                #  demo. We'll remove the condition when
                #  celery work fine.
                if settings.environment in ["demo"]:
                    StudentActivity().add_student_timeline(
                        student_id=str(user.get("_id")),
                        event_type="Application",
                        event_status=f"Updated {stage_category}",
                        message=f"has updated its {stage_category.title().replace('_', ' ')}"
                        f" for programme:",
                        college_id=college.get("id"),
                    )
                else:
                    if not is_testing_env():
                        StudentActivity().add_student_timeline.delay(
                            student_id=str(user.get("_id")),
                            event_type="Application",
                            event_status=f"Updated {stage_category}",
                            message=f"has updated its {stage_category.title().replace('_', ' ')}"
                            f" for programme:",
                            college_id=college.get("id"),
                        )
        except KombuError as celery_error:
            logger.error(
                f"error storing {stage_category} " f"timeline data {celery_error}"
            )
        except Exception as error:
            logger.error(f"error storing {stage_category} " f"timeline data {error}")
        return {
            "data": response,
            "message": f"{stage_category.title().replace('_', ' ')}"
            f" added or updated successfully",
        }
    raise HTTPException(status_code=404, detail="No found.")
