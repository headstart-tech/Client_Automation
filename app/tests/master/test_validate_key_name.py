"""
This file contains test cases regarding Field Name Validation in Sub-Stages
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_validate_key_name(http_client_test, setup_module, college_super_admin_access_token,test_college_validation ,test_unique_key_name):
    """
    Test case for validating uniqueness of a key name
    """
    client_id = str(test_college_validation.get('_id'))
    college_id = str(test_college_validation.get('_id'))
    # Not authenticated
    response = await http_client_test.post(
        f"/master_stages/validate_key_name?client_id={client_id}&college_id={college_id}&feature_key={feature_key}",
        params={"key_name": "first_name"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for validating key name
    response = await http_client_test.post(
        f"/master_stages/validate_key_name?client_id={client_id}&college_id={college_id}&feature_key={feature_key}",
        params={"key_name": "first_name"},
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


    # Invalid Key Name Format (Not snake_case)
    response = await http_client_test.post(
        f"/master_stages/validate_key_name?clientId={client_id}&collegeId={college_id}&feature_key={feature_key}",
        params={"key_name": "InvalidKeyName#"},
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid format. Key name should be in snake_case format (e.g., 'name_1')."

    # Valid Key Name with Underscore
    response = await http_client_test.post(
        f"/master_stages/validate_key_name?clientId={client_id}&collegeId={college_id}&feature_key={feature_key}",
        params={"key_name": "unique_field"},
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Key name is unique"}

    # Completely New Key Name
    response = await http_client_test.post(
        f"/master_stages/validate_key_name?clientId={client_id}&collegeId={college_id}&feature_key={feature_key}",
        params={"key_name": "totally_new_field"},
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Key name is unique"}
