"""
This file contains test cases of create or update slot
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_or_slot(http_client_test, test_college_validation, setup_module, access_token,
                              college_super_admin_access_token, test_user_validation, test_slot_data):
    """
    Different scenarios of test cases for create or update slot
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/planner/create_or_update_slot/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for create or update slot
    response = await http_client_test.post(
        f"/planner/create_or_update_slot/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required body for add or update selection procedure
    response = await http_client_test.post(
        f"/planner/create_or_update_slot/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}

    # No permission for add or update selection procedure
    response = await http_client_test.post(
        f"/planner/create_or_update_slot/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json={}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Add panel data
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().slot_collection.delete_many({})
    response = await http_client_test.post(
        f"/planner/create_or_update_slot/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_slot_data
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Slot data added."}

    # Required college id for create or update slot
    response = await http_client_test.post(
        f"/planner/create_or_update_slot/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_slot_data
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    # Invalid college id for create or update slot
    response = await http_client_test.post(
        f"/planner/create_or_update_slot/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_slot_data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    # College not found when try to create or update slot
    response = await http_client_test.post(
        f"/planner/create_or_update_slot/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_slot_data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Update panel data
    slot_data = await DatabaseConfiguration().slot_collection.find_one({})
    response = await http_client_test.post(
        f"/planner/create_or_update_slot/?college_id={str(test_college_validation.get('_id'))}"
        f"&slot_id={str(slot_data.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_slot_data
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Slot data updated."}

    # Wrong panel id for update panel data
    response = await http_client_test.post(
        f"/planner/create_or_update_slot/?college_id={str(test_college_validation.get('_id'))}"
        f"&slot_id=123456789012&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=test_slot_data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Slot id must be a 12-byte input or a 24-character hex string'

    # Invalid panel id for update panel data
    response = await http_client_test.post(
        f"/planner/create_or_update_slot/?college_id={str(test_college_validation.get('_id'))}"
        f"&slot_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=test_slot_data
    )
    assert response.status_code == 404
    assert response.json()['detail'] == \
           "Slot not found. Make sure provided slot id should be correct."
