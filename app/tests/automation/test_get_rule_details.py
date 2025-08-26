"""
This file contains test cases related to API route/endpoint get automation rule details
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_automation_rule_details_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/automation/rule_details/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_automation_rule_details_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get automation rule details by id
    """
    response = await http_client_test.put(
        f"/automation/rule_details/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_automation_rule_details_required_automation_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Required page number for get automation rule details by id
    """
    response = await http_client_test.put(
        f"/automation/rule_details/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Automation Id must be required and valid.'}


@pytest.mark.asyncio
async def test_get_automation_rule_details_required_page_number(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Required page number for get automation rule details by id
    """
    response = await http_client_test.put(
        f"/automation/rule_details/?automation_id=123456789012345678901234"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Num must be required and valid."}


@pytest.mark.asyncio
async def test_get_automation_rule_details_required_page_size(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Field required for get automation rule details by id
    """
    response = await http_client_test.put(
        f"/automation/rule_details/?automation_id=123456789012345678901234&page_num=1"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Size must be required and valid."}


@pytest.mark.asyncio
async def test_get_automation_rule_details_no_permission(
        http_client_test, test_college_validation, access_token, test_automation_data, setup_module
):
    """
    No permission for get automation rule details by id
    """
    response = await http_client_test.put(
        f"/automation/rule_details/?automation_id=123456789012345678901234&page_num=1&"
        f"page_size=1&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_automation_rule_details(
        http_client_test, test_college_validation, college_super_admin_access_token,
        test_automation_rule_details_validation, setup_module
):
    """
    Get automation rule details by id
    """
    response = await http_client_test.put(
        f"/automation/rule_details/?automation_id={test_automation_rule_details_validation}"
        f"&page_num=1&page_size=1&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get automation rule details."


@pytest.mark.asyncio
async def test_get_automation_rule_details_by_module_type(
        http_client_test, test_college_validation, college_super_admin_access_token,
        test_automation_rule_details_validation, setup_module,
        test_automation_rule_details
):
    """
    Get automation rule details by id and module type
    """
    response = await http_client_test.put(
        f"/automation/rule_details/?automation_id={test_automation_rule_details_validation}"
        f"&page_num=1&page_size=1&module_type={test_automation_rule_details.get('module_name')}&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get automation rule details."


@pytest.mark.asyncio
async def test_get_automation_rule_details_by_data_segment_name(
        http_client_test, test_college_validation, college_super_admin_access_token,
        test_automation_rule_details_validation, setup_module,
        test_automation_rule_details
):
    """
    Get automation rule details by data segment name
    """
    response = await http_client_test.put(
        f"/automation/rule_details/?automation_id={test_automation_rule_details_validation}&"
        f"page_num=1&page_size=1&data_segment_name={test_automation_rule_details.get('data_segment_name')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get automation rule details."


@pytest.mark.asyncio
async def test_get_automation_rule_details_no_found(
        http_client_test, test_college_validation, college_super_admin_access_token,
        test_automation_rule_details_validation, setup_module
):
    """
    Get automation rule details by id not found
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().automation_activity_collection.delete_many({})
    response = await http_client_test.put(
        f"/automation/rule_details/?automation_id={test_automation_rule_details_validation}"
        f"&page_num=1&page_size=1&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get automation rule details."
    assert response.json()["data"] == []


@pytest.mark.asyncio
async def test_get_automation_rule_details_by_module_type_no_found(
        http_client_test, test_college_validation, college_super_admin_access_token,
        test_automation_rule_details_validation, setup_module,
        test_automation_rule_details
):
    """
    Get automation rule details by id and module type not found
    """
    response = await http_client_test.put(
        f"/automation/rule_details/?automation_id={test_automation_rule_details_validation}"
        f"&page_num=1&page_size=1&module_type={test_automation_rule_details.get('module_name')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get automation rule details."
    assert response.json()["data"] == []


@pytest.mark.asyncio
async def test_get_automation_rule_details_by_data_segment_name_no_found(
        http_client_test, test_college_validation, college_super_admin_access_token,
        test_automation_rule_details_validation, setup_module,
        test_automation_rule_details
):
    """
    Get automation rule details by data segment name and id not found
    """
    response = await http_client_test.put(
        f"/automation/rule_details/?automation_id={test_automation_rule_details_validation}"
        f"&page_num=1&page_size=1&data_segment_name=abc&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get automation rule details."
    assert response.json()["data"] == []
