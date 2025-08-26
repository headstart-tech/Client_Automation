'''
This file contains API routes related to get extracted info of student
documents.
'''
from pathlib import Path as path
from pathlib import PurePath

import boto3
from bson import ObjectId
from fastapi import APIRouter, Depends, Path, Query
from fastapi.exceptions import HTTPException

from app.background_task.doc_text_extraction import \
    update_extracted_document_data
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import CurrentUser, cache_dependency, insert_data_in_cache, cache_invalidation, \
    get_collection_from_cache, store_collection_in_cache
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.student_user_schema import User
from app.s3_events.s3_events_configuration import get_download_url

ExtractionRouter = APIRouter()
logger = get_logger(name=__name__)


async def get_details(student_id, index, season_year):
    """
    get the extracted details
    Params:
     student_id (str): unique id of student
     index (int): depending on the index send the respective data. If index= 0 then recent_photo
           if index=1 then tenth ....
     season_year (int): current season year
    Return:
        result dict
    """
    data, result = [], {}
    labels = {"recent_photo": "Recent Photo", "tenth": "10th",
              "inter": "12th", "graduation": "Graduation",
              "ug_consolidated_mark_sheet": "UG", "high_school": ""}
    analysis_names = {"tenth": "high_school_analysis", "inter": "senior_school_analysis",
                      "graduation": "graduation_analysis", "ug_consolidated_mark_sheet": "graduation_analysis"}
    if (stu_pri := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"_id": ObjectId(student_id)}
    )) is None:
        raise HTTPException(status_code=404,
                            detail="Student not found")
    if (stu_sec := await DatabaseConfiguration().studentSecondaryDetails.find_one(
        {"student_id": ObjectId(student_id), "attachments": {"$exists": True}}
    )) is None:
        raise HTTPException(status_code=404,
                            detail="Student documents not found.")
    attachments = stu_sec.get("attachments")
    total_count = len(attachments) - 1
    if index not in attachments:
        raise HTTPException(status_code=404,
                            detail=f"{index} document not found.")
    doc = attachments.get(index)
    doc_link = doc.get("file_s3_url")
    file_name = PurePath(doc_link).name
    user_value, ocr_value, accuracy, fields_name = {}, {}, {}, {}
    aws_env = settings.aws_env
    base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
    object_key = f"{utility_obj.get_university_name_s3_folder()}/{season_year}/{settings.s3_student_documents_bucket_name}/{student_id}/{index}/{file_name}"
    url = await get_download_url(
        base_bucket, object_key)
    temp_result = {
        "doc_name": index,
        "label_name": f"{labels.get(index,'')} MarkSheet" if index in ["tenth", "inter"] else labels.get(index,'')
                       if index in ["recent_photo", "graduation"] else index,
        "doc_link": doc_link,
        "download_url": url
    }
    if index not in ["tenth", "inter", "graduation", "ug_consolidated_mark_sheet"]:
        temp_result.update({"fields_name": {},
                            "user_value": {},
                            "ocr_value": {},
                            "accuracy": {}
                            })
    else:
        edu = stu_sec.get("education_details")
        school = edu.get(f"{index}_school_details", {}) if index != "graduation" else edu.get(f"{index}_details", {})
        if index in ["tenth", "inter"]:
            board_name = school.get("board")
            email_field_name = "tenth_document_verification_website" \
                             if index == "tenth" else "twelve_document_verification_website" if index == "inter" else ""
            board_details = await get_collection_from_cache(collection_name="board_details")
            if board_details:
                board_data = utility_obj.search_for_document(
                    collection=board_details,
                    field="board_name",
                    search_name=board_name
                )
            else:
                board_data = await DatabaseConfiguration().tenth_twelve_board_details.find_one(
                    {"board_name": board_name, email_field_name: {"$exists": True}})
                collections = await DatabaseConfiguration().tenth_twelve_board_details.aggregate([]).to_list(None)
                await store_collection_in_cache(collections, collection_name="board_details")
            if board_data and board_data.get(email_field_name):
                website_url = board_data.get(email_field_name, "")
                temp_result.update({"external_link": website_url})
        doc_analysis = stu_sec.get("document_analysis", {})
        present_doc_analysis = doc_analysis.get(analysis_names[index], {})
        doc_data = present_doc_analysis.get("data", {})
        fields_name.update({"applicant_name": "Applicant Name",
                            "DOB": "DOB",
                            f"{index}_board": f"{labels[index]} Board"
                            if index not in ["graduation", "ug_consolidated_mark_sheet"]
                            else "UG College",
                            f"{index}_roll_number": f"{labels[index]} Board Roll Number"
                            if index not in ["graduation", "ug_consolidated_mark_sheet"]
                            else f"{labels[index]} Roll Number",
                            f"{index}_marks": f"{labels[index]} Marks",
                            f"{index}_pass_year": f"{labels[index]} Pass out Year"
                            })
        basic_details = stu_pri.get("basic_details", {})
        name = utility_obj.name_can(basic_details)
        user_value.update({
            "applicant_name": name,
            "DOB": basic_details.get("date_of_birth", ""),
            f"{index}_board": school.get("board", ""),
            f"{index}_roll_number": school.get(f"{index}_registration_number", ''),
            f"{index}_marks": school.get("obtained_cgpa", ""),
            f"{index}_pass_year": school.get("year_of_passing", "")
        })
        if doc_analysis and present_doc_analysis and doc_data:
            ocr_value.update({
                "applicant_name": doc_data.get("name"),
                "DOB": doc_data.get("date_of_birth"),
                f"{index}_board": doc_data.get("board", ""),
                f"{index}_roll_number": doc_data.get("registration_number", ''),
                f"{index}_marks": school.get("obtained_cgpa", ""),
                f"{index}_pass_year": school.get("year_of_passing", "")
            })
            accuracy.update({
                "applicant_name": doc_data.get("name_accuracy"),
                "DOB": doc_data.get("date_of_birth_accuracy"),
                f"{index}_board": doc_data.get("board_accuracy", ""),
                f"{index}_roll_number": doc_data.get("registration_number_accuracy", ''),
                f"{index}_marks": school.get("obtained_cgpa_accuracy", ""),
                f"{index}_pass_year": school.get("year_of_passing_accuracy", "")
            })
        if index == "inter":
            if edu is not None and \
                    (school := edu.get(f"inter_school_details")) is not None and \
                    (marks := school.get(f"inter_subject_wise_details")) is not None:
                marks = list(marks)
                subject_wise = doc_data.get("subject_wise_marks", {})
                subject_wise_confidence = doc_data.get("subject_wise_confidence", {})
                for sub in marks:
                    subject = sub.get('subject_name')
                    if doc_analysis and present_doc_analysis and doc_data and subject_wise:
                        fields_name.update({
                            f"{subject}_marks": f"{subject} Marks"
                        })
                        user_value.update({
                            f"{subject}_marks": sub.get('obtained_marks')
                        })
                        ocr_value.update({
                            f"{subject}_marks": subject_wise.get(subject.upper(), "")
                        })
                        accuracy.update({
                            f"{subject}_marks": subject_wise_confidence.get(subject.upper(), "")
                        })
        if not ocr_value and not accuracy:
            fields_name, user_value = {}, {}
        temp_result.update(
            {"fields_name": fields_name, "user_value": user_value, "ocr_value": ocr_value, "accuracy": accuracy})
    data.append(temp_result)
    result.update({
        "total_doc": total_count,
        "data": data
    })

    return result


@ExtractionRouter.get(
    "/text_extraction_info/{student_id}/",
    summary="Get extracted data of student documents"
)
@requires_feature_permission("read")
async def get_extracted_details(
        current_user: CurrentUser,
        index: str,
        student_id: str = Path(
            description="ID of a student you'd like to view data ""\n*e.g., "
                        "**6223040bea8c8768d96d3880**", ),
        college_id: dict = Depends(get_college_id_short_version(short_version=True)),
        season: str = None,
        cache_data = Depends(cache_dependency)


):
    await UserHelper().is_valid_user(user_name=current_user)
    cache_key, data = cache_data
    if data:
        return data
    await utility_obj.is_id_length_valid(student_id, "Student id")
    season_year = utility_obj.get_year_based_on_season(season)
    result = await get_details(student_id, index, season_year)
    if cache_key:
        await insert_data_in_cache(cache_key, result)
    return result


@ExtractionRouter.get(
    "/retry_extraction/",
    summary="Get extracted data of student documents"
)
@requires_feature_permission("read")
async def get_extracted_details(
        current_user: CurrentUser,
        student_id: str = Query(
            description="ID of a student you'd like to view data ""\n*e.g., "
                        "**6223040bea8c8768d96d3880**", ),
        doc_type: str = Query(
            description="File to retry" ),
        college_id: dict = Depends(get_college_id_short_version(short_version=True)),
        season:str =None,
):
    user = await UserHelper().is_valid_user(user_name=current_user)
    if settings.environment != "demo":
        await utility_obj.is_id_length_valid(student_id, "Student id")
        season_year = utility_obj.get_year_based_on_season(season)
        student = await DatabaseConfiguration().studentSecondaryDetails.find_one(
            {"student_id": ObjectId(student_id)}
        )
        if not student:
            raise HTTPException(status_code=404,
                                detail="Student document not found")
        s3_res = boto3.resource(
            "s3", aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.region_name)
        aws_env = settings.aws_env
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        if doc_type in student.get('attachments', {}):
            file = student['attachments'][doc_type]['file_s3_url']
            file_name = PurePath(file).name
            file_path = path(file_name)
            try:
                object_key = f"{utility_obj.get_university_name_s3_folder()}/{season_year}/{settings.s3_student_documents_bucket_name}/{student_id}/{doc_type}/{file_name}"
                s3_res.Bucket(base_bucket).download_file(
                    object_key, file_name
                )
                field_name = "high_school" if doc_type == "tenth" else "senior_school" if doc_type == "inter" else "graduation"
                update_extracted_document_data(file_name, ObjectId(student_id), doc_type, field_name)
                await cache_invalidation(api_updated="retry_extraction/")
            except Exception as e:
                logger.error(f"Error in text extraction: {e}")
            finally:
                if file_path.is_file():
                    file_path.unlink()
            return {"message": "Text Extraction done once again."}
    return {"message": "Text Extraction does not work on Demo environment!"}

