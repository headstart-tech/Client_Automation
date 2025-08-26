"""
This file contains test cases related to add/update student data
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_or_update_details_not_authenticated(
        http_client_test, test_college_validation, setup_module
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/student/add_or_update_details/BSc/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_add_or_update_details_bad_credentials(
        http_client_test, test_college_validation, setup_module
):
    """
    Bad token for add or update details
    """
    response = await http_client_test.put(
        f"/student/add_or_update_details/BSc/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_add_or_update_details_no_permission(
        http_client_test,
        test_college_validation,
        college_counselor_access_token,
        test_student_education_details,
        setup_module,
        test_course_validation
):
    """
    No permission for add or update details
    """
    response = await http_client_test.put(
        f"/student/add_or_update_details/{test_course_validation.get('course_name')}/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_counselor_access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_education_details,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_add_or_update_details(
        http_client_test, test_college_validation, access_token, test_student_education_details, setup_module,
        test_course_validation
):
    """
    Add or update education details
    """
    response = await http_client_test.put(
        f"/student/add_or_update_details/{test_course_validation.get('course_name')}/"
        f"?college_id={str(test_college_validation.get('_id'))}&stage_category=education_details"
        f"&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_education_details,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Education Details added or updated successfully"


@pytest.mark.asyncio
async def test_add_or_update_details_course_not_found(
        http_client_test, test_college_validation, access_token, test_student_education_details, setup_module
):
    """
    Course not found. for add or update details
    """
    response = await http_client_test.put(
        f"/student/add_or_update_details/bsc/?college_id={str(test_college_validation.get('_id'))}"
        f"&stage_category=education_details&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_education_details,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "course not found."


@pytest.mark.asyncio
async def test_add_or_update_details_category_not_found(
        http_client_test, test_college_validation, access_token, test_student_education_details, setup_module
):
    """
    Category not found. for add or update details
    """
    response = await http_client_test.put(
        f"/student/add_or_update_details/bsc/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_education_details,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Stage Category must be required and valid."


@pytest.mark.asyncio
async def test_add_or_update_details_invalid_college_id(
        http_client_test, access_token, test_student_education_details, setup_module, test_course_validation):
    """
    Add or update education details
    """
    response = await http_client_test.put(
        f"/student/add_or_update_details/{test_course_validation.get('course_name')}/"
        f"?college_id=1234567890&stage_category=education_details&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_education_details,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College id must be a 12-byte input or a 24-character hex string"


@pytest.mark.asyncio
async def test_add_or_update_details_wrong_college_id(
        http_client_test, access_token, test_student_education_details, setup_module, test_course_validation):
    """
    Add or update education details
    """
    response = await http_client_test.put(
        f"/student/add_or_update_details/{test_course_validation.get('course_name')}/"
        f"?college_id=123456789012345678901234&stage_category=education_details&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_education_details,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College not found."
