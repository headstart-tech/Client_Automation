"""
This file contains test cases related to lead notifications
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_lead_notifications_not_authenticated(http_client_test,
                                                    test_college_validation,
                                                    setup_module):
    """
    Not authenticated for get lead profile header
    """
    response = await http_client_test.get(
        f"/lead/lead_notifications/62a057ef1ec1188907d262a3?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_lead_notifications_invalid_credentials(http_client_test,
                                                      test_college_validation,
                                                      setup_module):
    """
    Invalid credentials for get lead profile header
    """
    response = await http_client_test.get(
        f"/lead/lead_notifications/62a057ef1ec1188907d262a3?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_lead_notifications(
        http_client_test, test_college_validation,
        college_super_admin_access_token, setup_module, application_details
):
    """
    Get lead profile header
    """
    response = await http_client_test.get(
        f"/lead/lead_notifications/{application_details.get('_id')}?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_lead_notifications_application_not_found(
        http_client_test, test_college_validation,
        college_super_admin_access_token, setup_module
):
    """
    Application not found for get lead profile header
    """
    response = await http_client_test.get(
        f"/lead/lead_notifications/62a057ef1ec1188907d262a2"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"
