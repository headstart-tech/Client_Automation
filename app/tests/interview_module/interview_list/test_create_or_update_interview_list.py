"""
This file contains test cases of create or update interview list
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_or_update_interview_list(http_client_test,
                                               test_college_validation,
                                               setup_module, access_token,
                                               college_super_admin_access_token,
                                               test_user_validation):
    """
    Different scenarios of test cases for create or update interview list
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/interview/create_or_update_interview_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for create or update interview list
    response = await http_client_test.post(
        f"/interview/create_or_update_interview_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required body for add or update interview list
    response = await http_client_test.post(
        f"/interview/create_or_update_interview_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}

    # No permission for add or update interview list
    response = await http_client_test.post(
        f"/interview/create_or_update_interview_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json={}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Required school_name for add interview list
    response = await http_client_test.post(
        f"/interview/create_or_update_interview_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "school_name must be required and valid."}

    # Required list_name for add interview list
    response = await http_client_test.post(
        f"/interview/create_or_update_interview_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"school_name": "test"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "list_name must be required and valid."}

    # Required course_name for add interview list
    response = await http_client_test.post(
        f"/interview/create_or_update_interview_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"school_name": "test",
                                                                                       "list_name": "test"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "course_name must be required and valid."}

    # Required moderator_id for add interview list
    response = await http_client_test.post(
        f"/interview/create_or_update_interview_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"school_name": "test",
              "list_name": "test",
              "course_name": "test"}
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "moderator_id must be required and valid."}

    # Add interview list
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().interview_list_collection.delete_many({})
    response = await http_client_test.post(
        f"/interview/create_or_update_interview_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"school_name": "test",
              "list_name": "test",
              "course_name": "test",
              "moderator_id": str(
                  test_user_validation.get(
                      "_id"))}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Interview list added."}

    # Required college id for create or update procedure
    response = await http_client_test.post(
        f"/interview/create_or_update_interview_list/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"school_name": "test",
              "list_name": "test1",
              "course_name": "test",
              "moderator_id": str(test_user_validation.get("_id"))}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    # Invalid college id for create or update procedure
    response = await http_client_test.post(
        f"/interview/create_or_update_interview_list/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"school_name": "test",
              "list_name": "test1",
              "course_name": "test",
              "moderator_id": str(test_user_validation.get("_id"))}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    # College not found when try to create or update procedure
    response = await http_client_test.post(
        f"/interview/create_or_update_interview_list/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"school_name": "test",
              "list_name": "test1",
              "course_name": "test",
              "moderator_id": str(test_user_validation.get("_id"))}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Update interview list data
    interview_list = await DatabaseConfiguration().interview_list_collection.find_one(
        {})
    response = await http_client_test.post(
        f"/interview/create_or_update_interview_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&interview_list_id={str(interview_list.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"school_name": "test",
              "list_name": "test1",
              "course_name": "test",
              "moderator_id": str(
                  test_user_validation.get(
                      "_id"))}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Interview list data updated."}

    # Wrong interview list id for update interview list data
    response = await http_client_test.post(
        f"/interview/create_or_update_interview_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&interview_list_id=123456789012&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"school_name": "test",
                                                                                       "list_name": "test1",
                                                                                       "course_name": "test",
                                                                                       "moderator_id": str(
                                                                                           test_user_validation.get(
                                                                                               "_id"))}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Interview list id must be a 12-byte input or a 24-character hex string'

    # Invalid interview list id for update interview list data
    response = await http_client_test.post(
        f"/interview/create_or_update_interview_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&interview_list_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"school_name": "test",
                                                                                       "list_name": "test1",
                                                                                       "course_name": "test",
                                                                                       "moderator_id": str(
                                                                                           test_user_validation.get(
                                                                                               "_id"))}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == \
           "Interview list not found. Make sure provided interview" \
           " list id should be correct."
