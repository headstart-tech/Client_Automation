"""
This file contains test cases for map head counselor to counselor
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_head_counselors_list_not_authenticated(http_client_test, setup_module):
    """
    Test case -> not authenticate for map head counselor to counselor
    """
    response = await http_client_test.put(f"/counselor/map_with_head_counselor/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_get_head_counselors_list_required_college_id(http_client_test, super_admin_access_token, setup_module):
    """
    Test case -> required college id for map head counselor to counselor
    """
    response = await http_client_test.put(f"/counselor/map_with_head_counselor/?feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json() == {'detail': 'College Id must be required and valid.'}


@pytest.mark.asyncio
async def test_get_head_counselors_list_required_counselor_id(http_client_test, super_admin_access_token, setup_module,
                                                              test_college_validation):
    """
    Test case -> no permission for map head counselor to counselor
    """
    response = await http_client_test.put(
        f"/counselor/map_with_head_counselor/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json() == {'detail': 'Counselor Id must be required and valid.'}


@pytest.mark.asyncio
async def test_get_head_counselors_list_by_invalid_college_id(http_client_test, college_super_admin_access_token,
                                                              setup_module, test_counselor_validation,
                                                              test_counselor_data):
    """
    Test case -> invalid college id for map head counselor to counselor
    """
    response = await http_client_test.put(
        f"/counselor/map_with_head_counselor/?college_id=12345"
        f"&counselor_id={str(test_counselor_validation.get('_id'))}"
        f"&head_counselor_email_id={test_counselor_data['email']}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input or a 24-character hex string"}

# ToDo - Following test cases giving errors when running all test cases
# @pytest.mark.asyncio
# async def test_get_head_counselors_list_by_head_counselor_id(http_client_test, college_super_admin_access_token, setup_module, test_counselor_validation, test_counselor_data):
#     """
#     Test case -> for map head counselor to counselor by head counselor id
#     """
#     from app.database.configuration import user_collection
#     test_counselor_data["email"] = "publisher255@example.com"
#     await http_client_test.post(
#         "/user/create_new_user/?user_type=college_head_counselor",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#         json=test_counselor_data,
#     )
#     head_counselor = await user_collection.find_one({"email": "publisher255@example.com"})
#     response = await http_client_test.put(f"/counselor/map_with_head_counselor/?college_id={str(test_counselor_validation.get('associated_colleges')[0])}&counselor_id={str(test_counselor_validation.get('_id'))}&head_counselor_id={head_counselor.get('_id')}",
#                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
#     assert response.status_code == 200
#     assert response.json() == {"message": "Map head_counselor to counselor."}
#
#
# @pytest.mark.asyncio
# async def test_get_head_counselors_list_by_invalid_head_counselor_id(http_client_test, college_super_admin_access_token, setup_module, test_counselor_validation):
#     """
#     Test case -> invalid head counselor id for map head counselor to counselor
#     """
#     response = await http_client_test.put(f"/counselor/map_with_head_counselor/?college_id={str(test_counselor_validation.get('associated_colleges')[0])}&counselor_id={str(test_counselor_validation.get('_id'))}&head_counselor_id=1234",
#                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
#     assert response.status_code == 422
#     assert response.json() == {"detail": "Head counselor id must be a 12-byte input or a 24-character hex string"}
#
#
# @pytest.mark.asyncio
# async def test_get_head_counselors_list_wrong_counselor_id(http_client_test, college_super_admin_access_token, setup_module, test_counselor_validation, test_counselor_data):
#     """
#     Test case -> wrong counselor id for map head counselor to counselor
#     """
#     test_counselor_data["email"] = "publisher255@example.com"
#     await http_client_test.post(
#         "/user/create_new_user/?user_type=college_head_counselor",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#         json=test_counselor_data,
#     )
#     response = await http_client_test.put(f"/counselor/map_with_head_counselor/?college_id={str(test_counselor_validation.get('associated_colleges')[0])}&counselor_id=123456789012345678901234&head_counselor_email_id={test_counselor_data['email']}",
#                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
#     assert response.status_code == 200
#     assert response.json() == {"detail": "Counselor not found. Make sure counselor_id must be valid."}
#
#
# @pytest.mark.asyncio
# async def test_get_head_counselors_list_by_wrong_head_counselor_id(http_client_test, college_super_admin_access_token, setup_module, test_counselor_validation):
#     """
#     Test case -> wrong head counselor id for map head counselor to counselor
#     """
#     response = await http_client_test.put(f"/counselor/map_with_head_counselor/?college_id={str(test_counselor_validation.get('associated_colleges')[0])}&counselor_id={str(test_counselor_validation.get('_id'))}&head_counselor_id=123456789012345678901234",
#                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
#     assert response.status_code == 200
#     assert response.json() == {"detail": "Head counselor not found."}
#
#
# @pytest.mark.asyncio
# async def test_get_head_counselors_list_required_publisher_id_or_email(http_client_test, college_super_admin_access_token, setup_module, test_counselor_validation):
#     """
#     Test case -> required publisher id/email for map head counselor to counselor
#     """
#     response = await http_client_test.put(f"/counselor/map_with_head_counselor/?college_id={str(test_counselor_validation.get('associated_colleges')[0])}&counselor_id={str(test_counselor_validation.get('_id'))}",
#                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
#     assert response.status_code == 200
#     assert response.json() == {"detail": "Need to provide head_counselor_id or head_counselor_email"}
#
#
# @pytest.mark.asyncio
# async def test_get_head_counselors_list_by_head_counselor_email(http_client_test, college_super_admin_access_token, setup_module, test_counselor_validation, test_counselor_data):
#     """
#     Test case -> for map head counselor to counselor by head counselor email
#     """
#     test_counselor_data["email"] = "publisher255@example.com"
#     await http_client_test.post(
#         "/user/create_new_user/?user_type=college_head_counselor",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#         json=test_counselor_data,
#     )
#     response = await http_client_test.put(f"/counselor/map_with_head_counselor/?college_id={str(test_counselor_validation.get('associated_colleges')[0])}&counselor_id={str(test_counselor_validation.get('_id'))}&head_counselor_email_id={test_counselor_data['email']}",
#                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
#     assert response.status_code == 200
#     assert response.json() == {"message": "Map head_counselor to counselor."}
#
#
# @pytest.mark.asyncio
# async def test_get_head_counselors_list_invalid_counselor_id(http_client_test, college_super_admin_access_token, setup_module, test_counselor_validation, test_counselor_data):
#     """
#     Test case -> invalid counselor id for map head counselor to counselor
#     """
#     test_counselor_data["email"] = "publisher255@example.com"
#     await http_client_test.post(
#         "/user/create_new_user/?user_type=college_head_counselor",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#         json=test_counselor_data,
#     )
#     response = await http_client_test.put(f"/counselor/map_with_head_counselor/?college_id={str(test_counselor_validation.get('associated_colleges')[0])}&counselor_id=1234567&head_counselor_email_id={test_counselor_data['email']}",
#                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
#     assert response.status_code == 422
#     assert response.json() == {"detail": "Counselor id must be a 12-byte input or a 24-character hex string"}
