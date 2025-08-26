"""
This file contains test cases related to get client, master and college screen router
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_screen_info(http_client_test, setup_module, client_screen_data,
                               college_super_admin_access_token, access_token,
                               test_college_validation, master_data):
    """
     Test cases for Bench Marking
    """
    # Todo: For now we are passing dummy client id
    # Not authenticated
    response = await http_client_test.get(
        f"/client_automation/get_screen_details?page_num=1&page_size=2"
        f"&dashboard_type=admin_dashboard&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for Bench Marking
    response = await http_client_test.get(
        f"/client_automation/get_screen_details?page_num=1&page_size=2"
        f"&dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    response = await http_client_test.post(
        f"/master/add_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=master_data
    )

    # get screen details
    response = await http_client_test.get(
        f"/client_automation/get_screen_details?page_num=1&page_size=2"
        f"&dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == 'Get Screen details.'

    # get screen details with client id
    response = await http_client_test.get(
        f"/client_automation/get_screen_details?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=2&dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == 'Get Screen details.'
