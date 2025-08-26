"""
This file contains test cases for create voucher
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_voucher_not_authenticated(http_client_test, test_college_validation, setup_module,
                                                test_counselor_validation, test_course_validation,
                                                college_counselor_access_token, college_super_admin_access_token
                                                ):
    """
    Not authenticated if user not logged in
    """
    payload = {
        "name": "string",
        "quantity": 10,
        "cost_per_voucher": 100,
        "duration": {
            "start_date": "2024-02-18",
            "end_date": "2024-03-20"
        },
        "program_name":
            [
                {
                    "course_id": str(test_course_validation.get("_id")),
                    "spec_name": "sample"
                }
            ],
        "assign_to": str(test_counselor_validation.get("_id"))
    }
    response = await http_client_test.post(
        f"/promocode_vouchers/create_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    """
    Bad token to create voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/create_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    """
    No permission to create voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/create_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json= payload
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    """
    Body required to create voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/create_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}

    """
    Required mandetory fields to create voucher
    """
    payload.pop("name")
    response = await http_client_test.post(
        f"/promocode_vouchers/create_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json= payload
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Name must be required and valid."}
    payload["name"] = "string"

    """
    Required college id to create promoocode
    """
    response = await http_client_test.post(f"/promocode_vouchers/create_voucher/?feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           json= payload
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    """
    Invalid college id to create voucher
    """
    response = await http_client_test.post(f"/promocode_vouchers/create_voucher/?college_id=1234567890"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           json= payload
                                           )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    """
    College not found to create voucher
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/create_voucher/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json= payload
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    """
    create voucher
    """
    from app.database.configuration import DatabaseConfiguration
    response = await http_client_test.post(
        f"/promocode_vouchers/create_voucher/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json= payload
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Created voucher successfully!"
    check = await DatabaseConfiguration().voucher_collection.find_one({})
    assert check.get("name") == payload.get("name")
    await DatabaseConfiguration().voucher_collection.delete_many({})
