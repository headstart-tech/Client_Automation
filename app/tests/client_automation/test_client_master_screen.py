"""
This file contains test cases related to update client screen router
"""

import pytest
from bson import ObjectId
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_client_screen_info(
        http_client_test, setup_module, client_screen_data, master_data,
        college_super_admin_access_token, access_token,
        test_college_validation, test_super_admin_validation
):
    """
     Test cases for Bench Marking
    """
    from app.database.configuration import DatabaseConfiguration
    # Not authenticated
    response = await http_client_test.post(
        f"/client_automation/update_feature_screen?dashboard_type=admin_dashboard&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for Bench Marking
    response = await http_client_test.post(
        f"/client_automation/update_feature_screen?dashboard_type=admin_dashboard&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Check the required dashboard details
    response = await http_client_test.post(
        f"/client_automation/update_feature_screen?dashboard_type=admin_dashboard&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={}
    )
    assert response.status_code == 422
    assert response.json() == {'detail': 'Screen detail mandatory'}

    await DatabaseConfiguration().master_screens.delete_many(
        {"screen_type": "college_screen",
         "college_id": ObjectId(str(test_college_validation.get('_id')))})
    await DatabaseConfiguration().master_screens.delete_many(
        {"screen_type": "master_screen"})

    # master screen not found
    response = await http_client_test.post(
        f"/client_automation/update_feature_screen?dashboard_type=admin_dashboard&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=client_screen_data
    )
    assert response.status_code == 404
    assert response.json()['detail'] == 'Master screen not found'

    # Create the master screen controller data by the super admin
    response = await http_client_test.post(
        f"/master/add_master_screen?dashboard_type=admin_dashboard&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=master_data
    )

    data = await DatabaseConfiguration().master_screens.find_one(
        {"screen_type": "master_screen"})
    feature_id = ""
    for key, val in data.items():
        if isinstance(val, dict):
            feature_id = key
            break
    json_data = {
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
    from app.database.configuration import DatabaseConfiguration
    query = {"status": {"$in": ["pending", "partially_approved"]}}
    pending_approvals = await DatabaseConfiguration().approvals_collection.find(query).to_list(length=None)
    for approvals in pending_approvals:
        await http_client_test.put(
            f"/approval/update_status/{str(approvals['_id'])}?feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            params={"status": "reject"},
            json={"remarks": "Not good"}
        )
    response = await http_client_test.post(
        f"/client_automation/add_features_screen?dashboard_type=admin_dashboard&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=json_data
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

    # Todo: For now we are commented
    # response = await http_client_test.post(
    #     f"/client_automation/update_feature_screen?dashboard_type=admin_dashboard&"
    #     f"college_id={str(test_college_validation.get('_id'))}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=json_data
    # )
    # assert response.status_code == 200
    # assert response.json()['message'] == 'College screen has been updated successfully.'

    # If already exists send message to user another API for update
    # response = await http_client_test.post(
    #     f"/client_automation/update_feature_screen?dashboard_type=admin_dashboard&"
    #     f"college_id={str(test_college_validation.get('_id'))}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=client_screen_data
    # )
    # assert response.status_code == 404
    # assert response.json()['detail'] == "Feature id 'string' not found"
