"""
This file contains test cases related to invite student to interview by mail.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_invite_student_to_interview(
        http_client_test, test_college_validation,
        college_super_admin_access_token, setup_module, access_token,
        test_slot_details, application_details, test_meeting_validation
):
    """
    Different test cases scenarios for invite student to interview by mail.
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/planner/invite_student_to_meeting/?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # Wrong token for invite student to interview by mail
    response = await http_client_test.post(
        f"/planner/invite_student_to_meeting/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for invite student to interview by mail
    response = await http_client_test.post(
        f"/planner/invite_student_to_meeting/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

    # Invalid college id for invite student to interview by mail
    response = await http_client_test.post(
        f"/planner/invite_student_to_meeting/?college_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # Wrong college id for invite student to interview by mail
    response = await http_client_test.post(
        f"/planner/invite_student_to_meeting/?"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    # Required slot id for invite student to interview by mail
    response = await http_client_test.post(
        f"/planner/invite_student_to_meeting/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Slot Id must be required and valid."}

    # Required application id for invite student to interview by mail
    response = await http_client_test.post(
        f"/planner/invite_student_to_meeting/?"
        f"college_id={str(test_college_validation.get('_id'))}&"
        f"slot_id={str(test_slot_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Application Id must be required "
                                         "and valid."}

    # Invalid slot id for invite student to interview by mail
    response = await http_client_test.post(
        f"/planner/invite_student_to_meeting/?"
        f"college_id={str(test_college_validation.get('_id'))}&"
        f"slot_id=123&application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Slot id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # Wrong slot id for invite student to interview by mail
    response = await http_client_test.post(
        f"/planner/invite_student_to_meeting/?"
        f"college_id={str(test_college_validation.get('_id'))}&"
        f"slot_id=123456789012345678901234&"
        f"application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json() == {'detail': 'Slot not found. '
                                         'Make sure provided slot id should '
                                         'be correct.'}

    # Invalid application id for invite student to interview by mail
    response = await http_client_test.post(
        f"/planner/invite_student_to_meeting/?"
        f"college_id={str(test_college_validation.get('_id'))}&"
        f"slot_id={str(test_slot_details.get('_id'))}&application_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Application id `123` must be a "
                                         "12-byte input or a 24-character "
                                         "hex string"}

    response = await http_client_test.post(
        f"/planner/invite_student_to_meeting/?"
        f"college_id={str(test_college_validation.get('_id'))}&"
        f"slot_id={str(test_slot_details.get('_id'))}"
        f"&application_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Application not found"}

    response = await http_client_test.post(
        f"/planner/invite_student_to_meeting/?"
        f"college_id={str(test_college_validation.get('_id'))}&"
        f"slot_id={str(test_slot_details.get('_id'))}"
        f"&application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    response = await http_client_test.post(
        f"/planner/invite_student_to_meeting/?"
        f"college_id={str(test_college_validation.get('_id'))}&"
        f"slot_id={str(test_slot_details.get('_id'))}"
        f"&application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Email send to student."}
