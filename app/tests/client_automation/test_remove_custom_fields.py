import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_remove_fields(
    http_client_test,
    access_token,
    college_super_admin_access_token,
    setup_module,
    super_admin_access_token,
    test_college_validation,
        test_client_validation,
    test_super_admin_validation,
    test_remove_custom_field
):
    """
    Test case for the updated remove_custom_fields endpoint.
    """
    client_id = str(test_client_validation.get("_id"))
    college_id = str(test_college_validation.get("_id"))

    # 1. Not authenticated request
    response = await http_client_test.delete(
        f"/client_student_dashboard/remove_custom_field"
        f"?client_id={client_id}&college_id={college_id}&key_name=test_field&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # 2. Bad token
    response = await http_client_test.delete(
        f"/client_student_dashboard/remove_custom_field"
        f"?client_id={client_id}&college_id={college_id}&key_name=test_field&feature_key={feature_key}",
        headers={"Authorization": "Bearer wrong_token"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

    # 3. Missing both client_id and college_id
    response = await http_client_test.delete(
        "/client_student_dashboard/remove_custom_field?key_name=test_field&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Either client_id or college_id must be provided."

    # 4. No key_name provided
    response = await http_client_test.delete(
        f"/client_student_dashboard/remove_custom_field"
        f"?client_id={client_id}&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Key Name must be required and valid."

    # 5. Client does not exist
    non_existent_client_id = "67d96299812f11f7423387c4"
    response = await http_client_test.delete(
        f"/client_student_dashboard/remove_custom_field"
        f"?client_id={non_existent_client_id}&key_name=test_field&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found"

    # 6. College does not exist
    non_existent_college_id = "67d96299812f11f7423387c4"
    response = await http_client_test.delete(
        f"/client_student_dashboard/remove_custom_field"
        f"?college_id={non_existent_college_id}&key_name=test_field&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "College not found"

    # 7. Field removed successfully
    valid_field_name = test_remove_custom_field["key_name"]

    response = await http_client_test.delete(
        f"/client_student_dashboard/remove_custom_field"
        f"?college_id={college_id}&key_name={valid_field_name}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["message"] == "Field removed successfully"
    assert valid_field_name == response_json["removed_field"]