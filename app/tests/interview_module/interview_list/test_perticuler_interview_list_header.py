"""
This file contains test cases of deleting interview list
Which is interview_module_routers.py file.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_interview_list_header_no_authentication(
        http_client_test, test_interview_list_validation,
        test_college_validation, setup_module):
    """
        View interview list header by not authenticated users.

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
        f"/interview/interview_list_header/"
        f"?interview_list_id={str(test_interview_list_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not authenticated'


@pytest.mark.asyncio
async def test_interview_list_header_no_permission(
        http_client_test, test_interview_list_validation,
        test_college_validation, setup_module,
        access_token):
    """
        View interview list header by no permission users.

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
        f"/interview/interview_list_header/"
        f"?interview_list_id={str(test_interview_list_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"authorization": f"Bearer {access_token}"})
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not enough permissions'


@pytest.mark.asyncio
async def test_interview_list_header_invalid_id(
        http_client_test, test_interview_list_validation,
        test_college_validation, setup_module,
        college_super_admin_access_token):
    """
        View interview list header with invalid id.

        Params:\n
            http_client_test: This is the http client url
            test_interview_list_validation: get data of interview list
            test_college_validation: get college data.
            setup_module: This is upload data and delete in database
            collection.
            college_super_admin_access_token: get admin access token
        Assertions:\n
            response status code and json message
    """
    response = await http_client_test.get(
        f"/interview/interview_list_header/"
        f"?interview_list_id=3456789012345678901234"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == "Interview list id must be a 12-byte " \
                                        "input or a 24-character hex string"


@pytest.mark.asyncio
async def test_interview_list_header_application(
        http_client_test, test_interview_list_validation,
        test_college_validation, setup_module,
        college_super_admin_access_token):
    """
        View interview list header application found.

        Params:\n
            http_client_test: This is the http client url
            test_interview_list_validation: get data of interview list
            test_college_validation: get college data.
            setup_module: This is upload data and delete in database
            collection.
            college_super_admin_access_token: get admin access token
        Assertions:\n
            response status code and json message
    """
    response = await http_client_test.get(
        f"/interview/interview_list_header/"
        f"?interview_list_id={str(test_interview_list_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
