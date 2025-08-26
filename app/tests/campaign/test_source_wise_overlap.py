"""
This file contains test cases regarding for campaign header routes
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_campaign_overlap_not_authenticated(
        http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in campaign overlap utm source routes
    """
    response = await http_client_test.post(
        f"/campaign/source_wise_overlap"
        f"?change_indicator=last_7_days"
        f"&page_num=1&page_size=25"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_campaign_overlap_bad_credentials(
        http_client_test, test_college_validation, setup_module):
    """
    Bad token for campaign overlap utm source routes
    """
    response = await http_client_test.post(
        f"/campaign/source_wise_overlap"
        f"?change_indicator=last_7_days"
        f"&page_num=1&page_size=25"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_campaign_overlap_field_required(
        http_client_test, test_college_validation,
        college_super_admin_access_token, setup_module
):
    """
    Field required for campaign overlap utm source routes
    """
    response = await http_client_test.post(
        f"/campaign/source_wise_overlap"
        f"?change_indicator=last_7_days"
        f"&page_num=1&page_size=25&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be"
                                         " required and valid."}


@pytest.mark.asyncio
async def test_campaign_overlap_no_permission(
        http_client_test, test_college_validation, access_token,
        test_campaign_rule_data, setup_module
):
    """
    No permission for campaign overlap utm source routes
    """
    response = await http_client_test.post(
        f"/campaign/source_wise_overlap"
        f"?change_indicator=last_7_days"
        f"&page_num=1&page_size=25"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_campaign_overlap(http_client_test, test_college_validation,
                                college_super_admin_access_token,
                                setup_module):
    """
    Get the 200 response from the campaign header routes
    """
    response = await http_client_test.post(
        f"/campaign/source_wise_overlap"
        f"?change_indicator=last_7_days"
        f"&page_num=1&page_size=25"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
