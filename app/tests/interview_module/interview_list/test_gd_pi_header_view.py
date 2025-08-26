"""
This file contains test cases of view gt pi interview list header
Which is interview_module_routers.py file.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_gd_pi_header_interview_list_no_authentication(
        http_client_test, test_interview_list_validation,
        test_college_validation, setup_module):
    """
        View gd pi header interview list by not authenticated users.

        Params:\n
            http_client_test: This is the http client url
            test_interview_list_validation: get data of interview list
            test_college_validation: get college data.
            setup_module: This is upload data and delete in database
            collection.
        Assertions:\n
            response status code and json message
    """
    response = await http_client_test.get(
        f"/interview/gd_pi_header_list/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not authenticated'


@pytest.mark.asyncio
async def test_gd_pi_header_interview_list_no_permission(
        http_client_test, test_interview_list_validation,
        test_college_validation, setup_module,
        access_token):
    """
        Gd pi header interview list by no permission users.

        Params:\n
            http_client_test: This is the http client url
            test_interview_list_validation: get data of interview list
            test_college_validation: get college data.
            setup_module: This is upload data and delete in database
            collection.
            access_token: get student access token
        Assertions:\n
            response status code and json message
    """
    response = await http_client_test.get(
        f"/interview/gd_pi_header_list/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"authorization": f"Bearer {access_token}"})
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not enough permissions'
