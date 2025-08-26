import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_custom_field(
    http_client_test,
    access_token,
    college_super_admin_access_token,
    setup_module,
    super_admin_access_token,
    test_college_validation,
    test_client_validation,
    test_super_admin_validation,
    test_stages
):
    client_id = str(test_client_validation.get("_id"))
    college_id = str(test_college_validation.get('_id'))

    # Unauthorized Access
    response = await http_client_test.post(f"/client_student_dashboard/custom_field/?client_id={client_id}&college_id={college_id}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Invalid Token
    response = await http_client_test.post(
        "/client_student_dashboard/custom_field/"
        f"?client_id={client_id}&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": "Bearer wrong_token"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

    # Key name is Required
    response = await http_client_test.post(
        f"/client_student_dashboard/custom_field/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
        json={
            "field_name": "test_field",
            "field_type": "text"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Key Name must be required and valid."

    # Duplicate key_name
    valid_field_data = {
        "field_name": "Test Field",
        "field_type": "text",
        "key_name": "test_field",
        "is_mandatory": False,
        "options": [],
        "selectVerification": None,
        "isReadonly": False,
        "editable": True,
        "can_remove": True,
        "defaultValue": None,
        "addOptionsFrom": "API",
        "apiFunction": None,
        "with_field_upload_file": False,
        "separate_upload_API": False
    }
    from bson import ObjectId
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().custom_fields.insert_one({
        **valid_field_data,
        "client_id": ObjectId(client_id)
    })

    # Missing client_id and college_id
    response = await http_client_test.post(
        f"/client_student_dashboard/custom_field/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
        json={
            "field_name": "Missing IDs",
            "field_type": "text",
            "key_name": "missing_ids"
        }
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Either client_id or college_id must be provided."

    # Success case
    from app.database.configuration import DatabaseConfiguration
    DatabaseConfiguration().custom_fields.delete_many({})
    valid_field_data["key_name"] = "unique_key_name"
    valid_field_data["field_name"] = "Another Field"

    response = await http_client_test.post(
        "/client_student_dashboard/custom_field/"
        f"?client_id={client_id}&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
        json=valid_field_data
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Custom field added successfully"

    # file type invalid case
    file_field = valid_field_data.copy()
    file_field.update({
        "key_name": "file_invalid_key",
        "field_name": "File Upload",
        "field_type": "file",
        "with_field_upload_file": False,
        "separate_upload_API": False
    })
    response = await http_client_test.post(
        f"/client_student_dashboard/custom_field/?client_id={client_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
        json=file_field
    )
    assert response.status_code == 422
    assert "must be True" in response.json()["detail"]

    # text type with file upload params
    invalid_text_field = valid_field_data.copy()
    invalid_text_field.update({
        "key_name": "text_with_upload",
        "field_type": "text",
        "with_field_upload_file": True
    })
    response = await http_client_test.post(
        f"/client_student_dashboard/custom_field/?client_id={client_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
        json=invalid_text_field
    )
    assert response.status_code == 422
    assert "only allowed when field_type is 'file'" in response.json()["detail"]
