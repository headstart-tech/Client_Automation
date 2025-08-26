import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_account_manager_not_authenticated(http_client_test, setup_module, test_get_account_manager):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"account_manager/get/{test_get_account_manager.get('_id')}?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_get_account_manager_bad_credentials(http_client_test, setup_module, test_get_account_manager):
    """
    Test case -> bad credentials
    """
    response = await http_client_test.get(
        f"account_manager/get/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": "Bearer bad_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_get_account_manager_no_permission(http_client_test, setup_module, test_get_account_manager, access_token):
    """
    Test case -> no permission
    """
    response = await http_client_test.get(
        f"account_manager/get/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_get_account_manager_invalid_id(http_client_test, setup_module, test_get_account_manager, college_super_admin_access_token):
    """
    Test case -> invalid id
    """
    response = await http_client_test.get(
        f"account_manager/get/123?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_account_manager_not_found(http_client_test, setup_module, test_get_account_manager, college_super_admin_access_token):
    """
    Test case -> account manager not found
    """
    response = await http_client_test.get(
        f"account_manager/get/6ba8c7d4c8d4c8d4c8d4c8d4?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_account_manager(http_client_test, setup_module, test_get_account_manager, college_super_admin_access_token):
    """
    Test case -> get account manager
    """
    response = await http_client_test.get(
        f"account_manager/get/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_account_manager_all_not_authenticated(http_client_test, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"account_manager/get_all?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_get_account_manager_all_bad_credentials(http_client_test, setup_module):
    """
    Test case -> bad credentials
    """
    response = await http_client_test.get(
        f"account_manager/get_all?feature_key={feature_key}",
        headers={"Authorization": "Bearer bad_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_get_account_manager_all_no_permission(http_client_test, setup_module, access_token):
    """
    Test case -> no permission
    """
    response = await http_client_test.get(
        f"account_manager/get_all?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_get_account_manager_all(http_client_test, setup_module, college_super_admin_access_token):
    """
    Test case -> get all account manager
    """
    response = await http_client_test.get(
        f"account_manager/get_all?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200

