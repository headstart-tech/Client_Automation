"""
This file contains test cases related to API route/endpoint get leads details based on source
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_leads_details_based_on_source_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/campaign_manager/source_performance_details/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_leads_details_based_on_source_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get leads details based on source
    """
    response = await http_client_test.post(
        f"/campaign_manager/source_performance_details/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_leads_details_based_on_source_no_permission(
        http_client_test, access_token, test_campaign_data, setup_module, test_college_validation
):
    """
    No permission for get leads details based on source
    """
    response = await http_client_test.post(
        f"/campaign_manager/source_performance_details/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_leads_details_based_on_source_no_permission(
        http_client_test, access_token, test_campaign_data, setup_module, test_college_validation
):
    """
    No permission for get leads details based on source
    """
    response = await http_client_test.post(
        f"/campaign_manager/source_performance_details/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_leads_details_based_on_source(http_client_test, college_super_admin_access_token, test_campaign_data,
                                             setup_module, test_college_validation):
    """
    Get leads details based on source
    """
    response = await http_client_test.post(
        f"/campaign_manager/source_performance_details/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get source performance details."


@pytest.mark.asyncio
async def test_leads_details_based_on_source_and_date_range(http_client_test, college_super_admin_access_token,
                                                            test_campaign_data,
                                                            setup_module, test_college_validation, start_end_date):
    """
    Get leads details based on source and date range
    """
    response = await http_client_test.post(
        f"/campaign_manager/source_performance_details/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={"date_range": start_end_date})
    assert response.status_code == 200
    assert response.json()['message'] == "Get source performance details."
