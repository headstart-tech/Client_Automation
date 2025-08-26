"""
This file contains test cases for get calendar info
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_calendar_info_not_authenticated(
        http_client_test, setup_module, test_month_year,
        test_college_validation):
    """
    Not authenticate for get calendar info
    """
    response = await http_client_test.get(
        f"/counselor/"
        f"get_calendar_info/?date={test_month_year.get('day')}"
        f"&month={test_month_year.get('month')}"
        f"&year={test_month_year.get('year')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_get_calendar_info_required_college_id(http_client_test,
                                                     super_admin_access_token,
                                                     setup_module,
                                                     test_month_year):
    """
    Required college_id for get calender info
    """
    response = await http_client_test.get(
        f"/counselor/"
        f"get_calendar_info/?date={test_month_year.get('day')}"
        f"&month={test_month_year.get('month')}"
        f"&year={test_month_year.get('year')}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 400
    assert response.json() == {
        "detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_get_calendar_info_no_permission(http_client_test,
                                               test_college_validation,
                                               super_admin_access_token,
                                               setup_module, test_month_year):
    """
    Not permission for get calendar info
    """
    response = await http_client_test.get(
        f"/counselor/"
        f"get_calendar_info/?date={test_month_year.get('day')}"
        f"&month={test_month_year.get('month')}"
        f"&year={test_month_year.get('year')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {super_admin_access_token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_calendar_info_invalid_id(http_client_test,
                                            test_college_validation,
                                            college_super_admin_access_token,
                                            setup_module, test_month_year):
    """
    Get the details of acalendar info using invalid college_id
    """
    response = await http_client_test.get(
        f"/counselor/"
        f"get_calendar_info/?date={test_month_year.get('day')}"
        f"&month={test_month_year.get('month')}"
        f"&year={test_month_year.get('year')}"
        f"&college_id=1234&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}, )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "College id must be a 12-byte input or a 24-character hex string"}


@pytest.mark.asyncio
async def test_get_calendar_info_invalid_date(http_client_test,
                                              test_college_validation,
                                              college_counselor_access_token,
                                              setup_module, test_month_year):
    """
    Get the details of absent counselor
    """
    response = await http_client_test.get(
        f"/counselor/"
        f"get_calendar_info/?date=31"
        f"&month=9"
        f"&year={test_month_year.get('year')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_counselor_access_token}"}, )
    assert response.status_code == 400
    assert response.json()["detail"] == "InCorrect date"


@pytest.mark.asyncio
async def test_get_calendar_info(http_client_test, test_college_validation,
                                 college_counselor_access_token,
                                 setup_module, test_month_year):
    """
    Get the details of absent counselor
    """
    response = await http_client_test.get(
        f"/counselor/"
        f"get_calendar_info/?date={test_month_year.get('day')}"
        f"&month={test_month_year.get('month')}"
        f"&year={test_month_year.get('year')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_counselor_access_token}"}, )
    assert response.status_code == 200
    assert response.json()["message"] == "Get Calender Info"
