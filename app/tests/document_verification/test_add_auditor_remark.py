import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_auditor_remark(http_client_test, setup_module,
                                        college_super_admin_access_token, access_token,
                                        test_student_validation, test_college_validation, test_super_admin_validation,
                                  ):
    """
    Different test cases to get all college user details.

    Params:
        - http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        - setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
        - college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.
        - access_token: A fixture which create student if not exist
            and return access token for student.
        - test_student_validation: A fixture which create student if not exist and return student data.
        - test_college_validation: A fixture which create college if not exist and return college data.
        - test_super_admin_validation: A fixture which create super admin if not exist and return access token of super admin.
    Assertions:
        response status code and json message.
    """
    # Not authenticated
    response = await http_client_test.post(
        f"/document_verification/auditor_remark/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get remarks of  documents
    response = await http_client_test.post(
        f"/document_verification/auditor_remark/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for get remarks of  documents
    response = await http_client_test.post(
        f"/document_verification/auditor_remark/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    # Required student id for get remarks of  documents
    response = await http_client_test.post(
        f"/document_verification/auditor_remark/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Student Id must be required and valid.'}

    # Invalid student id

    response = await http_client_test.post(
        f"/document_verification/auditor_remark/?student_id=3a959fe6c43761fe2e"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json="Marks didn't match"
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "Student id must be a 12-byte input or a 24-character hex string"

    # Wrong student id

    response = await http_client_test.post(
        f"/document_verification/auditor_remark/?student_id=123456789012345678901234"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json="Marks didn't match"

    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Student not found."

    # Invalid college id to add remarks of documents
    response = await http_client_test.post(
        f"/document_verification/auditor_remark/?student_id={str(test_student_validation.get('_id'))}"
        f"&college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id for get comments of a document
    response = await http_client_test.post(
        f"/document_verification/auditor_remark/?student_id={str(test_student_validation.get('_id'))}&"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

     # Documents not found for get remarks

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentSecondaryDetails.delete_one({"student_id": test_student_validation.get("_id")})
    response = await http_client_test.post(
        f"/document_verification/auditor_remark/?student_id={str(test_student_validation.get('_id'))}&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json="Marks didn't match"
    )
    assert response.status_code == 404
    assert response.json()[
               'detail'] == f"Secondary data not found for student with ID: {test_student_validation.get('_id')}"

    # Add remark for documents

    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().studentSecondaryDetails.insert_one({"student_id": test_student_validation.get("_id"),
                                                                      "attachments": {"tenth": {"file_name": "test",
                                                                                                "file_s3_url": "test.jpg"}}})
    response = await http_client_test.post(
        f"/document_verification/auditor_remark/?student_id={str(test_student_validation.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json="Marks didn't match"

    )
    assert response.status_code == 200
    assert response.json()['message'] == "Auditor Remarks added."