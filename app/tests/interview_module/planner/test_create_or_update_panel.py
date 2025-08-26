"""
This file contains test cases of create or update panel
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_or_panel(http_client_test, test_college_validation, setup_module, access_token,
                               college_super_admin_access_token, test_user_validation, test_panel_data):
    """
    Different scenarios of test cases for create or update panel
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/planner/create_or_update_panel/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for create or update panel
    response = await http_client_test.post(
        f"/planner/create_or_update_panel/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required body for add or update selection procedure
    response = await http_client_test.post(
        f"/planner/create_or_update_panel/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}

    # No permission for add or update selection procedure
    response = await http_client_test.post(
        f"/planner/create_or_update_panel/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json={}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Required course name for add or update selection procedure
    response = await http_client_test.post(
        f"/planner/create_or_update_panel/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "slot_type must be required and "
                                         "valid."}
    # assert response.json() == {
    #     "detail": "Panel name must be required and valid."}

    # Add panel data
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().panel_collection.delete_many({})
    response = await http_client_test.post(
        f"/planner/create_or_update_panel/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_panel_data
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Panel data added."
    for key_name in ["panel_id", "slot_type", "date"]:
        assert key_name in response.json()

    # Required college id for create or update panel
    response = await http_client_test.post(
        f"/planner/create_or_update_panel/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_panel_data
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    # Invalid college id for create or update panel
    response = await http_client_test.post(
        f"/planner/create_or_update_panel/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_panel_data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    # College not found when try to create or update panel
    response = await http_client_test.post(
        f"/planner/create_or_update_panel/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_panel_data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Update panel data
    panel_data = await DatabaseConfiguration().panel_collection.find_one({})
    response = await http_client_test.post(
        f"/planner/create_or_update_panel/?college_id={str(test_college_validation.get('_id'))}"
        f"&panel_id={str(panel_data.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_panel_data
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Panel data updated."

    # Wrong panel id for update panel data
    response = await http_client_test.post(
        f"/planner/create_or_update_panel/?college_id={str(test_college_validation.get('_id'))}"
        f"&panel_id=123456789012&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=test_panel_data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Panel id must be a 12-byte input or a 24-character hex string'

    # Invalid panel id for update panel data
    response = await http_client_test.post(
        f"/planner/create_or_update_panel/?college_id={str(test_college_validation.get('_id'))}"
        f"&panel_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=test_panel_data
    )
    assert response.status_code == 404
    assert response.json()['detail'] == \
           "Panel not found. Make sure provided panel id should be correct."
