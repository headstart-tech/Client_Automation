"""
This file contains test cases of take a slot
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asycio
async def test_take_a_slot(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_user_validation,
        test_slot_details, panelist_access_token, application_details):
    """
    Different test cases scenarios for take a slot
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/planner/take_a_slot/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token to take a slot
    response = await http_client_test.post(
        f"/planner/take_a_slot/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id to take a slot
    response = await http_client_test.post(
        f"/planner/take_a_slot/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and ' \
                                        'valid.'

    # Required slot id to take a slot
    response = await http_client_test.post(
        f"/planner/take_a_slot/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Slot Id must be required and ' \
                                        'valid.'

    # Invalid college id to take a slot
    response = await http_client_test.post(
        f"/planner/take_a_slot/?college_id=12345628&"
        f"slot_id={test_slot_details.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input' \
                                        ' or a 24-character hex string'

    # College not found when try to take a slot
    response = await http_client_test.post(
        f"/planner/take_a_slot/"
        f"?college_id=123456789012345678901234&"
        f"slot_id={test_slot_details.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Invalid user when try to take a slot
    response = await http_client_test.post(
        f"/planner/take_a_slot/"
        f"?college_id={str(test_college_validation.get('_id'))}&"
        f"slot_id={str(test_slot_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    assert response.status_code == 401
    assert response.json()['detail'] == 'Only panelist can take a slot.'

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().slot_collection.update_one(
        {"_id": test_slot_details.get('_id')}, {"$unset": {"take_slot": True}})
    # Take a slot by panelist
    response = await http_client_test.post(
        f"/planner/take_a_slot/"
        f"?college_id={str(test_college_validation.get('_id'))}&"
        f"slot_id={str(test_slot_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{panelist_access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Slot is booked successfully."}

    # Take a slot by student
    response = await http_client_test.post(
        f"/planner/take_a_slot/"
        f"?college_id={str(test_college_validation.get('_id'))}&"
        f"slot_id={str(test_slot_details.get('_id'))}&is_student=true"
        f"&application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Slot is booked successfully."}
