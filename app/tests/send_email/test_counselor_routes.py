"""
This file contains test cases for send emails to multiple leads
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_send_email_to_multiple_lead_not_authenticated(
    http_client_test, setup_module
):
    """
    Test case -> not authenticated for send multiple email
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(f"/counselor/send_email_to_multiple_lead/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_send_email_to_multiple_lead_bad_credentials(
    http_client_test, setup_module
):
    """
    Test case -> bad token for send multiple email
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/counselor/send_email_to_multiple_lead/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_send_email_to_multiple_lead_required_subject(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Test case -> subject required for send multiple email
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/counselor/send_email_to_multiple_lead/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Subject must be required and valid."


@pytest.mark.asyncio
async def test_send_email_to_multiple_lead_required_payload(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Test case -> payload required for send multiple email
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/counselor/send_email_to_multiple_lead/?subject=test&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Payload must be required and valid."


@pytest.mark.asyncio
async def test_send_email_to_multiple_lead_required_template(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Test case -> template required for send multiple email
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/counselor/send_email_to_multiple_lead/?subject=test&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"payload": {"email_id": ["string"]}},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Template must be required and valid."


@pytest.mark.asyncio
async def test_send_email_to_multiple_lead(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Test case -> for send multiple email
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/counselor/send_email_to_multiple_lead/?subject=test&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"payload": {"email_id": ["test@example.com"]}, "template": "string"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "email sent"
