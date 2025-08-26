"""
This file contains test cases of add template merge field.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_template_merge_field_not_authenticated(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, access_token
):
    """
    Test cases for add template merge field.
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/templates/add_template_merge_field/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for add template merge field.
    response = await http_client_test.post(
        f"/templates/add_template_merge_field/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required body for add template merge field.
    response = await http_client_test.post(
        f"/templates/add_template_merge_field/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Body must be required and valid."

    # Required field name for add template merge field.
    response = await http_client_test.post(
        f"/templates/add_template_merge_field/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json={}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Field Name must be required " \
                                        "and valid."

    # Required value for add template merge field.
    response = await http_client_test.post(
        f"/templates/add_template_merge_field/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json={"field_name": "test"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Value must be required " \
                                        "and valid."

    # Required college id for add template merge field.
    response = await http_client_test.post(
        f"/templates/add_template_merge_field/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required "
                                         "and valid."}

    # Invalid college id for add template merge field.
    response = await http_client_test.post(
        f"/templates/add_template_merge_field/?college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # College not found for add template merge field.
    response = await http_client_test.post(
        f"/templates/add_template_merge_field/?"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    # No permission for add template merge field.
    response = await http_client_test.post(
        f"/templates/add_template_merge_field/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"field_name": "test", "value": ""}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().template_merge_fields_collection.delete_many(
        {})
    # Add template merge field.
    response = await http_client_test.post(
        f"/templates/add_template_merge_field/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json={"field_name": "test1", "value": "xyz"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Template merge field "
                                          "added successfully."}
