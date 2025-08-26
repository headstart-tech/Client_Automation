"""
This file contains test cases for send otp through email or mobile
"""
import pytest


# ToDo - Following commented test cases giving error when run all test cases
# @pytest.mark.asyncio
# async def test_login_with_otp(http_client_test, test_college_validation, setup_module, test_student_validation):
#     """
#     Send otp through email or mobile
#     """
#     response = await http_client_test.post(
#         f"/student_user_crud/login_with_otp/?email_or_mobile={test_student_validation.get('user_name')}&college_id={str(test_college_validation.get('_id'))}")
#     assert response.status_code == 200
#     assert response.json() == {'message': "OTP is sent through email id or mobile number.", 'time_remaining': 900000}


@pytest.mark.asyncio
async def test_login_with_otp_by_wrong_email_or_mobile(http_client_test, test_college_validation, setup_module):
    """
    Wrong email or mobile for send otp through email or mobile
    """
    response = await http_client_test.post(
        f"/student_user_crud/login_with_otp/?email_or_mobile=12345678&college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Enter correct email id or mobile number."}


@pytest.mark.asyncio
async def test_login_with_otp_required_field(http_client_test, test_college_validation, setup_module):
    """
    Required field named email_or_mobile for send otp through email or mobile
    """
    response = await http_client_test.post(
        f"/student_user_crud/login_with_otp/?college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 400
    assert response.json() == {"detail": "Email Or Mobile must be required and valid."}
