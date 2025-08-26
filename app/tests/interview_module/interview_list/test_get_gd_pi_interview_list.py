"""
This file contains test cases of get gd pi interview list
Which is interview_module_routers.py file.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_gd_pi_interview_list_no_authentication(
        http_client_test,
        test_college_validation, setup_module):
    """
        Get gd pi interview list by not authenticated users.

        Params:\n
            http_client_test: This is the http client url
            test_college_validation: get college data.
            setup_module: This is upload data and delete in database
            collection.
        Assertions:\n
            response status code and json message
    """
    response = await http_client_test.get(
        f"/interview/gd_pi_interview_list/"
        f"?page_num=1&page_size=24&feature_key={feature_key}"
        f"&college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not authenticated'


@pytest.mark.asyncio
async def test_gd_pi_interview_list_no_permission(
        http_client_test,
        test_college_validation, setup_module,
        access_token):
    """
        Get gd pi interview list by no permission users.

        Params:\n
            http_client_test: This is the http client url
            test_college_validation: get college data.
            setup_module: This is upload data and delete in database
            collection.
            access_token: get student access token
        Assertions:\n
            response status code and json message
    """
    response = await http_client_test.get(
        f"/interview/gd_pi_interview_list/"
        f"?page_num=1&page_size=24"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"authorization": f"Bearer {access_token}"})
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not enough permissions'


@pytest.mark.asyncio
async def test_gd_pi_interview_list_k(
        http_client_test, test_interview_list_validation,
        test_college_validation, setup_module,
        college_super_admin_access_token):
    """
        Get gd pi interview list.

        Params:\n
            http_client_test: This is the http client url
            test_college_validation: get college data.
            setup_module: This is upload data and delete in database
            collection.
            access_token: get student access token
        Assertions:\n
            response status code and json message
    """
    response = await http_client_test.get(
        f"/interview/gd_pi_interview_list/"
        f"?page_num=1&page_size=24"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()["message"] == 'data fetch successfully'
