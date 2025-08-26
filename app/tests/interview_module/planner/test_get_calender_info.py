"""
This file contains test cases of calender information(pi/gd information)
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

json_data={"filter_slot": [], "slot_status": [], "moderator": [], "slot_state": "", "program_name": []}
@pytest.mark.asycio
async def test_calender_info_not_authenticated(http_client_test, test_college_validation, setup_module, access_token,
                                college_super_admin_access_token, test_user_validation, test_month_year
                                ):
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/planner/calender_info/?month={test_month_year.get('month')}&year={test_month_year.get('year')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        json= json_data
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_calender_info_bad_token(http_client_test, test_college_validation, setup_module, access_token,
                                    college_super_admin_access_token, test_user_validation, test_month_year
                                    ):
    # Bad token to get details
    response = await http_client_test.post(
        f"/planner/calender_info/?month={test_month_year.get('month')}&year={test_month_year.get('year')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
        json=json_data
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_calender_info_college_required_field(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation, test_month_year
                                             ):
    # Required college id
    response = await http_client_test.post(
        f"/planner/calender_info/?month={test_month_year.get('month')}&year={test_month_year.get('year')}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=json_data
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'


@pytest.mark.asyncio
async def test_calender_info_required_month_field(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation, test_month_year
                                             ):
    # Required month field
    response = await http_client_test.post(
        f"/planner/calender_info/?month={test_month_year.get('month')}&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=json_data
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Year must be required and valid.'


@pytest.mark.asyncio
async def test_calender_info_required_year_field(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation, test_month_year
                                             ):
    #required year field
    response = await http_client_test.post(
        f"/planner/calender_info/?year={test_month_year.get('year')}&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=json_data
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Month must be required and valid.'


@pytest.mark.asyncio
async def test_calender_info_invalid_college_id(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation, test_month_year
                                             ):

    # Invalid college id
    response = await http_client_test.post(
        f"/planner/calender_info/?month={test_month_year.get('month')}&year={test_month_year.get('year')}"
        f"&college_id=123456&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=json_data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_calender_info_college_not_found(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation, test_month_year
                                             ):
    # College not found
    response = await http_client_test.post(
        f"/planner/calender_info/?month={test_month_year.get('month')}&year={test_month_year.get('year')}"
        f"&college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=json_data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_calender_info_month_not_valid(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation, test_month_year
                                             ):
    # given month is not valid
    response = await http_client_test.post(
        f"/planner/calender_info/?month=14&year={test_month_year.get('year')}&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=json_data
    )
    assert response.status_code == 400
    assert response.json()['detail'] == "Month must be required and valid."


@pytest.mark.asyncio
async def test_calender_info_year_format_not_valid(http_client_test, test_college_validation, setup_module, access_token,
                                             college_super_admin_access_token, test_user_validation, test_month_year
                                             ):
    # Year is not in valid format
    response = await http_client_test.post(
        f"/planner/calender_info/?month={test_month_year.get('month')}&year=23"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=json_data
    )
    assert response.status_code == 400
    assert response.json()['detail'] == "Year must be required and valid."


@pytest.mark.asyncio
async def test_calender_info(http_client_test, test_college_validation, setup_module, access_token,
                                college_super_admin_access_token, test_user_validation, test_month_year):
    #get calender info
    response = await http_client_test.post(
        f"/planner/calender_info/?month={test_month_year.get('month')}&year={test_month_year.get('year')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=json_data
    )
    assert response.status_code == 200
    assert response.json()[0]["PiTotal"] == 0
