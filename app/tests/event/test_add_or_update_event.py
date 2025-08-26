"""
This file contains test cases related to API route/endpoint add/update event in database
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_or_update_event_not_authenticated(http_client_test, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(f"/event/add_or_update/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_add_or_update_event_bad_credentials(http_client_test, setup_module):
    """
    Bad token for add or update event
    """
    response = await http_client_test.post(
        f"/event/add_or_update/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_add_or_update_event_required_college_id(
        http_client_test, setup_module, access_token
):
    """
    Required college id for add or update event
    """
    response = await http_client_test.post(f"/event/add_or_update/?feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 400
    assert response.json() == {'detail': "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_add_or_update_event_no_permission(
        http_client_test, access_token, test_college_validation, setup_module
):
    """
    No permission for add or update event
    """
    response = await http_client_test.post(
        f"/event/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_add_or_update_event_required_body(
        http_client_test, access_token, test_college_validation, setup_module
):
    """
    Required body for add or update event
    """
    response = await http_client_test.post(
        f"/event/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {'detail': 'Body must be required and valid.'}
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_add_or_update_event_no_permission(
        http_client_test, access_token, test_college_validation, setup_module, test_event_data
):
    """
    No permission for add or update event
    """
    response = await http_client_test.post(
        f"/event/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json=test_event_data
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_add_event(
        http_client_test, college_super_admin_access_token, test_college_validation, setup_module, test_event_data
):
    """
    Add event into database
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.update_one({"_id": test_college_validation.get('_id')},
                                                                {'$set': {'event_types': ['Test']}})
    await DatabaseConfiguration().event_collection.delete_many({})
    response = await http_client_test.post(
        f"/event/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=test_event_data
    )
    assert response.json()['message'] == "Event created."
    assert response.json()['data']['event_name'] == str(test_event_data.get("event_name")).title()
    assert response.json()['data']['learning'] == test_event_data.get("learning")
    assert response.json()['data']['event_description'] == test_event_data.get("event_description")
    assert response.json()['data']['event_type'] == str(test_event_data.get("event_type")).title()
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_event(
        http_client_test, college_super_admin_access_token, test_college_validation, setup_module, test_event_data
):
    """
    Update event data
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.update_one({"_id": test_college_validation.get('_id')},
                                                                {'$set': {'event_types': ['Test']}})
    await DatabaseConfiguration().event_collection.delete_many({})
    await http_client_test.post(
        f"/event/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=test_event_data
    )
    event = await DatabaseConfiguration().event_collection.find_one(
        {'event_name': str(test_event_data.get("event_name")).title()})
    response = await http_client_test.post(
        f"/event/add_or_update/?college_id={str(test_college_validation.get('_id'))}"
        f"&event_id={str(event.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=test_event_data
    )
    assert response.json() == {"message": "Event data updated."}
    assert response.status_code == 200
