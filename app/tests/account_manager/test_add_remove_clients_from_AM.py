import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_clients_to_AM_not_authenticated(http_client_test, setup_module, test_get_account_manager, test_get_client):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"account_manager/add_clients/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        json={"client_ids": [str(test_get_client.get('_id'))]}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_add_clients_to_AM_bad_credentials(http_client_test, setup_module, test_get_account_manager, test_get_client):
    """
    Test case -> bad credentials
    """
    response = await http_client_test.put(
        f"account_manager/add_clients/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": "Bearer bad_token"},
        json={"client_ids": [str(test_get_client.get('_id'))]}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_add_clients_to_AM_no_permission(http_client_test, setup_module, test_get_account_manager, access_token, test_get_client):
    """
    Test case -> no permission
    """
    response = await http_client_test.put(
        f"account_manager/add_clients/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"client_ids": [str(test_get_client.get('_id'))]}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_add_client_to_AM_college_id_not_found(http_client_test, setup_module, test_get_account_manager, college_super_admin_access_token, test_get_client):
    """
    Test case -> college id not found
    """
    response = await http_client_test.put(
        f"account_manager/add_clients/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"client_ids": [str(test_get_client.get('_id')), "67075b7edaa75713388a679f"]}
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_add_client_to_AM(http_client_test, setup_module, college_super_admin_access_token, test_client_data, test_new_account_manager):
    """
    Test case -> add client to AM
    """

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().client_collection.delete_many({"client_name": "Delta University"})
    await DatabaseConfiguration().user_collection.delete_many({"user_type": "account_manager"})
    await DatabaseConfiguration().user_collection.delete_many({"user_type": "client_admin"})
    test_new_account_manager["email"] = "1@email.com"
    test_new_account_manager["mobile_number"] = "1111111111"
    account_manager_1 = await http_client_test.post(
        "account_manager/create?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_new_account_manager
    )
    test_new_account_manager["email"] = "2@email.com"
    test_new_account_manager["mobile_number"] = "2222222222"
    account_manager_2 = await http_client_test.post(
        "account_manager/create?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_new_account_manager
    )
    test_client_data["client_email"] = "1@client.com"
    test_client_data["assigned_account_managers"] = [account_manager_1.json().get("account_manager_id")]
    client1 = await http_client_test.post(
        "client/create/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_client_data
    )
    test_client_data["client_email"] = "2@client.com"
    test_client_data["assigned_account_managers"] = [account_manager_2.json().get("account_manager_id")]
    client2 = await http_client_test.post(
        "client/create/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_client_data
    )
    test_main = await http_client_test.put(
        f"account_manager/add_clients/{account_manager_1.json().get('account_manager_id')}?feature_key={feature_key}",
        headers = {"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "client_ids": [client2.json()['data'][0]['client_id']]
        }
    )
    assert test_main.status_code == 200
    client_2 = await DatabaseConfiguration().client_collection.find_one({"client_email": "2@client.com"})
    assert len(client_2.get('assigned_account_managers')) > 1





@pytest.mark.asyncio
async def test_remove_clients_to_AM_not_authenticated(http_client_test, setup_module, test_get_account_manager, test_get_client):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"account_manager/remove_client/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        json={"client_id": str(test_get_client.get('_id'))}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_remove_clients_to_AM_bad_credentials(http_client_test, setup_module, test_get_account_manager, test_get_client):
    """
    Test case -> bad credentials
    """
    response = await http_client_test.put(
        f"account_manager/remove_client/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": "Bearer bad_token"},
        json={"client_id": str(test_get_client.get('_id'))}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_remove_clients_to_AM_no_permission(http_client_test, setup_module, test_get_account_manager, access_token, test_get_client):
    """
    Test case -> no permission
    """
    response = await http_client_test.put(
        f"account_manager/remove_client/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"client_id": str(test_get_client.get('_id'))}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_remove_client_to_AM_college_id_not_found(http_client_test, setup_module, test_get_account_manager, college_super_admin_access_token, test_get_client):
    """
    Test case -> college id not found
    """
    response = await http_client_test.put(
        f"account_manager/remove_client/{test_get_account_manager.get('_id')}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"client_id": "67075b7edaa75713388a679f"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_remove_client_to_AM(http_client_test, setup_module, test_get_account_manager, college_super_admin_access_token, test_get_client):
    """
    Test case -> remove client to AM
    """
    from app.database.configuration import DatabaseConfiguration
    client_2 = await DatabaseConfiguration().client_collection.find_one({"client_email": "2@client.com"})
    prev_length = len(client_2.get('assigned_account_managers'))
    AM_id = str(client_2.get('assigned_account_managers')[0])
    client_id = str(client_2.get('_id'))
    response = await http_client_test.put(
        f"account_manager/remove_client/{AM_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"client_id": client_id}
    )
    assert response.status_code == 200
    client_2 = await DatabaseConfiguration().client_collection.find_one({"client_email": "2@client.com"})
    assert prev_length > len(client_2.get('assigned_account_managers'))

# Its working while Testing Through API Calls
@pytest.mark.asyncio
async def test_remove_client_to_AM_only_one_AM_exists(http_client_test, setup_module, test_get_account_manager, college_super_admin_access_token):
    """
    Test case -> remove client to AM and only one AM exists
    """
    from app.database.configuration import DatabaseConfiguration
    client_2 = await DatabaseConfiguration().client_collection.find_one({"client_email": "2@client.com"})
    AM_id = str(client_2.get('assigned_account_managers')[0])
    client_id = str(client_2.get('_id'))
    response = await http_client_test.put(
        f"account_manager/remove_client/{AM_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"client_id": client_id}
    )
    assert response.status_code == 422