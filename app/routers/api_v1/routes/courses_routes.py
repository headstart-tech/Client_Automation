"""
This file contains API routes related to course
"""
from typing import Union
from bson import ObjectId
from fastapi import APIRouter, Body, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from app.core.custom_error import (CustomError, ObjectIdInValid,
                                   DataNotFoundError)
from app.core.log_config import get_logger
from app.core.utils import utility_obj, requires_feature_permission
from app.dependencies.college import get_college_id_short_version
from app.dependencies.oauth import (CurrentUser, cache_invalidation,
                                    Is_testing)
from app.helpers.course_configuration import CourseHelper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.course_schema import Course, UpdateCourse, \
    UpdateCourseStatus, CourseCategory, CourseSpecialization, \
    UpdateCourseSpecializations, AcademicCategory
from app.core.reset_credentials import Reset_the_settings

course_router = APIRouter()
logger = get_logger(name=__name__)


@course_router.post("/create/", response_description="Create new course")
@requires_feature_permission("write")
async def create_course(
        current_user: CurrentUser,
        course: Course,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Create New Course\n
    * :*param* **college_id**: e.g. 624e8d6a92cc415f1f578a24\n
    * :*param* **course_name**: e.g. Bsc\n
    * :*param* **course_description**: e.g. Bachelor of Technology\n
    * :*param* **course_specialization**: e.g. ["Mathematics", "Chemistry"]\n
    * :*param* **duration** (In Years): e.g. 3\n
    * :*param* **fees** (In Rs): e.g. 60000\n
    * :*param* **is_activated**: e.g. true\n
    * :*param* **banner_image_url**: e.g. ./resource.txt#frag01\n
    * :*return* **Create new course and reply with message 'New course
    created successfully.'**:
    """
    await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"],
        condition=False)
    course = jsonable_encoder(course)
    course = await CourseHelper().create_new_course(course, college.get("id"))
    await cache_invalidation(api_updated="course/create/")
    if course:
        return utility_obj.response_model(
            data=course, message="New course created successfully.")
    raise HTTPException(status_code=400, detail="Course already exist.")


@course_router.put("/edit/", response_description="Edit course")
@requires_feature_permission("edit")
async def edit_course(
        current_user: CurrentUser,
        course: UpdateCourse = Body(...),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        course_id: str = Query(
            ..., description="Course ID\n* e.g.,"
                             "**62551f6d7a3f3d06d4196b7f**"
        ),
):
    """
    Edit Course
    * :*param* **college_id**: e.g. 624e8d6a92cc415f1f578a24\n
    * :*param* **course_id**: e.g. 62551f6d7a3f3d06d4196b7f\n
    * :*param* **course_name**: e.g. Bsc\n
    * :*param* **course_description**: e.g. Bachelor of Technology\n
    * :*param* **course_specialization**: e.g. ["Mathematics", "Chemistry"]\n
    * :*param* **duration** (In Years): e.g. 3\n
    * :*param* **fees** (In Rs): e.g. 60000\n
    * :*param* **is_activated**: e.g. true\n
    * :*param* **banner_image_url**: e.g. ./resource.txt#frag01\n
    * :*return* **Edit course and reply with message 'Updated data.'**:
    """
    await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"],
        condition=False)
    course = {k: v for k, v in course.model_dump().items() if v is not None}
    if len(course) < 1:
        raise HTTPException(
            status_code=422, detail="Need to pass atleast 1 field to "
                                    "update course."
        )
    new_course = await CourseHelper().update_course(
        course, college.get("id"), course_id)
    await cache_invalidation(api_updated="course/edit")
    if new_course:
        return utility_obj.response_model(new_course,
                                          "Course updated successfully.")


@course_router.put("/status/", response_description="Enable or disable course")
@requires_feature_permission("edit")
async def course_status(
        current_user: CurrentUser,
        update_status: UpdateCourseStatus,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        course_id: str = Query(
            ..., description="Course ID " "\n* e.g., "
                             "**62551f6d7a3f3d06d4196b7f**"
        )
):
    """
    Enable or Disable Course\n
    * :*param* **college_id**: e.g. 624e8d6a92cc415f1f578a24\n
    * :*param* **course_id** e.g. 62551f6d7a3f3d06d4196b7f:
    * :*param* **is_activated**: e.g. true\n
    * :*return* **Update course status**:
    """
    await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"],
        condition=False)
    if not (update_status.is_activated is False or
            update_status.is_activated is True):
        raise HTTPException(422, detail="Field 'is_activated' "
                                        "should not be empty.")
    update_status = jsonable_encoder(update_status)
    updated_status, course = await CourseHelper().update_course_status(
        update_status, college.get("id"), course_id)
    if updated_status:
        return utility_obj.response_model(
            updated_status, "Course status updated successfully.")


@course_router.get("/list/", response_description="List of course")
async def course_list(
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        page_num: Union[int, None] = Query(None, gt=0),
        page_size: Union[int, None] = Query(None, gt=0),
        course_names: str = Query(None, description="name of courses"),
        category: CourseCategory = None,
        show_disable_courses: bool = Query(
            False, description="Useful for show disable courses to user. "
                               "When value is true then We'll show both active"
                               " and deactivate courses"),
        academic_category:  AcademicCategory = None
):
    """
    List of Course\n
    * :*param* **college_id** e.g. 624e8d6a92cc415f1f578a24:
    * :*return* **List of course**:
    """
    return await CourseHelper().retrieve_courses(
        college.get("id"), page_num, page_size, route_name="/course/list/",
        course_names=course_names, category=category,
        show_disable_courses=show_disable_courses, academic_category=academic_category
    )


@course_router.get(
    "/specialization_list/",
    response_description="List of course specializations"
)
async def specialization_list(
        testing: Is_testing,
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        course_id: str | None = Query(
            None, description="Course ID \n* e.g., "
                              "**62551f6d7a3f3d06d4196b7f**"
        ),
        course_name: str | None = Query(
            None, description="Course name \n* e.g., **b.tech**"),
        student_id: str | None = Query(
            None, description="Enter student id when want to get "
                              "available specialization (s) information for "
                              "student. \n* e.g., **b.tech**"),
):
    """
    List of Course Specializations.\n

    Params:\n
        - college_id: Required field. Useful for get particular college
            course specialization (s) information.
            e.g., 624e8d6a92cc415f1f578a24\n
        - course_id: Optional field. Useful for get college course
            specialization (s) information by course_id.
            e.g. 62551f6d7a3f3d06d4196b7f\n
        - course_name: Optional field. Useful for get college course
            specialization (s) information by course_id.
            e.g., b.tech\n
        - student_id: Optional field. Useful when want to show course
            specialization (s) list based on student.
            e.g. 62551f6d7a3f3d06d4196b72\n

    Returns:\n
        - dict: A dictionary which contains list of course specializations
            along with message.
    """
    try:
        if student_id:
            await utility_obj.is_length_valid(student_id, "Student id")
        if not testing:
            Reset_the_settings().check_college_mapped(college.get("id"))
        return utility_obj.response_model(
            await CourseHelper().retrieve_specialization_list(
                college.get("id"), course_id, course_name, student_id
            ),
            "Course specializations data fetched successfully."
        )
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        logger.error(
            f"An error got when get the specialization (s) list. "
            f"Error - {error}")
        raise HTTPException(
            status_code=500, detail=f"An error got when get the "
                                    f"specialization (s) list. "
                                    f"Error - {error}")


@course_router.post("/add_specializations/",
                    summary="Add specializations to the course")
@requires_feature_permission("write")
async def add_specializations_to_course(
        current_user: CurrentUser,
        new_course_specs: list[CourseSpecialization],
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        course_id: str = Query(
            None, description="Course ID \n* e.g., "
                              "**62551f6d7a3f3d06d4196b7f**"
        ),
        course_name: str = Query(
            None, description="Course name \n* e.g., **B.Tech.**"),
):
    """
    Add specializations to the course.

    Params:
        - college_id (str): Required field. A unique id of a college.
            e.g., 123456789012345678901234
        - course_id (str): Optional field. A unique id of a course.
            e.g., 123456789012345678901231
        - course_name (str): Optional field. Name of a course.
            e.g., B.Tech.

    Request body parameters:
        new_course_specs (list[CourseSpecialization]): An object of
            pydantic class `CourseSpecialization`
            which contains following fields:
                - current_spec_name (str): A specialization which need to
                    update. e.g. test
                - spec_name (str): Specialization name if user want to update
                    specialization name. e.g., test1
                - is_activated (bool): Specialization activation status when
                    user want update specialization activation status.

    Returns:
        dict: A dictionary which contains course specializations update info.

    Raises:
        ObjectIdInValid: An exception which occur when course id will
            be wrong.
        CustomError: An exception which occur when certain condition fails.
        Exception: An exception which occur when got error other than
            ObjectIdInValid and CustomError.
    """
    await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"],
        condition=False)
    new_course_specs = jsonable_encoder(new_course_specs)
    try:
        return await CourseHelper().add_course_specs(
            course_id, course_name, new_course_specs,
            ObjectId(college.get('id')))
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=422, detail=error.message)
    except Exception as error:
        logger.exception(
            f"An error occurred when add specializations of course. Error: {error}")
        raise HTTPException(
            status_code=500, detail=f"An error occurred when add "
                                    f"specializations of course. Error: {error}")


@course_router.put("/update_specializations/",
                   summary="Update specializations of the course")
@requires_feature_permission("edit")
async def update_specializations_of_course(
        current_user: CurrentUser,
        update_course_specs: list[UpdateCourseSpecializations],
        college: dict = Depends(get_college_id_short_version(short_version=True)),
        course_id: str = Query(
            None, description="Course ID \n* e.g., "
                              "**62551f6d7a3f3d06d4196b7f**"
        ),
        course_name: str = Query(
            None, description="Course name \n* e.g., **B.Tech.**"),
):
    """
    Update existing specializations

    Params:
        - college_id (str): Required field. A unique id of a college.
            e.g., 123456789012345678901234
        - course_id (str): Optional field. A unique id of a course.
            e.g., 123456789012345678901231
        - course_name (str): Optional field. Name of a course.
            e.g., B.Tech.

    Request body parameters:
        new_course_specs (list[UpdateCourseSpecializations]): An object of
            pydantic class `UpdateCourseSpecializations`
            which contains following fields:
                - current_spec_name (str): A specialization which need to
                    update. e.g. test
                - spec_name (str): Specialization name if user want to update
                    specialization name. e.g., test1
                - is_activated (bool): Specialization activation status when
                    user want update specialization activation status.

    Returns:
        dict: A dictionary which contains course specializations update info.

    Raises:
        ObjectIdInValid: An exception which occur when course id will
            be wrong.
        CustomError: An exception which occur when certain condition fails.
        Exception: An exception which occur when got error other than
            ObjectIdInValid and CustomError.
    """
    await UserHelper().check_user_has_permission(
        current_user, check_roles=["college_super_admin", "college_admin"],
        condition=False)
    update_course_specs = jsonable_encoder(update_course_specs)
    try:
        return await CourseHelper().update_course_specs(
            course_id, course_name, update_course_specs,
            ObjectId(college.get('id')))
    except ObjectIdInValid as error:
        raise HTTPException(status_code=422, detail=error.message)
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except Exception as error:
        logger.exception(
            f"An error occurred when update specializations. Error: {error}")
        raise HTTPException(
            status_code=500, detail=f"An error occurred when update "
                                    f"specializations. Error: {error}")
