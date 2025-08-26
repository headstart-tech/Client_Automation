"""
This file contains test cases of get template details
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_template_not_authenticated(
        http_client_test, test_college_validation,
        test_template_validation, setup_module, test_student_validation):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/templates/get_template_details"
        f"?template_id={str(test_template_validation.get('_id'))}&feature_key={feature_key}"
        f"&template_type=email"
        f"&student_id={str(test_student_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_templates_bad_credentials(
        http_client_test, test_college_validation, setup_module,
        test_template_validation, test_student_validation ):
    """
    Bad token for get all templates
    """
    response = await http_client_test.get(
        f"/templates/get_template_details"
        f"?template_id={str(test_template_validation.get('_id'))}&feature_key={feature_key}"
        f"&template_type=email"
        f"&student_id={str(test_student_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_templates_required_college_id(
        http_client_test, test_college_validation, access_token, setup_module,
        test_template_validation, test_student_validation
):
    """
    Required college id for get all templates
    """
    response = await http_client_test.get(
        f"/templates/get_template_details"
        f"?template_id={str(test_template_validation.get('_id'))}"
        f"&template_type=email&feature_key={feature_key}"
        f"&student_id={str(test_student_validation.get('_id'))}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_get_specific_templates(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_validation,
        test_student_validation
):
    """
    Get template details
    """
    response = await http_client_test.get(
        f"/templates/get_template_details"
        f"?template_id={str(test_template_validation.get('_id'))}&feature_key={feature_key}"
        f"&template_type={test_template_validation.get('template_type')}"
        f"&student_id={str(test_student_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_validation_template_type(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_validation,
        test_student_validation
):
    """
    Test the validation of template type
    """
    response = await http_client_test.get(
        f"/templates/get_template_details"
        f"?template_id={str(test_template_validation.get('_id'))}"
        f"&template_type=mail&feature_key={feature_key}"
        f"&student_id={str(test_student_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "template type is not a valid template"}


@pytest.mark.asyncio
async def test_invalid_template_id(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_validation,
        test_student_validation
):
    """
    Test the invalid of template id
    """
    response = await http_client_test.get(
        f"/templates/get_template_details"
        f"?template_id=65aa7145ecaa9d00a45ec27"
        f"&template_type=email&feature_key={feature_key}"
        f"&student_id={str(test_student_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "Template ID `65aa7145ecaa9d00a45ec27` must be a"
                  " 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_not_found_template_id(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_validation,
        test_student_validation
):
    """
    Test the not found of template details
    """
    response = await http_client_test.get(
        f"/templates/get_template_details"
        f"?template_id=65aa7145ecaa9d00a1234567&feature_key={feature_key}"
        f"&template_type={test_template_validation.get('template_type')}"
        f"&student_id={str(test_student_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Template not found id: 65aa7145ecaa9d00a1234567"}
