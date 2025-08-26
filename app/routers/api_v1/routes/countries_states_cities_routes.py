"""
This file contain API routes/endpoints related to country, state and city
"""
from typing import Union
from fastapi import APIRouter, Path, Query, Depends
from fastapi.exceptions import HTTPException

from app.dependencies.oauth import cache_dependency_public_access, insert_data_in_cache
from app.helpers.countries_configuration import CountryHelper
from app.models.country_state_city_schema import StateCities
from app.database.aggregation.country_state_city import CountryStateCity

country_router = APIRouter()


@country_router.get("/", response_description="Get List of Countries")
async def country_list(
    page_num: Union[int, None] = Query(None, gt=0),
    page_size: Union[int, None] = Query(None, gt=0),
):
    """
    Get List of Countries
    :return:
    """
    if page_num and page_size:
        countries = await CountryHelper().retrieve_countries(
            page_num, page_size, route_name="/countries/"
        )
    else:
        countries = await CountryHelper().retrieve_countries()
    if countries:
        return countries
    raise HTTPException(status_code=404, detail={"error": "Country not found."})


@country_router.get(
    "/{country_code}/", response_description="Get Country Details using ISO2 Code"
)
async def get_country_details(
    country_code: str = Path(..., description="Enter country ISO2 code")
):
    """
    Get Country Details using ISO2 Code
    :param country_code:
    :return:
    """
    country = await CountryHelper().retrieve_country_details(country_code)
    if country:
        return country
    raise HTTPException(status_code=404, detail={"error": "Country not found."})


@country_router.get(
    "/{country_code}/states/", response_description="List of States within the Country"
)
async def country_states(
    cache_data=Depends(cache_dependency_public_access),
    country_code: str = Path(..., description="Enter country code"),
    page_num: Union[int, None] = Query(None, gt=0),
    page_size: Union[int, None] = Query(None, gt=0),
):
    """
    List of States within the Country
    :param cache_data
    :param page_size:
    :param page_num:
    :param country_code:
    :return:
    """
    cache_key, data = cache_data
    if data:
        return data
    states = await CountryHelper().retrieve_country_states(
        country_code,
        page_num,
        page_size,
        route_name=f"/countries/{country_code}/states/",
    )
    if cache_key:
        await insert_data_in_cache(cache_key, states, expiration_time=2592000)
    return states


@country_router.get(
    "/{country_code}/states/{state_code}",
    response_description="Get the state details of the Country",
)
async def country_state_details(
    country_code: str = Path(..., description="Enter country code"),
    state_code: str = Path(..., description="Enter state code"),
):
    """
    Get the state details of the Country
    :param country_code:
    :param state_code:
    :return:
    """
    state = await CountryHelper().retrieve_country_state_details(country_code, state_code)
    if state:
        return state
    raise HTTPException(status_code=404, detail={"error": "No State/Region found."})


@country_router.get(
    "/{country_code}/states/{state_code}/cities",
    response_description="Cities By State & Country",
)
async def country_state_cities(
    cache_data=Depends(cache_dependency_public_access),
    country_code: str = Path(..., description="Enter country code"),
    state_code: str = Path(..., description="Enter country code"),
    page_num: Union[int, None] = Query(None, gt=0),
    page_size: Union[int, None] = Query(None, gt=0),
):
    """
    Cities By State & Country
    :param cache_data:
    :param page_size:
    :param page_num:
    :param country_code:
    :param state_code:
    :return:
    """
    key, data = cache_data
    if data:
        return data
    cities = await CountryHelper().retrieve_cities_by_country_state(
        country_code,
        state_code,
        page_num,
        page_size,
        route_name=f"/countries/{country_code}/states/{state_code}/cities",
    )
    if key:
        await insert_data_in_cache(key, cities, expiration_time=2592000)
    return cities


@country_router.post(
    "/get_cities_based_on_states/",
    response_description="Get cities based on multiple state codes",
)
async def get_cities_based_on_states(
    payload: StateCities
):
    """
    Get cities based on multiple state codes.

    Request body parameters:
        - country_code (str): Optional field. Default value: IN.
            Useful for get country state cities.
        - state_codes (list[str]): Required field. A list which contains state
            codes. Useful for get cities based country code and state codes.
            e.g., ["AN", "AP"]

    Returns:
        dict: A dictionary which contains list of cities.
    """
    payload = payload.model_dump()
    cities = await CountryStateCity().get_cities_based_on_states(payload)
    if cities:
        return {"data": cities, "message": "Get cities based on "
                                           "state codes."}
    raise HTTPException(status_code=404, detail="No cities matching the "
                                                "given criteria.")
