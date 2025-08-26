"""
This file contains test cases regarding refresh token verification
"""
import pytest


@pytest.mark.asyncio
async def test_verify_refresh_token(http_client_test, student_refresh_token, setup_module, test_student_validation):
    """
    Test case -> for obtain refresh token info
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().refresh_token_collection.insert_one(
        {'user_id': test_student_validation.get("_id"), 'refresh_token': student_refresh_token.get("refresh_token"),
         "expiry_time": student_refresh_token.pop("expiry_time"), "issued_at": student_refresh_token.pop("issued_at"),
         "revoked": False, "college_info": [{"name": "test", "_id": test_student_validation.get("college_id")}]})
    response = await http_client_test.post(
        f"/oauth/refresh_token/verify/?token={student_refresh_token.get('refresh_token')}")
    assert response.status_code == 200
    for key in ["access_token", "token_type"]:
        assert key in response.json()


@pytest.mark.asyncio
async def test_read_existent_student_bad_token(http_client_test, setup_module):
    """
    Test case -> bad refresh token send for verification
    """
    response = await http_client_test.post("/oauth/refresh_token/verify/?token=wrongtoken")
    assert response.status_code == 422
    assert response.json()["detail"] == "Token is not valid"


@pytest.mark.asyncio
async def test_read_existent_student_token_not_send(http_client_test, setup_module):
    """
    Test case -> refresh token not send for verification
    """
    response = await http_client_test.post("/oauth/refresh_token/verify/")
    assert response.status_code == 422
    assert response.json()["detail"] == "Token is not valid"
