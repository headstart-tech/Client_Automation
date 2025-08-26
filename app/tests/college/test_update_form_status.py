"""
This file contains test cases related to update college status
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_college_status_not_authorized(http_client_test, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(f"/college/update_status/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_college_status_bad_credentials(http_client_test, setup_module):
    """
    Bad token for update college status
    """
    response = await http_client_test.put(
        f"/college/update_status/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_update_college_status_required_college_id(
        http_client_test, college_super_admin_access_token, setup_module
):
    """
    Required college id for update college status
    """
    response = await http_client_test.put(
        f"/college/update_status/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_update_college_status_required_status(
        http_client_test, test_college_validation, client_manager_access_token, setup_module
):
    """
    Required status for update college status
    """
    response = await http_client_test.put(
        "/college/update_status/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {client_manager_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Status must be required and valid."}


@pytest.mark.asyncio
async def test_update_college_status_no_permission(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    No permission for update college status
    """
    response = await http_client_test.put(
        "/college/update_status/"
        f"?college_id={str(test_college_validation.get('_id'))}&status=pending&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_update_college_status_wrong(
        http_client_test, test_college_validation, client_manager_access_token, setup_module
):
    """
    Update college status
    """
    response = await http_client_test.put(
        "/college/update_status/"
        f"?college_id={str(test_college_validation.get('_id'))}&status=test&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {client_manager_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Status must be required and valid."}


@pytest.mark.asyncio
async def test_update_college_status(
        http_client_test,
        client_manager_access_token,
        setup_module,
        test_college_validation,
):
    """
    Update college status
    """
    response = await http_client_test.put(
        "/college/update_status/"
        f"?college_id={str(test_college_validation.get('_id'))}&status=pending&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {client_manager_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Status updated."


@pytest.mark.asyncio
async def test_update_college_status_college_not_exist(
        http_client_test,
        client_manager_access_token,
        setup_module,
        test_college_validation,
):
    """
    College not exist for update college status
    """
    response = await http_client_test.put(
        "/college/update_status/"
        f"?college_id=123456789012345678901234&status=pending&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {client_manager_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "College not found."}


@pytest.mark.asyncio
async def test_update_college_status_wrong_college_id(
        http_client_test,
        client_manager_access_token,
        setup_module,
        test_college_validation,
):
    """
    Wrong college id for update college status
    """
    response = await http_client_test.put(
        f"/college/update_status/?college_id=12345678901234567890&status=pending&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {client_manager_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input or a 24-character hex string"}
