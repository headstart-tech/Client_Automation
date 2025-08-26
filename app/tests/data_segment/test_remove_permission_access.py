"""
This file contains test cases of remove permission access API
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_remove_permission_access(
        http_client_test, test_college_validation, access_token,
        college_super_admin_access_token, setup_module, test_create_data_segment_helper, test_user_validation
):
    """
    Different test cases of Remove permission access 
    """
    college_id = str(test_college_validation.get('_id'))
    data_segment_id = str(test_create_data_segment_helper.get("_id"))
    user_id = str(test_user_validation.get("_id"))

    # Not authenticated if user not logged in
    response = await http_client_test.get(
        f"/data_segment/remove_data_segment_permission_access?college_id={college_id}"
        f"&data_segment_id={data_segment_id}&user_id={user_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token
    response = await http_client_test.get(
        f"/data_segment/remove_data_segment_permission_access?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id
    response = await http_client_test.get(
        f"/data_segment/remove_data_segment_permission_access?data_segment_id={data_segment_id}"
        f"&user_id={user_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be "
                                         "required and valid."}

    # Invalid college id
    response = await http_client_test.get(
        f"/data_segment/remove_data_segment_permission_access?college_id=12345678"
        f"&data_segment_id={data_segment_id}&user_id={user_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # College not found
    response = await http_client_test.get(
        f"/data_segment/remove_data_segment_permission_access?college_id=123456789012345678901234"
        f"&data_segment_id={data_segment_id}&user_id={user_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    # Required data segment id
    response = await http_client_test.get(
        f"/data_segment/remove_data_segment_permission_access?college_id={college_id}&user_id={user_id}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Data Segment Id must be "
                                         "required and valid."}

    # Invalid data segment id
    response = await http_client_test.get(
        f"/data_segment/remove_data_segment_permission_access?college_id={college_id}&data_segment_id=12345678"
        f"&user_id={user_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "data_segment_id `12345678` must be a 12-byte input or a 24-character hex string"}

    # data segment not found
    response = await http_client_test.get(
        f"/data_segment/remove_data_segment_permission_access?college_id={college_id}"
        f"&data_segment_id=123456789012345678901234&user_id={user_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "data_segment not found id: 123456789012345678901234"}

    # Required user id
    response = await http_client_test.get(
        f"/data_segment/remove_data_segment_permission_access?college_id={college_id}"
        f"&data_segment_id={data_segment_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "User Id must be "
                                         "required and valid."}

    # Invalid user id
    response = await http_client_test.get(
        f"/data_segment/remove_data_segment_permission_access?college_id={college_id}"
        f"&data_segment_id={data_segment_id}&user_id=12345678&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "user_id `12345678` must be a 12-byte input or a 24-character hex string"}

    # user id not found
    response = await http_client_test.get(
        f"/data_segment/remove_data_segment_permission_access?college_id={college_id}"
        f"&data_segment_id={data_segment_id}&user_id=123456789012345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "user_id not found id: 123456789012345678901234"}

    # Remove permission access
    from app.database.configuration import DatabaseConfiguration
    response = await http_client_test.get(
        f"/data_segment/remove_data_segment_permission_access?college_id={college_id}"
        f"&data_segment_id={data_segment_id}&user_id={user_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Removed Permission access successfully!"
    data_segment = await DatabaseConfiguration().data_segment_collection.find_one(
        {"data_segment_name": "test"}
    )
    shared_with = data_segment.get("shared_with", [])
    user_ids = [user_dict.get("user_id") for user_dict in shared_with if user_dict.get("user_id") == user_id]
    assert user_ids == []
