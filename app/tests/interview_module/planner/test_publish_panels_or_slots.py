"""
This file contains test cases of publish slots or panels by ids or
specific date
"""
import pytest
from datetime import datetime
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_publish_slots_or_panels_by_ids_or_specific_date_not_authenticated(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_slot_details,
        test_panel_validation, application_details):
    """
    Different scenarios of test cases for publish slots or panels by ids or
    specific date
    """
    college_id = str(test_college_validation.get('_id'))
    # Not authenticated if user not logged in
    response = await http_client_test.put(
        f"/planner/publish_slots_or_panels/?"
        f"college_id={college_id}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_publish_slots_or_panels_by_ids_or_specific_date_bad_token(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_slot_details,
        test_panel_validation, application_details):
    college_id = str(test_college_validation.get('_id'))
    # Bad token for publish slots or panels by ids or specific date
    response = await http_client_test.put(
        f"/planner/publish_slots_or_panels/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_publish_slots_or_panels_by_ids_or_specific_date_required_body(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_slot_details,
        test_panel_validation, application_details):
    college_id = str(test_college_validation.get('_id'))

    # Required body for publish slots or panels by ids or specific date
    response = await http_client_test.put(
        f"/planner/publish_slots_or_panels/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

@pytest.mark.asyncio
async def test_publish_slots_or_panels_by_ids_or_specific_date_publish_slot_or_panel(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_slot_details,
        test_panel_validation, application_details):
    college_id = str(test_college_validation.get('_id'))

    published_data = {"slots_panels_ids": [str(test_slot_details.get("_id"))]}
    # Publish slots or panels
    response = await http_client_test.put(
        f"/planner/publish_slots_or_panels/?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=published_data
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Published slots/panels."}

@pytest.mark.asyncio
async def test_publish_slots_or_panels_by_ids_or_specific_date_required_body_publish_slot_specific_date(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_slot_details,
        test_panel_validation, application_details):
    college_id = str(test_college_validation.get('_id'))

    current_date = datetime.utcnow()
    date = current_date.strftime("%Y-%m-%d")
    # Publish slots or panels by specific date
    response = await http_client_test.put(
        f"/planner/publish_slots_or_panels/?college_id={college_id}&"
        f"date={date}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Published slots/panels."}

@pytest.mark.asyncio
async def test_publish_slots_or_panels_by_ids_or_specific_date_required_body_required_college_id(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_slot_details,
        test_panel_validation, application_details):
    college_id = str(test_college_validation.get('_id'))
    published_data = {"slots_panels_ids": [str(test_slot_details.get("_id"))]}

    # Required college id for publish slots or panels by ids or
    # specific date
    response = await http_client_test.put(
        f"/planner/publish_slots_or_panels/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=published_data
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and ' \
                                        'valid.'

@pytest.mark.asyncio
async def test_publish_slots_or_panels_by_ids_or_specific_date_required_body_invalid_college_id(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_slot_details,
        test_panel_validation, application_details):
    college_id = str(test_college_validation.get('_id'))
    published_data = {"slots_panels_ids": [str(test_slot_details.get("_id"))]}
    
    # Invalid college id for publish slots or panels by ids or
    # specific date
    response = await http_client_test.put(
        f"/planner/publish_slots_or_panels/?college_id=1234567890&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=published_data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input ' \
                                        'or a 24-character hex string'

@pytest.mark.asyncio
async def test_publish_slots_or_panels_by_ids_or_specific_date_required_body_college_not_found(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_slot_details,
        test_panel_validation, application_details):
    college_id = str(test_college_validation.get('_id'))
    published_data = {"slots_panels_ids": [str(test_slot_details.get("_id"))]}
    
    # College not found when try to publish slots or panels by ids or
    # specific date
    response = await http_client_test.put(
        f"/planner/publish_slots_or_panels/?"
        f"college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=published_data
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

@pytest.mark.asyncio
async def test_publish_slots_or_panels_by_ids_or_specific_date_required_body_wrong_id(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_slot_details,
        test_panel_validation, application_details):
    college_id = str(test_college_validation.get('_id'))
    
    # Wrong id for publish slots/panels by ids
    response = await http_client_test.put(
        f"/planner/publish_slots_or_panels/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"slots_panels_ids": ["123"]}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Id `123` must be a 12-byte input or' \
                                        ' a 24-character hex string'
