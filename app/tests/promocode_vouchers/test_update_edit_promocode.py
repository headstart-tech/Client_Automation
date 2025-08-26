"""
This file contains test cases to update/ edit promocode
"""
import datetime

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_promocode_not_authenticated(http_client_test, test_college_validation, setup_module, test_promocode):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/update_promocode/?college_id={str(test_college_validation.get('_id'))}"
        f"&_id={str(test_promocode.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_promocode_bad_credentials(http_client_test, test_college_validation, setup_module, test_promocode):
    """
    Bad token to update promocode
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/update_promocode/?college_id={str(test_college_validation.get('_id'))}&"
        f"_id={str(test_promocode.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_update_promocode_no_permission(http_client_test, test_college_validation, setup_module, college_counselor_access_token, test_promocode, access_token):
    """
    No permission to update promocode
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/update_promocode/?college_id={str(test_college_validation.get('_id'))}&"
        f"_id={str(test_promocode.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_update_promocode_required_id(
        http_client_test, test_college_validation, access_token, setup_module, college_super_admin_access_token
):
    """
    promocode id required to update promocode
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/update_promocode/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": " Id must be required and valid."}


@pytest.mark.asyncio
async def test_update_promocode_required_college_id(http_client_test, test_college_validation,
                                                        college_super_admin_access_token, test_promocode):
    """
    Required college id to update promoocode
    """
    response = await http_client_test.post(f"/promocode_vouchers/update_promocode/?"
                                           f"_id={str(test_promocode.get('_id'))}&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'


@pytest.mark.asyncio
async def test_update_promocode_invalid_college_id(http_client_test, test_college_validation,
                                                       college_super_admin_access_token):
    """
    Invalid college id to update promocode
    """
    response = await http_client_test.post(f"/promocode_vouchers/update_promocode/"
                                           f"?college_id=1234567890&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_update_promocode_college_not_found(http_client_test, test_college_validation,
                                                      college_super_admin_access_token, test_promocode):
    """
    College not found to update promocode
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/update_promocode/?college_id=123456789012345678901234&"
        f"_id={str(test_promocode.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

@pytest.mark.asyncio
async def test_update_promocode_required_promocode_id(http_client_test, test_college_validation,
                                                        college_super_admin_access_token, test_promocode):
    """
    Required college id to update promoocode
    """
    response = await http_client_test.post(f"/promocode_vouchers/update_promocode/?"
                                           f"college_id={str(test_college_validation.get('_id'))}"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == ' Id must be required and valid.'


@pytest.mark.asyncio
async def test_update_promocode_invalid_promocode_id(http_client_test, test_college_validation,
                                                       college_super_admin_access_token):
    """
    Invalid promocode id to updatee promocode
    """
    response = await http_client_test.post(f"/promocode_vouchers/update_promocode/?"
                                           f"college_id={str(test_college_validation.get('_id'))}&_id=123456"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Promocode id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_update_promocode_not_found(http_client_test, test_college_validation,
                                                      college_super_admin_access_token, test_promocode):
    """
    promocode not found to update promocode
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/update_promocode/?college_id={str(test_college_validation.get('_id'))}"
        f"&_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()['detail'] == 'Promocode not found id: 123456789012345678901234'


@pytest.mark.asyncio
async def test_update_promocode(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, application_details, test_promocode
):
    """
    update promocode
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/update_promocode/?college_id={str(test_college_validation.get('_id'))}"
        f"&_id={str(test_promocode.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json= {"units": 20}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Updated successfully!"
    from app.database.configuration import DatabaseConfiguration
    check = await DatabaseConfiguration().promocode_collection.find_one({"_id": test_promocode.get("_id")})
    assert check.get("units") == 20

@pytest.mark.asyncio
async def test_update_promocode_with_condition_match(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, application_details, test_promocode
):
    """
    update promocode check conditions
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().promocode_collection.update_one({"_id": test_promocode.get("_id")},
                                                                  {"$set": {
                                                                      "duration.start_date": datetime.datetime.utcnow(),
                                                                      "units": 5, "applied_count": 3}}
                                                                  )
    response = await http_client_test.post(
        f"/promocode_vouchers/update_promocode/?college_id={str(test_college_validation.get('_id'))}"
        f"&_id={str(test_promocode.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json= {"units": 2}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Units cannot be less than applied count"
