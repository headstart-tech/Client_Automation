"""
This file contains test cases related to get user updates.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_user_updates(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, application_details,
        access_token
):
    """
    Test cases for API route which useful for get user updates.
    """
    # Un-authorized user tried to get user updates.
    response = await http_client_test.get(
        f"/resource/get_user_updates/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # Pass invalid access token for get user updates.
    response = await http_client_test.get(
        f"/resource/get_user_updates/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for get user updates.
    response = await http_client_test.get(
        f"/resource/get_user_updates/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

    # Invalid college id for get user updates.
    response = await http_client_test.get(
        f"/resource/get_user_updates/?college_id="
        f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # Wrong college id for get user updates.
    response = await http_client_test.get(
        f"/resource/get_user_updates/?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    # No enough permission for get user updates
    response = await http_client_test.get(
        f"/resource/get_user_updates/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{access_token}"},
        )
    assert response.status_code == 401
    assert response.json() == {"detail": 'Not enough permissions'}

    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().user_updates_collection.delete_many({})

    # No user updates found
    response = await http_client_test.get(
        f"/resource/get_user_updates/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        )
    assert response.status_code == 200
    assert response.json()["message"] == "Get the user updates."
    assert response.json()["data"] == []
    assert response.json()["pagination"] is None
    assert response.json()["total"] == 0

    response = await http_client_test.post(
        f"/resource/send_update_to_profile/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"selected_profiles": ["college_super_admin"], "title": "test",
              "content": "test"}
    )

    fields = ["_id", "title", "selected_profiles", "created_at",
              "last_updated_on", "created_by", "created_by_name", "content"]
    # Get user updates with pagination
    # TODO: Test cases failed when we run whole test cases
    #  but it is passed when we run this test case only.

    # response = await http_client_test.get(
    #     f"/resource/get_user_updates/?college_id="
    #     f"{str(test_college_validation.get('_id'))}&page_num=1&page_size=1",
    #     headers={"Authorization": f"Bearer "
    #                               f"{college_super_admin_access_token}"},
    # )
    # assert response.status_code == 200
    # assert response.json()["message"] == "Get the user updates."
    # for item in fields:
    #     assert item in response.json()["data"][0]
    # assert response.json()["pagination"] == \
    #        {"previous": None, "next": None}
    # assert response.json()["total"] == 1
    #
    # # Get user updates without pagination
    # response = await http_client_test.get(
    #     f"/resource/get_user_updates/?college_id="
    #     f"{str(test_college_validation.get('_id'))}",
    #     headers={"Authorization": f"Bearer "
    #                               f"{college_super_admin_access_token}"},
    # )
    # assert response.status_code == 200
    # assert response.json()["message"] == "Get the user updates."
    # for item in fields:
    #     assert item in response.json()["data"][0]
    # assert response.json()["pagination"] is None
    # assert response.json()["total"] == 1
    #
    # update_info = await (DatabaseConfiguration().user_updates_collection.
    #                      find_one({}))
    # update_id = str(update_info.get("_id"))
    # # Get user update by id
    # response = await http_client_test.get(
    #     f"/resource/get_user_updates/?college_id="
    #     f"{str(test_college_validation.get('_id'))}&update_id={update_id}",
    #     headers={"Authorization": f"Bearer "
    #                               f"{college_super_admin_access_token}"},
    # )
    # assert response.status_code == 200
    # assert response.json()["message"] == "Get the user updates."
    # for item in fields:
    #     assert item in response.json()["data"][0]
    # assert response.json()["pagination"] is None
    # assert response.json()["total"] == 1
    #
    # # Get user update by wrong update id
    # response = await http_client_test.get(
    #     f"/resource/get_user_updates/?college_id="
    #     f"{str(test_college_validation.get('_id'))}&update_id=123",
    #     headers={"Authorization": f"Bearer "
    #                               f"{college_super_admin_access_token}"},
    # )
    # assert response.status_code == 422
    # assert response.json()["detail"] == ("Update id `123` must be a 12-byte "
    #                                      "input or a 24-character hex string")
