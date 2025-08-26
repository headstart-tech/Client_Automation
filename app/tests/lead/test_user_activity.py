"""
This file contains test cases related to get user activity
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_user_activity_authentication(http_client_test, test_college_validation, setup_module):
    """
    Check authentication of user by passing wrong token value
    """
    response = await http_client_test.get(
        f"/lead/user_activity/?page_num=1&page_size=25&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": "wrong bearer"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_user_activity(http_client_test, test_college_validation, super_admin_access_token, setup_module):
    """
    Super admin not authorized because of super admin not have college id
    """
    response = await http_client_test.get(
        f"/lead/user_activity/?page_num=1&page_size=25"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_user_activity_check(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Check response success
    """
    response = await http_client_test.get(
        f"/lead/user_activity/?page_num=1&page_size=25"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetched successfully"
