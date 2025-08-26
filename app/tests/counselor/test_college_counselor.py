"""
This file contains test cases for get the list of college counselors
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_college_counselor_not_authenticated(http_client_test, setup_module):
    """
    Not authenticate for get the list of college counselors
    """
    response = await http_client_test.post(
        f"/counselor/all_counselor_list?page_num=1&page_size=5&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_get_college_counselor_required_college_id(http_client_test, super_admin_access_token,
                                                         setup_module):
    """
    Required college id for get the list of college counselors
    :param http_client_test:
    :param setup_module:
    :return:
    """
    response = await http_client_test.post(f"/counselor/all_counselor_list?page_num=1"
                                           f"&page_size=5&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_get_college_counselor_no_permission(http_client_test, test_college_validation, super_admin_access_token,
                                                   setup_module):
    """
    No permission for get the list of college counselors
    :param http_client_test:
    :param setup_module:
    :return:
    """
    response = await http_client_test.post(
        f"/counselor/all_counselor_list?page_num=1&page_size=5"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_college_counselor_previous_none(http_client_test, test_college_validation,
                                                   college_super_admin_access_token, setup_module):
    """
    Get the list of college counselors using college_id
    """
    response = await http_client_test.post(
        f"/counselor/all_counselor_list?page_num=1&page_size=5"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
    assert response.json()["pagination"]["previous"] == None


@pytest.mark.asyncio
async def test_get_college_counselor(http_client_test, test_college_validation, college_super_admin_access_token,
                                     setup_module):
    """
    Get the list of college counselors using college_id
    """
    response = await http_client_test.post(
        f"/counselor/all_counselor_list?page_num=2&page_size=5"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"


@pytest.mark.asyncio
async def test_get_college_counselor_next_none(http_client_test, test_college_validation,
                                               college_super_admin_access_token, setup_module):
    """
    Get the list of college counselors using college_id
    """
    response = await http_client_test.post(
        f"/counselor/all_counselor_list?page_num=2&page_size=8"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
    assert response.json()["pagination"]["next"] == None


@pytest.mark.asyncio
async def test_get_college_counselor_by_source_and_state(http_client_test, test_college_validation,
                                                         college_super_admin_access_token,
                                                         setup_module):
    """
    Get the list of college counselors using college_id by source and state
    """
    response = await http_client_test.post(
        f"/counselor/all_counselor_list?page_num=2&page_size=5"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"source": ["online"], "state": ["NL"]})
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
