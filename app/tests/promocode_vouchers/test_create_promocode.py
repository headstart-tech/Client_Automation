"""
This file contains test cases for create promocode
"""
import pytest

from app.tests.conftest import access_token, user_feature_data

feature_key = user_feature_data()

payload = {
    "name": "test",
    "discount": 50,
    "code": "test_sample",
    "units": 0,
    "duration": {
        "start_date": "2024-02-12",
        "end_date": "2024-03-12"
    }
}

@pytest.mark.asyncio
async def test_create_promocode_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/create_promocode/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_promocode_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token to create promocode
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/create_promocode/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_create_promocode_no_permission(http_client_test, test_college_validation, setup_module, college_counselor_access_token):
    """
    No permission to create promocode
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/create_promocode/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json= payload
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_create_promocode_required_body(
        http_client_test, test_college_validation, access_token, setup_module, college_super_admin_access_token
):
    """
    Body required to create promocode
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/create_promocode/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}


@pytest.mark.asyncio
async def test_create_promocode_mandetory_field_check(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required mandetory fields to create promocode
    """
    payload.pop("code")
    response = await http_client_test.post(
        f"/promocode_vouchers/create_promocode/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json= payload
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Code must be required and valid."}
    payload["code"] = "test_sample"


@pytest.mark.asyncio
async def test_create_promocode_required_college_id(http_client_test, test_college_validation,
                                                        college_super_admin_access_token):
    """
    Required college id to create promoocode
    """
    response = await http_client_test.post(f"/promocode_vouchers/create_promocode/?feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           json= payload
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'


@pytest.mark.asyncio
async def test_create_promocode_invalid_college_id(http_client_test, test_college_validation,
                                                       college_super_admin_access_token):
    """
    Invalid college id to create promocode
    """
    response = await http_client_test.post(f"/promocode_vouchers/create_promocode/?college_id=1234567890"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           json= payload
                                           )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_create_promocode_college_not_found(http_client_test, test_college_validation,
                                                      college_super_admin_access_token):
    """
    College not found to create promocode
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/create_promocode/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json= payload
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_create_promocode(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, application_details
):
    """
    create promocode
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().promocode_collection.delete_many({})
    response = await http_client_test.post(
        f"/promocode_vouchers/create_promocode/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json= payload
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Successfully created promocode!"
    check = await DatabaseConfiguration().promocode_collection.find_one({})
    assert check.get("name") == payload.get("name")
    await DatabaseConfiguration().promocode_collection.delete_many({})

@pytest.mark.asyncio
async def test_create_promocode_already_exists(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, application_details
):
    """
    promocode already exists
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().promocode_collection.delete_many({})
    response = await http_client_test.post(
        f"/promocode_vouchers/create_promocode/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json= payload
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully created promocode!"

    response = await http_client_test.post(
        f"/promocode_vouchers/create_promocode/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=payload
    )

    assert response.json()["detail"] == "Promo code already exists."
    await DatabaseConfiguration().promocode_collection.delete_many({})
