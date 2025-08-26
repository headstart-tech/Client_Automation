"""
This file contains test cases of get all tag names by template type
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_all_tag_names_by_template_type_not_authenticated(
        http_client_test, test_college_validation, setup_module
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(f"/templates/tags/?college_id={str(test_college_validation.get('_id'))}"
                                          f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_all_tag_names_by_template_type_bad_credentials(
        http_client_test, test_college_validation, setup_module
):
    """
    Bad token for get all tag names by template type
    """
    response = await http_client_test.get(
        f"/templates/tags/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_all_tag_names_by_template_type_required_type(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Required template type for get all tag names by template type
    """
    response = await http_client_test.get(
        f"/templates/tags/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Template Type must be required and valid."}


@pytest.mark.asyncio
async def test_get_all_tag_names_by_template_type_no_permission(
        http_client_test, test_college_validation, access_token, setup_module, test_template_validation
):
    """
    No permission for get all tag names by template type
    """
    response = await http_client_test.get(
        f"/templates/tags/?college_id={str(test_college_validation.get('_id'))}&template_type=test"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_all_tag_names_by_template_type(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_validation,
):
    """
    Get all tag names by template type
    """
    response = await http_client_test.get(
        f"/templates/tags/?college_id={str(test_college_validation.get('_id'))}&template_type=email&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all tag names."


@pytest.mark.asyncio
async def test_get_all_tag_names_by_template_type_not_exist(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Get all tag names by template type
    """
    response = await http_client_test.get(
        f"/templates/tags/?college_id={str(test_college_validation.get('_id'))}&template_type=sms&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all tag names."


@pytest.mark.asyncio
async def test_get_all_tag_names_by_invalid_template_type(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Invalid template type for get all tag names by template type
    """
    response = await http_client_test.get(
        f"/templates/tags/?college_id={str(test_college_validation.get('_id'))}&template_type=test&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "Template type should be any of the following: email, sms and whatsapp"
    )
