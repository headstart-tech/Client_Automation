import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_deactivate_AM_not_authenticated(http_client_test, setup_module, test_get_account_manager):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"account_manager/deactivate/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_deactivate_AM_bad_credentials(http_client_test, setup_module, test_get_account_manager):
    """
    Test case -> bad credentials
    """
    response = await http_client_test.put(
        f"account_manager/deactivate/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": "Bearer bad_token"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_deactivate_AM_no_permission(http_client_test, setup_module, test_get_account_manager, access_token):
    """
    Test case -> no permission
    """
    response = await http_client_test.put(
        f"account_manager/deactivate/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_deactivate_AM_have_clients(http_client_test, setup_module, test_get_account_manager, college_super_admin_access_token):
    """
    Test case -> Account Manager have Clients
    """
    response = await http_client_test.put(
        f"account_manager/deactivate/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Account Manager have Allocated Clients"}

@pytest.mark.asyncio
async def test_deactivate_AM(http_client_test, setup_module, college_super_admin_access_token, test_new_account_manager):
    """
    Test case -> Account Manager Deactivation
    """
    from app.database.configuration import DatabaseConfiguration
    test_new_account_manager["email"] = "2@mail.com"
    test_new_account_manager["mobile_number"] = "8523697415"
    # create an Account Manager
    acc_mng_resp = await http_client_test.post(
        f"/account_manager/create?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_new_account_manager
    )
    AM_ID = acc_mng_resp.json().get("account_manager_id")
    response = await http_client_test.put(
        f"account_manager/deactivate/{AM_ID}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    updated_account_manager = await DatabaseConfiguration().user_collection.find_one({"email": "2@mail.com"})
    assert updated_account_manager.get('is_activated') == False

@pytest.mark.asyncio
async def test_deactivate_AM_already_deactiavted(http_client_test, setup_module, college_super_admin_access_token):
    """
    Test case -> Account Manager Already Deactivated
    """
    from app.database.configuration import DatabaseConfiguration
    account_manager = await DatabaseConfiguration().user_collection.find_one({"email": "2@mail.com"})
    response = await http_client_test.put(
        f"account_manager/deactivate/{str(account_manager.get('_id'))}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Account Manager is already Deactivated"}

@pytest.mark.asyncio
async def test_activate_AM_not_authenticated(http_client_test, setup_module, test_get_account_manager):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"account_manager/activate/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_activate_AM_bad_credentials(http_client_test, setup_module, test_get_account_manager):
    """
    Test case -> bad credentials
    """
    response = await http_client_test.put(
        f"account_manager/activate/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": "Bearer bad_token"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_activate_AM_no_permission(http_client_test, setup_module, test_get_account_manager, access_token):
    """
    Test case -> no permission
    """
    response = await http_client_test.put(
        f"account_manager/activate/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_activate_AM_already_activated(http_client_test, setup_module, test_get_account_manager, college_super_admin_access_token):
    """
    Test case -> Account Manager already activated
    """
    response = await http_client_test.put(
        f"account_manager/activate/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Account Manager is already Active"}

@pytest.mark.asyncio
async def test_activate_AM(http_client_test, setup_module, test_get_account_manager, college_super_admin_access_token):
    """
    Test case -> Account Manager activated
    """
    from app.database.configuration import DatabaseConfiguration
    account_manager = await DatabaseConfiguration().user_collection.find_one({"email": "2@mail.com"})
    response = await http_client_test.put(
        f"account_manager/activate/{str(account_manager.get('_id'))}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    updated_account_manager = await DatabaseConfiguration().user_collection.find_one({"email": "2@email.com"})
    assert updated_account_manager.get('is_activated') == True