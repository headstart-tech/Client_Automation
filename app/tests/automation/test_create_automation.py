"""
This file contains test cases related to create automation API route/endpoint
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_automation_not_authenticated(
        http_client_test, setup_module, test_college_validation):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/automation_beta/create/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_automation_bad_credentials(
        http_client_test, setup_module, test_college_validation):
    """
    Test case -> bad token for create automation
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/automation_beta/create/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_create_automation_field_required(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    Test case -> field required for create automation
    :param http_client_test:
    :param access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/automation_beta/create/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}


@pytest.mark.asyncio
async def test_create_automation_no_permission(
        http_client_test, access_token, test_automation_data, setup_module,
        test_college_validation
):
    """
    Test case -> no permission for create automation
    :param http_client_test:
    :param access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/automation_beta/create/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=test_automation_data,
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_automation(
        http_client_test, college_super_admin_access_token,
        test_automation_data, setup_module, test_college_validation):
    """
    Test case -> for create automation
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    DatabaseConfiguration().rule_collection.delete_many({})
    response = await http_client_test.post(
        f"/automation_beta/create/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_automation_data)
    assert response.status_code == 200
    assert response.json()['message'] == "Automation create successfully"


@pytest.mark.asyncio
async def test_create_automation_required_name(
        http_client_test, college_super_admin_access_token,
        test_automation_data, setup_module, test_college_validation):
    """
    Test case -> required name for create automation
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    test_automation_data.get("automation_details", {}).pop('automation_name')
    response = await http_client_test.post(
        f"/automation_beta/create/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_automation_data, )
    assert response.status_code == 400
    assert response.json()['detail'] == ("Automation Name must "
                                         "be required and valid.")

