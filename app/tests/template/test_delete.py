"""
This file contains test cases of delete template by id
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_template_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.delete(f"/templates/delete/?college_id={str(test_college_validation.get('_id'))}"
                                             f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_template_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for delete template by id
    """
    response = await http_client_test.delete(
        f"/templates/delete/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_delete_template_field_required(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Field required for delete template by id
    """
    response = await http_client_test.delete(
        f"/templates/delete/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Template Id must be required and valid."}


@pytest.mark.asyncio
async def test_delete_template_no_permission(
        http_client_test, test_college_validation, access_token, setup_module, test_template_validation
):
    """
    No permission for delete template by id
    """
    response = await http_client_test.delete(
        f"/templates/delete/?template_id={str(test_template_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_delete_template_by_id(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_data
):
    """
    Delete template by id
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().template_collection.delete_many({})
    await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data
    )
    template = await DatabaseConfiguration().template_collection.find_one({})
    response = await http_client_test.delete(
        f"/templates/delete/?template_id={str(template.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Template deleted."}


@pytest.mark.asyncio
async def test_delete_active_template_by_id(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_validation
):
    """
    Try to delete activate template by id
    """

    from app.database.configuration import DatabaseConfiguration
    # Set the first template to be active
    await DatabaseConfiguration().template_collection.update_one({"_id": test_template_validation.get("_id")}, {
        "$set": {"email_type": "default", "email_provider": "default", "email_category": "welcome", 'active': True}})
    response = await http_client_test.delete(
        f"/templates/delete/?template_id={str(test_template_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Template is activated. For delete template, need to deactivate it."}


@pytest.mark.asyncio
async def test_delete_template_by_invalid_id(
        http_client_test,
        test_college_validation,
        setup_module,
        college_super_admin_access_token,
        test_template_validation,
):
    """
    Invalid template id for delete template by id
    """
    response = await http_client_test.delete(
        f"/templates/delete/?template_id=1234567890&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "Template id must be a 12-byte input or a 24-character hex string"
    )


@pytest.mark.asyncio
async def test_delete_template_by_wrong_id(
        http_client_test,
        test_college_validation,
        setup_module,
        college_super_admin_access_token,
        test_template_validation,
):
    """
    Wrong template id for delete template by id
    """
    response = await http_client_test.delete(
        f"/templates/delete/?template_id=123456789012345678901234"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Template not found. Make sure provided template id should be correct."
    )
