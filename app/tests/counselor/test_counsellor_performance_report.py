"""
This file contains test cases related to API route/endpoint counselor performance report
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_counsellor_performance_report_not_authenticate(
        http_client_test, setup_module, test_college_validation
):
    """
    Not authenticate for get counselor performance report
    """
    response = await http_client_test.put(
        f"/counselor/counsellor_performance_report"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": "wrong Bearer"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_counsellor_performance_report(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Get counselor performance report
    """
    response = await http_client_test.put(
        f"/counselor/counsellor_performance_report"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetched successfully"
