"""
This file contains test cases for manual counselor allocation
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_list_of_counselor_not_found(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    Counselor not found when try to fetch counselors data
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().user_collection.delete_many({"role.role_name": "college_counselor"})
    response = await http_client_test.get(
        f"/counselor/college_counselor_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
    assert response.json()["data"][0] == []


@pytest.mark.asyncio
async def test_get_list_of_counselor_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated for get counselors data
    """
    response = await http_client_test.get(
        f"/counselor/college_counselor_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": "wrong bearer"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_list_of_counselor(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
        test_counselor_validation
):
    """
    Get counselors data
    """
    response = await http_client_test.get(
        f"/counselor/college_counselor_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
    assert response.json()["data"][0] is not None


@pytest.mark.asyncio
async def test_get_list_of_counselor_except_holiday_counselor(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
        test_counselor_validation
):
    """
    Get counselors data except today holiday counselors
    """
    response = await http_client_test.get(
        f"/counselor/college_counselor_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&holiday=true&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
    assert response.json()["data"][0] is not None


@pytest.mark.asyncio
async def test_get_list_of_counselor_required_college_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
        test_counselor_validation
):
    """
    Required college id for get counselors data
    """
    response = await http_client_test.get(
        f"/counselor/college_counselor_list/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_get_list_of_counselor_invalid_college_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
        test_counselor_validation
):
    """
    Invalid college id for get counselors data
    """
    response = await http_client_test.get(
        f"/counselor/college_counselor_list/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_get_list_of_counselor_college_not_found(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
        test_counselor_validation
):
    """
    College not found when try to get counselors data
    """
    response = await http_client_test.get(
        f"/counselor/college_counselor_list/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}
