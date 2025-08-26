"""
This file contains test cases for successful lead
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_successful_lead_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/manage/show_successful_lead?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_successful_lead_required_page_num(http_client_test, test_college_validation, super_admin_access_token,
                                                 setup_module,
                                                 successful_lead):
    """
    Required page number for get the successful leads
    """
    response = await http_client_test.post(
        f"/manage/show_successful_lead?offline_id={str(successful_lead.get('offline_data_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}, )
    assert response.status_code == 400
    assert response.json()["detail"] == 'Page Num must be required and valid.'


@pytest.mark.asyncio
async def test_successful_lead_required_page_size(http_client_test, test_college_validation, super_admin_access_token,
                                                  setup_module,
                                                  successful_lead):
    """
    Required page size for get the successful leads
    """
    response = await http_client_test.post(
        f"/manage/show_successful_lead?offline_id={str(successful_lead.get('offline_data_id'))}"
        f"&page_num=1&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}, )
    assert response.status_code == 400
    assert response.json()["detail"] == 'Page Size must be required and valid.'


@pytest.mark.asyncio
async def test_successful_lead_no_permission(http_client_test, test_college_validation, super_admin_access_token,
                                             setup_module, successful_lead):
    """
    Permission required for get the successful leads
    """
    response = await http_client_test.post(
        f"/manage/show_successful_lead?offline_id={str(successful_lead.get('offline_data_id'))}&page_num=1"
        f"&page_size=5&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}, )
    assert response.status_code == 401
    assert response.json()["detail"] == 'Not enough permissions'


@pytest.mark.asyncio
async def test_successful_lead_invalid_id(http_client_test, test_college_validation, college_super_admin_access_token,
                                          setup_module):
    """
    If user try to get successful lead with invalid offline_id
    """
    response = await http_client_test.post(f"/manage/show_successful_lead?offline_id="
                                           f"63469aba9fea74b450e3753&page_num=1&page_size=5&"
                                           f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 422
    assert response.json()["detail"] == "offline_id must be a 12-byte input or a 24-character hex string"


@pytest.mark.asyncio
async def test_successful_leads(http_client_test, test_college_validation, college_super_admin_access_token,
                                successful_lead, setup_module):
    """
    When user will pass valid credentials, will get all successful leads
    on the basis of offline_id
    """
    response = await http_client_test.post(f"/manage/show_successful_lead?offline_id="
                                           f"{str(successful_lead.get('offline_data_id'))}&page_num=1&page_size=5&"
                                           f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetch successfully"
    assert response.json()["pagination"]["previous"] is None


@pytest.mark.asyncio
async def test_successful_leads_page_size(http_client_test, test_college_validation, college_super_admin_access_token,
                                          successful_lead, setup_module):
    """
    When user will pass valid credentials, will get all successful leads
    on the basis of offline_id
    """
    response = await http_client_test.post(f"/manage/show_successful_lead?offline_id="
                                           f"{str(successful_lead.get('offline_data_id'))}&page_num=1"
                                           f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Size must be required and valid."}


@pytest.mark.asyncio
async def test_successful_leads_required_offline_id(http_client_test, test_college_validation,
                                                    college_super_admin_access_token,
                                                    successful_lead, setup_module):
    """
    Required offline id
    When user will pass valid credentials, will get all successful leads
    on the basis of offline_id
    """
    response = await http_client_test.post(
        f"/manage/show_successful_lead?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 400
    assert response.json() == {'detail': 'Offline Id must be required and valid.'}


@pytest.mark.asyncio
async def test_successful_leads_required_page_num(http_client_test, test_college_validation,
                                                  college_super_admin_access_token, successful_lead,
                                                  setup_module):
    """
    When user will pass valid credentials, will get all successful leads
    on the basis of offline_id
    """
    response = await http_client_test.post(f"/manage/show_successful_lead?offline_id="
                                           f"{str(successful_lead.get('offline_data_id'))}&page_size=1&"
                                           f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 400
    assert response.json() == {"detail": "Page Num must be required and valid."}
