"""
This file contains test case regarding get applications based on matched email string
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_list_of_username_based_on_matched_string_not_authenticated(
        http_client_test, test_college_validation, setup_module
):
    """
    Not Authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/admin/get_usernames_by_pattern?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_list_of_username_based_on_matched_string_no_permission(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    User has no permission to get the records
    """
    response = await http_client_test.get(
        f"/admin/get_usernames_by_pattern?username=wrong_username&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

"""
This file contains test case regarding get applications based on matched email string
"""
import pytest


@pytest.mark.asyncio
async def test_list_of_username_based_on_matched_string_not_authenticated(
        http_client_test, test_college_validation, setup_module
):
    """
    Not Authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/admin/get_usernames_by_pattern?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_list_of_username_based_on_matched_string_invalid_username(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Get records with invalid username
    """
    response = await http_client_test.get(
        f"/admin/get_usernames_by_pattern?username=wrong_username&college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "username not found"}


@pytest.mark.asyncio
async def test_list_of_username_based_on_matched_string_valid_username(
        http_client_test,
        test_college_validation,
        test_student_validation,
        college_super_admin_access_token,
        setup_module,
):
    """
    Get records with valid username
    """
    response = await http_client_test.get(
        f"/admin/get_usernames_by_pattern?username={test_student_validation['user_name']}"
        f"&page_num=1&page_size=1&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_of_username_based_on_matched_string_valid_username_second_page(
        http_client_test,
        test_college_validation,
        test_student_validation,
        college_super_admin_access_token,
        setup_module,
):
    """
    Test Case : Get records with valid username
    :return:
    :return:
    """
    response = await http_client_test.get(
        f"/admin/get_usernames_by_pattern?username={test_student_validation['user_name']}"
        f"&page_num=2&page_size=1&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_of_username_based_on_matched_string_valid_username_invalid_page_num(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Get records with valid username
    """
    response = await http_client_test.get(
        f"/admin/get_usernames_by_pattern?username=wrong_username&page_num=0&page_size=80"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Num must be required and valid."}


@pytest.mark.asyncio
async def test_list_of_username_based_on_matched_string_valid_username_invalid_page_size(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Get records with valid username
    """
    response = await http_client_test.get(
        f"/admin/get_usernames_by_pattern?username=wrong_username"
        f"&page_num=5&page_size=0&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Size must be required and valid."}

