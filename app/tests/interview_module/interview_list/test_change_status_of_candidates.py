"""
This file contains test cases of change the status of interview candidates
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_status_of_interview_lists(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_user_validation,
        application_details, test_interview_list_validation):
    """
    Different scenarios of test cases for Change the status of interview
    candidates.
    """
    college_id = str(test_college_validation.get('_id'))
    application_id = str(application_details.get("_id"))
    interview_list_id = str(test_interview_list_validation.get("_id"))
    data = {"interview_list_id": interview_list_id,
            "application_ids": [application_id], "status": "Interviewed"}

    # Not authenticated if user not logged in
    response = await http_client_test.put(
        f"/interview_list/change_interview_status_of_candidates/"
        f"?college_id={college_id}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for change the status of interview candidates
    response = await http_client_test.put(
        f"/interview_list/change_interview_status_of_candidates/"
        f"?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required body for change the status of interview candidates
    response = await http_client_test.put(
        f"/interview_list/change_interview_status_of_candidates/"
        f"?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}

    # Required interview list id for change the status of interview candidates
    response = await http_client_test.put(
        f"/interview_list/change_interview_status_of_candidates/"
        f"?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"}, json={}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Interview List Id must be "
                                         "required and valid."}

    # Required application_ids for change the status of interview candidates
    response = await http_client_test.put(
        f"/interview_list/change_interview_status_of_candidates/"
        f"?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json={"interview_list_id": interview_list_id}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Application Ids must be "
                                         "required and valid."}

    # Required status for change the status of interview candidates
    response = await http_client_test.put(
        f"/interview_list/change_interview_status_of_candidates/"
        f"?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json={"interview_list_id": interview_list_id,
              "application_ids": [application_id]}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Status must be "
                                         "required and valid."}

    # Invalid status for change the status of interview candidates
    response = await http_client_test.put(
        f"/interview_list/change_interview_status_of_candidates/"
        f"?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json={"interview_list_id": interview_list_id,
              "application_ids": [application_id], "status": "test"}
    )
    assert response.status_code == 400
    assert response.json() == \
           {"detail": "Status must be required and valid."}

    # Invalid application id for change the status of interview candidates
    response = await http_client_test.put(
        f"/interview_list/change_interview_status_of_candidates/"
        f"?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"interview_list_id": interview_list_id,
              "application_ids": ["123"], "status": "Interviewed"}
    )
    assert response.status_code == 422
    assert response.json() == \
           {"detail": "Application id `123` must be a 12-byte input or a "
                      "24-character hex string"}

    # Update interview status of candidates
    response = await http_client_test.put(
        f"/interview_list/change_interview_status_of_candidates/"
        f"?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json=data
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Updated the status of candidates."}

    # No permission for change the status of interview candidates
    response = await http_client_test.put(
        f"/interview_list/change_interview_status_of_candidates/"
        f"?college_id={college_id}&feature_key={feature_key}"
        f"",
        headers={"Authorization":
                     f"Bearer {access_token}"},
        json=data
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Required college id for change the status of interview candidates
    response = await http_client_test.put(
        f"/interview_list/change_interview_status_of_candidates/?feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json=data
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and ' \
                                        'valid.'

    # Invalid college id for change the status of interview candidates
    response = await http_client_test.put(
        f"/interview_list/change_interview_status_of_candidates/?"
        f"college_id=123&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json=data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input ' \
                                        'or a 24-character hex string'

    # College not found when try to change the status of interview candidates
    response = await http_client_test.put(
        f"/interview_list/change_interview_status_of_candidates/"
        f"?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json=data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Update approval status of candidates
    response = await http_client_test.put(
        f"/interview_list/change_interview_status_of_candidates/"
        f"?college_id={college_id}&is_approval_status=true&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json=data
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Updated the status of candidates."}

    # Invalid interview list id for change the status of interview candidates
    response = await http_client_test.put(
        f"/interview_list/change_interview_status_of_candidates/"
        f"?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"interview_list_id": "123",
              "application_ids": [application_id], "status": "Interviewed"}
    )
    assert response.status_code == 422
    assert response.json() == \
           {"detail": "Interview list id `123` must be a 12-byte input or a "
                      "24-character hex string"}

    # Interview list not found for change the status of interview candidates
    response = await http_client_test.put(
        f"/interview_list/change_interview_status_of_candidates/"
        f"?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"interview_list_id": "123456789012345678901234",
              "application_ids": [application_id], "status": "Interviewed"}
    )
    assert response.status_code == 404
    assert response.json() == \
           {"detail": "Interview list not found"}
