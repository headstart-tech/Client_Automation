"""
This file contains test cases related to send payment receipt through mail
API route/endpoint.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_cases_of_send__payment_receipt(
        http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token, super_admin_access_token,
        access_token, application_details
        ):
    """
    Different test cases of send payment receipt through mail.

    Params:\n
        - http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        - setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
        - test_college_validation: A fixture which create college if not exist
            and return college data.
        - college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.
        - super_admin_access_token: A fixture which create super admin if not
            exist and return access token for super admin.
        - test_student_validation: A fixture which create student if not exist
            and return student data.
        - application_details: A fixture which create application if not exist
            and return application data.

    Assertions:\n
        - response status code and json message.
    """
    # Check authentication send wrong token
    response = await http_client_test.post(
        f"/payments/send_receipt_through_mail/?feature_key={feature_key}",
        headers={"Authorization": "wrong token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    college_id = str(test_college_validation.get('_id'))
    # Wrong token for send payment receipt through mail
    response = await http_client_test.post(
        f"/payments/send_receipt_through_mail/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # No permission for send payment receipt through mail
    response = await http_client_test.post(
        f"/payments/send_receipt_through_mail/?application_id=123&feature_key={feature_key}"
        f"&college_id={college_id}",
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"

    # Validate successful response
    response = await http_client_test.post(
        f"/payments/send_receipt_through_mail/?application_id="
        f"{str(application_details.get('_id'))}"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json() == {"detail": "Not able to send mail in the "
                                         "case testing environment."}

    # Required college id for send payment receipt through mail
    response = await http_client_test.post(
        f"/payments/send_receipt_through_mail/?application_id=123&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be ' \
                                        'required and valid.'

    # Invalid college id for send payment receipt through mail
    response = await http_client_test.post(
        f"/payments/send_receipt_through_mail/?application_id=123"
        f"&college_id=1234567890&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input' \
                                        ' or a 24-character hex string'

    # College not found for send payment receipt through mail
    response = await http_client_test.post(
        f"/payments/send_receipt_through_mail/?application_id=123"
        f"&payment_id=test1&reason_type=test&"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Required application id for send payment receipt through mail
    response = await http_client_test.post(
        f"/payments/send_receipt_through_mail/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'Application Id must be ' \
                                        'required and valid.'

    # Invalid application id for send payment receipt through mail
    response = await http_client_test.post(
        f"/payments/send_receipt_through_mail/?application_id=123"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == \
           'Application id must be a 12-byte input or a 24-character ' \
           'hex string'

    # Application not found for send payment receipt through mail
    response = await http_client_test.post(
        f"/payments/send_receipt_through_mail/?"
        f"application_id=123456789012345678901233&college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 404
    assert response.json()['detail'] == 'Application not found.'
