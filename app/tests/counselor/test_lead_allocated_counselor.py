"""
This file contains test cases for get lead allocation counselor
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_lead_allocated_counselor_not_authenticate(
        http_client_test, setup_module, test_college_validation
):
    """
    Not authenticated for get lead allocation counselor
    """
    response = await http_client_test.get(
        f"/counselor/lead_allocated_counselor/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f" wrong Bearer "},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_lead_allocated_counselor(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Get lead allocation counselor
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/counselor/lead_allocated_counselor/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
