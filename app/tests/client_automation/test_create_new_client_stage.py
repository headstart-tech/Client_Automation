import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_new_client_stage(http_client_test, college_super_admin_access_token, setup_module, access_token,
                                        test_college_validation, test_super_admin_validation,):
    """
    Test case for creating a new client stage.
    """
    # Not authenticated request
    response = await http_client_test.post(f"/client_student_dashboard/create_client_stage?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token
    response = await http_client_test.post(
        f"/client_student_dashboard/create_client_stage?feature_key={feature_key}",
        headers={"Authorization": "Bearer wrong_token"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Successfully creating a client stage
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().client_stages.delete_many({})
    valid_stage_data = {
        "stage_name": "Sample Stage",
        "stage_order": 1,
        "description": "Declaration of the Student",
        "sub_stages": []
    }

    response = await http_client_test.post(
        f"/client_student_dashboard/create_client_stage?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=valid_stage_data,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Client stage created successfully"
    assert "id" in response.json()

    # Stage name already exists for this client
    response = await http_client_test.post(
        f"/client_student_dashboard/create_client_stage?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=valid_stage_data
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Stage name already exists for this client"