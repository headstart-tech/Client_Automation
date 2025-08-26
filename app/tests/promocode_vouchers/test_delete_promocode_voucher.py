"""
This file contains test cases to delete promocode/voucher
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_promocode_voucher(http_client_test, test_college_validation, setup_module, test_voucher, access_token, college_super_admin_access_token):
    """
    Not authenticated if user not logged in
    """
    body = [str(test_voucher.get("_id"))]
    response = await http_client_test.post(
        f"/promocode_vouchers/delete_promocode_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    """
    Bad token to delete promocode/voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/delete_promocode_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    """
    No permission to delete promocode/voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/delete_promocode_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&promocode=false&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=body
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    """
    promocode (bool) required to delete promocode/voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/delete_promocode_voucher/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=body
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Promocode must be required and valid."}

    """
    Required college id to delete promocode/voucher
    """
    response = await http_client_test.post(f"/promocode_vouchers/delete_promocode_voucher/"
                                           f"?promcode=false&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           json=body
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    """
    Invalid college id to delete promocode/voucher
    """
    response = await http_client_test.post(f"/promocode_vouchers/delete_promocode_voucher/"
                                           f"?college_id=1234567890&promocode=false&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           json=body
                                           )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    """
    College not found to delete promocode/voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/delete_promocode_voucher/"
        f"?college_id=123456789012345678901234&voucher_id={str(test_voucher.get('_id'))}&promocode=false"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=body
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    """
    Required list of  ids to delete promocode/voucher
    """
    response = await http_client_test.post(f"/promocode_vouchers/delete_promocode_voucher/"
                                           f"?college_id={str(test_college_validation.get('_id'))}&promocode=true"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Body must be required and valid.'

    """
    Invalid id to delete promocode/voucher
    """
    response = await http_client_test.post(f"/promocode_vouchers/delete_promocode_voucher/"
                                           f"?college_id={str(test_college_validation.get('_id'))}&promocode=true"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           json=["1111"]
                                           )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Id must be a 12-byte input or a 24-character hex string'

    """
    delete promocode/voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/delete_promocode_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&promocode=false&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=body
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully deleted vouchers!"
    from app.database.configuration import DatabaseConfiguration
    check = await DatabaseConfiguration().voucher_collection.find_one({"_id": test_voucher.get("_id")})
    assert check is None
