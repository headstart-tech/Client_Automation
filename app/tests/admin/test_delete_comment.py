"""
This file contains test cases related to delete comment of a document
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_comment_of_document(http_client_test, setup_module, test_user_validation,
                                          college_super_admin_access_token, access_token,
                                          test_student_validation, test_college_validation):
    """
     Test cases for delete comment of a document
    """
    # Not authenticated
    response = await http_client_test.delete(
        f"/admin/delete_comment/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for delete comment of a document
    response = await http_client_test.delete(
        f"/admin/delete_comment/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for delete comment of a document
    response = await http_client_test.delete(
        f"/admin/delete_comment/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    # Required comment id for delete comment of a document
    response = await http_client_test.delete(
        f"/admin/delete_comment/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Comment Id must be required and valid.'}

    # Required student id for delete comment of a document
    response = await http_client_test.delete(
        f"/admin/delete_comment/?college_id={str(test_college_validation.get('_id'))}"
        f"&comment_id=0&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Student Id must be required and valid.'}

    # Required permission for delete comment of a document
    response = await http_client_test.delete(
        f"/admin/delete_comment/?student_id={str(test_student_validation.get('_id'))}&comment_id=0"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json()['detail'] == "Not enough permissions"

    # Invalid student id
    response = await http_client_test.delete(
        f"/admin/delete_comment/?student_id=1234567&comment_id=0"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "Student id must be a 12-byte input or a 24-character hex string"

    # Wrong student id
    response = await http_client_test.delete(
        f"/admin/delete_comment/?student_id=123456789012345678901234&comment_id=0"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Student not found."

    # Invalid college id for delete comment of a document
    response = await http_client_test.delete(
        f"/admin/delete_comment/?student_id={str(test_student_validation.get('_id'))}&comment_id=0"
        f"&college_id=123&feature_key={feature_key}", headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id for delete comment of a document
    response = await http_client_test.delete(
        f"/admin/delete_comment/?student_id={str(test_student_validation.get('_id'))}&comment_id=0&"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Document not found for add comment
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentSecondaryDetails.delete_one({"student_id": test_student_validation.get("_id")})
    response = await http_client_test.delete(
        f"/admin/delete_comment/?student_id={str(test_student_validation.get('_id'))}&comment_id=0&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Student document not found."

    # Add comment for a delete
    await DatabaseConfiguration().studentSecondaryDetails.insert_one(
        {"student_id": test_student_validation.get("_id"),
         "attachments": {"tenth": {"file_name": "test",
                                   "file_s3_url": "test.jpg",
                                   "comments": [{"message": "test",
                                                 "user_id": test_user_validation.get(
                                                     "_id")}]}}})
    response = await http_client_test.delete(
        f"/admin/delete_comment/?student_id={str(test_student_validation.get('_id'))}&comment_id=0"
        f"&tenth=true&feature_key={feature_key}"
        f"&college_id={str(test_college_validation.get('_id'))}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Comment deleted."
