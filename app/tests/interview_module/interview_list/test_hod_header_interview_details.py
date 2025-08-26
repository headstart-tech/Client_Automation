"""
This file contains test cases of get summary of interview applicants
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_summary_of_interview_applicants(
        http_client_test, test_college_validation,
        college_super_admin_access_token, setup_module, access_token):
    """
    Different scenarios of test cases for get summary of interview
    applicants.

    Params:
        - http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        - test_interview_list_validation: A fixture useful for get interview
            list data.
        - test_college_validation: A fixture useful for get college data.
        - setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.

    Assertions:
        - response status code and json message
    """
    # Not authenticated when user not logged in
    response = await http_client_test.get(
        f"/interview/get_hod_header/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not authenticated'

    # Try to get summary of interview applicants using wrong token
    response = await http_client_test.get(
        f"/interview/get_hod_header/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"authorization": f"Bearer wrong"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Unauthorized user try to get summary of interview applicants
    response = await http_client_test.get(
        f"/interview/get_hod_header/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"authorization": f"Bearer {access_token}"})
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not enough permissions'

    # Get summary of interview applicants
    response = await http_client_test.get(
        f"/interview/get_hod_header/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    for name in ["interview_done", "selected_candidate", "pending_for_review",
                 "rejected_candidate"]:
        assert name in response.json()
