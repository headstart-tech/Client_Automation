"""
This file contains testcases to get quick view details
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_quick_view(http_client_test, test_college_validation, setup_module, college_super_admin_access_token):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_quick_view/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    """
    Bad token to get quick view details
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_quick_view/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


    """
    Required college id to get quick view details
    """
    response = await http_client_test.post(f"/promocode_vouchers/get_quick_view/?feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    """
    Invalid college id to get quick view details
    """
    response = await http_client_test.post(f"/promocode_vouchers/get_quick_view/?college_id=1234567890"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
                                           )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    """
    College not found to get quick view details
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_quick_view/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


    """
    get quick view details
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_quick_view/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=10&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Get quick view details!"
