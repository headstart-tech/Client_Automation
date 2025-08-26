# """
# This file contains test cases for get all college user details.
# """
# import pytest
# from app.tests.conftest import user_feature_data
# feature_key = user_feature_data()
#
# @pytest.mark.asyncio
# async def test_all_user_get_details(
#         http_client_test, setup_module, college_super_admin_access_token,
#         access_token, test_user_validation):
#     """
#     Different test cases of get all college user details.
#
#     Params:\n
#         http_client_test: A fixture which return AsyncClient object.
#             Useful for test API with particular method.
#         setup_module: A fixture which upload necessary data in the db before
#             test cases start running/executing and delete data from collection
#              after test case execution completed.
#         college_super_admin_access_token: A fixture which create college super
#             admin if not exist and return access token of college super admin.
#         access_token: A fixture which create student if not exist
#             and return access token for student.
#         test_user_validation: A fixture which create user if not exist
#             and return user data.
#
#     Assertions:\n
#         response status code and json message.
#     """
#     # Not authenticated if user not logged in
#     response = await http_client_test.post(f"/user/get_details/?feature_key={feature_key}")
#     assert response.status_code == 401
#     assert response.json()["detail"] == "Not authenticated"
#
#     # Bad token for get all college user details
#     response = await http_client_test.post(
#         f"/user/get_details/?feature_key={feature_key}",
#         headers={"Authorization": f"Bearer wrong"}
#     )
#     assert response.status_code == 401
#     assert response.json() == {"detail": "Could not validate credentials"}
#
#     # Get all college user details by page number and page size
#     response = await http_client_test.post(
#         f"/user/get_details/?page_num=1&page_size=1&feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Get all user details."
#     for name in ["data", "total", "count", "pagination"]:
#         assert name in response.json()
#
#     # No permission for get all college user details
#     response = await http_client_test.post(
#         f"/user/get_details/?page_num=1&page_size=1&feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {access_token}"},
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "Not enough permissions"
#
#     # Get all college user details
#     response = await http_client_test.post(
#         f"/user/get_details/?feature_key={feature_key}",
#         headers={
#             "Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "data fetch successfully"
#     assert "data" in response.json()
#
#     # Get all college user details by sort data based on role
#     response = await http_client_test.post(
#         f"/user/get_details/?sort_type=asc&column_name=role&feature_key={feature_key}",
#         headers={
#             "Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "data fetch successfully"
#     assert "data" in response.json()
#
#     # Get all college user details by search pattern
#     response = await http_client_test.post(
#         f"/user/get_details/?search_pattern=user25&feature_key={feature_key}",
#         headers={
#             "Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "data fetch successfully"
#     assert "data" in response.json()
#
#     # Download all college user details
#     response = await http_client_test.post(
#         f"/user/get_details/?download_data=true&feature_key={feature_key}",
#         headers={
#             "Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "File downloaded successfully."
#     assert "file_url" in response.json()
#
#     # Download all college user details by search pattern
#     response = await http_client_test.post(
#         f"/user/get_details/?search_pattern=user25&download_data=true&feature_key={feature_key}",
#         headers={
#             "Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "File downloaded successfully."
#     assert "file_url" in response.json()
