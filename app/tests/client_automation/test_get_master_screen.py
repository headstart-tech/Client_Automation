"""
This file contains test cases related to get the master router.
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_master_screen_info(http_client_test, setup_module, master_data,
                                      college_super_admin_access_token, access_token,
                                      test_college_validation, test_super_admin_validation):
    """
     Test cases for Bench Marking
    """
    # Not authenticated
    response = await http_client_test.get(
        f"/master/get_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for Bench Marking
    response = await http_client_test.get(
        f"/master/get_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Update the master screen controller data by the super admin
    from app.database.configuration import DatabaseConfiguration
    data = await DatabaseConfiguration().master_screens.find_one({"screen_type": "master_screen"})
    if not data:
        response = await http_client_test.post(
            f"/master/add_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            json=master_data
        )
    response = await http_client_test.get(
        f"/master/get_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == 'Master screen controller details fetched successfully.'

    # Dashboard is required
    response = await http_client_test.get(
        f"/master/get_master_screen?dashboard_type=admin_dashboard&feature_id=67587&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()[
               'detail'] == "Feature ID '67587' not found."
