"""
This file contains API routes/endpoints related to campaign
"""
from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, Query, Body
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException

from app.core.utils import utility_obj, requires_feature_permission
from app.database.aggregation.get_all_campaign_rules import CampaignRule
from app.database.configuration import DatabaseConfiguration
from app.dependencies.college import get_college_id, get_college_id_short_version
from app.dependencies.oauth import cache_dependency, \
    insert_data_in_cache, CurrentUser, cache_invalidation, change_indicator_cache
from app.helpers.campaign.campaign_configuration import RuleHelper
from app.helpers.campaign.campaign_helper import campaign_manager
from app.helpers.campaign.campaign_manager import campaign
from app.helpers.campaign.campaign_overlap import campaign_source_overlap
from app.helpers.campaign.utm_campaign_details import utm_campaign
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.applications import DateRange
from app.models.campaign_schema import Rule
from app.models.student_user_schema import User, ChangeIndicator

campaign_router = APIRouter()


# Todo: We are delete this route first confirmation
#  this API available in old design
@campaign_router.post('/create_rule/', summary="Create or update rule")
@requires_feature_permission("write")
async def create_rule(
        rule_create: Rule,
        current_user: CurrentUser,
        rule_id: str = Query(None,
                             description="Enter rule id if you want to update rule data"),
        college: dict = Depends(get_college_id_short_version(short_version=True))):
    """
    Create rule and store it in the collection named rule
    """
    user = await UserHelper().is_valid_user(current_user)
    rule_create = {key: value for key, value in rule_create.dict().items() if
                   value is not None}
    if await DatabaseConfiguration().rule_collection.find_one(
            {'rule_name': str(
                rule_create.get('rule_name')).title()}) is not None:
        return {'detail': "Rule name already exists."}
    if rule_create.get("script", {}).get('action_type') and rule_create.get(
            "script", {}).get(
        'selected_template_id'):
        action_types, template_ids = [], []
        for action_type, template_id in zip(
                rule_create.get("script", {}).get('action_type'),
                rule_create.get("script", {}).get('selected_template_id')):
            if len(template_id) != 24:
                return {'detail': 'Template id should be valid.'}
            elif (
                    template := await DatabaseConfiguration().template_collection.find_one(
                        {'_id': ObjectId(str(template_id)),
                         'template_type': str(action_type).lower()})) is None:
                return {'detail': 'Template is should be valid'}
            else:
                action_types.append(template.get('template_type'))
                template_ids.append(template.get('_id'))
                if str(action_type).lower() == "sms":
                    rule_create['script'][
                        'sms_template_content'] = template.get('content')
                    rule_create['script']['dlt_content_id'] = template.get(
                        'dlt_content_id')
                elif str(action_type).lower() == "email":
                    rule_create['script'][
                        'email_template_content'] = template.get('content')
                elif str(action_type).lower() == "whatsapp":
                    rule_create['script'][
                        'whatsapp_template_content'] = template.get('content')
        rule_create['script']['action_type'] = action_types
        rule_create['script']['selected_template_id'] = template_ids
    if rule_create.get("script", {}).get('when_exec', {}).get('schedule_type'):
        rule_create['script']['when_exec']['schedule_type'] = str(
            rule_create.get("script", {}).get('when_exec', {}).get(
                'schedule_type')).title()
    if rule_create.get('rule_name'):
        rule_create['rule_name'] = str(rule_create.get('rule_name')).title()
    data_segment = {}
    if rule_create.get('data_segment_name'):
        if (
                data_segment := await DatabaseConfiguration().data_segment_collection.find_one(
                    {'data_segment_name': str(
                        rule_create.get(
                            'data_segment_name')).title()})) is None:
            return {'detail': "Data segment name should be valid."}
        rule_create['data_segment_name'] = data_segment.get(
            'data_segment_name')
        rule_create['data_segment_id'] = [data_segment.get('_id')]
    rule_create.update(
        {'updated_on': datetime.utcnow(), 'updated_by': user.get('_id'),
         'updated_by_name': utility_obj.name_can(user)})
    if rule_id:
        await utility_obj.is_id_length_valid(_id=rule_id, name="Rule id")
        rule = await DatabaseConfiguration().rule_collection.find_one(
            {"_id": ObjectId(rule_id)})
        if not rule:
            return {
                'detail': "Rule not found. Make sure provided template id should be correct."}
        await DatabaseConfiguration().rule_collection.update_one(
            {'_id': rule.get('_id')}, {'$set': rule_create})
        return {"message": "Rule updated."}
    if rule_create.get('rule_name') in ["", None]:
        return {'detail': "Rule name should be valid."}
    elif rule_create.get('data_segment_name') in ["", None]:
        return {'detail': "Data segment name should be valid."}
    rule_create.update(
        {'created_by_id': user.get('_id'),
         'created_by_name': utility_obj.name_can(user),
         'created_on': datetime.utcnow()})
    created_automation = await DatabaseConfiguration().rule_collection.insert_one(
        rule_create)
    rule_create.update({'_id': created_automation.inserted_id})
    linked_automation = data_segment.get("linked_automation", [])
    if not linked_automation:
        linked_automation = []
    linked_automation.append(rule_create.get('rule_name'))
    await DatabaseConfiguration().data_segment_collection.update_one(
        {"_id": rule_create.get("data_segment_id")},
        {"$set": {"linked_automation": linked_automation}})
    await cache_invalidation(api_updated="campaign/create_rule/")
    return {"data": await RuleHelper().rule_helper(rule_create),
            "message": "Rule created."}


@campaign_router.get("/get_rules/")
@requires_feature_permission("read")
async def get_campaign_rules(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        page_num: int = Query(..., gt=0,
                              description="Enter page number where you want to show data"),
        page_size: int = Query(..., gt=0,
                               description="Enter page size means how many data you want to show on page number"),
        college: dict = Depends(get_college_id_short_version(short_version=True)),):
    await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
    all_records = await CampaignRule().get_all_rules(skip, limit)
    total = await DatabaseConfiguration().rule_collection.count_documents({})
    response = await utility_obj.pagination_in_aggregation(
        page_num, page_size, total, route_name="/get_rules/"
    )
    data = {"data": all_records,
            "total": total,
            "count": page_size,
            "pagination": response["pagination"],
            "message": "Get all campaign rules.",
            }
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@campaign_router.get('/check_rule_name_exist_or_not/',
                     summary="Check campaign rule name exist or not")
async def check_rule_name_exist_or_not(
        rule_name: str = Query(..., description="Enter campaign rule name"),
        college: dict = Depends(get_college_id_short_version(short_version=True)),):
    """
    Check campaign rule name exist or not in the collection named campaign
    """
    if rule_name == "":
        return {'detail': "Rule name should be valid."}
    elif await DatabaseConfiguration().rule_collection.find_one(
            {'rule_name': str(rule_name).title()}) is not None:
        return {'detail': 'Rule name already exists.'}
    return {'message': 'Rule name not exist.'}


@campaign_router.put("/update_status_of_rule/",
                     summary="Change status of campaign rule")
@requires_feature_permission("edit")
async def update_status_of_campaign_rule(
        current_user: CurrentUser,
        rule_id: str = Query(None,
                             description="Enter campaign rule ID \n* e.g.," "**624e8d6a92cc415f1f578a24**"),
        rule_name: str = Query(None,
                               description="Enter campaign rule name \n* e.g., "
                                           "**Test**"),
        enabled: bool = Query(...,
                              description="Enter status of campaign rule"),
        college: dict = Depends(get_college_id)):
    """
    Change status of campaign rule
    """
    user = await UserHelper().is_valid_user(current_user)
    if rule_id:
        await utility_obj.is_id_length_valid(_id=rule_id,
                                             name="Campaign rule id")
        rule = await DatabaseConfiguration().rule_collection.find_one(
            {"_id": ObjectId(rule_id)})
    elif rule_name:
        rule = await DatabaseConfiguration().rule_collection.find_one(
            {"rule_name": rule_name.title()})
    else:
        return {'detail': "Need to provide rule_id or rule_name."}
    if rule:
        await DatabaseConfiguration().rule_collection.update_one(
            {'_id': rule.get('_id')}, {
                '$set': {'enabled': enabled, 'updated_on': datetime.utcnow(),
                         'updated_by': user.get('_id'),
                         'updated_by_name': utility_obj.name_can(user)}})
        return {"message": "Updated status of rule."}
    return {'detail': "Rule not found."}


@campaign_router.post('_manager/')
@requires_feature_permission("read")
async def get_source_campaign(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        date_range: DateRange = None,
        college: dict = Depends(get_college_id_short_version(short_version=True)),):
    """
    Get source based campaign data
    """
    await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    data = await campaign().campaign_manager_helper(college.get('id'),
                                                    date_range)
    data = {"data": data, "message": "Get campaign manager data."}
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@campaign_router.post('_manager/source_wise_details/')
@requires_feature_permission("read")
async def get_source_campaign(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        source_name: str = Query(None, description="Enter source name"),
        date_range: DateRange = None, college: dict = Depends(get_college_id_short_version(short_version=True)),):
    """
    Get source wise details
    """
    await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    data = await campaign().get_source_wise_details(source_name, date_range)
    data = {"data": data, "message": "Get source wise details."}
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@campaign_router.post('_manager/source_performance_details/')
@requires_feature_permission("write")
async def leads_details_based_on_source(
        current_user: CurrentUser,
        college_id: str = Query(
            ...,
            description="Enter college ID \n* "
                        "e.g." "**624e8d6a92cc415f1f578a24**"),
        cache_data=Depends(cache_dependency),
        cache_change_indicator=Depends(change_indicator_cache),
        date_range: DateRange = None,
        change_indicator: ChangeIndicator = "last_7_days",
        page_num: int = 1,
        page_size: int = 5,
        college: dict = Depends(get_college_id_short_version(short_version=True))):
    """
    Get source wise details
    """
    await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    start_date, end_date = None, None
    if date_range:
        date_range = await utility_obj.format_date_range(date_range)
        start_date, end_date = await utility_obj.get_start_and_end_date(
            date_range=date_range)
    data, total_count_data = await campaign().get_source_performance_details(
        college_id, start_date, end_date)
    data = await campaign().get_source_performance_details_change_indicator(
        college_id, data, change_indicator, cache_change_indicator)
    response = await utility_obj.pagination_in_api(
        page_num, page_size, data, len(data),
        route_name="/campaign_manager/source_performance_details/")
    data = {
        "data": response["data"],
        "total_count_data": total_count_data,
        "total": len(data),
        "count": page_size,
        "pagination": response["pagination"],
        "message": "Get source performance details.",
    }
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@campaign_router.put("/get_utm_campaign")
@requires_feature_permission("read")
async def get_utm_campaign_detail(source_name: str, utm_name: str,
                                  current_user: CurrentUser,
                                  cache_data=Depends(cache_dependency),
                                  date_range: DateRange = Body(None),
                                  college: dict = Depends(get_college_id_short_version(short_version=True)),
                                  page_num: int = Query(gt=0),
                                  page_size: int = Query(gt=0)):
    """**source name will be googled, facebook, Twitter**
    **/n utm_source wil be utm_campaign, medium, keyword**"""
    if (user := await DatabaseConfiguration().user_collection.find_one(
            {"user_name": current_user.get("user_name")})) is None:
        raise HTTPException(status_code=404, detail="user not found")
    if user.get("role", {}).get("role_name") in ["college_publisher_console"]:
        raise HTTPException(status_code=401, detail="Not enough permission")
    cache_key, data = cache_data
    if data:
        return data
    start_date, end_date = None, None
    if date_range:
        date_range = jsonable_encoder(date_range)
        start_date, end_date = await utility_obj.date_change_format(
            date_range.get("start_date"), date_range.get("end_date")
        )
    data = await utm_campaign(source_name, utm_name, start_date, end_date,
                              page_num, page_size).get_source_wise_data()
    if cache_key:
        await insert_data_in_cache(cache_key, data)
    return data


@campaign_router.post("/campaign_header")
@requires_feature_permission("read")
async def get_campaign_header(
        current_user: CurrentUser,
        cache_data=Depends(cache_dependency),
        cache_change_indicator=Depends(change_indicator_cache),
        lead_type: str = "API",
        change_indicator: ChangeIndicator = "last_7_days",
        date_range: DateRange = Body(None),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get the campaign header for the given campaign details

    params:
        current_user (str): Get current user from the token automatically
        lead_type (str): Get the lead type will be API, Online and offline,
            by default lead type should be API,
        change_indicator (str): Get the change the indicator for the given
            last_7_days, last_15_days and last_30_days,
        date_range (dict): Get the date range for campaign details indicator,
        college (dict): Get the college details from the college id

    return:
        response: A dictionary containing the following campaign details counts
    """
    await UserHelper().is_valid_user(current_user)
    cache_key, data = cache_data
    if data:
        return data
    try:
        data = await campaign_manager().get_campaign_helper(
            lead_type=lead_type.lower(),
            date_range=date_range,
            change_indicator=change_indicator,
            college=college,
            change_indicator_cache=cache_change_indicator
        )
        if cache_key:
            await insert_data_in_cache(cache_key, data)
        return data
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occurred "
                                                    f"{error}")


@campaign_router.put("/utm_details")
@requires_feature_permission("read")
async def get_utm_details(
        current_user: CurrentUser,
        source_name: list[str] = None,
        utm_type: str = None,
        field_name: str = None,
        change_indicator: ChangeIndicator = "last_7_days",
        date_range: DateRange = Body(None),
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    get the utm counts wise campaign, median and keywords

    params:
        current_user (str): Get the current user from the token automatically,
        source_name (str): Get the multiple source name in the list for filter
            the data by source name,
        utm_type (str): Get the utm type e.q. campaign, keyword and median
        change_indicator (str): Get the change indicator for the indicator
            position by default is "last_7_days"
        field_name (str): Get the field name for the sorting the data,
            e.q. total_leads, paid_application, form_initiated,
             total_application, verified_leads
        date_range (dict): Get the date range for the filter data by datetime.
        page_num (int): Get the number of the page
        page_size (int): Get the size of the page
        college (dict): Get the college details from the college id.

    return:
        response: A list containing the utm counts data of total_leads,
            total_application, paid_application, form_initiated etc.
    raise:
        401 Not enough permission: Access denied for None admin user
        404 Not found error: Not fount college
        500 Internal server error: If error occur during processing
            of the request
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await campaign_manager().get_utm_campaign_count(
            utm_type=utm_type, source_name=source_name,
            change_indicator=change_indicator,
            college_id=str(college.get("id")),
            date_range=date_range, field_name=field_name, page_num=page_num,
            page_size=page_size)
    except Exception as error:
        raise HTTPException(status_code=500, detail=error)


@campaign_router.post("/source_wise_overlap")
@requires_feature_permission("read")
async def get_source_wise_overlap(
        current_user: CurrentUser,
        change_indicator: ChangeIndicator,
        date_range: DateRange = Body(None),
        page_num: int = Query(gt=0),
        page_size: int = Query(gt=0),
        source_name: list[str] = Body(None),
        college: dict = Depends(get_college_id_short_version(short_version=True)),
):
    """
    Get the source wise overlap details

    params:
        current_user (str): Get the current user from the token automatically
        change_indicator (str): Get the change indicator for the datetime range
        college (dict): get the college details based on college id
        date_range (DateRange | None): Either None or get the date range
            for get data based on date_range.
        page_num (int): get the page number of the range
        page_size (int): get the page size of the range of limit data
        source_name (str): Get the name of the source for the filter by source

    returns:
        response: - dict: A dict which containing the source overlap
            details along with count and message.

    raise:
        Internal server error: "An error occurred error details"
    """
    await UserHelper().is_valid_user(current_user)
    try:
        return await campaign_source_overlap().get_source_overlap(
            college_id=str(college.get("id")),
            change_indicator=change_indicator, source_name=source_name,
            date_range=date_range, page_num=page_num, page_size=page_size)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occurred "
                                                    f"{error}")
