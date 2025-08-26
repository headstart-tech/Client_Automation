"""
This file contains test cases related to get communication performance dashboard data
"""
import pytest
from app.tests.conftest import access_token, user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_communication_performance_dashboard_not_authenticated(http_client_test, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(f"/college/communication_performance_dashboard/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_communication_performance_dashboard_bad_credentials(http_client_test, setup_module):
    """
    Bad token for get estimated bill of college
    """
    response = await http_client_test.get(
        f"/college/communication_performance_dashboard/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_communication_performance_dashboard_no_permission(
        http_client_test, access_token, test_college_validation, setup_module
):
    """
    No permission for get estimated bill of college
    """
    response = await http_client_test.get(
        "/college/communication_performance_dashboard/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_communication_performance_dashboard(http_client_test, test_college_validation,
                                                   client_manager_access_token, setup_module):
    """
    Get estimated bill of college
    """
    response = await http_client_test.get(
        "/college/communication_performance_dashboard/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {client_manager_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get communication performance dashboard data."


@pytest.mark.asyncio
async def test_communication_performance_dashboard_college_no_found(http_client_test, client_manager_access_token,
                                                                    setup_module):
    """
    College not found for get estimated bill of college
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.delete_many({})
    response = await http_client_test.get(
        "/college/communication_performance_dashboard/"
        f"?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {client_manager_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."


@pytest.mark.asyncio
async def test_communication_performance_dashboard_invalid_college_id(http_client_test, client_manager_access_token,
                                                                      setup_module):
    """
    College not found for get estimated bill of college
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.delete_many({})
    response = await http_client_test.get(
        "/college/communication_performance_dashboard/"
        f"?college_id=12345678901234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {client_manager_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"
