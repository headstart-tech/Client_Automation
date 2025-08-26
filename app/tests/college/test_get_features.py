"""
This file contains test cases related to get features
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_features_not_authenticated(http_client_test, setup_module):
    """
    Test case -> not authenticated if user not logged in
    """
    response = await http_client_test.get(f"/college/features/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_features_bad_credentials(http_client_test, setup_module):
    """
    Test case -> bad token for get features data
    """
    response = await http_client_test.get(
        f"/college/features/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_features_required_college_id(
        http_client_test, super_admin_access_token, setup_module
):
    """
    Test case -> required college id for get features data
    """
    response = await http_client_test.get(
        f"/college/features/?feature_key={feature_key}", headers={"Authorization": f"Bearer {super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}


@pytest.mark.asyncio
async def test_get_features_invalid_college_id(http_client_test, test_college_validation,
                                               super_admin_access_token):
    """
    Test case -> invalid college id for get features data
    """
    response = await http_client_test.get(
        f"/college/features/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_test_get_features_college_not_found(http_client_test, test_college_validation,
                                                   super_admin_access_token):
    """
    Test case -> college not found for get features data
    """
    response = await http_client_test.get(
        f"/college/features/?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_get_features_no_permission(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    Test case -> no permission for get features data
    """
    response = await http_client_test.get(
        f"/college/features/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {'detail': 'Not enough permissions'}


@pytest.mark.asyncio
async def test_get_features(
        http_client_test, super_admin_access_token, setup_module, test_college_validation
):
    """
    Test case -> Get features data
    """
    # Feature data not found
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.update_one({"_id": test_college_validation.get('_id')},
                                                                {'$unset': {'features': True}})
    response = await http_client_test.get(
        f"/college/features/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['features'] == {}

    # Feature data found
    await DatabaseConfiguration().college_collection.update_one({"_id": test_college_validation.get('_id')},
                                                                {'$set': {'features': {"navbar_search": True}}})
    response = await http_client_test.get(
        f"/college/features/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['features'] == {"navbar_search": True}
