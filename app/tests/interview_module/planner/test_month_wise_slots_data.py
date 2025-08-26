"""
This file contains test cases of get day-wise slots data
"""
import datetime

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asycio
async def test_get_month_wise_slots_data(
        http_client_test, test_interview_list_validation,
        test_college_validation, setup_module, access_token,
        application_details, test_slot_details):
    """
    Different test cases scenarios for get month-wise slots info.
    """
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/planner/month_wise_slots_info/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token to get month-wise slots data
    response = await http_client_test.post(
        f"/planner/month_wise_slots_info/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id to get month-wise slots data
    response = await http_client_test.post(
        f"/planner/month_wise_slots_info/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and ' \
                                        'valid.'

    # Invalid college id to get month-wise slots data
    response = await http_client_test.post(
        f"/planner/month_wise_slots_info/?college_id=12345628&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input' \
                                        ' or a 24-character hex string'

    # College not found when try to get month-wise slots data
    response = await http_client_test.post(
        f"/planner/month_wise_slots_info/"
        f"?college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentApplicationForms.update_one(
        {"_id": application_details.get("_id")},
        {"$set": {"interview_list_id":
                      [test_interview_list_validation.get('_id')]}})
    # Get month-wise slots data
    response = await http_client_test.post(
        f"/planner/month_wise_slots_info/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"application_id": str(application_details.get("_id"))}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get month-wise slots data."
    resp = response.json()["data"]
    date_str = (datetime.datetime.utcnow() + datetime.timedelta(
        hours=5, minutes=30)).strftime("%d")
    assert date_str in [item.get("date") for item in resp]

    # Invalid application id for get month-wise slots data
    response = await http_client_test.post(
        f"/planner/month_wise_slots_info/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"application_id": "123"}
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Application id `123` must be a " \
                                        "12-byte input or a 24-character " \
                                        "hex string"
