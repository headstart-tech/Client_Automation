"""
The file contains aws s3 related functions.
"""
import csv
import datetime
import inspect
import logging
import pathlib
from pathlib import Path, PurePath
from zipfile import ZipFile

import boto3
from botocore.exceptions import ClientError
from bson.objectid import ObjectId
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException

from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.database.configuration import DatabaseConfiguration
from app.helpers.student_curd.student_application_configuration import \
    StudentApplicationHelper

logger = get_logger(name=__name__)


async def get_download_url(bucket_name, object_name, expire_time=300):
    """
    Return download url of s3 object
    """
    s3_client = settings.s3_client
    download_url = ""
    try:
        download_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
            ExpiresIn=expire_time,
        )
    except Exception as error:
        logger.error(f"An error occurred while downloading recent_photo"
                     f" {error}")
    return download_url


async def upload_file(file, bucket_name, object_name=None):
    """Upload a file to AWS S3 bucket
    * :param file_name: File to upload
    * :param bucket_name: Bucket name where we want to upload file
    * :param object_name: S3 object name. If not specified then file_name is used
    * :return: True if file was uploaded, else False
    """
    file_copy = await utility_obj.temporary_path(file)
    s3 = settings.s3_client

    try:
        with open(file_copy.name, "rb") as f:
            s3.upload_fileobj(f, bucket_name, object_name)
        # response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    finally:
        file_copy.close()  # Remember to close any file instances before removing the temp file
        Path(file_copy.name).unlink()  # unlink (remove) the file
    return True


# Todo: We're not using below function for create unique filename because to generate
#  a unique file name reference S3 seems to be an expensive call.
async def get_unique_name(file_name, bucket_name):
    """
    asynchronous function for get unique name
    """
    name_1 = utility_obj.rename_func()
    split_f = PurePath(file_name).stem
    split_l = PurePath(file_name).suffix
    name_1 = split_f + name_1 + split_l

    s3 = settings.session.resource("s3")
    your_bucket = s3.Bucket(bucket_name)
    ted = your_bucket.objects.all()
    name_of_bucket = [file.key for file in ted]

    if name_1 not in name_of_bucket:
        return name_1
    return get_unique_name(file_name=file_name, bucket_name=bucket_name)


async def upload_files(filename: list, _id: str, course_name: str, data=None, college_id=None):
    """asynchronous function for upload multiple documents of student"""
    dummy = dict()
    data = jsonable_encoder(data)
    name_of_file = ["recent_photo", "tenth", "inter", "adhar_card",
                    "diploma_marksheet", "diploma_certificate", "graduation",
                    "ug_consolidated_mark_sheet"]
    name_of_file = [i for i in name_of_file if data.get(i) is True]
    file_title = data.get("title")
    if not file_title:
        name_of_file.append(file_title)
    else:
        name_of_file.extend(file_title.split(","))
    i = 0
    aws_env = settings.aws_env
    base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
    base_bucket_url = getattr(settings, f"s3_{aws_env}_base_bucket_url")
    document = await DatabaseConfiguration().studentSecondaryDetails.find_one(
        {"student_id": ObjectId(_id)}
    )
    for file in filename:
        extension = PurePath(file.filename).suffix
        unique_filename = utility_obj.create_unique_filename(
            extension=extension)
        season = utility_obj.get_year_based_on_season()
        check = await upload_file(
            file=file,
            bucket_name=base_bucket,
            object_name=f"{utility_obj.get_university_name_s3_folder()}/{season}/{settings.s3_student_documents_bucket_name}/{_id}/{name_of_file[i]}/{unique_filename}",
        )
        fileset = {
            "file_s3_url": f"{base_bucket_url}{utility_obj.get_university_name_s3_folder()}/{season}/{settings.s3_student_documents_bucket_name}/{_id}/"
                           f"{name_of_file[i]}/{unique_filename}",
            "file_name": file.filename,
        }
        if document and "attachments" in document and name_of_file[i] in document["attachments"]:
            existing_doc = document["attachments"][name_of_file[i]]
            reupload_count = existing_doc.get("reupload_count", 0) + 1
            fileset["reuploaded"] = True
            fileset["reupload_count"] = reupload_count

        dummy[name_of_file[i]] = fileset
        if not check:
            raise HTTPException(
                status_code=422, detail="{file.filename} is not uploaded in s3"
            )
        i += 1
    if (
            user := await DatabaseConfiguration().studentSecondaryDetails.find_one(
                {"student_id": ObjectId(_id)})
    ) is not None:
        data = {"attachments": dummy}
        if user.get("attachments"):
            user.get("attachments").update(dummy)
            data = {"attachments": user.get("attachments")}
        await DatabaseConfiguration().studentSecondaryDetails.update_one(
            {"_id": ObjectId(str(user.get("_id")))}, {"$set": data}
        )
        await StudentApplicationHelper().update_stage(
            _id, course_name, 8.75, upload_files=True, college_id=college_id)
        return True
    data = {"attachments": dummy, "student_id": ObjectId(_id)}
    user = await DatabaseConfiguration().studentSecondaryDetails.insert_one(
        data)
    if user:
        await DatabaseConfiguration().studentsPrimaryDetails.update_one({
            "_id": ObjectId(_id)},
            {
                "$set": {"last_accessed": datetime.datetime.utcnow()}
            }
        )
        await StudentApplicationHelper().update_stage(
            _id, course_name, 8.75, upload_files=True, college_id=college_id)
        return True
    return False

async def validate_file(attachments:list, college_id:str):
    """
    Validate file size and format.
    Params:
        - attachments (List): List of files to be validated.
        - college_id (str): ID of the college to fetch specific validation rules.
    Raises:
        - HTTPException: If the file format is unsupported.
        - HTTPException: If the file size exceeds the allowed limit.
    """
    result = await DatabaseConfiguration().client_collection.aggregate(
        [
            {
                '$match': {
                    'client_id': ObjectId(college_id)
                }
            }, {
            '$project': {
                '_id': 0,
                'file_format': 1
            }
        }
        ]
    ).to_list(length=None)

    default_extensions = {".jpg", ".jpeg", ".png", ".doc", ".pdf"}
    default_max_size_mb = 5

    file_format = result[0]['file_format'] if result and 'file_format' in result[0] else {}
    allowed_extensions = set(file_format.get('format', default_extensions))
    max_size_mb = file_format.get('size', default_max_size_mb)

    for file in attachments:
        extension = PurePath(file.filename).suffix
        file_size_mb = len(await file.read()) / 1048576
        if extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {extension}. File: {file.filename}")
        if file_size_mb > max_size_mb:
            raise HTTPException(status_code=400, detail=f"File size exceeds the {max_size_mb} MB limit. File: {file.filename}")

async def upload_multiple_files(files, bucket_name,base_url, path):
    """
    asynchronous function for upload multiple files to an aws s3 bucket
    """
    file_details = []
    for file in files:
        extension = PurePath(file.filename).suffix
        unique_filename = utility_obj.create_unique_filename(
            extension=extension)
        object_key = f"{path}{unique_filename}"
        uploaded_file = await upload_file(
            file=file, bucket_name=bucket_name, object_name=object_key
        )
        if not uploaded_file:
            raise HTTPException(status_code=422,
                                detail="File is not uploaded in s3")
        settings.s3_client.put_object_acl(
            ACL="public-read", Bucket=bucket_name, Key="%s" % object_key
        )
        data = {
            "file_name": f"{unique_filename}",
            "public_url": f"{base_url}{object_key}",
        }
        file_details.append(data)
    return file_details


async def upload_multiple_files_and_return_temporary_urls(files, bucket_name):
    """
    Upload multiple files to an aws s3 bucket and return temporary urls
    """
    season_year = utility_obj.get_year_based_on_season()
    file_details = []
    for file in files:
        extension = PurePath(file.filename).suffix
        unique_filename = utility_obj.create_unique_filename(
            extension=extension)
        path = f"{utility_obj.get_university_name_s3_folder()}/{season_year}/{settings.s3_assets_bucket_name}/{unique_filename}"
        uploaded_file = await upload_file(
            file=file, bucket_name=bucket_name, object_name=path
        )
        if not uploaded_file:
            raise HTTPException(status_code=422,
                                detail="File is not uploaded in s3")
        presigned_url = await get_download_url(
            bucket_name, path, expire_time=1800
        )
        file_details.append({
            "file_name": f"{unique_filename}",
            "public_url": f"{presigned_url}",
        })
    return file_details


async def upload_file_and_return_temporary_public_url(
        file_name, bucket, object_name=None
):
    """Upload a file to an S3 bucket
    Generate a presigned URL to share an S3 object
    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: Presigned URL as string. If error, returns None.
    """
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = Path(file_name).name

    s3_client = settings.s3_client
    # Upload the file
    try:
        with open(file_name, "rb") as f:
            s3_client.upload_fileobj(f, bucket, object_name)
            # Generate a presigned URL for the S3 object
            presigned_url = await get_download_url(
                bucket, object_name
            )
    except ClientError as e:
        logger.error(e)
        return False
    # The response contains the download URL of s3 object
    return presigned_url


async def upload_csv_and_get_public_url(fieldnames, data, name=None):
    """
    Store data into csv, upload that csv file into s3 bucket and return public url of csv file\n
    * :param **fieldnames** description="Fieldnames means columns which we want in a csv file, ":\n
    * :param **data** description="Data which we want to add in a csv file":
    * :param **name** description="Using this field or parameter for define data length and based on data length
     we will write that data in the csv":\n
    * :return **Public url of csv file which uploaded in s3 bucket**:
    """
    fieldnames = fieldnames
    with open("data.csv", "w", encoding="UTF8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        if (
                name == "form_wise_status_data"
                or name == "applications_data"
                or name == "users_data"
                or name == "counselors_data"
                or name == "call_quality_data"
                or name == "offline_data"
        ):
            writer.writerows(data)
        elif name == "utm":
            for dct in data:
                writer.writerow(dct)
        elif name == "lead_application":
            for date, lead, application in zip(data.get('date'),
                                               data.get('lead'),
                                               data.get('application')):
                writer.writerow(
                    {"date": date, "lead": lead, "application": application})
        elif name == "chart_info":
            for label, percentage in zip(data.get('labels'), data.get('data')):
                writer.writerow({"label": label, "percentage": percentage})
        else:
            writer.writerow(data)
    unique_filename = utility_obj.create_unique_filename(extension=".csv")
    aws_env = settings.aws_env
    base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
    base_bucket_url = getattr(settings, f"s3_{aws_env}_base_bucket_url")
    season_year = utility_obj.get_year_based_on_season()
    path = f"{utility_obj.get_university_name_s3_folder()}/{season_year}/{settings.s3_reports_bucket_name}/{unique_filename}"
    temporary_public_url = await upload_file_and_return_temporary_public_url(
        file_name="data.csv",
        bucket=base_bucket,
        object_name=path
    )
    rem_file = pathlib.Path("data.csv")
    rem_file.unlink()
    return {
        "file_url": f"{temporary_public_url}",
        "message": "File downloaded successfully."
    }


async def get_primary_sec_download_link(student_id, college_id):
    student = await DatabaseConfiguration().studentsPrimaryDetails.find_one(
        {"_id": ObjectId(student_id), 'college_id': ObjectId(college_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    documents = await DatabaseConfiguration().studentSecondaryDetails.find_one(
        {"student_id": ObjectId(student_id), "attachments": {"$exists": True}}
    )
    if not documents:
        raise HTTPException(status_code=404,
                            detail="Student documents not found.")

    s3_res = boto3.resource(
        "s3", aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.region_name)
    s3 = settings.s3_client

    path = Path(inspect.getfile(inspect.currentframe())).resolve()
    pth = PurePath(path).parent
    path = PurePath(pth, Path("primary_detail.csv"))
    primary_detail_filename = PurePath(path).name
    path_zip = PurePath(pth, Path("sample.zip"))
    fieldnames = list(student.keys())
    with open(str(path), "w", encoding="UTF8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(student)
    aws_env = settings.aws_env
    base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
    attachments = documents.get("attachments", {})
    with ZipFile(str(path_zip), "w") as zipObj:
        zipObj.write(str(path), arcname=primary_detail_filename)
        if Path(str(path)).is_file():
            Path(str(path)).unlink()
        for document_name, document in attachments.items():
            if document is not None:
                file = document.get("file_s3_url")
                object_name = PurePath(file).name
                path = PurePath(pth, Path(object_name))
                season = utility_obj.get_year_based_on_season()
                object_key = f"{utility_obj.get_university_name_s3_folder()}/{season}/{settings.s3_student_documents_bucket_name}/{student_id}/{document_name}/{object_name}"
                try:
                    s3_res.Bucket(
                        base_bucket).download_file(
                        object_key, str(path)
                    )
                except Exception as error:
                    logger.error(f"Error downloading file %s: %s", object_name,
                                 error)
                try:
                    zipObj.write(str(path), arcname=f"{document_name}/{object_name}")
                except FileNotFoundError as error:
                    logger.error(f"Error write the file inn zipObj {error}", )
                if Path(str(path)).is_file():
                    Path(str(path)).unlink()
    unique_filename = utility_obj.create_unique_filename(extension=".zip")
    path_to_unique_filename = f"{utility_obj.get_university_name_s3_folder()}/{settings.s3_download_bucket_name}/{unique_filename}"
    try:
        with open(str(path_zip), "rb") as f:
            s3.upload_fileobj(
                f, base_bucket, path_to_unique_filename
            )
    except ClientError as e:
        logging.error(e)
        return False
    finally:
        if Path(str(path_zip)).is_file():
            Path(str(path_zip)).unlink()  # unlink (remove) the file
    zip_s3_url = await get_download_url(
        base_bucket, path_to_unique_filename
    )
    return zip_s3_url


async def get_attachment_information(template_information: dict) -> list:
    """
    Get the attachments information which useful when sending mail.

    Params:
        - template_information (dict): A dictionary which contains information about template.

    Returns:
        - list: A list which contains information about attachments.
    """
    documents, attachments = template_information.get("attachment_document_link", []), []
    if isinstance(template_information, dict) and isinstance(documents, list) and documents:
        season = utility_obj.get_year_based_on_season()
        path = Path(inspect.getfile(inspect.currentframe())).resolve()
        path = PurePath(path).parent
        s3_res = boto3.resource(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.region_name,
        )
        aws_env = settings.aws_env
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        for document in documents:
            if document != "":
                file_name = PurePath(document).name
                object_key = (
                    f"{utility_obj.get_university_name_s3_folder()}/"
                    f"{season}/"
                    f"{settings.s3_assets_bucket_name}/"
                    f"template-gallery/{file_name}"
                )
                file_name = PurePath(file_name).name
                path = str(PurePath(path, Path(file_name)))
                try:
                    s3_res.Bucket(base_bucket).download_file(object_key, path)
                except Exception as e:
                    logger.error(
                        f"Something went wrong while downloading attachments: {e}"
                    )
                    continue
                attachments.append(path)
    return attachments
