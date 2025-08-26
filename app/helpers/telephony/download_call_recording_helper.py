"""
Download call recordings from mcube to our s3 server.
"""

from app.database.configuration import DatabaseConfiguration
from app.core.utils import settings, utility_obj
from fastapi.exceptions import HTTPException
from app.s3_events.s3_events_configuration import upload_multiple_files
from app.helpers.telephony.outbound_call_summary_helper import OutboundCallSummary
from app.helpers.telephony.inbound_call_summary_helper import InboundCallSummary
from bson.objectid import ObjectId
from fastapi import UploadFile
import aiohttp
import io


class CallRecording:
    """
    all related functions to download and store call recordings
    """

    async def download_file(self, url: str) -> list[UploadFile]:
        """
        Download audio from given url.

        Params:
            url (str): call recording url

        Returns:
            list[UploadFile]: Downloaded file instance
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Failed to download file from url.")
                file_content =  await response.read()

                # Create an in-memory file-like object
                in_memory_file = io.BytesIO(file_content)

                # Create an UploadFile object from the in-memory file
                upload_file = UploadFile(filename="recording_file", file=in_memory_file)
                return [upload_file]
            

    async def download_recording_helper(self, call: dict) -> dict:
        """
        Download call records from mcube to s3 server

        Params:
            call (dict): Call details

        Returns:
            dict: Message response
        """

        fixed_url = call.get("mcube_file_path").replace("\\", "")

        file_content = await self.download_file(fixed_url)

        aws_env = settings.aws_env
        season = utility_obj.get_year_based_on_season()
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        student_id = str(call.get("call_to")) if call.get("type") == "Outbound" else str(call.get("call_from"))
        if student_id == None:
            student_id = "unknown"
        base_bucket_url = getattr(settings, f"s3_{aws_env}_base_bucket_url")
        upload_files = await upload_multiple_files(
            files=file_content,
            bucket_name=base_bucket,
            base_url=base_bucket_url,
            path=f"{utility_obj.get_university_name_s3_folder()}/{season}/{settings.s3_student_documents_bucket_name}/"
                 f"{student_id}/call_recordings/"
        )
        
        await DatabaseConfiguration().call_activity_collection.update_one({
                "_id": call.get("_id")
            }, 
            {
                "$set": {
                    "recording": upload_files[0].get("public_url") if upload_files else None
                }
            }
        )

        data = await DatabaseConfiguration().call_activity_collection.find_one({
            "_id": call.get("_id")
        })

        response = await OutboundCallSummary().call_data_helper(data) if data.get("type") == "Outbound" else await InboundCallSummary().call_data_helper(data)

        return response