"""
This file contains test cases related to get external links of student documents
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_external_links_of_student_documents(
        http_client_test, setup_module, college_super_admin_access_token,
        access_token, application_details, test_college_validation,
        test_super_admin_validation):
    """
     Test cases for get external links of student documents
    """
    # Not authenticated
    response = await http_client_test.get(
        f"/admin/get_external_links_of_student_documents/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get external links of student documents
    response = await http_client_test.get(
        f"/admin/get_external_links_of_student_documents/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for get external links of student documents
    response = await http_client_test.get(
        f"/admin/get_external_links_of_student_documents/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and '
                                         'valid.'}

    # Required application id for get external links of student documents
    response = await http_client_test.get(
        f"/admin/get_external_links_of_student_documents/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Application Id must be required and '
                                         'valid.'}

    # Required permission for get external links of student documents
    response = await http_client_test.get(
        f"/admin/get_external_links_of_student_documents/?application_id="
        f"{str(application_details.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json()['detail'] == "Not enough permissions"

    # Invalid application id
    response = await http_client_test.get(
        f"/admin/get_external_links_of_student_documents/?application_id="
        f"1234567&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "Application id must be a 12-byte " \
                                        "input or a 24-character hex string"

    # Wrong application id
    response = await http_client_test.get(
        f"/admin/get_external_links_of_student_documents/?application_id="
        f"123456789012345678901234&college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Application not found."

    # Invalid college id for get external links of student documents
    response = await http_client_test.get(
        f"/admin/get_external_links_of_student_documents/?"
        f"application_id={str(application_details.get('_id'))}"
        f"&college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input " \
                                        "or a 24-character hex string"

    # Wrong college id for get external links of student documents
    response = await http_client_test.get(
        f"/admin/get_external_links_of_student_documents/?"
        f"application_id={str(application_details.get('_id'))}&"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    # Get external links of student documents
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentSecondaryDetails.insert_one(
        {"student_id": application_details.get("student_id"),
         "attachments": {"tenth": {"file_name": "test",
                                   "file_s3_url": "test.jpg"}}})
    response = await http_client_test.get(
        f"/admin/get_external_links_of_student_documents/?"
        f"application_id={str(application_details.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get external links of student " \
                                         "documents."
    assert len(response.json()['data']) > 0
