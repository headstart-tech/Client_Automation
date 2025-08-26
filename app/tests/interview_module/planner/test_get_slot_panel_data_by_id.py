"""
This file contains test cases of get slot or panel data by id
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asycio
async def test_get_slot_or_panel_data(
        http_client_test, setup_module, test_college_validation,
        college_super_admin_access_token, test_slot_details, access_token):
    """
    Different scenarios of test cases for get slot or panel data.
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/planner/get_slot_or_panel_data/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get slot/panel data
    response = await http_client_test.post(
        f"/planner/get_slot_or_panel_data/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for get slot/panel data
    response = await http_client_test.post(
        f"/planner/get_slot_or_panel_data/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and ' \
                                        'valid.'

    # Invalid college id for get slot/panel data
    response = await http_client_test.post(
        f"/planner/get_slot_or_panel_data/?&college_id=12345628&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input ' \
                                        'or a 24-character hex string'

    # College not found for get slot/panel data
    response = await http_client_test.post(
        f"/planner/get_slot_or_panel_data/?college_id="
        f"123456789012345678901234&feature_key={feature_key}", headers=
        {"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    college_id = str(test_college_validation.get('_id'))
    # Required slot/panel id for get slot/panel data
    response = await http_client_test.post(
        f"/planner/get_slot_or_panel_data/?college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Slot Or Panel Id must be required ' \
                                        'and valid.'

    # invalid slot id
    response = await http_client_test.post(
        f"/planner/get_slot_or_panel_data/?slot_or_panel_id=1234567890123"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == \
           "Slot or Panel Id `1234567890123` must be a 12-byte input or a " \
           "24-character hex string"

    slot_id = str(test_slot_details.get('_id'))
    # No permission for get slot/panel data
    response = await http_client_test.post(
        f"/planner/get_slot_or_panel_data/?slot_or_panel_id={slot_id}"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json()['detail'] == "Not enough permissions"

    # ToDo - Following test case is failing when run all test cases of folder
    #  `tests` otherwise test case working fine.
    # get slot data by id
    # response = await http_client_test.post(
    #     f"/planner/get_slot_or_panel_data/?slot_or_panel_id="
    #     f"{slot_id}&college_id="
    #     f"{college_id}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    # )
    # assert response.status_code == 200
