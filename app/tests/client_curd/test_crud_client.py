"""
This file contains test cases related to Client CRUD Operation
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_client_not_authenticated(http_client_test, setup_module):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(f"/client/create/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_client_bad_credentials(http_client_test, setup_module):
    """
    Test case -> bad token for create client
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/client/create/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_create_client_field_required(
        http_client_test, college_super_admin_access_token, setup_module
):
    """
    Test case -> field required for create client
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/client/create/?feature_key={feature_key}", headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}


@pytest.mark.asyncio
async def test_create_client_no_permission(
        http_client_test, access_token, test_client_data, setup_module
):
    """
    Test case -> no permission for create client
    :param http_client_test:
    :param access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/client/create/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=test_client_data,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_create_client(http_client_test, college_super_admin_access_token, test_client_data, test_get_account_manager):
    """
    Test case -> for create client
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().client_collection.delete_many({'client_email': test_client_data.get('client_email')})
    await DatabaseConfiguration().user_collection.delete_many({'email': test_client_data.get('client_email')})
    test_client_data['assigned_account_managers'] = [str(test_get_account_manager.get('_id'))]
    response = await http_client_test.post(f"/client/create/?feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           json=test_client_data)
    assert response.status_code == 200
    assert response.json()['message'] == "Client Created Successfully"

# TODO WILL FIX IT LATER, IN API CALLS IT IS WORKING
# @pytest.mark.asyncio
# async def test_get_client_configuration_not_exist(http_client_test, college_super_admin_access_token, test_client_data):
#     """
#     Test case -> for read client configuration which doesnot exist
#     :param http_client_test:
#     :param college_super_admin_access_token:
#     :param test_client_data:
#     :return:
#     """
#     response = await http_client_test.get(f"/client/{str(test_client_data.get('client_id'))}/configuration",
#                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
#     assert response.status_code == 404
#     assert response.json() == {"detail": "Client Configuration Not Found"}

@pytest.mark.asyncio
async def test_create_client_email_exists(http_client_test, college_super_admin_access_token, test_client_data):
    """
    Test case -> for create client when email already exists
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    response = await http_client_test.post(f"/client/create/?feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           json=test_client_data)
    assert response.status_code == 422
    assert response.json() == {"detail": "Email Already Exists"}

@pytest.mark.asyncio
async def test_get_client_by_id_not_authenticated(http_client_test, setup_module, test_client_data):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.get(f"/client/{str(client.get('client_id'))}/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_client_by_id_bad_credentials(http_client_test, setup_module, test_client_data):
    """
    Test case -> bad token for get client by id
    :param http_client_test:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.get(
        f"/client/{str(client.get('client_id'))}/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_get_client_by_id_no_permission(
        http_client_test, access_token, setup_module, test_client_data
):
    """
    Test case -> no permission for get client by id
    :param http_client_test:
    :param access_token:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.get(
        f"/client/{str(client.get('client_id'))}/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_client_by_id_invalid_objId(http_client_test, college_super_admin_access_token):
    """
    Test case -> for get client by invalid objectId
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    response = await http_client_test.get(f"/client/123/?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid client id"}

@pytest.mark.asyncio
async def test_get_client_by_id_objId_not_exist(http_client_test, college_super_admin_access_token):
    """
    Test case -> for read client by client_id not exist
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    random_ObjectId = '60f1b9b3e4b3b3b3b3b3b3b3'
    response = await http_client_test.get(f"/client/{random_ObjectId}/?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Data not found id: Client or Configuration"}
@pytest.mark.asyncio
async def test_get_client_by_id(http_client_test, college_super_admin_access_token, test_client_data):
    """
    Test case -> for read client by id
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.get(f"/client/{str(client.get('_id'))}/?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['_id'] == str(client.get('_id'))

@pytest.mark.asyncio
async def test_get_all_client_not_authenticated(http_client_test, setup_module, test_client_data):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(f"/client/all?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_all_client_bad_credentials(http_client_test, setup_module, test_client_data):
    """
    Test case -> bad token for get all client
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/client/all?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_get_all_client_no_permission(
        http_client_test, access_token, setup_module, test_client_data
):
    """
    Test case -> no permission for get all client
    :param http_client_test:
    :param access_token:
    :return:
    """
    response = await http_client_test.get(
        f"/client/all?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_all_client(http_client_test, college_super_admin_access_token, test_client_data):
    """
    Test case -> for read all client
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    response = await http_client_test.get(f"/client/all?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Client Data List Found"

@pytest.mark.asyncio
async def test_get_all_client_pagination(http_client_test, college_super_admin_access_token, test_client_data):
    """
    Test case -> for read all client with pagination
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    response = await http_client_test.get(f"/client/all?page=1&limit=2&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Client Data List Found"

@pytest.mark.asyncio
async def test_update_client_not_authenticated(http_client_test, setup_module, test_client_data):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.put(f"/client/{str(client.get('client_id'))}/update?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_update_client_bad_credentials(http_client_test, setup_module, test_client_data):
    """
    Test case -> bad token for update client
    :param http_client_test:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.put(
        f"/client/{str(client.get('client_id'))}/update?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_update_client_no_permission(
        http_client_test, access_token, setup_module, test_client_data, test_client_update_data
):
    """
    Test case -> no permission for update client
    :param http_client_test:
    :param access_token:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.put(
        f"/client/{str(client.get('client_id'))}/update?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=test_client_update_data,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_update_client_invalid_objId(http_client_test, college_super_admin_access_token, test_client_data, test_client_update_data):
    """
    Test case -> for update client by invalid objectId
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    response = await http_client_test.put(f"/client/123/update?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                          json=test_client_update_data)
    assert response.status_code == 422
    assert response.json() == {"detail": "Client Id must be a 12-byte input or a 24-character hex string"}

@pytest.mark.asyncio
async def test_update_client_objId_not_exist(http_client_test, college_super_admin_access_token, test_client_data, test_client_update_data):
    """
    Test case -> for update client by client_id not exist
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    random_ObjectId = '60f1b9b3e4b3b3b3b3b3b3b3'
    response = await http_client_test.put(f"/client/{random_ObjectId}/update?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                          json=test_client_update_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Data not found id: Client or Configuration"}

@pytest.mark.asyncio
async def test_update_client_wrong_address(http_client_test, college_super_admin_access_token, test_client_data, test_client_update_data):
    """
    Test case -> for update client with wrong address
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    test_client_update_data['address']['city_name'] = "Random_City"
    response = await http_client_test.put(f"/client/{str(client.get('_id'))}/update?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                          json=test_client_update_data)

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid Address"}

@pytest.mark.asyncio
async def test_update_client(http_client_test, college_super_admin_access_token, test_client_data, test_client_update_data):
    """
    Test case -> for update client
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.put(f"/client/{str(client.get('_id'))}/update?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                          json=test_client_update_data)
    assert response.status_code == 200
    assert response.json()['message'] == "Client Updated Successfully"

@pytest.mark.asyncio
async def test_delete_client_not_authenticated(http_client_test, setup_module, test_client_data):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.delete(f"/client/{str(client.get('client_id'))}/delete?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_delete_client_bad_credentials(http_client_test, setup_module, test_client_data):
    """
    Test case -> bad token for delete client
    :param http_client_test:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.delete(
        f"/client/{str(client.get('client_id'))}/delete?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_delete_client_no_permission(
        http_client_test, access_token, setup_module, test_client_data
):
    """
    Test case -> no permission for delete client
    :param http_client_test:
    :param access_token:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    client = await DatabaseConfiguration().client_collection.find_one({"client_name": test_client_data.get('client_name')})
    response = await http_client_test.delete(
        f"/client/{str(client.get('client_id'))}/delete?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_delete_client_invalid_objId(http_client_test, college_super_admin_access_token, test_client_data):
    """
    Test case -> for delete client by invalid objectId
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    response = await http_client_test.delete("/client/123/delete?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid client id"}

@pytest.mark.asyncio
async def test_delete_client_objId_not_exist(http_client_test, college_super_admin_access_token, test_client_data):
    """
    Test case -> for delete client by client_id not exist
    :param http_client_test:
    :param college_super_admin_access_token:
    :param test_client_data:
    :return:
    """
    random_ObjectId = '60f1b9b3e4b3b3b3b3b3b3b3'
    response = await http_client_test.delete(f"/client/{random_ObjectId}/delete?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Data not found id: Client or Configuration"}