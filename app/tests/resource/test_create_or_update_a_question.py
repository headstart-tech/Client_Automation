"""
This file contains test cases related to create or update a question.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_or_update_a_question(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, application_details
):
    """
    Test cases for API route which useful for create or update a question.
    """
    # Un-authorized user tried to create or update a question.
    response = await http_client_test.post(
        f"/resource/create_or_update_a_question/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # Pass invalid access token for create or update a question.
    response = await http_client_test.post(
        f"/resource/create_or_update_a_question/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for create or update a question.
    response = await http_client_test.post(
        f"/resource/create_or_update_a_question/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

    # Invalid college id for create or update a question.
    response = await http_client_test.post(
        f"/resource/create_or_update_a_question/?college_id="
        f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # Wrong college id for create or update a question.
    response = await http_client_test.post(
        f"/resource/create_or_update_a_question/?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    # Required body for create or update a question.
    response = await http_client_test.post(
        f"/resource/create_or_update_a_question/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and "
                                         "valid."}

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().questions.delete_many({})

    # Create a question.
    response = await http_client_test.post(
        f"/resource/create_or_update_a_question/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"question": "test", "answer": "test", "tags": ["test"]}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Question created successfully."}

    question = await DatabaseConfiguration().questions.find_one({})

    # Update a question.
    response = await http_client_test.post(
        f"/resource/create_or_update_a_question/?college_id="
        f"{str(test_college_validation.get('_id'))}&"
        f"question_id={str(question.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"question": "test1"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Question information updated "
                                          "successfully."}

    # Unable to Update a question.
    response = await http_client_test.post(
        f"/resource/create_or_update_a_question/?college_id="
        f"{str(test_college_validation.get('_id'))}&"
        f"question_id={str(question.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "There is nothing to update."}

    # Invalid question id for update a question.
    response = await http_client_test.post(
        f"/resource/create_or_update_a_question/?college_id="
        f"{str(test_college_validation.get('_id'))}&"
        f"question_id=123&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"question": "test1"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Question id `123` must be a 12-byte "
                                         "input or a 24-character hex string"}

    # Wrong question id for update a question.
    response = await http_client_test.post(
        f"/resource/create_or_update_a_question/?college_id="
        f"{str(test_college_validation.get('_id'))}&"
        f"question_id=123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"question": "test1"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Question not found by id: "
                                         "123456789012345678901234"}
