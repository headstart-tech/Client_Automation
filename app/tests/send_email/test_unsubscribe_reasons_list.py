"""
this file contains test cases of unsubscribe reasons list
"""

import pytest

@pytest.mark.asyncio
async def test_unsubscribe_reasons_list(
        http_client_test, setup_module, test_jwt_token_with_wrong_username, test_jwt_token
):
    """
    Check token is valid or not
    """
    response = await http_client_test.get(
        f"/email/unsubscribe/reason_list/bdhgwdwqjdidqdjqndhwbchwegvcwabbcvweajhcbwagvcuwgdwd"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token is not valid"

    """
    Actual API
    """
    response = await http_client_test.get(
        f"/email/unsubscribe/reason_list/{test_jwt_token}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Unsubscribe Reason List"
    assert "others" in response.json()["data"]
