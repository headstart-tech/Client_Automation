"""
This file contains test cases for get source performance reports
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_source_lead_performing_not_authenticate(http_client_test, setup_module, test_college_validation):
    """
    Not authenticated for get source performance reports
    """
    response = await http_client_test.get(
        f"/counselor/source_lead_performing?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": "wrong Bearer"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_source_lead_performing(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Get source performance reports
    """
    response = await http_client_test.get(
        f"/counselor/source_lead_performing?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetched successfully"
