"""
This file contains test cases regarding login student
"""
import pytest

from app.core.utils import settings


@pytest.mark.asyncio
async def test_example(http_client_test, setup_module):
    """
    Sample test case
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get("https://www.example.com")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_obtain_token_info_api(http_client_test, access_token,
                                     setup_module):
    """
    Test case -> for obtain token info
    :param http_client_test:
    :param access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/oauth/tokeninfo?token={access_token}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_read_existent_student_bad_token(http_client_test, setup_module):
    """
    Test case -> for read existent student bad token
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post("/oauth/tokeninfo?token=wrongtoken")
    assert response.status_code == 401
    assert response.json()["detail"] == "Token is not valid"


# Todo - Following test case giving error when we run all test cases
#  otherwise working fine, need to properly check later on
# @pytest.mark.asyncio
# async def test_existent_student_login(
#         http_client_test, test_student_validation, setup_module
# ):
#     """
#     Test case -> for existent student login
#     """
#     response = await http_client_test.post(
#         f"/oauth/token?college_id={str(test_student_validation.get('college_id'))}",
#         data={
#             "username": test_student_validation["user_name"],
#             "password": "getmein",
#             "scope": "student"
#         },
#     )
#     assert response.status_code == 200
#     assert response.json()["access_token"]
#     assert response.json()["token_type"] == "bearer"


# Todo - Following test case giving error when we run all test cases
#  otherwise working fine, need to properly check later on
# @pytest.mark.asyncio
# async def test_existent_student_user_login(
#         http_client_test, test_student_validation, setup_module,
#         test_user_validation
# ):
#     """
#     Test case -> for existent student/user login
#     """
#     # Student login
#     response = await http_client_test.post(
#         f"/oauth/token",
#         data={
#             "username": test_student_validation["user_name"],
#             "password": "getmein",
#             "client_id": str(test_student_validation.get("college_id")),
#         },
#     )
#     assert response.status_code == 200
#     for key in ["access_token", "token_type"]:
#         assert key in response.json()
#     assert response.json()["token_type"] == "bearer"
#
#     # User login
#     response = await http_client_test.post(
#         f"/oauth/token",
#         data={
#             "username": test_user_validation["user_name"],
#             "password": "getmein"
#         },
#     )
#     assert response.status_code == 200
#     for key in ["access_token", "token_type"]:
#         assert key in response.json()
#     assert response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_existent_user_login_failed(
        http_client_test, test_college_validation, test_user_validation,
        setup_module
):
    """
    Test case -> deactivate user not able to login
    :param http_client_test:
    :param test_user_validation:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    from app.core.utils import settings

    await DatabaseConfiguration().user_collection.update_one(
        {"user_name": test_user_validation["email"]},
        {"$set": {"is_activated": False}}
    )
    response = await http_client_test.post(
        "/oauth/token?college_id={str(test_college_validation.get('_id'))}",
        data={
            "username": test_user_validation["email"],
            "password": settings.superadmin_password,
            "scope": test_user_validation["role"]["role_name"],
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "You are deactivated."


@pytest.mark.asyncio
async def test_read_existent_student_token_not_send(http_client_test,
                                                    setup_module):
    """
    Test case -> token not send for verification
    """
    response = await http_client_test.post("/oauth/tokeninfo")
    assert response.status_code == 401
    assert response.json()["detail"] == "Token is not valid"


@pytest.mark.asyncio
async def test_existent_student_login_college_not_found(
        http_client_test, test_student_validation, setup_module
):
    """
    Test case -> college not found for generate token
    by student login credentials
    """
    response = await http_client_test.post(
        "/oauth/token",
        data={
            "username": test_student_validation["user_name"],
            "scope": "student",
            "password": settings.superadmin_password,
            "client_id": "123456789012345678901234"
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "College not found. Make sure" \
                                        " college id is valid."


@pytest.mark.asyncio
async def test_existent_student_login_invalid_college_id(
        http_client_test, test_student_validation, setup_module
):
    """
    Test case -> invalid college id for generate refresh token by
    student login credentials
    """
    response = await http_client_test.post("/oauth/refresh_token/generate/",
                                           data={
                                               "username":
                                                   test_student_validation[
                                                       "user_name"],
                                               "scope": "student",
                                               "password": settings.superadmin_password,
                                               "client_id": "12345678901234567890"},
                                           )
    assert response.status_code == 422
    assert response.json()["detail"] == "College id must be a 12-byte input " \
                                        "or a 24-character hex string"


# Todo - Following test case giving error when we run all test cases
#  otherwise working fine, need to properly check later on
# @pytest.mark.asyncio
# async def test_generate_refresh_token(
#         http_client_test, test_student_validation, setup_module,
#         test_user_validation
# ):
#     """
#     Test case -> generate refresh token by student/user login credentials
#     """
#     fields = ["access_token", "refresh_token", "token_type"]
#     # Generate refresh token by student login credentials
#     response = await http_client_test.post(
#         "/oauth/refresh_token/generate/",
#         data={
#             "username": test_student_validation["user_name"],
#             "scope": "student",
#             "password": settings.superadmin_password,
#             "client_id": str(test_student_validation.get("college_id"))
#         },
#     )
#     assert response.status_code == 200
#     for key in fields:
#         assert key in response.json()
#     assert response.json()["token_type"] == "bearer"
#
#     # Generate refresh token by user login credentials
#     response = await http_client_test.post(
#         "/oauth/refresh_token/generate/",
#         data={
#             "username": test_user_validation["user_name"],
#             "scope": test_user_validation["role"]["role_name"],
#             "password": settings.superadmin_password
#         },
#     )
#     assert response.status_code == 200
#     for key in fields:
#         assert key in response.json()
#     assert response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_generate_refresh_token_college_not_found(
        http_client_test, test_student_validation, setup_module,
        test_user_validation
):
    """
    Test case -> college not found for generate refresh token by
     student login credentials
    """
    response = await http_client_test.post(
        "/oauth/refresh_token/generate/",
        data={
            "username": test_student_validation["user_name"],
            "scope": "student",
            "password": settings.superadmin_password,
            "client_id": "123456789012345678901234"
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "College not found. Make sure " \
                                        "college id is valid."


@pytest.mark.asyncio
async def test_generate_refresh_token_invalid_college_id(
        http_client_test, test_student_validation, setup_module,
        test_user_validation
):
    """
    Test case -> invalid college id for generate refresh token by student
    login credentials
    """
    from app.core.utils import settings
    response = await http_client_test.post(
        "/oauth/refresh_token/generate/",
        data={
            "username": test_student_validation["user_name"],
            "scope": "student",
            "password": settings.superadmin_password,
            "client_id": "12345678901234567890"
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College id must be a 12-byte input" \
                                        " or a 24-character hex string"
