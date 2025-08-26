"""
This file contains test cases of get all otp templates
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_all_otp_templates_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(f"/templates/otp/?college_id={str(test_college_validation.get('_id'))}"
                                           f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_all_otp_templates_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get all templates
    """
    response = await http_client_test.post(
        f"/templates/otp/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_all_otp_templates_required_page_number(
        http_client_test, test_college_validation, access_token, setup_module, test_template_validation
):
    """
    Page number for get all templates
    """
    response = await http_client_test.post(
        f"/templates/otp/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Num must be required and valid."}


@pytest.mark.asyncio
async def test_get_all_otp_templates_required_page_size(
        http_client_test, test_college_validation, access_token, setup_module, test_template_validation
):
    """
    Page size for get all templates
    """
    response = await http_client_test.post(
        f"/templates/otp/?college_id={str(test_college_validation.get('_id'))}&page_num=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Size must be required and valid."}


@pytest.mark.asyncio
async def test_get_all_otp_templates(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_validation,
):
    """
    Get all templates
    """
    response = await http_client_test.post(
        f"/templates/otp/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
        f"&page_num=1&page_size=1",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all otp templates."
    assert response.json()["pagination"]["previous"] is None


@pytest.mark.asyncio
async def test_get_all_otp_templates_with_pagination(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_validation,
):
    """
    Get all templates
    """
    response = await http_client_test.post(
        f"/templates/otp/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
        f"&page_num=2&page_size=1",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all otp templates."
    assert response.json()["pagination"]["next"] is None
    assert response.json()["data"] == []
