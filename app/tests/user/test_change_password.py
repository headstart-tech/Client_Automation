"""
This file contains test cases of change password of user
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_change_password_user_not_authenticated(http_client_test, setup_module):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.put(f"/user/change_password/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_change_password_user_bad_credentials(http_client_test, setup_module):
    """
    Test case -> bad token for change password of user
    :param http_client_test:
    :return:
    """
    response = await http_client_test.put(
        f"/user/change_password/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_change_password_user_field_required(
    http_client_test, access_token, setup_module
):
    """
    Test case -> required current password for change password of user
    :param http_client_test:
    :param access_token:
    :return:
    """
    response = await http_client_test.put(
        f"/user/change_password/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Current Password must be required and valid."}


@pytest.mark.asyncio
async def test_change_password_user_wrong_current_password(
    http_client_test,
    super_admin_access_token,
    setup_module,
):
    """
    Test case -> wrong current password for change password of user
    :param http_client_test:
    :param super_admin_access_token:
    :return:
    """
    response = await http_client_test.put(
        "/user/change_password/?current_password=getmein1&new_password=getmein1"
        f"&confirm_password=getmein1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Current password is incorrect."}


@pytest.mark.asyncio
async def test_change_password_user_required_new_password(
    http_client_test,
    super_admin_access_token,
    setup_module,
):
    """
    Test case -> required new password for change password of user
    :param http_client_test:
    :param super_admin_access_token:
    :return:
    """
    response = await http_client_test.put(
        f"/user/change_password/?current_password=getmein&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "New Password must be required and valid."}


@pytest.mark.asyncio
async def test_change_password_user_not_match_passwords(
    http_client_test,
    super_admin_access_token,
    setup_module,
):
    """
    Test case -> not match password for change password of user
    :param http_client_test:
    :param super_admin_access_token:
    :return:
    """
    response = await http_client_test.put(
        "/user/change_password/?current_password=getmein&"
        f"new_password=getmein1&confirm_password=getmein&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "New Password and Confirm Password doesn't match."
    }


@pytest.mark.asyncio
async def test_change_password_user(
    http_client_test,
    super_admin_access_token,
    setup_module,
):
    """
    Test case -> for change password of user
    :param http_client_test:
    :param super_admin_access_token:
    :return:
    """
    response = await http_client_test.put(
        "/user/change_password/?current_password=getmein&"
        f"new_password=getmein1&confirm_password=getmein1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Your password has been updated successfully."
