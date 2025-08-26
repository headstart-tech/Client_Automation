"""
This file contains test cases of get slot details
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asycio
async def test_get_slot_details_not_authenticated(http_client_test, test_college_validation, setup_module, access_token,
                                college_super_admin_access_token, test_user_validation, test_panel_data,test_slot_details
                                ):
    # Not authenticated if user not logged in
    response = await http_client_test.get(
        f"/planner/slot/get_data_by_id/?slot_id={str(test_slot_details.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_get_slot_details_bad_token(http_client_test, test_college_validation, setup_module, access_token,
                                    college_super_admin_access_token, test_user_validation, test_panel_data,test_slot_details
                                    ):
    # Bad token to get details
    response = await http_client_test.get(
        f"/planner/slot/get_data_by_id/?slot_id={str(test_slot_details.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}" ,
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_get_slot_details_required_field(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation, test_panel_data,test_slot_details
                                             ):
    # Required college id to get slot details
    response = await http_client_test.get(
        f"/planner/slot/get_data_by_id/?slot_id={str(test_slot_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'
#
@pytest.mark.asyncio
async def test_get_slot_details_invalid_college_id(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation, test_panel_data,test_slot_details
                                             ):

    # Invalid college id to get slot details
    response = await http_client_test.get(
        f"/planner/slot/get_data_by_id/?slot_id={str(test_slot_details.get('_id'))}"
        f"&college_id=12345628&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_get_slot_details_invalid_id(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation, test_panel_data,test_slot_details
                                             ):

    # Invalid slot id to get slot details
    response = await http_client_test.get(
        f"/planner/slot/get_data_by_id/?slot_id=12345628&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Slot id must be a 12-byte input or a 24-character hex string'

@pytest.mark.asyncio
async def test_get_slot_details_not_found(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation, test_panel_data,test_slot_details
                                             ):
    # College not found when try to get slot details
    response = await http_client_test.get(
        f"/planner/slot/get_data_by_id/?slot_id={str(test_slot_details.get('_id'))}"
        f"&college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_get_slot_details_invalid_slot_id(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation, test_panel_data,
                                             ):
    # invalid slot id
    response = await http_client_test.get(
        f"/planner/slot/get_data_by_id/?slot_id=123456789012345678901234"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == \
           "Slot not found. Make sure provided slot id should be correct."

@pytest.mark.asyncio
async def test_get_slot_details(http_client_test, test_college_validation, setup_module, access_token,
                                college_super_admin_access_token, test_user_validation, test_panel_data,
                                test_slot_details):
    #get slot details
    response = await http_client_test.get(
        f"/planner/slot/get_data_by_id/?slot_id={str(test_slot_details.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert "created_at" in response.json()
