"""
This file contains test cases of get counselors list API
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_counselors_list_not_authenticated(
        http_client_test, setup_module, test_month_year,
        test_college_validation):
    """
    Not authenticate for get counselors list
    """
    response = await http_client_test.get(
        f"/counselor/"
        f"get_counselors_list/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_get_counselord_list_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get counselors lit
    """
    response = await http_client_test.get(
        f"/counselor/get_counselors_list/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_counselors_list_required_college_id(http_client_test,
                                                     super_admin_access_token,
                                                     setup_module,
                                                     test_month_year):
    """
    Required college_id for get counselors list
    """
    response = await http_client_test.get(
        f"/counselor/"
        f"get_counselors_list/?feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json() == {
        "detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_get_counselors_list_invalid_id(http_client_test,
                                            test_college_validation,
                                            college_super_admin_access_token,
                                            setup_module, test_month_year):
    """
    Get the details of counselors list using invalid college_id
    """
    response = await http_client_test.get(
        f"/counselor/"
        f"get_counselors_list/?college_id=1234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "College id must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_get_counselors_list(http_client_test, test_college_validation,
                                 college_counselor_access_token,
                                 setup_module, test_month_year):
    """
    Get the counselors list
    """
    response = await http_client_test.get(
        f"/counselor/"
        f"get_counselors_list/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_counselor_access_token}"}, )
    assert response.status_code == 200
    assert response.json()["message"] == "Get counselors list"
