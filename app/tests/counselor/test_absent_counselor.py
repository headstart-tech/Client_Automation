"""
This file contains test cases for get details of absent counselor
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_absent_counselor_not_authenticated(http_client_test, setup_module):
    """
    Not authenticate for get details of absent counselor
    """
    response = await http_client_test.get(
        f"/counselor/absent?counselor_id=62bfd13a5ce8a398ad101bd7&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_get_absent_counselor_required_college_id(http_client_test, super_admin_access_token, absent_counselor,
                                                        setup_module):
    """
    Required college_id for get details of absent counselor
    """
    response = await http_client_test.get(f"/counselor/absent?counselor_id={str(absent_counselor.get('counselor_id'))}"
                                          f"&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_get_absent_counselor_no_permission(http_client_test, test_college_validation, super_admin_access_token,
                                                  absent_counselor, setup_module):
    """
    Not permission for get details of absent counselor
    """
    response = await http_client_test.get(
        f"/counselor/absent?counselor_id={str(absent_counselor.get('counselor_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_absent_counselor_invalid_id(http_client_test, test_college_validation,
                                               college_super_admin_access_token, setup_module):
    """
    Get the details of absent counselor using invalid counselor_id
    """
    response = await http_client_test.get(
        f"/counselor/absent?counselor_id=62bfd13a5ce8a398ad101bd"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 422
    assert response.json() == {"detail": "counselor_id must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_get_absent_counselor_not_found(http_client_test, test_college_validation,
                                              college_super_admin_access_token, setup_module):
    """
    Counselor not found in db for get details of absent counselor
    """
    response = await http_client_test.get(
        f"/counselor/absent?counselor_id=62bfd13a5ce8a398ad101bd8"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 404
    assert response.json() == {"detail": "Counselor not found"}


@pytest.mark.asyncio
async def test_get_absent_counselor(http_client_test, test_college_validation, college_super_admin_access_token,
                                    absent_counselor, setup_module):
    """
    Get the details of absent counselor
    """
    response = await http_client_test.get(
        f"/counselor/absent?counselor_id={str(absent_counselor.get('counselor_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
