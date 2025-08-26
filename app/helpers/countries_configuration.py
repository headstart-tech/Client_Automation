"""
This file contains class and functions related to countries configuration
"""
from bson import ObjectId

from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache


class CountryHelper:
    """
    Contain functions related to country
    """

    def country_details_helper(self, country) -> dict:
        """
        Get country details
        """
        return {
            "id": str(country["_id"]),
            "name": country["name"],
            "iso3": country["iso3"],
            "iso2": country["iso2"],
            "phonecode": country["phone_code"],
            "capital": country["capital"],
            "currency": country["currency"],
            "native": country["native"],
            "emoji": country["emoji"],
            "emojiU": country["emojiU"],
        }

    def country_helper(self, country) -> dict:
        """
        Get country details
        """
        return {
            "id": str(country.get("_id")),
            "name": country.get("name"),
            "iso2": country.get("iso2"),
            "country_code": country.get("phone_code"),
            "phone_length": country.get("phone_length")
        }

    def state_details_helper(self, state) -> dict:
        """
        Get state details
        """
        return {
            "id": state["id"],
            "name": state["name"],
            "country_id": state["country_id"],
            "country_code": state["country_code"],
            "state_code": state["state_code"],
        }

    def state_helper(self, state) -> dict:
        """
        Get country states details
        """
        return {"id": str(state["id"]), "name": state["name"], "iso2": state["state_code"]}

    def city_helper(self, city) -> dict:
        """
        Get city details
        """
        return {"id": city["id"], "name": city["name"]}

    async def retrieve_countries(self, page_num=None, page_size=None, route_name=None):
        """
        Get list of countries
        """
        from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache
        countries = await get_collection_from_cache(collection_name="countries")
        if countries:
            countries = sorted(countries, key=lambda x: x['name'])
        else:
            pipeline = [
                {
                    "$sort": {
                        "name": 1
                    }
                }
            ]
            countries = await DatabaseConfiguration().country_collection.aggregate(pipeline).to_list(None)
            await store_collection_in_cache(collection=countries, collection_name="countries")
        countries = [
            self.country_helper(country)
            for country in countries
        ]
        if page_num and page_size:
            countries_length = len(countries)
            response = await utility_obj.pagination_in_api(
                page_num, page_size, countries, countries_length, route_name
            )
        if countries:
            if page_num and page_size:
                return {
                    "data": response["data"],
                    "total": response["total"],
                    "count": page_size,
                    "pagination": response["pagination"],
                    "message": "Get all countries.",
                }
            return countries
        return False

    async def retrieve_country_details(self, country_code):
        """
        Get country details using iso2 code
        """
        from app.dependencies.oauth import get_collection_from_cache, store_collection_in_cache
        countries = await get_collection_from_cache(collection_name="countries")
        if countries:
            country = utility_obj.search_for_document(countries, field="iso2", search_name=country_code)
        else:
            country = await DatabaseConfiguration().country_collection.find_one({"iso2": country_code})
            countries = await DatabaseConfiguration().country_collection.aggregate([]).to_list(None)
            await store_collection_in_cache(collection=countries, collection_name="countries")
        if country:
            return self.country_details_helper(country)
        return False

    async def retrieve_country_states(
            self, country_code, page_num=None, page_size=None, route_name=None
    ):
        """
        Get list of states within the country
        """
        pipeline = [
            {
                "$match": {
                    "country_code": country_code
                }
            },
            {
                "$sort": {
                    "name": 1
                }
            }
        ]
        states = await DatabaseConfiguration().state_collection.aggregate(pipeline).to_list(None)
        states = [self.state_helper(state) for state in states]
        if page_size and page_num:
            states_length = len(states)
            response = await utility_obj.pagination_in_api(
                page_num, page_size, states, states_length, route_name
            )
            return {
                "data": response["data"],
                "total": response["total"],
                "count": page_size,
                "pagination": response["pagination"],
                "message": "Get all states.",
            }
        return states

    async def retrieve_country_state_details(self, country_code, state_code):
        """
        Get cities by country & state
        """
        states = await get_collection_from_cache(collection_name="states")
        if states:
            state = utility_obj.search_for_document_two_fields(states,
                                                             field1="country_code",
                                                             field1_search_name=country_code,
                                                             field2="state_code",
                                                             field2_search_name=state_code,

                                                             )
        else:
            state = await DatabaseConfiguration().state_collection.find_one(
                {"country_code": country_code, "state_code": state_code}
            )
            collection = await DatabaseConfiguration().state_collection.aggregate([]).to_list(None)
            await store_collection_in_cache(collection, collection_name="states")
        if state:
            return self.state_details_helper(state)
        return False

    async def retrieve_cities_by_country_state(
            self, country_code, state_code, page_num=None, page_size=None, route_name=None
    ):
        """
        Get list of country state cities
        """
        pipeline = [
            {
                "$match": {
                        "country_code": country_code,
                        "state_code": state_code
                    }
            },
            {
                "$sort": {
                    "name": 1
                }
            }
        ]
        city = await DatabaseConfiguration().city_collection.aggregate(pipeline).to_list(None)
        cities = [self.city_helper(cit) for cit in city]
        if page_num and page_size:
            cities_length = len(cities)
            response = await utility_obj.pagination_in_api(
                page_num, page_size, cities, cities_length, route_name
            )
            return {
                "data": response["data"],
                "total": response["total"],
                "count": page_size,
                "pagination": response["pagination"],
                "message": "Get all cities.",
            }
        return cities
