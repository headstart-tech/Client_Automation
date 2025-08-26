"""
This file contains test cases of get lead detail by mobile number
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_lead_by_mobile(http_client_test, test_college_validation, setup_module,
                                  college_super_admin_access_token):
    """
    Permission restrict every one except college counselor
    """
    response = await http_client_test.put(
        f"/admin/get_lead_detail_by_number?mobile_number=224&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_get_lead_number(http_client_test, test_college_validation, setup_module, college_counselor_access_token,
                               test_counselor_data):
    """
    Check with college counselor
    """
    response = await http_client_test.put(
        f"/admin/get_lead_detail_by_number?mobile_number={test_counselor_data.get('mobile_number')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_get_lead_number_by_wrong_mobile_number(http_client_test, test_college_validation, setup_module,
                                                      college_counselor_access_token,
                                                      test_counselor_data):
    """
    Try to get leads details by passing wrong mobile number
    """
    response = await http_client_test.put(
        f"/admin/get_lead_detail_by_number?mobile_number=str&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
    assert response.json()["data"] == []
