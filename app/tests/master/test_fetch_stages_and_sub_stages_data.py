"""
This file contains test cases regarding Retrieving Stages and Sub-Stages
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_fetch_stages_and_sub_stages(http_client_test, setup_module, college_super_admin_access_token):
    """
    Test case for retrieving all stages and sub-stages.
    """

    # Not authenticated
    response = await http_client_test.get(f"/master_stages/Retrieve_all_stages_and_sub_stages?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for fetching stages and sub-stages
    response = await http_client_test.get(
        "/master_stages/Retrieve_all_stages_and_sub_stages?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Successful retrieval of stages and sub-stages
    response = await http_client_test.get(
        "/master_stages/Retrieve_all_stages_and_sub_stages?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert "application_form" in response.json()
    assert isinstance(response.json()["application_form"], list)

