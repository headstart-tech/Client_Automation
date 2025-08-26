"""
This file contains test cases related to check API route/endpoint campaign rule name exists or not
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_check_rule_name_already_exist(http_client_test, test_college_validation, setup_module,
                                             test_campaign_rule_data,
                                             college_super_admin_access_token):
    """
    Campaign rule name already exist
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().rule_collection.delete_many({})
    await http_client_test.post(
        f"/campaign/create_rule/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            json=test_campaign_rule_data)
    response = await http_client_test.get(
        f"/campaign/check_rule_name_exist_or_not/?rule_name={test_campaign_rule_data.get('rule_name')}&college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 200
    assert response.json() == {'detail': 'Rule name already exists.'}


@pytest.mark.asyncio
async def test_check_rule_name_not_exist(http_client_test, test_college_validation, setup_module,
                                         test_campaign_rule_data,
                                         college_super_admin_access_token):
    """
    Campaign rule name not exist
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().rule_collection.delete_many({})
    response = await http_client_test.get(
        f"/campaign/check_rule_name_exist_or_not/?rule_name={test_campaign_rule_data.get('rule_name')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 200
    assert response.json() == {'message': 'Rule name not exist.'}


@pytest.mark.asyncio
async def test_check_rule_name_required_field(http_client_test, test_college_validation, setup_module,
                                              test_campaign_rule_data,
                                              college_super_admin_access_token):
    """
    Required field name rule_name for campaign rule name not exist
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().rule_collection.delete_many({})
    response = await http_client_test.get(
        f"/campaign/check_rule_name_exist_or_not/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 400
    assert response.json() == {'detail': 'Rule Name must be required and valid.'}
