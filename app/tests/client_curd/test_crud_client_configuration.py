"""
This file will test the client configuration CRUD operations
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_add_client_configuration_no_authentication(http_client_test, setup_module, test_client_data):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.post(f"/client/{str(client.get('client_id'))}/configuration/add"
                                           f"?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_add_client_configuration_bad_credentials(http_client_test, setup_module, test_client_data):
    """
    Test case -> bad token for add client configuration
    :param http_client_test:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.post(
        f"/client/{str(client.get('client_id'))}/configuration/add?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_add_client_configuration_no_permission(
        http_client_test, access_token, setup_module, test_client_data, test_client_configuration_data
):
    """
    Test case -> no permission for add client configuration
    :param http_client_test:
    :param access_token:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.post(
        f"/client/{str(client.get('client_id'))}/configuration/add?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=test_client_configuration_data
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_add_client_configuration_invalid_objId(
        http_client_test, setup_module, college_super_admin_access_token, test_client_configuration_data
    ):
    """
    Test case -> for add client configuration by invalid objectId
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    response = await http_client_test.post(f"/client/123/configuration/add?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                          json=test_client_configuration_data
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_add_client_configuration_client_id_not_exist(
        http_client_test, setup_module, college_super_admin_access_token, test_client_data, test_client_configuration_data
    ):
    """
    Test case -> for add client configuration by client_id not exist
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    random_ObjectId = '60f1b9b3e4b3b3b3b3b3b3b3'
    response = await http_client_test.post(f"/client/{str(random_ObjectId)}/configuration/add?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                          json=test_client_configuration_data
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Data not found id: Client or Configuration"}

@pytest.mark.asyncio
async def test_add_client_configuration(
        http_client_test, setup_module, college_super_admin_access_token, test_client_data, test_client_configuration_data
    ):
    """
    Test case -> for add client configuration
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.post(f"/client/{str(client.get('_id'))}/configuration/add?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                          json=test_client_configuration_data
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Client Configuration Added Successfully"

@pytest.mark.asyncio
async def test_get_all_client_not_authenticated(http_client_test, setup_module, test_client_data):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.get(f"/client/{str(client.get('client_id'))}/configuration/get?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_client_configuration_bad_credentials(http_client_test, setup_module, test_client_data):
    """
    Test case -> bad token for get client configuration
    :param http_client_test:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.get(
        f"/client/{str(client.get('client_id'))}/configuration/get?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_get_client_configuration_no_permission(
        http_client_test, access_token, setup_module, test_client_data
):
    """
    Test case -> no permission for get client configuration
    :param http_client_test:
    :param access_token:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.get(
        f"/client/{str(client.get('client_id'))}/configuration/get?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_get_client_configuration_invalid_objId(http_client_test, setup_module, college_super_admin_access_token):
    """
    Test case -> for read client configuration by invalid objectId
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    response = await http_client_test.get(f"/client/123/configuration/get?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_client_configuration_objId_not_exist(http_client_test, setup_module, college_super_admin_access_token, test_client_data):
    """
    Test case -> for read client configuration by objectId not exist
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    random_ObjectId = '60f1b9b3e4b3b3b3b3b3b3b3'
    response = await http_client_test.get(f"/client/{random_ObjectId}/configuration/get?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 404
    assert response.json() == {"detail": "Data not found id: Client or Configuration"}

@pytest.mark.asyncio
async def test_get_client_configuration(http_client_test, setup_module, college_super_admin_access_token, test_client_data):
    """
    Test case -> for read client configuration by objectId
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.get(f"/client/{str(client.get('_id'))}/configuration/get?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 200
    assert response.json()['message'] == "Client Configuration Found"

@pytest.mark.asyncio
async def test_delete_client(http_client_test, setup_module, college_super_admin_access_token, test_client_data):
    """
    Test case -> for delete client
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.delete(f"/client/{str(client.get('_id'))}/delete?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Client Deleted Successfully"