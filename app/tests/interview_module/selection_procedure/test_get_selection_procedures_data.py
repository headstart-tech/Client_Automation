"""
This file contains test cases of get selection procedures data
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_selection_procedures_data(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation):
    """
    Different scenarios of test cases for get selection procedures data
    """
    # Not authenticated if user not logged in
    response = await http_client_test.get(
        f"/interview/selection_procedures/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get selection procedures data
    response = await http_client_test.get(
        f"/interview/selection_procedures/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required page number for get selection procedures data
    response = await http_client_test.get(
        f"/interview/selection_procedures/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Num must be required and valid."}

    # Required procedure id for get selection procedures data
    response = await http_client_test.get(
        f"/interview/selection_procedures/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Size must be required and valid."}

    # Delete selection procedures if any
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().selection_procedure_collection.delete_many({})

    # No selection procedures found
    response = await http_client_test.get(
        f"/interview/selection_procedures/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get Selection procedure data."
    assert response.json()['total'] == 0
    assert response.json()['count'] == 1
    assert response.json()['pagination']["next"] is None
    assert response.json()['pagination']["previous"] is None
    assert response.json()['data'] == []

    # Create selection procedure
    await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"course_name": "test",
                                                                                       "offer_letter": {
                                                                                           "template": "test",
                                                                                           "authorized_approver": str(
                                                                                               test_user_validation.get(
                                                                                                   "_id"))}}
    )
    # No permission for get selection procedures data
    response = await http_client_test.get(
        f"/interview/selection_procedures/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Get selection procedures data
    response = await http_client_test.get(
        f"/interview/selection_procedures/?college_id={str(test_college_validation.get('_id'))}&page_num=1"
        f"&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get Selection procedure data."
    assert response.json()['total'] == 1
    assert response.json()['count'] == 1
    assert response.json()['pagination']["next"] is None
    assert response.json()['pagination']["previous"] is None
    for name in ["procedure_id", "course_name", "specialization_name", "eligibility_criteria",
                 "gd_parameters_weightage", "pi_parameters_weightage", "offer_letter", "created_by",
                 "created_at", "created_by_name", "last_modified_timeline"]:
        assert name in response.json()['data'][0]

    # Required college id for get selection procedures data
    response = await http_client_test.get(
        f"/interview/selection_procedures/?page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    # Invalid college id for get selection procedures data
    response = await http_client_test.get(
        f"/interview/selection_procedures/?college_id=1234567890&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    # College not found when try to get selection procedures data
    response = await http_client_test.get(
        f"/interview/selection_procedures/?college_id=123456789012345678901234&page_num=1&page_size=1"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'
