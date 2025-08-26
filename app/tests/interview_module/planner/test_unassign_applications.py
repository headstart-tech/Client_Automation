"""
This file contains test cases of unassign applications of given slot
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asycio
async def test_unassign_applications_of_slot_not_authenticated(http_client_test, test_college_validation, setup_module):
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/planner/unassign_applicants_from_slots/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        json= []
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_unassign_applications_of_slot_bad_token(http_client_test, test_college_validation, setup_module,
                                    college_super_admin_access_token):
    # Bad token to get details
    response = await http_client_test.post(
        f"/planner/unassign_applicants_from_slots/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
        json=[]
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_unassign_applications_of_slot_college_required_field(http_client_test, test_college_validation, setup_module,
                                             college_super_admin_access_token
                                             ):
    # Required college id
    response = await http_client_test.post(
        f"/planner/unassign_applicants_from_slots/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[]
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'


@pytest.mark.asyncio
async def test_unassign_applications_of_slot_invalid_college_id(http_client_test, test_college_validation, setup_module,
                                             college_super_admin_access_token
                                             ):

    # Invalid college id
    response = await http_client_test.post(
        f"/planner/unassign_applicants_from_slots/?college_id=1223&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[]
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_unassign_applications_of_slot_college_not_found(http_client_test, test_college_validation, setup_module,
                                             college_super_admin_access_token
                                             ):
    # College not found
    response = await http_client_test.post(
        f"/planner/unassign_applicants_from_slots/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[]
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

@pytest.mark.asyncio
async def test_unassign_applications_of_slot(http_client_test, test_college_validation, setup_module, access_token,
                                college_super_admin_access_token,test_take_slot,test_slot_details):
    # unassign all applications of given slots
    response = await http_client_test.post(
        f"/planner/unassign_applicants_from_slots/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[str(test_slot_details.get("_id"))]
    )
    assert response.status_code == 200
    assert response.json()["message"] == "All applicants are unassigned from given slots."

