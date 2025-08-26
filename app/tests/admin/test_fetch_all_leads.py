"""
This file contains test cases for fetch all leads
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_all_leads_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/admin/all_leads/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_all_leads_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for fetch all leads
    """
    response = await http_client_test.post(
        f"/admin/all_leads/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_all_leads_required_page_num(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required page number for fetch all leads
    """
    response = await http_client_test.post(
        f"/admin/all_leads/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Num must be required and valid."}


@pytest.mark.asyncio
async def test_get_all_leads_required_page_size(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required page number for fetch all leads
    """
    response = await http_client_test.post(
        f"/admin/all_leads/?page_num=1&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Size must be required and valid."}


@pytest.mark.asyncio
async def test_get_all_leads_no_permission(
        http_client_test, test_college_validation, super_admin_access_token, setup_module
):
    """
    No permission for fetch all leads
    """
    response = await http_client_test.post(
        f"/admin/all_leads/?page_num=1&page_size=1&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_all_leads_required_college_id(http_client_test,
                                                 test_college_validation,
                                                 college_super_admin_access_token,
                                                 setup_module):
    """
    Required college id for fetch all leads
    """
    response = await http_client_test.post(
        f"/admin/all_leads/?page_num=1&page_size=1&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json()[
               'detail'] == 'College Id must be required and valid.'


@pytest.mark.asyncio
async def test_get_all_leads_invalid_college_id(http_client_test,
                                                test_college_validation,
                                                college_super_admin_access_token,
                                                setup_module):
    """
    Invalid college id for fetch all leads
    """
    response = await http_client_test.post(
        f"/admin/all_leads/?college_id=1234567890&page_num=1&page_size=1&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()[
               'detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_get_all_leads_college_not_found(http_client_test,
                                               test_college_validation,
                                               college_super_admin_access_token,
                                               setup_module):
    """
    College not found for fetch all leads
    """
    response = await http_client_test.post(
        f"/admin/all_leads/?college_id=123456789012345678901234&page_num=1&page_size=1&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_get_all_leads_no_found(http_client_test,
                                      test_college_validation,
                                      college_super_admin_access_token,
                                      setup_module):
    """
    Get all leads no found
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentsPrimaryDetails.delete_many({})
    response = await http_client_test.post(
        f"/admin/all_leads/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Leads data fetched successfully!"
    # assert response.json()['data'] == []
    # assert response.json()['count'] == 1
    # assert response.json()['total'] == 1
    assert response.json()['pagination']["next"] is None
    assert response.json()['pagination']["previous"] is None


@pytest.mark.asyncio
async def test_get_all_leads_for_1st_page(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, application_details
):
    """
    Get all leads
    """
    response = await http_client_test.post(
        f"/admin/all_leads/?page_num=1&page_size=1&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Leads data fetched successfully!"
    if response.json()["data"]:
        columns = ['application_id', 'student_id', 'student_name', 'custom_application_id', 'student_email_id',
                   'student_mobile_no', 'payment_status', "verification", "twelve_marks_name"]
        for column in columns:
            assert column in response.json()["data"][0]


@pytest.mark.asyncio
async def test_get_all_leads_no_data_for_page(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    no data found for fetch all leads
    """
    response = await http_client_test.post(
        f"/admin/all_leads/?page_num=441&page_size=1&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Leads data fetched successfully!"
    assert response.json()["data"] == []
    assert response.json()["pagination"]["next"] is None


@pytest.mark.asyncio
async def test_get_all_leads_by_season_wise(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, start_end_date,
        application_details
):
    """
    Get all leads by season wise
    """
    response = await http_client_test.post(
        f"/admin/all_leads/?page_num=1&page_size=1&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={'season': 'test'})
    assert response.status_code == 200
    assert response.json()["message"] == "Leads data fetched successfully!"
    if response.json()["data"]:
        columns = ['application_id', 'student_id', 'student_name',
                   'custom_application_id', 'student_email_id',
                   'student_mobile_no', 'payment_status', "verification",
                   "twelve_marks_name"]
        for column in columns:
            assert column in response.json()["data"][0]


@pytest.mark.asyncio
async def test_get_all_leads_by_season_wise_no_found(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, start_end_date
):
    """
    No found data for fetch all leads by season wise
    """
    response = await http_client_test.post(
        f"/admin/all_leads/?page_num=1&page_size=1&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"},
        json={'season': 'test'})
    assert response.status_code == 200
    assert response.json()["message"] == "Leads data fetched successfully!"
    assert response.json()["pagination"]["next"] is None


@pytest.mark.asyncio
async def test_get_all_leads_with_column_utm_medium_and_campaign(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, application_details
):
    """
    Get leads data with column named utm medium and utm_campaign
    """
    response = await http_client_test.post(
        f"/admin/all_leads/?page_num=1&page_size=1&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"utm_medium_b": True, "utm_campaign_b": True}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Leads data fetched successfully!"
    assert response.json()["data"] is not None
    if response.json()["data"]:
        columns = ['application_id', 'student_id', 'student_name', 'custom_application_id', 'student_email_id',
                   "course_name", 'student_mobile_no', 'payment_status', 'utm_medium', 'utm_campaign', "verification",
                   "twelve_marks_name"]
        for column in columns:
            assert column in response.json()["data"][0]
