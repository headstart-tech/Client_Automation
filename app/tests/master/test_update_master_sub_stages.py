
"""
This file contains test cases regarding Updation of  Master Sub Stages
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_master_sub_stage(http_client_test, setup_module, college_super_admin_access_token,test_master_sub_stages):
    """
    Test case for updating a master sub-stage.
    """

    test_sub_stage_id = str(test_master_sub_stages.get("_id"))
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
                "value": "",
                "error": "",
            }
        ],
    }

    # Not authenticated
    response = await http_client_test.put(
        f"/master_stages/update_master_sub_stage/{test_sub_stage_id}?feature_key={feature_key}", json=update_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for updating master sub-stage
    response = await http_client_test.put(
        f"/master_stages/update_master_sub_stage/{test_sub_stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
        json=update_data,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Invalid ID Format
    invalid_sub_stage_id = "invalid_id_123"
    response = await http_client_test.put(
        f"/master_stages/update_master_sub_stage/{invalid_sub_stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=update_data,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Field Name must be required and valid."

    # # Successful update
    # response = await http_client_test.put(
    #     f"/master_stages/update_master_sub_stage/{test_sub_stage_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=update_data,
    # )
    #
    # assert response.status_code == 200
    # assert response.json()["message"] == "Sub-stage updated successfully"


