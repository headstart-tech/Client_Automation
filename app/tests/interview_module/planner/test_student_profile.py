"""
This file contains test cases to display student profile
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asycio
async def test_student_profile_not_authenticated(http_client_test, test_college_validation, setup_module,
                                    application_details
                                ):
    from app.database.configuration import DatabaseConfiguration
    interview_list = await DatabaseConfiguration().interview_list_collection.find_one(
        {})
    interview_list_id = str(interview_list.get('_id'))
    # Not authenticated if user not logged in
    response = await http_client_test.get(
        f"/planner/student_profile/?interview_list_id={interview_list_id}&application_id="
        f"{str(application_details.get('_id'))}&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_student_profile_bad_token(http_client_test, test_college_validation, setup_module, application_details
                                    ):
    # Bad token to get details
    from app.database.configuration import DatabaseConfiguration
    interview_list = await DatabaseConfiguration().interview_list_collection.find_one(
        {})
    interview_list_id = str(interview_list.get('_id'))
    response = await http_client_test.get(
        f"/planner/student_profile/?interview_list_id={interview_list_id}&"
        f"application_id={str(application_details.get('_id'))}&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_student_profile_required_college_id(http_client_test, test_college_validation, setup_module,
                                             college_super_admin_access_token,  application_details
                                             ):
    # Required college id
    from app.database.configuration import DatabaseConfiguration
    interview_list = await DatabaseConfiguration().interview_list_collection.find_one(
        {})
    interview_list_id = str(interview_list.get('_id'))
    response = await http_client_test.get(
        f"/planner/student_profile/?interview_list_id={interview_list_id}&"
        f"application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'


@pytest.mark.asyncio
async def test_student_profile_required_application_id(http_client_test, test_college_validation, setup_module,
                                             college_super_admin_access_token,application_details
                                             ):
    # Required application id
    from app.database.configuration import DatabaseConfiguration
    interview_list = await DatabaseConfiguration().interview_list_collection.find_one(
        {})
    interview_list_id = str(interview_list.get('_id'))
    response = await http_client_test.get(
        f"/planner/student_profile/?interview_list_id={interview_list_id}&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Application Id must be required and valid.'


async def test_student_profile_required_interview_list_id(http_client_test, test_college_validation, setup_module,
                                             college_super_admin_access_token,application_details
                                             ):
    # Required interview list id
    from app.database.configuration import DatabaseConfiguration
    interview_list = await DatabaseConfiguration().interview_list_collection.find_one(
        {})
    interview_list_id = str(interview_list.get('_id'))
    response = await http_client_test.get(
        f"/planner/student_profile/?application_id={str(application_details.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Interview List Id must be required and valid.'

@pytest.mark.asyncio
async def test_student_profile_invalid_college_id(http_client_test, test_college_validation, setup_module,
                                             college_super_admin_access_token, application_details
                                             ):

    # Invalid college id
    from app.database.configuration import DatabaseConfiguration
    interview_list = await DatabaseConfiguration().interview_list_collection.find_one(
        {})
    interview_list_id = str(interview_list.get('_id'))
    response = await http_client_test.get(
        f"/planner/student_profile/?interview_list_id={interview_list_id}"
        f"&application_id={str(application_details.get('_id'))}&college_id=123455&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_student_profile_invalid_application_id(http_client_test, test_college_validation, setup_module,
                                             college_super_admin_access_token,  application_details
                                             ):
    from app.database.configuration import DatabaseConfiguration
    interview_list = await DatabaseConfiguration().interview_list_collection.find_one(
        {})
    interview_list_id = str(interview_list.get('_id'))
    # Invalid application id to display student profile
    response = await http_client_test.get(
        f"/planner/student_profile/?interview_list_id={interview_list_id}&application_id=12334&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Application id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_student_profile_invalid_interview_list_id(http_client_test, setup_module,
                                college_super_admin_access_token, application_details,test_student_profile_details):
    #invalid interview list id
    from app.database.configuration import DatabaseConfiguration
    interview_list = await DatabaseConfiguration().interview_list_collection.find_one(
        {})
    interview_list_id = str(interview_list.get('_id'))
    response = await http_client_test.get(
        f"/planner/student_profile/?interview_list_id=12233&application_id={str(application_details.get('_id'))}"
        f"&college_id={str(application_details.get('college_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )


@pytest.mark.asyncio
async def test_student_profile_college_not_found(http_client_test, test_college_validation, setup_module,
                                             college_super_admin_access_token, application_details
                                             ):
    from app.database.configuration import DatabaseConfiguration
    interview_list = await DatabaseConfiguration().interview_list_collection.find_one(
        {})
    interview_list_id = str(interview_list.get('_id'))
    # College not found
    response = await http_client_test.get(
        f"/planner/student_profile/?interview_list_id={interview_list_id}&"
        f"application_id={str(application_details.get('_id'))}&college_id=123456789012345678901234"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'


@pytest.mark.asyncio
async def test_student_profile_application_not_found(http_client_test, test_college_validation, setup_module,
                                college_super_admin_access_token,application_details):
    #appilacation not found
    from app.database.configuration import DatabaseConfiguration
    interview_list = await DatabaseConfiguration().interview_list_collection.find_one(
        {})
    interview_list_id = str(interview_list.get('_id'))
    response = await http_client_test.get(
        f"/planner/student_profile/?interview_list_id={interview_list_id}&"
        f"application_id=123456789012345678901234&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == f"Application not found id: 123456789012345678901234"


@pytest.mark.asyncio
async def test_student_profile_interview_list_id_not_found(http_client_test, test_college_validation, setup_module,
                                college_super_admin_access_token,application_details):
    #interview list not found
    response = await http_client_test.get(
        f"/planner/student_profile/?interview_list_id=123456789012345678901234&"
        f"application_id={str(application_details.get('_id'))}&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == f"Interview List not found id: 123456789012345678901234"

@pytest.mark.asyncio
async def test_student_profile_display(http_client_test, setup_module,
                                       college_super_admin_access_token, application_details, test_student_profile_details,
                                       test_college_validation):
    #display student profile
    from app.database.configuration import DatabaseConfiguration
    interview_list = await DatabaseConfiguration().interview_list_collection.find_one(
        {})
    interview_list_id = str(interview_list.get('_id'))
    response = await http_client_test.get(
        f"/planner/student_profile/?interview_list_id={interview_list_id}&"
        f"application_id={str(application_details.get('_id'))}&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert "student_name" in response.json()
