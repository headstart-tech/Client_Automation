"""
This file contains test cases regarding deleting Master Stages
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_master_stage(http_client_test, setup_module, college_super_admin_access_token):
    """
    Test case for deleting a master stage by ID.
    """

    stage_id = "60c72b2f9b1e8b0f1c8e4d62"

    #  Not authenticated
    response = await http_client_test.delete(f"/master_stages/delete_master_stage/{stage_id}?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    #  Bad token for deleting master stage
    response = await http_client_test.delete(
        f"/master_stages/delete_master_stage/{stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    #  Master stage not found
    invalid_stage_id = "60c72b2f9b1e8b0f1c8e4d99"
    response = await http_client_test.delete(
        f"/master_stages/delete_master_stage/{invalid_stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Stage not found"

    # Successful deletion of a master stage
    from bson import ObjectId
    from app.database.configuration import DatabaseConfiguration
    stage = await DatabaseConfiguration().stages.find_one({})
    if not stage:
        pytest.skip("No stage found in the database to delete.")

    stage_id = str(stage["_id"])

    response = await http_client_test.delete(
        f"/master_stages/delete_master_stage/{stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert response.json()["message"] == "Stage deleted successfully"

    # Verify that the stage is actually deleted
    deleted_stage = await DatabaseConfiguration().stages.find_one({"_id": ObjectId(stage_id)})
    assert deleted_stage is None
