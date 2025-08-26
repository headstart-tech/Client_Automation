"""
This file test cases related to send email to student
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_send_email_sidebar_not_authentication(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Check authentication user
    """
    response = await http_client_test.post(
        f"/lead/send_email_sidebar?to=test@example.com&subject=testing&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f" wrong Bearer"},
        json={"message": "hey this this test only"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

# @pytest.mark.asyncio
# async def test_send_mail_sidebar(http_client_test, test_college_validation, college_super_admin_access_token):
#     """
#     access_token
#     to: email_id
#     subject: string type
#     message: string type
#     """
#     response = await http_client_test.post(
#         f"/lead/send_email_sidebar?to=test@example.com&subject=testing&college_id={str(test_college_validation.get('_id'))}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#         json={"message": "hey this this test only"}
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Mail send successfully"
