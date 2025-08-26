"""
This file contains test cases related to master screen router
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_master_screen_info(http_client_test, setup_module, master_data,
                                  college_super_admin_access_token, access_token,
                                  test_college_validation, test_super_admin_validation):
    """
     Test cases for Bench Marking
    """
    # Not authenticated
    response = await http_client_test.post(
        f"/master/add_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for Bench Marking
    response = await http_client_test.post(
        f"/master/add_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Check the required Screen details
    response = await http_client_test.post(
        f"/master/add_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={}
    )
    assert response.status_code == 422
    assert response.json() == {'detail': 'Screen details must be required'}

    # Create the master screen controller data by the super admin
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().master_screens.delete_many({"screen_type": "master_screen"})
    response = await http_client_test.post(
        f"/master/add_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=master_data
    )
    assert response.status_code == 200
    assert response.json()['message'] == 'Master screen controller created successfully.'

    # If already exists send message to user another API for update else create new
    response = await http_client_test.post(
        f"/master/add_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=master_data
    )
    try:
        assert response.status_code == 422
        assert response.json()[
                   'detail'] == "Master screen controller already exists."
    except:
        assert response.status_code == 200
        assert response.json()['message'] == 'Master screen controller created successfully.'
