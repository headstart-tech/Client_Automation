"""
This file contains test cases regarding revoke refresh token
"""
import pytest


@pytest.mark.asyncio
async def test_revoke_refresh_token(http_client_test, student_refresh_token, setup_module, test_student_validation):
    """
    Test case -> for revoke refresh token
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().refresh_token_collection.insert_one(
        {'user_id': test_student_validation.get("_id"), 'refresh_token': student_refresh_token.get("refresh_token"),
         "expiry_time": student_refresh_token.pop("expiry_time"), "issued_at": student_refresh_token.pop("issued_at"),
         "revoked": False})
    response = await http_client_test.post(
        f"/oauth/refresh_token/revoke/?token={student_refresh_token.get('refresh_token')}")
    assert response.status_code == 200
    assert response.json() == {"message": "Refresh token is revoked."}

    # Try to revoke already revoked refresh token

    response = await http_client_test.post(
        f"/oauth/refresh_token/revoke/?token={student_refresh_token.get('refresh_token')}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Refresh token is already revoked."}


@pytest.mark.asyncio
async def test_revoke_bad_refresh_token(http_client_test, setup_module):
    """
    Test case -> bad refresh token send for revoke
    """
    response = await http_client_test.post("/oauth/refresh_token/revoke/?token=wrongtoken")
    assert response.status_code == 422
    assert response.json()["detail"] == "Token is not valid"


@pytest.mark.asyncio
async def test_revoke_refresh_token_not_send(http_client_test, setup_module):
    """
    Test case -> refresh token not send for revoke
    """
    response = await http_client_test.post("/oauth/refresh_token/revoke/")
    assert response.status_code == 422
    assert response.json()["detail"] == "Token is not valid"
