"""
This file contains test cases related to API route/endpoint for manual capture
payment.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_cases_of_manual_capture_payment(
        http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token, super_admin_access_token,
        access_token, application_details
        ):
    """
    Different test cases of manual capture payment.

    Params:\n
        http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
             after test case execution completed.
        test_college_validation: A fixture which create college if not exist
            and return college data.
        college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.
        super_admin_access_token: A fixture which create super admin if not exist
            and return access token for super admin.
        test_student_validation: A fixture which create student if not exist
            and return student data.
        application_details: A fixture which create application if not exist
            and return application data.

    Assertions:\n
        response status code and json message.
    """
    # Check authentication send wrong token
    response = await http_client_test.post(
        f"/payments/manual_capture/?feature_key={feature_key}",
        headers={"Authorization": "wrong token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    college_id = str(test_college_validation.get('_id'))
    # Wrong token for manual capture payment
    response = await http_client_test.post(
        f"/payments/manual_capture/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # No permission for manual capture payment
    response = await http_client_test.post(
        f"/payments/manual_capture/?application_id=123"
        f"&payment_id=test1&reason_type=test&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"

    # Manual capture payment
    response = await http_client_test.post(
        f"/payments/manual_capture/?application_id="
        f"{str(application_details.get('_id'))}"
        f"&payment_id=test1&reason_type=test&college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "Payment is captured through "
                                          "offline way."}

    # Required college id for manual capture payment
    response = await http_client_test.post(
        f"/payments/manual_capture/?application_id=123"
        f"&payment_id=test1&reason_type=test&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be ' \
                                        'required and valid.'

    # Invalid college id for manual capture payment
    response = await http_client_test.post(
        f"/payments/manual_capture/?application_id=123"
        f"&payment_id=test1&reason_type=test&college_id=1234567890&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input' \
                                        ' or a 24-character hex string'

    # College not found for manual capture payment
    response = await http_client_test.post(
        f"/payments/manual_capture/?application_id=123"
        f"&payment_id=test1&reason_type=test&"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Required application id for manual capture payment
    response = await http_client_test.post(
        f"/payments/manual_capture/?college_id={college_id}"
        f"&payment_id=test1&reason_type=test&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'Application Id must be ' \
                                        'required and valid.'

    # Invalid application id for manual capture payment
    response = await http_client_test.post(
        f"/payments/manual_capture/?application_id=123"
        f"&payment_id=test1&reason_type=test&college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == \
           'Application id `123` must be a 12-byte input or a 24-character ' \
           'hex string'

    # Application not found for manual capture payment
    response = await http_client_test.post(
        f"/payments/manual_capture/?application_id=123456789012345678901233"
        f"&payment_id=test1&reason_type=test&college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 404
    assert response.json()['detail'] == 'Application not found id: ' \
                                        '123456789012345678901233'

    # Required payment id for manual capture payment
    response = await http_client_test.post(
        f"/payments/manual_capture/?college_id={college_id}"
        f"&application_id=test1&reason_type=test&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'Payment Id must be ' \
                                        'required and valid.'

    # Required reason type for manual capture payment
    response = await http_client_test.post(
        f"/payments/manual_capture/?college_id={college_id}"
        f"&application_id=test1&payment_id=test&feature_key={feature_key}",
        headers={"Authorization":
                     f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == 'Reason Type must be ' \
                                        'required and valid.'
