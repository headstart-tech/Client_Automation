"""
This file contains test cases of get assigned and unaasigned API
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()


@pytest.mark.asyncio
async def test_get_assigned_unassigned_details_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/admin/get_assigned_unassigned_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_assigned_unassigned_details_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get unassigned and assigned details
    """
    response = await http_client_test.post(
        f"/admin/get_assigned_unassigned_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_assigned_unassigned_details_required_college_id(http_client_test, test_college_validation,
                                                        college_super_admin_access_token):
    """
    Required college id for get assigned and unassigned
    """
    response = await http_client_test.post(f"/admin/get_assigned_unassigned_details/?feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'


@pytest.mark.asyncio
async def test_get_assigned_unassigned_details_invalid_college_id(http_client_test, test_college_validation,
                                                       college_super_admin_access_token):
    """
    Invalid college id for get all applications
    """
    response = await http_client_test.post(f"/admin/get_assigned_unassigned_details/?college_id=1234567890"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_get_assigned_unassigned_details_college_not_found(http_client_test, test_college_validation,
                                                      college_super_admin_access_token):
    """
    College not found for get all applications
    """
    response = await http_client_test.post(
        f"/admin/get_assigned_unassigned_details/?college_id=123456789012345678901234&"
        f"feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_get_assigned_unassigned_details_no_data_for_page(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    no data found for get all applications
    """
    response = await http_client_test.post(
        f"/admin/get_assigned_unassigned_details/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Fetched assigned and unassigned details"
