"""
This file contains test cases regarding for create data segment
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_data_segment_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(f"/data_segment/create/?college_id={test_college_validation.get('_id')}"
                                           f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_data_segment_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for create data segment
    """
    response = await http_client_test.post(
        f"/data_segment/create/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_create_data_segment_field_required(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Field required for create data segment
    """
    response = await http_client_test.post(
        f"/data_segment/create/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}


@pytest.mark.asyncio
async def test_create_data_segment_no_permission(http_client_test, test_college_validation, access_token,
                                                 test_create_data_segment,
                                                 setup_module):
    """
    No permission for create data segment
    """
    response = await http_client_test.post(
        f"/data_segment/create/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=test_create_data_segment,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_create_data_segment_success(
        http_client_test, test_college_validation, college_super_admin_access_token, test_create_data_segment,
        setup_module
):
    """
    Create data segment
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().data_segment_collection.delete_many({})
    response = await http_client_test.post(
        f"/data_segment/create/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_create_data_segment,
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Data segment created."


@pytest.mark.asyncio
async def test_create_data_segment_already_exist(
        http_client_test, test_college_validation, college_super_admin_access_token, test_create_data_segment,
        setup_module
):
    """
    Already exist for create data segment
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().data_segment_collection.delete_many({})
    await http_client_test.post(
        f"/data_segment/create/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_create_data_segment
    )
    response = await http_client_test.post(
        f"/data_segment/create/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_create_data_segment,
    )
    assert response.status_code == 200
    assert response.json() == {'detail': 'Data segment name already exists.'}


@pytest.mark.asyncio
async def test_create_data_segment_with_custom_period(http_client_test, test_college_validation,
                                                      college_super_admin_access_token,
                                                      test_create_data_segment, setup_module, start_end_date):
    """
    Create data segment with custom period
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().data_segment_collection.delete_many({})
    test_create_data_segment['period'] = start_end_date
    response = await http_client_test.post(
        f"/data_segment/create/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_create_data_segment,
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Data segment created."


@pytest.mark.asyncio
async def test_edit_data_segment(
        http_client_test, test_college_validation, college_super_admin_access_token, test_create_data_segment,
        setup_module
):
    """
    Edit data segment
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().data_segment_collection.delete_many({})
    await http_client_test.post(
        f"/data_segment/create/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_create_data_segment
    )
    data_segment = await DatabaseConfiguration().data_segment_collection.find_one(
        {'data_segment_name': test_create_data_segment.get('data_segment_name').title()})
    test_create_data_segment['data_segment_name'] = "test"
    response = await http_client_test.post(
        f"/data_segment/create/?college_id={test_college_validation.get('_id')}"
        f"&data_segment_id={str(data_segment.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_create_data_segment,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Data segment details updated."}
