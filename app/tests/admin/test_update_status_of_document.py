"""
This file contains test cases related to update status of a document
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_status_of_document(http_client_test, setup_module,
                                         college_super_admin_access_token, access_token,
                                         application_details, test_college_validation):
    """
     Test cases for update status of a document
    """
    college_id = str(test_college_validation.get('_id'))
    application_id = str(application_details.get('_id'))
    # Not authenticated
    response = await http_client_test.put(
        f"/admin/update_status_of_document/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for update status of document
    response = await http_client_test.put(
        f"/admin/update_status_of_document/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for update status of document
    response = await http_client_test.put(
        f"/admin/update_status_of_document/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}

    # Required application id for update status of document
    response = await http_client_test.put(
        f"/admin/update_status_of_document/?college_id={college_id}&status=Accepted&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Application Id must be required and valid.'}

    # Required status for update status of document
    response = await http_client_test.put(
        f"/admin/update_status_of_document/?application_id={application_id}"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == "Status must be required and valid."

    # Invalid status for update status of document
    response = await http_client_test.put(
        f"/admin/update_status_of_document/?application_id={application_id}&status=test"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == "Status must be required and valid."

    # Required permission for update status of document
    response = await http_client_test.put(
        f"/admin/update_status_of_document/?application_id={application_id}&status=Accepted"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json()['detail'] == "Not enough permissions"

    # Invalid application id
    response = await http_client_test.put(
        f"/admin/update_status_of_document/?application_id=1234567&status=Accepted"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "Application id must be a 12-byte input or a 24-character hex string"

    # Wrong application id
    response = await http_client_test.put(
        f"/admin/update_status_of_document/?application_id=123456789012345678901234&status=Accepted"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Application not found."

    # Invalid college id for update status of document
    response = await http_client_test.put(
        f"/admin/update_status_of_document/?application_id={application_id}&status=Accepted"
        f"&college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College id must be a 12-byte input or a 24-character hex string"

    # Wrong college id for update status of document
    response = await http_client_test.put(
        f"/admin/update_status_of_document/?application_id={application_id}&status=Accepted&"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == "College not found."

    student_id = application_details.get("student_id")
    # Document not found for update status of a document
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentSecondaryDetails.delete_one({"student_id": student_id})
    response = await http_client_test.put(
        f"/admin/update_status_of_document/?application_id={application_id}&status=Accepted&"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Student document not found."

    # Update status of a document
    await DatabaseConfiguration().studentSecondaryDetails.insert_one({"student_id": student_id,
                                                                      "attachments": {"tenth": {"file_name": "test",
                                                                                                "file_s3_url": "test.jpg"}}})
    response = await http_client_test.put(
        f"/admin/update_status_of_document/?application_id={application_id}&status=Accepted&tenth=true"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Updated status of a document."
