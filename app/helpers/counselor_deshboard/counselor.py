"""
This file contain class and functions related to counselor
"""

import calendar
from datetime import date, datetime, timezone
from bson.objectid import ObjectId
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from kombu.exceptions import KombuError

from app.celery_tasks.celery_student_timeline import StudentActivity
from app.core.utils import utility_obj, logger, settings
from app.database.aggregation.call_log import CallLog
from app.database.aggregation.get_all_applications import Application
from app.database.aggregation.student import Student
from app.database.configuration import DatabaseConfiguration
from app.models.student_user_schema import ChangeIndicator


class CounselorDashboardHelper:
    """
    Contain functions related counselor dashboard
    """

    def lead_counselor_of_student(self, item):
        """
        Get the primary details of student along with counselor details
        """
        return {"id": str(item.get("_id")),
                "name": utility_obj.name_can(item.get("basic_details")),
                "allocate_to_counselor": (self.counselor_helper(
                    item.get("allocate_to_counselor")) if item.get(
                    "allocate_to_counselor") is not None else item.get(
                    "allocate_to_counselor")), }

    def counselor_helper(self, item):
        """
        Get counselor details
        """
        return {"counselor_id": str(item.get("counselor_id")),
                "counselor_name": item.get("counselor_name"),
                "last_update": utility_obj.get_local_time(
                    item.get("last_update")), }

    def associated(self, item):
        """
        Get the list of data
        """
        return [str(i) for i in item]

    def college_counselor_serialize(self, item):
        """
        Get the details of college counselor
        """
        return {"id": str(item.get("_id")), "name": utility_obj.name_can(item),
                "last_activity": item.get("last_activity",
                                          datetime.strptime(
                                              "2022-08-15 01:55:19",
                                              "%Y-%m-%d %H:%M:%S"), ),
                "associated_colleges": self.associated(
                    item.get("associated_colleges")), }

    async def filter_counselor(self, item):
        """
        Filter all activated college counselor
        """
        today = str(utility_obj.local_time_for_compare(
            datetime.now(timezone.utc).strftime("%d-%m-%Y %H:%M:%S")).date())
        count = 0
        for index in range(len(item)):
            if (
                    counselor_man := await DatabaseConfiguration().counselor_management.find_one(
                        {"counselor_id": ObjectId(
                            item[count].get("id"))})) is not None:
                if today in counselor_man.get("no_allocation_date", []):
                    item.pop(count)
                else:
                    count += 1
            else:
                count += 1
        return item

    async def list_counselor(self, current_user: str, college_id,
                             holiday=False, season=None):
        """
        Get the list of counselor
        """
        if (user := await DatabaseConfiguration().user_collection.find_one(
                {"user_name": current_user})) is None:
            user = {}
        user_length = await DatabaseConfiguration().user_collection.count_documents(
            {})
        if user.get("role", {}).get("role_name") == "college_counselor":
            return [self.college_counselor_serialize(user)]
        college_counselor = [self.college_counselor_serialize(i) for i in
                             await DatabaseConfiguration().user_collection.aggregate(
                                 [{"$match": {"role.role_name": "college_counselor",
                                  "is_activated": True}}]).to_list(
                                 length=user_length)]
        if len(college_counselor) < 1:
            return college_counselor
        try:
            college_counselor = [i for i in college_counselor if
                                 str(college_id) in i.get(
                                     "associated_colleges")]
        except:
            college_counselor = [i for i in college_counselor if
                                 current_user in i.get("associated_colleges")]
        if holiday:
            college_counselor = await self.filter_counselor(college_counselor)
        return college_counselor

    async def get_counselor_list(self, student, state_code=None, course=None,
                                 source_name=None, specialization=None,
                                 college_id=None, ):
        """
        get counselor list based on state, course and source parameter
        """
        length = await DatabaseConfiguration().user_collection.count_documents(
            {})
        counselors = []
        if state_code is not None:
            counselors = (await DatabaseConfiguration().user_collection.aggregate(
                [{"$match": {"course_assign": {"$in": [course]},
                             "role.role_name": "college_counselor",
                             "state_assign": {"$in": [state_code]},
                             "is_activated": True,
                             "source_assign": {"$in": [source_name]}, "$expr": {
                    "$in": [ObjectId(college_id), {
                        "$ifNull": ["$associated_colleges",
                                    []]}, ]}, }}]).to_list(length=length))
            if len(counselors) == 0:
                counselors = (
                    await DatabaseConfiguration().user_collection.aggregate(
                        [{"$match": {"course_assign": {"$exists": False},
                                     "role.role_name": "college_counselor",
                                     "state_assign": {"$exists": False},
                                     "is_activated": True,
                                     "specialization_name.spec_name": {"exists": False},
                         "source_assign": {"$in": [source_name]}, "$expr": {
                            "$in": [ObjectId(college_id), {
                                "$ifNull": ["$associated_colleges",
                                            []]}, ]}, }}]).to_list(
                        length=length))
                if len(counselors) == 0:
                    counselors = (
                        await DatabaseConfiguration().user_collection.aggregate(
                            [{"$match": {"role.role_name": "college_counselor",
                                         "is_activated": True,
                                         "state_assign": {"$in": [state_code]},
                                         "source_assign": {"$exists": False},
                                         "course_assign": {"$in": [course]}, "$expr": {
                                            "$in": [ObjectId(college_id), {
                                                "$ifNull": ["$associated_colleges",
                                                    []]}, ]}, }}]).to_list(
                            length=length))
                    if len(counselors) == 0:
                        counselors = (
                            await DatabaseConfiguration().user_collection.aggregate(
                                [{"$match": {"role.role_name": "college_counselor",
                                             "is_activated": True,
                                             "state_assign": {"$in": [state_code]},
                                             "course_assign": {"$exists": False},
                                             "source_assign": {"$in": [source_name]},
                                  "$expr": {"$in": [ObjectId(college_id), {
                                                    "$ifNull": ["$associated_colleges",
                                                     []]}, ]}, }}]).to_list(
                                length=length))
                        if len(counselors) == 0:
                            counselors = (
                                await DatabaseConfiguration().user_collection.aggregate(
                                    [{"$match": {"role.role_name": "college_counselor",
                                                 "is_activated": True,
                                                 "state_assign": {"$in": [state_code]},
                                                 "source_assign": {"$exists": False},
                                                 "course_assign": {"$exists": False},
                                     "$expr": {"$in": [ObjectId(college_id),
                                                       {"$ifNull": [
                                                           "$associated_colleges",
                                                           [], ]}, ]}, }}]).to_list(
                                    length=length))
                            if len(counselors) == 0:
                                counselors = (
                                    await DatabaseConfiguration().user_collection.aggregate(
                                        [{"$match": {"role.role_name": "college_counselor",
                                                     "is_activated": True,
                                                     "course_assign": {"$in": [course]},
                                                     "state_assign": {"$exists": False},
                                         "source_assign": {
                                             "$in": [source_name]},
                                         "$expr": {
                                             "$in": [ObjectId(college_id), {
                                                 "$ifNull": [
                                                     "$associated_colleges",
                                                     [], ]}, ]}, }}]).to_list(
                                        length=length))
                                if len(counselors) == 0:
                                    counselors = (
                                        await DatabaseConfiguration().user_collection.aggregate(
                                            [{"$match": {
                                                "role.role_name": "college_counselor",
                                                "is_activated": True,
                                                "course_assign": {
                                                    "$in": [course]},
                                                "specialization_name.spec_name": {
                                                    "$in": [specialization]},
                                                "state_assign": {
                                                    "$exists": False},
                                                "source_assign": {
                                                    "$exists": False},
                                                "$expr": {"$in": [
                                                    ObjectId(college_id), {
                                                        "$ifNull": [
                                                            "$associated_colleges",
                                                            [], ]}, ]}, }}]).to_list(
                                            length=length))
                                    if len(counselors) == 0:
                                        counselors = (
                                            await DatabaseConfiguration().user_collection.aggregate(
                                                [{"$match": {
                                                    "role.role_name": "college_counselor",
                                                    "is_activated": True,
                                                    "course_assign": {
                                                        "$in": [course]},
                                                    "state_assign": {
                                                        "$exists": False},
                                                    "source_assign": {
                                                        "$exists": False},
                                                    "$expr": {"$in": [
                                                        ObjectId(college_id), {
                                                            "$ifNull": [
                                                                "$associated_colleges",
                                                                [], ]}, ]}, }}]).to_list(
                                                length=length))
                                        if len(counselors) == 0:
                                            counselors = (
                                                await DatabaseConfiguration().user_collection.aggregate(
                                                    [{"$match": {
                                                        "role.role_name": "college_counselor",
                                                        "is_activated": True,
                                                        "source_assign": {
                                                            "$in": [
                                                                source_name]},
                                                        "course_assign": {
                                                            "$exists": False},
                                                        "state_assign": {
                                                            "$exists": False},
                                                        "$expr": {"$in": [
                                                            ObjectId(
                                                                college_id), {
                                                                "$ifNull": [
                                                                    "$associated_colleges",
                                                                    [], ]}, ]}, }}]).to_list(
                                                    length=length))
                                            if len(counselors) == 0:
                                                counselors = (
                                                    await DatabaseConfiguration().user_collection.aggregate(
                                                        [{"$match": {"course_assign": {
                                                            "$exists": False},
                                                            "role.role_name": "college_counselor",
                                                            "state_assign": {
                                                                "$exists": False},
                                                            "is_activated": True,
                                                            "source_assign": {
                                                                "$exists": False},
                                                            "$expr": {"$in": [
                                                                ObjectId(
                                                                    college_id),
                                                                {"$ifNull": [
                                                                    "$associated_colleges",
                                                                    [], ]}, ]}, }}]).to_list(
                                                        length=length))
        else:
            course_name = list(student["course_details"].keys())[0]
            if (
                    course := await DatabaseConfiguration().course_collection.find_one(
                        {"course_name": course_name,
                         "course_counselor": {"$exists": True}})) is not None:
                course_counselors = course["course_counselor"]
                counselors = (
                    await DatabaseConfiguration().user_collection.aggregate(
                        [{"$match": {"_id": {"$in": course_counselors},
                         "is_activated": True, "$expr": {
                            "$in": [ObjectId(college_id), {
                                "$ifNull": ["$associated_colleges",
                                            []]}, ]}, }}]).to_list(
                        length=length))
            else:
                counselors = (
                    await DatabaseConfiguration().user_collection.aggregate(
                        [{"$match": {"role.role_name": "college_counselor",
                         "course_assign": {"$exists": False},
                         "is_activated": True, "$expr": {
                            "$in": [ObjectId(college_id), {
                                "$ifNull": ["$associated_colleges",
                                            []]}, ]}, }}]).to_list(
                        length=length))
        return counselors

    async def active_counselors(self, counselors, state_code=None):
        """
        Get the active counselor list
        """
        if state_code is not None:
            college_counselor = [self.college_counselor_serialize(j) for j in
                                 counselors]
        else:
            college_counselor = [self.college_counselor_serialize(j) async for
                                 j in counselors]
        counselors = await self.filter_counselor(college_counselor)
        return counselors

    async def allocate_counselor(self, application_id: str, current_user=None,
                                 counselor_id=None, state_code=None,
                                 source_name=None, course=None,
                                 student=None, specialization=None, ):
        """
        Allocate the counselor_id
        """
        from app.dependencies.oauth import is_testing_env, cache_invalidation

        try:
            if (
                    student_application := await DatabaseConfiguration().studentApplicationForms.find_one(
                        {"_id": ObjectId(application_id)})) is None:
                raise HTTPException(status_code=404,
                                    detail="application not found")
        except Exception:
            raise HTTPException(status_code=403,
                                detail="application_id not valid")
        if (
                student_details := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(
                        str(student_application.get("student_id")))})) is None:
            raise HTTPException(status_code=404, detail="student not found")
        if counselor_id is None:
            if source_name == "organic":
                source_name = None
            counselors = []
            pipeline = [{"$match": {"is_activated": True, "$expr": {
                "$in": [ObjectId(student_application.get("college_id")),
                        {"$ifNull": ["$associated_colleges", []]}, ]}, }}]
            if course is not None:
                pipeline[0].get("$match", {}).update({"course_assign": course})
            if specialization is not None:
                pipeline[0].get("$match", {}).update(
                    {"specialization_name.spec_name": specialization})
            if source_name is not None:
                pipeline[0].get("$match", {}).update(
                    {"source_assign": source_name})
            counselor_details = DatabaseConfiguration().user_collection.aggregate(
                pipeline)
            async for data in counselor_details:
                count = await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
                    {"allocate_to_counselor.counselor_id": data.get("_id")})
                if data.get("fresh_lead_limit"):
                    if data.get("fresh_lead_limit", 0) > count:
                        counselors.append(data)
            if len(counselors) == 0:
                pipeline = [{"$match": {"is_activated": True,
                                        "fresh_lead_limit": {"$exists": True},
                                        "specialization_name.spec_name": {
                                            "$exists": False},
                                        "source_assign": {"$exists": False},
                                        "state_assign": {"$exists": False},
                                        "course_assign": {"$exists": False},
                                        "$expr": {"$in": [
                                            ObjectId(student_application.get(
                                                "college_id")),
                                            {"$ifNull": [
                                                "$associated_colleges",
                                                []]}, ]}, }}]
                counselor_details = DatabaseConfiguration().user_collection.aggregate(
                    pipeline)
                async for data in counselor_details:
                    count = await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
                        {"allocate_to_counselor.counselor_id": data.get(
                            "_id")})
                    if data.get("fresh_lead_limit"):
                        if data.get("fresh_lead_limit", 0) > count:
                            counselors.append(data)
            if len(counselors) == 0:
                counselors = await self.get_counselor_list(
                    student=student_details, state_code=state_code,
                    course=course, source_name=source_name,
                    specialization=specialization,
                    college_id=str(student_application.get("college_id")), )
            active_counselor = await self.active_counselors(counselors,
                                                            state_code)
            if len(active_counselor) < 1:
                counselors = DatabaseConfiguration().user_collection.aggregate(
                    [{"$match": {"course_assign": {"$exists": False},
                                 "role.role_name": "college_counselor",
                                 "state_assign": {"$exists": False},
                                 "is_activated": True,
                     "source_assign": {"$exists": False}, "$expr": {"$in": [
                        ObjectId(student_application.get("college_id")),
                        {"$ifNull": ["$associated_colleges", []]}, ]}, }}])
                active_counselor = await self.active_counselors(counselors)
            data = sorted(active_counselor,
                          key=lambda x: x.get("last_activity"))
            if len(data) == 0:
                return 0
            final_value = {"counselor_id": ObjectId(data[0].get("id")),
                           "counselor_name": data[0].get("name"),
                           "last_update": datetime.now(timezone.utc)}
            await DatabaseConfiguration().user_collection.update_one(
                {"_id": ObjectId(data[0].get("id"))},
                {"$set": {"last_activity": datetime.now(timezone.utc)}}, )
            await cache_invalidation(api_updated="updated_user", user_id=data[0].get("email"))
            counselor = await DatabaseConfiguration().user_collection.find_one(
                {"_id": ObjectId(ObjectId(data[0].get("id")))})
            user = counselor
            data = {"assigned_counselor_id": ObjectId(data[0].get("id")),
                    "assigned_counselor_name": data[0].get("name"),
                    "lead_stage": "Fresh Lead",
                    "timestamp": datetime.now(timezone.utc),
                    "user_id": ObjectId(str(student_details.get("_id"))),
                    "added_by": utility_obj.name_can(
                        student_details.get("basic_details")), }
            await DatabaseConfiguration().leadsFollowUp.insert_one(
                {"student_id": ObjectId(str(student_details.get("_id"))),
                 "application_id": ObjectId(application_id),
                 "lead_stage": "Fresh Lead",
                 "counselor_timeline": [data], })
        else:
            if student is None:
                if (
                        user := await DatabaseConfiguration().user_collection.find_one(
                            {"user_name": current_user})) is None:
                    raise HTTPException(status_code=404,
                                        detail="user not found")
            else:
                if (
                        student_details := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                            {"_id": ObjectId(student_application.get(
                                "student_id"))})) is None:
                    raise HTTPException(status_code=404,
                                        detail="student not found")
                user = student_details.get("basic_details", {})
                user["_id"] = student_details.get("_id")
            if (
                    counselor := await DatabaseConfiguration().user_collection.find_one(
                        {"_id": ObjectId(counselor_id)})) is None:
                raise HTTPException(status_code=404,
                                    detail="counselor not found")
            final_value = {"counselor_id": ObjectId(str(counselor.get("_id"))),
                           "counselor_name": utility_obj.name_can(counselor),
                           "last_update": datetime.now(timezone.utc)}
            if (lead := await DatabaseConfiguration().leadsFollowUp.find_one(
                    {"application_id": ObjectId(application_id)})) is not None:
                if lead.get("counselor_timeline") is None:
                    lead["counselor_timeline"] = []
                lead.get("counselor_timeline", []).insert(0, {
                    "assigned_counselor_id": ObjectId(
                        str(counselor.get("_id"))),
                    "assigned_counselor_name": utility_obj.name_can(counselor),
                    "lead_stage": "Fresh Lead",
                    "timestamp": datetime.now(timezone.utc),
                    "user_id": ObjectId(str(user.get("_id"))),
                    "added_by": utility_obj.name_can(user), }, )
                temp = lead.get("counselor_timeline")
                await DatabaseConfiguration().leadsFollowUp.update_one(
                    {"application_id": ObjectId(application_id)},
                    {"$set": {"counselor_timeline": temp}}, )
            else:
                await DatabaseConfiguration().leadsFollowUp.insert_one(
                    {"student_id": ObjectId(str(student_details.get("_id"))),
                     "application_id": ObjectId(application_id),
                     "lead_stage": "Fresh Lead", })
        data = {"allocate_to_counselor": final_value}
        await DatabaseConfiguration().studentsPrimaryDetails.update_one(
            {"_id": ObjectId(str(student_details.get("_id")))}, {"$set": data})
        await DatabaseConfiguration().studentApplicationForms.update_one(
            {"_id": ObjectId(application_id)}, {"$set": data})
        course = await DatabaseConfiguration().course_collection.find_one(
            {"_id": student_application.get("course_id")})
        if course is None:
            course = {}
        if not is_testing_env():
            course_name = (
                f"{course.get('course_name')} in {student_application.get('spec_name1')}" if student_application.get(
                    "spec_name1") not in ["",
                                          None] else f"{course.get('course_name')} Program")
            try:
                # Todo: We will delete this repeatedly code
                #  when celery is working fine
                name = utility_obj.name_can(
                    student_details.get("basic_details", {}))
                if current_user:
                    counselor_name = student_details.get(
                        'allocate_to_counselor', {}).get('counselor_name')
                    message = (f"Lead of {name} is assigned to "
                               f"{utility_obj.name_can(counselor)} from"
                               f" {counselor_name} "
                               f"by {utility_obj.name_can(user)} "
                               f"(for manual transfer)")
                else:
                    message = (f"Lead of {name} is assigned to "
                               f"{utility_obj.name_can(counselor)} "
                               f"by automated system"
                               f" (for round robin allocated leads)")

                if settings.environment in ["demo"]:
                    StudentActivity().student_timeline(
                        student_id=str(student_details.get("_id")),
                        event_type="Application",
                        event_status=f"Allocated Counselor",
                        application_id=str(student_application.get("_id")),
                        user_id=str(user.get("_id")) if user.get(
                            "_id") else None,
                        message=message,
                        college_id=str(
                            student_application.get("college_id")), )
                else:
                    StudentActivity().student_timeline.delay(
                        student_id=str(student_details.get("_id")),
                        event_type="Application",
                        event_status=f"Allocated Counselor",
                        application_id=str(student_application.get("_id")),
                        user_id=str(user.get("_id")) if user.get(
                            "_id") else None,
                        message=message,
                        college_id=str(
                            student_application.get("college_id")), )
            except KombuError as celery_error:
                logger.error(
                    f"error storing allocate counselor" f" timeline data {celery_error}")
            except Exception as error:
                logger.error(
                    f"error storing allocate counselor timeline data exception {error}")
        return True

    async def list_of_counselor_allocated_to_lead(self, current_user,
                                                  page_num=None,
                                                  page_size=None,
                                                  route_name=None,
                                                  college_id=None, ):
        """
        Get the list of counselor allocated to particular lead
        """
        length = await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
            {})
        if length < 1:
            raise HTTPException(status_code=404, detail="lead not found")
        if page_num and page_size:
            s = (page_num * page_size) - page_size
            total_lead = [self.lead_counselor_of_student(i) for i in
                          await DatabaseConfiguration().studentsPrimaryDetails.aggregate(
                              [{"$skip": s}, {"$limit": page_size}]).to_list(
                              length=length) if
                          i.get("allocate_to_counselor") is not None]
            response = await utility_obj.pagination_in_aggregation(page_num,
                                                                   page_size,
                                                                   length,
                                                                   route_name)
            return {"data": total_lead, "total": length, "count": page_size,
                    "pagination": response["pagination"],
                    "message": "Applications data fetched successfully!", }
        allocated_counselor = [self.lead_counselor_of_student(i) for i in
                               await DatabaseConfiguration().studentsPrimaryDetails.aggregate(
                                   []).to_list(length=length) if
                               i.get("allocate_to_counselor") is not None]
        return allocated_counselor

    async def counselor_wise_lead(self, current_user: str, date_range,
                                  college_id):
        """
        Get the detail of activities on the basis of counselor
        """
        if len(date_range) < 2:
            date_range = await utility_obj.last_3_month()
        start_date, end_date = await utility_obj.date_change_format(
            date_range.get("start_date"), date_range.get("end_date"))
        if (user := await DatabaseConfiguration().user_collection.find_one(
                {"user_name": current_user})) is None:
            raise HTTPException(status_code=404, detail="user not found")
        if user.get("role").get("role_name") == "college_publisher_console":
            raise HTTPException(status_code=403, detail="Not authenticated")
        lst = []
        if user.get("role").get("role_name") == "college_counselor":
            counselor_name = utility_obj.name_can(user)
            lead_length = (
                await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
                    {"allocate_to_counselor.counselor_id": ObjectId(
                        str(user.get("_id"))),
                        "created_at": {"$gte": start_date,
                                       "$lte": end_date}, }))
            data = len(["a" for i in
                        await DatabaseConfiguration().studentApplicationForms.aggregate(
                            [{"$match": {
                                "allocate_to_counselor.counselor_id": ObjectId(
                                    str(user.get("_id"))),
                                "enquiry_date": {"$gte": start_date,
                                                 "$lte": end_date}, }}]).to_list(
                            length=lead_length) if
                        i.get("declaration") is True])
            lst = [
                {"counselor_name": counselor_name, "total_lead": lead_length,
                 "total_paid": data, }]
            return lst
        total_counselor = await self.list_counselor(current_user, college_id)
        for i in total_counselor:
            lead_length = (
                await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
                    {"allocate_to_counselor.counselor_id": ObjectId(
                        str(i.get("id"))), "created_at": {"$gte": start_date,
                                                          "$lte": end_date}, }))
            data = len(["a" for i in
                        await DatabaseConfiguration().studentApplicationForms.aggregate(
                            [{"$match": {
                                "allocate_to_counselor.counselor_id": ObjectId(
                                    str(i.get("id"))),
                                "enquiry_date": {"$gte": start_date,
                                                 "$lte": end_date}}}]).to_list(
                            length=lead_length) if
                        i.get("declaration") is True])
            st = {"counselor_name": i.get("name"), "total_lead": lead_length,
                  "total_paid": data, }
            lst.append(st)
        return lst

    async def followup_reports(self, current_user, date_range,
                               counselor_filter, todays_followup,
                               upcoming_followup,
                               overdue_followup, completed_followup,
                               college_id, sort, sort_name, sort_type, 
                               search=None):
        """Returns the followup data of current user"""
        if (user := await DatabaseConfiguration().user_collection.find_one(
                {"user_name": current_user})) is None:
            raise HTTPException(status_code=404, detail="user not found")
        date_range = jsonable_encoder(date_range)
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date"))
        if counselor_filter is None:
            counselor_filter = {}
        counselor_filter = jsonable_encoder(counselor_filter)
        pipeline = list()
        counselor_id = []
        if user.get("role", {}).get("role_name") == "college_counselor":
            counselor_id = [ObjectId(user.get("_id"))]
        else:
            if counselor_filter.get("counselor_id"):
                counselor_id = [ObjectId(counselor) for counselor in
                                counselor_filter.get("counselor_id")]
            elif user.get("role", {}).get(
                    "role_name") == "college_head_counselor":
                counselor_detail = DatabaseConfiguration().user_collection.aggregate(
                    [{"$match": {"head_counselor_id": ObjectId(user.get("_id")),"associated_colleges": {"$in": college_id}}}])
                counselor_id = [ObjectId(counselor.get("_id"))
                                async for counselor in counselor_detail]
            else:
                counselor_detail = await DatabaseConfiguration().user_collection.aggregate([{"$match": {
                    "role.role_name": "college_counselor",
                    "is_activated": True,
                    "associated_colleges": {"$in": college_id}
                }}]).to_list(None)
                counselor_id = [ObjectId(counselor.get("_id")) for counselor in counselor_detail]
        pipeline.extend([{"$match": {"$or": [{"lead_stage": "Follow-up"}, {
            "followup": {
                "$all": [{"$elemMatch": {"status": "Completed"}}]}}, ],
                                     "followup": {"$exists": True,
                                                  "$all": [{"$elemMatch": {
                                                      "assigned_counselor_id": {
                                                          "$in": counselor_id}}}], }, }},
                         {
                             "$project": {"_id": 0, "student_id": 1,
                                          "application_id": 1,
                                          "followup": 1, }}, {
                             "$lookup": {"from": "studentApplicationForms",
                                         "let": {
                                             "application_id": "$application_id"},
                                         "pipeline": [{
                                             "$match": {
                                                 "$expr": {"$eq": ["$_id",
                                                                   "$$application_id"]}}},
                                             {
                                                 "$project": {"_id": 0,
                                                              "payment_info": 1,
                                                              "spec_name1": 1,
                                                              "course_id": 1, }}, ],
                                         "as": "student_application", }},
                         {"$unwind": {"path": "$student_application"}}, {
                             "$lookup": {"from": "studentsPrimaryDetails",
                                         "let": {"student_id": "$student_id"},
                                         "pipeline": [{
                                             "$match": {
                                                 "$expr": {"$eq": ["$_id",
                                                                   "$$student_id"]}}},
                                             {"$project": {"_id": 0,
                                                           "basic_details": 1}}, ],
                                         "as": "student_primary", }}, {
                             "$unwind": {"path": "$student_primary",
                                         "preserveNullAndEmptyArrays": True, }},
                         {
                             "$lookup": {"from": "courses",
                                         "let": {
                                             "course_id": "$student_application.course_id"},
                                         "pipeline": [{
                                             "$match": {"$expr": {
                                                 "$eq": ["$_id",
                                                         "$$course_id"]}}},
                                             {"$project": {"_id": 0,
                                                           "course_name": 1}}, ],
                                         "as": "course_details", }},
                         {"$unwind": {"path": "$course_details"}}, ])
        if date_range:
            pipeline[0].get("$match", {}).get("followup", {}).get("$all", [])[
                0].get("$elemMatch", {}).update(
                {"followup_date": {"$gte": start_date, "$lte": end_date}})
        if counselor_filter.get("lead_stage"):
            for load in counselor_filter.get("lead_stage", []):
                lead_stages = load.get("name", [])
                if "Fresh Lead" in lead_stages:
                    lead_stages.append(None)

                if load.get("label"):
                    pipeline[0].get("$match").update(
                        {"lead_stage_label": {"$in": load.get("label", [])}})
                if lead_stages:
                    pipeline[0].get("$match").update(
                        {"lead_stage": {"$in": lead_stages}})
        if counselor_filter.get("course"):
            course_id, specialization_name = [], []
            for course in counselor_filter.get("course"):
                if (course.get("course_id") is not None and course.get(
                        "course_id") != ""):
                    course_id.append(ObjectId(course.get("course_id")))
                if (course.get(
                        "specialization_name") is not None and course.get(
                    "specialization_name") != ""):
                    specialization_name.append(
                        course.get("specialization_name"))
            if len(course_id) > 0:
                pipeline[2].get("$lookup").get("pipeline")[0].get(
                    "$match").update({"course_id": {"$in": course_id}})
            if len(specialization_name) > 0:
                pipeline[2].get("$lookup").get("pipeline")[0].get(
                    "$match").update(
                    {"spec_name1": {"$in": specialization_name}})
        result = DatabaseConfiguration().leadsFollowUp.aggregate(pipeline)
        all_followups_data, today = [], datetime.now(timezone.utc).date()
        async for followup_data in result:
            data = {}
            data.update({"student_name": utility_obj.name_can(
                followup_data.get("student_primary", {}).get("basic_details")),
                "student_id": str(followup_data.get("student_id")),
                "application_id": str(followup_data.get("application_id")),
                "course_name": (
                    f"{followup_data.get('course_details', {}).get('course_name')} in {followup_data.get('student_application', {}).get('spec_name1')}" if followup_data.get(
                        "student_application", {}).get(
                        "spec_name1") is not None and followup_data.get(
                        "student_application", {}).get(
                        "spec_name1") != "" else f"{followup_data.get('course_details').get('course_name')}"),
                "counselor_name": followup_data.get("followup")[0].get(
                    "assigned_counselor_name"),
                "created_by": followup_data.get("followup")[0].get(
                    "added_by"), })
            for count, i in enumerate(followup_data.get("followup")):
                followup_date = i.get("followup_date")
                followup_date = utility_obj.get_local_time(followup_date)
                datetime_obj = datetime.strptime(followup_date,
                                                          "%d %b %Y %I:%M:%S %p")
                followup_date = datetime_obj.strftime("%Y-%m-%d")
                if i.get("assigned_counselor_id") in counselor_id:
                    if date_range:
                        if (datetime.strftime(start_date,
                                                       "%Y-%m-%d") <= followup_date <= datetime.strftime(
                            end_date, "%Y-%m-%d")):
                            pass
                        else:
                            continue
                    status = ("Upcoming" if followup_date > today.strftime(
                        "%Y-%m-%d") else "Overdue")
                    status = ("Today" if followup_date == today.strftime(
                        "%Y-%m-%d") else status)
                    status = ("completed" if str(
                        i.get("status")).lower() == "completed" else status)
                    days = 0
                    if status == "Overdue":
                        over = datetime.now(timezone.utc) - i.get(
                            "followup_date")
                        days = over.days
                    days_gap = 0
                    if status == "completed":
                        if i.get("updated_date"):
                            if i.get("updated_date") > i.get("followup_date"):
                                days_gap = i.get("updated_date") - i.get(
                                    "followup_date")
                                days_gap = days_gap.days
                    if todays_followup:
                        if status != "Today":
                            continue
                    if upcoming_followup:
                        if status != "Upcoming":
                            continue
                    if overdue_followup:
                        if status != "Overdue":
                            continue
                    if completed_followup:
                        if status != "completed":
                            continue
                    data.update({"status": status,
                                 "followup_date": utility_obj.get_local_time(
                                     i.get("followup_date")),
                                 "lead_activity": utility_obj.get_local_time(
                                     i.get("timestamp")), "overdue_days": days,
                                 "index_number": count,
                                 "updated_by": i.get("updated_by", ""),
                                 "created_on": utility_obj.get_local_time(
                                     i.get("timestamp")), "updated_date": (
                            utility_obj.get_local_time(
                                i.get("updated_date")) if i.get("updated_date",
                                                                "") != "" else i.get(
                                "updated_date", "")), "days_gap": days_gap, 
                                "followup_label": None})    # TODO: The follow-up label should be stored with the follow-up in the database.
                    all_followups_data.append(data.copy())
        if search is not None:
            all_followups_data = [data for data in all_followups_data if
                                  search == data.get("student_name")]
            
        if sort:
            if sort_name in ['followup_date', 'lead_activity', "created_on"]:
                all_followups_data.sort(key=lambda x: datetime.strptime(x[sort_name], '%d %b %Y %I:%M:%S %p'), reverse=False if sort_type == "asc" else True)
            else:
                all_followups_data.sort(key=lambda x: x[sort_name], reverse=False if sort_type == "asc" else True)

        return all_followups_data, len(all_followups_data)

    async def counselor_timeline_history(self, lead, data, application_id):
        """
        Get the history of counselor timeline
        """
        data.update({"lead_stage": (lead.get("lead_stage") if lead.get(
            "lead_stage") is not None else "Fresh Lead")})
        if lead.get("counselor_timeline"):
            lead.get("counselor_timeline").insert(0, data)
            temp = lead.get("counselor_timeline")
            await DatabaseConfiguration().leadsFollowUp.update_one(
                {"application_id": ObjectId(application_id)},
                {"$set": {"counselor_timeline": temp}}, )
        else:
            temp = [data]
            await DatabaseConfiguration().leadsFollowUp.update_one(
                {"application_id": ObjectId(application_id)},
                {"$set": {"counselor_timeline": temp}}, )

    async def counselor_allocate_to_multiple(self, application_id: list,
                                             counselor_id: str, user: dict):
        try:
            counselor = await DatabaseConfiguration().user_collection.find_one(
                {"_id": ObjectId(counselor_id)})
        except:
            raise HTTPException(status_code=404, detail="counselor not found")
        counselor_name, counselor_id = (utility_obj.name_can(counselor),
                                        ObjectId(str(counselor.get("_id"))),)
        assigned_lead_count, user_name = 0, utility_obj.name_can(user)
        for app_id in application_id:
            data = {"allocate_to_counselor": {"counselor_id": counselor_id,
                                              "counselor_name": counselor_name,
                                              "last_update": datetime.now(timezone.utc)}}
            try:
                application = (await (
                    DatabaseConfiguration().studentApplicationForms.find_one(
                        {"_id": ObjectId(app_id)})))
            except Exception:
                raise HTTPException(status_code=404,
                                    detail=f"{app_id} application_id not found")
            if (
                    student := await DatabaseConfiguration().studentsPrimaryDetails.find_one(
                        {"_id": ObjectId(
                            str(application.get("student_id")))})) is None:
                continue
            prev_counselor = student.get("allocate_to_counselor", {})
            if prev_counselor:
                data["previous_allocate_to_counselor"] = prev_counselor
            lead = await DatabaseConfiguration().leadsFollowUp.find_one(
                {"application_id": ObjectId(app_id),
                 "student_id": ObjectId(str(student.get("_id"))), })
            queries = await DatabaseConfiguration().queries.aggregate([
                {"$match": {"application_id": ObjectId(app_id), "student_id": student.get("_id")}},
                {"$group": {"_id": "$application_id", "query_ids": {"$push": "$_id"}}},
                {"$project": {"_id": 0, "query_ids": 1}}
            ]).to_list(None)
            query_ids = queries[0].get("query_ids", []) if queries and queries[0] else None
            if query_ids:
                query_data = {"assigned_counselor_id": counselor_id, "assigned_counselor_name": counselor_name,
                              "updated_at": datetime.now(timezone.utc)}
                await DatabaseConfiguration().queries.update_many(
                    {"_id": {"$in": query_ids}}, {"$set": query_data}
                )
            current_datetime = datetime.now(timezone.utc)
            update_info = {**data, "last_user_activity_date": current_datetime}
            if not student.get("first_lead_activity_date"):
                update_info["first_lead_activity_date"] = current_datetime
            await DatabaseConfiguration().studentsPrimaryDetails.update_one(
                {"_id": ObjectId(str(student.get("_id")))}, {"$set": update_info})
            assigned_lead_count += 1
            await DatabaseConfiguration().studentApplicationForms.update_one(
                {"_id": ObjectId(app_id)}, {"$set": data})
            course = await DatabaseConfiguration().course_collection.find_one(
                {"_id": application.get("course_id")})
            if course is None:
                course = {}
            try:
                toml_data = utility_obj.read_current_toml_file()
                if toml_data.get("testing", {}).get("test") is False:
                    StudentActivity().student_timeline.delay(
                        student_id=str(student.get("_id")),
                        event_type="Application",
                        event_status=f"Allocated Counselor whose name: "
                                     f"{counselor_name}",
                        application_id=str(application.get("_id")),
                        event_name=(f"{course.get('course_name')} in "
                                    f"{application.get('spec_name1')}" if (
                                application.get(
                                    "spec_name1") != "" and application.get(
                            "spec_name1")) else f"{course.get('course_name')} Program"),
                        message=f"Lead of {utility_obj.name_can(student.get('basic_details'))} is assigned"
                                f" to {counselor_name} from"
                                f" {prev_counselor.get('counselor_name', 'None')} by {user_name}",
                        college_id=str(student.get("college_id")), )
            except KombuError as celery_error:
                logger.error(f"error storing time line data {celery_error}")
            except Exception as error:
                logger.error(f"error storing time line data {error}")
            if lead is not None:
                if lead.get("followup"):
                    followup = {"assigned_counselor_id": counselor_id,
                                "assigned_counselor_name": counselor_name,
                                "lead_stage": (
                                    lead.get("lead_stage") if lead.get(
                                        "lead_stage") is not None else "Fresh Lead"),
                                "timestamp": datetime.now(timezone.utc),
                                "user_id": ObjectId(str(user.get("_id"))),
                                "added_by": user_name, }
                    await self.counselor_timeline_history(lead, followup,
                                                          app_id)
                    lead.get("followup")[0].update(followup)
                    followup_data = {"followup": lead.get("followup")}
                    await DatabaseConfiguration().leadsFollowUp.update_one(
                        {"_id": ObjectId(str(lead.get("_id")))},
                        {"$set": followup_data})
        data.update({"assigned_lead_count": assigned_lead_count,
                     "user_name": user_name,
                     "user_role": user.get("role", {}).get("role_name"), })
        await utility_obj.update_notification_db(event="Allocate counselor",
                                                 data=data)
        return True, counselor

    async def counselor_wise_data(self, date_range, college_id, season=None):
        """
        Get data on the basis of counselor
        """
        if len(date_range) < 2:
            date_range = await utility_obj.last_3_month()
        start_date, end_date = await utility_obj.date_change_format(
            date_range.get("start_date"), date_range.get("end_date"))
        pipeline = [{"$match": {"college_id": ObjectId(college_id),
                                "enquiry_date": {"$gte": start_date,
                                                 "$lte": end_date}, }}, {
                        "$project": {"_id": 1, "student_id": 1,
                                     "allocate_to_counselor": 1,
                                     "current_stage": 1, }}, {
                        "$lookup": {"from": "leadsFollowUp",
                                    "localField": "_id",
                                    "foreignField": "application_id",
                                    "as": "student_source", }}, {
                        "$unwind": {"path": "$student_source",
                                    "preserveNullAndEmptyArrays": True, }}, {
                        "$group": {
                            "_id": "$allocate_to_counselor.counselor_id",
                            "student": {"$push": {"form_initialize": {
                                "$cond": [{"$gte": ["$current_stage", 2.0]}, 1,
                                          0]},
                                "lead_stage": {
                                    "$ifNull": ["$student_source.lead_stage",
                                                "Fresh Lead"]}, }}, }}, {
                        "$project": {"_id": "$_id",
                                     "count": {
                                         "$sum": "$student.form_initialize"},
                                     "lead_stage": {
                                         "$ifNull": ["$student.lead_stage",
                                                     "Fresh Lead"]}, }}, ]
        result = DatabaseConfiguration(
            season=season).studentApplicationForms.aggregate(pipeline)
        lst = []
        async for doc in result:
            if (user := await DatabaseConfiguration(
                    season=season).user_collection.find_one(
                {"_id": doc.get("_id")})) is None:
                continue
            data = {"counselor_name": utility_obj.name_can(user),
                    "total_count": doc.get("count"), }
            leads = list(set(doc.get("lead_stage")))
            for lead in leads:
                if lead == "":
                    data["fresh_lead"] = doc.get("lead_stage").count(lead)
                else:
                    data[lead] = doc.get("lead_stage").count(lead)
            lst.append(data)
        lst_temp = sorted(lst, key=lambda x: x.get("total_count"),
                          reverse=True)
        return lst_temp[:5]

    async def counselor_performance_average(self, counselor_id, start_date,
                                            end_date):
        """getting value total allocate and paid application"""
        pipeline = [{"$match": {
            "allocate_to_counselor.counselor_id": ObjectId(counselor_id),
            "allocate_to_counselor.last_update": {"$gte": start_date,
                                                  "$lte": end_date, }, }},
            {"$project": {"_id": 1, "payment_info": 1}}, {
                "$group": {"_id": "", "total_allocate": {"$sum": 1},
                           "paid_lead": {"$push": {"$cond": [
                               {"$eq": ["$payment_info.status", "captured"]},
                               1,
                               0, ]}}, }}, {
                "$project": {"_id": 0, "total_lead": "$total_allocate",
                             "paid_lead": {"$sum": "$paid_lead"}, }}, ]
        result = DatabaseConfiguration().studentApplicationForms.aggregate(
            pipeline)
        async for data in result:
            if data is not None:
                return data
        return {}
     
    async def data_date_helper(self, date_range: dict, college_id: str, counselor_id: list, season: str | None = None,
                               counselor_ids: list | None = None, mode: str | None = None) -> list:
        """Helper function to get data according to the different dates.

        Params:
            date_range (_type_): Date range - start_date and end_date.
            college_id (_type_): COllege unique id
            counselor_id (_type_): counselor id which has to be retrive
            season (_type_, optional): season year.
            counselor_ids (_type_, optional): List of counsellor id which data has to retrive. Defaults to None.
            mode (str | None): Default value: None. Name of a mode. Possible values: Origin, Activity and Assignment.

        Returns:
            list: Return the sets of data as per counselor.
        """
        base_match = {"college_id": ObjectId(college_id)}
        filter_field_name = "allocate_to_counselor.last_update" if mode == "Assignment" else "lead_stage_change_at" \
            if mode == "Activity" else "enquiry_date"
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date"))
            base_match.update({filter_field_name: {"$gte": start_date, "$lte": end_date}})

        if counselor_ids:
            base_match.update({
                "allocate_to_counselor.counselor_id": {"$in": [ObjectId(_id) for _id in counselor_ids]}
            })
        
        return await DatabaseConfiguration(season=season).studentApplicationForms.aggregate([
            {"$match": base_match},
            {"$project": {"_id": 1, "student_id": 1, "allocate_to_counselor": 1, "declaration": 1}},
            {"$match": {"allocate_to_counselor.counselor_id": {"$in": counselor_id}}},
            {"$lookup": {
                "from": "leadsFollowUp",
                "localField": "_id",
                "foreignField": "application_id",
                "as": "lead_source",
            }},
            {"$addFields": {"lead_source": {"$arrayElemAt": ["$lead_source", 0]}}},
            {"$group": {
                "_id": {
                    "counselor_id": "$allocate_to_counselor.counselor_id",
                    "counselor_name": "$allocate_to_counselor.counselor_name",
                    "lead_stage": {"$ifNull": ["$lead_source.lead_stage", "Fresh Lead"]},
                    "lead_sub_stage": {"$ifNull": ["$lead_source.lead_stage_label", ""]}
                },
                "count": {"$sum": 1},
                "submitted_leads": {"$sum": {"$cond": [{"$eq": ["$declaration", True]}, 1, 0]}}
            }},
            {"$project": {
                "_id": {"$toString": "$_id.counselor_id"},
                "counselor_name": "$_id.counselor_name",
                "lead_stage": "$_id.lead_stage",
                "lead_sub_stage": "$_id.lead_sub_stage",
                "count": 1,
                "submitted_leads": 1
            }}
        ]).to_list(None)

    async def counselor_performance(self, date_range, college_id, change_indicator=None, 
                                    season=None, counselor_ids=None, mode=None):
        """
        Get the performance of counselor
        """
        pipeline2 = [
            {"$match": {"is_activated": True, "role.role_name": "college_counselor"}},
            {"$group": {"_id": None, "counselor_ids": {"$push": "$_id"}}},
        ]
        
        results = DatabaseConfiguration().user_collection.aggregate(pipeline2)
        counselor_id = []
        async for data2 in results:
            counselor_id = data2.get("counselor_ids", [])
        
        base_match, paid_app_match = {}, {"payment_info.status": "captured"}

        result = await self.data_date_helper(date_range, college_id, counselor_id, season, counselor_ids, mode)
        
        query_pipeline = [
            {"$group": {"_id": {"$toString": "$assigned_counselor_id"}, "count": {"$sum": 1}}}
        ]
        filter_field_name = "allocate_to_counselor.last_update" if mode == "Assignment" else "lead_stage_change_at" \
            if mode == "Activity" else "created_at"
        app_filter_field_name = "payment_info.created_at" if filter_field_name == "created_at" else filter_field_name
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date"))
            date_range_match = {"$gte": start_date, "$lte": end_date}
            query_pipeline.insert(1, {"$match": {"created_at": date_range_match}})
            base_match.update({filter_field_name: date_range_match})
            paid_app_match.update({app_filter_field_name: date_range_match})
        
        queries = (
            await DatabaseConfiguration(season=season).queries.aggregate(query_pipeline).to_list(None)
        )
        queries = {item["_id"]: item["count"] for item in queries}
        headers = [{"lead_stage": "counselor_name", "sub_stage": []},
                   {"lead_stage": "total_leads", "sub_stage": []},
                   {"lead_stage": "verified", "sub_stage": []},
                   {"lead_stage": "paid", "sub_stage": []},
                   {"lead_stage": "submitted", "sub_stage": []},
                   {"lead_stage": "queries", "sub_stage": []},
                   ]
        headers_names = ["counselor_name", "total_leads", "verified", "paid",
                         "submitted", "queries"]
        total_data_dict = {
            "counselor_name": {"value": "Total", "sub_stage_data": {}},
            "total_leads": {"value": 0, "sub_stage_data": {}},
            "verified": {"value": 0, "sub_stage_data": {}},
            "paid": {"value": 0, "sub_stage_data": {}},
            "submitted": {"value": 0, "sub_stage_data": {}},
            "queries": {"value": 0, "sub_stage_data": {}}}
        lead, final_result, temp_dict, final_data = {}, [], {}, []
        existing_lead_stages = {}

        if change_indicator is not None:
            start_date, middle_date, previous_date = await utility_obj.get_start_date_and_end_date_by_change_indicator(change_indicator)

            previous_date_data = await self.data_date_helper({"start_date": str(start_date), "end_date": str(middle_date)}, college_id, counselor_id, season, counselor_ids)
            current_date_data = await self.data_date_helper({"start_date": str(previous_date), "end_date": str(date.today())}, college_id, counselor_id, season, counselor_ids)

        for doc in result:

            if change_indicator:
                prev_data_counselor, curr_data_counselor = {}, {}
                for prev_data in previous_date_data:
                    if prev_data.get("_id") == doc.get("_id"):
                        prev_data_counselor = prev_data
                        break
                
                for curr_data in current_date_data:
                    if curr_data.get("_id") == doc.get("_id"):
                        curr_data_counselor = curr_data
                        break

            counselor_id = doc.get("_id")
            if counselor_id != "None":
                if doc.get('lead_stage') in ["", None]:
                    lead_stage = "fresh_lead"
                else:
                    lead_stage = doc.get('lead_stage').replace(' ',
                                                               '_').lower()
                data_count = doc.get("count", 0)
                if change_indicator:
                    data_count_prev = prev_data_counselor.get("count", 0)
                    data_count_curr = curr_data_counselor.get("count", 0)
                    data_count_change_indicator = await utility_obj.get_percentage_difference_with_position(data_count_prev, data_count_curr)

                lead_sub_stage = doc.get("lead_sub_stage")
                sub_stage_data = {
                    lead_sub_stage: data_count} if lead_sub_stage not in ["",
                                                                          None] else {}
                if lead_stage in total_data_dict:
                    sub_stage_data_info = total_data_dict.get(
                        lead_stage, {}).get("sub_stage_data", {})
                    if lead_sub_stage not in ["", None] and sub_stage_data:
                        if lead_sub_stage not in sub_stage_data_info:
                            sub_stage_data_info.update(sub_stage_data)
                            total_data_dict.get(lead_stage, {})[
                                "sub_stage_data"] = sub_stage_data_info
                            total_data_dict.get(lead_stage, {}).get(
                                "sub_stage_data", {})[
                                lead_sub_stage] = total_data_dict.get(
                                lead_stage, {}).get("sub_stage_data", {}).get(
                                lead_sub_stage, 0) + data_count
                        else:
                            total_data_dict.get(lead_stage, {}).get(
                                "sub_stage_data", {})[
                                lead_sub_stage] = total_data_dict.get(
                                lead_stage, {}).get("sub_stage_data", {}).get(
                                lead_sub_stage, 0) + data_count
                    total_data_dict.get(lead_stage)[
                        "value"] = data_count + total_data_dict.get(
                        lead_stage, {}).get("value", 0)
                else:
                    total_data_dict.update({lead_stage: {
                        "value": data_count,
                        "sub_stage_data": sub_stage_data}})

                if lead_stage in existing_lead_stages:
                    if lead_sub_stage not in ["",
                                              None] and lead_sub_stage not in existing_lead_stages.get(
                        lead_stage):
                        temp_value = existing_lead_stages.get(lead_stage) + [
                            lead_sub_stage]
                        existing_lead_stages[lead_stage] = temp_value
                        for _id, item in enumerate(headers):
                            if item.get("lead_stage") == lead_stage:
                                headers[_id]["sub_stage"] = temp_value
                                break
                else:
                    lead_stage_exist = False
                    for _id, item in enumerate(headers):
                        if item.get("lead_stage") == lead_stage:
                            if lead_sub_stage not in ["", None]:
                                temp_value = [lead_sub_stage]
                                headers[_id]["sub_stage"] = temp_value
                            lead_stage_exist = True
                            break
                    if lead_stage_exist is False:
                        headers.append({"lead_stage": lead_stage,
                                        "sub_stage": [
                                            lead_sub_stage] if lead_sub_stage not in [
                                            "",
                                            None] else []})
                        headers_names.append(lead_stage)

                    if lead_sub_stage not in ["", None]:
                        existing_lead_stages.update(
                            {lead_stage: [lead_sub_stage]})

                if temp_dict.get(counselor_id):
                    update_data = temp_dict.get(counselor_id, {})
                    for item in [("submitted", "submitted_leads")]:
                        key_name = item[0]
                        update_data.get(key_name, {})[
                            "value"] = update_data.get(key_name, {}).get(
                            "value", 0) + doc.get(item[1], 0)
                        total_data_dict.get(key_name)["value"] = doc.get(
                            item[1], 0) + total_data_dict.get(key_name).get(
                            "value")
                    if lead_stage in temp_dict.get(counselor_id, {}):
                        sub_stage_data_update = update_data.get(
                            lead_stage).get("sub_stage_data")

                        sub_stage_data_update.update(sub_stage_data)
                        update_data.get(lead_stage).update({
                            "value": update_data.get(lead_stage, {}).get(
                                "value", 0) + data_count,
                            "sub_stage_data": sub_stage_data_update})
                    else:
                        update_data.update({lead_stage: {"value": data_count, "sub_stage_data": sub_stage_data}} if lead_stage != "fresh_lead" else {
                            lead_stage: {"value": data_count, "sub_stage_data": sub_stage_data, "percentage": data_count_change_indicator.get("percentage", 0), "position": data_count_change_indicator.get("position", "equal")}
                        })
                    temp_dict[counselor_id] = update_data
                else:
                    query_count = queries.get(counselor_id)
                    if query_count is None:
                        query_count = 0
                    common_match: dict = {"college_id": ObjectId(college_id),
                                          "allocate_to_counselor.counselor_id":
                                              ObjectId(counselor_id)}
                    base_match.update(common_match)
                    paid_app_match.update(common_match)
                    doc["total_lead"] = await DatabaseConfiguration(season=season).studentsPrimaryDetails.count_documents(base_match)
                    doc["paid_lead"] = await DatabaseConfiguration(season=season).studentApplicationForms.count_documents(paid_app_match)
                    base_match.update({"is_verify": True})
                    doc["verified_leads"] = await DatabaseConfiguration(season=season).studentsPrimaryDetails.count_documents(base_match)
                    base_match.pop("is_verify")

                    total_lead_change_indicator, verified_lead_change_indicator, paid_lead_change_indicator, submitted_lead_change_indicator = {}, {}, {}, {}
                    if change_indicator:
                        start_date, middle_date, previous_date = await utility_obj.get_start_date_and_end_date_by_change_indicator(change_indicator)
                        base_match.update({filter_field_name: {"start_date": str(start_date), "end_date": str(middle_date)}})
                        paid_app_match.update({app_filter_field_name: {"start_date": str(start_date), "end_date": str(middle_date)}})

                        prev_data_counselor["total_lead"] = await DatabaseConfiguration(season=season).studentsPrimaryDetails.count_documents(base_match)
                        prev_data_counselor["paid_lead"] = await DatabaseConfiguration(season=season).studentApplicationForms.count_documents(paid_app_match)
                        prev_data_counselor["verified_leads"] = await DatabaseConfiguration(season=season).studentsPrimaryDetails.count_documents(base_match)

                        base_match.update({filter_field_name: {"start_date": str(previous_date), "end_date": str(date.today())}})
                        paid_app_match.update({app_filter_field_name: {"start_date": str(previous_date), "end_date": str(date.today())}})

                        curr_data_counselor["total_lead"] = await DatabaseConfiguration(season=season).studentsPrimaryDetails.count_documents(base_match)
                        curr_data_counselor["paid_lead"] = await DatabaseConfiguration(season=season).studentApplicationForms.count_documents(paid_app_match)
                        curr_data_counselor["verified_leads"] = await DatabaseConfiguration(season=season).studentsPrimaryDetails.count_documents(base_match)

                        total_lead_change_indicator = await utility_obj.get_percentage_difference_with_position(prev_data_counselor.get("total_lead", 0), curr_data_counselor.get("total_lead", 0))
                        paid_lead_change_indicator = await utility_obj.get_percentage_difference_with_position(prev_data_counselor.get("paid_lead", 0), curr_data_counselor.get("paid_lead", 0))
                        verified_lead_change_indicator = await utility_obj.get_percentage_difference_with_position(prev_data_counselor.get("verified_leads", 0), curr_data_counselor.get("verified_leads", 0))
                        submitted_lead_change_indicator = await utility_obj.get_percentage_difference_with_position(prev_data_counselor.get("submitted_leads", 0), curr_data_counselor.get("submitted_leads", 0))

                    
                    temp_dict[counselor_id] = {
                        "counselor_name": {"value": doc.get("counselor_name", ""), "sub_stage_data": {}},
                        "total_leads": {"value": doc.get("total_lead", 0), "sub_stage_data": {}, "percentage": total_lead_change_indicator.get("percentage", 0), "position": total_lead_change_indicator.get("position", "equal")},
                        "verified": {"value": doc.get("verified_leads", 0), "sub_stage_data": {}, "percentage": verified_lead_change_indicator.get("percentage", 0), "position": verified_lead_change_indicator.get("position", "equal")},
                        "paid": {"value": doc.get("paid_lead", 0), "sub_stage_data": {}, "percentage": paid_lead_change_indicator.get("percentage", 0), "position": paid_lead_change_indicator.get("position", "equal")},
                        "submitted": {"value": doc.get("submitted_leads", 0), "sub_stage_data": {}, "percentage": submitted_lead_change_indicator.get("percentage", 0), "position": submitted_lead_change_indicator.get("position", "equal")},
                        "queries": {"value": query_count, "sub_stage_data": {}, "percentage": 0, "position": "equal"}
                    }
                    
                    temp_dict[counselor_id].update({lead_stage: {"value": data_count, "sub_stage_data": sub_stage_data}} if lead_stage != "fresh_lead" else {
                        lead_stage: {"value": data_count, "sub_stage_data": sub_stage_data, "percentage": data_count_change_indicator.get("percentage", 0), "position": data_count_change_indicator.get("position", "equal")}
                    })
                    
                    for item in [("total_leads", "total_lead"), ("verified", "verified_leads"), ("paid", "paid_lead"), ("submitted", "submitted_leads")]:
                        total_data_dict.get(item[0])["value"] = doc.get(item[1], 0) + total_data_dict.get(item[0]).get("value")
                    total_data_dict.get("queries")["value"] = query_count + total_data_dict.get("queries").get("value", 0)

        for _id, data_dict in enumerate(temp_dict.values()):
            final_temp_dict = {}
            for name in headers_names:
                if name in data_dict:
                    if name in existing_lead_stages:
                        sub_stages = data_dict.get(name, {}).get(
                            "sub_stage_data", {})
                        sub_stages_info = {}
                        for item in existing_lead_stages.get(name, []):
                            if item not in ["", None]:
                                if item in sub_stages:
                                    sub_stages_info.update(
                                        {item: sub_stages[item]})
                                else:
                                    sub_stages_info.update({item: 0})
                        data_dict[name]["sub_stage_data"] = sub_stages_info
                    final_temp_dict.update({name: data_dict[name]})
                else:
                    sub_stages_info = {}
                    [sub_stages_info.update({item: 0}) for item in
                     existing_lead_stages.get(name, [])]
                    final_temp_dict.update({name: {
                        "value": 0,
                        "sub_stage_data": sub_stages_info}} if name != "fresh_lead" else {
                        name: {
                            "value": 0, "sub_stage_data": sub_stages_info,
                            "percentage": 0, "position": "equal"}})
            if final_temp_dict:
                final_data.append(final_temp_dict)
        return headers, final_data, [total_data_dict]

    async def leave_counselor(self, counselor_leave, college_id):
        try:
            counselor = await DatabaseConfiguration().user_collection.find_one(
                {"_id": ObjectId(counselor_leave.get("counselor_id")),
                 "associated_colleges": {"$in": college_id}, })
        except Exception:
            raise HTTPException(status_code=404, detail="counselor not found")
        if counselor is None:
            counselor = {}
        if (
                user := await DatabaseConfiguration().counselor_management.find_one(
                    {"counselor_id": ObjectId(
                        counselor_leave.get("counselor_id"))})) is not None:
            all_dates = user.get("no_allocation_date")
            if counselor_leave.get("dates") is not None:
                all_dates.extend(counselor_leave.get("dates"))
                all_dates = list(set(all_dates))
            remove_date = counselor_leave.get("remove_dates")
            if remove_date is None:
                remove_date = []
            elif len(remove_date) > 0:
                for leave_date in remove_date:
                    if leave_date in all_dates:
                        all_dates.remove(leave_date)
            await DatabaseConfiguration().counselor_management.update_one(
                {"_id": ObjectId(str(user.get("_id")))}, {
                    "$set": {"no_allocation_date": all_dates,
                             "last_update": datetime.now(timezone.utc)}})
        else:
            await DatabaseConfiguration().counselor_management.insert_one(
                {"counselor_id": ObjectId(counselor_leave.get("counselor_id")),
                 "counselor_name": utility_obj.name_can(counselor),
                 "no_allocation_date": counselor_leave.get("dates"),
                 "last_update": datetime.now(timezone.utc)})
        return True, str(counselor.get("_id")), counselor

    async def change_counselor_behave(self, counselor_id, status, college_id):
        from app.dependencies.oauth import cache_invalidation
        try:
            counselor = await DatabaseConfiguration().user_collection.find_one(
                {"_id": ObjectId(counselor_id),
                 "role.role_name": "college_counselor"})
        except:
            raise HTTPException(status_code=404, detail="counselor not found")
        if not counselor:
            raise HTTPException(status_code=404, detail="counselor not found")
        update = await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(counselor_id),
             "associated_colleges": {"$in": college_id}},
            {"$set": {"is_activated": status}}, )
        await cache_invalidation(api_updated="updated_user", user_id=counselor.get("email"))
        if update:
            return True, counselor

    async def add_emails_to_list(self, result):
        """
        Store student email ids in the list
        :param result: description="Result which we get after perform aggregation on the collection named studentApplicationForms"
        """
        student_email_ids = []
        async for data in result:
            if (data.get("student_primary", {}).get("basic_details", {}).get(
                    "email") not in student_email_ids):
                student_email_ids.append(
                    data.get("student_primary", {}).get("basic_details",
                                                        {}).get("email"))
        return student_email_ids

    async def get_email_ids(self, payload, date_range, publisher=False,
                            user=None, form_initiated=True):
        """
        Get the email ids
        """
        result = await Application().get_aggregation_result(date_range,
                                                            payload,
                                                            publisher=publisher,
                                                            user=user,
                                                            form_initiated=form_initiated, )
        student_email_ids = await self.add_emails_to_list(result=result)
        return student_email_ids

    def college_counselors_serialize(self, item):
        """
        Get the details of college counselor
        """
        return {"id": str(item.get("_id")),
                "counselor_name": utility_obj.name_can(item),
                "email": item.get("user_name"),
                "allocate_courses": item.get("course_assign"),
                "allocate_state": item.get("state_assign"),
                "allocate_source": item.get("source_assign"),
                "allocate_state_name": item.get("state_name"),
                "head_counselor_name": item.get("head_counselor_name"),
                "head_counselor_id": (
                    str(item.get("head_counselor_id")) if item.get(
                        "head_counselor_id") else None),
                "head_counselor_email_id": item.get("head_counselor_email_id"),
                "allocated_specialization": item.get("specialization_name",
                                                     []),
                "status": "Active" if item.get("is_activated",
                                               False) else "Inactive",
                "language": item.get("language", []),
                "fresh_lead_limit": item.get("fresh_lead_limit"), }

    async def get_calendar_info(self, date, month, year, users):
        """
         Get calendar-wise followup count data which useful in
            counselor dashboard.

         Params:
          date (int): Date which useful for get extra information like paid
            application and form initiated count.
          month (int): Month which useful for get particular month data.
          year (int): Year which useful for get data based on year.

        Returns:
            list: A list which contains particular month follow-up count
                information based on date, month and year.
        """
        result = []
        num_days_in_month = calendar.monthrange(year, month)[1]
        for day in range(1, num_days_in_month + 1):
            sub_result = {}
            start_date, end_date = await utility_obj.date_change_format(
                f"{year}-{month}-{day}", f"{year}-{month}-{day}")
            if date == day:
                application = {"payment_info.status": "captured",
                               "payment_info.created_at": {"$gte": start_date,
                                                           "$lte": end_date},
                               "allocate_to_counselor.counselor_id": {
                                   "$in": users}, }
                paid_application = await DatabaseConfiguration().studentApplicationForms.count_documents(
                    application)
                application = {
                    "allocate_to_counselor.counselor_id": {"$in": users},
                    "allocate_to_counselor.last_update": {"$gte": start_date,
                                                          "$lte": end_date, }, }
                leads_assigned = await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
                    application)
                sub_result.update({"paidApplications": paid_application,
                                   "admissionConfirmed": "N/A",
                                   "leadAssigned": leads_assigned, })
            follow_up = {"lead_stage": "Follow-up", "followup": {"$all": [{
                "$elemMatch": {"status": "Completed",
                               "assigned_counselor_id": {"$in": users},
                               "followup_date": {"$gte": start_date,
                                                 "$lte": end_date}, }}]}, }

            completed_followup = (
                await DatabaseConfiguration().leadsFollowUp.count_documents(
                    follow_up))
            follow_up.get("followup").get("$all")[0].get("$elemMatch").pop(
                "status")
            total_followup = (
                await DatabaseConfiguration().leadsFollowUp.count_documents(
                    follow_up))
            sub_result.update({"date": day, "month": month,
                               "totalFollowUpCount": total_followup,
                               "followUpCount": completed_followup, })
            result.append(sub_result)
        return result

    async def get_key_indicators_for_counselor(self, counselor_ids: list,
                                               change_indicator,
                                               lcr_type: str | None) -> dict:
        """
        Get key indicator section information by counselor id (s).

        Params:
          - counselor_id(list): unique counselor id (str if counselor, list if head counselor)
          - lcr_type (str): Type of lead stage. Possible values are
            "Interested", "Not Interested", "Not picked",
            "Number Switched Off", "Not Reachable".
          - change_indicator (ChangeIndicator): An object of class
                `ChangeIndicator` which useful for show percentage comparison.
                Default showing "last_7_days" comparison of data.
                Possible values: last_7_days, last_15_days and last_30_days.

        Returns:
            - dict: A dictionary which contains key indicator section
                information by counselor ids.
        """
        result = {}
        current_date_ = date.today()
        current_date = str(current_date_)
        start_date, end_date = await utility_obj.date_change_format(
            current_date, current_date)
        cursor = DatabaseConfiguration().studentsPrimaryDetails.aggregate([{
            "$match": {
                "allocate_to_counselor.counselor_id": {
                    "$in": counselor_ids}}}])
        student_ids = [doc["_id"] async for doc in cursor]
        cursor = DatabaseConfiguration().studentApplicationForms.aggregate(
            [{"$match": {"student_id": {"$in": student_ids}}}])
        app_ids = [doc["_id"] async for doc in cursor]
        follow_up = {"application_id": {"$in": app_ids}, "followup": {
            "$all": [{"$elemMatch": {"followup_date": {"$gte": end_date}}}]}, }
        upcoming_followup_count = (
            await DatabaseConfiguration().leadsFollowUp.count_documents(
                follow_up))
        follow_up.pop("followup")
        follow_up.update({"lead_stage": {"$in": ["Fresh Lead", None]}})
        fresh_lead_count = await DatabaseConfiguration().leadsFollowUp.count_documents(
            follow_up)
        follow_up.update({"lead_stage": "Interested"})
        interested_lead_count = (
            await DatabaseConfiguration().leadsFollowUp.count_documents(
                follow_up))
        student_queries = await DatabaseConfiguration().queries.count_documents(
            {"student_id": {"$in": student_ids},
             "status": {"$in": ["TO DO", "IN PROGRESS"]}, })
        pipeline = [{"$match": {"$and": [{
            "$or": [{"call_from": {"$in": counselor_ids}},
                    {"call_to": {"$in": counselor_ids}}, ]}]}}, {
            "$group": {"_id": None,
                       "total_duration": {"$sum": "$call_duration"},
                       "days_included": {"$addToSet": {
                           "$dateToString": {"format": "%Y-%m-%d",
                                             "date": "$created_at", }}}, }}, ]
        talk_time_doc = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)
        talk_time = await talk_time_doc.to_list(None)
        if talk_time:
            total_duration = talk_time[0]["total_duration"]
            days_included = len(talk_time[0]["days_included"])
            total_duration_day = (round(total_duration / days_included,
                                        0) if days_included != 0 else 0)
        else:
            total_duration_day = 0
            days_included = 0
        pipeline.pop(1)
        pipeline[0].get("$match").get("$and").append(
            {"call_duration": {"$gt": 0}})
        connected_doc = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)
        connected_call = len(await connected_doc.to_list(None))
        pipeline[0].get("$match").get("$and")[1].update(
            {"call_duration": {"$gte": 0}})
        all_call_doc = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)
        all_call = len(await all_call_doc.to_list(None))
        percent_connected_call = (round((connected_call / all_call) * 100,
                                        2) if all_call != 0 else 0)
        pipeline = [{"$match": {"$or": [{"call_from": {"$in": counselor_ids}},
                                        {"call_to": {
                                            "$in": counselor_ids}}, ]}},
                    {"$project": {"_id": 0,
                                  "selected_id": {"$cond": {
                                      "if": {"$eq": ["$type", "Outbound"]},
                                      "then": "$call_to",
                                      "else": "$call_from", }}, }}, {
                        "$lookup": {"from": "studentsPrimaryDetails",
                                    "localField": "selected_id",
                                    "foreignField": "basic_details.mobile_number",
                                    "as": "student_data", }},
                    {"$unwind": {"path": "$student_data"}},
                    {"$project": {"_id": 0,
                                  "student_id": "$student_data._id"}}, {
                        "$lookup": {"from": "leadsFollowUp",
                                    "localField": "student_id",
                                    "foreignField": "student_id",
                                    "as": "leads_data", }},
                    {"$unwind": {"path": "$leads_data"}},
                    {"$match": {"leads_data.lead_stage": lcr_type}},
                    {"$group": {"_id": None, "count": {"$sum": 1}}}, ]
        lcr_count_doc = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)
        lcr_count = await lcr_count_doc.to_list(None)
        total_students_lead_stage = (
            await DatabaseConfiguration().leadsFollowUp.count_documents(
                {"student_id": {"$in": student_ids}, "lead_stage": lcr_type}))
        lcr_count = ((lcr_count[0].get("count",
                                       0)) / total_students_lead_stage if lcr_count and total_students_lead_stage else 0)
        result.update({"upcoming_follow_up": upcoming_followup_count,
                       "fresh_lead": fresh_lead_count,
                       "student_queries": student_queries,
                       "avg_talk_time_day": total_duration_day,
                       "connected_calls": (
                           round(connected_call / days_included,
                                 2) if days_included != 0 else 0),
                       "interested_lead": (
                           round((interested_lead_count / len(app_ids)) * 100,
                                 2) if len(
                               app_ids) != 0 else 0),
                       "percentage_connected_call": percent_connected_call,
                       "lcr_count": round(lcr_count, 2), })
        if change_indicator:
            result = await self.get_key_indicators_based_on_change_indicator(
                change_indicator, result, counselor_ids, lcr_type, app_ids,
                total_students_lead_stage, )
        return result

    async def get_key_indicators_based_on_change_indicator(self,
                                                           change_indicator,
                                                           result,
                                                           counselor_ids,
                                                           lcr_type, app_ids,
                                                           total_students_lead_stage, ):
        """
        returns change indicator results for key indicator
        Params:
          change_indicator:
          result (dict): the result dict which is to be updated
          counselor(id): unique counselor id
          lcr_type (str): filter used .
              This may have values("Interested","Not Interested","Not picked","Number Switched Off","Not Reachable")
          app_ids (list): application ids whose counselor is given counselor_id
          head_counselor (bool) : True if head counselor False if counselor
          total_students_lead_stage (list): list of students who has given lead stage
        """
        number = int(change_indicator.split("_")[1])
        start_date, middle_date, previous_date = (
            await utility_obj.get_start_date_and_end_date_by_change_indicator(
                change_indicator))
        previous_start_date, previous_end_date = await utility_obj.date_change_format(
            str(start_date), str(middle_date))
        current_start_date, current_end_date = await utility_obj.date_change_format(
            str(previous_date), str(date.today()))
        pipeline = [{"$project": {"call_from": 1, "call_to": 1, "type": 1,
                                  "call_started_at": {
                                      "$dateFromString": {
                                          "dateString": "$call_started_at",
                                          "timezone": "Asia/Kolkata", }}, }},
                    {"$match": {"$and": [{
                        "$or": [{"call_from": {"$in": counselor_ids}},
                                {"call_to": {"$in": counselor_ids}}, ],
                        "call_started_at": {"$gte": previous_start_date,
                                            "$lte": previous_end_date, }, }]}},
                    {"$project": {"_id": 0,
                                  "selected_id": {"$cond": {
                                      "if": {"$eq": ["$type", "Outbound"]},
                                      "then": "$call_to",
                                      "else": "$call_from", }}, }}, {
                        "$lookup": {"from": "studentsPrimaryDetails",
                                    "localField": "selected_id",
                                    "foreignField": "basic_details.mobile_number",
                                    "as": "student_data", }},
                    {"$unwind": {"path": "$student_data"}},
                    {"$project": {"_id": 0,
                                  "student_id": "$student_data._id"}}, {
                        "$lookup": {"from": "leadsFollowUp",
                                    "localField": "student_id",
                                    "foreignField": "student_id",
                                    "as": "leads_data", }},
                    {"$unwind": {"path": "$leads_data"}},
                    {"$match": {"leads_data.lead_stage": lcr_type}},
                    {"$group": {"_id": None, "count": {"$sum": 1}}}, ]
        lcr_count_doc = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)
        lcr_count = await lcr_count_doc.to_list(None)
        previous_lcr_count = ((lcr_count[0].get("count",
                                                0)) / total_students_lead_stage if lcr_count and total_students_lead_stage else 0)
        pipeline[1].get("$match").get("$and")[0].get("call_started_at").update(
            {"$gte": current_start_date, "$lte": current_end_date})
        lcr_count_doc = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)
        lcr_count = await lcr_count_doc.to_list(None)
        current_lcr_count = ((lcr_count[0].get("count",
                                               0)) / total_students_lead_stage if lcr_count and total_students_lead_stage else 0)
        lcr = await utility_obj.get_percentage_difference_with_position(
            previous_lcr_count, current_lcr_count)
        pipeline = [{
            "$project": {"call_from": 1, "call_to": 1, "call_duration": 1,
                         "call_started_at": {
                             "$dateFromString": {
                                 "dateString": "$call_started_at",
                                 "timezone": "Asia/Kolkata", }}, }},
            {"$match": {
                "$and": [{"$or": [{"call_from": {"$in": counselor_ids}},
                                  {"call_to": {"$in": counselor_ids}}, ]}, {
                             "call_started_at": {"$gte": previous_start_date,
                                                 "$lte": previous_end_date, }}, ]}},
            {
                "$group": {"_id": None,
                           "total_duration": {"$sum": "$call_duration"}}}, ]
        talk_time_doc = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)
        talk_time = await talk_time_doc.to_list(None)
        previous_total_duration_day = ((talk_time[0].get("total_duration",
                                                         0)) / number if talk_time else 0)
        pipeline[1].get("$match").get("$and")[1].get("call_started_at").update(
            {"$gte": current_start_date, "$lte": current_end_date})
        talk_time_doc = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)
        talk_time = await talk_time_doc.to_list(None)
        current_total_duration_day = ((talk_time[0].get("total_duration",
                                                        0)) / number if talk_time else 0)
        total_duration = await utility_obj.get_percentage_difference_with_position(
            previous_total_duration_day, current_total_duration_day)
        pipeline.pop(2)
        pipeline[1].get("$match").get("$and").append(
            {"call_duration": {"$gt": 0}})
        connected_doc = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)
        current_connected_call = len(await connected_doc.to_list(None))
        pipeline[1].get("$match").get("$and")[1].get("call_started_at").update(
            {"$gte": previous_start_date, "$lte": previous_end_date})
        connected_doc = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)
        previous_connected_call = len(await connected_doc.to_list(None))
        connected_call_doc = await utility_obj.get_percentage_difference_with_position(
            previous_connected_call, current_connected_call)
        pipeline[1].get("$match").get("$and")[2].update(
            {"call_duration": {"$gte": 0}})
        all_call_doc = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)
        all_call = len(await all_call_doc.to_list(None))
        previous_percent_connected_call = (
            (previous_connected_call / all_call) * 100 if all_call != 0 else 0)
        pipeline[1].get("$match").get("$and")[1].get("call_started_at").update(
            {"$gte": current_start_date, "$lte": current_end_date})
        all_call_doc = DatabaseConfiguration().call_activity_collection.aggregate(
            pipeline)
        all_call = len(await all_call_doc.to_list(None))
        current_percent_connected_call = (
            (current_connected_call / all_call) * 100 if all_call != 0 else 0)
        percent_connected_call = (
            await utility_obj.get_percentage_difference_with_position(
                previous_percent_connected_call,
                current_percent_connected_call))
        follow_up = {"application_id": {"$in": app_ids},
                     "lead_stage": "Interested",
                     "followup": {"$all": [{"$elemMatch": {
                         "followup_date": {"$gte": previous_start_date,
                                           "$lte": previous_end_date, }}}]}, }
        previous_interested_lead_count = (
            await DatabaseConfiguration().leadsFollowUp.count_documents(
                follow_up))
        follow_up.get("followup").get("$all")[0].get("$elemMatch").get(
            "followup_date").update(
            {"$gte": current_start_date, "$lte": current_end_date})
        current_interested_lead_count = (
            await DatabaseConfiguration().leadsFollowUp.count_documents(
                follow_up))
        interested_lead_count = (
            await utility_obj.get_percentage_difference_with_position(
                previous_interested_lead_count, current_interested_lead_count))
        result.update({"lcr_perc": lcr.get("percentage"),
                       "lcr_position": lcr.get("position"),
                       "avg_talk_time_perc": total_duration.get("percentage"),
                       "avg_talk_time_position": total_duration.get(
                           "position"),
                       "connected_call_perc": connected_call_doc.get(
                           "percentage"),
                       "connected_call_position": connected_call_doc.get(
                           "position"),
                       "percent_connected_perc": percent_connected_call.get(
                           "percentage"),
                       "percent_connected_position": percent_connected_call.get(
                           "position"),
                       "interested_lead_perc": interested_lead_count.get(
                           "percentage"),
                       "interested_lead_position": interested_lead_count.get(
                           "position"), })
        return result

    async def get_quick_view_for_counselor(self, college_id, counselor_id,
                                           change_indicator, date_range):
        """
        Get the counselor quick view summary information.
        Params:
           college_id (str): unique college id
           counselor_id (str): unique counselor id
           change_indicator (str): Filter  used , This can I values last_7_day/last_15_days/last_30_days
           date_range: Date range filter
        Returns:
           result (dict): Contains all quick view required values
        """
        lead_filter = {
            "allocate_to_counselor.counselor_id": {"$in": counselor_id}}
        application_filter = {"college_id": ObjectId(college_id),
                              "current_stage": {"$gte": 2},
                              "allocate_to_counselor.counselor_id": {
                                  "$in": counselor_id}, }
        student_ids = await DatabaseConfiguration().studentsPrimaryDetails.distinct(
            "_id",
            {"allocate_to_counselor.counselor_id": {"$in": counselor_id}})
        if len(date_range) >= 2:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date"))
            application_filter.update(
                {"enquiry_date": {"$gte": start_date, "$lte": end_date}})
            lead_filter.update(
                {"created_at": {"$gte": start_date, "$lte": end_date}})
            student_ids = await DatabaseConfiguration().studentsPrimaryDetails.distinct(
                "_id",
                {"allocate_to_counselor.counselor_id": {"$in": counselor_id},
                 "created_at": {"$gte": start_date, "$lte": end_date}, }, )
        lead_assigned = (
            await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
                lead_filter))
        form_initiated = (
            await DatabaseConfiguration().studentApplicationForms.count_documents(
                application_filter))
        lead_filter.update({"is_verify": True})
        verify_leads = (
            await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
                lead_filter))
        application_filter.update({"payment_info.status": "captured"})
        if date_range:
            application_filter.pop("enquiry_date")
            application_filter.update({
                "payment_info.created_at": {"$gte": start_date,
                                            "$lte": end_date}})
        paid_application = (
            await DatabaseConfiguration().studentApplicationForms.count_documents(
                application_filter))
        followup_filter = {"lead_stage": {"$in": ["Fresh Lead", None]},
                           "student_id": {"$in": student_ids}, }
        fresh_lead_count = await DatabaseConfiguration().leadsFollowUp.count_documents(
            followup_filter)
        followup_filter.update({"lead_stage": "Interested"})
        interested_lead_count = (
            await DatabaseConfiguration().leadsFollowUp.count_documents(
                followup_filter))
        followup_filter.pop("student_id")
        followup_filter.update({"lead_stage": "Follow-up", "followup": {
            "$all": [{"$elemMatch": {
                "assigned_counselor_id": {"$in": counselor_id}}}]}, })
        if date_range:
            followup_filter.get("followup", {}).get("$all", [{}])[0].get(
                "$elemMatch", {}).update(
                {"followup_date": {"$gte": start_date, "$lte": end_date}})

        follow_up_lead_count = (
            await DatabaseConfiguration().leadsFollowUp.count_documents(
                followup_filter))
        result = {"lead_assigned": lead_assigned,
                  "fresh_leads": fresh_lead_count,
                  "followup_leads": follow_up_lead_count,
                  "interested_leads": interested_lead_count,
                  "verified_leads": verify_leads,
                  "form_initiated": form_initiated,
                  "live_applicants": "N/A",
                  "total_applicants": paid_application, }
        if change_indicator:
            result = await self.get_quick_view_change_indicator(
                college_id=college_id, counselor_id=counselor_id,
                result=result, change_indicator=change_indicator, )
        return result

    async def get_quick_view_change_indicator(self, college_id, counselor_id,
                                              result, change_indicator):
        """
        returns change indicator values
        Params:
          counselor id (str/list): unique counselor id
          result (dict): the result dict that is to be updated
          change_indicator
          head_counselor(bool) : True if the user is head counselor, false if the user is counselor
        """
        start_date, middle_date, previous_date = (
            await utility_obj.get_start_date_and_end_date_by_change_indicator(
                change_indicator))
        previous_start_date, previous_end_date = await utility_obj.date_change_format(
            str(start_date), str(middle_date))
        current_start_date, current_end_date = await utility_obj.date_change_format(
            str(previous_date), str(date.today()))

        lead_filter = {
            "allocate_to_counselor.counselor_id": {"$in": counselor_id},
            "created_at": {"$gte": previous_start_date,
                           "$lte": previous_end_date}, }
        application_filter = {"college_id": ObjectId(college_id),
                              "allocate_to_counselor.counselor_id": {
                                  "$in": counselor_id},
                              "current_stage": {"$gte": 2},
                              "enquiry_date": {"$gte": previous_start_date,
                                               "$lte": previous_end_date}, }
        previous_leads = (
            await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
                lead_filter))
        lead_filter.update({"is_verify": True})
        previous_verify_leads = (
            await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
                lead_filter))
        previous_form_initiated = (
            await DatabaseConfiguration().studentApplicationForms.count_documents(
                application_filter))
        application_filter.pop("enquiry_date")
        application_filter.update({"payment_info.status": "captured",
                                   "payment_info.created_at": {
                                       "$gte": previous_start_date,
                                       "$lte": previous_end_date, }, })
        previous_paid_application = (
            await DatabaseConfiguration().studentApplicationForms.count_documents(
                application_filter))
        lead_filter["created_at"] = {"$gte": current_start_date,
                                     "$lte": current_end_date, }
        application_filter["enquiry_date"] = {"$gte": current_start_date,
                                              "$lte": current_end_date, }
        application_filter.pop("payment_info.status")
        application_filter.pop("payment_info.created_at")
        current_leads = (
            await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
                lead_filter))
        current_verify_leads = (
            await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
                lead_filter))
        current_form_initiated = (
            await DatabaseConfiguration().studentApplicationForms.count_documents(
                application_filter))
        application_filter.pop("enquiry_date")
        application_filter.update({"payment_info.status": "captured",
                                   "payment_info.created_at": {
                                       "$gte": current_start_date,
                                       "$lte": current_end_date, }, })
        current_paid_application = (
            await DatabaseConfiguration().studentApplicationForms.count_documents(
                application_filter))
        verify_leads = await utility_obj.get_percentage_difference_with_position(
            previous_verify_leads, current_verify_leads)
        form_initiated = await utility_obj.get_percentage_difference_with_position(
            previous_form_initiated, current_form_initiated)
        paid_applications = await utility_obj.get_percentage_difference_with_position(
            previous_paid_application, current_paid_application)
        lead_assigned = await utility_obj.get_percentage_difference_with_position(
            previous_leads, current_leads)
        result.update({"lead_assigned_perc": lead_assigned.get("percentage"),
                       "lead_assigned_pos": lead_assigned.get("position"),
                       "verified_leads_perc": verify_leads.get("percentage"),
                       "verified_leads_pos": verify_leads.get("position"),
                       "form_initiated_perc": form_initiated.get("percentage"),
                       "form_initiated_pos": form_initiated.get("position"),
                       "total_applicants_perc": paid_applications.get(
                           "percentage"),
                       "total_applicants_pos": paid_applications.get(
                           "position"), })
        return result

    async def get_followup_info_by_change_indicator(self,
                                                    change_indicator: ChangeIndicator | str | None,
                                                    current_date: str,
                                                    data: dict,
                                                    counselor_ids: list, ) -> dict:
        """
        Get total followup difference based on change indicator.

        Params:
            change_indicator (ChangeIndicator | str | None): Useful for get
                comparison total followup count call related data.
            current_date (str): Current date in a string format like
                "YYYY-MM-DD".

        Returns:
            dict: A dictionary which contains total followup difference based
                on change indicator.
        """
        start_date, middle_date, previous_date = (
            await utility_obj.get_start_date_and_end_date_by_change_indicator(
                change_indicator))
        previous_start_date, previous_end_date = await utility_obj.date_change_format(
            str(start_date), str(middle_date))
        pipeline = [{"$unwind": {"path": "$followup"}}, {"$match": {
            "$or": [{"lead_stage": "Follow-up"},
                    {"followup.status": "Completed"}, ],
            "followup.assigned_counselor_id": {"$in": counselor_ids}, }},
                    {"$count": "total"}, ]
        pipeline[1].get("$match", {}).update({
            "followup.followup_date": {"$gte": previous_start_date,
                                       "$lte": previous_end_date, }})
        prev_total_followup = (
            await DatabaseConfiguration().leadsFollowUp.aggregate(
                pipeline).to_list(None))
        prev_total_followup = (prev_total_followup[0].get("total",
                                                          0) if prev_total_followup else 0)
        current_start_date, current_end_date = await utility_obj.date_change_format(
            str(previous_date), current_date)
        pipeline[1].get("$match", {}).update({
            "followup.followup_date": {"$gte": current_start_date,
                                       "$lte": current_end_date, }})
        current_total_followup = (
            await DatabaseConfiguration().leadsFollowUp.aggregate(
                pipeline).to_list(None))
        current_total_followup = (current_total_followup[0].get("total",
                                                                0) if current_total_followup else 0)
        total_followup_diff = await utility_obj.get_percentage_difference_with_position(
            prev_total_followup, current_total_followup)
        data.update(
            {"total_followups_pos": total_followup_diff.get("position"),
             "total_followups_perc": total_followup_diff.get(
                 "percentage"), })
        return data

    async def get_followup_info_by_counselor_ids(self,
                                                 counselor_ids: list[ObjectId],
                                                 start_date: datetime | None,
                                                 end_date: datetime | None,
                                                 change_indicator: ChangeIndicator | str | None, ) -> dict:
        """
        Get follow-up related summary information based on counselor ids.

        Params:
            counselor_ids (list[ObjectId]): A list which contains counselor
                ids. e.g., [ObjectId("123456789012345678901234")]
            start_date (datetime | None): Either none or start date which
                useful for filter data.
            end_date (datetime | None): Either none or end date which
                useful for filter data.
            change_indicator (ChangeIndicator | str | None): Useful for get
                comparison total followup count call related data.

        Returns:
            dict: A dictionary which contains followup details summary
                information.
        """
        current_date = str(date.today())
        today_start, today_end = await utility_obj.date_change_format(
            current_date, current_date)
        pipeline = [{"$unwind": {"path": "$followup"}}, {
            "$match": {"lead_stage": "Follow-up",
                       "followup.status": {"$ne": "Completed"},
                       "followup.assigned_counselor_id": {
                           "$in": counselor_ids},
                       "followup.followup_date": {"$gte": today_start,
                                                  "$lte": today_end}, }},
                    {"$count": "total"}, ]
        today_followup = (
            await DatabaseConfiguration().leadsFollowUp.aggregate(
                pipeline).to_list(None))
        today_followup = today_followup[0].get("total",
                                               0) if today_followup else 0
        pipeline[1].get("$match", {}).update(
            {"followup.followup_date": {"$gte": today_end}})
        upcoming_followup = (
            await DatabaseConfiguration().leadsFollowUp.aggregate(
                pipeline).to_list(None))
        upcoming_followup = (
            upcoming_followup[0].get("total", 0) if upcoming_followup else 0)
        pipeline[1].get("$match", {}).update({"followup.status": "Completed"})
        pipeline[1].get("$match", {}).pop("followup.followup_date")
        pipeline[1].get("$match", {}).pop("lead_stage")
        if start_date and end_date:
            pipeline[1].get("$match", {}).update({
                "followup.followup_date": {"$gte": start_date,
                                           "$lte": end_date}})
        completed_followup = (
            await DatabaseConfiguration().leadsFollowUp.aggregate(
                pipeline).to_list(None))
        completed_followup = completed_followup[0].get("total",
                                               0) if completed_followup else 0
        pipeline[1].get("$match", {}).update(
            {"followup.followup_date": {"$lte": today_start},
             "followup.status": {"$ne": "Completed"}, "lead_stage": "Follow-up"})
        overdue_followup = (
            await DatabaseConfiguration().leadsFollowUp.aggregate(
                pipeline).to_list(None))
        overdue_followup = (
            overdue_followup[0].get("total", 0) if overdue_followup else 0)
        (total_connected_call,
         total_missed_call,) = await CallLog().connected_and_missed_call_count(
            counselor_ids, start_date, end_date)
        data = {
                "total_followups": completed_followup+upcoming_followup+overdue_followup,
                "completed_followups": completed_followup,
                "today_followups": today_followup,
                "upcoming_followups": upcoming_followup,
                "overdue_followups": overdue_followup,
                "missed_calls": total_missed_call,
                "connected_calls": total_connected_call
            }
        if change_indicator:
            data = await self.get_followup_info_by_change_indicator(
                change_indicator, current_date, data, counselor_ids)
        return data

    async def get_followup_details(self, counselor_ids: list[ObjectId],
                                   date_range: dict,
                                   change_indicator: ChangeIndicator | str | None, ) -> dict:
        """
        Get follow-up details summary information based on counselor ids.

        Params:
            counselor_ids (list[ObjectId]): A list which contains counselor
                ids. e.g., [ObjectId("123456789012345678901234")]
            date_range (dict): A dictionary which contains start date and end
                date which useful for filter data according to date range.
                e.g., {"start_date": "2023-10-27", "end_date": "2023-10-27"}
            change_indicator (ChangeIndicator | str | None): Useful for get
                comparison total followup count call related data.

        Returns:
            dict: A dictionary which contains followup details summary
                information.
        """
        start_date, end_date = None, None
        if len(date_range) >= 2:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date"))
        data = await self.get_followup_info_by_counselor_ids(counselor_ids,
                                                             start_date,
                                                             end_date,
                                                             change_indicator)
        return {"data": data, "message": "Get the counselor followup details."}

    async def lead_stage_count_summary(self, source_names: list[str],
                                       date_range: dict, sort_type: str | None,
                                       column_name: str | None,
                                       counselor_id: list,
                                       is_head_counselor: bool, ) -> list:
        """
        Get lead stage count summary information.

        Params:
            source_names (list[str]): Either none or a list which
            contains source names. e.g., ["Organic", "Google"]
            date_range (dict): A dictionary which contains start date and end
                date which useful for filter data according to date range.
                e.g., {"start_date": "2023-10-27", "end_date": "2023-10-27"}
            is_head_counselor (bool): True if requested user is a head counsellor.

        Returns:
            dict: A dictionary which contains lead stage count summary
                information.
        """
        pipeline = [{"$group": {
            "_id": {"lead_stage": {"$ifNull": ["$lead_stage", "Fresh Lead"]},
                    "lead_stage_label": "$lead_stage_label", },
            "total": {"$sum": 1}, }}, {"$project": {"_id": 0,
                                                    "lead_stage": {"$ifNull": [
                                                        "$_id.lead_stage",
                                                        "Fresh Lead"]},
                                                    "lead_stage_label": "$_id.lead_stage_label",
                                                    "total": "$total", }}, ]
        match_stage = []
        if source_names or counselor_id or is_head_counselor:
            student_ids = await Student().get_students_based_on_source(
                source=source_names, season=None, counselor_id=counselor_id,
                is_head_counselor=is_head_counselor, )
            match_stage.append({"student_id": {"$in": student_ids}})
        if len(date_range) >= 2:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date"))
            application_ids = await Application().get_applications_based_on_date_range(
                start_date, end_date)
            match_stage.append({"application_id": {"$in": application_ids}})
        if match_stage:
            pipeline.insert(0, {"$match": {"$and": match_stage}})
        if sort_type and column_name:
            sort_order = 1 if sort_type == "asc" else -1
            pipeline.append({"$sort": {column_name: sort_order}})
        aggregation_result = DatabaseConfiguration().leadsFollowUp.aggregate(
            pipeline)
        data, temp_dict = [], {}
        async for lead_stage_data in aggregation_result:
            lead_stage = lead_stage_data.get("lead_stage")
            total = lead_stage_data.get("total", 0)
            lead_stage_label = lead_stage_data.get("lead_stage_label")
            if lead_stage not in temp_dict:
                temp_dict[lead_stage] = {"lead_stage": lead_stage,
                                         "lead_stage_label": (
                                             [{"name": lead_stage_label,
                                               "total": total}] if lead_stage_label not in [
                                                 None, ""] else []),
                                         "total": total, }
            else:
                exist_lead_stage = temp_dict.get(lead_stage, {})
                exist_lead_stage_label = exist_lead_stage.get(
                    "lead_stage_label", [])
                exist_lead_stage_names = [label.get("name") for label in
                                          exist_lead_stage_label]
                exist_lead_stage_names.extend([None, ""])
                if lead_stage_label not in exist_lead_stage_names:
                    exist_lead_stage_label.append(
                        {"name": lead_stage_label, "total": total})
                exist_lead_stage.update(
                    {"total": total + exist_lead_stage.get("total", 0),
                     "lead_stage_label": exist_lead_stage_label, })
        if temp_dict:
            data = list(temp_dict.values())
        return data

    async def get_pending_followups(self, counselor_ids, date_range=None,
                                    season=None):
        """
        returns the pending followup details of given counselor ids
        Params:
          counselor_ids (list): List of counselor ids
          date_range: Filter to get data of certain time
          season: To get season wise data
        Returns:
            result
        """
        final_result = []
        current_date = str(date.today())
        curr_start_date, curr_end_date = await utility_obj.date_change_format(
            current_date, current_date)
        pipeline = [{"$unwind": {"path": "$followup"}}, {"$match": {
            "followup.assigned_counselor_id": {"$in": counselor_ids}}}, {
                        "$group": {"_id": "$followup.assigned_counselor_id",
                                   "counselor_data": {"$push": {
                                       "todays": {"$cond": [{"$and": [
                                           {"$gte": ["$followup.followup_date",
                                                     curr_start_date, ]},
                                           {"$lt": ["$followup.followup_date",
                                                    curr_end_date, ]}, ]},
                                           1, 0, ]},
                                       "future": {"$cond": [{"$and": [
                                           {"$gte": ["$followup.followup_date",
                                                     curr_end_date, ]}]},
                                           1, 0, ]}, "past": {"$cond": [{
                                           "$and": [{"$eq": ["$lead_stage",
                                                             "Follow-up"]},
                                                    {"$eq": [
                                                        "$followup.status",
                                                        "Incomplete"]}, {
                                                        "$lt": [
                                                            "$followup.followup_date",
                                                            curr_start_date, ]}, ]},
                                           1, 0, ]},
                                       "completed": {"$cond": [
                                           {"$and": [{"$eq": [
                                               "$followup.status",
                                               "Completed"]}]},
                                           1, 0, ]}, }}, }},
                    {"$project": {"_id": "$_id",
                                  "todays": {"$sum": "$counselor_data.todays"},
                                  "future": {"$sum": "$counselor_data.future"},
                                  "past": {"$sum": "$counselor_data.past"},
                                  "completed": {
                                      "$sum": "$counselor_data.completed"}, }}, ]
        if date_range:
            date_range = jsonable_encoder(date_range)
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date"))
            pipeline[2].get("$group", {}).get("student", {}).get("$push",
                                                                 {}).get(
                "completed", {}).get("$cond", [{}])[0].get("$and", []).extend(
                [{"$gte": ["$followup.followup_date", start_date]},
                 {"$lte": ["$followup.followup_date", end_date]}, ])
        result = DatabaseConfiguration(season=season).leadsFollowUp.aggregate(
            pipeline)
        async for doc in result:
            id = doc.get("_id")
            if id:
                if (user := await DatabaseConfiguration(
                        season=season).user_collection.find_one(
                    {"_id": ObjectId(id)})) is None:
                    continue
                data = {"counselor_name": utility_obj.name_can(user),
                        "counselor_mail": user.get("user_name", ""), }
                doc["_id"] = str(doc["_id"])
                data.update(doc)
                final_result.append(data)
        return final_result

    async def get_lead_day_wise_data(self, counselor_id, date, head_counselor):
        """
        returns no. of leads assigned for given counselor and no. of leads called by the counselor
        Params:
           counselor_id (str): unique Id of counselor,
           date(str): in format YYYY-MM-DD
           head_counselor(bool) : true if user is head counselor false if the user is counselor
        Returns:
            hour wise data of leads info
        """
        start_date, end_date = await utility_obj.date_change_format(date, date)
        sort_stage = {"$sort": {"_id": 1}}
        counselor_id = ([ObjectId(id) for id in
                         counselor_id] if head_counselor else ObjectId(
            counselor_id))
        project_stage = {"$project": {"_id": 0, "hour": "$_id", "count": 1}}
        pipeline = [{"$lookup": {"from": "studentsPrimaryDetails",
                                 "localField": "student_id",
                                 "foreignField": "_id",
                                 "as": "student_details", }},
                    {"$unwind": {"path": "$student_details"}}, {"$match": {
                "student_details.allocate_to_counselor.counselor_id": counselor_id,
                "student_details.allocate_to_counselor.last_update": {
                    "$gte": start_date, "$lte": end_date, }, }}, {"$project": {
                "hour": {
                    "$hour": "$student_details.allocate_to_counselor.last_update"},
                "minute": {
                    "$minute": "$student_details.allocate_to_counselor.last_update"},
                "student_numbers": "$student_details.basic_details.mobile_number",
                "count": 1, }}, {"$addFields": {"adjustedHour": {
                "$add": ["$hour",
                         {"$cond": [{"$gte": ["$minute", 30]}, 1, 0]}]}}}, {
                        "$group": {"_id": "$adjustedHour", "date": {
                            "$first": "$student_details.allocate_to_counselor.last_update"},
                                   "count": {"$sum": 1},
                                   "student_numbers": {
                                       "$push": "$student_numbers"}, }},
                    sort_stage,
                    {"$project": {"_id": 0, "hour": "$_id", "count": 1,
                                  "student_numbers": 1}}, ]
        if head_counselor:
            pipeline[2].get("$match")[
                "student_details.allocate_to_counselor.counselor_id"] = {
                "$in": counselor_id}
        result = (await DatabaseConfiguration().leadsFollowUp.aggregate(
            pipeline).to_list(None))
        utc_local_dict = utility_obj.get_local_hour_utc_hour_dict()
        final_result = {}
        student_numbers = []
        for res in result:
            student_numbers.extend(res.get("student_numbers", []))
        for hour in utc_local_dict:
            for res in result:
                if res.get("hour") == utc_local_dict[hour]:
                    final_result[hour] = {"leads_assigned": res.get("count")}
            if hour not in final_result:
                final_result[hour] = {"leads_assigned": 0}
        pipeline = [{"$match": {"call_from": counselor_id,
                                "call_to": {"$in": student_numbers},
                                "created_at": {"$gte": start_date,
                                               "$lte": end_date}, }}, {
                        "$project": {"hour": {"$hour": "$created_at"},
                                     "minute": {"$minute": "$created_at"},
                                     "student_phone": "$call_to",
                                     "count": 1, }}, {"$addFields": {
            "adjustedHour": {"$add": ["$hour", {
                "$cond": [{"$gte": ["$minute", 30]}, 1, 0]}]}}}, {"$group": {
            "_id": {"adjustedHour": "$adjustedHour",
                    "student_phone": "$student_phone", }}},
                    {"$group": {"_id": "$_id.adjustedHour",
                                "count": {"$sum": 1}}},
                    sort_stage, project_stage, ]
        if head_counselor:
            pipeline[0].get("$match")["call_from"] = {"$in": counselor_id}
        result = (
            await DatabaseConfiguration().call_activity_collection.aggregate(
                pipeline).to_list(None))
        for hour in utc_local_dict:
            for res in result:
                if res.get("hour") == utc_local_dict[hour]:
                    final_result[hour].update(
                        {"leads_called": res.get("count")})
            if "leads_called" not in final_result[hour]:
                final_result[hour].update({"leads_called": 0})
        return final_result

    async def get_application_day_wise_data(self, counselor_id, date,
                                            head_counselor):
        """
        returns no. of applications submitted for allocated counselor and no. of applications paid for allocated counselor
        Params:
           counselor_id (str): unique Id of counselor,
           date(str): in format YYYY-MM-DD
           head_counselor(bool): if true the user is head counselor else the user is counseloe
        Returns:
            hour wise data of application info
        """
        start_date, end_date = await utility_obj.date_change_format(date, date)
        sort_stage = {"$sort": {"_id": 1}}
        project_stage = {"$project": {"_id": 0, "hour": "$_id", "count": 1}}
        counselor_id = ([ObjectId(id) for id in
                         counselor_id] if head_counselor else ObjectId(
            counselor_id))
        pipeline = [{
            "$match": {"allocate_to_counselor.counselor_id": counselor_id,
                       "payment_info.created_at": {"$gte": start_date,
                                                   "$lte": end_date}, }}, {
            "$project": {"hour": {"$hour": "$payment_info.created_at"},
                         "minute": {"$minute": "$payment_info.created_at"},
                         "count": 1, }}, {"$addFields": {"adjustedHour": {
            "$add": ["$hour", {"$cond": [{"$gte": ["$minute", 30]}, 1, 0]}]}}},
            {"$group": {"_id": "$adjustedHour",
                        "date": {"$first": "$payment_info.created_at"},
                        "count": {"$sum": 1}, }}, sort_stage, project_stage, ]
        if head_counselor:
            pipeline[0].get("$match")["allocate_to_counselor.counselor_id"] = {
                "$in": counselor_id}
        result = (
            await DatabaseConfiguration().studentApplicationForms.aggregate(
                pipeline).to_list(None))
        utc_local_dict = utility_obj.get_local_hour_utc_hour_dict()
        final_result = {}
        for hour in utc_local_dict:
            for res in result:
                if res.get("hour") == utc_local_dict[hour]:
                    final_result[hour] = {
                        "applications_paid": res.get("count")}
            if hour not in final_result:
                final_result[hour] = {"application_paid": 0}
        pipeline = [{
            "$match": {"allocate_to_counselor.counselor_id": counselor_id,
                       "declaration": True,
                       "last_updated_time": {"$gte": start_date,
                                             "$lte": end_date}, }},
            {"$project": {"hour": {"$hour": "$last_updated_time"},
                          "minute": {"$minute": "$last_updated_time"},
                          "count": 1, }}, {
                "$addFields": {"adjustedHour": {"$add": ["$hour", {
                    "$cond": [{"$gte": ["$minute", 30]}, 1, 0]}]}}}, {
                "$group": {"_id": "$adjustedHour",
                           "date": {"$first": "$last_updated_time"},
                           "count": {"$sum": 1}, }}, sort_stage,
            project_stage, ]
        if head_counselor:
            pipeline[0].get("$match")["allocate_to_counselor.counselor_id"] = {
                "$in": counselor_id}
        result = (
            await DatabaseConfiguration().studentApplicationForms.aggregate(
                pipeline).to_list(None))
        for hour in utc_local_dict:
            for res in result:
                if res.get("hour") == utc_local_dict[hour]:
                    final_result[hour].update(
                        {"applications_submitted": res.get("count")})
            if "applications_submitted" not in final_result[hour]:
                final_result[hour].update({"applications_submitted": 0})
        return final_result

    async def get_counselors_list(self, college: dict, head_counselor: str | None) -> dict:
        """
        Returns counselors details
        Params:
            college (dict): Details of college
            head_counselor (str): The unique id of head counselor if user is head counselor else None
        Returns:
            dict: Details of counselor
        """
        pipeline = [
            {
                '$match': {
                    'associated_colleges': {
                        '$in': [
                            ObjectId(college.get("id"))
                        ]
                    },
                    'role.role_name': {
                        '$in': [
                            'college_counselor', 'college_head_counselor'
                        ]
                    },
                    'is_activated': True
                }
            }, {
                '$project': {
                    'full_name': {
                        '$concat': [
                            '$first_name', {
                                '$cond': [
                                    {
                                        '$ne': [
                                            '$middle_name', ''
                                        ]
                                    }, {
                                        '$concat': [
                                            ' ', '$middle_name'
                                        ]
                                    }, ''
                                ]
                            }, ' ', '$last_name'
                        ]
                    },
                    'role_name': '$role.role_name',
                    'head_counselor_id': {"$toString": '$head_counselor_id'},
                    'head_counselor_name': 1,
                    '_id': {"$toString": "$_id"}
                }
            }, {
                '$facet': {
                    'withHeadCounselor': [
                        {
                            '$match': {
                                'head_counselor_id': {
                                    '$ne': None
                                }
                            }
                        }, {
                            '$group': {
                                '_id': '$head_counselor_id',
                                'name': {
                                    '$first': '$head_counselor_name'
                                },
                                'counselors': {
                                    '$push': {
                                        'name': '$full_name',
                                        '_id': '$_id',
                                        'role': '$role_name'
                                    }
                                }
                            }
                        }, {
                            '$project': {
                                '_id': 1,
                                'name': 1,
                                'counselors': 1
                            }
                        }
                    ],
                    'withoutHeadCounselor': [
                        {
                            '$match': {
                                'head_counselor_id': None
                            }
                        }, {
                            '$project': {
                                '_id': 0,
                                'name': '$full_name',
                                '_id': '$_id',
                                'role': '$role_name'
                            }
                        }
                    ]
                }
            }, {
                '$project': {
                    'combined': {
                        '$concatArrays': [
                            '$withHeadCounselor', '$withoutHeadCounselor'
                        ]
                    }
                }
            }, {
                '$unwind': '$combined'
            }, {
                '$replaceRoot': {
                    'newRoot': '$combined'
                }
            }
        ]
        if head_counselor:
            pipeline[0].get("$match").update({"head_counselor_id": ObjectId(head_counselor)})
        results = await DatabaseConfiguration().user_collection.aggregate(pipeline).to_list(None)
        return {
            "data": results,
            "message": "Get counselors list"
        }


