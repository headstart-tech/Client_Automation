"""
This file contains test cases related to add course specializations to course.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_spec_to_course(
        http_client_test, test_college_validation,
        college_super_admin_access_token, access_token,
        test_course_validation, setup_module):
    """
    test cases related to add course specializations to course.
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(f"/course/add_specializations/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for add specializations to course.
    response = await http_client_test.post(
        f"/course/add_specializations/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for add specializations to course.
    response = await http_client_test.post(
        f"/course/add_specializations/?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == \
           {"detail": "College Id must be required and valid."}

    # Invalid college id for add specializations to course.
    response = await http_client_test.post(
        f"/course/add_specializations/?college_id=1234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == \
           {"detail": 'College id must be a 12-byte input or a 24-character '
                      'hex string'}

    # College not found when for add specializations to course.
    response = await http_client_test.post(
        f"/course/add_specializations/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == \
           {"detail": 'College not found.'}

    college_id = str(test_college_validation.get('_id'))
    # Required body for add specializations to course.
    response = await http_client_test.post(
        f"/course/add_specializations/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == \
           {'detail': 'Body must be required and valid.'}

    # No permission for add specializations to course.
    response = await http_client_test.post(
        f"/course/add_specializations/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}"},
        json=[]
    )
    assert response.status_code == 401
    assert response.json() == {'detail': 'Not enough permissions'}

    # Required course info for add specializations to course.
    response = await http_client_test.post(
        f"/course/add_specializations/?college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[]
    )
    assert response.status_code == 200
    assert response.json() == {'detail': 'Course not found. Make sure course'
                                         ' id or name is correct.'}

    # Invalid course id for add specializations to course.
    response = await http_client_test.post(
        f"/course/add_specializations/?"
        f"college_id={college_id}&course_id=123&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[]
    )
    assert response.status_code == 422
    assert response.json() == {"detail": 'Course id `123` must be a 12-byte '
                                         'input or a 24-character hex string'}

    # Specialization info not provided for add specializations to course.
    response = await http_client_test.post(
        f"/course/add_specializations/?"
        f"college_id={college_id}&"
        f"course_id={str(test_course_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[]
    )
    assert response.status_code == 200
    assert response.json() == \
           {'detail': 'Course specializations data not provided.'}

    # Todo: will will check later
    # Add specializations to course.
    # response = await http_client_test.post(
    #     f"/course/add_specializations/?"
    #     f"college_id={college_id}&"
    #     f"course_id={str(test_course_validation.get('_id'))}",
    #     headers={
    #         "Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=[{"spec_name": "test", "is_activated": True}]
    # )
    # assert response.status_code == 200
    # assert response.json() == \
    #        {'message': 'Course specializations added.'}
