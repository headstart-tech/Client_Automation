import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_activation_status_of_college(http_client_test, college_super_admin_access_token, test_college_validation):
    """
    Test case for updating the activation status of a college.
    """
    college_id = str(test_college_validation.get("_id"))

    # Not authenticated
    response = await http_client_test.post(f"/client_automation/update_activation_status_of_college"
                                           f"?college_id={college_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Invalid token
    response = await http_client_test.post(
        f"/client_automation/update_activation_status_of_college?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": "Bearer wrong_token"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

    # Missing is_activated field
    response = await http_client_test.post(
        f"/client_automation/update_activation_status_of_college?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={},  # Missing required field
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Is Activated must be required and valid."

    # Valid request - Activate college
    response = await http_client_test.post(
        f"/client_automation/update_activation_status_of_college?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"is_activated": True},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "College Activation status updated successfully"

    # Valid request - Deactivate college
    response = await http_client_test.post(
        f"/client_automation/update_activation_status_of_college?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"is_activated": False},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "College Activation status updated successfully"

    # Non-existent college ID
    non_existent_college_id = "64f5b10a87d94f001e5a1234"
    response = await http_client_test.post(
        f"/client_automation/update_activation_status_of_college"
        f"?college_id={non_existent_college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"is_activated": True},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "College not found"