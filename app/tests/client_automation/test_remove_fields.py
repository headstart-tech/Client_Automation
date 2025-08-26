
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_remove_fields(http_client_test, college_super_admin_access_token, test_college_validation,test_remove_field
                             ):
    """
    Test case for removing fields from a client section.
    """
    client_id = str(test_college_validation.get("_id"))
    # Not authenticated request
    response = await http_client_test.post(f"/client_student_dashboard/remove_fields?client_id={client_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token
    response = await http_client_test.post(
        f"/client_student_dashboard/remove_fields?client_id={client_id}&feature_key={feature_key}",
        headers={"Authorization": "Bearer wrong_token"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Client does not exist
    non_existent_client_id = "67d96299812f11f7423387c4"
    response = await http_client_test.post(
        f"/client_student_dashboard/remove_fields?client_id={non_existent_client_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"section_title": "Personal Details", "key_names": ["Declaration"]}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found"

    # Section does not exist
    response = await http_client_test.post(
        f"/client_student_dashboard/remove_fields?client_id={client_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"section_title": "NonExistentSection", "key_names": ["Declaration"]}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Section not found"

    # Section Title is Required
    response = await http_client_test.post(
        f"/client_student_dashboard/remove_fields?client_id={client_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"section_title": None, "key_names": ["Declaration"]}
    )

    assert response.status_code == 400
    response_json = response.json()
    assert "detail" in response_json
    assert response_json["detail"] == "Section Title must be required and valid."


    # Field cannot be removed
    response = await http_client_test.post(
        f"/client_student_dashboard/remove_fields?client_id={client_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"section_title": "Personal Details", "key_names": ["caste"]}
    )
    assert response.status_code == 404
    response_json = response.json()
    assert "detail" in response_json

    valid_request_data = {
        "section_title": "Additional Details",
        "key_names": ["aadhar_number"]
    }

    # Field Removed Successfully
    response = await http_client_test.post(
        f"/client_student_dashboard/remove_fields?client_id={client_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=valid_request_data,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Fields removed successfully"

    response = await http_client_test.post(
        f"/client_student_dashboard/remove_fields?client_id={client_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"section_title": "Additional Details", "key_names": ["Declaration"]}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Specified fields in the section not found"