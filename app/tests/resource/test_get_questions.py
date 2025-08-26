"""
This file contains test cases related to get questions.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_questions(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, access_token,
        test_question_validation
):
    """
    Test cases for API route which useful for get questions.
    """
    # Un-authorized user tried to get questions.
    response = await http_client_test.post(
        f"/resource/get_questions/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # Pass invalid access token for get questions.
    response = await http_client_test.post(
        f"/resource/get_questions/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for get questions.
    response = await http_client_test.post(
        f"/resource/get_questions/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

    # Invalid college id for get questions.
    response = await http_client_test.post(
        f"/resource/get_questions/?college_id="
        f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # Wrong college id for get questions.
    response = await http_client_test.post(
        f"/resource/get_questions/?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    college_id = str(test_college_validation.get('_id'))

    fields = ["_id", "question", "answer", "tags", "created_by_id",
              "last_updated_on", "created_by", "last_updated_by",
              "last_updated_by_id", "school_name", "program_list"]

    # Get question with pagination
    response = await http_client_test.post(
        f"/resource/get_questions/?college_id="
        f"{college_id}&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the questions."
    for item in fields:
        assert item in response.json()["data"][0]
    assert response.json()["pagination"] == \
           {"previous": None, "next": None}
    assert response.json()["total"] == 1

    # Get user updates without pagination
    response = await http_client_test.post(
        f"/resource/get_questions/?college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the questions."
    for item in fields:
        assert item in response.json()["data"][0]
    assert response.json()["pagination"] is None
    assert response.json()["total"] == 1

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().questions.delete_many({})
    # No any question found
    response = await http_client_test.post(
        f"/resource/get_questions/?college_id="
        f"{college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the questions."
    assert response.json()["data"] == []
    assert response.json()["pagination"] is None
    assert response.json()["total"] == 0
