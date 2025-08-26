"""
This file contains test cases of panels, slots , hours information
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asycio
async def test_panels_slots_hours_not_authenticated(http_client_test, test_college_validation, setup_module,
                                                    test_month_year):
    # Not authenticated if user not logged in
    response = await http_client_test.get(
        f"/planner/date_wise_panel_slot_hours/?is_slot=true&date={test_month_year.get('date')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}" )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_panels_slots_hours_bad_token(http_client_test, test_college_validation, setup_module,
                                    college_super_admin_access_token,  test_month_year):
    # Bad token to get details
    response = await http_client_test.get(
        f"/planner/date_wise_panel_slot_hours/?is_slot=true&date={test_month_year.get('date')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_panels_slots_hours_college_required_field(http_client_test, test_college_validation, setup_module,
                                             college_super_admin_access_token,  test_month_year
                                             ):
    # Required college id
    response = await http_client_test.get(
        f"/planner/date_wise_panel_slot_hours/?is_slot=true&date={test_month_year.get('date')}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'


@pytest.mark.asyncio
async def test_panels_slots_hours_required_date_field(http_client_test, test_college_validation, setup_module,
                                             college_super_admin_access_token
                                             ):
    # Required date field
    response = await http_client_test.get(
        f"/planner/date_wise_panel_slot_hours/?is_slot=true&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Date must be required and valid.'


@pytest.mark.asyncio
async def test_panels_slots_hours_required_is_slot_field(http_client_test, test_college_validation, setup_module,
                                             college_super_admin_access_token,test_month_year):
    # Required is_slot field
    response = await http_client_test.get(
        f"/planner/date_wise_panel_slot_hours/?date={test_month_year.get('date')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Is Slot must be required and valid.'


@pytest.mark.asyncio
async def test_panels_slots_hours_invalid_college_id(http_client_test, test_college_validation, setup_module,
                                             college_super_admin_access_token, test_month_year
                                             ):

    # Invalid college id
    response = await http_client_test.get(
        f"/planner/date_wise_panel_slot_hours/?is_slot=true&date={test_month_year.get('date')}"
        f"&college_id=1223&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_panels_slots_hours_college_not_found(http_client_test, test_college_validation, setup_module,
                                             college_super_admin_access_token,  test_month_year
                                             ):
    # College not found
    response = await http_client_test.get(
        f"/planner/date_wise_panel_slot_hours/?is_slot=true&date={test_month_year.get('date')}"
        f"&college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

@pytest.mark.asyncio
async def test_panels_slots_hours(http_client_test, test_college_validation, setup_module, access_token,
                                college_super_admin_access_token, test_month_year):
    # get panels, slots, hours information
    response = await http_client_test.get(
        f"/planner/date_wise_panel_slot_hours/?is_slot=true&date={test_month_year.get('date')}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert "date" in response.json()[0]

