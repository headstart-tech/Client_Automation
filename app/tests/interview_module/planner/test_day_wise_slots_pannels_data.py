"""
This file contains test cases of get day-wise slots and panels data
"""
import datetime
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asycio
async def test_get_day_wise_slots_panels_data(
        http_client_test, test_college_validation, setup_module, access_token,
        college_super_admin_access_token, test_user_validation):
    """
    Different test cases scenarios for get day-wise slots and panels info.
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/planner/day_wise_slot_panel_data/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token to get day-wise slots and panels data
    response = await http_client_test.post(
        f"/planner/day_wise_slot_panel_data/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id to get day-wise slots and panels data
    response = await http_client_test.post(
        f"/planner/day_wise_slot_panel_data/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and ' \
                                        'valid.'

    # Invalid college id to get day-wise slots and panels data
    response = await http_client_test.post(
        f"/planner/day_wise_slot_panel_data/?college_id=12345628&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input' \
                                        ' or a 24-character hex string'

    # College not found when try to get day-wise slots and panels data
    response = await http_client_test.post(
        f"/planner/day_wise_slot_panel_data/"
        f"?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    # Get day-wise slots and panels data (default case)
    response = await http_client_test.post(
        f"/planner/day_wise_slot_panel_data/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get day-wise slots and panels data."
    resp = response.json()["data"]
    resp_data = resp[0]
    date_str = (datetime.datetime.utcnow() + datetime.timedelta(
                hours=5, minutes=30)).strftime("%a, %b %d, %Y")
    assert date_str in [resp_data.get("date"), resp[1].get("date")]
    test_data = [
        (resp_data, ["date", "allTime", "activePI", "activeGD", "totalPI",
                     "totalGD"]), (resp_data["allTime"][0],
                                   ["time", "allPanel", "allSlot"])]
    for data, fields in test_data:
        for field in fields:
            assert field in data

    # Get day-wise slots and panels data (for specific date)
    from app.core.utils import utility_obj
    response = await http_client_test.post(
        f"/planner/day_wise_slot_panel_data/"
        f"?college_id={str(test_college_validation.get('_id'))}"
        f"&date=2020-12-01&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get day-wise slots and panels data."
    resp = response.json()["data"]
    resp_data = resp[0]
    date_utc = await utility_obj.date_change_utc("2020-12-02",
                                                 date_format="%Y-%m-%d")
    date_str = date_utc.strftime("%a, %b %d, %Y")
    assert date_str in [resp_data.get("date"), resp[1].get("date")]
    for data, fields in test_data:
        for field in fields:
            assert field in data
