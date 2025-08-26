"""
This file contains test cases of create or update selection procedure
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_or_update_selection(http_client_test, test_college_validation, setup_module, access_token,
                                          college_super_admin_access_token, test_user_validation):
    """
    Different scenarios of test cases for create or update selection procedure
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for create or update selection procedure
    response = await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required body for add or update selection procedure
    response = await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}

    # No permission for add or update selection procedure
    response = await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json={}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Required course name for add or update selection procedure
    response = await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Course name must be required and valid."}

    # Required offer letter details for add or update selection procedure
    response = await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"course_name": "test"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Offer letter details must be required and valid."}

    # Add selection procedure
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().selection_procedure_collection.delete_many({})
    response = await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"course_name": "test",
                                                                                       "offer_letter": {
                                                                                           "template": "test",
                                                                                           "authorized_approver": str(
                                                                                               test_user_validation.get(
                                                                                                   "_id"))}}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Selection procedure data added."}

    # Selection procedure already exist
    response = await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"course_name": "test",
                                                                                       "offer_letter": {
                                                                                           "template": "test",
                                                                                           "authorized_approver": str(
                                                                                               test_user_validation.get(
                                                                                                   "_id"))}}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Selection procedure for course already exist."}

    # Required college id for create or update procedure
    response = await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"course_name": "test",
              "offer_letter": {"template": "test", "authorized_approver": str(test_user_validation.get("_id"))}}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    # Invalid college id for create or update procedure
    response = await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"course_name": "test",
              "offer_letter": {"template": "test", "authorized_approver": str(test_user_validation.get("_id"))}}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    # College not found when try to create or update procedure
    response = await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/?college_id=123456789012345678901234"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"course_name": "test",
              "offer_letter": {"template": "test", "authorized_approver": str(test_user_validation.get("_id"))}}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Update selection procedure data
    selection_procedure = await DatabaseConfiguration().selection_procedure_collection.find_one({})
    response = await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/?college_id={str(test_college_validation.get('_id'))}"
        f"&procedure_id={str(selection_procedure.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"offer_letter": {
            "template": "test",
            "authorized_approver": str(
                test_user_validation.get(
                    "_id"))}}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Selection procedure data updated."}

    # Wrong procedure id for update selection procedure data
    response = await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/?"
        f"college_id={str(test_college_validation.get('_id'))}"
        f"&procedure_id=123456789012&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"offer_letter": {
            "template": "test",
            "authorized_approver": str(
                test_user_validation.get(
                    "_id"))}}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Procedure id must be a 12-byte input' \
                                        ' or a 24-character hex string'

    # Invalid procedure id for update selection procedure data
    response = await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/?college_id={str(test_college_validation.get('_id'))}"
        f"&procedure_id=123456789012345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"offer_letter": {
            "template": "test",
            "authorized_approver": str(
                test_user_validation.get(
                    "_id"))}}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == \
           "Selection procedure not found. Make sure " \
           "provided procedure id should be correct."
