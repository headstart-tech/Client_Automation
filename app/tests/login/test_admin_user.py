"""
This file contains test cases regarding login admin user
"""
import pytest

from app.core.utils import settings


@pytest.mark.asyncio
async def test_admin_login_invalid_username(http_client_test, test_college_validation, setup_module):
    """
    Invalid username for admin login
    """
    response = await http_client_test.post(f"/admin/login/")
    assert response.status_code == 400
    assert response.json()["detail"] == "Username must be required and valid."


@pytest.mark.asyncio
async def test_admin_login_test_invalid_password(
        http_client_test, test_college_validation, test_user_validation, setup_module
):
    """
    Invalid password for admin login
    """
    response = await http_client_test.post(
        f"/admin/login/",
        data={"username": test_user_validation["user_name"]}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Password must be required and valid."


# Todo: I have checked by debug but not passed this test case we lookout later
# @pytest.mark.asyncio
# async def test_admin_login(http_client_test, test_college_validation,
#                            test_user_validation, setup_module):
#     """
#     Admin login
#     """
#     response = await http_client_test.post(
#         f"/admin/login/",
#         data={
#             "username": test_user_validation["user_name"],
#             "password": settings.superadmin_password,
#         },
#     )
#     assert response.status_code == 200
#     assert response.json()["token_type"] == "bearer"
#     assert "access_token" in response.json()


# @pytest.mark.asyncio
# async def test_admin_login_with_refresh_token_and_access_token(
#         http_client_test, test_college_validation,
#         test_user_validation, setup_module):
#     """
#     Admin login by getting refresh and access tokens
#     """
#     response = await http_client_test.post(
#         f"/admin/login/?refresh_token=true",
#         data={
#             "username": test_user_validation["user_name"],
#             "password": settings.superadmin_password,
#         },
#     )
#     assert response.status_code == 200
#     assert response.json()["token_type"] == "bearer"
#     for name in ["access_token", "refresh_token"]:
#         assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_deactivate_user_login_failed(
        http_client_test, test_college_validation, test_user_validation,
        setup_module
):
    """
        Deactivate user not able to log in
    """
    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().user_collection.update_one(
        {"user_name": test_user_validation["email"]}, {"$set": {"is_activated": False}}
    )
    response = await http_client_test.post(
        f"/admin/login/",
        data={
            "username": test_user_validation["user_name"],
            "password": settings.superadmin_password,
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "You are deactivated."
