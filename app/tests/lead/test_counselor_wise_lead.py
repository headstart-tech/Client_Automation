"""
This file contains test cases related to counselor wise lead
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_counselor_wise_lead_not_authenticate(http_client_test, test_college_validation, setup_module):
    """
    Counselor wise lead not authenticated
    """
    response = await http_client_test.post(
        f"/counselor/counselor_wise_lead?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": "wrong bearer"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_counselor_wise_lead(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Counselor wise lead
    """
    response = await http_client_test.post(
        f"/counselor/counselor_wise_lead?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_counselor_wise_lead_date_range(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, start_end_date
):
    """
    Counselor wise lead with date_range
    """
    response = await http_client_test.post(
        f"/counselor/counselor_wise_lead?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=start_end_date
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
