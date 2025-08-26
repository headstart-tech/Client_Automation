"""
This file contains test cases regarding Retrieving Master Sub Stage By ID
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_master_stage(http_client_test, setup_module, college_super_admin_access_token,test_master_stages):
    """
    Test case for retrieving a specific master stage by ID.
    """
    stage_id = str(test_master_stages["_id"])

    # Not authenticated
    response = await http_client_test.get(f"/master_stages/get_master_stage/{stage_id}?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for fetching master stage
    response = await http_client_test.get(
        f"/master_stages/get_master_stage/{stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Master stage not found
    invalid_stage_id = "60c72b2f9b1e8b0f1c8e4d99"  # Non-existent ObjectId
    response = await http_client_test.get(
        f"/master_stages/get_master_stage/{invalid_stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Master stage not found"

    # Successful retrieval of a master stage
    from app.database.configuration import DatabaseConfiguration

    stage = await DatabaseConfiguration().stages.find_one({})
    stage_id = str(stage.get("_id"))
    response = await http_client_test.get(
        f"/master_stages/get_master_stage/{stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert "stage_name" in response.json()
