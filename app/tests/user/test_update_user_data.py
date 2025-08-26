"""
This file contains test cases regarding update user data
"""
import pytest
from app.tests.conftest import user_feature_data
feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_user_info(http_client_test, test_college_validation, setup_module, access_token,
                                test_user_validation, college_super_admin_access_token, super_admin_access_token):
    """
    Different scenarios of test cases regarding update user info
    """
    # Not authenticated if user not logged in
    response = await http_client_test.put(
        f"/user/update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for update user data
    response = await http_client_test.put(
        f"/user/update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required user_id for update user data
    response = await http_client_test.put(
        f"/user/update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "User Id must be required and valid."}

    # No permission for update user data
    response = await http_client_test.put(
        f"/user/update/?college_id={str(test_college_validation.get('_id'))}"
        f"&user_id={str(test_user_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json={"first_name": "test"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Required college id for update user data
    response = await http_client_test.put(
        f"/user/update/?user_id={str(test_user_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"first_name": "test"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    # Invalid college id for update user data
    response = await http_client_test.put(
        f"/user/update/?college_id=1234567890"
        f"&user_id={str(test_user_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"first_name": "test"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    # College not found for update user data
    response = await http_client_test.put(
        f"/user/update/?college_id=123456789012345678901234"
        f"&user_id={str(test_user_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"first_name": "test"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # User not found for update info
    response = await http_client_test.put(
        f"/user/update/?college_id={str(test_college_validation.get('_id'))}"
        f"&user_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"first_name": "test"}
    )
    assert response.status_code == 200
    assert response.json() == {'detail': "User not found. Make sure provided user id should be correct."}

    # Invalid user id for update user info
    response = await http_client_test.put(
        f"/user/update/?college_id={str(test_college_validation.get('_id'))}"
        f"&user_id=12345678901234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"first_name": "test"}
    )
    assert response.status_code == 422
    assert response.json() == {'detail': "User id must be a 12-byte input or a 24-character hex string"}

    # Update user info
    response = await http_client_test.put(
        f"/user/update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
        f"&user_id={str(test_user_validation.get('_id'))}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}, json={"first_name": "Test"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "User data updated."}
