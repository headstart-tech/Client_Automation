"""
This file contains test cases for get leads application data
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_leads_application_data_not_authenticated(http_client_test, setup_module, test_month_year,
                                                   test_college_validation):
    """
    Not authenticate for get leads and application data
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_leads_application_data?date={test_month_year.get('date_YMD')}"
                                          f"&lead_data=true"
                                          f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_get_leads_application_data_bad_token(http_client_test, test_college_validation, college_counselor_access_token,
                                 setup_module, test_month_year, super_admin_access_token):
    """
    bad token to get application data
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_leads_application_data?date={test_month_year.get('date_YMD')}"
                                          f"&lead_data=true"
                                          f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}, )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_get_leads_application_data_required_date(http_client_test, super_admin_access_token,
                                                        setup_module, test_month_year, test_college_validation):
    """
    Required college_id for get leads_application_data
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_leads_application_data?"
                                          f"lead_data=true"
                                          f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Date must be required and valid."}


@pytest.mark.asyncio
async def test_get_leads_application_data_required_college_id(http_client_test, super_admin_access_token,
                                                     setup_module, test_month_year):
    """
    Required college_id for get leads_application_data
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_leads_application_data?date={test_month_year.get('date_YMD')}"
                                          f"&lead_data=true&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_get_leads_application_data_invalid_college_id(http_client_test, super_admin_access_token,
                                                             setup_module, test_month_year):
    """
    invalid  college_id for get leads_application_data
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_leads_application_data?date={test_month_year.get('date_YMD')}"
                                          f"&lead_data=true"
                                          f"&college_id=1234&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json() == {"detail": 'College id must be a 12-byte input ' \
                                        'or a 24-character hex string'}

@pytest.mark.asyncio
async def test_get_leads_application_data_not_found_college_id(http_client_test, super_admin_access_token,
                                                             setup_module, test_month_year):
    """
    not found college_id for get leads_application_data
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_leads_application_data?date={test_month_year.get('date_YMD')}"
                                          f"&lead_data=true"
                                          f"&college_id=123456789012345678901234&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json() == {"detail": 'College not found.'}

@pytest.mark.asyncio
async def test_get_leads_application_data_no_permission(http_client_test, test_college_validation, super_admin_access_token,
                                               setup_module, test_month_year):
    """
    Not permission for get leads_application_data
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_leads_application_data?date={test_month_year.get('date_YMD')}"
                                          f"&lead_data=true"
                                          f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_leads_applications_data_invalid_id(http_client_test, test_college_validation,
                                            college_super_admin_access_token, setup_module, test_month_year):
    """
    Get the details of leads application data using invalid college_id
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_leads_application_data?date={test_month_year.get('date_YMD')}"
                                          f"&lead_data=true"
                                          f"&college_id=1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input or a 24-character hex string"}

@pytest.mark.asyncio
async def test_get_leads_application_data_invalid_date(http_client_test, test_college_validation,
                                              college_counselor_access_token,setup_module, test_month_year):
    """
    Get the details of leads application data
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_leads_application_data?date=31"
                                          f"&lead_data=true"
                                          f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"}, )
    assert response.status_code == 400
    assert response.json()["detail"] == "InCorrect date"

@pytest.mark.asyncio
async def test_get_leads_application_data(http_client_test, test_college_validation, college_counselor_access_token,
                                 setup_module, test_month_year):
    """
    Get the details of leads_application data
    """
    response = await http_client_test.get(f"/counselor/"
                                          f"get_leads_application_data?date={test_month_year.get('date_YMD')}"
                                          f"&lead_data=true"
                                          f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"}, )
    assert response.status_code == 200
    assert response.json()["message"] == "Get leads and application data."
