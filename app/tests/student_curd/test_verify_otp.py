"""
This file contains test cases for verify otp of email or mobile
"""
import pytest


@pytest.mark.asyncio
async def test_verify_otp(http_client_test, test_college_validation, setup_module, test_student_validation):
    """
    Verify otp of email or mobile
    """
    response = await http_client_test.get(
        f"/student_user_crud/verify_otp/?email_or_mobile={test_student_validation.get('user_name')}&otp=123456&college_id={str(test_college_validation.get('_id'))}&college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 200
    assert response.json() == {"message": "testing"}


@pytest.mark.asyncio
async def test_verify_otp_by_wrong_email_or_mobile(http_client_test, test_college_validation, setup_module):
    """
    Wrong email or mobile for verify otp of email or mobile
    """
    response = await http_client_test.get(
        f"/student_user_crud/verify_otp/?email_or_mobile=12345678&otp=123456&college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Enter correct email id or mobile number."}


@pytest.mark.asyncio
async def test_verify_otp_required_field_named_email_or_mobile(http_client_test, test_college_validation, setup_module):
    """
    Required field named email_or_mobile for verify otp of email or mobile
    """
    response = await http_client_test.get(
        f"/student_user_crud/verify_otp/?otp=123456&college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 400
    assert response.json() == {"detail": "Email Or Mobile must be required and valid."}


@pytest.mark.asyncio
async def test_verify_otp_required_field_named_otp(http_client_test, test_college_validation, setup_module):
    """
    Required field named otp for verify otp of email or mobile
    """
    response = await http_client_test.get(
        f"/student_user_crud/verify_otp/?email_or_mobile=12345678&college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 400
    assert response.json() == {"detail": "Otp must be required and valid."}
