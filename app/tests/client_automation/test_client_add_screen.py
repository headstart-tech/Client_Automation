"""
This file contains test cases related to client screen router
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_client_screen_info(http_client_test, setup_module, client_screen_data, master_data,
                                  college_super_admin_access_token, access_token,
                                  test_college_validation, test_super_admin_validation,
                                  client_manager_access_token, test_client_manager_validation):
    """
     Test cases for Bench Marking
    """
    # Not authenticated
    response = await http_client_test.post(
        f"/client_automation/add_features_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for Bench Marking
    response = await http_client_test.post(
        f"/client_automation/add_features_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Check the required Screen details
    response = await http_client_test.post(
        f"/client_automation/add_features_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {client_manager_access_token}"},
        json={}
    )
    assert response.status_code == 422
    assert response.json() == {'detail': 'Screen details must be required'}

    # Create the master screen controller data by the super admin
    from app.database.configuration import DatabaseConfiguration
    response = await http_client_test.post(
        f"/master/add_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=master_data
    )
    await DatabaseConfiguration().master_screens.delete_many(
        {"screen_type": "client_screen"})
    data = await DatabaseConfiguration().master_screens.find_one(
        {"screen_type": "master_screen"})
    feature_id = ""
    for key, val in data.items():
        if isinstance(val, dict):
            feature_id = key
            break
    response = await http_client_test.post(
        f"/client_automation/add_features_screen?dashboard_type=admin_dashboard&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "screen_details": [
                {
                    "feature_id": str(feature_id),
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
    assert response.status_code == 200
    approval_id = response.json().get("approval_id")

    # Approving the Request
    response = await http_client_test.put(
        f"/approval/update_status/{approval_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"status": "approve"},
        json={"remarks": "Looks good"}
    )
    assert response.status_code == 200

