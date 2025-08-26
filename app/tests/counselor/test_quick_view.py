"""
This file contains test cases for get quick view
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_quick_view_not_authenticated(http_client_test, setup_module):
    """
    Not authenticate for get quick view
    """
    response = await http_client_test.post(f"/counselor/quick_view/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_get_quick_view_required_college_id(http_client_test, super_admin_access_token,
                                                        setup_module,):
    """
    Required college_id for get quick view
    """
    response = await http_client_test.post(f"/counselor/quick_view/?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}

@pytest.mark.asyncio
async def test_get_quick_view_invalid_college_id(http_client_test,
                                               college_super_admin_access_token, setup_module):
    """
    Get the details of quick view using invalid college_id
    """
    response = await http_client_test.post(
        f"/counselor/quick_view/?college_id=1224&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_quick_view_college_not_found(http_client_test,
                                              college_super_admin_access_token, setup_module):
    """
    College not found in db for get details of quick view
    """
    response = await http_client_test.post(
        f"/counselor/quick_view/?college_id=123456787012386876543212&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}



@pytest.mark.asyncio
async def test_get_quick_view_no_permission(http_client_test, test_college_validation, super_admin_access_token,
                                                   setup_module):
    """
    Not permission for get quick view
    """
    response = await http_client_test.post(
        f"/counselor/quick_view/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_quick_view(http_client_test, test_college_validation,college_counselor_access_token ,
                                    setup_module):
    """
    Get the details of quick view
    """
    response = await http_client_test.post(
        f"/counselor/quick_view/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"}, )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the counselor quick view data."
