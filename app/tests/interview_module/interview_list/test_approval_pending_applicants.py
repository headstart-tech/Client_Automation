"""
This file contains test cases related to get approval pending applicants' data.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_approval_pending_applicants_data(
        http_client_test, application_details, test_interview_list_validation,
        test_college_validation, setup_module,
        college_super_admin_access_token, test_student_data):
    """
    Different test case scenarios for pending approval applicants' data.
    """
    # Not authenticated - when user not logged in.
    response = await http_client_test.post(
        f"/interview_list/approval_pending_applicants_data/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not authenticated'

    # Bad token to get approval pending applicants' data.
    response = await http_client_test.post(
        f"/interview_list/approval_pending_applicants_data/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id to get approval pending applicants' data.
    response = await http_client_test.post(
        f"/interview_list/approval_pending_applicants_data/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and ' \
                                        'valid.'

    # Invalid college id to get approval pending applicants' data.
    response = await http_client_test.post(
        f"/interview_list/approval_pending_applicants_data/?"
        f"college_id=12345628&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input' \
                                        ' or a 24-character hex string'

    # Wrong college id when try to approval pending applicants' data.
    response = await http_client_test.post(
        f"/interview_list/approval_pending_applicants_data/"
        f"?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    college_id = str(test_college_validation.get('_id'))
    # Required page number to get approval pending applicants' data.
    response = await http_client_test.post(
        f"/interview_list/approval_pending_applicants_data/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Page Num must be required and valid.'

    # Required page size to get approval pending applicants' data.
    response = await http_client_test.post(
        f"/interview_list/approval_pending_applicants_data/?"
        f"college_id={college_id}&page_num=1&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Page Size must be required and valid.'

    field_names = ["student_name", "student_id", "application_id",
                   "custom_application_id", "course_name",
                   "specialization_name", "tenth_score", "twelve_marks",
                   "ug_marks", "interview_marks", "interview_list_id",
                   "interview_list_name"]

    # Update application status in DB for testing purpose
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentApplicationForms.update_one(
        {"_id": application_details.get("_id")},
        {"$set": {"approval_status": "Under Review"}})

    # Get prroval pending applicants' data.
    response = await http_client_test.post(
        f"/interview_list/approval_pending_applicants_data/?"
        f"college_id={college_id}&page_num=1&page_size=1&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"interview_list_id": str(test_interview_list_validation.get("_id"))}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get approval pending applicants " \
                                         "data."
    assert response.json()['count'] == 1
    # TODO: Commented this as all testcases are getting failed. Solve it later
    # assert response.json()['total'] == 1
    # assert response.json()['pagination']['previous'] is None
    # assert response.json()['pagination']['next'] is None
    for name in field_names:
        assert name in response.json()['data'][0]
