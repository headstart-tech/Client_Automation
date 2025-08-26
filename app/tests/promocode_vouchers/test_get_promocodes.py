"""
This file contains testcases to get list of promo-codes.
"""
import pytest
from app.tests.conftest import access_token
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_promocodes(http_client_test, test_college_validation, setup_module,
                              college_super_admin_access_token, test_promocode):
    """
    Different test cases of get list of promo-codes.

    Params:
        - http_client_test: A fixture which return AsyncClient object.
            Useful for test API with particular method.
        - test_college_validation: A fixture which create college if not exist
            and return college data.
        - setup_module: A fixture which upload necessary data in the db before
            test cases start running/executing and delete data from collection
            after test case execution completed.
        - college_super_admin_access_token: A fixture which create college super
            admin if not exist and return access token of college super admin.
        - test_promocode: A fixture which add promo-code details in DB if not exist
            and return promo-code data.

    Assertions:\n
        response status code and json message.
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/promocode_vouchers/get_promocodes/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token to get promo-codes
    response = await http_client_test.post(
        f"/promocode_vouchers/get_promocodes/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id to get promo-codes
    response = await http_client_test.post(f"/promocode_vouchers/get_promocodes/?page_num=1&page_size=10"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    # Invalid college id to get promo-codes
    response = await http_client_test.post(
        f"/promocode_vouchers/get_promocodes/?college_id=1234567890&page_num=1&page_size=10"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
        )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    # College not found to get promo-codes
    response = await http_client_test.post(
        f"/promocode_vouchers/get_promocodes/?college_id=123456789012345678901234&page_num=1"
        f"&page_size=10&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    def validate_successful_response(response_info):
        response_data = response_info.json()["data"][0]
        assert response_info.json()["message"] == "Get all promocodes"
        for key in ["_id", "code", "name", "discount", "applied_count", "total_units", "available", "start_date",
                    "end_date", "status", "estimated_cost", "created_at", "data_segment_ids"]:
            assert key in response_data

    # Get promo-codes with pagination
    response = await http_client_test.post(
        f"/promocode_vouchers/get_promocodes/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=10&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    validate_successful_response(response)

    def validate_download_successful_response(response_info):
        assert response.status_code == 200
        assert "file_url" in response.json()
        assert response.json()["message"] == "File downloaded successfully."

    # Download promo-codes
    response = await http_client_test.post(
        f"/promocode_vouchers/get_promocodes/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=10&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"download": True}
    )
    validate_download_successful_response(response)

    # Get promo-codes without pagination
    response = await http_client_test.post(
        f"/promocode_vouchers/get_promocodes/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    validate_successful_response(response)

    # Download promo-codes without pagination
    response = await http_client_test.post(
        f"/promocode_vouchers/get_promocodes/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"download": True}
    )
    validate_download_successful_response(response)

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().promocode_collection.delete_many({})
    # Get promo-codes without pagination
    response = await http_client_test.post(
        f"/promocode_vouchers/get_promocodes/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["data"] == []

    # Get promo-codes with pagination
    response = await http_client_test.post(
        f"/promocode_vouchers/get_promocodes/?college_id={str(test_college_validation.get('_id'))}&"
        f"page_num=1&page_size=10&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["data"] == []
