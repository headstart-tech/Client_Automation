"""
This file contains test cases related to API route/endpoint counselor-wise lead stage
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_counselor_wise_lead_stage_not_authentication(
        http_client_test, setup_module, test_college_validation
):
    """
    Not authentication for counselor-wise lead stage
    """
    response = await http_client_test.put(
        f"/counselor/counselor_wise_lead_stage?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": "wrong bearer"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_counselor_wise_lead_stage(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, start_end_date
):
    """
    Counselor-wise lead stage
    """
    response = await http_client_test.put(
        f"/counselor/counselor_wise_lead_stage?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=start_end_date
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetched successfully"
