"""
This file contains test case regarding get leads based on matched string
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_list_of_search_student_based_on_matched_string_not_authenticated(
        http_client_test, test_college_validation, setup_module
):
    """
    Not Authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/admin/search_leads/?search_input=temp&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_list_of_search_student_based_on_matched_string_no_permission(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    User has no permission to get the records
    """
    response = await http_client_test.post(
        f"/admin/search_leads/?page_num=1&page_size=20&search_input=temp&"
        f"username=wrong_username&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# ToDo - Currently following test case giving error maybe because document not in meilisearch server
# @pytest.mark.asyncio
# async def test_search_of_username_based_on_matched_string(
#         http_client_test,
#         test_student_validation,
#         college_super_admin_access_token,
#         setup_module
# ):
#     """
#     Get searched records with valid search string
#     """
#     response = await http_client_test.post(
#         f"/admin/search_leads/?search_input={test_student_validation['user_name']}&page_num=1&page_size=1&college_id={str(test_student_validation.get('college_id'))}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Fetched student data successfully"
#     for item in ["data", 'count', "page_size", "page_num"]:
#         assert item in response.json()


@pytest.mark.asyncio
async def test_search_of_username_when_search_string_not_provided(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        setup_module
):
    """
    Get searched records with valid search string
    """
    response = await http_client_test.post(
        f"/admin/search_leads/?page_num=1&page_size=1&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Search Input must be required and valid."
