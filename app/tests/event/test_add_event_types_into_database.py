"""
This file contains test cases related to API route/endpoint add event types in database
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_or_update_event_types_not_authenticated(http_client_test, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(f"/event/type/add_or_update/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_add_or_update_event_types_bad_credentials(http_client_test, setup_module):
    """
    Bad token for add or update event types
    """
    response = await http_client_test.post(
        f"/event/type/add_or_update/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_add_or_update_event_types_required_college_id(
        http_client_test, setup_module, access_token
):
    """
    Required college id for add or update event types
    """
    response = await http_client_test.post(f"/event/type/add_or_update/?feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 400
    assert response.json() == {'detail': "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_add_or_update_event_types_no_permission(
        http_client_test, access_token, test_college_validation, setup_module
):
    """
    No permission for add or update event types
    """
    response = await http_client_test.post(
        f"/event/type/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_add_or_update_event_types_required_body(
        http_client_test, access_token, test_college_validation, setup_module
):
    """
    Required body for add or update event types
    """
    response = await http_client_test.post(
        f"/event/type/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {'detail': 'Body must be required and valid.'}
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_add_or_update_event_types_no_permission(
        http_client_test, access_token, test_college_validation, setup_module
):
    """
    No permission for add or update event types
    """
    response = await http_client_test.post(
        f"/event/type/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json=["Test"]
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_add_event_types(
        http_client_test, college_super_admin_access_token, test_college_validation, setup_module
):
    """
    Add event types into database
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.update_one({"_id": test_college_validation.get('_id')},
                                                                {'$unset': {'event_types': True}})
    response = await http_client_test.post(
        f"/event/type/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=["Test"]
    )
    assert response.json() == {"data": ["Test"], "message": "Added event types."}
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_event_types_which_already_exist(
        http_client_test, college_super_admin_access_token, test_college_validation, setup_module
):
    """
    Try to update event types which already into database
    """
    await http_client_test.post(
        f"/event/type/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=["Test"]
    )
    response = await http_client_test.post(
        f"/event/type/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=["Test"]
    )
    assert response.json() == {"data": [], "message": "Updated event types."}
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_event_types_into_database(
        http_client_test, college_super_admin_access_token, test_college_validation, setup_module
):
    """
    Update event types into database
    """
    await http_client_test.post(
        f"/event/type/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=["Test"]
    )
    response = await http_client_test.post(
        f"/event/type/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=["String"]
    )
    assert response.json() == {"data": ["String"], "message": "Updated event types."}
    assert response.status_code == 200
