"""
This file contains test cases of delete selection procedures by ids.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_selection_procedures_by_ids(
        http_client_test, test_college_validation, setup_module, access_token,
        test_selection_procedure_validation, college_super_admin_access_token,
        super_admin_access_token):
    """
    Different scenarios of test cases for delete selection procedures by ids.
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/interview/delete_selection_procedures/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for delete selection procedures by ids
    response = await http_client_test.post(
        f"/interview/delete_selection_procedures/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required body for delete selection procedures by ids
    response = await http_client_test.post(
        f"/interview/delete_selection_procedures/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}

    from app.database.configuration import DatabaseConfiguration
    selection_procedure = await DatabaseConfiguration().selection_procedure_collection. \
        find_one({})
    procedure_id = str(selection_procedure.get('_id'))

    # No permission for delete selection procedures by ids
    response = await http_client_test.post(
        f"/interview/delete_selection_procedures/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=[procedure_id]
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Required college id for delete selection procedures by ids
    response = await http_client_test.post(
        f"/interview/delete_selection_procedures/?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[procedure_id])
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and ' \
                                        'valid.'

    # Invalid college id for delete selection procedures by ids
    response = await http_client_test.post(
        f"/interview/delete_selection_procedures/?college_id=1234567890&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[procedure_id])
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input ' \
                                        'or a 24-character hex string'

    # College not found for delete selection procedures by ids
    response = await http_client_test.post(
        f"/interview/delete_selection_procedures/?"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[procedure_id])
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Delete selection procedures by ids
    response = await http_client_test.post(
        f"/interview/delete_selection_procedures/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=[procedure_id]
    )
    assert response.status_code == 200
    assert response.json() == \
           {"message": "Deleted selection procedures by ids."}

    # Invalid selection procedure id for delete procedure
    response = await http_client_test.post(
        f"/interview/delete_selection_procedures/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=["123"]
    )
    assert response.status_code == 422
    assert response.json()["detail"] == 'Selection procedure' \
                                        ' id `123` must be a 12-byte input ' \
                                        'or a 24-character hex string'
