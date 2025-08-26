"""
This file contains test cases related to communication log API routes/endpoints
"""
import pytest


@pytest.mark.asyncio
async def test_get_communication_log(
        http_client_test, test_college_validation, setup_module,
        application_details):
    """
    Test cases for get communication log of a student.
    """
    application_id = str(application_details.get('_id'))
    # Get call log of a student
    response = await http_client_test.post(
        f"/student_communication_log/{application_id}/"
        f"?college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the call logs."

    # Wrong application id for get student communication log
    response = await http_client_test.post(
        f"/student_communication_log/123456789012345678901234/"
        f"?college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"

    # invalid application id for get student communication log
    response = await http_client_test.post(
        f"/student_communication_log/1234/"
        f"?college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 422
    assert response.json()["detail"] == \
           "Application id must be a 12-byte input or a 24-character " \
           "hex string"

    # Required college id for get student communication log
    response = await http_client_test.post(
        f"/student_communication_log/1234/"
    )
    assert response.status_code == 400
    assert response.json()["detail"] == \
           "College Id must be required and valid."

    # invalid college id for get student communication log
    response = await http_client_test.post(
        f"/student_communication_log/{application_id}/"
        f"?college_id=1234"
    )
    assert response.status_code == 422
    assert response.json()["detail"] == \
           "College id must be a 12-byte input or a 24-character " \
           "hex string"

    # Wrong college id for get student communication log
    response = await http_client_test.post(
        f"/student_communication_log/{application_id}/"
        f"?college_id=123456789012345678901234"
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College not found."

    # Get email log with timeline
    response = await http_client_test.post(
        f"/student_communication_log/{application_id}/"
        f"?college_id={str(test_college_validation.get('_id'))}&email=true"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the email logs."

    # Get sms log with timeline
    response = await http_client_test.post(
        f"/student_communication_log/{application_id}/"
        f"?college_id={str(test_college_validation.get('_id'))}&sms=true"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the sms logs."

    # Get whatsappa log with timeline
    response = await http_client_test.post(
        f"/student_communication_log/{application_id}/"
        f"?college_id={str(test_college_validation.get('_id'))}&whatsapp=true"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the whatsapp logs."
