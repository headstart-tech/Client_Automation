
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_relocate_field(http_client_test, college_super_admin_access_token, test_college_validation,
                              setup_module, access_token, test_super_admin_validation, test_stages):
    """
    Test case for relocating a field within sections.
    """
    client_id = str(test_college_validation.get('_id'))
    college_id = str(test_college_validation.get('_id'))

    # Not authenticated request
    response = await http_client_test.patch(f"/client_student_dashboard/relocate_field"
                                            f"?client_id={client_id}&college_id={college_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token
    response = await http_client_test.patch(
        f"/client_student_dashboard/relocate_field"
        f"?client_id={client_id}&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": "Bearer wrong_token"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Source Section Not Found
    invalid_source_data = {
        "source_section_name": "Invalid Section",
        "destination_section_name": "Parent/Guardians/Spouse Details",
        "key_name": "middle_name"
    }
    response = await http_client_test.patch(
        f"/client_student_dashboard/relocate_field"
        f"?client_id={client_id}&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=invalid_source_data
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Source section not found"

    # Destination Section Not Found
    invalid_destination_data = {
        "source_section_name": "Personal Details",
        "destination_section_name": "Invalid Destination",
        "key_name": "middle_name"
    }
    response = await http_client_test.patch(
        f"/client_student_dashboard/relocate_field"
        f"?client_id={client_id}&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=invalid_destination_data
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Destination section not found"

     # Successfully moving middle_name field
    move_middle_name = {
        "source_section_name": "Personal Details",
        "destination_section_name": "Parent/Guardians/Spouse Details",
        "key_name": "middle_name"
    }
    response = await http_client_test.patch(
        f"/client_student_dashboard/relocate_field"
        f"?client_id={client_id}&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=move_middle_name
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Field moved successfully"
    assert response.json()["field_name"] == "middle_name"

    #  Move it back to original section
    revert_middle_name = {
        "source_section_name": "Parent/Guardians/Spouse Details",
        "destination_section_name": "Personal Details",
        "key_name": "middle_name"
    }
    response = await http_client_test.patch(
        f"/client_student_dashboard/relocate_field"
        f"?client_id={client_id}&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=revert_middle_name
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Field moved successfully"
    assert response.json()["field_name"] == "middle_name"

    # Field is Locked
    locked_field_data = {
        "source_section_name": "Personal Details",
        "destination_section_name": "Parent/Guardians/Spouse Details",
        "key_name": "first_name"
    }
    response = await http_client_test.patch(
        f"/client_student_dashboard/relocate_field"
        f"?client_id={client_id}&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=locked_field_data
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Field 'first_name' is locked"