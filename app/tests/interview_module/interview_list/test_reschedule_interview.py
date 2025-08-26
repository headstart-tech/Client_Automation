"""
This file contains the rescheduled route test cases
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_rescheduled_interview_not_authenticated(
        http_client_test,
        setup_module,
        application_details,
        test_slot_details
):
    """
        Rescheduled interview application not authenticated.

        Params:\n
            http_client_test: This is the http client url
            test_slot_details: get data of slot collection
            application_details: get application data.
            setup_module: This is upload data and delete in database
            collection.
        Assertions:\n
            response status code and json message
    """
    response = await http_client_test.post(f"/interview_list"
                                           f"/reschedule_interview"
                                           f"?slot_id={str(test_slot_details.get('_id'))}"
                                           f"&application_id={str(application_details.get('_id'))}"
                                           f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not authenticated'


@pytest.mark.asyncio
async def test_rescheduled_interview_no_permission(
        http_client_test,
        setup_module,
        application_details,
        test_slot_details,
        access_token
):
    """
        Rescheduled interview application no permission.

        Params:\n
            http_client_test: This is the http client url
            test_slot_details: get data of slot collection
            application_details: get application data.
            setup_module: This is upload data and delete in database
            collection.
            access_token: get student access token
        Assertions:\n
            response status code and json message
    """
    response = await http_client_test.post(
        f"/interview_list"
        f"/reschedule_interview"
        f"?origin_slot_id={str(test_slot_details.get('_id'))}"
        f"&reschedule_slot_id={str(test_slot_details.get('_id'))}"
        f"&application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={
            "authorization": f"Bearer {access_token}"})
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not enough permissions'


@pytest.mark.asyncio
async def test_rescheduled_interview_invalid_slot_id(
        http_client_test,
        setup_module,
        application_details,
        test_slot_details,
        college_super_admin_access_token
):
    """
        Rescheduled interview application invalid slot id.

        Params:\n
            http_client_test: This is the http client url
            test_slot_details: get data of slot collection
            application_details: get application data.
            setup_module: This is upload data and delete in database
            collection.
            college_super_admin_access_token: get student access token
        Assertions:\n
            response status code and json message
    """
    response = await http_client_test.post(
        f"/interview_list"
        f"/reschedule_interview"
        f"?origin_slot_id=65768676568765"
        f"&reschedule_slot_id={str(test_slot_details.get('_id'))}"
        f"&application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={
            "authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == f"Slot id must be a 12-byte" \
                                        f" input or a 24-character hex string"


@pytest.mark.asyncio
async def test_rescheduled_interview_invalid_application_id(
        http_client_test,
        setup_module,
        application_details,
        test_slot_details,
        college_super_admin_access_token
):
    """
        Rescheduled interview application invalid slot id.

        Params:\n
            http_client_test: This is the http client url
            test_slot_details: get data of slot collection
            application_details: get application data.
            setup_module: This is upload data and delete in database
            collection.
            college_super_admin_access_token: get student access token
        Assertions:\n
            response status code and json message
    """
    response = await http_client_test.post(
        f"/interview_list"
        f"/reschedule_interview"
        f"?origin_slot_id={str(test_slot_details.get('_id'))}"
        f"&reschedule_slot_id={str(test_slot_details.get('_id'))}"
        f"&application_id=1233545676876755&feature_key={feature_key}",
        headers={
            "authorization": f"Bearer {college_super_admin_access_token}"})
    assert response.status_code == 422
    assert response.json()['detail'] == f"Application id must be a 12-byte" \
                                        f" input or a 24-character hex string"
