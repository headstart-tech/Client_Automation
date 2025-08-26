"""
This file contains test cases related to API route/endpoint counselor productivity report
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_counselor_productivity_report_not_authenticate(
        http_client_test, test_college_validation, setup_module
):
    """
    Not authenticated For lead allocation counselor
    """
    response = await http_client_test.post(
        f"/counselor/counselor_productivity_report/?page_num=1&page_size=25"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f" wrong Bearer "},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_counselor_productivity_report_required_page_number(http_client_test, test_college_validation,
                                                                  college_super_admin_access_token,
                                                                  setup_module):
    """
    Required page number for get counselor productivity report
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/counselor/counselor_productivity_report/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == "Page Num must be required and valid."


@pytest.mark.asyncio
async def test_counselor_productivity_report_required_page_size(http_client_test, test_college_validation,
                                                                college_super_admin_access_token,
                                                                setup_module):
    """
    Test case -> required page size for get counselor productivity report
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/counselor/counselor_productivity_report/?page_num=1"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()['detail'] == "Page Size must be required and valid."

# ToDo - Following test cases giving error when running all test cases by folder because of college not found,
#  need to fix it
# @pytest.mark.asyncio
# async def test_counselor_productivity_report_counselor_not_found(http_client_test, test_college_validation, college_super_admin_access_token,
#                                                                  setup_module):
#     """
#     Counselor not found for lead allocation counselor
#     :param http_client_test:
#     :return:
#     """
#     from app.database.configuration import user_collection
#     await user_collection.delete_many({'role.role_name': 'college_counselor'})
#     response = await http_client_test.post(
#         f"/counselor/counselor_productivity_report/?page_num=1&page_size=25&college_id={str(test_college_validation.get('_id'))}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
#     assert response.status_code == 404
#     assert response.json()['detail'] == 'College counselor not found'
#
#
# @pytest.mark.asyncio
# async def test_counselor_productivity_report(http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
#                                              test_counselor_validation):
#     """
#     Counselor lead allocation
#     :param http_client_test:
#     :return:
#     """
#     response = await http_client_test.post(
#         f"/counselor/counselor_productivity_report/?page_num=1&page_size=25&college_id={str(test_college_validation.get('_id'))}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"})
#     assert response.status_code == 200
#     assert response.json()['message'] == "Get counselor productivity report."
