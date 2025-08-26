"""
This file contains test cases related to client automation router
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_college_detail_info(
    http_client_test,
    setup_module,
    college_super_admin_access_token,
    access_token,
    test_college_validation,
    test_super_admin_validation,
    test_get_client,
):
    """
    Test cases for Bench Marking
    """
    # Not authenticated
    response = await http_client_test.post(f"/client_automation/add_college?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for Bench Marking
    response = await http_client_test.post(
        f"/client_automation/add_college?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for Bench Marking
    response = await http_client_test.post(
        f"/client_automation/add_college?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Name must be required and valid."}

    response = await http_client_test.post(
        f"/client_automation/add_college?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "name": "test1733",
            "email": "user@gmail.com",
            "phone_number": "8787676565",
            "associated_client": str(test_get_client.get("_id")),
            "address": {
                "address_line_1": "string",
                "address_line_2": "string",
                "country_code": "IN",
                "state_code": "UP",
                "city_name": "mumbai",
            },
        },
    )
    assert response.status_code == 422
    try:
        assert response.json()["detail"] == "Wrong address"
    except:
        assert response.json()["detail"] == "College already exists"

    # Invalid Phone Number for Bench Marking
    response = await http_client_test.post(
        f"/client_automation/add_college?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "name": "test1733",
            "email": "user@gmail.com",
            "phone_number": "87876765652",
            "associated_client": str(test_get_client.get("_id")),
            "address": {
                "address_line_1": "string",
                "address_line_2": "string",
                "country_code": "IN",
                "state_code": "UP",
                "city_name": "Mathura",
            },
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Phone Number must be required and valid."

    # TODO: need to update testcase, according to the updated api.
    # # College Creation for Bench Marking
    # response = await http_client_test.post(
    #     f"/client_automation/add_college?feature_key={feature_key}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json={
    #         "name": "test1733",
    #         "email": "user@gmail.com",
    #         "phone_number": "8787676565",
    #         "associated_client": str(test_get_client.get("_id")),
    #         "address": {
    #             "address_line_1": "string",
    #             "address_line_2": "string",
    #             "country_code": "IN",
    #             "state_code": "UP",
    #             "city_name": "Mathura",
    #         },
    #     },
    # )
    # assert response.status_code == 200
    # assert response.json()["message"] == "College create successfully."

    # College Already Exists for Bench Marking
    response = await http_client_test.post(
        f"/client_automation/add_college?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "name": "test1733",
            "email": "user@gmail.com",
            "phone_number": "8787676565",
            "associated_client": str(test_get_client.get("_id")),
            "address": {
                "address_line_1": "string",
                "address_line_2": "string",
                "country_code": "IN",
                "state_code": "UP",
                "city_name": "Mathura",
            },
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "College already exists"
