"""
This file contains test cases to display student profile and marking scheme
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asycio
async def test_profile_marking_not_authenticated(
        http_client_test, test_college_validation, setup_module,
        test_slot_details):
    # Not authenticated if user not logged in
    response = await http_client_test.get(
        f"/planner/profile_marking_details/?slot_id="
        f"{str(test_slot_details.get('_id'))}&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_profile_marking_bad_token(
        http_client_test, test_college_validation, setup_module,
        test_slot_details):
    # Bad token to get details
    response = await http_client_test.get(
        f"/planner/profile_marking_details/?slot_id="
        f"{str(test_slot_details.get('_id'))}&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_profile_marking_required_college_id(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, test_slot_details):
    # Required college id
    response = await http_client_test.get(
        f"/planner/profile_marking_details/?"
        f"slot_id={str(test_slot_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and ' \
                                        'valid.'


@pytest.mark.asyncio
async def test_profile_marking_required_slot_id(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, test_slot_details):
    # Required slot id
    response = await http_client_test.get(
        f"/planner/profile_marking_details/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Slot Id must be required and valid.'


@pytest.mark.asyncio
async def test_profile_marking_invalid_college_id(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, test_slot_details):

    # Invalid college id
    response = await http_client_test.get(
        f"/planner/profile_marking_details/?"
        f"slot_id={str(test_slot_details.get('_id'))}&college_id=123455&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input ' \
                                        'or a 24-character hex string'


@pytest.mark.asyncio
async def test_profile_marking_invalid_slot_id(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, test_slot_details):

    # Invalid slot id to display student profile and marking
    response = await http_client_test.get(
        f"/planner/profile_marking_details/?slot_id=12334&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Slot id must be a 12-byte input or ' \
                                        'a 24-character hex string'


# @pytest.mark.asyncio
# async def test_profile_marking_college_not_found(
#         http_client_test, test_college_validation, setup_module,
#         college_super_admin_access_token, test_slot_details):
#     # College not found
#     response = await http_client_test.get(
#         f"/planner/profile_marking_details/?slot_id="
#         f"{str(test_slot_details.get('_id'))}&college_id="
#         f"123456789012345678901234",
#         headers={"Authorization": f"Bearer "
#                                   f"{college_super_admin_access_token}"},
#     )
#     assert response.status_code == 422
#     assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_profile_marking_slot_not_found(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, test_slot_details):
    # slot not found
    response = await http_client_test.get(
        f"/planner/profile_marking_details/?slot_id="
        f"123456789012345678901234&college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == f"Slot not found id: " \
                                        f"123456789012345678901234"


@pytest.mark.asyncio
async def test_profile_marking_no_applications(
        http_client_test, setup_module, test_college_validation,
        application_details,  college_super_admin_access_token,
        test_student_profile_details,test_slot_details,
        test_marking_details_by_programname):
    # no applications present
    response = await http_client_test.get(
        f"/planner/profile_marking_details/?slot_id="
        f"{str(test_slot_details.get('_id'))}&college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "no applications present."


@pytest.mark.asyncio
async def test_profile_marking_display(
        http_client_test, setup_module,test_college_validation,
        application_details, college_super_admin_access_token,
        test_student_profile_details, test_slot_details, test_take_slot,
        test_marking_details_by_programname):
    # display student profile and marking scheme
    response = await http_client_test.get(
        f"/planner/profile_marking_details/?"
        f"slot_id={str(test_slot_details.get('_id'))}&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert "marking_scheme" in response.json()
