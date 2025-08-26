"""
This file contains test cases to update voucher
"""
import datetime

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_voucher(http_client_test, test_college_validation, setup_module, test_voucher, access_token, college_super_admin_access_token):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/update_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&voucher_id={str(test_voucher.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    """
    Bad token to update voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/update_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&voucher_id={str(test_voucher.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    """
    No permission to update voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/update_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&voucher_id={str(test_voucher.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


    """
    voucher id required to update voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/update_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Voucher Id must be required and valid."}

    """
    Required college id to update voucher
    """
    response = await http_client_test.post(f"/promocode_vouchers/update_voucher/?voucher_id="
                                           f"{str(test_voucher.get('_id'))}&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    """
    Invalid college id to update voucher
    """
    response = await http_client_test.post(f"/promocode_vouchers/update_voucher/?college_id=1234567890"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    """
    College not found to update voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/update_voucher/?college_id=123456789012345678901234&voucher_id="
        f"{str(test_voucher.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    """
    Required college id to update voucher
    """
    response = await http_client_test.post(f"/promocode_vouchers/update_voucher/?college_id="
                                           f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Voucher Id must be required and valid.'

    """
    Invalid voucher id to updatee voucher
    """
    response = await http_client_test.post(f"/promocode_vouchers/update_voucher/?college_id="
                                           f"{str(test_college_validation.get('_id'))}&voucher_id=123456"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Voucher id must be a 12-byte input or a 24-character hex string'

    """
    voucher not found to update voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/update_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&voucher_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()['detail'] == 'Voucher not found id: 123456789012345678901234'

    """
    update voucher
    """
    now = datetime.datetime.utcnow()
    response = await http_client_test.post(
        f"/promocode_vouchers/update_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&voucher_id={str(test_voucher.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"name": "test_sample", "status": False}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Updated successfully!"
    from app.database.configuration import DatabaseConfiguration
    check = await DatabaseConfiguration().voucher_collection.find_one({"_id": test_voucher.get("_id")})
    assert check.get("name") == "test_sample"
    await DatabaseConfiguration().voucher_collection.delete_many({})
