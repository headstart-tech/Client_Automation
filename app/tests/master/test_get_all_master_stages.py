"""
This file contains test cases regarding Retrieving Master Stages
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_all_master_stages(http_client_test, setup_module, college_super_admin_access_token):
    """
    Test case for retrieving all master stages.
    """
    # Not authenticated
    response = await http_client_test.get(f"/master_stages/get_all_master_stages?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for fetching master stages
    response = await http_client_test.get(
        f"/master_stages/get_all_master_stages?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Successful retrieval of master stages
    response = await http_client_test.get(
        f"/master_stages/get_all_master_stages?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)