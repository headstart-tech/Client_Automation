"""
This file contains test cases related to get auditor remarks of document
"""
import datetime

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_auditor_remarks(http_client_test, setup_module, college_super_admin_access_token,
                                   access_token, test_student_validation, test_college_validation,
                                   test_super_admin_validation):
    """
     Test cases for get auditor remarks of documents
    """
    # Not authenticated
    response = await http_client_test.get(
        f"/document_verification/get_auditor_remarks/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get auditor remarks of documents
    response = await http_client_test.get(
        f"/document_verification/get_auditor_remarks/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for get auditor remarks of documents
    response = await http_client_test.get(
        f"/document_verification/get_auditor_remarks/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    # Required student id for get auditor remarks of documents
    response = await http_client_test.get(
        f"/document_verification/get_auditor_remarks/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Student Id must be required and valid.'}

    # Invalid student id
    response = await http_client_test.get(
        f"/document_verification/get_auditor_remarks/?student_id=1234567"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "Student id must be a 12-byte input or a 24-character hex string"

    # Wrong student id
    response = await http_client_test.get(
        f"/document_verification/get_auditor_remarks/?student_id=123456789012345678901234"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Student not found."

    # Invalid college id for get auditor remarks of documents
    response = await http_client_test.get(
        f"/document_verification/get_auditor_remarks/?student_id={str(test_student_validation.get('_id'))}"
        f"&college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id for get auditor remarks of documents
    response = await http_client_test.get(
        f"/document_verification/get_auditor_remarks/?student_id={str(test_student_validation.get('_id'))}&"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Document not found to get auditor remarks
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentSecondaryDetails.delete_one({"student_id": test_student_validation.get("_id")})
    response = await http_client_test.get(
        f"/document_verification/get_auditor_remarks/?student_id={str(test_student_validation.get('_id'))}&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == f"Secondary data not found for student with ID: {str(test_student_validation.get('_id'))}"

    # assert response.json()['detail'] == "Student document not found."

    # No Remarks for documents (Empty List)
    await DatabaseConfiguration().studentSecondaryDetails.insert_one({"student_id": test_student_validation.get("_id"),
                                                                      "attachments": {"tenth": {"file_name": "test",
                                                                                                "file_s3_url": "test.jpg"}}})
    response = await http_client_test.get(
        f"/document_verification/get_auditor_remarks/?student_id={str(test_student_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get Auditor Remarks."
    assert response.json()['remarks'] == []

    # Remarks for documents(Non Empty List)
    await DatabaseConfiguration().studentSecondaryDetails.update_one({"student_id": test_student_validation.get("_id")},
                                                                     {"$set":  {"auditor_remarks": [{
                                                                         "message": "test",
                                                                         "timestamp": datetime.datetime.utcnow(),
                                                                         "user_name": "test",
                                                                         "user_id": test_super_admin_validation.get(
                                                                             "_id")
                                                                     }]}})
    response = await http_client_test.get(
        f"/document_verification/get_auditor_remarks/?student_id={str(test_student_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get Auditor Remarks."
    assert response.json()['remarks'] != []

