"""
This file contains test cases of delete all users
"""
import pytest
from app.tests.conftest import user_feature_data
feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_all_users_not_authenticated(http_client_test, setup_module):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.delete(f"/user/delete_all_users/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_all_users_bad_credentials(http_client_test, setup_module):
    """
    Test case -> bad token for delete all users
    :param http_client_test:
    :return:
    """
    response = await http_client_test.delete(
        f"/user/delete_all_users/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_delete_all_users_field_required(
    http_client_test, access_token, setup_module
):
    """
    Test case -> field required for delete all users
    :param http_client_test:
    :param access_token:
    :return:
    """
    response = await http_client_test.delete(
        f"/user/delete_all_users/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "User Type must be required and valid."}


@pytest.mark.asyncio
async def test_delete_all_users(
    http_client_test,
    college_super_admin_access_token,
    setup_module,
):
    """
    Test case -> for delete all users
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.delete(
        f"/user/delete_all_users/?user_type=college_counselor&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "All users removed successfully."


@pytest.mark.asyncio
async def test_delete_all_users_not_found(
    http_client_test,
    college_super_admin_access_token,
    setup_module,
):
    """
    Test case -> not found try to delete all users
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.delete(
        f"/user/delete_all_users/?user_type=college_counselor&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."
