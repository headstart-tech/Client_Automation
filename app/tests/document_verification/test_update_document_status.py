import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_document_status(http_client_test, test_college_validation, setup_module,
                                      college_super_admin_access_token,access_token,application_details):
    """
    Not authenticated if user not logged in
    """
    college_id = str(test_college_validation.get('_id'))
    application_id = str(application_details.get('_id'))
    response = await http_client_test.put(
        f"/document_verification/update_dv_status/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    """
    Bad token to update document status
    """
    response = await http_client_test.put(
        f"/document_verification/update_dv_status/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    """
    Required college id to update document status
    """
    response = await http_client_test.put(f"/document_verification/update_dv_status/?feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    """
    Invalid college id to update document status
    """
    response = await http_client_test.put(f"/document_verification/update_dv_status/?college_id=3214567890"
                                          f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
                                           )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    """
    College not found to update document status
    """
    response = await http_client_test.put(
        f"/document_verification/update_dv_status/?college_id=765432189012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'
    """
    Application ID must be Required
    """
    response = await http_client_test.put(
        f"/document_verification/update_dv_status/?college_id={college_id}&status=Accepted&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Application Id must be required and valid.'}
    """
    Wrong Application ID
    """
    response = await http_client_test.put(
        f"/document_verification/update_dv_status/?application_id=123456789012345678901234&status=Accepted"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Application not found."

    """
    Update Document Status
    """
    from app.database.configuration import DatabaseConfiguration
    student_id = application_details.get("student_id")
    await DatabaseConfiguration().studentSecondaryDetails.insert_one({"student_id": student_id,
                                                                      "attachments": {"tenth": {"file_name": "test",
                                                                                                "file_s3_url": "test.jpg"}}})
    response = await http_client_test.put(
        f"/document_verification/update_dv_status/?application_id={application_id}&status=Accepted"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})

    assert response.status_code == 200
    assert response.json()['message'] == "Updated dv_status of a document."