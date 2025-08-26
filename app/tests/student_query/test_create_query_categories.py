"""
This file contains test cases for create query categories
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_query_categories(http_client_test, setup_module):
    """
    Test case -> for create query categories
    :param http_client_test:
    :param setup_module:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().queryCategories.delete_many({})
    response = await http_client_test.post(f"/create_query_categories/?feature_key={feature_key}")
    assert response.status_code == 200
    assert response.json()["message"] == "Query categories created successfully."


# ToDo - Following test cases giving error when running all test cases by folder because of query categories found,
#  need to fix it
# @pytest.mark.asyncio
# async def test_create_query_categories_already_exist(
#         http_client_test, setup_module, create_query_categories
# ):
#     """
#     Test case -> for create query categories
#     :param http_client_test:
#     :param setup_module:
#     :return:
#     """

#     response = await http_client_test.post("/create_query_categories/")
#     assert response.status_code == 422
#     assert response.json()["detail"] == "Query categories already exists."
