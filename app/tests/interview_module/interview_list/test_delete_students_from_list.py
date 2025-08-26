"""
This file contains test cases of delete students from interview list
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_student_from_interview_list(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_user_validation,
        application_details):
    """
    Different scenarios of test cases for delete students from interview list
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/interview/delete_students_from_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for delete students from interview list
    response = await http_client_test.post(
        f"/interview/delete_students_from_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required body for delete students from interview list
    response = await http_client_test.post(
        f"/interview/delete_students_from_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Interview List Id must be required and valid."}

    # Required interview list id for delete students from interview list
    response = await http_client_test.post(
        f"/interview/delete_students_from_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json=[]
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Interview List Id must be required and valid."}

    # Add interview list
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().interview_list_collection.delete_many({})
    await http_client_test.post(
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
    interview_list = await DatabaseConfiguration().interview_list_collection.find_one(
        {})
    interview_list_id = str(interview_list.get('_id'))
    application_id = str(application_details.get("_id"))

    # No permission for delete students from interview list
    response = await http_client_test.post(
        f"/interview/delete_students_from_list/?college_id={str(test_college_validation.get('_id'))}&"
        f"interview_list_id={interview_list_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json=[]
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Add students into interview list
    await http_client_test.post(
        f"/interview/add_students_into_list/?college_id={str(test_college_validation.get('_id'))}&"
        f"interview_list_id={interview_list_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[application_id]
    )

    # Add students into interview list
    response = await http_client_test.post(
        f"/interview/delete_students_from_list/?college_id={str(test_college_validation.get('_id'))}&"
        f"interview_list_id={interview_list_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[application_id]
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Students deleted from interview list."}

    # Required college id for delete students from interview list
    response = await http_client_test.post(
        f"/interview/delete_students_from_list/?interview_list_id={application_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[application_id]
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    # Invalid college id for delete students from interview list
    response = await http_client_test.post(
        f"/interview/delete_students_from_list/?college_id=1234567890&interview_list_id={application_id}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[application_id]
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    # College not found when try to delete students from interview list
    response = await http_client_test.post(
        f"/interview/delete_students_from_list/?college_id=123456789012345678901234&"
        f"interview_list_id={interview_list_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[application_id]
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Wrong interview list id for update interview list data
    response = await http_client_test.post(
        f"/interview/delete_students_from_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&interview_list_id=123456789012&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[application_id]
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Interview list id must be a 12-byte input or a 24-character hex string'

    # Invalid interview list id for update interview list data
    response = await http_client_test.post(
        f"/interview/delete_students_from_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&interview_list_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[application_id]
    )
    assert response.status_code == 404
    assert response.json()['detail'] == \
           "Interview list not found. Make sure provided interview list id should be correct."
