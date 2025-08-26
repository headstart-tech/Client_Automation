"""
This file contains test cases of delete student by user_name or email
"""
import json

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_user_by_email(
        http_client_test, test_college_validation, super_admin_access_token, setup_module, test_student_validation
):
    """
    Delete the student record if email id matches with the student record
    """
    response = await http_client_test.request(
        "DELETE",
        f"/admin/delete_student_by_email_id"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {super_admin_access_token}",
            "Content-Type": "application/json"
        },
        content=json.dumps([test_student_validation.get('user_name')]).encode('utf-8')
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Records deleted successfully"}


@pytest.mark.asyncio
async def test_delete_email_wrong_token(
        http_client_test, test_college_validation, access_token, setup_module, test_student_validation):
    """
    If user logged in with wrong token
    """
    response = await http_client_test.request(
        "DELETE",
        f"/admin/delete_student_by_email_id"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        content=json.dumps([test_student_validation.get('user_name')]).encode('utf-8')
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Not enough permissions"}


@pytest.mark.asyncio
async def test_read_email_not_token(http_client_test, test_college_validation, setup_module, test_student_validation):
    """
    If user logged in without token
    """
    response = await http_client_test.request(
        "DELETE",
        f"/admin/delete_student_by_email_id"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        content=json.dumps([test_student_validation.get('user_name')]).encode('utf-8')
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
