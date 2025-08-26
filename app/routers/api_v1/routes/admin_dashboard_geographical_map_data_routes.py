"""
This file contains API route/endpoint for get map date and city-wise data
"""
from bson import ObjectId
from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from app.core.utils import utility_obj, requires_feature_permission
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import CurrentUser, cache_dependency, \
    insert_data_in_cache, change_indicator_cache, get_collection_from_cache, store_collection_in_cache
from app.helpers.admin_dashboard.admin_board import AdminBoardHelper
from app.helpers.college_configuration import CollegeHelper
from app.models.applications import DateRange
from app.models.lead_schema import program_base
from app.models.student_user_schema import User, ChangeIndicator
from app.helpers.user_curd.user_configuration import UserHelper
from app.database.aggregation.admin_user import AdminUser

map_router = APIRouter()


@map_router.post("/{college_id}", summary="Get the geographical map data")
@requires_feature_permission("read")
async def get_geographical_data(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        cache_change_indicator=Depends(change_indicator_cache),
        college_id: str = Path(description="Enter college id."),
        season: str | None = Body(None,
                                  description="Enter season value if want to"
                                              " get data season-wise"),
        payload: program_base | None = Body(None),
        change_indicator: ChangeIndicator = "last_7_days"
):
    """
    Get the geographical map data of college
    """
    user = await UserHelper().is_valid_user(current_user)
    await CollegeHelper().check_college_exist(college_id=college_id)
    cache_key, data = cache_data
    if data:
        return data
    if payload is None:
        payload = {}
    payload = jsonable_encoder(payload)
    if season == "":
        season = None
    counselor_ids = None
    is_head_counselor = False
    role_name = user.get("role", {}).get("role_name")
    if role_name == "college_head_counselor":
        is_head_counselor = True
        counselor_ids = await AdminUser().get_users_ids_by_role_name(
            "college_counselor", college_id, user.get("_id"))
    if role_name == "college_counselor":
        counselor_ids = [ObjectId(user.get('_id'))]
    (state_dict, total_leads_all_states,
     total_applications_all_states,
     total_admission_all_states) = await AdminBoardHelper().get_state_details(
        college_id, payload, season=season, counselor_ids=counselor_ids, is_head_counselor=is_head_counselor)
    cache_ci_key, ci_data = None, None
    if cache_change_indicator:
        cache_ci_key, ci_data = cache_change_indicator
    if ci_data:
        change_indicator_data = ci_data
    else:
        change_indicator_data = await AdminBoardHelper().get_indicator_data(
            change_indicator, payload, college_id, season=season,
            counselor_ids=counselor_ids, is_head_counselor=is_head_counselor)
        await insert_data_in_cache(cache_ci_key, change_indicator_data, change_indicator=True)
    final_result, other_data = [], {}
    for state in state_dict:
        value = state_dict[state]
        value.lead_percentage = utility_obj.get_percentage_result(
            value.total_lead, total_leads_all_states
        )
        value.application_percentage = utility_obj.get_percentage_result(
            value.application_count, total_applications_all_states
        )
        value.admission_percentage = utility_obj.get_percentage_result(
            value.admission_count, total_admission_all_states
        )
        value = jsonable_encoder(value)
        if value.get('state_code') in change_indicator_data:
            state_code = change_indicator_data.get(
                    value.get('state_code'))
            value.update(
                {"lead_percentage_difference": state_code.get('lead_percentage_difference'),
                 "lead_percentage_position": state_code.get('lead_percentage_position'),
                 'application_percentage_difference': state_code.get('application_percentage_difference'),
                 "application_percentage_position": state_code.get('application_percentage_position'),
                 "admission_percentage_difference": state_code.get("admission_percentage_difference"),
                 "admission_percentage_position": state_code.get('admission_percentage_position')})
        else:
            value.update({"lead_percentage_difference": 0,
                          "lead_percentage_position": "equal",
                          'application_percentage_difference': 0,
                          "application_percentage_position": "equal",
                          'admission_percentage_difference': 0,
                          "admission_percentage_position": "equal"
                          })
        final_result.insert(len(final_result), value)
    other_data = {}
    sorts = ["lead_percentage", "application_percentage",
             "admission_percentage", "total_lead", "application_count", "admission_count"]
    for sort in sorts:
        final_data = sorted(final_result, key=lambda x: x[sort], reverse=True)
        for item in final_data[8:]:
            for key, value in item.items():
                if key in [sort]:
                    if key not in other_data:
                        other_data[key] = round(value, 2)
                    else:
                        other_data[key] = round((other_data[key] + value), 2)
                if key in [f"{sort}_difference"]:
                    key = f"other_{key}"
                    if key not in other_data:
                        other_data[key] = value
                        key = key.replace("difference", "position")
                        other_data[key] = "equal"
                    else:
                        if value > other_data[key]:
                            other_data[key] = value
                            key = key.replace("difference", "position")
                            other_data[key] = "up"

    all_data = {
        "total_applications": total_applications_all_states,
        "total_leads": total_leads_all_states,
        "total_admissions": total_admission_all_states,
        "map": final_result,
        "Other": other_data
    }
    data = utility_obj.response_model(data=all_data,
                                      message="Data fetched successfully.")
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@map_router.post(
    "/city_wise_data/{state_code}",
    summary="Get the geographical map city wise data"
)
@requires_feature_permission("read")
async def get_city_wise_data(
        current_user: CurrentUser,
        state_code: str,
        cache_data=Depends(cache_dependency),
        college_id: str = Query(..., description="Enter college id."),
        date_range: DateRange = Body(None),
):
    """
    Get the geographical map city wise data of college
    """
    user = await DatabaseConfiguration().user_collection.find_one(
        {"user_name": current_user.get("user_name")})
    if not user:
        raise HTTPException(status_code=401, detail="Not enough permissions")
    states = await get_collection_from_cache(collection_name="states")
    if states:
        state = utility_obj.search_for_document(collection=states, field="state_code", search_name=state_code.upper())
    else:
        state = await DatabaseConfiguration().state_collection.find_one(
            {"state_code": state_code.upper()})
        collection = await DatabaseConfiguration().state_collection.aggregate([]).to_list(None)
        await store_collection_in_cache(collection, collection_name="states")
    if state is None:
        raise HTTPException(status_code=404, detail="state not found")
    await CollegeHelper().check_college_exist(college_id=college_id)
    date_range = await utility_obj.format_date_range(date_range)
    cache_key, data = cache_data
    if data:
        return data
    if len(date_range) < 2:
        date_range = await utility_obj.last_3_month()

    start_date, end_date = await utility_obj.date_change_format(
        date_range.get("start_date"), date_range.get("end_date")
    )
    result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
        [
            {
                "$match": {
                    "college_id": ObjectId(college_id),
                    "created_at": {"$gte": start_date, "$lte": end_date},
                }
            },
            {"$project": {"_id": 1, "address_details": 1}},
            {
                "$match": {
                    "address_details.communication_address.state.state_code": state_code.upper()
                }
            },
            {
                "$group": {
                    "_id": "$address_details.communication_address.city.city_name",
                    "student": {"$push": {"student_id": "$_id"}},
                }
            },
            {
                "$lookup": {
                    "from": "studentApplicationForms",
                    "localField": "student.student_id",
                    "foreignField": "student_id",
                    "as": "results",
                }
            },
            {"$unwind": {"path": "$results",
                         "includeArrayIndex": "arrayIndex"}},
            {
                "$group": {
                    "_id": {
                        "city_name": "$_id",
                        "payment_info": "$results.payment_info.status",
                    },
                    "payment_info_count": {"$count": {}},
                }
            },
        ]
    )
    lst = []
    async for i in result:
        if i.get("_id").get("payment_info") == "captured":
            data = {
                "city_name": i.get("_id").get("city_name"),
                "paid_application": i.get("payment_info_count"),
            }
            lst.append(data)
    lst = sorted(lst, key=lambda x: x.get("paid_application"), reverse=True)
    lst = lst[:5]
    if cache_key:
        await insert_data_in_cache(cache_key, lst)
    return lst
