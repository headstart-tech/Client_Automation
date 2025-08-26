"""
This file contains testcases to get voucher details
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_voucher_details(http_client_test, test_college_validation, setup_module, college_super_admin_access_token, test_voucher):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_voucher_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    """
    Bad token to get voucher details
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_voucher_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&voucher_id={str(test_voucher.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    """
    page num required to get voucher details
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_voucher_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&voucher_id={str(test_voucher.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Num must be required and valid."}

    """
    Required page size to get voucher details
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_voucher_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&voucher_id={str(test_voucher.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Size must be required and valid."}

    """
    Required college id to get voucher details
    """
    response = await http_client_test.post(f"/promocode_vouchers/get_voucher_details/?page_num=1&page_size=10"
                                           f"&voucher_id={str(test_voucher.get('_id'))}&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    """
    Invalid college id to get voucher details
    """
    response = await http_client_test.post(f"/promocode_vouchers/get_voucher_details/?college_id=1234567890"
                                           f"&page_num=1&page_size=10&voucher_id={str(test_voucher.get('_id'))}"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
                                           )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    """
    College not found to get voucher details
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_voucher_details/?college_id=123456789012345678901234&page_num=1&page_size=10"
        f"&voucher_id={str(test_voucher.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    """
        Required voucher id to get voucher details
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_voucher_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Voucher Id must be required and valid.'

    """
    Invalid voucher id to get voucher details
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_voucher_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&voucher_id=123456&page_num=1&page_size=10&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Voucher id must be a 12-byte input or a 24-character hex string'

    """
    voucher not found to get voucher details
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_voucher_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&voucher_id=123456789012345678901234&page_num=1&page_size=10&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()['detail'] == 'Voucher not found id: 123456789012345678901234'

    """
    get voucher details
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_voucher_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=10&voucher_id={str(test_voucher.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Get voucher details"
