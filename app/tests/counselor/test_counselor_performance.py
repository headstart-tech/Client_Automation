"""
This file contains test cases related to API route/endpoint
counselor performance report
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_counsellor_performance_not_authenticate(
        http_client_test, setup_module, test_college_validation
):
    """
    Not authenticate for get counselor performance
    """
    response = await http_client_test.put(
        f"/counselor/counselor_performance?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": "wrong Bearer"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_counsellor_performance_no_permission(
        http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token
):
    """
    No permission get counselor performance
    """
    response = await http_client_test.put(
        f"/counselor/counselor_performance?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {'detail': 'Not enough permissions'}


@pytest.mark.asyncio
async def test_counsellor_performance(
        http_client_test, setup_module, test_college_validation,
        college_counselor_access_token
):
    """
    No permission get counselor performance
    """
    response = await http_client_test.put(
        f"/counselor/counselor_performance?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
    )
    assert response.status_code == 200
