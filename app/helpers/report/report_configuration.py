"""
This file contains class and functions which useful for report API routes.
"""
import datetime
from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.database.configuration import DatabaseConfiguration
from bson import ObjectId
from app.core.custom_error import DataNotFoundError, CustomError
from app.models.report_schema import ReportFilter, GenerateReport
from fastapi.encoders import jsonable_encoder
from fastapi import Request, BackgroundTasks
from app.core.teamcity_config import TeamcityConfig
from app.background_task.admin_user import DownloadRequestActivity
import pandas as pd
from app.dependencies.oauth import is_testing_env

logger = get_logger(name=__name__)


class ReportHelper:
    """
    Contains functions related to report API routes.
    """

    async def get_period_in_proper_format(
            self, period: str | dict, requested_on: str | None = None) \
            -> str | None:
        """
        Get the period in a proper format.

        Params:
            - period (str | dict): A period which is either in string or
                dictionary format.
            - requested_on (str | None): Default value: None.
                Report requested datetime.

        Returns:
            str | None: Either None or a string which represents period value.
        """
        if isinstance(period, dict):
            start_date = period.get("start_date")
            end_date = period.get("end_date")
            check_list = ["", None]
            period = ""
            if start_date not in check_list:
                start_date = await utility_obj.date_change_utc(start_date)
                start_date = utility_obj.get_local_time(
                    start_date, season=True, hour_minute=True)
                period += f"Date Range: {start_date}"
            else:
                seasons = settings.seasons
                for season in seasons:
                    if settings.current_season == season.get("season_id"):
                        period += f"{season.get('start_date')}"
            if end_date not in check_list:
                end_date = await utility_obj.date_change_utc(end_date)
                end_date = utility_obj.get_local_time(
                    end_date, season=True, hour_minute=True)
                period += f" to {end_date}"
            else:
                period += f" to {requested_on}"
        return period

    async def report_template_helper(self, item: dict) -> dict:
        """
        Format all the data of report template

        Params:
            item (dict): Single un-formatted data of report template

        Returns:
            dict: Formatted single data for response in list.
        """
        period = item.get("period")
        requested_on = utility_obj.get_local_time(item.get("requested_on"))
        period = await self.get_period_in_proper_format(period, requested_on)
        auto_schedule_info = item.get('generate_and_reschedule', {})
        data = {
            "_id": str(item.get('_id')),
            "report_type": item.get("report_type"),
            "report_name": item.get("report_name"),
            "format": item.get("format"),
            "report_details": item.get("report_details"),
            "payload": item.get("payload"),
            "advance_filter": item.get("advance_filter"),
            "send_mail_recipients_info": item.get("recipient_details"),
            "add_column": item.get("add_column"),
            "generate_and_reschedule": item.get("generate_and_reschedule"),
            "period": period,
            "requested_by": str(item.get("requested_by", "")),
            "requested_by_name": item.get("requested_by_name"),
            "report_send_to": item.get("report_send_to", None),
            "status": item.get("status"),
            "requested_on": utility_obj.get_local_time(
                item.get("requested_on")),
            "request_finished_on": requested_on,
            "schedule_created_on": utility_obj.get_local_time(
                item.get("schedule_created_on")) if item.get(
                "schedule_created_on") else None,
            "sent_mail": item.get("sent_mail", False),
            "is_auto_schedule": item.get("is_auto_schedule", False),
            "interval": auto_schedule_info.get("interval"),
            "trigger_by": auto_schedule_info.get("trigger_by"),
            "date_range": auto_schedule_info.get("date_range")
        }
        return data

    async def get_all_saved_report_templates(self) -> list:
        """
        For filteration of all saved report template from database.

        Returns:
            list: Return list of all saved report template data.
        """
        report_template = DatabaseConfiguration().report_collection.aggregate([
            {
                "$match": {
                    "save_template": True
                }
            }
        ])
        return [
            await self.report_template_helper(item) for item in await
            report_template.to_list(None)
        ]

    async def delete_report_template_by_id(
            self, ids: list[str]
    ) -> dict:
        """
        Delete report template helper which help to delete data from the
        database by the using of there unique id.

        Params:
            ids (list[str]): List of Report template unique id.

        Returns:
            dict: Response msg of the status of deletion.
        """
        report_ids = [ObjectId(id) for id in ids
                      if await utility_obj.is_length_valid(
                id, "Report id") and await DatabaseConfiguration().
            report_collection.find_one({"_id": ObjectId(id)}) is not None]

        if report_ids:
            await DatabaseConfiguration().report_collection.delete_many(
                {"_id": {"$in": report_ids}})

            return {"message": "Reports deleted successfully."}

        return {"detail": "Make sure provided report ids are correct."}

    async def validate_and_format_report_data(
            self, request_data: GenerateReport) -> tuple:
        """
        Validate and format the report data which want to add/update.

        Params:
            - request_data (GenerateReport): Report data which want to
                add/update.

        Returns:
            - tuple: A tuple which contains formatted report data along with
                report_type and report_format.

        Raises:
            - CustomError: An error occurred when report type is invalid.
        """
        request_data = {key: value for key, value in
                        request_data.model_dump().items() if value is not None}
        report_type = request_data.get("report_type")
        if report_type not in ["", None]:
            report_type = report_type.capitalize()
            if report_type not in ["Leads", "Forms", "Applications",
                                   "Payments"]:
                raise CustomError(
                    "Report type should be any of the following: "
                    "'Leads', 'Forms', 'Applications', 'Payments'.")
            request_data["report_type"] = report_type
        report_name = request_data.get("report_name")
        if report_name not in ["", None]:
            report_name = report_name.capitalize()
            request_data["report_name"] = report_name
        report_format = request_data.get("format")
        if report_format not in ["", None]:
            report_format = report_format.upper()
            request_data["format"] = report_format
        return request_data, report_type, report_format

    async def update_report_data(
            self, report_id: str, user: dict, request_data: dict,
            payload: None | ReportFilter) -> dict:
        """
        Update the report data by report id.

        Params:
            - report_id (str): An unique id/identifier of report which useful
                for update report data. e.g., 123456789012345678901234
            - user (dict): A dictionary which contains user data.
            - report_data (dict): A dictionary which contains report data
                which want to update.
            - payload (None | ReportFilter): Either None or filters of
                report.

        Returns:
            - dict: A dictionary which contains information about update
                report data.

        Raises:
            - ObjectIdInValid: An error occurred when report_id not valid.
            - DataNotFoundError: An error occurred when report not found by id.
        """
        await utility_obj.is_length_valid(report_id, "Report id")
        if (report_data := await DatabaseConfiguration().report_collection.
                find_one({"_id": ObjectId(report_id)})) is None:
            raise DataNotFoundError(_id=report_id, message="Report data")
        last_modified_timeline = [{
            "last_modified_at": datetime.datetime.utcnow(),
            "user_id": ObjectId(str(user.get("_id"))),
            "user_name": utility_obj.name_can(user),
        }]
        if payload is None:
            payload = {}
        payload = jsonable_encoder(payload)
        if payload:
            request_data["payload"] = payload
        if report_data.get("last_modified_timeline"):
            report_data.get("last_modified_timeline", []).insert(
                0, last_modified_timeline[0])
            last_modified_timeline = report_data.get("last_modified_timeline")
        request_data["last_modified_timeline"] = last_modified_timeline
        await DatabaseConfiguration().report_collection.update_one(
            {"_id": ObjectId(report_id)}, {"$set": request_data})
        return {"message": "Report data updated successfully."}

    async def get_date_range_based_on_period(self, period: str | dict,
                                             date_range: dict) -> tuple:
        """
        Get date_range (start_date and end_date) based on period.

        Params:
            - period (str | None): Either string or dictionary which contains
                information about report generation period.
            - date_range (dict): Default empty dictionary.

        Returns:
            - tuple: A tuple which contains date_range, start_date and
                end_date.
        """
        if isinstance(period, dict):
            start_date = await utility_obj.date_change_utc(
                period.get("start_date"))
            end_date = period.get("end_date")
            if end_date not in ["", None]:
                end_date = await utility_obj.date_change_utc(end_date)
                date_range = {"start_date":
                                  start_date.strftime("%Y-%m-%d %H:%M"),
                              "end_date": end_date.strftime("%Y-%m-%d %H:%M")}
            else:
                date_range = {"start_date":
                                  start_date.strftime("%Y-%m-%d %H:%M"),
                              "end_date": None}
        else:
            if period == "Today":
                current_datetime = datetime.datetime.utcnow()
                current_date = current_datetime.strftime("%Y-%m-%d")
                date_range = {"start_date": current_date,
                              "end_date": current_date}
            elif period == "Yesterday":
                date_range = await utility_obj.yesterday()
            elif period == "This Month":
                date_range = await utility_obj.get_current_month_date_range()
            elif period == "Last Month":
                end_date = datetime.datetime.utcnow()
                start_date = end_date - pd.offsets.DateOffset(months=1)
                date_range = {
                    "start_date": start_date.to_pydatetime().strftime(
                        "%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")}
            elif period == "This Year":
                date_range = await utility_obj.get_current_year_date_range()
            elif period in ["This Week", "Last 7 Days"]:
                date_range = await utility_obj.week()
            elif period == "Last 30 Days":
                date_range = await utility_obj.last_30_days()
            start_date = date_range.get("start_date")
            end_date = date_range.get("end_date")
        return date_range, start_date, end_date

    async def generate_or_save_report(
            self, payload: None | ReportFilter, request: Request,
            request_data: dict, report_type: str | None,
            report_format: str | None, current_datetime: datetime.datetime,
            user: dict, college_id: str, background_tasks: BackgroundTasks) \
            -> dict:
        """
        Generate or save report.

        Params:
            - payload (None | ReportFilter): Either None or filters of report.
            - request (Request): An object of class `Request` which useful for
                get user info.
            - request_data (dict): A dictionary which contains report data.
            - report_type (str | None): Either None or type of report.
            - report_format (str | None): Either None or format of a report.
            - current_datetime (datetime): Datetime of perform request of
                generate/save report.
            - user (dict): A dictionary which contains user data.
            - college_id (str): An unique id/identifier of a college.
                e.g., 123456789012345678901234
            - background_tasks (BackgroundTasks): An object of
                `BackgroundTasks` which useful for perform background task.

        Returns:
            - dict: A dictionary which contains information about
                generate/save report.
        """
        if payload is None:
            payload = {}
        payload = jsonable_encoder(payload)
        ip_address = utility_obj.get_ip_address(request)
        data, start_date, end_date, date_range = {}, None, None, {}
        reschedule_report = request_data.get("reschedule_report")
        period = request_data.get("period")
        if period:
            date_range, start_date, end_date = await self. \
                get_date_range_based_on_period(period, date_range)
        if start_date:
            start_date = date_range.get("start_date")
            end_date = date_range.get("end_date")
            if end_date in ["", None]:
                end_date = utility_obj.get_local_time(current_datetime)
            request_data.update(
                {"statement": f"{start_date} to {end_date}",
                 "date_range": {"start_date": start_date,
                                "end_date": end_date}})
            end_date = date_range.get("end_date")
        save_template = request_data.get("save_template")
        if not reschedule_report and not save_template:
            payload.update({"advance_filters": request_data.get(
                "advance_filter"), "add_column": request_data.get("add_column")})
            response = None
            if not is_testing_env():
                response = await TeamcityConfig().generate_report_using_teamcity(
                    report_type, report_format, start_date, end_date, payload)
            payload.pop("advance_filters")
            payload.pop("add_column")
            if response is not None:
                data = response.json()
        if not reschedule_report and not save_template:
            status = "In progress"
        else:
            status = None
        request_id = data.get("id")
        schedule_type = request_data.get("schedule_type")
        request_data.update({
            "request_id": request_id, "status": status,
            "report_send_to": request_data.get("report_send_to"),
            "payload": payload, "requested_on": current_datetime,
            "schedule_created_on": current_datetime,
            "requested_by": ObjectId(str(user.get("_id"))),
            "requested_by_name": utility_obj.name_can(user),
            "college_id": ObjectId(college_id), "ip_address": ip_address,
            "user_type": user.get("role", {}).get("role_name"),
            "user_name": user.get("user_name"),
            "reschedule_report": reschedule_report,
            "schedule_type": str(schedule_type).title() if schedule_type
            else None,
            "schedule_value": request_data.get("schedule_value")
        })
        insert_report_data = await DatabaseConfiguration().report_collection. \
            insert_one(request_data)
        if request_data.get("_id"):
            request_data.pop("_id")
        request_data.update({"report_id": str(insert_report_data.inserted_id),
                             "requested_by": str(request_data.get(
                                 "requested_by")),
                             "college_id": str(college_id)})
        background_tasks.add_task(
            DownloadRequestActivity().store_download_request_activity,
            request_type=f"Generate report with request id {request_id}",
            requested_at=current_datetime, ip_address=ip_address,
            user=user, total_request_data=1, is_status_completed=False)
        return {
            "request_data": request_data,
            "message": f"Request received for `{report_type}`on "
                       f"{utility_obj.get_local_time(current_datetime)} "
                       f"with request id {request_id}"
        }

    async def get_headers_info(
            self, college_id: str, search_pattern: str | None,
            report_type: str) -> tuple:
        """
        Get the report header information based on report type.

        Params:
            - college_id (str): An unique id/identifier of a college.
            - search_pattern (str | None): Either None or string which useful
                for get report header information based on search_pattern.
            - report_type (str): Type of report. Possible values are: Leads, Applications and Forms.

        Returns:
            tuple: A tuple which contains report header information
                along with total count.
        """
        field_filter = '$$field.v.field_name'
        if search_pattern not in ["", None]:
            field_filter = {
                '$filter': {
                    'input': '$$field.v.field_name',
                    'as': 'field_name',
                    'cond': {
                        '$regexMatch': {
                            'input': '$$field_name',
                            'regex': f".*{search_pattern}.*",
                            'options': "i"
                        }
                    }
                }
            }
        aggregation_pipeline = [
            {"$match": {"college_id": ObjectId(college_id)}},
            {
                '$project': {
                    "_id": 0,
                    'categories_info': {
                        '$filter': {
                            'input': {
                                '$map': {
                                    'input': {
                                        '$objectToArray': '$$ROOT'
                                    },
                                    'as': 'field',
                                    'in': {
                                        'fields': field_filter,
                                        'category_name': {
                                            '$cond': {
                                                'if': {'$in': ['$$field.k', ['Student Default Fields'
                                                                             if report_type.lower() == "leads" else
                                                                             "Application Default Fields"]]},
                                                'then': "Default",
                                                'else': '$$field.k'
                                            }
                                        }
                                    }
                                }
                            },
                            'as': 'field',
                            'cond': {
                                '$not': {
                                    '$in': ["$$field.category_name",
                                            ['_id', 'college_id',
                                             "Application Default Fields"] if report_type.lower() == "leads"
                                            else ['_id', 'college_id', "Student Default Fields"]]
                                }
                            }
                        }
                    }
                }
            },
            {
                "$unwind": "$categories_info"
            },
            {
                "$group": {
                    "_id": "$categories_info.category_name",
                    "fields": {"$push": "$categories_info.fields"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "category_name": "$_id",
                    "fields": {"$arrayElemAt": ["$fields", 0]}
                }
            },
            {
                "$facet": {
                    "paginated_results": [],
                    "totalCount": [{"$count": "count"}],
                }
            }
        ]

        aggregation_result = DatabaseConfiguration(). \
            report_field_collection.aggregate(aggregation_pipeline)
        data, total_data = {}, 0
        async for document in aggregation_result:
            try:
                total_data = document.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
            data = {item.get("category_name"): item.get("fields", []) for item in document.get("paginated_results", [{}])}
        return data, total_data
