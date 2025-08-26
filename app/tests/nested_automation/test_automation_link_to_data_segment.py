"""
This file contains test cases related to automation_link_to_data_segment
 API route/endpoint
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_link_automation_not_authenticated(
        http_client_test,
        test_college_validation,
        test_automation_validation,
        setup_module,
        test_create_data_segment_helper):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/nested_automation/automation_link_to_data_segment"
        f"?automation_id={str(test_automation_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        json=[str(test_create_data_segment_helper.get("_id"))])
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_link_automation_bad_credentials(
        http_client_test,
        test_automation_validation,
        test_college_validation,
        test_create_data_segment_helper,
        setup_module):
    """
    Test case -> bad token for data segment link to automation
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/nested_automation/automation_link_to_data_segment"
        f"?automation_id={str(test_automation_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        json=[str(test_create_data_segment_helper.get("_id"))],
        headers={"Authorization": f"Bearer token"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_link_automation_field_required(
        http_client_test, access_token, setup_module,
        test_automation_validation, test_college_validation,
        test_create_data_segment_helper
):
    """
    Test case -> field required for data segment link to automation
    :param http_client_test:
    :param access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/nested_automation/automation_link_to_data_segment"
        f"?automation_id={str(test_automation_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}


@pytest.mark.asyncio
async def test_link_automation_no_permission(
        http_client_test, access_token, setup_module,
        test_automation_validation, test_college_validation,
        test_create_data_segment_helper
):
    """
    Test case -> no permission for data segment link to automation
    :param http_client_test:
    :param access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/nested_automation/automation_link_to_data_segment"
        f"?automation_id={str(test_automation_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        json=[str(test_create_data_segment_helper.get("_id"))],
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_automation(
        http_client_test, college_super_admin_access_token, setup_module,
        test_automation_validation, test_college_validation,
        test_create_data_segment_helper):
    """
    Test case -> for data segment link to automation
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/nested_automation/automation_link_to_data_segment"
        f"?automation_id={str(test_automation_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        json=[str(test_create_data_segment_helper.get("_id"))],
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == (f"Data segment assign to the"
                                          f" automation successfully")


@pytest.mark.asyncio
async def test_link_automation_invalid_automation_id(
        http_client_test, college_super_admin_access_token, setup_module,
        test_automation_validation, test_college_validation,
        test_create_data_segment_helper):
    """
    Test case -> for data segment link to automation
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/nested_automation/automation_link_to_data_segment"
        f"?automation_id={str(test_automation_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        json=["1234857689753"],
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == ("Data Segment id `1234857689753`"
                                         " must be a 12-byte input or a"
                                         " 24-character hex string")


@pytest.mark.asyncio
async def test_link_automation_invalid_data_segment_id(
        http_client_test, college_super_admin_access_token, setup_module,
        test_automation_validation, test_college_validation,
        test_create_data_segment_helper):
    """
    Test case -> for data segment link to automation
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/nested_automation/automation_link_to_data_segment"
        f"?automation_id=76296192456425"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        json=[str(test_create_data_segment_helper.get("_id"))],
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == ("Automation id `76296192456425`"
                                         " must be a 12-byte input or a"
                                         " 24-character hex string")
