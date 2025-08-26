"""
This file contains test cases of create new user
"""
import pytest
from app.tests.conftest import user_feature_data
feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_new_user(
        http_client_test, setup_module,
        test_college_validation, test_counselor_data,
        college_super_admin_access_token, access_token,
        test_course_validation):
    """
    Different scenarios of test case for create new user
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(f"/user/create_new_user/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for create new user
    response = await http_client_test.post(
        f"/user/create_new_user/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Field required for create new user
    response = await http_client_test.post(
        f"/user/create_new_user/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "User Type must be required and"
                                         " valid."}

    field_names = ["email", "first_name", "middle_name", "last_name",
                   "mobile_number", "associated_colleges", "role_name",
                   "role_id", "last_accessed", "created_on", "created_by",
                   "is_activated", "associated_source_value", "user_type"]

    # Create new counselor
    test_counselor_data.update({"email": "testcounselor@example.com"})
    response = await http_client_test.post(
        f"/user/create_new_user/?user_type=college_counselor&college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=test_counselor_data,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User created successfully."
    for name in field_names:
        assert name in response.json()['data'][0]

    # User already exist
    response = await http_client_test.post(
        f"/user/create_new_user/?user_type=college_counselor&college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=test_counselor_data,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "user_name already exists!"

    # Create new panelist
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().user_collection.delete_one(
        {"role.role_name": "panelist"})
    test_counselor_data.update(
        {"email": "testpanelist@example.com", "designation": "Test",
         "school_name": "test", "selected_programs":
             [f"{test_course_validation.get('course_name')} in "
              f"{test_course_validation.get('course_specialization')[0]}"]})
    response = await http_client_test.post(
        f"/user/create_new_user/?user_type=panelist&college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=test_counselor_data
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User created successfully."
    for name in field_names:
        assert name in response.json()['data'][0]

    # Create new moderator
    test_counselor_data.update({"email": "testmoderator@example.com"})
    response = await http_client_test.post(
        f"/user/create_new_user/?user_type=moderator&college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=test_counselor_data
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User created successfully."
    for name in field_names:
        assert name in response.json()['data'][0]

    # Create new moderator
    test_counselor_data.update(
        {"email": "testauthorized_approver@example.com"})
    response = await http_client_test.post(
        "/user/create_new_user/?user_type=authorized_approver&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_counselor_data
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User created successfully."
    for name in field_names:
        assert name in response.json()['data'][0]
