"""
This file contains test cases regarding for get data segment details by name or ud
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_data_segment_by_name_or_id_not_authenticated(http_client_test, test_college_validation,
                                                                setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/data_segment/get_by_name_or_id/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_data_segment_by_name_or_id_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get data segment details by name or id
    """
    response = await http_client_test.get(
        f"/data_segment/get_by_name_or_id/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_data_segment_by_name_or_id_field_required(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Field required for get data segment details by name or id
    """
    response = await http_client_test.get(
        f"/data_segment/get_by_name_or_id/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_get_data_segment_by_name_or_id_no_permission(
        http_client_test, test_college_validation, access_token, test_campaign_data, setup_module
):
    """
    No permission for get data segment details by name or id
    """
    response = await http_client_test.get(
        f"/data_segment/get_by_name_or_id/?college_id={test_college_validation.get('_id')}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# ToDo - Following commented test cases giving error when run all test cases
# @pytest.mark.asyncio
# async def test_get_data_segment_by_name_or_id_required_field(
#         http_client_test, test_college_validation, college_super_admin_access_token, test_create_data_segment, setup_module
# ):
#     """
#     Required field for get data segment details by name or id
#     """
#     response = await http_client_test.get(
#         f"/data_segment/get_by_name_or_id/?college_id={test_college_validation.get('_id')}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#     )
#     assert response.status_code == 200
#     assert response.json() == {"detail": "Data segment not found. Make sure you provided data_segment_id or "
#                                          "data_segment_name is correct."}


# @pytest.mark.asyncio
# async def test_get_data_segment_by_name_or_id_not_found(
#         http_client_test, test_college_validation, college_super_admin_access_token, test_create_data_segment, setup_module
# ):
#     """
#     Not found for get data segment details by name or id
#     """
#     response = await http_client_test.get(
#         f"/data_segment/get_by_name_or_id/?college_id={test_college_validation.get('_id')}&data_segment_id=123456789012345678901234",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#     )
#     assert response.status_code == 200
#     assert response.json() == {"detail": "Data segment not found. Make sure you provided data_segment_id or "
#                                          "data_segment_name is correct."}


# @pytest.mark.asyncio
# async def test_get_data_segment_by_name_or_id_invalid_id(
#         http_client_test, test_college_validation, college_super_admin_access_token, test_create_data_segment, setup_module
# ):
#     """
#     Invalid id for get data segment details by name or id
#     """
#     response = await http_client_test.get(
#         f"/data_segment/get_by_name_or_id/?college_id={test_college_validation.get('_id')}&data_segment_id=12345678901234567890",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#     )
#     assert response.status_code == 422
#     assert response.json() == {"detail": "Data segment id must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_get_data_segment_by_name_or_id_invalid_college_id(
        http_client_test, college_super_admin_access_token, test_create_data_segment, setup_module
):
    """
    Get data segment details
    """
    response = await http_client_test.get(
        f"/data_segment/get_by_name_or_id/?college_id=1234567890&data_segment_id=123456789012345678901234"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input or a 24-character hex string"}

# @pytest.mark.asyncio
# async def test_get_data_segment_by_name_or_id(
#         http_client_test, test_college_validation, college_super_admin_access_token, test_create_data_segment, setup_module
# ):
#     """
#     Get data segment details
#     """
#     from app.database.configuration import data_segment_collection
#     await data_segment_collection.delete_many({})
#     await http_client_test.post(
#         f"/data_segment/create/?college_id={test_college_validation.get('_id')}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#         json=test_create_data_segment
#     )
#     data_segment = await data_segment_collection.find_one({'data_segment_name': test_create_data_segment.get('data_segment_name').title()})
#     response = await http_client_test.get(
#         f"/data_segment/get_by_name_or_id/?college_id={test_college_validation.get('_id')}&data_segment_id={str(data_segment.get('_id'))}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#     )
#     assert response.status_code == 200
#     assert response.json()['message'] == "Get data segment details."
