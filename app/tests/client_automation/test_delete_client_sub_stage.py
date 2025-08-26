"""
This file contains test cases regarding Deleting Client Sub Stages
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_client_sub_stage(http_client_test, setup_module,
                                       college_super_admin_access_token, access_token,
                                       test_college_validation, test_super_admin_validation):
    """
    Test case for deleting a client sub-stage by ID.
    """

    sub_stage_id = "60c72b2f9b1e8b0f1c8e4d62"

    # Not authenticated
    response = await http_client_test.delete(
        f"/client_student_dashboard/delete_client_sub_stage/?sub_stage_id={sub_stage_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for deleting client sub-stage
    response = await http_client_test.delete(
        f"/client_student_dashboard/delete_client_sub_stage/?sub_stage_id={sub_stage_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Client sub-stage not found
    invalid_sub_stage_id = "60c72b2f9b1e8b0f1c8e4d99"
    response = await http_client_test.delete(
        "/client_student_dashboard/delete_client_sub_stage/"
        f"?sub_stage_id={invalid_sub_stage_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Client sub-stage not found"

    # Successful deletion of a client sub-stage
    from bson import ObjectId
    from app.database.configuration import DatabaseConfiguration
    sub_stage = await DatabaseConfiguration().client_sub_stages.find_one({})
    if not sub_stage:
        pytest.skip("No sub-stage found in the database to delete.")

    sub_stage_id = str(sub_stage["_id"])

    response = await http_client_test.delete(
        "/client_student_dashboard/delete_client_sub_stage/"
        f"?sub_stage_id={sub_stage_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert response.json()["message"] == "Client sub-stage deleted successfully"

    # Verify that the sub-stage is actually deleted
    deleted_sub_stage = await DatabaseConfiguration().sub_stages.find_one(
        {"_id": ObjectId(sub_stage_id)})
    assert deleted_sub_stage is None
