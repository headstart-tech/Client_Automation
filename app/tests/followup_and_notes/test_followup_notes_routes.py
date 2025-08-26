"""
This file contains test cases related to followup-notes routes
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_followup_notes_not_authenticated(http_client_test, test_college_validation,
                                                setup_module):
    """
    Test case -> not authenticated if followup_notes not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.put(f"/followup_notes/62ac13e38ad84805ecae3d7c/"
                                          f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_followup_notes_bad_credentials(http_client_test, test_college_validation,
                                              setup_module):
    """
    Test case -> bad token for followup_notes
    :param http_client_test:
    :return:
    """
    response = await http_client_test.put(
        f"/followup_notes/62ac13e38ad84805ecae3d7c/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_followup_notes_no_permission(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    Test case -> no permission for get followup_notes
    :param http_client_test:
    :param access_token:
    :return:
    """
    response = await http_client_test.put(
        f"/followup_notes/62a9b8774035e93c7ff2466f/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "note": "no answer Whats app sent",
            "followup": {
                "assigned_counselor_id": "62bfd13a5ce8a398ad101bd7",
                "followup_date": "06/06/2022 08:19 am",
                "followup_note": "Take followup on time",
            },
            "lead_stage": "string",
            "application_substage": "string",
        },
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_followup_notes(
        http_client_test, college_super_admin_access_token, setup_module, application_details,
        test_college_validation
):
    """
    Add followup_notes
    """
    from app.database.configuration import DatabaseConfiguration
    from bson import ObjectId
    await DatabaseConfiguration().leadsFollowUp.delete_many(
        {"application_id": ObjectId(str(application_details.get('_id')))})
    response = await http_client_test.put(f"/followup_notes/{str(application_details.get('_id'))}/"
                                          f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
                                          headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                          json={
                                              "note": "no answer Whats app sent"
                                          },
                                          )
    assert response.status_code == 200
    assert response.json()["message"] == "Follow-up and notes data added."


@pytest.mark.asyncio
async def test_followup_notes_not_found(
        http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    Test case -> not found for get followup_notes
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.put(
        f"/followup_notes/62ac13e38ad84805ecae3d7c/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "note": "no answer Whats app sent",
            "followup": {
                "assigned_counselor_id": "62bfd13a5ce8a398ad101bd7",
                "followup_date": "06/06/2022 08:19 am",
                "followup_note": "Take followup on time",
            },
            "lead_stage": "string",
            "application_substage": "string",
        },
    )
    assert response.status_code == 404
    assert (
            response.json()["detail"]
            == "Application not found. Enter correct application id."
    )


@pytest.mark.asyncio
async def test_followup_notes_wrong_type_application_id(
        http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    Test case -> invalid application id for get followup_notes
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.put(
        f"/followup_notes/62ac13e38ad84805ae/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "note": "no answer Whats app sent",
            "followup": {
                "assigned_counselor_id": "62bfd13a5ce8a398ad101bd7",
                "followup_date": "06/06/2022 08:19 am",
                "followup_note": "Take followup on time",
            },
            "lead_stage": "string",
            "application_substage": "string",
        },
    )
    assert response.status_code == 422
    assert (
            response.json()["detail"]
            == "Application id must be a 12-byte input or a 24-character hex string."
    )


@pytest.mark.asyncio
async def test_followup_notes_add(
        http_client_test, college_super_admin_access_token, setup_module, application_details,
        test_college_validation
):
    """
    Test case -> for update followup_notes
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.put(
        f"/followup_notes/{str(application_details.get('_id'))}/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"notes": {"note": "no answer Whats app sent"}},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get follow-up and notes."


@pytest.mark.asyncio
async def test_update_followup_status_not_authenticated(http_client_test,
                                                        test_college_validation, setup_module):
    """
    Test case -> not authenticated if update_followup_status not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.put(
        f"/followup_notes/update_followup_status/62ac13e38ad84805ecae3d7c/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_followup_status_bad_credentials(http_client_test, setup_module, test_college_validation):
    """
    Test case -> bad token for update followup status
    :param http_client_test:
    :return:
    """
    response = await http_client_test.put(
        f"/followup_notes/update_followup_status/62ac13e38ad84805ecae3d7c/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_update_followup_status_no_permission(
        http_client_test, access_token, setup_module, application_details, test_college_validation
):
    """
    Test case -> no permission for get update_followup_status
    :param http_client_test:
    :param access_token:
    :return:
    """
    response = await http_client_test.put(
        f"/followup_notes/update_followup_status/{str(application_details.get('_id'))}/"
        f"?status=true&followup_datetime=06/06/2022 08:19 am&index_number=0"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_update_followup_status_required(
        http_client_test, college_super_admin_access_token, setup_module, test_college_validation
):
    """
    Test case -> status required for get update_followup_status
    :param http_client_test:
    :param college_super_admin_access_token:
    :return:
    """
    response = await http_client_test.put(
        f"/followup_notes/update_followup_status/62ac13e38ad84805ecae3d7c/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Status must be required and valid."
