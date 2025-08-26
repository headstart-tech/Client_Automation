"""
This file contain class and functions related to admin dashboard
"""
import datetime
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.helpers.admin_dashboard.admin_board import AdminBoardHelper
from app.helpers.college_configuration import CollegeHelper
from app.helpers.student_curd.student_application_configuration import \
    StudentApplicationHelper
from app.models.serialize import StudentCourse
from app.core.custom_error import DataNotFoundError, CustomError


class AdminDashboardHelper:
    """
    Contain helper functions related to admin dashboard
    """

    async def source_by(self, lst_lead_source):
        """
        Get lead details by source
        """
        total_lead = []
        if (
                check := await DatabaseConfiguration().studentApplicationForms.find_one(
                    {"student_id": ObjectId(lst_lead_source[0]["student_id"])}
                )
        ) is not None:
            a = 0
            if check["declaration"] is True:
                a = 1
        dct = {
            "utm_source": lst_lead_source[0]["primary_source"]["utm_source"],
            "total_utm": 1,
            "paid_utm": a
        }
        total_lead.append(dct)
        for i in range(1, len(lst_lead_source)):
            for j in range(len(total_lead)):
                if (
                        total_lead[j]["utm_source"]
                        == lst_lead_source[i]["primary_source"]["utm_source"]
                ):
                    total_lead[j]["total_utm"] += 1
                    if (
                            check := await DatabaseConfiguration().studentApplicationForms.find_one(
                                {"student_id": ObjectId(
                                    lst_lead_source[i]["student_id"])}
                            )
                    ) is not None:
                        if check["declaration"] is True:
                            total_lead[j]["paid_utm"] += 1
                elif len(total_lead) - 1 == j:
                    if (
                            check := await DatabaseConfiguration().studentApplicationForms.find_one(
                                {"student_id": ObjectId(
                                    lst_lead_source[i]["student_id"])}
                            )
                    ) is not None:
                        a = 0
                        if check["declaration"] is True:
                            a = 1
                    dct = {
                        "utm_source": lst_lead_source[i]["primary_source"][
                            "utm_source"],
                        "total_utm": 1,
                        "paid_utm": a,
                    }
                    total_lead.append(dct)
        return total_lead

    async def application_initiate(self, all_student_id: list):
        """
        Get the count of application status of student by application_id
        """
        total_applications = await DatabaseConfiguration().studentApplicationForms.count_documents(
            {})
        student_application1 = [
            StudentApplicationHelper().student_application_helper(i)
            for i in
            await DatabaseConfiguration().studentApplicationForms.aggregate([]).to_list(
                length=total_applications)
        ]
        student_application1 = [
            i for i in student_application1 if
            str(i.get("student_id")) in all_student_id
        ]
        form_initiated = len(student_application1)
        all_application_payment_done = len(
            ["d" for i in student_application1 if
             i["payment_info"]["status"] == "captured"]
        )
        all_application_payment_initiated = len(
            ["i" for i in student_application1 if
             i.get("payment_initiated") is True]
        )
        all_application_submitted = len(
            ["i" for i in student_application1 if i.get("declaration") is True]
        )
        return {
            "all_application_payment_done": all_application_payment_done,
            "all_application_payment_initiated": all_application_payment_initiated,
            "all_application_submitted": all_application_submitted,
            "form_initiated": form_initiated,
        }

    async def lead_dashboard(
            self, college_id: str, page_num=None, page_size=None,
            route_name=None
    ):
        """
        Get the status of Student's Application based on college_id
        """
        date_range = await utility_obj.last_3_month()
        start_date, end_date = await utility_obj.date_change_format(
            date_range.get("start_date"), date_range.get("end_date")
        )
        count_students = await DatabaseConfiguration().studentsPrimaryDetails.count_documents(
            {})
        lst_all_student = [
            StudentCourse().student_primary(i)
            for i in await DatabaseConfiguration().studentsPrimaryDetails.aggregate(
                [{"$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date},
                    "college_id": ObjectId(college_id),
                }}]
            ).to_list(length=count_students)
        ]
        if page_num and page_size:
            all_students_length = len(lst_all_student)
            student_response = await utility_obj.pagination_in_api(
                page_num, page_size, lst_all_student, all_students_length,
                route_name
            )
            lst_all_student = student_response["data"]
        count_source = await (DatabaseConfiguration().studentsPrimaryDetails
                              .count_documents({}))
        lst_lead_source = [
            StudentCourse().lead_source_serialize(i)
            for i in
            await DatabaseConfiguration().studentsPrimaryDetails.aggregate([]).to_list(
                length=count_source)
        ]
        if page_num and page_size:
            lead_source_length = len(lst_all_student)
            lead_response = await utility_obj.pagination_in_api(
                page_num, page_size, lst_lead_source, lead_source_length,
                route_name
            )
            lst_lead_source = lead_response["data"]
        if len(lst_all_student) == 0:
            raise HTTPException(status_code=404, detail="student not found")
        all_student_id = [str(i.get("id")) for i in lst_all_student]
        lst_lead_source = [
            i for i in lst_lead_source if
            str(i.get("student_id")) in all_student_id
        ]
        frame = await self.application_initiate(all_student_id)
        verify_user = len(
            ["verify" for i in lst_all_student if i.get("is_verify")])
        total_lead_source = len(lst_lead_source)
        total_lead = len(lst_all_student)
        total_unpaid = total_lead - frame.get("all_application_payment_done")
        not_verified = total_lead - verify_user
        payment_not_initiate = frame.get("form_initiated") - frame.get(
            "all_application_payment_initiated"
        )
        direct_lead = total_lead - total_lead_source
        source_paid_application = 0
        if total_lead_source > 0:
            for i in range(total_lead_source):
                if (
                        student_application := await DatabaseConfiguration().studentApplicationForms.find_one(
                            {"student_id": ObjectId(
                                lst_lead_source[i]["student_id"])}
                        )
                ) is None:
                    raise HTTPException(status_code=404,
                                        detail="from not found")
                if student_application["payment_info"]["status"] == "captured":
                    source_paid_application += 1
            dct_source = await self.source_by(lst_lead_source)
        direct_paid_app = (
                frame.get(
                    "all_application_payment_done") - source_paid_application
        )
        if total_lead_source > 0:
            source_wise_lead = sorted(dct_source, key=lambda x: x["total_utm"])
            source_wise_lead.reverse()
            source_wise_lead = source_wise_lead[:3]
        else:
            source_wise_lead = {}
        graph = await AdminBoardHelper().lead_application(college_id, {})
        data = {
            "total_lead": total_lead,
            "verified": verify_user,
            "unverified": not_verified,
            "all_application_payment_done": frame.get(
                "all_application_payment_done"),
            "total_unpaid": total_unpaid,
            "payment_initiated": frame.get(
                "all_application_payment_initiated"),
            "payment_not_initiated": payment_not_initiate,
            "direct_lead": direct_lead,
            "direct_paid": direct_paid_app,
            "source_wise_lead": source_wise_lead,
            "payment_approved": frame.get("all_application_payment_done"),
            "form_initiated": frame.get("form_initiated"),
            "payment_submitted": frame.get("all_application_submitted"),
            "graph": graph,
        }
        if data:
            if page_num and page_size:
                return {
                    "data": data,
                    "total": student_response["total"],
                    "count": page_size,
                    "pagination": student_response["pagination"],
                    "message": "Applications data fetched successfully!",
                }
            return data
        return False

    async def form_wise_aggregation(self,
                                    college_id: str | None,
                                    source: list | None,
                                    school_names: list | None,
                                    counselor_id: list | None,
                                    start_date=None, end_date=None,
                                    season=None, is_head_counselor=False,
                                    preference=None):
        """
        get the form wise count aggregation with filters and date range

        param:
            college_id (str): Get the college id from the college
            source (list): Get the source data in list
            school_names (list): Get the school name type in list
            counselor_id (list): Get the counselor identifier number
            start_date (datetime): Get the start date filter
            end_date (datetime): Get the end date filter
            season (str): Get the season name
            preference (list[str] | None): Either None or a list of preference
                information.

        return:
            A dictionary of dictionary contains counts of the application and
             lead based on program wise
        """
        base_match = {"college_id": ObjectId(college_id)}
        application_stage = {
            "$expr": {
                "$and": [
                    {"$eq": ["$$courseId", "$course_id"]},
                    {"$eq": ["$$courseSpecialization", "$spec_name1"]}
                ]
            }
        }
        if preference:
            preference_filter = \
                await StudentApplicationHelper().filter_by_preference(
                    preference, "$$courseId",
                    "$$courseSpecialization"
                )
            if preference_filter:
                application_stage = preference_filter
        if start_date and end_date:
            application_stage.update({"enquiry_date": {
                "$gte": start_date, "$lte": end_date}})
        if season == "":
            season = None
        if counselor_id or is_head_counselor:
            application_stage.update(
                {"allocate_to_counselor.counselor_id": {
                    "$in": [ObjectId(c_id) for c_id in counselor_id]}}
            )
        if school_names:
            application_stage.update({"school_name": {"$in": school_names}})
        pipeline = [
            {"$match": base_match},
            {
                "$project": {
                    "_id": 1,
                    "course_name": 1,
                    "course_specialization": {
                        "$filter": {
                            "input": "$course_specialization",
                            "as": "spec",
                            "cond": {
                                "$or": [{"$and": [{"$eq": ["$$spec.spec_name",
                                                           None]},
                                                  "$$spec.is_activated"]},
                                        {"$ne": ["$$spec.spec_name", None]}]
                            }
                        }
                    },
                    "college_id": 1
                }
            },
            {
                "$unwind": {
                    "path": "$course_specialization",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "let": {
                        "courseId": "$_id",
                        "courseSpecialization": "$course_specialization"
                                                ".spec_name"
                    },
                    "pipeline": [
                        {
                            "$match": application_stage
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "student_id": 1,
                                "payment_info": 1,
                                "current_stage": 1,
                                "spec_name1": 1,
                                "spec_name2": 1,
                                "spec_name3": 1,
                                "declaration": 1,
                                "payment_initiated": 1,
                                "allocate_to_counselor": 1,
                                "course_id": 1,
                                "preference_info": 1
                            }
                        }
                    ],
                    "as": "student_application",
                },
            },
            {
                "$unwind": {
                    "path": "$student_application"
                }
            },
            {
                "$group": {
                    "_id": {
                        "course_name": "$course_name",
                        "course_id": {"$toString": "$_id"},
                        "spec": "$course_specialization.spec_name"},
                    "students": {
                        "$addToSet": "$student_application.student_id"},
                    "count": {"$sum": {
                        "$cond": [{"$gte": [
                            "$student_application.current_stage", 2]},
                            1, 0]}},
                    "declaration": {
                        "$sum": {
                            "$cond": [{"$ifNull": [
                                "$student_application.declaration", False]}, 1,
                                0]}
                    },
                    "payment_initiated": {
                        "$sum": {
                            "$cond": [{"$ifNull": [
                                "$student_application.payment_initiated",
                                False]}, 1,
                                0]}
                    },
                    "captured": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$student_application."
                                        "payment_info.status",
                                        "captured",
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "course": "$_id.course_name",
                    "course_name": {"$cond": {
                        "if": {
                            "$eq": ["$_id.spec", None]},
                        "then": "$_id.course_name",
                        "else": {"$cond": {
                            "if": {
                                "$in": [{"$toLower": "$_id.course_name"},
                                        ["master", "bachelor"]]},
                            "then": {"$concat": [
                                "$_id.course_name", " of ", "$_id.spec"]},
                            "else": {"$concat": [
                                "$_id.course_name", " in ", "$_id.spec"]},
                        }}}},
                    "course_id": "$_id.course_id",
                    "spec": "$_id.spec",
                    "total_application": "$count",
                    "total_lead": {"$size": {"$ifNull": ["$students", []]}},
                    "application_submitted": "$declaration",
                    "total_paid_application": "$captured",
                    "payment_initiated_count": "$payment_initiated"
                }
            }
        ]
        if source:
            pipeline.insert(5, {
                    "$lookup": {
                        "from": "studentsPrimaryDetails",
                        "let": {
                            "student_id": "$student_application.student_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": ["$_id", "$$student_id"]
                                    },
                                    "source.primary_source.utm_source": {
                                        "$in": source}
                                }
                            },
                            {
                                "$project": {
                                    "_id": 1
                                }
                            }
                        ],
                        "as": "student_primary"
                    }
                })
            pipeline.insert(6, {
                    "$unwind": {
                        "path": "$student_primary"
                    }
                })
        result = DatabaseConfiguration(
            season=season).course_collection.aggregate(pipeline)
        return {data.get("course_name"): data async for data in result}

    async def get_indicators_form_wise(self, college_id,
                                       counselor_id: list | None,
                                       season: str | None,
                                       change_indicator: str | None,
                                       source: list | None,
                                       school_names: list | None,
                                       is_head_counselor: bool | None
                                       = None, preference=None):
        """
        Get the form wise indicator and position

        param:
            college_id (str): Get the college id from the college
            source (list): Get the source data in list
            school_names (list): Get the school name type in list
            counselor_id (list): Get the counselor identifier number
            change_indicator (str): Get the change indicator as string
                default value is last_7_days
            season (str): Get the season name
            preference (list[str] | None): Either None or a list of preference
                information.

        return:
            A dictionary containing the form wise indicator and position
        """
        start_date_indicate, middle_date, previous_date = await (utility_obj
        .get_start_date_and_end_date_by_change_indicator(
            change_indicator))
        previous_start_date, previous_end_date = await (utility_obj
        .date_change_format(
            str(start_date_indicate),
            str(middle_date)))
        current_start_date, current_end_date = await (utility_obj
        .date_change_format(
            str(previous_date),
            str(datetime.date.today())))
        previous_program_details = await self.form_wise_aggregation(
            college_id=college_id, source=source,
            school_names=school_names, counselor_id=counselor_id,
            start_date=previous_start_date, end_date=previous_end_date,
            season=season, is_head_counselor=is_head_counselor,
            preference=preference
        )
        current_program_details = await self.form_wise_aggregation(
            college_id=college_id, source=source,
            school_names=school_names, counselor_id=counselor_id,
            start_date=current_start_date, end_date=current_end_date,
            season=season, is_head_counselor=is_head_counselor,
            preference=preference
        )
        temp_program_details = {}
        for key in previous_program_details.keys() | current_program_details.keys():
            total_lead = total_application = application_submitted = \
                total_paid_application = payment_initiated_count = {}
            if key in current_program_details and key in previous_program_details:
                total_lead = await (
                    utility_obj.get_percentage_difference_with_position(
                        float(previous_program_details.get(
                            key, {}).get("total_lead", 0)),
                        float(current_program_details.get(
                            key, {}).get("total_lead", 0))))
                total_application = await (
                    utility_obj.get_percentage_difference_with_position(
                        float(previous_program_details.get(
                            key, {}).get("total_application", 0)),
                        float(current_program_details.get(
                            key, {}).get("total_application", 0))))
                application_submitted = await (
                    utility_obj.get_percentage_difference_with_position(
                        float(previous_program_details.get(
                            key, {}).get("application_submitted", 0)),
                        float(current_program_details.get(
                            key, {}).get("application_submitted", 0))))
                total_paid_application = await (
                    utility_obj.get_percentage_difference_with_position(
                        float(previous_program_details.get(
                            key, {}).get("total_paid_application", 0)),
                        float(current_program_details.get(
                            key, {}).get("total_paid_application", 0))))
                payment_initiated_count = await (
                    utility_obj.get_percentage_difference_with_position(
                        float(previous_program_details.get(
                            key, {}).get("payment_initiated_count", 0)),
                        float(current_program_details.get(
                            key, {}).get("payment_initiated_count", 0))))
            elif key in previous_program_details:
                total_lead = await (
                    utility_obj.get_percentage_difference_with_position(
                        float(previous_program_details.get(
                            key, {}).get("total_lead", 0)),
                        0))
                total_application = await (
                    utility_obj.get_percentage_difference_with_position(
                        float(previous_program_details.get(
                            key, {}).get("total_application", 0)),
                        0))
                application_submitted = await (
                    utility_obj.get_percentage_difference_with_position(
                        float(previous_program_details.get(
                            key, {}).get("application_submitted", 0)),
                        0))
                total_paid_application = await (
                    utility_obj.get_percentage_difference_with_position(
                        float(previous_program_details.get(
                            key, {}).get("total_paid_application", 0)),
                        0))
                payment_initiated_count = await (
                    utility_obj.get_percentage_difference_with_position(
                        float(previous_program_details.get(
                            key, {}).get("payment_initiated_count", 0)),
                        0))
            elif key in current_program_details:
                total_lead = await (
                    utility_obj.get_percentage_difference_with_position(
                        0,
                        float(current_program_details.get(
                            key, {}).get("total_lead", 0))))
                total_application = await (
                    utility_obj.get_percentage_difference_with_position(
                        0,
                        float(current_program_details.get(
                            key, {}).get("total_application", 0))))
                application_submitted = await (
                    utility_obj.get_percentage_difference_with_position(
                        0,
                        float(current_program_details.get(
                            key, {}).get("application_submitted", 0))))
                total_paid_application = await (
                    utility_obj.get_percentage_difference_with_position(
                        0,
                        float(current_program_details.get(
                            key, {}).get("total_paid_application", 0))))
                payment_initiated_count = await (
                    utility_obj.get_percentage_difference_with_position(
                        0,
                        float(current_program_details.get(
                            key, {}).get("payment_initiated_count", 0))))
            temp_program_details.update({key: {
                "total_indicator_lead_percentage": total_lead.get("percentage",
                                                                  0),
                "total_indicator_lead_position": total_lead.get("position",
                                                                "equal"),
                "application_indicator_percentage": total_application.get(
                    "percentage", 0),
                "application_indicator_position": total_application.get(
                    "position", "equal"),
                "submit_indicator_application_percentage": application_submitted.get(
                    "percentage", 0),
                "submit_indicator_application_position": application_submitted.get(
                    "position", "equal"),
                "paid_indicator_percentage": total_paid_application.get(
                    "percentage", 0),
                "paid_indicator_position": total_paid_application.get(
                    "position", "equal"),
                "payment_initiated_count_percentage": payment_initiated_count.get(
                    "percentage", 0),
                "payment_initiated_count_position": payment_initiated_count.get(
                    "position", "equal")
            }})
        return temp_program_details

    async def form_wise_record(
            self, college_id: str | None,
            date_range: dict | None,
            counselor_id: list | None,
            season: str | None,
            change_indicator: str | None,
            source: list | None,
            school_names: list | None,
            is_head_counselor: bool = False,
            preference=None):
        """
        Get the form wise record count of the specified programs

        param:
            college_id (str): Get the college id from the college
            source (list): Get the source data in list
            school_names (list): Get the school name type in list
            counselor_id (list): Get the counselor identifier number
            date_range (dict): Get the date range for the filter of the program
            change_indicator (str): Get the change indicator as string
                default value is last_7_days
            season (str): Get the season name
            preference (list[str] | None): Either None or a list of preference
                information.

        return:
            A list of dictionary representing the record count of
             the specified programs counts and percentage
        """
        start_date = None
        end_date = None
        date_range = jsonable_encoder(date_range)
        if len(date_range) >= 2:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
        try:
            await DatabaseConfiguration().college_collection.find_one(
                {"_id": ObjectId(college_id)})
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"{e} - college "
                                                        f"not found")
        program_details = await self.form_wise_aggregation(
            college_id=college_id, source=source,
            school_names=school_names, counselor_id=counselor_id,
            start_date=start_date, end_date=end_date, season=season,
            is_head_counselor=is_head_counselor,
            preference=preference
        )
        temp_program_details = {}
        if change_indicator:
            temp_program_details = await self.get_indicators_form_wise(
                college_id=college_id, source=source,
                school_names=school_names, counselor_id=counselor_id,
                change_indicator=change_indicator, season=season,
                is_head_counselor=is_head_counselor,
                preference=preference
            )
        final_program_list = []
        for key in program_details.keys() | temp_program_details.keys():
            temp = {}
            if key in program_details and key in temp_program_details:
                temp = program_details.get(key, {})
                temp.update(temp_program_details.get(key, {}))
            elif key in program_details:
                temp = program_details.get(key, {})
                temp.update({
                    "total_indicator_lead_percentage": 0,
                    "total_indicator_lead_position": "equal",
                    "application_indicator_percentage": 0,
                    "application_indicator_position": "equal",
                    "submit_indicator_application_percentage": 0,
                    "submit_indicator_application_position": "equal",
                    "paid_indicator_percentage": 0,
                    "paid_indicator_position": "equal",
                    "payment_initiated_count_percentage": 0,
                    "payment_initiated_count_position": "equal"
                })
            if temp:
                final_program_list.append(temp)
        return final_program_list

    async def college_data(self, current_user):
        """
        Get the college data on the basis of associated college ids of user
        """
        total_colleges = await DatabaseConfiguration().college_collection.count_documents(
            {})
        data = [
            CollegeHelper().college_serialize(i)
            for i in
            await DatabaseConfiguration().college_collection.aggregate([]).to_list(
                length=total_colleges)
        ]
        if len(data) == 0:
            raise HTTPException(status_code=404, detail="college not found")
        if (user := await DatabaseConfiguration().user_collection.find_one(
                {"user_name": current_user})) is None:
            raise HTTPException(status_code=404, detail="user not found")
        user_college_list = user.get("associated_colleges")
        if len(user_college_list) == 0:
            raise HTTPException(status_code=422,
                                detail="college id not associated")
        col_lst = []
        for i in user_college_list:
            college = [j for j in data if str(i) in j.get("id")]
            if len(college) > 0:
                col_lst.append(college[0])
        return col_lst

    async def create_menu_permission(self, user_type: str, user_menus, user_permission=None, student_menus=None):
        """
        Update the menu permission in role_collection
        """
        role_name = user_type.lower()
        if (
                check := await DatabaseConfiguration().role_collection.find_one(
                    {"role_name": role_name})
        ) is None:
            raise DataNotFoundError(message=f"Role `{role_name}`")
        update_data, data = False, {}
        if student_menus:
            data.update({"student_menus": check.pop("student_menus", {})})
            data.get("student_menus", {}).update(student_menus)
        if user_permission:
            data.update({"permission": check.pop("permission", {})})
            data.get("permission", {}).update(user_permission)
        if user_menus:
            data.update({"menus": check.pop("menus", {})})
            data.get("menus", {}).update(user_menus)
        if data:
            update_data = await DatabaseConfiguration().role_collection.update_one(
                {"_id": ObjectId(check["_id"])}, {"$set": data}
            )
        if update_data:
            return True
        raise CustomError(f"Menu permission not updated for Role `{role_name}`.")

    async def get_users_by_college_id(self, college_id):
        """
        Get the details of user by college_id
        """
        result = DatabaseConfiguration().user_collection.aggregate(
            [
                {"$unwind": {"path": "$associated_colleges"}},
                {
                    "$match": {
                        "$expr": {"$in": [ObjectId(college_id),
                                          ["$associated_colleges"]]}
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "first_name": 1,
                        "middle_name": 1,
                        "last_name": 1,
                        "role": 1,
                    }
                },
            ]
        )
        users = []
        async for user in result:
            users.append(
                {
                    "_id": str(user.get("_id")),
                    "user_name": utility_obj.name_can(user),
                    "role": user.get("role", {}).get("role_name"),
                }
            )
        return users

    async def get_preference_wise_info(
            self, college_id: str, season: str | None,
            system_preference: dict | None, data_for: str,
            program_name: list | None, date_range: dict,
            counselor_id: None | list[ObjectId]) -> tuple:
        """
        Get/download the preference wise data.

        Params:
            - college_id (str): An unique id/identifier of a college.
                e.g., 123456789012345678901234
            - season: An unique id of season useful for get particular season
                data.
            - program_name (list | None): Either None or program
                names which useful for get data based on program (s).
                e.g., [{"course_id": "123456789012345678901234",
                    "spec_name1": "xyx"}]
            - date_range (dict): A daterange which useful for filter data based on
                date_range.
                e.g., {"start_date": "2023-09-07", "end_date": "2023-09-07"}
            - counselor_id (None | list[ObjectId]): Either None or a list of
                counselor ids for get counselor wise preference count information.
                e.g., [ObjectId('123456789012345678901234')]

        Returns:
            tuple: A tuple which contains information like header, data and
                total.
        """
        application_match_cond = {"preference_info": {"$exists": True}}
        if data_for == "Applications":
            application_match_cond.update({"current_stage": {"$gte": 2}})
        if counselor_id:
            application_match_cond.update(
                {"allocate_to_counselor.counselor_id": {
                    "$in": counselor_id}}
            )
        if len(date_range) >= 2:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
            application_match_cond.update({"enquiry_date": {
                "$gte": start_date, "$lte": end_date}})
        if season == "":
            season = None
        if program_name:
            program_name = [
                {"course_id": ObjectId(program_info.get('course_id')),
                 "spec_name1": program_info.get("spec_name1")} for program_info
                in program_name]
            application_match_cond.update({"$or": program_name})

        if system_preference is None:
            system_preference = {}
        preference_count: int = system_preference.get("preference_count", 0)
        preference_data, preference_header = [], []
        for count in range(preference_count):
            if preference_count > 0:
                preference_data.append(f"preference{count + 1}")
                preference_header.append(f"Preference {count + 1}")
        header = ["Course Name"]
        if preference_header:
            header = header + preference_header
        group_stage = {
                    "_id": ""
                }
        if preference_data:
            temp_dict: dict = {item: {
            "$push": {
                "$cond": {
                    "if": {"$ne": [{"$arrayElemAt": [
                        "$preference_info", _id]},
                        None]},
                    "then": {"$arrayElemAt": [
                        "$preference_info", _id]} if data_for == "Applications" else {"spec_name": {"$arrayElemAt": [
                            "$preference_info", _id]}, "student_id": "$student_id"},
                    "else": "$empty",
                }
            }
        } for _id, item in enumerate(preference_data)}
            if temp_dict:
                group_stage.update(temp_dict)

        application_pipeline = [
            {
                "$match": application_match_cond
            },
            {
                "$group": group_stage
            }
        ]

        application_result = DatabaseConfiguration(
            season=season).studentApplicationForms.aggregate(
            application_pipeline)
        final_data, preference_information = [], {}
        async for data in application_result:
            preference_information = data

        course_pipeline = [
            {
                "$match": {
                    "college_id": ObjectId(college_id)
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "course_name": 1,
                    "course_specialization": {
                        "$filter": {"input": "$course_specialization",
                                    "as": "spec",
                                    "cond": {"$or": [{"$and": [
                                        {"$eq": ["$$spec.spec_name", None]},
                                        "$$spec.is_activated"]}, {
                                        "$ne": ["$$spec.spec_name",
                                                None]}]}}}
                }
            },
            {
                "$unwind": {"path": "$course_specialization",
                            "preserveNullAndEmptyArrays": True}
            },
            {
                "$project": {
                    "_id": 0,
                    "course_id": "$_id",
                    "course_name": "$course_name",
                    "spec_name1": "$course_specialization.spec_name"
                }
            }
        ]
        if program_name:
            course_pipeline.append({"$match": {"$or": program_name}})
        course_result = (
                await DatabaseConfiguration(season=season)
                .course_collection.aggregate(course_pipeline)
                .to_list(None)
            )

        count_information = {}
        total = ["Total"]
        for course_info in course_result:
            course_name = course_info.get('course_name')
            specialization_name = course_info.get('spec_name1')
            between_character = 'of' if course_name in ['Master', 'Bachelor'] else 'in'
            temp_data = {
                "course_name": f"{course_name}{f' {between_character} {specialization_name}' if specialization_name else ''}"}
            if data_for == "Leads":
                if preference_information:
                    for key, value in preference_information.items():
                        if key == "_id":
                            continue
                        count = 0
                        for item in value:
                            if "spec_name" not in item:
                                continue
                            if item.get('spec_name') == specialization_name:
                                student_id = item.get("student_id")
                                if key not in count_information:
                                    count_information[key] = [student_id]
                                    count += 1
                                else:
                                    if student_id not in count_information[key]:
                                        count_information[key] = count_information[
                                                                    key] + [
                                                                    student_id]
                                        count += 1
                        if key not in count_information:
                            count_information.update({key: []})
                        temp_data.update({key: count})
                else:
                    for key in preference_data:
                        count_information.update({key: []})
                        temp_data.update({key: 0})
            elif data_for == "Applications":
                pref_temp_dict: dict = {}
                for item in preference_data:
                    preference_count = preference_information.get(
                        item, []).count(course_info.get('spec_name1'))
                    pref_temp_dict.update({item: preference_count})
                    if item in count_information:
                        count_information.update({item: count_information[item] + preference_count})
                    else:
                        count_information[item] = preference_count
                if pref_temp_dict:
                    temp_data.update(pref_temp_dict)
            final_data.append(temp_data)
        total_count = [item_count if data_for == "Applications" else len(item_count) for item_count in count_information.values()]
        if total_count:
            total = total + total_count
        return header, final_data, total
