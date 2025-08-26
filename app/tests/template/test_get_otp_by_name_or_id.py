"""
This file contains test cases regarding for get otp template details by name or ud
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_otp_template_details_by_name_or_id_not_authenticated(http_client_test, test_college_validation,
                                                                        setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/templates/otp/get_by_name_or_id/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_otp_template_details_by_name_or_id_bad_credentials(http_client_test, test_college_validation,
                                                                      setup_module):
    """
    Bad token for get otp template details by name or id
    """
    response = await http_client_test.get(
        f"/templates/otp/get_by_name_or_id/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_otp_template_details_by_name_or_id_field_required(http_client_test, test_college_validation,
                                                                     access_token, setup_module):
    """
    Field required for get otp template details by name or id
    """
    response = await http_client_test.get(
        f"/templates/otp/get_by_name_or_id/?feature_key={feature_key}", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_get_otp_template_details_by_name_or_id_no_permission(http_client_test, test_college_validation,
                                                                    access_token, test_campaign_data, setup_module
                                                                    ):
    """
    No permission for get otp template details by name or id
    """
    response = await http_client_test.get(
        f"/templates/otp/get_by_name_or_id/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_otp_template_details_by_name_or_id_required_field(
        http_client_test, test_college_validation, college_super_admin_access_token, test_create_data_segment,
        setup_module
):
    """
    Required field for get otp template details by name or id
    """
    response = await http_client_test.get(
        f"/templates/otp/get_by_name_or_id/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "detail": "Template not found. Make sure you provided template_id or template_name is correct."}


@pytest.mark.asyncio
async def test_get_otp_template_details_by_name_or_id_not_found(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Not found for get otp template details by name or id
    """
    response = await http_client_test.get(
        f"/templates/otp/get_by_name_or_id/?college_id={test_college_validation.get('_id')}"
        f"&template_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "detail": "Template not found. Make sure you provided template_id or template_name is correct."}


@pytest.mark.asyncio
async def test_get_otp_template_details_by_name_or_id_invalid_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Invalid id for get otp template details by name or id
    """
    response = await http_client_test.get(
        f"/templates/otp/get_by_name_or_id/?college_id={test_college_validation.get('_id')}"
        f"&template_id=12345678901234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Template id must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_get_otp_template_details_by_name_or_id_invalid_college_id(
        http_client_test, college_super_admin_access_token, setup_module
):
    """
    Get data segment details
    """
    response = await http_client_test.get(
        f"/templates/otp/get_by_name_or_id/?college_id=1234567890"
        f"&template_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_get_otp_template_details_by_name_or_id(
        http_client_test, test_college_validation, college_super_admin_access_token, test_template_data, setup_module
):
    """
    Get data segment details
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().otp_template_collection.delete_many({})
    await http_client_test.put(
        f"/templates/otp/add_or_update/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data
    )
    template_data = await DatabaseConfiguration().otp_template_collection.find_one(
        {'template_name': test_template_data.get('template_name').lower()})
    response = await http_client_test.get(
        f"/templates/otp/get_by_name_or_id/?college_id={test_college_validation.get('_id')}"
        f"&template_id={str(template_data.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get otp template details."
