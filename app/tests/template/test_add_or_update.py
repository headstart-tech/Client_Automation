"""
This file contains test cases of add or update template
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_or_update_template_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_add_or_update_template_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for add or update template
    """
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_add_or_update_template_no_permission(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    No permission for add or update template
    """
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_add_or_update_template_required_type(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token
):
    """
    Required template type for add template
    """
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Template type not provided."}


@pytest.mark.asyncio
async def test_add_or_update_template_required_name(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_template_data
):
    """
    Required template name for add template
    """
    test_template_data.pop("template_name")
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data,
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Template name not provided."}


@pytest.mark.asyncio
async def test_add_or_update_template_required_sender_email(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_template_data
):
    """
    Required sender email for add template
    """
    test_template_data.pop("sender_email_id")
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data,
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Sender email id of email template not provided."}


@pytest.mark.asyncio
async def test_add_or_update_template_required_content(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_template_data
):
    """
    Required content for add template
    """
    test_template_data.pop("content")
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data,
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Template content not provided."}


@pytest.mark.asyncio
async def test_add_or_update_template_required_subject(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_template_data
):
    """
    Required subject for add template
    """
    test_template_data.pop("subject")
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data,
    )
    assert response.status_code == 422
    assert response.json() == {'detail': 'Subject of email not provided.'}


@pytest.mark.asyncio
async def test_add_whatsapp_template(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_whatsapp_template_data
):
    """
    Add whatsapp template
    """
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_whatsapp_template_data,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Template created."
    assert response.json()["data"]["template_type"] == test_whatsapp_template_data.get("template_type", "").lower()
    assert response.json()["data"]["template_name"] == test_whatsapp_template_data.get("template_name", "").lower()
    assert response.json()["data"]["content"] == test_whatsapp_template_data.get("content")
    assert response.json()["data"]["template_status"] == "enabled"


@pytest.mark.asyncio
async def test_add_email_template(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_template_data
):
    """
    Add email template
    """
    test_template_data.update({"email_type": "default", "email_provider": "default"})
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Template created."
    assert response.json()["data"]["template_type"] == test_template_data.get("template_type", "").lower()
    assert response.json()["data"]["template_name"] == test_template_data.get("template_name", "").lower()
    assert response.json()["data"]["content"] == test_template_data.get("content")
    assert response.json()["data"]["subject"] == test_template_data.get("subject") if test_template_data.get(
        "subject") else None
    assert response.json()["data"]["email_type"] == test_template_data.get("email_type",
                                                                           "").title() if test_template_data.get(
        "email_type") else None
    assert response.json()["data"]["email_provider"] == test_template_data.get("email_provider",
                                                                               "").title() if test_template_data.get(
        "email_provider") else None
    assert response.json()["data"]["template_status"] == "enabled"


@pytest.mark.asyncio
async def test_add_email_template_with_type_provider_and_category(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_template_data
):
    """
    Add email template with type, provider and category
    """
    test_template_data.update({"email_type": "default", "email_provider": "default", "email_category": "welcome"})
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Template created."
    assert response.json()["data"]["template_type"] == test_template_data.get("template_type", "").lower()
    assert response.json()["data"]["template_name"] == test_template_data.get("template_name", "").lower()
    assert response.json()["data"]["content"] == test_template_data.get("content")
    assert response.json()["data"]["subject"] == test_template_data.get("subject")
    assert response.json()["data"]["email_type"] == test_template_data.get("email_type", "").title()
    assert response.json()["data"]["email_provider"] == test_template_data.get("email_provider", "").title()
    assert response.json()["data"]["email_category"] == test_template_data.get(
        "email_category", "")


@pytest.mark.asyncio
async def test_add_template_required_college_id(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_template_data
):
    """
    Required college id for add template
    """
    response = await http_client_test.put(
        f"/templates/add_or_update/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data,
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'


@pytest.mark.asyncio
async def test_add_template_invalid_college_id(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_template_data
):
    """
    Invalid college id for add template
    """
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data,
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_add_template_college_not_found(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_template_data
):
    """
    College not found when try to add template
    """
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data,
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_add_sms_template_required_dlt_content_id(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_template_data
):
    """
    Required dlt content id for add sms template
    """
    test_template_data["template_type"] = "sms"
    if test_template_data.get("dlt_content_id"):
        test_template_data.pop("dlt_content_id")
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "DLT content id not provided."


@pytest.mark.asyncio
async def test_add_sms_template(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_template_data
):
    """
    Add sms template
    """
    test_template_data["template_type"] = "sms"
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Template created."
    assert response.json()["data"]["template_type"] == test_template_data.get("template_type")
    assert response.json()["data"]["template_name"] == test_template_data.get("template_name")
    assert response.json()["data"]["content"] == test_template_data.get("content")
    assert response.json()["data"]["dlt_content_id"] == test_template_data.get("dlt_content_id")
    assert response.json()["data"]["sms_type"] == test_template_data.get("sms_type")


@pytest.mark.asyncio
async def test_update_existing_template_by_id(
        http_client_test,
        test_college_validation,
        setup_module,
        college_super_admin_access_token,
        test_template_validation,
):
    """
    Update existing template by id
    """
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}"
        f"&template_id={str(test_template_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Template data updated."


@pytest.mark.asyncio
async def test_update_existing_template_by_invalid_id(
        http_client_test,
        test_college_validation,
        setup_module,
        college_super_admin_access_token,
        test_template_validation,
):
    """
    Invalid template id for update existing template by id
    """
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}"
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
        college_super_admin_access_token,
        test_template_validation,
):
    """
    Wrong template id for update existing template by id
    """
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}"
        f"&template_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert (
            response.json()["detail"]
            == "Template not found. Make sure provided template id should be correct."
    )


@pytest.mark.asyncio
async def test_add_sms_template_with_category(
        http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_template_data
):
    """
    Add sms template with category
    """
    test_template_data.update({"template_type": "sms", "sms_category": "otp"})
    response = await http_client_test.put(
        f"/templates/add_or_update/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_template_data,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Template created."
    assert response.json()["data"]["template_type"] == test_template_data.get("template_type")
    assert response.json()["data"]["template_name"] == test_template_data.get("template_name")
    assert response.json()["data"]["content"] == test_template_data.get("content")
    assert response.json()["data"]["dlt_content_id"] == test_template_data.get("dlt_content_id")
    assert response.json()["data"]["sms_type"] == test_template_data.get("sms_type")
