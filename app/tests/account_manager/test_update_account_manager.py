import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_update_account_manager_not_authenticated(http_client_test, setup_module,
                                                        test_get_account_manager,
                                                        test_update_account_manager):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"account_manager/update/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        json=test_update_account_manager
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_account_manager_bad_credentials(http_client_test, setup_module,
                                                      test_get_account_manager,
                                                      test_update_account_manager):
    """
    Test case -> bad credentials
    """
    response = await http_client_test.put(
        f"account_manager/update/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": "Bearer bad_token"},
        json=test_update_account_manager
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_update_account_manager_no_permission(http_client_test, setup_module,
                                                    test_get_account_manager, access_token,
                                                    test_update_account_manager):
    """
    Test case -> no permission
    """
    response = await http_client_test.put(
        f"account_manager/update/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=test_update_account_manager
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_update_account_manager(http_client_test, setup_module, test_get_account_manager,
                                      college_super_admin_access_token,
                                      test_update_account_manager):
    """
    Test case -> success
    """
    response = await http_client_test.put(
        f"account_manager/update/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_update_account_manager
    )
    assert response.status_code == 200
    from app.database.configuration import DatabaseConfiguration
    account_manager = await DatabaseConfiguration().user_collection.find_one(
        {"_id": test_get_account_manager.get('_id')})
    assert account_manager.get("email") == test_update_account_manager.get("email")


@pytest.mark.asyncio
async def test_change_super_account_manager_not_authenticated(http_client_test, setup_module,
                                                              test_get_account_manager):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"account_manager/change_super_account_manager/{test_get_account_manager.get('_id')}"
        f"?feature_key={feature_key}",
        json={"super_account_manager_id": str(test_get_account_manager.get('_id'))}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_change_super_account_manager_bad_credentials(http_client_test, setup_module,
                                                            test_get_account_manager):
    """
    Test case -> bad credentials
    """
    response = await http_client_test.put(
        "account_manager/change_super_account_manager/"
        f"{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": "Bearer bad_token"},
        json={"super_account_manager_id": str(test_get_account_manager.get('_id'))}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_change_super_account_manager_no_permission(http_client_test, setup_module,
                                                          test_get_account_manager, access_token):
    """
    Test case -> no permission
    """
    response = await http_client_test.put(
        f"account_manager/change_super_account_manager/"
        f"{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"super_account_manager_id": str(test_get_account_manager.get('_id'))}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_change_super_account_manager(http_client_test, setup_module,
                                            test_get_account_manager,
                                            college_super_admin_access_token, test_sam_data):
    """
    Test case -> success
    """
    test_sam_data['email'] = "XW4trBc@example.com"
    test_sam_data['mobile_number'] = "1234123490"

    # Creating Super Account Manager
    sam = await http_client_test.post(
        f"super_account_manager/create?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_sam_data
    )

    new_sam_id = sam.json().get('super_account_manager_id')

    response = await http_client_test.put(
        "account_manager/change_super_account_manager/"
        f"{str(test_get_account_manager.get('_id'))}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"super_account_manager_id": new_sam_id}
    )

    assert response.status_code == 200
    from app.database.configuration import DatabaseConfiguration
    account_manager = await DatabaseConfiguration().user_collection.find_one(
        {"_id": test_get_account_manager.get('_id')})
    assert str(account_manager.get("associated_super_account_manager")) == new_sam_id
