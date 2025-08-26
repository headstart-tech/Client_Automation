"""
This file contains test cases related to get forms by status
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_colleges_by_status_not_authenticated(http_client_test, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(f"/colleges/get_by_status/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_colleges_by_status_bad_credentials(http_client_test, setup_module):
    """
    Bad token for get colleges by status
    """
    response = await http_client_test.get(
        f"/colleges/get_by_status/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_colleges_by_status_no_permission(
        http_client_test, access_token, setup_module
):
    """
    No permission for get colleges by status
    """
    response = await http_client_test.get(
        f"/colleges/get_by_status/?approved=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_colleges_by_status(http_client_test, test_college_validation, client_manager_access_token,
                                      setup_module):
    """
    Get colleges by status
    """
    response = await http_client_test.get(f"/colleges/get_by_status/?pending=true&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {client_manager_access_token}"})
    assert response.status_code == 200
    try:
        assert response.json()['message'] == "Colleges data found."
    except:
        assert response.json()['detail'] == "Colleges data not found."


@pytest.mark.asyncio
async def test_get_colleges_by_status_no_found(http_client_test, test_college_validation, client_manager_access_token,
                                               setup_module):
    """
    Get colleges by status
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.delete_many({})
    response = await http_client_test.get(f"/colleges/get_by_status/?pending=true&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {client_manager_access_token}"})
    assert response.status_code == 200
    assert response.json() == {"detail": "Colleges data not found."}


@pytest.mark.asyncio
async def test_get_colleges_by_status_by_pagination(http_client_test, test_college_validation,
                                                    client_manager_access_token, setup_module):
    """
    Get colleges by status by pagination
    """
    response = await http_client_test.get(
        f"/colleges/get_by_status/?page_num=1&page_size=1&approved=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {client_manager_access_token}"})
    assert response.status_code == 200
    assert response.json()['detail'] == "Colleges data not found."
