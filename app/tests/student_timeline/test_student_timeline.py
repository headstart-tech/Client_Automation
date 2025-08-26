"""
This file contains test cases regarding student time apis
"""

import pytest


@pytest.mark.asyncio
async def test_get_student_timeline_not_found(
        http_client_test, test_college_validation, setup_module,
        application_details
):
    """
    Student timeline not found
    """
    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().studentTimeline.delete_many({})
    response = await http_client_test.post(
        f"/student_timeline/{str(application_details.get('_id'))}/?college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Student timeline not found."}


@pytest.mark.asyncio
async def test_get_student_timeline(
        http_client_test, test_college_validation, setup_module,
        application_details, student_timeline
):
    """
    Get student timeline
    """
    response = await http_client_test.post(
        f"/student_timeline/{str(application_details.get('_id'))}/?college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the student timelines."


@pytest.mark.asyncio
async def test_get_student_timeline_invalid_application_id(
        http_client_test, test_college_validation, setup_module,
        application_details
):
    """
    Invalid application id for get student timeline
    """
    response = await http_client_test.post(
        f"/student_timeline/2238dfe54035e93c7ff24612/?college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"


@pytest.mark.asyncio
async def test_get_timeline_of_followup_and_notes_application_not_found(
        http_client_test, test_college_validation, setup_module,
        application_details
):
    """
    Application not found for get student timeline
    """
    response = await http_client_test.post(
        f"/student_timeline/followup_and_notes/123456789012345678901234/?college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"
