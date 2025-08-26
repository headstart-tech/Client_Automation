"""
This file contains test cases regarding API routes/endpoints related to send email to student
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_reset_password_template_required_email(
        http_client_test, test_college_validation,
        college_counselor_access_token, setup_module):
    """
    Required email for reset student password
    """
    response = await http_client_test.post(
        f"/student/email/reset_password_template/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Email must be required and valid."


@pytest.mark.asyncio
async def test_reset_password_template(
        http_client_test, test_college_validation, setup_module,
        test_student_validation, college_counselor_access_token
):
    """
    Reset student password
    """
    response = await http_client_test.post(
        f"/student/email/reset_password_template/?email={test_student_validation['user_name']}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 200
    assert response.json()["message"] == "Mail sent successfully."


@pytest.mark.asyncio
async def test_reset_password_field_required(http_client_test, setup_module):
    """
    Field required for reset password of student
    """
    response = await http_client_test.get(
        f"/student/email/reset_password/test/?feature_key={feature_key}")
    assert response.status_code == 400
    assert response.json()[
               "detail"] == "New Password must be required and valid."


@pytest.mark.asyncio
async def test_send_verification_email_required_email(
        http_client_test, test_college_validation,
        setup_module, college_counselor_access_token):
    """
    Test case -> required student email id for send verification email to student
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/student/email/verification/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Body must be required and valid."


@pytest.mark.asyncio
async def test_send_verification_email__empty(
        http_client_test, test_college_validation,
        setup_module, college_counselor_access_token):
    """
    Test case -> required student email id for send verification email to student is null
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/student/email/verification/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json=[])
    assert response.status_code == 422
    assert response.json()["detail"] == "Please enter student email id"


@pytest.mark.asyncio
async def test_send_verification_email(
        http_client_test, test_college_validation, setup_module,
        test_student_validation, college_counselor_access_token
):
    """
    Test case -> for send verification email to student
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/student/email/verification/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json=[test_student_validation.get('user_name')]
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Verification email sent."
