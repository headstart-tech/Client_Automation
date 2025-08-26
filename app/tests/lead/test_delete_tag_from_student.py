"""
This file contains test cases related to API route/endpoint which useful for
delete tag from student.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_tag_from_student(
        http_client_test, test_college_validation, access_token,
        test_student_validation, college_super_admin_access_token,
        setup_module):
    """
    Test cases related to API route/endpoint which useful for delete tag
    from student.
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(f"/lead/delete_tag/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for delete tag from student.
    response = await http_client_test.post(
        f"/lead/delete_tag/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for delete tag from student.
    response = await http_client_test.post(
        f"/lead/delete_tag/?feature_key={feature_key}", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 400
    assert response.json() == \
           {'detail': "College Id must be required and valid."}

    # Required student id for delete tag from student.
    response = await http_client_test.post(
        f"/lead/delete_tag/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json={}
    )
    assert response.json() == {'detail': "Student Id must be "
                                         "required and valid."}
    assert response.status_code == 400

    # Required tag for delete tag from student
    response = await http_client_test.post(
        f"/lead/delete_tag/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"student_id": str(test_student_validation.get('_id'))}
    )
    assert response.json() == {'detail': "Tag must be required and valid."}
    assert response.status_code == 400

    # Required body for delete tag from student
    response = await http_client_test.post(
        f"/lead/delete_tag/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.json() == {'detail': 'Body must be required and valid.'}
    assert response.status_code == 400

    # No permission for delete tag from student
    response = await http_client_test.post(
        f"/lead/delete_tag/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"student_id": "123456789012345678901234", "tag": "test1"}
    )
    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 401

    # Tag not present to remove tag from student
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentsPrimaryDetails.update_one(
        {"_id": test_student_validation.get('_id')},
        {'$unset': {'tags': True}})
    response = await http_client_test.post(
        f"/lead/delete_tag/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
        , json={"student_id": str(test_student_validation.get('_id')),
                "tag": "test1"}
    )
    assert response.json() == {"message": "No any tag present for student."}
    assert response.status_code == 200

    # Remove tag from student
    await DatabaseConfiguration().studentsPrimaryDetails.update_one(
        {"_id": test_student_validation.get('_id')},
        {'$set': {'tags': ["test"]}})
    response = await http_client_test.post(
        f"/lead/delete_tag/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
        , json={"student_id": str(test_student_validation.get('_id')),
                "tag": "test1"}
    )
    assert response.json() == {"message": "Tag `test1` not found for student."}
    assert response.status_code == 200

    response = await http_client_test.post(
        f"/lead/delete_tag/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
        , json={"student_id": str(test_student_validation.get('_id')),
                "tag": "test"}
    )
    assert response.json() == {"message": "Tag deleted."}
    assert response.status_code == 200
