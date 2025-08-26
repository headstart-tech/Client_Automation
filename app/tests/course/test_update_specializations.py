"""
This file contains test cases related to update course specializations of
course.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_spec_of_course_not_authorized(
        http_client_test, test_college_validation, test_course_validation,
        college_super_admin_access_token, access_token, setup_module):
    """
    Test cases related to update course specializations of course.
    """
    # Not authenticated if user not logged in
    response = await http_client_test.put(f"/course/update_specializations/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for update specializations of course.
    response = await http_client_test.put(
        f"/course/update_specializations/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for update specializations of course.
    response = await http_client_test.put(
        f"/course/update_specializations/?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == \
           {"detail": "College Id must be required and valid."}

    # Invalid college id for update specializations of course.
    response = await http_client_test.put(
        f"/course/update_specializations/?college_id=1234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == \
           {"detail": 'College id must be a 12-byte input or a 24-character '
                      'hex string'}

    # College not found when for update specializations of course.
    response = await http_client_test.put(
        f"/course/update_specializations/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == \
           {"detail": 'College not found.'}

    # Required body for update specializations of course.
    response = await http_client_test.put(
        f"/course/update_specializations/?"
        f"college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == \
           {'detail': 'Body must be required and valid.'}

    # No permission for update specializations of course.
    response = await http_client_test.put(
        f"/course/update_specializations/?"
        f"college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}"},
        json=[]
    )
    assert response.status_code == 401
    assert response.json() == {'detail': 'Not enough permissions'}

    # Required course info for update specializations of course.
    response = await http_client_test.put(
        f"/course/update_specializations/?"
        f"college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[]
    )
    assert response.status_code == 200
    assert response.json() == {'detail': 'Course not found. Make sure course'
                                         ' id or name is correct.'}

    # Invalid course id for update specializations of course.
    response = await http_client_test.put(
        f"/course/update_specializations/?"
        f"college_id={test_college_validation.get('_id')}&course_id=123&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[]
    )
    assert response.status_code == 422
    assert response.json() == {"detail": 'Course id `123` must be a 12-byte '
                                         'input or a 24-character hex string'}

    # Specialization info not provided for update specializations of course.
    response = await http_client_test.put(
        f"/course/update_specializations/?"
        f"college_id={test_college_validation.get('_id')}&"
        f"course_id={test_course_validation.get('_id')}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[]
    )
    assert response.status_code == 200
    assert response.json() == \
           {"message": "Course specializations not updated."}

    # Update specializations to course.
    response = await http_client_test.put(
        f"/course/update_specializations/?"
        f"college_id={test_college_validation.get('_id')}&"
        f"course_id={test_course_validation.get('_id')}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[{"spec_index": 1, "spec_name": "test", "is_activated": True}]
    )
    assert response.status_code == 200
    assert response.json() == \
           {"message": "Course specializations updated."}
