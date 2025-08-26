"""
This file contains test cases for counselor  pending follwups
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_pending_folloups_not_authenticated(http_client_test, setup_module):
    """
    Not authenticate for get pending_folloups
    """
    response = await http_client_test.post("/counselor/get_pending_followup/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_get_pending_folloups_required_college_id(http_client_test, super_admin_access_token,
                                                        setup_module,):
    """
    Required college_id for get pending_folloups
    """
    response = await http_client_test.post(f"/counselor/get_pending_followup/?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}

@pytest.mark.asyncio
async def test_get_pending_folloups_invalid_college_id(http_client_test,
                                               college_super_admin_access_token, setup_module):
    """
    Get the details of pending_folloups using invalid college_id
    """
    response = await http_client_test.post(
        f"/counselor/get_pending_followup/?college_id=1224&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_pending_folloups_college_not_found(http_client_test,
                                              college_super_admin_access_token, setup_module):
    """
    College not found in db for get details of pending_folloups
    """
    response = await http_client_test.post(
        f"/counselor/get_pending_followup/?college_id=123456787012386876543212&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}



@pytest.mark.asyncio
async def test_get_pending_folloups_no_permission(http_client_test, test_college_validation, super_admin_access_token,
                                                   setup_module):
    """
    Not permission for get pending_folloups
    """
    response = await http_client_test.post(
        f"/counselor/get_pending_followup/?page_num=1&page_size=10"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_pending_folloups(http_client_test, test_college_validation,college_super_admin_access_token,
                                    setup_module):
    """
    Get the details of pending_folloups
    """
    response = await http_client_test.post(
        f"/counselor/get_pending_followup/?page_num=1&page_size=10"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetched successfully"
