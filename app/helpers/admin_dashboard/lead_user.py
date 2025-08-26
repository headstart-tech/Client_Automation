"""
This file contain class and functions related to lead user
"""
import datetime
from pathlib import PurePath
from bson.objectid import ObjectId
from fastapi.exceptions import HTTPException
from app.core.utils import utility_obj, settings
from app.database.aggregation.call_log import CallLog
from app.database.configuration import DatabaseConfiguration
from app.s3_events.s3_events_configuration import get_download_url
from app.database.aggregation.student import Student


class LeadUser:
    """
    Contain helper functions related to lead user
    """

    async def student_application_data(self, application_id, season=None):
        """
        Get the Application and Primary details of student
        """
        if (
                application := await DatabaseConfiguration(
                    season=season).studentApplicationForms.find_one(
                    {"_id": ObjectId(application_id)}
                )
        ) is None:
            raise HTTPException(status_code=404,
                                detail="Application not found")
        if (
                student := await DatabaseConfiguration(
                    season=season).studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(str(application.get("student_id")))}
                )
        ) is None:
            raise HTTPException(status_code=404, detail="student not found")
        return student, application

    async def user_header(self, application_id: str,
                          season: str | None = None) -> dict:
        """
        Get the user profile header data.

        Params:
            application_id (str): A unique id/identifier of application.
                e.g., 123456789012345678901234
            season (ste | None): Useful for get season based data.
                e.g., season 1

        Returns:
            dict:
        """
        season_year = utility_obj.get_year_based_on_season(season)
        student, application = await self.student_application_data(
            application_id, season=season)
        upcoming_lead = "NA"
        secondary_details = await DatabaseConfiguration(season=season). \
            studentSecondaryDetails.find_one(
            {"student_id": ObjectId(str(student.get("_id")))})
        recent_photo = "NA"
        if secondary_details:
            object_name = secondary_details.get("attachments", {}).get(
                "recent_photo", {}).get("file_s3_url")
            aws_env = settings.aws_env
            base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
            if object_name not in [None, ""]:
                name = str(PurePath(object_name).name)
                object_key = \
                    (f"{utility_obj.get_university_name_s3_folder()}/"
                     f"{season_year}/"
                     f"{settings.s3_student_documents_bucket_name}/"
                     f"{student.get('_id')}/recent_photo/"
                     f"{name}")
                url = await get_download_url(base_bucket, object_key)
                recent_photo = url
        if (
                lead := await DatabaseConfiguration(
                    season=season).leadsFollowUp.find_one(
                    {
                        "application_id": ObjectId(application_id),
                        "student_id": ObjectId(str(student.get("_id"))),
                    }
                )
        ) is None:
            lead = {}
        if lead.get("followup") is not None:
            today_date = datetime.datetime.utcnow()
            upcoming_lead = [
                i
                for i in lead.get("followup")
                if i.get("followup_date").strftime(
                    "%Y-%m-%d %H:%M:%S") > today_date.strftime(
                    "%Y-%m-%d %H:%M:%S")]
            if len(upcoming_lead) > 0:
                upcoming_lead = sorted(
                    upcoming_lead,
                    key=lambda x: x.get("followup_date").strftime(
                        "%Y-%m-%d %H:%M:%S"),
                )
                upcoming_lead = [
                    utility_obj.get_local_time(i.get("followup_date")) for i in
                    upcoming_lead[:3]
                ]
            else:
                upcoming_lead = "NA"
        (lead_source, lead_source_extra, utm_campaign_name, utm_medium,
         utm_campaign_name_extra, utm_medium_extra) = "Organic", [
            "NA", "NA"], "NA", "NA", ["NA", "NA"], ["NA", "NA"]
        if (
                lead_sources := await DatabaseConfiguration(
                    season=season).studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(str(student.get("_id")))}
                )
        ) is not None:
            lead_source = lead_sources.get("source", {}).get("primary_source",
                                                             {}).get(
                "utm_source", "Organic"
            )
            utm_campaign_name = lead_sources.get("source", {}).get(
                "primary_source", {}).get(
                "utm_campaign", "NA"
            )
            utm_medium = lead_sources.get("source", {}).get(
                "primary_source", {}).get(
                "utm_medium", "NA"
            )
            lead_source_extra = [
                lead_sources.get("source", {}).get(
                    "secondary_source", {}).get("utm_source",
                                                "NA"),
                lead_sources.get("source", {}).get(
                    "tertiary_source", {}).get("utm_source",
                                               "NA")]
            utm_campaign_name_extra = [
                lead_sources.get("source", {}).get(
                    "secondary_source", {}).get("utm_campaign",
                                                "NA"),
                lead_sources.get("source", {}).get(
                    "tertiary_source", {}).get("utm_campaign",
                                               "NA")]
            utm_medium_extra = [
                lead_sources.get("source", {}).get(
                    "secondary_source", {}).get("utm_medium",
                                                "NA"),
                lead_sources.get("source", {}).get(
                    "tertiary_source", {}).get("utm_medium",
                                               "NA")]
        if (
                communication_status := await DatabaseConfiguration(
                    season=season).communication_log_collection.find_one(
                    {"student_id": ObjectId(str(student.get("_id")))}
                )
        ) is None:
            communication_status = {}
        course = await DatabaseConfiguration(season=season). \
            course_collection.find_one({"_id": application.get("course_id")})
        if course is None:
            course = {}
        basic_details = student.get("basic_details", {})
        mobile_number = basic_details.get("mobile_number", "NA")
        created_at = student.get("created_at")
        inbound_duration, outbound_duration = await (
            CallLog().get_call_duration(mobile_number))
        lead_age = datetime.datetime.now() - created_at
        lead_age = lead_age.days
        lead_age_date = " ".join(utility_obj.get_local_time(
            created_at).split(" ")[:3])
        lead_stage = lead.get("lead_stage")
        lead_stage_label = lead.get("lead_stage_label")
        payment_status_value = application.get("payment_info", {}).get("status")
        return {
            "basic_info": {
                "name": utility_obj.name_can(basic_details),
                "application_stage": (
                    "Completed" if application.get(
                        "declaration") is True else "Incomplete"
                ),
                "application_id": str(application.get("_id")),
                "custom_application_id": application.get(
                    "custom_application_id"),
                "lead_merged": "NA",
                "course_id": str(application.get("course_id", "NA")),
                "course_name": course.get("course_name"),
                "amount": course.get("fees"),
                "payment_status": (
                        await Student().get_payment_status(
                            application.get("payment_initiated", False)
                        )
                        if payment_status_value in ["", None]
                        else str(payment_status_value).title()
                    ),
                "spec_name": application.get("spec_name1"),
                "lead_stage": lead_stage if lead_stage is not None
                else "Fresh Lead",
                "lead_sub_stage": lead_stage_label
                if lead_stage_label not in [None, ""] else "NA",
                "email": basic_details.get("email"),
                "verify_email": student.get("is_email_verify"),
                "verify_mobile": student.get("is_mobile_verify"),
                "verify_lead": student.get("is_verify"),
                "mobile": mobile_number,
                "added_on": utility_obj.get_local_time(
                    application.get("enquiry_date")),
                "last_active": utility_obj.get_local_time(
                    application.get("last_updated_time")),
                "recent_photo": recent_photo,
            },
            "communication_status": {
                "email_sent": communication_status.get('email_summary',
                                                       {}).get("email_sent",
                                                               0),
                "sms_sent": communication_status.get('sms_summary', {}).get(
                    "sms_sent", 0),
                "whatsapp_sent": communication_status.get('whatsapp_summary',
                                                          {}).get(
                    "whatsapp_sent", 0)},
            "telephony_status": {
                "inbound_call": await DatabaseConfiguration(
                    season=season).call_activity_collection.count_documents(
                    {
                        "$and": [
                            {
                                "$or": [
                                    {"call_from": str(mobile_number)},
                                    {"call_from_number": int(mobile_number)},
                                    {"call_to": str(mobile_number)},
                                    {"call_to_number": int(mobile_number)}
                                ]
                            },
                            {"type": "Inbound"}
                        ]
                    }

                ),
                "inbound_call_duration": f"0.{inbound_duration}",
                "outbound_call_duration": f"0.{outbound_duration}",
                "outbound_call": await DatabaseConfiguration(
                    season=season).call_activity_collection.count_documents(
                    {
                        "$and": [
                            {
                                "$or": [
                                    {"call_from": str(mobile_number)},
                                    {"call_from_number": int(mobile_number)},
                                    {"call_to": str(mobile_number)},
                                    {"call_to_number": int(mobile_number)},
                                ]
                            },
                            {"type": "Outbound"}
                        ]
                    }
                ),
                "missed_call": await DatabaseConfiguration(season=season).
                call_activity_collection.count_documents({
                    "$or": [
                        {
                            "call_from": str(mobile_number),
                            "call_duration": 0
                        },
                        {
                            "call_from_number": int(mobile_number),
                            "status": {
                                "$in": ['NOANSWER', 'BUSY', 'CANCEL', "Missed"]
                            }
                        }
                    ]
                }),
            },
            "assigned_counselor": application.get("allocate_to_counselor",
                                                  {}).get(
                "counselor_name"
            )
            if application.get("allocate_to_counselor") is not None
            else "NA",
            "upcoming_followup": upcoming_lead
            if lead.get("followup") is not None
            else "NA",
            "lead_source": lead_source,
            "sec_ter_source": lead_source_extra,
            "utm_campaign_name": utm_campaign_name,
            "utm_campaign_name_extra": utm_campaign_name_extra,
            "utm_medium": utm_medium,
            "utm_medium_extra": utm_medium_extra,
            "lead_age": lead_age,
            "lead_age_date": lead_age_date,
            "tags": student.get("tags", [])
        }

    async def lead_details_additional(self, application_id):
        """
        Get the lead_details, Application details and download url of
        application details
        """
        student, application = await self.student_application_data(
            application_id)
        if await DatabaseConfiguration().college_collection.find_one(
                {"_id": ObjectId(str(student["college_id"]))}
        ) is None:
            raise HTTPException(status_code=404, detail="college not found")
        course_id = str(application.get("course_id"))
        if (courses := await DatabaseConfiguration().course_collection.
                find_one(
            {"_id": ObjectId(course_id)}
        )
        ) is None:
            raise HTTPException(status_code=404, detail="course not found")
        course_name = courses.get('course_name')
        spec_name = application.get('spec_name1')
        program_list = [{
            "course_name": course_name,
            "course_id": course_id,
            "course_specialization": spec_name
        }]
        course_name = (
            f"{course_name} in {spec_name}" if spec_name else course_name)
        course_type = "Post Graduate" if courses.get(
            "is_pg") is True else "Under Graduate"
        application_stage = (
            "Completed" if application.get(
                "declaration") is True else "Incompleted"
        )
        communication_address = student.get("address_details", {}).get(
            "communication_address", {})
        if (secondary := await DatabaseConfiguration().
                studentSecondaryDetails.find_one(
            {"student_id": ObjectId(str(student.get("_id")))}
        )
        ) is None:
            secondary = {}
        upcoming_followup = None
        upcoming_followup_status = None
        upcoming_followup_index = None
        if (lead_followup := await DatabaseConfiguration().leadsFollowUp.
                find_one(
            {"application_id": ObjectId(application_id),
             "student_id": student.get("_id")}
        )
        ) is not None:
            if lead_followup.get("followup") is not None:
                today_date = datetime.datetime.utcnow()
                for i in lead_followup.get("followup"):
                    if (i.get("followup_date").strftime("%Y-%m-%d %H:%M:%S")
                            > today_date.strftime("%Y-%m-%d %H:%M:%S")):
                        upcoming_followup = utility_obj.get_local_time(
                            i.get("followup_date"))
                        upcoming_followup_status = i.get("status")
                        upcoming_followup_index = lead_followup.get(
                            "followup").index(i)
                        break
        education_details = secondary.get("education_details", {})
        inter_details = education_details.get("inter_school_details", {})
        graduation_details = education_details.get("graduation_details", {})
        basic_details = student.get("basic_details", {})
        course_details = student.get("course_details", {})
        second_course, second_spec = "NA", None
        if len(course_details) > 1:
            for _id, value in enumerate(course_details):
                if courses.get('course_name') != course_details.get(
                        value, {}).get("course_name"):
                    second_course = value
                    try:
                        second_spec = course_details.get(
                            value, {}).get("specs", [{}])[0].get("spec_name")
                        program_list.append({
                            "course_name": second_course,
                            "course_id": str(course_details.get(value, {}).get(
                                "course_id")),
                            "course_specialization": second_spec
                        })
                    except IndexError:
                        pass
                    break
        return {
            "lead_details": {
                "course_name": course_name,
                "application_id": str(application.get("_id")),
                "custom_application_id":
                    application.get("custom_application_id"),
                "email": student.get("user_name"),
                "mobile": student.get("basic_details").get("mobile_number"),
                "alternative_mobile": student.get("basic_details").get(
                    "alternate_number", "NA"
                ),
                "name": utility_obj.name_can(basic_details),
                "state": communication_address.get("state", {}).get(
                    "state_name"),
                "city": communication_address.get("city", {}).get("city_name"),
                "programing_level": course_type,
                "scholarship": "NA",
                "application_stage": application_stage,
                "note": "no answer",
                "gender": basic_details.get("gender"),
                "last_active": f"{utility_obj.get_local_time(student.get('last_accessed'))}",
                "lead_added": f"{utility_obj.get_local_time(student.get('created_at'))}",
                "entitled_scholarship": 0,
                "automation_count": "N/A",
                "upcoming_followup": upcoming_followup,
                "upcoming_followup_status": upcoming_followup_status,
                "upcoming_followup_index": upcoming_followup_index,
                "secondary_mobile": basic_details.get(
                    "alternate_mobile_number", ""),
                "secondary_email": basic_details.get("alternate_email", ""),
                "tertiary_mobile": basic_details.get("tertiary_mobile_number",
                                                     ""),
                "tertiary_email": basic_details.get("tertiary_email", ""),
                "secondary_email_set_as_default": basic_details.get(
                    "secondary_email_set_as_default", None),
                "tertiary_email_set_as_default": basic_details.get(
                    "tertiary_email_set_as_default", None),
                "secondary_number_set_as_default": basic_details.get(
                    "secondary_number_set_as_default", None),
                "tertiary_number_set_as_default": basic_details.get(
                    "tertiary_number_set_as_default", None),
                "lead_score": student.get("lead_score", "NA"),
                "second_program": f"{second_course} in {second_spec}"
                if second_spec not in [None, ""] else second_course,
                "second_course": second_course,
                "second_spec": second_spec,
                "program_list": program_list,
                "preference_info": application.get("preference_info")
            },
            "additioan_details": {
                "alternative_mobile": student.get("basic_details", {}).get(
                    "alternate_number", "NA"
                ),
                "alternative_email": student.get("basic_details", {}).get(
                    "alternate_email", "NA"
                ),
                "12th_school_name": inter_details.get("school_name", "NA"),
                "12th_percentage": inter_details.get("obtained_cgpa", "NA"),
                "12th_subject": inter_details.get("stream", "NA"),
                "12th_pass_year": inter_details.get("year_of_passing", "NA"),
                "graduation_subject": graduation_details.get(
                    "ug_course_name", "NA"),
                "graduation_year": graduation_details.get(
                    "year_of_passing", "NA"),
                "college_name": graduation_details.get(
                    "name_of_institute", "NA"),
                "allocated_course": "NA",
                "exam_taken": "NA",
                "mat": "NA",
                "callback_request": "NA",
            },
            "application_download_url": application.get(
                'application_download_url')
        }
    
    
    async def offline_data_list(self, raw_data_ids: list[str]) -> list:
        """Helper function of getting list of particular offline data by passing list of unique ids.

        Params:
            raw_data_ids (list[str]): List of offline data unique id

        Returns:
            list: List of data and no. of datas
        """
        raw_data_ids = [ObjectId(data_id) for data_id in raw_data_ids]

        data_list, total =  await self.offline_display(
            payload={},
            start_date=None,
            end_date=None,
            skip=0,
            limit=len(raw_data_ids),
            raw_data_ids=raw_data_ids
        )

        return data_list, total

    async def converted_count(self, offline_id: str, is_application: bool, start_date, end_date, skip: int, limit: int) -> tuple:
        """Converted lead and application of raw data helper to find list of students

        Params:
            offline_id (str): offline_data unique id
            is_application (bool): Need data with application list or not. Default it is false.
            start_date (_type_): start_date
            end_date (_type_): end_date
            skip (int): No. of page which have to skip.
            limit (int): Data limit no.

        Returns:
            tuple: List of student details and application details
        """

        final_project = {
            'raw_data_mandatory_field': '$mandatory_field', 
            'raw_data_other_field': '$other_field', 
            'imported_by': '$offline_data.imported_by', 
            'imported_time': {
                '$toDate': '$offline_data.uploaded_on'
            }, 
            'student_basic_details': '$matched_students.basic_details'
        }

        pipeline = [
            {
                '$match': {
                    'offline_data_id': ObjectId(offline_id),
                    'created_at': {
                        '$gte': start_date, 
                        '$lte': end_date
                    }
                }
            }, {
                '$lookup': {
                    'from': 'offline_data', 
                    'localField': 'offline_data_id', 
                    'foreignField': '_id', 
                    'as': 'offline_data'
                }
            }, {
                '$unwind': '$offline_data'
            }, {
                '$lookup': {
                    'from': 'studentsPrimaryDetails', 
                    'let': {
                        'email': '$mandatory_field.email', 
                        'mobile': '$mandatory_field.mobile_number', 
                        'uploaded_on': '$offline_data.uploaded_on'
                    }, 
                    'pipeline': [
                        {
                            '$match': {
                                '$expr': {
                                    '$and': [
                                        {
                                            '$gte': [
                                                '$created_at', '$$uploaded_on'
                                            ]
                                        }, {
                                            '$or': [
                                                {
                                                    '$eq': [
                                                        '$basic_details.email', '$$email'
                                                    ]
                                                }, {
                                                    '$eq': [
                                                        '$basic_details.mobile_number', {
                                                            '$toString': '$$mobile'
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    ], 
                    'as': 'matched_students'
                }
            }, {
                '$match': {
                    'matched_students.0': {
                        '$exists': True
                    }
                }
            }, {
                '$unwind': '$matched_students'
            }, {
                '$project': final_project
            }, {
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            }
        ]

        if is_application:
            final_project.update({
                "application": {
                    'course_id': '$applications.course_id', 
                    'specialization': '$applications.spec_name1'
                }
            })

            pipeline.insert(6, {
                '$lookup': {
                    'from': 'studentApplicationForms', 
                    'localField': 'matched_students._id', 
                    'foreignField': 'student_id', 
                    'as': 'applications'
                }
            })
            pipeline.insert(7, {
                '$unwind': '$applications'
            })

        raw_data = await (DatabaseConfiguration().raw_data.aggregate(pipeline)).to_list(None)

        raw_data = raw_data[0] if raw_data else {}
        raw_data_list = raw_data.get("paginated_results", [])
        raw_data_count = raw_data.get("totalCount")[0].get("count", 0) if raw_data.get("totalCount") else 0
        
        for data in raw_data_list:
            data.update({
                "_id": str(data.pop("_id")),
                "imported_time": utility_obj.get_local_time(data.pop("imported_time")) if data.get("imported_time") else None,
                "imported_by": utility_obj.name_can(await DatabaseConfiguration().user_collection.find_one({"_id": data.get("imported_by")})),
                "lead_full_name": utility_obj.name_can(data.pop("student_basic_details")),
            })

            if is_application:
                application = data['application']
                application.update({
                    "course_id": str(application.get("course_id")),
                    "course_name": (await DatabaseConfiguration().course_collection.find_one({"_id": application.get("course_id")})).get("course_name"),
                    "specialization": application.get("specialization")
                })

        return raw_data_list, raw_data_count
           

    async def offline_display(self, payload, start_date, end_date, skip, limit,
                              lead_upload=None, raw_data_ids=None):
        """
        Get offline data with date_range and payload
        """
        pipeline = [
            {
                "$sort": {
                    "uploaded_on": -1
                }
            },
            {"$facet": {"totalCount": [{"$count": "value"}],
                        "pipelineResults": [{"$skip": skip}, {"$limit": limit}]
                        }},
            {"$unwind": "$pipelineResults"},
            {"$unwind": "$totalCount"},
            {
                "$replaceRoot": {
                    "newRoot": {
                        "$mergeObjects": [
                            "$pipelineResults",
                            {"totalCount": "$totalCount.value"},
                        ]
                    }
                }
            },
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "imported_by": {"$toString": "$imported_by"},
                    "uploaded_by": 1,
                    "uploaded_on": {
                        "$dateToString": {
                            "date": "$uploaded_on",
                            "format": "%d-%b-%Y %H:%M:%S",
                            "timezone": "Asia/Kolkata",
                            "onNull": None
                        }},
                    "failed_lead": 1,
                    "data_name": 1,
                    "duplicate_leads": 1,
                    "lead_processed": 1,
                    "import_status": 1,
                    "duplicate_lead_data": [],
                    "failed_lead_data": [],
                    "totalCount": 1,
                    "successfully_lead": {"$ifNull": [
                        "$successful_lead_count", {"$literal": 0}]}
                }
            }
        ]
        if start_date not in [None, ""] and end_date not in [None, ""]:
            pipeline.insert(0, {"$match": {"uploaded_on": {"$gte": start_date,
                                                           "$lte": end_date}}})
        if payload.get("imported_by"):
            if pipeline[0].get("$match"):
                pipeline[0].get("$match").update(
                    {"imported_by": {"$in": [ObjectId(_id) for _id in
                                             payload.get("imported_by")]}}
                )
            else:
                pipeline.insert(0, {"$match": {
                    "imported_by": {"$in": [ObjectId(_id) for _id in
                                            payload.get("imported_by")]}}})
        if payload.get("import_status") != "" and payload.get(
                "import_status") is not None:
            if pipeline[0].get("$match"):
                pipeline[0].get("$match").update(
                    {"import_status": payload.get("import_status")}
                )
            else:
                pipeline.insert(0, {"$match": {
                    "import_status": payload.get("import_status")}})
        if lead_upload is not None:
            result = await DatabaseConfiguration().lead_upload_history.aggregate(
                pipeline).to_list(None)
        else:
            result = await DatabaseConfiguration().offline_data.aggregate(
                pipeline).to_list(None)
        try:
            total = result[0].get("totalCount", 0)
        except IndexError:
            total = 0
        except Exception:
            total = 0
        return result, total

    async def current_date_lead_data(
            self, counselor_ids, season: str | None) \
            -> dict:
        """
        Get the lead stage data on current date

        Params:
            - counselor_ids (list): list of counselor ids
            - season (str | None): Either None or unique identifier of season
                which useful for get season-wise data.

        Returns:
            dict: A dictionary which contains lead stage count data.
        """
        today_date = datetime.date.today()
        start_date, end_date = await utility_obj.date_change_format(
            str(today_date), str(today_date))
        primary_pipeline = [
            {
                "$group": {
                    "_id": None,
                    "students": {"$addToSet": "$_id"}
                }
            }
        ]
        if counselor_ids:
            primary_pipeline.insert(0, {
                "$match": {
                    "allocate_to_counselor.counselor_id":
                        {"$in": counselor_ids}
                }
            })
        result = await (DatabaseConfiguration(
            season=season).studentsPrimaryDetails.aggregate(
            primary_pipeline)).to_list(None)
        result = result[0] if result else {}
        students = result.get("students", [])
        followup_pipeline = [
            {
                "$match": {
                    "student_id": {"$in": students}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "lead_stage": {
                        "$ifNull": ['$lead_stage',
                                    "Fresh Lead"]
                    }
                }
            },
            {
                "$group": {
                    "_id": "",
                    "fresh_lead": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$lead_stage",
                                        "Fresh Lead"]},
                                1, 0]}
                    },
                    "follow_up": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$lead_stage",
                                        "Follow-up"]},
                                1, 0]}
                    },
                    "interested": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$lead_stage",
                                        "Interested"]},
                                1, 0]}
                    },
                    "admission_confirm": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$lead_stage",
                                        "Admission confirmed"]},
                                1, 0]}
                    },
                    "today_assigned": {
                        "$sum": {
                            "$cond": [
                                {"$and": [
                                    {"$gte": [
                                        "$allocate_to_counselor.last_update",
                                        start_date]}, {"$lte": [
                                        "$allocate_to_counselor.last_update",
                                        end_date]}]},
                                1, 0]}
                    }
                }
            }
        ]
        result = await (
            DatabaseConfiguration(season=season).leadsFollowUp.aggregate(
                followup_pipeline)).to_list(None)
        result = result[0] if result else {}
        return result

    async def get_duplicate_or_failed_data(
            self,
            offline_id: str,
            data_type: str,
            page_num: int,
            page_size: int,
            lead_upload: bool
    ):
        """
        Get the duplicate of failed data from the offline database

        params:
            offline_id (str): Get the offline ObjectId
            data_type (str): Get the data type identify the data

        return:
            A dictionary containing the offline duplicate and failed
             with pagination
        """
        skip, limit = await utility_obj.return_skip_and_limit(
            page_num=page_num, page_size=page_size)
        field_type = "duplicate_lead_data"
        if data_type == "failed":
            field_type = "failed_lead_data"
        pipeline = [
            {
                "$match": {
                    "_id": ObjectId(offline_id)
                }
            },
            {
                "$project": {
                    "_id": 0,
                    f"{field_type}": {"$ifNull": [f"${field_type}", []]}
                }
            },
            {
                "$unwind": f"${field_type}"
            },
            {"$facet": {"totalCount": [{"$count": "value"}],
                        "pipelineResults": [{"$skip": skip}, {"$limit": limit}]
                        }},
            {"$unwind": "$pipelineResults"},
            {"$unwind": "$totalCount"},
            {
                "$replaceRoot": {
                    "newRoot": {
                        "$mergeObjects": [
                            "$pipelineResults",
                            {"totalCount": "$totalCount.value"},
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": {"_id": None, "totalCount": "$totalCount"},
                    f"{field_type}": {"$push": f"${field_type}"}
                }
            }
        ]
        if lead_upload is True:
            result = await DatabaseConfiguration().lead_upload_history.aggregate(
                pipeline).to_list(None)
        else:
            result = await DatabaseConfiguration().offline_data.aggregate(
                pipeline).to_list(None)
        try:
            total = result[0].get("_id", {}).get("totalCount", 0)
            data = result[0].get(f"{field_type}", [])
        except IndexError:
            total = 0
            data = []
        except Exception:
            total = 0
            data = []
        response = await utility_obj.pagination_in_aggregation(
            page_num, page_size, total,
            route_name="/manage/duplicate_failed_data/"
        )
        return {
            "data": data,
            "total": total,
            "count": len(data),
            "pagination": response["pagination"],
            "message": "data fetched successfully",
        }
