"""
This file contains test cases of unassigned applicant from a slot.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_unassigned_application_not_authenticated(
        http_client_test, setup_module, test_college_validation,
        test_take_slot, test_slot_details, application_details, access_token,
        college_super_admin_access_token, test_panelist_validation):
    """
    Different test cases of unassigned applicant from a slot.

    Params:\n
        http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
        application_details: A dictionary which contains application data.
    Assertions:\n
        response status code and json message
    """
    # Un-authorized user tried to unassigned user from a slot.
    response = await http_client_test.get(f"/interview_list"
                                          f"/unassigned_application?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not authenticated'

    application_id = str(application_details.get('_id'))
    slot_id = str(test_slot_details.get('_id'))
    college_id = str(test_college_validation.get('_id'))

    # Wrong token send for unassigned user from a slot.
    response = await http_client_test.get(
        f"/interview_list/unassigned_application?application_id="
        f"{application_id}&slot_id="
        f"{slot_id}&college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={"authorization": f"Bearer wrong"})
    assert response.status_code == 401
    assert response.json()['detail'] == "Could not validate credentials"

    # Required college id for unassigned user from a slot.
    response = await http_client_test.get(
        f"/interview_list/unassigned_application?application_id="
        f"{application_id}&slot_id="
        f"{slot_id}&feature_key={feature_key}",
        headers={"authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == "College Id must be required and " \
                                        "valid."

    # Invalid college id for unassigned user from a slot.
    response = await http_client_test.get(
        f"/interview_list/unassigned_application?application_id="
        f"{application_id}&slot_id="
        f"{slot_id}&college_id=123&feature_key={feature_key}",
        headers={"authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input ' \
                                        'or a 24-character hex string'

    # College not found for unassigned user from a slot.
    response = await http_client_test.get(
        f"/interview_list/unassigned_application?application_id="
        f"{application_id}&slot_id="
        f"{slot_id}&college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={
            "authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Not enough permission for unassigned user from a slot.
    response = await http_client_test.get(
        f"/interview_list/unassigned_application?application_id="
        f"{application_id}&slot_id="
        f"{slot_id}&college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={"authorization": f"Bearer {access_token}"})
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not enough permissions'

    # Invalid application id for unassigned applicant from a slot.
    response = await http_client_test.get(
        f"/interview_list/unassigned_application?application_id="
        f"121673874877424&slot_id={slot_id}"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={"authorization":
                     f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()["detail"] == f"Application id must be a 12-byte" \
                                        f" input or a 24-character hex string"

    # Invalid slot id for unassigned user from a slot.
    response = await http_client_test.get(
        f"/interview_list/unassigned_application?application_id="
        f"{application_id}&slot_id="
        f"123&college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={"authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'Slot id must be a 12-byte input ' \
                                        'or a 24-character hex string'

    # Wrong slot id for unassigned user from a slot.
    response = await http_client_test.get(
        f"/interview_list/unassigned_application?application_id="
        f"{application_id}&college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={"authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == "Slot Id must be required and valid."

    # Slot not found for unassigned user from a slot.
    response = await http_client_test.get(
        f"/interview_list/unassigned_application?application_id="
        f"{application_id}&slot_id="
        f"123456789012345678901234&college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={
            "authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 404
    assert response.json()['detail'] == 'Slot not found id: ' \
                                        '123456789012345678901234'

    # Application not found for unassigned applicant from a slot.
    response = await http_client_test.get(
        f"/interview_list/unassigned_application?application_id="
        f"123456789012345678901234&slot_id="
        f"{slot_id}&college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={
            "authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 404
    assert response.json()['detail'] == 'Application not found id: ' \
                                        '123456789012345678901234'

    # Unassigned applicant from a slot.
    response = await http_client_test.get(
        f"/interview_list/unassigned_application?application_id="
        f"{application_id}&slot_id="
        f"{slot_id}&college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={
            "authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "User has unassigned from a slot."

    # Unassigned panelist from a slot.
    response = await http_client_test.get(
        f"/interview_list/unassigned_application?panelist_id="
        f"{str(test_panelist_validation.get('_id'))}&slot_id="
        f"{slot_id}&college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={
            "authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "User has unassigned from a slot."

    # Panelist not found for unassigned panelist from a slot.
    response = await http_client_test.get(
        f"/interview_list/unassigned_application?panelist_id="
        f"123456789012345678901234&slot_id="
        f"{slot_id}&college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={
            "authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 404
    assert response.json()['detail'] == 'Panelist not found id: ' \
                                        '123456789012345678901234'

    # Invalid panelist id for unassigned panelist from a slot.
    response = await http_client_test.get(
        f"/interview_list/unassigned_application?panelist_id="
        f"121673874877424&slot_id={slot_id}"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={"authorization":
                     f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()["detail"] == f"Panelist id must be a 12-byte" \
                                        f" input or a 24-character hex string"
