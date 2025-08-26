"""
This file contains test cases for manual allocate counselor
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_manual_counselor_application_not_found(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Not found for manual allocate counselor
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/counselor/manual_counselor?application_id=62a8ca5f4035e93c7ff2460g"
        f"&counselor_id=62bfcb0fd7a6a3c9a4e6d32b&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "application_id not valid"


@pytest.mark.asyncio
async def test_manual_counselor_not_authenticate(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Not authenticated for manual allocate counselor
    """
    response = await http_client_test.post(
        f"/counselor/manual_counselor?application_id=62a8ca5f4035e93c7ff2460f&counselor_id="
        f"62bfcb0fd7a6a3c9a4e6d32b&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f" wrong Bearer "},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# @pytest.mark.asyncio
# async def test_manual_counselor2(
#         http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
#         test_counselor_validation, application_details
# ):
#     """
#     Manual allocate counselor
#     """
#     response = await http_client_test.post(
#         f"/counselor/manual_counselor?application_id={application_details.get('_id')}&feature_key={feature_key}"
#         f"&counselor_id={test_counselor_validation.get('_id')}&college_id={str(test_college_validation.get('_id'))}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "counselor update successfully"
