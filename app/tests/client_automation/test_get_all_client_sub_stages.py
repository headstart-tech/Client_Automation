"""
This file contains test cases regarding Retrieving Client Sub Stages
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_all_client_sub_stages(http_client_test, college_super_admin_access_token):
    """
    Test case for retrieving all client sub-stages.
    """

    # Not authenticated
    response = await http_client_test.get(f"/client_student_dashboard/get_all_client_sub_stages/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for fetching client sub-stages
    response = await http_client_test.get(
        f"/client_student_dashboard/get_all_client_sub_stages/?feature_key={feature_key}",
        headers={"Authorization": "Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Successful retrieval of client sub-stages
    response = await http_client_test.get(
        f"/client_student_dashboard/get_all_client_sub_stages/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)