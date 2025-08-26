"""
This file contains test cases regarding country state city routes
"""
import pytest


@pytest.mark.asyncio
async def test_get_countries_list(http_client_test, setup_module):
    """
    Test case for get countries list
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get("/countries/")
    assert response.status_code == 200
    assert response.json()[0]["iso2"] == "AF"


# Commented below test case because currently data present in database so it'll give error
# @pytest.mark.asyncio
# async def test_get_countries_list_not_found(http_client_test):
#     response = await http_client_test.get("/countries/")
#     assert response.status_code == 404
#     assert response.json()['detail'] == {'error': "Country not found."}


@pytest.mark.asyncio
async def test_get_country_details(http_client_test, setup_module):
    """
    Test case for get country details
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get("/countries/IN/")
    assert response.status_code == 200
    assert response.json()["iso2"] == "IN"


@pytest.mark.asyncio
async def test_country_details_not_found(http_client_test, setup_module):
    """
    Test case for country details not found
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get("/countries/I/")
    assert response.status_code == 404
    assert response.json()["detail"] == {"error": "Country not found."}


@pytest.mark.asyncio
async def test_get_states_details(http_client_test, setup_module):
    """
    Test case for get states details
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get("/countries/IN/states/")
    assert response.status_code == 200
    assert response.json()[0]["iso2"] == "AN"


@pytest.mark.asyncio
async def test_states_details_not_found(http_client_test, setup_module):
    """
    Test case for get states details not found
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get("/countries/I/states/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_state_details(http_client_test, setup_module):
    """
    Test case for get states details
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get("/countries/IN/states/MH")
    assert response.status_code == 200
    assert response.json()["country_code"] == "IN"


@pytest.mark.asyncio
async def test_state_details_not_found(http_client_test, setup_module):
    """
    Test case for get state details not found
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get("/countries/I/states/MH")
    assert response.status_code == 404
    assert response.json()["detail"] == {"error": "No State/Region found."}


@pytest.mark.asyncio
async def test_cities_details(http_client_test, setup_module):
    """
    Test case for get cities details
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get("/countries/IN/states/MH/cities")
    assert response.status_code == 200
    assert response.json()[0]["id"] == 57589


@pytest.mark.asyncio
async def test_cities_not_found(http_client_test, setup_module):
    """
    Test case for cities details not found
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get("/countries/I/states/MH/cities")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_first_page_data(http_client_test, setup_module):
    """
    Test case for get countries list based on pagination
    :return:
    """
    response = await http_client_test.get("/countries/?page_num=1&page_size=5")
    assert response.status_code == 200
    assert response.json()["message"] == "Get all countries."
    assert response.json()["pagination"]["previous"] is None


@pytest.mark.asyncio
async def test_get_last_page_data(http_client_test, setup_module):
    """
    Test case for get countries list based on pagination
    :return:
    """
    response = await http_client_test.get("/countries/?page_num=10&page_size=25")
    assert response.status_code == 200
    assert response.json()["message"] == "Get all countries."
    assert response.json()["pagination"]["next"] is None


@pytest.mark.asyncio
async def test_get_one_page_data(http_client_test, setup_module):
    """
    Test case for get countries list based on pagination
    :return:
    """
    response = await http_client_test.get("/countries/?page_num=1&page_size=250")
    assert response.status_code == 200
    assert response.json()["message"] == "Get all countries."
    assert response.json()["pagination"]["next"] is None
    assert response.json()["pagination"]["previous"] is None


@pytest.mark.asyncio
async def test_get_second_page_data(http_client_test, setup_module):
    """
    Test case for get countries list based on pagination
    :return:
    """
    response = await http_client_test.get("/countries/?page_num=2&page_size=250")
    assert response.status_code == 200
    assert response.json()["message"] == "Get all countries."
    assert response.json()["pagination"]["next"] is None


@pytest.mark.asyncio
async def test_get_invalid_input_page_data(http_client_test, setup_module):
    """
    Invalid page number for get countries list based on pagination
    :return:
    """
    response = await http_client_test.get("/countries/?page_num=0&page_size=10")
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Num must be required and valid."}


@pytest.mark.asyncio
async def test_get_invalid_input_size_data(http_client_test, setup_module):
    """
    Invalid page size for get countries list based on pagination
    :return:
    """
    response = await http_client_test.get("/countries/?page_num=1&page_size=0")
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Size must be required and valid."}
