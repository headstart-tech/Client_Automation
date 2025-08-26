"""
This file contains test cases related to send document to board.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_send_document_to_board(
    http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token, application_details, access_token
):
    """
    Different scenarios of test cases for send document to respective board.
    """
    # Not authenticated
    response = await http_client_test.post(f"/admin/send_student_document_to_board/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # bad token for send document to respective board
    response = await http_client_test.post(
        f"/admin/send_student_document_to_board/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for send document to respective board
    response = await http_client_test.post(
        f"/admin/send_student_document_to_board/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "College Id must be required and " \
                                        "valid."

    # Required application id for send document to respective board
    response = await http_client_test.post(
        f"/admin/send_student_document_to_board/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Application Id must be required and" \
                                        " valid."

    # Send document to respective board
    response = await http_client_test.post(
        f"/admin/send_student_document_to_board/"
        f"?college_id={str(test_college_validation.get('_id'))}&"
        f"application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Send document to respective board."}

    # Invalid college id for send document to respective board
    response = await http_client_test.post(
        f"/admin/send_student_document_to_board/"
        f"?college_id=123&"
        f"application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College id must be a 12-byte input " \
                                        "or a 24-character hex string"

    # Wrong college id for send document to respective board
    response = await http_client_test.post(
        f"/admin/send_student_document_to_board/"
        f"?college_id=123456789012345678901234&"
        f"application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College not found."

    # Not permission for send document to respective board
    response = await http_client_test.post(
        f"/admin/send_student_document_to_board/"
        f"?college_id={str(test_college_validation.get('_id'))}&"
        f"application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"

    # Invalid application id for send document to respective board
    response = await http_client_test.post(
        f"/admin/send_student_document_to_board/"
        f"?college_id={str(test_college_validation.get('_id'))}&"
        f"application_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Application id must be a 12-byte " \
                                        "input or a 24-character hex string"

    # Wrong application id for send document to respective board
    response = await http_client_test.post(
        f"/admin/send_student_document_to_board/"
        f"?college_id={str(test_college_validation.get('_id'))}&"
        f"application_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found."
