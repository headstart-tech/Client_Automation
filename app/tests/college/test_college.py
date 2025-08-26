"""
This file contains test cases related to college API routes/endpoints
"""
import pytest
from bson import ObjectId
from app.tests.conftest import access_token, user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_college_not_authenticated(http_client_test, setup_module):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(f"/college/create/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_college_bad_credentials(http_client_test, setup_module):
    """
    Test case -> bad token for create college
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/college/create/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_create_college_field_required(
        http_client_test, super_admin_access_token, setup_module
):
    """
    Test case -> field required for create college
    :param http_client_test:
    :param super_admin_access_token:
    :return:
    """
    response = await http_client_test.post(
        f"/college/create/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}


@pytest.mark.asyncio
async def test_create_college_no_permission(
        http_client_test, access_token, test_college_data, setup_module
):
    """
    Test case -> no permission for create college
    :param http_client_test:
    :param access_token:
    :return:
    """
    course_details = test_college_data.get("course_details")
    if course_details:
        course_details[0]["course_id"] = str(course_details[0].get("course_id"))
    response = await http_client_test.post(
        f"/college/create/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=test_college_data,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_create_college(http_client_test, super_admin_access_token, test_college_data):
    """
    Test case -> for create college
    :param http_client_test:
    :param super_admin_access_token:
    :param test_college_data:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.delete_many(
        {'name': test_college_data.get('name').title()})
    response = await http_client_test.post(f"/college/create/?feature_key={feature_key}",
                                           headers={
                                               "Authorization": f"Bearer {super_admin_access_token}"},
                                           json=test_college_data)
    assert response.status_code == 200
    assert response.json()['message'] == "New college data added successfully."


@pytest.mark.asyncio
async def test_create_college_already_exist(http_client_test, client_manager_access_token,
                                            test_college_data,
                                            test_college_validation):
    """
    Test case -> for create college already exist
    :param http_client_test:
    :param test_college_data:
    :return:
    """
    response = await http_client_test.post(
        f"/college/create/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {client_manager_access_token}"}, json={
            "website_url": "./resource.txt#frag01"})
    assert response.status_code == 200
    assert response.json() == {"message": "Updated college data."}


@pytest.mark.asyncio
async def test_get_list_of_colleges_not_authenticated(http_client_test, setup_module):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(f"/college/list_college/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_list_of_colleges_bad_credentials(http_client_test, setup_module):
    """
    Test case -> bad token for get list of colleges
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/college/list_college/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# ToDo - Need to resolve following test case problem, it is giving error when run all test cases o.w it's working
# @pytest.mark.asyncio
# async def test_get_list_of_colleges(
#         http_client_test, college_super_admin_access_token, test_college_validation, setup_module
# ):
#     """
#     Test case -> for get list of colleges
#     :param http_client_test: The object of async client
#     :param college_super_admin_access_token: Access token of college super admin
#     :param test_college_validation: Create college if not exist and return college data
#     """
#     response = await http_client_test.get(
#         "/college/list_college/",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Colleges data found."
#     for column in ["id", "name", "address", "website_url", "pocs", "subscriptions", "enforcements", "status_info",
#                    "charges_per_release", "course_details", "is_different_forms", "form_details", "status",
#                    "charges_details", "background_image", "logo"]:
#         assert column in response.json()["data"][0]


@pytest.mark.asyncio
async def test_get_list_of_colleges_not_found(http_client_test,
                                              super_admin_access_token):
    """
    Test case -> for get list of colleges not found
    :param http_client_test: The object of async client
    :param super_admin_access_token: Access token of super admin
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.delete_many({})
    response = await http_client_test.get(f"/college/list_college/?feature_key={feature_key}",
                                          headers={
                                              "Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 404
    assert response.json()['detail'] == "Data not found id: Colleges"


# ToDo - Need to resolve following test case problem, it is giving error when run all test cases o.w it's working
# @pytest.mark.asyncio
# async def test_get_list_of_colleges_with_query_parameter(
#         http_client_test, college_super_admin_access_token, test_college_validation, setup_module
# ):
#     """
#     Test case -> for get list of colleges using query parameter
#     :param http_client_test: The object of async client
#     :param college_super_admin_access_token: Access token of college super admin
#     :param test_college_validation:: Get college data
#     """
#     response = await http_client_test.get(
#         "/college/list_college/?using_for=authentication",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Colleges data found."
#     for column in ["id", "name"]:
#         assert column in response.json()["data"][0]


@pytest.mark.asyncio
async def test_get_list_of_colleges_with_query_parameter_invalid_value(
        http_client_test, college_super_admin_access_token, test_college_validation, setup_module
):
    """
    Test case -> for get list of colleges using query parameter with invalid value
    :param http_client_test: The object of async client
    :param college_super_admin_access_token: Access token of college super admin
    :param test_college_validation: Get college data
    """
    response = await http_client_test.get(
        f"/college/list_college/?using_for=authenticate&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Using For must be required and valid."


@pytest.mark.asyncio
async def test_get_college_details_by_id_or_name_not_authenticated(
        http_client_test, setup_module
):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(f"/college/get_by_id_or_name/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_college_details_by_id_or_name_bad_credentials(
        http_client_test, setup_module
):
    """
    Test case -> bad token for get college_details by college_id or college_name
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/college/get_by_id_or_name/?feature_key={feature_key}", headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_college_details_by_id_or_name_not_found(
        http_client_test, college_super_admin_access_token, setup_module
):
    """
    Test case -> for get college_details by college_id or college_name not found
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/college/get_by_id_or_name/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "College not found."}


@pytest.mark.asyncio
async def test_get_college_details_by_id(
        http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    Test case -> for get college_details by college_id
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/college/get_by_id_or_name/?id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "College details fetched successfully."


@pytest.mark.asyncio
async def test_get_college_details_by_name(
        http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    Test case -> for get college_details by college_name
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/college/get_by_id_or_name/?name={test_college_validation.get('name')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "College details fetched successfully."


@pytest.mark.asyncio
async def test_get_college_details_by_id_not_found(
        http_client_test, college_super_admin_access_token, setup_module
):
    """
    Test case -> for get college_details by college_id not found
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/college/get_by_id_or_name/?id=624e8d6a92cc415f1f578a25&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "College not found."


@pytest.mark.asyncio
async def test_get_college_details_by_name_not_found(
        http_client_test, college_super_admin_access_token, setup_module
):
    """
    Test case -> for get college_details by college_name not found
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/college/get_by_id_or_name/?name=wrong_name&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "College not found."


# Test Case: Get Colleges by Client IDs Without Authentication
@pytest.mark.asyncio
async def test_get_colleges_by_client_ids_unauthenticated(http_client_test):
    """ Test Case: Get Colleges by Client IDs Without Authentication """
    response = await http_client_test.post(
        f"/college/get_colleges_by_client_ids/?feature_key={feature_key}",
        json={"client_ids": [str(ObjectId())]})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

# Test Case: Get Colleges by Client IDs With Invalid Token
@pytest.mark.asyncio
async def test_get_colleges_by_client_ids_invalid_token(http_client_test):
    """ Test Case: Get Colleges by Client IDs With Invalid Token """
    response = await http_client_test.post(
        f"/college/get_colleges_by_client_ids/?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"},
        json={"client_ids": [str(ObjectId())]}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

# Test Case: Get Colleges by Client IDs with No Permission
@pytest.mark.asyncio
async def test_get_colleges_by_client_ids_no_permission(http_client_test, access_token, test_get_client):
    """ Test Case: Get Colleges by Client IDs with No Permission """
    response = await http_client_test.post(
        f"/college/get_colleges_by_client_ids/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"client_ids": [str(test_get_client.get("_id"))]}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

# Test Case: Missing Required Query Parameter client_ids
@pytest.mark.asyncio
async def test_get_colleges_by_client_ids_missing_param(http_client_test, college_super_admin_access_token):
    """ Test Case: Missing Required Query Parameter client_ids """
    response = await http_client_test.post(
        f"/college/get_colleges_by_client_ids/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400

# Test Case: Invalid Client ID
@pytest.mark.asyncio
async def test_get_colleges_by_invalid_client_id(http_client_test, college_super_admin_access_token):
    """ Test Case: Invalid Client ID """
    response = await http_client_test.post(
        f"/college/get_colleges_by_client_ids/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"client_ids": ["123"]},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid client ids"}

# Test Case: Successfully Get Colleges
@pytest.mark.asyncio
async def test_get_colleges_by_client_ids_success_no_pagination(http_client_test, college_super_admin_access_token, test_get_client, test_client_configuration_data):
    """ Test Case: Successfully Get Colleges """
    response = await http_client_test.post(
        f"/client/{str(test_get_client.get('_id'))}/configuration/add?feature_key={feature_key}",
           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
           json=test_client_configuration_data
    )
    college_data = {
        "name": "Test College",
        "email": "test@example.com",
        "phone_number": "8854295556",
        "associated_client": str(test_get_client.get("_id")),
        "address": {
            "address_line_1": "",
            "address_line_2": "",
            "country_code": "IN",
            "state_code": "MH",
            "city_name": "Pune",
        },
    }
    response = await http_client_test.post(
        f"/client_automation/add_college?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=college_data,
    )
    assert response.status_code == 200

    response = await http_client_test.post(
        f"/college/get_colleges_by_client_ids/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"client_ids": [str(test_get_client.get("_id"))]}
    )
    assert response.status_code == 200