"""
This file contains test cases of deleting interview list
Which is interview_module_routers.py file.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_interview_list_no_authentication(
        http_client_test, test_interview_list_validation,
        test_college_validation, setup_module):
    """
        Deleting interview list by not authenticated users.

        Params:\n
            http_client_test: This is the http client url
            test_interview_list_validation: get data of interview list
            test_college_validation: get college data.
            setup_module: This is upload data and delete in database
            collection.
        Assertions:\n
            response status code and json message
    """
    response = await http_client_test.put(
        f"/interview/delete_list/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        json=[str(test_interview_list_validation.get('_id'))])
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not authenticated'


@pytest.mark.asyncio
async def test_delete_interview_list_no_permission(
        http_client_test, test_interview_list_validation,
        test_college_validation, setup_module,
        access_token):
    """
        Deleting interview list by no permission users.

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
    response = await http_client_test.put(
        f"/interview/delete_list/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"authorization": f"Bearer {access_token}"},
        json=[str(test_interview_list_validation.get('_id'))])
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not enough permissions'


@pytest.mark.asyncio
async def test_delete_interview_list_invalid_id(
        http_client_test, test_interview_list_validation,
        test_college_validation, setup_module,
        college_super_admin_access_token):
    """
    Deleting interview list with invalid id
    """
    """
        Deleting interview list with invalid id.

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
    response = await http_client_test.put(
        f"/interview/delete_list/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "authorization": f"Bearer {college_super_admin_access_token}"},
        json=["3456789012345678901234"])
    assert response.status_code == 422
    assert response.json()['detail'] == "interview_id `3456789012345678901234` " \
                                        "must be a 12-byte " \
                                        "input or a 24-character hex string"


@pytest.mark.asyncio
async def test_delete_interview_list(
        http_client_test, test_interview_list_validation,
        test_college_validation, setup_module,
        college_super_admin_access_token):
    """
        Deleting interview list.

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
    response = await http_client_test.put(
        f"/interview/delete_list/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "authorization": f"Bearer {college_super_admin_access_token}"},
        json=[str(test_interview_list_validation.get('_id'))])
    assert response.status_code == 200
    assert response.json()['message'] == "Interview list has been" \
                                         " deleted successfully."
