"""
This file contains test cases of update status of interview lists
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
    Different scenarios of test cases for update status of interview lists
    """
    # Not authenticated if user not logged in
    response = await http_client_test.put(
        f"/interview_list/change_status_by_ids/?feature_key={feature_key}"
        f"?college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for update status of interview lists
    response = await http_client_test.put(
        f"/interview_list/change_status_by_ids/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required status for update status of interview lists
    response = await http_client_test.put(
        f"/interview_list/change_status_by_ids/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Status "
                                         "must be required and valid."}

    # Required body for update status of interview lists
    response = await http_client_test.put(
        f"/interview_list/change_status_by_ids/"
        f"?college_id={str(test_college_validation.get('_id'))}&status=closed&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be "
                                         "required and valid."}

    # Update interview list status
    response = await http_client_test.put(
        f"/interview_list/change_status_by_ids/"
        f"?college_id={str(test_college_validation.get('_id'))}"
        f"&status=closed&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json=[str(test_interview_list_validation.get("_id"))]
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Interview lists status updated."}

    # No permission for update status of interview lists
    response = await http_client_test.put(
        f"/interview_list/change_status_by_ids/"
        f"?college_id={str(test_college_validation.get('_id'))}"
        f"&status=closed&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {access_token}"},
        json=[str(test_interview_list_validation.get("_id"))]
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Required college id for update status of interview lists
    response = await http_client_test.put(
        f"/interview_list/change_status_by_ids/?status=closed&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json=[str(test_interview_list_validation.get("_id"))]
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and ' \
                                        'valid.'

    # Invalid college id for update status of interview lists
    response = await http_client_test.put(
        f"/interview_list/change_status_by_ids/?college_id=123&"
        f"status=closed&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json=[str(test_interview_list_validation.get("_id"))]
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input ' \
                                        'or a 24-character hex string'

    # College not found when try to update status of interview lists
    response = await http_client_test.put(
        f"/interview_list/change_status_by_ids/"
        f"?college_id=123456789012345678901234&status=closed&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json=[str(test_interview_list_validation.get("_id"))]
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Wrong interview list id for update interview list data
    response = await http_client_test.put(
        f"/interview_list/change_status_by_ids/"
        f"?college_id={str(test_college_validation.get('_id'))}&status=closed&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"},
        json=["1234"]
    )
    assert response.status_code == 422
    assert response.json()['detail'] == ("Interview list id `1234` must be a"
                                         " 12-byte input or"
                                         " a 24-character hex string")
