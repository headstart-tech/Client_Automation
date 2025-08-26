"""
This file contains test case of get all filters of user
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_all_filters_of_user(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(f"/admin/filter/"
                                          f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_all_filters_of_user_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get all filters of user
    """
    response = await http_client_test.get(f"/admin/filter/?"
                                          f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer wrong"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_all_filters_no_permission(http_client_test, test_college_validation, access_token, setup_module,
                                             test_student_validation):
    """
    No permission for get all filters of user
    """
    response = await http_client_test.get(f"/admin/filter/?college_id="
                                          f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_all_filters(http_client_test, test_college_validation, setup_module, test_counselor_validation,
                               college_counselor_access_token):
    """
    Get all filters of user
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().user_collection.update_one({"_id": test_counselor_validation.get('_id')},
                                                             {'$set': {'saved_filter': [
                                                                 {'name': 'test', 'payload': {'test': 'test'}}]}})
    response = await http_client_test.get(f"/admin/filter/?"
                                          f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get all filters."


@pytest.mark.asyncio
async def test_get_all_filters_no_found(http_client_test, test_college_validation, setup_module,
                                        test_counselor_validation,
                                        college_counselor_access_token):
    """
    All application filters not found
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().user_collection.update_one({"_id": test_counselor_validation.get('_id')},
                                                             {'$unset': {'saved_filter': True}})
    response = await http_client_test.get(f"/admin/filter/?college_id="
                                          f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get all filters."
    assert response.json()['data'] == []


@pytest.mark.asyncio
async def test_get_all_paid_applications_filters(http_client_test, test_college_validation, setup_module,
                                                 test_counselor_validation,
                                                 college_counselor_access_token):
    """
    Get all paid applications filters of user
    :param http_client_test:
    :param college_counselor_access_token:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().user_collection.update_one({"_id": test_counselor_validation.get('_id')},
                                                             {'$set': {
                                                                 'paid_applications_filter': [
                                                                     {'name': 'test', 'payload': {'test': 'test'}}]}})
    response = await http_client_test.get(
        f"/admin/filter/?paid_applications_filter=true&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get all filters."


@pytest.mark.asyncio
async def test_get_all_paid_applications_filters_no_found(http_client_test, test_college_validation, setup_module,
                                                          test_counselor_validation,
                                                          college_counselor_access_token):
    """
    Paid applications filters not found
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().user_collection.update_one({"_id": test_counselor_validation.get('_id')},
                                                             {'$unset': {'paid_applications_filter': True}})
    response = await http_client_test.get(
        f"/admin/filter/?paid_applications_filter=true&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get all filters."
    assert response.json()['data'] == []
