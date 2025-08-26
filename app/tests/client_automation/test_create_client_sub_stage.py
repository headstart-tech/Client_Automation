import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_client_sub_stage(http_client_test, college_super_admin_access_token, setup_module, access_token,
                                        test_college_validation, test_super_admin_validation):
    """
    Test case for creating a new client stage.
    """
    # Not authenticated request
    response = await http_client_test.post(f"/client_student_dashboard/create_client_sub_stage?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token
    response = await http_client_test.post(
        f"/client_student_dashboard/create_client_sub_stage?feature_key={feature_key}",
        headers={"Authorization": "Bearer wrong_token"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Successfully creating a client stage
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().client_sub_stages.delete_many({})
    sub_stage_name = "Sample Sub Stage"
    valid_sub_stage_data = {
        "sub_stage_name": sub_stage_name,
        "fields": [
            {
                "name": "field_name",
                "label": "Field 1",
                "type": "text",
                "is_required": True,
                "description": "This is the first field",
                "locked": False,
                "is_custom": False,
                "depends_on": None
            },
            {
                "name": "field_names",
                "label": "Field 2",
                "type": "number",
                "is_required": False,
                "description": "This is the second field",
                "locked": True,
                "is_custom": True,
                "depends_on": "field1"
            }
        ],
    }
    response = await http_client_test.post(
        f"/client_student_dashboard/create_client_sub_stage?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=valid_sub_stage_data,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Client sub-stage created successfully"
    assert "id" in response.json()

    # Sub Stage name already exists for this client
    response = await http_client_test.post(
        f"/client_student_dashboard/create_client_sub_stage?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=valid_sub_stage_data
    )
    assert response.status_code == 422
    assert response.json()["detail"] == f"Sub-stage '{sub_stage_name}' already exists for this client."


