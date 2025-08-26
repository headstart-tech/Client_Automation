"""
This file contains test cases related to API route/endpoint which useful for
delete tag from student.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_secondary_tertiary_details_not_authenticated(
        http_client_test, test_college_validation, access_token,
        setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(f"/lead/add_secondary_tertiary_email_phone/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_add_secondary_tertiary_details_bad_token(
        http_client_test, test_college_validation, access_token,
        setup_module):
    """
       Bad token to add secondary tertiary details
    """
    response = await http_client_test.get(
        f"/lead/add_secondary_tertiary_email_phone/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_add_secondary_tertiary_details_required_collleeg_id(
        http_client_test, test_college_validation,
        test_student_validation, college_super_admin_access_token,
        setup_module):
    """
    Required college id to add secondary tertiary details.
    """
    response = await http_client_test.get(
        f"/lead/add_secondary_tertiary_email_phone/?student_id={str(test_student_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json() == \
           {'detail': "College Id must be required and valid."}

@pytest.mark.asyncio
async def test_add_secondary_tertiary_details_invalid_college_id(http_client_test, test_college_validation,
                                                                 college_super_admin_access_token,
                                                                 test_student_validation):
    """
    Invalid college id to add secondary tertiary details
    """
    response = await http_client_test.get(f"/lead/add_secondary_tertiary_email_phone/?college_id=1234567890"
                                          f"&student_id={str(test_student_validation.get('_id'))}&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

@pytest.mark.asyncio
async def test_add_secondary_tertiary_details_college_not_found(http_client_test, test_college_validation,
                                                                college_super_admin_access_token,
                                                                test_student_validation
                                                                ):
    """
    college not found to add secondary tertiary details
    """
    response = await http_client_test.get(f"/lead/add_secondary_tertiary_email_phone/?"
                                          f"college_id=123456789098765432123456&student_id="
                                          f"{str(test_student_validation.get('_id'))}&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

@pytest.mark.asyncio
async def test_add_secondary_tertiary_details_required_student_id(
        http_client_test, test_college_validation, access_token,
        test_student_validation, college_super_admin_access_token,
        setup_module):
    """
      Required student id to add secondary_details
    """
    response = await http_client_test.get(
        f"/lead/add_secondary_tertiary_email_phone/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {'detail': "Student Id must be "
                                         "required and valid."}
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_add_secondary_tertiary_details_no_permissions(
        http_client_test, test_college_validation, access_token,
        test_student_validation, college_super_admin_access_token,
        setup_module):
    """
    No permission to add secondary teritiary details
    """
    response = await http_client_test.get(
        f"/lead/add_secondary_tertiary_email_phone/?student_id={str(test_student_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_add_secondary_tertiary_details_number(
        http_client_test, test_college_validation,
        test_student_validation, college_super_admin_access_token,
        setup_module):
    """
        add secondary tertiary details
    """
    response = await http_client_test.get(
        f"/lead/add_secondary_tertiary_email_phone/?student_id={str(test_student_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&phone=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.json() == {"message": "Added number"}
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_add_secondary_tertiary_details_email(
        http_client_test, test_college_validation,
        test_student_validation, college_super_admin_access_token,
        setup_module):
    """
      add secondary tertiary details
    """
    response = await http_client_test.get(
        f"/lead/add_secondary_tertiary_email_phone/?student_id={str(test_student_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&phone=false&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.json() == {"message": "Added email"}
    assert response.status_code == 200
