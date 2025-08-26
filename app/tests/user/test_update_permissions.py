"""
This file contains test cases for update user permissions
"""
import pytest
from app.tests.conftest import user_feature_data
feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_user_update_permissions_not_authenticated(
    http_client_test, setup_module
):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.put(f"/user/update_permissions/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_user_update_permissions_bad_credentials(http_client_test, setup_module):
    """
    Test case -> bad token for update user permissions
    :param http_client_test:
    :return:
    """
    response = await http_client_test.put(
        f"/user/update_permissions/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_user_update_permissions_field_required(
    http_client_test, access_token, setup_module
):
    """
    Test case -> field required for update user permissions
    :param http_client_test:
    :param access_token:
    :return:
    """
    response = await http_client_test.put(
        f"/user/update_permissions/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "User Type must be required and valid."}


@pytest.mark.asyncio
async def test_user_update_permissions_body_required(
    http_client_test,
    super_admin_access_token,
    setup_module,
):
    """
    Test case -> body required for update user permissions
    :param http_client_test:
    :param super_admin_access_token:
    :return:
    """
    response = await http_client_test.put(
        f"/user/update_permissions/?user_type=super_admin&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Body must be required and valid."


@pytest.mark.asyncio
async def test_user_update_permissions(
    http_client_test,
    super_admin_access_token,
    setup_module,
):
    """
    Test case -> for update user permissions
    :param http_client_test:
    :param super_admin_access_token:
    :return:
    """
    response = await http_client_test.put(
        f"/user/update_permissions/?user_type=super_admin&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
        json={"add_client": True},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Permission updated."


@pytest.mark.asyncio
async def test_user_update_permissions_not_permission(
    http_client_test,
    college_super_admin_access_token,
    setup_module,
):
    """
    Test case -> no permission for update user permissions
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.put(
        f"/user/update_permissions/?user_type=super_admin&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"add_client": True},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Not enough permissions"
