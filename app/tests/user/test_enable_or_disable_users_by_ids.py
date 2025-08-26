"""
This file contains test cases of update statuses of users
"""
import pytest
from app.tests.conftest import user_feature_data
feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_enable_or_disable_users(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_user_validation):
    """
    Different scenarios of test cases for update statuses of users
    """
    # Not authenticated if user not logged in
    response = await http_client_test.put(
        f"/user/enable_or_disable_users/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for update statuses of users
    response = await http_client_test.put(
        f"/user/enable_or_disable_users/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required status for update statuses by ids
    response = await http_client_test.put(
        f"/user/enable_or_disable_users/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Is Activated must be required and "
                                         "valid."}

    # Required body for update statuses by ids
    response = await http_client_test.put(
        f"/user/enable_or_disable_users/?is_activated=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}

    user_id = str(test_user_validation.get('_id'))
    # No permission for get selection procedure id
    response = await http_client_test.put(
        f"/user/enable_or_disable_users/?is_activated=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=[user_id]
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Update statuses of users
    response = await http_client_test.put(
        f"/user/enable_or_disable_users/?is_activated=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=[user_id]
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Updated status of users."}

    # Invalid user id for update status of user
    response = await http_client_test.put(
        f"/user/enable_or_disable_users/?is_activated=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=["123"]
    )
    assert response.status_code == 422
    assert response.json()["detail"] == 'User id `123` must be a 12-byte ' \
                                        'input or a 24-character hex string'
