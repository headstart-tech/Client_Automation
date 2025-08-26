"""
This file contains test cases related to get student call logs
"""
import pytest


@pytest.mark.asyncio
async def test_get_call_log(http_client_test, test_college_validation, setup_module, application_details,
                            test_call_history):
    """
    Get student call logs
    """
    response = await http_client_test.get(
        f"/student_call_log/{str(application_details.get('_id'))}/?college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 200
    assert response.json()["message"] == "Get the call logs."


@pytest.mark.asyncio
async def test_get_call_log_invalid_application_id(http_client_test, test_college_validation, setup_module):
    """
    Invalid application id for get student call logs
    """
    response = await http_client_test.get(
        f"/student_call_log/123456789012345678901234/?college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"
