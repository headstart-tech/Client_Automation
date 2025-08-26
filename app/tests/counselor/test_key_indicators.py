"""
This file contains test cases for get key indicators
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_key_indicators_not_authenticated(http_client_test, setup_module):
    """
    Not authenticate for get key indicators
    """
    response = await http_client_test.get(f"/counselor/key_indicators/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_get_key_indicators_required_college_id(http_client_test, super_admin_access_token,
                                                        setup_module,):
    """
    Required college_id for get key indicators
    """
    response = await http_client_test.get(f"/counselor/key_indicators/?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_get_key_indicators_no_permission(http_client_test, test_college_validation, super_admin_access_token,
                                                   setup_module):
    """
    Not permission for get key indicators
    """
    response = await http_client_test.get(
        f"/counselor/key_indicators/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_key_indicators(http_client_test, test_college_validation,college_counselor_access_token ,
                                    setup_module):
    """
    Get the details of key indicators
    """
    response = await http_client_test.get(
        f"/counselor/key_indicators/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"}, )
    assert response.status_code == 200
    assert response.json()["message"] == "Get key indicators"
