# Todo: When run all the test cases then raising error otherwise working fine.
"""
This file contains test cases of change preference order.
"""
# import pytest
#
#
# @pytest.mark.asyncio
# async def test_manage_preference(
#         http_client_test, setup_module, test_college_validation,
#         college_super_admin_access_token, application_details,
#         test_course_data):
#     """
#     Different test cases of change preference order.
#
#     Params:\n
#         http_client_test: A fixture which return AsyncClient object.
#             Useful for test API with particular method.
#         setup_module: A fixture which upload necessary data in the db before
#             test cases start running/executing and delete data from collection
#              after test case execution completed.
#         test_college_validation: A fixture which create college if not exist
#             and return college data.
#         college_super_admin_access_token: A fixture which create college super
#             admin if not exist and return access token of college super admin.
#         application_details: A fixture which create application if not exist
#             and return application details.
#         test_course_data: A fixture which return sample course data.
#
#     Assertions:\n
#         response status code and json message.
#     """
#     # Test case -> not authenticated if user not logged in
#     response = await http_client_test.put(
#         "/student_application/manage_preference/")
#     assert response.status_code == 401
#     assert response.json()["detail"] == "Not authenticated"
#
#     college_id = str(test_college_validation.get("_id"))
#     application_id = str(application_details.get("_id"))
#     preference1 = application_details.get("spec_name1")
#     preference2 = test_course_data.get("course_specialization", [])[1].get("spec_name")
#     from app.database.configuration import DatabaseConfiguration
#     await DatabaseConfiguration().studentApplicationForms.update_one(
#         {"_id": application_details.get("_id")},
#         {
#             "$set": {
#                 "preference_info": [preference1, preference2],
#             }
#         }
#     )
#     # Test case -> bad token for change preference order
#     response = await http_client_test.put(
#         f"/student_application/manage_preference/?college_id={college_id}",
#         headers={"Authorization": f"Bearer wrong"}
#     )
#     assert response.status_code == 401
#     assert response.json() == {"detail": "Could not validate credentials"}
#
#     # Test case -> field `application_id` required for change
#     # preference order
#     response = await http_client_test.put(
#         f"/student_application/manage_preference/?"
#         f"college_id={college_id}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#     )
#     assert response.status_code == 400
#     assert response.json() == {"detail": "Application Id must be required "
#                                          "and valid."}
#
#     # Test case -> field `change_preference` required for change
#     # preference order
#     response = await http_client_test.put(
#         f"/student_application/manage_preference/?"
#         f"application_id={application_id}&college_id={college_id}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#     )
#     assert response.status_code == 400
#     assert response.json() == {"detail": "Change Preference must be required "
#                                          "and valid."}
#
#     # Test case -> field `change_preference` required for change
#     # preference order
#     response = await http_client_test.put(
#         f"/student_application/manage_preference/?"
#         f"application_id={application_id}&college_id={college_id}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#     )
#     assert response.status_code == 400
#     assert response.json() == {"detail": "Change Preference must be required "
#                                          "and valid."}
#
#     # Test case -> field `change_preference_with` required for change
#     # preference order
#     response = await http_client_test.put(
#         f"/student_application/manage_preference/?"
#         f"application_id={application_id}&college_id={college_id}&"
#         f"change_preference={preference2}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#     )
#     assert response.status_code == 400
#     assert response.json() == {"detail": "Change Preference With must be "
#                                          "required and valid."}
#
#     # Test case -> for change preference order
#     response = await http_client_test.put(
#         f"/student_application/manage_preference/?"
#         f"application_id={application_id}&change_preference={preference2}&"
#         f"change_preference_with={preference1}&college_id={college_id}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Preference order updated"
#     from app.database.configuration import DatabaseConfiguration
#     from bson import ObjectId
#     application = await DatabaseConfiguration().studentApplicationForms.find_one(
#         {"_id": ObjectId(application_id)}
#     )
#     assert application["preference_info"] == [preference2, preference1]
#
#     # Test case -> for change preference order
#     response = await http_client_test.put(
#         f"/student_application/manage_preference/?"
#         f"application_id={application_id}&change_preference=Preference3&"
#         f"change_preference_with={preference1}&college_id={college_id}",
#         headers={
#             "Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 400
#     assert response.json()["detail"] == ("Make sure provided correct "
#                                          "change preference order information.")
#
#     # Test case -> Required college id for change preference order.
#     response = await http_client_test.put(
#         f"/student_application/manage_preference/?"
#         f"application_id={application_id}&change_preference=Preference2&"
#         f"change_preference_with=Preference1",
#         headers={
#             "Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 400
#     assert response.json()["detail"] == ("College Id must be required "
#                                          "and valid.")
#
#     # Test case -> Invalid college id for change preference order.
#     response = await http_client_test.put(
#         f"/student_application/manage_preference/?"
#         f"application_id={application_id}&change_preference={preference2}&"
#         f"change_preference_with={preference1}&college_id=123",
#         headers={
#             "Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 422
#     assert response.json() == {"detail": "College id must be a 12-byte input "
#                                          "or a 24-character hex string"}
#
#     # Test case -> Wrong college id for change preference order.
#     response = await http_client_test.put(
#         f"/student_application/manage_preference/?"
#         f"application_id={application_id}&change_preference={preference2}&"
#         f"change_preference_with={preference1}&"
#         f"college_id=123456789012345678901234",
#         headers={
#             "Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 422
#     assert response.json()['detail'] == 'College not found.'
#
#     # Test case -> Invalid application id for change preference order.
#     response = await http_client_test.put(
#         f"/student_application/manage_preference/?"
#         f"application_id=123&change_preference={preference2}&"
#         f"change_preference_with={preference1}&college_id={college_id}",
#         headers={
#             "Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 422
#     assert (response.json() ==
#             {"detail": "Application id `123` must be a 12-byte "
#                        "input or a 24-character hex string"})
#
#     # Test case -> Invalid college id for change preference order.
#     response = await http_client_test.put(
#         f"/student_application/manage_preference/?"
#         f"application_id=123456789012345678901234&change_preference="
#         f"{preference2}&change_preference_with={preference1}&"
#         f"college_id={college_id}",
#         headers={
#             "Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 404
#     assert response.json()['detail'] == 'Application not found'
