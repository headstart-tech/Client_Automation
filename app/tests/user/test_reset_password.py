"""
This file contains test cases of reset password of user
"""
import pytest


@pytest.mark.asyncio
async def test_reset_password_of_user_required_email_id(http_client_test, setup_module):
    """
    Test case -> required email id for reset password of user
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get("/user/dkper/user/{token}")
    assert response.status_code == 400
    assert response.json()["detail"] == "New Password must be required and valid."


@pytest.mark.asyncio
async def test_reset_password_of_user(http_client_test, setup_module):
    """
    Test case -> for reset password of user
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        "/user/dkper/user/{token}?new_password=test1234"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Your password has been updated successfully."
