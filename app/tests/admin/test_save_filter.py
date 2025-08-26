"""
This file contains test case of save filter
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_save_filter_not_authenticated(
        http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/admin/filter/add/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_save_filter_invalid_name(
        http_client_test, test_college_validation, setup_module,
        college_counselor_access_token):
    """
    Invalid name for save filter
    """
    response = await http_client_test.post(
        f"/admin/filter/add/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"})
    assert response.status_code == 200
    assert response.json() == {'detail': "Enter valid name of filter."}


@pytest.mark.asyncio
async def test_save_filter_invalid_payload(
        http_client_test, test_college_validation, setup_module,
        college_counselor_access_token):
    """
    Invalid payload for save filter
    """
    response = await http_client_test.post(
        f"/admin/filter/add/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json={'filter_name': 'test'})
    assert response.status_code == 200
    assert response.json() == {'detail': "Please provide valid payload."}


@pytest.mark.asyncio
async def test_save_filter_no_permission(
        http_client_test, test_college_validation, access_token, setup_module,
        test_student_validation):
    """
    No permission for save filter
    """
    response = await http_client_test.post(
        f"/admin/filter/add/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={'filter_name': 'test', 'payload': {'test': 'test'}})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_save_filter(
        http_client_test, setup_module, test_counselor_validation,
        college_counselor_access_token):
    """
    Save filter
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().user_collection.update_one(
        {"_id": test_counselor_validation.get('_id')},
        {'$unset': {'saved_filter': True}})
    response = await http_client_test.post(
        f"/admin/filter/add/?college_id="
        f"{str(test_counselor_validation.get('associated_colleges', [0])[0])}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json={'filter_name': 'test', 'payload': {'test': 'test'}})
    assert response.status_code == 200
    assert response.json()['message'] == "Filter saved."

    # Test - Filter already exist
    response = await http_client_test.post(
        f"/admin/filter/add/?college_id="
        f"{str(test_counselor_validation.get('associated_colleges', [0])[0])}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json={'filter_name': 'test', 'payload': {'test': 'test'}})
    assert response.status_code == 200
    assert response.json()['detail'] == \
           "Filter name already exist. Please use another name for " \
           "save filter."


@pytest.mark.asyncio
async def test_save_paid_application_filter(http_client_test, setup_module,
                                            test_counselor_validation,
                                            college_counselor_access_token):
    """
    Save paid application filter
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().user_collection.update_one(
        {"_id": test_counselor_validation.get('_id')},
        {'$unset': {'paid_applications_filter': True}})
    response = await http_client_test.post(
        f"/admin/filter/add/?paid_applications_filter=true&college_id="
        f"{str(test_counselor_validation.get('associated_colleges', [0])[0])}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json={'filter_name': 'test', 'payload': {'test': 'test'}})
    assert response.status_code == 200
    assert response.json()['message'] == "Filter saved."

    # Test - Filter already exist
    response = await http_client_test.post(
        f"/admin/filter/add/?paid_applications_filter=true&college_id="
        f"{str(test_counselor_validation.get('associated_colleges', [0])[0])}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json={'filter_name': 'test', 'payload': {'test': 'test'}})
    assert response.status_code == 200
    assert response.json()['detail'] == "Filter name already exist. Please " \
                                        "use another name for save filter."


@pytest.mark.asyncio
async def test_save_lead_filter(
        http_client_test, setup_module, test_counselor_validation,
        college_counselor_access_token):
    """
    Save lead filter
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().user_collection.update_one(
        {"_id": test_counselor_validation.get('_id')},
        {'$unset': {'leads_filter': True}})
    response = await http_client_test.post(
        f"/admin/filter/add/?leads_filter=true&college_id="
        f"{str(test_counselor_validation.get('associated_colleges', [0])[0])}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json={'filter_name': 'test', 'payload': {'test': 'test'}})
    assert response.status_code == 200
    assert response.json()['message'] == "Filter saved."

    # Test - Filter already exist
    response = await http_client_test.post(
        f"/admin/filter/add/?leads_filter=true&college_id="
        f"{str(test_counselor_validation.get('associated_colleges', [0])[0])}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
        json={'filter_name': 'test', 'payload': {'test': 'test'}})
    assert response.status_code == 200
    assert response.json()['detail'] == \
           "Filter name already exist. Please use another name for " \
           "save filter."
