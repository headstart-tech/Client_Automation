"""
This file contains the test cases of  today_application_count in
 application routes
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_today_application_count_not_authenticated(
        http_client_test,
        test_college_validation,
        setup_module):
    """
    Check the user is not authenticated
    """
    response = await http_client_test.get(
        f"/application_wrapper/"
        f"today_application_count"
        f"?college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

# TODO: API got updated by virendra, need to update the testcase
# @pytest.mark.asyncio
# async def test_today_application_count(
#         http_client_test,
#         test_college_validation,
#         setup_module,
#         college_super_admin_access_token):
#     """
#     get data from the database
#     """
#     response = await http_client_test.get(
#         f"/application_wrapper/"
#         f"today_application_count"
#         f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
#         headers={
#             "Authorization": f"Bearer {college_super_admin_access_token}"})
#     assert response.status_code == 200
