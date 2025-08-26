"""
This file contains test cases of delete slots or panels by ids
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_slots_or_panels(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_slot_details,
        test_panel_validation, application_details):
    """
    Different scenarios of test cases for delete slots or panels by ids
    """
    college_id = str(test_college_validation.get('_id'))
    # Not authenticated if user not logged in
    response = await http_client_test.put(
        f"/interview/delete_slots_or_panels/?"
        f"college_id={college_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for delete slots or panels by ids
    response = await http_client_test.put(
        f"/interview/delete_slots_or_panels/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required body for delete slots or panels by ids
    response = await http_client_test.put(
        f"/interview/delete_slots_or_panels/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}

    # Required slots/panels ids for delete slots or panels by ids
    response = await http_client_test.put(
        f"/interview/delete_slots_or_panels/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json={}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Slots Panels Ids must be required "
                                         "and valid."}

    delete_slots_data = {"slots_panels_ids": [str(test_slot_details.get("_id"))]}
    # No permission for delete slots or panels by ids
    response = await http_client_test.put(
        f"/interview/delete_slots_or_panels/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=delete_slots_data
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Delete slots from db
    response = await http_client_test.put(
        f"/interview/delete_slots_or_panels/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=delete_slots_data
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Operation successfully done."}

    # Required college id for delete slots or panels by ids
    response = await http_client_test.put(
        f"/interview/delete_slots_or_panels/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=delete_slots_data
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and ' \
                                        'valid.'

    # Invalid college id for delete slots or panels by ids
    response = await http_client_test.put(
        f"/interview/delete_slots_or_panels/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=delete_slots_data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input ' \
                                        'or a 24-character hex string'

    # College not found when try to delete slots or panels by ids
    response = await http_client_test.put(
        f"/interview/delete_slots_or_panels/?"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=delete_slots_data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Wrong id for delete panels by ids
    response = await http_client_test.put(
        f"/interview/delete_slots_or_panels/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"slots_panels_ids": ["123"]}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Id `123` must be a 12-byte input or' \
                                        ' a 24-character hex string'
