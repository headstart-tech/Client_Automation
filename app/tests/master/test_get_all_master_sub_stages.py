"""
This file contains test cases regarding Retrieving Master Sub Stages
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_all_master_sub_stages(http_client_test, college_super_admin_access_token):
    """
    Test case for retrieving all master sub-stages.
    """

    # Not authenticated
    response = await http_client_test.get(f"/master_stages/get_all_master_sub_stages?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for fetching master sub-stages
    response = await http_client_test.get(
        f"/master_stages/get_all_master_sub_stages?feature_key={feature_key}",
        headers={"Authorization": "Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Successful retrieval of master sub-stages
    response = await http_client_test.get(
        f"/master_stages/get_all_master_sub_stages?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Ensure response contains expected fields
    if response.json():  # Check if there are sub-stages in the response
        first_sub_stage = response.json()[0]
        assert "sub_stage_name" in first_sub_stage
        assert "fields" in first_sub_stage
        assert isinstance(first_sub_stage["fields"], list)

        if first_sub_stage["fields"]:  # Check if there are fields
            first_field = first_sub_stage["fields"][0]
            assert "name" in first_field
            assert "label" in first_field
            assert "type" in first_field
            assert "is_required" in first_field
            assert "description" in first_field
            assert "locked" in first_field
            assert "is_custom" in first_field
            assert "depends_on" in first_field