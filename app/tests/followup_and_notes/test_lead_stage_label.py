"""
test cases of lead stage label routes
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_lead_label_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    test case lead label not authenticated
    """
    response = await http_client_test.get(f"/followup_notes/get_lead_stage_label"
                                          f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer wrong token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_lead_label(http_client_test, college_super_admin_access_token,
                              test_college_validation, setup_module):
    """
    test case lead label not authenticated
    """
    response = await http_client_test.get(f"/followup_notes/get_lead_stage_label"
                                          f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
