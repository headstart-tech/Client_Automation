"""
this route for call activity glance
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_call_activity_glance_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    test case for not authenticated
    """
    response = await http_client_test.get(f"/call_activities/one_glance_view"
                                          f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                          headers={"Authorization": "Bearer wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_call_activity_glance(http_client_test, test_college_validation,
                                    college_super_admin_access_token, setup_module):
    """
    test case for get data from call activity
    """
    response = await http_client_test.get(f"/call_activities/one_glance_view"
                                          f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
