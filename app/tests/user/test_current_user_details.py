"""
This file contains test cases for get current user details
"""
import pytest
from app.tests.conftest import user_feature_data
feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_current_user_details_not_authenticated(http_client_test, setup_module):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(f"/user/current_user_details/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_current_user_details_bad_credentials(http_client_test, setup_module):
    """
    Test case -> bad token for get current user details
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/user/current_user_details/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_current_user_details(
    http_client_test,
    college_super_admin_access_token,
    setup_module,
):
    """
    Test case -> for get current user details
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.get(
        f"/user/current_user_details/?user_type=college_counselor&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get current user details"


@pytest.mark.asyncio
async def test_current_user_details_no_permission(
    http_client_test,
    access_token,
    setup_module,
):
    """
    Test case -> no permission for get current user details
    :param http_client_test:
    :param access_token:
    :return:
    """
    response = await http_client_test.get(
        f"/user/current_user_details/?user_type=college_counselor&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"
