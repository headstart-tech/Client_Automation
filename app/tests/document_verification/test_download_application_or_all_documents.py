"""
This file contains test cases for download applications or download all documents of students
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_download_application_or_all_documents(http_client_test, test_college_validation,
                                                     super_admin_access_token, college_super_admin_access_token,
                                                     test_student_validation, setup_module):
    """
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
    Assertions:
        response status code and json message.
    """

    # Not authenticated if user not logged in

    response = await http_client_test.post(
        f"/document_verification/download_application_or_all_documents/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    """
    Bad token for download documents
    """
    response = await http_client_test.post(
        f"/document_verification/download_application_or_all_documents/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    """
    Required college id for download documents
    """
    response = await http_client_test.post(f"/document_verification/download_application_or_all_documents/"
                                           f"?feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    """
    Invalid college id for download documents
    """
    response = await http_client_test.post(f"/document_verification/download_application_or_all_documents/"
                                           f"?college_id=1234567890&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    """
    College not found for download documents
    """
    response = await http_client_test.post(
        f"/document_verification/download_application_or_all_documents/"
        f"?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    """
    Found no applications to download 
    """

    response = await http_client_test.post(
        f"/document_verification/download_application_or_all_documents/"
        f"?college_id={str(test_college_validation.get('_id'))}&download_applications=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[str(test_student_validation.get('_id'))]
    )
    assert response.status_code == 200
    # assert "data" in response.json()
    assert response.json()['message'] == 'Found no documents to download'

    """
    Found no documents to download
    """

    response = await http_client_test.post(
        f"/document_verification/download_application_or_all_documents/"
        f"?college_id={str(test_college_validation.get('_id'))}&download_applications=false&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=[str(test_student_validation.get('_id'))]
    )
    assert response.status_code == 200
    assert response.json()['message'] == 'Found no documents to download'