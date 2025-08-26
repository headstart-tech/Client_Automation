"""
This file contain helper classes and functions related to admin board
"""

import asyncio
import datetime
import json
import re
from dataclasses import dataclass

import arrow
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from pymongo import UpdateOne

from app.core.custom_error import DataNotFoundError
from app.core.utils import utility_obj, settings
from app.database.aggregation.event import Event
from app.database.aggregation.get_all_applications import Application
from app.database.aggregation.student import Student
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import insert_data_in_cache, get_collection_from_cache, store_collection_in_cache


@dataclass
class StateStats:
    state_name: str
    state_code: str
    total_lead: float = 0
    lead_percentage: float = 0
    application_count: float = 0
    application_percentage: float = 0
    admission_count: float = 0
    admission_percentage: float = 0


@dataclass
class SourceStats:
    """
    Set default attributes for source
    """

    source_name: str
    total_utm: float = 0
    paid_utm: float = 0
    submit_utm: float = 0
    total_percentage: float = 0
    paid_application_percentage: float = 0
    submit_application_percentage: float = 0


state_map = {
    "DL": "Delhi",
    "UP": "Uttar Pradesh",
    "RJ": "Rajasthan",
    "ML": "Meghalya",
    "AS": "Assam",
    "AR": "Arunachal Pradesh",
    "TN": "Tamil Nadu",
    "AP": "Andhra Pradesh",
    "JK": "Jammu and Kashmir",
    "HR": "Haryana",
    "MH": "Maharashtra",
    "WB": "West Bengal",
    "KA": "Karnataka",
    "TS": "Telangana",
    "MP": "Madhya Pradesh",
    "GJ": "Gujarat",
    "MZ": "Mizoram",
    "DH": "Dadra and Nagar Haveli and Daman and Diu",
    "JH": "Jharkhand",
    "UT": "Uttarakhand",
    "OD": "Odisha",
    "BR": "Bihar",
    "TR": "Tripura",
    "KL": "Kerala",
    "LD": "Lakshadweep",
    "HP": "Himachal Pradesh",
    "SK": "Sikkim",
    "PB": "Punjab",
    "CH": "Chandigarh",
    "LA": "Ladakh",
    "MN": "Manipur",
    "AN": "Andaman and Nicobar Islands",
    "GA": "Goa",
    "NL": "Nagaland",
    "CT": "Chhattisgarh",
    "PY": "Pondicherry",
    "Other": "Other",
}
today = datetime.date.today()


class AdminBoardHelper:
    """
    Contain helper functions related to admin board
    """

    async def get_state_name(self, state_code):
        """
        returns the name of state on the basis of state_code
        """
        if state_map.get(state_code) is None:
            states = await get_collection_from_cache(collection_name="states")
            if states:
                doc = utility_obj.search_for_document_two_fields(states,
                                                                 field1="state_code",
                                                                 field1_search_name=state_code,
                                                                 field2="country_code",
                                                                 field2_search_name="IN"
                                                                 )
            else:
                doc = await DatabaseConfiguration().state_collection.find_one(
                    {"country_code": "IN", "state_code": state_code}
                )
                collection = await DatabaseConfiguration().state_collection.aggregate([]).to_list(None)
                await store_collection_in_cache(collection, collection_name="states")
            return doc.get("name")
        return state_map[state_code]

    async def get_state_code_from_id(self, state_id):
        """
        For given state_id returns state_code and name
        Params:
        - state_id (str) : The unique id of state
        """
        states = await get_collection_from_cache(collection_name="states")
        if states:
            doc = utility_obj.search_for_document(states, field="_id", search_name=str(state_id))
        else:
            doc = await DatabaseConfiguration().state_collection.find_one(
                {"_id": ObjectId(state_id)})
            collection = await DatabaseConfiguration().state_collection.aggregate([]).to_list(None)
            await store_collection_in_cache(collection, collection_name="states")
        if not doc:
            return "Others", "Others"
        return doc.get("state_code"), doc.get("name")

    async def get_state_details(
            self,
            college_id,
            payload,
            season=None,
            counselor_ids=None,
            is_head_counselor=False,
    ):
        """
        Get the state details
        """
        if payload.get("date_range") is None:
            payload["date_range"] = {}
        start_date = payload.get("date_range", {}).get("start_date")
        end_date = payload.get("date_range", {}).get("end_date")
        mode = payload.get("mode")
        base_match = {"college_id": ObjectId(college_id)}
        filter_field_name = "allocate_to_counselor.last_update" if mode == "Assignment" else "lead_stage_change_at" \
            if mode == "Activity" else "created_at"
        app_filter_field_name = "payment_info.created_at" if filter_field_name == "created_at" else filter_field_name
        if counselor_ids or is_head_counselor:
            base_match.update(
                {"allocate_to_counselor.counselor_id": {"$in": counselor_ids}}
            )
        if start_date is not None and end_date is not None:
            start_date, end_date = await utility_obj.date_change_format(
                start_date, end_date
            )
            base_match.update({filter_field_name: {"$gte": start_date, "$lte": end_date}})
            total_leads_all_states = await DatabaseConfiguration(
                season=season
            ).studentsPrimaryDetails.count_documents(base_match)
            base_match.update(
                {
                    app_filter_field_name: base_match.pop(filter_field_name),
                    "current_stage": {"$gte": 2},
                    "payment_info.status": "captured"
                }
            )
            total_applications_all_states = await DatabaseConfiguration(
                season=season
            ).studentApplicationForms.count_documents(base_match)
            base_match.pop("payment_info.status")
            total_admission_all_states = 0
        else:
            total_leads_all_states = await DatabaseConfiguration(
                season=season
            ).studentsPrimaryDetails.count_documents(base_match)
            base_match.update(
                {"current_stage": {"$gte": 2}, "payment_info.status": "captured"}
            )
            total_applications_all_states = await DatabaseConfiguration(
                season=season
            ).studentApplicationForms.count_documents(base_match)
            base_match.pop("payment_info.status")
            base_match.update({"declaration": True})
            total_admission_all_states = 0
        for item in ["current_stage", "declaration", filter_field_name, app_filter_field_name]:
            if base_match.get(item):
                base_match.pop(item)

        if payload.get("source_name"):
            student_ids = await Student().get_students_based_on_source(
                source=payload.get("source_name", []), season=season
            )
            base_match["_id"] = {"$in": student_ids}
        if start_date is not None and end_date is not None:
            base_match.update(
                {filter_field_name: {"$gte": start_date, "$lte": end_date}})
        pipeline = [
            {"$match": base_match},
            {
                "$group": {
                    "_id": "$address_details.communication_address.state" ".state_id",
                    "students": {"$push": {"student_id": "$_id"}},
                    "lead_count": {"$count": {}},
                    "state_code": {"$first": "$address_details.communication_address.state.state_code"},
                    "state_name": {"$first": "$address_details.communication_address.state.state_name"}
                }
            },
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "localField": "students.student_id",
                    "foreignField": "student_id",
                    "pipeline": [
                        {"$project": {"_id": 1, "payment_info": 1, "admission": 1}}
                    ],
                    "as": "results",
                }
            },
            {
                "$unwind": {
                    "path": "$results",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            {
                "$group": {
                    "_id": {
                        "state_id": "$_id",
                        "state_code": "$state_code",
                        "state_name": "$state_name"
                    },
                    "total_leads": {"$first": "$lead_count"},
                    "payment_info_count": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$results.payment_info.status", "captured"]},
                                1,
                                0,
                            ]
                        }
                    },
                    "admission": {
                        "$sum": {"$cond": [{"$eq": ["$results.admission", True]}, 1, 0]}
                    },
                }
            },
        ]
        if payload.get("course_id") not in ["", None]:
            pipeline.insert(
                4, {"$match": {"results.course_id": ObjectId(payload.get("course_id"))}}
            )
            if payload.get("spec_name") not in ["", None]:
                pipeline[4].get("$match", {}).update(
                    {"results.spec_name1": payload.get("spec_name")}
                )
        result = DatabaseConfiguration(season=season).studentsPrimaryDetails.aggregate(
            pipeline
        )
        state_dict = dict()

        async for doc in result:
            id_node = doc.get("_id")
            state_code, state_name = id_node.get("state_code"), id_node.get("state_name")
            if state_dict.get(state_code) is None:
                stateStats = StateStats(state_name=state_name, state_code=state_code)
            else:
                stateStats = state_dict.get(state_code)
            stateStats.total_lead = doc.get("total_leads", 0)
            stateStats.application_count = doc.get("payment_info_count", 0)
            stateStats.admission_count = doc.get("admission", 0)
            state_dict[state_code] = stateStats

        return (
            state_dict,
            total_leads_all_states,
            total_applications_all_states,
            total_admission_all_states,
        )

    async def get_indicator_data(
            self,
            change_indicator,
            payload,
            college_id,
            season=None,
            counselor_ids=None,
            is_head_counselor=False,
    ):
        """
        Get change indicator data
        """
        start_date, middle_date, previous_date = (
            await utility_obj.get_start_date_and_end_date_by_change_indicator(
                change_indicator
            )
        )
        payload["date_range"] = {
            "start_date": str(start_date),
            "end_date": str(middle_date),
        }
        (
            previous_state_dict,
            previous_total_leads_all_states,
            previous_total_applications_all_states,
            previous_total_admission_all_states,
        ) = await self.get_state_details(
            college_id,
            payload,
            season=season,
            counselor_ids=counselor_ids,
            is_head_counselor=is_head_counselor,
        )
        payload["date_range"] = {
            "start_date": str(previous_date),
            "end_date": str(today),
        }
        (
            current_state_dict,
            current_total_leads_all_states,
            current_total_applications_all_states,
            current_total_admission_all_states,
        ) = await self.get_state_details(
            college_id,
            payload,
            season=season,
            counselor_ids=counselor_ids,
            is_head_counselor=is_head_counselor,
        )
        dct_temp = {}
        for key in previous_state_dict.keys() | current_state_dict.keys():
            lead_percentage = application_percentage = admission_percentage = {}
            if key in previous_state_dict and key in current_state_dict:
                lead_percentage = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            float(previous_state_dict[key].total_lead),
                            float(current_state_dict[key].total_lead),
                        )
                    )
                )
                application_percentage = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            float(previous_state_dict[key].application_count),
                            float(current_state_dict[key].application_count),
                        )
                    )
                )
                admission_percentage = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            float(previous_state_dict[key].admission_count),
                            float(current_state_dict[key].admission_count),
                        )
                    )
                )
            elif key in previous_state_dict:
                lead_percentage = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            float(previous_state_dict[key].total_lead), 0
                        )
                    )
                )
                application_percentage = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            float(previous_state_dict[key].application_count), 0
                        )
                    )
                )
                admission_percentage = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            float(previous_state_dict[key].admission_count), 0
                        )
                    )
                )
            elif key in current_state_dict:
                lead_percentage = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            0, float(current_state_dict[key].total_lead)
                        )
                    )
                )
                application_percentage = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            0, float(current_state_dict[key].application_count)
                        )
                    )
                )
                admission_percentage = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            0, float(current_state_dict[key].admission_count)
                        )
                    )
                )
            dct_temp.update(
                {
                    key: {
                        "lead_percentage_difference": lead_percentage.get("percentage"),
                        "application_percentage_difference": application_percentage.get(
                            "percentage"
                        ),
                        "lead_percentage_position": lead_percentage.get("position"),
                        "application_percentage_position": application_percentage.get(
                            "position"
                        ),
                        "admission_percentage_difference": admission_percentage.get(
                            "percentage"
                        ),
                        "admission_percentage_position": admission_percentage.get(
                            "position"
                        ),
                    }
                }
            )
        return dct_temp

    async def get_admin_graph_data_based_on_change_indicator(
            self,
            college_id,
            change_indicator,
            data,
            route,
            form_stage_wise_segregation,
            lead_funnel,
            application_type=None,
            season=None,
    ):
        """
        Get admin graph data based on change indicator
        """
        application = {"college_id": ObjectId(college_id), "current_stage": {"$gte": 2}}
        start_date, middle_date, previous_date = (
            await utility_obj.get_start_date_and_end_date_by_change_indicator(
                change_indicator
            )
        )
        previous_start_date, previous_end_date = await utility_obj.date_change_format(
            str(start_date), str(middle_date)
        )
        current_start_date, current_end_date = await utility_obj.date_change_format(
            str(previous_date), str(today)
        )
        application.update(
            {"enquiry_date": {"$gte": previous_start_date, "$lte": previous_end_date}}
        )
        previous_applications = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.update({"payment_info.status": "captured"})
        previous_paid_applications = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.pop("enquiry_date")
        application.update(
            {
                "payment_info.created_at": {
                    "$gte": previous_start_date,
                    "$lte": previous_end_date,
                }
            }
        )
        razor_pay_previous_paid_applications = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.update(
            {
                "payment_info.created_at": {
                    "$gte": current_start_date,
                    "$lte": current_end_date,
                }
            }
        )
        razor_pay_current_paid_applications = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.pop("payment_info.created_at")
        application.pop("payment_info.status")
        application.update(
            {
                "payment_initiated": True,
                "enquiry_date": {"gte": previous_start_date, "$lte": previous_end_date},
            }
        )
        previous_payment_initiated_applications = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.pop("payment_initiated")
        application.update({"declaration": True})
        previous_form_submitted = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.pop("declaration")
        previous_unpaid_application = previous_applications - previous_paid_applications
        application.update(
            {"enquiry_date": {"$gte": current_start_date, "$lte": current_end_date}}
        )
        current_applications = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.update({"payment_info.status": "captured"})
        current_paid_applications = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.pop("payment_info.status")
        application.update({"payment_initiated": True})
        current_payment_initiated_applications = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.pop("payment_initiated")
        application.update({"declaration": True})
        current_form_submitted = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.pop("declaration")
        paid_application = await utility_obj.get_percentage_difference_with_position(
            razor_pay_previous_paid_applications, razor_pay_current_paid_applications
        )
        form_initiated = await utility_obj.get_percentage_difference_with_position(
            previous_applications, current_applications
        )

        data.update(
            {
                "form_initiated_percentage": form_initiated.get("percentage"),
                "form_initiated_position": form_initiated.get("position"),
            }
        )
        if route == "score_board":
            data = await self.get_score_board_data_by_change_indicator(
                data,
                college_id,
                previous_start_date,
                previous_end_date,
                current_start_date,
                current_end_date,
                season=season,
            )
            data = (
                await self.get_score_board_application_communication_change_indicator(
                    data,
                    college_id,
                    previous_start_date,
                    previous_end_date,
                    current_start_date,
                    current_end_date,
                    application_type,
                    season=season,
                )
            )
        if route != "score_board":
            count_of_applications = await DatabaseConfiguration(
                season=season
            ).studentApplicationForms.count_documents({})
            form_submitted = await utility_obj.get_percentage_difference_with_position(
                previous_form_submitted, current_form_submitted
            )
            data.update(
                {
                    "paid_application_percentage": paid_application.get("percentage"),
                    "paid_application_position": paid_application.get("position"),
                    "form_submitted_percentage": form_submitted.get("percentage"),
                    "form_submitted_position": form_submitted.get("position"),
                }
            )

        if (
                form_stage_wise_segregation is False and lead_funnel is False
        ) and route != "score_board":
            current_unpaid_application = (
                    current_applications - current_paid_applications
            )
            unpaid_application = (
                await utility_obj.get_percentage_difference_with_position(
                    previous_unpaid_application, current_unpaid_application
                )
            )
            data.update(
                {
                    "unpaid_application_percentage": unpaid_application.get(
                        "percentage"
                    ),
                    "unpaid_application_position": unpaid_application.get("position"),
                }
            )
        if lead_funnel:
            total_initiated = await utility_obj.get_percentage_difference_with_position(
                previous_payment_initiated_applications,
                current_payment_initiated_applications,
            )
            data.update(
                {
                    "total_initiated_percentage": total_initiated.get("percentage"),
                    "total_initiated_position": total_initiated.get("position"),
                }
            )
        return data

    async def get_score_board_data_by_change_indicator(
            self,
            data,
            college_id,
            previous_start_date,
            previous_end_date,
            current_start_date,
            current_end_date,
            season=None,
    ):
        """
        Get score board data by change indicator
        """
        count_of_leads = await DatabaseConfiguration(
            season=season
        ).studentsPrimaryDetails.count_documents({})
        total_lead = {"college_id": ObjectId(college_id)}
        total_lead.update(
            {"created_at": {"$gte": previous_start_date, "$lte": previous_end_date}}
        )
        previous_leads = await DatabaseConfiguration(
            season=season
        ).studentsPrimaryDetails.count_documents(total_lead)
        total_lead.update(
            {"created_at": {"$gte": current_start_date, "$lte": current_end_date}}
        )
        current_leads = await DatabaseConfiguration(
            season=season
        ).studentsPrimaryDetails.count_documents(total_lead)
        leads = await utility_obj.get_percentage_difference_with_position(
            previous_leads, current_leads
        )
        data.update(
            {
                "lead_percentage": leads.get("percentage"),
                "lead_position": leads.get("position"),
            }
        )
        return data

    async def get_whatsapp_count(
            self, communication: list, season: str | None = None , for_score_board_api: bool = None
    ) -> int:
        """
        This function is for counting the number of whatsapp message

        Params:
            communication (list): Base query for counting the sms, It holds the date range in the query
            season (str | None, optional): Season of the database. Defaults to None.
            for_score_board_api (bool, optional): Flag to indicate if the function is called for score board API. Defaults to None.

        Returns:
            int: total count of sms
        """
        if for_score_board_api:
            communication.extend(
                [
                    {
                        "$project": {
                            "send_to_length": {"$size": {
                            '$filter': {
                                'input': {
                                    '$ifNull': [
                                        '$whatsapp_summary.transaction_id', []
                                    ]
                                },
                                'as': 'data',
                                'cond': {"$and": []}
                            }
                        }},
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "total_send_to_length": {"$sum": "$send_to_length"},
                        }
                    },
                ]
            )
        else:
            communication.extend(
                [
                    {
                        "$project": {
                            "_id": 0,
                            "send_to_length": {"$size": {"$ifNull": ["$send_to", []]}},
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "total_send_to_length": {"$sum": "$send_to_length"},
                        }
                    },
                ]
            )

        whatsapp_total = (
            await DatabaseConfiguration(season=season)
            .communication_log_collection.aggregate(communication)
            .to_list(None)
        )
        return whatsapp_total[0].get("total_send_to_length", 0) if whatsapp_total else 0

    async def get_sms_count(
            self, communication: list, season: str | None = None, for_score_board_api : bool = None
    ) -> int:    
        """
        This function is for counting the number of sms

        Args:
            communication (list): Base query for counting the sms, It holds the date range in the query.
            season (str | None): Season of the database. Defaults to None.
            for_score_board_api (bool, optional): Flag to indicate if the function is called for score board API. Defaults to None.

        Returns:
            int: total count of sms
        """
    
        base_pipeline = communication.copy()

        if for_score_board_api:
            pipeline = [
                {
                    '$project': {
                        'submitted_count': {
                            '$size': {
                                '$ifNull': ['$sms_summary.transaction_id', []]
                            }
                        }
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'total_messages': { '$sum': '$submitted_count' }
                    }
                }
            ]
        else:
            pipeline = [
                { '$match': { 'sms_response.submitResponses.state': 'SUBMIT_ACCEPTED' } },
                {
                    '$project': {
                        'submitted_count': {
                            '$size': {
                                '$filter': {
                                    'input': '$sms_response.submitResponses',
                                    'as': 'response',
                                    'cond': { '$eq': ['$$response.state', 'SUBMIT_ACCEPTED'] }
                                }
                            }
                        }
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'total_messages': { '$sum': '$submitted_count' }
                    }
                }
            ]

        base_pipeline.extend(pipeline)

        sms_total = (
            await DatabaseConfiguration(season=season)
            .communication_log_collection.aggregate(base_pipeline)
            .to_list(length=None)
        )
        
        return sms_total[0].get("total_messages", 0) if sms_total else 0

    async def get_score_board_application_communication_change_indicator(
            self,
            data,
            college_id,
            previous_start_date,
            previous_end_date,
            current_start_date,
            current_end_date,
            application_type,
            season=None,
    ):
        """
        Get the score board appliication type and communication change indicator based data.
        Params:
         data(dict) : The existing data which is grabbed for different schemes
         college_id(str): Unique id of college
         previous_start_date(date): In change indicator this is the previous data start date
         previous_end_date(date): In change indicator this is the previous data end date
         current_start_date(date): In change indicator this is the current data start date
         current_end_date(date): In change indicator this is the current data end date
         application_type(str): This is the type of application given in filer. this can have value
                                  paid/submitted/enrolled/interview_done/interview_scheduled/dv_approved
                                  /dv_rejected/offer_letter_sent
        returns:
         data(dict) : updated dict
        """
        application = {"college_id": ObjectId(college_id), "current_stage": {"$gte": 2}}
        communication = []
        if application_type in ["enrolled", "submitted"]:
            application.update({"current_stage": 10})
        elif application_type == "paid":
            application.update({"payment_info.status": "captured"})
        elif application_type in ["dv rejected", "dv approved", "dv accepted"]:
            application.update(
                {"created_at": {"$gte": previous_start_date, "$lte": previous_end_date}}
            )
            previous_count = await self.get_overall_verified_rejected_data(
                application, application_type, season=season
            )
            application.update(
                {"created_at": {"$gte": current_start_date, "$lte": current_end_date}}
            )
            current_count = await self.get_overall_verified_rejected_data(
                application, application_type, season=season
            )
            leads = await utility_obj.get_percentage_difference_with_position(
                previous_count, current_count
            )
            data.update(
                {
                    "application_count_percentage": leads.get("percentage"),
                    "application_count_position": leads.get("position"),
                }
            )
        elif application_type == "interview_scheduled":
            application.update({"interviewStatus.status": "Scheduled"})
        elif application_type == "interview_done":
            application.update({"interviewStatus.status": "Done"})
        elif application_type == "offer_letter_sent":
            application.update({"offer_letter": {"$exists": True}})
        if application_type not in ["dv_approved", "dv_rejected"]:
            application.update(
                {
                    "payment_info.created_at": {
                        "$gte": previous_start_date,
                        "$lte": previous_end_date,
                    }
                }
            )
            previous_application_lead = await DatabaseConfiguration(
                season=season
            ).studentApplicationForms.count_documents(application)
            application.update(
                {
                    "payment_info.created_at": {
                        "$gte": current_start_date,
                        "$lte": current_end_date,
                    }
                }
            )
            current_application_lead = await DatabaseConfiguration(
                season=season
            ).studentApplicationForms.count_documents(application)
            leads = await utility_obj.get_percentage_difference_with_position(
                previous_application_lead, current_application_lead
            )
            data.update(
                {
                    "application_count_percentage": leads.get("percentage"),
                    "application_count_position": leads.get("position"),
                }
            )

        communication.append(
            {
                "$match": {
                    "created_at": {
                        "$gte": previous_start_date,
                        "$lte": previous_end_date,
                    }
                }
            }
        )
        communication.append(
            {"$group": {"_id": None, "total_email_sum": {"$sum": "$total_email"}}}
        )
        total_email = (
            await DatabaseConfiguration(season=season)
            .activity_email.aggregate(communication)
            .to_list(None)
        )
        total_email_sum = total_email[0].get("total_email_sum", 0) if total_email else 0
        communication.pop(-1)

        sms_total = await self.get_sms_count(communication, season)

        whatsapp_total = await self.get_whatsapp_count(communication, season)

        previous_total_communication = total_email_sum + sms_total + whatsapp_total
        communication = []
        communication.append(
            {
                "$match": {
                    "created_at": {"$gte": current_start_date, "$lte": current_end_date}
                }
            }
        )
        communication.append(
            {"$group": {"_id": None, "total_email_sum": {"$sum": "$total_email"}}}
        )
        total_email = (
            await DatabaseConfiguration(season=season)
            .activity_email.aggregate(communication)
            .to_list(None)
        )
        total_email_sum = total_email[0].get("total_email_sum", 0) if total_email else 0
        communication.pop(-1)

        sms_total = await self.get_sms_count(communication, season)

        whatsapp_total = await self.get_whatsapp_count(communication, season)

        current_total_communication = total_email_sum + sms_total + whatsapp_total
        communication_leads = await utility_obj.get_percentage_difference_with_position(
            previous_total_communication, current_total_communication
        )
        data.update(
            {
                "total_communication_percentage": communication_leads.get("percentage"),
                "total_communication_position": communication_leads.get("position"),
            }
        )
        return data

    async def get_overall_verified_rejected_data(
            self, application, application_type, season
    ):
        """
        get overall document verified and rejected data
        Params:
          application(dict) : Filter used depending on the conditions given
          application_type(str): This is the type of application given in filer. this can have value
                                  dv_approved/dv_rejected

        Returns:
            Count of verified/rejected students
        """
        application.update({"current_stage": {"$gte": 8}})
        if application_type in ["dv approved", "dv accepted"]:
            application.update({"dv_status": "Accepted"})
        elif application_type == "dv rejected":
            application.update({"dv_status": "Rejected"})
        return (
            await DatabaseConfiguration().studentApplicationForms.count_documents(
                application
            )
        )

    async def get_application_type_based_data(
            self, application, application_type, data, season
    ):
        """
        get the application data of given application_data
        params:
        application(dict) : Filter used depending on the conditions given
        application_type(str): This is the type of application given in filer. this can have value
                                  paid/submitted/enrolled/interview_done/interview_scheduled/dv_approved
                                  /dv_rejected/offer_letter_sent
        data(dict) : The existing data which is grabbed for different schemes

        """

        if application_type in ["enrolled", "submitted"]:
            application.update({"current_stage": 10})
            submitted_applications = await DatabaseConfiguration(
                season=season
            ).studentApplicationForms.count_documents(application)
            data.update({"application_count": submitted_applications})
        elif application_type in ["dv approved", "dv rejected", "dv accepted"]:
            count = await self.get_overall_verified_rejected_data(
                application, application_type, season=season
            )
            data.update({"application_count": count})
        elif application_type == "interview_scheduled":
            application.update({"interviewStatus.status": "Scheduled"})
            interview_scheduled_applications = await DatabaseConfiguration(
                season=season
            ).studentApplicationForms.count_documents(application)
            data.update({"application_count": interview_scheduled_applications})
        elif application_type == "interview_done":
            application.update({"interviewStatus.status": "Done"})
            interview_done_applications = await DatabaseConfiguration(
                season=season
            ).studentApplicationForms.count_documents(application)
            data.update({"application_count": interview_done_applications})
        elif application_type == "offer_letter_sent":
            application.update({"offer_letter": {"$exists": True}})
            offer_letter_applications = await DatabaseConfiguration(
                season=season
            ).studentApplicationForms.count_documents(application)
            data.update({"application_count": offer_letter_applications})
        return data

    async def score_board(
            self,
            college_id: str,
            date_range: dict,
            route=None,
            user=None,
            season=None,
            lead_funnel=False,
            form_stage_wise_segregation=False,
            change_indicator=None,
            application_type=None,
    ):
        """
        Get the Admission details/status of Students on the basis of college_id
        """
        total_lead = {"college_id": ObjectId(college_id)}
        application = {"college_id": ObjectId(college_id), "current_stage": {"$gte": 2}}
        communication = []
        if season == "":
            season = None
        if (date_range == {}) and ((route == "score_board") or (lead_funnel is True)):
            pass
        elif form_stage_wise_segregation and (date_range == {}):
            date_range = await utility_obj.last_30_days(days=28)
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
            total_lead.update({"created_at": {"$gte": start_date, "$lte": end_date}})
            application.update({"enquiry_date": {"$gte": start_date, "$lte": end_date}})
            communication.append(
                {"$match": {"created_at": {"$gte": start_date, "$lte": end_date}}}
            )
        data = {}
        if user.get("role", {}).get("role_name", "").lower() == "college_counselor":
            allocate_to_counselor = {
                "allocate_to_counselor.counselor_id": ObjectId(str(user.get("_id")))
            }
            total_lead.update(allocate_to_counselor)
            application.update(allocate_to_counselor)
        if route == "score_board":
            total_leads = await DatabaseConfiguration(
                season=season
            ).studentsPrimaryDetails.count_documents(total_lead)
            total_lead.update({"is_verify": True})
            verify_leads = await DatabaseConfiguration(
                season=season
            ).studentsPrimaryDetails.count_documents(total_lead)
            un_verify_leads = total_leads - verify_leads
            temp = {
                "total_lead": total_leads,
                "verify_student": verify_leads,
                "un_verify_student": un_verify_leads,
            }
            data.update(temp)
            communication.append(
                {"$group": {"_id": None, "total_email_sum": {"$sum": "$total_email"}}}
            )
            total_email = (
                await DatabaseConfiguration(season=season)
                .activity_email.aggregate(communication)
                .to_list(None)
            )
            total_email_sum = (
                total_email[0].get("total_email_sum", 0) if total_email else 0
            )
            communication.pop(-1)

            sms_total = await self.get_sms_count(communication, season)

            whatsapp_total = await self.get_whatsapp_count(communication, season)

            total_communication = total_email_sum + sms_total + whatsapp_total
            data.update(
                {
                    "total_communication": total_communication,
                    "total_email": total_email_sum,
                    "total_sms": sms_total,
                    "total_whatsapp": whatsapp_total,
                }
            )
        form_initiated = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.update({"payment_info.status": "captured"})
        paid_application = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        if date_range:
            application.pop("enquiry_date")
            application.update(
                {"payment_info.created_at": {"$gte": start_date, "$lte": end_date}}
            )
        razor_pay_paid_application = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        if date_range:
            application.pop("payment_info.created_at")
            application.update({"enquiry_date": {"$gte": start_date, "$lte": end_date}})
        application.pop("payment_info.status")
        application.update({"payment_initiated": True})
        payment_initiated_applications = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        total_unpaid_application = form_initiated - paid_application
        not_initiated_application = form_initiated - payment_initiated_applications
        initiated_application = payment_initiated_applications - paid_application
        if route == "declaration":
            application.update({"declaration": True})
            form_submitted = await DatabaseConfiguration(
                season=season
            ).studentApplicationForms.count_documents(application)
            application.pop("declaration")
            payment_initiated = await DatabaseConfiguration(
                season=season
            ).studentApplicationForms.count_documents(application)
            temp3 = {
                "form_submitted": form_submitted,
                "total_initiated": payment_initiated,
            }
            data.update(temp3)
        application.pop("payment_initiated")
        if application_type:
            if application_type == "paid":
                data.update({"application_count": razor_pay_paid_application})
            else:
                data = await self.get_application_type_based_data(
                    application, application_type, data, season=season
                )
        if change_indicator:
            data = await self.get_admin_graph_data_based_on_change_indicator(
                college_id,
                change_indicator,
                data,
                route,
                form_stage_wise_segregation,
                lead_funnel,
                application_type,
                season=season,
            )
        if route != "score_board":
            data.update(
                {
                    "application_paid": razor_pay_paid_application,
                    "unpaid_application": total_unpaid_application,
                    "total_initiated": payment_initiated_applications,
                }
            )

        data.update(
            {
                "form_initiated": form_initiated,
                "payment_init_but_not_paid": initiated_application,
                "payment_not_initiated": not_initiated_application,
            }
        )
        return data

    async def get_application_counts_details(
            self,
            college_id: str,
            start_date: datetime = None,
            end_date: datetime = None,
            application_type="paid",
            season: str = None,
            counselor_id: list | None = None,
    ):
        """
        get the application count based on application type

        params:
            college_id (str): Get the college id of the application
            start_date (datetime): Get the start date of the application
            end_date (datetime): Get the end date of the application
            application_type (str): Get the application_type e.q. paid,
             dv_rejected, submitted etc

        return:
            A dictionary of the count of the application and paid etc
        """
        pipeline = [
            {"$match": {"college_id": ObjectId(college_id)}},
            {
                "$group": {
                    "_id": None,
                    "total_applications": {"$sum": 1},
                    "form_initiated": {
                        "$sum": {"$cond": [{"$gte": ["$current_stage", 2]}, 1, 0]}
                    },
                    "payment_init_but_not_paid": {
                        "$sum": {
                            "$cond": {
                                "if": {"$eq": ["$payment_info.status", "captured"]},
                                "then": 0,
                                "else": {"$cond": ["$payment_initiated", 1, 0]},
                            }
                        }
                    },
                    "payment_not_initiated": {
                        "$sum": {
                            "$cond": {
                                "if": {"$eq": ["$payment_initiated", False]},
                                "then": {
                                    "$cond": {
                                        "if": {"$gte": ["$current_stage", 2]},
                                        "then": 1,
                                        "else": 0,
                                    }
                                },
                                "else": 0,
                            }
                        }
                    },
                    "application_count": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$payment_info.status", "captured"]},
                                1,
                                0,
                            ]
                        }
                    },
                }
            },
        ]

        match_base = pipeline[0].get("$match", {})

        if start_date not in [None, ""] and end_date in [None, ""]:
            match_base.update({"enquiry_date": {"$gte": start_date}})
        if start_date not in [None, ""] and end_date not in [None, ""]:
            match_base.update(
                {"enquiry_date": {"$gte": start_date, "$lte": end_date}}
            )
        if counselor_id:
            match_base.update(
                {"allocate_to_counselor.counselor_id": {"$in": counselor_id}}
            )
        if application_type == "submitted":
            pipeline[1].get("$group", {}).update(
                {
                    "application_count": {
                        "$sum": {
                            "$cond": [
                                "$declaration",
                                1,
                                0,
                            ]
                        }
                    }
                }
            )
        if application_type == "interview scheduled":
            pipeline[1].get("$group", {}).update(
                {
                    "application_count": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$interviewStatus.status", "Scheduled"]},
                                1,
                                0,
                            ]
                        }
                    }
                }
            )
        if application_type == "interview done":
            pipeline[1].get("$group", {}).update(
                {
                    "application_count": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$interviewStatus.status", "Done"]},
                                1,
                                0,
                            ]
                        }
                    }
                }
            )

        if application_type == 'paid':
            if start_date not in [None, ""]:
                if match_base.get("enquiry_date"):
                    match_base.pop('enquiry_date')

                if end_date in [None, ""]:
                    match_base.update({
                        "payment_info.created_at": {"$gte": start_date}
                    })
                else:
                    match_base.update({
                        "payment_info.created_at": {"$gte": start_date, "$lte": end_date}
                    })

            pipeline[1].get("$group", {}).update({
                "application_count": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$payment_info.status", "captured"]},
                            1,
                            0,
                        ]
                    }
                }
            })

        if application_type == "offer letter sent":
            pipeline[1].get("$group", {}).update(
                {
                    "application_count": {
                        "$sum": {
                            "$cond": [
                                {"$ifNull": ["$offer_letter", False]},
                                1,
                                0,
                            ]
                        }
                    }
                }
            )

        result = DatabaseConfiguration(season=season).studentApplicationForms.aggregate(
            pipeline
        )
        data = {}
        async for data in result:
            if data is None:
                data = {}
        if application_type in ["dv approved", "dv rejected", "dv accepted"]:
            application = {}
            count = await self.get_overall_verified_rejected_data(
                application, application_type, season=season
            )
            data.update({"application_count": count})
        if application_type == "enrolled":
            data.update({"application_count": 0})
        return data

    async def get_lead_counts_details(
            self,
            college_id: str | None = None,
            start_date: datetime = None,
            end_date: datetime = None,
            season: str | None = None,
            counselor_id: list | None = None,
    ):
        """
        Get the lead count details of the
        """
        pipeline = [
            {
                "$match": {
                    "college_id": ObjectId(college_id),
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_lead": {"$sum": 1},
                    "verify_student": {"$sum": {"$cond": ["$is_verify", 1, 0]}},
                    "un_verify_student": {"$sum": {"$cond": ["$is_verify", 0, 1]}},
                }
            },
        ]
        if start_date is not None:
            pipeline[0].get("$match", {}).update({"created_at": {"$gte": start_date}})
        if start_date is not None and end_date is not None:
            pipeline[0].get("$match", {}).update(
                {"created_at": {"$gte": start_date, "$lte": end_date}}
            )
        if counselor_id:
            pipeline[0].get("$match", {}).update(
                {"allocate_to_counselor.counselor_id": {"$in": counselor_id}}
            )
        result = DatabaseConfiguration(season=season).studentsPrimaryDetails.aggregate(
            pipeline
        )
        data = {}
        async for data in result:
            if data is None:
                data = {}
        return data

    async def get_percentage_details(
            self,
            college_id: str | None = None,
            change_indicator: str | None = None,
            application_type: str | None = None,
            season: str | None = None,
            counselor_id: list | None = None,
    ):
        """
        get the percentage and position of the application and lead counts

        params:
            college_id (str): Get the college id of the application
            change_indicator (str): Get the change indicator e.g. last_7_days,
                last_15_days and last_30_days
            application_type (str): get the application type of the application
            season (str): Get the season of the student

        return:
            A dictionary containing the percentage and position of the application
        """
        start_date, middle_date, previous_date = (
            await utility_obj.get_start_date_and_end_date_by_change_indicator(
                change_indicator
            )
        )
        previous_start_date, previous_end_date = await utility_obj.date_change_format(
            str(start_date), str(middle_date)
        )
        current_start_date, current_end_date = await utility_obj.date_change_format(
            str(previous_date), str(today)
        )
        previous_application_details = await self.get_application_counts_details(
            college_id=college_id,
            start_date=previous_start_date,
            end_date=previous_end_date,
            application_type=application_type,
            season=season,
            counselor_id=counselor_id,
        )
        current_application_details = await self.get_application_counts_details(
            college_id=college_id,
            start_date=current_start_date,
            end_date=current_end_date,
            application_type=application_type,
            season=season,
            counselor_id=counselor_id,
        )
        previous_lead_details = await self.get_lead_counts_details(
            college_id=college_id,
            start_date=previous_start_date,
            end_date=previous_end_date,
            season=season,
            counselor_id=counselor_id,
        )
        current_lead_details = await self.get_lead_counts_details(
            college_id=college_id,
            start_date=current_start_date,
            end_date=current_end_date,
            season=season,
            counselor_id=counselor_id,
        )
        previous_communication_details = await self.get_communication_details(
            start_date=previous_start_date, end_date=previous_end_date, season=season
        )
        current_communication_details = await self.get_communication_details(
            start_date=current_start_date, end_date=current_end_date, season=season
        )
        form_initiated = await utility_obj.get_percentage_difference_with_position(
            previous_application_details.get("form_initiated", 0),
            current_application_details.get("form_initiated", 0),
        )
        application_count = await utility_obj.get_percentage_difference_with_position(
            previous_application_details.get("application_count", 0),
            current_application_details.get("application_count", 0),
        )
        total_lead = await utility_obj.get_percentage_difference_with_position(
            previous_lead_details.get("total_lead", 0),
            current_lead_details.get("total_lead", 0),
        )
        total_communication = await utility_obj.get_percentage_difference_with_position(
            previous_communication_details.get("total_communication", 0),
            current_communication_details.get("total_communication", 0),
        )
        return {
            "form_initiated_percentage": form_initiated.get("percentage"),
            "form_initiated_position": form_initiated.get("position"),
            "application_count_percentage": application_count.get("percentage"),
            "application_count_position": application_count.get("position"),
            "total_communication_percentage": total_communication.get("percentage"),
            "total_communication_position": total_communication.get("position"),
            "lead_percentage": total_lead.get("percentage"),
            "lead_position": total_lead.get("position"),
        }

    async def get_communication_details(
            self,
            start_date: datetime = None,
            end_date: datetime = None,
            season: str | None = None,
    ):
        """
        Get count of email, sms and whatsapp

        params:
            start_date (datetime): get the start date of the email and sms
            end_date (datetime): get the start date of the email and sms
            season (str): get the season name of the college

        return:
            A dictionary contains count of sms, email and whatsapp
        """
        result = {}

        pipeline = [
            {
                '$project': {
                    'email_sent': {
                        '$size': {
                            '$filter': {
                                'input': {
                                    '$ifNull': [
                                        '$email_summary.transaction_id', []
                                    ]
                                },
                                'as': 'data',
                                'cond': {"$and": []}
                            }
                        }
                    },
                    
                    
                    'sms_sent': {
                        '$size': {
                            '$filter': {
                                'input': {
                                    '$ifNull': [
                                        '$sms_summary.transaction_id', []
                                    ]
                                },
                                'as': 'data',
                                'cond': {"$and": []}
                            }
                        }
                    },
                    
                    'whatsapp_sent': {
                        '$size': {
                            '$filter': {
                                'input': {
                                    '$ifNull': [
                                        '$whatsapp_summary.transaction_id', []
                                    ]
                                },
                                'as': 'data',
                                'cond': {"$and": []}
                            }
                        }
                    }
                }   
            }, {
                '$group': {
                    '_id': None,
                    'email_sent': {
                        '$sum': '$email_sent'
                    },
                    'sms_sent': {
                        '$sum': '$sms_sent'
                    },
                    'whatsapp_sent': {
                        '$sum': '$whatsapp_sent'
                    }
                }
            }
        ]

        #TODO: Here we don't need to call this functions as we are already getting the count in the pipeline
        # sms_total = await self.get_sms_count(communication, season, True)

        # whatsapp_total = await self.get_whatsapp_count(communication, season, True)

        if start_date is not None and end_date is not None:

            for stage in pipeline:
                if "$project" in stage:
                    for field in stage["$project"]:
                        if "$size" in stage["$project"][field]:
                            cond = stage["$project"][field]["$size"]["$filter"]["cond"]
                            if "$and" in cond:
                                cond["$and"].extend([
                                    {"$gte": ["$$data.created_at", start_date]},
                                    {"$lt": ["$$data.created_at", end_date]}
                                ])
        result = await DatabaseConfiguration().communication_log_collection.aggregate(pipeline).to_list(None)
        result = result[0] if result else {}
        communication_sent = result.get("email_sent", 0) + result.get("sms_sent", 0) + result.get(
            "whatsapp_sent", 0)
        
        result= {
                "total_communication": communication_sent,
                "total_email": result.get("email_sent", 0),
                "total_sms": result.get("sms_sent", 0),
                "total_whatsapp": result.get("whatsapp_sent", 0)
            }
        return result

    async def score_board_helper(
            self,
            college_id: str,
            date_range: dict | None = None,
            user: dict | None = None,
            season: str | None = None,
            change_indicator: str | None = None,
            application_type: str | None = None,
            cache_change_indicator: tuple | None = None
    ):
        """
        Get the score board count of application paid, initialize and lead

        params:
            date_range: (dict): Get the datetime start date and end date
            user: (dict): Get the user details of the current user
            change_indicator: (str): Get the indicator last_7_days,
             last_15_days and last_30_days, None
            application_type (str): Get the count and percentage based on the
            application_type e.g. paid, submitted, dv_rejected, etc
            cache_change_indicator (tuple): Change indicator key and cached value

        returns:
            A dictionary contains the count of application and percentage
        """
        counselor_id = []
        if user.get("role", {}).get("role_name") == "college_counselor":
            counselor_id = [ObjectId(user.get("_id"))]
        elif user.get("role", {}).get("role_name") == "college_head_counselor":
            pipeline = [
                {
                    "$match": {
                        "is_activated": True,
                        "head_counselor_id": ObjectId(user.get("_id")),
                    }
                }
            ]
            user_details = DatabaseConfiguration().user_collection.aggregate(pipeline)
            counselor_id = [
                ObjectId(counselor.get("_id")) async for counselor in user_details
            ]
        data_temp = {}
        start_date, end_date = None, None
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
        application_details = await self.get_application_counts_details(
            college_id=college_id,
            start_date=start_date,
            end_date=end_date,
            application_type=application_type,
            season=season,
            counselor_id=counselor_id,
        )
        data_temp.update(application_details)
        lead_details = await self.get_lead_counts_details(
            college_id=college_id,
            start_date=start_date,
            end_date=end_date,
            season=season,
            counselor_id=counselor_id,
        )
        data_temp.update(lead_details)
        communication_details = await self.get_communication_details(
            start_date=start_date, end_date=end_date, season=season
        )
        data_temp.update(communication_details)
        if change_indicator and not date_range:
            key, cache_data = None, None
            if cache_change_indicator:
                key, cache_data = cache_change_indicator
            if cache_data:
                data_temp.update(cache_data)
                return data_temp
            indicator_details = await self.get_percentage_details(
                college_id=college_id,
                application_type=application_type,
                change_indicator=change_indicator,
                season=season,
                counselor_id=counselor_id,
            )
            data_temp.update(indicator_details)
            if key:
                await insert_data_in_cache(key, indicator_details, change_indicator=True)
        return data_temp

    async def get_top_performing_channel_data(
            self, college_id: str, date_range: dict, season, programs
    ):
        """
        Get top performing channel data
        """
        pipeline = [
            {"$match": {"college_id": ObjectId(college_id)}},
            {
                '$group': {
                    '_id': '$source.primary_source.utm_source',
                    'students': {
                        '$addToSet': '$student_id'
                    },
                    'application_count': {
                        '$sum': 1
                    },
                    'declaration_count': {
                        '$sum': {
                            '$cond': [
                                '$declaration', 1, 0
                            ]
                        }
                    },
                    'paid_count': {
                        '$sum': {
                            '$cond': [
                                {
                                    "$and": [
                                        {"$eq": ["$payment_info.status", "captured"]}
                                    ]
                                }, 1, 0
                            ]
                        }
                    }
                }
            }, {
                '$project': {
                    '_id': '$_id',
                    'application_count': '$application_count',
                    'declaration_count': '$declaration_count',
                    'students': {
                        '$size': '$students'
                    },
                    'paid_count': '$paid_count'
                }
            }
        ]
        if programs:
            app_program_filter = []
            for program in programs:
                app_program_filter.append(
                    {
                        "$and": [
                            {"course_id": ObjectId(program.get("course_id"))},
                            {"spec_name1": program.get("course_specialization")},
                        ]
                    }
                )
            if app_program_filter:
                pipeline[0].get("$match", {}).update({"$or": app_program_filter})
        if season == "":
            season = None
        total_pipeline = [
            {
                "$facet": {
                    "total_paid_application_count": [
                        {"$match": {"college_id": ObjectId(college_id), "payment_info.status": "captured"}},
                        {"$count": "count"}
                    ],
                    "total_applications": [
                        {"$match": {"current_stage": {"$gte": 2}}},
                        {"$count": "count"}
                    ],
                    "total_completed_applications": [
                        {"$match": {"declaration": True}},
                        {"$count": "count"}
                    ]
                }
            },
            {
                "$project": {
                    "total_paid_application_count": {
                        "$arrayElemAt": ["$total_paid_application_count.count", 0]
                    },
                    "total_applications": {
                        "$arrayElemAt": ["$total_applications.count", 0]
                    },
                    "total_completed_applications": {
                        "$arrayElemAt": ["$total_completed_applications.count", 0]
                    }
                }
            }
        ]
        if len(date_range) < 2:
            # get total students count
            total_students_count = await DatabaseConfiguration(
                season=season
            ).studentsPrimaryDetails.count_documents(
                {"college_id": ObjectId(college_id)}
            )
            result = await DatabaseConfiguration(season=season).studentApplicationForms.aggregate(
                total_pipeline).to_list(
                length=None)
            result = result[0] if result else {}
            total_paid_application_count = result.get('total_paid_application_count', 0)
            total_applications = result.get('total_applications', 0)
            total_completed_applications = result.get('total_completed_applications', 0)
        else:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
            pipeline[0].get("$match", {}).update(
                {
                    "enquiry_date": {
                        "$gte": start_date,
                        "$lte": end_date,
                    }
                }
            )
            (pipeline[1].get("$group", {}).get("paid_count", {}).get("$sum", {}).get("$cond", [])[0].get(
                "$and", []).extend(
                [
                    {"$gte": ["$payment_info.created_at", start_date]},
                    {"$lte": ["$payment_info.created_at", end_date]}]
            ))
            total_students_count = await DatabaseConfiguration(
                season=season
            ).studentsPrimaryDetails.count_documents(
                {
                    "college_id": ObjectId(college_id),
                    "created_at": {"$gte": start_date, "$lte": end_date},
                }
            )
            facet_phase = total_pipeline[0].get("$facet")
            (facet_phase.get("total_paid_application_count")[0].get("$match")
             .update({"payment_info.created_at": {"$gte": start_date, "$lte": end_date}}))
            (facet_phase.get("total_applications")[0].get("$match")
             .update({"enquiry_date": {"$gte": start_date, "$lte": end_date}}))
            (facet_phase.get("total_completed_applications")[0].get("$match")
             .update({"enquiry_date": {"$gte": start_date, "$lte": end_date}}))
            result = await DatabaseConfiguration(season=season).studentApplicationForms.aggregate(
                total_pipeline).to_list(
                length=None)
            result = result[0] if result else {}
            total_paid_application_count = result.get('total_paid_application_count', 0)
            total_applications = result.get('total_applications', 0)
            total_completed_applications = result.get('total_completed_applications', 0)
        result = DatabaseConfiguration(season=season).studentApplicationForms.aggregate(
            pipeline
        )
        total_leads = 0
        submit_applications = 0
        paid_application = 0
        source_dict = dict()

        async for doc in result:
            source = doc.get("_id")
            if source_dict.get(source) is None:
                sourceStats = SourceStats(source_name=str(source))
            else:
                sourceStats = source_dict.get(source)
            sourceStats.submit_utm = doc.get("declaration_count", 0)
            sourceStats.paid_utm += doc.get("paid_count", 0)
            submit_applications += sourceStats.submit_utm
            paid_application += doc.get("paid_count", 0)
            sourceStats.total_utm = doc.get("students", 0)
            total_leads += doc.get("students", 0)

            source_dict[source] = sourceStats

        return (
            source_dict,
            {
                "total_applications": total_applications,
                "total_leads": total_leads,
                "total_paid_applications": total_paid_application_count,
                "total_submit_applications": total_completed_applications,
                "total_lead_count": total_students_count,
            },
        )

    async def get_top_performing_channel_data_based_on_change_indicator(
            self, college_id, change_indicator, season=None, programs=None
    ):
        """
        Get top performing channel data based on change indicator
        """
        (
            start_date,
            middle_date,
            previous_date,
        ) = await utility_obj.get_start_date_and_end_date_by_change_indicator(
            change_indicator
        )
        # previous application data
        date_range = {"start_date": str(start_date), "end_date": str(middle_date)}
        previous_source_dict, previous_perform_helper = (
            await self.get_top_performing_channel_data(
                college_id, date_range, season=season, programs=programs
            )
        )
        # current application data
        date_range = {"start_date": str(previous_date), "end_date": str(today)}
        current_source_dict, current_perform_helper = (
            await self.get_top_performing_channel_data(
                college_id, date_range, season=season, programs=programs
            )
        )

        dct_temp = {}
        for key in previous_source_dict.keys() | current_source_dict.keys():
            if key in previous_source_dict and key in current_source_dict:
                total_lead_percentage = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            float(previous_source_dict[key].total_utm),
                            float(current_source_dict[key].total_utm),
                        )
                    )
                )
                paid_application = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            float(previous_source_dict[key].paid_utm),
                            float(current_source_dict[key].paid_utm),
                        )
                    )
                )
                submit_application = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            float(previous_source_dict[key].submit_utm),
                            float(current_source_dict[key].submit_utm),
                        )
                    )
                )
            elif key in previous_source_dict:
                total_lead_percentage = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            float(previous_source_dict[key].total_utm), 0
                        )
                    )
                )
                paid_application = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            float(previous_source_dict[key].paid_utm), 0
                        )
                    )
                )
                submit_application = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            float(previous_source_dict[key].submit_utm), 0
                        )
                    )
                )
            else:
                total_lead_percentage = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            0, float(current_source_dict[key].total_utm)
                        )
                    )
                )
                paid_application = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            0, float(current_source_dict[key].paid_utm)
                        )
                    )
                )
                submit_application = (
                    await (
                        utility_obj.get_percentage_difference_with_position(
                            0, float(current_source_dict[key].submit_utm)
                        )
                    )
                )
            dct_temp.update(
                {
                    key: {
                        "total_lead_percentage_difference": total_lead_percentage.get(
                            "percentage", 0
                        ),
                        "paid_application_percentage_difference": paid_application.get(
                            "percentage", 0
                        ),
                        "total_lead_percentage_position": total_lead_percentage.get(
                            "position", "equal"
                        ),
                        "paid_application_percentage_position": paid_application.get(
                            "position", "equal"
                        ),
                        "submit_application_percentage_position": submit_application.get(
                            "position", "equal"
                        ),
                        "submit_application_percentage_difference": submit_application.get(
                            "percentage", 0
                        ),
                    }
                }
            )

        return {"source_wise_lead_dict": dct_temp}

    async def top_performing_channel(
            self, college_id: str, date_range: dict, season, change_indicator, programs, cache_change_indicator=None
    ):
        """
        Get top performing channel by college id
        """
        source_dict, perform_helper = await self.get_top_performing_channel_data(
            college_id, date_range, season, programs
        )
        cache_ci_key, ci_data = None, None
        if cache_change_indicator:
            cache_ci_key, ci_data = cache_change_indicator
        if ci_data:
            change_indicator_data = ci_data
        else:
            change_indicator_data = (
                await self.get_top_performing_channel_data_based_on_change_indicator(
                    college_id, change_indicator, programs=programs
                )
            )
            await insert_data_in_cache(cache_ci_key, change_indicator_data, change_indicator=True)
        final_result = []
        for source_key in source_dict:
            source = source_dict[source_key]
            source.total_percentage = utility_obj.get_percentage_result(
                source.total_utm, perform_helper.get("total_lead_count", 0)
            )
            source.paid_application_percentage = utility_obj.get_percentage_result(
                source.paid_utm, perform_helper.get("total_paid_applications", 0)
            )
            source.submit_application_percentage = utility_obj.get_percentage_result(
                source.submit_utm, perform_helper.get("total_submit_applications", 0)
            )
            source = jsonable_encoder(source)
            if source.get("source_name") in change_indicator_data.get(
                    "source_wise_lead_dict", {}
            ):
                source.update(
                    {
                        "total_lead_percentage_difference": change_indicator_data.get(
                            "source_wise_lead_dict", {}
                        )
                        .get(source.get("source_name"))
                        .get("total_lead_percentage_difference", 0),
                        "total_lead_percentage_position": change_indicator_data.get(
                            "source_wise_lead_dict", {}
                        )
                        .get(source.get("source_name"))
                        .get("total_lead_percentage_position", "equal"),
                        "paid_application_percentage_difference": change_indicator_data.get(
                            "source_wise_lead_dict", {}
                        )
                        .get(source.get("source_name"))
                        .get("paid_application_percentage_difference"),
                        "paid_application_percentage_position": change_indicator_data.get(
                            "source_wise_lead_dict", {}
                        )
                        .get(source.get("source_name"))
                        .get("paid_application_percentage_position"),
                        "submit_application_percentage_difference": change_indicator_data.get(
                            "source_wise_lead_dict", {}
                        )
                        .get(source.get("source_name"))
                        .get("submit_application_percentage_difference"),
                        "submit_application_percentage_position": change_indicator_data.get(
                            "source_wise_lead_dict", {}
                        )
                        .get(source.get("source_name"))
                        .get("submit_application_percentage_position"),
                    }
                )
            else:
                source.update(
                    {
                        "total_lead_percentage_difference": 0,
                        "total_lead_percentage_position": "equal",
                        "paid_application_percentage_difference": 0,
                        "paid_application_percentage_position": "equal",
                        "submit_application_percentage_difference": 0,
                        "submit_application_percentage_position": "equal",
                    }
                )
            final_result.insert(len(final_result), source)
        return {
            "source_wise_lead": final_result,
            "message": "Applications data fetched successfully!",
        }

    async def format_event_data(
            self,
            date: str,
            events_data: dict,
            leads_data: dict,
            applications_data: dict,
            events: list,
            leads: list,
            applications: list,
            formatted_dates: list,
    ) -> any:
        """
        Get event data in a respective format
        """
        formatted_date = arrow.get(date, "YYYY-MM-DD").format("D MMMM")
        event_data = events_data.get(date, [])
        if event_data:
            event_data_list = [
                {"date": formatted_date, "event": event_dict}
                for event_dict in event_data
            ]
            events.extend(event_data_list)
        leads.append(
            {"x": formatted_date, "y": leads_data.get(date, 0), "event": event_data}
        )
        applications.append(
            {
                "x": formatted_date,
                "y": applications_data.get(date, 0),
                "event": event_data,
            }
        )
        formatted_dates.append(formatted_date)

    async def lead_application(
            self, college_id: str, date_range: dict, counselor_id, season, source=None
    ):
        if len(date_range) < 2:
            date_range = await utility_obj.last_30_days(days=28)
        start_date, end_date = await utility_obj.date_change_format(
            date_range.get("start_date"), date_range.get("end_date")
        )

        if season == "":
            season = None

        base_match = {
            "college_id": ObjectId(college_id),
            "created_at": {"$gte": start_date, "$lte": end_date},
        }

        if source:
            student_ids = await Student().get_students_based_on_source(
                source=source, season=season
            )
            base_match["_id"] = {"$in": student_ids}
        if counselor_id:
            base_match["allocate_to_counselor.counselor_id"] = {
                "$in": [ObjectId(c_id) for c_id in counselor_id]
            }

        pipeline = [
            {"$match": base_match},
            {
                "$project": {
                    "created_date": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at",
                            "timezone": "+05:30",
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$created_date",
                    "leads": {"$sum": 1},
                }
            },
        ]

        leads_data = {}
        async for doc in DatabaseConfiguration(
                season=season
        ).studentsPrimaryDetails.aggregate(pipeline):
            leads_data[doc["_id"]] = doc["leads"]

        base_match["payment_info.created_at"] = base_match.pop("created_at")
        if source:
            base_match["student_id"] = base_match.pop("_id")
        base_match["payment_info.status"] = "captured"
        pipeline[0]["$match"] = base_match
        pipeline[1]["$project"]["created_date"] = {
            "$dateToString": {
                "format": "%Y-%m-%d",
                "date": "$payment_info.created_at",
                "timezone": "+05:30",
            }
        }

        applications_data = {}
        async for doc in DatabaseConfiguration(
                season=season
        ).studentApplicationForms.aggregate(pipeline):
            applications_data[doc["_id"]] = doc["leads"]

        events_data = await Event().get_events_by_date_range(start_date, end_date)

        all_dates = sorted(
            list(
                set(leads_data.keys())
                | set(applications_data.keys())
                | set(events_data.keys())
            )
        )

        leads, applications, formatted_dates, events, event_ids = [], [], [], [], []
        gather_data = [
            self.format_event_data(
                date,
                events_data,
                leads_data,
                applications_data,
                events,
                leads,
                applications,
                formatted_dates,
            )
            for date in all_dates
        ]
        await asyncio.gather(*gather_data)
        return {
            "date": formatted_dates,
            "lead": leads,
            "application": applications,
            "event": events,
        }

    def custom_sort_key(self, elements: list) -> list:
        """
        Sorts the given list of elements in specific required order
        Params:
            elements (list): List which is to be sorted
        Returns:
            elements (list): Sorted list
        """
        order = {
            "total_leads": 0,
            "fresh_lead": 1,
            "interested": 2,
            "paid_application": 3,
            "admission_confirmed": 4
        }
        return order.get(elements, float('inf'))

    async def get_source_wise_details(
            self,
            start_date: datetime.datetime | None,
            end_date: datetime.datetime | None,
            season: str | None,
            lead_stage_list=None,
            mode=None,
            lead_type=None
    ) -> tuple:
        """
        Get the source wise details.

        Params:
            - start_date (datetime | None): Either None or start datetime for
                get sourcewise data.
            - end_date (datetime | None): Either None or end datetime for get
                sourcewise data.
            - season (str | None): Either None or a string which represents
                season identifier which useful for get season bases
                source wise data.
            - lead_stage_list (str | None): Lead stage list of college
            - mode (str | None): mode to filter field name
            - lead_type (str | None) : Either None or API or Online to filter student data accordingly

        Returns:
            tuple: A tuple which represents all_stages, sources and
                all_lead_stages information.
        """
        all_lead_stages = [lead_stage.lower().replace(" ", "_").replace("-", "_") for lead_stage in lead_stage_list]
        all_lead_stages.extend(["paid_application", "total_leads"])
        all_lead_stages = sorted(all_lead_stages, key=self.custom_sort_key)
        pipeline = [
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "localField": "_id",
                    "foreignField": "student_id",
                    "as": "student_application",
                }
            },
            {"$unwind": {"path": "$student_application"}},
            {
                "$lookup": {
                    "from": "leadsFollowUp",
                    "localField": "student_application._id",
                    "foreignField": "application_id",
                    "as": "leads",
                }
            },
            {"$unwind": {"path": "$leads",
                         "preserveNullAndEmptyArrays": True
                         }},
            {
                "$group": {
                    "_id": {
                        "source": "$source.primary_source.utm_source",
                        "lead_stage": {"$ifNull": ["$leads.lead_stage", "Fresh Lead"]},
                    },
                    "count": {"$sum": 1},
                    "paid_application": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$student_application.payment_info.status",
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
                    "source": "$_id.source",
                    "lead_stage": "$_id.lead_stage",
                    "count": 1,
                    "paid_application": 1,
                }
            },
        ]
        if lead_type:
            pipeline.insert(0, {"$match": {"source.primary_source.lead_type": lead_type.lower()}})
        filter_field_name = "allocate_to_counselor.last_update" if mode == "Assignment" else "lead_stage_change_at" \
            if mode == "Activity" else "created_at"
        if start_date and end_date:
            match = {
                "$match": {
                    filter_field_name: {
                        "$gte": start_date,
                        "$lte": end_date,
                    }
                }
            }
            pipeline.insert(2, match)
        result = (
            await DatabaseConfiguration(season=season)
            .studentsPrimaryDetails.aggregate(pipeline)
            .to_list(None)
        )
        sources = {}
        all_stages = {lead_stage: [] for lead_stage in all_lead_stages}
        for entry in result:
            if entry.get("source") is None:
                entry["source"] = "organic"
            source = entry.get("source", "").lower().replace("-", "_").replace(" ", "_")
            if source not in sources:
                sources[source] = {"source_name": source}
                sources[source].update({stage: 0 for stage in all_lead_stages})
            lead_stage = (
                entry.get("lead_stage", "").lower().replace("-", "_").replace(" ", "_")
            )
            count = entry.get("count")
            paid_application = entry.get("paid_application")
            sources[source].update(
                {
                    lead_stage: count,
                    "paid_application": paid_application
                                        + sources[source].get("paid_application"),
                    "total_leads": count
                                   + sources[source].get("total_leads")
                }
            )
        return all_stages, sources, all_lead_stages

    async def build_pipeline_source_wise_record(
            self,
            date_range,
            change_indicator,
            sort=None,
            sort_type="asc",
            lead_type=None,
            season=None,
            download_function=False,
            cache_change_indicator=None,
            lead_stage_list=None,
            mode=None
    ):
        """
        get source wise record pipeline
        Params:
          - date_range (DateRange): The date range filter if required
          - change_indicator (str): The change indicator value as per requirement
          - sort (bool): True if need to sort else false
          - sort_type (str): asc if need to sort in ascending order else dsc
          - lead_type (str): Filter lead_type if required
          - season (str): The season wise data if required
          - download_function (bool): True if want to download the data else false
        Returns:
          - result (dict): source wise performance of all lead stages
        Raise:
          - Exception : An unexpected error caused in some situation
        """
        headers, sources_result = [{"lead_stage": "source_name", "sub_stage": []}], []
        final_result = {}
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
        else:
            start_date, end_date = None, None
        all_stages, sources, all_lead_stages = await self.get_source_wise_details(
            start_date=start_date, end_date=end_date, season=season, lead_stage_list=lead_stage_list,
            mode=mode, lead_type=lead_type
        )
        pipeline = [
            {
                "$lookup": {
                    "from": "leadsFollowUp",
                    "localField": "_id",
                    "foreignField": "student_id",
                    "as": "leads",
                }
            },
            {"$unwind": {"path": "$leads"}},
            {"$match": {"leads.lead_stage_label": {"$nin": [None, ""]}}},
            {
                "$group": {
                    "_id": {
                        "source": "$source.primary_source.utm_source",
                        "lead_stage": "$leads.lead_stage",
                        "lead_stage_label": "$leads.lead_stage_label",
                    },
                    "count": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "source": "$_id.source",
                    "lead_stage": "$_id.lead_stage",
                    "lead_stage_label": "$_id.lead_stage_label",
                    "count": 1,
                }
            },
        ]
        if lead_type:
            pipeline.insert(0, {"$match": {"source.primary_source.lead_type": lead_type.lower()}})
        result = (
            await DatabaseConfiguration(season=season)
            .studentsPrimaryDetails.aggregate(pipeline)
            .to_list(None)
        )
        for entry in result:
            if entry.get("source") is None:
                entry["source"] = "organic"
            source = entry.get("source", "").lower().replace("-", "_").replace(" ", "_")
            lead_stage = (
                entry.get("lead_stage", "").lower().replace("-", "_").replace(" ", "_")
            )
            lead_stage_label = (
                entry.get("lead_stage_label", "")
                .lower()
                .replace("-", "_")
                .replace(" ", "_")
                .replace("___", "_")
            )
            count = entry.get("count")
            if all_stages.get(lead_stage) and lead_stage_label not in all_stages[lead_stage]:
                all_stages[lead_stage].append(lead_stage_label)
            if source in sources:
                sources[source].update({lead_stage_label: count})
            else:
                sources[source] = {lead_stage_label: count}
        for stage, sub_stages in all_stages.items():
            headers.append({"lead_stage": stage, "sub_stage": sub_stages})
            for source in sources:
                for sub in sub_stages:
                    sources[source].update({sub: 0})
        all_lead_stages.insert(0, "source_name")
        cache_ci_key, ci_data = None, None
        if cache_change_indicator:
            cache_ci_key, ci_data = cache_change_indicator
        if ci_data:
            prev_doc, curr_doc, keys = ci_data.get("prev_data", {}), ci_data.get("curr_doc", {}), ci_data.get("keys",
                                                                                                              [])
        else:
            prev_doc, curr_doc, keys = await self.get_source_percentage_details(
                change_indicator, sources, season=season
            )
            if cache_ci_key:
                await insert_data_in_cache(cache_ci_key, {"prev_doc": prev_doc, "curr_doc": curr_doc, "keys": keys},
                                           change_indicator=True)
        for lead_name in sources:
            prev_data = prev_doc.get(lead_name, {})
            curr_data = curr_doc.get(lead_name, {})
            for key in keys:
                prev_value = prev_data.get(key, 0)
                curr_value = curr_data.get(key, 0)
                diff = await utility_obj.get_percentage_difference_with_position(
                    prev_value, curr_value
                )
                sources[lead_name].update(
                    {
                        f"{key}_perc": diff.get("percentage"),
                        f"{key}_position": diff.get("position"),
                    }
                )
        for source in sources:
            sources_result.append(sources[source])
        try:
            if sort:
                sources_result = (
                    sorted(sources_result, key=lambda x: x[sort], reverse=True)
                    if sort_type == "dsc"
                    else sorted(sources_result, key=lambda x: x[sort])
                )
        except KeyError:
            raise HTTPException(status_code=404, detail="No such key to sort")
        if download_function:
            return sources_result
        final_sources_result, total_sub = [], {
            "source_name": {"value": "Total", "sub_stage_data": {}}
        }
        for sources in sources_result:
            updated_sources = {}
            for source, value in sources.items():
                if source in all_lead_stages:
                    sources[source] = {"value": value}
                    if source != "source_name":
                        if source in total_sub:
                            total_sub[source]["value"] = (
                                    total_sub[source]["value"] + value
                            )
                        else:
                            total_sub.update({source: {"value": value}})
                    if source in [
                        "paid_application",
                        "fresh_lead",
                        "interested",
                        "admission_confirmed",
                    ]:
                        sources[source].update(
                            {
                                "position": sources[f"{source}_position"],
                                "percentage": sources[f"{source}_perc"],
                            }
                        )
                    if source not in ["paid_application"]:
                        present_sub_stages = all_stages.get(source, [])
                        for present_sub in present_sub_stages:
                            if "sub_stage_data" not in sources[source]:
                                sources[source]["sub_stage_data"] = {
                                    present_sub: sources[present_sub]
                                }
                            else:
                                sources[source]["sub_stage_data"].update(
                                    {present_sub: sources[present_sub]}
                                )
                            if source != "source_name":
                                if "sub_stage_data" not in total_sub[source]:
                                    total_sub[source]["sub_stage_data"] = {
                                        present_sub: sources[present_sub]
                                    }
                                else:
                                    if (
                                            present_sub
                                            in total_sub[source]["sub_stage_data"]
                                    ):
                                        total_sub[source]["sub_stage_data"].update(
                                            {
                                                present_sub: total_sub[source][
                                                                 "sub_stage_data"
                                                             ][present_sub]
                                                             + sources[present_sub]
                                            }
                                        )
                                    else:
                                        total_sub[source]["sub_stage_data"].update(
                                            {present_sub: sources[present_sub]}
                                        )
                    if "sub_stage_data" not in sources[source]:
                        sources[source]["sub_stage_data"] = {}
                    if "sub_stage_data" not in total_sub[source]:
                        total_sub[source]["sub_stage_data"] = {}
                    updated_sources.update({source: sources[source]})
            final_sources_result.append(updated_sources)
        final_result.update(
            {"headers": headers, "data": final_sources_result, "total": [total_sub]}
        )
        return final_result

    async def get_source_number(self, source_name, utm_name, current_data):
        """
        Get source number of inter_school
        """
        return next(
            (
                source.get(source_name)
                for source in current_data
                if source.get("utm_source") == utm_name
            ),
            0,
        )

    async def get_source_percentage_details(
            self, change_indicator, final_result, season=None
    ):
        """
        Get source wise details percentage and compare
        Params:
            - change_indicator (str): The change indicator value as per requirement
            - final_result (dict): The result dict that is to be updated
            - season (str): Used to get season wise data
        Returns:
            - final_result (dict): updated result dict
        """
        previous_start_date, previous_end_date, current_start_date = (
            await utility_obj.get_start_date_and_end_date_by_change_indicator(
                change_indicator
            )
        )
        previous_start_date, previous_end_date = await utility_obj.date_change_format(
            str(previous_start_date), str(previous_end_date)
        )
        current_start_date, current_end_date = await utility_obj.date_change_format(
            str(current_start_date), str(datetime.date.today())
        )
        pipeline = [
            {"$project": {"_id": 1, "source": 1}},
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "localField": "_id",
                    "foreignField": "student_id",
                    "as": "student_application",
                }
            },
            {
                "$unwind": {
                    "path": "$student_application",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            {
                "$lookup": {
                    "from": "leadsFollowUp",
                    "localField": "student_application._id",
                    "foreignField": "application_id",
                    "as": "lead_source",
                }
            },
            {"$unwind": {"path": "$lead_source", "preserveNullAndEmptyArrays": True}},
            {
                "$match": {
                    "lead_source.followup.followup_date": {
                        "$gte": previous_start_date,
                        "$lte": previous_end_date,
                    },
                    "student_application.payment_info.created_at": {
                        "$gte": previous_start_date,
                        "$lte": previous_end_date,
                    },
                }
            },
            {
                "$group": {
                    "_id": "$source.primary_source.utm_source",
                    "students": {"$addToSet": "$_id"},
                    "student": {
                        "$push": {
                            "lead_stage": {
                                "$ifNull": ["$lead_source.lead_stage", "Fresh Lead"]
                            },
                            "paid_application": {
                                "$cond": [
                                    {
                                        "$eq": [
                                            "$student_application.payment_info.status",
                                            "captured",
                                        ]
                                    },
                                    1,
                                    0,
                                ]
                            },
                            "fresh_lead": {
                                "$cond": [
                                    {
                                        "$eq": [
                                            "$lead_source.lead_stage",
                                            "Fresh Lead",
                                        ]
                                    },
                                    1,
                                    0,
                                ]
                            },
                            "interested_lead": {
                                "$cond": [
                                    {"$eq": ["$lead_source.lead_stage", "Interested"]},
                                    1,
                                    0,
                                ]
                            },
                            "followup": {
                                "$cond": [
                                    {"$eq": ["$lead_source.lead_stage", "Follow-up"]},
                                    1,
                                    0,
                                ]
                            },
                            "admission_confirmed": {
                                "$cond": [
                                    {
                                        "$eq": [
                                            "$lead_source.lead_stage",
                                            "Admission confirmed",
                                        ]
                                    },
                                    1,
                                    0,
                                ]
                            },
                        }
                    },
                }
            },
            {
                "$project": {
                    "lead_name": "$_id",
                    "paid_application": {"$sum": "$student.paid_application"},
                    "fresh_lead": {"$sum": "$student.fresh_lead"},
                    "interested": {"$sum": "$student.interested_lead"},
                    "followup": {"$sum": "$student.followup"},
                    "admission_confirmed": {"$sum": "$student.admission_confirmed"},
                }
            },
        ]
        prev_doc, curr_doc = {}, {}
        result = DatabaseConfiguration(season=season).studentsPrimaryDetails.aggregate(
            pipeline
        )
        async for doc in result:
            if doc["lead_name"] is None:
                doc["lead_name"] = "None"
            prev_doc.update({doc["lead_name"]: doc})
        pipeline[5].get("$match")["lead_source.followup.followup_date"] = {
            "$gte": current_start_date,
            "$lte": current_end_date,
        }
        result = DatabaseConfiguration(season=season).studentsPrimaryDetails.aggregate(
            pipeline
        )
        async for doc in result:
            if doc["lead_name"] is None:
                doc["lead_name"] = "None"
            curr_doc.update({doc["lead_name"]: doc})
        keys = ["paid_application", "fresh_lead", "interested", "admission_confirmed"]
        return prev_doc, curr_doc, keys

    async def source_wise_application(
            self,
            date_range=None,
            sort=None,
            sort_type="asc",
            lead_type=None,
            season=None,
            change_indicator=None,
            download_function=False,
            cache_change_indicator=None,
            lead_stage_list=None,
            mode=None
    ):
        """
        Get source_wise application details
        """
        result = await self.build_pipeline_source_wise_record(
            date_range,
            change_indicator,
            sort=sort,
            sort_type=sort_type,
            lead_type=lead_type,
            season=season,
            download_function=download_function,
            cache_change_indicator=cache_change_indicator,
            lead_stage_list=lead_stage_list,
            mode=mode
        )
        return result

    async def add_application_id_to_list(self, result):
        """
        Store student email ids in the list
        :param result: description="Result which we get after perform aggregation on the collection named studentApplicationForms"
        """
        application_ids = [str(data.get("_id")) async for data in result]
        if len(application_ids) > 200:
            raise HTTPException(
                status_code=400, detail="You can download atmost 200 data."
            )
        return application_ids

    async def get_application_ids(
            self,
            payload,
            date_range,
            publisher=False,
            user=None,
            form_initiated=True,
            twelve_score_sort=None,
    ):
        """
        Get application ids
        """
        result = await Application().get_aggregation_result(
            date_range,
            payload,
            publisher,
            user,
            form_initiated=form_initiated,
            twelve_score_sort=twelve_score_sort,
        )
        application_ids = await self.add_application_id_to_list(result=result)
        return application_ids

    async def get_lead_detail_by_number(self, mobile_number, user, college_id):
        """
        Get lead data based on mobile number
        """
        result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            [
                {"$match": {"college_id": college_id}},
                {"$project": {"_id": 1, "basic_details": 1}},
            ]
        )
        denied_metrics = [re.compile(mobile_number), re.compile(f"{mobile_number}$")]
        return [
            {
                "student_id": str(student_data.get("_id")),
                "student_name": utility_obj.name_can(student_data.get("basic_details")),
                "student_mobile_no": student_data.get("basic_details", {}).get(
                    "mobile_number"
                ),
            }
            async for student_data in result
            if any(
                dm.search(
                    str(student_data.get("basic_details", {}).get("mobile_number", ""))
                )
                for dm in denied_metrics
            )
        ]

    async def get_application_funnel_data(
            self,
            college_id,
            date_range=None,
            source=None,
            counselor_id=None,
            season=None,
            is_head_counselor=False,
    ):
        """
        get application funnel data
        params:
        current_user
        college_id (str): unique college id
        data_range (date): Used as filter
        source (list): source filter
        user_counselor (bool): if this is true then the user is counselor related else admin
        return:
          result
        """
        total_lead = {"college_id": ObjectId(college_id)}
        application = {"college_id": ObjectId(college_id), "current_stage": {"$gte": 2}}
        if counselor_id or is_head_counselor:
            total_lead.update(
                {"allocate_to_counselor.counselor_id": {"$in": counselor_id}}
            )
            application.update(
                {"allocate_to_counselor.counselor_id": {"$in": counselor_id}}
            )
        start_date, end_date = None, None
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
            total_lead.update({"created_at": {"$gte": start_date, "$lte": end_date}})
            application.update(
                {"payment_info.created_at": {"$gte": start_date, "$lte": end_date}}
            )
        if source:
            student_ids = await Student().get_students_based_on_source(
                source=source, season=season
            )
            application.update({"student_id": {"$in": student_ids}})
            total_lead["source.primary_source.utm_source"] = {"$in": source}
        application.update({"payment_info.status": "captured"})
        paid_application = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.pop("payment_info.status")
        if date_range:
            application.pop("payment_info.created_at")
            application.update({"enquiry_date": {"gte": start_date, "$lte": end_date}})
        application.update({"declaration": True})
        form_submitted = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        total_leads = await DatabaseConfiguration(
            season=season
        ).studentsPrimaryDetails.count_documents(total_lead)
        total_lead.update({"is_verify": True})
        verify_leads = await DatabaseConfiguration(
            season=season
        ).studentsPrimaryDetails.count_documents(total_lead)
        verified_leads_perc = utility_obj.get_percentage_result(
            verify_leads, total_leads
        )
        verified_paid_app_perc = utility_obj.get_percentage_result(
            paid_application, verify_leads
        )
        submitted_paid_app_perc = utility_obj.get_percentage_result(
            form_submitted, paid_application
        )
        data = {
            "total_leads": total_leads,
            "verified_leads": verify_leads,
            "paid_applications": paid_application,
            "submitted_applications": form_submitted,
            "enrollments": 0,
            "verified_leads_perc": round(verified_leads_perc, 2),
            "verified_paid_app_perc": round(verified_paid_app_perc, 2),
            "submitted_paid_app_perc": round(submitted_paid_app_perc, 2),
            "submitted_enrolments_perc": 0,
        }
        return data

    async def get_key_indicators_data_based_on_change_indicator(
            self, college_id, change_indicator, data, application, season=None
    ):
        """
        get the key indicator section change indicator values
        Params:
        college_id(str): Unique college id
        change_indicator (str) : This can have values last_7_days/last_15_days/last_30_days
        data (dict) : The result dict which is need to be updated
        application (dict): The filters which are to be used
        season : To get season wise data
        """
        application.update(
            {"college_id": ObjectId(college_id), "current_stage": {"$gte": 2}}
        )
        start_date, middle_date, previous_date = (
            await utility_obj.get_start_date_and_end_date_by_change_indicator(
                change_indicator
            )
        )
        previous_start_date, previous_end_date = await utility_obj.date_change_format(
            str(start_date), str(middle_date)
        )
        current_start_date, current_end_date = await utility_obj.date_change_format(
            str(previous_date), str(today)
        )
        application.update(
            {
                "payment_initiated": True,
                "payment_info.status": {"$ne": "captured"},
                "enquiry_date": {
                    "$gte": previous_start_date,
                    "$lte": previous_end_date,
                },
            }
        )
        previous_payment_initiated_applications = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.update(
            {
                "enquiry_date": {
                    "$gte": current_start_date,
                    "$lte": current_end_date,
                }
            }
        )
        current_payment_initiated_applications = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        init_application = await utility_obj.get_percentage_difference_with_position(
            previous_payment_initiated_applications,
            current_payment_initiated_applications,
        )
        data.update(
            {
                "payment_init_perc": init_application.get("percentage"),
                "payment_init_position": init_application.get("position"),
            }
        )
        application.pop("payment_initiated")
        application.pop("payment_info.status")
        application.update(
            {
                "current_stage": {"$gte": 7},
                "payment_info.created_at": {
                    "$gte": previous_start_date,
                    "$lte": previous_end_date,
                },
            }
        )
        previous_application_gte_seventy = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.update(
            {
                "payment_info.created_at": {
                    "$gte": current_start_date,
                    "$lte": current_end_date,
                }
            }
        )
        current_application_gte_seventy = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        seventy_application = await utility_obj.get_percentage_difference_with_position(
            previous_application_gte_seventy, current_application_gte_seventy
        )
        data.update(
            {
                "app_completed_perc": seventy_application.get("percentage"),
                "app_completed_position": seventy_application.get("position"),
            }
        )
        application.pop("current_stage")
        application.update(
            {
                "approval_status": "Selected",
                "payment_info.created_at": {
                    "$gte": previous_start_date,
                    "$lte": previous_end_date,
                },
            }
        )
        previous_application_selected = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.update(
            {
                "payment_info.created_at": {
                    "$gte": current_start_date,
                    "$lte": current_end_date,
                }
            }
        )
        current_application_selected = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        selected_application = (
            await utility_obj.get_percentage_difference_with_position(
                previous_application_selected, current_application_selected
            )
        )
        data.update(
            {
                "selected_app_perc": selected_application.get("percentage"),
                "selected_app_position": selected_application.get("position"),
            }
        )
        application.pop("approval_status")
        application.update(
            {
                "feedback.status": "Shortlisted",
                "payment_info.created_at": {
                    "$gte": previous_start_date,
                    "$lte": previous_end_date,
                },
            }
        )
        previous_application_shortlisted = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.update(
            {
                "payment_info.created_at": {
                    "$gte": current_start_date,
                    "$lte": current_end_date,
                }
            }
        )
        current_application_shortlisted = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        shortlisted_application = (
            await utility_obj.get_percentage_difference_with_position(
                previous_application_shortlisted, current_application_shortlisted
            )
        )
        data.update(
            {
                "shortlisted_app_perc": shortlisted_application.get("percentage"),
                "shortlisted_app_position": shortlisted_application.get("position"),
            }
        )
        application.pop("feedback.status")
        return data

    async def get_key_indicators(
            self, college_id, program_name=None, change_indicator=None, season=None
    ):
        """
        get key indicators for  admin dashboard
        param:
        college_id (str): unique id of the college
        program_name (dict) : course_name and spec_name for filter
        change_indicator(str): this might have values last_7_days/last_15_days/last_30_days
        season : season to get season wise data
        """
        data = {}
        application = {"college_id": ObjectId(college_id), "current_stage": {"$gte": 2}}
        if program_name:
            course_filter = [
                {
                    "course_id": ObjectId(prog.get("course_id")),
                    "spec_name1": prog.get("course_specialization"),
                }
                for prog in program_name
            ]
            application.update({"$or": course_filter})
        application.update(
            {"payment_initiated": True, "payment_info.status": {"$ne": "captured"}}
        )
        payment_initiated_applications = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.pop("payment_initiated")
        application.update({"payment_info.status": "failed"})
        payment_failed_applications = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.pop("payment_info.status")
        application.update({"current_stage": {"$gte": 7}})
        application_gte_seventy = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.pop("current_stage")
        application.update({"approval_status": "Selected"})
        applications_selected = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.pop("approval_status")
        application.update({"offer_letter": {"$exists": True}})
        applications_offer_letter = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.pop("offer_letter")
        application.update({"feedback.status": "Shortlisted"})
        applications_shortlisted = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.count_documents(application)
        application.pop("feedback.status")
        pipeline = [{"$match": {"status": {"$in": ["TO DO", "IN PROGRESS"]}}}]
        if program_name:
            query_course = [
                {
                    "student_application.course_id": ObjectId(prog.get("course_id")),
                    "student_application.spec_name1": prog.get("course_specialization"),
                }
                for prog in program_name
            ]
            temp_pipeline = [
                {
                    "$lookup": {
                        "from": "studentApplicationForms",
                        "localField": "student_id",
                        "foreignField": "student_id",
                        "as": "student_application",
                    }
                },
                {"$unwind": {"path": "$student_application"}},
                {"$match": {"$or": query_course}},
            ]
            pipeline.extend(temp_pipeline)
        pipeline.append({"$count": "count"})
        open_query = (
            await DatabaseConfiguration(season=season)
            .queries.aggregate(pipeline)
            .to_list(None)
        )
        open_query = open_query[0].get("count") if open_query else 0
        data.update(
            {
                "payment_init": payment_initiated_applications,
                "total_payment_failed": payment_failed_applications,
                "live_applicants": 0,
                "applications_completed": application_gte_seventy,
                "selected_students": applications_selected,
                "offer_letter_sent": applications_offer_letter,
                "open_queries": open_query,
                "shortlisted_applications": applications_shortlisted,
            }
        )
        if change_indicator:
            data = await self.get_key_indicators_data_based_on_change_indicator(
                college_id, change_indicator, data, application, season
            )
        return data

    async def get_student_queries_on_status(
            self, students, status_code, status, counselor_id, result, season=None
    ):
        """
        get student queries depending on given status
        Params:
          students (list): list of student ids  that have to bee checked in
          status_code (str): This can be "TO DO"/"IN PROGRESS"/"DONE"
          status (str): This is the status which is to be added in result
                   This may have valu "open"/"un_resolved"/"resolved"
          counselor_id (Object_id): The unique id of counselor
          result (dict) : Already updated result dict which is to be updated
          query_type (list): The query_type flter
        Returns:
          Result
        """
        query = {"student_id": {"$in": students}, "status": status_code}
        todo_count = await DatabaseConfiguration(season=season).queries.count_documents(
            query
        )
        counselor = await DatabaseConfiguration(
            season=season
        ).studentApplicationForms.find_one(
            {"allocate_to_counselor.counselor_id": counselor_id}
        )
        if counselor_id is not None:
            counselor_name = counselor.get("allocate_to_counselor", {}).get(
                "counselor_name"
            )
            if counselor_name in result.keys():
                result[counselor_name].update({status: todo_count})
            else:
                result.update(
                    {counselor_name: {"_id": str(counselor_id), status: todo_count}}
                )
        return result

    async def get_student_queires(
            self,
            college_id,
            program_name=None,
            date_range=None,
            search=None,
            counselor_id=None,
            season=None,
    ):
        """
        get the student queries considering the filters
        Params:
        college_id (str): unique id of the college
        program_name (dict) : course_name and spec_name for filter
        query_type (list) : this filter is  used tto filter data on query type given
        date_range:
        season : season to get season wise data
        returns:
        result
        """
        pipeline = [
            {
                "$group": {
                    "_id": "$assigned_counselor_id",
                    "counselor_data": {
                        "$push": {
                            "name": "$assigned_counselor_name",
                            "resolved": {"$cond": [{"$eq": ["$status", "DONE"]}, 1, 0]},
                            "un_resolved": {
                                "$cond": [{"$eq": ["$status", "TO DO"]}, 1, 0]
                            },
                            "open": {
                                "$cond": [{"$eq": ["$status", "IN PROGRESS"]}, 1, 0]
                            },
                        }
                    },
                }
            },
            {
                "$project": {
                    "_id": {"$ifNull": [{"$toString": "$_id"}, "None"]},
                    "name": {"$ifNull": [{"$first": "$counselor_data.name"}, "None"]},
                    "resolved": {"$sum": "$counselor_data.resolved"},
                    "un_resolved": {"$sum": "$counselor_data.un_resolved"},
                    "open": {"$sum": "$counselor_data.open"},
                }
            },
        ]
        match = {}
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
            match.update({"created_at": {"$gte": start_date, "$lte": end_date}})
        if program_name:
            program_name_filter = []
            for prog in program_name:
                program_name_filter.append(
                    {
                        "course_name": prog.get("course_name"),
                        "specialization_name": prog.get("course_specialization"),
                    }
                )
            match.update({"$or": program_name_filter})
        if search:
            match.update(
                {
                    "assigned_counselor_name": {
                        "$regex": f".*{search}.*",
                        "$options": "i",
                    }
                }
            )
        if counselor_id:
            counselor_id = [ObjectId(id) for id in counselor_id]
            match.update({"assigned_counselor_id": {"$in": counselor_id}})
        if match:
            pipeline.insert(0, {"$match": match})
        result = (
            await DatabaseConfiguration(season=season)
            .queries.aggregate(pipeline)
            .to_list(None)
        )
        return result

    async def get_student_total_queires_header(
            self, college_id, date_range=None, counselor_id=None, season=None
    ):
        """
        get total student queries
        Params:
          college_id(str): unique id of college
          date_range: Date range filter
          header (bool) : True if header section, false if not
        Retyrms:
          result
        """
        current_date = str(datetime.date.today())
        today_start_date, today_end_date = await utility_obj.date_change_format(
            current_date, current_date
        )
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": today_start_date, "$lte": today_end_date}
                }
            },
            {"$count": "count"},
        ]
        if counselor_id:
            pipeline[0].get("$match").update(
                {"assigned_counselor_id": {"$in": counselor_id}}
            )
        today_queries_list = (
            await DatabaseConfiguration().queries.aggregate(pipeline).to_list(None)
        )
        today_queries = (
            today_queries_list[0].get("count", 0) if today_queries_list else 0
        )
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "count": {
                        "$push": {
                            "unresolved": {
                                "$cond": [
                                    {"$or": [
                                        {"$eq": ["$status", "IN PROGRESS"]},
                                        {"$eq": ["$status", "TO DO"]}
                                      ]}, 1, 0]},
                            "resolved": {"$cond": [{"$eq": ["$status", "DONE"]}, 1, 0]},
                            "open": {"$cond": [{"$eq": ["$status", "TO DO"]}, 1, 0]},
                        }
                    },
                }
            },
            {
                "$project": {
                    "resolved": {"$sum": "$count.resolved"},
                    "unresolved": {"$sum": "$count.unresolved"},
                    "open": {"$sum": "$count.open"},
                }
            },
        ]
        match = {}
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
            match.update({"created_at": {"$gte": start_date, "$lte": end_date}})
        if counselor_id:
            match.update({"assigned_counselor_id": {"$in": counselor_id}})
        if match:
            pipeline.insert(0, {"$match": match})
        all_counts = (
            await DatabaseConfiguration().queries.aggregate(pipeline).to_list(None)
        )
        counts = all_counts[0] if all_counts else {}
        return {
            "today_queries": today_queries,
            "un_resolved": counts.get("unresolved", 0),
            "resolved": counts.get("resolved", 0),
            "open": counts.get("open", 0),
        }

    async def get_student_total_queries(
            self,
            college_id,
            program_name=None,
            query_type=None,
            date_range=None,
            search=None,
            page_num=None,
            page_size=None,
            season=None,
    ):
        """
        get student total queires
        Params:
          college_id(str) : Unique id of college,
          program_name (list): this is a filter. This includes both corse_name,spec_name
          query_type: This is a filter, this may have different types as queries.
          data_range: Data range filter
          search: Retuens the data which is searched for
          page_num: This is used for pagination
          page_size: This is also used for pagination
        """
        query = {}
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get("start_date"), date_range.get("end_date")
            )
            query.update({"created_at": {"$gte": start_date, "$lte": end_date}})
        if program_name:
            application = {}
            course_ids = []
            spec_names = []
            for prog in program_name:
                course_ids.append(ObjectId(prog.get("course_id")))
                spec_names.append(prog.get("course_specialization"))
            application.update(
                {"course_id": {"$in": course_ids}, "spec_name1": {"$in": spec_names}}
            )
            student_app = DatabaseConfiguration(
                season=season
            ).studentApplicationForms.find(application)
            student_ids = [
                doc.get("student_id")
                async for doc in student_app
                if doc.get("student_id")
            ]
            query.update({"student_id": {"$in": student_ids}})
        if query_type:
            query.update({"category_name": {"$in": query_type}})
        pipeline = [
            {
                "$lookup": {
                    "from": "studentsPrimaryDetails",
                    "localField": "student_id",
                    "foreignField": "_id",
                    "as": "studentPrimaryData",
                }
            },
            {"$unwind": "$studentPrimaryData"},
            {
                "$project": {
                    "email_id": "$studentPrimaryData.user_name",
                    "created_at": 1,
                    "updated_at": 1,
                    "ticket_id": 1,
                    "student_name": 1,
                    "category_name": 1,
                    "replies": 1,
                }
            },
        ]
        if query:
            pipeline.append({"$match": query})
        query_docs = DatabaseConfiguration(season=season).queries.aggregate(pipeline)
        result = []
        async for doc in query_docs:
            created_on = doc.get("created_at")
            updated_on = doc.get("updated_at")
            replies = doc.get("replies", [])
            if replies:
                last_reply = replies[-1]
                resolved_on = last_reply.get("timestamp")
                response = last_reply.get("message")
            else:
                resolved_on = None
                response = ""

            sub_result = {
                "query_id": doc.get("ticket_id"),
                "name": doc.get("student_name"),
                "email_id": doc.get("email_id"),
                "category": doc.get("category_name"),
                "created_on": (
                    utility_obj.get_local_time(created_on)
                    if created_on is not None
                    else None
                ),
                "updated_on": (
                    utility_obj.get_local_time(updated_on)
                    if updated_on is not None
                    else None
                ),
                "resolution_time": (
                    utility_obj.get_local_time(resolved_on)
                    if resolved_on is not None
                    else None
                ),
                "response": response,
            }
            result.append(sub_result)
        if search:
            result_search = []
            for doc in result:
                if (
                        search in doc.get("email_id")
                        or search.lower() in doc.get("name").lower()
                ):
                    result_search.append(doc)
            result = result_search

        response = await utility_obj.pagination_in_api(
            page_num,
            page_size,
            result,
            len(result),
            route_name="/admin/student_total_queries/",
        )
        return {
            "data": response.get("data"),
            "total": len(result),
            "count": page_size,
            "pagination": response.get("pagination"),
            "message": "Get student queries.",
        }

    async def student_documents_info(self, item, student_id, season=None):
        """
        Returns document information
        Params:
         item (dict) : Student related information dictionary which has documents data.
        """
        season_year = utility_obj.get_year_based_on_season(season)
        result = {}
        data = item.get("attachments", {})
        aws_env = settings.aws_env
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        base_bucket_url = getattr(settings, f"s3_{aws_env}_base_bucket_url")
        for key in data:
            file_s3_url = data[key].get("file_s3_url", "")
            if file_s3_url:
                if not file_s3_url.startswith("https"):
                    file_s3_url = (
                        f"{base_bucket_url}{utility_obj.get_university_name_s3_folder()}/{season_year}/{settings.s3_student_documents_bucket_name}/"
                        f'{student_id}/{key}/{data[key]["file_s3_url"]}'
                    )
                file_s3_url = settings.s3_client.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": base_bucket,
                        "Key": f"{utility_obj.get_university_name_s3_folder()}/{season_year}/{settings.s3_student_documents_bucket_name}/{student_id}/"
                               f"{key}/{file_s3_url.split('/')[8]}",
                    },
                    ExpiresIn=600,
                )
            file_name = data[key].get("file_name", "")
            status = data[key].get("status", "")
            reupload_count = data[key].get("reupload_count", 0)
            if (document_analysis := item.get("document_analysis")) is None:
                accuracy = ("N/A",)
                count = 0
            else:
                present_doc = (
                    document_analysis.get("high_school_analysis")
                    if key == "tenth"
                    else (
                        document_analysis.get("senior_school_analysis")
                        if key == "inter"
                        else (
                            document_analysis.get("graduation_analysis")
                            if key == "graduation"
                            else {}
                        )
                    )
                )
                if present_doc:
                    ocr_status = present_doc.get("status")
                    accuracy = (
                        "failed"
                        if ocr_status == "Failed"
                        else (
                            "In_progress"
                            if ocr_status == "In Progress"
                            else (
                                present_doc.get("metadata", {}).get("accuracy", "")
                                if ocr_status == "Completed"
                                else "N/A"
                            )
                        )
                    )
                    count = present_doc.get("count", 0)
                else:
                    accuracy = "N/A"
                    count = 0
            comments = data[key].get("comments", [])
            if comments:
                comments = [
                    {
                        "message": comment.get("message", ""),
                        "timestamp": utility_obj.get_local_time(
                            comment.get("timestamp", "")
                        ),
                        "user_name": comment.get("user_name", ""),
                        "user_id": str(comment.get("user_id", "")),
                        "comment_id": _id,
                    }
                    for _id, comment in enumerate(comments)
                ]
            result.update(
                {
                    key: {
                        "file_s3_url": file_s3_url,
                        "file_name": file_name,
                        "status": status,
                        "count": count,
                        "reupload_count": reupload_count,
                        "ocr_accuracy": (
                            round(accuracy, 2)
                            if isinstance(accuracy, float)
                            else accuracy
                        ),
                        "comments": comments,
                    }
                }
            )
        return result

    async def get_assigned_unassigned_details(self, date_range: dict | None) -> dict:
        """
        Get assigned and unassigned details
        Params:
            date_range (Date_range): The is used to apply date range filter.
        Returns:
            dict : The details of assigned and assigned leads
        """
        start_time, end_time = await utility_obj.date_change_format(
            start_date=str(datetime.date.today()),
            end_date=str(datetime.date.today()),
        )
        hours = []
        current_time = start_time
        current_time = current_time.replace(minute=30, second=0, microsecond=0, tzinfo=datetime.timezone.utc)
        while current_time <= end_time.replace(minute=30, second=1):
            hours.append(current_time)
            current_time += datetime.timedelta(hours=1)
        start_date_, middle_date_, previous_date = (
            await utility_obj.get_start_date_and_end_date_by_change_indicator(
                "last_30_days"
            )
        )
        daily_start_date, daily_end_date = await utility_obj.date_change_format(
            str(previous_date), str(today)
        )
        pipeline = [
            {
                '$facet': {
                    'overall_counts': [
                        {
                            '$group': {
                                '_id': None,
                                'total_unassigned': {
                                    '$sum': {
                                        '$cond': [
                                            {
                                                '$not': {
                                                    '$ifNull': [
                                                        '$allocate_to_counselor', False
                                                    ]
                                                }
                                            }, 1, 0
                                        ]
                                    }
                                },
                                'today_unassigned': {
                                    '$sum': {
                                        '$cond': [
                                            {
                                                '$and': [
                                                    {
                                                        '$not': {
                                                            '$ifNull': [
                                                                '$allocate_to_counselor', False
                                                            ]
                                                        }
                                                    }, {
                                                        '$gte': [
                                                            '$enquiry_date', start_time
                                                        ]
                                                    }, {
                                                        '$lte': [
                                                            '$enquiry_date', end_time
                                                        ]
                                                    }
                                                ]
                                            }, 1, 0
                                        ]
                                    }
                                }
                            }
                        }, {
                            '$project': {
                                '_id': 0,
                                'total_unassigned': 1,
                                'today_unassigned': 1
                            }
                        }
                    ],
                    'hourly_counts': [
                        {
                            '$match': {
                                '$or': [
                                    {
                                        'enquiry_date': {
                                            '$gte': start_time,
                                            '$lte': end_time
                                        }
                                    }, {
                                        'allocate_to_counselor.last_update': {
                                            '$gte': start_time,
                                            '$lte': end_time
                                        }
                                    }
                                ]
                            }
                        }, {
                            '$group': {
                                '_id': {
                                    'hour': {
                                        '$hour': '$enquiry_date'
                                    },
                                    'date': {
                                        '$dateToString': {
                                            'format': '%Y-%m-%d',
                                            'date': '$enquiry_date'
                                        }
                                    }
                                },
                                'unassigned_count': {
                                    '$sum': {
                                        '$cond': [
                                            {
                                                '$and': [
                                                    {
                                                        '$not': {
                                                            '$ifNull': [
                                                                '$allocate_to_counselor', False
                                                            ]
                                                        }
                                                    }, {
                                                        '$gte': [
                                                            '$enquiry_date', start_time
                                                        ]
                                                    }, {
                                                        '$lte': [
                                                            '$enquiry_date', end_time
                                                        ]
                                                    }
                                                ]
                                            }, 1, 0
                                        ]
                                    }
                                },
                                'assigned_count': {
                                    '$sum': {
                                        '$cond': [
                                            {
                                                '$and': [
                                                    {
                                                        '$ifNull': [
                                                            '$allocate_to_counselor', False
                                                        ]
                                                    }, {
                                                        '$gte': [
                                                            '$allocate_to_counselor.last_update', start_time
                                                        ]
                                                    }, {
                                                        '$lte': [
                                                            '$allocate_to_counselor.last_update', end_time
                                                        ]
                                                    }
                                                ]
                                            }, 1, 0
                                        ]
                                    }
                                }
                            }
                        }, {
                            '$project': {
                                '_id': 0,
                                'hour': '$_id.hour',
                                'date': {
                                    '$dateToString': {
                                        'format': '%b %d, %Y',
                                        'date': {
                                            '$dateFromString': {
                                                'dateString': '$_id.date'
                                            }
                                        }
                                    }
                                },
                                'unassigned_count': 1,
                                'assigned_count': 1,
                                'total_count': {
                                    '$sum': [
                                        '$unassigned_count', '$assigned_count'
                                    ]
                                }
                            }
                        }, {
                            '$sort': {
                                'date': 1,
                                'hour': 1
                            }
                        }
                    ],
                    'daily_counts': [
                        {
                            '$match': {
                                '$or': [
                                    {
                                        'enquiry_date': {
                                            '$gte': daily_start_date,
                                            '$lte': daily_end_date
                                        }
                                    }, {
                                        'allocate_to_counselor.last_update': {
                                            '$gte': daily_start_date,
                                            '$lte': daily_end_date
                                        }
                                    }
                                ]
                            }
                        }, {
                            '$group': {
                                '_id': {
                                    'day': {
                                        '$dayOfMonth': '$enquiry_date'
                                    },
                                    'month': {
                                        '$month': '$enquiry_date'
                                    },
                                    'year': {
                                        '$year': '$enquiry_date'
                                    }
                                },
                                'unassigned_count': {
                                    '$sum': {
                                        '$cond': [
                                            {
                                                '$and': [
                                                    {
                                                        '$not': {
                                                            '$ifNull': [
                                                                '$allocate_to_counselor', False
                                                            ]
                                                        }
                                                    },
                                                    {
                                                        '$gte': [
                                                            '$enquiry_date',
                                                            daily_start_date
                                                        ]
                                                    }, {
                                                        '$lte': [
                                                            '$enquiry_date',
                                                            daily_end_date
                                                        ]
                                                    }
                                                ]
                                            }, 1, 0
                                        ]
                                    }
                                },
                                'assigned_count': {
                                    '$sum': {
                                        '$cond': [
                                            {
                                                '$and': [
                                                    {
                                                        '$ifNull': [
                                                            '$allocate_to_counselor', False
                                                        ]
                                                    },
                                                    {
                                                        '$gte': [
                                                            '$allocate_to_counselor.last_update',
                                                            daily_start_date
                                                        ]
                                                    }, {
                                                        '$lte': [
                                                            '$allocate_to_counselor.last_update',
                                                            daily_end_date
                                                        ]
                                                    }
                                                ]
                                            }, 1, 0
                                        ]
                                    }
                                }
                            }
                        }, {
                            '$project': {
                                '_id': 0,
                                'date': {
                                    '$dateToString': {
                                        'format': '%b %d, %Y',
                                        'date': {
                                            '$dateFromParts': {
                                                'year': '$_id.year',
                                                'month': '$_id.month',
                                                'day': '$_id.day'
                                            }
                                        }
                                    }
                                },
                                'time': {
                                    '$dateToString': {
                                        'format': '%b %d',
                                        'date': {
                                            '$dateFromParts': {
                                                'year': '$_id.year',
                                                'month': '$_id.month',
                                                'day': '$_id.day'
                                            }
                                        }
                                    }
                                },
                                'unassigned_count': 1,
                                'assigned_count': 1,
                                'total_count': {
                                    '$sum': [
                                        '$unassigned_count', '$assigned_count'
                                    ]
                                }
                            }
                        }, {
                            '$sort': {
                                'date': 1
                            }
                        }
                    ]
                }
            }, {
                '$addFields': {
                    'hourly_counts': {
                        '$concatArrays': [
                            {
                                '$map': {
                                    'input': hours,
                                    'as': 'hour',
                                    'in': {
                                        'date': {
                                            '$dateToString': {
                                                'format': '%b %d, %Y',
                                                'date': '$$hour'
                                            }
                                        },
                                        'hour': {
                                            '$hour': '$$hour'
                                        },
                                        'unassigned_count': 0,
                                        'assigned_count': 0,
                                        'total_count': 0
                                    }
                                }
                            }, '$hourly_counts'
                        ]
                    },
                    'daily_counts': {
                        '$map': {
                            'input': {
                                '$range': [
                                    0, {
                                        '$subtract': [
                                            {
                                                '$dateDiff': {
                                                    'startDate': daily_start_date,
                                                    'endDate': daily_end_date,
                                                    'unit': 'day'
                                                }
                                            }, -1
                                        ]
                                    }
                                ]
                            },
                            'as': 'daysAgo',
                            'in': {
                                '$let': {
                                    'vars': {
                                        'date': {
                                            '$dateAdd': {
                                                'startDate': daily_start_date,
                                                'unit': 'day',
                                                'amount': '$$daysAgo'
                                            }
                                        }
                                    },
                                    'in': {
                                        '$mergeObjects': [
                                            {
                                                'date': {
                                                    '$dateToString': {
                                                        'format': '%b %d, %Y',
                                                        'date': '$$date'
                                                    }
                                                }
                                            }, {
                                                'time': {
                                                    '$dateToString': {
                                                        'format': '%b %d',
                                                        'date': '$$date'
                                                    }
                                                }
                                            }, {
                                                '$arrayElemAt': [
                                                    {
                                                        '$filter': {
                                                            'input': '$daily_counts',
                                                            'as': 'dc',
                                                            'cond': {
                                                                '$eq': [
                                                                    '$$dc.date', {
                                                                        '$dateToString': {
                                                                            'format': '%b %d, %Y',
                                                                            'date': '$$date'
                                                                        }
                                                                    }
                                                                ]
                                                            }
                                                        }
                                                    }, 0
                                                ]
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
            },
            {
                '$facet': {
                    'overall': [
                        {
                            '$group': {
                                '_id': None,
                                'total_unassigned': {
                                    '$first': '$overall_counts.total_unassigned'
                                },
                                'today_unassigned': {
                                    '$first': '$overall_counts.today_unassigned'
                                }
                            }
                        }, {
                            '$unwind': '$total_unassigned'
                        }, {
                            '$unwind': '$today_unassigned'
                        }
                    ],
                    'total': [
                        {
                            '$unwind': '$hourly_counts'
                        },
                        {
                            '$group': {
                                '_id': {
                                    'hour': '$hourly_counts.hour'
                                },
                                'date': {"$first": '$hourly_counts.date'},
                                'unassigned_count': {
                                    '$sum': '$hourly_counts.unassigned_count'
                                },
                                'assigned_count': {
                                    '$sum': '$hourly_counts.assigned_count'
                                },
                                'total_count': {
                                    '$sum': '$hourly_counts.total_count'
                                }
                            }
                        }, {
                            '$project': {
                                '_id': 0,
                                'date': '$date',
                                'time': '$_id.hour',
                                'unassigned_count': 1,
                                'assigned_count': 1,
                                'total_count': 1
                            }
                        }, {
                            '$sort': {
                                'time': 1
                            }
                        }
                    ],
                    'daily': [
                        {
                            '$project': {
                                'daily_counts': '$daily_counts'
                            }
                        }
                    ]
                }
            }, {
                '$unwind': {
                    'path': '$overall'
                }
            },
            {
                '$unwind': {
                    'path': '$daily'
                }
            },
            {
                '$project': {
                    'total_unassigned_count': '$overall.total_unassigned',
                    'today_unassigned_count': '$overall.today_unassigned',
                    'today_assigned_and_unassigned': '$total',
                    'total_assigned_and_unassigned': '$daily.daily_counts'
                }
            }
        ]
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                start_date=date_range.get("start_date"),
                end_date=date_range.get("end_date")
            )
        results = await DatabaseConfiguration().studentApplicationForms.aggregate(pipeline).to_list(None)
        results = results[0] if results else {}
        utc_to_local = utility_obj.get_local_hour_utc_hour_dict()
        latest_date = max(doc.get('date') for doc in results.get('today_assigned_and_unassigned', {}))
        for res in results.get("total_assigned_and_unassigned", []):
            if "unassigned_count" not in res:
                res.update({
                    "unassigned_count": 0,
                    "assigned_count": 0,
                    "total_count": 0
                })
        for local, utc in utc_to_local.items():
            for res in results.get("today_assigned_and_unassigned", {}):
                if res.get("time") == utc:
                    res["time"] = local
                    res["date"] = latest_date
        results.update({"message": "Fetched assigned and unassigned details"})
        return results

    async def get_exclusion_list_headers(self):
        """
        Return Exclusion list Headers
        Params:
            None
        Return:
            dict: Details of exclusion list
        """
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'excluded': {
                        '$sum': {
                            '$cond': [
                                {
                                    '$eq': [
                                        '$unsubscribe.excluded', True
                                    ]
                                }, 1, 0
                            ]
                        }
                    },
                    'current_excluded': {
                        '$sum': {
                            '$cond': [
                                {
                                    '$eq': [
                                        '$unsubscribe.value', True
                                    ]
                                }, 1, 0
                            ]
                        }
                    }
                }
            }, {
                '$addFields': {
                    'resumed': {
                        '$subtract': [
                            '$excluded', '$current_excluded'
                        ]
                    },
                    'email_excluded': '$current_excluded',
                    'whatsapp_excluded': 0
                }
            }
        ]
        data = await DatabaseConfiguration().studentsPrimaryDetails.aggregate(pipeline).to_list(None)
        return data[0] if data else {}

    async def get_exclusion_students_list(self, filters: dict, page_num: int, page_size: int) -> tuple:
        """
        Return Exclusion list
        Params:
            filters (dict): Dict of filters
            page_num (int): Page number
            page_size (int): Page Size
        Return:
            Tuple: Details of exclusion list
        """
        pipeline = [
            {
                '$addFields': {
                    'excludedhourIST': {
                        '$add': [
                            {
                                '$hour': {
                                    'date': '$unsubscribe.excluded_timestamp',
                                    'timezone': 'Asia/Kolkata'
                                }
                            }, 0
                        ]
                    },
                    'excludedminuteIST': {
                        '$dateToString': {
                            'format': '%M',
                            'date': '$unsubscribe.excluded_timestamp',
                            'timezone': 'Asia/Kolkata'
                        }
                    },
                    'excludedsecondIST': {
                        '$dateToString': {
                            'format': '%S',
                            'date': '$unsubscribe.excluded_timestamp',
                            'timezone': 'Asia/Kolkata'
                        }
                    },
                    'releasehourIST': {
                        '$add': [
                            {
                                '$hour': {
                                    'date': '$unsubscribe.release_date',
                                    'timezone': 'Asia/Kolkata'
                                }
                            }, 0
                        ]
                    },
                    'releaseminuteIST': {
                        '$dateToString': {
                            'format': '%M',
                            'date': '$unsubscribe.release_date',
                            'timezone': 'Asia/Kolkata'
                        }
                    },
                    'releasesecondIST': {
                        '$dateToString': {
                            'format': '%S',
                            'date': '$unsubscribe.release_date',
                            'timezone': 'Asia/Kolkata'
                        }
                    }
                }
            }, {
                '$addFields': {
                    'excludedformatted_hour': {
                        '$cond': {
                            'if': {
                                '$eq': [
                                    '$excludedhourIST', 0
                                ]
                            },
                            'then': 12,
                            'else': {
                                '$cond': {
                                    'if': {
                                        '$eq': [
                                            '$excludedhourIST', 12
                                        ]
                                    },
                                    'then': 12,
                                    'else': {
                                        '$mod': [
                                            '$excludedhourIST', 12
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    'excludedAMPM': {
                        '$cond': [
                            {
                                '$lt': [
                                    '$excludedhourIST', 12
                                ]
                            }, 'AM', 'PM'
                        ]
                    },
                    'releaseformatted_hour': {
                        '$cond': {
                            'if': {
                                '$eq': [
                                    '$releasehourIST', 0
                                ]
                            },
                            'then': 12,
                            'else': {
                                '$cond': {
                                    'if': {
                                        '$eq': [
                                            '$releasehourIST', 12
                                        ]
                                    },
                                    'then': 12,
                                    'else': {
                                        '$mod': [
                                            '$releasehourIST', 12
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    'releaseAMPM': {
                        '$cond': [
                            {
                                '$lt': [
                                    '$releasehourIST', 12
                                ]
                            }, 'AM', 'PM'
                        ]
                    }
                }
            }, {
                '$addFields': {
                    'excluded_on': {
                        '$concat': [
                            {
                                '$toString': {
                                    '$dayOfMonth': {
                                        'date': '$unsubscribe.excluded_timestamp',
                                        'timezone': 'Asia/Kolkata'
                                    }
                                }
                            }, ' ', {
                                '$dateToString': {
                                    'format': '%b %Y',
                                    'date': '$unsubscribe.excluded_timestamp',
                                    'timezone': 'Asia/Kolkata'
                                }
                            }, ' ', {
                                '$toString': '$excludedformatted_hour'
                            }, ':', '$excludedminuteIST', ':', '$excludedsecondIST', ' ', '$excludedAMPM'
                        ]
                    },
                    'release_date': {
                        '$concat': [
                            {
                                '$toString': {
                                    '$dayOfMonth': {
                                        'date': '$unsubscribe.release_date',
                                        'timezone': 'Asia/Kolkata'
                                    }
                                }
                            }, ' ', {
                                '$dateToString': {
                                    'format': '%b %Y',
                                    'date': '$unsubscribe.release_date',
                                    'timezone': 'Asia/Kolkata'
                                }
                            }, ' ', {
                                '$toString': '$releaseformatted_hour'
                            }, ':', '$releaseminuteIST', ':', '$releasesecondIST', ' ', '$releaseAMPM'
                        ]
                    }
                }
            }, {
                '$lookup': {
                    'from': 'data_segment_student_mapping',
                    'let': {
                        'student_id': '$_id'
                    },
                    'pipeline': [
                        {
                            '$match': {
                                '$expr': {
                                    '$eq': [
                                        '$$student_id', '$student_id'
                                    ]
                                }
                            }
                        }, {
                            '$project': {
                                '_id': 0,
                                'student_id': 1,
                                'automation': {
                                    '$size': {
                                        '$ifNull': [
                                            '$automation_id', []
                                        ]
                                    }
                                },
                                'automation_ids': {
                                    '$ifNull': [
                                        '$automation_id', []
                                    ]
                                },
                                'automation_names': {
                                    '$ifNull': [
                                        '$automation_names', []
                                    ]
                                }
                            }
                        }, {
                            '$group': {
                                '_id': '$student_id',
                                'automation': {
                                    '$sum': {
                                        '$ifNull': [
                                            '$automation', 0
                                        ]
                                    }
                                },
                                'automation_id': {
                                    '$push': '$automation_ids'
                                },
                                'automation_names': {
                                    '$push': '$automation_names'
                                }
                            }
                        }
                    ],
                    'as': 'automation_details'
                }
            }, {
                '$unwind': {
                    'path': '$automation_details',
                    'preserveNullAndEmptyArrays': True
                }
            }, {
                '$addFields': {
                    'automation_id': {
                        '$reduce': {
                            'input': '$automation_details.automation_id',
                            'initialValue': [],
                            'in': {
                                '$concatArrays': [
                                    '$$value', '$$this'
                                ]
                            }
                        }
                    }
                }
            }, {
                '$lookup': {
                    'from': 'rule',
                    'localField': 'automation_id',
                    'foreignField': '_id',
                    'as': 'rules'
                }
            }, {
                '$addFields': {
                    'automation_names': {
                        '$map': {
                            'input': '$rules',
                            'as': 'rule',
                            'in': '$$rule.rule_name'
                        }
                    }
                }
            }
        ]
        project = {
            '_id': 0,
            "student_id": {"$toString": "$_id"},
            'email': '$user_name',
            'name': {
                '$trim': {
                    'input': {
                        '$concat': [
                            '$basic_details.first_name', ' ', {
                                '$ifNull': [
                                    '$basic_details.middle_name', ''
                                ]
                            }, ' ', '$basic_details.last_name'
                        ]
                    }
                }
            },
            'excluded_on': '$excluded_on',
            'automation': {
                '$ifNull': [
                    '$automation_details.automation', 0
                ]
            },
            "present_unsubscribed": "$unsubscribe.value",
            'automation_names': '$automation_names',
            'template_id': {
                '$toString': {
                    '$ifNull': [
                        '$unsubscribe.template_id', 'None'
                    ]
                }
            },
            'template_name': {
                '$ifNull': [
                    '$unsubscribe.template_name', ''
                ]
            },
            'release_date': '$release_date',
            'sender_id': {
                '$ifNull': [
                    '$unsubscribe.user_name', ''
                ]
            },
            'exclusion_category': {
                '$ifNull': [
                    '$unsubscribe.category', ''
                ]
            },
            'unsubscribe_reason': {
                '$ifNull': [
                    '$unsubscribe.reason', ''
                ]
            },
            "totalCount": 1
        }
        early_match, match, app_stage, limited = {}, {}, None, False
        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
        if filters:
            if (app_stage := filters.get("application_stage")) not in [None, ""]:
                pipeline.append(
                    {
                        "$lookup": {
                            "from": "studentApplicationForms",
                            "localField": "_id",
                            "foreignField": "student_id",
                            "as": "applications",
                        }
                    }
                )
                project.update({
                    "application_status": {
                        "$map": {
                            "input": "$applications",
                            "as": "app",
                            "in": {
                                "$cond": {
                                    "if": "$$app.declaration",
                                    "then": "Completed",
                                    "else": "In progress",
                                }
                            },
                        }
                    }
                })
                match.update({
                    "application_status": "Completed" if app_stage.lower() == "completed" else "In progress"
                })
            if (category := filters.get("exclusion_category")) not in [None, "", []]:
                early_match.update({
                    "unsubscribe.category": {"$in": category}
                })
            if (lead_stages := filters.get("lead_stage")) not in [None, "", []]:
                pipeline.extend([
                    {
                        "$lookup": {
                            "from": "leadsFollowUp",
                            "localField": "_id",
                            "foreignField": "student_id",
                            "as": "lead_details",
                        }
                    },
                    {
                        "$match": {
                          "lead_details.lead_stage": {"$in": lead_stages}
                        }
                    }
                ])
            if (automations := filters.get("automation")) not in [None, "", []]:
                automations = [ObjectId(automation) for automation in automations if ObjectId.is_valid(automation)]
                pipeline.append({
                    "$match": {
                        "automation_id": {"$in": automations}
                    }
                })
            if (sources := filters.get("source_list")) not in [None, "", []]:
                early_match.update({
                    "source.primary_source.utm_source": {"$in": sources}
                })
            if (mediums := filters.get("utm_medium")) not in [None, "", []]:
                for medium in mediums:
                    early_match.update({
                        "source.primary_source.utm_medium": medium.get("utm_medium"),
                        "source.primary_source.utm_source": medium.get("source_name")
                    })
            if (state := filters.get("state")) not in [None, "", []]:
                early_match.update({
                    "address_details.communication_address.state.state_code": {"$in": state}
                })
            if (programs := filters.get("program_name")) not in [None, "", []]:
                app_program_filter = []
                for program in programs:
                    app_program_filter.append(
                        {
                            "$and": [
                                {"applications.course_id": ObjectId(program.get("course_id"))},
                                {"applications.spec_name1": program.get("course_specialization")},
                            ]
                        }
                    )
                if not app_stage:
                    pipeline.append({
                        "$lookup": {
                            "from": "studentApplicationForms",
                            "localField": "_id",
                            "foreignField": "student_id",
                            "as": "applications",
                        }
                    })
                pipeline.append({"$match": {"$or": app_program_filter}})
            if (templates := filters.get("templateName")) not in [None, "", []]:
                templates = [ObjectId(temp) for temp in templates if ObjectId.is_valid(temp)]
                early_match.update({
                    "unsubscribe.template_id": {"$in": templates}
                })
            if (search := filters.get("search")):
                early_match.update({
                        "$or": [
                            {"basic_details.first_name": {"$regex": f".*{search}.*", "$options": "i"}},
                            {"basic_details.middle_name": {"$regex": f".*{search}.*", "$options": "i"}},
                            {"basic_details.last_name": {"$regex": f".*{search}.*", "$options": "i"}},
                            {"user_name": {"$regex": f".*{search}.*", "$options": "i"}},
                            {"basic_details.mobile_number": {"$regex": f".*{search}.*", "$options": "i"}}
                       ]
                    })
        else:
            limited = True
            pipeline = [
                {"$facet": {"totalCount": [{"$count": "value"}], "pipelineResults": [{"$skip": skip}, {"$limit": limit}]}},
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
            ] + pipeline
        pipeline.insert(0, {
            "$match": {
                "unsubscribe.excluded": True
            }
        })
        pipeline.append({"$project": project})
        if early_match:
            pipeline.insert(0, {"$match": early_match})
        if match:
            pipeline.append({"$match": match})
        if not limited:
            pipeline.append({
                "$facet": {
                    "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            })
        result = await DatabaseConfiguration().studentsPrimaryDetails.aggregate(pipeline).to_list(None)
        if not limited:
            total_count = result[0].get('totalCount', [{}]) if result else [{}]
            count = total_count[0].get('count', 0) if total_count else 0
            result = result[0].get('paginated_results', []) if result else []
            return result, count
        else:
            return result if result else [], result[0].get("totalCount", 0) if result else 0

    async def update_subscribe_status(self, student_ids: list[str], action: str) -> None:
        """
        Updates the subscription status of a student based on the specified action.

        Params:
            student_id (list): The unique identifier of the student whose subscription status needs to be updated.
            action (str): The action to perform, either "Resume" or "Exclude".
                          - "Exclude": Marks the student as unsubscribed.
                          - "Resume": Marks the student as subscribed.

        Returns:
            None

        Raises:
            HTTPException: If student not found
            DatabaseError: If there is an issue updating the student's subscription status in the database.

        Example Usage:
            await update_subscribe_status(student_id="12345", action="unsubscribe")
        """
        existing_students = await DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            [
                {
                    "$match": {
                        "_id": {"$in": [ObjectId(student_id) for student_id in student_ids if ObjectId.is_valid(student_id)]}
                    }
                }
            ]
        ).to_list(None)
        existing_student_ids = {str(student["_id"]) for student in existing_students}
        missing_students = [student_id for student_id in student_ids if student_id not in existing_student_ids]
        if missing_students:
            raise DataNotFoundError(message=f"Students not found: {missing_students}")
        bulk_operations = []
        timestamp = datetime.datetime.utcnow()
        for student_id in student_ids:
            unsubscribe_data = {
                "unsubscribe.user_id": None,
                "unsubscribe.datasegment_id": None,
                "unsubscribe.template_id": None,
                "unsubscribe.timestamp": timestamp,
                "unsubscribe.data_segment_data_type": None,
                "unsubscribe.data_segment_type": None
            }
            if action.lower() == "resume":
                unsubscribe_data.update({
                    "unsubscribe.value": False,
                    "unsubscribe.release_type": None,
                    "unsubscribe.resumed": True
                })
            else:
                unsubscribe_data.update({
                    "unsubscribe.value": True,
                    "unsubscribe.excluded": True,
                    "unsubscribe.resumed": False,
                    "unsubscribe.release_type": "Manual",
                    "unsubscribe.reason": "Excluded by user"
                })
            bulk_operations.append(
                UpdateOne({"_id": ObjectId(student_id)}, {"$set": unsubscribe_data})
            )
        if bulk_operations:
            await DatabaseConfiguration().studentsPrimaryDetails.bulk_write(bulk_operations)

    async def get_pending_leads(self, page_num: int, page_size: int) -> tuple:
        """
            Retrieve a paginated list of pending leads.

            Parameters:
            ----------
            page_num : int
                The page number to retrieve (used for pagination).
            page_size : int
                The number of leads to retrieve per page.

            Returns:
            -------
            tuple
                A tuple containing:
                    - A list of pending lead documents (List[dict]).
                    - The total count of pending leads (int).

            Raises:
            ------
            Exception
                If the lead retrieval or database query fails.
        """
        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
        pipeline = [
            {
                "$lookup": {
                  "from": "studentApplicationForms",
                  "localField": "_id",
                  "foreignField": "student_id",
                  "as": "applications"
                }
            },
            {
                "$match": {
                    "applications": {"$size": 0}
                }
            },
            {
                "$facet": {
                    "metadata": [{"$count": "total"}],
                    "data": [
                        {"$skip": skip},
                        {"$limit": limit},
                        {
                            "$project": {
                                "_id": 0,
                                "student_id": {"$toString": "$_id"},
                                "student_name": {
                                    "$trim": {
                                        "input": {
                                            "$concat": [
                                                {"$ifNull": ["$basic_details.first_name", ""]},
                                                " ",
                                                {"$ifNull": ["$basic_details.middle_name", ""]},
                                                " ",
                                                {"$ifNull": ["$basic_details.last_name", ""]}
                                            ]
                                        }
                                    }
                                },
                                "user_name": "$basic_details.email",
                                "mobile_number": "$basic_details.mobile_number",
                                "address_details": 1
                            }
                        }
                    ]
                }
            },
            {
                "$project": {
                    "totalCount": {"$ifNull": [{"$arrayElemAt": ["$metadata.total", 0]}, 0]},
                    "paginated_results": "$data"
                }
            }
        ]
        try:
            result = await DatabaseConfiguration().studentsPrimaryDetails.aggregate(pipeline).next()
            return json.loads(json.dumps(result.get("paginated_results"), default=str)), result.get("totalCount", 0)
        except StopAsyncIteration:
            return [], 0
