"""
This file contains test cases related to API route/endpoint for remove students by source name
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_remove_students_by_source_name_not_authenticated(
        http_client_test, test_college_validation, setup_module
):
    """
    Not Authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/admin/remove_students_by_source_name/?source_name=google&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_remove_students_by_source_name_no_permission(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    User has no permission to delete the records
    """
    response = await http_client_test.get(
        f"/admin/remove_students_by_source_name/?source_name=google&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_remove_students_by_source_name_wrong_source(
        http_client_test, test_college_validation, super_admin_access_token, setup_module
):
    """
    Source name not exists for remove students
    """
    response = await http_client_test.get(
        f"/admin/remove_students_by_source_name/?source_name=g&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json() == {'detail': ' No Data Found in with Source = g '}


@pytest.mark.asyncio
async def test_remove_students_by_source_name_right_input(
        http_client_test, test_college_validation, super_admin_access_token, setup_module, test_student_validation,
        test_source_data
):
    """
    If user is authenticated, and source name is right,
    based on source name records will be deleted
    """
    response = await http_client_test.get(
        f"/admin/remove_students_by_source_name/"
        f"?source_name={test_source_data.get('primary_source', {}).get('utm_source')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Deleted student records whose utm_source"
                   f" named {test_source_data.get('primary_source', {}).get('utm_source')}"
    }
