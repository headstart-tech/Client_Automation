"""
This file contains test cases of activate email template API
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_activate_email_template_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/templates/set_active/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_activate_email_template_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for activate email template based on category
    """
    response = await http_client_test.put(
        f"/templates/set_active/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_activate_email_template_required_body(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required body for activate email template based on category
    """
    response = await http_client_test.put(
        f"/templates/set_active/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}


@pytest.mark.asyncio
async def test_activate_email_template_no_permission(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    No permission for activate email template based on category
    """
    response = await http_client_test.put(
        f"/templates/set_active/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json={"template_id": "12345"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_activate_email_template_required_template_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Required template id for activate email template based on category
    """
    response = await http_client_test.put(
        f"/templates/set_active/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json={}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Template Id must be required and valid."}


@pytest.mark.asyncio
async def test_activate_email_template_required_college_id(http_client_test, college_super_admin_access_token,
                                                           setup_module):
    """
    Required college id for activate email template based on category
    """
    response = await http_client_test.put(
        f"/templates/set_active/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"template_id": "123456789012345678901234", "email_category": "welcome"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'


@pytest.mark.asyncio
async def test_activate_email_template_invalid_college_id(http_client_test, test_college_validation,
                                                          college_super_admin_access_token, setup_module):
    """
    Invalid college id for activate email template based on category
    """
    response = await http_client_test.put(
        f"/templates/set_active/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"template_id": "123456789012345678901234"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_activate_email_template_college_not_found(http_client_test, test_college_validation,
                                                         college_super_admin_access_token, setup_module):
    """
    College not found for activate email template based on category
    """
    response = await http_client_test.post(
        f"/admin/all_paid_applications/?college_id=123456789012345678901234&page_num=1&page_size=1"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_activate_email_template_invalid_template_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Invalid template id when try to activate email template based on category
    """
    response = await http_client_test.put(
        f"/templates/set_active/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"template_id": "12345", "email_category": "welcome"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Template id must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_activate_email_template_template_not_found(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Test activating a template that does not exist in the database
    """
    response = await http_client_test.put(
        f"/templates/set_active/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"template_id": "123456789012345678901234", "email_category": "welcome"}
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Template not found."}


@pytest.mark.asyncio
async def test_activate_email_template(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
        test_template_validation
):
    """
    Activate email template based on category
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().template_collection.update_one({"_id": test_template_validation.get("_id")}, {
        "$unset": {"active": True}})
    await DatabaseConfiguration().template_collection.update_one({"_id": test_template_validation.get("_id")}, {
        "$set": {"email_type": "default", "email_provider": "default", "email_category": "welcome"}})
    response = await http_client_test.put(
        f"/templates/set_active/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"template_id": str(test_template_validation.get("_id")), "email_category": "welcome"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Template activated."}


@pytest.mark.asyncio
async def test_activate_email_template_already_activate(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
        test_template_validation
):
    """
    Test activating a template that is already active
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().template_collection.update_one({"_id": test_template_validation.get("_id")}, {
        "$set": {"email_type": "default", "email_provider": "default", "email_category": "welcome", 'active': True}})
    response = await http_client_test.put(
        f"/templates/set_active/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"template_id": str(test_template_validation.get("_id")), "email_category": "welcome"}
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Template is already activated."}


@pytest.mark.asyncio
async def test_activate_template_with_active_email_template_in_same_category(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
        test_template_validation, test_template_validation_2
):
    """
    Try to activate an email template with another template already active in the same category
    """
    from app.database.configuration import DatabaseConfiguration
    # Set the first template to be active
    await DatabaseConfiguration().template_collection.update_one({"_id": test_template_validation.get("_id")}, {
        "$set": {"email_type": "default", "email_provider": "default", "email_category": "welcome", 'active': True}})
    # Set the second template in the same category as the first template
    await DatabaseConfiguration().template_collection.update_one({"_id": test_template_validation_2.get("_id")}, {
        "$set": {"email_type": "default", "email_provider": "default", "email_category": "welcome"}})
    # Try to activate the second template while the first template is still active
    response = await http_client_test.put(
        f"/templates/set_active/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"template_id": str(test_template_validation_2.get("_id")), "email_category": "welcome"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Template activated."}
    # Check that the first template is no longer active
    assert (await DatabaseConfiguration().template_collection.find_one(
        {"_id": test_template_validation.get("_id"), "active": True})) is None
    # Check that the second template is now active
    assert (await DatabaseConfiguration().template_collection.find_one(
        {"_id": test_template_validation_2.get("_id"), "active": True})) is not None


@pytest.mark.asyncio
async def test_activate_email_template_with_default_category(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
        test_template_data
):
    """
    Try to activate email template based on default category
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().template_collection.delete_many({})
    await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data,
    )
    template = await DatabaseConfiguration().template_collection.find_one({})
    response = await http_client_test.put(
        f"/templates/set_active/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"template_id": str(template.get("_id")), "email_category": "welcome"}
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Enter a valid email category."}
