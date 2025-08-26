"""
This file contains test cases regarding for get events data
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_events_data_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/events/?college_id={test_college_validation.get('_id')}&page_num=1&page_size=1&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_events_data_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get events data
    """
    response = await http_client_test.post(
        f"/events/?college_id={test_college_validation.get('_id')}&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_events_data_field_required(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Field required for get events data
    """
    response = await http_client_test.post(
        f"/events/?page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_get_events_data_no_permission(
        http_client_test, test_college_validation, access_token, test_campaign_data, setup_module
):
    """
    No permission for get events data
    """
    response = await http_client_test.post(
        f"/events/?college_id={test_college_validation.get('_id')}&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_events_data_invalid_college_id(
        http_client_test, college_super_admin_access_token, test_create_data_segment, setup_module
):
    """
    Get events data
    """
    response = await http_client_test.post(
        f"/events/?college_id=1234567890&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_get_events_data_by_pagination(
        http_client_test, test_college_validation, college_super_admin_access_token, test_create_data_segment,
        setup_module, test_event_data
):
    """
    Get events data by pagination
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.update_one({"_id": test_college_validation.get('_id')},
                                                                {'$set': {'event_types': ['Test']}})
    await DatabaseConfiguration().event_collection.delete_many({})
    await http_client_test.post(
        f"/event/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=test_event_data
    )
    response = await http_client_test.post(
        f"/events/?college_id={test_college_validation.get('_id')}&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get all events data."
    assert response.json()['total'] == 1
    assert response.json()['count'] == 1
    assert response.json()['pagination']['next'] is None
    assert response.json()['data'][0]['event_name'] == str(test_event_data.get("event_name")).title()
    assert response.json()['data'][0]['learning'] == test_event_data.get("learning")
    assert response.json()['data'][0]['event_description'] == test_event_data.get("event_description")
    assert response.json()['data'][0]['event_type'] == str(test_event_data.get("event_type")).title()


@pytest.mark.asyncio
async def test_get_events_data_no_found(
        http_client_test, test_college_validation, college_super_admin_access_token, test_create_data_segment,
        setup_module, test_event_data
):
    """
    No events data found when try to get it
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().event_collection.delete_many({})
    response = await http_client_test.post(
        f"/events/?college_id={test_college_validation.get('_id')}&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get all events data."
    assert response.json()['total'] == 0
    assert response.json()['count'] == 1
    assert response.json()['pagination']['next'] is None
    assert response.json()['pagination']['previous'] is None
    assert response.json()['data'] == []


@pytest.mark.asyncio
async def test_get_events_data_without_pagination(
        http_client_test, test_college_validation, college_super_admin_access_token, test_create_data_segment,
        setup_module, test_event_data
):
    """
    Get events data without pagination
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.update_one({"_id": test_college_validation.get('_id')},
                                                                {'$set': {'event_types': ['Test']}})
    await DatabaseConfiguration().event_collection.delete_many({})
    await http_client_test.post(
        f"/event/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=test_event_data
    )
    response = await http_client_test.post(
        f"/events/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get all events data."
    assert response.json()['total'] == 1
    assert response.json()['count'] is None
    assert response.json()['pagination'] == {}
    assert response.json()['data'][0]['event_name'] == str(test_event_data.get("event_name")).title()
    assert response.json()['data'][0]['learning'] == test_event_data.get("learning")
    assert response.json()['data'][0]['event_description'] == test_event_data.get("event_description")
    assert response.json()['data'][0]['event_type'] == str(test_event_data.get("event_type")).title()


@pytest.mark.asyncio
async def test_get_events_data_with_filter_event_name_by_search_string(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, test_event_data
):
    """
    Get events data with the help of filter event_name
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.update_one({"_id": test_college_validation.get('_id')},
                                                                {'$set': {'event_types': ['Test']}})
    await DatabaseConfiguration().event_collection.delete_many({})
    await http_client_test.post(
        f"/event/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=test_event_data
    )
    response = await http_client_test.post(
        f"/events/?college_id={test_college_validation.get('_id')}&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"search_input": test_event_data.get("event_name", "").title()}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get all events data."
    assert response.json()['total'] == 1
    assert response.json()['count'] == 1
    assert response.json()['pagination']['next'] is None
    assert response.json()['data'][0]['event_name'] == str(test_event_data.get("event_name")).title()
    assert response.json()['data'][0]['learning'] == test_event_data.get("learning")
    assert response.json()['data'][0]['event_description'] == test_event_data.get("event_description")
    assert response.json()['data'][0]['event_type'] == str(test_event_data.get("event_type")).title()


@pytest.mark.asyncio
async def test_get_events_data_with_date_range(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, test_event_data,
        start_end_date
):
    """
    Get events data with the help data_range
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.update_one({"_id": test_college_validation.get('_id')},
                                                                {'$set': {'event_types': ['Test']}})
    await DatabaseConfiguration().event_collection.delete_many({})
    await http_client_test.post(
        f"/event/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=test_event_data
    )
    response = await http_client_test.post(
        f"/events/?college_id={test_college_validation.get('_id')}&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"date_range": start_end_date}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get all events data."
    assert response.json()['total'] == 1
    assert response.json()['count'] == 1
    assert response.json()['pagination']['next'] is None
    assert response.json()['data'][0]['event_name'] == str(test_event_data.get("event_name")).title()
    assert response.json()['data'][0]['learning'] == test_event_data.get("learning")
    assert response.json()['data'][0]['event_description'] == test_event_data.get("event_description")
    assert response.json()['data'][0]['event_type'] == str(test_event_data.get("event_type")).title()


@pytest.mark.asyncio
async def test_get_events_data_with_event_type(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, test_event_data
):
    """
    Get events data with the help event type
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.update_one({"_id": test_college_validation.get('_id')},
                                                                {'$set': {'event_types': ['Test']}})
    await DatabaseConfiguration().event_collection.delete_many({})
    await http_client_test.post(
        f"/event/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=test_event_data
    )
    response = await http_client_test.post(
        f"/events/?college_id={test_college_validation.get('_id')}&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"event_type": [test_event_data.get("event_type", "").title()]}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get all events data."
    assert response.json()['total'] == 1
    assert response.json()['count'] == 1
    assert response.json()['pagination']['next'] is None


@pytest.mark.asyncio
async def test_get_events_data_with_filter_event_name(
        http_client_test, test_college_validation,
        college_super_admin_access_token, setup_module, test_event_data
):
    """
    Get events data with the help of filter event_name
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.update_one(
        {"_id": test_college_validation.get('_id')},
        {'$set': {'event_types': ['Test']}})
    await DatabaseConfiguration().event_collection.delete_many({})
    await http_client_test.post(
        f"/event/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=test_event_data
    )
    response = await http_client_test.post(
        f"/events/?college_id={test_college_validation.get('_id')}&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"event_name": [test_event_data.get("event_name", "").title()]}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get all events data."
    assert response.json()['total'] == 1
    assert response.json()['count'] == 1
    assert response.json()['pagination']['next'] is None
    assert response.json()['data'][0]['event_name'] == str(test_event_data.get("event_name")).title()
    assert response.json()['data'][0]['learning'] == test_event_data.get("learning")
    assert response.json()['data'][0]['event_description'] == test_event_data.get("event_description")
    assert response.json()['data'][0]['event_type'] == str(test_event_data.get("event_type")).title()


@pytest.mark.asyncio
async def test_download_events_data_with_filter_event_name(
        http_client_test, test_college_validation,
        college_super_admin_access_token, setup_module, test_event_data
):
    """
    Get events data with the help of filter event_name
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.update_one(
        {"_id": test_college_validation.get('_id')},
        {'$set': {'event_types': ['Test']}})
    await DatabaseConfiguration().event_collection.delete_many({})
    await http_client_test.post(
        f"/event/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=test_event_data
    )
    response = await http_client_test.post(
        f"/events/?college_id={test_college_validation.get('_id')}"
        f"&page_num=1&page_size=1&download_data=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"event_name": [test_event_data.get("event_name", "").title()]}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "File downloaded successfully."
    assert "file_url" in response.json()


@pytest.mark.asyncio
async def test_download_events_data_no_found(
        http_client_test, test_college_validation,
        college_super_admin_access_token, setup_module
):
    """
    Get events data with the help of filter event_name
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.update_one(
        {"_id": test_college_validation.get('_id')},
        {'$set': {'event_types': ['Test']}})
    await DatabaseConfiguration().event_collection.delete_many({})
    response = await http_client_test.post(
        f"/events/?college_id={test_college_validation.get('_id')}"
        f"&page_num=1&page_size=1&download_data=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Event data not found."
