"""
This file contains test cases related to add student by user
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_student_by_user_not_authenticated(http_client_test, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/admin/add_student/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_add_student_by_user_bad_credentials(http_client_test, setup_module):
    """
    Bad token for add student by user
    """
    response = await http_client_test.post(
        f"/admin/add_student/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_add_student_by_user_required_body(
        http_client_test, access_token, setup_module
):
    """
    Required body for add student by user
    """
    response = await http_client_test.post(
        f"/admin/add_student/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}


@pytest.mark.asyncio
async def test_add_student_by_user_no_permission(
        http_client_test, access_token, setup_module, test_student_data
):
    """
    No permission for add student by user
    """
    response = await http_client_test.post(
        f"/admin/add_student/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json=test_student_data
    )
    assert response.status_code == 401
    assert response.json() == {'detail': 'Not enough permissions'}


@pytest.mark.asyncio
async def test_add_student_by_user(
        http_client_test, college_super_admin_access_token, setup_module, test_student_data
):
    """
    Add student by user
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentsPrimaryDetails.delete_many({})
    response = await http_client_test.post(
        f"/admin/add_student/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=test_student_data
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Account Created Successfully."


@pytest.mark.asyncio
async def test_add_student_by_user_already_exist(
        http_client_test, college_super_admin_access_token, setup_module, test_student_data, test_student_validation
):
    """
    Student already exist when try to add student by user
    """
    response = await http_client_test.post(
        f"/admin/add_student/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, json=test_student_data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "Email already exists."
