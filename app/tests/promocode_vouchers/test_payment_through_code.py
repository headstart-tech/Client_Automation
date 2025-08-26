"""
This file contains test cases to apply voucher code
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_payment_through_code(http_client_test, test_college_validation, setup_module, application_details,
                                                      college_super_admin_access_token, access_token, test_voucher):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/payment_through_code/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    """
    Bad token for payment through code
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/payment_through_code/?college_id={str(test_college_validation.get('_id'))}"
        f"&application_id={str(application_details.get('_id'))}&code=sample&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    """
    application id required to payment through code
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/payment_through_code/?college_id={str(test_college_validation.get('_id'))}"
        f"&code=sample&code_type=voucher&course_fee=1000&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Application Id must be required and valid."}

    """
    Required college id to payment through code
    """
    response = await http_client_test.post(f"/promocode_vouchers/payment_through_code/"
                                           f"?application_id={str(application_details.get('_id'))}&code=sample&"
                                           f"code_type=voucher&course_fee=1000&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    """
    Invalid college id to payment through code
    """
    response = await http_client_test.post(f"/promocode_vouchers/payment_through_code/?college_id=1234567890"
                                           f"&application_id={str(application_details.get('_id'))}&code=sample&"
                                           f"code_type=voucher&course_fee=1000&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    """
    College not found to payment through code
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/payment_through_code/?college_id=123456789012345678901234&"
        f"application_id={str(application_details.get('_id'))}&code_type=voucher&course_fee=1000"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    """
    Required application id to payment through code
    """
    response = await http_client_test.post(f"/promocode_vouchers/payment_through_code/"
                                           f"?college_id={str(test_college_validation.get('_id'))}&code=sample&"
                                           f"code_type=voucher&course_fee=1000&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Application Id must be required and valid.'

    """
    Required code to payment through code
    """
    response = await http_client_test.post(f"/promocode_vouchers/payment_through_code/"
                                           f"?college_id={str(test_college_validation.get('_id'))}&"
                                           f"application_id={str(application_details.get('_id'))}&code_type=voucher"
                                           f"&course_fee=1000&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Code must be required and valid.'

    """
        Required course fee to pay through code
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/payment_through_code/?college_id={str(test_college_validation.get('_id'))}"
        f"&application_id={str(application_details.get('_id'))}&code_type=voucher&code=sample&"
        f"feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Course Fee must be required and valid.'


    """
    Invalid application id to payment through code
    """
    response = await http_client_test.post(f"/promocode_vouchers/payment_through_code/?"
                                           f"college_id={str(test_college_validation.get('_id'))}&application_id="
                                           f"123456&code=sample&code_type=voucher&course_fee=1000&"
                                           f"feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {access_token}"},
                                           )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Application id must be a 12-byte input or a 24-character hex string'

    """
    Application not found to payment through code
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/payment_through_code/?college_id={str(test_college_validation.get('_id'))}"
        f"&application_id=123456789012345678901234&code=sample&code_type=voucher&course_fee=1000"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 404
    assert response.json()['detail'] == 'Application not found'

    """
    payment through code
    """
    from app.database.configuration import DatabaseConfiguration
    response = await http_client_test.post(
        f"/promocode_vouchers/payment_through_code/?college_id={str(test_college_validation.get('_id'))}"
        f"&application_id={str(application_details.get('_id'))}&code=sam12300&code_type=voucher&course_fee=1000"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    await DatabaseConfiguration().voucher_collection.delete_many({})
    assert response.status_code == 200
    assert response.json()["message"] == "Code applied and payment done successfully"
