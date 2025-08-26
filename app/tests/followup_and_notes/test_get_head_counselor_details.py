"""
this file contains all test case of pending followup leads
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_head_counselor_not_authorization(http_client_test, setup_module, test_college_validation):
    """
    this test case checking the user authenticated or not
    """
    response = await http_client_test.put(
        f"/followup_notes/head_counselor_details?page_num=1&page_size=25"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_head_counselor_with_college_super_admin(http_client_test, college_super_admin_access_token,
                                                           setup_module, test_college_validation):
    """
    this test case checking the response with college super admin
    """
    response = await http_client_test.put(f"/followup_notes/head_counselor_details?page_num=1&page_size=25"
                                          f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "Get all head counselor details."


@pytest.mark.asyncio
async def test_get_head_counselor_with_college_counselor(http_client_test, college_counselor_access_token,
                                                         setup_module, test_college_validation):
    """
    this test case checking the response with college counselor
    """
    response = await http_client_test.put(f"/followup_notes/head_counselor_details?page_num=1&page_size=25"
                                          f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permission"


@pytest.mark.asyncio
async def test_get_head_counselor_with_college_publisher(http_client_test, publisher_access_token,
                                                         setup_module, test_college_validation):
    """
    this test case checking the response with college publisher
    """
    response = await http_client_test.put(f"/followup_notes/head_counselor_details?page_num=1&page_size=25"
                                          f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {publisher_access_token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permission"
