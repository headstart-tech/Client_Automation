"""
This file contains test cases regarding Updation of  Master Stages
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_master_stage(http_client_test, setup_module, college_super_admin_access_token,test_master_stages):
    """
    Test case for updating a master stage.
    """
    test_stage_id = str(test_master_stages.get("_id"))
    update_data = {
        "stage_name": "Updated Stage Name",
        "stage_order": 2,
        "sub_stages": []
    }
    # Not authenticated
    response = await http_client_test.put(
        f"/master_stages/update_master_stage/{test_stage_id}?feature_key={feature_key}", json=update_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for updating master stage
    response = await http_client_test.put(
        f"/master_stages/update_master_stage/{test_stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
        json=update_data,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Master stage not found
    invalid_stage_id = "60c72b2f9b1e8b0f1c8e4d99"  # Non-existent ObjectId
    response = await http_client_test.put(
        f"/master_stages/update_master_stage/{invalid_stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=update_data,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Stage not found"

    # Successful update
    from app.database.configuration import DatabaseConfiguration

    stages = await DatabaseConfiguration().stages.find_one({})
    stage_id = str(stages.get("_id"))
    update_data["stage_id"]=[test_stage_id]
    response = await http_client_test.put(
        f"/master_stages/update_master_stage/{stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=update_data,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Master stage updated successfully"