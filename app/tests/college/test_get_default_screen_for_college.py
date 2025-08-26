"""
This File Contains Test Cases For Get Default Screen For College
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_default_screen_for_college_no_authentication(http_client_test, setup_module):
    """
    Test case -> not authenticated if user not logged in
    """
    response = await http_client_test.get(f"/college/default_screen_by_client?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_get_default_screen_for_college_bad_credentials(http_client_test, setup_module):
    """
    Test case -> request with bad credentials
    """

    response = await http_client_test.get(
        f"/college/default_screen_by_client?feature_key={feature_key}",
        headers={"Authorization": "Bearer bad_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_get_default_screen_for_college_no_permission(http_client_test, setup_module, access_token):
    """
    Test case -> request with no permission
    """
    response = await http_client_test.get(
        f"/college/default_screen_by_client?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_get_default_screen_for_college(http_client_test, setup_module, college_super_admin_access_token, client_screen_data):
    """
    Test case -> get default screen for college
    """
    from bson import ObjectId
    client_screen_data.update(
        {
            "client_id": ObjectId("67e674235128e7b3960907fb"),
            "screen_type": "client_screen"
        }
    )
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().master_screens.insert_one(client_screen_data)
    response = await http_client_test.get(
        f"/college/default_screen_by_client?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
