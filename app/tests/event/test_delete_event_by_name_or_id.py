"""
This file contains test cases regarding for delete event data by name or id
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_event_data_by_name_or_id_not_authenticated(http_client_test, test_college_validation,
                                                                 setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.delete(
        f"/event/delete_by_name_or_id/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_event_data_by_name_or_id_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for delete event data by name or id
    """
    response = await http_client_test.delete(
        f"/event/delete_by_name_or_id/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_delete_event_data_by_name_or_id_field_required(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Field required for delete event data by name or id
    """
    response = await http_client_test.delete(
        f"/event/delete_by_name_or_id/?feature_key={feature_key}", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_delete_event_data_by_name_or_id_no_permission(
        http_client_test, test_college_validation, access_token, test_campaign_data, setup_module
):
    """
    No permission for delete event data by name or id
    """
    response = await http_client_test.delete(
        f"/event/delete_by_name_or_id/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_delete_event_data_by_name_or_id_required_event_name_or_id(
        http_client_test, test_college_validation, college_super_admin_access_token, test_create_data_segment,
        setup_module
):
    """
    Required event name or id for delete event data by name or id
    """
    response = await http_client_test.delete(
        f"/event/delete_by_name_or_id/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Event not found. Make sure you provided event_id or event_name is correct."}


@pytest.mark.asyncio
async def test_delete_event_data_by_name_or_id_by_invalid_id(
        http_client_test, test_college_validation, college_super_admin_access_token, test_create_data_segment,
        setup_module
):
    """
    Invalid id for get event data by id
    """
    response = await http_client_test.delete(
        f"/event/delete_by_name_or_id/?college_id={test_college_validation.get('_id')}"
        f"&event_id=12345678901234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": 'Event id must be a 12-byte input or a 24-character hex string'}


@pytest.mark.asyncio
async def test_delete_event_data_by_name_or_id_invalid_college_id(
        http_client_test, college_super_admin_access_token, test_create_data_segment, setup_module
):
    """
    Try to get event data by invalid college id
    """
    response = await http_client_test.delete(
        f"/event/delete_by_name_or_id/?college_id=1234567890"
        f"&event_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_delete_event_data_by_name_or_id(
        http_client_test, test_college_validation, college_super_admin_access_token, test_create_data_segment,
        setup_module, test_event_data
):
    """
    Get event data by id
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
    response = await http_client_test.delete(
        f"/event/delete_by_name_or_id/?college_id={test_college_validation.get('_id')}"
        f"&event_id={str(event.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Event deleted."}
