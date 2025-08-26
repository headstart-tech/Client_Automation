
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_client_stage(http_client_test, setup_module, college_super_admin_access_token, test_client_stages):
    """
    Test case for updating a client stage.
    """
    test_stage_id = str(test_client_stages.get("_id"))
    update_data = {
        "stage_name": "Updated Client Stage Name",
        "stage_order": 3,
        "sub_stages": []
    }

    # Not authenticated
    response = await http_client_test.put(
        f"/client_student_dashboard/update_client_stage/{test_stage_id}?feature_key={feature_key}",
        json=update_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Invalid token
    response = await http_client_test.put(
        f"/client_student_dashboard/update_client_stage/{test_stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer invalid_token"},
        json=update_data,
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

    # Client stage not found
    invalid_stage_id = "60c72b2f9b1e8b0f1c8e4d99"  # Non-existent ObjectId
    response = await http_client_test.put(
        f"/client_student_dashboard/update_client_stage/{invalid_stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=update_data,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Client Stage not found"

    # Successful update
    stage_id = str(test_client_stages.get("_id"))
    response = await http_client_test.put(
        f"/client_student_dashboard/update_client_stage/{stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=update_data,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Client stage updated successfully"
