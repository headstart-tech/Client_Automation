"""
This file contains test cases related to API route/endpoint update status of campaign rule
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

# Todo: We are delete this route first confirmation
@pytest.mark.asyncio
async def test_update_status_of_campaign_rule_not_authenticated(http_client_test, test_college_validation,
                                                                setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/campaign/update_status_of_rule/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_status_of_campaign_rule_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for update status of campaign rule
    """
    response = await http_client_test.put(
        f"/campaign/update_status_of_rule/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_update_status_of_campaign_rule_required_status(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, access_token
):
    """
    Required for update status of campaign rule
    """
    response = await http_client_test.put(
        f"/campaign/update_status_of_rule/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 400
    assert response.json() == {'detail': "Enabled must be required and valid."}


@pytest.mark.asyncio
async def test_update_status_of_campaign_rule_no_permission(
        http_client_test, test_college_validation, access_token, test_campaign_rule_data, setup_module
):
    """
    Required status for update status of campaign rule
    """
    response = await http_client_test.put(
        f"/campaign/update_status_of_rule/?enabled=true"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_status_of_campaign_rule_required_field(
        http_client_test, test_college_validation, college_super_admin_access_token, test_campaign_rule_data,
        setup_module
):
    """
    No permission for update status of campaign rule
    """
    response = await http_client_test.put(
        f"/campaign/update_status_of_rule/"
        f"?enabled=true&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {'detail': "Need to provide rule_id or rule_name."}


@pytest.mark.asyncio
async def test_update_status_of_campaign_rule_by_name(http_client_test, test_college_validation,
                                                      college_super_admin_access_token,
                                                      test_campaign_rule_data, setup_module):
    """
    Update status of campaign rule by name
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().rule_collection.delete_many({})
    await http_client_test.post(
        f"/campaign/create_rule/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            json=test_campaign_rule_data)
    response = await http_client_test.put(
        f"/campaign/update_status_of_rule/?enabled=false&feature_key={feature_key}"
        f"&rule_name={test_campaign_rule_data.get('rule_name')}&college_id={str(test_college_validation.get('_id'))}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "Updated status of rule."}


@pytest.mark.asyncio
async def test_update_status_of_campaign_rule_by_id(http_client_test, test_college_validation,
                                                    college_super_admin_access_token,
                                                    test_campaign_rule_data, setup_module):
    """
    Update status of campaign rule by is
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().rule_collection.delete_many({})
    await http_client_test.post(
        f"/campaign/create_rule/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            json=test_campaign_rule_data)
    campaign_rule = await DatabaseConfiguration().rule_collection.find_one(
        {'rule_name': str(test_campaign_rule_data.get('rule_name')).title()})
    response = await http_client_test.put(
        f"/campaign/update_status_of_rule/?enabled=false&feature_key={feature_key}&"
        f"rule_id={str(campaign_rule.get('_id'))}&college_id={str(test_college_validation.get('_id'))}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "Updated status of rule."}


@pytest.mark.asyncio
async def test_update_status_of_campaign_rule_no_found(http_client_test, test_college_validation,
                                                       college_super_admin_access_token, setup_module,
                                                       test_campaign_rule_data):
    """
    Campaign not found by name
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().rule_collection.delete_many({})
    response = await http_client_test.put(
        f"/campaign/update_status_of_rule/?enabled=false&feature_key={feature_key}"
        f"&rule_name={test_campaign_rule_data.get('rule_name')}&college_id={str(test_college_validation.get('_id'))}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['detail'] == 'Rule not found.'
