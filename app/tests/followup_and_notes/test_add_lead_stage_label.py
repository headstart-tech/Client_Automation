"""
this file contains add lead stage label test cases
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_lead_stage_label_not_authentication(http_client_test, setup_module, test_college_validation):
    """
    test case for checking data is update or not
    """
    response = await http_client_test.put(f"/followup_notes/add_lead_stage_label?lead_stage=checking&label=check"
                                          f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer wrong bearer"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_add_lead_stage_label(http_client_test, college_super_admin_access_token, setup_module,
                                    test_college_validation):
    """
    test case for checking authentication user
    """
    response = await http_client_test.put(f"/followup_notes/add_lead_stage_label?lead_stage=checking&label=check"
                                          f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    print(response.json()["data"][0]["checking"])
    assert response.status_code == 200
    assert "check" in response.json()["data"][0]["checking"]
