"""
This file contain API route/endpoint for download log file
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.core.utils import settings, utility_obj
from app.s3_events.s3_events_configuration import (
    upload_file_and_return_temporary_public_url,
)

logs = APIRouter()


class LogFileHandler:
    """
    Contain functions related to log file
    """

    def latest_file(self, path: Path, pattern: str = "*"):
        """
        Find the latest log file when requested
        """
        files = path.glob(pattern)
        return max(files, key=lambda x: x.stat().st_ctime)

    def log_file_download(self):
        """
        Get recent log_file which can be directly download
        :return: logs file path
        """
        path = Path("logs")
        file = self.latest_file(path)
        return file


@logs.get("/")
async def log_file():
    """
    Recent Log File Download
    Upload recent log file in S3 bucket and return temporary downloadable public url
    """
    file = LogFileHandler().log_file_download()
    season_year = utility_obj.get_year_based_on_season()
    aws_env = settings.aws_env
    base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
    path = f"{utility_obj.get_university_name_s3_folder()}/{season_year}/{settings.s3_reports_bucket_name}/{file}"
    response = await upload_file_and_return_temporary_public_url(
        file, base_bucket, path
    )
    if not response:
        raise HTTPException(
            status_code=422, detail="File is not uploaded in s3 check logs"
        )
    return JSONResponse(status_code=200, content=response)
