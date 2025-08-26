"""
this file contains test cases of email unsubscribe function
"""

import pytest

@pytest.mark.asyncio
async def test_send_wrong_token(
        http_client_test, setup_module
):
    """
    Check token is valid or not
    """
    response = await http_client_test.get(
        f"/email/unsubscribe/bdhgwdwqjdidqdjqndhwbchwegvcwabbcvweajhcbwagvcuwgdwd?unsubscribe_status=true"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token is not valid"
# TODO Test cases are not passing, Check why?
# @pytest.mark.asyncio
# async def test_send_wrong_email(
#         http_client_test, setup_module, test_jwt_token_with_wrong_username
# ):
#     """
#     send wrong email in token who is not exists in our collection
#     """
#     response = await http_client_test.get(
#         f"/email/unsubscribe/{test_jwt_token_with_wrong_username}?unsubscribe_status=true"
#     )
#     assert response.status_code == 404
#     assert response.json()["detail"] == "student not exists"


# @pytest.mark.asyncio
# async def test_unsubscribe_token(
#         http_client_test, setup_module, test_jwt_token
# ):
#     """
#     send email in token who is exists in our collection
#     """
#     response = await http_client_test.get(
#         f"/email/unsubscribe/{test_jwt_token}?unsubscribe_status=true"
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Promotional email notification has been unsubscribe successfully"
#
#
# async def test_subscribe_token(
#         http_client_test, setup_module, test_jwt_token
# ):
#     """
#     send email in token who is exists in our collection
#     """
#     response = await http_client_test.get(
#         f"/email/unsubscribe/{test_jwt_token}?unsubscribe_status=false"
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Promotional email notification has been subscribe successfully"
