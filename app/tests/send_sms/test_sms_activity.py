"""This file contains Test cases for SMS Activity"""
import pytest


@pytest.mark.asyncio
async def test_sms_activity_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Test case : Not Authenticated if user not logged in
    """
    response = await http_client_test.post(f"/sms/send_to_user/?college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

# ToDo - Following commented test case giving error when run all test cases
# @pytest.mark.asyncio
# async def test_sms_activity_send_sms(
#         http_client_test, test_college_validation, setup_module, super_admin_access_token, test_student_validation
# ):
#     response = await http_client_test.post(
#         f"/sms/send_to_user/?college_id={str(test_college_validation.get('_id'))}&send_to={test_student_validation.get('basic_details', {}).get('mobile_number')}&sms_content=string&dlt_content_id=1234",
#         headers={"Authorization": f"Bearer {super_admin_access_token}"}, json=["9898989898"])
#     """
#     if user is authenticated sms will be sent to user
#     """
#     assert response.status_code == 200
#     assert response.json()["message"] == "SMS sent successfully"
