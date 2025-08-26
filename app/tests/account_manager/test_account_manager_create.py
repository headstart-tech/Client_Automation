""" This file contains test cases for creating the account manager """
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_account_manager_no_authentication(http_client_test, setup_module, test_new_account_manager):
    """
    Test case -> not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/account_manager/create?feature_key={feature_key}",
        json=test_new_account_manager
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_create_account_manager_bad_credentials(http_client_test, setup_module, test_new_account_manager):
    """
    Test case -> bad credentials
    """
    response = await http_client_test.post(
        f"/account_manager/create?feature_key={feature_key}",
        json=test_new_account_manager,
        headers={"Authorization": "Bearer bad_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_create_account_manager_no_permission(http_client_test, setup_module, test_new_account_manager, access_token):
    """
    Test case -> no permission
    """
    response = await http_client_test.post(
        f"/account_manager/create?feature_key={feature_key}",
        json=test_new_account_manager,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_create_account_manager(http_client_test, setup_module, test_new_account_manager, college_super_admin_access_token, test_get_super_account_manager):
    """
    Test case -> create account manager
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().user_collection.delete_many({'email': test_new_account_manager.get('email')})
    test_new_account_manager["associated_super_account_manager"] = str(test_get_super_account_manager.get("_id"))
    response = await http_client_test.post(
        f"/account_manager/create?feature_key={feature_key}",
        json=test_new_account_manager,
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200

    from app.database.configuration import DatabaseConfiguration
    account_manager = await DatabaseConfiguration().user_collection.find_one(
        {
            "email": test_new_account_manager.get("email")
        }
    )
    assert account_manager is not None

@pytest.mark.asyncio
async def test_create_account_manager_duplicate_email(http_client_test, setup_module, test_new_account_manager, college_super_admin_access_token):
    """
    Test case -> create account manager with duplicate email
    """
    response = await http_client_test.post(
        f"/account_manager/create?feature_key={feature_key}",
        json=test_new_account_manager,
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Email or Mobile Number already exists"}

@pytest.mark.asyncio
async def test_create_account_manager_duplicate_mobile_number(http_client_test, setup_module, test_new_account_manager, college_super_admin_access_token):
    """
    Test case -> create account manager with duplicate mobile number
    """
    test_new_account_manager['email'] = "new@email.com"
    response = await http_client_test.post(
        f"/account_manager/create?feature_key={feature_key}",
        json=test_new_account_manager,
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Email or Mobile Number already exists"}