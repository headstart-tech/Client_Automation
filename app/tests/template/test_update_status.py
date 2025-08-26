"""
This file contains test cases of update status of template by id
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_status_of_template_not_authenticated(
        http_client_test, test_college_validation, setup_module
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/templates/update_status/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_status_of_template_bad_credentials(
        http_client_test, test_college_validation, setup_module
):
    """
    Bad token for update status of template by id
    """
    response = await http_client_test.put(
        f"/templates/update_status/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_update_status_of_template_required_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Required id for update status of template by id
    """
    response = await http_client_test.put(
        f"/templates/update_status/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Template Id must be required and valid."}


@pytest.mark.asyncio
async def test_update_status_of_template_required_status(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_validation,
):
    """
    Required status for update status of template by id
    """
    response = await http_client_test.put(
        f"/templates/update_status/?college_id={str(test_college_validation.get('_id'))}"
        f"&template_id={str(test_template_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Template Status must be required and valid."}


@pytest.mark.asyncio
async def test_update_status_of_template_no_permission(
        http_client_test, test_college_validation, access_token, setup_module, test_template_validation
):
    """
    No permission for update status of template by id
    """
    response = await http_client_test.put(
        f"/templates/update_status/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}&template_id={str(test_template_validation.get('_id'))}&template_status=test",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_update_status_of_template_wrong_status(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_validation,
):
    """
    Wrong status for update status of template by id
    """
    response = await http_client_test.put(
        f"/templates/update_status/?college_id={str(test_college_validation.get('_id'))}"
        f"&template_id={str(test_template_validation.get('_id'))}&template_status=testV"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Template status should be any of the following: enabled and disabled."
    }


@pytest.mark.asyncio
async def test_update_status_of_template_by_id(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module,
        test_template_validation,
):
    """
    Update status of template by id
    """
    response = await http_client_test.put(
        f"/templates/update_status/?college_id={str(test_college_validation.get('_id'))}"
        f"&template_id={str(test_template_validation.get('_id'))}&template_status=disabled"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Template status updated."}


@pytest.mark.asyncio
async def test_update_status_template_by_invalid_id(
        http_client_test,
        test_college_validation,
        setup_module,
        college_super_admin_access_token,
        test_template_validation,
):
    """
    Invalid template id for update_status template by id
    """
    response = await http_client_test.put(
        f"/templates/update_status/?college_id={str(test_college_validation.get('_id'))}"
        f"&template_id=1234567890&template_status=disabled&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "Template id must be a 12-byte input or a 24-character hex string"
    )


@pytest.mark.asyncio
async def test_update_status_template_by_wrong_id(
        http_client_test,
        test_college_validation,
        setup_module,
        college_super_admin_access_token,
        test_template_validation,
):
    """
    Wrong template id for update_status template by id
    """
    response = await http_client_test.put(
        f"/templates/update_status/?college_id={str(test_college_validation.get('_id'))}"
        f"&template_id=123456789012345678901234&template_status=disabled&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Template not found. Make sure provided template id should be correct."
    )
