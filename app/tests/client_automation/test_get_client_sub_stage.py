
"""
This file contains test cases regarding Retrieving Client Sub Stage By ID
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_client_sub_stage(http_client_test, setup_module, college_super_admin_access_token, test_client_sub_stages, college_counselor_access_token,
                                         test_college_validation):
    """
    Test case for retrieving a specific client sub-stage by ID.
    """

    sub_stage_id = str(test_client_sub_stages["_id"])

    #  Not authenticated
    response = await http_client_test.get(f"/client_student_dashboard/get_client_sub_stage/"
                                          f"?sub_stage_id={sub_stage_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for fetching client sub-stage
    response = await http_client_test.get(
        f"/client_student_dashboard/get_client_sub_stage/"
        f"?sub_stage_id={sub_stage_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Sub-stage not found
    invalid_sub_stage_id = "60c72b2f9b1e8b0f1c8e4d99"
    response = await http_client_test.get(
        f"/client_student_dashboard/get_client_sub_stage/"
        f"?sub_stage_id={invalid_sub_stage_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Client sub-stage not found"

    # Successful retrieval of a  client sub-stage
    from app.database.configuration import DatabaseConfiguration
    sub_stage = await DatabaseConfiguration().client_sub_stages.find_one({})
    if not sub_stage:
        pytest.skip("No sub-stage found in the database.")

    sub_stage_id = str(sub_stage.get("_id"))

    response = await http_client_test.get(
        f"/client_student_dashboard/get_client_sub_stage/?sub_stage_id={sub_stage_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert "sub_stage_name" in response.json()
