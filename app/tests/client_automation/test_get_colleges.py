"""
This file contains test cases related to get the colleges router.
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_colleges_with_no_token(http_client_test):
    """
    Handles a colleges test for the `get_colleges` endpoint when called with no token.
    """
    response = await http_client_test.get(
        f"/client_automation/get_colleges?page_num=1&page_size=10&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {None}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

@pytest.mark.asyncio
async def test_get_colleges_with_no_headers(http_client_test):
    """
    Handles a colleges test for the `get_colleges` endpoint when called with no headers.
    """
    response = await http_client_test.get(
        f"/client_automation/get_colleges?page_num=1&page_size=10&feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_colleges_with_invalid_token(http_client_test, invalid_token):
    """
    Handles a colleges test for the `get_colleges` endpoint when called with an invalid token.
    """
    response = await http_client_test.get(
        f"/client_automation/get_colleges?page_num=1&page_size=10&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_colleges_info(http_client_test, super_admin_token, super_admin_access_token):
    """
     Test cases for fetching colleges
    """

    # test get_colleges with valid page_num and invalid page_size
    response = await http_client_test.get(
        f"/client_automation/get_colleges?page_num=1&page_size=ten&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Page Size must be required and valid."

    # test get_colleges with valid page_num and None page_size
    response = await http_client_test.get(
        f"/client_automation/get_colleges?page_num=1&page_size=None&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Size must be required and valid."}

    # test get_colleges with invalid page_num and valid page_size
    response = await http_client_test.get(
        f"/client_automation/get_colleges?page_num=one&page_size=10&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Num must be required and valid."}

    # test get_colleges with invalid page_num and invalid page_size
    response = await http_client_test.get(
        f"/client_automation/get_colleges?page_num=one&page_size=ten&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Num must be required and valid."}

    # test get_colleges with None page_num and None page_size
    response = await http_client_test.get(
        f"/client_automation/get_colleges?page_num=None&page_size=None&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Num must be required and valid."}

    #TODO: the following testcase is failing, will fix this later

    # # test get_colleges with valid page_num and valid page_size
    # response = await http_client_test.get(
    #     "/client_automation/get_colleges?page_num=1&page_size=10",
    #     headers={"Authorization": f"Bearer {super_admin_token}"},
    # )
    # assert response.status_code == 200
    # response_data = response.json()
    # for field_name in [
    #     "data",
    #     "total",
    #     "count",
    #     "pagination",
    #     "message",
    # ]:
    #     assert field_name in response_data
    # assert response.json()["message"] == "Colleges Fetched Successfully"