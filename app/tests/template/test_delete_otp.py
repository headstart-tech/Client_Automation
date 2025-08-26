"""
This file contains test cases of delete otp template by id
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_otp_template_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.delete(
        f"/templates/otp/delete/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_otp_template_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for delete template by id
    """
    response = await http_client_test.delete(
        f"/templates/otp/delete/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_delete_otp_template_field_required(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Field required for delete template by id
    """
    response = await http_client_test.delete(
        f"/templates/otp/delete/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Template Id must be required and valid."}


@pytest.mark.asyncio
async def test_delete_otp_template_no_permission(
        http_client_test, test_college_validation, access_token, setup_module, test_template_validation
):
    """
    No permission for delete template by id
    """
    response = await http_client_test.delete(
        f"/templates/otp/delete/?template_id={str(test_template_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_delete_otp_template_by_id(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_otp_template_validation,
):
    """
    Delete template by id
    """
    response = await http_client_test.delete(
        f"/templates/otp/delete/?template_id={str(test_otp_template_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Template deleted."}


@pytest.mark.asyncio
async def test_delete_otp_template_by_invalid_id(
        http_client_test,
        test_college_validation,
        setup_module,
        college_super_admin_access_token
):
    """
    Invalid template id for delete template by id
    """
    response = await http_client_test.delete(
        f"/templates/otp/delete/?template_id=1234567890&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert (
            response.json()["detail"]
            == "Template id must be a 12-byte input or a 24-character hex string"
    )


@pytest.mark.asyncio
async def test_delete_otp_template_by_wrong_id(
        http_client_test,
        test_college_validation,
        setup_module,
        college_super_admin_access_token
):
    """
    Wrong template id for delete template by id
    """
    response = await http_client_test.delete(
        f"/templates/otp/delete/?template_id=123456789012345678901234"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert (
            response.json()["detail"]
            == "Template not found. Make sure provided template id should be correct."
    )
