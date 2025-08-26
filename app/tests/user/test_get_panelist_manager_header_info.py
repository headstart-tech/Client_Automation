"""
This file contains test cases regarding get panelist manager header info
"""
import pytest
from app.tests.conftest import user_feature_data
feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_panelist_manager_header_info(
        http_client_test, test_college_validation, setup_module,
        test_student_validation, access_token,
        college_super_admin_access_token):
    """
    Different test cases regarding get panelist manager header info
    """
    # Not authenticated if user not logged in
    response = await http_client_test.get(
        f"/user/panelist_manager_header_info/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get panelist manager header info
    response = await http_client_test.get(
        f"/user/panelist_manager_header_info/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # No permission for get panelist manager header info
    response = await http_client_test.get(
        f"/user/panelist_manager_header_info/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Required college id for get panelist manager header info
    response = await http_client_test.get(
        f"/user/panelist_manager_header_info/?feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and ' \
                                        'valid.'

    # Invalid college id for get panelist manager header info
    response = await http_client_test.get(
        f"/user/panelist_manager_header_info/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input ' \
                                        'or a 24-character hex string'

    # College not found for get panelist manager header info
    response = await http_client_test.get(
        f"/user/panelist_manager_header_info/?"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Get panelist manager header info
    response = await http_client_test.get(
        f"/user/panelist_manager_header_info/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get panelist manager header info."
    for name in ["active_panelist", "available_slots", "interview_done",
                 "total_panelists"]:
        assert name in response.json()["data"]
