import pytest

from app.core.utils import settings


@pytest.mark.asyncio
async def test_database(http_client_test, setup_module):
    """
    Test case -> for check database connection
    :return:
    """
    response = await http_client_test.post(
        "/check/check_connections",
        json={
            "user_name": settings.db_username,
            "database_name": settings.db_name,
            "password": settings.db_password,
            "url": settings.db_url,
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_authenticate_database(http_client_test, setup_module):
    """
    Test case -> non-authoritative database when try to connect with database
    :return:
    """
    response = await http_client_test.post(
        "/check/check_connections",
        json={
            "user_name": settings.db_username,
            "database_name": "wrong",
            "password": settings.db_password,
            "url": settings.db_url,
        },
    )
    assert response.status_code == 203
    assert response.json() == {"detail": "Non-Authoritative database"}


@pytest.mark.asyncio
async def test_database_bad_getway(http_client_test, setup_module):
    """
    Test case -> bad gateway when try to connect with database
    :return:
    """
    response = await http_client_test.post(
        "/check/check_connections",
        json={
            "user_name": settings.db_username,
            "database_name": settings.db_name,
            "password": settings.db_password,
            "url": "wrong",
        },
    )
    assert response.status_code == 502
    assert response.json() == {"detail": "Bad gateway."}


@pytest.mark.asyncio
async def test_database_user_name_not_found(http_client_test, setup_module):
    """
    Test case -> user_name not found when try to connect with database
    :return:
    """
    response = await http_client_test.post(
        "/check/check_connections",
        json={
            "user_name": "wrong",
            "database_name": settings.db_name,
            "password": settings.db_password,
            "url": settings.db_url,
        },
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "User_name not found."}


@pytest.mark.asyncio
async def test_database_unauthorize(http_client_test, setup_module):
    """
    Test case -> unauthorized when try to connect with database
    :return:
    """
    response = await http_client_test.post(
        "/check/check_connections",
        json={
            "user_name": settings.db_username,
            "database_name": settings.db_name,
            "password": "wrong",
            "url": settings.db_url,
        },
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized."}
