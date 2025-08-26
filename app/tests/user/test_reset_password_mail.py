"""
This file contains test cases of send reset password mail to user
"""
import pytest


@pytest.mark.asyncio
async def test_send_reset_password_mail_to_user_required_email_id(
        http_client_test, setup_module, test_college_validation
):
    """
    Required email id for send reset password mail to user
    """
    response = await http_client_test.post(
        f"/user/reset_password/?college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Email must be required and valid."


@pytest.mark.asyncio
async def test_send_reset_password_mail_to_user(http_client_test, setup_module, test_college_validation):
    """
    Send reset password mail to user
    """
    response = await http_client_test.post(
        f"/user/reset_password/?email=apollo@example.com&college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Mail sent successfully."}
