
"""
This file contains test cases regarding Retrieving Master Sub Stage By ID
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_master_sub_stage(http_client_test, setup_module, college_super_admin_access_token):
    """
    Test case for retrieving a specific master sub-stage by ID.
    """

    sub_stage_id = "67c9259194870eb19c7a543f"

    #  Not authenticated
    response = await http_client_test.get(f"/master_stages/get_master_sub_stage/{sub_stage_id}?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for fetching master sub-stage
    response = await http_client_test.get(
        f"/master_stages/get_master_sub_stage/{sub_stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Sub-stage not found
    invalid_sub_stage_id = "60c72b2f9b1e8b0f1c8e4d99"  # Non-existent ObjectId
    response = await http_client_test.get(
        f"/master_stages/get_master_sub_stage/{invalid_sub_stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Master stage not found"

    # Successful retrieval of a master sub-stage
    from app.database.configuration import DatabaseConfiguration
    sub_stage = await DatabaseConfiguration().sub_stages.find_one({})  # Fetch a valid sub-stage
    if not sub_stage:
        pytest.skip("No sub-stage found in the database.")

    sub_stage_id = str(sub_stage.get("_id"))

    response = await http_client_test.get(
        f"/master_stages/get_master_sub_stage/{sub_stage_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert "sub_stage_name" in response.json()  # Ensure response contains sub-stage data
