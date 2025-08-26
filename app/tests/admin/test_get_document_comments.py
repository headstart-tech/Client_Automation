"""
This file contains test cases related to get comments of a document
"""
import datetime

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_comment_for_document(http_client_test, setup_module,
                                        college_super_admin_access_token, access_token,
                                        test_student_validation, test_college_validation, test_super_admin_validation):
    """
     Test cases for get comments of a document
    """
    # Not authenticated
    response = await http_client_test.get(
        f"/admin/get_document_comments/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get comments of a document
    response = await http_client_test.get(
        f"/admin/get_document_comments/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for get comments of a document
    response = await http_client_test.get(
        f"/admin/get_document_comments/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    # Required student id for get comments of a document
    response = await http_client_test.get(
        f"/admin/get_document_comments/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Student Id must be required and valid.'}

    # Invalid student id
    response = await http_client_test.get(
        f"/admin/get_document_comments/?student_id=1234567"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "Student id must be a 12-byte input or a 24-character hex string"

    # Wrong student id
    response = await http_client_test.get(
        f"/admin/get_document_comments/?student_id=123456789012345678901234"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Student not found."

    # Invalid college id for get comments of a document
    response = await http_client_test.get(
        f"/admin/get_document_comments/?student_id={str(test_student_validation.get('_id'))}"
        f"&college_id=123&feature_key={feature_key}", headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id for get comments of a document
    response = await http_client_test.get(
        f"/admin/get_document_comments/?student_id={str(test_student_validation.get('_id'))}&"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Document not found for get comments
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentSecondaryDetails.delete_one({"student_id": test_student_validation.get("_id")})
    response = await http_client_test.get(
        f"/admin/get_document_comments/?student_id={str(test_student_validation.get('_id'))}&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Student document not found."

    # Comments of a document not found
    await DatabaseConfiguration().studentSecondaryDetails.insert_one({"student_id": test_student_validation.get("_id"),
                                                                      "attachments": {"tenth": {"file_name": "test",
                                                                                                "file_s3_url": "test.jpg"}}})
    response = await http_client_test.get(
        f"/admin/get_document_comments/?student_id={str(test_student_validation.get('_id'))}&tenth=true"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get document comments."
    assert response.json()['document_comments'] == []

    # Comments of a document not found
    await DatabaseConfiguration().studentSecondaryDetails.update_one({"student_id": test_student_validation.get("_id")},
                                                                     {"$set": {"attachments.tenth": {"comments": [{
                                                                         "message": "test",
                                                                         "timestamp": datetime.datetime.utcnow(),
                                                                         "user_name": "test",
                                                                         "user_id": test_super_admin_validation.get(
                                                                             "_id")
                                                                     }]}}})
    response = await http_client_test.get(
        f"/admin/get_document_comments/?student_id={str(test_student_validation.get('_id'))}&tenth=true"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get document comments."
    assert response.json()['document_comments'] != []
