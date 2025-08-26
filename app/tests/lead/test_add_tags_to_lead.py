"""
This file contains test cases related to API route/endpoint which useful for
add tags to students.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_tags_to_student(
        http_client_test, test_college_validation, access_token,
        test_student_validation, college_super_admin_access_token,
        setup_module):
    """
    Test cases related to API route/endpoint which useful for add tags to
    students.
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post("/lead/add_tag/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for add tag to student.
    response = await http_client_test.post(
        f"/lead/add_tag/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for add tag to student.
    response = await http_client_test.post(
        f"/lead/add_tag/?feature_key={feature_key}", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 400
    assert response.json() == \
           {'detail': "College Id must be required and valid."}

    # Required student id for add tag to student.
    response = await http_client_test.post(
        f"/lead/add_tag/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json={}
    )
    assert response.json() == {'detail': "Student Ids must be "
                                         "required and valid."}
    assert response.status_code == 400

    # Required tags for add tag to student
    response = await http_client_test.post(
        f"/lead/add_tag/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"student_ids": [str(test_student_validation.get('_id'))]}
    )
    assert response.json() == {'detail': "Tags must be required and valid."}
    assert response.status_code == 400

    # Required body for add tag to student
    response = await http_client_test.post(
        f"/lead/add_tag/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {'detail': 'Body must be required and valid.'}
    assert response.status_code == 400

    # No permission for add tag to student
    response = await http_client_test.post(
        f"/lead/add_tag/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"student_ids": ["123456789012345678901234"], "tags": ["test1"]}
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401

    # Add tags to student
    response = await http_client_test.post(
        f"/lead/add_tag/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
        , json={"student_ids": [str(test_student_validation.get('_id'))],
                "tags": ["test1"]}
    )
    assert response.json() == {"message": "Tags added to the leads."}
    assert response.status_code == 200
