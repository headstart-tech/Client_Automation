"""
This file contains test cases of send applicants for approval
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_send_applicants_for_approval(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_user_validation,
        application_details, test_interview_list_validation):
    """
    Different scenarios of test cases -> send applicants for approval
    """
    college_id = str(test_college_validation.get('_id'))

    # Not authenticated if user not logged in
    response = await http_client_test.put(
        f"/interview_list/send_applicants_for_approval/?"
        f"college_id={college_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token -> send applicants for approval
    response = await http_client_test.put(
        f"/interview_list/send_applicants_for_approval/?"
        f"college_id={college_id}&feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required interview list id -> send applicants for approval
    response = await http_client_test.put(
        f"/interview_list/send_applicants_for_approval/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Payload must be required "
                                         "and valid."}

    interview_list_id = str(test_interview_list_validation.get('_id'))
    data = {"payload": {"interview_list_id": interview_list_id}}
    # Required body -> send applicants for approval
    response = await http_client_test.put(
        f"/interview_list/send_applicants_for_approval/?college_id="
        f"{college_id}&feature_key={feature_key}", json={"payload": {}},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Interview List Id must be required "
                                         "and valid."}

    application_id = str(application_details.get("_id"))
    # No permission for send applicants for approval
    response = await http_client_test.put(
        f"/interview_list/send_applicants_for_approval/?"
        f"college_id={college_id}&interview_list_id={interview_list_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}, json=data
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Send applicants for approval
    response = await http_client_test.put(
        f"/interview_list/send_applicants_for_approval/?"
        f"college_id={college_id}&interview_list_id={interview_list_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"payload": {"interview_list_id": interview_list_id},
              "application_ids": [application_id]}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Send applicants for approval."}

    # Required college id for send applicants for approval
    response = await http_client_test.put(
        f"/interview_list/send_applicants_for_approval/?interview_list_id="
        f"{interview_list_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=data
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and ' \
                                        'valid.'

    # Invalid college id for send applicants for approval
    response = await http_client_test.put(
        f"/interview_list/send_applicants_for_approval/?college_id=1234567890"
        f"&interview_list_id={interview_list_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input ' \
                                        'or a 24-character hex string'

    # College not found when try to send applicants for approval
    response = await http_client_test.put(
        f"/interview_list/send_applicants_for_approval/"
        f"?college_id=123456789012345678901234&interview_list_id="
        f"{interview_list_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Invalid application id -> send applicants for approval
    response = await http_client_test.put(
        f"/interview_list/send_applicants_for_approval/"
        f"?college_id={college_id}&interview_list_id={interview_list_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"payload": {"interview_list_id": interview_list_id},
              "application_ids": ["123"]}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Application id `123` must be a ' \
                                        '12-byte input or a 24-character ' \
                                        'hex string'

    # Invalid interview list id for applicants for approval
    response = await http_client_test.put(
        f"/interview_list/send_applicants_for_approval/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"payload": {"interview_list_id": "123"}}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Interview list id `123` must be a "
                                         "12-byte input or a 24-character "
                                         "hex string"}

    # Wrong interview list id for applicants for approval
    response = await http_client_test.put(
        f"/interview_list/send_applicants_for_approval/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"payload": {"interview_list_id": "123456789012345678901234"}}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Interview list not found"}
