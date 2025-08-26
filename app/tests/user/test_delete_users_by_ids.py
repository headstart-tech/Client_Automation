"""
This file contains test cases of delete users by ids
"""
import pytest
from app.tests.conftest import user_feature_data
feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_users_by_ids(http_client_test, test_college_validation, setup_module, access_token,
                                   test_user_validation, college_super_admin_access_token, super_admin_access_token):
    """
    Different scenarios of test cases for delete users by ids
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/user/delete_by_ids/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for delete users by ids
    response = await http_client_test.post(
        f"/user/delete_by_ids/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required user_id for delete users by ids
    response = await http_client_test.post(
        f"/user/delete_by_ids/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}

    # No permission for delete users by ids
    response = await http_client_test.post(
        f"/user/delete_by_ids/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json=[str(test_user_validation.get('_id'))]
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Required college id for delete users by ids
    response = await http_client_test.post(
        f"/user/delete_by_ids/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[str(test_user_validation.get('_id'))])
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    # Invalid college id for delete users by ids
    response = await http_client_test.post(
        f"/user/delete_by_ids/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[str(test_user_validation.get('_id'))])
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    # College not found for delete users by ids
    response = await http_client_test.post(
        f"/user/delete_by_ids/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[str(test_user_validation.get('_id'))])
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Delete users by ids
    response = await http_client_test.post(
        f"/user/delete_by_ids/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}&user_id={str(test_user_validation.get('_id'))}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
        json=[str(test_user_validation.get('_id'))]
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Deleted users by ids."}
