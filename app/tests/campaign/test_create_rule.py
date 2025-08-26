"""
This file contains test cases related to check API route/endpoint create campaign rule
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

# Todo: We are delete this route first confirmation
@pytest.mark.asyncio
async def test_create_campaign_rule_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/campaign/create_rule/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_campaign_rule_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for create campaign rule
    """
    response = await http_client_test.post(
        f"/campaign/create_rule/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_create_campaign_rule_field_required(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Field required for create campaign rule
    """
    response = await http_client_test.post(
        f"/campaign/create_rule/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}


@pytest.mark.asyncio
async def test_create_campaign_rule_no_permission(
        http_client_test, test_college_validation, access_token, test_campaign_rule_data, setup_module
):
    """
    No permission for create campaign rule
    """
    response = await http_client_test.post(
        f"/campaign/create_rule/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=test_campaign_rule_data,
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_campaign_rule(http_client_test, test_college_validation, college_super_admin_access_token,
                                    test_campaign_rule_data,
                                    setup_module):
    """
    Create campaign rule
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().rule_collection.delete_many({})
    response = await http_client_test.post(
        f"/campaign/create_rule/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_campaign_rule_data)
    assert response.status_code == 200
    assert response.json()['message'] == "Rule created."


@pytest.mark.asyncio
async def test_create_campaign_rule_already_exist(http_client_test, test_college_validation,
                                                  college_super_admin_access_token,
                                                  test_campaign_rule_data,
                                                  setup_module):
    """
    Already exist for create campaign rule
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().rule_collection.delete_many({})
    await http_client_test.post(
        f"/campaign/create_rule/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            json=test_campaign_rule_data)
    response = await http_client_test.post(
        f"/campaign/create_rule/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_campaign_rule_data)
    assert response.status_code == 200
    assert response.json()['detail'] == 'Rule name already exists.'


@pytest.mark.asyncio
async def test_update_campaign_rule(http_client_test, test_college_validation, college_super_admin_access_token,
                                    test_campaign_rule_data,
                                    setup_module):
    """
    Update campaign rule
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().rule_collection.delete_many({})
    await http_client_test.post(
        f"/campaign/create_rule/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            json=test_campaign_rule_data)
    rule = await DatabaseConfiguration().rule_collection.find_one(
        {'rule_name': str(test_campaign_rule_data.get('rule_name')).title()})
    response = await http_client_test.post(
        f"/campaign/create_rule/?rule_id={str(rule.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"rule_description": "string"})
    assert response.status_code == 200
    assert response.json()['message'] == 'Rule updated.'
