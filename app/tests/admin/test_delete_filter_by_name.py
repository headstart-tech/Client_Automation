"""
This file contains test cases of delete filter by name
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_filter_by_name(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.delete(
        f"/admin/filter/delete_by_name/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_filter_by_name_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for delete filter by name
    """
    response = await http_client_test.delete(
        f"/admin/filter/delete_by_name/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_delete_filter_by_name_required_field(http_client_test, test_college_validation,
                                                    college_counselor_access_token, setup_module,
                                                    test_student_validation):
    """
    Required field for delete filter by name
    """
    response = await http_client_test.delete(
        f"/admin/filter/delete_by_name/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Filter Name must be required and valid."}


@pytest.mark.asyncio
async def test_delete_filter_by_name_no_permission(http_client_test, test_college_validation, access_token,
                                                   setup_module,
                                                   test_student_validation):
    """
    No permission for delete filter by name
    """
    response = await http_client_test.delete(
        f"/admin/filter/delete_by_name/"
        f"?filter_name=test&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_delete_filter_by_name(http_client_test, test_college_validation, college_counselor_access_token,
                                     setup_module,
                                     test_counselor_validation):
    """
    Delete filter by name
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().user_collection.update_one({"_id": test_counselor_validation.get('_id')},
                                                             {'$set': {'saved_filter': [
                                                                 {'name': 'test', 'payload': {'test': 'test'}}]}})
    response = await http_client_test.delete(
        f"/admin/filter/delete_by_name/"
        f"?filter_name=test&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == 'Filter deleted.'


@pytest.mark.asyncio
async def test_delete_filter_by_incorrect_name(http_client_test, setup_module, test_college_validation,
                                               test_counselor_validation,
                                               college_counselor_access_token):
    """
    Delete filter by incorrect name
    """
    response = await http_client_test.delete(
        f"/admin/filter/delete_by_name/"
        f"?filter_name=&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()['detail'] == "Enter valid name of filter."


@pytest.mark.asyncio
async def test_delete_paid_application_filter_by_name(http_client_test, test_college_validation,
                                                      college_counselor_access_token, setup_module,
                                                      test_counselor_validation):
    """
    Delete paid application filter by name
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().user_collection.update_one({"_id": test_counselor_validation.get('_id')},
                                                             {'$set': {
                                                                 'paid_applications_filter': [
                                                                     {'name': 'test', 'payload': {'test': 'test'}}]}})
    response = await http_client_test.delete(
        f"/admin/filter/delete_by_name/"
        f"?filter_name=test&paid_applications_filter=true"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == 'Filter deleted.'
