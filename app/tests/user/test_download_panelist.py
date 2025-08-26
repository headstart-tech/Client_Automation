# ToDo - Following commented test cases giving error when run all test cases
# """
# This file contains test cases for download panelist data by IDs
# """
# import pytest
#
#
# @pytest.mark.asyncio
# async def test_download_panelist(http_client_test, setup_module,
#                                  college_super_admin_access_token,
#                                  test_panelist_validation, access_token):
#     """
#     Different test cases scenarios for download panelist data
#     """
#     college_id = str(test_panelist_validation.get("associated_colleges")[0])
#     # Not authenticated if user not logged in
#     response = await http_client_test.post(f"/user/download_panelist/?college_id={college_id}")
#     assert response.status_code == 401
#     assert response.json()["detail"] == "Not authenticated"
#
#     # Bad token for download panelist data
#     response = await http_client_test.post(
#         f"/user/download_panelist/?college_id={college_id}", headers={"Authorization": f"Bearer wrong"}
#     )
#     assert response.status_code == 401
#     assert response.json() == {"detail": "Could not validate credentials"}
#
#     # Download panelist data without passing ids
#     response = await http_client_test.post(
#         f"/user/download_panelist/?college_id={college_id}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#     )
#     assert response.status_code == 200
#     assert response.json()['message'] == "File downloaded successfully."
#     assert "file_url" in response.json()
#
#     # download panelist data by IDs
#     response = await http_client_test.post(
#         f"/user/download_panelist/?college_id={college_id}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#         , json=[f"{str(test_panelist_validation.get('_id'))}"]
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "File downloaded successfully."
#     assert "file_url" in response.json()
#
#     # Wrong panelist id
#     response = await http_client_test.post(
#         f"/user/download_panelist/?college_id={college_id}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#         , json=["1234567890"]
#     )
#     assert response.status_code == 422
#     assert response.json()["detail"] == "Panelist id `1234567890` must be a" \
#                                         " 12-byte input or a 24-character " \
#                                         "hex string"
#
#     # Download panelist data by IDs
#     response = await http_client_test.post(
#         f"/user/download_panelist/?college_id={college_id}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#         , json=[f"{str(test_panelist_validation.get('_id'))}"]
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "File downloaded successfully."
#     assert "file_url" in response.json()
#
#     # Panelist data no found
#     from app.database.configuration import DatabaseConfiguration
#     await DatabaseConfiguration().user_collection.delete_many(
#         {"role.role_name":
#              "panelist"})
#     response = await http_client_test.post(
#         f"/user/download_panelist/?college_id={college_id}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#     )
#     assert response.status_code == 404
#     assert response.json() == {"detail": "Panelist not found."}
#
#     # No permission for download panelist data
#     response = await http_client_test.post(
#         f"/user/download_panelist/?college_id={college_id}",
#         headers={"Authorization": f"Bearer {access_token}"},
#     )
#     assert response.status_code == 401
#     assert response.json()["detail"] == "Not enough permissions"
