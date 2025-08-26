"""
This file contain class and functions related to reports
"""
from datetime import datetime
from botocore.exceptions import ClientError
from bson import ObjectId
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.database.configuration import DatabaseConfiguration
from app.helpers.report.update_report_status import ReportStatusHelper
from app.helpers.report.report_configuration import ReportHelper
from app.s3_events.s3_events_configuration import get_download_url
import boto3
from pathlib import Path, PurePath
import inspect
from zipfile import ZipFile

logger = get_logger(name=__name__)


class Report:
    """
    Contain functions related to report activities
    """

    async def return_pipeline_for_perform_aggregation_on_collection_reports(
            self, start_date, end_date, college_id, reschedule_report,
            auto_schedule_reports=False, search_pattern=None
    ):
        """
        Get pipeline for perform aggregation on the collection reports
        """
        match_stage = {"requested_on": {"$gte": start_date, "$lte": end_date},
                       'college_id': college_id,
                       "save_template": {"$in": [None, False]}}
        if search_pattern not in ["", None]:
            match_stage.update(
                {"report_name": {"$regex": f".*{search_pattern}.*",
                                 "$options": "i"}})
        for _id, item in enumerate([reschedule_report, auto_schedule_reports]):
            key_name = "reschedule_report" if _id == 0 else "is_auto_schedule"
            if item:
                match_stage.update({key_name: True})
            else:
                match_stage.update(
                    {key_name: {"$in": [None, False]}})
        pipeline = [
            {"$match": match_stage},
            {"$sort": {"requested_on": -1}},
        ]
        return pipeline

    async def reports_data(self, pipeline, skip, limit, request, college,
                           action_type="system"):
        """
        Get reports data
        """
        from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache
        pipeline.append(
            {
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            }
        )
        result = DatabaseConfiguration().report_collection.aggregate(pipeline)
        reports, total_data = [], 0
        states = await get_collection_from_cache(collection_name="states")
        async for documents in result:
            try:
                total_data = documents.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
            for data in documents.get("paginated_results"):
                time_difference = datetime.utcnow() - data.get("requested_on")
                time = time_difference.total_seconds() / 60
                period = data.get("period")
                requested_on = \
                    f"{utility_obj.get_local_time(data.get('requested_on'))}"
                period = await ReportHelper().get_period_in_proper_format(
                    period, requested_on)
                report_data = {
                    "statement": data.get("statement"),
                    "report_id": str(data.get("_id")),
                    "request_id": data.get("request_id"),
                    "report_type": data.get("report_type"),
                    "format": data.get("format"),
                    "requested_on": requested_on,
                    "user_type": await utility_obj.get_role_name_in_proper_format(
                        data.get("user_type")),
                    "requested_by": str(data.get("requested_by")),
                    "requested_by_name": data.get("requested_by_name"),
                    "record_count": data.get("record_count", 0),
                    "period": period,
                    "sent_mail": data.get("sent_mail", False),
                    "is_auto_schedule": data.get("is_auto_schedule", False),
                    "send_mail_recipients_info": data.get("recipient_details"),
                    "report_name": data.get("report_name"),
                    "advance_filter": data.get("advance_filter"),
                    "add_column": data.get("add_column")
                }
                if data.get('reschedule_report'):
                    report_data.update(
                        {'schedule_type': data.get('schedule_type'),
                         'schedule_value': data.get('schedule_value')})
                if data.get("payload"):
                    counselor_names, state_names = [], []
                    for item in data.get('payload', {}).get('counselor_id',
                                                            []):
                        counselor_names.append(utility_obj.name_can(
                            await DatabaseConfiguration().user_collection.find_one(
                                {'_id': ObjectId(item)})))
                    for state_code in data.get('payload', {}).get('state_code',
                                                                  []):
                        if states:
                            state = utility_obj.search_for_document_two_fields(states,
                                                                               field1="state_code",
                                                                               field1_search_name=str(state_code).upper(),
                                                                               field2="country_code",
                                                                               field2_search_name="IN"
                                                                               )
                        else:
                            state = await DatabaseConfiguration().state_collection.find_one(
                                {'state_code': str(state_code).upper(),
                                 'country_code': "IN"})
                        state_names.append(state.get('name'))
                    data['payload']['counselor_names'] = counselor_names
                    data['payload']['state_names'] = state_names
                    report_data.update(
                        {"payload": data.get("payload")}
                    )
                if data.get("report_details"):
                    report_data.update(
                        {"report_details": data.get("report_details")}
                    )
                if data.get("date_range"):
                    report_data.update(
                        {"date_range": data.get("date_range")}
                    )
                auto_schedule_info = data.get('generate_and_reschedule', {})
                if auto_schedule_info and \
                        auto_schedule_info.get("trigger_by"):
                    start_date = auto_schedule_info.get(
                        'date_range', {}).get("start_date")
                    last_trigger_time = data.get("last_trigger_time")
                    next_trigger_time = data.get("next_trigger_time")
                    if start_date:
                        start_date, end_date = await utility_obj.date_change_format(
                            start_date, start_date)
                    report_data.update(
                        {"interval": auto_schedule_info.get("interval"),
                         "trigger_by": auto_schedule_info.get("trigger_by"),
                         "start_date": f"{utility_obj.get_local_time(start_date)}"
                         if start_date else None,
                         "last_trigger_time":
                             f"{utility_obj.get_local_time(last_trigger_time)}"
                             if last_trigger_time else None,
                         "next_trigger_time": f"{utility_obj.get_local_time(next_trigger_time)}"
                         if next_trigger_time else None,
                         "recipient_info": auto_schedule_info.get(
                             "recipient_details")
                         })
                if data.get("status") == "In progress" and time >= 30:
                    await ReportStatusHelper(). \
                        update_status_report_by_request_id(
                        data.get("request_id"), request, college,
                        action_type=action_type)
                    data = await DatabaseConfiguration().report_collection.find_one(
                        {"request_id": data.get("request_id")}
                    )
                if data.get("status") == "Done":
                    if data.get("format", "").lower() == "excel":
                        data["format"] = "xlsx"
                    try:
                        download_obj = settings.s3_client.get_object(
                            Bucket=settings.s3_reports_bucket_name,
                            Key=f'{settings.report_folder_name}/{settings.teamcity_build_type}/{data.get("request_id")}/data.{data.get("format", "").lower()}')
                        if download_obj.get('ResponseMetadata', {}).get(
                                'HTTPStatusCode') == 200:
                            download_url = await get_download_url(
                                settings.s3_reports_bucket_name,
                                f'{settings.report_folder_name}/{settings.teamcity_build_type}/{data.get("request_id")}/data.{data.get("format", "").lower()}',
                            )
                            report_data.update({"download_url": download_url})
                    except ClientError as ex:
                        if ex.response["Error"]["Code"] == "NoSuchKey":
                            logger.info("No object found - returning empty")
                        error = "Data not found"
                        report_data.update({"error": error})
                report_data.update(
                    {
                        "status": data.get("status"),
                        "request_finished_on": data.get("request_finished_on"),
                    }
                )
                reports.append(report_data)
        if not states:
            collection = await DatabaseConfiguration().state_collection.aggregate([]).to_list(None)
            await store_collection_in_cache(collection, collection_name="states")
        return reports, total_data

    async def current_user_reports(
            self, page_num, page_size, start_date, end_date, user_id,
            college_id, reschedule_report, request, college,
            action_type="system", auto_schedule_reports=False,
            search_pattern=None):
        """
        Get reports of current user based on filter on date range and pagination
        """
        skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                              page_size)
        pipeline = await self. \
            return_pipeline_for_perform_aggregation_on_collection_reports(
            start_date, end_date, college_id, reschedule_report,
            auto_schedule_reports=auto_schedule_reports,
            search_pattern=search_pattern)
        pipeline[0].get("$match").update({"requested_by": ObjectId(user_id)})
        reports, total_data = await self.reports_data(
            pipeline, skip, limit, request, college, action_type=action_type)
        return reports, total_data

    async def get_reports(
            self, page_num, page_size, start_date, end_date, user_type,
            user_id, user_name, report_type, college_id, reschedule_report,
            request, college, auto_schedule_reports=False,
            search_pattern=None
    ):
        """
        Get all reports based on filter on date range and pagination
        """
        skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                              page_size)
        pipeline = await self.return_pipeline_for_perform_aggregation_on_collection_reports(
            start_date, end_date, college_id, reschedule_report,
            auto_schedule_reports=auto_schedule_reports,
            search_pattern=search_pattern
        )
        if user_id not in ["", None]:
            pipeline[0].get("$match").update(
                {"requested_by": ObjectId(user_id)})
        if user_name not in ["", None]:
            pipeline[0].get("$match").update({"user_name": user_name.lower()})
        if user_type:
            pipeline[0]["$match"].update(
                {"user_type": {"$in": [type.lower() for type in user_type]}})
        if report_type not in ["", None]:
            pipeline[0].get("$match").update(
                {"report_type": report_type.capitalize()})
        reports, total_data = await self.reports_data(pipeline, skip, limit,
                                                      request, college)
        return reports, total_data

    async def get_reports_data_by_ids(self, report_ids: list[str]) -> dict:
        """
        Get reports data by ids.

        Params:
            - report_ids (list[str]): A list which contains unique reports ids
                which useful for get reports data.

        Returns:
            - list: A list which contains reports data.

        Raises:
            - ObjectIdInValid: An error occurred when report_id is not valid.
        """
        report_ids = [ObjectId(report_id) for report_id in report_ids
                      if await utility_obj.is_length_valid(
                report_id, "Report id")]
        aggregation_result = await DatabaseConfiguration().report_collection. \
            aggregate([{"$match": {"_id": {"$in": report_ids},
                                   "status": "Done"}}, {
         "$group": {
             "_id": None,
             "request_info":
                 {"$push": {"request_id": "$request_id",
                            "report_format":
                                {
                                    "$cond": {
                                        "if": {"$eq": ["$format", "EXCEL"]},
                                        "then": "xlsx",
                                        "else": "csv"
                                    }
                                }}}
         }
     },
     {"$project":
          {"_id": 0, "request_ids":
              "$request_info.request_id",
           "report_formats": "$request_info.report_format"}}
     ]).to_list(None)
        try:
            aggregation_result = aggregation_result[0]
            request_ids = aggregation_result.get("request_ids", [])
            report_formats = aggregation_result.get("report_formats", [])
        except IndexError:
            request_ids = report_formats = []
        if not request_ids:
            return {}
        season = utility_obj.get_year_based_on_season()
        s3_res = boto3.resource(
            "s3", aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.region_name)
        s3 = settings.s3_client

        path = Path(inspect.getfile(inspect.currentframe())).resolve()
        pth = PurePath(path).parent
        aws_env = settings.aws_env
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        if len(request_ids) == 1:
            key_name = (f'{utility_obj.get_university_name_s3_folder()}/'
                        f'{season}/{settings.s3_reports_bucket_name}/'
                        f'{settings.report_folder_name}/'
                        f'{settings.teamcity_build_type}/{request_ids[0]}/'
                        f'data.{report_formats[0]}')
            try:
                s3.head_object(Bucket=base_bucket, Key=key_name)
            except:
                return
            s3_url = await get_download_url(
                base_bucket, key_name

            )
            return {"file_url": s3_url,
                    "message": "File downloaded successfully.",
                    "data_length": len(request_ids)}
        path_zip = PurePath(pth, Path("sample.zip"))

        with ZipFile(str(path_zip), "w") as zipObj:
            for request_id, report_format in zip(request_ids, report_formats):
                object_key = \
                    f'{utility_obj.get_university_name_s3_folder()}/' \
                    f'{season}/{settings.s3_reports_bucket_name}/' \
                    f'{settings.report_folder_name}/' \
                    f'{settings.teamcity_build_type}/{request_id}/' \
                    f'data.{report_format}'
                object_name = PurePath(object_key).name
                path = PurePath(pth, Path(object_name))
                try:
                    s3_res.Bucket(
                        base_bucket).download_file(
                        object_key, str(path)
                    )
                except Exception as error:
                    logger.error(f"Error downloading file %s: %s",
                                 object_name,
                                 error)
                try:
                    zipObj.write(str(path), arcname=f"{request_id}/{object_name}")
                except FileNotFoundError as error:
                    logger.error(
                        f"Error write the file inn zipObj {error}")
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
            logger.error(e)
            return {'Error': e}
        finally:
            if Path(str(path_zip)).is_file():
                Path(str(path_zip)).unlink()  # unlink (remove) the file
        zip_s3_url = await get_download_url(
            base_bucket, path_to_unique_filename
        )
        return {"file_url": zip_s3_url,
                "message": "File downloaded successfully.",
                "data_length": len(request_ids)}
