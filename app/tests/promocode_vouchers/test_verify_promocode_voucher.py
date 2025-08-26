"""
This file contains testcases to verify promocode and vouchers
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_verify_promocode_voucher(http_client_test, test_college_validation, setup_module,
                                                college_super_admin_access_token, test_promocode, access_token, application_details):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/verify_promocode_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    """
    Bad token to verify promocode/voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/verify_promocode_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    """
    course fee required to verify promocode/voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/verify_promocode_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&application_id={str(application_details.get('_id'))}&code=sample&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Course Fee must be required and valid."}

    """
    Required code to verify promocode/voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/verify_promocode_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&course_fee=1000&application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Code must be required and valid."}

    """
    Required college id to verify promocode/voucher
    """
    response = await http_client_test.post(f"/promocode_vouchers/verify_promocode_voucher/?course_fee=1"
                                           f"&code=sample&application_id={str(application_details.get('_id'))}"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    """
        Required application id to verify promocode/voucher
    """
    response = await http_client_test.post(f"/promocode_vouchers/verify_promocode_voucher/"
                                           f"?college_id={str(test_college_validation.get('_id'))}&course_fee=1&"
                                           f"code=sample&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Application Id must be required and valid.'

    """
    Invalid college id to verify promocode/voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/verify_promocode_voucher/?college_id=1234567890&course_fee=1000&code=sample&"
        f"application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
        )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    """
        Invalid application id to verify promocode/voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/verify_promocode_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&application_id=9999&course_fee=1000&code=sample&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Application id must be a 12-byte input or a 24-character hex string'

    """
        Application not found to verify promocode/voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/verify_promocode_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&application_id=123456789012345678901234&code=sample&course_fee=1000&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 404
    assert response.json()['detail'] == 'Application not found'

    """
    College not found to verify promocode/voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/verify_promocode_voucher/?college_id=123456789012345678901234&code=sample&"
        f"course_fee=1000&application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    """
     verify promocode/voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/verify_promocode_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&course_fee=1000&code={test_promocode.get('code')}&application_id={str(application_details.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    assert "status" in response.json()
