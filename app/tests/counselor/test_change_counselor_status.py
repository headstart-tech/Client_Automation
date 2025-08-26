"""
This file contain test cases for change counselor status
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_change_counselor_status_not_authenticate(http_client_test, setup_module, test_counselor_validation):
    """
    Not authenticate for change counselor status
    """
    response = await http_client_test.post(
        f"/counselor/change_status?counselor_id={str(test_counselor_validation.get('_id'))}"
        f"&status=true&feature_key={feature_key}",
        headers={"Authorization": "wrong Bearer"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_change_counselor_status_wrong_counselor_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Wrong counselor id for change counselor status
    :param http_client_test:
    :param setup_module:
    :return:
    """
    response = await http_client_test.post(
        f"/counselor/change_status?counselor_id=1234567890123456789012&status=true"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "counselor not found"


@pytest.mark.asyncio
async def test_change_counselor_status_invalid_counselor_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Invalid counselor id for change counselor status
    """
    response = await http_client_test.post(
        f"/counselor/change_status?counselor_id=123456789012345678901234&status=true"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "counselor not found"


@pytest.mark.asyncio
async def test_change_counselor_status(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Change counselor status
    """
    response = await http_client_test.post(
        f"/counselor/change_status?counselor_id=62bfd13a5ce8a398ad101bd7&status=true"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "status update successfully"
