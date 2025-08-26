"""
This file contains test cases related to delete questions.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_delete_questions(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, access_token,
        test_question_validation
):
    """
    Test cases for API route which useful for delete questions.
    """
    # Un-authorized user tried to delete questions.
    response = await http_client_test.post(
        f"/resource/delete_questions/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # Pass invalid access token for delete questions.
    response = await http_client_test.post(
        f"/resource/delete_questions/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for delete questions.
    response = await http_client_test.post(
        f"/resource/delete_questions/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

    # Invalid college id for delete questions.
    response = await http_client_test.post(
        f"/resource/delete_questions/?college_id="
        f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # Wrong college id for delete questions.
    response = await http_client_test.post(
        f"/resource/delete_questions/?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    college_id = str(test_college_validation.get('_id'))
    # Required body for delete questions.
    response = await http_client_test.post(
        f"/resource/delete_questions/?college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and "
                                         "valid."}

    # Invalid question id for delete questions
    response = await http_client_test.post(
        f"/resource/delete_questions/?college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=["123"]
        )
    assert response.status_code == 422
    assert response.json()["detail"] == "Question id `123` must be a 12-byte input" \
                                        " or a 24-character hex string"

    # Wrong question id for delete questions
    response = await http_client_test.post(
        f"/resource/delete_questions/?college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=["123456789012345678901234"]
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Make sure provided questions "
                                         "ids are correct."}

    from app.database.configuration import DatabaseConfiguration
    question = await DatabaseConfiguration().questions.find_one({})

    # Delete questions
    response = await http_client_test.post(
        f"/resource/delete_questions/?college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json=[str(question.get('_id'))]
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Questions deleted successfully."}
