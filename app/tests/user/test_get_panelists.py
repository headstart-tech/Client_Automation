# ToDo - Following commented test cases giving error when run all test cases
# """
# This file contains test cases of get panelists data
# """
# import pytest
#
#
# @pytest.mark.asyncio
# async def test_get_panelists_data(
#         http_client_test, setup_module, access_token,
#         college_super_admin_access_token, test_panelist_validation):
#     """
#     Different test cases of get panelist data.
#     """
#     college_id = str(test_panelist_validation.get("associated_colleges")[0])
#     # Not authenticated if user not logged in
#     response = await http_client_test.post(f"/user/panelists/?college_id={college_id}")
#     assert response.status_code == 401
#     assert response.json()["detail"] == "Not authenticated"
#
#     # Wrong token for get panelists data
#     response = await http_client_test.post(
#         f"/user/panelists/?college_id={college_id}", headers={"Authorization": f"Bearer wrong"}
#     )
#     assert response.status_code == 401
#     assert response.json() == {"detail": "Could not validate credentials"}
#
#     # No permission for get panelists data
#     response = await http_client_test.post(
#         f"/user/panelists/?college_id={college_id}", headers={"Authorization": f"Bearer {access_token}"}
#     )
#     assert response.status_code == 401
#     assert response.json() == {"detail": "Not enough permissions"}
#
#     # Get panelists data
#     response = await http_client_test.post(
#         f"/user/panelists/?college_id={college_id}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "List of panelists fetched " \
#                                          "successfully."
#     for name in ["_id", "name", "school", "designation", "selected_programs",
#                  "email"]:
#         assert name in response.json()['data'][0]
#
#     # Get panelists data by page number and page size
#     response = await http_client_test.post(
#         f"/user/panelists/?page_num=1&page_size=1&college_id={college_id}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "List of panelists fetched " \
#                                          "successfully."
#     assert response.json()["total"] == 1
#     assert response.json()["count"] == 1
#     assert response.json()["pagination"] == {"previous": None, "next": None}
#     for name in ["_id", "name", "school", "designation", "selected_programs",
#                  "email"]:
#         assert name in response.json()['data'][0]
#
#     # No panelist found
#     from app.database.configuration import DatabaseConfiguration
#     await DatabaseConfiguration().user_collection.delete_many(
#         {"role.role_name":
#                                                         "panelist"})
#     response = await http_client_test.post(
#         f"/user/panelists/?college_id={college_id}",
#         headers={
#             "Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Panelists not found."
#     assert response.json()["data"] == []
