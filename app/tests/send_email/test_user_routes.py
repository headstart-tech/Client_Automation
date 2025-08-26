"""
This file contains test cases regarding API routes/endpoints related to send email to user
"""
import pytest


@pytest.mark.asyncio
async def test_reset_password_required_email(http_client_test, test_college_validation, setup_module):
    """
    Test case -> required email for reset student password
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/user/reset_password/?college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Email must be required and valid."


@pytest.mark.asyncio
async def test_reset_password_template_wrong_email(http_client_test, test_college_validation, setup_module):
    """
    Test case -> wrong email for reset user password
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/user/reset_password/?email=wrong_email&college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 400
    assert response.json()["detail"] == "value is not a valid email address: The email address is not valid. It must have exactly one @-sign."


@pytest.mark.asyncio
async def test_reset_password_template(
        http_client_test, test_college_validation, setup_module, test_user_validation
):
    """
    Test case -> for reset user password
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/user/reset_password/?email={test_user_validation.get('user_name')}&college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Mail sent successfully."


@pytest.mark.asyncio
async def test_reset_password_field_required(http_client_test, setup_module):
    """
    Test case -> field required for reset student password
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get("/student/email/reset_password/test/")
    assert response.status_code == 400
    assert response.json()["detail"] == "New Password must be required and valid."
