"""
This file contains test cases of get all templates
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_all_templates_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(f"/templates/?college_id={str(test_college_validation.get('_id'))}"
                                           f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_all_templates_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get all templates
    """
    response = await http_client_test.post(
        f"/templates/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_all_templates_required_college_id(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required college id for get all templates
    """
    response = await http_client_test.post(
        f"/templates/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_get_all_templates_required_page_number(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required page number for get all templates
    """
    response = await http_client_test.post(
        f"/templates/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Num must be required and valid."}


@pytest.mark.asyncio
async def test_get_all_templates_required_page_size(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required page size for get all templates
    """
    response = await http_client_test.post(
        f"/templates/?college_id={str(test_college_validation.get('_id'))}&page_num=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Size must be required and valid."}


@pytest.mark.asyncio
async def test_get_all_email_templates(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_data
):
    """
    Get all email templates
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().template_collection.delete_many({})
    test_template_data.update({"email_type": "default", "email_provider": "default"})
    await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data
    )
    response = await http_client_test.post(
        f"/templates/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
        f"&page_num=1&page_size=1&email_templates=true",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all templates."
    assert response.json()["pagination"]["previous"] is None
    assert response.json()["pagination"]["next"] is None
    assert response.json()["data"] is not None


@pytest.mark.asyncio
async def test_get_all_sms_templates(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_data
):
    """
    Get all sms templates
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().template_collection.delete_many({})
    test_template_data.update({"template_type": "sms"})
    await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data
    )
    response = await http_client_test.post(
        f"/templates/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
        f"&page_num=1&page_size=1&sms_templates=true",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all templates."
    assert response.json()["pagination"]["previous"] is None
    assert response.json()["pagination"]["next"] is None
    assert response.json()["data"] is not None


@pytest.mark.asyncio
async def test_get_all_whatsapp_templates(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_whatsapp_template_data
):
    """
    Get all whatsapp templates
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().template_collection.delete_many({})
    await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_whatsapp_template_data
    )
    response = await http_client_test.post(
        f"/templates/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}&page_num=1"
        f"&page_size=1&whatsapp_templates=true",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all templates."
    assert response.json()["pagination"]["previous"] is None
    assert response.json()["pagination"]["next"] is None
    assert response.json()["data"] is not None
    assert response.json()["count"] == 1
    if response.json()["data"]:
        columns = ['template_id', 'template_type', 'template_name', 'content', 'added_tags',
                   "last_modified_timeline", 'created_by', 'created_by_user_name', 'created_on', 'is_published',
                   "template_status", 'dlt_content_id', 'subject', 'email_type', 'email_provider', 'email_category',
                   'sms_type']
        for column in columns:
            assert column in response.json()["data"][0]


@pytest.mark.asyncio
async def test_get_all_draft_email_templates(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_data
):
    """
    Get all draft email templates
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().template_collection.delete_many({})
    test_template_data.update({"is_published": False, "email_type": "default", "email_provider": "default"})
    await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data
    )
    response = await http_client_test.post(
        f"/templates/?college_id={str(test_college_validation.get('_id'))}&page_num=1&page_size=1"
        f"&draft_email_templates=true&own_templates=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all templates."
    assert response.json()["pagination"]["previous"] is None
    assert response.json()["pagination"]["next"] is None
    assert response.json()["data"] is not None
    assert response.json()["total"] == 1
    assert response.json()["count"] == 1
    if response.json()["data"]:
        columns = ['template_id', 'template_type', 'template_name', 'content', 'added_tags',
                   "last_modified_timeline", 'created_by', 'created_by_user_name', 'created_on', 'is_published',
                   "template_status", 'dlt_content_id', 'subject', 'email_type', 'email_provider', 'email_category',
                   'sms_type']
        for column in columns:
            assert column in response.json()["data"][0]


@pytest.mark.asyncio
async def test_get_all_draft_sms_templates(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_data
):
    """
    Get all draft sms templates
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().template_collection.delete_many({})
    test_template_data.update({"template_type": "sms", "is_published": False})
    await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data
    )
    response = await http_client_test.post(
        f"/templates/?college_id={str(test_college_validation.get('_id'))}&page_num=1"
        f"&page_size=1&draft_sms_templates=true&own_templates=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all templates."
    assert response.json()["pagination"]["previous"] is None
    assert response.json()["pagination"]["next"] is None
    assert response.json()["data"] is not None


@pytest.mark.asyncio
async def test_get_all_draft_whatsapp_templates(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_whatsapp_template_data
):
    """
    Get all draft whatsapp templates
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().template_collection.delete_many({})
    test_whatsapp_template_data.update({"is_published": False})
    await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_whatsapp_template_data
    )
    response = await http_client_test.post(
        f"/templates/?college_id={str(test_college_validation.get('_id'))}&page_num=1&page_size=1"
        f"&draft_whatsapp_templates=true&own_templates=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all templates."
    assert response.json()["pagination"]["previous"] is None
    assert response.json()["pagination"]["next"] is None
    assert response.json()["data"] is not None
    assert response.json()["total"] == 1
    assert response.json()["count"] == 1
    if response.json()["data"]:
        columns = ['template_id', 'template_type', 'template_name', 'content', 'added_tags',
                   "last_modified_timeline", 'created_by', 'created_by_user_name', 'created_on', 'is_published',
                   "template_status", 'dlt_content_id', 'subject', 'email_type', 'email_provider', 'email_category',
                   'sms_type']
        for column in columns:
            assert column in response.json()["data"][0]


@pytest.mark.asyncio
async def test_get_all_templates_invalid_college_id(
        http_client_test,
        college_super_admin_access_token,
        setup_module,
        test_template_data
):
    """
    Invalid college id for get all templates
    """
    response = await http_client_test.post(
        f"/templates/?college_id=1234567890&page_num=1&page_size=1&email_templates=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_get_all_templates_college_not_found(
        http_client_test,
        college_super_admin_access_token,
        setup_module,
        test_template_data
):
    """
    College not found when try to get all templates
    """
    response = await http_client_test.post(
        f"/templates/?college_id=123456789012345678901234&page_num=1&page_size=1&email_templates=true"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_get_all_templates_with_pagination(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_data
):
    """
    Get all templates
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().template_collection.delete_many({})
    test_template_data.update({"email_type": "default", "email_provider": "default"})
    await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data
    )
    response = await http_client_test.post(
        f"/templates/?college_id={str(test_college_validation.get('_id'))}&page_num=2&page_size=1"
        f"&email_templates=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all templates."
    assert response.json()["pagination"]["next"] is None
    assert response.json()["data"] == []
    assert response.json()["pagination"]["previous"] is not None


@pytest.mark.asyncio
async def test_get_email_all_templates_with_category(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module, test_template_data
):
    """
    Get all templates with category
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().template_collection.delete_many({})
    test_template_data.update({"email_type": "default", "email_provider": "default", "email_category": "welcome"})
    await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data
    )
    response = await http_client_test.post(
        f"/templates/?college_id={str(test_college_validation.get('_id'))}&page_num=1&page_size=1"
        f"&email_templates=true&email_category=welcome&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all templates."
    assert response.json()["pagination"]["previous"] is None
    assert response.json()["data"] is not None
    assert response.json()["pagination"]["next"] is None


@pytest.mark.asyncio
async def test_get_all_templates_no_found(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module
):
    """
    Template not found when try to get templates
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().template_collection.delete_many({})
    response = await http_client_test.post(
        f"/templates/?college_id={str(test_college_validation.get('_id'))}&page_num=1&page_size=1"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all templates."
    assert response.json()["pagination"]["previous"] is None
    assert response.json()["pagination"]["next"] is None
    assert response.json()["data"] == []
    assert response.json()["total"] == 0
    assert response.json()["count"] == 1


@pytest.mark.asyncio
async def test_get_all_templates_with_tag_names(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module, test_tag_list_validation
):
    """
    Get all templates with tag names
    """
    response = await http_client_test.post(
        f"/templates/?college_id={str(test_college_validation.get('_id'))}&page_num=1&page_size=1"
        f"&email_templates=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[test_tag_list_validation.get("tag_name", "")],
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all templates."
    assert response.json()["pagination"]["previous"] is None
    assert response.json()["data"] is not None
    assert response.json()["pagination"]["next"] is None
    assert response.json()["count"] == 1
    if response.json()["data"]:
        columns = ['template_id', 'template_type', 'template_name', 'content', 'added_tags',
                   "last_modified_timeline", 'created_by', 'created_by_user_name', 'created_on', 'is_published',
                   "template_status", 'dlt_content_id', 'subject', 'email_type', 'email_provider', 'email_category',
                   'sms_type']
        for column in columns:
            assert column in response.json()["data"][0]


@pytest.mark.asyncio
async def test_get_all_templates_with_tag_names_no_found(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module, test_template_data
):
    """
    Get all templates with tag names
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().tag_list_collection.delete_many({})
    response = await http_client_test.post(
        f"/templates/?college_id={str(test_college_validation.get('_id'))}&page_num=1&page_size=1"
        f"&email_templates=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=["test"],
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all templates."
    assert response.json()["pagination"]["previous"] is None
    assert response.json()["data"] == []
    assert response.json()["pagination"]["next"] is None
    assert response.json()["total"] == 0
    assert response.json()["count"] == 1


@pytest.mark.asyncio
async def test_get_sms_all_templates_with_category(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module, test_template_data
):
    """
    Get all sms templates with category
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().template_collection.delete_many({})
    test_template_data.update({"template_type": "sms", "sms_category": "otp"})
    await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data
    )
    response = await http_client_test.post(
        f"/templates/?college_id={str(test_college_validation.get('_id'))}&page_num=1&page_size=1"
        f"&sms_templates=true&sms_category=otp&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get all templates."
    assert response.json()["pagination"]["previous"] is None
    assert response.json()["data"] is not None
    assert response.json()["pagination"]["next"] is None


@pytest.mark.asyncio
async def test_get_sms_all_templates_with_invalid_category(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module, test_template_data
):
    """
    Tey to get all sms templates with invalid category
    """
    response = await http_client_test.post(
        f"/templates/?college_id={str(test_college_validation.get('_id'))}&page_num=1&page_size=1"
        f"&sms_templates=true&sms_category=test&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Sms Category must be required and valid."
