"""
This file contains test cases of add or update otp template
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_or_update_otp_template_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/templates/otp/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_add_or_update_otp_template_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for add or update template
    """
    response = await http_client_test.put(
        f"/templates/otp/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_add_or_update_otp_template_no_permission(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    No permission for add or update template
    """
    response = await http_client_test.put(
        f"/templates/otp/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_add_or_update_otp_template_required_name(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_template_data
):
    """
    Required template name for add template
    """
    test_template_data.pop("template_name")
    response = await http_client_test.put(
        f"/templates/otp/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data,
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Template name not provided."}


@pytest.mark.asyncio
async def test_add_or_update_otp_template_required_content(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_template_data
):
    """
    Required content for add template
    """
    test_template_data.pop("content")
    response = await http_client_test.put(
        f"/templates/otp/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data,
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Template content not provided."}


@pytest.mark.asyncio
async def test_add_otp_template(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_template_data
):
    """
    Add email template
    """
    response = await http_client_test.put(
        f"/templates/otp/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Template created."


@pytest.mark.asyncio
async def test_update_existing_template_by_id(
        http_client_test,
        test_college_validation,
        setup_module,
        college_super_admin_access_token,
        test_otp_template_validation,
):
    """
    Update existing template by id
    """
    response = await http_client_test.put(
        f"/templates/otp/add_or_update/?college_id={str(test_college_validation.get('_id'))}"
        f"&template_id={str(test_otp_template_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Template data updated."


@pytest.mark.asyncio
async def test_update_existing_template_by_invalid_id(
        http_client_test,
        test_college_validation,
        setup_module,
        college_super_admin_access_token
):
    """
    Invalid template id for update existing template by id
    """
    response = await http_client_test.put(
        f"/templates/otp/add_or_update/?college_id={str(test_college_validation.get('_id'))}"
        f"&template_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert (
            response.json()["detail"]
            == "Template id must be a 12-byte input or a 24-character hex string"
    )


@pytest.mark.asyncio
async def test_update_existing_template_by_wrong_id(
        http_client_test,
        test_college_validation,
        setup_module,
        college_super_admin_access_token
):
    """
    Wrong template id for update existing template by id
    """
    response = await http_client_test.put(
        f"/templates/otp/add_or_update/?college_id={str(test_college_validation.get('_id'))}"
        f"&template_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert (
            response.json()["detail"]
            == "Template not found. Make sure provided template id should be correct."
    )
