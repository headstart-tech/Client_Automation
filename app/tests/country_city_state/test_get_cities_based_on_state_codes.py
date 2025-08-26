"""
This file contains test cases of get cities based on states
"""
import pytest


@pytest.mark.asyncio
async def test_get_cities_based_on_states(
        http_client_test, setup_module):
    """
    Different scenarios of test cases -> get cities based on states
    """

    from app.database.configuration import DatabaseConfiguration
    city = await DatabaseConfiguration().city_collection.find_one(
        {"country_code": "IN"})

    # Get cities based on states
    response = await http_client_test.post(
        f"/countries/get_cities_based_on_states/",
        json={"state_code": [city.get("state_code")]}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get cities based on state codes."
    for name in ["label", "value", "role"]:
        assert name in response.json()["data"][0]

    # Cities not found based on states
    response = await http_client_test.post(
        f"/countries/get_cities_based_on_states/",
        json={"state_code": ["test"]}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "No cities matching the given " \
                                        "criteria."
