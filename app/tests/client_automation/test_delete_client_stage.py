
"""
This file contains test cases regarding deleting client Stages
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_client_stage(http_client_test, setup_module, college_super_admin_access_token,college_counselor_access_token, test_college_validation,
                                 access_token,test_super_admin_validation, test_client_stages):
    """
    Test case for deleting a client stage by ID.
    """
    stage_id = str(test_client_stages.get("_id"))
    client_id = str(test_college_validation.get("_id"))

    #  Not authenticated
    response = await http_client_test.delete(
        "/client_student_dashboard/delete_client_stage/"
        f"?client_id={client_id}&stage_id={stage_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


    #  Bad token for deleting client stage
    response = await http_client_test.delete(
        "/client_student_dashboard/delete_client_stage/"
        f"?client_id={client_id}&stage_id={stage_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    #  Client stage not found
    invalid_stage_id = "60c72b2f9b1e8b0f1c8e4d99"
    response = await http_client_test.delete(
        "/client_student_dashboard/delete_client_stage/"
        f"?client_id={client_id}&stage_id={invalid_stage_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Stage ID not found"

    # Successful deletion of a Client stage
    from bson import ObjectId
    from app.database.configuration import DatabaseConfiguration

    response = await http_client_test.delete(
        "/client_student_dashboard/delete_client_stage/"
        f"?client_id={client_id}&stage_id={stage_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert response.json()["message"] == "Client stage deleted successfully"

    # Verify that the client stage is actually deleted
    deleted_stage = await DatabaseConfiguration().client_stages.find_one({"_id": ObjectId(stage_id)})
    assert deleted_stage is None