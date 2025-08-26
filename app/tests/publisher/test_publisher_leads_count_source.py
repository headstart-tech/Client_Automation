"""
This file contains all test case of get_publisher_leads_count
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_publisher_leads_count_permission(http_client_test, test_college_validation, setup_module,
                                                    college_super_admin_access_token):
    """
    No permission except publisher counselor
    """
    response = await http_client_test.post(
        f"/publisher/get_publisher_percentage_data?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_get_publisher_leads_count(http_client_test, test_college_validation, setup_module,
                                         publisher_access_token):
    """
    No permission except publisher counselor
    """
    response = await http_client_test.post(
        f"/publisher/get_publisher_percentage_data?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {publisher_access_token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "fetch all count of sources successfully"


@pytest.mark.asyncio
async def test_get_publisher_leads_count_wrong_token(http_client_test, test_college_validation, setup_module):
    """
    check api with wrong token
    """
    response = await http_client_test.post(
        f"/publisher/get_publisher_percentage_data?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": "wrong token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
