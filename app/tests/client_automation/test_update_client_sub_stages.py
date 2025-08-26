
"""
This file contains test cases regarding Updation of  Client Sub Stages
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_client_sub_stages(http_client_test, setup_module, college_super_admin_access_token,test_client_sub_stages, test_client_stages, college_counselor_access_token,
                                         test_college_validation):
    """
    Test case for updating a client sub-stage.
    """

    test_sub_stage_id = str(test_client_sub_stages["_id"])
    update_data = {
        "sub_stage_name": "Updated Sub-Stage Name",
        "fields": [
            {
                "name": "field_name",
                "label": "Field 1",
                "type": "text",
                "is_required": True,
                "description": "Sample description",
                "locked": False,
                "is_custom": False,
                "depends_on": None,
            }
        ],
    }

    # Not authenticated
    response = await http_client_test.put(
        f"/client_student_dashboard/update_client_sub_stage/{test_sub_stage_id}?feature_key={feature_key}",
        json=update_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for updating client sub-stage
    response = await http_client_test.put(
        f"/client_student_dashboard/update_client_sub_stage/{test_sub_stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
        json=update_data,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Sub-stage not found
    invalid_sub_stage_id = "60c72b2f9b1e8b0f1c8e4d99"
    response = await http_client_test.put(
        f"/client_student_dashboard/update_client_sub_stage/{invalid_sub_stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=update_data,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Sub-stage not found"

    # Successful update
    response = await http_client_test.put(
        f"/client_student_dashboard/update_client_sub_stage/{test_sub_stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=update_data,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Client sub-stage updated successfully"


