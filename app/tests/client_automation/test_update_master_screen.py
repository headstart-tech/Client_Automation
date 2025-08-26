"""
This file contains test cases related to update the master router.
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_master_screen_info(http_client_test, setup_module, master_data,
                                         college_super_admin_access_token, access_token,
                                         test_college_validation, test_super_admin_validation):
    """
     Test cases for Bench Marking
    """
    # Not authenticated
    response = await http_client_test.post(
        f"/master/update_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for Bench Marking
    response = await http_client_test.post(
        f"/master/update_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Check the required Screen details
    response = await http_client_test.post(
        f"/master/update_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={}
    )
    assert response.status_code == 422
    assert response.json() == {'detail': 'Screen details must be required'}

    # Update the master screen controller data by the super admin
    response = await http_client_test.post(
        f"/master/update_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=master_data
    )
    from app.database.configuration import DatabaseConfiguration
    data = await DatabaseConfiguration().master_screens.find_one({"screen_type": "master_screen"})
    if data:
        assert response.status_code == 200
        assert response.json()['message'] == 'Master screen controller updated successfully.'
    else:
        assert response.status_code == 422
        assert response.json() == {'detail': 'Master screen controller not exists.'}
    if not data:
        # Create the master screen controller data by the super admin
        response = await http_client_test.post(
            f"/master/add_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            json=master_data
        )
        assert response.status_code == 200
        assert response.json()['message'] == 'Master screen controller created successfully.'

    # Feature id not exists
    response = await http_client_test.post(
        f"/master/update_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "screen_details": [
                {
                    "feature_id": "453456",
                    "name": "string",
                    "description": "string",
                    "icon": "string",
                    "amount": 0,
                    "visibility": True,
                    "need_api": True,
                    "permissions": {
                        "read": True,
                        "write": True,
                        "delete": True
                    },
                    "features": [],
                    "additionalProp1": {}
                }
            ]
        }
    )
    assert response.status_code == 404
    assert response.json()[
               'detail'] == "This key '453456' is not found"
