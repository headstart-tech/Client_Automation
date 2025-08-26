import logging
from io import StringIO

import aiobotocore
import boto3
import pandas as pd
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi.exceptions import HTTPException

from app.core.utils import settings, utility_obj

logger = logging.getLogger(__name__)

"""
For Asynchronous Events
"""


class S3_SERVICE(object):
    def __init__(
        self, aws_access_key_id, aws_secret_access_key, region, *args, **kwargs
    ):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region = region

    async def upload_fileobj(self, fileobject, bucket, key):
        session = aiobotocore.get_session()
        async with session.create_client(
            "s3",
            region_name=self.region,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_access_key_id=self.aws_access_key_id,
        ) as client:
            file_upload_response = await client.put_object(
                ACL="public-read", Bucket=bucket, Key=key, Body=fileobject
            )

            if file_upload_response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                logger.info(
                    f"File uploaded path : https://{bucket}.s3.{self.region}.amazonaws.com/{key}"
                )
                return True
        return False

    async def upload_to_aws(self, local_file, bucket, s3_file):
        s3 = settings.s3_client

        try:
            s3.get_object(Bucket=bucket, Key=s3_file)
        except ClientError as ex:
            if ex.response["Error"]["Code"] == "NoSuchKey":
                logger.info("No object found - returning empty")
            try:
                s3.upload_file(f"{local_file}", bucket, s3_file)
                print("Upload Successful")
                return True
            except FileNotFoundError:
                print("The file was not found")
                return False
            except NoCredentialsError:
                print("Credentials not available")
                return False
        else:
            raise HTTPException(
                status_code=422,
                detail=f"Filename {s3_file} already exist in s3 bucket.\nChange name of file or delete exist file.",
            )

    async def delete_from_s3(self, model):
        season_year = utility_obj.get_year_based_on_season()
        aws_env = settings.aws_env
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        try:
            path = f"{utility_obj.get_university_name_s3_folder()}/{season_year}/{settings.s3_public_bucket_name}/{model}"
            async with settings.s3_client as s3:
                await s3.delete_object(Bucket=base_bucket, Key=path)
                return True
        except Exception as ex:
            logger.error(str(ex))
            return False

    async def read_csv_from_s3(self, bucket_name, object_key):
        client = settings.s3_client

        csv_obj = client.get_object(Bucket=bucket_name, Key=object_key)
        body = csv_obj["Body"]
        csv_string = body.read().decode("utf-8")
        df = pd.read_csv(StringIO(csv_string))
        return df
