"""
This file contains test cases of store_feedback route
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asycio
async def test_store_feedback_not_authenticated(http_client_test, test_college_validation, setup_module, access_token,
                                college_super_admin_access_token, test_user_validation, application_details,test_slot_details
                                ):
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/interview/store_feedback/?application_id={str(application_details.get('_id'))}&"
        f"slot_id={str(test_slot_details.get('_id'))}&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_store_feedback_bad_token(http_client_test, test_college_validation, setup_module, access_token,
                                        college_super_admin_access_token, test_user_validation, application_details
                                        , test_slot_details):
    # Bad token to get details
    response = await http_client_test.post(
        f"/interview/store_feedback/?application_id={str(application_details.get('_id'))}&"
        f"slot_id={str(test_slot_details.get('_id'))}&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_store_feedback_college_required_field(http_client_test, test_college_validation, setup_module, access_token,
                                                     college_super_admin_access_token, test_user_validation, application_details
                                                     , test_slot_details):
    # Required college id
    response = await http_client_test.post(
        f"/interview/store_feedback/?application_id={str(application_details.get('_id'))}&"
        f"{str(test_slot_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'


@pytest.mark.asyncio
async def test_store_feedback_required_application_id_field(http_client_test, test_college_validation, setup_module, access_token,
                                                            college_super_admin_access_token, test_user_validation, application_details
                                                            , test_slot_details):
    # Required application id
    response = await http_client_test.post(
        f"/interview/store_feedback/?college_id={str(test_college_validation.get('_id'))}&"
        f"slot_id={str(test_slot_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Application Id must be required and valid.'


@pytest.mark.asyncio
async def test_store_feedback_required_slot_id_field(http_client_test, test_college_validation, setup_module, access_token,
                                                            college_super_admin_access_token, test_user_validation, application_details
                                                            ):
    # Required slot id
    response = await http_client_test.post(
        f"/interview/store_feedback/?college_id={str(test_college_validation.get('_id'))}&"
        f"application_id={str(application_details.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Slot Id must be required and valid.'


@pytest.mark.asyncio
async def test_store_feedback_invalid_college_id(http_client_test, test_college_validation, setup_module, access_token,
                                                 college_super_admin_access_token, test_user_validation, application_details
                                                 , test_slot_details):

    # Invalid college id
    response = await http_client_test.post(
        f"/interview/store_feedback/?application_id={str(application_details.get('_id'))}&"
        f"slot_id={str(test_slot_details.get('_id'))}&college_id=123455&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_store_feedback_invalid_application_id(http_client_test, test_college_validation, setup_module, access_token,
                                                     college_super_admin_access_token, test_user_validation, application_details
                                                     , test_slot_details):

    # Invalid application id to store feed back
    response = await http_client_test.post(
        f"/interview/store_feedback/?application_id=12334&slot_id={str(test_slot_details.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"scores":[{"name": "Communication Skill","point": 1.5}],"status": "Shortlisted","comments": "string"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Application id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_store_feedback_invalid_slot_id(http_client_test, test_college_validation, setup_module, access_token,
                                                     college_super_admin_access_token, test_user_validation, application_details
                                                     , test_slot_details):

    # Invalid slot id to store feed back
    response = await http_client_test.post(
        f"/interview/store_feedback/?application_id={str(application_details.get('_id'))}&"
        f"slot_id=1112&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"scores":[{"name": "Communication Skill","point": 1.5}],"status": "Shortlisted","comments": "string"}
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Slot id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_store_feedback_college_not_found(http_client_test, test_college_validation, setup_module, access_token,
                                                college_super_admin_access_token, test_user_validation, application_details
                                                , test_slot_details):
    # College not found
    response = await http_client_test.post(
        f"/interview/store_feedback/?application_id={str(application_details.get('_id'))}"
        f"&slot_id={str(test_slot_details.get('_id'))}&college_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

@pytest.mark.asyncio
async def test_store_feedback(http_client_test, test_college_validation, setup_module, access_token,
                              college_super_admin_access_token, test_user_validation, application_details,
                              test_slot_details):
    #store the feedbaack
    response = await http_client_test.post(
        f"/interview/store_feedback/?application_id={str(application_details.get('_id'))}&"
        f"slot_id={str(test_slot_details.get('_id'))}&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"scores":[{"name": "Communication Skill","point": 1.5}],"status": "Shortlisted","comments": "string"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "feedback data added."


@pytest.mark.asyncio
async def test_store_feedback_body_required(http_client_test, test_college_validation, setup_module, access_token,
                                            college_super_admin_access_token, test_user_validation, application_details,
                                            test_slot_details):
    #body required to store feedback
    response = await http_client_test.post(
        f"/interview/store_feedback/?application_id={str(application_details.get('_id'))}&"
        f"slot_id={str(test_slot_details.get('_id'))}&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}


@pytest.mark.asyncio
async def test_store_feedback_application_not_found(http_client_test, test_college_validation, setup_module, access_token,
                                                    college_super_admin_access_token, test_user_validation, application_details,
                                                    test_slot_details):
    #appilacation not found
    response = await http_client_test.post(
        f"/interview/store_feedback/?application_id=123456789012345678901234&"
        f"slot_id={str(test_slot_details.get('_id'))}&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"scores":[{"name": "Communication Skill","point": 1.5}],"status": "Shortlisted","comments": "string"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == f"Application not found id: 123456789012345678901234"
