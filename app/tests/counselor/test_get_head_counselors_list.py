"""
This file contains test cases for get head counselors list
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_head_counselors_list_not_authenticated(http_client_test, setup_module):
    """
    Test case -> not authenticate for get head counselors list
    """
    response = await http_client_test.get("/counselor/get_head_counselors_list/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_get_head_counselors_list_required_college_id(http_client_test, super_admin_access_token, setup_module):
    """
    Test case -> required college id for get head counselors list
    """
    response = await http_client_test.get(f"/counselor/get_head_counselors_list/?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}


@pytest.mark.asyncio
async def test_get_head_counselors_list_no_permission(http_client_test, super_admin_access_token, setup_module,
                                                      test_college_validation):
    """
    Test case -> no permission for get head counselors list
    """
    response = await http_client_test.get(
        f"/counselor/get_head_counselors_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 401
    assert response.json() == {'detail': 'Not enough permissions'}


@pytest.mark.asyncio
async def test_get_head_counselors_list(http_client_test, college_super_admin_access_token, setup_module,
                                        test_college_validation):
    """
    Test case -> for get head counselors list
    """
    response = await http_client_test.get(
        f"/counselor/get_head_counselors_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get head counselors list."
