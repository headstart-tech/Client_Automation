"""
this file contains all counselor wise inbound router
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_counselor_wise_outbound_activity_not_authenticated(http_client_test, test_college_validation,
                                                                  setup_module):
    """
    test case for checking the authenticated
    """
    response = await http_client_test.put(f"/call_activities/counselor_wise_outbound_report"
                                          f"?page_num=1&page_size=25&college_id={str(test_college_validation.get('_id'))}"
                                          f"&feature_key={feature_key}",
                                          headers={"Authorization": "Bearer wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

# Todo - Following test cases failing maybe because of no any data in meilisearch index
# @pytest.mark.asyncio
# async def test_counselor_wise_outbound_activity(http_client_test, test_college_validation,
#                                                 college_super_admin_access_token, setup_module):
#     """
#     test case for the inbound activity
#     """
#     response = await http_client_test.put(f"/call_activities/counselor_wise_outbound_report"
#                                           f"?page_num=1&page_size=25&college_id={str(test_college_validation.get('_id'))}",
#                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
#     assert response.status_code == 200
#     assert response.json()["message"] == "Fetched calls data successfully"
#
#
# @pytest.mark.asyncio
# async def test_counselor_wise_outbound_activity_with_filter(http_client_test, test_college_validation,
#                                                             college_super_admin_access_token, setup_module):
#     """
#     test case with filter thing
#     """
#     response = await http_client_test.put(f"/call_activities/counselor_wise_outbound_report"
#                                           f"?page_num=1&page_size=25&lead_status=verify"
#                                           f"&college_id={str(test_college_validation.get('_id'))}",
#                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
#     assert response.status_code == 200
#     assert response.json()["message"] == "Fetched calls data successfully"
