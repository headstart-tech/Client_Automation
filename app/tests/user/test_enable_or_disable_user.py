"""
This file contains test cases for enable or disable user
"""
import pytest
from app.tests.conftest import user_feature_data
feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_user_enable_or_disable(http_client_test, setup_module, super_admin_access_token, test_user_validation,
                                      college_super_admin_access_token):
    """
    Different scenarios of test cases for enable or disable user
    """
    # Not authenticated if user not logged in
    response = await http_client_test.put(f"/user/enable_or_disable/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for enable or disable user
    response = await http_client_test.put(
        f"/user/enable_or_disable/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Field user_id required for enable or disable user
    response = await http_client_test.put(
        f"/user/enable_or_disable/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "User Id must be required and valid."

    # Field is_activated required for enable or disable user
    response = await http_client_test.put(
        f"/user/enable_or_disable/?user_id={str(test_user_validation['_id'])}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Is Activated must be required and valid."

    # Disable user
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().user_collection.update_one({"_id": test_user_validation.get('_id')},
                                                             {'$unset': {'is_activated': True}})
    response = await http_client_test.put(
        f"/user/enable_or_disable/?user_id={str(test_user_validation['_id'])}&"
        f"is_activated=false&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "User status updated."}

    # No changes made for enable or disable user
    response = await http_client_test.put(
        f"/user/enable_or_disable/?user_id={str(test_user_validation['_id'])}&"
        f"is_activated=false&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Unable to update, no changes have been made."

    # Wrong user id for enable or disable user
    response = await http_client_test.put(
        f"/user/enable_or_disable/?user_id=25a9b8774035e93c7ff2466f&"
        f"is_activated=false&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "User id not exist. Provide correct user id."}
