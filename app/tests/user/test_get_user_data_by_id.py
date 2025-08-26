"""
This file contains test cases for get user data by id.
"""
import pytest
from app.tests.conftest import user_feature_data
feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_user_data_by_id(
        http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token, test_panelist_validation,
        access_token
):
    """
    Different test cases for get user data by id.
    """
    # Not authenticated if user not logged in
    response = await http_client_test.get("/user/get_data_by_id/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get user data by id
    response = await http_client_test.get(
        f"/user/get_data_by_id/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for get user data by id
    response = await http_client_test.get(
        f"/user/get_data_by_id/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "College Id must be required and " \
                                        "valid."

    # Required user id for get user data by id
    response = await http_client_test.get(
        f"/user/get_data_by_id/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "User Id must be required and " \
                                        "valid."

    # No permission for get user data by id
    response = await http_client_test.get(
        f"/user/get_data_by_id/?"
        f"user_id={str(test_panelist_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"

    # Get user data by id
    response = await http_client_test.get(
        f"/user/get_data_by_id/?"
        f"user_id={str(test_panelist_validation.get('_id'))}&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get user data."
    for name in ["id", "email", "first_name", "middle_name", "last_name",
                 "mobile_number", "associated_colleges", "role_name",
                 "role_id", "last_accessed", "created_on", "created_by",
                 "is_activated", "associated_source_value", "user_type",
                 "designation", "school_name", "selected_programs",
                 "interview_taken", "selected_students", "rejected_students",
                 "selection_ratio"]:
        assert name in response.json()["data"]

    # Invalid college id for get user data by id
    response = await http_client_test.get(
        f"/user/get_data_by_id/?"
        f"user_id={str(test_panelist_validation.get('_id'))}&"
        f"college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College id must be a 12-byte input" \
                                        " or a 24-character hex string"

    # Wrong college id for get user data by id
    response = await http_client_test.get(
        f"/user/get_data_by_id/?"
        f"user_id={str(test_panelist_validation.get('_id'))}&"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College not found."

    # Invalid user id for get user data by id
    response = await http_client_test.get(
        f"/user/get_data_by_id/?"
        f"user_id=123&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "User id must be a 12-byte input" \
                                        " or a 24-character hex string"

    # Wrong college id for get user data by id
    response = await http_client_test.get(
        f"/user/get_data_by_id/?"
        f"user_id=123456789012345678901234&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."
