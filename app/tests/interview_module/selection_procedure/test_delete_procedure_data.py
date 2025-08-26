"""
This file contains test cases of delete selection procedure data
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_selection_procedure_data(http_client_test, test_college_validation, setup_module, access_token,
                                               college_super_admin_access_token, test_user_validation):
    """
    Different scenarios of test cases for delete selection procedure data
    """
    # Not authenticated if user not logged in
    response = await http_client_test.delete(
        f"/interview/delete_selection_procedure/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for delete selection procedure data
    response = await http_client_test.delete(
        f"/interview/delete_selection_procedure/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required procedure id for get selection procedure id
    response = await http_client_test.delete(
        f"/interview/delete_selection_procedure/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Procedure Id must be required and valid."}

    # Create selection procedure
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().selection_procedure_collection.delete_many({})
    await http_client_test.post(
        f"/interview/create_or_update_selection_procedure/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"course_name": "test",
                                                                                       "offer_letter": {
                                                                                           "template": "test",
                                                                                           "authorized_approver": str(
                                                                                               test_user_validation.get(
                                                                                                   "_id"))}}
    )
    selection_procedure = await DatabaseConfiguration().selection_procedure_collection.find_one({})
    # No permission for get selection procedure id
    response = await http_client_test.delete(
        f"/interview/delete_selection_procedure/?college_id={str(test_college_validation.get('_id'))}"
        f"&procedure_id={str(selection_procedure.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Delete selection procedure data
    response = await http_client_test.delete(
        f"/interview/delete_selection_procedure/?college_id={str(test_college_validation.get('_id'))}"
        f"&procedure_id={str(selection_procedure.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Selection procedure deleted."}

    # Required college id for delete selection procedure data
    response = await http_client_test.delete(
        f"/interview/delete_selection_procedure/?procedure_id={str(selection_procedure.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    # Invalid college id for delete selection procedure data
    response = await http_client_test.delete(
        f"/interview/delete_selection_procedure/"
        f"?college_id=1234567890&procedure_id={str(selection_procedure.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    # College not found when try to delete selection procedure data
    response = await http_client_test.delete(
        f"/interview/delete_selection_procedure/?college_id=123456789012345678901234"
        f"&procedure_id={str(selection_procedure.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Invalid procedure id for delete selection procedure data
    response = await http_client_test.delete(
        f"/interview/delete_selection_procedure/"
        f"?college_id={str(test_college_validation.get('_id'))}&procedure_id=123456&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Procedure id must be a 12-byte input or a 24-character hex string'

    # Wrong procedure id for delete selection procedure data
    response = await http_client_test.delete(
        f"/interview/delete_selection_procedure/?college_id={str(test_college_validation.get('_id'))}"
        f"&procedure_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == \
           'Selection procedure not found. Make sure provided procedure id should be correct.'
